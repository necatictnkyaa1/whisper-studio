from pathlib import Path
import urllib.request,time,hashlib,json
root=Path('models/large-v3-quality');root.mkdir(parents=True,exist_ok=True)
for name in ('config.json','preprocessor_config.json','tokenizer.json','vocabulary.json','model.bin'):
 target=root/name
 if target.exists():continue
 url='https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/'+name+'?download=true'
 if name=='model.bin':url+='&full=20261016'
 expected=3087284237 if name=='model.bin' else 0
 headers={'Range':f'bytes=0-{expected-1}'} if expected else {}
 print('DOWNLOAD',name,flush=True);n=0;last=time.monotonic();digest=hashlib.sha256()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as response,(root/(name+'.partial')).open('wb') as out:
   while True:
    chunk=response.read(1024*1024)
    if not chunk:break
    out.write(chunk);digest.update(chunk);n+=len(chunk)
    if time.monotonic()-last>10:print('MB',n//1048576,flush=True);last=time.monotonic()
 except urllib.error.HTTPError as e:
  if name=='vocabulary.json' and e.code==404:continue
  raise
 if expected and (n!=expected or digest.hexdigest()!='69f74147e3334731bc3a76048724833325d2ec74642fb52620eda87352e3d4f1'):raise ValueError('Model bütünlük kontrolü başarısız')
 (root/(name+'.partial')).replace(target)
 print('READY',name,n,flush=True)
