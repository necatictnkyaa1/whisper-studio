# Whisper Studio: transkript odaklı ürün ve kalite araştırması

18 Ekim 2026. Çalışma kağıdı oluşturma ürün kapsamından çıkarıldı. Transkript ve mevcut isteğe bağlı İngilizce↔Türkçe çeviri korunuyor. Çeviri, ses çözümlemesinden ayrı değerlendirilmelidir. Bu belge yeni kalite yöntemlerinin uygulanmış veya başarı sağlamış olduğu iddiası değildir.

## Üründe tamamlanan sadeleştirme

- app.py: föy worker'ı, oluşturma/iptal/dışa aktarma işlemleri ve kaynak dosyası akışı kaldırıldı.
- ui.py ve studio.py: çalışma kağıdı sekmesi, kaynak ekleme/kaldırma ve föy çıktı düğmesi kaldırıldı. Sağ panelde kayıt bilgisi, transkript çıktıları ve kişisel notlar kaldı.
- Geçmiş oturumlar açılır; metin düzenleme, otomatik kayıt, yeniden açma ve TXT/SRT devam eder. Eski föy alanları uyumluluk verisi olarak korunur, çalıştırılmaz. Önceki araştırma/hesaplama modülleri ve testleri arşiv niteliğinde dosyalarda bulunabilir; uygulama bunlarla föy oluşturmaz. Çeviri için gerekli yerel LLM bileşenleri silinmedi.
- Kaynak kod yedeği: yedekler/transcript-only-20261018. Testler: 223 test / 28.688 saniye / OK. Önceki 230 testten sekiz kaldırılmış föy arayüz testi çıkarıldı, eski oturum uyumluluğu için bir test eklendi. Ekran: transcript-only-preview.png. Kullanıcının açık penceresi kapatılmadı; yeni sürüm yeniden açıldığında görünür.

## Elimizdeki kanıt

quality_bench/RAPOR.md: 20 kısa açık kayıt, üretim Whisper WER %9,91, Qwen ASR %9,20. Yalnızca üç sözcüklük fark; sayı yazımı eşitlenince ikisi de %7,75. Qwen Türkçe medya grubunda daha kötü. Float16 genel üstünlük getirmedi. Bunlar teknik ders başarısı veya %90 anlam doğruluğu değildir. Kullanıcının kaydındaki beş Qwen denemesinde de hatalar kaldı.

## Öncelikli araştırma ve uygulama sırası

### 1. Bölütleme ve dil geçişi — ilk deney

Mevcut recognition.py Türkçe/İngilizce için 12 saniyelik çekirdek ve iki saniye pay kullanıyor; yarım pencerelerde dil değişimi arıyor. Zorunlu kısa pencereler cümle bağlamını azaltabilir: bu kod incelemesinden çıkan bir hipotez, henüz kanıtlanmış neden değil. 12 saniyelik temel ayarı; konuşma sınırlarına oturan 20–28 saniyelik, paylı pencerelerle aynı seslerde karşılaştır. Dil geçişinde pencereyi ayır, tek dili tüm derse zorla uygulama. Sınırda sözcük kaybı/tekrar, sayı ve dil geçişi hatalarını ayrı say.

Faster-whisper Silero VAD, sözcük zamanları ve çok dilli seçenekler sunar. VAD'ın uzak veya kısık konuşmayı kesip kesmediği ayrıca ölçülmeli; mevcut vad_filter=False ayarını körlemesine True yapmak kalite garantisi değildir.
Kaynak: https://github.com/SYSTRAN/faster-whisper ; https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py

### 2. Teknik terim bağlamı — ikinci deney

Mevcut kodda iki ders alanına ait sınırlı hotword listesi zaten var. Tekrar eklenmiş özellik gibi sunulmamalı. Daha genel yaklaşım: ders başlığı ve kayıtta birden fazla kez duyulan terimlerden kısa aday listesi çıkar; aynı ses için bağlamsız/bağlamlı sonucu karşılaştır. Kaynakta olmayan terimi cümleye zorla ekleme. Kullanıcıdan model veya donanım ayarı isteme.

Faster-whisper hotwords/initial_prompt destekler. Bunlar ipucu verir; doğruluk kuralı değildir ve yanlış bağlam çıktıyı yanlış yöne çekebilir. Uzun önceki metni her pencereye taşımak yerine kısa, sınırlandırılmış bağlam deneyi yapılmalı.
Kaynak: https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py ; https://github.com/openai/whisper/blob/main/whisper/transcribe.py

