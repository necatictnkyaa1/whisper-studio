# Whisper Studio — 20 kısa kayıtta kalite karşılaştırması

20 kaynak kayıt ve 4 ayrı yapay stres kontrolü. Kaynak ses: 200,825 saniye. Her model aynı yerel WAV dosyalarını kullanır; SHA256 ve kaynak satırları manifest.json içindedir. Referanslar ASR çıktılarından üretilmedi.

| Motor / ayar | Kaynak kayıt | Sözcük hatası / referans | WER ↓ | CER ↓ | TR sayı yazımı eşitlenmiş ek WER ↓ |
|---|---:|---:|---:|---:|---:|
| whisper-production | 20 | 42 / 424 | 9.91% | 6.05% | 7.75% |
| whisper-plain | 20 | 44 / 424 | 10.38% | 6.67% | 8.22% |
| whisper-plain-float16 | 20 | 42 / 424 | 9.91% | 5.92% | 7.75% |
| qwen-asr | 20 | 39 / 424 | 9.20% | 3.80% | 7.75% |

WER, ekleme + silme + değiştirme sayısının referans sözcük sayısına oranıdır; 100-WER genel anlam doğruluğu değildir. Ana WER sayıları kelimelere dönüştürmez. Ek gösterge yalnızca Türkçedeki bağımsız 0–9999 tamsayılarını sözle açar; yanlış sayıyı doğru kabul etmez. Türkçe harfler korunur. CER boşluksuz karakterler üzerinden hesaplanır.

| Motor | Grup | Hata / sözcük | WER ↓ |
|---|---|---:|---:|
| whisper-production | fleurs-tr | 7 / 90 | 7.78% |
| whisper-production | media-tr | 22 / 150 | 14.67% |
| whisper-production | libri-clean | 9 / 95 | 9.47% |
| whisper-production | libri-other | 4 / 89 | 4.49% |
| whisper-production | stress-switch | 4 / 70 | 5.71% |
| whisper-production | stress-noise | 6 / 43 | 13.95% |
| whisper-plain | fleurs-tr | 7 / 90 | 7.78% |
| whisper-plain | media-tr | 24 / 150 | 16.00% |
| whisper-plain | libri-clean | 9 / 95 | 9.47% |
| whisper-plain | libri-other | 4 / 89 | 4.49% |
| whisper-plain | stress-switch | 14 / 70 | 20.00% |
| whisper-plain | stress-noise | 7 / 43 | 16.28% |
| whisper-plain-float16 | fleurs-tr | 7 / 90 | 7.78% |
| whisper-plain-float16 | media-tr | 24 / 150 | 16.00% |
| whisper-plain-float16 | libri-clean | 8 / 95 | 8.42% |
| whisper-plain-float16 | libri-other | 3 / 89 | 3.37% |
| whisper-plain-float16 | stress-switch | 15 / 70 | 21.43% |
| whisper-plain-float16 | stress-noise | 6 / 43 | 13.95% |
| qwen-asr | fleurs-tr | 7 / 90 | 7.78% |
| qwen-asr | media-tr | 26 / 150 | 17.33% |
| qwen-asr | libri-clean | 3 / 95 | 3.16% |
| qwen-asr | libri-other | 3 / 89 | 3.37% |
| qwen-asr | stress-switch | 7 / 70 | 10.00% |
| qwen-asr | stress-noise | 3 / 43 | 6.98% |

| Mevcut akışa göre | WER farkı (puan) | Parça yeniden örnekleme %95 aralığı |
|---|---:|---:|
| whisper-plain | +0.47 | +0.00 … +1.11 |
| whisper-plain-float16 | +0.00 | -0.87 … +0.89 |
| qwen-asr | -0.71 | -4.55 … +2.99 |

Eksi fark daha az hata demektir. Aralık 20 parçanın eşli bootstrap yeniden örneklemesine dayanır; tüm ders kayıtları için garanti değildir. Sıfırı içeren aralıkla kesin üstünlük iddia edilmez.

Dört stres dosyası bağımsız doğal kayıt değildir; 20 kaynak kaydın ana ortalamasına katılmaz. Dil geçişi iki gerçek kaydın birleştirilmesidir; doğal ders içi kod değiştirmesi iddiası yoktur. Gürültü/yankı kontrollü olarak eklenmiştir.

Küçük bir ön eleme setidir. İngilizce bölümü sesli kitap; Türkçe bölümü okuma ve medyadır. Teknik üniversite dersi, belirli hoca aksanı ve uzun kayıtlar için sonuç genellenemez. Eğitim verisi örtüşmesi dışlanamadı. Ayarlar bu set üzerinde değiştirilirse bu sonuçlar geliştirme sonucu olarak kalır; yeni bağımsız doğrulama gerekir.

Süreler model yüklemesini dışarıda bırakır; arka plandaki indirme ve diğer Windows uygulamaları nedeniyle standartlaştırılmış hız testi sayılmaz.

Kaynak ve lisanslar: ATTRIBUTION.md. ASR kayıtları CC BY 4.0. Ayrı çeviri referansları FLORES-200: FLORES-LICENSE.txt (CC BY-SA 4.0). TranslateGemma ağırlığı Gemma lisansındadır; Qwen3-ASR ve Qwen3.5 Apache 2.0 lisansındadır.

## Ayrı çeviri karşılaştırması

chrF++ referans çeviriyle sözcüksel benzerlik puanıdır; anlam doğruluğu yüzdesi değildir. Hatalı veya kesilen yanıt boş çıktı olarak puana girer ve ayrıca sayılır.

| Motor | Ayrım | Cümle | Hatalı yanıt | chrF++ ↑ |
|---|---|---:|---:|---:|
| Argos-en-tr-1.5 | development | 10 | 0 | 51.50 |
| Qwen3.5-9B-current | development | 10 | 0 | 55.53 |
| Argos-en-tr-1.5 | holdout | 10 | 0 | 48.29 |
| Qwen3.5-9B-current | holdout | 10 | 0 | 56.04 |
| TranslateGemma-12B | development | 10 | 0 | 51.20 |
| TranslateGemma-12B | holdout | 10 | 0 | 54.56 |
| Qwen3.5-9B-plain-prompt | development | 10 | 0 | 54.94 |
| Qwen3.5-9B-plain-prompt | holdout | 10 | 0 | 51.66 |