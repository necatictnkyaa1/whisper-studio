# Whisper Studio — kişisel çalışma alanı güncellemesi

- Misket: dokununca sıçrama/el sallama, sürükleme yönünde eğilme, bırakınca esnek iniş. Mevcut sakin bekleme, ilerleme ifadesi ve seyrek konuşma korunur.
- Üç panel: solda aranabilir ders geçmişi / yeni ders / isim değiştirme; ortada kompakt kayıt alanı ve Ders metni / Çalışma kağıdı sekmeleri; sağda kayıt, kaynaklar, föy, dışa aktarılan dosyalar ve kişisel notlar.
- Bölmeler sürüklenerek boyutlandırılır ve düğmelerle açılıp kapanır. Küçük pencerelerde yan paneller gizlenir.
- SQLite ile atomik yerel kayıt: düzenlenen metin, zamanlar ve kaynak dil bilgisi, notlar, föy ve föyün kaynak alıntıları, kaynak dosya yolları, çıktı yolları, son sekme ve çıktı dili korunur. Son açılan ders geri yüklenir.
- Oturumlar varsayılan olarak %LOCALAPPDATA%\WhisperStudio\sessions\dersler.sqlite3 içinde tutulur. WHISPER_STUDIO_DATA ile test dizini ayrılır.
- Ses/video ve ek dosyalar çoğaltılmaz; özgün konumlarına bağlantı saklanır. Dosya taşınırsa kayıtlı metin ve föy kalır, sesi tekrar işlemek için dosya yeniden seçilir.
- Yeni derse geçişte mevcut oturum kaydedilir. Aktif işlem sürerken ders değiştirilmez. Disk kayıt hatası durumunda pencere kapanışı ve ders değişimi engellenir; dışa aktarma kullanılabilir.
- Test: 178 test / 24.774 saniye OK. Son çıktı listesi eklemesi sonrası ilgili 31 test / 2.414 saniye OK. Geniş ve dar pencere ekran görüntüleri görsel olarak incelendi.
- Motorlar ve doğrulama prototipi değiştirilmedi; bu çalışma yeni uzun GPU transkripsiyonu çalıştırmadı.
