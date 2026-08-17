#!/usr/bin/env python3
"""Write the after-soldering check for every joint on canfuel.

    python tools/render-solder-check.py

Writes canfuel/docs/solder-check.md.

`canfuel/docs/install.md` step 5 says to measure every part *before* it goes in,
which catches a misread colour code and nothing else. A joint fails in two
directions and neither is visible:

    open    - the iron never wetted the pad, or the lead moved while it cooled
    bridged - solder reached the nearest copper, which is rarely the next pad

So each pad gets two readings rather than one: **where the meter must show
continuity**, which proves the joint, and **what it must stay open to**, which
proves nothing else got caught. Both are looked up rather than reasoned about,
because the nearest copper to a pad is usually not where you would guess. SGND
is poured on both layers, so for most pads the answer is "ground, a fraction of
a millimetre away, on every side".

Everything here is measured off canfuel.kicad_pcb: the nets come from the
netlist, the distances from the filled copper. Nothing is typed in, which is the
point - a table of forty clearances maintained by hand would be wrong within one
re-layout and there would be no way to tell.

The distances are **copper edge to copper edge, as designed**. They are not
solder mask, and mask does not make a bridge impossible - it makes it less
likely. A number under about half a millimetre means the bridge is easy and the
check is worth the ten seconds.

Needs pcbnew, which ships with KiCad. On Windows the stock interpreter cannot
import it, so the script re-runs itself under KiCad's bundled Python.
"""

import math
import os
import re
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
OUT = os.path.join(BOARD_DIR, "docs", "solder-check.md")

# Parts with nothing to check: the mounting holes are not plated, and R5 is the
# termination that must not be fitted.
SKIP = {"H1", "H2", "H3", "H4", "R5"}

# Where to send somebody with a probe, best first. A numbered header hole beats
# a capacitor lead: you can find it without counting.
PROBE_ORDER = ["J3", "JP1", "JP2", "J1", "J2", "U1", "U2"]

# The two nets that are everywhere. Naming one pad of them would be arbitrary.
BULK = {"SGND": "any ground", "+5V": "any +5 V pin"}

NEAR = 1.0        # mm: report every foreign net at least this close
WORTH = 0.60      # mm: below this, call the bridge easy

mm = lambda v: v / 1e6

board = pcbnew.LoadBoard(PCB)


# --- pads as axis-aligned rectangles ---------------------------------------
#
# Every pad on this board sits at a multiple of 90 degrees, so a rectangle in
# board coordinates is exact rather than an approximation. Assert it, so that a
# future rotated part fails loudly instead of quietly reporting wrong gaps.

def pad_rect(p):
    """A pad as (cx, cy, ex, ey, r): the rectangle it would be with square
    corners, plus the corner radius that rounds it off.

    Every shape on this board is a round-rectangle in that sense - a circular
    pad is one with ex = ey = 2r, an oval one with r = min(ex, ey)/2 - and one
    representation keeps every distance below exact. Treating a 1.6 mm circular
    pad as a 1.6 mm square is not conservative-but-safe, it is wrong by 0.33 mm
    at the corners, which is the whole margin being reported.
    """
    rot = round(p.GetOrientationDegrees()) % 180
    if rot not in (0, 90):
        sys.exit(f"pad at {mm(p.GetPosition().x)},{mm(p.GetPosition().y)} is "
                 f"rotated {rot} deg; this script assumes multiples of 90")
    sx, sy = mm(p.GetSizeX()), mm(p.GetSizeY())
    if rot == 90:
        sx, sy = sy, sx
    shape = p.GetShape()
    if shape in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL):
        r = min(sx, sy) / 2
    elif shape == pcbnew.PAD_SHAPE_ROUNDRECT:
        r = mm(p.GetRoundRectCornerRadius())
    else:
        r = 0.0
    return (mm(p.GetPosition().x), mm(p.GetPosition().y),
            max(sx - 2 * r, 0.0), max(sy - 2 * r, 0.0), r)


def rect_pt(rect, pt):
    cx, cy, ex, ey, r = rect
    return max(math.hypot(max(abs(pt[0] - cx) - ex / 2, 0),
                          max(abs(pt[1] - cy) - ey / 2, 0)) - r, 0.0)


def rect_rect(a, b):
    return max(math.hypot(max(abs(a[0] - b[0]) - (a[2] + b[2]) / 2, 0),
                          max(abs(a[1] - b[1]) - (a[3] + b[3]) / 2, 0))
               - a[4] - b[4], 0.0)


def seg_rect(rect, s, e, halfw):
    """Distance from a track's copper edge to a pad's copper edge."""
    cx, cy, ex, ey, r = rect
    reach = NEAR + 1 + r
    if (min(s[0], e[0]) - halfw > cx + ex / 2 + reach or
            max(s[0], e[0]) + halfw < cx - ex / 2 - reach or
            min(s[1], e[1]) - halfw > cy + ey / 2 + reach or
            max(s[1], e[1]) + halfw < cy - ey / 2 - reach):
        return 1e9
    n = max(2, int(math.dist(s, e) / 0.05))
    best = 1e9
    for i in range(n + 1):
        t = i / n
        best = min(best, rect_pt(rect, (s[0] + (e[0] - s[0]) * t,
                                        s[1] + (e[1] - s[1]) * t)))
    return max(best - halfw, 0.0)


