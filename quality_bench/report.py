"""Ham ölçümlerden yeniden üretilebilir karşılaştırma tabloları."""
import json,csv,random
from pathlib import Path
from quality_bench.metrics import aggregate,spoken_number_score
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
files=('whisper-production.json','whisper-plain.json','whisper-plain-float16.json','qwen-asr.json')
summaries=[];details=[]
completed={}
for name in files:
 path=ROOT/'results'/name
 if not path.exists():continue
 data=json.loads(path.read_text(encoding='utf-8'))
 if len(data['rows'])!=len(manifest['samples']):continue
 label=name.removesuffix('.json')
 completed[label]=[row for row in data['rows'] if not row['derived']]
 groups=['original-20','fleurs-tr','media-tr','libri-clean','libri-other','stress-switch','stress-noise']
 for group in groups:
  rows=[r for r in data['rows'] if (not r['derived'] if group=='original-20' else r['group']==group)]
  summary=aggregate(rows)
  auxiliary=[{**r,'score':spoken_number_score(r['reference'],r['text'],r['language'])} for r in rows]
  summary.update(engine=label,group=group,number_format_wer=aggregate(auxiliary)['wer'])
  summaries.append(summary)
 for row in data['rows']:details.append({'engine':label,**{k:row[k] for k in ('id','group','reference','text','seconds')},
  'wer':row['score']['wer'],'substitutions':row['score']['substitutions'],'deletions':row['score']['deletions'],'insertions':row['score']['insertions']})
(ROOT/'results/asr-scores.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'results/clip-results.csv').open('w',encoding='utf-8-sig',newline='') as output:
 writer=csv.DictWriter(output,fieldnames=list(details[0]));writer.writeheader();writer.writerows(details)
lines=['# Whisper Studio — 20 kısa kayıtta kalite karşılaştırması','',
 '20 kaynak kayıt ve 4 ayrı yapay stres kontrolü. Kaynak ses: 200,825 saniye. Her model aynı yerel WAV dosyalarını kullanır; SHA256 ve kaynak satırları manifest.json içindedir. Referanslar ASR çıktılarından üretilmedi.','',
 '| Motor / ayar | Kaynak kayıt | Sözcük hatası / referans | WER ↓ | CER ↓ | TR sayı yazımı eşitlenmiş ek WER ↓ |',
 '|---|---:|---:|---:|---:|---:|']
for s in summaries:
 if s['group']=='original-20':lines.append(f"| {s['engine']} | {s['clips']} | {s['errors']} / {s['reference_words']} | {s['wer']:.2%} | {s['cer']:.2%} | {s['number_format_wer']:.2%} |")
lines+=['','WER, ekleme + silme + değiştirme sayısının referans sözcük sayısına oranıdır; 100-WER genel anlam doğruluğu değildir. Ana WER sayıları kelimelere dönüştürmez. Ek gösterge yalnızca Türkçedeki bağımsız 0–9999 tamsayılarını sözle açar; yanlış sayıyı doğru kabul etmez. Türkçe harfler korunur. CER boşluksuz karakterler üzerinden hesaplanır.','',
 '| Motor | Grup | Hata / sözcük | WER ↓ |','|---|---|---:|---:|']
for s in summaries:
 if s['group']!='original-20':lines.append(f"| {s['engine']} | {s['group']} | {s['errors']} / {s['reference_words']} | {s['wer']:.2%} |")
baseline=completed.get('whisper-production');uncertainty=[]
if baseline:
 for name,candidate in completed.items():
  if name=='whisper-production':continue
  assert [s['id'] for s in candidate]==[s['id'] for s in baseline]
  rng=random.Random(20261017);deltas=[]
  for _ in range(2000):
   indices=[rng.randrange(len(baseline)) for _ in baseline]
   total=sum(baseline[i]['score']['reference_words'] for i in indices)
   deltas.append(sum(candidate[i]['score']['errors']-baseline[i]['score']['errors'] for i in indices)/total)
  deltas.sort();point=(sum(s['score']['errors'] for s in candidate)-sum(s['score']['errors'] for s in baseline))/sum(s['score']['reference_words'] for s in baseline)
  uncertainty.append({'engine':name,'delta_wer':point,'resampled_95_low':deltas[49],'resampled_95_high':deltas[1949]})
 (ROOT/'results/asr-uncertainty.json').write_text(json.dumps(uncertainty,indent=2),encoding='utf-8')
 lines+=['','| Mevcut akışa göre | WER farkı (puan) | Parça yeniden örnekleme %95 aralığı |','|---|---:|---:|']
 for u in uncertainty:lines.append(f"| {u['engine']} | {u['delta_wer']*100:+.2f} | {u['resampled_95_low']*100:+.2f} … {u['resampled_95_high']*100:+.2f} |")
 lines+=['','Eksi fark daha az hata demektir. Aralık 20 parçanın eşli bootstrap yeniden örneklemesine dayanır; tüm ders kayıtları için garanti değildir. Sıfırı içeren aralıkla kesin üstünlük iddia edilmez.']
lines+=['','Dört stres dosyası bağımsız doğal kayıt değildir; 20 kaynak kaydın ana ortalamasına katılmaz. Dil geçişi iki gerçek kaydın birleştirilmesidir; doğal ders içi kod değiştirmesi iddiası yoktur. Gürültü/yankı kontrollü olarak eklenmiştir.','',
 'Küçük bir ön eleme setidir. İngilizce bölümü sesli kitap; Türkçe bölümü okuma ve medyadır. Teknik üniversite dersi, belirli hoca aksanı ve uzun kayıtlar için sonuç genellenemez. Eğitim verisi örtüşmesi dışlanamadı. Ayarlar bu set üzerinde değiştirilirse bu sonuçlar geliştirme sonucu olarak kalır; yeni bağımsız doğrulama gerekir.','',
 'Süreler model yüklemesini dışarıda bırakır; arka plandaki indirme ve diğer Windows uygulamaları nedeniyle standartlaştırılmış hız testi sayılmaz.','',
 'Kaynak ve lisanslar: ATTRIBUTION.md. ASR kayıtları CC BY 4.0. Ayrı çeviri referansları FLORES-200: FLORES-LICENSE.txt (CC BY-SA 4.0). TranslateGemma ağırlığı Gemma lisansındadır; Qwen3-ASR ve Qwen3.5 Apache 2.0 lisansındadır.','']
mtpath=ROOT/'results/translation-scores.json'
if mtpath.exists():
 lines+=['## Ayrı çeviri karşılaştırması','','chrF++ referans çeviriyle sözcüksel benzerlik puanıdır; anlam doğruluğu yüzdesi değildir. Hatalı veya kesilen yanıt boş çıktı olarak puana girer ve ayrıca sayılır.','',
 '| Motor | Ayrım | Cümle | Hatalı yanıt | chrF++ ↑ |','|---|---|---:|---:|---:|']
 for s in json.loads(mtpath.read_text(encoding='utf-8')):
  lines.append(f"| {s['engine']} | {s['split']} | {s['clips']} | {s['failures']} | {s['chrf_plus_plus']:.2f} |")
(ROOT/'RAPOR.md').write_text('\n'.join(lines),encoding='utf-8')
print('REPORT_READY',len(summaries),'GROUPS',len(details),'TRANSCRIPTS')
