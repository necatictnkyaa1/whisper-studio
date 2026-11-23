"""Yeni çeviri yoluyla tam kayıt karşılaştırması. Önceki sonuçlar korunur."""
import json,time,sys
from pathlib import Path
from dataclasses import asdict
from core import Segment,render_plain,render
from lecture_translation import LectureTranslator,validate,validate_alignment,SYSTEM
from llm import OllamaClient
baseline=Path('ornekler/29-09-kalite');root=baseline/(sys.argv[1] if len(sys.argv)>1 else 'ikinci-inceleme');root.mkdir(exist_ok=True)
data=json.loads((baseline/'ayrintili-sonuc.json').read_text(encoding='utf-8'))
raw=[Segment(s['start'],s['end'],s['original'],original=s['original'],source_language=s['source_language']) for s in data['rows']]
# İki farklı uzun pencere create/delete konusunda anlaşıyor; kısa pencere talent demişti.
# Bu, insan tarafından hazırlanmış bir referans değil; ayrı akustik yeniden çözümlemedir.
views=json.loads(Path('../../work/audit29/communication-words.json').read_text(encoding='utf-8'))
assert len(views)==2
for view in views:
 assert 'create, delete communication' in ' '.join(r['text'].strip() for r in view['rows']).casefold()
s=raw[60];before=s.original
replacement=' '.join(w['word'].strip() for r in views[0]['rows'] for w in r['words'] if s.start<=(w['start']+w['end'])/2<s.end)
assert 'Create, delete communication' in replacement and 'shared memory model' in replacement
raw[60]=Segment(s.start,s.end,replacement,original=replacement,source_language='en')
acoustic_audit={'row':60,'original_short_window_asr':before,'new_context_window_asr':replacement,
 'method':'Large-v3, aynı ses, EN, anahtar sözcük zorlaması yok; 408–466 ve 420–466 saniye iki görünüm; ilk görünüm sözcük zamanlarıyla bölüm aralığına kırpıldı.',
 'human_reference':False}
rows=[];checkpoint=root/'kismi-sonuc.json'
if checkpoint.exists():
 candidate=[Segment(**s) for s in json.loads(checkpoint.read_text(encoding='utf-8'))]
 if len(candidate)<=len(raw) and all(s.original==raw[i].original for i,s in enumerate(candidate)):rows=candidate
client=OllamaClient(host='127.0.0.1:11438');translator=None;started=time.monotonic()
try:
 translator=LectureTranslator(True,print,lambda:False,client)
 translator.previous_translations=rows[-2:]
 def emit(segment,progress):
  rows.append(segment)
  checkpoint.write_text(json.dumps([asdict(s) for s in rows],ensure_ascii=False,indent=2),encoding='utf-8')
  if len(rows)%20==0:print('PUBLISHED',len(rows),'/',len(raw),flush=True)
 translator.translate(raw,'tr',emit,start_at=len(rows))
 assert len(rows)==len(raw)
 previous=[]
 for i,row in enumerate(rows):
  validate([{'id':str(i),'text':row.original}],{'translations':{str(i):row.text}},'tr')
  validate_alignment(row.original,row.text,previous)
  previous=(previous+[(row.original,row.text)])[-2:]
 output={'seconds_this_translation_run':round(time.monotonic()-started,2),'selection':data['selection'],
  'pipeline':'topic-context-small-batches-coverage-v6','rows':[asdict(s) for s in rows],
  'acoustic_revision':acoustic_audit,'normalizations':getattr(translator,'normalizations',[]),
  'quality_status':'İnceleme sürümü; tam ses için insan referansı veya doğruluk yüzdesi yok.'}
 (root/'ayrintili-sonuc.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
 (root/'ders-metni.txt').write_text(render_plain(rows),encoding='utf-8-sig')
 (root/'ders-altyazi.srt').write_text(render(rows,True),encoding='utf-8-sig')
 (root/'orijinal-transkript.txt').write_text(render_plain(raw),encoding='utf-8-sig')
 (root/'akustik-duzeltme.json').write_text(json.dumps(acoustic_audit,ensure_ascii=False,indent=2),encoding='utf-8')
 print('COMPLETE',len(rows),output['seconds_this_translation_run'],flush=True)
finally:
 if translator:translator.close()
 client.stop()
