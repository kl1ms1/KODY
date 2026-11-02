#!/usr/bin/python3
"""KODY v9 — генератор двух плат (этап 1: механика и разъёмы) для KiCad 7 → импорт в EasyEDA Pro.

Создаёт:
  front.kicad_pcb — передняя плата: гнездо Pi (насквозь), GPIO наружу (разведено 1:1),
                    крутилка, 3 кнопки, ползунок питания, USB-C, 4× SMA, ИК-порт,
                    индикатор заряда (4 светодиода), разъёмы экрана и HDMI, разъём к задней плате,
                    площадки аккумулятора; зоны модулей (рация, LoRa, …) — разметкой.
  back.kicad_pcb  — задняя плата: ответный разъём, pogo-площадки к Pi, катушка NFC дорожками,
                    площадки большой катушки 125 кГц, череп + KODY на шелкографии.

Запуск: /usr/bin/python3 hardware/pcb/generate_boards.py [--drc]
Нужен KiCad 7: sudo apt install kicad kicad-footprints
"""

import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")

W, H, R = 51.6, 99.6, 3.0          # плата, мм
PX, PY = 3.5, 4.0                 # центр Pi в координатах модели (x вправо, y вверх, 0 — центр платы)
P = 2.54
TRACK = 0.2

PIN_NETS = {
    1: "+3V3", 2: "+5V", 3: "GPIO2_SDA1", 4: "+5V", 5: "GPIO3_SCL1", 6: "GND", 7: "GPIO4", 8: "GPIO14_TXD",
    9: "GND", 10: "GPIO15_RXD", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23",
    17: "+3V3", 18: "GPIO24", 19: "GPIO10_MOSI", 20: "GND", 21: "GPIO9_MISO", 22: "GPIO25", 23: "GPIO11_SCLK",
    24: "GPIO8_CE0", 25: "GND", 26: "GPIO7_CE1", 27: "ID_SD", 28: "ID_SC", 29: "GPIO5", 30: "GND", 31: "GPIO6",
    32: "GPIO12", 33: "GPIO13", 34: "GND", 35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20", 39: "GND",
    40: "GPIO21",
}
B2B_NETS = ["+5V", "+5V", "GND", "GND", "USB1_DP", "USB1_DN", "GND", "GND", "USB2_DP", "USB2_DN", "GND", "+3V3",
            "NFC_SCK", "NFC_MOSI", "NFC_MISO", "NFC_CS", "NFC_IRQ", "GND", "RF125_TX", "RF125_RX", "RF125_MOD", "GND",
            "I2C_SDA", "I2C_SCL"]


def mm(v): return pcbnew.FromMM(v)
def vec(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def K(x, y): return (x + W / 2, H / 2 - y)          # модель → KiCad (y вниз, начало в левом верхнем углу)
def xy(p): return (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))


def load(lib, name):
    fp = pcbnew.FootprintLoad(os.path.join(LIB, lib + ".pretty"), name)
    if fp is None:
        sys.exit(f"нет посадочного места {lib}:{name}")
    return fp


def pads(fp):
    out = {}
    for p in fp.Pads():
        out.setdefault(p.GetNumber(), []).append(xy(p.GetPosition()))
    return out


def bbox(fp, layer):
    xs, ys = [], []
    for d in fp.GraphicalItems():
        if d.GetLayer() == layer:
            b = d.GetBoundingBox()
            xs += [pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetRight())]
            ys += [pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetBottom())]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def pad_bbox(fp):
    pts = [q for v in pads(fp).values() for q in v]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def body_dir(fp):
    x0, y0, x1, y1 = bbox(fp, pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
    a, b, c, d = pad_bbox(fp)
    ext = {"+x": x1 - c, "-x": a - x0, "+y": y1 - d, "-y": b - y0}
    return max(ext, key=ext.get)


def orient(board, fp, back, ok):
    board.Add(fp)
    if back:
        fp.Flip(fp.GetPosition(), False)
    for flip_lr in (False, True):
        for _ in range(4):
            if ok(fp):
                return fp
            fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 90)
        if back:
            break
        fp.Flip(fp.GetPosition(), True)
        fp.Flip(fp.GetPosition(), True)
    sys.exit(f"не сориентировать {fp.GetFPID().GetLibItemName()}")