# --- the board's copper, bucketed so the search is not quadratic ------------

CELL = 2.0


def key(x, y):
    return (int(x // CELL), int(y // CELL))


# The pour outline is tens of thousands of segments once every thermal relief
# and clearance cutout is in it, so it goes into a grid keyed by each segment's
# bounding box. Only the handful of segments near a pad are ever measured.
zone_seg = {}          # (net, layer) -> {cell: [(a, b), ...]}


def load_zones():
    for z in board.Zones():
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(layer):
                continue
            ps = z.GetFilledPolysList(layer)
            grid = zone_seg.setdefault((z.GetNetname(), layer), {})
            for i in range(ps.OutlineCount()):
                rings = [ps.Outline(i)] + [ps.Hole(i, k)
                                           for k in range(ps.HoleCount(i))]
                for ring in rings:
                    n = ring.PointCount()
                    pts = [(mm(ring.CPoint(k).x), mm(ring.CPoint(k).y))
                           for k in range(n)]
                    for k in range(n):
                        a, c = pts[k], pts[(k + 1) % n]
                        x0, y0 = key(min(a[0], c[0]) - NEAR,
                                     min(a[1], c[1]) - NEAR)
                        x1, y1 = key(max(a[0], c[0]) + NEAR,
                                     max(a[1], c[1]) + NEAR)
                        for gx in range(x0, x1 + 1):
                            for gy in range(y0, y1 + 1):
                                grid.setdefault((gx, gy), []).append((a, c))


load_zones()

TRACKS = []
for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA":
        # A via's diameter comes off its bounding box. PCB_VIA::GetWidth() wants
        # a layer argument in KiCad 10 and asserts without one, and an assert
        # here is a modal dialog on a machine with no display: the script hangs
        # rather than failing.
        layers = [pcbnew.F_Cu, pcbnew.B_Cu]
        bx = t.GetBoundingBox()
        rad = mm(min(bx.GetWidth(), bx.GetHeight())) / 2
        r = (mm(t.GetStart().x), mm(t.GetStart().y), 0.0, 0.0, rad)
        TRACKS.append(("via", t.GetNetname(), layers, r, None, None))
    else:
        layers = [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if t.IsOnLayer(l)]
        TRACKS.append(("track", t.GetNetname(), layers, None,
                       (mm(t.GetStart().x), mm(t.GetStart().y)),
                       (mm(t.GetEnd().x), mm(t.GetEnd().y)),
                       ))
        TRACKS[-1] = TRACKS[-1] + (mm(t.GetWidth()) / 2,)

def netname(n):
    """Strip KiCad's escaping and its unconnected-pad placeholders."""
    if n.startswith("unconnected-"):
        return ""
    return n.replace("~{", "~").replace("{slash}", "/").replace("}", "")


PADS = []
for fp in board.GetFootprints():
    for p in fp.Pads():
        if not p.GetNumber():
            continue
        layers = [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)]
        PADS.append((fp.GetReference(), p.GetNumber(), netname(p.GetNetname()),
                     layers, pad_rect(p), p))


def probe(net, exclude_ref=None, exclude_pad=None):
    """Where to put a probe for `net`, named so it can be found by eye.

    R5 never appears: it is the termination that must not be fitted, so its
    pads are two holes with nothing in them and are no use as a probe point.
    """
    if net in BULK:
        extra = [f"{r} pin {n}" for r, n, nt, _, _, _ in PADS
                 if nt == net and r in PROBE_ORDER]
        extra.sort(key=lambda s: (PROBE_ORDER.index(s.split()[0]), s))
        return BULK[net] + (f" — {extra[0]}" if extra else "")
    cands = [(r, n) for r, n, nt, _, _, _ in PADS
             if nt == net and r not in SKIP
             and not (r == exclude_ref and n == exclude_pad)]
    if not cands:
        return ""

    def rank(rn):
        r = rn[0]
        return (PROBE_ORDER.index(r) if r in PROBE_ORDER else 99, r, rn[1])

    cands.sort(key=rank)
    return ", ".join(f"{r} pin {n}" if r[0] in "JU" else f"{r} pad {n}"
                     for r, n in cands[:3])


def neighbours(ref, num, net, layers, rect):
    """Every foreign net within NEAR of this pad's copper, nearest first."""
    found = {}

    def note(n, d):
        n = netname(n)
        if not n or n == net:
            return
        if d < found.get(n, 9e9):
            found[n] = d

    for item in TRACKS:
        kind, tnet, tlayers, vrect = item[0], item[1], item[2], item[3]
        if not set(tlayers) & set(layers) or netname(tnet) in ("", net):
            continue
        if kind == "via":
            d = rect_rect(rect, vrect)
        else:
            d = seg_rect(rect, item[4], item[5], item[6])
        if d < NEAR:
            note(tnet, d)

    for r2, n2, net2, l2, rect2, _ in PADS:
        if (r2, n2) == (ref, num) or not set(l2) & set(layers):
            continue
        d = rect_rect(rect, rect2)
        if d < NEAR:
            note(net2, d)

    for (znet, zlayer), grid in zone_seg.items():
        if zlayer not in layers or netname(znet) in ("", net):
            continue
        cx, cy, ex, ey, r = rect
        best = 9e9
        seen = set()
        x0, y0 = key(cx - ex / 2 - r - NEAR, cy - ey / 2 - r - NEAR)
        x1, y1 = key(cx + ex / 2 + r + NEAR, cy + ey / 2 + r + NEAR)
        for gx in range(x0, x1 + 1):
            for gy in range(y0, y1 + 1):
                for a, c in grid.get((gx, gy), ()):
                    if (a, c) in seen:
                        continue
                    seen.add((a, c))
                    best = min(best, seg_rect(rect, a, c, 0.0))
        if best < NEAR:
            note(znet, best)

    # Three is as many as anybody checks. They are the three nearest, and the
    # nearest is nearly always the pour.
    return sorted(found.items(), key=lambda kv: kv[1])[:3]


# --- the document -----------------------------------------------------------

def natural(ref):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


lines = []
w = lines.append

w("<!-- Generated by kicad/tools/render-solder-check.py. Do not edit. -->")
w("")
w("# After each joint: what must read zero, and what must not")
w("")
w("`canfuel/docs/install.md` step 5 has you measure every part **before** it")
w("goes in, which catches a misread colour code and nothing else. This is the")
w("other half, and it is per **joint** rather than per part.")
w("")
w("A soldered joint fails in two directions and neither one is visible:")
w("")
w("- **open** — the iron never wetted the pad, or the lead moved as it cooled")
w("- **bridged** — solder reached the nearest copper, which is hardly ever the")
w("  next pad along")
w("")
w("So every pad gets two readings. **Continuity** proves the joint exists;")
w("**isolation** proves nothing else got caught. Look the second one up rather")
w("than guessing it — SGND is poured on both layers, so for most pads the")
w("nearest copper is ground, a fraction of a millimetre away, on every side.")
w("")
w("## How to hold the meter")
w("")
w("- **Continuity (beeper) for the \"zero\" column.** A joint either rings or")
w("  it does not.")
w("- **Resistance, not the beeper, for anything with a capacitor across it.**")
w("  A 10 µF part charges through the meter, so the beeper chirps once and")
w("  goes quiet. That chirp is the capacitor, not a bridge. Watch the number")
w("  climb instead: it must settle in megohms or `OL`. A steady near-zero that")
w("  never moves is a bridge.")
w("- **Measure with nothing else fitted yet**, which is what the solder order")
w("  in install.md gives you for free. Once the neighbours are in, every")
w("  reading is of whatever else shares the net.")
w("- **The distances below are copper edge to copper edge, as designed.**")
w(f"  Solder mask sits between most of them, which makes a bridge less likely")
w(f"  and not impossible. Anything under about {WORTH:.1f} mm is worth the ten")
w("  seconds.")
w("")
w("## How to read it")
w("")
w("Find the part you have just soldered. Every one of its pads gets a row.")
w("")
w("- **`—` in the zero column** means the pad is on no net. Fourteen of U1's")
w("  pins are like that: the pin goes nowhere and there is nothing it should")
w("  ring to. Its **open** column still matters — the firmware drives every")
w("  unused pin low, so a bridge from one of them to +5 V is a short through")
w("  the port driver.")
w("- **U1 and U2 are the socket holes**, so their rows are checked once the")
w("  socket is soldered and before either chip goes in. That is also the only")
w("  time the holes are reachable.")
w("- **A named probe point is a hole you can find by eye** — `J3 pin 1` is the")
w("  square pad of the ICSP header, `U1 pin 1` the end the silk notch marks.")
w("  Where several are listed, any of them will do.")
w("")

order = sorted((fp for fp in board.GetFootprints()
                if fp.GetReference() not in SKIP),
               key=lambda fp: natural(fp.GetReference()))

for fp in order:
    ref = fp.GetReference()
    side = "bottom" if fp.GetLayer() == pcbnew.B_Cu else "top"
    w(f"## {ref} — {fp.GetValue()}" + (" *(bottom side)*" if side == "bottom"
                                       else ""))
    w("")
    w("| Pad | Net | Must read **zero** to | Must stay **open** to |")
    w("|---|---|---|---|")
    for p in fp.Pads():
        num = p.GetNumber()
        if not num:
            continue
        net = netname(p.GetNetname())
        layers = [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)]
        rect = pad_rect(p)
        zero = probe(net, ref, num) if net else ""
        near = neighbours(ref, num, net, layers, rect)
        cells = []
        for n, d in near:
            where = probe(n, ref, num)
            cells.append(f"**{n}** {d:.2f} mm" + (f" ({where})" if where else ""))
        w(f"| {num} | {net or '—'} | {zero or '—'} | "
          + ("; ".join(cells) if cells else "nothing within "
             f"{NEAR:.1f} mm") + " |")
    w("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("wrote", OUT)
