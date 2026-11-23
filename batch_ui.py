"""Tek ders oturumuna dokunmadan açılan toplu kayıt penceresi."""
from pathlib import Path
from PySide6.QtCore import QThread,Signal,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
    QTableWidget,QTableWidgetItem,QHeaderView,QFileDialog,QMessageBox,QProgressBar,QAbstractItemView,QComboBox)
from batch_transcription import create_job,load_job,run_job

MEDIA='Medya (*.mp3 *.wav *.m4a *.mp4 *.mkv *.mov *.aac *.flac *.ogg *.webm *.wma *.avi)'


class QueueWorker(QThread):
    status=Signal(str);changed=Signal(int,object);failed=Signal(str)
    def __init__(self,path,offline,parent):super().__init__(parent);self.path=path;self.offline=offline
    def run(self):
        import sys
        prevent_sleep=None
        try:
            if sys.platform=='win32':
                import ctypes
                prevent_sleep=ctypes.windll.kernel32.SetThreadExecutionState
                prevent_sleep(0x80000001)  # İşlem boyunca boşta kalmaya bağlı sistem uykusunu önle.
            run_job(self.path,self.offline,self.status.emit,self.isInterruptionRequested,self.changed.emit)
        except Exception as error:self.failed.emit(str(error))
        finally:
            if prevent_sleep:prevent_sleep(0x80000000)