def header_ok(fp, pin1, d2, d3):
    pm = pads(fp)
    p1, p2, p3 = pm["1"][0], pm["2"][0], pm["3"][0]
    if abs(p2[0] - p1[0] - d2[0]) > .01 or abs(p2[1] - p1[1] - d2[1]) > .01:
        return False
    if abs(p3[0] - p1[0] - d3[0]) > .01 or abs(p3[1] - p1[1] - d3[1]) > .01:
        return False
    fp.Move(vec(pin1[0] - p1[0], pin1[1] - p1[1]))
    return True


def edge_part(board, lib, name, ref, value, back, direction, along, by="pads", margin=0.5, overhang=0.0):
    """Деталь у края: «рабочая» сторона смотрит в direction (+x вправо, +y вниз в KiCad)."""
    fp = orient(board, load(lib, name), back, lambda f: body_dir(f) == direction)
    fp.SetReference(ref); fp.SetValue(value)
    layer = pcbnew.B_Fab if back else pcbnew.F_Fab
    x0, y0, x1, y1 = bbox(fp, layer) if by == "fab" else pad_bbox(fp)
    fx0, fy0, fx1, fy1 = bbox(fp, layer)
    if direction in ("+x", "-x"):
        fp.Move(vec(0, along - (fy0 + fy1) / 2))
    else:
        fp.Move(vec(along - (fx0 + fx1) / 2, 0))
    x0, y0, x1, y1 = bbox(fp, layer) if by == "fab" else pad_bbox(fp)
    target = {"+x": W, "-x": 0, "+y": H, "-y": 0}[direction]
    if by == "fab":
        d = {"+x": target + overhang - x1, "-x": target - overhang - x0, "+y": target + overhang - y1, "-y": target - overhang - y0}[direction]
    else:
        d = {"+x": target - margin - x1, "-x": target + margin - x0, "+y": target - margin - y1, "-y": target + margin - y0}[direction]
    fp.Move(vec(d, 0) if direction in ("+x", "-x") else vec(0, d))
    return fp


def at(board, lib, name, ref, value, back, x, y, rot=0):
    fp = load(lib, name); board.Add(fp)
    fp.SetPosition(vec(x, y))
    if back:
        fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(rot); fp.SetReference(ref); fp.SetValue(value)
    return fp


def shape(board, kind, layer, a, b=None, width=0.15, mid=None, fill=False, pts=None):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(kind); s.SetLayer(layer); s.SetWidth(mm(width))
    if kind == pcbnew.SHAPE_T_ARC:
        s.SetArcGeometry(vec(*a), vec(*mid), vec(*b))
    elif kind == pcbnew.SHAPE_T_POLY:
        s.SetPolyPoints([vec(*p) for p in pts])
    else:
        s.SetStart(vec(*a)); s.SetEnd(vec(*b))
    if fill:
        s.SetFilled(True)
    board.Add(s); return s


def rect(board, layer, cx, cy, w, h, width=0.12):
    shape(board, pcbnew.SHAPE_T_RECT, layer, (cx - w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), width)


def text(board, layer, x, y, t, size=1.0, mirror=False, thick=None):
    o = pcbnew.PCB_TEXT(board); o.SetText(t); o.SetLayer(layer); o.SetPosition(vec(x, y))
    o.SetTextSize(vec(size, size)); o.SetTextThickness(mm(thick or size * 0.15))
    if mirror:
        o.SetMirrored(True)
    board.Add(o)


def outline(board):
    L = pcbnew.Edge_Cuts; r = R; k = r * (1 - 0.70710678)
    for a, b in [((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r))]:
        shape(board, pcbnew.SHAPE_T_SEGMENT, L, a, b, 0.1)
    for a, m, b in [((0, r), (k, k), (r, 0)), ((W - r, 0), (W - k, k), (W, r)), ((W, H - r), (W - k, H - k), (W - r, H)), ((r, H), (k, H - k), (0, H - r))]:
        shape(board, pcbnew.SHAPE_T_ARC, L, a, b, 0.1, mid=m)


