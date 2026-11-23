#!/usr/bin/env python3
"""Draw canfuel's harness as what it physically is: two cables.

    python tools/render-harness.py

Writes canfuel/docs/harness-cables.svg.

    cable 1 - three connectors: the car's 12 V 4-pin, MFD15 plug B, and a
              Micro-Fit onto the converter. It splits at the 4-pin: 12 V and
              ground to the display, the CAN pair on to the converter.
    cable 2 - two connectors: MFD15 plug C and a Micro-Fit onto the
              converter. 5 V (through the fuse), SGND and the display's CAN
              pair.

J1 and J2 are on the same four nets, so the board joins the two cables and is
what carries CAN from the car to the display.

Every connector is drawn from the rear / cable side, the MFD15 manual's
convention and the one pinout.md uses: the view in front of you while pushing
crimps in. The cavity layouts are the ones in harness-pinout.svg.

What is read from the board rather than typed in: the net on each Micro-Fit
circuit, out of J1's and J2's pads in canfuel.kicad_pcb. The script refuses to
draw if J1 and J2 ever stop being in parallel, because the whole two-cable
arrangement rests on it.

What is typed in, and where it comes from:

    plug B / plug C cavities  - MFD15 Gen2 manual Rev 1.0 (via pinout.md)
    the car 4-pin circuits    - car-wiring.md, recorded on the vehicle; its
                                cavity geometry was never recorded, so it is
                                drawn as circuit numbers in a row, nothing more
    wire colours              - harness.md, pinout.md, car-wiring.md
    which wire is on which cable - the owner, 23/11/2026

Plain Python; no pcbnew needed, the pads are read from the board's text.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.join(os.path.dirname(HERE), "canfuel")
PCB = os.path.join(BOARD_DIR, "canfuel.kicad_pcb")
OUT = os.path.join(BOARD_DIR, "docs", "harness-cables.svg")


# --- the board: which net is on which Micro-Fit circuit ---------------------

def footprint_block(text, ref):
    m = re.search(r'\(property "Reference" "%s"' % re.escape(ref), text)
    if not m:
        sys.exit("%s not found in %s" % (ref, PCB))
    start = text.rfind("(footprint ", 0, m.start())
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    sys.exit("unbalanced footprint block for %s" % ref)


def pad_nets(text, ref):
    block = footprint_block(text, ref)
    nets = {}
    for m in re.finditer(r'\(pad "(\d+)"(.*?)\(net "([^"]+)"\)', block, re.S):
        if "(pad " in m.group(2):            # ran past a pad with no net
            continue
        nets[int(m.group(1))] = m.group(3)
    return nets


with open(PCB, encoding="utf-8") as f:
    _pcb = f.read()
J1 = pad_nets(_pcb, "J1")
J2 = pad_nets(_pcb, "J2")
if J1 != J2 or sorted(J1) != [1, 2, 3, 4]:
    sys.exit("J1 %r and J2 %r are not four circuits in parallel - the "
             "two-cable harness depends on it; fix the drawing's premise "
             "first" % (J1, J2))
MF = J1                                       # circuit -> net, both headers

# --- wire colours, as the harness documents name them -----------------------

COL = {
    "red":    ("#d43a3a", None),
    "black":  ("#22262c", None),
    "white":  ("#ffffff", "#22262c"),          # white needs an outline
    "yellow": ("#e3bd1f", None),
    "brown":  ("#8b5a2b", None),
    "grey":   ("#9aa0a6", None),
    "yellow/green": ("#e3bd1f", "#3c9a4a"),    # drawn striped
}
NET_WIRE = {"+5V": "red", "SGND": "black", "CANH": "white", "CANL": "yellow"}
NET_LABEL = {"+5V": "+5V", "SGND": "SGND", "CANH": "CAN H", "CANL": "CAN L"}
for n in MF.values():
    if n not in NET_WIRE:
        sys.exit("unexpected net %r on J1/J2 - update NET_WIRE" % n)

# halo tint per cable, so the two looms can be told apart at a glance
HALO = {1: "#4f8fe0", 2: "#ef8a2f"}

INK, MUTED, RULE, FILL = "#15181d", "#7b8794", "#c7ced6", "#f2f4f7"
W, H = 1240, 1310

out = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=12, fill=INK, weight=None, anchor=None, extra=""):
    a = ' text-anchor="%s"' % anchor if anchor else ""
    w = ' font-weight="%s"' % weight if weight else ""
    out.append('<text x="%g" y="%g" fill="%s" font-size="%g"%s%s%s>%s</text>'
               % (x, y, fill, size, w, a, extra, esc(s)))


def rect(x, y, w, h, fill="none", stroke=MUTED, sw=1.4, rx=4, extra=""):
    out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" '
               'stroke="%s" stroke-width="%g"%s/>' % (x, y, w, h, rx, fill,
                                                     stroke, sw, extra))


def wire(points, colour, cable=None):
    d = "M" + " L".join("%g %g" % p for p in points)
    base, edge = COL[colour]
    if cable:
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="15" '
                   'stroke-opacity="0.22" stroke-linejoin="round" '
                   'stroke-linecap="round"/>' % (d, HALO[cable]))
    if colour == "yellow/green":
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="5" '
                   'stroke-linejoin="round"/>' % (d, base))
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="5" '
                   'stroke-dasharray="6 6"/>' % (d, edge))
        return
    if edge:
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="6.5" '
                   'stroke-linejoin="round"/>' % (d, edge))
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="4" '
                   'stroke-linejoin="round"/>' % (d, base))
    else:
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="5" '
                   'stroke-linejoin="round"/>' % (d, base))


def cell(x, y, w, h, name, signal, colour=None):
    """One cavity. A used one is filled with its wire's colour."""
    if colour:
        base, edge = COL[colour]
        fg = INK if colour in ("white", "yellow") else "#ffffff"
        rect(x, y, w, h, fill=base, stroke=edge or base, sw=1.4, rx=6)
    else:
        fg = MUTED
        rect(x, y, w, h, fill=FILL, stroke=RULE, sw=1, rx=6)
    text(x + 8, y + 19, name, 13, fg, "700")
    text(x + w - 8, y + 19, signal, 11.5, fg, "700", "end")
    if colour:
        text(x + 8, y + h - 9, colour + " wire", 10.5, fg)
    # where a wire lands: the top edge from above, the bottom edge from below
    return {"x": x + w / 2, "top": y, "bot": y + h}