### 3. Sorunlu bölgeye ikinci ses çözümleme

Mevcut core.refine_segment zaten düşük log olasılık, tekrar ve sıkışma oranı üzerinden yeniden deniyor. Daha yüksek log olasılık, gerçek doğruluğun garantisi değildir. Geliştirme adayı: düşük güvenli bölgeleri komşu ses payıyla Whisper ve Qwen3-ASR üzerinden sırayla çöz. Yalnızca metne bakan bir LLM'ye “doğrusunu uydurtma”. İki model aynı yanlış sözcüğü söyleyebilir; uyuşma tek başına doğrulama değildir. Otomatik seçim, ayrı insan referanslı sette kazanç gösterene kadar üretime alınmamalı. Modeller GPU belleğinde aynı anda tutulmak zorunda değil.

Qwen3-ASR-1.7B Türkçe ve İngilizceyi destekliyor; resmî paket uzun sesleri ve ince ayar araçlarını sunuyor. Bizim küçük kıyasımızdaki sonuç, tüm uygulamayı Qwen'e geçirmek için yeterli değil. Qwen ForcedAligner'ın yayımlanan dil listesinde Türkçe yok; ASR dil desteği ile hizalayıcı dil desteği karıştırılmamalı. Hizalama duyulmayan kelimeyi düzeltmez.
Kaynak: https://github.com/QwenLM/Qwen3-ASR ; https://huggingface.co/Qwen/Qwen3-ASR-1.7B

### 4. Ses kanalı ve gürültü kontrolü

Stereo kanalları otomatik ortalamadan önce kanal bazında kısa örnekleri karşılaştır: bir kanalda gürültü veya zayıf konuşma varsa ortalama zarar verebilir. Kırpılma, çok düşük seviye ve kesintileri tespit et. Gürültü/yankı temizleme orijinalin yerine geçmesin; ayrı aday ses olarak değerlendirilsin. Microsoft'un DNS çalışması gürültü bastırma ile konuşma bozulması arasındaki ödünleşimi açıkça belirtiyor. Temiz duyulan ses her zaman daha doğru ASR demek değildir; WER ve terim hataları ile ölçmek gerekir.
Kaynak: https://www.microsoft.com/en-us/research/academic-program/deep-noise-suppression-challenge-icassp-2023/

### 5. Ders alanına uyarlama — sonraki aşama

Tekrarlayan aksan/alan hataları yeterli, izinli ve elle doğrulanmış ses-metin çiftiyle devam ederse LoRA/ince ayar araştırılabilir. Qwen'in resmî deposunda fine-tuning araçları var. Eğitim çıktılarından ayrı, aynı cümlelerin bulunmadığı test grubu gerekir. Otomatik bozuk transkriptleri gerçek etiket gibi eğitime vermek hatayı çoğaltabilir. Bu aşamada eğitim başlatılmadı; maliyet ve bellek ihtiyacı ayrıca ölçülmeli.
Kaynak: https://github.com/QwenLM/Qwen3-ASR/tree/main/finetuning

## Yeni model konusunda eleme

- NVIDIA Parakeet TDT 0.6B v3'ün resmî 25 dil listesinde Türkçe yok. İngilizce deney adayı olabilir; karışık Türkçe–İngilizce ürünün tek motoru olarak uygun değil. https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
- Distil-large-v3 İngilizce odaklıdır; hız avantajı Türkçe ders kalitesinin yerine geçmez. https://huggingface.co/distil-whisper/distil-large-v3
- Daha büyük beam veya float16 otomatik iyileşme varsayımı değildir; mevcut yerel ölçümde float16 genel kazanç sağlamadı.

## Kabul ölçütleri

İlk geliştirme: bölütleme deneyi. Doğru sesle elle eşleştirilmiş teknik ders referanslarında mevcut sürüme göre sözcük hataları, teknik terimler, sayılar/olumsuzluklar, dil geçişleri ve atlanan konuşma ölçülecek. Temel ve yeni ayarlar aynı örnekler üzerinde çalışacak; ayar seçmek için kullanılan geliştirme parçaları ayrı doğrulama parçalarına karışmayacak. Süre ve en yüksek RAM/VRAM de raporlanacak. Kazanç görülmeden yeni bir yöntem “kaliteyi artırdı” diye sunulmayacak. Kullanıcı arayüzü tek kayıt → başlat akışında kalacak; araştırma ayarları son kullanıcıya yüklenmeyecek.