def track(board, net, layer, pts, width=TRACK):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board); t.SetStart(vec(*a)); t.SetEnd(vec(*b)); t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(net); board.Add(t)


def via(board, net, p):
    v = pcbnew.PCB_VIA(board); v.SetPosition(vec(*p)); v.SetDrill(mm(0.3)); v.SetWidth(mm(0.6)); v.SetNet(net); board.Add(v)


def nets_for(board, names):
    out = {}
    for n in sorted(set(names)):
        ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); out[n] = ni
    return out


def holes(board):
    for i, (hx, hy) in enumerate([(-11.5, -29), (11.5, -29), (-11.5, 29), (11.5, 29)], 1):
        at(board, "MountingHole", "MountingHole_2.7mm_M2.5", f"H{i}", "Pi M2.5", False, *K(PX + hx, PY + hy))
    for i, (hx, hy) in enumerate([(-22.8, -46.8), (22.8, -46.8), (-22.8, 46.8), (22.8, 46.8)], 5):
        at(board, "MountingHole", "MountingHole_2.2mm_M2", f"H{i}", "корпус M2", False, *K(hx, hy))


B2B_ORIGIN = (-12.0, -46.5)     # центр разъёма в координатах модели


def _rel(fp, num):
    o = xy(fp.GetPosition()); p = pads(fp)[num][0]
    return (p[0] - o[0], p[1] - o[1])


def b2b(board, back, nets):
    """Разъём плата-плата 2×12 1.27 мм (SMD) внизу слева, вне Pi.
    Гнездо — на задней плате сверху, штырь — на передней снизу; центры совпадают,
    контакт 1 штыря попадает в контакт 1 гнезда (проверяется по сторонам контактов 1 и 2)."""
    tmp = pcbnew.BOARD(); ref = load("Connector_PinSocket_1.27mm", "PinSocket_2x12_P1.27mm_Vertical_SMD"); tmp.Add(ref)
    ref.SetOrientationDegrees(90)
    want1, want2 = _rel(ref, "1"), _rel(ref, "2")
    sgn = lambda v: (round(v[0] / max(abs(v[0]), 1e-6)) if abs(v[0]) > .3 else 0, round(v[1] / max(abs(v[1]), 1e-6)) if abs(v[1]) > .3 else 0)
    name = ("Connector_PinSocket_1.27mm", "PinSocket_2x12_P1.27mm_Vertical_SMD") if not back else ("Connector_PinHeader_1.27mm", "PinHeader_2x12_P1.27mm_Vertical_SMD")
    fp = load(*name); board.Add(fp); fp.SetPosition(vec(*K(*B2B_ORIGIN)))
    if back:
        fp.Flip(fp.GetPosition(), True)
    for _ in range(4):
        if sgn(_rel(fp, "1")) == sgn(want1) and sgn(_rel(fp, "2")) == sgn(want2):
            break
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 90)
    else:
        sys.exit("B2B: не совпали контакты")
    fp.SetReference("J20"); fp.SetValue("B2B 2x12 1.27 SMD (к другой плате)")
    for p in fp.Pads():
        p.SetNet(nets[B2B_NETS[int(p.GetNumber()) - 1]])
    return fp


def fill_and_save(board, path, drc):
    pcbnew.SaveBoard(path, board)
    board = pcbnew.LoadBoard(path)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)
    if drc:
        pcbnew.WriteDRCReport(board, path.replace(".kicad_pcb", "-drc.rpt"), pcbnew.EDA_UNITS_MILLIMETRES, True)
    print("OK:", path)


def gnd_zone(board, net, layer):
    z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(net); z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline(); o.NewOutline()
    for x, y in [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]:
        o.Append(mm(x), mm(y))
    board.Add(z)


LAYOUT = []

