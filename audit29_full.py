from pathlib import Path
import time,json
from dataclasses import asdict
from core import transcribe,render_plain,render
root=Path('ornekler/29-09-kalite');root.mkdir(parents=True,exist_ok=True)
model=Path('models/large-v3-quality/model.bin')

print('FULL_START',flush=True);rows=[];started=time.monotonic();last=0

def status(text):
 global last
 if time.monotonic()-last>12:print(text,flush=True);last=time.monotonic()

def emit(segment,progress):
 rows.append(segment)
 (root/'kismi-sonuc.json').write_text(json.dumps([asdict(s) for s in rows],ensure_ascii=False),encoding='utf-8')
 (root/'ilerleme.json').write_text(json.dumps({'progress':progress,'rows':len(rows),'seconds':round(time.monotonic()-started)}),encoding='utf-8')
 if len(rows)%20==0:print('PUBLISHED',len(rows),progress,flush=True)
 (root/'kismi-ders-metni.txt').write_text(render_plain(rows),encoding='utf-8-sig')

transcribe(Path(r'C:\Users\Necati\Downloads\29-09-2026.mp3'),'auto',None,'auto',True,emit,status,lambda:False,'tr')
(root/'ders-metni.txt').write_text(render_plain(rows),encoding='utf-8-sig')
(root/'ders-altyazi.srt').write_text(render(rows,True),encoding='utf-8-sig')
(root/'ayrintili-sonuc.json').write_text(json.dumps({'seconds':round(time.monotonic()-started,2),'selection':json.loads(Path('automatic-selection.json').read_text(encoding='utf-8')),'rows':[asdict(s) for s in rows]},ensure_ascii=False,indent=2),encoding='utf-8')
print('FULL_COMPLETE',len(rows),round(time.monotonic()-started,2),flush=True)
