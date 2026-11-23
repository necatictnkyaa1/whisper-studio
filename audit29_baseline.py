import json,time
from pathlib import Path
from dataclasses import asdict
from core import transcribe
root=Path('../../work/audit29');results=[]
for name in ('parameters','system-calls','turkish'):
 rows=[];started=time.monotonic()
 transcribe(root/(name+'.wav'),'small',None,'cuda',True,lambda s,p:rows.append(asdict(s)),lambda _:None,lambda:False,'tr')
 results.append(dict(clip=name,seconds=time.monotonic()-started,rows=rows))
 (root/'small-argos.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print(name,len(rows),flush=True)
