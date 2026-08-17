#!/usr/bin/env python3
"""Draw canfuel's assembly figure: which way round every polarised part goes.

    python tools/render-assembly.py

Writes canfuel/docs/assembly-orientation.svg.

The board's own silkscreen already carries every reference designator, so this
figure is not for finding R3. It is for the one question the silkscreen answers
only obliquely: **which end of a part that can go in backwards faces which way**.
Five parts on this board can, and they are the only ones drawn in colour.

Everything geometric is read out of canfuel.kicad_pcb - outline, silk, pads,
reference positions - so the figure cannot drift from the board. The polarity is
read out of the *netlist* rather than typed in, for the same reason:

    an LED's cathode  is the pad on SGND
    C6's positive end is the pad on +5V
    a DIP's pin 1     is pad "1"

which is the same set of facts check-netlist.py asserts against the schematic.
If the board is ever re-laid-out with a part turned round, this drawing turns it
round too.

What is *not* read off the board is the part side of each pairing - long leg,
stripe, notch. That is industry convention, no datasheet held here states it,
and canfuel/docs/install.md step 5 says so at length. It is repeated in the
callouts because a figure that says "pad 1" and stops is not an instruction.

Needs pcbnew, which ships with KiCad. On Windows the stock interpreter cannot
import it, so the script re-runs itself under KiCad's bundled Python - the same
trick check-placement.py uses.
"""

import math
import os
import subprocess
import sys

try:
    import pcbnew
except ImportError:                                    # pragma: no cover
    if sys.platform == "win32" and not os.environ.get("_CANFUEL_REEXEC"):
        kicad_py = r"C:\Program Files\KiCad\10.0\bin\python.exe"
        if os.path.exists(kicad_py):
            os.environ["_CANFUEL_REEXEC"] = "1"
            sys.exit(subprocess.call([kicad_py, os.path.abspath(__file__)]
                                     + sys.argv[1:]))
    sys.exit("cannot import pcbnew - run this under KiCad's Python")

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.join(os.path.dirname(HERE), "canfuel")
PCB = os.path.join(BOARD_DIR, "canfuel.kicad_pcb")
OUT = os.path.join(BOARD_DIR, "docs", "assembly-orientation.svg")

# --- page ------------------------------------------------------------------

PAD_L = 300                     # callout column, left of the board
PAD_R = 300                     # callout column, right of the board
MARGIN = 26
TOP_Y = 118                     # top view, board origin
S_TOP = 11.4                    # px per mm, top view
S_BOT = 7.6                     # px per mm, bottom view

INK = "#15181d"
DIM = "#7b8794"
RULE = "#d5dbe2"
BOARDFILL = "#e2eade"
BOARDEDGE = "#4d5b52"
SILK = "#8d99a6"
COPPER = "#e0cf9d"
COPPEREDGE = "#b09a58"
POUR = "#f2e8d2"
TRACK = "#e6d8b6"
HOLE = "#ffffff"
REFTX = "#3c4652"

PLUS = "#c0392b"                # positive / anode
MINUS = "#1f4e79"               # negative / cathode
PIN1 = "#6c3d9a"                # pin 1 of a chip
HILITE = "#fdf1ee"

FONT = "DejaVu Sans, Segoe UI, Arial, sans-serif"

out = []


def add(s):
    out.append(s)


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def text(x, y, t, size=13, fill=INK, weight="400", anchor="start",
         family=None, extra=""):
    add(f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}"'
        + (f' font-family="{family}"' if family else "")
        + (" " + extra if extra else "") + f'>{esc(t)}</text>')


mm = lambda v: v / 1e6


class View:
    """A board view: mm -> px, optionally mirrored for the bottom side."""

    def __init__(self, ox, oy, scale, mirror, bbox):
        self.ox, self.oy, self.s, self.mirror = ox, oy, scale, mirror
        self.x0, self.y0, self.x1, self.y1 = bbox

    def px(self, x, y):
        if self.mirror:
            x = self.x0 + self.x1 - x
        return (self.ox + (x - self.x0) * self.s,
                self.oy + (y - self.y0) * self.s)

    def w(self):
        return (self.x1 - self.x0) * self.s

    def h(self):
        return (self.y1 - self.y0) * self.s


# --- geometry off the board -------------------------------------------------

