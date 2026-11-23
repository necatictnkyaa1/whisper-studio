# DersYazı · Kaynaklı çalışma föyü ve abonelik platformu

Karar taslağı: 15 Ekim 2026. Bu belge plan ve doğrulanmış kaynakları içerir;
föy motoru, mobil uygulama, uzak sunucu ve abonelik sistemi henüz uygulanmadı.

## Ürün kararı

Hedef: öğrencinin ders kaydı, okul kaynakları ve kişisel notlarından kaynaklı, Türkçe,
öğretici bir çalışma föyü hazırlamak. İlk pilot, sahibinin Windows bilgisayarında çalışır.
Daha sonra aynı iş motoru ayrı sunucuya taşınır. Kullanıcı teknik model/donanım seçmez.

Öğrenci akışı: Ders oluştur → kayıt/not ekle → Çalışma kağıdı oluştur → sonucu oku/indir.
Öğrenme seviyesi ve tekrar/sınav amacı, isteğe bağlı kişiselleştirme olabilir.

## Model kararı

İlk aday Qwen3.5-9B, 4-bit sürüm. Resmî ağırlık lisansı Apache-2.0.
Ollama qwen3.5:9b paketi yaklaşık 6,6 GB ve görsel projektör içerir.
Model dosya boyutu toplam RAM/VRAM ihtiyacı değildir. Bağlam ve görüntüler ek bellek kullanır.
Yerel çalıştırıcı olarak Ollama değerlendirilecek; kod lisansı MIT.
Bu cihazda RTX 5070 Ti Laptop GPU 12227 MiB VRAM; sistem RAM'i yaklaşık 16 GB.
9B gerçek dersle denenmeden kalite, hız veya kapasite vaadi verilemez.
Bellek yetmezse 4B gibi küçük aday otomatik değerlendirilir; 27B başlangıç hedefi değildir.
“Dünyanın en iyi modeli” iddiası yok: cihazda çalışan adaylar aynı ders ve ölçütlerle kıyaslanır.
İlk model indirmesi ve gerçek üretim testi bu çalışma kapsamında yapılmadı.

## İlk dikey prototip

1. Mevcut transkript + metin notu + metin içeren PDF ile bir ders oluştur.
2. Kaynakları kimliklendir: transkript bölüm/zamanı, PDF sayfası, not dosyası.
3. Uzun kaynakları parçalara böl; konu haritası oluştur; ilgili parçaları seç.
4. Küçük bağlamlarla konu anlatımı, tanımlar, çözümlü örnek ve soru/cevap üret.
5. Kaynak kimliği/sayfa numarası gerçekten var mı, cevap anahtarı eksik mi,
   dil ve biçim doğru mu kontrol et; sorunlu bölümü otomatik yeniden üret.
6. Tek bir okunabilir föy halinde sun. Sonraki adım PDF ve DOCX çıktısı.

Başlangıçta bağımsız vektör veritabanı, çoklu ajan ve karmaşık bulut servisleri gerekmez.
Yerel SQLite ve basit arama yeterli başlangıç olabilir; ilgili kaynakları kaçırıyorsa
embedding katmanı ölçümle eklenir. Bütün 81 dakikalık dersi ve tüm PDF'leri tek isteme
yerleştirmek yerine kaynak kapsamı izlenen bölümleme yapılır.

İlk üretim hedefi: amaçlar → konu anlatımı → terimler/formüller → çözümlü örnekler →
alıştırmalar → açıklamalı cevap anahtarı → kaynaklar. Kaynakta bulunmayan örnekler
üretilmiş örnek olarak ayrılır. Öğrenci notu öğretmen anlatımıyla çelişiyorsa kaynaklar
sessizce tek bir doğru gibi birleştirilmez. Kaynak kimliğinin var olması, açıklamanın
gerçekten kaynağa dayandığını tek başına kanıtlamaz; içerik sadakati ayrıca ölçülür.

Hatalı transkriptten güvenilir föy kendiliğinden çıkmaz. İngilizce orijinal konuşma
metni de Türkçe çevirinin yanında kaynak olarak tutulur. Dil modeli matematiksel
doğruluk kanıtlayıcısı sayılmaz. Kaynak dosyasındaki talimatlar veri olarak işlenir;
sistem talimatı, ağ çağrısı veya dosya komutu yetkisi kazanmaz.

## Dosya kapsamının genişletilmesi

İlk prototip: TXT/Markdown ve metinli PDF. Sonra DOCX, PPTX ve görsel PDF/fotoğraf.
Fotoğraf, el yazısı ve formül için görsel çıkarım/OCR ayrı test edilir; okunmamış
sayfalar okunmuş gibi kabul edilmez. Dosya ve sayfa bazında işleme durumu tutulur.
Docling/Tesseract adaydır; zorunlu ilk bağımlılık değildir. Kod ve kullanılan ek
model/codec lisansları ayrı kaydedilir. PyMuPDF otomatik olarak pakete eklenmez.

