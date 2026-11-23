## 31 Ekim 2026: C++ kuyruğu 17/17 tamamlandı
Klasör: `C:/Users/Necati/Desktop/Rumeysa’m/cpp ses kayıtları/Whisper Studio 2026-10-31 16-28-03 a2d9f4` (gerçek klasörde düz ASCII apostrof var).
Son kayıtta token repeat limit hatası: 154/290 TR, 0 EN noktasından devam edildi. JSON ve sade istemin ikisi de döngüye girdiğinden noktalama sınırlarında kısa parçalara bölme ve her parça/son birleşim için aynı validate kontrolü eklendi. Sınırlı onarım; başarısızlığı gizlemez. 259 test geçti.
Gerçek kuyruk 17/17, 34 TXT, eski 32 TXT hashleri aynı. Kaynak 290 bölüm yedekle aynı, TR/EN 290 bölüm tamam. ASR tekrar yapılmadı. Bu işlem anlamsal doğruluk garantisi değildir; örnek kaynakta “hominid” gibi tanıma kusurları mevcut. Yedek/sonuç: `work/recovery-cpp-2026-10-31`.

## 30 Ekim 2026: 23 kayıtlık fizik kuyruğu tamamlandı
Klasör: `C:/Users/Necati/Desktop/Rumi Fizik/ses kayıtlar 30.10/Whisper Studio 2026-10-30 18-25-02 941d78`.
23/23 tamamlandı, 46 TXT. Önceden tamamlanan 42 TXT hash karşılaştırmasıyla değişmedi. İki eksik kaydın kaynak transkriptleri yedekle aynı; TR/EN bölüm sayıları kaynakla eşit. ASR yeniden çalıştırılmadı.
Boş JSON çevirisi (kaynak “blank”) için uzunluk hatası sonrası aynı doğrulamayı kullanan sade istek eklendi. Yanıt kesilmesi için sayısal parça onarımına geçiş eklendi. 256 test geçti. Yedek ve sonuç: `work/recovery-2026-10-30`. Bu kontroller anlamsal kusursuzluk iddiası değildir.

# EN GÜNCEL — 22 Ekim / fizik13kuyrukTAMAMLANDI

HEDEF-DIL-ONARIMI-2026-10-22.md ayrıntı. Hedef dil hatasında sade onarım fallback eklendi; kontroller korunur. Full254testOK. Kullanıcının 13lüfizikkuyruğundakalan6.kayıttranslation_onlyileburadangerçektamamlandı. 13/13başarılı,26TXT. Eski24TXTshaaynı,kaynakASRdeğişmedi,kalan119TR119ENtamam. work/physics-final-recovery-result.json kanıt. Kullanıcıyenidenbaşlatmakişleminiyapmakzorundadeğil;dosyalarhazır.EskiUIkuyrukyenidenaçılıncagüncelgörünür.

---
# EN GÜNCEL — 20 Ekim / fiziksel windows bağlamı

Rumi Mat4/5tamam,teorik telafiilkdosyaTR424/537,EN0. 424–427blokta426satır physical wall/windows yanlışlıklaWindowsişletimsistemiolarakkorunuyordu. protected_identifiers darşekildegüncellendi: küçükharf windows +100karakteryakınındawall/door/room/house/building, ve computingcueyoksaözeladkabul edilmez. GerçekWindows/OSyazılımbağlamıkorunur. 3yenitest,full252/16.443snOK. Gerçek426satırrepair_row geçti,work/math-windows-context-test.json. KullanıcıTXT/kuyruk/checkpointdeğişmedi; dosyanıngeri kalanıişlenmedi. Eskiuygulamayenidenaçılıpaynıkuyrukladevamgerekiyor. Başkaanlamhatalarınınçözüldüğüiddiasıyok.

---
# EN GÜNCEL — 20 Ekim / Rumi Mat sayısal fallback

