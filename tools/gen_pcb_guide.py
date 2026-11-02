"""Страница-схема сборки плат KODY: каждая деталь нарисована, подписана, по нажатию — что это и зачем.

Берёт раскладку из hardware/pcb/layout.json (её пишет generate_boards.py).
Запуск: python3 tools/gen_pcb_guide.py  →  docs/pcb/kody-pcb-guide.html
"""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAY = json.loads((ROOT / "hardware/pcb/layout.json").read_text(encoding="utf-8"))
W, H = LAY["W"], LAY["H"]

# key → (короткое имя, что это, почему здесь, кто ставит, цвет-тип)
INFO = {
    "pi": ("Raspberry Pi Zero 2 WH", "Мозг. Втыкается снизу в гнездо J1 одним движением.", "Стоит под передней платой; её 4 отверстия совпадают с отверстиями платы — 4 винта M2.5.", "ты: вставить", "module"),
    "J1": ("Гнездо для Pi (J1)", "40 дырок «мама». Гребёнка Pi входит сюда снизу — все 40 контактов сразу.", "Ровно над гребёнкой Pi.", "завод", "conn"),
    "J2": ("GPIO наружу (J2)", "Угловое гнездо 2×20 на левом боку — для твоих проектов. Каждый пин соединён с таким же пином Pi дорожкой внутри платы.", "Рядом с J1, чтобы дорожки были короткими (они уже нарисованы).", "завод", "conn"),
    "lora": ("LoRa E22-900M22S", "Связь на километры, Meshtastic.", "Под своей антенной «LoRa» наверху: от модуля до антенны — пара сантиметров, сигнал не теряется. Между отверстиями Pi, тонкий — помещается над Pi.", "ты: впаять модуль (как SMD-деталь)", "rf"),
    "gps": ("GPS MAX-M10S", "Координаты, скорость, точное время.", "Под антенной «GPS» в левом верхнем углу.", "ты: впаять модуль", "rf"),
    "nrf": ("NRF24 PA/LNA", "2.4 ГГц: мыши, клавиатуры, дроны.", "Под антенной «2.4 ГГц» в правом верхнем углу (раньше стоял низко — это была моя ошибка: 6 см дорожки до антенны съели бы сигнал).", "ты: впаять модуль", "rf"),
    "radio": ("Рация SA818-U", "Голос FM на 400–480 МГц, как настоящая рация, до 1 Вт.", "Самый большой модуль — наверху ему нет места, поэтому он внизу, а к антенне «Рация 433» идёт короткий кабель с защёлками на концах (вставляется, не паяется).", "ты: впаять модуль", "rf"),
    "cc1101": ("Пульты CC1101 (E07-433M20S)", "Запись и повтор своих пультов 433 МГц, как у Flipper.", "Рядом с рацией: они делят одну антенну «Рация 433» через переключатель.", "ты: впаять модуль", "rf"),
    "battery": ("Аккумулятор 8.5×24×70", "≈ 2000 мА·ч, ≈ 3 часа.", "Лежит на передней плате под экраном, лепестки — на площадки BT1–BT3.", "ты: 3 точки пайки", "power"),
    "BT1": ("Площадка BAT+", "Сюда припаивается плюсовой лепесток аккумулятора.", "У верхнего края аккумулятора.", "ты", "power"),
    "BT2": ("Площадка BAT−", "Минусовой лепесток.", "", "ты", "power"),
    "BT3": ("Площадка NTC", "Датчик температуры аккумулятора (защита от перегрева).", "", "ты", "power"),
    "speaker": ("Динамик 1511", "Звук как в телефоне. Решётка — на нижнем торце корпуса.", "Внизу, рядом с решёткой.", "ты: положить, 2 контакта", "audio"),
    "ENC1": ("Крутилка (энкодер EC11)", "Крутится бесконечно в обе стороны + нажимается.", "Правый бок, выше всех кнопок — под большой палец.", "завод", "ui"),
    "SW1": ("Кнопка 1", "Угловая кнопка 6×6, сверху надевается большой колпачок корпуса.", "Правый бок, под крутилкой.", "завод", "ui"),
    "SW2": ("Кнопка 2", "Угловая кнопка 6×6.", "Правый бок.", "завод", "ui"),
    "SW3": ("Кнопка 3", "Угловая кнопка 6×6.", "Правый бок.", "завод", "ui"),
    "SW4": ("Ползунок питания", "Как на игрушечной машинке: вверх — включено, вниз — аккуратное выключение.", "Правый бок, в самом низу.", "завод", "ui"),
    "J3": ("USB-C", "Один разъём: быстрая зарядка + данные.", "Нижний торец, посередине.", "завод", "conn"),
    "J4": ("Антенна GPS (SMA)", "Накручивается GPS-антенна или заглушка.", "Верхний торец, посередине толщины корпуса.", "завод", "rf"),
    "J5": ("Антенна LoRa (SMA)", "Антенна 868 МГц.", "Над модулем LoRa.", "завод", "rf"),
    "J6": ("Антенна «Рация 433» (SMA)", "Антенна как у рации (Nagoya NA-771 SMA-M).", "К ней кабелем подходит модуль рации снизу.", "завод", "rf"),
    "J7": ("Антенна 2.4 ГГц (SMA)", "Антенна 2.4 ГГц.", "Над модулем NRF24.", "завод", "rf"),
    "J10": ("Разъём экрана", "Шлейф экрана защёлкивается сюда. Модель разъёма подберём под купленный экран.", "Над аккумулятором, у верхнего края экрана.", "завод", "conn"),
    "J11": ("Разъём HDMI-шлейфа", "Картинка от Pi: переходник mini-HDMI → шлейф → сюда.", "Снизу платы, рядом с mini-HDMI у Pi.", "завод", "conn"),
    "J20": ("Разъём плата-плата", "Соединяет переднюю и заднюю платы (USB, питание, NFC). Просто вставляется.", "Внизу слева — вне Pi, чтобы платы могли «встретиться».", "завод", "conn"),
    "D1": ("Индикатор заряда 25 %", "4 зелёных светодиода — видно сквозь прозрачный корпус.", "Над USB-C.", "завод", "led"),
    "D2": ("Индикатор заряда 50 %", "", "", "завод", "led"),
    "D3": ("Индикатор заряда 75 %", "", "", "завод", "led"),
    "D4": ("Индикатор заряда 100 %", "", "", "завод", "led"),
    "D5": ("ИК-светодиод дальний (VSLY5940)", "Узкий мощный луч — пульт на десятки метров.", "Левый бок под GPIO — светит сквозь прозрачный корпус.", "завод или ты (2 ножки)", "ir"),
    "D6": ("ИК-светодиод широкий (TSAL6400)", "Широкий луч — не нужно точно целиться.", "", "завод или ты", "ir"),
    "D7": ("ИК-светодиод широкий (TSAL6400)", "", "", "завод или ты", "ir"),
    "D8": ("ИК-светодиод дальний (VSLY5940)", "", "", "завод или ты", "ir"),
    "U30": ("ИК-приёмник TSOP38238", "Ловит обычные пульты.", "Левый бок, над GPIO.", "завод или ты (3 ножки)", "ir"),
    "U31": ("ИК-приёмник «обучающий» TSMP58000", "Копирует любой пульт.", "Левый бок, над GPIO.", "завод или ты", "ir"),
    "TP1": ("Pogo: питание Pi", "Подпружиненный контакт упирается в площадку снизу Pi.", "Точное место снимем с твоей Pi.", "ты: впаять пружинку", "conn"),
    "TP2": ("Pogo: GND", "", "", "ты", "conn"),
    "TP3": ("Pogo: USB D+", "", "", "ты", "conn"),
    "TP4": ("Pogo: USB D−", "", "", "ты", "conn"),
    "TP10": ("Вывод антенны NFC", "Концы катушки NFC — к микросхеме ST25R3916.", "", "—", "rf"),
    "TP11": ("Вывод антенны NFC", "", "", "—", "rf"),
    "TP21": ("Вывод катушки 125 кГц", "Сюда вставляются 2 вывода большой катушки домофонных ключей.", "", "ты: 2 точки", "rf"),
    "TP22": ("Вывод катушки 125 кГц", "", "", "ты", "rf"),
    "nfc": ("Катушка NFC 13.56 МГц", "Нарисована медью прямо на плате — читает и эмулирует карты.", "Нижняя половина спины — прикладываешь карту сюда.", "завод (это дорожки)", "rf"),
    "coil125": ("Катушка 125 кГц на всю спину", "Намотанная катушка по периметру — домофонные ключи на 3–6 см.", "По краю задней платы.", "ты: положить и 2 точки", "rf"),
    "logo": ("Череп + KODY", "Белая краска на чёрной плате, видно сквозь корпус. Логотип ещё обсудим.", "Верх спины, над катушками (краска NFC не мешает).", "завод", "logo"),
}
COLORS = {"module": "#2e7d4a", "rf": "#c9a24a", "conn": "#9aa0a6", "power": "#7ea8e6", "ui": "#e08a4f", "led": "#5fbf7f",
          "ir": "#d06a6a", "audio": "#b88ad9", "logo": "#e7ecef"}

