"""Проект «Лампочка»: пресеты, расчёт резистора и эффекты (вкл/мигание/плавно)."""

from __future__ import annotations

from dataclasses import dataclass

from .pins import check_user_pin

GPIO_VOLTAGE = 3.3       # GPIO Raspberry Pi — только 3.3 В
GPIO_MAX_MA = 16.0       # безопасный ток на один пин
E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]


@dataclass(frozen=True)
class LampPreset:
    name: str
    voltage: float        # прямое напряжение светодиода / напряжение лампы, В
    current_ma: float     # рабочий ток, мА
    dimmable: bool = True # можно ли плавно менять яркость (реле — нельзя)
    note: str = ""


PRESETS: list[LampPreset] = [
    LampPreset("Светодиод 5 мм — красный", 2.0, 15),
    LampPreset("Светодиод 5 мм — жёлтый", 2.1, 15),
    LampPreset("Светодиод 5 мм — зелёный", 2.2, 15),
    LampPreset("Светодиод 5 мм — синий", 3.0, 10, note="при 3.3 В будет светить вполсилы"),
    LampPreset("Светодиод 5 мм — белый", 3.0, 10, note="при 3.3 В будет светить вполсилы"),
    LampPreset("Светодиодная лента 12 В", 12.0, 500, note="через MOSFET-модуль и блок питания 12 В"),
    LampPreset("Лампа 220 В", 220.0, 200, dimmable=False,
               note="ТОЛЬКО через готовый модуль реле, опасное напряжение!"),
]


@dataclass(frozen=True)
class WiringAdvice:
    direct: bool               # можно ли подключить напрямую к пину (через резистор)
    resistor_ohm: int | None   # рекомендуемый резистор (ближайший больший из E12)
    current_ma: float | None   # реальный ток с этим резистором
    text: str


def nearest_e12_above(ohms: float) -> int:
    """Ближайший стандартный номинал E12, не меньше заданного (чтобы не превысить ток)."""
    decade = 1.0
    while True:
        for base in E12:
            if base * decade >= ohms - 1e-9:
                return int(round(base * decade))
        decade *= 10


def wiring_advice(preset: LampPreset) -> WiringAdvice:
    """Подсказать, как подключить: напрямую с резистором или через драйвер."""
    headroom = GPIO_VOLTAGE - preset.voltage
    if preset.voltage > GPIO_VOLTAGE or headroom < 0.2:
        if preset.voltage <= GPIO_VOLTAGE:
            # синий/белый светодиод: почти нет запаса напряжения, но светить будет
            r = nearest_e12_above(max(headroom, 0.01) / (preset.current_ma / 1000))
            i = 1000 * headroom / r
            return WiringAdvice(True, r, round(i, 1),
                                f"Резистор {r} Ом последовательно. Ток ≈ {i:.1f} мА. {preset.note}".strip())
        driver = "модуль реле" if not preset.dimmable else "MOSFET-модуль (например IRLZ44N/AO3400)"
        return WiringAdvice(False, None, None,
                            f"Напрямую к GPIO нельзя: нужно {preset.voltage:g} В, а пин даёт 3.3 В. "
                            f"Подключи через {driver}; GPIO → вход модуля. {preset.note}".strip())
    current = min(preset.current_ma, GPIO_MAX_MA)
    r = nearest_e12_above(headroom / (current / 1000))
    i = 1000 * headroom / r
    return WiringAdvice(True, r, round(i, 1),
                        f"GPIO → резистор {r} Ом → длинная ножка (+) светодиода, "
                        f"короткая (−) → GND. Ток ≈ {i:.1f} мА. {preset.note}".strip())


class Lamp:
    """Лампочка на пине. Эффекты делегируются ШИМ-выходу (gpiozero или симуляция)."""

    def __init__(self, bcm: int, preset: LampPreset, led_factory, disabled_features=frozenset()):
        self.pin = check_user_pin(bcm, frozenset(disabled_features))
        self.preset = preset
        self.led = led_factory(bcm)

    def on(self, brightness: float = 1.0) -> None:
        if not self.preset.dimmable or brightness >= 1.0:
            self.led.on()
        else:
            self.led.value = max(0.0, brightness)

    def off(self) -> None:
        self.led.off()

    def blink(self, on_time: float = 0.5, off_time: float = 0.5) -> None:
        self.led.blink(on_time=on_time, off_time=off_time, background=True)

    def breathe(self, period: float = 2.0) -> None:
        """Плавно «жик-жик»: разгорается и гаснет."""
        if not self.preset.dimmable:
            raise ValueError("Эта лампа подключена через реле — плавно менять яркость нельзя")
        self.led.pulse(fade_in_time=period / 2, fade_out_time=period / 2, background=True)

    def soft_blink(self, on_time: float = 0.4, off_time: float = 0.4, fade: float = 0.3) -> None:
        """Мигание с плавными фронтами."""
        if not self.preset.dimmable:
            return self.blink(on_time, off_time)
        self.led.blink(on_time=on_time, off_time=off_time,
                       fade_in_time=fade, fade_out_time=fade, background=True)

    def close(self) -> None:
        self.led.close()