Matematik kuyruğu3hata2tamam. MATEMATIK-KUYRUK-DUZELTMESI.md ayrıntı. repair_row artık son numeric/signed/schema hatasında repair_numeric_fragments kullanır; numerikler modelkontrolündendeğil uygulamadan eklenir. Yalnız aradaki metinler batch ile çevrilir; bütünsatır validate edilir. plus/artı da mask_numbers NUMBER_SPAN içinde. Koddaöncekionarımlar korundu. 3ilkblok ve2ekgerçeksatırmodeltestigeçti; kullanıcıJSON/TXTlerine yazılmadı. Tamkuyrukçalıştırılmadı. Eski uygulamayenidenaçılıpaynıkuyruk.jsoniledevamgerekiyor. AkıcılıkveASRhataları çözülmüşsayılmaz.

---
# EN GÜNCEL — 20 Ekim 2026 / fizik negatif üs

Kullanıcı Rumi Fizik kuyruğunda 13 hata,14/15 tamamlandı ekranı gönderdi. FIZIK-EKSI-DUZELTMESI.md ayrıntılı. lecture_translation.py bir önceki başka çalışmada sayısal slot/repair_row ile genişletilmişti; o kod korundu. Yeni düzeltmeler: numeric slotlarda boşluk, Unicode numeric kaçak kontrolü, okunabilir <NUM_A> ve özgün alıntı bağlamı, dar written negative exponent guard. Gerçek sorunlu119satırı v3te doğalTürkçe/eksi altı/eksi9 ile geçti. Önceki iki adaykötüydü; kullanıcıverisine yazılmadı. Full245/16.919snOK. GerçekkuyrukveTXTler değiştirilmedi, ilkdosyanıntamamı yenidenişlenmedi. Eski uygulama yenidenaçılıpaynıkuyruk.jsoniledevamedilmeli.

---
# EN GÜNCEL — 19 Ekim 2026 / toplu iki dilli TXT

Kullanıcı 43 kaydı birlikte seçip her biri için Türkçe ve İngilizce TXT istiyor. batch_transcription.py ve batch_ui.py eklendi. app.py çoklu dosya seçme/sürükle bırakmayı ayrı modal kuyruğa yönlendirir; studio.py üst kartta Toplu TXT düğmesi var. Tek ders geçmişi korunur. ASR kayıt başına bir kez, sonra iki dil; dosya adı-tr.txt/en.txt. Yeni tarihli ayrı çıktı klasörü, kuyruk.json ve kayıt.durum.json kontrol noktaları. Hata dosya bazında devam, iptal güvenli, resume tamamlananları atlar ve ASR tekrarını önler. Aynı ad farklı kaynak çakışması sayılı ekle çözülür. Bitmiş TXT üzerine yazılmaz. Windows boşta uykusu QThread boyunca geçici engellenir.

Gerçek testte İngilizce hedef Türkçe SYSTEM nedeniyle başarısızdı; SYSTEM_EN eklendi, quality_pipeline EN cache anahtarına bu yönerge dahil edildi. TR yönergesi aynı. Aynı kuyruk resume ile başarılı oldu. Türkçe FLEURS gerçek test de iki TXT çıkardı. work/batch-real-smoke. Çeviri kalite sorunları sürüyor; bu toplu işlev kalite artışı iddiası değil.

Testler: 43 sahte kayıt/86 TXT, resume/cancel, hata sonrasıdevam, kaynak değişikliği, boş ses, aynıad ve UI. Son full suite239 /15.147sn/OK. 43 gerçek ders denenmedi. Kullanıcının dosyaları henüz seçilmedi ve işlenmedi; gerçek oturumlarına dokunulmadı. Güncel kullanım TOPLU-TRANSKRIPT.md. Masaüstü kısayolu aynı app.py açar.

---
Önceki notlar:

# EN GÜNCEL — 18 Ekim 2026 / transkript odaklı sürüm

Çalışma kağıdı özelliği app.py/ui.py/studio.py içinden kaldırıldı. Eski oturumlardaki föy verisi pasif uyumluluk verisi olarak korunur. Kaynak ekleme yok, transkript/çeviri/TXT-SRT/geçmiş/notlar var. Eski belge ve modüller tarihî olabilir.

