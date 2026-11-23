import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QProgressBar, QMessageBox
from app import Window
from core import Segment

class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
    def test_edit_and_export(self):
        window = Window()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            window.path = Path(folder) / 'ders.mp4'
            window.append(Segment(0, 1.5, 'İlk metin'), 50)
            window.table.item(0, 2).setText('Düzeltilmiş Türkçe')
            for srt in [False, True]:
                output = str(Path(folder) / ('ders.srt' if srt else 'ders.txt'))
                with patch('app.QFileDialog.getSaveFileName', return_value=(output, '')):
                    window.save(srt)
                saved = Path(output).read_text(encoding='utf-8-sig')
                self.assertIn('Düzeltilmiş Türkçe', saved)
                if srt:
                    self.assertIn('00:00:00,000 --> 00:00:01,500', saved)
                else:
                    self.assertNotIn('00:00:', saved)
            window.copy()
            self.assertIn('Düzeltilmiş Türkçe', self.app.clipboard().text())
        window.dirty = False
        window.close()

    def test_search_preserves_export_and_follows_edits(self):
        window = Window()
        window.append(Segment(0, 1, 'Matematik dersi'), 50)
        window.append(Segment(1, 2, 'Sosyoloji dersi'), 99)
        window.search.setText('sosyoloji')
        self.assertTrue(window.table.isRowHidden(0))
        self.assertFalse(window.table.isRowHidden(1))
        self.assertEqual(len(window.edited()), 2)
        window.table.item(1, 2).setText('Fizik dersi')
        self.assertTrue(window.table.isRowHidden(1))
        window.search.clear()
        self.assertFalse(window.table.isRowHidden(0))
        self.assertFalse(window.table.isRowHidden(1))
        window.dirty = False
        window.close()

    def test_device_guidance(self):
        window = Window()
        self.assertFalse(hasattr(window, 'device'))
        self.assertFalse(hasattr(window, 'model'))
        self.assertFalse(hasattr(window, 'lang'))
        self.assertEqual(window.target_lang.currentText(), 'Türkçe')
        window.close()

    def test_source_and_output_are_separate(self):
        window = Window()
        window.target_lang.setCurrentIndex(1)
        self.assertEqual(window.target_lang.currentText(), 'Türkçe')
        window.append(Segment(0, 2, 'Türkçe çıktı', 'English original'), 99)
        self.assertEqual(window.table.item(0, 3).text(), 'English original')
        self.assertEqual(window.edited()[0].text, 'Türkçe çıktı')
        window.export_original.setChecked(True)
        self.assertEqual(window.edited()[0].text, 'English original')
        window.dirty = False
        window.close()

    def test_begin_uses_automatic_configuration(self):
        window = Window()
        window.path = Path('test.wav')
        with patch('app.Worker') as worker:
            window.begin()
            options = worker.call_args.args[0]
            self.assertEqual(options[1:4], ('auto', None, 'auto'))
            self.assertEqual(worker.call_args.args[1], 'tr')
        window.activity_timer.stop()
        window.worker = None
        window.close()

    def test_file_selection_confirmation(self):
        window = Window()
        self.assertFalse(window.start.isEnabled())
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            audio = Path(folder) / 'ders.mp3'
            audio.write_bytes(b'file-selection-test')
            window.set_file(audio)
            self.assertEqual(window.path, audio)
            self.assertIn('hazır', window.file_feedback.text())
            self.assertIn('MB', window.file_feedback.text())
            self.assertTrue(window.start.isEnabled())
            self.assertEqual(window.file_animation.duration(), 650)
            window.file_animation.stop()
        window.close()

    def test_processing_does_not_change_upload_confirmation(self):
        window = Window()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            audio = Path(folder) / 'ders.mp3'
            audio.write_bytes(b'test')
            window.set_file(audio)
            confirmation = window.file_feedback.text()
            with patch('app.Worker') as worker:
                worker.return_value.isInterruptionRequested.return_value = False
                window.begin()
                window.set_status('Türkçeye çevriliyor')
                window.append(Segment(0, 2, 'Örnek'), 35)
                self.assertEqual(window.file_feedback.text(), confirmation)
                self.assertEqual(window.status.text(), 'Türkçeye çevriliyor')
                self.assertIn('Geçen süre', window.elapsed_label.text())
                self.assertEqual(len(window.findChildren(QProgressBar)), 1)
                window.finished()
                self.assertEqual(window.file_feedback.text(), confirmation)
                self.assertFalse(window.ready_icon.isHidden())
        window.worker = None
        window.dirty = False
        window.close()

    def test_quality_flags_do_not_ask_user_to_review(self):
        window = Window()
        window.append(Segment(0, 2, 'Metin', 'Text', 'en', True, True), 20)
        self.assertNotIn('kontrol et', window.table.item(0, 4).text())
        window.dirty = False
        window.close()

    def test_expanded_reading_keeps_text_and_can_return(self):
        window = Window()
        window.append(Segment(0, 2, 'Korunan metin'), 10)
        window.expand_button.setChecked(True)
        self.assertTrue(window.upload_card.isHidden())
        self.assertTrue(window.settings_card.isHidden())
        self.assertEqual(window.table.item(0, 2).text(), 'Korunan metin')
        window.expand_button.setChecked(False)
        self.assertFalse(window.upload_card.isHidden())
        self.assertFalse(window.settings_card.isHidden())
        window.dirty = False
        window.close()

    def test_completion_replaces_percentage_only_after_success(self):
        from unittest.mock import Mock
        window = Window()
        window.worker = Mock()
        window.worker.target_language = 'tr'
        window.worker.isInterruptionRequested.return_value = False
        window.append(Segment(0,1,'Hazır metin'),99)
        window.finished()
        self.assertIn('Çeviri tamamlandı', window.completion_banner.text())
        self.assertFalse(window.completion_banner.isHidden())
        self.assertTrue(window.progress.isHidden())
        window.worker = None
        window.close()

    def test_cancelled_run_has_no_completion_banner(self):
        from unittest.mock import Mock
        window = Window()
        window.worker = Mock()
        window.worker.isInterruptionRequested.return_value = True
        window.finished()
        self.assertTrue(window.completion_banner.isHidden())
        window.worker = None
        window.close()

    def test_empty_transcript_is_not_reported_as_completed(self):
        from unittest.mock import Mock
        for rows in ([],[Segment(0,1,'   ')]):
            window=Window()
            window.worker=Mock()
            window.worker.isInterruptionRequested.return_value=False
            for row in rows:window.append(row,100)
            window.finished()
            self.assertTrue(window.completion_banner.isHidden())
            self.assertTrue(window.progress.isHidden())
            self.assertIn('elde edilemedi',window.status.text())
            window.worker=None
            window.close()


if __name__=='__main__':unittest.main()
