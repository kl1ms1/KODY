"""Генератор docs/shopping-list.md: что купить и ссылки на поиск по российским маркетплейсам.

Запуск: python3 tools/gen_shopping_list.py
"""

from pathlib import Path
from urllib.parse import quote_plus

# (section, item, qty, query, check, stage)  stage: M = макетка сейчас, P = для платы v1
ITEMS = [
 ("Мозги", "Raspberry Pi Zero 2 WH (потом, когда будешь брать новую)", "1", "Raspberry Pi Zero 2 WH", "Именно «2 WH» — с распаянной гребёнкой. Сейчас работаем на твоей Zero WH", "P"),
 ("Мозги", "Raspberry Pi Pico (RP2040) — сопроцессор радио на макетке", "2", "Raspberry Pi Pico RP2040", "Оригинал или клон на RP2040", "M"),
 ("Мозги", "Карта microSD 32 ГБ, класс A1 (системная + для файлов)", "2", "microSD 32GB A1 Samsung EVO", "Samsung/Kingston/SanDisk, не no-name", "M"),
 ("Экран (спереди)", "Экран 1.9\" IPS 170×320 ST7789 с ёмкостным тачем", "2", "1.9 inch IPS 170x320 ST7789 capacitive touch", "IPS, 170×320, тач ёмкостный (CST816), интерфейс SPI. Это самый близкий к размеру Pi Zero серийный экран", "M"),
 ("Экран (спереди)", "Запасной вариант без тача: Waveshare 1.9inch LCD 170×320", "1", "Waveshare 1.9inch LCD 170x320", "Если с тачем не найдётся — для отладки картинки", "M"),
 ("Кнопки и крутилка (бока)", "Тактовые кнопки 6×6 мм угловые (боковые) + колпачки Ø9", "10", "тактовая кнопка 6x6 угловая боковая", "3 на девайс: 2 слева, 1 справа. Большой колпачок печатаем на 3D-принтере", "M"),
 ("Кнопки и крутилка (бока)", "Энкодер EC11 с кнопкой (крутилка)", "3", "энкодер EC11 с кнопкой", "Бесконечное вращение + нажатие. Можно «без щелчков» (без фиксации) — будет плавнее", "M"),
 ("Кнопки и крутилка (бока)", "Ручка для энкодера металлическая, рифлёная, Ø12–15 мм", "2", "ручка для энкодера алюминиевая 6мм рифленая", "Под вал 6 мм. Скинь фото своей ручки — подберу точнее", "M"),
 ("Ядро", "Гироскоп + акселерометр LSM6DSO / LSM6DS3 (модуль)", "2", "LSM6DS3 модуль гироскоп акселерометр", "На своей плате будет LSM6DSO. Для макетки подойдёт и MPU-6050", "M"),
 ("Ядро", "Вибромотор монетка 0820 / 1027", "3", "вибромотор монетка 1027 3V", "8–10 мм в диаметре", "M"),
 ("Ядро", "Гнездо 2×20 «мама» 2.54 мм (в него втыкается Pi WH)", "4", "гребенка 2x20 мама 2.54", "Прямое, высота 8.5 мм — стандартная для Pi", "P"),
 ("Ядро", "EEPROM 24C02 (паспорт каждой платы пазла) + 24C32 (HAT EEPROM ядра)", "10+3", "24C02 SOT-23", "По одной на каждую часть пазла — по ним KODY проверяет, что всё вставлено", "P"),
 ("Ядро", "Латунные стойки M2.5 высотой 11 мм и 3 мм + винты", "1 набор", "стойки латунные M2.5 набор", "Зажимают Pi между ядром и задней платой", "M"),
 ("GPS (сзади)", "GPS-модуль ATGM336H с антенной — для макетки", "2", "ATGM336H GPS модуль", "Сим-карта не нужна. Скорость, координаты, время", "M"),
 ("GPS (сзади)", "GPS-модуль u-blox MAX-M10S — для своей платы", "1", "MAX-M10S", "Маленький и чувствительный; на плату", "P"),
 ("Радио + антенны", "Sub-GHz: CC1101 с усилителем — Ebyte E07-433M20S", "2", "E07-433M20S", "Именно M20S — с усилителем, разъём IPEX", "M"),
 ("Радио + антенны", "LoRa: SX1262 — Ebyte E22-900M22S (868 МГц)", "2", "E22-900M22S SX1262", "Именно SX1262, 22 dBm, разъём IPEX", "M"),
 ("Радио + антенны", "2.4 ГГц: NRF24L01+ с усилителем PA+LNA (SMD-модуль, разъём IPEX)", "2", "NRF24L01 PA LNA SMD IPEX", "Плоский SMD-модуль с IPEX, а не большой с SMA — он не влезет", "M"),
 ("Радио + антенны", "Антенна SMA 433 МГц (резиновая, складная)", "1", "антенна SMA 433 МГц складная", "Разъём SMA-male (штырь внутри)", "M"),
 ("Радио + антенны", "Антенна SMA 868 МГц (резиновая)", "1", "антенна SMA 868 МГц", "Разъём SMA-male", "M"),
 ("Радио + антенны", "Антенна SMA 2.4 ГГц (резиновая)", "1", "антенна SMA 2.4 ГГц", "Разъём SMA-male", "M"),
 ("Радио + антенны", "Заглушки-нагрузки SMA 50 Ом («заклёпки» вместо антенн)", "3", "нагрузка SMA 50 Ом заглушка терминатор", "Именно нагрузка 50 Ом (terminator, 1–2 Вт), а не пылезащитный колпачок: спасёт усилитель, если передать без антенны", "M"),
 ("Радио + антенны", "Гнёзда SMA female на плату (в торец платы) + пигтейлы IPEX → SMA", "по 5", "SMA female на плату торцевой", "Edge-mount", "P"),
 ("NFC / RFID (сзади)", "Плата NFC на ST25R3916: X-NUCLEO-NFC08A1 (или NFC06A1)", "1", "X-NUCLEO-NFC08A1", "Готовая плата с тем же чипом, что во Flipper — для отладки до нашей платы", "M"),
 ("NFC / RFID (сзади)", "Микросхема ST25R3916 / ST25R3916B (для своей платы)", "2", "ST25R3916", "QFN32. На маркетплейсах редкость — проще заказать монтаж на JLCPCB, они её поставят", "P"),
 ("NFC / RFID (сзади)", "Тестовые метки: NFC NTAG215, брелоки T5577 и EM4100", "набор", "брелок T5577 перезаписываемый 125 кГц", "Чтобы было на чём проверять чтение/запись/эмуляцию", "M"),
 ("ИК (сверху)", "ИК-приёмник TSOP38238 (38 кГц)", "3", "TSOP38238", "", "M"),
 ("ИК (сверху)", "ИК-светодиоды 940 нм (3 мм или SMD)", "10", "ИК светодиод 940нм 3мм", "", "M"),
 ("USB", "Гнёзда USB-C 16 pin на плату", "10", "USB Type-C 16pin гнездо на плату SMD", "Два на девайс: снизу — быстрая зарядка, сверху — данные", "P"),
 ("Питание (снизу)", "Аккумулятор Li-Po ≈ 7 × 20 × 50 мм (≈ 1000 мА·ч)", "2", "Li-Po 702050 3.7V", "Типоразмер 702050 (толщина 7 мм). С платой защиты и проводами, лучше с NTC", "M"),
 ("Питание (снизу)", "Модуль BQ25895 (быстрая зарядка, I2C) — для макетки", "1", "BQ25895 модуль", "", "M"),
 ("Питание (снизу)", "Защита аккумулятора: DW01A + сборка ключей FS8205A", "5+5", "DW01A FS8205A", "Защита от перезаряда, переразряда и КЗ", "P"),
 ("Питание (снизу)", "Слот microSD push-push на плату", "5", "слот microSD push push SMD", "", "P"),
 ("Питание (снизу)", "Мини-выключатель (slide) угловой", "5", "микро переключатель движковый угловой SMD", "", "P"),
 ("Сборка пазла", "Гнездо 2×20 «мама» низкопрофильное (GPIO наружу)", "4", "гребенка 2x20 мама низкая", "Чем ниже, тем меньше торчит сверху", "P"),
 ("Сборка пазла", "Разъёмы плата-плата 1.27 мм (штырь + гнездо, угловые)", "по 10", "гребенка 1.27 угловая штырь гнездо", "Ими соединяются платы пазла между собой", "P"),
 ("Макетка и проекты", "Макетная плата + провода Dupont", "1", "макетная плата 830 провода dupont набор", "", "M"),
 ("Макетка и проекты", "Набор светодиодов и резисторов (проект «Лампочка»)", "1", "набор светодиодов и резисторов", "", "M"),
 ("Инструмент", "Паяльная станция + флюс-гель + припой + оплётка", "1", "паяльная станция T12", "Если ещё нет", "M"),
 ("Инструмент", "Мультиметр", "1", "мультиметр", "Если ещё нет", "M"),
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
        "(v4: Pi в ядре, пазл по краям, крутилка, GPS, гироскоп), см. `docs/concept.md`.",
        "",
        "**Этап:** 🟢 — нужно сейчас для макетки, 🔵 — понадобится при сборке своей платы.",
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
var KEY="kody-shop-v4", st={}; try{ st=JSON.parse(localStorage.getItem(KEY)||"{}"); }catch(e){}
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
           '<button data-f="M" aria-pressed="false">Сейчас, для макетки</button>'
           '<button data-f="P" aria-pressed="false">Для своей платы</button><span class="prog" id="prog"></span></div>']
    section = None
    for i, (sec, item, qty, query, check, stage) in enumerate(ITEMS):
        if sec != section:
            if section is not None:
                out.append("</section>")
            section = sec
            out.append(f"<section><h2>{e(sec)}</h2>")
        q = quote_plus(query)
        shops = "".join(f'<a href="{e(url.format(q))}" target="_blank" rel="noopener">{e(name)}</a>' for name, url in SHOPS)
        st_cls, st_txt = ("now", "СЕЙЧАС") if stage == "M" else ("later", "ДЛЯ ПЛАТЫ")
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
