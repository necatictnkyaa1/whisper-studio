# DersYazı süreç planı

## Çalışma düzeni

Tek güncel proje klasörü, küçük ve tamamlanabilir işler. Claude uygulama geliştirir;
ChatGPT/Codex ayrı oturumda planı, farkları ve test kanıtlarını inceler. Aynı dosyayı
iki asistan aynı anda değiştirmez. Her devirde GELISTIRME-DURUMU.md güncellenir.
Abonelik limitleri nedeniyle dev bir sohbet yerine her aşama dosyaya kaydedilir.
Geliştirme abonelikleri ürünün çalışma motoru değildir; kullanıcılar bunlara bağlı çalışmaz.

## Aşama 0 — Mevcut uygulamayı sabitle

Kaynak yedeği; bağımlılıklar; mevcut testlerin yeniden doğrulanması; bilinen kalite hataları.
Kabul: var olan transkripsiyon, karışık dil, paragraf TXT/SRT, okuma alanı çalışmaya devam eder.

## Aşama 1 — Yerel çalışma föyü

Kaynaklar: transkript, TXT/Markdown ve metinli PDF. Ders bazında kaynak listesi ve sayfa kimliği.
Qwen3.5-9B adayını yerel çalıştırma; kaynakları bölümleme; konu haritası; kaynaklı föy üretme.
Arayüz: kaynak ekle, Çalışma kağıdı oluştur, görünür aşama/süre, iptal, sonuç kaydet.
Kabul: gerçek bir ders + not ile uçtan uca örnek; kaynak kimlikleri doğrulanır; özel dosyalar dışarı gitmez.
Formül/soru/cevap tutarlılığı ayrıca incelenir; modelin kendi onayı doğruluk kanıtı sayılmaz.

## Aşama 2 — İnternetle genişletme

SearXNG + Trafilatura adayları. Ders konusundan arama; güvenilir kaynaklara öncelik;
ilgili sayfaları okuma, adres/tarih/metin saklama, tekrarlı kaynakları ayıklama.
Dersin içeriği, ek araştırma ve üretilen örnekler ayrılır. Kaynak göstermek uydurma bağlantı yazmak değildir.
Kabul: gerçek kaynaklarla ek açıklamalar; sorgular kişisel bilgileri/ham ders kaydını içermez;
erişim engelinde bütün görev kaybolmaz; kaynak ve hizmet lisansları kaydedilir.

## Aşama 3 — Kaynak kapsamı ve çıktı kalitesi

DOCX/PPTX, görsel PDF ve fotoğraf/defter notu. Sayfa bazında okunabilirlik ve formül çıkarımı.
PDF/DOCX föy çıktısı; ders kütüphanesi; otomatik kurtarma ve işlerin kalıcı tutulması.
Kabul: dosya sayfalarının işlenme durumu gerçek; metin/denklem hataları ölçülmüş; prototip sonuçları arşivlenir.

## Aşama 4 — Bu bilgisayarla davetli pilot

Yerel model motorunun önüne kullanıcı sahipliği, kalıcı iş kuyruğu ve kimlik doğrulamalı HTTPS hizmeti.
GPU işleri sırayla; ağ/sistem kesintisinde kurtarma; dosya silme/saklama; kullanım ölçümü.
Herkese açık yayın öncesi veri erişim sınırları ve güvenlik incelenir. Model sunucusu doğrudan açılmaz.
Kabul: farklı öğrencilerin dosyaları birbirinden ayrılır; iş süresi ve kapasite gerçek ölçümle belirlenir.

## Aşama 5 — Android/iPhone ve abonelik

Ortak mobil istemci; güvenli API; hesap ve cihazlar arası ders listesi; mağaza kurallarına uygun abonelik.
Mevcut masaüstü bir anda yeniden yazılmaz. Önce hizmet kapasitesi ve ödeme ekonomisi ölçülür.
Apple/Google kuralları ülke/kanala göre doğrulanır. 7/24 veya sınırsız kullanım sözü kapasitesiz verilmez.

## Her aşamanın bitiş ölçütü

Çalışan özellik + anlamlı otomatik test + gerçek örnek + bilinen sınırlar + güncel devir notu.
Bu plan tahmini teslim tarihi veya tamamlanmış özellik listesi değildir.
