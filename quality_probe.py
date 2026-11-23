import json,time,gc
from pathlib import Path
import core
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from automatic import inspect_hardware
root=Path('../../work/quality');audio=decode_audio(str(root/'language-switch.wav'))
print('before',inspect_hardware(),flush=True)
model=WhisperModel('turbo',device='cuda',compute_type='float16',download_root='models',local_files_only=True)
print('loaded',inspect_hardware(),flush=True)
for name,opts in [('gentle-vad',dict(vad_filter=True,vad_parameters=dict(threshold=.25,min_silence_duration_ms=500,speech_pad_ms=400))),('no-vad',dict(vad_filter=False))]:
    rows,info=model.transcribe(audio,multilingual=True,beam_size=5,condition_on_previous_text=False,temperature=(0,.2,.4),word_timestamps=True,**opts)
    values=[dict(start=s.start,end=s.end,text=s.text,score=s.avg_logprob,ratio=s.compression_ratio) for s in rows]
    (root/(name+'.json')).write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf-8')
    print(name,len(values),flush=True)
from translation import LocalTranslator
translator=LocalTranslator('en','tr',True,print,lambda:False)
for text in ['In the next week, as well, we will do some code practices.','We will also leave all the topics.','What was the last topic in the previous session we were told? What was the last topic?','Which function? Loss function? MSA. MSA. What is MSA?']:
    print(repr(text),'=>',repr(translator.translate(text)),flush=True)
