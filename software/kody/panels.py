"""Самопроверка KODY: какие модули на месте и всё ли на них отвечает.

Как KODY узнаёт свои платы:
  * Основная плата (в неё вставлена Pi) несёт стандартный HAT EEPROM на пинах
    ID_SD/ID_SC. Linux читает его при загрузке и кладёт имя в
    /proc/device-tree/hat/product.
  * Экран узнаём по контроллеру тача (GT911), задняя плата — по тому, что её
    микроконтроллер RP2350 виден по USB.
  * Дополнительно проверяются главные микросхемы на плате (тач, зарядка,
    гироскоп). Если EEPROM отвечает, а микросхема нет — плата вставлена,
    но с ней что-то не так (плохой контакт, брак пайки).
  * Задняя плата (радио) проверяется по ответу RP2040 через UART.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum

HAT_PRODUCT_PATH = "/proc/device-tree/hat/product"
CORE_PRODUCT = "KODY Main"


class Status(Enum):
    OK = "OK"
    PARTIAL = "ЕСТЬ, НО НЕИСПРАВНА"
    MISSING = "НЕТ"


@dataclass(frozen=True)
class Device:
    addr: int
    name: str


@dataclass(frozen=True)
class Panel:
    key: str
    name: str
    presence: int | None            # адрес I2C, по которому видно, что модуль на месте (None — HAT EEPROM)
    devices: tuple[Device, ...] = ()


# KODY v7: передняя плата (питание, экран, кнопки, датчики) + задняя плата (радио, USB).
PANELS: tuple[Panel, ...] = (
    Panel("front", "Передняя плата: питание, кнопки, крутилка, датчики", None,
          (Device(0x2A, "микроконтроллер питания и кнопок STM32"), Device(0x6A, "зарядка BQ25895"),
           Device(0x36, "датчик заряда MAX17048"), Device(0x6B, "гироскоп LSM6DSV16X"),
           Device(0x10, "датчик света VEML7700"), Device(0x5A, "вибро DRV2605L"), Device(0x52, "часы RV-3028"))),
    Panel("screen", "Экран с тачем", 0x5D),
    Panel("back", "Задняя плата: радио, NFC, GPS, USB", -1),
)


@dataclass
class Result:
    panel: Panel
    status: Status
    problems: list[str] = field(default_factory=list)


def check(i2c_present: set[int], hat_product: str | None, rp2040_ok: bool | None) -> list[Result]:
    """Чистая функция: по найденным адресам I2C и ответам решить, что вставлено."""
    results = []
    for p in PANELS:
        if p.presence is None:
            present = bool(hat_product) and hat_product.strip("\x00 \n") == CORE_PRODUCT
        elif p.presence == -1:          # задняя плата видна по USB, а не по I2C
            present = bool(rp2040_ok)
        else:
            present = p.presence in i2c_present
        if not present:
            results.append(Result(p, Status.MISSING))
            continue
        problems = [f"не отвечает {d.name} (0x{d.addr:02X})" for d in p.devices if d.addr not in i2c_present]
        results.append(Result(p, Status.PARTIAL if problems else Status.OK, problems))
    return results


# ---------------------------------------------------------------- железо
def scan_i2c(bus_no: int = 1) -> set[int] | None:
    """Опросить шину I2C. None — если шины нет (не Raspberry Pi)."""
    try:
        from smbus2 import SMBus  # type: ignore
    except ImportError:
        return None
    found = set()
    try:
        with SMBus(bus_no) as bus:
            for addr in range(0x08, 0x78):
                try:
                    bus.read_byte(addr)
                    found.add(addr)
                except OSError:
                    pass
    except (OSError, FileNotFoundError):
        return None
    return found


def read_hat_product(path: str = HAT_PRODUCT_PATH) -> str | None:
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def simulated_inputs(missing: frozenset[str] = frozenset()):
    """Как будто вставлено всё, кроме missing — для работы на ПК."""
    present: set[int] = set()
    hat = None
    for p in PANELS:
        if p.key in missing:
            continue
        if p.presence is None:
            hat = CORE_PRODUCT
        elif p.presence != -1:
            present.add(p.presence)
        present.update(d.addr for d in p.devices)
    return present, hat, "back" not in missing


def run(simulate: bool) -> list[Result]:
    if not simulate:
        found = scan_i2c()
        if found is not None:
            return check(found, read_hat_product(), None)
    return check(*simulated_inputs())


def report(results: list[Result]) -> str:
    lines = []
    for r in results:
        mark = {"OK": "✔", "НЕТ": "✘"}.get(r.status.value, "!")
        lines.append(f" {mark} {r.panel.name:<58} {r.status.value}")
        lines += [f"     └ {p}" for p in r.problems]
    ok = sum(r.status is Status.OK for r in results)
    lines.append(f"\n Итого: {ok} из {len(results)} модулей в порядке")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report(run(simulate=not os.path.exists("/dev/i2c-1"))))
