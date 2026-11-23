# Codex'e son devir · Claude yerel oturumu · 16.10.2026 13:20

Kullanıcının isteğiyle geliştirme Codex'e devredildi. Bu oturum kod yazmayı bıraktı; başka oturum başlatılmadı.
Ayrıntı: `GELISTIRME-DURUMU.md` bölüm **5j** (öncesi 5h, 5i). Commit yok (klasör git deposu değil).

## Son değişen dosyalar ve fonksiyonlar
- `verify.py`
  - Yeni: `_kinds`, `FUNCTION_DEF`, `_function_slot`, `ALTERNATIVES`, `_display`, `_rounded`, `_computed_value`, `_phrases`,
    `Verifier.meaning_fix`, `Verifier.decide_meaning`, `Verifier.raw` (ham model yanıtları).
  - Değişti: `interpretations` (`;` ile ayrılan yan cümleler de taranır), `interpretation_expression(slot, context)`
    (artik için fonksiyon yuvası sadeleşir/bağlamdan dolar), `Verifier.ask(..., about=())` (ham yanıtı kaydeder),
    `Verifier.interpret` (kayda `yuvalar` ekler, bağlamı geçirir), `Verifier.decide` (yorum çelişkisinde modele
    düzeltme sorulmaz → `decide_meaning`), modül belge dizgisi.
- `test_verify.py`: `FakeModel.schemas`; yeni `MeaningCorrectionTests` (12 test); `test_wrong_distance_paraphrases_are_contradicted`
  güncellendi; `test_fix_must_carry_checked_meaning_to_be_accepted` → `test_model_fix_is_never_used_for_meaning_contradiction`.
- `dogrulama_kiyas.py`: `ham-kayit.json` içine `model_yanitlari`; rapora ham yanıt sayısı ve "Düzeltme yolu" satırı.
- `GELISTIRME-DURUMU.md` (5j eklendi), bu dosya.
- Dokunulmayan: `app.py`, `ui.py`, `mascot.py`, `assets`, `sympy_worker.py`, `worksheet.py`. Codex'in `SympyChecker.close` düzeltmesi yerinde.

## Gerçek test komutları ve sonuçları
- `.venv\Scripts\python.exe -W error::ResourceWarning -m unittest discover -s .` → **160 test, OK** (21.9 sn, 13:19).
  Kayıt: `ornekler\dogrulama\sonuc-20261016-1317\test-sonucu.txt`. Sonda başka bir modülden gelen kapanmamış soket
  "Exception ignored … ResourceWarning" satırı görünüyor (verify değil; 5i'de de vardı, incelenmedi).
- `.venv\Scripts\python.exe -W error::ResourceWarning -m unittest test_verify` → 50 test OK.

## Gerçek kıyas (tek koşu)
- Komut: `.venv\Scripts\python.exe dogrulama_kiyas.py --birimler Y2,Y4,D1,D9 --onbellek`
- Yol: `ornekler\dogrulama\sonuc-20261016-1317\` (`rapor.md`, `ham-kayit.json` + `model_yanitlari`, `elle-etiket.json`, `test-sonucu.txt`).
- Dürüst sonuç: **Y4 ilk kez gerçekten düzeltildi** (model değil kod şablonu; SymPy ile yeniden doğrulandı; matematiği
  Claude teyit etti, öğretmen teyidi yok). Y2 çözülemedi (alıntı "..." ile birleştirilmiş, birebir değil → kanıt yetersiz).
  D1 ve D9 temiz korundu. Yanlış doğrulanan 0. 44.7 sn, 2 model çağrısı, 0 web, VRAM tepe 6665 MiB, boş RAM en düşük 838 MB.
  4 madde ve tek koşu: genelleme yok; diğer 7 hatalı madde denenmedi.

## Arka plan işleri / portlar
- Bu oturumun Ollama sunucusu (127.0.0.1:11436) betik sonunda kapandı; 13:19 itibarıyla 11435 ve 11436'da dinleyen süreç
  yok, `ollama` süreci yok, GPU 12 MiB.
- Açık kalan: `pythonw.exe` PID 23752 ve 19552 — büyük olasılıkla kullanıcının uygulaması; dokunulmadı.
- Bu oturumun çalışan arka plan işi yok.

## Ürün entegrasyonu
**Yok.** Doğrulama hattı prototip; `worksheet.Builder.build` hâlâ eski `scan()` uyarılarını kullanıyor. Başarı tek maddede
olduğu için bağlanmamalı.

## Bilinen kusurlar
1. Kavram cümleleri (Y2): iddia atomik alt iddialara bölünmüyor; model alıntıyı "..." ile birleştiriyor veya ilgisiz parça seçiyor.
2. Biçimlendirme kararsız: aynı D1 13:05'te `hesap_tutarli`, 13:17'de `kontrol_disi` (model taylor() yerine elle açılım ve `.subs` yazdı).
3. Şablon gösterimi: model fonksiyon yuvasını "f(x) =" önekiyle vermezse "f(1.5)" yerine "x = 1.5 için x² − 2" yazılır
   (doğru ama daha az doğal). Bağlamda aynı ifadeli "f(x) = …" varsa adı oradan almak küçük bir iyileştirme olur.
4. Şablon yalnız sayının anlamını söyler; özgün cümlenin varsa başka iddiaları düşer (`degisiklik` alanında yazıyor).
5. `_computed_value` SymPy alt sürecinin ayrıntı metni biçimine ("<ifade> = <değer>;") bağlı; biçim değişirse ikinci
   yan cümle (iddia edilen anlamın gerçek değeri) yazılmaz, yalnız seçilen anlam yazılır.
6. Anlam seçimi model yuvalarına (tahmin/gercek) dayanır; bağlama dayanma (`anchored`) şartı var ama model uydurma bir
   `gercek` yazıp başka bir türü tutarlı gösterebilir — iki tür tutarlıysa seçim yapılmaz, tek uydurma tür yakalanmaz.
7. Boş RAM 838 MB'ye düştü (kullanıcının açık uygulamalarıyla); uzun koşularda risk.

## Sonraki en küçük somut iş
Y2 türü kavram cümlesini kodla atomik alt iddialara bölmek ("GD gradyan kullanır", "GD Hessian kullanır", "GD yerel
maksimum bulur") ve her alt iddia için birebir + ilgili (quote_relevance) alıntı aramak; sahte-model testleri fixture
dışı kavramlarla; sonra yalnız aynı 4 maddeyle en fazla bir gerçek kıyas. Başarı olmadan ürüne bağlamamak.
Altın/not alanları modele gitmemeli; fixture'ı ezberleyen kural yazılmamalı (`test_rules_do_not_hardcode_fixture_values`).
