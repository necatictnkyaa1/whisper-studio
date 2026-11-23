"""İnsan referanslı bağımsız cümlelerde eski/yeni yerel çeviri karşılaştırması."""
import json,time,gc,argparse
from pathlib import Path
import core
from translation import LocalTranslator
from lecture_translation import LectureTranslator
from llm import OllamaClient
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--holdout',action='store_true');args=parser.parse_args()
manifest=json.loads((ROOT/('translation-holdout-manifest.json' if args.holdout else 'translation-manifest.json')).read_text(encoding='utf-8'))
results=ROOT/'results';results.mkdir(exist_ok=True);path=results/('translation-holdout.json' if args.holdout else 'translation.json');rows=[]
legacy=LocalTranslator('en','tr',True,print,lambda:False)
for row in manifest['rows']:
 started=time.monotonic();text=legacy.translate(row['source'])
 rows.append({**row,'engine':'Argos-en-tr-1.5','text':text,'seconds':round(time.monotonic()-started,3),'error':None})
 path.write_text(json.dumps({'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
 print('ARGOS',row['id'],flush=True)
del legacy;gc.collect()
client=OllamaClient(host='127.0.0.1:11438');translator=None
try:
 translator=LectureTranslator(True,print,lambda:False,client)
 for row in manifest['rows']:
  started=time.monotonic();text=None;error=None
  try:text=translator.batch([{'id':row['id'],'text':row['source']}],'tr','')[row['id']]
  except Exception as problem:error=str(problem)
  rows.append({**row,'engine':'Qwen3.5-9B-current','text':text,'seconds':round(time.monotonic()-started,3),'error':error})
  path.write_text(json.dumps({'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
  print('QWEN-MT',row['id'],error or 'OK',flush=True)
finally:
 if translator:translator.close()
 client.stop()