def housing(x, y, w, h, latch):
    rect(x - 9, y - 9, w + 18, h + 18, stroke=MUTED, sw=1.6, rx=9)
    lx = x + w / 2 - 29
    ly = y - 22 if latch == "up" else y + h + 9
    rect(lx, ly, 58, 13, fill="#e9edf1", stroke=MUTED, sw=1.4, rx=3)
    text(x + w / 2, ly - 4 if latch == "up" else ly + 25, "latch", 10.5,
         MUTED, anchor="middle")


def badge(x, y, cable, label):
    rect(x, y, 22 + 7.3 * len(label), 24, fill=HALO[cable], stroke=HALO[cable],
         rx=12)
    text(x + 11, y + 16.5, label, 12, "#ffffff", "700")


# --- page head ---------------------------------------------------------------

out.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d" font-family="DejaVu Sans, Segoe UI, Arial, '
           'sans-serif">' % (W, H, W, H))
rect(0, 0, W, H, fill="#ffffff", stroke="none", sw=0, rx=0)
text(40, 46, "canfuel harness — two cables, five connectors", 21, INK, "700")
text(40, 70, "Cable 1 splits the car's 4-pin between the display and the "
     "converter; cable 2 joins the display's plug C to the converter. "
     "The board's J1 and J2 join the two.", 12.5, MUTED)
text(40, 88, "Every connector is drawn from the rear / cable side, as in "
     "pinout.md — pin the wires exactly as drawn, do not mirror or rotate. "
     "Wires are drawn schematically, not to length.", 12.5, MUTED)
out.append('<line x1="40" y1="102" x2="%d" y2="102" stroke="%s"/>'
           % (W - 40, RULE))

# --- the car's 4-pin -----------------------------------------------------------

FP_X, FP_Y, FP_W, FP_H = 470, 190, 95, 54
CAR = [  # circuit, signal, car-side colour, MFD-side colour (car-wiring.md)
    (1, "GND",   "brown",        "black"),
    (2, "+12 V", "black",        "red"),
    (3, "CAN H", "grey",         "white"),
    (4, "CAN L", "yellow/green", "yellow"),
]
text(FP_X + 2 * FP_W, 128, "Car 4-pin (12 V) — already fitted", 15, INK,
     "700", "middle")
