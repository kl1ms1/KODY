"""Автоопределение платы: одна прошивка (одна SD-карта) для всех Pi Zero.

Как это работает:
  * Linux пишет модель платы в /proc/device-tree/model, например
    «Raspberry Pi Zero W Rev 1.1» или «Raspberry Pi Zero 2 W Rev 1.0».
  * По модели выбирается профиль: сколько ядер, какую частоту кадров
    интерфейса держать, какие тяжёлые функции включать.
  * Гребёнка 40 GPIO у всех Zero одинаковая, поэтому плата KODY и карта
    пинов (pins.py) не меняются. Отличается только производительность.

Чтобы SD-карта подходила к обеим платам, ставим Raspberry Pi OS Lite
**32-bit** (armhf): она запускается и на Zero W (ARMv6), и на Zero 2 W.
64-bit образ на Zero W / WH не загрузится.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

MODEL_PATH = "/proc/device-tree/model"


@dataclass(frozen=True)
class BoardProfile:
    key: str
    name: str
    cores: int
    ui_fps: int            # целевая частота кадров интерфейса
    display_spi_hz: int    # частота SPI для экрана
    sdr_waterfall: bool    # «водопад» SDR в реальном времени (тяжёлый)
    sdr_max_rate: int      # макс. частота дискретизации SDR, выборок/с
    simulated: bool = False


PROFILES = {
    "zero_w": BoardProfile("zero_w", "Raspberry Pi Zero W / WH", 1, 30,
                           48_000_000, False, 1_024_000),
    "zero_2w": BoardProfile("zero_2w", "Raspberry Pi Zero 2 W / WH", 4, 50,
                            62_500_000, True, 2_400_000),
    "pc": BoardProfile("pc", "Компьютер (симуляция)", os.cpu_count() or 1, 60,
                       0, True, 2_400_000, simulated=True),
}


def profile_for_model(model: str | None) -> BoardProfile:
    """Профиль по строке модели. Неизвестную Pi считаем слабой — безопасный вариант."""
    if not model:
        return PROFILES["pc"]
    m = model.strip("\x00 \n").lower()
    if "zero 2" in m:
        return PROFILES["zero_2w"]
    if "raspberry pi" in m:
        # Zero, Zero W, Zero WH и любые незнакомые Pi — консервативный профиль.
        # (Pi 3/4/5 тоже заработают, гребёнка та же, просто с запасом.)
        return PROFILES["zero_w"]
    return PROFILES["pc"]


def read_model(path: str = MODEL_PATH) -> str | None:
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def detect(path: str = MODEL_PATH) -> tuple[BoardProfile, str | None]:
    model = read_model(path)
    return profile_for_model(model), model
