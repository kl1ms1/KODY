"""Генератор docs/shopping-list.md: что купить и ссылки на поиск по российским маркетплейсам.

Запуск: python3 tools/gen_shopping_list.py
"""

from pathlib import Path
from urllib.parse import quote_plus

# (section, item, qty, query, check, stage)  stage: M = макетка сейчас, P = для платы v1
ITEMS = [
 # (раздел, что, шт., поисковый запрос, на что смотреть, M = купить и поставить самому / P = мелкая микросхема на плату)
 ("1. Мозги", "Raspberry Pi Zero 2 WH (с распаянной гребёнкой)", "1", "Raspberry Pi Zero 2 WH", "Именно «2 WH»: 4 ядра и гребёнка уже впаяна. Твоя Zero WH — для макетки", "M"),
 ("1. Мозги", "Карта microSD 64 ГБ, класс A2 (SanDisk Extreme / Samsung PRO Plus)", "1", "microSD 64GB A2 SanDisk Extreme", "Не no-name — от карты зависит скорость системы", "M"),
 ("2. Экран", "Waveshare 3.5inch DSI LCD (H): 3.5″ IPS 480×800, ёмкостный тач, 60 Гц", "1", "Waveshare 3.5inch DSI LCD H 480x800", "Именно (H) 480×800, портретный. Подключается через наш мост HDMI→DSI", "M"),
 ("2. Экран", "Для макетки сразу: Waveshare 3.5inch HDMI LCD (E) 640×480 с тачем", "1", "Waveshare 3.5inch HDMI LCD E 640x480", "Втыкается в mini-HDMI Pi напрямую — можно писать интерфейс, пока нет нашей платы", "M"),
 ("2. Экран", "Переходник mini-HDMI (папа) → FPC-шлейф + шлейф 5–10 см", "1 комплект", "mini HDMI FPC adapter ribbon", "Комплект «HDMI FPC»: штекер mini-HDMI + плоский шлейф + ответная плата", "M"),
 ("3. Управление", "Энкодер EC11 с кнопкой, без упора, 20 щелчков, вал 15 мм (угловой / horizontal)", "2", "энкодер EC11 горизонтальный с кнопкой", "Энкодер крутится бесконечно в обе стороны. Угловой — вал выходит вбок", "M"),
 ("3. Управление", "Ручка для энкодера алюминиевая рифлёная Ø15 мм, под вал 6 мм D", "2", "ручка энкодера алюминиевая 15мм рифленая", "", "M"),
 ("3. Управление", "Тактовая кнопка угловая 6×6×5 мм (боковая, THT)", "6", "тактовая кнопка 6x6 угловая", "3 на устройство + запас. Колпачки печатаем вместе с корпусом", "M"),
 ("3. Управление", "Переключатель-ползунок «как на машинке» SS12D07 / SS-12D00G4 (2 положения, 3 вывода)", "3", "SS12D07 переключатель движковый угловой", "Угловой (ползунок смотрит вбок). Он только даёт сигнал «вкл/выкл» микроконтроллеру", "M"),
 ("3. Управление", "Вибромотор линейный LRA 0832 / 1027 + драйвер DRV2605L (модуль для макетки)", "1+1", "DRV2605L модуль", "Даёт чёткие «щелчки» крутилки", "M"),
 ("4. Звук", "Динамик-коробочка от смартфона 1511 (15×11×3 мм), 8 Ом", "2", "динамик 1511 8 Ом speaker box", "Коробочка с камерой — басовитее и громче голого динамика", "M"),
 ("4. Звук", "Усилитель I2S MAX98357A (модуль для макетки / микросхема на плату)", "1+1", "MAX98357A", "Звук берётся прямо из HDMI через мост", "M"),
 ("4. Звук", "Цифровой микрофон I2S ICS-43434 / INMP441 (модуль для макетки)", "2", "INMP441 модуль", "Голос для рации и заметок", "M"),
 ("5. Радио", "Рация: модуль SA818-U (или SA868-U), 400–480 МГц FM, до 1 Вт", "1", "SA818-U модуль рации", "Именно U (UHF). Это «внутренности рации» — голос на каналах LPD/PMR", "M"),
 ("5. Радио", "Пульты 433: модуль CC1101 Ebyte E07-433M20S", "1", "E07-433M20S", "Версия с усилителем, IPEX", "M"),
 ("5. Радио", "LoRa: Ebyte E22-900M22S (SX1262, 868 МГц)", "1", "E22-900M22S SX1262", "SX1262, 22 dBm, IPEX", "M"),
 ("5. Радио", "2.4 ГГц: NRF24L01+ PA+LNA SMD-модуль с IPEX", "1", "NRF24L01 PA LNA SMD IPEX", "Плоский SMD, не с большой SMA-антенной", "M"),
 ("5. Радио", "Wi-Fi / Bluetooth: модуль ESP32-C5-WROOM-1", "1", "ESP32-C5-WROOM-1", "Если не найдёшь — ESP32-C6-WROOM-1 (только 2.4 ГГц)", "M"),
 ("5. Радио", "GPS: модуль u-blox MAX-M10S (или для макетки ATGM336H)", "1", "MAX-M10S", "Сим-карта не нужна", "M"),
 ("5. Радио", "Гнездо SMA-female на край платы (edge-mount)", "4", "SMA female edge mount PCB", "4 антенны посередине толщины", "M"),
 ("5. Радио", "Кабели IPEX (u.FL) 5 см — запас", "4", "кабель IPEX 5см", "На случай, если модуль встанет не впритык к гнезду", "M"),
 ("6. Антенны", "LoRa 868 МГц, 5 dBi, SMA-male (штырёк)", "1", "антенна 868 МГц 5 dBi SMA", "", "M"),
 ("6. Антенны", "Рация 433/446 МГц «как у рации», SMA-male — Nagoya NA-771 версии SMA-M", "1", "Nagoya NA-771 SMA-M", "Для Baofeng продают SMA-F — такая НЕ подойдёт", "M"),
 ("6. Антенны", "2.4 ГГц, 3–5 dBi, SMA-male", "1", "антенна 2.4 ГГц 5 dBi SMA", "", "M"),
 ("6. Антенны", "GPS активная короткая антенна, SMA-male", "1", "активная GPS антенна SMA", "Короткая «шайба» или «пенёк»", "M"),
 ("6. Антенны", "Заглушка-нагрузка SMA 50 Ом, 1–2 Вт", "4", "нагрузка SMA 50 Ом терминатор", "Нагрузка, а не пылевой колпачок — спасает усилитель", "M"),
 ("7. NFC / RFID", "Плата X-NUCLEO-NFC08A1 (ST25R3916B) — отладить NFC до нашей платы", "1", "X-NUCLEO-NFC08A1", "Тот же чип, что во Flipper", "M"),
 ("7. NFC / RFID", "Ферритовая плёнка для NFC-антенны 40×40 мм", "2", "ферритовая пленка NFC", "Между катушкой и платой — иначе NFC не ловит", "M"),
 ("7. NFC / RFID", "Катушка 125 кГц (RFID, ~700 мкГн) готовая", "2", "катушка 125 кГц RFID", "", "M"),
 ("7. NFC / RFID", "Метки: NTAG215, брелоки T5577, EM4100", "набор", "брелок T5577 125 кГц", "Чтобы проверять", "M"),
 ("8. ИК-порт", "ИК-светодиод Vishay VSLY5940 (940 нм, узкий луч ±3°) — дальность", "4", "VSLY5940", "2 на плату + запас. Импульсы до 1 А — десятки метров", "M"),
 ("8. ИК-порт", "ИК-светодиод Vishay TSAL6400 (940 нм, широкий ±25°) — чтобы не целиться", "4", "TSAL6400", "2 на плату + запас", "M"),
 ("8. ИК-порт", "ИК-приёмник Vishay TSOP38238 (38 кГц)", "2", "TSOP38238", "Обычные пульты", "M"),
 ("8. ИК-порт", "ИК-приёмник «обучающий» Vishay TSMP58000 (широкополосный)", "1", "TSMP58000", "Ловит любые несущие — копирует любой пульт", "M"),
 ("8. ИК-порт", "Чёрный ИК-прозрачный акрил 1–2 мм (окно ИК)", "1 лист", "ИК прозрачный акрил черный", "Снаружи чёрный, ИК проходит", "M"),
 ("9. Питание", "Аккумулятор Li-Po ≈ 7 × 28 × 80 мм, 2000–2300 мА·ч, с NTC (3 вывода), лепестки без проводов", "2", "Li-Po 3.7V 2000mAh 7x28x80", "Искать по размеру; ёмкость проверить — у дешёвых бывает завышена", "M"),
 ("9. Питание", "Гнездо USB-C 16 pin (HRO TYPE-C-31-M-12 или аналог)", "3", "TYPE-C-31-M-12", "Одно на устройство: данные + быстрая зарядка", "M"),
 ("9. Питание", "Для макетки: модуль зарядки BQ25895 + модуль USB-PD триггер CH224K", "1+1", "BQ25895 модуль", "", "M"),
 ("9. Питание", "Термопрокладка 1.5–2 мм (процессор Pi → плата)", "1", "термопрокладка 2мм", "", "M"),
 ("9. Питание", "Каптоновый скотч 20 мм", "1", "каптоновый скотч 20мм", "", "M"),
 ("10. Сборка", "Гнездо 2×20 2.54 мм «вход снизу» (bottom-entry) для Pi", "2", "гнездо 2x20 bottom entry 2.54", "Гребёнка Pi проходит насквозь через плату. Высоту проверим по твоей Pi", "M"),
 ("10. Сборка", "Гнездо 2×20 2.54 мм угловое (GPIO наружу)", "2", "гребенка 2x20 мама угловая 2.54", "", "M"),
 ("10. Сборка", "Разъём плата-плата 1.27 мм 2×12 (штырь + гнездо), высота стека ~7 мм", "2", "гребенка 1.27 2x12 штырь гнездо", "", "M"),
 ("10. Сборка", "Pogo-пины SMD Ø1 мм, высота 2.5 мм", "10", "pogo pin SMD 1мм", "4 на устройство + запас", "M"),
 ("10. Сборка", "Винты M2 × 12 и M2 × 6 + латунные вставки M2", "набор", "винты M2 набор вставки", "", "M"),
 ("10. Сборка", "Корпус: печать PA12 (SLS) на заводе, 2 части + колпачки кнопок", "1", "SLS печать PA12", "JLC3DP или местная SLS-печать", "M"),
 ("11. Мелочь на плату", "Мост HDMI → MIPI DSI: Lontium LT6911C (QFN64)", "1", "LT6911C", "Мелкий корпус — ставит завод", "P"),
 ("11. Мелочь на плату", "Микроконтроллер радио: RP2350B (QFN80) + флеш W25Q128 + кварц 12 МГц", "1", "RP2350B", "", "P"),
 ("11. Мелочь на плату", "Микроконтроллер питания и кнопок: STM32G031K8 (LQFP32)", "1", "STM32G031K8", "Его можно паять руками", "P"),
 ("11. Мелочь на плату", "Зарядка BQ25895 + PD-триггер CH224K + повышайка TPS61088", "1+1+1", "BQ25895", "", "P"),
 ("11. Мелочь на плату", "Защита аккумулятора DW01A + ключи FS8205A, датчик заряда MAX17048", "1+1+1", "DW01A FS8205A", "", "P"),
 ("11. Мелочь на плату", "USB: хаб USB2514B, переключатели TS3USB221 ×2, определитель роли TUSB320", "1+2+1", "USB2514B", "", "P"),
 ("11. Мелочь на плату", "NFC: ST25R3916 + кварц 27.12 МГц; 125 кГц: компаратор TLV3201 + MOSFET AO3400", "1", "ST25R3916", "", "P"),
 ("11. Мелочь на плату", "Датчики: гироскоп LSM6DSV16X, свет VEML7700, часы RV-3028-C7, вибро DRV2605L", "1+1+1+1", "LSM6DSV16X", "", "P"),
 ("11. Мелочь на плату", "Защита GPIO от статики (TVS-сборки) + самовосстанавливающиеся предохранители", "по 4", "TVS ESD array", "", "P"),
 ("12. Инструмент", "Паяльная станция + фен, флюс-гель, оплётка", "1", "паяльная станция с феном", "Для модулей и разъёмов", "M"),
 ("12. Инструмент", "Мультиметр, NanoVNA (настройка антенн NFC)", "1+1", "NanoVNA", "", "M"),
]

