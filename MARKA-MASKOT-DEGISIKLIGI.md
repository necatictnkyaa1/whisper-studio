# Whisper Studio · ad ve maskot değişikliği

16.10.2026, Codex. Kullanıcı isteğiyle uygulamanın görünür adı Whisper Studio oldu.
Eski DersYazi klasörü/model/veri yolları korunur. app.py pencere başlığı ve ikon,
ui.py marka ve maskot kartı, Baslat.bat başlık, README güncellendi.

Özgün sarı/kulaklıklı maskot Misket image_gen ile üretildi; assets/whisper-mascot.png.
Üretim istemi assets/MASCOT.md içinde. mascot.py tamamen yerel, ağ/model çağrısı yapmaz.
Karşılama, seçilen dosya, transkripsiyon durumu, föy aşaması ve bitiş/hata mesajları,
beş konulu Nasıl yaparım menüsü, küçült/göster ve kısa giriş animasyonu vardır.
Genişletilmiş okuma modunda maskot gizlenir; metin alanını daraltmaz.
Bu karakter genel sorulara yanıt veren bir LLM sohbeti değildir.

Doğrulama: gerçek Qt pencere görüntüsü whisper-studio-preview.png üretildi ve görsel incelendi.
Pencere adı, PNG yüklenmesi, küçült/göster ve mesaj güncelleme smoke kontrolü geçti.
19 mevcut UI testi OK (0,806 sn). Model/GPU işleri çalıştırılmadı; kullanıcının açık uygulaması kapatılmadı.

Yeni yerel Claude Code oturumu YENI-OTURUM-DEVIR.md okuduğunu ve geçmiş hataları anladığını
bildirdi, verify prototipinin ilk küçük görevi üzerinde çalışmaya başladı. Bu marka dosyalarına
eşzamanlı dokunmaması istendi. Detaylı devir belgesi diskten tekrar okunabilir.
