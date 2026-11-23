# DersYazı · Geliştirme durumu

16.10.2026 Codex devralma güncellemesi: Claude'un son raporu `CODEX-SON-DEVIR.md` alındı;
geliştirme artık Codex'te. Kanıt cümleleri için serbest alıntı yerine kaynak kimliği seçimi,
kimlik doğrulaması ve her parça için ayrı URL kaydı eklendi. 166 test OK (21,481 sn).
Gerçek son kıyas: 1 sayısal düzeltme, 2 temiz korundu, 1 kavramsal sorun çözülemedi.
verify hâlâ prototip; ürüne bağlanmadı. Ayrıntı/sonraki iş: `CODEX-DEVAM-RAPORU.md`.

Codex son kontrolü (16.10.2026): tüm paket bağımsız olarak çalıştırıldı: 134 test, OK (10,861 sn).
Bu koşuda SymPy alt süreçleri için ResourceWarning görüldü. `verify.SympyChecker.close` kendi
alt sürecini öldürdükten sonra bekleyecek ve stdin/stdout kanallarını kapatacak şekilde düzeltildi.
Ardından `-W error::ResourceWarning -m unittest test_verify -q`: 24 test, OK (3,998 sn).
Gerçek içerik düzeltme başarısı bu testlerle kanıtlanmış değildir; doğrulama hattı hâlâ prototiptir.

Claude son durum (16.10.2026 ~13:10, bölüm 5i): yorum denetimi + alıntı ilgi kapısı eklendi; tüm paket 148 test OK. Gerçek Qwen 4 madde: yanlış doğrulandı 0 (önceden 1), temiz korundu 2/2, hatalı temizlendi 0, çözülemedi 2. Başarılı düzeltme yok → ürüne BAĞLANMADI.

Son güncelleme: 16.10.2026 01:30, Claude Code (yerel oturum). Durum: Aşama 1 — föy akışı gerçek yerel
modelle (qwen3.5:9b, GPU) sentetik kaynaklarla ve 13.10.2026 gerçek ders transkriptiyle uçtan uca çalıştı.
Kaynak sadakati katmanı (üç düzeyli örnek etiketi, sayı/formül denetimi, düşünme modlu föy denetimi,
ders kaydı uyarısı) eklendi ve aynı gerçek dersle denendi (bölüm 5c). **Aşama 2 ilk sürümü** (Vikipedi ile
ayrı "Ek araştırma" bölümü) eklendi ve gerçek internetle gerçek derste denendi (bölüm 5d).
Uygulama penceresinden uçtan uca deneme yapıldı (5e) ve tam föy son düzeltmeyle yeniden üretildi (5f). Föy denetimi kıyaslanıp şemalı 2 turlu denetime geçildi (5g).
Son güncelleme saati: 16.10.2026 ~12:05. Föy doğrulama-düzeltme hattı prototip; ürüne bağlanmadı, hedef henüz
karşılanmadı (5h).

## 0. Devralma bulgusu (önemli)

Önceki sohbetin oluşturduğu söylenen `sources.py`, `llm.py`, `worksheet.py` ve diğer dosyalar diskte
**yoktu**. Proje klasörü, üst klasörler ve kullanıcı dizininde arandı; bulunamadı.
`yedekler/kaynak-2026-10-15-2215` yedeği mevcut kaynakla birebir aynıydı (`diff -rq` farksız).
Bu nedenle bu üç modül bu oturumda sıfırdan yazıldı. Mevcut dosyalar geri alınmadı veya yeniden yazılmadı.

## 1. Ortam ve donanım (bu bilgisayarda ölçüldü)

- GPU: NVIDIA GeForce RTX 5070 Ti Laptop, 12227 MiB, compute 12.0, sürücü 616.92.
- CPU: Intel Core Ultra 7 255HX (20 çekirdek). RAM: 15789 MB. Boş RAM ölçümde 1,3–2,7 GB
  arasındaydı (Opera ve diğer uygulamalar). Disk: C: ~740 GB boş.
- Python 3.12 `.venv`. Açık bir DersYazı penceresi vardı (PID 23752, boşta); **kapatılmadı**.
- Ollama sistemde kurulu değildi. Sistem geneline kurulmadı: resmî GitHub sürümü v0.40.5
  (`ollama-windows-amd64.zip`, SHA-256 `5134ce7e…4bb7` GitHub digest ile eşleşti) proje içine
  `.runtime/ollama/` altına açıldı (1,9 GB). Sunucu yalnızca `127.0.0.1:11435`'i dinliyor;
  modeller `models/ollama/` altında. `OLLAMA_NO_CLOUD=1` ile bulut özellikleri kapalı.