SHOPS = [
    ("Ozon", "https://www.ozon.ru/search/?text={}"),
    ("WB", "https://www.wildberries.ru/catalog/0/search.aspx?search={}"),
    ("Я.Маркет", "https://market.yandex.ru/search?text={}"),
    ("AliExpress", "https://aliexpress.ru/wholesale?SearchText={}"),
    ("ЧипДип", "https://www.chipdip.ru/search?searchtext={}"),
]


def links(query):
    q = quote_plus(query)
    return " · ".join(f"[{name}]({url.format(q)})" for name, url in SHOPS)


def render():
    out = [
        "# KODY — список покупок",
        "",
        "> Файл сгенерирован `tools/gen_shopping_list.py` — правь список там.",
        "",
        "Ссылки ведут на **поиск** по каждому маркетплейсу (готовый запрос), а не на",
        "конкретного продавца: цены и наличие меняются каждый день. Выбирай карточку",
        "с отзывами и сверяй колонку «Проверить». Список под концепцию v2 «пазл»",
        "(KODY v9: экран 3.5″, ≈3 ч, крутилка, ИК-порт, 1 USB-C), см. `docs/concept.md`.",
        "",
        "**🟢 — купить и поставить самому, 🔵 — мелкая микросхема: её ставит завод при заказе платы (или паять феном).**",
        "",
    ]
    section = None
    for sec, item, qty, query, check, stage in ITEMS:
        if sec != section:
            section = sec
            out += ["", f"## {sec}", "", "| | Что | Шт. | Проверить | Где искать |", "|---|---|---|---|---|"]
        mark = "🟢" if stage == "M" else "🔵"
        out.append(f"| {mark} | {item}<br>`{query}` | {qty} | {check or '—'} | {links(query)} |")
    return "\n".join(out) + "\n"


