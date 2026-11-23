# Pencereleme deneyinin kararı — 18 Ekim 2026

recognition.py içine iki deneysel pencere planı eklendi. En az 200 ms düşük ses enerjili aralık tercih ediliyor; hiçbir ses örneği filtrelenmiyor veya atılmıyor. Aralık yoksa süre sınırında kesiliyor. İki saniye bağlam payı ve mevcut dil değişimi kontrolü korunuyor. Uzun aday 16–26 saniye, kısa aday 8–12 saniye arasında kesiyor. Enerji eşiği konuşma sınıflandırıcısı veya kusursuz cümle sınırı bulucu değildir.

Her aday aynı 20 kaynak kayıt ve ana puandan ayrı dört yapay stres örneğinde Large-v3 / CUDA int8_float16 ile çalıştırıldı. Referanslar model istemlerine verilmedi. Sonuçlar temel koşunun üzerine yazılmadı. Toplam 48 yeni dosya çözümlemesi yapıldı.

| Yöntem | Ana 20 kayıtta hata / 424 sözcük | WER | Yapay dil geçişinde hata / 70 sözcük |
|---|---:|---:|---:|
| Mevcut sabit kısa pencere | 42 | %9,91 | 4 |
| Uzun, sessiz araya kaydırılmış | 43 | %10,14 | 26 |
| Kısa, sessiz araya kaydırılmış | 43 | %10,14 | 5 |

Karar: iki aday da üretim varsayılanı yapılmadı. speech_windows varsayılan strategy='fixed' olarak kaldı. Önbellek sürümü değişmedi; kullanıcı kayıtları yeniden üretilmedi veya üzerine yazılmadı. Uzun bağlamın yararlı olacağı hipotezi bu küçük sette desteklenmedi. Kısa aday kaynakta bulunmayan “Türkiye'de” eklemesi yaptı; yalnızca duraklama sınırına yaslanmak bunu önlemedi.

Bu veri ayar geliştirmede kullanıldığı için bağımsız doğrulama seti değildir. Yapay dil geçişleri doğal ders konuşması sayılmaz. Bir sözcüklük ana fark için istatistiksel veya genel üstünlük iddiası yoktur; WER anlam doğruluğu yüzdesi değildir. Önceki ve yeni koşuların güç/arka plan koşulları standartlaştırılmadı; süreler hız üstünlüğü olarak yorumlanmamalıdır.

## Üretimde düzeltilen hata

app.Window.finished daha önce sıfır bölüm veya yalnızca boşluk içeren sonuçta da başarı animasyonu gösterebiliyordu. Artık boş çıktı başarı olarak gösterilmez; yüzde ve tamamlanma kartı gizlenip konuşma metni elde edilemediği belirtilir. İptal/hata ve dolu çıktı davranışı korunur. Bu, ASR doğruluğu artışı değildir.

## Tekrar çalıştırma

Uygulama klasöründe:

```powershell
.\.venv\Scripts\python.exe -m quality_bench.run_whisper --mode pause
.\.venv\Scripts\python.exe -m quality_bench.run_whisper --mode pause-short
.\.venv\Scripts\python.exe -m quality_bench.compare_windows --candidate pause
.\.venv\Scripts\python.exe -m quality_bench.compare_windows --candidate pause-short
```

Tam çıktılar PENCERE-KIYASI-pause.md ve PENCERE-KIYASI-pause-short.md içinde. JSON sonuçları results/whisper-pause*.json ve results/window-comparison-pause*.json. Karşılaştırıcı manifest özeti, kimlikler, referanslar ve hesaplama hassasiyeti eşleşmezse puan üretmez; eksik koşuyu tamamlanmış saymaz.

Altı yeni sınır testi; zaman çizgisinde boşluk olmaması, kuyrukların korunması, iptal, üst süre sınırı ve dil değişimini kontrol eder. Boş çıktı için ayrıca arayüz regresyon testi eklendi.

Sıradaki kalite deneyi, aynı sette pencere ayarlarını tekrar değiştirerek uydurmak yerine gerçek dersin zor bölümlerinde teknik terim bağlamını ve ikinci ASR adayını karşılaştırmaktır. Sesle doğrulanmış ayrı referans olmadan genel ders kalitesi artışı ilan edilmemeli.

Son tam doğrulama: 230 test, 24.788 saniye, OK. Testler ayrı work/test-sessions klasöründe çalıştı.
