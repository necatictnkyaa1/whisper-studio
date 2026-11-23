import sys
import time
from pathlib import Path
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QCloseEvent, QFontDatabase, QColor
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem,
    QFileDialog, QMessageBox)
from core import Segment, stamp, render, render_plain, transcribe

EXTENSIONS = {'.mp3', '.wav', '.m4a', '.mp4', '.mkv', '.mov', '.aac', '.flac', '.ogg', '.webm', '.wma', '.avi'}

class Worker(QThread):
    segment = Signal(object, int)
    status = Signal(str)
    failed = Signal(str)
    def __init__(self, options, target_language=None):
        super().__init__()
        self.options = options
        self.target_language = target_language
    def run(self):
        try:
            transcribe(*self.options, self.segment.emit, self.status.emit, self.isInterruptionRequested,
                       target_language=self.target_language)
        except Exception as e:
            self.failed.emit(str(e))

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        font = Path('C:/Windows/Fonts/segoeui.ttf')
        if font.exists():
            QFontDatabase.addApplicationFont(str(font))
        self.setWindowTitle('DersYazı · Yerel ders asistanı')
        self.resize(1100, 760)
        self.setAcceptDrops(True)
        self.path = None
        self.worker = None
        self.segments = []
        self.error = False
        self.dirty = False
        from ui import build_ui
        build_ui(self)
        self.started_at = None
        self.activity_message = ''
        self.activity_timer = QTimer(self)
        self.activity_timer.setInterval(1000)
        self.activity_timer.timeout.connect(self.refresh_activity)
    def set_status(self, message):
        self.status.setText(message)
        self.activity_message = message
        self.refresh_activity()
    def set_reading_mode(self, expanded):
        self.upload_card.setVisible(not expanded)
        self.settings_card.setVisible(not expanded)
        self.table.setMinimumHeight(240 if expanded else 400)
        self.expand_button.setText('Normal görünüme dön' if expanded else 'Genişlet')
        self.read_stop.setVisible(expanded and self.stop.isEnabled())
        QTimer.singleShot(0, lambda: self.centralWidget().verticalScrollBar().setValue(0))
    def show_completion(self):
        text = 'Çeviri tamamlandı — ders notların hazır' if self.worker.target_language else 'Yazıya dönüştürüldü — ders notların hazır'
        self.completion_banner.setText(text)
        self.completion_banner.show()
        self.progress.hide()
        self.completion_animation = QVariantAnimation(self)
        self.completion_animation.setDuration(700)
        self.completion_animation.setStartValue(QColor('#fff1b8'))
        self.completion_animation.setEndValue(QColor('#b6e2ce'))
        self.completion_animation.valueChanged.connect(lambda color: self.completion_banner.setStyleSheet(f'background-color:{color.name()};'))
        self.completion_animation.start()
    def refresh_activity(self):
        if self.started_at is not None:
            elapsed = int(time.monotonic() - self.started_at)
            self.elapsed_label.setText(f'Geçen süre · {elapsed // 60:02}:{elapsed % 60:02}')
    def animate_file_ready(self):
        if hasattr(self, 'file_animation'):
            self.file_animation.stop()
        self.file_animation = QVariantAnimation(self)
        self.file_animation.setDuration(650)
        self.file_animation.setStartValue(QColor('#fff1b8'))
        self.file_animation.setEndValue(QColor('#b6e2ce'))
        self.file_animation.valueChanged.connect(lambda color: self.file_feedback.setStyleSheet(f'background-color:{color.name()};'))
        self.file_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.file_animation.start()
    def changed(self, item):
        self.dirty = True
        if item.column() == 2:
            self.filter_rows()
    def filter_rows(self):
        query = self.search.text().strip().casefold()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)
            self.table.setRowHidden(row, bool(query) and (item is None or query not in item.text().casefold()))
    def confirm_discard(self):
        return not self.dirty or QMessageBox.question(self, 'Metni koru', 'Kaydedilmemiş metin var. Devam edip bu metni silmek istiyor musun?') == QMessageBox.Yes
    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Ses veya video seç', '', 'Medya (*.mp3 *.wav *.m4a *.mp4 *.mkv *.mov *.aac *.flac *.ogg *.webm *.wma *.avi)')
        if path:
            self.set_file(path)
    def set_file(self, path):
        path = Path(path)
        if path.is_file() and path.suffix.lower() in EXTENSIONS:
            try:
                size = path.stat().st_size / (1024 * 1024)
            except OSError as error:
                QMessageBox.warning(self, 'Dosya okunamadı', str(error))
                return
            self.path = path
            self.file_label.setText(path.name)
            self.file_feedback.setProperty('ready', True)
            self.file_feedback.style().unpolish(self.file_feedback)
            self.file_feedback.style().polish(self.file_feedback)
            self.ready_icon.show()
            self.file_feedback.setText(f'Ses/video dosyan seçildi ve hazır!  ·  {size:.1f} MB\nDosya bu bilgisayarda işlenir; internete yüklenmez.')
            self.start.setEnabled(True)
            self.animate_file_ready()
            self.status.setText('Dosyan hazır. İstediğin çıktı dilini seçip başlatabilirsin; gerisini otomatik ayarlayacağım.')
        else:
            QMessageBox.warning(self, 'Dosya açılamadı', 'Desteklenen bir ses veya video dosyası seç.')
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not (self.worker and self.worker.isRunning()):
            event.acceptProposedAction()
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls) == 1:
            self.set_file(urls[0].toLocalFile())
        else:
            QMessageBox.information(self, 'Tek kayıt', 'Bu sürümde her seferinde bir kayıt seç.')
    def busy(self, active):
        for widget in [self.open_btn, self.start, self.target_lang, self.offline]:
            widget.setEnabled(not active)
        self.stop.setEnabled(active)
        self.read_stop.setVisible(active and self.expand_button.isChecked())
        self.read_stop.setEnabled(active)
        if not active:
            self.start.setEnabled(self.path is not None)
    def begin(self):
        if not self.path:
            QMessageBox.information(self, 'Kayıt seç', 'Önce bir ses veya video dosyası seç.')
            return
        if not self.confirm_discard():
            return
        target = [None, 'tr', 'en'][self.target_lang.currentIndex()]
        self.segments = []
        self.search.clear()
        self.table.setRowCount(0)
        self.dirty = False
        self.error = False
        if hasattr(self, 'completion_animation'):
            self.completion_animation.stop()
        self.completion_banner.hide()
        self.progress.show()
        self.progress.setRange(0, 0)
        self.busy(True)
        self.started_at = time.monotonic()
        if hasattr(self, 'file_animation'):
            self.file_animation.stop()
            self.file_feedback.setStyleSheet('background-color:#b6e2ce;')
        self.elapsed_label.show()
        self.activity_timer.start()
        self.set_status('Başlatılıyor · model hazırlanırken ve ses okunurken biraz sürebilir.')
        options = (self.path, 'auto', None, 'auto', self.offline.isChecked())
        target = [None, 'tr', 'en'][self.target_lang.currentIndex()]
        self.table.setColumnHidden(3, not self.show_original.isChecked())
        self.worker = Worker(options, target)
        self.worker.segment.connect(self.append)
        self.worker.status.connect(self.set_status)
        self.worker.failed.connect(self.failed)
        self.worker.finished.connect(self.finished)
        self.worker.start()
    def append(self, segment, progress):
        self.segments.append(segment)
        row = self.table.rowCount()
        self.table.insertRow(row)
        state = (f'{segment.source_language} → çevrildi' if segment.translated else
                 f'{segment.source_language or "—"} · orijinal')
        for col, text in enumerate([stamp(segment.start), stamp(segment.end), segment.text, segment.original or segment.text, state]):
            item = QTableWidgetItem(text)
            if col < 2 or col >= 3:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, item)
        self.progress.setRange(0, 100)
        self.progress.setValue(progress)
    def cancel(self):
        self.worker.requestInterruption()
        self.stop.setEnabled(False)
        self.read_stop.setEnabled(False)
        self.set_status('Durduruluyor… model indirmesi veya mevcut bölüm tamamlanınca duracak.')
    def failed(self, error):
        self.error = True
        self.set_status('İşlem tamamlanamadı. Mevcut bölümleri kaydedebilirsin.')
        QMessageBox.warning(self, 'İşlem tamamlanamadı', 'Oluşan metin korunuyor. Gerekli dosyalar indirilemiyorsa internet bağlantısını kontrol edip tekrar deneyebilirsin.\n\n' + error)
    def finished(self):
        self.refresh_activity()
        self.activity_timer.stop()
        self.started_at = None
        self.busy(False)
        self.progress.setRange(0, 100)
        if self.error:
            self.status.setText('İşlem tamamlanamadı. Oluşan metin korunuyor; hata açıklamasını kontrol et.')
        if not self.error:
            cancelled = self.worker.isInterruptionRequested()
            self.progress.setValue(self.progress.value() if cancelled else 100)
            if not cancelled:
                self.show_completion()
            self.status.setText(('Durduruldu · kısmi metin korunuyor.' if cancelled else f'Tamamlandı · {len(self.segments)} bölüm. Metni düzenleyebilir ve kaydedebilirsin.'))
            if self.worker.target_language and not cancelled:
                translated_count = sum(s.translated for s in self.segments)
                result = f'Tamamlandı · {len(self.segments)} bölüm hazır. {translated_count} bölüm çevrildi; diğer bölümlerde orijinal metin korundu.'
                self.status.setText(result)
    def edited(self):
        return [Segment(s.start, s.end, (s.original or s.text) if self.export_original.isChecked()
                        else self.table.item(i, 2).text(), s.original) for i, s in enumerate(self.segments)]
    def copy(self):
        QApplication.clipboard().setText(render_plain(self.edited()))
    def save(self, srt):
        if not self.segments:
            QMessageBox.information(self, 'Metin yok', 'Önce bir kaydı transkripte çevir.')
            return
        suffix = '.srt' if srt else '.txt'
        path, _ = QFileDialog.getSaveFileName(self, 'Metni kaydet', str(self.path.with_suffix(suffix)), f'Metin (*{suffix})')
        if path:
            try:
                if not path.lower().endswith(suffix):
                    path += suffix
                content = render(self.edited(), True) if srt else render_plain(self.edited())
                Path(path).write_text(content, encoding='utf-8-sig')
                self.dirty = False
                self.status.setText('Kaydedildi · ' + path)
            except OSError as e:
                QMessageBox.warning(self, 'Kaydedilemedi', str(e))
    def closeEvent(self, event: QCloseEvent):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, 'İşlem sürüyor', 'Önce Durdur düğmesine bas ve işlemin durmasını bekle.')
            event.ignore()
        elif not self.confirm_discard():
            event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
