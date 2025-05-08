import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import math
from scipy import optimize
from copy import deepcopy as dc

class RigidLink(qtw.QGraphicsItem):
    def __init__(self, stX=0, stY=0, enX=1, enY=1, radius=10, mass=10, parent=None, pen=None, brush=None, name='RigidLink',
                 label_pen=qtg.QPen(qtc.Qt.black)):
        super().__init__(parent)
        self.pen = pen
        self.label_pen = label_pen
        self.brush = brush
        self.name = name
        self.stPt = qtc.QPointF(stX, stY)
        self.enPt = qtc.QPointF(enX, enY)
        self.radius = radius
        self.mass = mass
        self.angle = self.linkAngle()
        self.rect = qtc.QRectF(-self.radius, -self.radius, self.length + self.radius, self.radius)
        self.transform = qtg.QTransform()
        self.transform.reset()

    def boundingRect(self):
        boundingRect = self.transform.mapRect(self.rect)
        return boundingRect

    def deltaY(self):
        self.DY = self.enPt.y() - self.stPt.y()
        return self.DY

    def deltaX(self):
        self.DX = self.enPt.x() - self.stPt.x()
        return self.DX

    def linkLength(self):
        self.length = math.sqrt(math.pow(self.deltaX(), 2) + math.pow(self.deltaY(), 2))
        return self.length

    def linkAngle(self):
        self.linkLength()
        if self.length == 0.0:
            self.angle = 0
        else:
            self.angle = math.acos(self.DX / self.length)
            self.angle *= -1 if (self.DY > 0) else 1
        self.rangeAngle()
        return self.angle

    def rangeAngle(self):
        while (self.angle < 0):
            self.angle += 2 * math.pi
        while (self.angle > 2 * math.pi):
            self.angle -= 2 * math.pi

    def AngleDeg(self):
        return self.angle * 180 / math.pi

    def paint(self, painter, option, widget=None):
        path = qtg.QPainterPath()
        len = self.linkLength()
        angLink = self.linkAngle() * 180 / math.pi
        rectSt = qtc.QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        rectEn = qtc.QRectF(self.length - self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        centerLinePen = qtg.QPen()
        centerLinePen.setStyle(qtc.Qt.DashDotLine)
        r, g, b, a = self.pen.color().getRgb()
        centerLinePen.setColor(qtg.QColor(r, g, b, 128))
        centerLinePen.setWidth(1)
        p1 = qtc.QPointF(0, 0)
        p2 = qtc.QPointF(len, 0)
        painter.setPen(centerLinePen)
        painter.drawLine(p1, p2)
        path.arcMoveTo(rectSt, 90)
        path.arcTo(rectSt, 90, 180)
        path.lineTo(self.length, self.radius)
        path.arcMoveTo(rectEn, 270)
        path.arcTo(rectEn, 270, 180)
        path.lineTo(0, -self.radius)
        if self.pen is not None:
            painter.setPen(self.pen)
        if self.label_pen is None:
            self.label_pen = qtg.QPen(qtg.QColor('red'))
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)
        pivotStart = qtc.QRectF(-self.radius / 6, -self.radius / 6, self.radius / 3, self.radius / 3)
        pivotEnd = qtc.QRectF(self.length - self.radius / 6, -self.radius / 6, self.radius / 3, self.radius / 3)
        painter.drawEllipse(pivotStart)
        painter.drawEllipse(pivotEnd)
        self.rect = qtc.QRectF(-self.radius, -self.radius, self.length + 2 * self.radius, 2 * self.radius)
        painter.setBrush(qtg.QBrush(qtc.Qt.black))
        painter.setPen(self.label_pen)
        painter.setFont(qtg.QFont("Times", self.radius))
        painter.drawText(self.rect, qtc.Qt.AlignCenter, self.name)
        self.transform.reset()
        self.transform.translate(self.stPt.x(), self.stPt.y())
        self.transform.rotate(-angLink)
        self.setTransform(self.transform)
        self.transform.reset()
        stTT = self.name + "\nstart: ({:0.3f}, {:0.3f})\nend:({:0.3f},{:0.3f})\nlength: {:0.3f}\nangle: {:0.3f}".format(
            self.stPt.x(), self.stPt.y(), self.enPt.x(), self.enPt.y(), self.length, self.angle * 180 / math.pi)
        self.setToolTip(stTT)

