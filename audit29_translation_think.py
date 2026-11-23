import json,time
from pathlib import Path
from lecture_translation import LectureTranslator
from llm import OllamaClient
source=json.loads(Path('ornekler/29-09-kalite/ayrintili-sonuc.json').read_text(encoding='utf-8'))['rows']
client=OllamaClient(host='127.0.0.1:11438');translator=None;results=[]
try:
 translator=LectureTranslator(True,print,lambda:False,client);chat=client.chat
 def configured(*args,**kwargs):
  kwargs.update(temperature=.6,think=True,max_tokens=4096)
  return chat(*args,**kwargs)
 client.chat=configured
 for i in (40,42,64,65):
  started=time.monotonic();context=' '.join(s['original'] for s in source[max(0,i-2):i])
  try:result=translator.batch([{'id':str(i),'text':source[i]['original']}],'tr',context)[str(i)]
  except Exception as error:result='ERROR: '+str(error)
  results.append({'row':i,'source':source[i]['original'],'translation':result,'seconds':round(time.monotonic()-started,2)})
  Path('../../work/audit29/translation-thinking.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
  print(i,result,flush=True)
finally:
 if translator:translator.close()
 client.stop()
