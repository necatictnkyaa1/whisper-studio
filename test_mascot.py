import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QWidget
from mascot import Companion

class CompanionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
    def setUp(self):
        self.window = QWidget(); self.window.resize(1000,800)
        self.pet = Companion(self.window)
        self.pet.reset_position(); self.window.show(); self.app.processEvents()
    def tearDown(self):
        self.pet.settings.remove('position')
        self.window.close(); self.window.deleteLater(); self.app.processEvents()
    def test_default_and_resize(self):
        self.assertEqual(self.pet.x()+self.pet.width()+12,1000)
        self.window.resize(920,640); self.app.processEvents()
        self.assertEqual(self.pet.y()+self.pet.height()+12,640)
    def test_moods_follow_progress(self):
        self.pet.start_job('transcript')
        for value,mood in [(10,'waiting'),(50,'working'),(90,'excited')]:
            self.pet.progress(value); self.assertEqual(self.pet.mood,mood)
        self.pet.end_job('Hazır')
        self.assertFalse(self.pet.check_in.isActive())
        self.assertEqual(self.pet.mood,'happy')
    def test_no_repeat_from_status_updates(self):
        self.pet.start_job('transcript'); message=self.pet.message.text()
        for _ in range(100): self.pet.activity('Türkçeye çevriliyor')
        self.assertEqual(self.pet.message.text(),message)
    def test_quiet_and_cooldown(self):
        self.pet.say('İlk'); self.pet.say('Tekrar',automatic=True)
        self.assertEqual(self.pet.message.text(),'İlk')
        self.pet.set_muted(True); self.pet.say('Sessiz')
        self.assertTrue(self.pet.bubble.isHidden())
    def test_file_messages_and_interrupt(self):
        self.pet.file_loading()
        self.assertEqual(self.pet.message.text(),'Kaydın yükleniyor dostum')
        self.pet.file_ready(); self.assertTrue(self.pet.ready_timer.isActive())
        self.pet.ready_timer.timeout.emit()
        self.assertIn('Yüklendi kankacım',self.pet.message.text())
        self.pet.start_job('sheet'); self.assertFalse(self.pet.ready_timer.isActive())
    def test_hidden_bubble_does_not_block_content(self):
        self.pet.hide_bubble()
        self.assertFalse(self.pet.mask().contains(self.pet.bubble.geometry().center()))
    def test_error_stops_reassurance(self):
        self.pet.start_job('transcript');self.pet.activity('İşlem tamamlanamadı')
        self.assertIsNone(self.pet.job)
        self.assertFalse(self.pet.check_in.isActive())

if __name__ == '__main__': unittest.main()