# Модули и крупные детали, которые ставятся «целиком»: (подпись, x, y, ширина, высота, сторона)
# Радио — у своих антенн наверху; рация и пульты 433 — внизу (большой модуль), к антенне — кабель с защёлками.
FRONT_ZONES = {
    "pi":      ("Raspberry Pi Zero 2 WH", PX, PY, 30, 65, "bottom"),
    "lora":    ("LoRa E22-900M22S", 2, 37, 14, 20, "bottom"),
    "gps":     ("GPS MAX-M10S", -17, 44, 10, 10, "bottom"),
    "nrf":     ("NRF24 PA/LNA", 15, 44.5, 10, 10, "bottom"),
    "radio":   ("РАЦИЯ SA818-U", 16, -40, 18, 18, "bottom"),
    "cc1101":  ("ПУЛЬТЫ CC1101", -12, -37, 12, 11, "bottom"),
    "battery": ("АККУМУЛЯТОР 8.5x24x70", 8.5, 0, 24, 70, "top"),
    "speaker": ("ДИНАМИК 1511", -10, -44, 15, 11, "top"),
}


def export_footprints(board, name):
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H"):
            continue
        bb = fp.GetBoundingBox(False, False)
        LAYOUT.append(dict(board=name, key=ref, name=fp.GetValue(), side="bottom" if fp.IsFlipped() else "top",
                           x=pcbnew.ToMM(bb.GetLeft()), y=pcbnew.ToMM(bb.GetTop()), w=pcbnew.ToMM(bb.GetWidth()), h=pcbnew.ToMM(bb.GetHeight())))


