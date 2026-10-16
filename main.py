import sys
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGroupBox,
                               QFormLayout, QDoubleSpinBox, QCheckBox, QPushButton,
                               QScrollArea, QLabel)
from canvas import Canvas
from part import DEFAULTS


class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЛР1. Лінійні перетворення. Варіант 15")
        self.canvas = Canvas(self.dragged)
        self.w, self.defaults = {}, {}

        panel = QVBoxLayout()
        panel.addWidget(self.group("Вигляд", [("ppc", "Щільність (px/см)", 20, 6, 60, 1)]))
        g = self.group("Розміри деталі (см) - кожен елемент окремо", [
            ("Rt", "R верхньої дуги (Ø160)", DEFAULTS["Rt"], 0.6, 20),
            ("Rb", "R нижньої дуги (Ø160)", DEFAULTS["Rb"], 0.6, 20),
            ("D", "Лівий відрізок: відстань до центру (50)", DEFAULTS["D"], 0.5, 20),
            ("ht", "Верхня лінія: висота над центром (60)", DEFAULTS["ht"], 0.5, 20),
            ("hb", "Нижня лінія: висота під центром (60)", DEFAULTS["hb"], 0.5, 20),
            ("Lt", "Верхня лінія: правий край від центру (210)", DEFAULTS["Lt"], 1, 30),
            ("Lb", "Нижня лінія: правий край від центру (210)", DEFAULTS["Lb"], 1, 30),
            ("r", "R отвору (Ø60)", DEFAULTS["r"], 0.2, 20)])
        panel.addWidget(g)
        b = QPushButton("Скинути розміри деталі (до креслення)")
        b.clicked.connect(self.reset_geometry)
        panel.addWidget(b)

        panel.addWidget(self.group("Положення деталі (блакитна точка)", [
            ("fx", "Положення X", 11, -40, 60), ("fy", "Положення Y", 9, -40, 60)]))
        panel.addWidget(self.group("Точка обертання / симетрії / масштабу (жовта)", [
            ("cx", "X", 11, -40, 60), ("cy", "Y", 9, -40, 60),
            ("angle", "Кут обертання (°)", 0, -360, 360, 1)]))
        g = self.group("Масштабування та симетрія", [
            ("sx", "Масштаб Sx", 1, -10, 10), ("sy", "Масштаб Sy", 1, -10, 10)])
        self.sym = QCheckBox("Симетрія відносно жовтої точки")
        self.sym.stateChanged.connect(self.changed)
        g.layout().addRow(self.sym)
        panel.addWidget(g)

        self.aff = QCheckBox("Афінне перетворення (змінює осі, сітку і деталь)")
        self.aff.stateChanged.connect(self.changed)
        panel.addWidget(self.aff)
        panel.addWidget(self.group("Афінні: нова система координат (чорна/червона/зелена точки)", [
            ("aox", "O  x", 0, -60, 60), ("aoy", "O  y", 0, -60, 60),
            ("axx", "X  x", 1, -60, 60), ("axy", "X  y", 0, -60, 60),
            ("ayx", "Y  x", 0, -60, 60), ("ayy", "Y  y", 1, -60, 60)]))

        self.proj = QCheckBox("Проективне перетворення")
        self.proj.stateChanged.connect(self.changed)
        panel.addWidget(self.proj)
        panel.addWidget(self.group("Проективні: кінці осей та ваги", [
            ("pxx", "Xend x", 16, -60, 60), ("pxy", "Xend y", 0, -60, 60),
            ("pyx", "Yend x", 0, -60, 60), ("pyy", "Yend y", 16, -60, 60),
            ("pox", "O x", 0, -60, 60), ("poy", "O y", 0, -60, 60),
            ("wx", "Вага wx", 1, 0.01, 1000, 0.1), ("wy", "Вага wy", 1, 0.01, 1000, 0.1),
            ("w0", "Вага w0", 1, 0.01, 1000, 0.1)]))

        btn = QPushButton("Скинути все")
        btn.clicked.connect(self.reset)
        panel.addWidget(btn)
        panel.addStretch()

        host = QWidget()
        host.setLayout(panel)
        scroll = QScrollArea()
        scroll.setWidget(host)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(420)
        lay = QHBoxLayout(self)
        lay.addWidget(scroll)
        lay.addWidget(self.canvas, 1)
        self.changed()

    def group(self, title, rows):
        box = QGroupBox(title)
        form = QFormLayout(box)
        for row in rows:
            key, label, val, lo, hi = row[:5]
            step = row[5] if len(row) > 5 else 0.1
            sp = QDoubleSpinBox()
            sp.setRange(lo, hi)
            sp.setDecimals(2)
            sp.setSingleStep(step)
            sp.setValue(val)
            sp.valueChanged.connect(self.changed)
            form.addRow(label, sp)
            self.w[key] = sp
            self.defaults[key] = val
        return box

    def dragged(self, name, x, y):
        keys = {"fig": ("fx", "fy"), "pivot": ("cx", "cy"),
                "aO": ("aox", "aoy"), "aX": ("axx", "axy"), "aY": ("ayx", "ayy"),
                "pO": ("pox", "poy"), "pX": ("pxx", "pxy"), "pY": ("pyx", "pyy")}[name]
        for k, v in zip(keys, (x, y)):
            self.w[k].blockSignals(True)
            self.w[k].setValue(v)
            self.w[k].blockSignals(False)
        self.changed()

    def changed(self, *_):
        w = self.w
        # залежні обмеження, щоб сусідні елементи завжди могли стикуватись
        w["Rt"].setMinimum(max(w["D"].value(), w["ht"].value()) + 0.1)
        w["Rb"].setMinimum(max(w["D"].value(), w["hb"].value()) + 0.1)
        w["r"].setMaximum(max(min(w["Rt"].value(), w["Rb"].value(), w["D"].value()) - 0.1, 0.2))
        p = {k: s.value() for k, s in w.items()}
        p.update(sym=self.sym.isChecked(), aff=self.aff.isChecked(), proj=self.proj.isChecked())
        self.canvas.set_params(p)

    def reset_geometry(self):
        for k in DEFAULTS:
            self.w[k].setValue(DEFAULTS[k])

    def reset(self):
        for k, s in self.w.items():
            s.setValue(self.defaults[k])
        for c in (self.sym, self.aff, self.proj):
            c.setChecked(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Main()
    win.resize(1300, 820)
    win.show()
    sys.exit(app.exec())