text(FP_X + 2 * FP_W, 145, "car-wiring.md. Circuit numbers only — its cavity "
     "layout was never recorded.", 11.5, MUTED, anchor="middle")
fp = {}
for i, (c, sig, car_col, _mfd) in enumerate(CAR):
    cx = FP_X + FP_W * i + FP_W / 2
    wire([(cx, FP_Y - 26), (cx, FP_Y)], car_col)
    text(cx + 6, FP_Y - 14, car_col, 10.5, MUTED)
    rect(FP_X + FP_W * i + 4, FP_Y, FP_W - 8, FP_H, fill=FILL, stroke=RULE,
         sw=1, rx=6)
    text(FP_X + FP_W * i + 12, FP_Y + 20, str(c), 13, INK, "700")
    text(FP_X + FP_W * (i + 1) - 12, FP_Y + 20, sig, 11.5, INK, "700", "end")
    fp[c] = cx
rect(FP_X - 6, FP_Y - 6, 4 * FP_W + 12, FP_H + 12, stroke=MUTED, sw=1.6, rx=9)
text(FP_X - 18, FP_Y - 14, "car side ↑", 11, MUTED, anchor="end")
text(FP_X - 18, FP_Y + 2, "(not part of the loom)", 10.5, MUTED, anchor="end")
text(FP_X - 18, FP_Y + FP_H + 2, "loom side ↓", 11, MUTED, anchor="end")
text(FP_X + 4 * FP_W + 18, FP_Y + 24, "⚠ black is +12 V on the car side", 11,
     "#b3261e", "700")
text(FP_X + 4 * FP_W + 18, FP_Y + 40, "and ground on the loom side.", 11,
     "#b3261e")

# --- MFD15 body: plug B and plug C ---------------------------------------------

rect(40, 330, 598, 430, stroke=RULE, sw=1.4, rx=12,
     extra=' stroke-dasharray="7 5"')
text(624, 352, "MFD15 — rear of the display", 13, MUTED, "700", "end")

# plug B, latch up: B6 B5 B4 / B3 B2 B1
PB_X, PB_Y, PB_W, PB_H = 80, 410, 110, 52
housing(PB_X, PB_Y, 3 * PB_W, 2 * PB_H, "up")
text(PB_X + 3 * PB_W + 26, PB_Y + 18, "Plug B", 15, INK, "700")
text(PB_X + 3 * PB_W + 26, PB_Y + 36, "Molex 43025-0600", 11.5, MUTED)
text(PB_X + 3 * PB_W + 26, PB_Y + 52, "the display's own 12 V.", 11.5, MUTED)
text(PB_X + 3 * PB_W + 26, PB_Y + 68, "Nothing here feeds", 11.5, MUTED)
text(PB_X + 3 * PB_W + 26, PB_Y + 84, "the converter.", 11.5, MUTED)
PLUG_B = [("B6", "GND", "black"), ("B5", "12 V", "red"), ("B4", "USB GND", None),
          ("B3", "USB 5V", None), ("B2", "USB D_P", None),
          ("B1", "USB D_N", None)]
pb = {}
for k, (n, sig, col) in enumerate(PLUG_B):
    r, c = divmod(k, 3)
    pb[n] = cell(PB_X + c * PB_W + 3, PB_Y + r * PB_H + 3, PB_W - 6, PB_H - 6,
                 n, sig, col)

# plug C, latch down (mounted upside down): C1..C6 / C7..C12
PC_X, PC_Y, PC_W, PC_H = 72, 600, 88, 52
housing(PC_X, PC_Y, 6 * PC_W, 2 * PC_H, "down")
text(PC_X, PC_Y - 46, "Plug C", 15, INK, "700")
text(PC_X + 62, PC_Y - 46, "Molex 43025-1200 — upside down on the display, "
     "so pin 1 top left", 11.5, MUTED)
PLUG_C_SIG = {1: "MPP 1", 2: "AIN1", 3: "AIN2", 4: "AIN3", 5: "AIN4",
              6: "5 V", 7: "CAN H", 8: "CAN L", 9: "AIN5", 10: "AIN6",
              11: "MPP 2", 12: "SGND"}
