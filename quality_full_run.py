import json,time
from dataclasses import asdict
from pathlib import Path
from core import transcribe,render_plain,render
root=Path('ornekler/kalite-20261016');root.mkdir(parents=True,exist_ok=True)
rows=[];started=time.monotonic();last=0

def status(text):
    global last
    if time.monotonic()-last>=10:
        last=time.monotonic();print(text,flush=True)

def emit(segment,progress):
    rows.append(segment)
    if len(rows)%20==0:
        (root/'ilerleme.json').write_text(json.dumps({'progress':progress,'rows':len(rows),'seconds':round(time.monotonic()-started)},ensure_ascii=False),encoding='utf-8')
        print('PROGRESS',progress,len(rows),flush=True)

transcribe(Path(r'C:\Users\Necati\Downloads\13-10-2026.mp3'),'turbo',None,'cuda',True,emit,status,lambda:False,'tr')
(root/'ders-metni.txt').write_text(render_plain(rows),encoding='utf-8-sig')
(root/'ders-altyazi.srt').write_text(render(rows,True),encoding='utf-8-sig')
(root/'ayrintili-sonuc.json').write_text(json.dumps({'seconds':round(time.monotonic()-started,2),'model':'turbo','rows':[asdict(s) for s in rows]},ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE',len(rows),round(time.monotonic()-started,2),flush=True)
