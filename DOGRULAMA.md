# Doğrulama · 15 Ekim 2026

- Donanım: NVIDIA GeForce RTX 5070 Ti Laptop GPU, 12227 MiB VRAM, compute capability 12.0.
- NVIDIA sürücüsü: 616.92. nvidia-smi CUDA üst sınırı: 13.4; bu bilgi kurulu CUDA Toolkit sürümü anlamına gelmez.
- Python 3.12.14, faster-whisper 1.2.1, CTranslate2 4.8.3, PyAV 16.1.0, PySide6 6.12.0.
- NVIDIA cuBLAS 12.9.2.10 ve NVRTC 12.9.86 uygulama ortamında. Ayrı cuDNN kurulmadan GPU testi geçti.
- Yerel SAPI sesiyle oluşturulmuş yaklaşık 10 saniyelik İngilizce konuşma: tiny çok dilli modelle CUDA float16 ve CPU int8 başarılı. Beklenen ders cümleleri her iki çıktıda bulundu. `smoke_test.py` çıkış kodu 0.
- Aynı ses ve görüntü içeren MKV dosyası: gerçek Windows penceresinde CPU int8, önbellekteki tiny modeli ve çevrimdışı seçenekle başarılı. Qt iş parçacığı, bölüm tablosu ve %100 ilerleme doğrulandı.
- 4 otomatik test geçti: zaman damgasında dakika/saat sınırları, SRT biçimi, Türkçe TXT, arayüzde metin düzenleme/kopyalama ve iki biçime kaydetme.
- `arayuz.png` başlangıç görünümü, `video-test.png` tamamlanmış gerçek video testi görünümü.
- PyAV 19.0.1 ile metadata_errors uyumsuzluğu giderildi; kurulum dosyası doğrulanan paket sürümlerini kullanır.

Henüz doğrulanmayanlar: gerçek Türkçe ders doğruluğu, birkaç saatlik kayıtların bellek tüketimi, büyük modellerin bu bilgisayardaki hız/kalite karşılaştırması, her codec türü. GPU uyumluluğu tiny ile gerçek çıkarım yapılarak doğrulandı; large-v3/turbo performans garantisi verilmez.

## Kâğıt teması güncellemesi

Sarı/krem/kahverengi/mint Qt teması eklendi. Model/CPU/GPU seçeneklerinin işleme değerleri
korundu. Arama, düzenleme sırasında güncellenir ve dışa aktarılan metni filtrelemez.
CPU/GPU seçimine göre açıklama gösterilir. Boyu kısa pencerelerde ana içerik kaydırılır.
Yeni arayüz önizlemeleri ekran dışı Qt çizimiyle kontrol edildi; `yeni-arayuz-ornek.png`
görselindeki Türkçe cümleler açıkça örnek metin olarak işaretlidir.

## Kaynak/çıktı dili güncellemesi

Kayıttaki dil ve Çıktı dili ayrıldı. Orijinal / Türkçe / İngilizce seçenekleri var;
çeviri İngilizce↔Türkçe çiftleriyle sınırlı. Orijinal sütunu ve orijinali dışa aktarma eklendi.
11 otomatik test geçti; gerçek MKV transkripsiyonu yeni arayüzle CPU/çevrimdışı modda tekrar geçti.
Çeviri yönlendirme, kaynak koruma ve SRT zamanları sahte çeviri motoruyla test edildi.
Bu oturumda ağ erişimi DNS düzeyinde engellendiği için SentencePiece/model indirilemedi;
gerçek çeviri modeli çalıştırılmadı. CeviriKurulum.bat kullanıcı tarafında indirme ve örnek test yapar.

## Gerçek ders incelemesi ve karışık dil hatası

Kullanıcının verdiği transkript Türkçe giriş + İngilizce ders içeriyor. Başlangıç dilinin tüm
dosyanın çeviri kararında kullanılması hatası bulundu. Otomatik çok dilli çözümleme ve
çeviriye ayrı ses penceresi dil kontrolü eklendi. Bu düzeltme ilk Türkçe bölümden sonra gelen
İngilizce bölümle regresyon testinde doğrulandı. Aynen kopyalanan İngilizce cümlenin başarılı
çeviri olarak sunulmadığı da test edildi.
Gerçek kayıttan toplam 63 saniyelik iki örnek turbo / CUDA float16 ile çözümlendi;
ders-ornek-kontrol.json içinde zamanlar ve model log olasılıkları var. Bu değerler kalibre edilmiş
doğruluk oranı değildir. İnsan dinlemesiyle referans transkript oluşturulmadı.
Çeviri model klasörü boş; SentencePiece mevcut, Argos modeli eksik. Ağ erişimi engeli nedeniyle
gerçek modelle Türkçe çeviri ve 81 dakikalık tam kaydın son hali henüz doğrulanmadı.

## Kullanıcı ayarı gerektirmeyen çalışma

Model, kaynak dil ve GPU/CPU seçimleri arayüzden kaldırıldı. Tek çıktı dili seçimi kaldı;
Türkçe varsayılandır. Model seçimi boş RAM ve VRAM, CUDA desteği ve güvenlik paylarıyla yapılır.
Bu kural cihazda tam performans/kalite benchmark'ı değildir. Donanım hatasında metin üretimi
başlamadıysa alternatif denenir; çıktı varken otomatik baştan başlatılmaz.
Test sırasında sistem: toplam RAM 15789 MB, boş RAM yaklaşık 3606 MB, boş VRAM 11933 MB.
Seçilen yol turbo / CUDA. Gerçek MKV, otomatik kaynak dil + otomatik model + GPU ile
çevrimdışı/orijinal çıktı modunda tamamlandı. Çeviri modelinin indirilmesi ayrıca denendi,
bu araç ortamındaki DNS kısıtı devam etti. Mobil ağın durumu hakkında çıkarım yapılmaz.
