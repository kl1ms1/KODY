"""Карта 40-пиновой гребёнки KODY (см. docs/hardware.md, раздел 4).

Каждый пин помечен статусом:
  FREE     — свободен, можно брать для своих проектов;
  SHARED   — общая шина (I2C/SPI): можно подключать свои устройства на шину,
             но нельзя использовать пин как обычный вход/выход;
  RESERVED — занят самим девайсом.

Некоторые занятые пины принадлежат отключаемой функции (feature). Если
пользователь отключил функцию в настройках, её пины становятся свободными.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PinStatus(Enum):
    FREE = "свободен"
    SHARED = "общая шина"
    RESERVED = "занят"


@dataclass(frozen=True)
class Pin:
    bcm: int
    phys: int
    function: str
    status: PinStatus
    feature: str | None = None  # функция, которую можно отключить


PINS: dict[int, Pin] = {
    p.bcm: p
    for p in [
        Pin(0, 27, "ID EEPROM HAT (SDA)", PinStatus.RESERVED),
        Pin(1, 28, "ID EEPROM HAT (SCL)", PinStatus.RESERVED),
        Pin(2, 3, "I2C1 SDA (тач)", PinStatus.SHARED),
        Pin(3, 5, "I2C1 SCL (тач)", PinStatus.SHARED),
        Pin(4, 7, "Прерывание тача", PinStatus.RESERVED),
        Pin(5, 29, "RP2040 RUN", PinStatus.RESERVED),
        Pin(6, 31, "RP2040 BOOTSEL", PinStatus.RESERVED),
        Pin(7, 26, "SPI0 CE1", PinStatus.FREE),
        Pin(8, 24, "SPI0 CE0 — экран", PinStatus.RESERVED),
        Pin(9, 21, "SPI0 MISO", PinStatus.SHARED),
        Pin(10, 19, "SPI0 MOSI (экран)", PinStatus.SHARED),
        Pin(11, 23, "SPI0 SCLK (экран)", PinStatus.SHARED),
        Pin(12, 32, "PWM0 — пищалка", PinStatus.RESERVED),
        Pin(13, 33, "PWM1 — подсветка экрана", PinStatus.RESERVED),
        Pin(14, 8, "UART TX", PinStatus.FREE),
        Pin(15, 10, "UART RX", PinStatus.FREE),
        Pin(16, 36, "SPI1 CE2", PinStatus.FREE),
        Pin(17, 11, "SPI1 CE1 — microSD №2", PinStatus.RESERVED, "sd2"),
        Pin(18, 12, "SPI1 CE0 — LoRa SX1262", PinStatus.RESERVED, "lora"),
        Pin(19, 35, "SPI1 MISO", PinStatus.SHARED),
        Pin(20, 38, "SPI1 MOSI", PinStatus.SHARED),
        Pin(21, 40, "SPI1 SCLK", PinStatus.SHARED),
        Pin(22, 15, "SX1262 BUSY", PinStatus.RESERVED, "lora"),
        Pin(23, 16, "SX1262 DIO1", PinStatus.RESERVED, "lora"),
        Pin(24, 18, "Экран D/C", PinStatus.RESERVED),
        Pin(25, 22, "Экран RESET", PinStatus.RESERVED),
        Pin(26, 37, "—", PinStatus.FREE),
        Pin(27, 13, "SX1262 RESET", PinStatus.RESERVED, "lora"),
    ]
}


class PinUnavailable(ValueError):
    """Пин нельзя использовать в пользовательском проекте."""


def effective_status(pin: Pin, disabled_features: frozenset[str] = frozenset()) -> PinStatus:
    if pin.feature is not None and pin.feature in disabled_features:
        return PinStatus.FREE
    return pin.status


def user_pins(disabled_features: frozenset[str] = frozenset()) -> list[Pin]:
    """Пины, которые можно отдать пользователю как обычный вход/выход."""
    return [
        p for p in sorted(PINS.values(), key=lambda p: p.phys)
        if effective_status(p, disabled_features) is PinStatus.FREE
    ]


def check_user_pin(bcm: int, disabled_features: frozenset[str] = frozenset()) -> Pin:
    """Вернуть пин, если он свободен, иначе поднять PinUnavailable с понятной причиной."""
    pin = PINS.get(bcm)
    if pin is None:
        raise PinUnavailable(f"GPIO{bcm} нет на гребёнке Raspberry Pi")
    status = effective_status(pin, disabled_features)
    if status is PinStatus.RESERVED:
        hint = f" (освободится, если отключить «{pin.feature}» в настройках)" if pin.feature else ""
        raise PinUnavailable(f"GPIO{bcm} (пин {pin.phys}) занят: {pin.function}{hint}")
    if status is PinStatus.SHARED:
        raise PinUnavailable(
            f"GPIO{bcm} (пин {pin.phys}) — линия шины ({pin.function}). "
            "На неё можно вешать I2C/SPI-устройства, но не лампочку"
        )
    return pin
