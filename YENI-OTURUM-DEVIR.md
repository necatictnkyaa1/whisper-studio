# Whisper Studio · yeni yerel Code oturumuna devir

## Önce oku
Bu dosya, `GELISTIRME-DURUMU.md` (özellikle 5h), `README.md`, `SUREC-PLANI.md` ve
`CLAUDE-DEVIR.md`. Eski ürün adı DersYazı; yeni kullanıcı adı **Whisper Studio**.
Mevcut klasörün adı ve veri/model yolları uyumluluk için DersYazi kalacak.

## Ürün ve ortam
Türkçe, yerel Windows/PySide6 uygulaması: ses/video → otomatik dil/donanım/model seçimiyle
transkript ve çeviri → kaynaklı çalışma föyü. Sarı/krem/kahve/mint görünüm.
TXT/clipboard düz paragraf, SRT zamanlı. Karışık EN/TR kayıtlar var. Kullanıcı teknik seçim istemiyor.
Föy transkript + TXT/MD/metinli PDF alıyor; Vikipedi ek araştırması ayrı bölüm.
Gelecekte genel web, OCR, mobil (Android+iOS), abonelik düşünülüyor; şimdi bunları başlatma.
RTX 5070 Ti Laptop 12 GB VRAM, 16 GB sistem RAM; sanal ortam `.venv`.
Ollama taşınabilir `.runtime/ollama`, Qwen3.5:9b modelleri `models/ollama`.
Ücretli API/ödeme/hesap açma/yayın veya başka kişisel klasörlere erişim yok.

## Geçmişte gerçekten yapılanlar ve sonuç
İlk sohbetin yazdığını söylediği dosyalar diskte yoktu. Yerel Code oturumunda gerçek modüller
yazıldı: sources.py, llm.py, worksheet.py ve app/ui entegrasyonu. Gerçek model/GPU çalıştı.
Kullanıcının gerçek kötü föyü `ornekler/kullanici-foyu-2026-10-16.md` içinde; veri olarak oku.
Örnek yanlışlar: tüm optimizasyon yöntemleri GD sayılıyor, GD Hessian/maksimumla karışıyor,
delta eksenler arası fark deniyor, residual köke uzaklık sayılıyor, Taylor doğruluğu koşulsuz
terim sayısına orantılı deniyor. Eski scan yalnız uyarı koyuyor; bu hedefi karşılamıyor.

Son turda `verify.py`, `sympy_worker.py`, `dogrulama_kiyas.py`, `test_verify.py` eklendi.
İddia biçimlendirme → kanıt/hesap → düzeltme → yeniden doğrulama prototipi. Ürüne BAĞLI DEĞİL:
worksheet.Builder.build hâlâ eski scan yolunu kullanıyor. Uyarı metni temizliği doğruluk iyileşmesi değildir.
SymPy artık eval/parse_expr yerine AST kuruyor, ayrı süre sınırlı süreç, kesin/yaklaşık iddia ayrımı,
hesabın iki tarafını kaynak bağlamına bağlama, örneklemeyi ispat saymama var.
Arama ilk ilgisiz sonucu kabul etmez, BM25 benzeri paragraf sıralaması ve aşama bütçeleri var.

Gerçek kıyaslar `ornekler/dogrulama/sonuc-*/rapor.md` ve `ham-kayit.json` içinde.
İlk deney 24 web isteği sınırına takıldı, sıfır düzeltme. 4 maddelik deney de sıfır düzeltme;
sonraki denemede hatalı bir cümle hesap_tutarli sayıldı: bağlamdaki doğru hesabı kontrol etmiş,
cümlenin yanlış anlamını kaçırmıştı. Birebir alıntı kontrolü de alıntı-iddia ilgisini garanti etmiyor.
Bu yüzden Codex ürün entegrasyonunu ONAYLAMADI. Genel güvenilir düzeltme hâlâ çözülmedi.
Temiz maddeyi internette bulunamadı diye silme; kanıt yetersizliği yanlışlık kanıtı değildir.
Yanlışlığı kanıtlanan ama düzeltilemeyen maddeyi başarılı sunma. Ham içerik/izler korunsun.
Eski transkript atfını düzeltilmiş cümlenin bilimsel kanıtı gibi bırakma.
Altın etiket/notlar modele sızmamalı. Sadece bu föyü ezberleyen kurallar/testler yazma.

## En son bağımsız doğrulama
Codex: tüm paket 134 test OK (10,861 sn). ResourceWarning görüldü ve
verify.SympyChecker.close kendi sürecine kill sonrası wait + pipe.close yapacak biçimde düzeltildi.
Sonra `-W error::ResourceWarning -m unittest test_verify -q`: 24 test OK (3,998 sn).
Bu küçük Codex düzeltmesini geri alma. Model/üretim kalitesini birim test geçmesi kanıtlamaz.
Önceki Claude kendi 11436 motorunu kapattı; kullanıcının app/motorunu kapatma.

## Şimdi sana verilen İLK görev (küçük ve ölçülebilir)
1. Önce mevcut dosyaların ve önceki kıyasların gerçek durumunu doğrula. Büyük yeniden yazım yok.
2. Yalnız 4 maddelik fixture'da (GD/Hessian, residual, temiz Taylor, temiz backward difference)
   iddianın anlamıyla biçimlendirilen hesabın uyuşmadığı durumda `hesap_tutarli` ile cümleyi
   doğrulamayı engelle. Doğru bağlam hesabı yanlış yorum cümlesini aklayamaz.
3. Yeni paraphrase karşı örnekleriyle test et. İlgisiz ama birebir alıntıyı doğrulama kanıtı sayma.
   Salt BM25 yüksekliği anlamsal ispat değildir. Uygun kanıt yoksa dürüst belirsiz sonuç ver.
4. Önce sahte-model/yerel hesap testleri, sonra en fazla bir kısa gerçek Qwen kıyası.
   Hatalı temizlendi / temiz korundu / yanlış doğrulandı / çözülemedi ölç; sonuç raporu kaydet.
   Başarı yoksa ürüne bağlama. Başarı olsa bile sadece 4 örnekle genelleme yapma.
5. GELISTIRME-DURUMU.md'ye dosyalar, testler, gerçek sonuç ve sonraki tek işi yaz.

## Eşzamanlı çalışma sınırı
Codex şu anda uygulama adı ve sarı maskotu app.py/ui.py ve yeni mascot.py/assets üzerinde hazırlıyor.
BU İLK GÖREVDE app.py/ui.py/mascot.py/assets dosyalarına dokunma; verify/sympy_worker/test/kıyas
ve bu görevin raporlarıyla sınırlı kal. Gerekli entegrasyonu sonra birlikte yapacağız.
Kullanıcı model/donanım seçimi veya denetleme görevi istemiyor; maskot bulut sohbeti olmayacak,
yerel karşılama, aşama açıklaması ve yardım sunacak. Yeni marka OpenAI resmî ürünü gibi sunulmasın.