def arc_pts(p1, pm, p2, n=18):
    """Sample a circular arc given three points on it."""
    (x1, y1), (xm, ym), (x2, y2) = p1, pm, p2
    d = 2 * (x1 * (ym - y2) + xm * (y2 - y1) + x2 * (y1 - ym))
    if abs(d) < 1e-12:
        return [p1, p2]
    ux = ((x1 ** 2 + y1 ** 2) * (ym - y2) + (xm ** 2 + ym ** 2) * (y2 - y1)
          + (x2 ** 2 + y2 ** 2) * (y1 - ym)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x2 - xm) + (xm ** 2 + ym ** 2) * (x1 - x2)
          + (x2 ** 2 + y2 ** 2) * (xm - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1 = math.atan2(y1 - uy, x1 - ux)
    am = math.atan2(ym - uy, xm - ux)
    a2 = math.atan2(y2 - uy, x2 - ux)
    tw = (am - a1) % (2 * math.pi)          # sweep the mid point lies on
    full = (a2 - a1) % (2 * math.pi)
    if full < tw:                            # mid is not between: go the other way
        full -= 2 * math.pi
    return [(ux + r * math.cos(a1 + full * i / n),
             uy + r * math.sin(a1 + full * i / n)) for i in range(n + 1)]


def shape_polys(g):
    """A PCB_SHAPE as a list of (closed, [(x_mm, y_mm), ...])."""
    t = g.GetShape()
    p = lambda q: (mm(q.x), mm(q.y))
    if t == pcbnew.SHAPE_T_SEGMENT:
        return [(False, [p(g.GetStart()), p(g.GetEnd())])]
    if t == pcbnew.SHAPE_T_ARC:
        return [(False, arc_pts(p(g.GetStart()), p(g.GetArcMid()),
                                p(g.GetEnd())))]
    if t == pcbnew.SHAPE_T_CIRCLE:
        cx, cy = p(g.GetCenter())
        r = mm(g.GetRadius())
        return [(True, [(cx + r * math.cos(a * math.pi / 18),
                         cy + r * math.sin(a * math.pi / 18))
                        for a in range(36)])]
    if t == pcbnew.SHAPE_T_RECT:
        (ax, ay), (bx, by) = p(g.GetStart()), p(g.GetEnd())
        return [(True, [(ax, ay), (bx, ay), (bx, by), (ax, by)])]
    if t == pcbnew.SHAPE_T_POLY:
        ps = g.GetPolyShape()
        res = []
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            res.append((True, [(mm(o.CPoint(k).x), mm(o.CPoint(k).y))
                               for k in range(o.PointCount())]))
        return res
    return []


def draw_shape(v, g, stroke, width_px=None, opacity=1.0):
    w = width_px if width_px is not None else max(0.8, mm(g.GetWidth()) * v.s)
    for closed, pts in shape_polys(g):
        d = " ".join(("M" if i == 0 else "L") + "%.2f %.2f" % v.px(*q)
                     for i, q in enumerate(pts))
        if closed:
            d += " Z"
        add(f'<path d="{d}" fill="none" stroke="{stroke}" '
            f'stroke-width="{w:.2f}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity="{opacity}"/>')


def draw_pad(v, pad, fill=COPPER, edge=COPPEREDGE):
    cx, cy = v.px(mm(pad.GetPosition().x), mm(pad.GetPosition().y))
    sx = mm(pad.GetSizeX()) * v.s
    sy = mm(pad.GetSizeY()) * v.s
    rot = pad.GetOrientationDegrees()
    if v.mirror:
        rot = -rot
    shape = pad.GetShape()
    g = (f'<g transform="translate({cx:.2f},{cy:.2f}) rotate({-rot:.1f})">')
    if shape == pcbnew.PAD_SHAPE_CIRCLE:
        body = f'<circle r="{sx/2:.2f}" fill="{fill}" stroke="{edge}" stroke-width="0.7"/>'
    elif shape == pcbnew.PAD_SHAPE_OVAL:
        body = (f'<rect x="{-sx/2:.2f}" y="{-sy/2:.2f}" width="{sx:.2f}" '
                f'height="{sy:.2f}" rx="{min(sx,sy)/2:.2f}" fill="{fill}" '
                f'stroke="{edge}" stroke-width="0.7"/>')
    else:                                   # rect, roundrect, trapezoid
        r = 0.0
        if shape == pcbnew.PAD_SHAPE_ROUNDRECT:
            r = mm(pad.GetRoundRectCornerRadius()) * v.s
        body = (f'<rect x="{-sx/2:.2f}" y="{-sy/2:.2f}" width="{sx:.2f}" '
                f'height="{sy:.2f}" rx="{r:.2f}" fill="{fill}" '
                f'stroke="{edge}" stroke-width="0.7"/>')
    add(g + body + "</g>")
    dx = mm(pad.GetDrillSizeX()) * v.s
    if dx > 0:
        dy = mm(pad.GetDrillSizeY()) * v.s
        add(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{dx/2:.2f}" '
            f'ry="{dy/2:.2f}" fill="{HOLE}" stroke="{edge}" stroke-width="0.5"/>')


# --- the board --------------------------------------------------------------

board = pcbnew.LoadBoard(PCB)
bb = board.GetBoardEdgesBoundingBox()
BBOX = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
FPS = {fp.GetReference(): fp for fp in board.GetFootprints()}


def pad_of(ref, num):
    p = FPS[ref].FindPadByNumber(num)
    if p is None:
        sys.exit(f"{ref} has no pad {num}")
    q = p.GetPosition()
    return mm(q.x), mm(q.y)


def pad_on_net(ref, net):
    """The one pad of `ref` that sits on `net`. Errors if it is not exactly one."""
    hits = [p for p in FPS[ref].Pads() if p.GetNetname() == net]
    if len(hits) != 1:
        sys.exit(f"{ref}: {len(hits)} pads on {net}, expected 1")
    q = hits[0].GetPosition()
    return hits[0].GetNumber(), (mm(q.x), mm(q.y))


def other_pad(ref, num):
    for p in FPS[ref].Pads():
        if p.GetNumber() != num:
            q = p.GetPosition()
            return p.GetNumber(), (mm(q.x), mm(q.y))
    sys.exit(f"{ref} has only one pad")


def render_side(v, side):
    """Outline, silk, pads and reference designators for one side."""
    cu = pcbnew.F_Cu if side == "F" else pcbnew.B_Cu
    silk = "F.Silkscreen" if side == "F" else "B.Silkscreen"

    # board outline as a filled path, from the Edge.Cuts segments in order
    segs = [g for g in board.GetDrawings() if g.GetLayerName() == "Edge.Cuts"]
    pts = []
    for g in segs:
        for _, ps in shape_polys(g):
            pts.append(ps)
    # walk the segments into one loop
    loop = list(pts.pop(0))
    while pts:
        for i, ps in enumerate(pts):
            if math.dist(loop[-1], ps[0]) < 1e-6:
                loop += ps[1:]; pts.pop(i); break
            if math.dist(loop[-1], ps[-1]) < 1e-6:
                loop += ps[-2::-1]; pts.pop(i); break
        else:
            loop += pts.pop(0)
    d = " ".join(("M" if i == 0 else "L") + "%.2f %.2f" % v.px(*q)
                 for i, q in enumerate(loop)) + " Z"
    add(f'<path d="{d}" fill="{BOARDFILL}" stroke="{BOARDEDGE}" '
        f'stroke-width="1.6"/>')

    # The SGND pour on this side. It is drawn because it is the nearest copper
    # to most pads on the board - C7's VCAP pad has it 0.2 mm away - so a
    # figure that leaves it out understates every bridge risk there is.
    for z in board.Zones():
        if not z.IsOnLayer(cu):
            continue
        ps = z.GetFilledPolysList(cu)
        d = []
        for i in range(ps.OutlineCount()):
            for ring in [ps.Outline(i)] + [ps.Hole(i, k)
                                           for k in range(ps.HoleCount(i))]:
                pts = [(mm(ring.CPoint(k).x), mm(ring.CPoint(k).y))
                       for k in range(ring.PointCount())]
                d.append(" ".join(("M" if j == 0 else "L") + "%.2f %.2f" % v.px(*q)
                                  for j, q in enumerate(pts)) + " Z")
        if d:
            add(f'<path d="{" ".join(d)}" fill="{POUR}" fill-rule="evenodd" '
                f'stroke="none"/>')

    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" and not t.IsOnLayer(cu):
            continue
        if t.GetClass() == "PCB_VIA":
            continue
        x1, y1 = v.px(mm(t.GetStart().x), mm(t.GetStart().y))
        x2, y2 = v.px(mm(t.GetEnd().x), mm(t.GetEnd().y))
        add(f'<path d="M{x1:.2f} {y1:.2f} L{x2:.2f} {y2:.2f}" stroke="{TRACK}" '
            f'stroke-width="{mm(t.GetWidth())*v.s:.2f}" stroke-linecap="round" '
            f'fill="none"/>')

    for g in board.GetDrawings():
        if g.GetClass() == "PCB_SHAPE" and g.GetLayerName() == silk:
            draw_shape(v, g, SILK)

    for fp in board.GetFootprints():
        on_this_side = (fp.GetLayer() == cu)
        holeonly = fp.GetReference().startswith("H")
        for g in fp.GraphicalItems():
            if g.GetClass() == "PCB_SHAPE" and g.GetLayerName() == silk:
                draw_shape(v, g, SILK)
        for p in fp.Pads():
            if p.IsOnLayer(cu):
                draw_pad(v, p, COPPER if on_this_side or holeonly else "#f0ece2",
                         COPPEREDGE if on_this_side or holeonly else "#cfc7b4")

    # reference designators, drawn where the silk carries them
    for fp in board.GetFootprints():
        ref = fp.Reference()
        if not ref.IsVisible() or ref.GetLayerName() != silk:
            continue
        x, y = v.px(mm(ref.GetPosition().x), mm(ref.GetPosition().y))
        ang = ref.GetTextAngleDegrees() % 360
        if ang > 180:
            ang -= 360
        if v.mirror:
            ang = -ang
        size = mm(ref.GetTextHeight()) * v.s * 1.05
        # The value goes under the designator for the parts a wrong-slot swap
        # is a real hazard on: three resistor values and two ceramic values in
        # two identical bodies. install.md step 5, "right part, wrong slot".
        r = fp.GetReference()
        val = fp.GetValue() if (r[0] in "RC" or r == "Y1") else ""
        if r == "R5":                      # 120 R termination, deliberately absent
            val = ""
        add(f'<g transform="translate({x:.2f},{y:.2f}) rotate({-ang:.1f})">'
            f'<text x="0" y="{size*0.35:.2f}" fill="{REFTX}" font-size="{size:.1f}" '
            f'font-weight="700" text-anchor="middle">{esc(r)}</text>'
            + (f'<text x="0" y="{size*1.35:.2f}" fill="{DIM}" '
               f'font-size="{size*0.78:.1f}" text-anchor="middle">{esc(val)}</text>'
               if val else "")
            + "</g>")

    for g in board.GetDrawings():
        if g.GetClass() == "PCB_TEXT" and g.GetLayerName() == silk:
            x, y = v.px(mm(g.GetPosition().x), mm(g.GetPosition().y))
            size = mm(g.GetTextHeight()) * v.s
            add(f'<text x="{x:.2f}" y="{y + size*0.35:.2f}" fill="{REFTX}" '
                f'font-size="{size:.1f}" font-weight="700" text-anchor="middle">'
                f'{esc(g.GetShownText(True))}</text>')


def badge(v, xy, glyph, colour, r=10.5):
    cx, cy = v.px(*xy)
    add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r+2.2:.1f}" fill="#ffffff" '
        f'opacity="0.85"/>')
    add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.1f}" fill="{colour}"/>')
    add(f'<text x="{cx:.2f}" y="{cy + r*0.36:.2f}" fill="#ffffff" '
        f'font-size="{r*1.5:.1f}" font-weight="700" text-anchor="middle">'
        f'{esc(glyph)}</text>')
    return cx, cy


