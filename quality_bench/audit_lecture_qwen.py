"""Kullanıcının dersindeki zor parçalar; insan referansı olmadığından WER hesaplanmaz."""
import json,time
from pathlib import Path
import torch,soundfile as sf,numpy as np
from transformers import AutoProcessor,AutoModelForMultimodalLM
ROOT=Path(__file__).resolve().parent;modelpath=ROOT.parent/'models/qwen3-asr-1.7b-compare'
processor=AutoProcessor.from_pretrained(modelpath,local_files_only=True)
model=AutoModelForMultimodalLM.from_pretrained(modelpath,device_map='cuda',dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).eval()
folder=(ROOT.parent/'../../work/quality-lecture-clips').resolve();rows=[]
clips=json.loads((folder/'clips.json').read_text(encoding='utf-8'))['rows']
for clip in clips:
  name,start,end=clip['clip'],clip['start'],clip['end']
  audio,rate=sf.read(clip['file'],dtype='float32');assert rate==16000
  started=time.monotonic();inputs=processor.apply_transcription_request(audio=audio,return_tensors='pt',audio_kwargs={'sampling_rate':16000}).to(model.device,model.dtype)
  with torch.inference_mode():ids=model.generate(**inputs,max_new_tokens=512,do_sample=False)
  parsed=processor.decode(ids[:,inputs['input_ids'].shape[1]:],return_format='parsed')[0]
  rows.append({'clip':name,'start':start,'end':end,'text':parsed['transcription'],'detected_language':parsed['language'],'seconds':round(time.monotonic()-started,3)})
  (ROOT/'results/lecture-audit-qwen.json').write_text(json.dumps({'human_reference':False,'metric':None,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
  print('LECTURE',name,parsed['transcription'],flush=True)
