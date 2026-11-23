import core,json
from pathlib import Path
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
model=WhisperModel('models/large-v3-quality',device='cuda',compute_type='int8_float16',local_files_only=True)
audio=decode_audio(r'C:\Users\Necati\Downloads\29-09-2026.mp3')[274*16000:280*16000]
results=[]
for lang in ('en','tr'):
 rows,_=model.transcribe(audio,language=lang,beam_size=8,vad_filter=False,condition_on_previous_text=False,temperature=0,word_timestamps=True)
 rows=list(rows);text=' '.join(s.text.strip() for s in rows);score=sum(s.avg_logprob for s in rows)/max(1,len(rows))
 results.append({'language':lang,'text':text,'score':score});print(lang,text,score,flush=True)
Path('../../work/audit29/code-switch-word.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
