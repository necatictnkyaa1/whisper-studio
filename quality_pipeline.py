"""Önce orijinal transkript, sonra bağlamlı yerel çeviri. Argos'a sessiz dönüş yok."""
import gc
import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from automatic import run_automatic, profiles, inspect_hardware, cached

VERSION='large-context-v5'

def run(path,offline,on_segment,status,cancelled,target,runner):
    if not target:
        return run_automatic(path,offline,on_segment,status,cancelled,None,runner)
    from lecture_translation import LectureTranslator, SYSTEM, SYSTEM_EN
    from llm import Cancelled
    from core import Segment
    translator=None
    try:
        translator=LectureTranslator(offline,status,cancelled)
        file=Path(path);stat=file.stat()
        candidates=profiles(inspect_hardware())
        if offline:candidates=[p for p in candidates if cached(p.model)]
        preferred=candidates[0].model if candidates else 'none'
        selected=[]
        def record_runner(path,model,*args,**kwargs):
            selected.append(model)
            return runner(path,model,*args,**kwargs)
        key=hashlib.sha256(f'{file.resolve()}:{stat.st_size}:{stat.st_mtime_ns}:{VERSION}:{preferred}'.encode()).hexdigest()
        folder=Path(__file__).resolve().parent/'.runtime'/'transcripts';folder.mkdir(parents=True,exist_ok=True)
        cache=folder/(key+'.json');rows=[]
        # Hazır kaynak transkript donanımın o anki boş belleğinden bağımsızdır.
        # Bellek değişti diye aynı sesin ASR'sini yeniden başlatma.
        for previous_model in dict.fromkeys((preferred,'large-v3','turbo','small','base','tiny')):
            previous_key=hashlib.sha256(f'{file.resolve()}:{stat.st_size}:{stat.st_mtime_ns}:{VERSION}:{previous_model}'.encode()).hexdigest()
            previous_cache=folder/(previous_key+'.json')
            if not previous_cache.is_file():continue
            try:
                saved=json.loads(previous_cache.read_text(encoding='utf-8'))
                if saved.get('complete') and saved.get('version')==VERSION and saved.get('model') in ('large-v3','turbo','small','base','tiny'):
                    rows=[Segment(**r) for r in saved['segments']]
                    if rows:
                        key=previous_key;cache=previous_cache
                        break
            except (OSError,ValueError,TypeError,KeyError):pass
        if not rows:
            def collect(segment,progress):
                rows.append(segment)
                status(f'Orijinal konuşma çözümleniyor · %{min(64,int(progress*.65))}')
            # Hedef dil yok: eski Argos çeviri yolu bu aşamada hiç çağrılmaz.
            run_automatic(path,offline,collect,status,cancelled,None,record_runner)
            if cancelled():return
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',suffix='.partial',dir=folder,delete=False) as output:
                temporary=Path(output.name)
                json.dump({'version':VERSION,'complete':True,'model':selected[-1] if selected else preferred,'segments':[asdict(s) for s in rows]},output,ensure_ascii=False)
            os.replace(temporary,cache)
        else:status('Orijinal transkript hazır · yerel önbellekten alındı · %65')
        if cancelled():return
        gc.collect()
        # Kaynak + hedef + model + çeviri ilkeleri değişirse eski çıktı kullanılmaz.
        translated_key=hashlib.sha256((key+target+str(translator.plan.name)+(SYSTEM_EN if target=='en' else SYSTEM)+'object-schema-v9-ranks-time-state').encode()).hexdigest()
        translated_cache=folder/(translated_key+'-translated.json')
        completed=[]
        if translated_cache.is_file():
            try:
                candidates=[Segment(**r) for r in json.loads(translated_cache.read_text(encoding='utf-8'))]
                if len(candidates)<=len(rows) and all(
                    (s.start,s.end,s.original)==(rows[i].start,rows[i].end,rows[i].original or rows[i].text)
                    for i,s in enumerate(candidates)):
                    completed=candidates
            except (OSError,ValueError,TypeError,KeyError):pass
        def persist():
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',suffix='.partial',dir=folder,delete=False) as output:
                temporary=Path(output.name)
                json.dump([asdict(s) for s in completed],output,ensure_ascii=False)
            os.replace(temporary,translated_cache)
        for i,segment in enumerate(completed):
            if cancelled():return
            on_segment(segment,min(99,65+int(34*(i+1)/max(1,len(rows)))))
        def publish(segment,progress):
            completed.append(segment)
            if len(completed)%8==0:persist()
            on_segment(segment,progress)
        try:
            translator.previous_translations=completed[-2:]
            translator.translate(rows,target,publish,start_at=len(completed))
        finally:
            if completed:persist()
    except Cancelled:
        if not cancelled():raise
    finally:
        if translator is not None:translator.close()
