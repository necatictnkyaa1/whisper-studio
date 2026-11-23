import core,time,json
from faster_whisper import WhisperModel
from pathlib import Path
print('Large-v3 indiriliyor / yükleniyor',flush=True)
started=time.monotonic()
model=WhisperModel('models/large-v3-quality',device='cuda',compute_type='int8_float16',download_root='models',local_files_only=True)
print('READY',time.monotonic()-started,flush=True)
from faster_whisper.audio import decode_audio
root=Path('../../work/audit29')
results=[]
for name in ('parameters','system-calls','turkish'):
 audio=decode_audio(str(root/(name+'.wav')))
 rows,info=model.transcribe(audio,language='tr' if name=='turkish' else 'en',beam_size=5,condition_on_previous_text=False,vad_filter=True,word_timestamps=True,temperature=(0,.2,.4))
 values=[dict(start=s.start,end=s.end,text=s.text,score=s.avg_logprob) for s in rows]
 results.append(dict(clip=name,rows=values))
 (root/'large-reference.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print(name,len(values),flush=True)
