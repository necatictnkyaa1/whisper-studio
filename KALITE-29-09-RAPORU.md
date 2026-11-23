# 29 Eylül kaydı — transkript ve çeviri incelemesi

Bu incelemede ses tanıma ile Türkçe çeviri ayrı ele alındı. Önceki testlerin geçmesi, anlam doğruluğunun doğrulandığı anlamına gelmiyordu. Önceki kalite değerlendirmesi bu açıdan yetersizdi.

## Bulunan hatalar

| Kullanıcı çıktısı | Sorun | Yeni yaklaşım |
|---|---|---|
| “biftek” (3 kez), “böre…” (2 kez) | Teknik stack/stacking bağlamı kayboluyor. Hem sesin steak gibi çözülmesi hem alan dışı çeviri mümkün. | Güçlü orijinal transkript ve bağlamlı teknik çeviri; doğru karşılık yığın/yığına yerleştirme. |
| “beş yönetim” (3 kez) | File/five karışıklığı, dosya yönetimini başka bir anlama taşıyor. | Orijinal İngilizceyi ayrı saklama; file management için dosya yönetimi. |
| “sistem kodu” (9 kez) | System call/code tanıma ve çeviri karışıklığı. | Kaynak doğruysa system call → sistem çağrısı. Gerçek code ifadesi varsayımla değiştirilmiyor. |
| “ücretsiz BSV”, “3DSP” | FreeBSD özel adı bozuluyor. | Kod ve özel ad koruma denetimi. |
| “Sebenarnya…”, “É só…” | EN/TR dersinde çözücü üçüncü bir dile geçiyor. | İlk dil etiketinin yanında iç çözücüye verilen dil de EN/TR ile sınırlandı. |
| Çok uzun “blah” ve benzeri tekrarlar | Sessizlik/gürültü ve otomatik çözümleme döngüsü. | Tekrar sınırlı çözücü ve şüpheli bölümün yeniden çözülmesi. |
| Büyük ekran kartında small seçilmesi | RAM eşiği kaliteyi gereksiz düşürüyordu. | CUDA'da int8_float16; boş VRAM/RAM ve kontrollü bellek hatası geri dönüşü. |

## Temel mimari değişikliği

Eski ürün yolu: small veya Turbo → kısa parçalarla Argos çeviri.

Yeni otomatik yol:
1. Uygun en güçlü ses modelini seç; bu bilgisayarda tam Whisper Large-v3 CUDA üzerinde çalıştırıldı.
2. Karışık dili kısa pencerelerde çöz. Pencere içinde TR/EN değişimi bulunursa iki alt pencereye ayır. Bağlam payını korurken sözcükleri zamanına göre tek pencereye ata.
3. Önce **orijinal transkripti** tamamla ve yerel önbelleğe atomik kaydet.
4. Ses modelinin kaynaklarını serbest bırak; bağlamlı Qwen3.5 çevirisini sırayla çalıştır.
5. Önceki cümle bağlamı, teknik terim karşılıkları ve yapılandırılmış bölüm kimlikleriyle Türkçe üret.
6. Eksik/fazla bölüm, değişen sayılar, kaybolan kod adları veya kesilen yanıt varsa küçük parçalar halinde yeniden dene. Denetim yine geçmezse işlemi hata ile bitir; sessizce Argos'a veya çevrilmemiş metne dönme.

Orijinal transkript korunur; öğretmenin söylemediği bilgiler eklenmez. Teknik bir ifadenin ses tanımada bozulması, yalnızca sözlük değiştirerek güvenilir biçimde çözülemez.

## Çeviri katmanı denemesi

Aşağıdaki örnekler, ses için insan tarafından hazırlanmış referans transkript değildir. Çeviri motorunu ayrı sınamak için hazırlanmış açık teknik cümlelerdir.

| Kaynak | Yeni yerel çeviri |
|---|---|
| Block and stack methods do not limit the number of parameters. | Bloklama ve yığına yerleştirme yöntemleri parametre sayısını sınırlamaz. |
| The shell executes the fork system call to create a process. | Kabuk, işlem oluşturmak için fork sistem çağrısını çalıştırır. |
| The linker combines object files, and the loader places the executable in memory. | Bağlayıcı nesne dosyalarını birleştirir ve yükleyici çalıştırılabilir dosyayı belleğe yerleştirir. |

8 metin örneğindeki 19 terim kontrolü geçti. Tam çıktılar: `ornekler/29-09-kalite/ceviri-denetimi.json`. Bu sayı, tam kayıt için bir doğruluk yüzdesi değildir.

## Kontroller ve sınırlar

