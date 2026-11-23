import json
from pathlib import Path
from dataclasses import asdict
from core import Segment,render_plain,render
from lecture_translation import LectureTranslator,validate,validate_alignment,ModelError
from llm import OllamaClient
root=Path('ornekler/29-09-kalite/ikinci-inceleme');data=json.loads((root/'ayrintili-sonuc.json').read_text(encoding='utf-8'))
rows=data['rows'];client=OllamaClient(host='127.0.0.1:11438');translator=None;audit=list(data.get('validation_repairs',[]))
try:
 translator=LectureTranslator(True,print,lambda:False,client)
 previous=[]
 for i,row in enumerate(rows):
  reason=None
  try:
   validate([{'id':str(i),'text':row['original']}],{'translations':{str(i):row['text']}},'tr')
   validate_alignment(row['original'],row['text'],previous)
  except ModelError as error:reason=str(error)
  if reason:
   context=' '.join(s['original'] for s in rows[max(0,i-2):i])
   old=row['text'];text=translator.batch([{'id':str(i),'text':row['original']}],'tr',context)[str(i)]
   validate_alignment(row['original'],text,previous)
   row['text']=text;row['translated']=text.casefold()!=row['original'].casefold()
   audit.append({'row':i,'reason':reason,'old':old,'new':text});print('REPAIRED',i,text,flush=True)
  previous=(previous+[(row['original'],row['text'])])[-2:]
 data['pipeline']='topic-context-v4-full-run + v6-individual-validation-repairs';data['validation_repairs']=audit
 (root/'ayrintili-sonuc.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 (root/'ceviri-duzeltmeleri.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
 segments=[Segment(**s) for s in rows]
 (root/'ders-metni.txt').write_text(render_plain(segments),encoding='utf-8-sig')
 (root/'ders-altyazi.srt').write_text(render(segments,True),encoding='utf-8-sig')
 print('VALIDATED',len(rows),'REPAIRS',len(audit),flush=True)
finally:
 if translator:translator.close()
 client.stop()
