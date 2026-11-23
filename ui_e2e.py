"""Gerçek uygulama penceresiyle uçtan uca föy denemesi (görünür pencere, gerçek model ve internet).

Kullanım: .venv\\Scripts\\python.exe ui_e2e.py <kaynak.txt> <çıktı klasörü>
04 kartına kaynak eklenir, "Çalışma kağıdı oluştur" düğmesine gerçek fare tıklaması gönderilir,
pencere görüntüleri ve durum metinleri zamanla kaydedilir, sonuç Markdown/HTML olarak kaydedilir.
Yalnızca dosya diyalogları ve "Ders kaydı mı?" sorusu otomatik yanıtlanır; geri kalan her şey uygulamanın kendisidir.
"""
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox
import app as appmod

def main():
    source, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    qapp = QApplication(sys.argv)
    window = appmod.Window()
    window.show()
    log, started = [], time.monotonic()
    def shot(name):
        window.centralWidget().ensureWidgetVisible(window.sheet_card, 0, 0)
        QApplication.processEvents()
        window.grab().save(str(out / f'{name}.png'))
    def note(event):
        log.append({'sn': round(time.monotonic() - started, 1), 'olay': event,
                    'adim': window.sheet_step.text(), 'durum': window.sheet_status.text(),
                    'sure': window.sheet_elapsed.text()})
    with patch.object(appmod.QMessageBox, 'question', return_value=QMessageBox.Yes):
        window.add_sources([source])  # TXT → "Ders kaydı mı?" sorusuna Evet
    note('kaynak eklendi: ' + window.source_list.item(0).text())
    shot('1-kaynak-eklendi')
    QTest.mouseClick(window.sheet_start, Qt.LeftButton)  # gerçek düğme tıklaması
    note('düğmeye tıklandı')
    counter = {'n': 0}
    def tick():
        counter['n'] += 1
        note('ara kayıt')
        if counter['n'] in (1, 4, 10):
            shot(f'2-calisiyor-{counter["n"]:02}')
    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(30000)
    def finished():
        timer.stop()
        note('bitti')
        shot('3-sonuc')
        window.sheet_view.grab().save(str(out / '4-foy-gorunumu.png'))
        for kind in ('md', 'html'):
            target = str(out / f'calisma-kagidi.{kind}')
            with patch.object(appmod.QFileDialog, 'getSaveFileName', return_value=(target, '')):
                window.save_sheet(kind)  # uygulamanın kendi kaydetme işlevi
        note('kaydedildi: ' + window.sheet_status.text())
        result = {'sheet': window.sheet is not None, 'banner': window.sheet_banner.text(),
                  'stats': window.sheet.stats if window.sheet else None,
                  'warnings': window.sheet.warnings if window.sheet else None,
                  'start_enabled_after': window.start.isEnabled() if window.path else None,
                  'sheet_start_enabled_after': window.sheet_start.isEnabled(), 'log': log}
        (out / 'pencere-gunlugu.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str),
                                                  encoding='utf-8')
        print(json.dumps({k: v for k, v in result.items() if k != 'log'}, ensure_ascii=False, default=str), flush=True)
        window.sheet_dirty = False
        window.close()  # kendi başlattığı föy motorunu kapatır
        qapp.quit()
    window.sheet_worker.finished.connect(lambda: QTimer.singleShot(500, finished))
    qapp.exec()

if __name__ == '__main__':
    main()
