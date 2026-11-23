"""20 açık veri kaydını referanslarıyla indirir. ASR sonucuna göre seçim yapmaz."""
import concurrent.futures as cf
import hashlib,json,time,urllib.request,urllib.parse,urllib.error,wave,re
from pathlib import Path
import numpy as np
from faster_whisper.audio import decode_audio

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data';DATA.mkdir(exist_ok=True)
SOURCES=[
 ('fleurs-tr','freyavoice/fleurs-tr-test','default','test','tr','raw_transcription',[0,200,400,600,800],
  'https://huggingface.co/datasets/google/fleurs','Google FLEURS contributors; Conneau et al., 2022'),
 ('media-tr','ymoslem/MediaSpeech','tr','train','tr','sentence',[0,200,400,600,800],
  'https://www.openslr.org/108/','NTRLab MediaSpeech; Kolobov et al., 2021; original media owners'),
 ('libri-clean','openslr/librispeech_asr','clean','test','en','text',[100,600,1100,1600,2100],
  'https://www.openslr.org/12/','LibriSpeech; Panayotov et al., 2015; LibriVox contributors'),
 ('libri-other','openslr/librispeech_asr','other','test','en','text',[100,600,1100,1600,2100],
  'https://www.openslr.org/12/','LibriSpeech; Panayotov et al., 2015; LibriVox contributors')]

def fetch(url):
 for attempt in range(4):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WhisperStudio-local-benchmark/1.0'}),timeout=40) as response:return response.read()
  except Exception as error:
   if attempt==3:raise
   pause=attempt+1
   if isinstance(error,urllib.error.HTTPError) and error.code in (429,503):
    pause=min(60,max(10*(attempt+1),int(error.headers.get('Retry-After','0'))))
   time.sleep(pause)

def write_audio(path,audio):
 with wave.open(str(path),'wb') as output:
  output.setnchannels(1);output.setsampwidth(2);output.setframerate(16000)
  output.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())

def acquire(job):
 source,index,ordinal=job
 group,dataset,config,split,lang,field,_,upstream,credit=source
 identity=f'{group}-{ordinal:02d}';path=DATA/(identity+'.wav');receipt=DATA/(identity+'.json')
 if receipt.exists() and path.exists():
  cached=json.loads(receipt.read_text(encoding='utf-8'))
  if hashlib.sha256(path.read_bytes()).hexdigest()==cached['sha256']:return cached
 # Sabit başlangıç satırları; yalnızca süre ve boş referans uygun değilse sonraki satıra geç.
 for row_index in range(index,index+10):
  query=urllib.parse.urlencode({'dataset':dataset,'config':config,'split':split,'offset':row_index,'length':1})
  response=json.loads(fetch('https://datasets-server.huggingface.co/rows?'+query))
  if not response['rows']:
   row_index=row_index%response['num_rows_total']
   query=urllib.parse.urlencode({'dataset':dataset,'config':config,'split':split,'offset':row_index,'length':1})
   response=json.loads(fetch('https://datasets-server.huggingface.co/rows?'+query))
  row_data=response['rows'][0]
  row=row_data['row'];reference=row.get(field) or row.get('transcription')
  if not reference or len(reference.split())<5:continue
  temporary=DATA/(identity+'.source')
  temporary.write_bytes(fetch(row['audio'][0]['src']))
  audio=decode_audio(str(temporary),sampling_rate=16000)
  duration=len(audio)/16000
  if not 3<=duration<=30:continue
  write_audio(path,audio)
  result={'id':identity,'language':lang,'group':group,'file':path.relative_to(ROOT).as_posix(),
   'reference':reference.strip(),'duration':round(duration,4),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
   'dataset':dataset,'config':config,'split':split,'row_index':row_index,
   'dataset_sample_id':str(row.get('id',row_index)),'speaker_id':row.get('speaker_id'),
   'gender':row.get('gender'),'upstream':upstream,'attribution':credit,
   'license':'CC-BY-4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
   'retrieval_api':'https://datasets-server.huggingface.co/rows?'+query,'derived':False,
   'distribution_revision':re.search(r'/--/([0-9a-f]{40})/--/',row['audio'][0]['src']).group(1)}
  receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  return result
 raise RuntimeError(f'Uygun süreli kaynak bulunamadı: {group}:{index}')