def leader(x1, y1, x2, y2, colour):
    add(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{colour}" '
        f'stroke-width="1.6" fill="none" stroke-dasharray="5 3"/>')
    add(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="2.6" fill="{colour}"/>')


def callout(x, y, w, ref, title, lines, colour):
    h = 30 + 17 * len(lines)
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="7" '
        f'fill="{HILITE}" stroke="{colour}" stroke-width="1.4"/>')
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="5" height="{h}" rx="2.5" '
        f'fill="{colour}"/>')
    text(x + 16, y + 21, ref, 15, colour, "700")
    text(x + 16 + 11 * len(ref) + 8, y + 21, title, 12.5, DIM, "400")
    for i, ln in enumerate(lines):
        b = "700" if ln.startswith("*") else "400"
        text(x + 16, y + 40 + 17 * i, ln.lstrip("*"), 12.5, INK, b)
    return h


# --- draw -------------------------------------------------------------------

top = View(MARGIN + PAD_L, TOP_Y, S_TOP, False, BBOX)
H_TOP = TOP_Y + top.h()
W = int(2 * MARGIN + PAD_L + PAD_R + top.w())

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="HEIGHT" '
    f'viewBox="0 0 {W} HEIGHT" font-family="{FONT}">')
add(f'<rect width="{W}" height="HEIGHT" fill="#ffffff"/>')

