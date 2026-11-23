import core,json
from pathlib import Path
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
audio=decode_audio(r'C:\Users\Necati\Downloads\29-09-2026.mp3');start,end=408,466
model=WhisperModel('models/large-v3-quality',device='cuda',compute_type='int8_float16',local_files_only=True)
result=[]
for left in (408,420):
 rows,_=model.transcribe(audio[left*16000:end*16000],language='en',beam_size=5,
  vad_filter=True,condition_on_previous_text=False,temperature=0,word_timestamps=True)
 values=[{'start':left+s.start,'end':left+s.end,'text':s.text,'score':s.avg_logprob,
  'words':[{'start':left+w.start,'end':left+w.end,'word':w.word} for w in s.words or []]} for s in rows]
 result.append({'clip_start':left,'rows':values})
 Path('../../work/audit29/communication-words.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(left,' '.join(s['text'] for s in values),flush=True)
