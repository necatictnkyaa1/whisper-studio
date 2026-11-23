import urllib.request,concurrent.futures,hashlib,time
from pathlib import Path
root=Path('models/large-v3-quality');partial=root/'model.bin.partial';size=3087284237
start=partial.stat().st_size if partial.exists() else 0
jobs=[]
for left in range(start,size,96*1048576):jobs.append((left,min(size-1,left+96*1048576-1)))
print('RESUME_MB',start//1048576,'parts',len(jobs),flush=True)
def fetch(pair):
 left,right=pair;target=root/f'model.range-{left}-{right}'
 if target.exists() and target.stat().st_size==right-left+1:return target
 for attempt in range(3):
  try:
   resume=target.stat().st_size if target.exists() else 0
   offset=left+resume
   url=f'https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/model.bin?download=true&range={offset}'
   req=urllib.request.Request(url,headers={'Range':f'bytes={offset}-{right}'})
   with urllib.request.urlopen(req,timeout=60) as r,target.open('ab') as output:
    if r.status!=206 or not r.headers.get('Content-Range','').startswith(f'bytes {offset}-'):raise ValueError('Beklenmeyen aralık yanıtı')
    while True:
     b=r.read(1048576)
     if not b:break
     output.write(b)
   if target.stat().st_size!=right-left+1:raise ValueError('Eksik aralık')
   return target
  except Exception:
   if attempt==2:raise
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
 futures=[pool.submit(fetch,j) for j in jobs]
 for i,f in enumerate(concurrent.futures.as_completed(futures),1):
  f.result();print('PART',i,'/',len(jobs),flush=True)
with partial.open('ab') as out:
 for left,right in jobs:
  with (root/f'model.range-{left}-{right}').open('rb') as r:
   while True:
    b=r.read(1048576)
    if not b:break
    out.write(b)
digest=hashlib.file_digest(partial.open('rb'),'sha256').hexdigest()
if partial.stat().st_size!=size or digest!='69f74147e3334731bc3a76048724833325d2ec74642fb52620eda87352e3d4f1':raise ValueError('SHA256 uyuşmadı '+digest)
partial.replace(root/'model.bin');print('VERIFIED_LARGE_V3',flush=True)
