import urllib.request,concurrent.futures,hashlib,time
from pathlib import Path
root=Path('models/large-v3-quality');prefix=root/'model.bin.partial';size=3087284237
start=prefix.stat().st_size;jobs=[];tails=[]
for left in range(start,size,96*1048576):
 right=min(size-1,left+96*1048576-1);parent=root/f'model.range-{left}-{right}'
 existing=parent.stat().st_size if parent.exists() else 0
 subtasks=[]
 for a in range(left+existing,right+1,1048576):
  b=min(right,a+1048576-1);subtasks.append((a,b));tails.append((a,b))
 jobs.append((parent,subtasks))
print('TAIL_PARTS',len(tails),flush=True)
def fetch(pair):
 a,b=pair;target=root/f'model.tail-{a}-{b}'
 if target.exists() and target.stat().st_size==b-a+1:return
 for attempt in range(3):
  try:
   url=f'https://hf-mirror.com/Systran/faster-whisper-large-v3/resolve/main/model.bin?download=true&tail={a}'
   with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}'}),timeout=30) as r:
    if r.status!=206 or not r.headers.get('Content-Range','').startswith(f'bytes {a}-'):raise ValueError('Aralık uyuşmadı')
    content=r.read()
   if len(content)!=b-a+1:raise ValueError('Parça boyutu uyuşmadı')
   target.write_bytes(content);return
  except Exception:
   if attempt==2:raise
   time.sleep(3)
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
 futures=[pool.submit(fetch,pair) for pair in tails]
 for i,f in enumerate(concurrent.futures.as_completed(futures),1):
  f.result()
  if i%20==0:print('TAIL_DONE',i,'/',len(tails),flush=True)
for parent,subtasks in jobs:
 if subtasks:
  with parent.open('ab') as out:
   for a,b in subtasks:out.write((root/f'model.tail-{a}-{b}').read_bytes())
with prefix.open('ab') as out:
 for parent,_ in jobs:
  with parent.open('rb') as stream:
   while True:
    content=stream.read(1048576)
    if not content:break
    out.write(content)
with prefix.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
if prefix.stat().st_size!=size or digest!='69f74147e3334731bc3a76048724833325d2ec74642fb52620eda87352e3d4f1':raise ValueError('SHA256 uyuşmadı '+digest)
prefix.replace(root/'model.bin');print('VERIFIED_LARGE_V3',flush=True)