class RigidPivotPoint(qtw.QGraphicsItem):
    def __init__(self, ptX=0, ptY=0, pivotHeight=10, pivotWidth=10, parent=None, pen=None, brush=None, rotation=0,
                 name='RigidPivotPoint', label_pen=None):
        super().__init__(parent)
        self.x = ptX
        self.y = ptY
        self.pt = qtc.QPointF(ptX, ptY)
        self.pen = pen if pen is not None else qtg.QPen(qtg.QColor('black'))
        self.brush = brush
        self.height = pivotHeight
        self.width = pivotWidth
        self.radius = min(self.height, self.width) / 4
        self.rect = qtc.QRectF(self.x - self.width / 2, self.y - self.radius, self.width, self.height + self.radius)
        self.rotationAngle = rotation
        self.name = name
        self.transformation = qtg.QTransform()
        stTT = self.name + "\nx={:0.3f}, y={:0.3f}".format(self.x, self.y)
        self.setToolTip(stTT)

    def boundingRect(self):
        bounding_rect = self.transformation.mapRect(self.rect)
        return bounding_rect

    def rotate(self, angle):
        self.rotationAngle = angle

    def paint(self, painter, option, widget=None):
        path = qtg.QPainterPath()
        radius = min(self.height, self.width) / 2
        name = self.name
        H = math.sqrt(math.pow(self.width / 2, 2) + math.pow(self.height, 2))
        phi = math.asin(radius / H)
        theta = math.asin(self.height / H)
        ang = math.pi - phi - theta
        l = H * math.cos(phi)
        x1 = self.width / 2
        y1 = self.height
        path.moveTo(x1, y1)
        x2 = l * math.cos(ang)
        y2 = l * math.sin(ang)
        path.lineTo(x1 + x2, y1 - y2)
        pivotRect = qtc.QRectF(-radius, -radius, 2 * radius, 2 * radius)
        stAng = math.pi / 2 - phi - theta
        spanAng = math.pi - 2 * stAng
        path.arcTo(pivotRect, stAng * 180 / math.pi, spanAng * 180 / math.pi)
        x4 = -self.width / 2
        y4 = +self.height
        path.lineTo(x4, y4)
        if self.pen is not None:
            painter.setPen(self.pen)
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)
        pivotPtRect = qtc.QRectF(-radius / 4, -radius / 4, radius / 2, radius / 2)
        painter.drawEllipse(pivotPtRect)
        x5 = -self.width
        x6 = +self.width
        painter.drawLine(x5, y4, x6, y4)
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        hatchbrush = qtg.QBrush(qtc.Qt.BDiagPattern)
        brushTransform = qtg.QTransform()
        brushTransform.scale(0.5, 0.5)
        hatchbrush.setTransform(brushTransform)
        painter.setPen(penOutline)
        painter.setBrush(hatchbrush)
        painter.setFont(qtg.QFont("Arial", 3))
        support = qtc.QRectF(x5, y4, self.width * 2, self.height)
        painter.drawRect(support)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawText(support, qtc.Qt.AlignCenter, name)
        self.rect = qtc.QRectF(-self.width, -self.radius, self.width * 2, self.height * 2 + self.radius)
        self.transformation.reset()
        self.transformation.translate(self.x, self.y)
        self.transformation.rotate(self.rotationAngle)
        self.setTransform(self.transformation)
        self.transformation.reset()

class Tracer(qtw.QGraphicsItem):
    def __init__(self, x=0, y=0, pen=None, penOutline=qtg.QPen(qtc.Qt.black)):
        super().__init__()
        self.pts = [qtc.QPointF(x, y)]
        self.rect = qtc.QRectF(-5, -5, 10, 10)
        self.pen = pen
        self.penOutline = penOutline

    def boundingRect(self):
        bounding_rect = self.rect
        return bounding_rect

    def lastPt(self):
        return self.pts[len(self.pts) - 1]

    def paint(self, painter, option, widget=None):
        if self.pen is not None:
            painter.setPen(self.pen)
        path = qtg.QPainterPath()
        if len(self.pts) > 0:
            path.moveTo(self.pts[0])
        for i in range(1, len(self.pts)):
            path.lineTo(self.pts[i])
        painter.drawPath(path)
        pt = self.pts[len(self.pts) - 1]
        painter.setPen(self.penOutline)
        painter.drawEllipse(qtc.QRectF(pt.x() - 2.5, pt.y() - 2.5, 5, 5))

