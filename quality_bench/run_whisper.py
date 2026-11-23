"""Üretim ASR akışı ve sade Large-v3 kontrolünü aynı dondurulmuş örneklerde ölç."""
import argparse,json,time,hashlib
from pathlib import Path
from dataclasses import asdict
import core
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from recognition import constrain_lecture_languages,speech_windows
from language_checks import text_language_hint
from quality_bench.metrics import score
ROOT=Path(__file__).resolve().parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('production','plain','pause','pause-short'),default='production')
 parser.add_argument('--compute-type',choices=('int8_float16','float16'),default='int8_float16');args=parser.parse_args()
 manifest_path=ROOT/'manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
 modelpath=Path(core.__file__).resolve().parent/'models/large-v3-quality'
 started=time.monotonic();model=WhisperModel(str(modelpath),device='cuda',compute_type=args.compute_type,local_files_only=True)
 if args.mode!='plain':constrain_lecture_languages(model)
 output={'model':'Whisper Large-v3','mode':args.mode,'device':'cuda','compute_type':args.compute_type,
  'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'load_seconds':round(time.monotonic()-started,3),'rows':[]}
 results=ROOT/'results';results.mkdir(exist_ok=True);path=results/f'whisper-{args.mode}{"-float16" if args.compute_type=="float16" else ""}.json'
 for sample in manifest['samples']:
  audio=decode_audio(str(ROOT/sample['file']));started=time.monotonic();segments=[]
  if args.mode=='plain':
   rows,info=model.transcribe(audio,language=None,beam_size=5,vad_filter=True,condition_on_previous_text=False,temperature=0,word_timestamps=True)
   for row in rows:segments.append({'start':row.start,'end':row.end,'text':row.text.strip()})
  else:
   # Aynı speech_windows/refine_segment kodu kullanılır. Model yükleme her dosyada tekrarlanmaz.
   language_cache={}
   for row in speech_windows(model,audio,lambda:False,None,strategy=args.mode if args.mode.startswith('pause') else 'fixed'):
    window=int(row.start//20)
    if window not in language_cache:
     sample_audio=audio[window*20*16000:min(len(audio),(window+1)*20*16000)]
     language_cache[window]=model.detect_language(audio=sample_audio,vad_filter=True)[:2]
    language,confidence=language_cache[window]
    if confidence<.5:
     left=max(0,int((row.start-5)*16000));right=min(len(audio),int((row.end+5)*16000))
     retry,confidence2,_=model.detect_language(audio=audio[left:right],vad_filter=False)
     if confidence2>confidence:language,confidence=retry,confidence2
    hint=text_language_hint(row.text)
    if hint and hint!=language:language=hint
    text,review=core.refine_segment(model,audio,row,language,lambda _:None,lambda:False)
    segments.append({'start':row.start,'end':row.end,'text':text,'review':review})
  text=' '.join(row['text'] for row in segments)
  result={key:sample[key] for key in ('id','group','language','duration','derived','reference')}
  result.update(text=text,seconds=round(time.monotonic()-started,3),segments=segments,score=score(sample['reference'],text,sample['language']))
  output['rows'].append(result)
  path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
  print(args.mode,sample['id'],'WER',round(result['score']['wer'] or 0,3),flush=True)
 print('COMPLETE',args.mode,len(output['rows']),flush=True)

if __name__=='__main__':main()
