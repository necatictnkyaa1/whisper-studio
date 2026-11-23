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

class SheetWorker(QThread):
    """Föyü arka planda hazırlar: kaynakları okur, modeli hazırlar, üretir, VRAM'i boşaltır."""
    stage = Signal(str, int, int)
    status = Signal(str)
    done = Signal(object)
    failed = Signal(str)
    def __init__(self, client, segments, files, offline, focus, title):
        super().__init__()
        self.client, self.segments, self.files = client, segments, files
        self.offline, self.focus, self.title = offline, focus, title
        self.current = ''
        self.last_status = 0.0
    def on_stage(self, text, step, total):
        self.current = text
        self.stage.emit(text, step, total)
    def on_tokens(self, count):
        if time.monotonic() - self.last_status > 0.5:
            self.last_status = time.monotonic()
            self.status.emit(f'{self.current} · {count:,} karakter işlendi'.replace(',', '.'))
    def run(self):
        import llm
        import worksheet
        from automatic import inspect_hardware
        from sources import SourceLibrary, SourceError
        cancelled = self.isInterruptionRequested
        plan = None
        try:
            library, skipped = SourceLibrary(), []
            if self.segments:
                library.add_transcript(self.segments, self.title)
            for path, kind in self.files:
                try:
                    library.add_file(path, kind)
                except SourceError as error:
                    skipped.append(str(error))
            self.status.emit('Bilgisayarın kontrol ediliyor · föy için uygun model otomatik seçiliyor')
            plan = llm.prepare(self.client, inspect_hardware(), self.offline, self.status.emit, cancelled)
            model = worksheet.LocalModel(self.client, plan, cancelled, self.on_tokens)
            import research
            # İnternetsiz çalışmada ek araştırma yapılmaz; aksi halde yalnızca terim adlarıyla Vikipedi aranır.
            sheet = worksheet.build_worksheet(library, model, cancelled, self.on_stage, self.focus,
                                              None if self.offline else research.research)
            sheet.warnings[:0] = skipped
            sheet.stats['vram_mb'] = sum(m.get('size_vram', 0) for m in self.client.loaded()) // 1048576
            sheet.stats['plan'] = plan.reason
            self.done.emit(sheet)
        except (worksheet.Cancelled, llm.Cancelled):
            pass
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            if plan is not None:
                self.client.unload(plan.name)

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
        self.segments = []
        self.error = False
        self.dirty = False
        self.source_files = []
        self.speech_files = set()
        self.sheet = None
        self.sheet_worker = None
        self.sheet_dirty = False
        self.sheet_started_at = None
        self.llm_client = None
        from ui import build_ui
        build_ui(self)
        self.sheet_timer = QTimer(self)
        self.sheet_timer.setInterval(1000)
        self.sheet_timer.timeout.connect(self.refresh_sheet_elapsed)
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
        path, _ = QFileDialog.getOpenFileName(self, 'Ses veya video seç', '', 'Medya (*.mp3 *.wav *.m4a *.mp4 *.mkv *.mov *.aac *.flac *.ogg *.webm *.wma *.avi)')
        if path:
            self.set_file(path)
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
        self.file_feedback.setVisible(not active)
        self.ready_icon.setVisible(not active and self.path is not None)
        self.upload_card.setMaximumHeight(70 if active else 16777215)
        self.read_stop.setVisible(active and self.expand_button.isChecked())
        self.read_stop.setEnabled(active)
        # Ekran kartı işleri sırayla: transkripsiyon sürerken föy başlatılmaz.
        self.sheet_start.setEnabled(not active and not self.sheet_running())
        if not active:
            self.start.setEnabled(self.path is not None and not self.sheet_running())
    # ---------- Çalışma kağıdı ----------
    def sheet_running(self):
        return bool(self.sheet_worker and self.sheet_worker.isRunning())
    def transcribing(self):
        return bool(self.worker and self.worker.isRunning())
    def refresh_sources(self):
        from sources import SourceLibrary, SourceError
        self.source_list.clear()
        for path in self.source_files:
            try:
                summary = SourceLibrary().add_file(path, self.source_kind(path)).summary()
            except SourceError as error:
                summary = str(error)
            self.source_list.addItem(f'{Path(path).name}  —  {summary}')
    def choose_sources(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Föy kaynağı seç', '', 'Kaynaklar (*.txt *.md *.markdown *.pdf)')
        self.add_sources(paths)
    def add_sources(self, paths):
        from sources import SourceLibrary, SourceError
        problems = []
        for path in paths:
            path = Path(path)
            if path in self.source_files:
                continue
            try:
                SourceLibrary().add_file(path)
            except (SourceError, OSError) as error:
                problems.append(str(error))
                continue
            if path.suffix.lower() == '.txt' and QMessageBox.question(
                    self, 'Ders kaydı mı?',
                    f'{path.name} bir ders kaydının yazıya dökümü mü (ör. Whisper Studio TXT çıktısı)?\n\n'
                    'Evet dersen föyde, konuşma tanıma hatalarından gelebilecek bilgiler için ayrıca uyarı yapılır.'
                    ) == QMessageBox.Yes:
                self.speech_files.add(path)
            self.source_files.append(path)
        self.refresh_sources()
        self.studio.schedule()
        if problems:
            QMessageBox.warning(self, 'Bazı kaynaklar eklenemedi', '\n'.join(problems))
        elif paths:
            self.companion.say('Notlarını da aldım dostum, çalışma kağıdında bunlardan yararlanabiliriz.')
            self.sheet_status.setText(f'{len(self.source_files)} kaynak hazır. Çalışma kağıdı oluşturabilirsin.')
    def remove_source(self):
        row = self.source_list.currentRow()
        if 0 <= row < len(self.source_files):
            self.speech_files.discard(self.source_files.pop(row))
            self.refresh_sources()
            self.studio.schedule()
            self.companion.say('Bu kaynağı çıkardım dostum; diğerleri duruyor.')
    def source_kind(self, path):
        return 'transkript' if path in self.speech_files else None
    def confirm_sheet_discard(self):
        return not self.sheet_dirty or QMessageBox.question(self, 'Föyü koru',
            'Kaydedilmemiş bir çalışma kağıdı var. Devam edersen kaybolacak. Devam edilsin mi?') == QMessageBox.Yes
    def begin_sheet(self):
        segments = self.edited() if self.use_transcript.isChecked() and self.segments else []
        if not segments and not self.source_files:
            QMessageBox.information(self, 'Kaynak gerekli', 'Önce bir kaydı yazıya dönüştür veya en az bir kaynak dosyası ekle.')
            return
        if self.transcribing():
            QMessageBox.information(self, 'İşlem sürüyor', 'Yazıya dönüştürme bitince çalışma kağıdını başlatabilirsin.')
            return
        if not self.confirm_sheet_discard():
            return
        if self.llm_client is None:
            import llm
            self.llm_client = llm.OllamaClient()
        title = f'Ders kaydı ({self.path.name})' if self.path else 'Ders kaydı'
        self.sheet = None
        self.sheet_dirty = False
        self.sheet_view.hide()
        self.sheet_banner.hide()
        for btn in self.sheet_buttons:
            btn.setEnabled(False)
        self.sheet_step.setText('Hazırlanıyor')
        self.sheet_step.show()
        self.sheet_busy(True)
        self.sheet_started_at = time.monotonic()
        self.sheet_elapsed.show()
        self.sheet_timer.start()
        self.refresh_sheet_elapsed()
        self.companion.start_job('sheet')
        self.sheet_status.setText('Başlatılıyor · kaynaklar okunuyor')
        files = [(path, self.source_kind(path)) for path in self.source_files]
        self.sheet_worker = SheetWorker(self.llm_client, segments, files, self.offline.isChecked(),
                                        self.sheet_focus.text(), title)
        self.sheet_worker.stage.connect(self.sheet_stage)
        self.sheet_worker.status.connect(self.sheet_status.setText)
        self.sheet_worker.done.connect(self.sheet_done)
        self.sheet_worker.failed.connect(self.sheet_failed)
        self.sheet_worker.finished.connect(self.sheet_finished)
        self.tabs.setCurrentIndex(1)
        self.sheet_worker.start()
    def sheet_busy(self, active):
        for widget in [self.sheet_start, self.add_source_btn, self.remove_source_btn, self.use_transcript, self.sheet_focus]:
            widget.setEnabled(not active)
        self.sheet_stop.setEnabled(active)
        self.start.setEnabled(not active and self.path is not None and not self.transcribing())
    def refresh_sheet_elapsed(self):
        if self.sheet_started_at is not None:
            elapsed = int(time.monotonic() - self.sheet_started_at)
            self.sheet_elapsed.setText(f'Geçen süre · {elapsed // 60:02}:{elapsed % 60:02}')
    def sheet_stage(self, text, step, total):
        self.sheet_status.setText(text)
        self.companion.progress(100 * step / max(1, total))
        self.sheet_step.setText(f'Adım {step}/{total}  ·  {text}' if total > 1 else text)
    def sheet_done(self, sheet):
        self.companion.end_job('Çalışma kağıdın hazır kankacım! Birlikte güzel çalışacağız. Kaydetmeyi unutma.')
        from worksheet import render_html
        self.sheet = sheet
        self.bag_output.setText('Çalışma kağıdını aç')
        self.bag_output.setEnabled(True)
        self.studio.schedule()
        self.sheet_dirty = True
        self.sheet_view.setHtml(render_html(sheet))
        self.sheet_view.show()
        for btn in self.sheet_buttons:
            btn.setEnabled(True)
        minutes, seconds = divmod(int(sheet.stats.get('seconds', 0)), 60)
        self.sheet_banner.setText(f'Çalışma kağıdın hazır  ·  {minutes} dk {seconds} sn')
        self.sheet_banner.show()
        self.sheet_animation = QVariantAnimation(self)
        self.sheet_animation.setDuration(700)
        self.sheet_animation.setStartValue(QColor('#fff1b8'))
        self.sheet_animation.setEndValue(QColor('#b6e2ce'))
        self.sheet_animation.valueChanged.connect(lambda color: self.sheet_banner.setStyleSheet(f'background-color:{color.name()};'))
        self.sheet_animation.start()
        notes = f' · {len(sheet.warnings)} otomatik kontrol notu föyün sonunda.' if sheet.warnings else ''
        self.sheet_status.setText(f'Hazır · {sheet.model} ile bu bilgisayarda üretildi{notes} Kaydetmeyi unutma.')
    def sheet_failed(self, error):
        self.companion.end_job('Çalışma kağıdında bir pürüz çıktı dostum. Ayrıntıya bakıp yeniden deneyebiliriz.', False)
        self.sheet_status.setText('Çalışma kağıdı hazırlanamadı.')
        QMessageBox.warning(self, 'Çalışma kağıdı hazırlanamadı', error)
    def sheet_finished(self):
        self.sheet_timer.stop()
        self.sheet_started_at = None
        self.sheet_busy(False)
        self.sheet_step.hide()
        if self.sheet is None and self.sheet_worker and self.sheet_worker.isInterruptionRequested():
            self.sheet_status.setText('Durduruldu · yarım föy gösterilmez. Yeniden başlatabilirsin.')
    def cancel_sheet(self):
        if self.sheet_worker:
            self.sheet_worker.requestInterruption()
        self.sheet_stop.setEnabled(False)
        self.companion.end_job('Peki dostum, çalışma kağıdını güvenle durduruyorum.', False)
        self.sheet_status.setText('Durduruluyor…')
    def sheet_markdown(self):
        from worksheet import render_markdown
        return render_markdown(self.sheet)
    def copy_sheet(self):
        if self.sheet:
            QApplication.clipboard().setText(self.sheet_markdown())
            self.companion.say('Çalışma kağıdını kopyaladım kankacım, istediğin yere yapıştırabilirsin.')
    def save_sheet(self, kind):
        if not self.sheet:
            return
        from worksheet import render_html
        stem = (self.path.stem if self.path else 'ders') + '-calisma-kagidi'
        folder = self.path.parent if self.path else (self.source_files[0].parent if self.source_files else Path.home())
        suffix = '.md' if kind == 'md' else '.html'
        path, _ = QFileDialog.getSaveFileName(self, 'Çalışma kağıdını kaydet', str(folder / (stem + suffix)),
                                              'Markdown (*.md)' if kind == 'md' else 'Web sayfası (*.html)')
        if not path:
            return
        if not path.lower().endswith(suffix):
            path += suffix
        content = self.sheet_markdown() if kind == 'md' else (
            '<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Çalışma kağıdı</title></head>'
            '<body style="background:#f2e9d9;max-width:860px;margin:24px auto;padding:24px;">'
            + render_html(self.sheet) + '</body></html>')
        try:
            Path(path).write_text(content, encoding='utf-8')
            self.sheet_dirty = False
            self.sheet_status.setText('Kaydedildi · ' + path)
            self.studio.record_export(path)
            self.companion.say('Çalışma kağıdın kaydedildi dostum. Emeğimiz artık dosyanda!')
        except OSError as e:
            QMessageBox.warning(self, 'Kaydedilemedi', str(e))
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
        if self.transcribing() or self.sheet_running():
            QMessageBox.information(self, 'İşlem sürüyor', 'Önce Durdur düğmesine bas ve işlemin durmasını bekle.')
            event.ignore()
        else:
            if self.llm_client:
                self.llm_client.stop()
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
