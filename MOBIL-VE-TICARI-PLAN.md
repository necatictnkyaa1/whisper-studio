# DersYazı · Masaüstü, Android ve iPhone

15 Ekim 2026. Bu dosya ürün ve mimari planıdır; mobil uygulama ve eşleştirme servisi henüz uygulanmadı.

## Şimdi hazır olan

Windows masaüstü uygulaması: sıcak sarı, krem defter, kahverengi kenarlıklar ve mint vurgular;
yerel transkripsiyon, model/dil/işlemci ayarı, çevrimdışı çalışma, metin arama, düzenleme,
kopyalama, TXT ve SRT. Fotoğraflardaki görseller kullanılmadı; benzer renk ve kâğıt hissiyle
özgün Qt bileşenleri oluşturuldu. Referanstaki Claude akışı eklenmedi; dış servise kayıt/metin gönderilmez.

## Kullanıcıya gösterilecek işlem seçenekleri

| Seçenek | Nerede çalışır? | Kullanıcı ne ayarlar? | Sınır |
|---|---|---|---|
| Bu bilgisayarda | NVIDIA GPU veya CPU | Varsayılan Otomatik, gerekirse CPU | Mevcut sürüm |
| Bu telefonda | Telefonun CPU'su; desteklenen aygıtta uygun hızlandırıcı | Küçük modeli bir kez indirir, kaliteyi seçer | Plan: pil, ısınma, bellek ve arka plan kısıtları ölçülecek |
| Kendi bilgisayarımda | Eşleşmiş kişisel bilgisayarın GPU/CPU'su | QR ile eşleştirir, bilgisayarın açık kalmasını sağlar | Plan: kayıt seçilen bilgisayara yerel ağdan aktarılır |
| Bulutta | İşletmecinin sunucusu | Açıkça seçer, aktarımı ve varsa ücreti onaylar | Şimdilik kapsam dışı, altyapı maliyeti var |

Telefon NVIDIA/CUDA kullanmaz; masaüstündeki Python/CTranslate2 paketini telefona aynen
taşımayacağız. Mobil için öneri: Flutter arayüz + cihaz içi whisper.cpp motoruna yerel bağlama.
whisper.cpp Android ve iOS örneklerine sahiptir. Bu bir başlangıç tercihidir; önce gerçek iki
cihazda kısa teknik deneme yapılmalı. iPhone'da Metal gibi desteklenen yollar, Android'de
CPU ve uygun hızlandırıcılar ayrı değerlendirilir. NPU veya her telefonda GPU hızlandırması
garanti edilmez. Mobil modeller ayrı biçimdedir; masaüstü model dosyaları doğrudan paylaşılmaz.

## Tatlı ve anlaşılır ilk açılış

1. “Kaydın nerede işlensin?” ekranı. Telefonda veya kişisel bilgisayarda seçenekleri.
2. Telefonda: “Daha hafif” / “Daha ayrıntılı”; indirme boyutu, boş alan ve çevrimdışı durumu.
3. Bilgisayarda: bilgisayar adı, son görülme, QR ile eşleştirme. Kullanıcıya CUDA ayarı yaptırılmaz.
4. İşlem öncesi görünür bilgi: “Bu telefonda kalır” veya “Yalnızca eşleşmiş X bilgisayarına gönderilir”.
5. Model inerken gerçek indirme durumu; işlem sırasında yüzde ve iptal. Henüz ölçülmeyen süre için tahmin verilmez.
6. Krem defterde zaman damgalı bölümler, arama ve düzenleme; sistem paylaşımıyla TXT/SRT çıktısı.

Bilgisayara bağlanma kullanıcı tarafından açılmalı. Eşleştirme tek kullanımlık sır, iki tarafta onay,
şifreli kanal ve cihaz iptali içermeli. Ağdaki her telefona açık bir transkripsiyon servisi kurulmamalı.
Eşleştirme ve aktarım, yerel işleme sayılmaz: kayıt telefondan seçilen bilgisayara gider; bu açıkça yazılmalı.
MVP aynı yerel ağla sınırlı olmalı; uzaktan internet erişimi sonraki ayrı güvenlik çalışmasıdır.

## Sıralı geliştirme

1. Masaüstünde uzun Türkçe dersle kalite/bellek ölçümü; otomatik kurtarma ve kayıt kuyruğu.
2. Flutter ile ortak Android/iPhone ekranları, uygulama içi dosya alma ve yerel model yönetimi.
3. Gerçek Android ve iPhone'da cihaz içi tiny/base/small karşılaştırması; hız, pil ve ısınma ölçümü.
   iPhone derleme ve imzalama için uygun macOS/Xcode ortamı ve Apple geliştirici süreci gerekir.
