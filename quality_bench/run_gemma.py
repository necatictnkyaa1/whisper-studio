"""Ollama resmî TranslateGemma istem biçimi; referanslar modele verilmez."""
import json,time,argparse
from pathlib import Path
from llm import OllamaClient
parser=argparse.ArgumentParser();parser.add_argument('--model',choices=('translategemma:12b','qwen3.5:9b'),default='translategemma:12b');args=parser.parse_args()
ROOT=Path(__file__).resolve().parent;client=OllamaClient(host='127.0.0.1:11438');results=[]
engine='TranslateGemma-12B' if args.model.startswith('translategemma') else 'Qwen3.5-9B-plain-prompt'
output='translation-gemma.json' if args.model.startswith('translategemma') else 'translation-qwen-plain.json'
try:
 client.ensure_running(print,lambda:False)
 assert args.model in client.installed(),'Adayın indirilmesi henüz tamamlanmadı.'
 for split,filename in [('development','translation-manifest.json'),('holdout','translation-holdout-manifest.json')]:
  manifest=json.loads((ROOT/filename).read_text(encoding='utf-8'))
  for row in manifest['rows']:
   prompt=('You are a professional English (en) to Turkish (tr) translator. Your goal is to accurately convey the meaning and nuances of the original English text while adhering to Turkish grammar, vocabulary, and cultural sensitivities.\n'
    'Produce only the Turkish translation, without any additional explanations or commentary. Please translate the following English text into Turkish:\n\n\n'+row['source'])
   started=time.monotonic();text=None;error=None
   try:
    answer=client._get_json('/api/chat',{'model':args.model,'messages':[{'role':'user','content':prompt}],
     'stream':False,'think':False,'keep_alive':'5m','options':{'num_ctx':2048,'num_predict':512,'temperature':0,'presence_penalty':0,'repeat_penalty':1.0}},timeout=180)
    if answer.get('done_reason')=='length':raise RuntimeError('Yanıt token sınırında kesildi.')
    text=answer['message']['content'].strip()
   except Exception as problem:error=str(problem)
   results.append({**row,'engine':engine,'split':split,'text':text,'error':error,'seconds':round(time.monotonic()-started,3)})
   (ROOT/'results'/output).write_text(json.dumps({'rows':results},ensure_ascii=False,indent=2),encoding='utf-8')
   print(engine,row['id'],error or 'OK',flush=True)
finally:
 client.unload(args.model);client.stop()
