# Fizik kuyruğu eksi işareti düzeltmesi — 20 Ekim 2026

Kuyruk: Masaüstü/Rumi Fizik/Whisper Studio 2026-10-20 14-26-53 5c7bc6. İlk kayıt hata, diğer ikisi tamamlandı. İlk kayıtta 448 kaynak bölüm, 119 Türkçe bölüm, 0 İngilizce bölüm kaydedilmiş. Kaynak ASR yeniden çalıştırılmadı; gerçek kuyruk ve çıktı TXT dosyaları değiştirilmedi.

119 numaralı satırda sayı parçaları modelin boşluk vermemesinden dolayı önceki sözcüğe yapışıyordu. assemble_number_slots artık sayı değerlerini boşluklarla ayırıyor; eksi işaretini kaldırma kontrolü korunuyor. Üstsimge rakamların metin parçalarına kaçırılması da reddediliyor. Özel Unicode işaretleri yerine okunabilir NUM_A yer tutucuları ve kaynak metin bağlamı kullanılıyor.

Gerçek satır denemesinde ilk iki aday biçim kontrolünden geçse de eksik/anlamsızdı; bunlar kullanıcı çıktısına yazılmadı. Bu inceleme sırasında açık derece/power minus zero–ten kalıbında yazıyla söylenen negatif üssün hedef Türkçe ifadesini koruma kontrolü eklendi. Genel matematik doğrulayıcısı değildir.

Son gerçek yerel model yanıtı: “mikrometre, 10 üzeri eksi altı olan bir değer olacak veya bir bölü bir olarak ifade ettiğimizde nanometre, 10 üzeri eksi 9’a eşit olur.” Kaynakta bulunan problemli sözlü ifade aynen çevrilir; dersin fiziksel iddiasının doğruluğu onaylanmış değildir. Deneme kaydı: work/physics-minus-repair-test-v3.json.

Son tam test: 245 test / 16.919 saniye / OK. Beş yeni regresyon testi: boşluksuz negatif sayı ekleme, gerçek hata satırı, eksi kaybını hâlâ reddetme, üstsimge kaçırmayı reddetme ve yazıyla negatif üs kaybı.

Devam: açık eski uygulamayı kapatıp masaüstü kısayolundan aç; Toplu TXT > Kayıtlı kuyruğu aç > aynı kuyruk.json > Başlat. Tamamlanan 14/15 kayıtları atlanır, 13 kaydının mevcut transkripti ve çeviri kontrol noktasından devam edilir. İlk kaydın geri kalanının başarılı biteceği henüz doğrulanmadı. Hata kontrolü sessizce gevşetilmedi ve kuyruk tamamlandı diye işaretlenmedi.