SHORT = {"J4": "GPS", "J5": "LoRa", "J6": "Рация", "J7": "2.4", "BT1": "+", "BT2": "−", "BT3": "t°", "U30": "ИК прм", "U31": "ИК учёба",
         "D5": "ИК", "D6": "ИК", "D7": "ИК", "D8": "ИК", "D1": "", "D2": "", "D3": "", "D4": "", "SW1": "Кн 1", "SW2": "Кн 2", "SW3": "Кн 3",
         "SW4": "ВКЛ", "J20": "плата-плата", "J11": "HDMI", "J10": "Экран", "J1": "Гнездо Pi", "J2": "GPIO наружу", "J3": "USB-C",
         "TP1": "", "TP2": "", "TP3": "", "TP4": "", "TP10": "", "TP11": "", "TP21": "", "TP22": "", "ENC1": "Крутилка"}

VIEWS = [
    ("front-top", "Передняя — лицо", "front", "top", False),
    ("front-bottom", "Передняя — низ", "front", "bottom", True),
    ("back-out", "Задняя — снаружи", "back", "bottom", True),
    ("back-in", "Задняя — внутри", "back", "top", False),
]
EXTRA_BACK = [
    dict(board="back", key="coil125", side="bottom", x=2.8, y=3.8, w=W - 5.6, h=H - 7.6),
    dict(board="back", key="nfc", side="bottom", x=W / 2 - 20.25, y=H / 2 + 17 - 27, w=40.5, h=54),
    dict(board="back", key="logo", side="bottom", x=W / 2 - 15, y=7, w=30, h=30),
]