PLUG_C_COL = {6: "red", 7: "white", 8: "yellow", 12: "black"}
pc = {}
for n in range(1, 13):
    r, c = divmod(n - 1, 6)
    pc[n] = cell(PC_X + c * PC_W + 3, PC_Y + r * PC_H + 3, PC_W - 6, PC_H - 6,
                 "C%d" % n, PLUG_C_SIG[n], PLUG_C_COL.get(n))

# --- the two converter plugs (Micro-Fit 43025-0400, latch up: 4 3 / 2 1) -------

MF_W, MF_H = 92, 54
MF1_X, MF2_X, MF_Y = 700, 975, 640


def microfit(x, y, used):
    housing(x, y, 2 * MF_W, 2 * MF_H, "up")
    pos = {4: (0, 0), 3: (1, 0), 2: (0, 1), 1: (1, 1)}
    centres = {}
    for circ, (c, r) in pos.items():
        net = MF[circ]
        col = NET_WIRE[net] if circ in used else None
        sig = NET_LABEL[net] if circ in used else "empty"
        centres[circ] = cell(x + c * MF_W + 3, y + r * MF_H + 3, MF_W - 6,
                             MF_H - 6, str(circ), sig, col)
    return centres


# cable 1 carries only the CAN pair to the converter; 5 V and SGND reach the
# board on cable 2 and appear on J1 through the board itself.
mf1 = microfit(MF1_X, MF_Y, used={3, 4})
mf2 = microfit(MF2_X, MF_Y, used={1, 2, 3, 4})
PL_Y = 905                                # plug captions, under the runs
for x, n, extra in ((MF1_X, 1, "1 and 2 empty"),
                    (MF2_X, 2, "all four circuits")):
    text(x - 6, PL_Y, "Converter plug, cable %d" % n, 14, INK, "700")
    text(x - 6, PL_Y + 17, "Molex 43025-0400 — " + extra, 11.5, MUTED)

# --- cable 1 --------------------------------------------------------------------

bot = FP_Y + FP_H
def land(c, side):
    return (c["x"], c[side])


wire([(fp[1], bot), (fp[1], 290), (pb["B6"]["x"], 290), land(pb["B6"], "top")],
     "black", 1)
wire([(fp[2], bot), (fp[2], 306), (pb["B5"]["x"], 306), land(pb["B5"], "top")],
     "red", 1)
wire([(fp[3], bot), (fp[3], 520), (mf1[3]["x"], 520), land(mf1[3], "top")],
     "white", 1)
wire([(fp[4], bot), (fp[4], 540), (mf1[4]["x"], 540), land(mf1[4], "top")],
     "yellow", 1)
badge(250, 252, 1, "CABLE 1")
text(342, 264, "12 V + ground to the display", 11, MUTED)
text(fp[4] + 14, 420, "CAN pair, twisted,", 11, MUTED)
text(fp[4] + 14, 434, "on to the converter", 11, MUTED)

# --- cable 2 --------------------------------------------------------------------

gx = (MF1_X + 2 * MF_W + MF2_X) / 2       # the gap between the two plugs
wire([land(pc[7], "bot"), (pc[7]["x"], 775), (gx - 10, 775), (gx - 10, 565),
      (mf2[3]["x"], 565), land(mf2[3], "top")], "white", 2)
wire([land(pc[8], "bot"), (pc[8]["x"], 790), (gx + 8, 790), (gx + 8, 585),
      (mf2[4]["x"], 585), land(mf2[4], "top")], "yellow", 2)
wire([land(pc[12], "bot"), (pc[12]["x"], 805), (mf2[2]["x"], 805),
      land(mf2[2], "bot")], "black", 2)
red_y = 825
wire([land(pc[6], "top"), (pc[6]["x"], 582), (624, 582), (624, red_y),
      (mf2[1]["x"], red_y), land(mf2[1], "bot")], "red", 2)
# the fuse, at the converter end of the red wire (harness.md B1)
fx = mf2[1]["x"] - 140
rect(fx, red_y - 11, 64, 22, fill="#ffffff", stroke=INK, sw=1.6, rx=5)
out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
           'stroke-width="1.6"/>' % (fx + 6, red_y, fx + 58, red_y, INK))
