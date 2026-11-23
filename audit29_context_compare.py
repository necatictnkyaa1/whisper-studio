"""Aynı zor ses parçalarında uzun bağlamlı Whisper karşılaştırması."""
import json,time
from pathlib import Path
import core
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
root=Path('../../work/audit29');root.mkdir(parents=True,exist_ok=True)
audio=decode_audio(r'C:\Users\Necati\Downloads\29-09-2026.mp3')
model=WhisperModel('models/large-v3-quality',device='cuda',compute_type='int8_float16',local_files_only=True)
results=[]
for name,start,end,language in [('opening',0,60,'tr'),('process',264,300,None),('communications',408,466,'en'),('parameters',170,245,'en')]:
 for previous in (False,True):
  stamp=time.monotonic()
  rows,info=model.transcribe(audio[round(start*16000):round(end*16000)],language=language,
      beam_size=5,vad_filter=True,condition_on_previous_text=previous,temperature=0,
      word_timestamps=True)
  values=[{'start':start+s.start,'end':start+s.end,'text':s.text,'avg_logprob':s.avg_logprob} for s in rows]
  result={'clip':name,'start':start,'end':end,'previous_context':previous,'seconds':round(time.monotonic()-stamp,2),'rows':values}
  results.append(result)
  (root/'whisper-context-comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
  print(name,previous,' '.join(s['text'] for s in values),flush=True)