class LinearSpring(qtw.QGraphicsItem):
    def __init__(self, ptSt=qtc.QPointF(0, 0), ptEn=qtc.QPointF(1, 1), coilsWidth=10, coilsLength=30, parent=None,
                 pen=None, name='Spring', label=None, k=10, nCoils=6):
        super().__init__(parent)
        self.stPt = ptSt
        self.enPt = ptEn
        self.freeLength = self.getLength()
        self.DL = self.length - self.freeLength
        self.centerPt = (self.stPt + self.enPt) / 2.0
        self.force = 0
        self.pen = pen
        self.coilsWidth = coilsWidth
        self.coilsLength = coilsLength
        self.top = -self.coilsLength / 2
        self.left = -self.coilsWidth / 2
        self.rect = qtc.QRectF(self.left, self.top, self.coilsWidth, self.coilsLength)
        self.name = name
        self.label = label
        self.k = k
        self.nCoils = nCoils
        self.transformation = qtg.QTransform()
        stTT = self.name + "\nx={:0.1f}, y={:0.1f}\nk = {:0.1f}".format(self.centerPt.x(), self.centerPt.y(), self.k)
        self.setToolTip(stTT)

    def setk(self, k=None):
        if k is not None:
            self.k = k
            stTT = self.name + "\nx={:0.3f}, y={:0.3f}\nk = {:0.3f}".format(self.stPt.x(), self.stPt.y(), self.k)
            self.setToolTip(stTT)

    def boundingRect(self):
        bounding_rect = self.transformation.mapRect(self.rect)
        return bounding_rect

    def getLength(self):
        p = self.enPt - self.stPt
        self.length = math.sqrt(p.x() ** 2 + p.y() ** 2)
        return self.length

    def getForce(self):
        self.force = self.k * self.getDL()
        return self.force

    def getDL(self):
        self.DL = self.length - self.freeLength
        return self.DL

    def getAngleDeg(self):
        p = self.enPt - self.stPt
        self.angleRad = math.atan2(p.y(), p.x())
        self.angleDeg = 180.0 / math.pi * self.angleRad
        return self.angleDeg

    def paint(self, painter, option, widget=None):
        self.transformation.reset()
        if self.pen is not None:
            painter.setPen(self.pen)
        self.getLength()
        self.getAngleDeg()
        self.getDL()
        ht = self.coilsWidth
        wd = self.coilsLength + self.DL
        top = -ht / 2
        left = -wd / 2
        right = wd / 2
        self.rect = qtc.QRectF(left, top, wd, ht)
        painter.drawLine(qtc.QPointF(left, 0), qtc.QPointF(left, ht / 2))
        dX = wd / (self.nCoils)
        for i in range(self.nCoils):
            painter.drawLine(qtc.QPointF(left + i * dX, ht / 2), qtc.QPointF(left + (i + 0.5) * dX, -ht / 2))
            painter.drawLine(qtc.QPointF(left + (i + 0.5) * dX, -ht / 2), qtc.QPointF(left + (i + 1) * dX, ht / 2))
        painter.drawLine(qtc.QPointF(right, ht / 2), qtc.QPointF(right, 0))
        painter.drawLine(qtc.QPointF(-self.length / 2, 0), qtc.QPointF(left, 0))
        painter.drawLine(qtc.QPointF(right, 0), qtc.QPointF(self.length / 2, 0))
        nodeRad = 2
        stRec = qtc.QRectF(-self.length / 2 - nodeRad, -nodeRad, 2 * nodeRad, 2 * nodeRad)
        enRec = qtc.QRectF(self.length / 2 - nodeRad, -nodeRad, 2 * nodeRad, 2 * nodeRad)
        painter.drawEllipse(stRec)
        painter.drawEllipse(enRec)
        self.transformation.translate(self.stPt.x(), self.stPt.y())
        self.transformation.rotate(self.angleDeg)
        self.transformation.translate(self.length / 2, 0)
        self.setTransform(self.transformation)
        font = painter.font()
        font.setPointSize(6)
        painter.setFont(font)
        text = f"k = {self.k:0.1f} N/m, F = {self.force:0.2f} N"
        fm = qtg.QFontMetrics(painter.font())
        centerPt = (self.stPt + self.enPt) / 2
        painter.drawText(qtc.QPointF(-fm.width(text) / 2.0, fm.height() / 2.0), text)
        if self.label is not None:
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(qtc.QPointF((self.coilsWidth / 2.0) + 10, 0), self.label)
        self.transformation.reset()