4. İsteğe bağlı kişisel bilgisayar eşleştirmesi, güvenli aktarım, durum takibi ve kesinti yönetimi.
5. Mağaza paketleme, erişilebilirlik, gizlilik metinleri ve lisans incelemesi.

## Ticari kullanım

Evet, lisans koşulları yerine getirilerek ücretli ürün yapılabilir. Açık kaynak olması
ücret almayı engellemez. Whisper kodu ve ağırlıkları MIT; faster-whisper ve CTranslate2 MIT.
Gerekli telif/lisans metinleri korunmalıdır. Yeni eklenen modellerin lisansları ayrıca kontrol edilir.
Uygulama adı için marka araştırması da ayrı yapılmalıdır.

PySide6/Qt tarafında LGPL/GPL/ticari seçenekler vardır. LGPL ile kapalı kaynak ticari ürün
mümkün olabilir; dinamik bağlama, kütüphaneyi değiştirebilme/yeniden bağlama, lisans bildirimleri,
ilgili kütüphane kaynakları ve değişikliklerin sağlanması gibi koşullar tam karşılanmalıdır.
Sadece “Qt kullanıyoruz” yazmak yeterli değildir. GPL-only modüller ayrıca değerlendirilir.
Mağaza koşulları ile LGPL'nin birlikte uygulanabilirliği de paket türüne göre incelenmelidir.

Kurulu PyAV'nin kendi lisansı BSD-3-Clause metnidir; beraberindeki FFmpeg ayrı incelenir.
Yerel `ffmpeg-build.json` çıktısı LGPLv3 bildiriyor, fakat yapılandırma x264/x265 seçeneklerini
de içeriyor. Bu çalışma zamanı bilgisi tek başına dağıtım lisansı onayı değildir. Ticari dağıtım
öncesi DLL'lerin gerçek kökeni, kaynakları, derleme seçenekleri, codec lisansları ve olası patent
yükümlülükleri doğrulanmalı; gerekirse yalnızca gerekli codec'lerle denetlenmiş bir dağıtım hazırlanmalı.
NVIDIA DLL'leri için yeniden dağıtım koşulları da ayrıca doğrulanmalıdır. Mevcut geliştirme klasörü,
lisans incelemesi tamamlanmış satış paketi olarak sunulmamalıdır.

Ses kayıtları kişisel veri içerebilir. Ürünün veri sorumlusu/işleyen rolleri, kayıt alma yetkisi,
aydınlatma, hukuki işleme şartı, saklama/silme ve bulut varsa aktarım koşulları belirlenmelidir.
Her durumda açık rıza tek hukuki dayanakmış gibi tasarlanmaz; kullanım senaryosu değerlendirilir.
Yerel çalışma veri aktarımını azaltır, tüm yükümlülükleri kendiliğinden kaldırmaz.
Satış/mağaza yayını öncesi somut dağıtım paketi için hukuk/lisans uzmanı incelemesi gerekir.

Ticari öneri: önce tek seferlik satın alınabilen yerel masaüstü ürün; sonra Android/iPhone
tamamlayıcısı. Bulut, istenirse ayrı ve maliyeti görünür bir seçenek olabilir. Yerel model için
dakika başı API bedeli yoktur; geliştirme, destek, mağaza ve varsa sunucu giderleri ayrıdır.

## Birincil kaynaklar

- [Whisper kod/ağırlık lisansı](https://github.com/openai/whisper#license)
- [faster-whisper lisansı](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE)
- [CTranslate2 lisansı](https://github.com/OpenNMT/CTranslate2/blob/master/LICENSE)
- [Qt LGPL yükümlülükleri](https://www.qt.io/development/open-source-lgpl-obligations)
- [Qt for Python lisansları](https://doc.qt.io/qtforpython-6/licenses.html)
- [FFmpeg yasal koşulları](https://ffmpeg.org/legal.html)
- [whisper.cpp ve mobil örnekleri](https://github.com/ggml-org/whisper.cpp)
- [Flutter yerel koda bağlama](https://docs.flutter.dev/platform-integration/bind-native-code)
- [KVKK aydınlatma yükümlülüğü](https://www.kvkk.gov.tr/Icerik/2033/Aydinlatma-Yukumlulugu-)