class BatchDialog(QDialog):
    def __init__(self,parent,paths=None):
        super().__init__(parent);self.setWindowTitle('Toplu transkript · TXT')
        self.resize(850,620);self.paths=[];self.manifest=None;self.worker=None;self.fatal_error=''
        layout=QVBoxLayout(self)
        intro=QLabel('Kayıtları ve çıktı dilini seç. Her kayıt için TXT otomatik kaydedilir.');intro.setWordWrap(True);layout.addWidget(intro)
        row=QHBoxLayout();layout.addLayout(row)
        self.add=QPushButton('+ Kayıtları seç');self.add.clicked.connect(self.choose);row.addWidget(self.add)
        self.resume=QPushButton('Kayıtlı kuyruğu aç');self.resume.clicked.connect(self.restore);row.addWidget(self.resume)
        self.open_folder=QPushButton('Çıktı klasörünü aç');self.open_folder.setEnabled(False);self.open_folder.clicked.connect(self.open_outputs);row.addWidget(self.open_folder)
        language_row=QHBoxLayout();layout.addLayout(language_row)
        language_label=QLabel('Çıktı dili')
        self.output_mode=QComboBox()
        self.output_mode.setAccessibleName('Toplu TXT çıktı dili')
        for label,mode in (('Türkçe + İngilizce','both'),('Yalnızca Türkçe','tr'),
                           ('Yalnızca İngilizce','en'),('Konuşulduğu dilde (çevirisiz)','original')):
            self.output_mode.addItem(label,mode)
        language_label.setBuddy(self.output_mode)
        language_row.addWidget(language_label);language_row.addWidget(self.output_mode,1)
        self.table=QTableWidget(0,3);self.table.setHorizontalHeaderLabels(['Kayıt','Durum','Ayrıntı'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);layout.addWidget(self.table,1)
        self.progress=QProgressBar();layout.addWidget(self.progress)
        self.message=QLabel('İlk model indirmeleri dışında kayıtlar bu bilgisayarda işlenir.');self.message.setWordWrap(True);layout.addWidget(self.message)
        controls=QHBoxLayout();layout.addLayout(controls)
        self.stop=QPushButton('Durdur');self.stop.setEnabled(False);self.stop.clicked.connect(self.cancel);controls.addWidget(self.stop)
        self.start=QPushButton('TXT oluştur');self.start.clicked.connect(self.begin);controls.addWidget(self.start)
        if paths:self.set_paths(paths)

    def running(self):return bool(self.worker and self.worker.isRunning())
    def set_paths(self,paths):
        from app import EXTENSIONS
        self.paths=list(dict.fromkeys(str(Path(p).resolve()) for p in paths if Path(p).is_file() and Path(p).suffix.lower() in EXTENSIONS))
        self.manifest=None;self.open_folder.setEnabled(False);self.table.setRowCount(len(self.paths))
        self.output_mode.setEnabled(True)
        for index,path in enumerate(self.paths):self.update_row(index,{'source':path,'state':'Bekliyor','error':''})
        self.message.setText(f'{len(self.paths)} kayıt seçildi. Başlatınca çıktı klasörünü seçeceksin.')
    def choose(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Kayıtları birlikte seç','',MEDIA)
        if paths:self.set_paths(paths)
    def update_row(self,index,record):
        for col,text in enumerate((Path(record['source']).name,record['state'],record.get('error',''))):
            item=QTableWidgetItem(text);item.setToolTip(text);self.table.setItem(index,col,item)
        done=sum(self.table.item(i,1).text()=='Tamamlandı' for i in range(self.table.rowCount()) if self.table.item(i,1))
        self.progress.setRange(0,max(1,self.table.rowCount()));self.progress.setValue(done)
        self.progress.setFormat(f'{done} / {self.table.rowCount()} kayıt tamamlandı')
    def restore(self):
        name,_=QFileDialog.getOpenFileName(self,'Çıktı klasöründeki kuyruk.json dosyasını aç','','Kuyruk (kuyruk.json)')
        if not name:return
        try:
            job=load_job(name);self.manifest=Path(name);self.table.setRowCount(len(job['records']))
            self.output_mode.setCurrentIndex(self.output_mode.findData(job['output_mode']))
            self.output_mode.setEnabled(False)
            for i,record in enumerate(job['records']):self.update_row(i,record)
            self.open_folder.setEnabled(True);self.message.setText('Başlatınca tamamlanan kayıtlar atlanır, yarım kalan çeviriye devam edilir.')
        except Exception as error:QMessageBox.warning(self,'Kuyruk açılamadı',str(error))
    def begin(self):
        if self.running():return
        try:
            if self.manifest is None:
                if not self.paths:self.choose()
                if not self.paths:return
                folder=QFileDialog.getExistingDirectory(self,'TXT dosyaları nereye kaydedilsin?')
                if not folder:return
                self.manifest=create_job(self.paths,folder,self.output_mode.currentData())
                self.output_mode.setEnabled(False)
            self.fatal_error=''
            self.worker=QueueWorker(self.manifest,self.parent().offline.isChecked(),self)
            self.worker.status.connect(self.show_status);self.worker.changed.connect(self.update_row)
            self.worker.failed.connect(self.show_failure)
            self.worker.finished.connect(self.job_finished)
            for button in (self.add,self.resume,self.start):button.setEnabled(False)
            self.stop.setEnabled(True);self.open_folder.setEnabled(True)
            self.worker.start()
        except Exception as error:QMessageBox.warning(self,'Kuyruk başlatılamadı',str(error))
    def show_status(self,text):
        self.message.setText(text)
    def show_failure(self,text):
        self.fatal_error=text;self.message.setText('İşlem durdu: '+text)
    def cancel(self):
        if self.worker:self.worker.requestInterruption()
        self.stop.setEnabled(False);self.message.setText('Güvenle durduruluyor. Kaydedilen TXT dosyaları korunacak.')
    def job_finished(self):
        for button in (self.add,self.resume,self.start):button.setEnabled(True)
        self.stop.setEnabled(False)
        if self.fatal_error:
            self.message.setText('Kuyruk durdu: '+self.fatal_error+'. Kaydedilen dosyalar korunuyor.');return
        try:
            records=load_job(self.manifest)['records'];done=sum(r['state']=='Tamamlandı' for r in records);errors=sum(r['state']=='Hata' for r in records)
            self.message.setText(f'{done}/{len(records)} kayıt tamamlandı · {errors} hata. TXT dosyaları çıktı klasöründe. Başlat ile eksiklere devam edebilirsin.')
        except Exception:pass
    def open_outputs(self):
        if self.manifest:QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.manifest.parent)))
    def closeEvent(self,event):
        if self.running():
            self.message.setText('Kapatmadan önce Durdur’a basıp işlemin durmasını bekle.');event.ignore()
        else:event.accept()
    def reject(self):
        if not self.running():super().reject()
        else:self.message.setText('Önce Durdur’a basıp işlemin durmasını bekle.')
