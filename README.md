# Whisper Studio

## Toplu kayıt: Türkçe + İngilizce TXT

**Toplu TXT · Türkçe + İngilizce** düğmesinden kayıtları birlikte seçip başlat.
Çıktı klasörünü bir kez seçersin; her kayıt için `dosya-adı-tr.txt` ve `dosya-adı-en.txt`
sırayla otomatik kaydedilir. Birden fazla dosyayı ana pencereye bırakmak da kuyruğu açar.
Kayıtlı kuyruğu aç ile çıktı klasöründeki `kuyruk.json` üzerinden devam edebilirsin.
Ayrıntı: [TOPLU-TRANSKRIPT.md](TOPLU-TRANSKRIPT.md).

Eski adı DersYazı. Mevcut kayıt/model yollarını korumak için proje klasörü DersYazi olarak kalır.
Sarı maskot Misket kullanıcıyı karşılar; dosya seçimi ve işlem aşamalarına göre kısa açıklamalar verir.
“Nasıl yaparım?” menüsü tamamen yerel yardım sunar; yapay zekâ sohbeti veya dış servise bağlantı değildir.
Yardımcı “Küçült” ile tek satıra iner. Yeni görünüm için uygulamayı, açık işlemini bitirip notlarını
kaydettikten sonra `Baslat.bat` ile yeniden açabilirsin.

## Güncel okuma ve çıktı görünümü

TXT kaydet ve Kopyala zaman damgasız, boş satırlarla ayrılmış paragraflar üretir.
Kelime içeriği paragraf düzenlemesi sırasında değiştirilmez. SRT altyazı biçimi zaman bilgilerini korur.
Ders defteri alanında Genişlet ile üst kartlar gizlenir; Alanı uzat ile metin alanı büyütülür.
Orijinal metin isteğe bağlı gösterilir. İşlem sonunda yüzde yerine animasyonlu tamamlanma kartı görünür;
iptal/hata durumunda başarı kartı gösterilmez.

Geniş ses penceresinin diline ters düşen belirgin EN/TR cümlelerinde cümlenin sesi ayrıca algılanır.
Çeviri cümlelere bölünerek yapılır. Kaynakta açıkça yer alan gradient descent, mean squared error
ve Taylor series terimleri için koruma uygulanır; kaynakta olmayan terim tahmin edilerek eklenmez.
Bu dar terim listesi genel çeviri kalite garantisi değildir. Tüm ders insan referansıyla doğrulanmadı.

Windows için Türkçe arayüzlü, yerel ses/video transkripsiyon ve İngilizce↔Türkçe çeviri uygulaması.
Kayıt ve metin dışarı gönderilmez. Hesap, API anahtarı veya dakika başı API bedeli yoktur.

## Kullanım

1. Baslat.bat dosyasını açın.
2. Kaydı pencereye bırakın veya Dosya seç düğmesine basın. Yeşil onay dosyanın hazır olduğunu gösterir.
3. Çıktı dilini seçin: Türkçe, İngilizce veya Orijinal dili koru.
4. Yazıya dönüştür düğmesine basın. Kaynak dil, kalite ve kullanılacak donanım otomatik belirlenir.
5. Metni düzenleyin, kopyalayın veya TXT/SRT olarak kaydedin.

## Transkript odaklı sürüm — 18 Ekim 2026

Çalışma kağıdı oluşturma, kaynak ekleme ve internetten föy araştırması uygulamadan kaldırıldı.
Transkript, mevcut İngilizce↔Türkçe çeviri, yerel geçmiş, kişisel notlar ve TXT/SRT çıktıları korunur.
Eski oturumların föy verileri uyumluluk için saklanır; etkin arayüzde kullanılmaz.
Geçmiş geliştirme belgeleri önceki sürümleri anlatabilir.
Kalite araştırması: TRANSKRIPT-ARASTIRMA-2026-10-18.md.

Kayıttaki dil değişimleri otomatik algılanır. Türkçe başlayıp İngilizce devam eden dersler için
ayrıca dil ayarı gerekmez. Çeviri şu anda yalnızca İngilizce↔Türkçe çiftlerinde desteklenir.
Diğer diller orijinal dilde yazıya dökülebilir. Kısa ve hızlı dil değişimleri yanlış algılanabilir.
Orijinal metin çevirinin yanında korunur. İstenirse dışa aktarmada orijinal metin seçilebilir.
Arama yalnızca görünümü filtreler; bütün metin dışa aktarılır.

## İlk kullanım ve internet

Gerekli konuşma/çeviri dosyaları ilk kullanımda otomatik indirilir; boyutları birkaç GB olabilir.
Süre ve hareketli gösterge görünür. Kayıt internetten bir servise yüklenmez.
Dosyalar hazır olduğunda İnternetsiz çalış seçeneğiyle ağ indirmeleri de kapatılabilir.
Çeviri bileşeni eksik olan eski kurulumlarda CeviriKurulum.bat onarım/kurulum için kullanılabilir.

Başka bilgisayarda önce uv kurun: https://docs.astral.sh/uv/getting-started/installation/
Sonra Kurulum.bat, ardından Baslat.bat çalıştırın. Kurulum doğrulanan sürümler için
requirements-lock.txt kullanır. Python 3.12 uygulama ortamındadır.
Visual C++ Runtime eksikse Microsoft x64 redistributable gerekebilir.

