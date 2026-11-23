# Konuşma aralarında pencereleme deneyi — 18 Ekim 2026

Temel: 12 saniyelik çekirdek. Aday: 8–12 saniye içinde en son en az 200 ms düşük enerjili aralık; yoksa üst sınırda kesim. İki saniye bağlam payı; hiçbir ses örneği filtrelenmez. Dil geçişinde bölme korunur. Aday üretim varsayılanı değildir.

| Grup | Temel hata/sözcük | Aday hata/sözcük | Temel WER | Aday WER |
|---|---:|---:|---:|---:|
| source-20 | 42/424 | 43/424 | 9.91% | 10.14% |
| derived-4 | 10/113 | 11/113 | 8.85% | 9.73% |
| fleurs-tr | 7/90 | 8/90 | 7.78% | 8.89% |
| libri-clean | 9/95 | 9/95 | 9.47% | 9.47% |
| libri-other | 4/89 | 4/89 | 4.49% | 4.49% |
| media-tr | 22/150 | 22/150 | 14.67% | 14.67% |
| stress-noise | 6/43 | 6/43 | 13.95% | 13.95% |
| stress-switch | 4/70 | 5/70 | 5.71% | 7.14% |

## Değişen örnekler

### fleurs-tr-02 — hata farkı +1
- Referans: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen ASUS Eee PC, 2007 Taipei BT Ayında sıcak bir gündem maddesi haline geldi.
- Temel: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen Asus EEE PC 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi.
- Aday: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya Türkiye'de sürülen Asus EEE PC 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi.

### fleurs-tr-03 — hata farkı +0
- Referans: Singapur Başbakan Yardımcısı Wong Kan Seng tarafından karşılandı ve Singapur Başbakanı Lee Hsien Loong ile ticaret ve terörizm konularını görüştü.
- Temel: Singapur Başbakan Yardımcısı Wong Kang Seng tarafından karşılandı ve Singapur Başbakanı Le Sen Long ile ticaret ve terörizm konularını görüştü.
- Aday: Singapur Başbakan Yardımcısı Wong Kang-Seng tarafından karşılandı ve Singapur Başbakanı Le Sen Long ile ticaret ve terörizm konularını görüştü.

### media-tr-01 — hata farkı +0
- Referans: kısıtlamalarına geri mi dönsek deniliyor şimdi ekonomik tedbirler bunu hani biz neleri geride bıraktık on bir mart'ta birinci vaka açıklandıktan sonra neleri yaşadık biz kepenkler indi dükkanlar kapandı işte günlük o
- Temel: ...kısıtlamalarına geri mi dönsek deniliyor. Şimdi ekonomik tedbirler, biz neleri geride bıraktık? 11 Mart'ta birinci vaka açıklandıktan sonra neleri yaşadık biz? Kepenkler indi, dükkanlar kapandı, işte günlük otobüs...
- Aday: ...kısıtlamalarına geri mi dönsek deniliyor. Şimdi ekonomik tedbirler, biz neleri geride bıraktık? 11 Mart'ta birinci vaka açıklandıktan sonra neleri yaşadık biz? Kepenkler indi, dükkanlar kapandı işte günlük

### stress-switch-02 — hata farkı +1
- Referans: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen ASUS Eee PC, 2007 Taipei BT Ayında sıcak bir gündem maddesi haline geldi. YOU SEE MY FRIEND IT'S AN ISSUE OF THE MONSTER THE NOTORIOUS NARWHALE
- Temel: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya sürülen Asus EEE PC 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi. You see, my friend, it's an issue of the monster, the notorious narwhal.
- Aday: Daha önce maliyet tasarrufu ve işlevsellik faktörleri için dünya çapında piyasaya Türkiye'de sürülen Asus EEE PC 2007 Taipei BT ayında sıcak bir gündem maddesi haline geldi. you see my friend it's an issue of the monster the notorious narwhal

Bu set ayar geliştirmede kullanıldı; bağımsız doğrulama değildir. WER anlam doğruluğu yüzdesi değildir. Yapay stres örnekleri ana 20 kayda dahil edilmez. Ayrıntı results/window-comparison-*.json.