from pathlib import Path
import json,time
from dataclasses import asdict
from core import transcribe
from lecture_translation import LectureTranslator
from llm import OllamaClient
root=Path('../../work/audit29');groups=[]
for name in ('parameters','system-calls','turkish'):
 rows=[]
 transcribe(root/(name+'.wav'),'turbo',None,'cuda',True,lambda s,p:rows.append(s),lambda _:None,lambda:False,None)
 groups.append((name,rows));print('ASR',name,len(rows),flush=True)
client=OllamaClient(host='127.0.0.1:11438');translator=None;results=[]
try:
 translator=LectureTranslator(True,print,lambda:False,client)
 for name,rows in groups:
  out=[];translator.translate(rows,'tr',lambda s,p:out.append(asdict(s)))
  results.append({'clip':name,'rows':out});print('TRANSLATED',name,flush=True)
  (root/'turbo-qwen.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 if translator:translator.close()
 client.stop()