## Bilgisayarın sunucu rolü

İlk aşama yalnızca bu bilgisayardaki masaüstü prototiptir. Sonra davetli pilot:
mobil/web istemci → kimlik doğrulamalı HTTPS hizmeti → kalıcı iş kuyruğu → bu PC'deki
tek GPU çalışanı → öğrenciye ait sonuç deposu. Model çalıştırıcısı doğrudan internete açılmaz.

GPU işleri sırayla çalışır; Whisper, çeviri ve föy modeli gereksiz yere aynı anda VRAM'de
tutulmaz. Durumlar: sırada, kaynaklar okunuyor, hazırlanıyor, tamamlandı, başarısız/iptal.
Her iş ve dosyanın sahibi belirlenir; bir öğrenci diğerinin dosyasını göremez.
Silme ve saklama süreleri tasarlanır. Bilgisayar uyur veya bağlantı koparsa kuyruk işi
kaybetmemeli; kullanıcıya erişilebilirlik durumu gösterilmelidir.

Bu PC küçük pilot için değerlendirilebilir; 7/24 ücretli hizmet kapasitesi kanıtlanmadı.
Elektrik, internet, disk, destek ve donanım yıpranması maliyetleri vardır. Gerçek kaç kullanıcı
taşınacağı ölçülür: ortanca/en kötü iş süresi, VRAM/RAM tepe değeri, kuyruk bekleme süresi,
hata/kurtarma oranı ve kullanıcı başına depolama. Sonra sunucu kiralama kararı alınır.

## Platform ve abonelik

Mevcut PySide6 masaüstü MVP korunur. Mobil için Flutter gibi ortak bir istemci
değerlendirilir; bu aşamada bütün masaüstünü yeniden yazmak gereksizdir. İstemci ile
iş motorunun ayrılması, ileride Android/iPhone/web ve ayrı GPU sunucusunu mümkün kılar.
Abonelik hakkı sunucu tarafında tutulur; yalnızca uygulamadaki düğmeyi kilitlemek yeterli değildir.

İlk pilot ücretsiz/davetli; ölçümden sonra sınırlı aylık föy hakkı ve ek kullanım gibi
planlar. Kapasite kanıtlanmadan sınırsız paket veya kesintisiz hizmet vaadi yok.
Apple/Google dijital hizmet ve abonelik kuralları ülke ve dağıtım kanalına göre uygulanır;
ödeme sağlayıcısı seçimi bu kurallardan bağımsız yapılmaz. Mağaza üyelikleri ve işlem
kesintileri modelin ücretsiz olmasından ayrı giderlerdir.

## Lisans ve haklar

Apache-2.0 şartlı ticari kullanım/değiştirme/dağıtma hakları verir; model lisansında
ciro payı veya kullanım başına telif bedeli öngörülmez. Lisans/atıf/NOTICE ve değişiklik
bildirimleri gerektiği şekilde korunur. Bu, tüm üçüncü taraf hakları veya üretilen
içeriğin hukuki sorunsuzluğu için garanti değildir. Seçilen sürüm ve model özeti sabitlenir.

Mevcut Qt/PySide6, FFmpeg, NVIDIA kitaplıkları ve yeni eklenen bileşenler ayrıca
denetlenir. Öğrencinin kaynak yüklemesi, materyali bütün müşterilere dağıtma veya
eğitim verisi olarak kullanma yetkisi vermez. Eğitim için yeniden kullanım varsayılan
olmaz. Veri işleme rolleri, aydınlatma, hukuki dayanak, saklama/silme ve aktarım
koşulları ürüne göre belirlenir. Satış paketi öncesi somut dağıtımın hukuk/lisans
incelemesi gerekir; “hiç hak talebi gelmeyecek” garantisi sunulamaz.

## Ölçülecek kabul koşulları

Bir gerçek ders + öğretmenin PDF'si + öğrenci notuyla uçtan uca prototip;
Türkçe anlatım, kaynak sadakati, formül/soru/cevap tutarlılığı ve kapsam kontrolü.
Hız/bellek ölçümü ve pilot kullanım geri bildirimi. Modelin kendi ürettiğini kendisinin
onaylaması bağımsız doğruluk kanıtı değildir. Föy prototipi bu ölçümlerle denenmeden
mağazaya hazır veya abonelik hizmeti tamamlanmış sayılmaz.

## Doğrulanan birincil kaynaklar

- https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/LICENSE
- https://huggingface.co/Qwen/Qwen3.5-9B
- https://ollama.com/library/qwen3.5:9b
- https://github.com/ollama/ollama/blob/main/LICENSE
- https://developer.apple.com/app-store/review/guidelines/
- https://support.google.com/googleplay/android-developer/answer/9858738
- https://www.qt.io/development/open-source-lgpl-obligations
- https://ffmpeg.org/legal.html