Son geliştirme: recognition.pause_boundaries + pause ve pause-short deneyleri. Aynı 20+4 örnekte iki aday 48 kez çözüldü. Ana WER temel9.91, iki aday10.14. Dil geçişi hata sayısı temel4/70, uzun26/70, kısa5/70. Üretime alınmadılar; default fixed, cache aynı. Ayrıntı quality_bench/PENCERE-DENEYI-KARAR.md. Bunlar geliştirme ölçümü; bağımsız ders doğrulaması değil.

Üretim düzeltmesi: boş/yalnız boşluk transkript artık tamamlandı animasyonu göstermiyor. Son full suite 230 test / 24.788sn / OK; test-sessions kullanıldı. GPU deneyleri bitti. Kullanıcının açık uygulaması kapatılmadı, gerçek oturumları üzerine yazılmadı. Sonraki iş: gerçek ders referanslarıyla terim bağlamı ve ikinci ASR karşılaştırması; aynı sete göre sınırsız ayar optimizasyonu yapma.

---
Önceki notlar:

# Aktif kalite ölçümü — 17 Ekim 2026

Kullanıcı internetten 15–20 referanslı kısa parça seçip planı gerçekten uygulamamızı istedi. 20 kaynak ses + 4 ayrı yapay stres dosyası quality_bench/manifest.json içinde donduruldu. Gruplar: 5 FLEURS TR (freyavoice dağıtımı), 5 MediaSpeech TR (ymoslem dağıtımı), 5 LibriSpeech test-clean, 5 test-other. Kaynaklar CC BY 4.0, atıflar quality_bench/ATTRIBUTION.md. Toplam özgün ses 200,825 sn, 424 sözcük. Referanslar modelden üretilmedi. Eğitim örtüşmesi dışlanamadı; üniversite/teknik/doğal kod değiştirmesi için temsil sınırlı.

Tamamlanan ASR: Whisper üretim int8_float16 42/424 hata (%9,91); sade aynı model int8 44/424; sade float16 42/424; Qwen3-ASR-1.7B native Transformers bf16 CUDA 39/424 (%9,20). TR bağımsız tamsayı yazımı eşitlenmiş ek WER üretim/Qwen aynı %7,75. Qwen İngilizcede daha iyi, TR medyada daha kötü. 20 parçalık bootstrap fark aralığı sıfırı içeriyor; kesin üstünlük yok. RAPOR.md sonuçlardan yeniden üretiliyor. Ana WER/CER + ek sayı-format WER birbirine karıştırılmamalı.

Qwen3-ASR 4.076.193.080 bayt ağırlığı TAMAM ve SHA256 doğrulandı: 2db53c7d81bd9b8cbc6a074e89be2c968a0d373fb4ee68bb1b1e14f7042dfee1. work/asr-compare-env artık PyTorch 2.10.0+cu128, Transformers 5.20.1, sacrebleu 2.6.0. GPU doğrulandı: CUDA True, SM12.0. Source modelo models/qwen3-asr-1.7b-compare. Üretim app motoruna henüz bağlanmadı.

TranslateGemma:12b Ollama üzerinden TAM indirildi (yaklaşık 8,1GB); Gemma lisansı, Apache/MIT değil. Resmî istem biçimi tek user rolü + professional English to Turkish translator + iki boş satır. source: ollama.com/library/translategemma ve huggingface.co/google/translategemma-12b-it. Varsayılan ürüne henüz alınmadı.

Çeviri için resmî Meta FLORES-200 tarından 10 geliştirme (1,101,...901) + 10 ayrı doğrulama (51,151,...951) EN/TR insan referansı seçildi. quality_bench/translation*-manifest.json. FLORES-LICENSE.txt CC BY-SA 4.0. İlk 10 dev sonucunda Argos chrF++51,50; mevcut Qwen JSON55,53, ama Qwen yanlışlıkla ninth->dördüncü ve used-to-be/now zamanını karıştırdı. Bu mevcut sayısal kontrollerin yetersizliğini gösteriyor; chrF++ anlam doğruluğu yüzdesi değil.