## Otomatik kalite

Uygulama boş sistem belleğini, NVIDIA kullanılabilirliğini ve boş ekran belleğini kontrol eder.
Yeterli kaynakta large-v3, daha sınırlı kaynakta turbo/small; GPU yoksa uygun CPU modeli seçilir.
Bu, bellek payı bırakan bir seçim kuralıdır; her cihazda bütün modellerle kalite/hız kıyaslaması yapan
bir benchmark değildir. Hedef mevcut kaynaklara uygun yüksek kalitedir. Başka açık uygulamalar
kullanılabilir belleği değiştirdiği için seçim de değişebilir.

Kaynak yetersizliği veya GPU çalışma hatasında henüz metin üretilmediyse sıradaki çalışma yolu
otomatik denenir. Metin üretildikten sonra baştan çalıştırılıp tekrar eden bölümler oluşturulmaz;
mevcut bölümler korunarak hata gösterilir. İnternet/model indirme hatası donanım hatası sayılmaz.
İnternetsiz modda uygun ve indirilmiş dosyalarla çalışılır. Seçim ayrıntıları tanılama için
automatic-selection.json dosyasındadır; arayüzde teknik seçim gerekmez.

## Sınırlar ve doğrulama

Ses çözümleme bellekte yapılır; çok uzun kayıtlar RAM kullanımını artırır. Çeviri bölüm bazındadır;
teknik terimler, isimler ve sayılar kontrol edilmelidir. Dil / işlem sütunu çevrilen bölümleri belirtir.
Düşük güven işareti doğruluk garantisi veya kalibre edilmiş hata yüzdesi değildir.
Durdurma mevcut bölüm tamamlandıktan sonra uygulanabilir; bazı indirmeler hemen kesilmeyebilir.

Testler: .venv\Scripts\python.exe -m unittest discover -s . -v
Gerçek dersin iki kısa GPU örneği ders-ornek-kontrol.json içindedir. Tam 81 dakikalık kaydın
çeviri doğruluğu insan referansıyla ölçülmedi. Çeviri modeli bu Codex çalışma ortamının ağ erişim
kısıtı nedeniyle indirilemedi; bu, kullanıcının mobil internetinin çalışmadığı anlamına gelmez.
Normal masaüstü çalıştırması ilk model indirmesini kendi ağ bağlantısıyla yapar.

### İndirmede HTTP 403 düzeltmesi

Tek argos-net.com adresi yerine önce resmi data.argosopentech.com dosya sunucusu,
sonra alternatif Argos depoları denenir. EN→TR paketinin SHA-256 özeti ve ZIP biçimi
kurulumdan önce doğrulanır. Kaynaklardan biri 403 döndürürse indirme sıradakine geçer.
Kurulum aracı hata ayrıntılarını kısa mesajla gösterir; genel bir internet bağlantısı hatası varsaymaz.
Resmi dosya dizini: https://data.argosopentech.com/argospm/v1/
Sabit EN→TR paket özeti ayrıca Hugging Face dosya kaydıyla kontrol edildi:
https://huggingface.co/TiberiuCristianLeon/Argostranslate/blob/3537c055a881609c0632fa53d69bca4fe2466ac5/translate-en_tr-1_5.argosmodel

## Lisans ve yol haritası

Uygulama kodu MIT lisanslıdır. Bağımlılıklar ve model ağırlıkları kendi lisanslarını korur.
Qt/PySide6 LGPL/GPL/ticari; PyAV BSD, FFmpeg ve NVIDIA bileşenlerinin dağıtım koşulları ayrıca
incelenmelidir. Bu geliştirme klasörü lisans denetimi tamamlanmış satış paketi değildir.
Android/iPhone, konuşmacı ayrımı, DOCX ve özet henüz uygulanmadı.
MOBIL-VE-TICARI-PLAN.md ve DOGRULAMA.md ayrıntıları içerir; önceki arayüz seçimlerine dair
notlar tarihsel olabilir. Güncel kullanıcı akışı bu dosyada anlatılandır.

## Otomatik ikinci kontrol

Kullanıcıya bölüm bazında kontrol görevi verilmez. Düşük puanlı konuşma bölümleri aynı yerel motorla daha ayrıntılı ikinci çözümlemeden geçirilir; daha güçlü aday varsa kullanılır. Boş veya uzun cümleyi değiştirmeyen çeviri daha geniş arama ve daha küçük parçalarla bir kez yeniden denenir. Aynı kalan metin silinmez. Bu yöntem kusursuz doğruluk garantisi değildir; model puanı insan doğruluk ölçümü yerine geçmez.

Güncel doğrulama: İngilizce→Türkçe modeli yerelde kurulu ve gerçek örnek çeviri başarıyla çalıştı. Önceki ağ engeli notları tarihsel kurulum durumudur. Otomatik ikinci denemeler ve görünür kontrol et işaretinin kaldırılması dahil 28 test geçti. Tam dersin insan referansıyla kalite ölçümü henüz yapılmadı.
