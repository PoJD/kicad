#!/usr/bin/env python3
"""Check canfuel's placement against the distance rules in DS39977C.

DRC proves the board is manufacturable. It cannot prove that C7 is still near
U1 pin 6, because a decoupling capacitor 40 mm from its pin is a perfectly
legal board - it is just a broken one. This checks the four numeric constraints
of canfuel/docs/implementation-plan.md 5.2, which all come from the datasheet:

    2.2.1  C3 -> U1 pin 20, C4 -> U2 pin 3, C5 -> U2 pin 5, trace <= 6 mm
    2.3    R1, R6, C8, JP2 placed within 6 mm of U1 pin 1
    2.4    C7 -> U1 pin 6 (VCAP), trace <= 6 mm
    2.6    Y1, C1, C2 within 12 mm of their respective oscillator pins,
           on the same side of the board as U1

It also re-checks what DRC does not: that nothing has drifted into the 7 mm
circle a nylon M3 standoff head needs around each mounting hole.

    python tools/check-placement.py

Needs pcbnew, which ships with KiCad. On Windows the stock interpreter cannot
import it, so the script re-runs itself under KiCad's bundled Python.

The datasheet is not uniform about what it measures and the difference decides
whether this board passes, so the two readings are kept apart:

    "trace length from the pin to the capacitor"   -> pad to pad
    "components ... placed within 6 mm of the pin" -> the whole courtyard

Where a rule cannot be met, the tolerated shortfall is recorded in ALLOW below
with its reason, so an intentional deviation and a regression never look alike.
When the design changes on purpose, change this file in the same commit.
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
PCB = os.path.join(os.path.dirname(HERE), "canfuel", "canfuel.kicad_pcb")

BOARD = (50.0, 50.0, 105.0, 95.0)      # Edge.Cuts extent, plan 5.1
EDGE_MARGIN = 0.3
HOLES = [("H1", 54, 54), ("H2", 101, 54), ("H3", 54, 91), ("H4", 101, 91)]
HOLE_KEEPOUT = 3.5                     # 7 mm circle: an M3 standoff head is 6 mm

# trace length, mm: (capacitor, its pad, chip, chip pin, limit, what)
TRACE = [
    ("C7", "1", "U1", "6",  6.0, "DS39977C 2.4   VCAP"),
    ("C3", "1", "U1", "20", 6.0, "DS39977C 2.2.1 U1 VDD"),
    ("C4", "1", "U2", "3",  6.0, "DS39977C 2.2.1 U2 VDD"),
    ("C5", "1", "U2", "5",  6.0, "DS39977C 2.2.1 U2 VIO"),
]

# DS39977C 2.3, measured over the whole courtyard
MCLR_PARTS = ["R1", "R6", "C8", "JP2"]
MCLR_LIMIT = 6.0

# DS39977C 2.6, measured to the pin each part is actually on
OSC = [("Y1", ["9", "10"]), ("C1", ["9"]), ("C2", ["10"])]
OSC_LIMIT = 12.0

# Deviations that are deliberate. Key -> (tolerated value, why).
#
# 2.3 asks for four parts inside a 6 mm circle centred on a corner pin of a
# DIP-28. Three quarters of that circle is free, about 85 mm2, and the four
# parts are 71 mm2 of courtyard between them: they do not fit, and no choice
# of footprint changes that.
#
# What is done instead is to make every one of them hug the pin: the
# arrangement was found by search, minimising the worst far corner, and all
# four have their nearest edge within 2.5 mm. The far corners below are the
# bodies extending outward, not the connections - which is what 2.3 is
# really about, since the pin sees the near end.
#
# MCLR_NEAR below is the assertion that actually carries weight now. If the
# far corners drift, something moved; do not widen these to make it green.
ALLOW = {
    "2.3 R6":  (8.0, "series resistor, nearest edge 2.46 mm from pin 1"),
    "2.3 C8":  (8.0, "reset capacitor, nearest edge 1.66 mm"),
    "2.3 JP2": (9.0, "in series with C8, nearest edge 1.88 mm"),
    "2.3 R1":  (8.5, "10 k pull-up to VDD: static bias, the least "
                     "distance-sensitive part of Figure 2-2"),
}
MCLR_NEAR = 3.0        # every MCLR part's nearest edge must be this close

# DS39977C 2.6 keep-outs, matching the ones the router is given.
OSC_GUARD = (64.0, 51.0, 86.5, 62.4)      # guard area on F.Cu, around Y1/C1/C2
CRYSTAL_BACK = (68.5, 55.0, 81.6, 62.0)   # the far side, under the crystal
OSC_OK = {"OSC1", "OSC2", "SGND"}         # the oscillator's own nets and ground


def _hits(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def mm(v):
    return v / 1e6


def pad_xy(fp, num):
    p = fp.FindPadByNumber(num)
    if p is None:
        sys.exit(f"{fp.GetReference()} has no pad {num}")
    q = p.GetPosition()
    return mm(q.x), mm(q.y)


def courtyard(fp):
    for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        poly = fp.GetCourtyard(layer)
        if poly.OutlineCount():
            bb = poly.BBox()
            return (mm(bb.GetLeft()), mm(bb.GetTop()),
                    mm(bb.GetRight()), mm(bb.GetBottom()))
    bb = fp.GetBoundingBox(False, False)
    return (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def far_corner(box, pt):
    return max(dist((x, y), pt) for x in (box[0], box[2]) for y in (box[1], box[3]))


def near_edge(box, pt):
    dx = max(box[0] - pt[0], 0, pt[0] - box[2])
    dy = max(box[1] - pt[1], 0, pt[1] - box[3])
    return math.hypot(dx, dy)


def main():
    if not os.path.exists(PCB):
        sys.exit(f"no board at {PCB}")
    board = pcbnew.LoadBoard(PCB)
    fps = {f.GetReference(): f for f in board.Footprints()}
    bad = []

    print("Trace length from pin to capacitor")
    for cap, cpad, chip, cpin, limit, what in TRACE:
        if cap not in fps or chip not in fps:
            bad.append(f"{cap} or {chip} is not on the board")
            continue
        d = dist(pad_xy(fps[cap], cpad), pad_xy(fps[chip], cpin))
        side = "B.Cu" if fps[cap].GetLayer() == pcbnew.B_Cu else "F.Cu"
        ok = d <= limit
        print(f"  {cap}.{cpad} -> {chip}.{cpin:<3} {d:6.2f} mm  "
              f"(limit {limit:.0f}, {side})  {what}  {'ok' if ok else 'FAIL'}")
        if not ok:
            bad.append(f"{what}: {cap} to {chip} pin {cpin} is {d:.2f} mm")

    print(f"\nMCLR network placed within {MCLR_LIMIT:.0f} mm of U1 pin 1 "
          f"(DS39977C 2.3)")
    p1 = pad_xy(fps["U1"], "1")
    for ref in MCLR_PARTS:
        box = courtyard(fps[ref])
        near, far = near_edge(box, p1), far_corner(box, p1)
        key = f"2.3 {ref}"
        if far <= MCLR_LIMIT:
            verdict = "ok"
        elif key in ALLOW and far <= ALLOW[key][0]:
            verdict = "allowed"
        else:
            verdict = "FAIL"
            bad.append(f"2.3: {ref} reaches {far:.2f} mm from U1 pin 1")
        if near > MCLR_NEAR:
            verdict = "FAIL"
            bad.append(f"2.3: {ref} nearest edge is {near:.2f} mm from U1 "
                       f"pin 1, wanted within {MCLR_NEAR}")
        print(f"  {ref:<4} nearest edge {near:5.2f}  farthest corner {far:5.2f} mm"
              f"  {verdict}")
        if verdict == "allowed":
            print(f"       deviation: {ALLOW[key][1]}")

    print(f"\nOscillator within {OSC_LIMIT:.0f} mm of its pins (DS39977C 2.6)")
    for ref, pins in OSC:
        box = courtyard(fps[ref])
        mid = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        pts = [pad_xy(fps["U1"], p) for p in pins]
        centre = max(dist(mid, p) for p in pts)
        far = max(far_corner(box, p) for p in pts)
        ok = centre <= OSC_LIMIT
        print(f"  {ref:<4} to U1 pin {'/'.join(pins):<5} centre {centre:5.2f}  "
              f"farthest corner {far:5.2f} mm  {'ok' if ok else 'FAIL'}")
        if not ok:
            bad.append(f"2.6: {ref} centre is {centre:.2f} mm from pin "
                       f"{'/'.join(pins)}")
    off = [r for r, _ in OSC if fps[r].GetLayer() != fps["U1"].GetLayer()]
    print(f"  same side of the board as U1: {'no - ' + ', '.join(off) if off else 'yes'}")
    if off:
        bad.append(f"2.6: {', '.join(off)} is not on the same side as U1")

    # DS39977C 2.6, the two rules about copper rather than parts:
    #   "Do not run any signal traces or power traces inside the ground pour"
    #   "avoid any traces on the other side of the board where the crystal is"
    # The ground pour itself is exempt: it IS the guard the section asks for.
    print("\nOscillator guard (DS39977C 2.6)")
    intruders = []
    for t in board.Tracks():
        if t.GetClass() == "PCB_VIA":
            box = (mm(t.GetPosition().x), mm(t.GetPosition().y)) * 2
            box = (box[0], box[1], box[0], box[1])
        else:
            s, e = t.GetStart(), t.GetEnd()
            box = (min(mm(s.x), mm(e.x)), min(mm(s.y), mm(e.y)),
                   max(mm(s.x), mm(e.x)), max(mm(s.y), mm(e.y)))
        net = t.GetNetname()
        on_front = t.GetLayer() == pcbnew.F_Cu or t.GetClass() == "PCB_VIA"
        if on_front and net not in OSC_OK and _hits(box, OSC_GUARD):
            intruders.append(f"{net} crosses the guard area on F.Cu")
        if t.GetLayer() == pcbnew.B_Cu and _hits(box, CRYSTAL_BACK):
            intruders.append(f"{net} runs under the crystal on B.Cu")
    for msg in sorted(set(intruders)):
        print("  " + msg + "  FAIL")
        bad.append("2.6: " + msg)
    if not intruders:
        print("  no signal or power traces in the guard area, nothing on B.Cu "
              "under the crystal")

    print("\nBoard outline and mounting-hole keepout")
    for ref, fp in sorted(fps.items()):
        if ref.startswith("H"):
            continue
        box = courtyard(fp)
        if (box[0] < BOARD[0] + EDGE_MARGIN or box[1] < BOARD[1] + EDGE_MARGIN
                or box[2] > BOARD[2] - EDGE_MARGIN or box[3] > BOARD[3] - EDGE_MARGIN):
            bad.append(f"{ref} is outside the board outline")
            print(f"  {ref} x[{box[0]:.2f},{box[2]:.2f}] y[{box[1]:.2f},{box[3]:.2f}]"
                  f"  FAIL")
        for hole, hx, hy in HOLES:
            d = near_edge(box, (hx, hy))
            if d < HOLE_KEEPOUT:
                bad.append(f"{ref} is {d:.2f} mm from {hole}, needs {HOLE_KEEPOUT}")
                print(f"  {ref} is {d:.2f} mm from {hole}  FAIL")
    if not any(b for b in bad if "outline" in b or "mm from H" in b):
        print("  clear")

    print()
    if bad:
        print(f"RESULT: {len(bad)} problems")
        for b in bad:
            print("  " + b)
        return 1
    print("RESULT: placement matches the datasheet constraints")
    return 0


if __name__ == "__main__":
    sys.exit(main())