class DashPot(qtw.QGraphicsItem):
    def __init__(self, ptSt=qtc.QPointF(0, 0), ptEn=qtc.QPointF(1, 1), dpWidth=10, dpLength=30, parent=None, pen=None,
                 name='Dashpot', label=None, c=10):
        super().__init__(parent)
        self.stPt = ptSt if isinstance(ptSt, qtc.QPointF) else qtc.QPointF(0, 0)
        self.enPt = ptEn if isinstance(ptEn, qtc.QPointF) else qtc.QPointF(1, 1)
        p = self.enPt - self.stPt
        self.length = math.sqrt(p.x() ** 2 + p.y() ** 2)
        self.freeLength = self.length
        self.DL = 0.0
        self.centerPt = qtc.QPointF((self.stPt.x() + self.enPt.x()) / 2.0, (self.stPt.y() + self.enPt.y()) / 2.0)
        self.pen = pen if pen else qtg.QPen(qtc.Qt.black)
        self.Width = dpWidth
        self.Length = dpLength
        self.conn1Len = (self.freeLength - self.Length) / 2 if self.freeLength > self.Length else 0
        self.conn2Len = self.freeLength / 2
        self.top = -self.Length / 2
        self.left = -self.Width / 2
        self.rect = qtc.QRectF(self.left, self.top, self.Width, self.Length)
        self.name = name
        self.label = label
        self.c = c
        self.previous_length = self.length
        self.previous_time = qtc.QTime.currentTime()
        self.current_force = 0.0
        self.transformation = qtg.QTransform()
        stTT = f"{self.name}\nx={self.centerPt.x():0.1f}, y={self.centerPt.y():0.1f}\nc={self.c:0.1f}"
        self.setToolTip(stTT)

    def updateForce(self):
        current_time = qtc.QTime.currentTime()
        current_length = self.getLength()
        delta_time = self.previous_time.msecsTo(current_time) / 1000.0
        if delta_time > 0:
            dl = current_length - self.previous_length
            velocity = dl / delta_time
            self.current_force = self.c * velocity
        else:
            self.current_force = 0.0
        self.previous_length = current_length
        self.previous_time = current_time
        return self.current_force

    def getLength(self):
        p = self.enPt - self.stPt
        self.length = math.sqrt(p.x() ** 2 + p.y() ** 2)
        return self.length

    def getAngleDeg(self):
        p = self.enPt - self.stPt
        self.angleRad = math.atan2(p.y(), p.x())
        self.angleDeg = 180.0 / math.pi * self.angleRad
        return self.angleDeg

    def getDL(self):
        self.DL = self.length - self.freeLength
        return self.DL

    def boundingRect(self):
        bounding_rect = self.transformation.mapRect(self.rect)
        return bounding_rect

    def paint(self, painter, option, widget=None):
        self.transformation.reset()
        if self.pen is not None:
            painter.setPen(self.pen)
        self.getLength()
        self.getAngleDeg()
        self.getDL()
        ht = self.Width
        wd = self.Length
        top = -ht / 2
        left = self.conn1Len
        right = left + wd
        self.rect = qtc.QRectF(left, top, wd, ht)
        painter.drawLine(qtc.QPointF(left, -ht / 2), qtc.QPointF(left, ht / 2))
        painter.drawLine(qtc.QPointF(left, -ht / 2), qtc.QPointF(right, -ht / 2))
        painter.drawLine(qtc.QPointF(left, ht / 2), qtc.QPointF(right, ht / 2))
        painter.drawLine(qtc.QPointF(left + wd / 2 + self.DL, ht / 2 * 0.95),
                         qtc.QPointF(left + wd / 2 + self.DL, -ht / 2 * 0.95))
        painter.drawLine(qtc.QPointF(0, 0), qtc.QPointF(left, 0))
        painter.drawLine(qtc.QPointF(left + wd / 2 + self.DL, 0),
                         qtc.QPointF(self.conn2Len + left + wd / 2 + self.DL, 0))
        nodeRad = 2
        painter.drawEllipse(qtc.QPointF(0, 0), nodeRad, nodeRad)
        painter.drawEllipse(qtc.QPointF(self.length, 0), nodeRad, nodeRad)
        self.transformation.translate(self.stPt.x(), self.stPt.y())
        self.transformation.rotate(self.angleDeg)
        self.setTransform(self.transformation)
        font = painter.font()
        font.setPointSize(6)
        painter.setFont(font)
        text = f"c = {self.c:0.1f} N·s/m, F = {self.current_force:0.2f} N"
        fm = qtg.QFontMetrics(font)
        text_width = fm.width(text)
        text_x = (self.length / 2) - (text_width / 2)
        text_y = self.Width / 2 + fm.height()
        painter.drawText(qtc.QPointF(text_x, text_y), text)
        self.transformation.reset()

