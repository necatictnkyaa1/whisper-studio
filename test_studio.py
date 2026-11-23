import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, Qt, QPointF
from PySide6.QtGui import QMouseEvent
from sessions import SessionStore
from core import Segment
from app import Window

class StudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'WHISPER_STUDIO_DATA':self.temp.name});self.env.start()
        self.windows=[]
    def tearDown(self):
        for w in self.windows:w.close();w.deleteLater()
        self.app.processEvents();self.env.stop();self.temp.cleanup()
    def window(self):
        w=Window();self.windows.append(w);return w
    def test_sessions_survive_new_window_with_edits_and_notes(self):
        w=self.window();w.lesson_title.setText('Makine öğrenmesi')
        w.path=Path(self.temp.name)/'missing.mp3'
        w.append(Segment(0,2,'İlk hali','Original','en',True),40)
        w.table.item(0,2).setText('Düzeltilmiş Türkçe')
        w.personal_notes.setPlainText('Vize salı günü')
        self.assertTrue(w.studio.save());identity=w.studio.identity
        other=self.window();other.studio.switch(identity,False)
        self.assertEqual(other.table.item(0,2).text(),'Düzeltilmiş Türkçe')
        self.assertEqual(other.segments[0].source_language,'en')
        self.assertEqual(other.personal_notes.toPlainText(),'Vize salı günü')
        self.assertFalse(other.start.isEnabled())
        self.assertIn('taşınmış',other.file_feedback.text())
        self.assertEqual(other.studio.store.last(),identity)
    def test_new_and_switch_preserve_separate_lessons(self):
        w=self.window();w.lesson_title.setText('Ders A');w.append(Segment(0,1,'A'),100)
        w.studio.save();identity=w.studio.identity
        w.studio.new();self.assertEqual(w.table.rowCount(),0)
        w.lesson_title.setText('Ders B');w.personal_notes.setPlainText('B notu')
        w.studio.switch(identity)
        self.assertEqual(w.lesson_title.text(),'Ders A')
        self.assertEqual(w.table.item(0,2).text(),'A')
        self.assertEqual(len(w.studio.store.list()),2)
        self.assertEqual(len(w.studio.store.list('Ders B')),1)
    def test_failed_save_blocks_session_switch_and_close(self):
        w=self.window()
        import sqlite3
        with patch.object(w.studio.store,'save',side_effect=sqlite3.OperationalError('disk full')):
            w.studio.new();self.assertIsNone(w.studio.identity)
            with patch('app.QMessageBox.warning'):
                self.assertFalse(w.close())
        self.assertIn('Kaydedilemedi',w.local_save_label.text())
    def test_small_window_and_panel_toggles(self):
        w=self.window();w.show();self.app.processEvents()
        w.resize(960,760);self.app.processEvents()
        self.assertTrue(w.bag_panel.isHidden());self.assertTrue(w.history_panel.isHidden())
        w.studio.toggle_bag();self.assertFalse(w.bag_panel.isHidden())
        self.assertEqual(w.tabs.count(),1)
        self.assertGreater(w.tabs.width(),400)
    def test_transcript_only_preserves_legacy_payload(self):
        w=self.window()
        legacy={'sheet':{'content':{'baslik':'Eski föy'}},'sources':['old.pdf'],'focus':'Eski odak','tab':1}
        w.studio.apply('Eski ders',legacy)
        self.assertEqual(w.tabs.count(),1)
        self.assertFalse(hasattr(w,'sheet_start'))
        self.assertFalse(hasattr(w,'begin_sheet'))
        self.assertEqual(w.studio.snapshot()['sheet'],legacy['sheet'])
        self.assertTrue(w.studio.save())
        other=self.window();other.studio.switch(w.studio.identity,False)
        self.assertEqual(other.studio.snapshot()['sources'],['old.pdf'])

    def test_touch_drag_and_landing_reactions(self):
        w=self.window();pet=w.companion
        pet.react('touch');self.assertEqual(pet.reaction,'touch')
        pet.drag_origin=QPoint(0,0);pet.drag_start=QPoint(0,0)
        event=QMouseEvent(QMouseEvent.MouseMove,QPointF(50,50),QPointF(450,350),Qt.NoButton,Qt.LeftButton,Qt.NoModifier)
        pet.mouseMoveEvent(event)
        self.assertEqual(pet.reaction,'drag');self.assertNotEqual(pet.lean,0)
        release=QMouseEvent(QMouseEvent.MouseButtonRelease,QPointF(50,50),QPointF(450,350),Qt.LeftButton,Qt.NoButton,Qt.NoModifier)
        pet.mouseReleaseEvent(release)
        self.assertEqual(pet.reaction,'land');self.assertIsNone(pet.drag_origin)
        pet.reset_position()

if __name__=='__main__':unittest.main()
