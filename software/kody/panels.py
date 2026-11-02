"""Самопроверка пазла: какие платы вставлены и всё ли на них отвечает.

Как KODY узнаёт свои платы:
  * Ядро (плата с гнездом, в которое вставлена Pi) несёт стандартный HAT
    EEPROM на пинах ID_SD/ID_SC. Linux читает его при загрузке и кладёт имя
    в /proc/device-tree/hat/product.
  * Каждая плата пазла несёт крошечный EEPROM 24C02 на общей шине I2C со
    своим адресом (0x50…0x55). Отвечает адрес — плата вставлена.
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
CORE_PRODUCT = "KODY Core"


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
    eeprom: int | None              # адрес EEPROM платы на I2C1 (None — особая проверка)
    devices: tuple[Device, ...] = ()


PANELS: tuple[Panel, ...] = (
    Panel("core", "Ядро (гнездо для Pi, гироскоп, вибро)", None,
          (Device(0x6B, "гироскоп LSM6DSO"),)),
    Panel("screen", "Экран с тачем (спереди)", 0x50, (Device(0x15, "тач CST816"),)),
    Panel("left", "Кнопки + SD (левый бок)", 0x51),
    Panel("right", "Крутилка + кнопка (правый бок)", 0x52),
    Panel("top", "GPIO + антенны + USB-C данные (верх)", 0x53),
    Panel("power", "Зарядка + аккумулятор (низ)", 0x54,
          (Device(0x6A, "зарядка BQ25895"), Device(0x36, "датчик заряда MAX17048"))),
    Panel("back", "Радио + NFC + GPS (сзади)", 0x55),
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
        if p.key == "core":
            present = bool(hat_product) and hat_product.strip("\x00 \n") == CORE_PRODUCT
        else:
            present = p.eeprom in i2c_present
        if not present:
            results.append(Result(p, Status.MISSING))
            continue
        problems = [f"не отвечает {d.name} (0x{d.addr:02X})" for d in p.devices if d.addr not in i2c_present]
        if p.key == "back" and rp2040_ok is False:
            problems.append("RP2040 не отвечает по UART")
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
        if p.key == "core":
            hat = CORE_PRODUCT
        else:
            present.add(p.eeprom)
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
        lines.append(f" {mark} {r.panel.name:<42} {r.status.value}")
        lines += [f"     └ {p}" for p in r.problems]
    ok = sum(r.status is Status.OK for r in results)
    lines.append(f"\n Итого: {ok} из {len(results)} плат в порядке")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report(run(simulate=not os.path.exists("/dev/i2c-1"))))
