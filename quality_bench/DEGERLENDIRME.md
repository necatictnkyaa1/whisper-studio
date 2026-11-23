# Kalite deneyi: karar ve somut hatalar

17 Ekim 2026. Ölçümler: [RAPOR.md](RAPOR.md). Kayıt kimlikleri, kaynaklar ve dosya özetleri: [manifest.json](manifest.json). Tekrar çalıştırma: [README.md](README.md).

## Ne yaptık?

İnternetten insan referans metni bulunan 20 kısa kayıt seçildi: 5 FLEURS Türkçe, 5 MediaSpeech Türkçe, 5 LibriSpeech clean ve 5 other İngilizce. Toplam 200,825 saniye ve 424 referans sözcük. Seçim model çıktılarından önce donduruldu. Ayrıca 4 yapay stres örneği ana sonuçtan ayrı tutuldu. Aynı kayıtlar üretim Whisper, sade Whisper int8, sade Whisper float16 ve Qwen3-ASR ile işlendi.

Çeviri ayrıca 20 FLORES EN/TR insan referansı üzerinde dört yöntemle karşılaştırıldı: Argos, mevcut Qwen JSON istemi, sade Qwen istemi ve TranslateGemma 12B. Toplam 80 çeviri. Referans metinleri modellere verilmedi. İndirme dışında işlem yerel yapıldı.

## Bulgular ve karar

Whisper üretim ayarı 42/424 sözcük hatası (%9,91 WER), Qwen ASR 39/424 (%9,20) verdi. Bu yalnızca üç sözcüklük fark; eşleştirilmiş bootstrap fark aralığı sıfırı içeriyor. Türkçe sayı yazımı eşitlendiğinde ikisi de %7,75. Qwen İngilizcede daha iyi, Türkçe medya grubunda daha kötü çıktı. Float16 kullanımı da genel iyileşme sağlamadı. Bu veriye dayanarak ana ASR motoru değiştirilmedi.

Kullanıcının ders kaydından ayrıca beş kısa parça Qwen ile yerelde işlendi. İnsan referansı olmadığı için bunlara doğruluk puanı verilmedi. Açılışta anlamsız ifadeler, teknik bölümde “shape memory module” gibi şüpheli duyumlar hâlâ var. Model değişimi ders sorununu çözmüş sayılmaz. Sonuçlar results/lecture-audit-qwen.json içinde.

Çeviri puanları tek başına güvenli karar vermiyor. Mevcut Qwen, doğrulama grubunda en yüksek chrF++ değerini aldı; buna rağmen geliştirme örneklerinde şu anlam hataları bulundu:

- “finishing ninth”: dokuzuncu yerine **dördüncü** üretildi.
- “used to be diabetic / now non-diabetic”: geçmiş ve şimdiki durum karıştırıldı.
- “Scandinavian”: daha geniş bir anlam olan **Kuzey Avrupa** kullanıldı.
- “phages”: Türkçedeki **faj** yerine **fag** üretildi.

Sade Qwen istemi ilk iki örneği düzeltti ama ayrı doğrulama grubunda toplam puanı düştü. TranslateGemma bazı terimleri daha iyi çevirdi; başka örnekte GMT için kaynakta bulunmayan bir açıklama ekledi. Hiçbiri kesin kazanan değil. TranslateGemma ayrıca Gemma lisanslı; üretim varsayılanı yapılmadı.

## Uygulamaya yapılan değişiklik

Sıralama ifadeleri için yazıyla verilen 1–20 sayılarının korunması, açık geçmiş/şimdi karşıtlığı için zaman belirteci ve dar kapsamlı online/offline durum geçişi kontrolü eklendi. Uyumsuz çıktı yeniden istenir; başarısız çıktı sessizce doğru kabul edilmez. Çeviri önbelleği v9'a yükseltildi. Bu kontroller genel anlam doğrulayıcısı değildir; örneğin her özel adı, teknik terimi veya taraf değişimini kapsamaz.

Önemli ara bulgu: v8 denemesinde “eskiden çevrimdışı, şimdi çevrimiçi” ifadesi iki kez çevrimdışı üretildi ve zaman belirteci kontrolünden geçti. Bu hata saklandı (results/repair-v8-smoke.json); durum geçişi kontrolünün eklenme nedeni budur. v9 sonuçları ayrı dosyadadır. Eski benchmark çıktıları yeni kodun başarısı gibi değiştirilmedi. RAPOR.md içindeki Qwen3.5-9B-current etiketi karşılaştırma anındaki **v6** temel sürümdür.

Son doğrulama: 230 otomatik test geçti. v9 gerçek model denemesinde dört istek de sonuçlandı; sıra sayıları, geçmiş/şimdiki durum ve karışık dil örneği korundu. Bununla birlikte “standing class” hâlâ “pistte sıralama yarışı” olarak kötü çevriliyor. Bu dört örnek genel kalite başarısı değildir.

## Sınırlar ve sıradaki kalite kapısı

Bu küçük set teknik dersleri veya doğal Türkçe–İngilizce geçişlerini temsil etmiyor. WER anlam doğruluğu yüzdesi değildir; chrF++ da çeviri doğruluğu yüzdesi değildir. Kayıtların eğitim verisiyle örtüşmesi dışlanamadı. Bilgisayar pilde ve GPU güç kısıtlı olduğundan süreler hız karşılaştırması olarak kullanılmamalı.

Bir sonraki karar için asıl derslerden insan tarafından sesle karşılaştırılmış ayrı referans parçalar gerekir. Teknik terim, sayı, olumsuzluk, isim ve dil geçişi hataları ayrıca sayılmalı; düzeltmeler yeni ve görülmemiş örneklerde sınanmalıdır. Mevcut ölçümlerle “ders kalitesi çözüldü” denemez.

Kaynak kayıt lisansları CC BY 4.0; FLORES çeviri referansları CC BY-SA 4.0. Atıflar ATTRIBUTION.md ve FLORES-LICENSE.txt dosyalarında tutulur. Kullanıcının özel kaydı açık veri setine dahil edilmez.
