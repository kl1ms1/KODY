"""Слой доступа к железу.

На Raspberry Pi используется gpiozero.PWMLED (настоящий ШИМ на пине).
На ПК — SimulatedPWMLED с тем же интерфейсом: рисует яркость полоской
в терминале, чтобы можно было разрабатывать без Pi.
"""

from __future__ import annotations

import math
import sys
import threading
import time


class SimulatedPWMLED:
    """Минимальная копия интерфейса gpiozero.PWMLED для работы без Pi."""

    def __init__(self, pin: int, render: bool = True):
        self.pin = pin
        self._value = 0.0
        self._render = render
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # --- базовые операции -------------------------------------------------
    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        self._cancel()
        self._set(v)

    def on(self) -> None:
        self.value = 1.0

    def off(self) -> None:
        self.value = 0.0

    def close(self) -> None:
        self._cancel()
        self._set(0.0)
        if self._render:
            sys.stdout.write("\n")

    # --- эффекты ----------------------------------------------------------
    def blink(self, on_time=1.0, off_time=1.0, fade_in_time=0.0, fade_out_time=0.0,
              n=None, background=True):
        def frames():
            count = 0
            while n is None or count < n:
                yield from _ramp(0.0, 1.0, fade_in_time)
                yield 1.0, on_time
                yield from _ramp(1.0, 0.0, fade_out_time)
                yield 0.0, off_time
                count += 1
        self._start(frames())

    def pulse(self, fade_in_time=1.0, fade_out_time=1.0, n=None, background=True):
        self.blink(0.0, 0.0, fade_in_time, fade_out_time, n, background)

    # --- внутреннее -------------------------------------------------------
    def _set(self, v: float) -> None:
        self._value = max(0.0, min(1.0, float(v)))
        if self._render:
            bar = "█" * round(self._value * 20)
            sys.stdout.write(f"\r  GPIO{self.pin:<2} [{bar:<20}] {self._value * 100:5.1f}% ")
            sys.stdout.flush()

    def _start(self, frames) -> None:
        self._cancel()
        self._stop.clear()

        def run():
            for value, hold in frames:
                self._set(value)
                if self._stop.wait(hold):
                    return

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def _cancel(self) -> None:
        if self._thread is not None:
            self._stop.set()
            self._thread.join()
            self._thread = None


def _ramp(start: float, end: float, duration: float, fps: int = 25):
    """Плавный переход яркости (с гамма-коррекцией, чтобы глазу казалось ровно)."""
    if duration <= 0:
        return
    steps = max(1, int(duration * fps))
    for i in range(1, steps + 1):
        t = i / steps
        linear = start + (end - start) * t
        yield math.pow(linear, 2.2), duration / steps


def make_pwm_led(pin: int, simulate: bool | None = None):
    """Создать ШИМ-выход: настоящий на Pi, симулированный на ПК."""
    if not simulate:
        try:
            from gpiozero import PWMLED  # type: ignore
            return PWMLED(pin)
        except Exception as exc:  # нет gpiozero или не Raspberry Pi
            if simulate is False:
                raise
            print(f"[симуляция] реальные GPIO недоступны ({exc.__class__.__name__}), работаю на экране")
    return SimulatedPWMLED(pin)