class FourBarLinkage_Model:
    def __init__(self):
        self.GroundLink = RigidLink()
        self.InputLink = RigidLink()
        self.DragLink = RigidLink()
        self.OutputLink = RigidLink()
        self.Pivot0 = RigidPivotPoint()
        self.Pivot1 = RigidPivotPoint()
        self.Spring = LinearSpring()
        self.DashPot = DashPot()
        self.Tracer0 = Tracer()
        self.Tracer1 = Tracer()
        self.Tracer2 = Tracer()
        self.Tracer3 = Tracer()

    def setInputLength(self, L=10):
        self.InputLink.enPt.setX(self.InputLink.stPt.x() + math.cos(self.InputLink.angle) * L)
        self.InputLink.enPt.setY(self.InputLink.stPt.y() - math.sin(self.InputLink.angle) * L)
        self.InputLink.linkLength()
        self.DragLink.stPt.setX(self.InputLink.enPt.x())
        self.DragLink.stPt.setY(self.InputLink.enPt.y())

    def setOutputLength(self, L=10):
        self.OutputLink.enPt.setX(self.OutputLink.stPt.x() + math.cos(self.OutputLink.angle) * L)
        self.OutputLink.enPt.setY(self.OutputLink.stPt.y() - math.sin(self.OutputLink.angle) * L)
        self.OutputLink.linkLength()
        self.DragLink.enPt.setX(self.OutputLink.enPt.x())
        self.DragLink.enPt.setY(self.OutputLink.enPt.y())

    def moveLinkage(self, pt=qtc.QPointF(0, 0)):
        l1 = self.InputLink.length
        l2 = self.DragLink.length
        l3 = self.OutputLink.length
        x = pt.x()
        y = pt.y()
        if (x == self.InputLink.stPt.x()):
            self.angle1 = math.pi / 2 if y <= self.InputLink.stPt.y() else math.pi * 3.0 / 2.0
        else:
            self.angle1 = math.atan(-(y - self.InputLink.stPt.y()) / (x - self.InputLink.stPt.x()))
            self.angle1 += math.pi if x < self.InputLink.stPt.x() else 0
        if (self.OutputLink.enPt.x() == self.OutputLink.stPt.x()):
            self.angle2 = math.pi / 2 if self.OutputLink.enPt.y() < self.OutputLink.stPt.y() else math.pi * 3.0 / 2.0
        else:
            self.angle2 = math.atan(-(self.OutputLink.enPt.y() - self.DragLink.stPt.y()) / (
                    self.OutputLink.enPt.x() - self.OutputLink.stPt.x()))
            self.angle2 += math.pi if self.OutputLink.enPt.x() < self.OutputLink.stPt.x() else 0
        self.InputLink.enPt.setX(self.InputLink.stPt.x() + math.cos(self.angle1) * l1)
        self.InputLink.enPt.setY(self.InputLink.stPt.y() - math.sin(self.angle1) * l1)
        x1 = self.InputLink.enPt.x()
        y1 = self.InputLink.enPt.y()
        self.lTest = l2
        def fn1(angle2):
            x2 = self.OutputLink.stPt.x() + l3 * math.cos(angle2)
            y2 = self.OutputLink.stPt.y() - l3 * math.sin(angle2)
            self.lTest = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))
            return l2 - self.lTest
        result = optimize.fsolve(fn1, [self.angle2])
        if abs(self.lTest - l2) > 0.001:
            self.angle2 = self.prevBeta
            self.angle1 = self.prevAlpha
            self.InputLink.enPt.setX(self.InputLink.stPt.x() + math.cos(self.angle1) * l1)
            self.InputLink.enPt.setY(self.InputLink.stPt.y() - math.sin(self.angle1) * l1)
        else:
            self.angle2 = result[0]
            self.prevAlpha = self.angle1
            self.prevBeta = self.angle2
        self.OutputLink.enPt.setX(self.OutputLink.stPt.x() + l3 * math.cos(self.angle2))
        self.OutputLink.enPt.setY(self.OutputLink.stPt.y() - l3 * math.sin(self.angle2))
        pt1 = dc(self.InputLink.enPt)
        pt0 = dc(self.OutputLink.enPt)
        ptMid = (pt0 + pt1) / 2
        self.Tracer1.pts.append(pt1)
        self.Tracer0.pts.append(pt0)
        self.Tracer2.pts.append(ptMid)
        self.Tracer3.pts.append(ptMid + 0.5 * (pt0 - ptMid))
        self.Spring.enPt = dc(self.Tracer3.lastPt())
        self.Spring.getForce()
        self.DashPot.enPt = dc(self.Tracer3.lastPt())
        self.DashPot.updateForce()
        if len(self.Tracer1.pts) >= 1000:
            self.Tracer0.pts = self.Tracer0.pts[1:]
            self.Tracer1.pts = self.Tracer1.pts[1:]
            self.Tracer2.pts = self.Tracer2.pts[1:]
            self.Tracer3.pts = self.Tracer3.pts[1:]
        self.DragLink.stPt = self.InputLink.enPt
        self.DragLink.enPt = self.OutputLink.enPt

