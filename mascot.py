"""Yerel, sürüklenebilir ve işlem durumuna duyarlı Misket."""
import math
import time
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint, QRectF, QSettings
from PySide6.QtGui import QColor, QPainter, QPen, QRegion
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu


class Companion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(290, 230)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAccessibleName('Misket, sürüklenebilir ders arkadaşın')
        self.setToolTip('Beni sürükleyebilirsin. Yardım ve sessize alma için sağ tıkla.')
        self.setCursor(Qt.OpenHandCursor)
        self.mood = 'calm'
        self.job = None
        self.phase = 0
        self.reaction_at = -100.0
        self.reaction = None
        self.lean = 0.0
        self.drag_start = None
        self.last_spoke = 0
        self.muted = False
        self.drag_origin = None
        self.dragged = False
        self.settings = QSettings('WhisperStudio', 'Misket')
        self.position = self.settings.value('position', None)
        self.bubble = QWidget(self)
        self.bubble.setGeometry(0, 0, 280, 104)
        self.bubble.setStyleSheet('background:#fff4c9;border:2px solid #806440;border-radius:16px;')
        layout = QVBoxLayout(self.bubble)
        layout.setContentsMargins(12, 8, 12, 8)
        self.heading = QLabel('Merhaba, ben Misket!')
        self.message = QLabel('Kaydını getir dostum, birlikte başlayalım.')
        for label in (self.heading, self.message):
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)
            label.setStyleSheet('border:0;background:transparent;color:#422c22;font-size:13px;')
            layout.addWidget(label)
        self.heading.setStyleSheet('border:0;background:transparent;color:#422c22;font-weight:bold;')
        self.bubble.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_bubble)
        self.hide_timer.start(7000)
        self.ready_timer = QTimer(self)
        self.ready_timer.setSingleShot(True)
        self.ready_timer.timeout.connect(lambda: self.say('Yüklendi kankacım! Hazırsan yazıya dönüştürelim.', 'Kaydın hazır'))
        self.animation = QTimer(self)
        self.animation.setInterval(25)
        self.animation.timeout.connect(self.animate)
        self.animation.start()
        self.check_in = QTimer(self)
        self.check_in.setInterval(90000)
        self.check_in.timeout.connect(self.reassure)
        parent.installEventFilter(self)
        QTimer.singleShot(0, self.place)

    def hide_bubble(self):
        self.bubble.hide()
        self.update_mask()

    def update_mask(self):
        region = QRegion(147, 105, 143, 125)
        if not self.bubble.isHidden():
            region = region.united(QRegion(self.bubble.geometry()))
        self.setMask(region)

    def place(self):
        parent = self.parentWidget()
        max_x, max_y = max(0, parent.width()-self.width()-12), max(0, parent.height()-self.height()-12)
        try:
            x, y = self.position if self.position is not None else (1, 1)
            self.move(round(float(x)*max_x), round(float(y)*max_y))
        except (TypeError, ValueError):
            self.move(max_x, max_y)
        self.raise_()
        self.update_mask()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.Show):
            self.place()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_origin = event.globalPosition().toPoint() - self.pos()
            self.dragged = False
            self.drag_start = event.globalPosition().toPoint()
            self.react('touch')
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drag_origin is not None:
            p = event.globalPosition().toPoint() - self.drag_origin
            bounds = self.parentWidget().rect()
            target = QPoint(max(0, min(p.x(), bounds.width()-self.width())),
                            max(0, min(p.y(), bounds.height()-self.height())))
            self.dragged |= (event.globalPosition().toPoint()-self.drag_start).manhattanLength() > 5
            self.lean = max(-18, min(18, (target.x()-self.x()) * 1.5))
            if self.dragged:
                self.reaction = 'drag'
            self.move(target)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self.drag_origin = None
        self.setCursor(Qt.OpenHandCursor)
        if self.dragged:
            self.react('land')
            parent = self.parentWidget()
            self.position = [self.x()/max(1,parent.width()-self.width()-12),
                             self.y()/max(1,parent.height()-self.height()-12)]
            self.position = [max(0,min(1,v)) for v in self.position]
            self.settings.setValue('position', self.position)
        else:
            self.react('touch')
            self.say('Heey, buradayım kankacım! Birlikte hallederiz.', automatic=True)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction('Beni sağ alta al', self.reset_position)
        quiet = menu.addAction('Konuşmaları sessize al')
        quiet.setCheckable(True)
        quiet.setChecked(self.muted)
        quiet.toggled.connect(self.set_muted)
        menu.addAction('Nasıl başlayayım?', lambda: self.say('01’de kaydını seç, çıktı dilini belirle ve Yazıya dönüştür’e bas. Gerisini birlikte hallederiz.'))
        menu.exec(event.globalPos())

    def reset_position(self):
        self.position = None
        self.settings.remove('position')
        self.place()

    def set_muted(self, value):
        self.muted = value
        if value:
            self.hide_bubble()

    def say(self, text, heading='Misket yanında', automatic=False):
        if self.muted or (automatic and time.monotonic()-self.last_spoke < 75):
            return
        self.heading.setText(heading)
        self.message.setText(text)
        self.bubble.show()
        self.update_mask()
        self.last_spoke = time.monotonic()
        self.hide_timer.start(7500)
        self.raise_()

    def file_loading(self):
        self.ready_timer.stop()
        self.mood = 'working'
        self.say('Kaydın yükleniyor dostum', 'Kaydını aldım')

    def file_ready(self):
        self.mood = 'happy'
        self.ready_timer.start(1600)

    def start_job(self, kind):
        self.ready_timer.stop()
        self.job = kind
        self.mood = 'working'
        self.say('Kaydını kelime kelime yakalamaya başlıyorum dostum.')
        self.check_in.start()

    def progress(self, value):
        if self.job:
            self.mood = 'excited' if value >= 85 else ('waiting' if value < 35 else 'working')

    def end_job(self, text, success=True):
        self.job = None
        self.check_in.stop()
        self.mood = 'happy' if success else 'calm'
        if success:
            self.react('celebrate')
        self.say(text, 'Hazır kankacım!' if success else 'Yanındayım dostum')

    def activity(self, message):
        value = message.casefold()
        if 'tamamlanamadı' in value or 'hata' in value:
            self.end_job('Bir pürüz çıktı dostum. Oluşan metnin duruyor; ayrıntıyı işlem bölümünde görebilirsin.', False)
        elif 'durdur' in value:
            self.end_job('Tamam dostum, güvenle durduruyorum. Hazır olduğunda devam ederiz.', False)

    def reassure(self):
        if self.job:
            self.say('Buradayım dostum, dersin üzerinde çalışmaya devam ediyorum. Sen biraz dinlenebilirsin.', automatic=True)

    def react(self, kind):
        self.reaction = kind
        self.reaction_at = time.monotonic()
        self.update()

    def animate(self):
        self.phase += .09
        if self.reaction != 'drag':
            self.lean *= .82
            if time.monotonic()-self.reaction_at > 1.4:
                self.reaction = None
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Ayrı çizilen göz ve ağız, yüz ifadesini gerçek zamanlı değiştirir.
        bob = math.sin(self.phase) * (3 if self.mood == 'excited' else 1.5)
        age = time.monotonic()-self.reaction_at
        bounce = 0
        squash = 1 + math.sin(self.phase)*.012
        if self.reaction in ('touch', 'celebrate'):
            bounce = -abs(math.sin(age*9))*15*max(0,1-age/1.4)
        elif self.reaction == 'land':
            squash += math.sin(age*15)*.16*max(0,1-age/1.0)
        elif self.reaction == 'drag':
            bounce = -6
        p.translate(157+64, 110+bob+bounce+102)
        p.rotate(self.lean)
        p.scale(squash, 1/squash)
        p.translate(-64,-102)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(66,44,34,30))
        p.drawEllipse(QRectF(12,103,106,8))
        p.setPen(QPen(QColor('#64452c'), 2.5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(QColor('#efb52f'))
        p.drawEllipse(QRectF(29,88,22,15)); p.drawEllipse(QRectF(76,88,22,15))
        p.setBrush(QColor('#ffda56'))
        p.drawEllipse(QRectF(7,50,22,28))
        p.save()
        p.translate(108,56)
        if self.reaction in ('touch','celebrate'):
            p.rotate(-40+math.sin(age*18)*25)
        elif self.reaction == 'drag':
            p.rotate(-55)
        p.drawEllipse(QRectF(-9,-9,22,28))
        p.restore()
        p.drawRoundedRect(QRectF(21,20,87,74),30,30)
        for x,y,r in [(27,18,28),(45,9,32),(68,14,31)]:
            p.drawEllipse(QRectF(x,y,r,r))
        p.setBrush(QColor('#ffda56')); p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(25,28,79,59),20,20)
        p.setPen(QPen(QColor('#467c68'),5))
        p.drawArc(QRectF(15,10,97,81),0,180*16)
        p.setBrush(QColor('#a7dec4')); p.setPen(QPen(QColor('#467c68'),2))
        p.drawRoundedRect(QRectF(14,37,14,30),6,6); p.drawRoundedRect(QRectF(100,37,14,30),6,6)
        p.setPen(QPen(QColor('#422c22'),3,Qt.SolidLine,Qt.RoundCap))
        blink = self.phase % 13 < .3
        for x in (48,78):
            if blink or self.mood == 'waiting':
                p.drawLine(x-3,48,x+3,48)
            elif self.mood in ('happy','excited') or self.reaction in ('touch','celebrate'):
                p.drawArc(QRectF(x-4,43,9,10),0,180*16)
            else:
                p.setBrush(QColor('#422c22')); p.drawEllipse(QRectF(x-3,43,6,10))
        p.setBrush(QColor('#ec9c65')); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(35,56,12,6)); p.drawEllipse(QRectF(82,56,12,6))
        p.setPen(QPen(QColor('#422c22'),2.5,Qt.SolidLine,Qt.RoundCap))
        if self.mood == 'excited':
            p.setBrush(QColor('#70412d')); p.drawEllipse(QRectF(58,56,13,13))
        else:
            p.drawArc(QRectF(56,51,16,15),180*16,180*16)
        p.setPen(Qt.NoPen); p.setBrush(QColor('#fff0af'))
        p.drawEllipse(QRectF(47,75,36,16))
        p.setPen(QPen(QColor('#70aa8d'),2,Qt.SolidLine,Qt.RoundCap))
        for i in range(5):
            h = 3+abs(math.sin(self.phase+i))*6
            p.drawLine(QPoint(55+i*5,int(83-h/2)),QPoint(55+i*5,int(83+h/2)))