text(MARGIN, 46, "canfuel — which way round the five polarised parts go", 21,
     INK, "700")
text(MARGIN, 70,
     "Outline, silkscreen, pads and reference designators are read out of "
     "canfuel.kicad_pcb; the polarity is read out of the netlist. Everything "
     "not coloured is symmetric — fit it either way.", 12.5, DIM)
text(MARGIN, 90,
     "The board's own silk carries every designator already. This figure "
     "exists for the orientation, which the silk states only as a notch and a "
     "flat.", 12.5, DIM)
add(f'<line x1="{MARGIN}" y1="102" x2="{W-MARGIN}" y2="102" stroke="{RULE}" '
    f'stroke-width="1"/>')

render_side(top, "F")
text(MARGIN + PAD_L + top.w() / 2, TOP_Y - 10,
     "TOP  ·  component side, as it lies with the two connectors nearest you",
     13, INK, "700", "middle")

# --- the five that can go in backwards --------------------------------------
#
# Which pad is which comes from the nets, not from a table here.

led_marks = []
for ref in ("D1", "D2"):
    cath_n, cath = pad_on_net(ref, "SGND")
    _, anode = other_pad(ref, cath_n)
    led_marks.append((ref, cath, anode))

c6_plus_n, c6_plus = pad_on_net("C6", "+5V")
_, c6_minus = other_pad("C6", c6_plus_n)