HTML_HEAD = """<title>KODY Покупки</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Golos+Text:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">
<style>
/* Layout: one narrow checklist column, sections as groups, shop links as chips. */
:root{--bg:#eef0ed;--panel:#fff;--ink:#18201b;--muted:#5b665e;--line:#d3d8d2;--accent:#b8612a;--now:#2f7d4a;--later:#3d6fb0;
 --f-display:"Unbounded","Golos Text",system-ui,sans-serif;--f-body:"Golos Text",system-ui,-apple-system,sans-serif;--f-mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#111613;--panel:#19201b;--ink:#e7ece7;--muted:#9aa69d;--line:#2a332d;--accent:#e08a4f;--now:#5fbf7f;--later:#7ea8e6;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111613;--panel:#19201b;--ink:#e7ece7;--muted:#9aa69d;--line:#2a332d;--accent:#e08a4f;--now:#5fbf7f;--later:#7ea8e6;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.5}
.wrap{max-width:760px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 48px;display:flex;flex-direction:column;gap:20px}
h1{font-family:var(--f-display);font-weight:700;font-size:clamp(24px,6vw,34px);margin:0;text-wrap:balance}
h2{font-family:var(--f-display);font-weight:500;font-size:17px;margin:0 0 8px}
p{margin:6px 0 0;color:var(--muted)}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:13px}
.bar button{font:inherit;font-weight:600;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:6px 12px;cursor:pointer}
.bar button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.prog{font-family:var(--f-mono);font-size:13px;margin-left:auto}
.item{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin-bottom:8px}
.item input{width:22px;height:22px;margin:2px 0 0;accent-color:var(--accent)}
.item.done{opacity:.55}
.item.done b{text-decoration:line-through}
.body{min-width:0;display:flex;flex-direction:column;gap:4px}
.meta{font-size:12px;font-family:var(--f-mono);color:var(--muted)}
.st{font-weight:600}.st.now{color:var(--now)}.st.later{color:var(--later)}
.chk{font-size:13px;color:var(--muted)}
.shops{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.shops a{font-size:13px;font-weight:600;color:var(--ink);text-decoration:none;border:1px solid var(--line);border-radius:7px;padding:4px 9px}
.shops a:hover,.shops a:focus-visible{border-color:var(--accent);color:var(--accent);outline:none}
code{font-family:var(--f-mono);font-size:12px;background:var(--bg);border-radius:4px;padding:1px 5px;overflow-wrap:anywhere}
</style>
"""