AKTİF tool exec session 29895 sırası: (1) plain float16 ASR bitti (2) run_translation --holdout şu anda çalışıyor (3) run_gemma --model qwen3.5:9b: aynı standart düz çeviri istemi, 20 dev+holdout (4) run_gemma --model translategemma:12b: aynı 20 cümle. GPU işleri aynı anda çalıştırılmamalı. 11438 bu koşuların özel Ollama sunucusu, kendileri açıp kapatır. Model indirme session30156 bitti. Diğer benchmark/model indirmeleri bitti. 29895 henüz bitmeden aynı portta başka GPU işi başlatma.

Mevcut üretim kodu v6 hâlâ aynı; baseline karşılaştırmaları tutarlı kalsın diye henüz sıra/ordinal koruması veya çeviri motoru değiştirilmedi. Yeni kodlar quality_bench/* ve test_bench_metrics.py (5 test geçti). Tam suite en son önceki aşamada213; yeni5 ile218 olması beklenir, son kodlar bitince tek tam tur çalıştır. WHISPER_STUDIO_DATA test-sessions olmalı.

Sıradaki işler: 29895 bitişini bekle; gerekirse quality_bench.audit_lecture_qwen ile kullanıcının 29Eylül kaydındaki 4 sorunlu 24sn parçayı yerelde karşılaştır (script hazır, insan referansı yok, WER iddiası yok); bu 20 kaynak benchmarkından ayrı özel ders denemesidir. MT kıyasının çıktıları source/reference/hypothesis olarak okuyup çelişki/sayı/sıra/ad kayıplarını incele. Referansları modele ASLA verme. Ölçümlerin ardından gerekirse genel ordinal/rank koruması için dar, testli bir düzeltme yap; ölçümdeki orijinal v6 sonuçları değiştirme/başarı gibi sunma. Motor seçimini yalnızca bu küçük setteki ufak farkla genelleştirme. Son kalite raporunu ve tekrar çalıştırma README'sini bitir; kullanıcının eski derslerine dokunma.

Rapor komutları (app cwd): .venv/Scripts/python.exe -m quality_bench.report ; chrF için work/asr-compare-env/Scripts/python.exe -m quality_bench.score_translation. Ana cwd outputs/DersYazi, work göreli ../../work.

Hız uyarısı: Windows PowerLineStatus Offline, pil%66; nvidia-smi P8/180MHz, software power cap Active, sıcaklık48C ölçüldü. Kullanıcıya prize takarsa hızlanabileceği söylendi. Sistem ayarı değiştirilmedi. Süreler standart hız kıyası değil; doğruluk esas. Her60sn anlamlı kısa Türkçe güncelleme ver. Alt ajan yok. Veri internete gönderilmez; yalnızca açık veri/model indirmeleri.
# SON DURUM — 17 Ekim 2026, önceki aktif iş notlarının yerine geçer

Tüm benchmark işleri tamamlandı: 20 kaynak ses + 4 ayrı stres, dört ASR ayarı; 20 FLORES cümlesinde dört çeviri kolu / 80 sonuç. Qwen-ASR ve TranslateGemma modelleri indirildi. Kullanıcının dersinden beş ek Qwen parçası işlendi (insan referansı yok). Kararlar quality_bench/DEGERLENDIRME.md, ölçümler RAPOR.md, tekrar komutları README.md içinde.

Ana motorlar değiştirilmedi. semantic_checks.py ve lecture_translation.py ile dar sıra/zaman/online-offline durum kontrolleri eklendi; cache sürümü object-schema-v9-ranks-time-state. v6 ölçümleri değiştirilmedi. v8 durum hatası trace olarak korundu. v9 dört gerçek model denemesinde hedef sıra/zaman/dil kontrolleri geçti; standing class teknik terimi hâlâ kötü. Son tam suite 230 test / 30.086sn / OK; test-sessions kullanıldı. Özel benchmark motoru kapandı, kullanıcı uygulaması ve eski dersler korunuyor.

Sonraki adım: asıl derslerden sesle elle doğrulanmış bağımsız referans seti. Açık veri setindeki ufak model farkı veya 230 test genel ders doğruluğu kanıtı değil. Aşağıdaki eski AKTİF session ve v6 henüz değişmedi notları artık güncel değildir.

