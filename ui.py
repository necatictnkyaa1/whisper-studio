"""Sıcak kâğıt teması ve yerel maskot; Qt Widgets, web servisi yok."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QProgressBar, QTableWidget, QHeaderView,
    QLineEdit, QAbstractItemView, QGraphicsDropShadowEffect, QMessageBox, QScrollArea, QLayout,
    QListWidget, QTextBrowser)

class Wave(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(140, 62)
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor('#194b40'))
        p.setPen(QPen(QColor('#422c22'), 3))
        p.drawRoundedRect(2, 2, 135, 56, 12, 12)
        p.setPen(QPen(QColor('#a6e1c8'), 5, Qt.SolidLine, Qt.RoundCap))
        for i, height in enumerate([6, 15, 9, 25, 14, 33, 10, 20, 8]):
            x = 25 + i * 11
            p.drawLine(x, 30 - height // 2, x, 30 + height // 2)

def label(text, name=None):
    result = QLabel(text)
    result.setWordWrap(True)
    if name:
        result.setObjectName(name)
    return result

class FileDropCard(QFrame):
    def __init__(self):
        super().__init__();self.setAcceptDrops(True)
    def dragEnterEvent(self,event):self.window().dragEnterEvent(event)
    def dragMoveEvent(self,event):self.window().dragEnterEvent(event)
    def dropEvent(self,event):self.window().dropEvent(event)


def card(name):
    widget = FileDropCard() if name=='yellowCard' else QFrame()
    widget.setObjectName(name)
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(0)
    shadow.setOffset(4, 5)
    shadow.setColor(QColor('#422c22'))
    widget.setGraphicsEffect(shadow)
    box = QVBoxLayout(widget)
    box.setContentsMargins(22, 18, 22, 18)
    box.setSpacing(12)
    return widget, box

def build_ui(w):
    w.resize(1120, 960)
    w.setMinimumSize(920, 640)
    root = QWidget()
    root.setObjectName('canvas')
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setWidget(root)
    w.setCentralWidget(scroll)
    layout = QVBoxLayout(root)
    layout.setContentsMargins(30, 24, 34, 28)
    layout.setSpacing(18)
    layout.setSizeConstraint(QLayout.SetMinimumSize)
    header = QHBoxLayout()
    heading = QVBoxLayout()
    heading.setSpacing(2)
    heading.addWidget(label('Whisper Studio', 'brand'))
    heading.addWidget(label('Bir kayıt, sayfalarca keşif.', 'subtitle'))
    header.addLayout(heading, 1)
    badge = label('  SENİN BİLGİSAYARINDA  ', 'badge')
    header.addWidget(badge)
    help_btn = QPushButton('İşlem nerede?')
    help_btn.clicked.connect(lambda: QMessageBox.information(w, 'Kayıt nerede işleniyor?',
        'Bu masaüstü sürümünde kayıt bu bilgisayarda işlenir.\n\n'
        'Bilgisayarının belleği ve kullanılabilir hızlandırıcısı kontrol edilir. '
        'Uygun kalite seçilir; kaynak yetersizse işlem başlamadan alternatif denenir.\n\n'
        'Model ilk kullanımda internetten indirilir. Kayıtların dışarı gönderilmez.\n\n'
        'Mobil sürüm henüz yok. Telefonun kendi donanımında çalışma ve '
        'izinle kişisel bilgisayara bağlanma, ayrı geliştirme aşamalarıdır.'))
    header.addWidget(help_btn)
    layout.addLayout(header)
    from mascot import Companion
    w.companion = Companion(w)

    upload, upload_box = card('yellowCard')
    w.upload_card = upload
    upload_row = QHBoxLayout()
    upload_row.addWidget(Wave())
    copy = QVBoxLayout()
    copy.addWidget(label('01  /  KAYDINI GETİR', 'eyebrow'))
    copy.addWidget(label('Dersi bırak, kelimeleri yakalayalım.', 'hero'))
    w.file_label = label('Ses veya videoyu buraya sürükle. İstersen dosyanı seç.', 'fileLabel')
    copy.addWidget(w.file_label)
    copy.addWidget(label('MP3 · M4A · WAV · MP4 · MKV ve diğer desteklenen kayıtlar', 'small'))
    upload_row.addLayout(copy, 1)
    w.open_btn = QPushButton('+  Dosya seç')
    w.open_btn.setObjectName('darkButton')
    w.open_btn.clicked.connect(w.choose)
    upload_row.addWidget(w.open_btn)
    upload_box.addLayout(upload_row)
    confirmation = QHBoxLayout()
    w.ready_icon = QLabel()
    icon = QPixmap(32, 32)
    icon.fill(Qt.transparent)
    painter = QPainter(icon)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor('#194b40'))
    painter.drawEllipse(1, 1, 30, 30)
    painter.setPen(QPen(QColor('#b6e2ce'), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(9, 16, 14, 21)
    painter.drawLine(14, 21, 23, 11)
    painter.end()
    w.ready_icon.setPixmap(icon)
    w.ready_icon.setFixedSize(32, 32)
    w.ready_icon.hide()
    confirmation.addWidget(w.ready_icon)
    w.file_feedback = label('Dosyan henüz seçilmedi.', 'fileFeedback')
    confirmation.addWidget(w.file_feedback, 1)
    upload_box.addLayout(confirmation)
    layout.addWidget(upload)

    settings, settings_box = card('paperCard')
    w.settings_card = settings
    caption = QHBoxLayout()
    caption.addWidget(label('02  /  NASIL BİR METİN İSTERSİN?', 'eyebrow'), 1)
    caption.addWidget(label('Gerekli dosyalar ilk kullanımda indirilir. Sonra internetsiz çalışabilirsin.', 'small'))
    settings_box.addLayout(caption)
    row = QHBoxLayout()
    w.target_lang = QComboBox()
    w.target_lang.addItems(['Orijinal dili koru', 'Türkçe', 'İngilizce'])
    w.target_lang.setCurrentIndex(1)
    row.addWidget(label('Metnin hangi dilde olsun?', 'fieldLabel'))
    row.addWidget(w.target_lang, 1)
    w.target_lang.setAccessibleName('Çıktı dili')
    settings_box.addLayout(row)
    w.translation_hint = label('Orijinal dili koru: konuşma hangi dildeyse metin o dilde yazılır.', 'small')
    def update_translation_hint():
        target = w.target_lang.currentIndex()
        w.translation_hint.setText('Orijinal dili koru: konuşma hangi dildeyse metin o dilde yazılır.' if target == 0 else
            'İngilizce ve Türkçe arasında yerel çeviri yapılır. Gerekli dosyalar ilk seferinde otomatik indirilir; orijinal metin korunur.')
    w.target_lang.currentIndexChanged.connect(update_translation_hint)
    update_translation_hint()
    settings_box.addWidget(w.translation_hint)
    settings_box.addWidget(label('Konuşulan dilleri ben algılarım. Bilgisayarına uygun en yüksek kaliteyi otomatik seçerim.', 'small'))
    bottom = QHBoxLayout()
    w.offline = QCheckBox('İnternetsiz çalış · indirme yapma')
    bottom.addWidget(w.offline, 1)
    w.start = QPushButton('Yazıya dönüştür  →')
    w.start.setObjectName('mintButton')
    w.start.clicked.connect(w.begin)
    w.start.setEnabled(False)
    w.stop = QPushButton('Durdur')
    w.stop.setEnabled(False)
    w.stop.clicked.connect(w.cancel)
    bottom.addWidget(w.stop)
    bottom.addWidget(w.start)
    settings_box.addLayout(bottom)
    layout.addWidget(settings)

    notebook, notebook_box = card('paperCard')
    w.notebook_card = notebook
    notes_header = QHBoxLayout()
    notes_header.addWidget(label('03  /  DERS DEFTERİN', 'eyebrow'), 1)
    notes_header.addWidget(label('Zamanı belli. Düzenlemesi sende.', 'small'))
    w.expand_button = QPushButton('Genişlet')
    w.expand_button.setCheckable(True)
    w.expand_button.toggled.connect(w.set_reading_mode)
    notes_header.addWidget(w.expand_button)
    w.read_stop = QPushButton('Durdur')
    w.read_stop.clicked.connect(w.cancel)
    w.read_stop.hide()
    notes_header.addWidget(w.read_stop)
    taller = QPushButton('Alanı uzat +')
    taller.clicked.connect(lambda: w.table.setMinimumHeight(w.table.minimumHeight() + 200))
    notes_header.addWidget(taller)
    notebook_box.addLayout(notes_header)
    w.completion_banner = label('', 'completion')
    w.completion_banner.hide()
    notebook_box.addWidget(w.completion_banner)
    w.progress = QProgressBar()
    w.progress.setValue(0)
    w.progress.setFixedHeight(16)
    notebook_box.addWidget(w.progress)
    w.status = label('Hazır. Bir kayıt seçerek başlayalım.', 'status')
    notebook_box.addWidget(w.status)
    w.elapsed_label = label('', 'small')
    w.elapsed_label.hide()
    notebook_box.addWidget(w.elapsed_label)
    w.search = QLineEdit()
    w.search.setPlaceholderText('Defterinde bir kelime ara…')
    w.search.setClearButtonEnabled(True)
    w.search.setAccessibleName('Transkriptte ara')
    w.search.textChanged.connect(w.filter_rows)
    notebook_box.addWidget(w.search)
    w.table = QTableWidget(0, 5)
    w.table.setHorizontalHeaderLabels(['Başlangıç', 'Bitiş', 'Çıktı metni · çift tıkla, düzenle', 'Orijinal metin', 'Dil / işlem'])
    w.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
    w.table.setColumnWidth(0, 108)
    w.table.setColumnWidth(1, 108)
    w.table.setColumnWidth(3, 280)
    w.table.setColumnHidden(3, True)
    w.table.setColumnWidth(4, 150)
    w.table.verticalHeader().hide()
    w.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    w.table.setSelectionBehavior(QAbstractItemView.SelectRows)
    w.table.setAlternatingRowColors(True)
    w.table.setWordWrap(True)
    w.table.itemChanged.connect(w.changed)
    w.table.setMinimumHeight(400)
    notebook_box.addWidget(w.table, 1)
    notebook.setMinimumHeight(370)
    w.show_original = QCheckBox('Orijinal metni de göster')
    w.show_original.toggled.connect(lambda checked: w.table.setColumnHidden(3, not checked))
    notebook_box.addWidget(w.show_original)
    w.table.setColumnHidden(4, True)
    w.export_original = QCheckBox('Kopyalama ve dışa aktarmada orijinal metni kullan')
    notebook_box.addWidget(w.export_original)
    exports = QHBoxLayout()
    exports.addWidget(label('Değişikliklerin dersine otomatik kaydedilir.', 'small'), 1)
    w.output_buttons = []
    for title, callback in [('Kopyala', w.copy), ('TXT kaydet', lambda: w.save(False)), ('SRT kaydet', lambda: w.save(True))]:
        btn = QPushButton(title)
        btn.clicked.connect(callback)
        exports.addWidget(btn)
        w.output_buttons.append(btn)
    notebook_box.addLayout(exports)
    layout.addWidget(notebook, 1)
    layout.addWidget(label('KAYIT → KELİMELER → SENİN NOTLARIN     ·     Hesap yok. API ücreti yok.', 'footer'))
    w.setStyleSheet(STYLE)

    # Yardımcı, eylemleri izler; metin üretimi veya ağ isteği yapmaz.
    w.expand_button.toggled.connect(lambda expanded: w.companion.say(
        'Defterini genişlettim dostum, rahat rahat okuyabilirsin.' if expanded else 'Normal görünüme döndük kankacım.'))
    w.table.itemChanged.connect(lambda item: w.companion.say(
        'Düzeltmen defterinde dostum. İşin bitince kaydetmeyi unutma.', automatic=True)
        if item.column() == 2 and w.table.state() == QAbstractItemView.EditingState else None)

    from studio import install
    install(w)

STYLE = '''
QWidget {color:#422c22;font-family:"Segoe UI";font-size:14px;}
QWidget#canvas {background:#f2e9d9;}
QLabel {background:transparent;border:0;}
QLabel#brand {font-size:32px;font-weight:800;letter-spacing:-1px;}
QLabel#subtitle {color:#766052;font-size:14px;}
QLabel#badge {background:#b6e2ce;border:2px solid #422c22;border-radius:8px;padding:8px;font-size:11px;font-weight:700;}
QFrame#yellowCard {background:#f7cb50;border:2px solid #422c22;border-radius:20px;}
QFrame#paperCard {background:#fffcf3;border:2px solid #422c22;border-radius:18px;}
QLabel#eyebrow {font-size:11px;font-weight:800;letter-spacing:1px;}
QLabel#hero {font-size:23px;font-weight:750;}
QLabel#fileLabel {font-size:14px;font-weight:600;}
QLabel#fileFeedback {background:#fff1b8;border-radius:8px;padding:10px;font-size:13px;font-weight:650;}
QLabel#fileFeedback[ready="true"] {background:#b6e2ce;color:#194b40;}
QLabel#small {color:#725b4d;font-size:12px;}
QLabel#fieldLabel {font-size:12px;font-weight:650;}
QLabel#status {font-size:12px;color:#5b5144;}
QLabel#completion {background:#b6e2ce;color:#194b40;border:2px solid #194b40;border-radius:12px;padding:16px;font-size:19px;font-weight:700;}
QLabel#footer {font-size:11px;color:#7b6658;}
QPushButton {background:#fffcf3;border:2px solid #422c22;border-radius:10px;padding:9px 14px;font-weight:650;}
QPushButton:hover {background:#fbe7a6;}
QPushButton:pressed {background:#e8c983;}
QPushButton:disabled {background:#eee8dd;color:#a39687;border-color:#c8bdae;}
QPushButton#darkButton {background:#422c22;color:#ffefb4;}
QPushButton#darkButton:hover {background:#654331;}
QPushButton#mintButton {background:#99d8bb;}
QPushButton#mintButton:hover {background:#b6e7d0;}
QPushButton:focus,QComboBox:focus,QLineEdit:focus {border:2px solid #23836a;}
QComboBox {background:#fff9e9;border:2px solid #b9a58b;border-radius:8px;padding:8px;min-height:20px;}
QComboBox::drop-down {border:0;width:22px;}
QComboBox QAbstractItemView {background:#fffcf3;selection-background-color:#b6e2ce;selection-color:#422c22;}
QCheckBox {spacing:8px;font-size:12px;}
QCheckBox::indicator {width:17px;height:17px;border:2px solid #92795d;border-radius:5px;background:#fffcf3;}
QCheckBox::indicator:checked {background:#23836a;border:2px solid #194b40;}
QLineEdit {background:#f6f0e3;border:2px solid #d7c7af;border-radius:8px;padding:7px 10px;}
QTableWidget {background:#fffcf3;alternate-background-color:#faf3e3;border:0;gridline-color:#e6dac3;selection-background-color:#b6e2ce;selection-color:#422c22;}
QTableWidget::item {padding:9px 4px;}
QHeaderView::section {background:#f6e6b3;border:0;border-bottom:2px solid #d8bd79;padding:8px;color:#5d4430;font-size:12px;font-weight:650;}
QProgressBar {background:#e8deca;border:0;border-radius:7px;text-align:center;font-size:10px;color:#194b40;}
QProgressBar::chunk {background:#8bd0b1;border-radius:7px;}
QScrollBar:vertical {background:#f1e8d6;width:10px;border-radius:5px;}
QScrollBar::handle:vertical {background:#bca88c;min-height:25px;border-radius:5px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
QMessageBox {background:#fffcf3;}
QListWidget#sourceList {background:#faf3e3;border:2px solid #d7c7af;border-radius:8px;padding:4px;font-size:13px;}
QListWidget#sourceList::item {padding:4px;}
QListWidget#sourceList::item:selected {background:#b6e2ce;color:#422c22;}
'''