HTML_SCRIPT = """<script>
(function(){
var KEY="kody-shop-v9", st={}; try{ st=JSON.parse(localStorage.getItem(KEY)||"{}"); }catch(e){}
var boxes=[].slice.call(document.querySelectorAll(".item input")), filter="all";
function save(){ try{ localStorage.setItem(KEY,JSON.stringify(st)); }catch(e){} }
function update(){ var done=0, shown=0;
  boxes.forEach(function(b){ var it=b.closest(".item"); it.classList.toggle("done",b.checked); if(b.checked) done++;
    var vis = filter==="all" || it.dataset.stage===filter; it.hidden=!vis; if(vis) shown++; });
  document.querySelectorAll("section").forEach(function(s){ s.hidden = !s.querySelector(".item:not([hidden])"); });
  document.getElementById("prog").textContent="Куплено "+done+" из "+boxes.length; }
boxes.forEach(function(b){ b.checked=!!st[b.id]; b.addEventListener("change",function(){ st[b.id]=b.checked; save(); update(); }); });
document.querySelectorAll("[data-f]").forEach(function(btn){ btn.addEventListener("click",function(){ filter=btn.dataset.f;
  document.querySelectorAll("[data-f]").forEach(function(x){ x.setAttribute("aria-pressed", x===btn ? "true":"false"); }); update(); }); });
update();
})();
</script>
"""


