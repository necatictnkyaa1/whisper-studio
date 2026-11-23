"""Resmî yerel Qwen3-ASR ile aynı sabit kayıtları, otomatik dil seçimiyle ölç."""
import argparse,json,time,hashlib,gc
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from transformers import AutoProcessor,AutoModelForMultimodalLM
from quality_bench.metrics import score
ROOT=Path(__file__).resolve().parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--device',choices=('cuda','cpu'),default='cuda');args=parser.parse_args()
 if args.device=='cuda' and not torch.cuda.is_available():raise RuntimeError('Karşılaştırma için CUDA PyTorch henüz hazır değil.')
 manifest_path=ROOT/'manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
 modelpath=ROOT.parent/'models/qwen3-asr-1.7b-compare';assert (modelpath/'model.safetensors').stat().st_size==4076193080
 started=time.monotonic();processor=AutoProcessor.from_pretrained(modelpath,local_files_only=True)
 model=AutoModelForMultimodalLM.from_pretrained(modelpath,local_files_only=True,device_map=args.device,
  dtype=torch.bfloat16,attn_implementation='sdpa');model.eval()
 output={'model':'Qwen3-ASR-1.7B','mode':'plain-auto','device':args.device,'dtype':'bfloat16','torch':torch.__version__,
  'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
  'load_seconds':round(time.monotonic()-started,3),'rows':[]}
 results=ROOT/'results';results.mkdir(exist_ok=True);path=results/'qwen-asr.json'
 for sample in manifest['samples']:
  audio,rate=sf.read(ROOT/sample['file'],dtype='float32');assert rate==16000 and audio.ndim==1
  if args.device=='cuda':torch.cuda.synchronize()
  started=time.monotonic()
  inputs=processor.apply_transcription_request(audio=np.asarray(audio),return_tensors='pt',audio_kwargs={'sampling_rate':rate}).to(model.device,model.dtype)
  with torch.inference_mode():output_ids=model.generate(**inputs,max_new_tokens=512,do_sample=False)
  generated_ids=output_ids[:,inputs['input_ids'].shape[1]:]
  parsed=processor.decode(generated_ids,return_format='parsed')
  if isinstance(parsed,list):parsed=parsed[0]
  text=parsed['transcription'].strip()
  if args.device=='cuda':torch.cuda.synchronize()
  row={key:sample[key] for key in ('id','group','language','duration','derived','reference')}
  row.update(text=text,detected_language=parsed['language'],seconds=round(time.monotonic()-started,3),
   generated_tokens=generated_ids.shape[1],truncated=generated_ids.shape[1]>=512,score=score(sample['reference'],text,sample['language']))
  output['rows'].append(row)
  path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
  print('qwen',sample['id'],'WER',round(row['score']['wer'] or 0,3),flush=True)
  del inputs,output_ids,generated_ids
 print('COMPLETE QWEN',len(output['rows']),flush=True)

if __name__=='__main__':main()