for ref, cath, anode in led_marks:
    badge(top, cath, "\u2212", MINUS)
    badge(top, anode, "+", PLUS)
badge(top, c6_plus, "+", PLUS, 9)          # C6's two leads are only 2 mm apart
badge(top, c6_minus, "\u2212", MINUS, 9)
for ref in ("U1", "U2"):
    badge(top, pad_of(ref, "1"), "1", PIN1, 11.5)

# J3 pin 1, quietly: not a part that can go in backwards, but the recovery in
# the U1 callout sends you here with a continuity probe.
jx, jy = top.px(*pad_of("J3", "1"))
add(f'<circle cx="{jx:.1f}" cy="{jy:.1f}" r="8.5" fill="none" stroke="{PIN1}" '
    f'stroke-width="1.8"/>')
text(jx, jy + 27, "J3 pin 1", 10.5, PIN1, "700", "middle")

# R5 is not fitted. Cross its pads rather than let it read as a missing part.
for p in FPS["R5"].Pads():
    q = p.GetPosition()
    px, py = top.px(mm(q.x), mm(q.y))
    add(f'<path d="M{px-7:.1f} {py-7:.1f} L{px+7:.1f} {py+7:.1f} '
        f'M{px+7:.1f} {py-7:.1f} L{px-7:.1f} {py+7:.1f}" stroke="{DIM}" '
        f'stroke-width="2" stroke-linecap="round"/>')

# left column: D1, D2, C6
LX = MARGIN
LW = PAD_L - 46
y = TOP_Y + 22
for ref, kind in (("D1", "led"), ("D2", "led"), ("C6", "cap")):
    if kind == "led":
        cath = [m for m in led_marks if m[0] == ref][0][1]
        anchor = cath
        colour = MINUS
        title = "LED — red" if ref == "D1" else "LED — yellow"
        lines = ["*Short leg (\u2212, cathode) outwards,",
                 "*towards the board edge.",
                 "The flat on the plastic rim is on",
                 "the same side, and the silk outline",
                 "carries the same flat. The long leg",
                 "(+) goes to the inner pad, the one",
                 "wired to %s." % ("R3" if ref == "D1" else "R4")]
    else:
        anchor = c6_plus
        colour = PLUS
        title = "10 µF electrolytic"
        lines = ["*Long leg (+) outwards, towards",
                 "*the board edge — the opposite way",
                 "*round to D1 and D2.",
                 "The printed stripe on the can marks",
                 "the negative side and faces inwards.",
                 "Backwards it heats and can vent:",
                 "if you double-check one part, this one."]
    h = callout(LX, y, LW, ref, title, lines, colour)
    ax, ay = top.px(*anchor)
    leader(LX + LW, y + h / 2, ax - 13, ay, colour)
    y += h + 22

