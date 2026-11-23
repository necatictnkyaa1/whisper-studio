"""Üç panelli ders alanı ve mevcut işlem motoruna yerel oturum bağlama."""
from dataclasses import asdict
from pathlib import Path
import sqlite3
from PySide6.QtCore import Qt, QTimer, QObject, QEvent
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QTabWidget,
    QPushButton,QLabel,QLineEdit,QListWidget,QListWidgetItem,QPlainTextEdit,QScrollArea,
    QMessageBox,QInputDialog,QSizePolicy)
from sessions import SessionStore


def move_widget(widget, layout):
    widget.setParent(None)
    layout.addWidget(widget)


class Studio(QObject):
    def __init__(self,w):
        super().__init__(w)
        self.w=w
        self.identity=None
        self.saved_exports=[]
        self.legacy_payload={}
        self.restoring=False
        self.initialized=False
        self.store=SessionStore()
        self.arrange()
        self.save_timer=QTimer(self);self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(900);self.save_timer.timeout.connect(self.save)
        for signal in (w.table.itemChanged,w.personal_notes.textChanged,
                       w.target_lang.currentIndexChanged,w.tabs.currentChanged):
            signal.connect(self.schedule)
        w.lesson_title.editingFinished.connect(self.schedule)
        w.installEventFilter(self)

    def arrange(self):
        w=self.w
        old=w.takeCentralWidget();w.legacy_scroll=old
        shell=QWidget();shell.setObjectName('studioCanvas')
        outer=QVBoxLayout(shell);outer.setContentsMargins(12,10,12,10);outer.setSpacing(10)
        bar=QHBoxLayout()
        left_toggle=QPushButton('Dersler');bar.addWidget(left_toggle)
        brand=QLabel('Whisper Studio');brand.setObjectName('studioBrand');bar.addWidget(brand)
        bar.addStretch()
        w.local_save_label=QLabel('Bu bilgisayarda saklanır');bar.addWidget(w.local_save_label)
        right_toggle=QPushButton('Ders çantası');bar.addWidget(right_toggle)
        outer.addLayout(bar)
        w.splitter=QSplitter(Qt.Horizontal)
        w.splitter.setChildrenCollapsible(False)
        outer.addWidget(w.splitter,1)
        w.history_panel=QWidget();w.history_panel.setObjectName('lessonSidebar');w.history_panel.setMinimumWidth(170)
        left=QVBoxLayout(w.history_panel);left.setContentsMargins(8,8,8,8)
        new=QPushButton('+  Yeni ders');new.setObjectName('newLesson');left.addWidget(new)
        w.history_search=QLineEdit();w.history_search.setPlaceholderText('Derslerinde ara…');left.addWidget(w.history_search)
        w.lesson_list=QListWidget();w.lesson_list.setWordWrap(True);w.lesson_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);left.addWidget(w.lesson_list,1)
        rename=QPushButton('Dersin adını değiştir');left.addWidget(rename)
        left.addWidget(QLabel('Derslerin yalnızca bu bilgisayarda.'))
        w.splitter.addWidget(w.history_panel)
        center=QWidget();center.setMinimumWidth(460)
        main=QVBoxLayout(center);main.setContentsMargins(12,0,12,0);main.setSpacing(8)
        w.lesson_title=QLineEdit('Yeni ders');w.lesson_title.setObjectName('lessonTitle');main.addWidget(w.lesson_title)
        # Büyük giriş kartlarının yerini iki kısa satır alır.
        w.upload_card.setParent(None)
        upload_layout=w.upload_card.layout()
        while upload_layout.count():
            item=upload_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
        compact=QVBoxLayout();compact.setContentsMargins(12,8,12,8)
        upload_layout.addLayout(compact)
        row=QHBoxLayout();move_widget(w.file_label,row);row.addStretch();move_widget(w.open_btn,row);w.open_btn.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed);compact.addLayout(row)
        w.batch_btn=QPushButton('Toplu TXT')
        w.batch_btn.clicked.connect(lambda:w.open_batch())
        compact.addWidget(w.batch_btn)
        confirmation=QHBoxLayout();move_widget(w.ready_icon,confirmation);move_widget(w.file_feedback,confirmation)
        compact.addLayout(confirmation)
        w.file_label.setText('Bir veya birden fazla ses/video kaydını buraya bırak.')
        w.file_label.setMinimumWidth(260)
        main.addWidget(w.upload_card)
        w.settings_card.setParent(None)
        settings=w.settings_card.layout()
        while settings.count():
            item=settings.takeAt(0)
            if item.widget(): item.widget().hide()
        config=QHBoxLayout();config.addWidget(QLabel('Çıktı dili'))
        for widget in (w.target_lang,w.stop,w.start):
            move_widget(widget,config);widget.show();widget.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        settings.addLayout(config);settings.setContentsMargins(10,6,10,6)
        main.addWidget(w.settings_card)
        config.insertStretch(2,1)
        w.tabs=QTabWidget();main.addWidget(w.tabs,1)
        w.notebook_card.setParent(None)
        w.tabs.addTab(w.notebook_card,'Ders metni')
        w.table.setColumnHidden(0,True);w.table.setColumnHidden(1,True)
        w.table.setMinimumHeight(180);w.notebook_card.setMinimumHeight(0)
        w.table.horizontalHeaderItem(2).setText('Ders metnin · çift tıkla, düzenle')
        w.notebook_card.layout().setContentsMargins(10,10,10,10)
        w.splitter.addWidget(center)
        w.bag_panel=QWidget();w.bag_panel.setObjectName('lessonBag');w.bag_panel.setMinimumWidth(210)
        bag=QVBoxLayout(w.bag_panel);bag.setContentsMargins(10,8,8,8)
        bag.addWidget(QLabel('DERS ÇANTASI'))
        w.bag_media=QLabel('Henüz ses kaydı eklenmedi.');w.bag_media.setWordWrap(True);bag.addWidget(w.bag_media)
        bag.addWidget(QLabel('Kaydedilen transkriptler'))
        w.export_list=QListWidget();w.export_list.setMaximumHeight(90);w.export_list.hide();bag.addWidget(w.export_list)
        w.export_list.itemDoubleClicked.connect(self.open_export)
        bag.addWidget(QLabel('Kişisel notların'))
        w.personal_notes=QPlainTextEdit();w.personal_notes.setPlaceholderText('Aklında kalanlar, sınav tarihleri…');bag.addWidget(w.personal_notes,1)
        w.offline.setParent(None);bag.addWidget(w.offline);w.offline.show()
        w.translation_hint.setParent(None);bag.addWidget(w.translation_hint);w.translation_hint.show()
        w.splitter.addWidget(w.bag_panel)
        w.splitter.setStretchFactor(1,1);w.splitter.setSizes([210,810,260])
        w.setCentralWidget(shell);old.hide()
        w.resize(1440,900);w.setMinimumSize(760,620)
        left_toggle.clicked.connect(lambda:w.history_panel.setVisible(w.history_panel.isHidden()))
        right_toggle.clicked.connect(self.toggle_bag)
        new.clicked.connect(self.new)
        rename.clicked.connect(self.rename)
        w.history_search.textChanged.connect(self.refresh)
        w.lesson_title.textEdited.connect(self.schedule)
        w.lesson_list.itemClicked.connect(lambda item:self.switch(item.data(Qt.UserRole)))
        w.setStyleSheet(w.styleSheet()+'''
        QWidget#studioCanvas {background:#f2e9d9;}
        QLabel#studioBrand {font-size:19px;font-weight:800;color:#422c22;}
        QWidget#lessonSidebar {background:#fff0b5;border:2px solid #694832;border-radius:14px;}
        QWidget#lessonBag {background:#fff8e7;border:2px solid #694832;border-radius:14px;}
        QLineEdit#lessonTitle {font-size:22px;font-weight:700;border:0;background:transparent;padding:6px;}
        QFrame#yellowCard {background:#f9d354;border:2px solid #422c22;border-radius:14px;}
        QFrame#paperCard {background:#fffcf3;border:2px solid #694832;border-radius:14px;}
        QLabel#fileFeedback {background:#fff0ad;color:#573c25;font-size:12px;padding:6px;font-weight:500;}
        QLabel#fileFeedback[ready="true"] {background:#b6e2ce;color:#194b40;}
        QLabel#completion {font-size:14px;padding:8px;border:0;}
        QPushButton {background:#fffcf3;font-size:12px;border:2px solid #694832;padding:7px 10px;border-radius:9px;}
        QPushButton:hover {background:#ffe59a;}
        QPushButton#mintButton {background:#99d8bb;border:2px solid #194b40;}
        QPushButton#darkButton {background:#422c22;color:#fff0ad;border:2px solid #422c22;}
        QPushButton:disabled {background:#eee8dd;color:#998b7b;border:2px solid #c8bdae;}
        QPushButton#newLesson {background:#f9d354;color:#422c22;border:2px solid #422c22;font-weight:800;}
        QListWidget {background:#fff8df;border:0;border-radius:10px;padding:4px;}
        QListWidget::item {padding:12px 6px;border-radius:7px;}
        QListWidget::item:selected {background:#f9d354;color:#422c22;border:1px solid #8c632d;font-weight:650;}
        QTabWidget::pane {border:0;}
        QTabBar::tab {padding:10px 20px;background:transparent;border-bottom:3px solid transparent;}
        QTabBar::tab:selected {background:#f9d354;color:#422c22;border-bottom:3px solid #694832;border-top-left-radius:9px;border-top-right-radius:9px;font-weight:750;}
        QTabBar::tab:hover {background:#ffe9a2;}
        QSplitter::handle {background:#d7bf8c;width:3px;}
        QPlainTextEdit {background:#fffcf3;border:2px solid #b9a078;border-radius:9px;padding:8px;}
        QHeaderView::section {background:#f8e3a0;color:#422c22;border-bottom:2px solid #c9a851;}
        QProgressBar {background:#ebdfbf;}
        QProgressBar::chunk {background:#79cbaa;}
        ''')
        for card in (w.upload_card,w.settings_card,w.notebook_card):
            card.setGraphicsEffect(None)
        self.bag_manual=False

    def record_export(self,path):
        path=str(path)
        if path not in self.saved_exports:self.saved_exports.append(path)
        self.refresh_exports();self.schedule()

    def refresh_exports(self):
        self.w.export_list.clear()
        for path in self.saved_exports:
            item=QListWidgetItem(Path(path).name);item.setToolTip(path)
            item.setData(Qt.UserRole,path);self.w.export_list.addItem(item)
        self.w.export_list.setVisible(bool(self.saved_exports))

    def open_export(self,item):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        path=Path(item.data(Qt.UserRole))
        if path.is_file():QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:self.w.companion.say('Bu çıktı taşınmış dostum; metnin kayıtlı, yeniden dışa aktarabiliriz.')

    def toggle_bag(self):
        self.bag_manual=True
        self.w.bag_panel.setVisible(self.w.bag_panel.isHidden())

    def eventFilter(self,obj,event):
        if event.type()==QEvent.Show and not self.initialized:
            self.initialized=True
            QTimer.singleShot(0,self.restore_last)
        elif event.type()==QEvent.Resize and not self.bag_manual:
            self.w.bag_panel.setVisible(self.w.width()>=1200)
            self.w.history_panel.setVisible(self.w.width()>=1000)
        return False

    def restore_last(self):
        self.switch(self.store.last(),save_first=False)
        self.refresh()

    def schedule(self,*args):
        if not self.restoring and self.initialized:
            if not self.save_timer.isActive():
                self.save_timer.start()

    def snapshot(self):
        w=self.w
        segments=[]
        for i,s in enumerate(w.segments):
            data=asdict(s)
            if i<w.table.rowCount() and w.table.item(i,2):data['text']=w.table.item(i,2).text()
            segments.append(data)
        # Eski oturumlardaki föy verisini silmeden, etkin üründe kullanmadan koru.
        data=dict(self.legacy_payload)
        data.update({'version':2,'path':str(w.path) if w.path else '', 'segments':segments,
                     'exports':self.saved_exports,'notes':w.personal_notes.toPlainText(),
                     'target':w.target_lang.currentIndex(),'tab':0})
        return data

    def save(self):
        if self.restoring:return False
        w=self.w
        try:
            self.identity=self.store.save(self.identity,w.lesson_title.text().strip() or 'Yeni ders',self.snapshot())
        except (OSError,ValueError,TypeError, sqlite3.Error) as error:
            w.local_save_label.setText('Kaydedilemedi · dışa aktararak koru')
            w.local_save_label.setToolTip(str(error))
            return False
        w.local_save_label.setText('Otomatik kaydedildi · bu bilgisayarda')
        w.dirty=False
        self.refresh()
        return True

    def refresh(self,*args):
        w=self.w;w.lesson_list.clear()
        for identity,title,updated in self.store.list(w.history_search.text()):
            item=QListWidgetItem(title+'\n'+updated[:16].replace('T','  '))
            item.setData(Qt.UserRole,identity);w.lesson_list.addItem(item)
            if identity==self.identity:w.lesson_list.setCurrentItem(item)

    def locked(self):
        if self.w.transcribing():
            self.w.companion.say('Önce bu dersi bitirelim veya durduralım dostum; sonra diğerine geçebiliriz.')
            return True
        return False

    def new(self):
        if self.locked() or not self.save():return
        self.identity=None
        self.apply('Yeni ders',{})
        self.save()
        self.w.companion.say('Yeni bir sayfa açtık kankacım. Kaydını bırak, başlayalım!')

    def rename(self):
        title,ok=QInputDialog.getText(self.w,'Dersin adı','Yeni ad:',text=self.w.lesson_title.text())
        if ok and title.strip():
            self.w.lesson_title.setText(title.strip());self.save()

    def switch(self,identity,save_first=True):
        if not identity:return
        if save_first and (self.locked() or not self.save()):return
        try:
            loaded=self.store.load(identity)
        except (sqlite3.Error, ValueError) as error:
            self.w.local_save_label.setText('Ders açılamadı · mevcut metnin duruyor')
            self.w.local_save_label.setToolTip(str(error))
            return
        if loaded:
            self.identity=identity;self.apply(*loaded);self.refresh()

    def apply(self,title,data):
        from core import Segment
        w=self.w;self.restoring=True
        self.save_timer.stop()
        try:
            self.legacy_payload={key:data[key] for key in ("sheet","sources","speech_files","focus") if key in data}
            self.saved_exports=data.get('exports',[]);self.refresh_exports()
            w.lesson_title.setText(title);w.path=Path(data['path']) if data.get('path') else None
            w.segments=[];w.table.setRowCount(0);w.search.clear()
            for raw in data.get('segments',[]):w.append(Segment(**raw),100)
            w.elapsed_label.hide()
            w.expand_button.setChecked(False)
            w.personal_notes.setPlainText(data.get('notes',''))
            w.target_lang.setCurrentIndex(data.get('target',1))
            w.completion_banner.hide()
            w.file_label.setText(w.path.name if w.path else 'Bir veya birden fazla ses/video kaydını buraya bırak.')
            w.bag_media.setText(str(w.path) if w.path else 'Henüz ses kaydı eklenmedi.')
            missing=w.path is not None and not w.path.is_file()
            w.file_feedback.setText('Ses dosyası taşınmış. Yeniden seçebilirsin; kayıtlı metnin burada.' if missing else
                                    'Kaydın hazır.' if w.path else 'Dosyan henüz seçilmedi.')
            w.ready_icon.setVisible(bool(w.path) and not missing)
            w.start.setEnabled(bool(w.path) and not missing)
            w.status.setText('Kaldığın yerden devam edebilirsin.' if w.segments else 'Hazır. Kaydını getir, başlayalım.')
            w.progress.setValue(100 if w.segments else 0)
            w.tabs.setCurrentIndex(0);w.dirty=False
        finally:self.restoring=False


def install(w):
    w.studio=Studio(w)