- Ollama günlüğü GPU'yu gerçekten algıladı: `library=CUDA compute=12.0 … RTX 5070 Ti Laptop GPU
  libdirs=ollama,cuda_v13 total="11.9 GiB" available="10.8 GiB"`.

## 2. Model ve lisans kontrolü (resmî kaynaklar, 15.10.2026)

| Bileşen | Sürüm | Lisans | Kaynak |
|---|---|---|---|
| Qwen3.5-9B / 4B (seçilen) | ollama `qwen3.5:9b` (6,6 GB), `qwen3.5:4b` (3,3 GB) | Apache-2.0 | huggingface.co/Qwen/Qwen3.5-9B, ollama.com/library/qwen3.5 |
| Ollama | v0.40.5 (14.10.2026) | MIT | github.com/ollama/ollama/blob/main/LICENSE |
| Gemma 4 (yedek aday; `gemma4:12b` denendi, 5g) | `gemma4:12b` 7,7 GB, `e4b` | Apache-2.0 (HF model kartı) | huggingface.co/google/gemma-4-E4B-it |
| Qt PDF (PDFium) | PySide6_Pdf 6.12.0.140 | LGPL-3.0/GPL | zaten kurulu Qt dağıtımı |

- Qwen3.5 model kartı 201 dil desteği diyor; Türkçe adı ayrıca geçmiyor. Türkçe kalite burada ölçülmeli.
- Qwen3.5 varsayılan olarak "düşünme" modunda; adaptör `think: false` gönderiyor.
- Ollama kütüphanesinde 15 GB altı daha yeni Qwen yok (qwen3.6/3.8 yalnız 27B+). Kıyas için
  sonraki aday `gemma4:12b` (Apache-2.0); aynı ders ve ölçütlerle karşılaştırılmadan seçim değişmez.
- Apache-2.0/MIT ticari kullanıma izin verir; NOTICE/atıf yükümlülükleri dağıtım paketinde korunmalı.
  Bu bir hukuki inceleme değildir.

## 3. Bu aşamada eklenen/değişen dosyalar

- `sources.py` (yeni): kaynak kütüphanesi. Transkript (zaman aralığı + çeviri varsa orijinal),
  TXT/Markdown (başlık → konum, UTF-8/cp1254), metinli PDF (Qt PDF, sayfa numarası; metinsiz sayfalar
  "okunmadı" olarak raporlanır, görsel PDF açıkça reddedilir). Parça kimlikleri P1…, kaynak K1….
- `llm.py` (yeni): Ollama adaptörü. Donanıma göre otomatik model (≥9 GB boş VRAM → 9B, ≥5,5 GB → 4B,
  yoksa CPU), internetsizde indirilmiş modele düşer; motoru ilk kullanımda indirir/SHA-256 doğrular/açar;
  akışlı sohbet, JSON şeması, düşünme kapalı, 0,25 sn içinde iptal (bağlantı kapatılır), iş sonunda
  VRAM boşaltma, yalnızca kendi başlattığı sunucuyu kapatma.
- `worksheet.py` (yeni): föy hattı. Kısa kaynakta doğrudan, uzunda parça parça not çıkarma; iki üretim
  adımı (anlatım/terim/formül + çözümlü örnek/alıştırma/cevap); atıf doğrulama (var olmayan kimlik
  silinir, kaynaksız "kaynakta" örneği "üretilmiş"e çevrilir, sözcük örtüşmesi düşükse "dayanak zayıf");
  bozuk JSON'da bir yeniden deneme; Türkçe olmayan bölüm uyarısı; HTML ve Markdown görünüm.
  Kaynak metinleri `<<<KAYNAKLAR …>>>` arasında veri olarak verilir.
- `app.py` (değişti): `SheetWorker` (QThread) ve föy işlemleri; GPU işleri sırayla (transkripsiyon
  sürerken föy, föy sürerken transkripsiyon başlamaz); kaydedilmemiş föy için kapanış uyarısı.
- `ui.py` (değişti): "04 / ÇALIŞMA KAĞIDI" kartı. Mevcut 01–03 kartları ve tema korunur. Föy için ayrı
  ilerleme çubuğu yok (mevcut "tek ilerleme çubuğu" testi korunur); "Adım n/3" etiketi + geçen süre.
- `requirements*.txt`: zaten kurulu ve kullanılan `PySide6_Pdf` sabitlendi (`uv pip install --dry-run`: değişiklik yok).
- `test_sources.py`, `test_llm.py`, `test_worksheet.py` (yeni), `test_ui.py` (7 föy testi eklendi).
- `mathcheck.py` (yeni, gerçek denemede bulunan hatalar üzerine): açık sayısal eşitlikleri (ör.
  `0,6 − 0,1·(−4,8) = 1,08`) güvenli AST değerlendiricisiyle yeniden hesaplar; cevap anahtarındaki sayı ile
  açıklamanın son sonucunu karşılaştırır; basit LaTeX'i okunur Unicode'a çevirir (η, ∇, ½→1/2, yᵢ, ŷᵢ, ²).
  `worksheet.py` tutarsız maddeyi bir kez modele yeniden hesaplatır; düzelmezse maddede "⚠ Otomatik hesap
  kontrolü" uyarısı gösterir. JSON ayrıştırma öncesi `\text`, `\times`, `\nabla`, `\frac` gibi komutların
  ters eğik çizgisi korunur (aksi halde JSON bunları sekme/satır sonu olarak çözüyordu).
- `fidelity.py` (yeni, 5c): çözümlü örneğin sorusundaki kurulum formülleri (ör. `x² - 4 = 0`) ve önemli
  sayıları (0/1/2 dışı; konuşmadaki "dört" gibi sayı sözcükleri dahil) kaynak metninde arar. Sonuç:
  `kaynakta` / `uyarlanmis` (bağ var, kurulumun bir kısmı yok; eksikler gerekçe notu olarak yazılır) /
  `uretilmis`. Modelin beyanı değil bu denetim belirleyicidir. Kaynakla birebir eşleşen atıfsız örneğe
  otomatik atıf eklenir. Kavramsal (sayısız) örneklerde mekanik denetim yapılamaz; atıf varsa model etiketi korunur.
- `worksheet.py` (5c eklemeleri): üç düzeyli `dayanak`; metne sızan `[P3]` kimliklerini atıf alanına taşıma,
  "KAYNAKTA:" gibi iç etiketleri silme; **düşünme modlu madde madde föy denetimi** (her madde
  dogru/supheli/yanlis; yalnızca maddeden birebir alıntılanan uyarılar kabul edilir; ders kaydına dayanan
  maddede "konuşma tanıma hatası olabilir" notu); föy başında ders kaydı uyarısı; adım sayacı tek toplam.
- `llm.py` (5c): `think` parametresi (düşünme metni yanıta katılmaz, ilerleme olarak sayılır); 9B GPU
  bağlamı 16K → 24K; önceki işten bellekte kalan kendi modelimizin VRAM'i model seçiminde boş sayılır
  (gerçek olay: aksi halde 9B işlemcide 4,45 token/sn çalıştı).
- `sources.py`: `add_text(kind='transkript')` — DersYazı TXT dökümü ders kaydı olarak işaretlenebilir.
  (5d) `add_web(page)`: `web` türü kaynak (adres, erişim tarihi, lisans); `lesson_passages()` yalnız ders kaynakları.
- `research.py` (yeni, Aşama 2): föyün **terim adlarından** (ve modelin verdiği İngilizce karşılıktan) sorgu üretir;
  rakam içeren veya 6 sözcükten uzun sorgu yok; ders metni/transkript gönderilmez. tr.wikipedia → en.wikipedia
  arama; yalnız başlığı terimle eşleşen sayfa; anlam ayrımı sayfası ve ders konusuyla ortak sözcüğü olmayan sayfa
  (ör. coğrafi "Delta") elenir; kaynakça bölümleri atılır, ~3200 karakterle sınırlı. İstekler arası 1 sn; HTTP 429'da
  Retry-After (≤5 sn) bekleyip bir kez tekrar; iki ağ hatasından sonra araştırma durur, föy devam eder. Ek bağımlılık yok.
- `worksheet.py` (5d): anlatımdan sonra "İnternetten ek kaynaklar aranıyor" adımı; web parçaları
  `<<<İNTERNET KAYNAKLARI>>>` bloğunda veri olarak verilir; model dersten ayrı **"Ek araştırma (internet)"**
  bölümü yazar; web parçasına atıf vermeyen ek araştırma maddesi atılır. Ders anlatımı, örnekler ve "kaynakta"
  etiketi yalnız ders kaynaklarına dayanır. Föyde arama sorguları, bağlantılar, erişim tarihi ve CC BY-SA 4.0
  gösterilir; internet kapalı/erişilemedi/bulunamadı durumları ayrı yazılır. Terimlere `ingilizce` alanı eklendi.
- `app.py`/`ui.py` (5d): "İnternetsiz çalış" işaretli değilse araştırma açık; kartta neyin internete gittiği yazılı.
- `ui_e2e.py` (yeni, 5e): gerçek pencereyle uçtan uca deneme (gerçek düğme tıklaması, ekran görüntüleri, zaman günlüğü).
- `denetim_kiyas.py` (yeni, 5g): denetimi altın etiketli iki föyde tekrarlı turlarla ve farklı modellerle ölçer.
- `foy_e2e.py` (yeni): gerçek modelle uçtan uca deneme ve ölçüm betiği; `--transkript-metin` seçeneği,
  örnek etiketlerini (model beyanı → son etiket → gerekçe) ve denetim sayılarını raporlar.
- `ornekler/foy-e2e/`: sentetik öğretmen notu (HTML → Edge ile metin katmanlı PDF) ve öğrenci notu
  (içinde kasıtlı talimat enjeksiyonu satırı). Gerçek okul belgesi değildir.

## 4. Test kanıtı

- Devralmada: `.venv\Scripts\python.exe -m unittest discover -s . -v` → 35 test, OK (1,0 sn).
- Şu an: **110 test, OK (~7 sn)**. Yeni 75 test: kaynaklar (8), model adaptörü (14: otomatik model seçimi,
  akış, iptal <3 sn, takılan indirmenin yenilenmesi, motor paketinin SHA-256/yol güvenliği, bellekte kalan
  modelin VRAM'i, düşünme ilerlemesi), föy hattı (19), kaynak sadakati (6), internet araştırması (10: sorgu
  gizliliği, tr→en geri düşüş, ilgisiz/anlam ayrımı sayfası, ağ hatası, iptal, 429), hesap/LaTeX (7), arayüz (8: TXT→ders kaydı sorusu dahil).
  İnternet testleri ağ kullanmaz (sahte MediaWiki yanıtları). Sahte model / yerel sahte HTTP sunucusu kullanır; gerçek üretim
  kalitesini kanıtlamaz. İki test, gerçek denemede görülen hataların birebir metnini içerir.
- Gerçek PDF okuma: Edge ile üretilmiş 3 sayfalık Türkçe PDF → "3/3 sayfa okundu"; η, ∇, w₀, f′, ² ve
  Türkçe karakterler doğru. Qt'nin kendi QPdfWriter çıktısında metin katmanı yok (test aracı sorunu, okuyucu değil).
- Gerçek GPU hesaplama: CTranslate2 4.8.3 CUDA cihazı 1, float16 destekli; Whisper turbo float16 GPU'ya
  3,7 sn'de yüklendi (2154 MiB), 30 sn ses 2,9 sn'de çözüldü (GPU %33).
- Arayüz ekran görüntüsü (offscreen) ile 04 kartı kontrol edildi; 01–03 kartları değişmedi.

## 5. Gerçek model uçtan uca deneme (16.10.2026, bu bilgisayar, qwen3.5:9b, GPU)

Model indirme: Ollama'nın paralel indirmesi bağlantı kopmalarıyla ilerleyemedi; ana katman
(`sha256:02d45dc1…278d`, 5.629.109.120 B) resmî kayıt deposundan `curl -C -` ile indirildi,
**SHA-256 manifest özetiyle birebir eşleşti**, blob klasörüne kondu; `llm.prepare` kalan katmanları tamamladı
(362 sn). `llm.pull`'a 90 sn ilerleme yoksa bağlantıyı yenileyen kod ve son 30 sn'lik hız gösterimi eklendi.

Kaynaklar: K1 gerçek ders kaydından 2 kısa İngilizce transkript parçası (`ders-ornek-kontrol.json`),
K2 sentetik 3 sayfalık öğretmen PDF'i, K3 sentetik öğrenci notu (içinde "ŞİFRE: 1234 yaz" enjeksiyonu).
Komut: `.venv\Scripts\python.exe foy_e2e.py --cikti ornekler\foy-e2e\<klasör> --transkript ders-ornek-kontrol.json ornekler\foy-e2e\hoca-ders-notu.pdf ornekler\foy-e2e\ogrenci-notlarim.md`

| Deneme | Klasör | Süre | Çıktı token | Token/sn (üretim) | VRAM tepe | Boş RAM min | Not |
|---|---|---|---|---|---|---|---|
| 1 | `sonuc-1-ilk` | 250 sn (soğuk) | 4225 | 28,3–28,7 | 6922 MiB | 1451 MB | cevap anahtarında hesap çelişkisi |
| 2 | `sonuc-2-hesap-kontrollu` | 158 sn | 4287 | 27,2 ort. | 6926 MiB | 1196 MB | hesap doğru; JSON'da LaTeX bozuldu |
| 3 | `sonuc-3-json-latex-duzeltmesi` | 142 sn | 4478 | 31,6 ort. | 6926 MiB | 2036 MB | biçim temiz; hesap doğru |

- Ollama günlüğü: 33/33 katman GPU'da, model 4812 MiB + KV 512 MiB (16K bağlam). İlk çağrının ~60 sn'si
  model yükleme, ~42 sn'si ilk istem işleme (37 token/sn; sonraki çağrıda 1752 token/sn). Üretim ~28–32 token/sn;
  9B için düşük — JSON şema kısıtlı örneklemenin payı ölçülmedi (sonraki iş).
- Her denemede 2 model çağrısı, 0 bozuk JSON yeniden denemesi. Enjeksiyon metni 3/3 denemede çıktıda yok;
  "Kendime not" parçası hiç atıf almadı.
- Atıflar: P-kimlikleri doğru sayfaya gidiyor (tanım/MSE s.1, örnek s.2, Taylor s.3). Var olmayan kimlik üretilmedi.

Bağımsız değerlendirme (elle + Python ile):
- **Deneme 1 — ciddi hata:** alıştırma "f(w)=w², w₀=2, η=0,2 → w₂" için kalın cevap **0,8**, açıklama doğru
  sonucu **0,72** hesaplıyor (elle doğrulandı: w₁=2−0,2·4=1,2; w₂=1,2−0,2·2,4=0,72). Atıf kontrolü bunu
  yakalayamadı → `mathcheck.py` eklendi; aynı metin üzerinde çelişkiyi yakalıyor (test var).
- **Deneme 1:** anlatımda ham LaTeX (`$\eta$`, `\frac{1}{2}`) → okunur gösterime çevrildi.
- **Deneme 2:** model JSON içine `\text{eta} \times \nabla` yazdı; JSON çözümü bunları sekme/satır sonuna
  çevirdi ("ext{eta}", "imes", satır bölünmüş "abla", 12 kalıntı). Ayrıştırma düzeltmesinden sonra deneme 3'te 0.
- Matematik: 3 denemede kaynaktaki örnek (w₁=0,6; w₂=1,08), 10w−10 türevi, w₁=0,6 alıştırması doğru.
- Kalan kalite sorunları: (a) Türkçe biçim hataları ("ırakşabilir", "yavaşlaşır", "ırakşmaya");
  (b) "sıfır olan bileşenler atılır" ifadesi 2 denemede kaynağın ötesinde yorumlandı;
  (c) Deneme 3'te kaynak PDF s.2'deki örnek birebir kullanıldığı halde model atıf vermedi, föy onu
  dürüstçe "üretilmiş örnek" diye etiketledi (köken bilgisi kayboldu); (d) gerçek transkript parçaları (K1)
  kısa ve konu dışı olduğundan hiç atıf almadı. Modelin kendi doğrulaması kanıt sayılmadı.

## 5b. Tam gerçek ders denemesi (16.10.2026 00:18, kullanıcı onayıyla)

Kaynak: `outputs/13-10-2026-paragraf-duzeni.txt` (proje dışı, yalnız okundu; 31.241 bayt, 3.997 sözcük,
107 paragraf; 13.10.2026 makine öğrenmesi laboratuvar dersinin DersYazı ile çevrilmiş transkripti).
Çıktı kişisel ders içeriği taşıdığı için `kisisel/foy-13-10-2026/` altında; `kisisel/` `.gitignore`'a eklendi,
kaynak yedeğine konmamalı. Komut:
`.venv\Scripts\python.exe foy_e2e.py --cikti kisisel\foy-13-10-2026 ..\13-10-2026-paragraf-duzeni.txt`

Ölçüm (qwen3.5:9b, GPU): 24 parça → **4 parçalı not çıkarma** (ilk kez gerçek modelle) + anlatım + örnek.
Toplam 174 sn (not çıkarma 89 sn, anlatım 47 sn, örnek/alıştırma 39 sn; motor hazırlığı 8,7 sn). 6 çağrı,
0 yeniden deneme, 19.331 girdi / 9.014 çıktı token, ortalama 51,7 çıktı token/sn. VRAM tepe 6926 MiB,
boş RAM en düşük 1475 MB. İş sonunda VRAM boşaldı (0 MiB). Otomatik uyarı: 2 maddede dayanak zayıf.

Bağımsız değerlendirme (çıktı transkriptle `grep` ve Python ile karşılaştırıldı):
- Kişisel veri: transkriptin başındaki öğrenci adları ve yoklama konuşması föyde **yok** (0 eşleşme).
- Kapsam: dersin ana çizgisi doğru yakalandı: Taylor serisiyle sin x yaklaşımı, analitik ve sayısal çözüm,
  sayısal integral (dikdörtgen sayısı 4'ten 100'e), iteratif karekök tahmini, gradyan inişi ve geri yayılım.
  Transkriptteki çeviri bozuklukları ("gradient tasarım", "MSA", "sipariş bileşeni") föye taşınmadı.
  19 farklı parçaya atıf var, hepsi geçerli parça.
- Hesaplar (Python ile doğrulandı): sin(0,1) ≈ 0,0998334 ve x − x³/6 = 0,0998333 doğru; Newton adımları
  x₁ = 2,083 doğru, x₂ "2,0015" (doğrusu 2,0017; küçük yuvarlama); dikdörtgen toplamı 0,21875 ve ∫₀¹x² = 1/3 doğru.
- **Hatalı transkriptten gelen içerik hatası:** transkript "ilk sipariş bileşeni sıfırdır, üçüncü sipariş
  bileşeni sıfırdır" diyor (tanıma/çeviri hatası; sin x'te sıfır olan çift dereceli terimler). Föy anlatımı
  bunu "tek dereceden ve üçüncü dereceden terimler ihmal edilebilir" diye aktardı ve kendi doğru formülüyle
  (x − x³/3!) çelişti. Model kaynaktaki yanlışı fark etmedi.
- **Melez örnekler yanlış etiketlendi:** derste x₀ = 1,5 ile √2 aranıyor (1,5² = 2,25 → 1,4² = 1,96, hata 0,04).
  Föy bunu x² − 4 = 0 ve Newton formülüne çevirdi ama "Kaynaktaki örnek" dedi. Derste integral 0 ile 2 arası
  bir eğri için anlatılıyor; föy x², [0,1], n = 4 kurdu ve yine "kaynakta" dedi. Sayılar kaynaktan,
  kurulum üretilmiş: mevcut "kaynakta/üretilmiş" ayrımı bu durumu yakalayamıyor.
- Küçük tutarsızlık: 1. alıştırma "ilk 3 terim" istiyor, cevap iki sıfır olmayan terim veriyor (x − x³/6).
- Sonuç: föy okunur ve büyük ölçüde konuya sadık bir çalışma kağıdı; ancak öğrenciye "kontrol edilmiş" diye
  sunulacak düzeyde değil. En büyük risk, transkript hatasının ve melez örneklerin kaynaklı gibi görünmesi.

Bu denemede görülen ve düzeltilen hata: adım sayacı parçalı modda "4/6"dan sonra "1/3"e düşüyordu;
artık tek toplamla ilerliyor (test eklendi, 81 test OK).

## 5c. Kaynak sadakati iyileştirmesi ve aynı gerçek dersle tekrar (16.10.2026 00:40–01:20)

Aynı kaynak (`13-10-2026-paragraf-duzeni.txt`), bu kez `--transkript-metin` ile ders kaydı olarak.

| Deneme | Klasör (`kisisel/`) | Süre | Örnek etiketleri (model → son) | Denetim | Not |
|---|---|---|---|---|---|
| 5b | `foy-13-10-2026` | 174 sn | 4× kaynakta (3'ü aslında melez) | yok | sin x çelişkisi, melez örnekler |
| A | `foy-13-10-2026-sadakat` | 196 sn | 6× kaynakta → 1 uyarlanmış | düşünmesiz: 0 işaret | iç etiket/[P] sızıntısı, kavramsal örnekler |
| B | `foy-13-10-2026-sadakat-2` | **532 sn** | 4× üretilmiş → 2 uyarlanmış + 2 üretilmiş | düşünmeli: **3 gerçek sorun** | sızıntı yok; 4 hesaplamalı örnek |

Deneme B ölçümü: not çıkarma 97 sn, anlatım 55 sn, örnek 77 sn, **föy denetimi 303 sn**; 7 çağrı,
20.599 çıktı token, VRAM tepe 7075 MiB (24K bağlam), boş RAM en düşük **142 MB** (bkz. eksikler).

Mekanik sadakat denetimi (B): Örnek 1 "uyarlanmış — kaynakta geçmeyen ifade: x = 0.1"; Örnek 2 "üretilmiş —
f(x) = x²; x = 2.5"; Örnek 3 "üretilmiş — f(x) = e^x"; Örnek 4 "uyarlanmış — f(x) = 2x" (dersteki
dikdörtgen/integral konusu). Aynı denetim 5b föyünde x² − 4 ve x², [0,1] örneklerini doğru biçimde
"uyarlanmış"a indirdi; sentetik PDF föyünde (deneme 3) kaynaktaki örneği bulup otomatik atıf ekledi.

Düşünme modu kararı (deney, Deneme A içeriği üzerinde): düşünmesiz madde madde denetim 27 maddeye
"doğru" dedi (22 sn). Düşünmeli denetim 238 sn / 11.953 token'da 3 sorun buldu (geri yayılım ≠ gradyan
inişinin genişletilmiş hali ×2, "Delta İtalyanca/Latince" anlamsızlığı) ama "sin x tek fonksiyon → y
eksenine göre simetrik" hatasını kaçırdı. Ollama'da düşünme + JSON şeması birlikte boş yanıt verdi;
düşünmeli çağrıda şema yanıt metninden ayrıştırılıyor.

Bağımsız değerlendirme (B, Python ile): sin(0,1): 0,0998334 / yaklaşım 0,0998333 ✓; x² Taylor (a=2)
x=2,5 → 6,25 ✓; ∫₀¹eˣ = 1,71828 ✓; 2x için sağ uç Riemann (n=4) = 5,0 ✓, gerçek değer 4.
Denetimin işaretledikleri (3/3 gerçek sorun): "gradyan inişi geri yayılımın genişletilmiş versiyonu";
"merkezi fark tüm geriye dönük farkları kullanır"; Örnek 4'te "analitik sonuç 2²/2 = 2" (doğrusu 4; aritmetik
kontrol bunu yakalayamaz, ifade kendi içinde 4/2 = 2 doğru). Kaçırılanlar: "'+h' farkı geriye dönük
farktır" (ileri farktır; terimler bölümünde de var); Örnek 1'de "ilk 3 terim" deyip 2 terim kullanması.
Kişisel veri: üç gerçek ders föyünde öğrenci adı yok (Unicode sözcük sınırıyla Python denetimi; grep
"içeren" içindeki "eren"i yanlış eşleştirdi). İç etiket/[P] sızıntısı: A'da 21, B'de 0.

Sonuç: etiketler artık dürüst ve gerekçeli; denetim gerçek hataları buluyor ama hepsini değil ve föy
süresini ~3 dk'dan ~9 dk'ya çıkarıyor. Föy hâlâ "kontrol edilmiş" diye sunulamaz; ⚠ işaretleri öğrenciyi
doğru yere yönlendiriyor.

## 5d. Aşama 2 — internet ile genişletme, gerçek deneme (16.10.2026)

Komut: `.venv\Scripts\python.exe foy_e2e.py --cikti kisisel\foy-13-10-2026-internet --transkript-metin ..\13-10-2026-paragraf-duzeni.txt`
(gerçek ders, gerçek Vikipedi, qwen3.5:9b GPU).

- Süre 443 sn: not çıkarma 86, anlatım 45, **ek araştırma 10**, örnek 40, föy denetimi 255 sn; 8 çağrı;
  VRAM tepe 7075 MiB; boş RAM en düşük 644 MB.
- Sorgular (föyde listelenir): Taylor Serisi, Gradient İniş, Gradient Descent, Sayısal Analiz, Delta, En Küçük
  Kareler — yalnızca terim adları. Kullanılan sayfalar: tr "Taylor serisi", en "Gradient descent", tr "Sayısal analiz".
  Coğrafi "Delta" ilgisiz diye elendi. Bir istek **HTTP 429 (Too Many Requests)** aldı; föy devam etti.
- 4 ek araştırma maddesi, hepsi web parçasına atıflı. Sayfa metinleriyle tek tek karşılaştırıldı: Cauchy 1847,
  Hadamard 1907, Curry 1944, "local search ile karıştırılmamalı", "derin ağların eğitiminde en temel algoritma",
  direkt/yinelemeli yöntemler, ikiye bölme, matris faktörizasyonu/lineer programlama, araba hızı ile ayrıklaştırma
  örneği — **hepsi kaynakta var**. Kaynakta olmayan tek ekleme: "yerel arama daha genel bir çerçevede çalışır".
- Ders bölümleri ile ek araştırma ayrı; örnek etiketleri web sayfasından "kaynakta" olamaz (test var).
- Bu denemeden sonra yapılan iki düzeltme: 429'da bekleyip tekrar + istekler arası 1 sn; anlam ayrımı sayfalarının
  elenmesi (tr "Delta" sonraki tekrarda sözcük filtresinden geçmişti). Düzeltmeler yalnız araştırma adımıyla gerçek
  ağda tekrarlandı (17 sn, 6 sorgu → 4 ilgili sayfa: Taylor serisi, Gradient descent, Sayısal analiz, En küçük kareler
  yöntemi; Delta elendi; 1 istek yine 429). Tam föy bu iki düzeltmeden sonra yeniden üretilmedi.

## 5e. Uygulama penceresinden uçtan uca deneme (16.10.2026 06:03–06:11)

Masaüstü kontrol aracı DersYazı penceresine bağlanamadı: uygulama `.venv` pythonw ile çalışıyor, Başlat
menüsünde kayıtlı değil; araç yalnız kurulu uygulamaları kabul ediyor. Bu yüzden `ui_e2e.py` yazıldı: aynı
`app.Window` **görünür gerçek pencere** olarak açılır, 04 kartına kaynak eklenir, "Çalışma kağıdı oluştur"
düğmesine gerçek Qt fare tıklaması (`QTest.mouseClick`) gönderilir. Gerçek `SheetWorker` iş parçacığı, gerçek
model ve gerçek internet kullanılır; 30 sn'de bir pencere durumu kaydedilir. Yalnız dosya diyalogları ve
"Ders kaydı mı?" sorusu otomatik yanıtlanır. Kullanıcının açık eski DersYazı penceresine (PID 23752) dokunulmadı.

Komut: `.venv\Scripts\python.exe ui_e2e.py ..\13-10-2026-paragraf-duzeni.txt kisisel\foy-13-10-2026-uygulama`

- Kaynak listesinde "13-10-2026-paragraf-duzeni.txt — Ders kaydı · 24 parça". Banner: **"Çalışma kağıdın hazır ·
  7 dk 59 sn"**. Adım sayacı 1/9 → 9/9 geri gitmeden ilerledi; düşünmeli denetim sırasında "… karakter işlendi"
  30 sn'de bir arttı (5.127 → 39.149), pencere donmuş görünmedi. Çalışırken Durdur etkin, Oluştur kilitliydi;
  bitince tersine döndü. Föy, uygulamanın kendi `save_sheet` işleviyle MD ve HTML olarak kaydedildi; pencere
  kapanınca föy motoru da kapandı (geride süreç kalmadı). Ekran görüntüleri ve zaman günlüğü aynı klasörde.
- Aşamalar: not çıkarma 90 sn, anlatım 42, ek araştırma 11, örnek 42, föy denetimi 278 sn; 8 çağrı, 0 yeniden deneme;
  28 maddenin 28'i denetlendi, 3 işaret (geri yayılım ≠ GD uzantısı, "Delta İtalyanca/Latince", sıfır bileşen
  cümlesi), 1 uydurma alıntılı uyarı reddedildi. Ders kaydı uyarısı föyün başında. Örnekler: 1 uyarlanmış, 3 üretilmiş.
- Zayıf nokta: yalnız 1 Vikipedi sayfası (Gradient descent) bulundu; model terimleri uzun yazdı ("Taylor Series
  Approximation", "Analitik Çözüm") ve katı başlık eşleştirmesi "Taylor series"i kaçırdı. Düzeltme: başlık sorgunun
  içinde geçiyorsa (en az iki sözcük ya da sorgunun ≥%60'ı) kabul (tek genel sözcük "Öğrenme" reddedilir; test var).
  Aynı terimlerle gerçek ağda tekrar: 14 sn, **2 sayfa** (en "Taylor series", en "Gradient descent").
  Tam föy bu son düzeltmeden sonra yeniden üretilmedi.
- Ağ gözlemleri: bir denemede Python'dan Vikipedi'ye **SSL "self-signed certificate in certificate chain"** hatası
  geldi (geçici; birkaç dakika sonra aynı istek doğrulamayla geçti). Muhtemel neden ağdaki bir ara katman (VPN /
  erişim noktası). Sertifika doğrulaması kapatılmadı; araştırma iki hatadan sonra durur, föy internetsiz tamamlanır.
  Wikimedia kısa sürede çok istekte HTTP 429 veriyor (art arda testlerde tekrar görüldü).
- Uygulama değişikliği (bu adım): arayüzde TXT kaynağı eklenince tek soru: "Bu bir ders kaydının yazıya dökümü mü?"
  Evet → kaynak "Ders kaydı" türünde okunur (konuşma tanıma uyarıları devreye girer). Teknik ayar eklenmedi.

## 5f. Tam föy, başlık eşleştirme düzeltmesiyle uygulama penceresinden yeniden (16.10.2026)

Komut: `.venv\Scripts\python.exe ui_e2e.py ..\13-10-2026-paragraf-duzeni.txt kisisel\foy-13-10-2026-uygulama-2`
Föy uygulamanın kendi kaydetme işleviyle `kisisel/foy-13-10-2026-uygulama-2/calisma-kagidi.md|html` olarak kaydedildi.

- Banner **"Çalışma kağıdın hazır · 10 dk 13 sn"** (önceki 7 dk 59 sn): not çıkarma 92, anlatım 75, ek araştırma 12,
  örnek 73, föy denetimi **343 sn**; 8 çağrı, 25.336 çıktı token. Süre, modelin bu sefer daha uzun yazmasından.
- İnternet: **2 sayfa** (tr "Taylor serisi", en "Loss function"), 4 ek araştırma maddesi; en.wikipedia bir kez 429.
  Maddeler sayfa metinleriyle karşılaştırıldı: Brook Taylor, Colin Maclaurin/Maclaurin serisi, "Laplace kadar eski,
  Wald tarafından 20. yy ortasında yeniden tanıtıldı", ekonomik maliyet/pişmanlık, karesel kayıp ve en küçük kareler
  — kaynakta var. (Sözcük örtüşmesi tek başına anlamı doğrulamaz; maddeler okunarak bakıldı.)
- Ders kaydı uyarısı föy başında; 4 örneğin 4'ü "uyarlanmış" (gerekçeli). Model 13 geçersiz parça kimliği yazdı,
  hepsi silindi; 1 anlatım maddesi kaynaksız diye işaretlendi.
- **Denetim bu sefer 0 madde işaretledi** (38/38 madde değerlendirildi; 2 uyarı birebir alıntı olmadığı için reddedildi).
  Önceki iki çalıştırmada 3'er gerçek sorun bulmuştu: düşünmeli denetim çalıştırmadan çalıştırmaya tutarsız.
  Reddedilen uyarılar artık teşhis için `stats.scan_rejected_items` içinde saklanıyor (föyde gösterilmez).
- Bu değerlendirmede bulunan ve düzeltilen küçük kusurlar (tam föy bunlardan sonra yeniden üretilmedi):
  Vikipedi düz metnindeki `{\displaystyle …}` ve satır satır dağılmış formül parçaları birleştirildi;
  sadakat notunda "x = 2'deki" gibi Türkçe ekin ifadeye karışması giderildi. Testler: 106, OK.

## 5g. Föy denetiminin tutarsızlığı: tekrarlı turlar ve gemma4:12b kıyası (16.10.2026 06:30–09:00)

Betik: `denetim_kiyas.py` (uygulamadaki `Builder.scan` aynen). Değerlendirme seti: 13.10 dersinden iki föy;
elle doğrulanmış sorunlu maddeler — föy A (`kisisel/foy-13-10-2026-sadakat`): A2, T6 (geri yayılım = GD uzantısı),
A5, O5 (Delta İtalyanca/Latince…), A6 ("sel yüzeyler"), C1 (tek fonksiyon y eksenine simetrik); föy B
(`…-sadakat-2`): A3, A4 (merkezi fark / +h geriye dönük), T7 (+h geriye dönük), O4 (2²/2 = 2). Puan madde
düzeyinde (aynı maddede başka bir sorunun işaretlenmesi de "yakalandı" sayılır — aşağıda düzeltilerek verildi).
Sonuçlar: `kisisel/denetim-kiyas/*.json`.

| Yöntem | A turları | B turları | Yanıtsız kalan tur | Süre/föy |
|---|---|---|---|---|
| qwen3.5:9b düşünmeli (tek çağrı, 16K) | 1/6, **yanıtsız** | 4/4, **yanıtsız** | 2/4 | 4–8 dk |
| gemma4:12b düşünmeli (FA kapalı) | 4/6, **yanıtsız** | 2/4, 2/4 | 1/4 | 2–6 dk |
| qwen düşünmeli, 10'luk gruplar | (durduruldu: her grup bütçeyi bitirdi, ~3,5 dk/çağrı) | | — | >30 dk |
| qwen düşünmesiz + şemada "kontrol" alanı, tek tur | 4/6, 4/6, 3/6 | 4/4, 3/4, 4/4 | 0/6 | ~1,6 dk |
| **Ürün ayarı:** aynısı, 2 tur birleşim | 3/6, 3/6 (sorun düzeyinde) | 4/4, 4/4 | 0/4 | 3,2–5,3 dk |

- Tutarsızlığın asıl nedeni: **düşünme modunun bütçeyi bitirip JSON yazmaması** ("done_reason: length", boş yanıt);
  "0 işaret" sonuçları "sorun yok" değil, denetim başarısızlığıydı. "Kısa düşün" talimatı etkisiz.
- gemma4:12b (Apache-2.0, Ollama `gemma4:12b` 7,5 GB, indirildi) bu GPU'da **Flash Attention çekirdeğinde çöktü**
  (`CUDA error: shared object initialization failed`, `fattn-mma-f16`, Ollama HTTP 500); `OLLAMA_FLASH_ATTENTION=0` ile
  çalıştı. A'da daha isabetli, B'de qwen'den zayıf, düşünme bütçesi sorunu onda da var. Sunucu genelinde FA kapatma
  ve model değiştirme maliyeti nedeniyle **benimsenmedi**; ana model qwen3.5:9b.
  Kullanıcı onayıyla `gemma4:12b` Ollama API'siyle (`/api/delete`) silindi; `models/ollama` 14 GB → 6,2 GB,
  yalnız `qwen3.5:9b` kaldı. Yeniden kıyas gerekirse `denetim_kiyas.py --model gemma4:12b --fa-kapali` öncesinde indirilmeli.
- Benimsenen: `SCAN_THINK = False`, `SCAN_ROUNDS = 2`, `SCAN_GROUP = 10`. Uyarıda "2/2 denetim turunda" gibi
  güven bilgisi; aynı sorun iki kez gösterilmez; yanlış kimlikle gelen ama başka maddede birebir geçen alıntı
  doğru maddeye taşınır; başarısız çağrı bir kez yeniden denenir ve föy bunu yazar.
- Kalan zayıflıklar: C1 ("y eksenine göre simetrik") ve O5 ürün ayarında iki çalıştırmada da kaçtı (tek turlu
  denemelerde bir kez yakalanmıştı). Föy başına 2–5 fazladan işaret: bir kısmı gerçek (ör. "en küçük kareler kesişim
  noktası bulur", "ilk 4 terim dahil" tutarsızlığı), bir kısmı titizlik ("a genelde 0 alınır"), en az biri yanlış alarm
  (A1: sin x terimleri aslında doğru). Denetim hâlâ "kesin değil" olarak sunuluyor.
- Ürün değişiklikleri (bu adım): `llm.chat` Ollama HTTP hatalarını açık `ModelError`'a çevirir; denetim ve ek araştırma
  gibi isteğe bağlı adımlarda model hatası föyü düşürmez (uyarı yazar); ayrıştırma hatalarının sonu teşhis için
  `stats.parse_failures`'ta saklanır. Testler: 110, OK.

## 5h. Föy doğruluğu: kanıtla doğrula → düzelt hattı (16.10.2026 11:30–12:05) — HEDEF HENÜZ KARŞILANMADI

Girdi: kullanıcının uygulamada aldığı gerçek föy `ornekler/kullanici-foyu-2026-10-16.md` (veri olarak okundu).
Doğrulanmış hatalar: "tüm optimizasyon algoritmaları GD'dir", "GD Hessian kullanır, min/maks arar", "Δ eksenler arası
fark / çarpım", "0.25 köke uzaklık" (artıktır; |1.5−√2|≈0.0858), "Δy/Δx çarpım", "doğruluk ∝ terim sayısı",
"türev 'fark' demektir", Hessian testinde tekil/belirsiz karışıklığı, "Taylor tarafından adlandırıldı".

**Durum: doğrulama hattı prototiptir, ürün akışına BAĞLANMADI.** `worksheet.Builder.build` hâlâ eski `scan()`
uyarılarını üretir; kullanıcının gördüğü föyde yanlış cümleler + uyarılar sorunu devam etmektedir.
Bu turdaki sunum değişiklikleri (aşağıda) doğruluk düzeltmesi değildir.

Gerçek denemeler (qwen3.5:9b, kendi sunucu 127.0.0.1:11436, 8K bağlam; kullanıcı motoru 11435'e istek yok):
| Çalıştırma | Klasör (`ornekler/dogrulama/`) | Sonuç |
|---|---|---|
| 14 madde, web | `sonuc-20261016-1150` | **0 düzeltme**; 3 kanıt yetersiz, 11 denetlenmedi (tek ortak bütçe 3 maddede bitti, 4× HTTP 429) |
| 4 madde, önbellek | `sonuc-20261016-1157` | **0 düzeltme**; 4 kanıt yetersiz (Y2 doğru kanıt "başlık:" önekiyle reddedildi; Y4 hesap `=` içerdi) |
| 4 madde, önbellek | `sonuc-20261016-1158` | **0 düzeltme**; **Y4 yanlış cümle "doğrulandı"** (bağlamdaki doğru hesaplar denetlendi) |
| 4 madde, önbellek (son) | `sonuc-20261016-1201` | **0 düzeltme**; Y2 çözülemedi (ekte), Y4 kaçırıldı (`hesap_tutarli`), D1 ve D9 korundu |

Son çalıştırma: 33.9 sn, 4 model çağrısı (biçimlendirme 2, yargı 1, düzeltme 1), 0 web isteği, VRAM tepe 6814 MiB,
boş RAM en düşük 2194 MB. Y2: çelişki kararı birebir ama ilgisiz parçalara dayandı ("should not be confused with
local search…"); üretilen düzeltme içerik olarak doğruydu ama yeniden biçimlendirmede birim dönmediği için
denetlenemedi → ekte kaldı. Y4: model cümlenin yorum iddiasını biçimlendiremedi.

Giderilen altyapı kusurları (testli): `eval` yok — AST izin listesiyle SymPy nesnesi kurma, düğüm/üs/faktöriyel
sınırı, ayrı süre sınırlı alt süreç (öldür/yeniden başlat); örnekleme yalnız karşı örnek arar (eşitse belirsiz);
kesin ondalık (0.1+0.2=0.4 yanlış) ile açık işaretli yaklaşık iddia ayrımı; hem iddia edilen değer hem hesap ifadesi
bağlama dayanmalı (uydurma 2+2=4 reddedilir); yalnız hesaplar tutarlıysa "doğrulandı" yerine `hesap_tutarli`;
kanıt yetersizliği içerik silmez; aşama bazlı bütçe (biçimlendirme/yargı/düzeltme/web/süre) — web biterse hesaplar
sürer; ilgisiz arama sonucu (ör. "Minimum wage…") kanıt olmaz; BM25 ile iddiaya göre paragraf; alıntı öneki
temizliği ve çok satırlı alıntının parça parça birebir denetimi; ders kaynağı ile düzeltme kaynağı ayrı; altın/not
alanlarının modele gitmediği test edildi; GPU koruması (kullanıcı motorunda model yüklüyse bekler).

Kalan nedenler (çözülmedi): (1) hangi iddianın hesaplanacağını/aranacağını aynı model seçiyor ve yorum
cümlelerinde yanlış biçimlendiriyor; (2) birebir alıntı şartı alıntının iddiayla ilgili olmasını garanti etmiyor;
(3) Vikipedi kapsamı/429; (4) düzeltilmiş cümlenin yeniden biçimlendirmesi kırılgan.

Sunum değişiklikleri (doğruluk düzeltmesi değildir): "öğretmenini esas al", "konuşma tanıma hatası olabilir",
"kendin kontrol et" ifadeleri kaldırıldı; üretilmiş örnekte "kaynakta yok" notu gösterilmiyor. Eski ⚠ denetim
uyarıları gizlenmedi.

Dosyalar (gerçek disk konumu: `C:\Users\Necati\Documents\Codex\2026-10-15\referenced-chatgpt-conversation-this-is-an\outputs\DersYazi\`):
`verify.py`, `sympy_worker.py`, `dogrulama_kiyas.py`, `test_verify.py` (yeni); `worksheet.py`, `requirements*.txt`
(sympy 1.14.0, mpmath 1.3.0 — BSD) değişti; `ornekler\dogrulama\fixture-2026-10-16.json` (9 hatalı + 5 temiz;
D8 kullanıcı uyarısıyla hatalı olarak etiketlendi, Y7 çıkarıldı); `ornekler\dogrulama\kanit-onbellek\`;
raporlar `ornekler\dogrulama\sonuc-*\rapor.md` ve tam denetim kaydı `ham-kayit.json`.

Test: `.venv\Scripts\python.exe -m unittest discover -s .` → **134 test, OK** (~10 sn).

Sonraki tek somut iş: iddia biçimlendirmesini modelden bağımsızlaştırmak için yorum cümlelerinde sayıların
anlamını (değer/artık/uzaklık/oran) cümle kalıbından çıkaran küçük belirlenimci çıkarıcı ve alıntı–iddia
ilgililik eşiği (BM25 skoru) ekleyip yalnız 4 maddelik setle yeniden ölçmek; başarılı olmadan ürüne bağlamamak.

## 5i. Yanlış yorum ve ilgisiz alıntı koruması (16.10.2026 12:50–13:10, Claude yerel oturum) — DÜZELTME HEDEFİ HÂLÂ KARŞILANMADI

Kapsam: yalnız `verify.py`, `test_verify.py`, `dogrulama_kiyas.py` ve rapor. `app.py`/`ui.py`/`mascot.py`/assets'e
dokunulmadı (Codex'in marka/maskot işi). `sympy_worker.py` değişmedi. Codex'in `SympyChecker.close` düzeltmesi korundu.
Değişiklik öncesi kopya: `yedekler\kaynak-2026-10-16-verify-oncesi\`. `worksheet.Builder.build` hâlâ eski `scan()` yolunda.

Ne değişti (alan bağımsız kurallar, fixture ezberi yok):
- **Yorum denetimi.** Cümle bir sayıya anlam yüklüyorsa (fark/göreli hata/artık/oran) türü KOD bulur
  (`verify.interpretations`, Türkçe+İngilizce kalıp, aynı yan cümlede "değil" olumsuzluğu). Model yalnız yuvaları
  (`yorumlar`: tahmin, gercek, fonksiyon, degisken, pay/payda) doldurur; formülü kod kurar (`interpretation_expression`),
  SymPy denetler. Kodun bulmadığı türde model yuvası yok sayılır (model daha kolay bir anlam seçemez). "Bu sonuç/değer"
  gönderiminde değer bağlamdaki son "= sayı"dan alınır, modelden değil. Anlam hesaplanamazsa yeni durum
  `yorum_denetlenemedi`: cümle korunur, `hesap_tutarli`/`dogrulandi` denmez.
- **Bağlam hesabının tekrarı** (`restates_context`) cümlenin kanıtı sayılmaz (`kapsam: baglam`). Doğru bağlam hesabı
  yanlış yorum cümlesini aklayamaz.
- **Alıntı–iddia ilgi kapısı** (`quote_relevance`): birebir alıntı ayrıca iddianın öznesini (ilk arama terimi) içeren
  parçalarda, kanıtta geçen ayırt edici iddia terimlerinin en az yarısını (en az 2) kapsamalı; yoksa `yetersiz`.
  Gerekli koşuldur, yeterli değildir; BM25 yüksekliği ispat sayılmaz.
- Kıyas raporu ölçüleri: hatalı temizlendi / temiz korundu / yanlış doğrulandı / çözülemedi.

Testler: `test_verify` 24 → 38 (`-W error::ResourceWarning` ile OK). Yeni karşı örnekler: Y4'ün 3 paraphrase'i ve
12:01 gerçek Qwen biçimlendirmesinin kendisi; fixture dışı sayılar (x³=5, x₀=2, f(2)=3); doğru yorumlar (artık,
gerçek farkı 0.0858) korunur; model anlam değiştiremez/değer uyduramaz; düzeltme aynı yanlış anlamı taşırsa kabul
edilmez; gerçek 4 parçalı Y2 alıntı yapısı reddedilir, ilgili alıntı kabul edilir; biçimlendirme isteminde fixture
cümlesi/notu yok. Eski `test_calculations_alone_never_mark_sentence_verified` artık `yorum_denetlenemedi` bekliyor
(eski beklenti zayıf davranışı sabitliyordu). Tüm paket: **148 test OK** (~18 sn). Not: başka bir modülün testinde
kapanmamış soket ResourceWarning'i "Exception ignored" olarak görünüyor (verify değil; bu işte incelenmedi).
Gerçek önbellek kontrolü: 12:01'deki Y2 alıntısı yeni kapıdan geçmiyor (2/5 terim).

Gerçek deneme (tek, kısa): `ornekler\dogrulama\sonuc-20261016-1305\` (rapor.md, ham-kayit.json, elle-etiket.json).
qwen3.5:9b, kendi sunucu 11436, yalnız önbellek, 39.6 sn, 4 model çağrısı, 0 web, VRAM tepe 6816 MiB, boş RAM en
düşük 1227 MB (öncekinden düşük). Kullanıcı motoru 11435'e istek yok; başlangıçta GPU 163 MiB, yüklü model yoktu.
| Madde | Altın | Sonuç | Ölçü |
|---|---|---|---|
| Y2 GD/Hessian | yanlış | `kanit_yetersiz` — çelişki yine ilgisiz alıntıya dayandı, kapı reddetti | çözülemedi (onaylanmadan kaldı) |
| Y4 artık/uzaklık | yanlış | yorum çelişkisi SymPy ile bulundu (0.0858 ≠ 0.25); Qwen düzeltmesi aynı yanlış anlamı taşıdı, yeniden biçimlendirme birim döndürmedi → `cozulemedi` | çözülemedi (ekte) |
| D1 Taylor | doğru | `hesap_tutarli` (model anlamsız yorum yuvaları yazdı, kod yok saydı) | temiz korundu |
| D9 backward diff. | doğru | `kontrol_disi` (model bu kez olgu_var=false dedi) | temiz korundu |

Özet: yanlış doğrulandı **0** (11:58'de 1, 12:01'de 1), temiz korundu 2/2, hatalı temizlendi **0**, çözülemedi 2.
Koruma iyileşti ama **düzeltme başarısı yok**; ürüne bağlanmadı. 4 örnekle genelleme yapılmamalı.

Kalan nedenler: (1) yorum çelişkisinde düzeltmeyi model yazıyor ve yanlış anlamı koruyor; (2) düzeltilmiş cümlenin
yeniden biçimlendirmesinde model birim döndürmüyor, ham yanıt kaydedilmiyor; (3) Y2 gibi birden çok alt iddiayı
tek İngilizce cümlede toplayan biçimlendirme kanıtla eşleşmiyor (atomik alt iddialara bölme gerekli); (4) olgu_var
kararı koşudan koşuya değişiyor (D9).

Sonraki tek somut iş: yorum çelişkisinde düzeltmeyi modelden almadan belirlenimci üretmek — aynı yuvalarla diğer
anlam türlerini (artık/fark/göreli hata) hesaplayıp değerle tutarlı çıkanı seçmek, Türkçe şablon cümleyi kodla kurmak
("Bu sonuç (0.25) f(1.5) değeridir, yani artıktır; tahminin gerçek değerden farkı |1.5 − √2| ≈ 0.0858'dir") ve
yeniden doğrulamayı aynı yuvalarla yapmak; ham model yanıtlarını kayda eklemek. Sonra yalnız aynı 4 maddeyle
bir gerçek kıyas; başarılı olmadan ürüne bağlamamak.

## 5j. Yorum çelişkisinde belirlenimci düzeltme (16.10.2026 13:00–13:20, Claude yerel oturum) — İLK GERÇEK DÜZELTME (1 madde)

Kapsam: yalnız `verify.py`, `test_verify.py`, `dogrulama_kiyas.py`, rapor ve bu dosya. `app.py`/`ui.py`/`mascot.py`/
assets'e ve `sympy_worker.py`'ye dokunulmadı. **Ürüne BAĞLI DEĞİL** (`worksheet.Builder.build` hâlâ eski `scan()`).
Devir: `CODEX-SON-DEVIR.md`.

Ne değişti (`verify.py`):
- Yorum (`kapsam: yorum`) çelişkisinde düzeltmeyi **model yazmaz** (`Verifier.decide_meaning`, `Verifier.meaning_fix`).
  Aynı yuvalarla (tahmin, gercek, fonksiyon, degisken) diğer türler (`ALTERNATIVES`: artik/fark/goreli_hata) hesaplanır;
  değerle SymPy'de tutarlı çıkan **tek** tür seçilir. Hiçbiri tutarlı değilse veya birden çoğu tutarlıysa `cozulemedi`
  (dürüst; tahmin yok). Türkçe cümle `_phrases` şablonundan kurulur; iddia edilen anlamın gerçek değeri SymPy çelişki
  ayrıntısından (`_computed_value`) alınır, `_rounded` ile 3 anlamlı basamağa yuvarlanır.
- Yeniden doğrulama modele yeniden biçimlendirme yaptırmadan, aynı yuvalarla: şablon cümlenin anlamlarını
  `interpretations` KOD olarak yeniden tanımalı ve her yuva SymPy'de tutarlı olmalı; aksi halde `cozulemedi`.
- `interpretations` artık `;` ile ayrılan yan cümleleri ayrıca tarar (bir cümlede hem fark hem göreli hata).
- `_function_slot`: model fonksiyon yuvasına "f(x) = …" yazarsa ad/ifade ayrılır; yuva boşsa bağlamdaki "f(x) = …"
  tanımı kullanılır (belirlenimci). `interpretation_expression(slot, context)` bunu kullanır.
- `Verifier.raw`: her model yanıtı ham olarak (aşama, birimler, süre, yanıt; çözümlenemeyenler dahil). `dogrulama_kiyas.py`
  bunu `ham-kayit.json → model_yanitlari` altına yazar; rapor düzeltme yolunu ve denenen türleri gösterir.

Testler: `test_verify` 38 → 50. Yeni `MeaningCorrectionTests` (fixture dışı sayılar: x³=5/x₀=2, x²=3/x₀=1.8, x²=7/x₀=2.5
negatif artık, göreli hata 4.2/4; Türkçe+İngilizce paraphrase'ler; uygun tür yok → çözülemedi; iki tür tutarlı → çözülemedi;
şablon yeniden tanınmazsa başarı yok; altın/not/kaynak modele gitmez; ham yanıt kaydı; kural kodunda fixture sayıları/
ifadeleri sabit yok). İki eski test yeni davranışa göre değişti: yorum çelişkisinde model düzeltmesi artık kullanılmıyor.
Tüm paket `.venv\Scripts\python.exe -W error::ResourceWarning -m unittest discover -s .` → **160 test OK** (~22 sn);
çıktı `ornekler\dogrulama\sonuc-20261016-1317\test-sonucu.txt`. Başka modülden kapanmamış soket uyarısı sürüyor (önceden de vardı).

Gerçek deneme (tek): `ornekler\dogrulama\sonuc-20261016-1317\` (rapor.md, ham-kayit.json + model_yanitlari, elle-etiket.json,
test-sonucu.txt). qwen3.5:9b, kendi sunucu 11436 (iş sonunda kapandı), yalnız önbellek, 44.7 sn, 2 model çağrısı
(biçimlendirme 1, yargı 1, düzeltme 0), 0 web, VRAM tepe 6665 MiB, boş RAM en düşük **838 MB** (düşük; başka uygulamalar açık).
Başlangıçta GPU 12 MiB, kullanıcı motoru 11435 kapalıydı.
| Madde | Altın | Sonuç | Ölçü |
|---|---|---|---|
| Y2 GD/Hessian | yanlış | model "çelişiyor" dedi ama alıntıyı "..." ile birleştirdi → birebir değil → `kanit_yetersiz` | çözülemedi (onaylanmadan kaldı) |
| Y4 artık/uzaklık | yanlış | yorum çelişkisi bulundu; şablon: "Bu sonuç (0.25), x = 1.5 için x² − 2 değeridir, yani artıktır; tahminin gerçek değerden farkı ise \|1.5 − √2\| ≈ 0.0858 olur." aynı yuvalarla yeniden doğrulandı → `duzeltildi` | **hatalı temizlendi** (Claude matematik teyidi; öğretmen teyidi yok) |
| D1 Taylor | doğru | model bu kez taylor() yerine elle açılım + .subs yazdı → hesaplar belirsiz → `kontrol_disi` | temiz korundu |
| D9 backward diff. | doğru | `kanit_yetersiz` (önbellekte kanıt yok) | temiz korundu |

Özet: hatalı temizlendi **1/2** (ilk kez), yanlış doğrulandı 0, temiz korundu 2/2, çözülemedi 1. Yalnız 4 maddeyle ve tek
koşuyla genelleme yapılamaz; Y4 dışındaki 7 hatalı madde hiç denenmedi. **Ürüne bağlanmadı.**

Kalan nedenler: (1) Y2 gibi kavram cümlelerinde alıntı birebir değil/ilgisiz; iddia atomik alt iddialara bölünmüyor;
(2) biçimlendirme koşudan koşuya değişiyor (D1: 13:05 hesap_tutarli, 13:17 kontrol_disi); (3) şablon gösterimi: model
"f(x) =" öneki vermezse "f(1.5)" yerine "x = 1.5 için x² − 2" yazılıyor; (4) şablon yalnız sayının anlamını söyler,
cümlenin varsa başka iddiaları düşer (kayıtta `degisiklik` alanında yazar).

Sonraki tek somut iş: Y2 türü kavram cümleleri için iddiayı kodla atomik alt iddialara bölmek (ör. "GD gradyan kullanır",
"GD Hessian kullanır", "yerel maksimum bulur") ve her biri için birebir + ilgili alıntı aramak; sonra yalnız aynı 4 maddeyle
bir gerçek kıyas. Başarı olmadan ürüne bağlamamak.

## 6. Bilinen eksikler

- Gerçek ders yalnız transkriptle denendi (5b); gerçek okul PDF'i ve öğrenci notuyla birlikte deneme yok.
- Föy denetimi (düşünme modu) yaklaşık 4–5 dk ekliyor ve hataların bir kısmını kaçırıyor (5c); kavramsal
  örneklerde sayı/formül denetimi yapılamıyor. Transkript hataları hâlâ föye geçebiliyor, yalnız işaretleniyor.
- Bellek baskısı: Deneme B'de boş sistem RAM'i 142 MB'ye düştü (Opera vb. açık; model VRAM'de). Uzun işlerde
  sayfalama/yavaşlama riski; föy başlamadan boş RAM kontrolü ve uyarı eklenmeli.
- Masaüstü kontrol aracı DersYazı penceresini tanımıyor (Başlat menüsü kaydı yok); arayüz denemesi `ui_e2e.py`
  ile gerçek pencerede programatik tıklamayla yapıldı, insan eliyle tıklama denemesi yapılmadı.
- Hesap kontrolü yalnız açık sayısal eşitlikleri doğrular; sembolik türev, formül dönüşümü ve sözel
  sonuçlar doğrulanmaz. Türkçe yazım hataları otomatik düzeltilmez.
- Uygulama penceresinde gerçek modelle föy akışı elle tıklanarak denenmedi (iş parçacığı ve ekran testleri
  otomatik; gerçek üretim `foy_e2e.py` ile aynı `llm.prepare`/`build_worksheet` yolundan geçti).
- İnternet araştırması yalnız Vikipedi (tr/en); genel web, ders kitabı/üniversite sayfaları yok. Wikimedia anonim
  hız sınırı (429) arada bir sayfayı kaçırtıyor. User-Agent'ta iletişim adresi yok — Wikimedia kullanıcı aracısı
  kuralı gereği dağıtımdan önce proje adresi/iletişim eklenmeli (kullanıcının e-postası izinsiz konmadı).
- Vikipedi metni CC BY-SA 4.0: föy özet + bağlantı + lisans verir; föy satılık bir paket olacaksa uyarlanmış
  içerik için "aynı lisansla paylaş" yükümlülüğü hukuken incelenmeli.
- Sorgular terim adlarından üretildiği için bir terim alışılmadık bir özel ad içerirse internete gidebilir;
  rakam/uzunluk filtresi var, ad tanıma filtresi yok.
- DOCX/PPTX, görsel PDF/OCR, fotoğraf yok. PDF okuma kaynak eklenirken UI iş parçacığında yapılır;
  çok büyük PDF'te kısa donma olabilir.
- Föy kalıcı kütüphanesi/otomatik kurtarma yok; kullanıcı kaydetmezse pencere kapanınca kaybolur (uyarı var).
- Formül/sayısal doğruluk modelce garanti edilmez; sözcük örtüşmesi kaba bir işarettir.
- Uygulama çökerse kendi başlattığı Ollama sunucusu açık kalabilir (yalnız 127.0.0.1); sonraki açılışta yeniden kullanılır.
- Föy hazırlanırken pencerede yalnızca "Adım n/3" ve süre var; uzun derslerde parça sayısı kadar adım görünür.

## 7. Sonraki adımlar

1. (Yapıldı, 5c) Üç düzeyli örnek etiketi, sayı/formül denetimi, otomatik atıf, ders kaydı uyarısı, düşünmeli denetim.
2. Küçük sağlamlaştırmalar: föy öncesi boş RAM kontrolü/uyarısı; arayüzde TXT kaynağını "ders kaydı"
   olarak işaretleme (DersYazı TXT çıktısı otomatik tanınabilir); denetimin kaçırdığı türler için deterministik
   kontroller (ör. ileri/geri fark tanımı gibi sık kavram hataları için küçük bir doğrulanmış kural listesi).
3. Aynı gerçek ders + öğretmen PDF'i + öğrenci notu ile deneme; uygulama penceresinde 04 kartından elle
   uçtan uca deneme. `gemma4:12b` ile aynı kaynaklarda kıyas (özellikle denetim isabeti ve süresi).
4. (İlk sürüm yapıldı, 5d) Aşama 2: Vikipedi tr/en ile ayrı "Ek araştırma" bölümü. Sıradaki genişletmeler:
   - (5e, 5f) Uygulama penceresinden internetli föy iki kez üretildi. Kalan: kullanıcının Baslat.bat ile açtığı
     pencerede elle bir kez denemesi. (5g) Denetim tutarsızlığı büyük ölçüde azaltıldı (yanıtsız tur yok; B 4/4 sabit, A 3/6 sabit): şemalı 2 turlu denetim; kalan iş, kaçan
     kavram hataları (ör. tek fonksiyon simetrisi) için küçük doğrulanmış kural listesi ve fazladan işaretlerin azaltılması.
   - User-Agent'a proje adresi/iletişim (kullanıcı kararı); Wikimedia hız sınırına göre istek sayısını azaltma
     (arama + sayfa tek çağrıda, sonuçları yerelde önbelleğe alma).
   - Genel web: yerel SearXNG (AGPL-3.0, ayrı süreç; Windows'ta kurulum yükü ölçülmeli) + Trafilatura
     (Apache-2.0) ile sayfa okuma; güvenilir alan adı listesi (üniversite, açık ders kitapları, resmî belgeler);
     her sayfanın lisansı ayrıca kaydedilir. Ücretli arama API'si yok.
   - Ek araştırmada kaynakta olmayan yorum cümlelerini (5d'deki "yerel arama…" gibi) yakalamak için
     madde–sayfa örtüşme denetimi; derste anlatılanla çelişen web bilgisini işaretleme.
