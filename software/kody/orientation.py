"""Автоповорот экрана по акселерометру — как у телефона.

Акселерометр в покое показывает, где «верх»: при вертикальном (портретном)
положении он видит +1 g вдоль оси Y платы. Повернул KODY боком — сила
тяжести «переехала» на ось X, и интерфейс поворачивается.

Чтобы экран не дёргался:
  * гистерезис — новый поворот принимается, только если наклон ушёл от
    текущего положения больше чем на 45° + запас (по умолчанию 20°);
  * удержание — новое положение должно продержаться N замеров подряд;
  * «лежит на столе» — если почти вся тяжесть идёт вдоль Z (экран смотрит
    вверх или вниз), поворот не меняется.

Оси (как на плате KODY, вид спереди): X — вправо, Y — вверх (к антеннам),
Z — из экрана на тебя. Поворот — угол, на который надо повернуть картинку
по часовой стрелке: 0 — портрет, 90 — боком (антенны справа),
180 — вверх ногами, 270 — боком (антенны слева).
"""

from __future__ import annotations

import math


class OrientationTracker:
    def __init__(self, hysteresis_deg: float = 20.0, flat_threshold: float = 0.8, hold_samples: int = 5):
        self.hysteresis = hysteresis_deg
        self.flat_threshold = flat_threshold
        self.hold_samples = hold_samples
        self.rotation = 0
        self._candidate: int | None = None
        self._count = 0

    @staticmethod
    def tilt_angle(ax: float, ay: float) -> float:
        """Угол «верха» в плоскости экрана, 0..360, по часовой стрелке от оси +Y."""
        return math.degrees(math.atan2(ax, ay)) % 360

    def _distance(self, angle: float, rotation: int) -> float:
        d = abs(angle - rotation) % 360
        return min(d, 360 - d)

    def update(self, ax: float, ay: float, az: float) -> int:
        """Скормить замер акселерометра (в g). Вернуть текущий поворот: 0/90/180/270."""
        g = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
        if abs(az) / g > self.flat_threshold:      # лежит на столе — ничего не меняем
            self._candidate, self._count = None, 0
            return self.rotation
        angle = self.tilt_angle(ax, ay)
        nearest = int(round(angle / 90.0)) % 4 * 90
        if nearest == self.rotation or self._distance(angle, self.rotation) < 45 + self.hysteresis:
            self._candidate, self._count = None, 0
            return self.rotation
        if nearest != self._candidate:
            self._candidate, self._count = nearest, 0
        self._count += 1
        if self._count >= self.hold_samples:
            self.rotation, self._candidate, self._count = nearest, None, 0
        return self.rotation


def tilt_to_accel(angle_deg: float, flat: float = 0.0) -> tuple[float, float, float]:
    """Обратная функция для симуляции: какой замер даст наклон angle_deg."""
    r = math.radians(angle_deg)
    k = math.sqrt(max(0.0, 1 - flat * flat))
    return math.sin(r) * k, math.cos(r) * k, flat