# right column: U1, U2
RX = MARGIN + PAD_L + top.w() + 46
RW = PAD_R - 46
y = TOP_Y + 22
for ref, title, extra in (
        ("U1", "PIC18F25K80, DIP-28", "The notch on the silk outline, and the"),
        ("U2", "MCP2562-E/P, DIP-8", "The notch on the silk outline, and the")):
    lines = ["*Pin 1 is the marked corner, and it",
             "*faces the right-hand board edge.",
             extra,
             "notch or dot on the chip, go the",
             "same way. Both sit in sockets:",
             "solder the socket only after you",
             "have photographed or marked the",
             "silk notch it is about to cover."]
    if ref == "U1":
        lines += ["Recovery: U1 pin 1 rings out to",
                  "J3 pin 1 (~MCLR)."]
    else:
        lines += ["Recovery: U2 pin 2 rings out to",
                  "SGND, pin 3 to +5 V."]
    h = callout(RX, y, RW, ref, title, lines, PIN1)
    ax, ay = top.px(*pad_of(ref, "1"))
    leader(RX, y + h / 2, ax + 14, ay, PIN1)
    y += h + 22

# --- bottom view ------------------------------------------------------------

BY = H_TOP + 74
bot = View(MARGIN + PAD_L, BY, S_BOT, True, BBOX)
text(MARGIN + PAD_L + bot.w() / 2, BY - 12,
     "BOTTOM  ·  flipped left-to-right, so the connectors stay nearest you",
     13, INK, "700", "middle")
render_side(bot, "B")

c7 = FPS["C7"]
cx, cy = bot.px(mm(c7.GetPosition().x), mm(c7.GetPosition().y))
add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="26" fill="none" stroke="{PLUS}" '
    f'stroke-width="2" stroke-dasharray="6 4"/>')

h = callout(MARGIN, BY + 10, PAD_L - 46, "C7", "10 µF X7R 1210", [
    "*The only surface-mount part, and the",
    "*only thing on this side of the board.",
    "Ceramic, so it has no polarity — fit it",
    "either way round.",
    "It goes on first, before any through-hole",
    "legs are in the way of the iron.",
    "It sits under U1 pin 6, VDDCORE/VCAP:",
    "that is a regulator compensation",
    "capacitor, not a supply bypass, and C6",
    "is not a substitute for it.",
], PLUS)
leader(MARGIN + PAD_L - 46, BY + 10 + h / 2, cx - 28, cy, PLUS)

NX = MARGIN + PAD_L + bot.w() + 46
ny = BY + 10
add(f'<rect x="{NX}" y="{ny}" width="{PAD_R - 46 + 0}" height="196" rx="7" '
    f'fill="#f7f9fb" stroke="{RULE}" stroke-width="1.4"/>')
text(NX + 16, ny + 24, "Do not derive a rule from pad 1", 13.5, INK, "700")
for i, ln in enumerate([
        "On C6 pad 1 is the positive lead.",
        "On D1 and D2 pad 1 is the cathode,",
        "the negative one. They are opposite,",
        "and that is what the badges above",
        "say instead of a pad number.",
        "",
        "R5 is not fitted. The silk reads",
        "120R DNF; the car's bus is already",
        "terminated at both ends."]):
    text(NX + 16, ny + 48 + 17 * i, ln, 12.5, INK)

FY = BY + bot.h() + 40
add(f'<line x1="{MARGIN}" y1="{FY-18}" x2="{W-MARGIN}" y2="{FY-18}" '
    f'stroke="{RULE}" stroke-width="1"/>')
text(MARGIN, FY,
     "The order to solder in, the multimeter check that settles which LED leg "
     "is the anode, and why the sockets have to be marked before they are "
     "soldered: canfuel/docs/install.md step 5.", 12.5, DIM)
text(MARGIN, FY + 19,
     "Generated by kicad/tools/render-assembly.py from canfuel.kicad_pcb — "
     "do not edit this file by hand.", 12.5, DIM)

H = FY + 40
add("</svg>")

svg = "\n".join(out).replace("HEIGHT", str(int(H)))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg + "\n")
print("wrote", OUT, f"({len(svg)} bytes)")