class FourBarLinkage_View:
    def __init__(self, gv_Main):
        self.gv_Main = gv_Main

    def setupGraphics(self):
        self.scene = qtw.QGraphicsScene()
        self.scene.setObjectName("MyScene")
        self.scene.setSceneRect(-200, -200, 400, 400)
        self.gv_Main.setScene(self.scene)
        self.setupPensAndBrushes()
        self.gv_Main.setViewportUpdateMode(qtw.QGraphicsView.FullViewportUpdate)

    def setupPensAndBrushes(self):
        self.penThick = qtg.QPen(qtc.Qt.darkGreen)
        self.penThick.setWidth(5)
        self.penMed = qtg.QPen(qtc.Qt.darkBlue)
        self.penMed.setStyle(qtc.Qt.SolidLine)
        self.penMed.setWidth(2)
        self.penLink = qtg.QPen(qtg.QColor("orange"))
        self.penLink.setWidth(1)
        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, 128))
        self.penTracer = qtg.QPen(qtc.Qt.blue)
        self.penTracerIcon = qtg.QPen(qtc.Qt.black)
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)
        self.brushHatch = qtg.QBrush()
        self.brushHatch.setStyle(qtc.Qt.DiagCrossPattern)
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, 128))
        self.brushLink = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))
        self.brushPivot = qtg.QBrush(qtg.QColor.fromHsv(0, 0, 128, 255))

    def BuildScene(self, FBL_M):
        self.scene.clear()
        self.drawAGrid(DeltaX=10, DeltaY=10, Height=400, Width=400, Pen=self.penGridLines, Brush=self.brushGrid)
        FBL_M.DragLink.stPt = qtc.QPointF(-100, -60)
        FBL_M.DragLink.enPt = qtc.QPointF(100, -150)
        FBL_M.Pivot0 = self.drawPivot(-100, 0, 10, 20)
        FBL_M.Pivot0.setTransformOriginPoint(qtc.QPointF(FBL_M.Pivot0.x, FBL_M.Pivot0.y))
        FBL_M.Pivot0.rotate(0)
        FBL_M.Pivot0.name = "RP 0"
        FBL_M.Pivot1 = self.drawPivot(60, 0, 10, 20)
        FBL_M.Pivot1.setTransformOriginPoint(qtc.QPointF(FBL_M.Pivot1.x, FBL_M.Pivot1.y))
        FBL_M.Pivot1.rotate(0)
        FBL_M.Pivot1.name = "RP 1"
        FBL_M.GroundLink = self.drawLinkage(FBL_M.Pivot0.x, FBL_M.Pivot0.y, FBL_M.Pivot1.x, FBL_M.Pivot1.y,
                                           radius=5, pen=self.penGridLines, brush=self.brushGrid)
        FBL_M.InputLink = self.drawLinkage(FBL_M.Pivot0.x, FBL_M.Pivot0.y, FBL_M.DragLink.stPt.x(),
                                           FBL_M.DragLink.stPt.y(), 5)
        FBL_M.DragLink = self.drawLinkage(FBL_M.DragLink.stPt.x(), FBL_M.DragLink.stPt.y(),
                                         FBL_M.DragLink.enPt.x(), FBL_M.DragLink.enPt.y(), 5)
        FBL_M.OutputLink = self.drawLinkage(FBL_M.Pivot1.x, FBL_M.Pivot1.y, FBL_M.DragLink.enPt.x(),
                                           FBL_M.DragLink.enPt.y(), 5)
        FBL_M.GroundLink.name = "Frame"
        FBL_M.InputLink.name = "Input"
        FBL_M.DragLink.name = "Coupler"
        FBL_M.OutputLink.name = "Output"
        FBL_M.Tracer0 = Tracer(x=100, y=-150, pen=self.penTracer)
        self.scene.addItem(FBL_M.Tracer0)
        FBL_M.Tracer1 = Tracer(x=-100, y=-60, pen=self.penTracer)
        self.scene.addItem(FBL_M.Tracer1)
        FBL_M.Tracer2 = Tracer(0, 0, pen=self.penTracer)
        FBL_M.Tracer2.pts[0] = (FBL_M.Tracer0.pts[0] + FBL_M.Tracer1.pts[0]) / 2
        self.scene.addItem(FBL_M.Tracer2)
        FBL_M.Tracer3 = Tracer(0, 0, pen=self.penTracer)
        FBL_M.Tracer3.pts[0] = (FBL_M.Tracer0.pts[0] + FBL_M.Tracer2.pts[0]) / 2
        self.scene.addItem(FBL_M.Tracer3)
        print(f"Pivot1.pt: {FBL_M.Pivot1.pt}, Tracer3.lastPt: {FBL_M.Tracer3.lastPt()}")
        FBL_M.Spring = LinearSpring(FBL_M.Pivot1.pt, FBL_M.Tracer3.lastPt(), 20, 50)
        self.scene.addItem(FBL_M.Spring)
        FBL_M.DashPot = DashPot(FBL_M.Pivot1.pt, FBL_M.Tracer3.lastPt(), 10, 80)
        self.scene.addItem(FBL_M.DashPot)

    def drawAGrid(self, DeltaX=10, DeltaY=10, Height=200, Width=200, CenterX=0, CenterY=0, Pen=None, Brush=None, SubGrid=None):
        height = self.scene.sceneRect().height() if Height is None else Height
        width = self.scene.sceneRect().width() if Width is None else Width
        left = self.scene.sceneRect().left() if CenterX is None else (CenterX - width / 2.0)
        right = self.scene.sceneRect().right() if CenterX is None else (CenterX + width / 2.0)
        top = self.scene.sceneRect().top() if CenterY is None else (CenterY - height / 2.0)
        bottom = self.scene.sceneRect().bottom() if CenterY is None else (CenterY + height / 2.0)
        Dx = DeltaX
        Dy = DeltaY
        pen = qtg.QPen() if Pen is None else Pen
        if Brush is not None:
            rect = self.drawARectangle(left, top, width, height)
            rect.setBrush(Brush)
            rect.setPen(pen)
        x = left
        while x <= right:
            lVert = self.drawALine(x, top, x, bottom)
            lVert.setPen(pen)
            x += Dx
        y = top
        while y <= bottom:
            lHor = self.drawALine(left, y, right, y)
            lHor.setPen(pen)
            y += Dy

    def drawARectangle(self, leftX, topY, widthX, heightY, pen=None, brush=None):
        rect = qtw.QGraphicsRectItem(leftX, topY, widthX, heightY)
        if brush is not None:
            rect.setBrush(brush)
        if pen is not None:
            rect.setPen(pen)
        self.scene.addItem(rect)
        return rect

    def drawALine(self, stX, stY, enX, enY, pen=None):
        if pen is None:
            pen = self.penMed
        line = qtw.QGraphicsLineItem(stX, stY, enX, enY)
        line.setPen(pen)
        self.scene.addItem(line)
        return line

    def polarToRect(self, centerX, centerY, radius, angleDeg=0):
        angleRad = angleDeg * 2.0 * math.pi / 360.0
        return centerX + radius * math.cos(angleRad), centerY + radius * math.sin(angleRad)

    def drawACircle(self, centerX, centerY, Radius, angle=0, brush=None, pen=None):
        ellipse = qtw.QGraphicsEllipseItem(centerX - Radius, centerY - Radius, 2 * Radius, 2 * Radius)
        if pen is not None:
            ellipse.setPen(pen)
        if brush is not None:
            ellipse.setBrush(brush)
        self.scene.addItem(ellipse)
        return ellipse

    def drawASquare(self, centerX, centerY, Size, brush=None, pen=None):
        sqr = qtw.QGraphicsRectItem(centerX - Size / 2.0, centerY - Size / 2.0, Size, Size)
        if pen is not None:
            sqr.setPen(pen)
        if brush is not None:
            sqr.setBrush(brush)
        self.scene.addItem(sqr)
        return sqr

    def drawATriangle(self, centerX, centerY, Radius, angleDeg=0, brush=None, pen=None):
        pts = []
        x, y = self.polarToRect(centerX, centerY, Radius, 0 + angleDeg)
        pts.append(qtc.QPointF(x, y))
        x, y = self.polarToRect(centerX, centerY, Radius, 120 + angleDeg)
        pts.append(qtc.QPointF(x, y))
        x, y = self.polarToRect(centerX, centerY, Radius, 240 + angleDeg)
        pts.append(qtc.QPointF(x, y))
        x, y = self.polarToRect(centerX, centerY, Radius, 0 + angleDeg)
        pts.append(qtc.QPointF(x, y))
        pg = qtg.QPolygonF(pts)
        PG = qtw.QGraphicsPolygonItem(pg)
        if pen is not None:
            PG.setPen(pen)
        if brush is not None:
            PG.setBrush(brush)
        self.scene.addItem(PG)
        return PG

    def drawAnArrow(self, startX, startY, endX, endY, pen=None, brush=None):
        line = qtw.QGraphicsLineItem(startX, startY, endX, endY)
        p = qtg.QPen() if pen is None else pen
        line.setPen(pen)
        angleDeg = 180.0 / math.pi * math.atan((endY - startY) / (endX - startX))
        self.scene.addItem(line)
        self.drawATriangle(endX, endY, 5, angleDeg=angleDeg, pen=pen, brush=brush)

    def drawRigidSurface(self, centerX, centerY, Width=10, Height=3, pen=None, brush=None):
        top = centerY
        left = centerX - Width / 2
        right = centerX + Width / 2
        self.drawALine(centerX - Width / 2, centerY, centerX + Width / 2, centerY, pen=pen)
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        self.drawARectangle(left, top, Width, Height, pen=penOutline, brush=brush)

    def drawLinkage(self, stX, stY, enX, enY, radius=10, pen=None, brush=None):
        if pen is None:
            pen = self.penLink
        if brush is None:
            brush = self.brushLink
        lin1 = RigidLink(stX, stY, enX, enY, radius, pen=pen, brush=brush)
        self.scene.addItem(lin1)
        return lin1

    def drawPivot(self, x, y, ht, wd):
        pivot = RigidPivotPoint(x, y, ht, wd, brush=self.brushPivot)
        self.scene.addItem(pivot)
        return pivot

    def pickAColor(self):
        cdb = qtw.QColorDialog(self)
        c = cdb.getColor()
        hsv = c.getHsv()
        self.penGridLines.setColor(qtg.QColor.fromHsv(hsv[0], hsv[1], hsv[2], hsv[3]))
        self.buildScene()

