# Toplu transkript — Türkçe ve İngilizce TXT

19 Ekim 2026. Masaüstü kısayolundan güncel Whisper Studio'yu aç.

1. **Toplu TXT · Türkçe + İngilizce** düğmesine bas.
2. **Kayıtları seç** ile 43 dosyanı birlikte seç (Ctrl+A veya Ctrl ile çoklu seçim). Birden fazla dosyayı ana pencereye sürüklemek veya normal Dosya seç ekranından birlikte seçmek de bu kuyruğu açar.
3. **Türkçe + İngilizce TXT oluştur** düğmesine bas ve çıktı klasörünü seç.
4. Uygulama bu klasör altında tarihli ayrı bir çalışma klasörü oluşturur. Kayıtları sırayla işler. Örneğin `29-09-2026.mp3` için `29-09-2026-tr.txt` ve `29-09-2026-en.txt` çıkar. Tümü tamamlanırsa 43 kayıt için 86 TXT olur. Metinler zaman damgasız paragraflardır; kaynakta İngilizce ve Türkçe karışık olsa da iki hedef dil ayrı hazırlanır.
5. Her dilin TXT'si hazır olur olmaz kaydedilir. **Çıktı klasörünü aç** ile işlem bitmeden de hazır dosyalara ulaşabilirsin.

## Durdurmak ve devam etmek

**Durdur** düğmesine bas; mevcut model çağrısının durması biraz sürebilir. Kaydedilmiş dosyalar ve tamamlanmış orijinal transkript korunur. Aynı pencerede Başlat ile veya sonraki açılışta **Kayıtlı kuyruğu aç** üzerinden çıktı klasöründeki `kuyruk.json` dosyasını seçerek devam et.

Tamamlanan kayıtlar atlanır. Tamamlanmış ses çözümleme tekrar çalıştırılmaz; yarım çevirinin tamamlanan bölümleri kullanılır. Ses çözümleme sırasında durdurulmuş kaydın ses çözümlemesi yeniden başlar. Ani kapanmada en son sekiz bölümlük çeviri kontrol noktasından sonraki bölüm yeniden işlenebilir. Çıktı klasöründeki `.durum.json` dosyalarını devam edebilmek için koru. Kaynak ses dosyalarını da taşıma veya değiştirme.

Bir kayıtta hata varsa ayrıntı satırda gösterilir, sonraki kayıt işlenir. Kayıt için yalnızca bir dil hazırsa o TXT saklanır; tamamı hazırmış gibi işaretlenmez. Disk/manifest yazımı gibi kuyruğun kendisini engelleyen hatalarda kuyruk durur. Aynı adlı farklı kayıtlar `(2)` gibi eklerle ayrılır; yeni kuyruk önceki çalışma klasörünün üstüne yazmaz. Kaydedilmiş TXT'ler devam etmede üzerine yazılmaz.

## Uzun kullanım

Kayıtlar bu bilgisayarda işlenir; ücretli API kullanılmaz. Gerekli model dosyalarının ilk indirmesi internet ister. Bilgisayar prize takılı, uygulama açık kalsın. İşlem sırasında Windows'un boşta kalmaya bağlı sistem uykusu geçici önlenir; işlem durunca normal davranış geri gelir. Elle uyutma, kapatma veya dizüstü kapağının kapanması ayrı davranışlardır. Toplam süre derslerin uzunluğuna ve donanıma bağlıdır; 43 uzun dersin tamamı için henüz süre ölçümü yapılmadı.

Bu geliştirme toplu işlem ve otomatik dışa aktarma sağlar. Önceden ölçülen transkript ve çeviri kalite sınırlamaları devam eder; vize için özellikle sayılar ve teknik terimlerde hata olabileceğini göz önünde bulundur.

## Doğrulama

43 sahte ses dosyasıyla otomatik kuyruk testi: 43 ASR çağrısı ve 86 ayrı TXT; bitenleri atlama, durdurma/devam, aynı ad çakışması, kaynak değişikliği, boş ses sonucu, hata sonrası sonraki dosyaya devam. Bu test 43 gerçek dersin doğrulandığı anlamına gelmez.

İki kısa gerçek açık kayıtla yerel motor denemesi: İngilizce LibriSpeech ve Türkçe FLEURS için iki dilde TXT oluştu. İlk İngilizce çıktı denemesi Türkçe ağırlıklı sistem yönergeleri nedeniyle hedef dil kontrolünden geçmedi; İngilizceye özel yönerge eklendi, aynı kuyruk ASR tekrarlanmadan tamamlandı. Test çıktıları work/batch-real-smoke altında. Bu bir kalite başarı oranı ölçümü değildir.

Son tam test: 239 test, 15.147 saniye, OK. Gerçek ders geçmişi yerine ayrı test-sessions kullanıldı.
