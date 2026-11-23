# Transkript ve çeviri kalitesi — 16.10.2026

İlk tanı:
- automatic-selection.json son çalışmada 11.933 MB boş VRAM'e rağmen 3.245 MB boş sistem RAM'i nedeniyle small/CUDA seçildiğini gösteriyordu.
- Kurulu Turbo modeli aynı bilgisayarda başarıyla yüklendi. GPU için Turbo RAM eşiği 3.500 MB'dan 2.000 MB'a indirildi; kaynak hatasında kontrollü geri dönüş korunuyor. Büyük model eşiği değiştirilmedi.
- 62–160 ve 415–475 saniye aralıkları yerel WAV parçalarıyla karşılaştırıldı. İlk eski akış denemesinde small ilk parçada 9, Turbo 5 bölüm verdi. Filtre kapalı karşılaştırma ve bağlam paylı pencereler, atlanan İngilizce soru ve gradient descent bölümünü geri getirdi. Bu sayılar bir doğruluk yüzdesi değildir; elle doğrulanmış referans transkript yok.

Uygulanan değişiklikler:
- Otomatik dil akışında 24 saniyelik ses çekirdeği ve iki yanda 2 saniyelik bağlam kullanılıyor. Her sözcük, zamanının orta noktası üzerinden yalnızca bir pencereye ait; mutlak zamanlar korunuyor.
- Bu akış, kayıtta konuşmayı atlayan VAD filtresini kullanmıyor. Dijital sessizlik atlanıyor; tamamen sessiz aralıklar için test var. Filtrenin kaldırılması çok gürültülü sessizliklerde yanlış tanıma riskini tamamen ortadan kaldırmaz.
- Pencere sınırında yarım kalan cümleler dil, süre ve ara kontrolüyle çeviriden önce birleştiriliyor.
- Çeviri kararı cümle bazında veriliyor. Türkçe ses penceresindeki açık İngilizce cümle çevriliyor; Türkçe cümle korunuyor. Kısa “What is MSA?” sorusu da algılanıyor.
- Aşırı sözcük tekrarları yeniden çeviriliyor; yine bozuksa uydurma çıktı yerine orijinal korunuyor. Kullanıcıya yeni teknik ayar eklenmedi.
- Tam Türkçe çeviri veya bilimsel doğruluk garantisi verilmez. “MSA / minus squared error” gibi duyum hataları, anlam tahminiyle otomatik MSE yapılmıyor.

Kontrol:
- 184 test / 25.425 saniye: OK.
- Örtüşmede tek sözcük sahipliği, mutlak zamanlar, iptal/sessizlik, karışık cümle dili, kısa soru, tekrar denetimi ve GPU seçim sınırı için yeni testler var.
- Tam kayıt çıktısı: ornekler/kalite-20261016/ (ders-metni.txt, ders-altyazi.srt, ayrintili-sonuc.json).
- Orijinal Downloads/13-10-2026.txt değiştirilmedi. Kayıt veya metin dış servise gönderilmedi; kurulu yerel modeller kullanıldı.

Teknik başvuru: https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py


Tam kayıt sonucu:
- 81,5 dakika ses; 525 bölüm; Turbo/CUDA ile 335,81 saniye, ek çeviri kontrolü 37,92 saniye.
- Son otomatik taramada açık İngilizce dil ipucu: 0 bölüm; ZXQ koruma işareti: 0. Bu metrikler anlam doğruluğu ölçümü değildir.
- 185 test / 27,628 saniye: OK.
- Yeni çıktı, yerel ders geçmişine “13-10-2026 · yeni çeviri” adıyla eklendi. Eski çıktı değiştirilmedi.
- Son teknik terim koruma düzeltmesi, bozulmuş işaretin de kullanıcı metnine sızmasını engelliyor.

Son ek kontrol: Türkçe ağırlıklı paragrafın virgülle ayrılan İngilizce cümlecikleri de denetlenir. Son çeviri kontrolü 38,14 saniye; 32 ilgili regresyon testi OK. Güncel ders adı: 13-10-2026 · kalite düzeltmesi.
