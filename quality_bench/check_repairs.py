"""v8 korumalarının gerçek yerel üretimde kontrolü; kıyas puanlarını değiştirmez."""
import json,time,argparse
from pathlib import Path
from lecture_translation import LectureTranslator
from llm import OllamaClient
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--tag',default='v8');args=parser.parse_args()
development=json.loads((ROOT/'translation-manifest.json').read_text(encoding='utf-8'))['rows']
cases=[('past-now',development[0]['source']),('written-rank',development[2]['source']),
 ('independent-past-now','This server used to be offline, but it is online now.'),
 ('mixed','Bu hafta buradaydım. What was the last topic?')]
client=OllamaClient(host='127.0.0.1:11438');translator=None;results=[]
try:
 translator=LectureTranslator(True,print,lambda:False,client)
 for identity,text in cases:
  started=time.monotonic();answer=None;error=None
  try:answer=translator.batch([{'id':identity,'text':text}],'tr','')[identity]
  except Exception as failure:error=str(failure)
  results.append({'id':identity,'source':text,'text':answer,'error':error,'seconds':round(time.monotonic()-started,3)})
  (ROOT/'results'/f'repair-{args.tag}-smoke.json').write_text(json.dumps({'purpose':'Geliştirme örneklerinde regresyon; bağımsız doğruluk yüzdesi değil.','rows':results},ensure_ascii=False,indent=2),encoding='utf-8')
  print(args.tag,identity,answer or error,flush=True)
finally:
 if translator:translator.close()
 client.stop()
if any(r['error'] for r in results):raise SystemExit(1)
