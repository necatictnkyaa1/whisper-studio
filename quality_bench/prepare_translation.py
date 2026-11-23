"""Çeviriyi ASR'dan bağımsız ölçmek için yayımlanmış EN/TR referans çiftleri."""
import hashlib,json,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
url='https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz'
archive=ROOT/'flores200_dataset.tar.gz'
if not archive.exists():
 with urllib.request.urlopen(url,timeout=60) as response,archive.with_suffix('.partial').open('wb') as output:
  while chunk:=response.read(1048576):output.write(chunk)
 archive.with_suffix('.partial').replace(archive)
with tarfile.open(archive) as tar:
 names=tar.getnames();found={}
 for language in ('eng_Latn','tur_Latn'):
  selected=[name for name in names if '/devtest/' in name and language in name]
  assert len(selected)==1,selected
  found[language]=tar.extractfile(selected[0]).read().decode('utf-8').splitlines()
 licenses=[name for name in names if 'license' in name.casefold()]
 license_text='\n\n'.join(tar.extractfile(name).read().decode('utf-8') for name in licenses if tar.getmember(name).isfile())
 if not license_text:
  license_text=urllib.request.urlopen('https://raw.githubusercontent.com/facebookresearch/flores/main/LICENSE_CC-BY-SA',timeout=30).read().decode('utf-8')
 (ROOT/'FLORES-LICENSE.txt').write_text(license_text,encoding='utf-8')
assert len(found['eng_Latn'])==len(found['tur_Latn'])
rows=[{'id':f'flores-{i+1:04d}','line':i+1,'source':found['eng_Latn'][i],'reference':found['tur_Latn'][i]} for i in range(0,1000,100)]
data={'source':url,'upstream':'https://github.com/facebookresearch/flores/tree/main/flores200',
 'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
 'selection':'devtest satırları 1,101,...,901; model yanıtları görülmeden seçildi.',
 'license_file':'FLORES-LICENSE.txt','rows':rows}
(ROOT/'translation-manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
holdout={**data,'selection':'Ayrı doğrulama: devtest 51,151,...,951; bu satırlar motor/talimat seçimi için kullanılmaz.',
 'rows':[{'id':f'flores-holdout-{i+1:04d}','line':i+1,'source':found['eng_Latn'][i],'reference':found['tur_Latn'][i]} for i in range(50,1000,100)]}
(ROOT/'translation-holdout-manifest.json').write_text(json.dumps(holdout,ensure_ascii=False,indent=2),encoding='utf-8')
print('TRANSLATION_REFERENCES',len(rows),'LICENSES',licenses,flush=True)
