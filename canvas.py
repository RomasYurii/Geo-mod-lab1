import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import QWidget

import transforms as T
from part import Part

AXIS_END = 16.0      # довжина осі (см) - «кінці осей» для проективних перетворень
MARGIN = 50          # відступ початку координат від лівого/нижнього краю, px


class Canvas(QWidget):
    def __init__(self, on_drag):
        super().__init__()
        self.setMinimumSize(780, 620)
        self.part = Part()
        self.p = {}
        self.on_drag = on_drag
        self.drag = None

    def set_params(self, p):
        self.p = p
        self.part.set(**{k: p[k] for k in ("Rt", "Rb", "D", "ht", "hb", "Lt", "Lb", "r")})
        self.update()

    # ---------- матриці ----------
    def matrices(self):
        p = self.p
        A = T.identity()
        P = T.identity()
        if p["aff"]:
            A = T.affine(p["aox"], p["aoy"], p["axx"], p["axy"], p["ayx"], p["ayy"])
        if p["proj"]:
            P = T.projective((p["pxx"], p["pxy"]), (p["pyx"], p["pyy"]),
                             (p["pox"], p["poy"]), p["wx"], p["wy"], p["w0"], AXIS_END)
        coord = T.chain(A, P)                    # зміна системи координат (осі + сітка + деталь)
        k = -1.0 if p["sym"] else 1.0            # симетрія = масштаб -1 відносно точки
        place = T.translation(p["fx"], p["fy"])  # положення деталі
        S = T.scaling_about(p["sx"] * k, p["sy"] * k, p["cx"], p["cy"])
        Rot = T.rotation_about(p["angle"], p["cx"], p["cy"])
        model = T.chain(place, S, Rot, coord)
        return model, coord

    # ---------- координати ----------
    def to_screen(self, x, y):
        s = self.p["ppc"]
        return QPointF(MARGIN + x * s, self.height() - MARGIN - y * s)  # вісь Y вгору

    def from_screen(self, sx, sy):
        s = self.p["ppc"]
        return (sx - MARGIN) / s, (self.height() - MARGIN - sy) / s

    def draw_poly(self, qp, pts, m):
        prev = None
        for x, y in pts:
            q = T.apply(m, x, y)
            if q and (abs(q[0]) > 1e4 or abs(q[1]) > 1e4):
                q = None
            if q and prev:
                qp.drawLine(self.to_screen(*prev), self.to_screen(*q))
            prev = q

    def label(self, qp, x, y, text, m, dx, dy):
        q = T.apply(m, x, y)
        if q:
            s = self.to_screen(*q)
            qp.drawText(QPointF(s.x() + dx, s.y() + dy), text)

    # ---------- керовані точки ----------
    def handles(self):
        p = self.p
        _, coord = self.matrices()
        H = []
        q = T.apply(coord, p["fx"], p["fy"])
        if q:
            H.append(("fig", q, "#17a2b8"))
        q = T.apply(coord, p["cx"], p["cy"])
        if q:
            H.append(("pivot", q, "#e6b800"))
        if p["aff"]:
            H += [("aO", (p["aox"], p["aoy"]), "#000000"),
                  ("aX", (p["axx"], p["axy"]), "#d62828"),
                  ("aY", (p["ayx"], p["ayy"]), "#2a9d2a")]
        if p["proj"]:
            H += [("pO", (p["pox"], p["poy"]), "#000000"),
                  ("pX", (p["pxx"], p["pxy"]), "#d62828"),
                  ("pY", (p["pyx"], p["pyy"]), "#2a9d2a")]
        return H

    def mousePressEvent(self, e):
        if not self.p:
            return
        best, bd = None, 12.0
        for name, (x, y), _ in self.handles():
            s = self.to_screen(x, y)
            d = math.hypot(s.x() - e.position().x(), s.y() - e.position().y())
            if d < bd:
                best, bd = name, d
        self.drag = best

    def mouseMoveEvent(self, e):
        if not self.drag:
            return
        x, y = self.from_screen(e.position().x(), e.position().y())
        if self.drag in ("fig", "pivot"):      # точки задані в координатах моделі -> обернене перетворення
            inv = T.inverse(self.matrices()[1])
            q = T.apply(inv, x, y, clip=False) if inv else None
            if not q:
                return
            x, y = q
        self.on_drag(self.drag, round(x, 2), round(y, 2))

    def mouseReleaseEvent(self, _):
        self.drag = None

    # ---------- малювання ----------
    def paintEvent(self, _):
        if not self.p:
            return
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.fillRect(self.rect(), QColor("#ffffff"))
        model_m, coord_m = self.matrices()
        s = self.p["ppc"]
        nx = int((self.width() - MARGIN) / s) + 2
        ny = int((self.height() - MARGIN) / s) + 2

        qp.setPen(QPen(QColor("#d9d9d9"), 1))              # сітка
        for i in range(1, nx + 1):
            self.draw_poly(qp, [(i, k) for k in range(ny + 1)], coord_m)
        for j in range(1, ny + 1):
            self.draw_poly(qp, [(k, j) for k in range(nx + 1)], coord_m)

        qp.setPen(QPen(QColor("#e03131"), 2))              # вісь X
        self.draw_poly(qp, [(k, 0) for k in range(nx + 1)], coord_m)
        qp.setPen(QPen(QColor("#2f9e44"), 2))              # вісь Y
        self.draw_poly(qp, [(0, k) for k in range(ny + 1)], coord_m)
        qp.setPen(QColor("#222222"))
        for i in range(5, nx + 1, 5):
            self.label(qp, i, 0, str(i), coord_m, -4, 15)
        for j in range(5, ny + 1, 5):
            self.label(qp, 0, j, str(j), coord_m, -20, 4)
        self.label(qp, nx, 0, "X", coord_m, -12, -8)
        self.label(qp, 0, ny, "Y", coord_m, 8, 12)

        qp.setPen(QPen(QColor("#111111"), 2.5))            # деталь
        for c in self.part.contours():
            self.draw_poly(qp, c, model_m)

        qp.setPen(QPen(QColor("#ffffff"), 1))              # керовані точки
        for _, (x, y), col in self.handles():
            qp.setBrush(QBrush(QColor(col)))
            qp.drawEllipse(self.to_screen(x, y), 5, 5)
        qp.end()