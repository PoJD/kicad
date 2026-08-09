#!/usr/bin/env python3
"""Check canfuel's schematic against its implementation plan.

ERC proves the sheet is electrically well formed. It cannot prove that RB2
went to the transceiver's TXD rather than RB3 - both are bidirectional pins
on a two-pin net either way. This does: it exports the netlist and compares
every ref.pin -> net against the tables in canfuel/docs/implementation-plan.md,
which are typed out below by hand.

    python tools/check-netlist.py

Needs kicad-cli on PATH. Exits nonzero on any mismatch, so it can be wired
into CI later if that turns out to be worth it.

When the design changes on purpose, change EXPECT here in the same commit -
that is the point of the file, not an inconvenience.
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(os.path.dirname(HERE), "canfuel", "canfuel.kicad_sch")

# --------------------------------------------------------------------------
# Expected connections, from canfuel/docs/implementation-plan.md
# --------------------------------------------------------------------------

EXPECT = {}

# Sentinel for a pin that carries a no-connect flag on purpose. KiCad names
# such a net "unconnected-(U1-RA1{slash}AN1-Pad3)", which is generated from the
# pin's own name and would turn this table into a transcription exercise; what
# is actually being asserted is "nothing is wired here, deliberately".
NC = object()

# 4.2 U1 - PIC18F25K80, the full 28-pin table. Pin 6 is VDDCORE/VCAP and pin
# 20 is Vdd; neither is a port pin and the plan says so twice for a reason.
#
# The LEDs are on RC0/RC1, not RA1/RA2: the Absolute Maximum Ratings on
# DS39977C page 541 allow PORTA<5:0> only 2 mA sourced or sunk, against 25 mA
# for PORTB and PORTC. RA1/RA2 took the RC0/RC1 escape slots in exchange, and
# when the escape header itself went (plan 5.4) all fourteen became NC.
for pin, net in {
        1: "~{MCLR}", 2: "DBG_EN", 3: NC, 4: NC, 5: NC,
        6: "VCAP", 7: NC, 8: "SGND", 9: "OSC1", 10: "OSC2",
        11: "LED_PWR", 12: "LED_CAN", 13: NC, 14: NC,
        15: NC, 16: NC, 17: NC, 18: NC,
        19: "SGND", 20: "+5V", 21: NC, 22: NC,
        23: "CAN_TX", 24: "CAN_RX", 25: NC, 26: NC,
        27: "PGC", 28: "PGD"}.items():
    EXPECT["U1.%d" % pin] = net

# 3.1 MCP2562. Pin 5 (Vio) and pin 8 (STBY) are the two that decide whether
# the board transmits at all.
for pin, net in {1: "CAN_TX", 2: "SGND", 3: "+5V", 4: "CAN_RX",
                 5: "+5V", 6: "CANL", 7: "CANH", 8: "SGND"}.items():
    EXPECT["U2.%d" % pin] = net

# 3.2 crystal and its 33 pF loading
EXPECT.update({"Y1.1": "OSC1", "Y1.2": "OSC2",
               "C1.1": "OSC1", "C1.2": "SGND",
               "C2.1": "OSC2", "C2.2": "SGND"})

# 3.3 termination across CANH/CANL, not fitted
EXPECT.update({"R5.1": "CANH", "R5.2": "CANL"})

# 3.4 both Micro-Fit headers on the same four nets
for j in ("J1", "J2"):
    EXPECT.update({j + ".1": "+5V", j + ".2": "SGND",
                   j + ".3": "CANH", j + ".4": "CANL"})

# 3.5 VDDCORE/VCAP, and 4.4 decoupling
EXPECT.update({"C7.1": "VCAP", "C7.2": "SGND"})
for c in ("C3", "C4", "C5", "C6"):
    EXPECT.update({c + ".1": "+5V", c + ".2": "SGND"})

# 4.3a the MCLR network of DS39977C Figure 2-2, in full: the 10k pull-up, the
# 470 ohm that limits what C8 can dump into the pin if MCLR ever breaks down,
# and the jumper that lifts C8 off the node during programming - section 2.5
# is explicit that a capacitor there interferes with the programmer.
EXPECT.update({"R6.1": "MCLR_RC", "R6.2": "~{MCLR}",
               "JP2.1": "MCLR_RC", "JP2.2": "MCLR_C",
               "C8.1": "MCLR_C", "C8.2": "SGND"})

# 4.2 LEDs and the debug jumper
EXPECT.update({"R1.1": "+5V", "R1.2": "MCLR_RC",
               "R2.1": "DBG_EN", "R2.2": "SGND",
               "JP1.1": "+5V", "JP1.2": "DBG_EN",
               "R3.1": "LED_PWR", "R3.2": "LED_PWR_A",
               "R4.1": "LED_CAN", "R4.2": "LED_CAN_A",
               "D1.1": "SGND", "D1.2": "LED_PWR_A",
               "D2.1": "SGND", "D2.2": "LED_CAN_A"})

# 4.3 ICSP
EXPECT.update({"J3.1": "~{MCLR}", "J3.2": "+5V", "J3.3": "SGND",
               "J3.4": "PGD", "J3.5": "PGC"})

# 5.4 escape hatch: REMOVED on 2026-08-09, see plan 5.4. The fourteen ESC_*
# labels above are now single-node nets and U1's unused pins carry no-connect
# flags. They stay named because the name is what says which pin is which.
#
# Why it went: with J4 fitted the router left 8 of 39 connections unroutable,
# and five of those eight were not escape signals - both status LEDs and the
# whole ICSP header. A header whose job is to rescue a design error was
# stopping the chip being programmed. Without it the board routes complete and
# DRC clean. Patching now means soldering to the PDIP socket pins underneath.

# Section 2 of the plan, less R5's absence from the BOM which is a separate
# check - see plan section 6.
WANT_REFS = {"U1", "U2", "Y1", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8",
             "R1", "R2", "R3", "R4", "R5", "R6", "D1", "D2",
             "J1", "J2", "J3", "JP1", "JP2"}

# --------------------------------------------------------------------------


def parse(text):
    """Just enough S-expression reader for a netlist."""
    pos, out = 0, []
    while pos < len(text):
        while pos < len(text) and text[pos] in " \t\r\n":
            pos += 1
        if pos >= len(text):
            break
        node, pos = _node(text, pos)
        out.append(node)
    return out


def _node(text, pos):
    pos += 1  # the opening paren
    items = []
    while True:
        while text[pos] in " \t\r\n":
            pos += 1
        c = text[pos]
        if c == ")":
            return items, pos + 1
        if c == "(":
            node, pos = _node(text, pos)
            items.append(node)
        elif c == '"':
            pos += 1
            buf = []
            while text[pos] != '"':
                if text[pos] == "\\":
                    pos += 1
                buf.append(text[pos])
                pos += 1
            items.append("".join(buf))
            pos += 1
        else:
            start = pos
            while text[pos] not in ' \t\r\n()':
                pos += 1
            items.append(text[start:pos])


def find(node, tag):
    for child in node:
        if isinstance(child, list) and child and child[0] == tag:
            return child
    return None


def find_all(node, tag):
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]


def main():
    sch = sys.argv[1] if len(sys.argv) > 1 else SCH
    if not os.path.exists(sch):
        sys.exit("no such schematic: " + sch)

    with tempfile.TemporaryDirectory() as tmp:
        net = os.path.join(tmp, "canfuel.net")
        subprocess.run(["kicad-cli", "sch", "export", "netlist",
                        "--format", "kicadsexpr", "-o", net, sch],
                       check=True, stdout=subprocess.DEVNULL)
        with open(net, encoding="utf-8") as fh:
            root = parse(fh.read())[0]

    actual = {}
    nets = find(root, "nets")
    for n in find_all(nets, "net"):
        name = find(n, "name")[1]
        for node in find_all(n, "node"):
            actual["%s.%s" % (find(node, "ref")[1], find(node, "pin")[1])] = name

    # The power-flag helpers carry no design intent.
    actual = {k: v for k, v in actual.items()
              if not k.startswith("#PWR") and not k.startswith("#FLG")}

    bad = 0
    for key in sorted(EXPECT, key=lambda k: (k.split(".")[0],
                                             int(k.split(".")[1]))):
        got = actual.get(key, "<not in netlist>")
        want = EXPECT[key]
        if want is NC:
            if not got.startswith("unconnected-"):
                print("MISMATCH %-8s plan says no-connect  netlist says %s"
                      % (key, got))
                bad += 1
        elif got != want:
            print("MISMATCH %-8s plan says %-12s netlist says %s"
                  % (key, want, got))
            bad += 1

    for key in sorted(set(actual) - set(EXPECT)):
        print("UNEXPECTED %-8s -> %s  (not in the plan)" % (key, actual[key]))
        bad += 1

    real = {find(c, "ref")[1]
            for c in find_all(find(root, "components"), "comp")}
    real = {r for r in real if not r.startswith("#")}
    if real != WANT_REFS:
        print("missing refs:   ", sorted(WANT_REFS - real))
        print("unexpected refs:", sorted(real - WANT_REFS))
        bad += 1

    print("%d nets, %d components, %d connections checked"
          % (len(find_all(nets, "net")), len(real), len(EXPECT)))
    print("RESULT: " + ("%d problem(s)" % bad if bad
                        else "schematic matches the implementation plan"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