def render_html():
    from html import escape as e
    out = [HTML_HEAD, '<div class="wrap"><header><h1>KODY: что купить</h1>',
           "<p>Нажми на магазин — откроется поиск с готовым запросом. Выбирай карточку с отзывами и сверяй, что написано серым. "
           "Галочки сохраняются в этом браузере.</p></header>",
           '<div class="bar"><button data-f="all" aria-pressed="true">Всё</button>'
           '<button data-f="M" aria-pressed="false">Купить и поставить самому</button>'
           '<button data-f="P" aria-pressed="false">Мелочь — ставит завод</button><span class="prog" id="prog"></span></div>']
    section = None
    for i, (sec, item, qty, query, check, stage) in enumerate(ITEMS):
        if sec != section:
            if section is not None:
                out.append("</section>")
            section = sec
            out.append(f"<section><h2>{e(sec)}</h2>")
        q = quote_plus(query)
        shops = "".join(f'<a href="{e(url.format(q))}" target="_blank" rel="noopener">{e(name)}</a>' for name, url in SHOPS)
        st_cls, st_txt = ("now", "КУПИТЬ") if stage == "M" else ("later", "НА ПЛАТУ (ЗАВОД)")
        out.append(
            f'<div class="item" data-stage="{stage}"><input type="checkbox" id="it{i}" aria-label="{e(item)}">'
            f'<div class="body"><b>{e(item)}</b>'
            f'<span class="meta"><span class="st {st_cls}">{st_txt}</span> · {e(qty)} шт. · <code>{e(query)}</code></span>'
            + (f'<span class="chk">{e(check)}</span>' if check else "")
            + f'<div class="shops">{shops}</div></div></div>')
    out.append("</section></div>")
    out.append(HTML_SCRIPT)
    return "\n".join(out)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    (root / "docs" / "shopping-list.md").write_text(render(), encoding="utf-8")
    (root / "docs" / "shopping" ).mkdir(exist_ok=True)
    (root / "docs" / "shopping" / "kody-shopping.html").write_text(render_html(), encoding="utf-8")
    print("OK:", f"{len(ITEMS)} позиций → docs/shopping-list.md, docs/shopping/kody-shopping.html")
