import sys,json,time
from dataclasses import asdict
from pathlib import Path
from core import transcribe
root=Path('../../work/quality')
results=[]
for model in ('small','turbo'):
    for name in ('language-switch','technical'):
        rows=[];started=time.monotonic()
        print('START',model,name,flush=True)
        transcribe(root/(name+'.wav'),model,None,'cuda',True,lambda s,p:rows.append(asdict(s)),lambda s:None,lambda:False,'tr')
        result={'model':model,'clip':name,'seconds':round(time.monotonic()-started,2),'rows':rows}
        results.append(result)
        (root/'baseline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print('DONE',model,name,len(rows),result['seconds'],flush=True)
