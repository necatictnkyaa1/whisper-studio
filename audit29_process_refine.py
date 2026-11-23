import core,json
from pathlib import Path
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
model=WhisperModel('models/large-v3-quality',device='cuda',compute_type='int8_float16',local_files_only=True)
audio=decode_audio(r'C:\Users\Necati\Downloads\29-09-2026.mp3')[round(272*16000):round(298*16000)]
results=[]
for label,hotwords in [('plain',None),('bilingual-terms','process, işlem, process control, system call types')]:
 rows,_=model.transcribe(audio,language='en',beam_size=8,vad_filter=False,condition_on_previous_text=False,temperature=0,word_timestamps=True,hotwords=hotwords)
 rows=list(rows);text=' '.join(s.text.strip() for s in rows);score=sum(s.avg_logprob for s in rows)/max(1,len(rows))
 results.append({'label':label,'text':text,'score':score});print(label,text,score,flush=True)
Path('../../work/audit29/process-refinement.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
