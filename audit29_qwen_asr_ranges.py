"""Kesilen resmî ağırlık indirmesini doğrulanan HTTP aralıklarıyla tamamlar."""
import concurrent.futures as cf,urllib.request,time,hashlib,os
from pathlib import Path
root=Path('models/qwen3-asr-1.7b-compare');revision='bcd2b5b7f32b480ab5790554cfa8347f246a14f3'
def download(name,size,sha):
 target=root/name
 if target.exists() and target.stat().st_size==size and hashlib.file_digest(target.open('rb'),'sha256').hexdigest()==sha:return
 folder=root/('.'+name+'-parts');folder.mkdir(exist_ok=True)
 ranges=[(s,min(size,s+32*1048576)) for s in range(0,size,32*1048576)]
 def one(pair):
  start,end=pair;p=folder/str(start)
  for attempt in range(5):
   offset=p.stat().st_size if p.exists() else 0
   if offset==end-start:return
   host=('https://huggingface.co','https://hf-mirror.com')[attempt%2]
   url=f'{host}/Qwen/Qwen3-ASR-1.7B-hf/resolve/{revision}/{name}?range={start+offset}-{end-1}&v=20261017'
   try:
    request=urllib.request.Request(url,headers={'Range':f'bytes={start+offset}-{end-1}'})
    with urllib.request.urlopen(request,timeout=30) as response:
     assert response.status==206 and response.headers.get('Content-Range')==f'bytes {start+offset}-{end-1}/{size}'
     with p.open('ab') as output:
      while chunk:=response.read(262144):output.write(chunk)
    assert p.stat().st_size==end-start
    return
   except Exception as error:
    if attempt==4:raise RuntimeError(f'{name} aralık {start}: {error}') from error
  raise RuntimeError('Aralık indirilemedi')
 with cf.ThreadPoolExecutor(max_workers=12) as pool:
  pending={pool.submit(one,pair) for pair in ranges}
  while pending:
   done,pending=cf.wait(pending,timeout=10,return_when=cf.FIRST_COMPLETED)
   for item in done:item.result()
   downloaded=sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
   print(name,round(downloaded/1048576), '/',round(size/1048576),'MB',flush=True)
 temporary=root/(name+'.assembling');digest=hashlib.sha256()
 with temporary.open('wb') as output:
  for start,_ in ranges:
   with (folder/str(start)).open('rb') as part:
    while chunk:=part.read(1048576):digest.update(chunk);output.write(chunk)
 assert temporary.stat().st_size==size and digest.hexdigest()==sha
 os.replace(temporary,target)
 print('VERIFIED',name,sha,flush=True)
download('tokenizer.json',11429653,'fe1fad59be22a41ee293363fcf95fdedbc7c93f3b49270b1d2e18bd1399a7a05')
download('model.safetensors',4076193080,'2db53c7d81bd9b8cbc6a074e89be2c968a0d373fb4ee68bb1b1e14f7042dfee1')
