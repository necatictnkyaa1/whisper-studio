# Whisper Studio · Codex geliştirmeyi devraldı

16.10.2026. Claude'un `CODEX-SON-DEVIR.md` raporu alındı ve okundu. Claude kod yazmayı bıraktı;
bu turdaki değişiklikler Codex tarafından yapıldı. Kullanıcının açık uygulamaları kapatılmadı.

## Yapılan ilk iş

`verify.py` kanıt yargısının sözleşmesi değişti. Model serbest alıntı yazmak yerine `K1C1` gibi
kaynak cümlesi kimliklerini seçiyor. Alıntı metni kod tarafından kaynak cümlesinden aynen alınır.
Üç noktayla birleştirilmiş veya yeniden yazılmış model alıntısı kullanılmaz. Eksik/uydurulmuş kimlik,
yanlış tür veya limit dışı seçim reddedilir. Kaynakta duran bir cümleyi seçmek anlamsal doğruluk
kanıtı değildir; önceki ilgi kontrolü devam eder. Ayrı URL'deki ilgisiz parça başka sayfadaki
sözcüklerle aklanamaz; her seçilen URL konu adını kendi seçilmiş metninde taşımalıdır.
Her alıntı parçası, cümle kimliği ve kendi URL'siyle kaydedilir; tek URL altında farklı sayfaların
metni birleştirilmez. Bu kurallar gerekli korumalardır, genel anlamsal doğrulama değildir.

`test_verify.py`: eski sabit-alıntılı sahte yanıtlar yeni cümle seçimi sözleşmesine taşındı;
6 yeni test eklendi (model alıntısının yok sayılması, yanlış kimlik/tür/limit, ilgisiz seçim,
kimliksiz eski yanıtın reddi, ondalık/sayfa sınırları, farklı sayfaların birbirini aklayamaması).

## Doğrulama

- `python -m unittest test_verify -q`: 56 test, OK (16,276 sn).
- `python -m unittest discover -s . -q`: **166 test, OK (21,481 sn)**.
- Gerçek Qwen3.5:9b kıyası: `dogrulama_kiyas.py --birimler Y2,Y4,D1,D9 --onbellek
  --cikti ornekler/dogrulama/codex-kanit-kaynak-kontrolu-20261016`.
- 41,4 sn; 4 model çağrısı, 0 web; VRAM tepe 6665 MiB; boş RAM en düşük 999 MB.
- Y4 düzeltildi: f(1.5)=0.25 artıktır; |1.5−√2|≈0.0858 köke uzaklıktır. Codex matematik kontrolüyle doğru.
- D1 temiz ve hesap tutarlı; D9 temiz korundu fakat yeterli kanıt bulunmadı.
- Y2 çözülemedi: modelin önerdiği düzeltme maksimum ifadesini hâlâ taşıdı; yeniden biçimlendirme
  yanıttaki kimliği `Y2` yerine `1` verdi. Başarılı sayılmadı. Genel düzeltme hedefi karşılanmadı.
- Önceki ara kıyas `codex-kanit-secimi-20261016` içinde: farklı URL'lerin birlikte seçilmesindeki
  kusur orada görüldü; bu nedenle ek kaynak kontrolü yapılıp son kıyas tekrarlandı.

Rapor/ham yanıtlar: `ornekler/dogrulama/codex-kanit-kaynak-kontrolu-20261016/`.
Ana ürün akışı değiştirilmedi; `worksheet.Builder.build` eski scan yolundadır, verify prototiptir.
Bu sonuçlar dört maddelik tek son koşuya aittir, başka dersler için başarı yüzdesi değildir.

## Sonraki somut iş

Biçimlendirme şemasında izinli birim kimliklerini çağrıya özel enum ile sınırla; bilinmeyen/yinelenen
kimliği güvenli reddet. Tek cümlenin bilimsel iddiası kaybolup `olgu_var=false` diye dönmesini
doğrulandıya dönüştürme. Ardından kavramları atomik iddialara ayırıp her birini aynı kanıtla sınamak
gerekiyor; salt alıntı/anahtar sözcük örtüşmesi bilimsel ispat değildir. Ürüne bağlamak için yeterli kanıt yok.
