"""Деталь варіанта 15 (одиниці - см), центр отвору і дуг - у (0, 0).

Елементи контуру (кожен змінюється окремо, сусідні стикуються автоматично):
  верхня дуга  (радіус Rt)  - від верхньої лінії до лівого вертикального відрізка;
  лівий вертикальний відрізок на відстані D ліворуч від центру (260-210 = 50 мм);
  нижня дуга   (радіус Rb);
  нижня лінія  (на висоті hb під центром, до x = Lb);
  права сторона - відрізок між кінцями верхньої та нижньої ліній;
  верхня лінія (на висоті ht над центром, до x = Lt);
  отвір радіусом r.
Кінці дуг і відрізків обчислюються з поточних параметрів, тому контур завжди замкнений."""
import math

DEFAULTS = dict(Rt=8.0, Rb=8.0, D=5.0, ht=6.0, hb=6.0, Lt=21.0, Lb=21.0, r=3.0)


class Part:
    def __init__(self, **kw):
        self.set(**{**DEFAULTS, **kw})

    def set(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    @staticmethod
    def arc(cx, cy, r, deg_beg, deg_end):
        """Дуга ламаною з кроком 1° (формули 2-3 методички)."""
        pts, i = [], deg_beg
        while i < deg_end:
            a = math.radians(i)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            i += 1.0
        a = math.radians(deg_end)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def effective(self):
        """Коригує параметри, щоб контур залишався коректним."""
        D = max(self.D, 0.5)
        ht, hb = max(self.ht, 0.5), max(self.hb, 0.5)
        Rt = max(self.Rt, D + 0.1, ht + 0.1)
        Rb = max(self.Rb, D + 0.1, hb + 0.1)
        r = min(max(self.r, 0.1), min(Rt, Rb, D) - 0.1)
        xt, xb = math.sqrt(Rt ** 2 - ht ** 2), math.sqrt(Rb ** 2 - hb ** 2)  # точки стику
        Lt, Lb = max(self.Lt, xt + 0.5), max(self.Lb, xb + 0.5)
        return Rt, Rb, D, ht, hb, Lt, Lb, r, xt, xb

    def contours(self):
        Rt, Rb, D, ht, hb, Lt, Lb, r, xt, xb = self.effective()
        t0 = math.degrees(math.asin(ht / Rt))            # кут стику верхньої лінії
        t1 = math.degrees(math.acos(-D / Rt))            # кут, де дуга перетинає x = -D
        b0 = math.degrees(math.asin(hb / Rb))
        b1 = math.degrees(math.acos(-D / Rb))
        outer = self.arc(0, 0, Rt, t0, t1)               # верхня дуга
        outer += self.arc(0, 0, Rb, 360 - b1, 360 - b0)  # (лівий відрізок з'єднує кінці дуг) нижня дуга
        outer += [(Lb, -hb), (Lt, ht), (xt, ht)]         # низ, права сторона, верх
        hole = self.arc(0, 0, r, 0, 360)
        return [outer, hole]