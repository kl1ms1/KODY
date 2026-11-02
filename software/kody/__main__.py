"""Текстовый прототип меню KODY: Проекты → Лампочка.

На устройстве это же меню будет на тачскрине и крутилке; логика та же.
Запуск: python3 -m kody [--sim]
"""

from __future__ import annotations

import sys

from .board import detect
from .hal import make_pwm_led
from .lamp import PRESETS, Lamp, LampPreset, wiring_advice
from .pins import PinUnavailable, user_pins


def choose(title: str, options: list[str]) -> int | None:
    print(f"\n=== {title} ===")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("  0. Назад")
    while True:
        raw = input("> ").strip()
        if raw == "0":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("Введи номер из списка")


def ask_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} [{default:g}]: ").strip().replace(",", ".")
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


def lamp_project(simulate: bool | None) -> None:
    idx = choose("Лампочка — выбери пресет", [p.name for p in PRESETS] + ["Своя (ввести вольтаж и ток)"])
    if idx is None:
        return
    if idx == len(PRESETS):
        preset = LampPreset("Своя", ask_float("Напряжение, В", 2.0), ask_float("Ток, мА", 10))
    else:
        preset = PRESETS[idx]

    advice = wiring_advice(preset)
    print(f"\nКак подключить «{preset.name}»:\n  {advice.text}")

    pins = user_pins()
    pidx = choose("На какой пин подключил?",
                  [f"GPIO{p.bcm} (физ. пин {p.phys})" for p in pins])
    if pidx is None:
        return
    try:
        lamp = Lamp(pins[pidx].bcm, preset, lambda bcm: make_pwm_led(bcm, simulate))
    except PinUnavailable as exc:
        print(exc)
        return

    effects = ["Включить", "Выключить", "Мигание", "Мигание плавное",
               "Дыхание (плавно жик-жик)", "Яркость"]
    try:
        while True:
            e = choose(f"{preset.name} на GPIO{lamp.pin.bcm}", effects)
            if e is None:
                break
            try:
                if e == 0:
                    lamp.on()
                elif e == 1:
                    lamp.off()
                elif e == 2:
                    t = ask_float("Скорость, сек на вспышку", 0.5)
                    lamp.blink(t, t)
                elif e == 3:
                    lamp.soft_blink()
                elif e == 4:
                    lamp.breathe(ask_float("Период, сек", 2.0))
                elif e == 5:
                    lamp.on(ask_float("Яркость, %", 50) / 100)
            except ValueError as exc:
                print(exc)
    finally:
        lamp.close()


def main(argv: list[str]) -> int:
    simulate = True if "--sim" in argv else None
    profile, model = detect()
    print(f"KODY: плата — {model.strip(chr(0)) if model else profile.name}; "
          f"профиль «{profile.key}»: {profile.cores} ядер, интерфейс {profile.ui_fps} FPS, "
          f"SDR-водопад {'вкл' if profile.sdr_waterfall else 'выкл'}")
    if profile.simulated:
        simulate = True
    projects = ["Лампочка"]
    try:
        while True:
            top = choose("KODY — главное меню", ["Проекты"])
            if top is None:
                return 0
            p = choose("Проекты", projects)
            if p == 0:
                lamp_project(simulate)
    except (KeyboardInterrupt, EOFError):
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