# =============================================================== FRONT
def front(drc):
    b = pcbnew.BOARD(); b.SetCopperLayerCount(2); b.GetDesignSettings().SetCopperLayerCount(2)
    outline(b); holes(b)
    N = nets_for(b, list(PIN_NETS.values()) + B2B_NETS)
    F, Bc, D, C = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.Dwgs_User, pcbnew.Cmts_User

    # J1 — гнездо, через которое проходит гребёнка Pi. Номера пинов как у Pi, вид сверху —
    # это зеркальная раскладка, поэтому посадочное место «перевёрнуто» (контакты сквозные, на работу не влияет).
    pin1 = K(PX - 10.23, PY - 24.13)
    j1 = orient(b, load("Connector_PinSocket_2.54mm", "PinSocket_2x20_P2.54mm_Vertical"), True,
                lambda f: header_ok(f, pin1, (-P, 0), (0, -P)))
    j1.SetReference("J1"); j1.SetValue("Pi socket 2x20 bottom-entry")
    for p in j1.Pads():
        p.SetNet(N[PIN_NETS[int(p.GetNumber())]])
    a = pads(j1)
    ys = sorted({round(v[0][1], 3) for v in a.values()})
    # J2 — GPIO наружу, угловое гнездо на левом краю; ряды точно напротив J1
    j2 = orient(b, load("Connector_PinSocket_2.54mm", "PinSocket_2x20_P2.54mm_Horizontal"), False, lambda f: body_dir(f) == "-x")
    j2.SetReference("J2"); j2.SetValue("GPIO 2x20 out (left edge)")
    c = pads(j2); j2.Move(vec(0, ys[0] - min(v[0][1] for v in c.values())))
    j2.Move(vec(0.0 - bbox(j2, pcbnew.F_Fab)[0], 0))
    c = pads(j2)
    x2cols = sorted({round(v[0][0], 3) for v in c.values()})          # [внешний, внутренний]
    x1odd = a["1"][0][0]
    j2_by_pos = {(round(v[0][0], 3), round(v[0][1], 3)): k for k, v in c.items()}
    pairs = {}
    for n in range(1, 41):
        xa, ya = a[str(n)][0]
        col = x2cols[1] if abs(xa - x1odd) < .01 else x2cols[0]
        k = j2_by_pos[(col, round(ya, 3))]
        pairs[n] = (xa, ya, col, ya)
        for pd in j2.Pads():
            if pd.GetNumber() == k:
                pd.SetNet(N[PIN_NETS[n]])
    for n, (xa, ya, xb, yb) in pairs.items():
        if n % 2:   # нечётные (внутренний ряд) — верхний слой, канал над строкой
            track(b, N[PIN_NETS[n]], F, [(xa, ya), (xa, ya - P / 2), (xb, yb - P / 2), (xb, yb)])
        else:       # чётные — нижний слой, канал под строкой
            track(b, N[PIN_NETS[n]], Bc, [(xa, ya), (xa, ya + P / 2), (xb, yb + P / 2), (xb, yb)])
    pin1_y = a["1"][0][1]
    text(b, pcbnew.F_SilkS, 1.2, pin1_y + 2.4, "1", 1.0)
    (x2, y2), (x4, y4) = a["2"][0], a["4"][0]
    track(b, N["+5V"], Bc, [(x2, y2), (x4, y4)])
    (x1, y1), (x17, y17) = a["1"][0], a["17"][0]
    track(b, N["+3V3"], F, [(x1, y1), (x1 + 1.6, y1), (x17 + 1.6, y17), (x17, y17)])

    b2b(b, True, N)

    # правый бок, сверху вниз: крутилка, 3 кнопки, ползунок питания
    edge_part(b, "Rotary_Encoder", "RotaryEncoder_Bourns_Horizontal_PEC12R-2x17F-Sxxxx", "ENC1", "EC11/PEC12R horizontal + push", False, "+x", K(0, 32)[1], margin=1.2)
    for i, y in enumerate((19, 8.5, -2), 1):
        edge_part(b, "Button_Switch_THT", "SW_Tactile_SPST_Angled_PTS645Vx31-2LFS", f"SW{i}", "Кнопка 6x6 угловая", False, "+x", K(0, y)[1], margin=1.2)
    edge_part(b, "Button_Switch_THT", "SW_Slide_SPDT_Angled_CK_OS102011MA1Q", "SW4", "Питание: ползунок SS12D07", False, "+x", K(0, -30)[1], margin=1.2)
    # низ: один USB-C, индикатор заряда
    edge_part(b, "Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12", "J3", "USB-C (данные + PD)", False, "+y", K(2, 0)[0], by="fab", overhang=0.6)
    for i, x in enumerate((11, 14, 17, 20), 1):
        at(b, "LED_SMD", "LED_0603_1608Metric", f"D{i}", f"Заряд {i*25}%", False, *K(x, -38))
    # верх: 4× SMA посередине толщины
    for i, x in enumerate((-16.5, -5.5, 5.5, 16.5), 1):
        edge_part(b, "Connector_Coaxial", "SMA_Amphenol_132289_EdgeMount", f"J{3+i}", ["SMA GPS", "SMA LoRa", "SMA Рация 433", "SMA 2.4 ГГц"][i - 1], False, "-y", K(x, 0)[0], margin=0.0)
    # ИК-порт слева под GPIO: 2 узких + 2 широких светодиода, 2 приёмника
    for i, y in enumerate((-24.2, -30.6, -37.0, -43.4), 1):
        edge_part(b, "LED_THT", "LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm", f"D{4+i}", ["VSLY5940", "TSAL6400", "TSAL6400", "VSLY5940"][i - 1], False, "-x", K(0, y)[1], margin=0.8)
    at(b, "OptoDevice", "Vishay_MINIMOLD-3Pin", "U30", "TSOP38238", False, *K(-21.5, 31.0), 90)
    at(b, "OptoDevice", "Vishay_MINIMOLD-3Pin", "U31", "TSMP58000", False, *K(-21.5, 38.0), 90)
    # экран и HDMI: разъёмы FPC (точная модель — по выбранному экрану)
    at(b, "Connector_FFC-FPC", "Hirose_FH12-30S-0.5SH_1x30-1MP_P0.50mm_Horizontal", "J10", "Экран (FPC, уточнить)", False, *K(-2, 41.0), 180)
    at(b, "Connector_FFC-FPC", "Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal", "J11", "HDMI-шлейф от Pi (FPC)", True, *K(PX + 6, PY - 20.1), 90)
    # аккумулятор: 3 площадки под лепестки
    for i, x in enumerate((0, 5, 10), 1):
        at(b, "TestPoint", "TestPoint_Pad_3.0x3.0mm", f"BT{i}", ["BAT+", "BAT-", "NTC"][i - 1], False, *K(x, 37.5))

    # разметка: зоны модулей и крупных деталей
    FS, BS = pcbnew.F_SilkS, pcbnew.B_SilkS
    for key, (label, cx, cy, w, h, side) in FRONT_ZONES.items():
        layer = FS if side == "top" else BS
        kx, ky = K(cx, cy); rect(b, layer, kx, ky, w, h, 0.15); text(b, layer, kx, ky, label, 1.0, mirror=(side == "bottom"))
        LAYOUT.append(dict(board="front", key=key, name=label, side=side, x=kx - w / 2, y=ky - h / 2, w=w, h=h))
    for ref, lab, dx, dy in [("ENC1", "КРУТИЛКА", -6, 0), ("SW1", "КН1", -4, 0), ("SW2", "КН2", -4, 0), ("SW3", "КН3", -4, 0),
                             ("SW4", "ПИТАНИЕ", -6, 0), ("J3", "USB-C", 0, -6), ("J2", "GPIO", 0, 0), ("J1", "СЮДА Pi", 0, 0)]:
        fp = b.FindFootprintByReference(ref); bb = fp.GetBoundingBox(False, False)
        fx, fy = pcbnew.ToMM(bb.GetCenter().x), pcbnew.ToMM(bb.GetCenter().y)
        if ref in ("ENC1", "SW1", "SW2", "SW3", "SW4"):
            fx = pcbnew.ToMM(bb.GetLeft())
        text(b, FS, fx + dx, fy + dy, lab, 1.0)
    text(b, pcbnew.F_SilkS, *K(15.5, -35.5), "ЗАРЯД", 0.9)
    text(b, pcbnew.F_SilkS, *K(-2, 40), "KODY v9 FRONT", 1.0)
    text(b, pcbnew.F_SilkS, *K(-19, 31.5), "GPIO 3.3V", 0.9)
    gnd_zone(b, N["GND"], Bc)
    export_footprints(b, "front")
    fill_and_save(b, os.path.join(HERE, "front.kicad_pcb"), drc)