text(fx + 32, red_y + 30, "fuse 200 mA T", 11, INK, "700", "middle")
text(fx + 32, red_y + 44, "SIBA 179120.0.2", 10.5, MUTED, anchor="middle")
text(fx + 32, red_y + 57, "in K23411 — harness.md B", 10.5, MUTED,
     anchor="middle")
badge(PC_X, 845, 2, "CABLE 2")
text(PC_X + 92, 861, "5 V and SGND for the converter, and the display's"
     " CAN pair — C7/C8 untouched", 11, MUTED)

# --- the board --------------------------------------------------------------------

BY = 965
rect(MF1_X - 30, BY, (MF2_X + 2 * MF_W + 30) - (MF1_X - 30), 116,
     fill="#eaf5ee", stroke="#2c6b4c", sw=1.5, rx=8)
text(MF1_X - 18, BY + 22, "canfuel board", 13, "#2c6b4c", "700")
for x, j in ((MF1_X, "J1"), (MF2_X, "J2")):
    rect(x + 30, BY + 48, 2 * MF_W - 60, 36, fill="#ffffff", stroke="#2c6b4c",
         sw=1.5, rx=4)
    text(x + MF_W, BY + 71, j, 14, "#2c6b4c", "700", "middle")
    out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
               'stroke-width="1.4" stroke-dasharray="4 4"/>'
               % (x + MF_W, PL_Y + 28, x + MF_W, BY + 46, MUTED))
out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#2c6b4c" '
           'stroke-width="2.5"/>' % (MF1_X + 2 * MF_W - 30, BY + 66,
                                     MF2_X + 30, BY + 66))
text((MF1_X + 2 * MF_W + MF2_X) / 2, BY + 60, "same 4 nets", 11, "#2c6b4c",
     "700", "middle")
text((MF1_X + 2 * MF_W + MF2_X) / 2, BY + 104, "either plug fits either "
     "header — CAN passes through even with U1 pulled", 11, "#2c6b4c",
     anchor="middle")

# --- wire-by-wire tables -------------------------------------------------------------

TY = 1115
out.append('<line x1="40" y1="%d" x2="%d" y2="%d" stroke="%s"/>'
           % (TY - 22, W - 40, TY - 22, RULE))


def table(x, y, cable, title, rows):
    badge(x, y - 18, cable, "CABLE %d" % cable)
    text(x + 96, y, title, 14, INK, "700")
    cols = (x, x + 92, x + 210, x + 340)
    for cx, h in zip(cols, ("WIRE", "FROM", "THROUGH", "TO")):
        text(cx, y + 26, h, 10.5, MUTED, "700", extra=' letter-spacing="0.6"')
    for k, row in enumerate(rows):
        yy = y + 48 + 21 * k
        base, edge = COL[row[0]]
        rect(cols[0], yy - 10, 14, 10, fill=base, stroke=edge or base, sw=1,
             rx=2)
        text(cols[0] + 20, yy, row[0], 12)
        for cx, s in zip(cols[1:], row[1:]):
            text(cx, yy, s, 12)


table(40, TY, 1, "car 4-pin → plug B + converter", [
    ("black",  "4-pin circ. 1", "—",          "plug B6  GND"),
    ("red",    "4-pin circ. 2", "—",          "plug B5  12 V"),
    ("white",  "4-pin circ. 3", "twisted",    "circuit 3  CANH"),
    ("yellow", "4-pin circ. 4", "twisted",    "circuit 4  CANL"),
])
table(650, TY, 2, "plug C → converter", [
    ("red",    "plug C6",  "200 mA T fuse", "circuit 1  +5V"),
    ("black",  "plug C12", "—",             "circuit 2  SGND"),
    ("white",  "plug C7",  "twisted",       "circuit 3  CANH"),
    ("yellow", "plug C8",  "twisted",       "circuit 4  CANL"),
])
text(40, H - 42, "Micro-Fit nets read from J1/J2 in canfuel.kicad_pcb "
     "(they must match; the script refuses otherwise). Plugs B and C: MFD15 "
     "Gen2 manual Rev 1.0, via pinout.md. 4-pin: car-wiring.md.", 10.5, MUTED)
text(40, H - 26, "Generated by tools/render-harness.py — edit the script, "
     "not this file.", 10.5, MUTED)

out.append("</svg>")
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(out) + "\n")
print("wrote", os.path.relpath(OUT, os.path.dirname(HERE)))
