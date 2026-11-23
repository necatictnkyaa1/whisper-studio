import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
from PySide6.QtWidgets import QApplication
from app import Window
from batch_ui import BatchDialog


class BatchUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_multi_select_and_single_select_route_separately(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WHISPER_STUDIO_DATA':folder}):
            w=Window()
            with patch('app.QFileDialog.getOpenFileNames',return_value=(['a.mp3','b.mp3'],'')),patch.object(w,'open_batch') as batch:
                w.choose();batch.assert_called_once_with(['a.mp3','b.mp3'])
            with patch('app.QFileDialog.getOpenFileNames',return_value=(['a.mp3'],'')),patch.object(w,'set_file') as single:
                w.choose();single.assert_called_once_with('a.mp3')
            w.close()
    def test_drop_43_files_directly_onto_yellow_card(self):
        from PySide6.QtCore import QMimeData,QUrl,QPoint,QPointF,Qt
        from PySide6.QtGui import QDragEnterEvent,QDropEvent
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WHISPER_STUDIO_DATA':folder}):
            paths=[]
            for i in range(43):
                p=Path(folder)/f'{i}.mp3';p.write_bytes(b'audio');paths.append(str(p))
            w=Window();w.show();self.app.processEvents()
            mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
            enter=QDragEnterEvent(QPoint(10,10),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
            self.app.sendEvent(w.upload_card,enter);self.assertTrue(enter.isAccepted())
            with patch.object(w,'open_batch') as batch:
                event=QDropEvent(QPointF(10,10),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
                self.app.sendEvent(w.upload_card,event);self.app.processEvents()
                self.assertTrue(event.isAccepted());batch.assert_called_once_with(paths)
            w.worker=Mock();w.worker.isRunning.return_value=True
            enter=QDragEnterEvent(QPoint(10,10),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
            self.app.sendEvent(w.upload_card,enter);self.assertFalse(enter.isAccepted())
            w.worker=None;w.close()
    def test_fatal_error_is_not_hidden_by_finished_summary(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WHISPER_STUDIO_DATA':folder}):
            w=Window();dialog=BatchDialog(w)
            dialog.show_failure('Disk dolu');dialog.job_finished()
            self.assertIn('Disk dolu',dialog.message.text())
            dialog.close();w.close()
    def test_43_rows_and_running_dialog_cannot_be_closed(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'WHISPER_STUDIO_DATA':folder}):
            paths=[]
            for i in range(43):
                path=Path(folder)/f'{i}.mp3';path.write_bytes(b'test');paths.append(path)
            w=Window();dialog=BatchDialog(w,paths)
            self.assertEqual(dialog.table.rowCount(),43)
            self.assertIn('43',dialog.message.text())
            dialog.worker=Mock();dialog.worker.isRunning.return_value=True
            w.batch_dialog=dialog
            self.assertTrue(w.transcribing())
            dialog.reject();self.assertIn('Durdur',dialog.message.text())
            dialog.worker=None;w.batch_dialog=None;dialog.close();w.close()


if __name__=='__main__':unittest.main()