# =============================================================== BACK
def back(drc):
    b = pcbnew.BOARD(); b.SetCopperLayerCount(2); b.GetDesignSettings().SetCopperLayerCount(2)
    outline(b); holes(b)
    N = nets_for(b, B2B_NETS + ["NFC_ANT1", "NFC_ANT2", "COIL125_A", "COIL125_B", "PI_5V", "PI_USB_DP", "PI_USB_DN"])
    S, D, C = pcbnew.B_SilkS, pcbnew.Dwgs_User, pcbnew.Cmts_User
    b2b(b, False, N)
    # pogo-площадки к Pi (точные места снимаем с платы Pi штангенциркулем)
    for i, (nm, dy) in enumerate([("PI_5V", 0), ("GND", 3.0), ("PI_USB_DP", 6.0), ("PI_USB_DN", 9.0)], 1):
        fp = at(b, "TestPoint", "TestPoint_Pad_D1.5mm", f"TP{i}", nm, False, *K(PX + 10, PY + 10 + dy))
        for p in fp.Pads():
            p.SetNet(N[nm])
    rect(b, C, *K(PX + 10, PY + 13.75), 4, 11, 0.1); text(b, C, *K(PX + 16, PY + 13.75), "POGO -> Pi PP1/PP6/PP22/PP23 (уточнить)", 0.8)
    # катушка NFC 13.56 МГц: 4 витка дорожками на нижнем слое, по центру нижней половины
    cx, cy = K(0.25, -17); w0, h0, step = 40.5, 54.0, 1.1
    pts = []
    for t in range(4):
        x0, y0, x1, y1 = cx - w0 / 2 + t * step, cy - h0 / 2 + t * step, cx + w0 / 2 - t * step, cy + h0 / 2 - t * step
        pts += [(x0 + (step if t else 0), y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + step)]
    track(b, N["NFC_ANT1"], pcbnew.B_Cu, pts, 0.5)
    start, end = pts[0], pts[-1]
    via(b, N["NFC_ANT1"], start); via(b, N["NFC_ANT1"], end)
    t1 = at(b, "TestPoint", "TestPoint_Pad_D1.5mm", "TP10", "NFC ANT1", False, start[0] + 3, start[1] - 3)
    t2 = at(b, "TestPoint", "TestPoint_Pad_D1.5mm", "TP11", "NFC ANT2", False, end[0] + 3, end[1] - 6)
    for t, n in ((t1, "NFC_ANT1"), (t2, "NFC_ANT1")):
        for p in t.Pads():
            p.SetNet(N[n])
    track(b, N["NFC_ANT1"], pcbnew.F_Cu, [start, (start[0] + 3, start[1] - 3)])
    track(b, N["NFC_ANT1"], pcbnew.F_Cu, [end, (end[0] + 3, end[1] - 6)])
    text(b, C, cx, cy + h0 / 2 + 2, "Катушка NFC: согласование ST25R3916 — по AN ST (NanoVNA)", 0.8)
    # большая катушка 125 кГц — намотанная, по периметру всей задней панели; 2 площадки под её выводы
    rect(b, D, W / 2, H / 2, 46, 92, 0.3); text(b, D, W / 2, 4.5, "Катушка 125 кГц по периметру (намотанная, ~700 мкГн)", 0.9)
    for i, (x, y) in enumerate([(W - 6, 8), (W - 6, 11)], 1):
        fp = at(b, "TestPoint", "TestPoint_THTPad_D1.5mm_Drill0.7mm", f"TP{20+i}", f"COIL125_{'AB'[i-1]}", False, x, y)
        for p in fp.Pads():
            p.SetNet(N[f"COIL125_{'AB'[i-1]}"])
    # логотип: череп + KODY на нижней шелкографии (вид снаружи)
    sx, sy = K(0, 28)
    shape(b, pcbnew.SHAPE_T_CIRCLE, S, (sx, sy), (sx + 9, sy), 0.6)
    shape(b, pcbnew.SHAPE_T_POLY, S, None, width=0.4, fill=True, pts=[(sx - 6, sy + 6), (sx + 6, sy + 6), (sx + 5, sy + 12), (sx - 5, sy + 12)])
    for ex in (-3.5, 3.5):
        shape(b, pcbnew.SHAPE_T_CIRCLE, S, (sx + ex, sy + 1), (sx + ex + 2.4, sy + 1), 0.3, fill=True)
    shape(b, pcbnew.SHAPE_T_POLY, S, None, width=0.3, fill=True, pts=[(sx, sy + 3.6), (sx - 1.2, sy + 6), (sx + 1.2, sy + 6)])
    for tx in (-3, -1, 1, 3):
        shape(b, pcbnew.SHAPE_T_SEGMENT, S, (sx + tx, sy + 8), (sx + tx, sy + 11.5), 0.5)
    for dx in (-1, 1):
        shape(b, pcbnew.SHAPE_T_SEGMENT, S, (sx - 14 * dx, sy - 8), (sx + 14 * dx, sy + 18), 0.8)
    text(b, S, sx, sy + 22, "KODY", 5.0, mirror=True, thick=0.9)
    text(b, S, sx, sy + 27, "SUB-GHZ  LORA  2.4G  GPS  NFC  IR", 1.1, mirror=True)
    text(b, pcbnew.F_SilkS, *K(10, -42), "KODY v9 BACK", 1.0)
    export_footprints(b, "back")
    fill_and_save(b, os.path.join(HERE, "back.kicad_pcb"), drc)


if __name__ == "__main__":
    import json
    drc = "--drc" in sys.argv
    front(drc)
    back(drc)
    with open(os.path.join(HERE, "layout.json"), "w", encoding="utf-8") as f:
        json.dump({"W": W, "H": H, "items": LAYOUT}, f, ensure_ascii=False, indent=1)
    print("OK: layout.json", len(LAYOUT))
