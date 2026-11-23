# Whisper Studio kalite ölçümü

Bu klasör uygulamanın kullanıcı ayarları değildir. Yerel motorları aynı kaynaklarla karşılaştırmak için geliştirme aracıdır. Ders oturumları/veritabanı değiştirilmez. İnternete ses veya metin gönderilmez; kaynak sesler ve modeller indirilir, çıkarım yerelde yapılır.

- `manifest.json`: 20 kaynak ses + 4 etiketli türev kontrol. Kaynak satırı, referans metin, süre, SHA256, dağıtım sürümü ve atıf bilgisi.
- `ATTRIBUTION.md`: ses kaynakları ve CC BY 4.0 atıfları.
- `translation-manifest.json`: FLORES-200 içinden 10 geliştirme cümlesi.
- `translation-holdout-manifest.json`: model/istem seçimi için kullanılmayan 10 ayrı doğrulama cümlesi.
- `FLORES-LICENSE.txt`: ayrı çeviri verisinin CC BY-SA 4.0 lisansı. Bu verinin lisansı uygulamanın tüm koduna verilmiş bir lisans değildir.
- `results/`: değiştirilmeyen ham model çıktıları, hata hizalamaları ve ölçümler.
- `RAPOR.md`: ölçümlerden üretilen karşılaştırma. WER ve chrF++ genel anlam doğruluğu değildir.

Komutlar uygulama klasörü `outputs/DersYazi` içinden çalıştırılır. Ana ortam mevcut `.venv`; Qwen3-ASR/chrF ortamı ayrı `../../work/asr-compare-env` klasöründedir. Sonuncusunda PyTorch 2.10.0+cu128, Transformers 5.20.1, sacrebleu 2.6.0 kullanıldı. PyTorch CUDA ve SM12.0 gerçek cihaz üzerinde doğrulandı. GPU işleri aynı anda çalıştırılmaz.

```powershell
.\.venv\Scripts\python.exe -m quality_bench.prepare
.\.venv\Scripts\python.exe -m quality_bench.run_whisper --mode production
.\.venv\Scripts\python.exe -m quality_bench.run_whisper --mode plain
.\.venv\Scripts\python.exe -m quality_bench.run_whisper --mode plain --compute-type float16
..\..\work\asr-compare-env\Scripts\python.exe -m quality_bench.run_qwen

.\.venv\Scripts\python.exe -m quality_bench.prepare_translation
.\.venv\Scripts\python.exe -m quality_bench.run_translation
.\.venv\Scripts\python.exe -m quality_bench.run_translation --holdout
.\.venv\Scripts\python.exe -m quality_bench.run_gemma --model qwen3.5:9b
.\.venv\Scripts\python.exe -m quality_bench.run_gemma --model translategemma:12b
..\..\work\asr-compare-env\Scripts\python.exe -m quality_bench.score_translation
.\.venv\Scripts\python.exe -m quality_bench.report
```

`prepare` mevcut manifesti yeniden seçmez; kayıt dosyalarını SHA256 ile doğrular. Yeni veri seçimi için yeni bir ölçüm sürümü gerekir. Model veya ayar geliştirmede kullanılan örnekler artık o değişiklik için bağımsız doğrulama sayılmaz. Referans metinler ASR/çeviri istemlerine verilmez.

İlk ölçümdeki `Qwen3.5-9B-current` etiketi, ölçüm sırasında kullanılan v6 JSON çeviri akışıdır. Ölçümden sonra eklenen v7 sıralama koruması bu eski sonuçlara geriye dönük uygulanmaz. Yanlış sıralama üretmiş satırın kaydı başarı gibi değiştirilmez.

Ek `audit_lecture_qwen` komutu kullanıcının yerel 29 Eylül kaydındaki sorunlu parçaları çözer. Bu **özel ders kaydı denemesidir**; açık veri setinin bir parçası değildir. İnsan referansı olmadığından WER hesaplanmaz ve sonuç genel kalite yüzdesi olarak kullanılmaz.

## 18 Ekim pencereleme deneyi

İki yeni aday ve tekrar komutları: PENCERE-DENEYI-KARAR.md. Her ikisi de ölçümde üstün gelmedi; uygulama varsayılanı fixed olarak kaldı. Eksik aday sonucu karşılaştırıcı tarafından reddedilir.
