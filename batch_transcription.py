"""Sıralı, iki dilli TXT kuyruğu. Her kaydın ASR'si bir kez çalışır."""
import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from core import Segment, render_plain, transcribe

OUTPUT_MODES = {
    'both': ('tr', 'en'),
    'tr': ('tr',),
    'en': ('en',),
    'original': ('original',),
}
OUTPUT_LABELS = {'tr': 'Türkçe', 'en': 'İngilizce', 'original': 'Orijinal'}


def atomic_write(path,text,encoding='utf-8'):
    path=Path(path);temporary=path.with_name(path.name+'.partial')
    try:
        with temporary.open('w',encoding=encoding) as output:
            output.write(text);output.flush();os.fsync(output.fileno())
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)


def save_job(path,job):
    atomic_write(path,json.dumps(job,ensure_ascii=False,indent=2))


def create_job(paths,folder,output_mode='both'):
    if output_mode not in OUTPUT_MODES:
        raise ValueError('Geçersiz çıktı dili.')
    unique=list(dict.fromkeys(str(Path(p).resolve()) for p in paths))
    if not unique:raise ValueError('En az bir kayıt seç.')
    records=[];names=set()
    for name in unique:
        source=Path(name);stat=source.stat()
        stem=source.stem[:140].rstrip(' .') or 'Kayit'
        title=stem;index=2
        while title.casefold() in names:title=f'{stem} ({index})';index+=1
        names.add(title.casefold())
        records.append({'source':name,'size':stat.st_size,'mtime_ns':stat.st_mtime_ns,
                        'title':title,'state':'Bekliyor','error':'','outputs':{}})
    directory=Path(folder)/('Whisper Studio '+datetime.now().strftime('%Y-%m-%d %H-%M-%S')+' '+uuid.uuid4().hex[:6])
    directory.mkdir(parents=True,exist_ok=False)
    manifest=directory/'kuyruk.json'
    save_job(manifest,{'version':1,'output_mode':output_mode,'records':records})
    return manifest


def load_job(manifest):
    job=json.loads(Path(manifest).read_text(encoding='utf-8'))
    if job.get('version')!=1 or not isinstance(job.get('records'),list):raise ValueError('Geçersiz kuyruk dosyası')
    job.setdefault('output_mode','both')
    if not isinstance(job['output_mode'],str) or job['output_mode'] not in OUTPUT_MODES:
        raise ValueError('Geçersiz kuyruk çıktı dili.')
    for record in job['records']:
        title=record['title']
        if not title or any(c in title for c in '/\\:') or title in ('.','..'):raise ValueError('Geçersiz çıktı adı')
    return job


def run_job(manifest,offline,status,cancelled,changed,runner=transcribe,translator_factory=None,translation_only=False):
    if translator_factory is None:
        from lecture_translation import LectureTranslator
        translator_factory=LectureTranslator
    manifest=Path(manifest);job=load_job(manifest);folder=manifest.parent
    languages=OUTPUT_MODES[job['output_mode']]
    for index,record in enumerate(job['records']):
        if cancelled():break
        translator=None
        checkpoint_path=folder/(record['title']+'.durum.json')
        def update(state):
            record['state']=state;save_job(manifest,job);changed(index,dict(record))
        def report(message):
            status(f'{index+1}/{len(job["records"])} · {Path(record["source"]).name} · {message}')
        try:
            record['error']=''
            # Bitmiş çıktı, kaynak taşınmış olsa da geçerlidir; silinmiş çıktı yeniden üretilir.
            if record['state']=='Tamamlandı' and all((folder/(record['title']+f'-{lang}.txt')).is_file() for lang in languages):
                changed(index,dict(record));continue
            source=Path(record['source']);stat=source.stat()
            if stat.st_size==0:
                raise ValueError('Ses dosyası boş (0 bayt). Orijinal kaydı yeniden indirip seç.')
            if (stat.st_size,stat.st_mtime_ns)!=(record['size'],record['mtime_ns']):
                raise ValueError('Kaynak kayıt değişmiş. Bu dosya için yeni kuyruk oluştur.')
            checkpoint=json.loads(checkpoint_path.read_text(encoding='utf-8')) if checkpoint_path.exists() else {'source':None,'tr':[],'en':[]}
            def persist():atomic_write(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False))
            if checkpoint['source'] is None:
                if translation_only:raise ValueError('Çeviri-only: kaynak transkript eksik; ASR başlatılmadı.')
                update('Konuşma çözümleniyor');rows=[]
                runner(source,'auto',None,'auto',offline,lambda row,progress:rows.append(row),report,cancelled,target_language=None)
                if cancelled():update('Durduruldu');break
                if not rows or not any(row.text.strip() for row in rows):raise ValueError('Kayıttan konuşma metni elde edilemedi.')
                checkpoint['source']=[asdict(row) for row in rows];persist()
            rows=[Segment(**row) for row in checkpoint['source']]
            if translation_only:
                if not rows:raise ValueError('Kaynak transkript boş.')
                for language in (lang for lang in languages if lang!='original'):
                    saved=checkpoint[language]
                    if len(saved)>len(rows):raise ValueError('Checkpoint satır sayısı tutarsız.')
                    for i,item in enumerate(saved):
                        if (item['start'],item['end'],item.get('original'))!=(rows[i].start,rows[i].end,rows[i].original or rows[i].text):
                            raise ValueError('Checkpoint kaynak/zaman hizası tutarsız.')
            for language in languages:
                label=OUTPUT_LABELS[language]
                if cancelled():break
                completed=rows if language=='original' else [Segment(**row) for row in checkpoint[language]]
                if len(completed)>len(rows):raise ValueError('Kayıt kontrol dosyası tutarsız.')
                output=folder/(record['title']+f'-{language}.txt')
                if len(completed)<len(rows):
                    update(label+' metin hazırlanıyor')
                    if translator is None:translator=translator_factory(offline,report,cancelled)
                    translator.previous_translations=completed[-2:]
                    def publish(row,progress):
                        completed.append(row)
                        checkpoint[language].append(asdict(row))
                        if len(completed)%8==0:persist()
                    try:translator.translate(rows,language,publish,start_at=len(completed))
                    finally:persist()
                if cancelled():break
                if len(completed)!=len(rows) or not all(row.text.strip() for row in completed):
                    raise ValueError(label+' metin tamamlanamadı; eksik çıktı başarı olarak kaydedilmedi.')
                if not output.exists():atomic_write(output,render_plain(completed),encoding='utf-8-sig')
                record['outputs'][language]=str(output);update(label+' TXT kaydedildi')
            if cancelled():update('Durduruldu');break
            update('Tamamlandı')
        except Exception as error:
            record['error']=str(error)
            update('Durduruldu' if cancelled() else 'Hata')
            if cancelled():break
        finally:
            if translator is not None:
                try:translator.close()
                except Exception as error:status('Çeviri motoru kapatma notu: '+str(error))
    return job
