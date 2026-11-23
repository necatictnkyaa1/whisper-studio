# Matematik kuyruğu — 20 Ekim 2026

Klasör: C:/Users/Necati/Desktop/Rumi Mat/Ses kaydı transkriptleri/Whisper Studio 2026-10-20 19-35-37 4a3566.

İki kayıt tamamlandı, üçü hata verdi. Kaynak bölümler mevcut: teorik telafi537, 20mat550, 28mat357. Türkçe kontrol noktaları sırasıyla176,148,174. 28mat kaydında asıl şema hatası174–177bloğundaki176numaralı satırdaydı. Henüz tamamlanmayan Türkçe/İngilizce bölümleri mevcut; tam kayıtlar yeniden çalıştırılmadı.

Sayısal şema üç denemede de üretilemezse repair_numeric_fragments devreye girer. Sayılar, eksi ve açık plus/artı ifadeleri kod tarafında tutulur. Yalnız aradaki metin parçaları normal çeviriyle işlenir; sonuç bütün kaynak satırın aynı validate kontrollerinden geçer. Eksik şema alanını boş metin sayarak geçme veya eksi kontrolünü kaldırma yapılmadı. Son noktalama boşlukları temizlenir. Bu yöntem kaynak sırasını korur, genel anlam doğrulayıcısı değildir ve çeviri akıcılığı sınırlı olabilir.

Gerçek model denemeleri work/math-fragment-repair-tests.json ve math-fragment-repair-tests-extra.json. Üç kaydın kaldığı ilk satırları, ek olarak28mat176 ve20mat149sayı dizisi denendi; çıktı doğrulamalarından geçti. Matrisin order/delay gibi kaynaktaki yanlış veya belirsiz ifadeleri hâlâ kötü çevrilebilir. Testler tüm ders kalitesi kanıtı değildir. 149satırı denemesinde plus→ve dönüşümü görüldüğünden sonrasında plus/artı da sabit sayı spanına dahil edildi; otomatik regresyon katsayı işaretlerini korur.

Dört yeni otomatik test: sayılar modele yazdırılmadan sabit ekleme, rakamsız satır, çeviri başarısızlığının gizlenmemesi ve şema denemelerinden sonra fallback. Gerçek kuyruk dosyaları ve tamamlanmış TXTler değiştirilmedi. Eski uygulama açık kalmış olabileceğinden kapatıp açıldıktan sonra aynı kuyruk.json yüklenip Başlat ile devam edilmeli; tamamlananlar atlanır. Bütün kayıtların sonuna kadar başarılı tamamlanması henüz denenmedi.
