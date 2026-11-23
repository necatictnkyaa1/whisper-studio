"""Gerçek kaynak cümlelerde üretim ayarı karşılaştırması; ASR doğruluk ölçümü değildir."""
import json,time
from pathlib import Path
from lecture_translation import LectureTranslator
from llm import OllamaClient
source=json.loads(Path('ornekler/29-09-kalite/ayrintili-sonuc.json').read_text(encoding='utf-8'))['rows']
client=OllamaClient(host='127.0.0.1:11438');translator=None;results=[]
try:
 translator=LectureTranslator(True,print,lambda:False,client)
 chat=client.chat
 for temperature in (.7,0):
  def configured(*args,**kwargs):
   kwargs['temperature']=temperature
   kwargs['max_tokens']=2048
   return chat(*args,**kwargs)
  client.chat=configured
  for i in (40,42,64,65):
   context=' '.join(s['original'] for s in source[max(0,i-2):i]);started=time.monotonic()
   try:result=translator.batch([{'id':str(i),'text':source[i]['original']}],'tr',context)[str(i)]
   except Exception as error:result='ERROR: '+str(error)
   results.append({'row':i,'temperature':temperature,'source':source[i]['original'],'previous_translation':source[i]['text'],'translation':result,'seconds':round(time.monotonic()-started,2)})
   Path('../../work/audit29/translation-sampling.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
   print(temperature,i,result,flush=True)
finally:
 if translator:translator.close()
 client.stop()
