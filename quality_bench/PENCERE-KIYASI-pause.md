# Konuşma aralarında pencereleme deneyi — 18 Ekim 2026

Temel: 12 saniyelik çekirdek. Aday: 16–26 saniye içinde en son en az 200 ms düşük enerjili aralık; yoksa üst sınırda kesim. İki saniye bağlam payı; hiçbir ses örneği filtrelenmez. Dil geçişinde bölme korunur. Aday üretim varsayılanı değildir.

| Grup | Temel hata/sözcük | Aday hata/sözcük | Temel WER | Aday WER |
|---|---:|---:|---:|---:|
| source-20 | 42/424 | 43/424 | 9.91% | 10.14% |
| derived-4 | 10/113 | 32/113 | 8.85% | 28.32% |
| fleurs-tr | 7/90 | 7/90 | 7.78% | 7.78% |
| libri-clean | 9/95 | 9/95 | 9.47% | 9.47% |
| libri-other | 4/89 | 4/89 | 4.49% | 4.49% |
| media-tr | 22/150 | 23/150 | 14.67% | 15.33% |
| stress-noise | 6/43 | 6/43 | 13.95% | 13.95% |
| stress-switch | 4/70 | 26/70 | 5.71% | 37.14% |

## Değişen örnekler

### fleurs-tr-02 — hata farkı +0
- Referans: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen ASUS Eee PC, 2007 Taipei BT Ayında sıcak bir gündem maddesi haline geldi.
- Temel: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen Asus EEE PC 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi.
- Aday: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen Asus EEE PC, 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi.

### media-tr-01 — hata farkı +1
- Referans: kısıtlamalarına geri mi dönsek deniliyor şimdi ekonomik tedbirler bunu hani biz neleri geride bıraktık on bir mart'ta birinci vaka açıklandıktan sonra neleri yaşadık biz kepenkler indi dükkanlar kapandı işte günlük o
- Temel: ...kısıtlamalarına geri mi dönsek deniliyor. Şimdi ekonomik tedbirler, biz neleri geride bıraktık? 11 Mart'ta birinci vaka açıklandıktan sonra neleri yaşadık biz? Kepenkler indi, dükkanlar kapandı, işte günlük otobüs...
- Aday: ...kısıtlamalarına geri mi dönsek deniliyor. Şimdi ekonomik tedbirler, biz neleri geride bıraktık? 11 Mart'ta birinci vaka açıklandıktan sonra neleri yaşadık biz? Kepenkler indi, dükkanlar kapandı, günlük otobüsler...

### media-tr-03 — hata farkı +0
- Referans: kaybedecek tek bir günü dahi yoktur kendi yolumuzda devam etmekten başka çaremiz kalmamıştır cumhurbaşkanı erdoğan'ın meclis açılışına verdiği mesajın ardından gözler sınırda ankara harekat kararlılığını sürdürürken
- Temel: Bunu da kaybedecek tek bir günü dahi yoktur. Kendi yolumuzda devam etmekten başka çaremiz kalmamıştır. Cumhurbaşkanı Erdoğan'ın meclis açılışına verdiği mesajın ardından Gözler sınırda Ankara harekat kararlılığını sürdürürken
- Aday: Bunu da kaybedecek tek bir günü dahi yoktur. Kendi yolumuzda devam etmekten başka çaremiz kalmamıştır. Cumhurbaşkanı Erdoğan'ın meclis açılışına verdiği mesajın ardından gözler sınırda Ankara harekat kararlılığını sürdürürken

### media-tr-05 — hata farkı +0
- Referans: kaldırılan tedbirlerden sonraki yansımaları görüyoruz evet asıl daha da riskte olan geçtiğimiz hafta sonu daha büyük kısıtlamalar kaldırdık altmış beş yaş üstü insanların sokağa çıkmalarını ve  diğer bazı
- Temel: ...kaldırılan tedbirlerden sonraki yansımaları görüyoruz. Asıl daha da riskli olan geçtiğimiz hafta sonu. Daha büyük ısıtmalar kaldırdık. 65 yaş üstü insanların sokağa çıkmalarını ve diğer bazı tecrübelerini
- Aday: ...kaldırılan tedbirlerden sonraki yansımaları görüyoruz. Asıl daha da riskli olan geçtiğimiz hafta sonu. Daha büyük ısıtmalar kaldırdık. 65 yaş üstü insanların sokağa çıkmalarını ve diğer bazı tedbirlerini...

### stress-switch-01 — hata farkı +10
- Referans: Aynı ay, başka bir yolcu uçağı Meşhed'deki bir pisti aşarak bir duvara çarptı ve on yedi kişinin ölümüne neden oldu. THE DELAWARES ARE CHILDREN OF THE TORTOISE AND THEY OUTSTRIP THE DEER
- Temel: Aynı ay başka bir yolcu uçağı meşetteki bir pisti aşarak bir duvara çarptı ve 17 kişinin ölümüne neden oldu. The Delawares are children of the tortoise, and they outstrip the deer.
- Aday: aynı ay başka bir yolcu uçağı meşetteki bir pisti aşarak bir duvara çarptı ve on yedi kişinin ölümüne neden oldu İzlediğiniz için teşekkür ederim.

### stress-switch-02 — hata farkı +12
- Referans: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen ASUS Eee PC, 2007 Taipei BT Ayında sıcak bir gündem maddesi haline geldi. YOU SEE MY FRIEND IT'S AN ISSUE OF THE MONSTER THE NOTORIOUS NARWHALE
- Temel: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen Asus EEE PC 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi. You see, my friend, it's an issue of the monster, the notorious narwhal.
- Aday: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen Asus EEE PC, 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi.

Bu set ayar geliştirmede kullanıldı; bağımsız doğrulama değildir. WER anlam doğruluğu yüzdesi değildir. Yapay stres örnekleri ana 20 kayda dahil edilmez. Ayrıntı results/window-comparison-*.json.