def items_for(board, side):
    out = [i for i in LAY["items"] + EXTRA_BACK if i["board"] == board and i["side"] == side and i["key"] in INFO]
    seen, res = set(), []
    for i in out:
        k = (i["key"], round(i["x"], 1))
        if k not in seen:
            seen.add(k); res.append(i)
    return sorted(res, key=lambda i: -i["w"] * i["h"])


def svg_for(board, side, mirror):
    s = 6
    parts = [f'<svg viewBox="-4 -4 {W*s+8} {H*s+8}" role="img" aria-label="плата">',
             f'<rect x="0" y="0" width="{W*s}" height="{H*s}" rx="{3*s}" class="pcb {board}"/>']
    for i in items_for(board, side):
        x = (W - i["x"] - i["w"]) if mirror else i["x"]
        key = i["key"]; name, *_rest, kind = INFO[key]
        col = COLORS[kind]
        lab = html.escape(SHORT.get(key, name.split(" (")[0]))
        fs = max(7, min(13, i["w"] * s / max(len(lab), 1) * 1.6, i["h"] * s * 0.45))
        parts.append(f'<g class="part" data-key="{key}" tabindex="0"><rect x="{x*s:.1f}" y="{i["y"]*s:.1f}" width="{i["w"]*s:.1f}" height="{i["h"]*s:.1f}" rx="4" '
                     f'style="--c:{col}"/><text x="{(x+i["w"]/2)*s:.1f}" y="{(i["y"]+(3.2 if key=="coil125" else i["h"]/2))*s:.1f}" font-size="{fs:.1f}">{lab}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def main():
    info_js = json.dumps({k: dict(name=v[0], what=v[1], why=v[2], who=v[3]) for k, v in INFO.items()}, ensure_ascii=False)
    tabs = "".join(f'<button role="tab" data-v="{v}" aria-selected="{str(n==0).lower()}">{html.escape(t)}</button>' for n, (v, t, *_r) in enumerate(VIEWS))
    boards = "".join(f'<div class="board" data-v="{v}"{"" if n == 0 else " hidden"}>{svg_for(b, sd, m)}</div>' for n, (v, t, b, sd, m) in enumerate(VIEWS))
    page = TEMPLATE.replace("%TABS%", tabs).replace("%BOARDS%", boards).replace("%INFO%", info_js)
    out = ROOT / "docs/pcb/kody-pcb-guide.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print("OK:", out)


TEMPLATE = """<title>KODY Платы</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap">
<style>
/* Layout: tabs for the four board sides, the board drawing, and a sticky info card. Kit-PCB look: red mask, white silkscreen. */
:root{--bg:#eef0ed;--panel:#fff;--ink:#18201b;--muted:#5b665e;--line:#d3d8d2;--accent:#b8612a;--mask-front:#9e1f1a;--mask-back:#141618;--silk:#f4f4f0;
 --f-body:"Golos Text",system-ui,-apple-system,sans-serif;--f-mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#111613;--panel:#19201b;--ink:#e7ece7;--muted:#9aa69d;--line:#2a332d;--accent:#e08a4f;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111613;--panel:#19201b;--ink:#e7ece7;--muted:#9aa69d;--line:#2a332d;--accent:#e08a4f;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.5}
.wrap{max-width:980px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:18px 40px;display:flex;flex-direction:column;gap:14px}
h1{font-size:clamp(22px,5vw,30px);margin:0;font-weight:600;text-wrap:balance}
p{margin:0;color:var(--muted);max-width:68ch}
.tabs{display:flex;flex-wrap:wrap;gap:6px}
.tabs button{font:inherit;font-size:14px;font-weight:600;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:7px 13px;cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.main{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:14px;align-items:start}
@media (max-width:720px){.main{grid-template-columns:1fr}}
.board svg{width:100%;height:auto;display:block;max-height:78vh}
.pcb.front{fill:var(--mask-front)} .pcb.back{fill:var(--mask-back)}
.part rect{fill:color-mix(in srgb,var(--c) 28%,transparent);stroke:var(--silk);stroke-width:1.6;cursor:pointer}
.part text{fill:var(--silk);font-family:var(--f-mono);font-weight:600;text-anchor:middle;dominant-baseline:middle;pointer-events:none}
.part:hover rect,.part:focus rect,.part.sel rect{fill:color-mix(in srgb,var(--c) 70%,transparent);stroke:#ffe08a;stroke-width:2.6;outline:none}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;position:sticky;top:12px}
.card h2{font-size:17px;margin:0 0 6px}
.card dl{margin:0;display:grid;gap:6px}
.card dt{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.card dd{margin:0}
.note{font-size:13px;color:var(--muted)}
</style>
<div class="wrap">
  <h1>KODY: что где на платах</h1>
  <p>Каждая деталь обведена и подписана, как на готовой плате-конструкторе. Нажми на деталь — справа (на телефоне ниже) появится, что это, зачем она здесь и кто её ставит. Размеры настоящие, в масштабе.</p>
  <div class="tabs" role="tablist">%TABS%</div>
  <p class="note">«Низ» и «снаружи» нарисованы так, как ты видишь плату, перевернув её, — поэтому лево и право там поменялись местами.</p>
  <div class="main">
    <div>%BOARDS%</div>
    <div class="card" id="card"><h2>Нажми на деталь</h2><p class="note">ESP32-C5 убран: Wi-Fi и Bluetooth у Pi свои, отдельный чип нужен был только для «хакерских» Wi-Fi-инструментов на 5 ГГц. Если захочешь — вернём.</p></div>
  </div>
</div>
<script>
(function(){
var INFO=%INFO%, card=document.getElementById("card");
function show(key){ var i=INFO[key]; if(!i) return; card.innerHTML="";
  var h=document.createElement("h2"); h.textContent=i.name; card.appendChild(h);
  var dl=document.createElement("dl"); [["Что это",i.what],["Почему здесь",i.why],["Кто ставит",i.who]].forEach(function(r){ if(!r[1]) return;
    var dt=document.createElement("dt"); dt.textContent=r[0]; var dd=document.createElement("dd"); dd.textContent=r[1]; dl.appendChild(dt); dl.appendChild(dd); });
  card.appendChild(dl);
  document.querySelectorAll(".part").forEach(function(p){ p.classList.toggle("sel", p.dataset.key===key); });
  if(window.innerWidth<720) card.scrollIntoView({behavior:"smooth",block:"nearest"}); }
document.querySelectorAll(".part").forEach(function(p){ p.addEventListener("click",function(){ show(p.dataset.key); }); p.addEventListener("keydown",function(e){ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); show(p.dataset.key);} }); });
document.querySelectorAll(".tabs button").forEach(function(b){ b.addEventListener("click",function(){
  document.querySelectorAll(".tabs button").forEach(function(x){ x.setAttribute("aria-selected", x===b); });
  document.querySelectorAll(".board").forEach(function(d){ d.hidden = d.dataset.v!==b.dataset.v; }); }); });
})();
</script>
"""

if __name__ == "__main__":
    main()