- Eksik kimlikler, sayı/kod adı kaybı, bireysel yeniden deneme, iptal, önbellek kullanımı, pencere içi dil değişimi ve çözücüde üçüncü dile geçmeme testleri eklendi.
- Son tam test turu (17 Ekim): 205 test, 23,587 saniye, OK. Bu kontroller anlam doğruluğu yüzdesi değildir.
- Ders sesi/metni dışarı gönderilmedi. Ağ yalnızca model ağırlıklarını indirmek için kullanıldı; çeviri 127.0.0.1 üzerindeki yerel motorda yapılıyor.
- Tam kaydın insan referansı olmadan WER veya “%99 doğru” iddiası yapılmaz. Arka plandaki belirsiz öğrenci konuşmaları, isimler ve düşük ses seviyesi hâlâ hata kaynağı olabilir.

Teknik kaynaklar: [Whisper resmî model kartı](https://github.com/openai/whisper/blob/main/model-card.md), [CTranslate2 nicemleme](https://github.com/OpenNMT/CTranslate2/blob/master/docs/quantization.md), [Qwen3.5-9B model kartı](https://huggingface.co/Qwen/Qwen3.5-9B).

## Tam kayıt sonucu — 17 Ekim 2026

42,5 dakikalık kayıt Large-v3 / CUDA int8_float16 ile yeniden çözüldü: 260 bölüm. Çeviri Qwen3.5:9b ile yerelde yapıldı. 312,41 saniyelik kayıt, ham ASR önbelleğinden devam eden çeviri koşusuna aittir; uçtan uca işlem süresi değildir. Turbo karşılaştırması ayrı alt klasörde korunuyor.

Large-v3 ağırlığı 3.087.284.237 bayt; SHA256: `69f74147e3334731bc3a76048724833325d2ec74642fb52620eda87352e3d4f1`. İndirme tamamlandı ve bütünlük doğrulandı.

Son incelemede beş bölüm yeniden çevrildi. İki register karşılığı yazmaç olarak düzeldi. İşlem kontrolü anlatımındaki HTML ve uydurma type çağrısı, ayrıca attach/detach ve message-passing karışıklıkları dar bağlam kurallarıyla işlendi. Bunlar sesin kesin olarak doğrulandığı iddiası değildir: ham ASR aynen korunur, yapılan normalizasyonlar `ornekler/29-09-kalite/normalizasyon-kaydi.json` içinde önceki ve yeni çeviriyle kaydedilir. Gerçek HTML veya güvenlik saldırısı bağlamlarına uygulanmaması için olumsuz testler eklendi.

Zorlanmış anahtar sözcüklerle yapılan kısa ses denemeleri bazen ek cümle uydurdu veya bir ifadeyi düşürdü; bu sonuçlar kabul edilmedi.

### Kalite açısından hâlâ kapanmayan konular

Bu çıktı son kalite onayı almış değildir. Açılıştaki platform adları ve arka plan konuşmaları hâlâ bozuk. Kaynakta `create a talent communication` gibi yanlış duyumlar var; çevirideki “yetenekli bir iletişim” de bu hatayı taşıyor. Bazı yerlerde “tamamı”, gereksiz tekrarlar ve Türkçede doğal olmayan cümleler sürüyor. Sayı/kimlik/terim denetimi bu anlam sorunlarının tamamını yakalamaz. Genel bir sözcük değiştirme ile bunları örtmek güvenilir olmaz.

Bir sonraki kalite işi, bu bölümler için insan denetimli kısa referans parçaları hazırlayıp aynı ses üzerinde ASR alternatiflerini karşılaştırmak; ardından çeviriyi kaynakla cümle cümle ölçmektir. Bu ölçüm tamamlanmadan otomatik föy üretimine güvenilir kaynak diye sunulmamalı.

Yeni çıktı `29-09-2026 · kalite incelemesi` adıyla ayrı yerel ders olarak eklendi. Önceki dersler ve Downloads dosyaları değiştirilmedi. Düz metin `ders-metni.txt`, ham metin `orijinal-transkript.txt`, zamanlı seçenek `ders-altyazi.srt` olarak ayrı saklanır.

## İkinci incelemede bulunan ek hatalar ve değişiklikler

- **Bölümler arasında metin taşınması:** 504. saniyedeki Windows cümlesinin yerine önceki bölümün çevirisi kopyalanmıştı. Kaynakta Windows varken çıktıdan düşmesi önceki kontrollerden kaçıyordu. Windows/Unix/macOS/Android/iOS adları koruma listesine eklendi; farklı kaynaklara verilen uzun, aynı çeviriler için komşu bölüm denetimi eklendi. Kaynağın kendisi gerçekten tekrar ediyorsa kabul edilir.
- **Bağlamın fazla geniş verilmesi:** Önceki iki tam cümleyi istek gövdesine koymak, bunların yeniden çevrilmesine yol açabiliyordu. Ses normalizasyonu kendi bağlamını korur; çeviri modeline ise önceki cümleler yerine yalnızca bu cümlelerde görülen sınırlı konu terimleri verilir. İlk karşılaştırmada aynı zor cümledeki üretim döngüsü bu değişiklikle kalktı.
- **Büyük çeviri grupları:** Uzun cümle tek başınayken daha düzgün, 8 bölümlük gruptayken daha bozuk çıktı. Üretim yolu artık en fazla 4 kısa bölümü birlikte işler; 300 karakter ve üzerindeki kaynak cümleler tek istek olur. Grupların toplam kaynak bütçesi 900 karakterdir.
- **okay → tamamı:** Kaynakta okay/ok varken Türkçe çıktıda bağımsız bir dolgu olarak “tamamı” oluşması reddedilir ve bölüm yeniden çevrilir. Metinden genel “tamamı” silme işlemi yoktur; “parametrelerin tamamı” gibi gerçek ifadeler korunur.
- **Kavram düşmesi:** Parametrelerin hem sayısı hem uzunluğu anılmışken yeniden çeviri bunlardan birini düşürebiliyordu. Bu iki kaynak kavramının da karşılığının korunması denetlenir. Bu, genel anlamsal doğruluğun tamamını ölçmez.

### Aynı ses üzerinde iletişim bölümü karşılaştırması

Kısa pencerede `create a talent communication` üretilen bölüm, 408–466 ve 420–466 saniyelik iki ayrı uzun pencerede `Create, delete communication` olarak çözüldü. Anahtar sözcük zorlaması kullanılmadı. İlk uzun görünüm sözcük zamanlarıyla 435–453,8 saniyelik mevcut bölüm aralığına kırpılarak bu bölüme uygulandı. Eski ses tanıma metni ve yeni aday `akustik-duzeltme.json` içinde ayrı saklanır. Bu, insan referansı değil, yerel modelin akustik yeniden çözümlemesidir. Uygulamaya her kayıtta bu özel ifadeyi değiştiren bir kural eklenmedi.

Uzun pencere her yerde daha iyi çıkmadı: başka parçalarda system call/code ve özel ad hataları arttı. Bu nedenle genel ses penceresi ayarı sırf bu örnek yüzünden büyütülmedi.

### Kabul edilmeyen denemeler

Sıcaklığı 0,7'ye çıkarmak anlamı güvenilir biçimde iyileştirmedi; önceki tam cümle bağlamıyla bilgi eklemeye de devam etti. Düşünme modu dört örnekte 4096 token sınırında kesildi, kullanılmadı. Daha kısa alternatif çeviri talimatı bazı cümleleri akıcı yaptı fakat başka yerde blocking'i “engelleme” diye bozdu; o talimat bütünüyle üretime alınmadı.

Qwen3-ASR-1.7B için ayrı deneme ortamı hazırlandı; ağırlık indirmesi zaman aşımına uğradı, alternatif indirme de çok yavaş kaldı ve durduruldu. Kısmi dosyalar devam edilebilmesi için korunuyor. **Qwen3-ASR ile ses karşılaştırması henüz yapılmadı; ürünün ses motoru hâlâ Whisper Large-v3.**

Tam test: **213 test / 23,169 saniye / OK**. Kaynak ve çeviri eşleştirme, ad koruma, büyük cümle gruplama, bağlam taşınması ve sayı/uzunluk kavramı kaybı için ek regresyon kontrolleri var. Bu sayı ses/çeviri doğruluk yüzdesi değildir.

İkinci çıktıdaki bütün 260 bölüm kimlik, sayı, belirli teknik terimler, hedef dil ipuçları ve komşu metin taşınması kontrollerinden geçti. Buna rağmen açılıştaki platform adları, “brain” diye duyulmuş ifade ve bazı doğal olmayan cümleler sürüyor. Bu kalan hatalar giderilmeden kalite işini bitmiş saymıyoruz.

### Son motor ayarlarıyla tam doğrulama

Küçük gruplar, uzun cümleyi ayrı işleme ve yeni koruma kontrolleri eklendikten sonra **260 bölümün tamamı bu son üretim ayarlarıyla baştan çevrildi**. Bu son tur 207,34 saniye sürdü; ses tanıma önceden tamamlanmıştı, bu yüzden bu süre uçtan uca ses işleme süresi değildir. Son dosyalar `ornekler/29-09-kalite/son-motor-denemesi/` altında. Önceki sonuçlar karşılaştırma için ayrı klasörlerde duruyor.

Uygulamadaki güncel ders adı `29-09-2026 · güncel çeviri`. Henüz kullanıcı tarafından düzenlenmemiş ikinci inceleme oturumu güvenli karşılaştırma ile güncellendi; bir kullanıcı düzenlemesi bulunsaydı ayrı ders oluşturulacaktı. Downloads içindeki orijinaller korunuyor.
