"""Карта 40-пиновой гребёнки KODY v7.

KODY не занимает GPIO: экран идёт через HDMI, кнопки/крутилка/питание —
через свой микроконтроллер на общей шине I2C, радио, NFC и GPS — через USB
(подпружиненные контакты к площадкам снизу Pi). Поэтому на боковом гнезде
все 26 GPIO твои, плюс общая шина I2C (свои устройства с другими адресами).
Пины 27/28 (ID EEPROM) по стандарту HAT заняты паспортом основной платы.

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
        Pin(0, 27, "ID EEPROM основной платы (SDA) — стандарт HAT", PinStatus.RESERVED),
        Pin(1, 28, "ID EEPROM основной платы (SCL) — стандарт HAT", PinStatus.RESERVED),
        Pin(2, 3, "I2C1 SDA — общая шина: KODY + твои I2C-устройства", PinStatus.SHARED),
        Pin(3, 5, "I2C1 SCL — общая шина: KODY + твои I2C-устройства", PinStatus.SHARED),
        Pin(4, 7, "свободен", PinStatus.FREE),
        Pin(5, 29, "свободен", PinStatus.FREE),
        Pin(6, 31, "свободен", PinStatus.FREE),
        Pin(7, 26, "SPI0 CE1", PinStatus.FREE),
        Pin(8, 24, "SPI0 CE0", PinStatus.FREE),
        Pin(9, 21, "SPI0 MISO", PinStatus.FREE),
        Pin(10, 19, "SPI0 MOSI", PinStatus.FREE),
        Pin(11, 23, "SPI0 SCLK", PinStatus.FREE),
        Pin(12, 32, "PWM0", PinStatus.FREE),
        Pin(13, 33, "PWM1", PinStatus.FREE),
        Pin(14, 8, "UART TX", PinStatus.FREE),
        Pin(15, 10, "UART RX", PinStatus.FREE),
        Pin(16, 36, "свободен", PinStatus.FREE),
        Pin(17, 11, "свободен", PinStatus.FREE),
        Pin(18, 12, "PCM CLK / PWM0", PinStatus.FREE),
        Pin(19, 35, "SPI1 MISO / PCM FS", PinStatus.FREE),
        Pin(20, 38, "SPI1 MOSI / PCM DIN", PinStatus.FREE),
        Pin(21, 40, "SPI1 SCLK / PCM DOUT", PinStatus.FREE),
        Pin(22, 15, "свободен", PinStatus.FREE),
        Pin(23, 16, "свободен", PinStatus.FREE),
        Pin(24, 18, "свободен", PinStatus.FREE),
        Pin(25, 22, "свободен", PinStatus.FREE),
        Pin(26, 37, "свободен", PinStatus.FREE),
        Pin(27, 13, "свободен", PinStatus.FREE),
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
