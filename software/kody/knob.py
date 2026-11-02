"""Крутилка KODY: бесконечно в обе стороны, в каждой программе — своё.

Железо: колёсико-энкодер на правом боку (крутится без упора в обе стороны,
нажимается). Его читает микроконтроллер передней платы и отдаёт Pi события:
  rotate(+N / −N)  — щелчки по часовой / против,
  press            — короткое нажатие,
  long_press       — удержание > 0.6 с,
  hold_rotate(±N)  — крутишь, удерживая нажатым.

Что делает крутилка, решает текущая программа (профиль). Плюс два общих
правила, которые работают везде:
  * удержал и крутишь — громкость (как колёсико на гарнитуре);
  * быстро крутишь — шаг растёт (ускорение), чтобы пролистать 400 каналов
    за секунду, а медленно — по одному.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Profile:
    """Что делает крутилка в конкретной программе."""
    name: str
    what: str                                   # подсказка на экране: «Канал», «Частота»…
    value: float
    step: float
    min_value: float
    max_value: float
    wrap: bool = False                          # по кругу (каналы) или упор (громкость)
    on_press: Callable[["Profile"], str] | None = None
    fmt: Callable[[float], str] = field(default=lambda v: f"{v:g}")

    def turn(self, steps: int) -> None:
        v = self.value + steps * self.step
        span = self.max_value - self.min_value + (self.step if self.wrap else 0)
        if self.wrap:
            v = self.min_value + (v - self.min_value) % span
        else:
            v = min(self.max_value, max(self.min_value, v))
        self.value = round(v, 6)


def accel(clicks: int, dt: float) -> int:
    """Ускорение: щелчки быстрее 30 мс друг за другом считаются ×10, быстрее 80 мс — ×3."""
    if dt < 0.03:
        return clicks * 10
    if dt < 0.08:
        return clicks * 3
    return clicks


def default_profiles() -> dict[str, Profile]:
    lpd = {i: 433.075 + (i - 1) * 0.025 for i in range(1, 70)}
    return {
        "menu": Profile("Меню", "Пункт", 0, 1, 0, 8, wrap=True),
        "radio": Profile("Рация", "Канал LPD", 1, 1, 1, 69, wrap=True,
                         fmt=lambda v: f"LPD {int(v)} · {lpd[int(v)]:.3f} МГц",
                         on_press=lambda p: "передача (держи для разговора)"),
        "subghz": Profile("Sub-GHz", "Частота, МГц", 433.92, 0.005, 300.0, 928.0,
                          fmt=lambda v: f"{v:.3f} МГц", on_press=lambda p: "запись сигнала"),
        "lora": Profile("LoRa-чат", "Сообщение", 0, 1, 0, 999, on_press=lambda p: "ответить"),
        "lamp": Profile("Лампочка", "Яркость, %", 50, 5, 0, 100, on_press=lambda p: "вкл/выкл"),
        "gps": Profile("GPS", "Масштаб карты", 15, 1, 3, 19),
    }


class KnobRouter:
    """Раздаёт события крутилки текущей программе. Громкость — общая для всех."""

    def __init__(self, profiles: dict[str, Profile] | None = None):
        self.profiles = profiles or default_profiles()
        self.app = "menu"
        self.volume = Profile("Громкость", "Громкость, %", 60, 5, 0, 100)
        self._last_t: float | None = None

    @property
    def current(self) -> Profile:
        return self.profiles[self.app]

    def open(self, app: str) -> None:
        if app not in self.profiles:
            raise KeyError(f"нет программы {app}")
        self.app = app

    def rotate(self, clicks: int, t: float) -> str:
        dt = 1.0 if self._last_t is None else t - self._last_t
        self._last_t = t
        p = self.current
        p.turn(accel(clicks, dt))
        return f"{p.what}: {p.fmt(p.value)}"

    def hold_rotate(self, clicks: int) -> str:
        self.volume.turn(clicks)
        return f"Громкость: {self.volume.value:g}%"

    def press(self) -> str:
        p = self.current
        return p.on_press(p) if p.on_press else "выбрать"

    def long_press(self) -> str:
        self.app = "menu"
        return "назад в меню"