def main():
 manifest=ROOT/'manifest.json'
 if manifest.exists():
  frozen=json.loads(manifest.read_text(encoding='utf-8'))
  assert len([s for s in frozen['samples'] if not s['derived']])==20
  for sample in frozen['samples']:
   assert hashlib.sha256((ROOT/sample['file']).read_bytes()).hexdigest()==sample['sha256']
  print('FROZEN_MANIFEST_VERIFIED',len(frozen['samples']),flush=True);return
 jobs=[(source,index,ordinal) for source in SOURCES for ordinal,index in enumerate(source[6],1)]
 with cf.ThreadPoolExecutor(max_workers=5) as pool:
  samples=[]
  for sample in pool.map(acquire,jobs):
   samples.append(sample);print('DOWNLOADED',sample['id'],sample['duration'],flush=True)
 assert len(samples)==20
 assert len({(s['dataset'],s['config'],s['dataset_sample_id']) for s in samples})==20
 # Ek kontroller: doğal kod değiştirme değil, açıkça etiketlenmiş yapay dil birleşimi ve akustik bozulma.
 derived=[]
 for index in range(2):
  first=samples[index];second=samples[10+index]
  audio=np.concatenate([decode_audio(str(ROOT/first['file'])),np.zeros(6400,np.float32),decode_audio(str(ROOT/second['file']))])
  identity=f'stress-switch-{index+1:02d}';path=DATA/(identity+'.wav');write_audio(path,audio)
  derived.append({'id':identity,'language':'mixed','group':'stress-switch','file':path.relative_to(ROOT).as_posix(),
   'reference':first['reference']+' '+second['reference'],'duration':len(audio)/16000,
   'parents':[first['id'],second['id']],'transformation':'TR kayıt + 0,4 saniye sessizlik + EN kayıt; doğal kod değiştirme değildir.',
   'derived':True,'license':'CC-BY-4.0','attribution':first['attribution']+'; '+second['attribution'],
   'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 for index,first in enumerate((samples[2],samples[12]),1):
  audio=decode_audio(str(ROOT/first['file']));rng=np.random.default_rng(20261017+index)
  noise=rng.normal(size=len(audio)).astype(np.float32)
  noise*=float(np.sqrt(np.mean(audio**2)/(10**1.5)))/max(float(np.std(noise)),1e-9)
  altered=audio+noise
  altered[560:]+=audio[:-560]*.25;altered[1280:]+=audio[:-1280]*.12
  peak=max(float(np.max(np.abs(altered))),1.0);altered/=peak
  identity=f'stress-noise-{index:02d}';path=DATA/(identity+'.wav');write_audio(path,altered)
  derived.append({'id':identity,'language':first['language'],'group':'stress-noise','file':path.relative_to(ROOT).as_posix(),
   'reference':first['reference'],'duration':len(altered)/16000,'parents':[first['id']],
   'transformation':'Deterministik 15 dB SNR beyaz gürültü + 35/80 ms yankı; yapay stres kontrolü.',
   'derived':True,'license':'CC-BY-4.0','attribution':first['attribution'],
   'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 frozen={'version':1,'selection':'Sabit satır aralıkları (veri boyutunu aşarsa mod N); ASR çıktıları görülmeden donduruldu. Süre 3–30 saniye; en az 5 referans sözcüğü.',
  'limits':'20 küçük örnek; ders/teknik konuşma ve doğal TR/EN kod değiştirmesi için temsil gücü sınırlı. Eğitim verisi örtüşmesi dışlanamadı.',
  'samples':samples+derived}
 manifest.write_text(json.dumps(frozen,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'ATTRIBUTION.md').write_text('# Kaynaklar ve atıflar\n\n'+'\n\n'.join(
  f"- {s[0]}: {s[8]}. Kaynak: {s[7]}. Alınan dağıtım: https://huggingface.co/datasets/{s[1]}. CC BY 4.0. WAV/mono/16 kHz dönüştürmesi yapıldı."
  for s in SOURCES)+'\n\nİlk 20 dosya kaynak kayıtlardır. Son dört dosya manifestte açıklanan türevlerdir; sonuçları ana örneklerle birleştirilmez.\n',encoding='utf-8')
 print('FROZEN',len(samples),'ORIGINAL +',len(derived),'STRESS',flush=True)

if __name__=='__main__':main()
