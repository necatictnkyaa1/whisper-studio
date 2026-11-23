import sys
import time
import re
from pathlib import Path
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QCloseEvent, QFontDatabase, QColor, QIcon
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
        self.setWindowTitle('Whisper Studio · Yerel ders asistanı')
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / 'assets' / 'whisper-mascot.png')))
        self.resize(1100, 760)
        self.setAcceptDrops(True)
        self.path = None
        self.worker = None
        self.batch_dialog = None
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
        percentage=re.search(r'%(\d{1,3})',message)
        if percentage:
            value=min(99,int(percentage.group(1)))
            self.progress.setRange(0,100);self.progress.setValue(value)
            self.companion.progress(value)
        self.companion.activity(message)
        self.activity_message = message
        self.refresh_activity()
    def set_reading_mode(self, expanded):
        self.upload_card.setVisible(not expanded)
        self.settings_card.setVisible(not expanded)
        self.table.setMinimumHeight(240 if expanded else 400)
        self.expand_button.setText('Normal görünüme dön' if expanded else 'Genişlet')
        self.read_stop.setVisible(expanded and self.stop.isEnabled())
        QTimer.singleShot(0, lambda: self.legacy_scroll.verticalScrollBar().setValue(0))
    def show_completion(self):
        self.companion.end_job('Ders notların hazır kankacım! Okuyabilir, düzenleyebilir ve kaydedebilirsin.')
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
        paths, _ = QFileDialog.getOpenFileNames(self, 'Ses veya video seç · birden fazla seçebilirsin', '', 'Medya (*.mp3 *.wav *.m4a *.mp4 *.mkv *.mov *.aac *.flac *.ogg *.webm *.wma *.avi)')
        if len(paths)==1:self.set_file(paths[0])
        elif paths:self.open_batch(paths)
    def open_batch(self,paths=None):
        if self.transcribing():return
        from batch_ui import BatchDialog
        dialog=BatchDialog(self,paths);self.batch_dialog=dialog
        try:dialog.exec()
        finally:self.batch_dialog=None
    def set_file(self, path):
        self.companion.file_loading()
        path = Path(path)
        if path.is_file() and path.suffix.lower() in EXTENSIONS:
            try:
                size = path.stat().st_size / (1024 * 1024)
            except OSError as error:
                QMessageBox.warning(self, 'Dosya okunamadı', str(error))
                return
            self.path = path
            self.bag_media.setText(str(path))
            if self.lesson_title.text() == "Yeni ders":
                self.lesson_title.setText(path.stem)
            self.studio.schedule()
            self.file_label.setText(path.name)
            self.file_feedback.setProperty('ready', True)
            self.file_feedback.style().unpolish(self.file_feedback)
            self.file_feedback.style().polish(self.file_feedback)
            self.ready_icon.show()
            self.file_feedback.setText(f'Ses/video dosyan seçildi ve hazır!  ·  {size:.1f} MB\nDosya bu bilgisayarda işlenir; internete yüklenmez.')
            self.start.setEnabled(True)
            self.animate_file_ready()
            self.companion.file_ready()
            self.status.setText('Dosyan hazır. İstediğin çıktı dilini seçip başlatabilirsin; gerisini otomatik ayarlayacağım.')
        else:
            self.companion.end_job('Bu dosyayı açamadım dostum. Bir ses veya video kaydı seçelim.', False)
            QMessageBox.warning(self, 'Dosya açılamadı', 'Desteklenen bir ses veya video dosyası seç.')
    def dragEnterEvent(self, event):
        if not self.transcribing() and self.dropped_paths(event):
            event.acceptProposedAction()
        else:event.ignore()
    def dropped_paths(self,event):
        return list(dict.fromkeys(str(Path(url.toLocalFile())) for url in event.mimeData().urls()
                    if url.isLocalFile() and Path(url.toLocalFile()).is_file()
                    and Path(url.toLocalFile()).suffix.lower() in EXTENSIONS))
    def dropEvent(self, event):
        paths=self.dropped_paths(event)
        if self.transcribing() or not paths:event.ignore();return
        event.acceptProposedAction()
        # Windows sürükleme işlemi bitsin; ardından toplu pencereyi aç.
        QTimer.singleShot(0,lambda:self.set_file(paths[0]) if len(paths)==1 else self.open_batch(paths))
    def busy(self, active):
        for widget in [self.open_btn, self.batch_btn, self.start, self.target_lang, self.offline]:
            widget.setEnabled(not active)
        self.stop.setEnabled(active)
        self.file_feedback.setVisible(not active)
        self.ready_icon.setVisible(not active and self.path is not None)
        self.upload_card.setMaximumHeight(70 if active else 16777215)
        self.read_stop.setVisible(active and self.expand_button.isChecked())
        self.read_stop.setEnabled(active)
        if not active:
            self.start.setEnabled(self.path is not None)
    def transcribing(self):
        return bool((self.worker and self.worker.isRunning()) or
                    (self.batch_dialog and self.batch_dialog.running()))
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
        self.companion.start_job('transcript')
        self.set_status('Başlatılıyor · model hazırlanırken ve ses okunurken biraz sürebilir.')
        options = (self.path, 'auto', None, 'auto', self.offline.isChecked())
        target = [None, 'tr', 'en'][self.target_lang.currentIndex()]
        self.table.setColumnHidden(3, not self.show_original.isChecked())
        self.worker = Worker(options, target)
        self.worker.segment.connect(self.append)
        self.worker.status.connect(self.set_status)
        self.worker.failed.connect(self.failed)
        self.worker.finished.connect(self.finished)
        self.tabs.setCurrentIndex(0)
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
        self.studio.schedule()
        self.companion.progress(progress)
    def cancel(self):
        self.worker.requestInterruption()
        self.stop.setEnabled(False)
        self.read_stop.setEnabled(False)
        self.set_status('Durduruluyor… model indirmesi veya mevcut bölüm tamamlanınca duracak.')
    def failed(self, error):
        self.error = True
        self.set_status('İşlem tamamlanamadı. Mevcut bölümleri kaydedebilirsin.')
        detail=('Çeviri doğrulaması bu bölümde durdu. Oluşan metin korunuyor; bu hata internet bağlantısıyla ilgili değil.'
                if 'Çeviri' in error or 'koruma' in error else 'Oluşan metin korunuyor. Hata ayrıntısı aşağıda.')
        QMessageBox.warning(self, 'İşlem tamamlanamadı', detail+'\n\n'+error)
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
            if not cancelled and not any(segment.text.strip() for segment in self.segments):
                self.progress.hide()
                self.completion_banner.hide()
                message = 'Bu kayıttan konuşma metni elde edilemedi. Kaydın sesini ve seçtiğin dosyayı kontrol et.'
                self.status.setText(message)
                self.companion.end_job('Bu kayıtta yazıya dökebildiğim konuşma bulamadım dostum.', False)
                return
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
        self.companion.say('Ders metnini kopyaladım dostum. Hazır, yapıştırabilirsin!')
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
                self.studio.record_export(path)
                self.companion.say('Altyazın kaydedildi kankacım!' if srt else 'Ders metnin kaydedildi kankacım. İyi çalışmalar!')
            except OSError as e:
                QMessageBox.warning(self, 'Kaydedilemedi', str(e))
    def closeEvent(self, event: QCloseEvent):
        if self.transcribing():
            QMessageBox.information(self, 'İşlem sürüyor', 'Önce Durdur düğmesine bas ve işlemin durmasını bekle.')
            event.ignore()
        else:
            if not self.studio.save():
                event.ignore()
                QMessageBox.warning(self, "Ders kaydedilemedi", "Yerel kayıt tamamlanamadı. Metnini dışa aktararak koru; diskte boş alan olduğunu kontrol et.")
                return
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