class FourBarLinkage_Controller:
    def __init__(self, widgets):
        self.widgets = widgets
        self.gv_Main, self.nud_InputAngle, self.lbl_OutputAngle_Val, self.nud_Link1Length, self.nud_Link3Length, self.spnd_Zoom = widgets
        self.FBL_M = FourBarLinkage_Model()
        self.FBL_V = FourBarLinkage_View(self.gv_Main)
        self.min_angle = 0.0
        self.max_angle = 360.0

    def set_min_angle(self, value):
        self.min_angle = value

    def set_max_angle(self, value):
        self.max_angle = value

    def setupGraphics(self):
        self.FBL_V.setupGraphics()

    def buildScene(self):
        self.FBL_V.BuildScene(self.FBL_M)

    def setInputLinkLength(self):
        self.FBL_M.setInputLength(self.nud_Link1Length.value())
        self.FBL_M.moveLinkage(self.FBL_M.InputLink.enPt)
        self.FBL_V.scene.update()

    def setOutputLinkLength(self):
        self.FBL_M.setOutputLength(self.nud_Link3Length.value())
        self.FBL_M.moveLinkage(self.FBL_M.InputLink.enPt)
        self.FBL_V.scene.update()

    def moveLinkage(self, scenePos):
        pivot = self.FBL_M.InputLink.stPt
        L = self.FBL_M.InputLink.length
        dx = scenePos.x() - pivot.x()
        dy = pivot.y() - scenePos.y()
        desired_angle_rad = math.atan2(dy, dx)
        desired_angle_deg = math.degrees(desired_angle_rad) % 360
        clamped_deg = max(self.min_angle, min(desired_angle_deg, self.max_angle))
        clamped_rad = math.radians(clamped_deg)
        new_x = pivot.x() + L * math.cos(clamped_rad)
        new_y = pivot.y() - L * math.sin(clamped_rad)
        adjusted_pos = qtc.QPointF(new_x, new_y)
        self.FBL_M.moveLinkage(adjusted_pos)
        self.FBL_V.scene.update()
        self.nud_InputAngle.setValue(self.FBL_M.InputLink.AngleDeg())
        self.lbl_OutputAngle_Val.setText("{:0.2f}".format(self.FBL_M.OutputLink.AngleDeg()))

if __name__ == "__main__":
    pass
