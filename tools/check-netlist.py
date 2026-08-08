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

# 4.2 U1 - PIC18F25K80, the full 28-pin table. Pin 6 is VDDCORE/VCAP and pin
# 20 is Vdd; neither is a port pin and the plan says so twice for a reason.
for pin, net in {
        1: "~{MCLR}", 2: "DBG_EN", 3: "LED_PWR", 4: "LED_CAN", 5: "ESC_RA3",
        6: "VCAP", 7: "ESC_RA5", 8: "SGND", 9: "OSC1", 10: "OSC2",
        11: "ESC_RC0", 12: "ESC_RC1", 13: "ESC_RC2", 14: "ESC_RC3",
        15: "ESC_RC4", 16: "ESC_RC5", 17: "CANTX2", 18: "CANRX2",
        19: "SGND", 20: "+5V", 21: "ESC_RB0", 22: "ESC_RB1",
        23: "CAN_TX", 24: "CAN_RX", 25: "ESC_RB4", 26: "ESC_RB5",
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

# 4.2 LEDs and the debug jumper
EXPECT.update({"R1.1": "+5V", "R1.2": "~{MCLR}",
               "R2.1": "DBG_EN", "R2.2": "SGND",
               "JP1.1": "+5V", "JP1.2": "DBG_EN",
               "R3.1": "LED_PWR", "R3.2": "LED_PWR_A",
               "R4.1": "LED_CAN", "R4.2": "LED_CAN_A",
               "D1.1": "SGND", "D1.2": "LED_PWR_A",
               "D2.1": "SGND", "D2.2": "LED_CAN_A"})

# 4.3 ICSP
EXPECT.update({"J3.1": "~{MCLR}", "J3.2": "+5V", "J3.3": "SGND",
               "J3.4": "PGD", "J3.5": "PGC"})

# 5.4 escape hatch: odd pins are row A, even pins row B
EXPECT.update({"J4.1": "ESC_RA3", "J4.3": "ESC_RA5", "J4.5": "ESC_RC0",
               "J4.7": "ESC_RC1", "J4.9": "ESC_RC2", "J4.11": "ESC_RC3",
               "J4.13": "ESC_RC4", "J4.15": "ESC_RC5",
               "J4.2": "CANTX2", "J4.4": "CANRX2", "J4.6": "ESC_RB0",
               "J4.8": "ESC_RB1", "J4.10": "ESC_RB4", "J4.12": "ESC_RB5",
               "J4.14": "+5V", "J4.16": "SGND"})

# Section 2 of the plan, less R5's absence from the BOM which is a separate
# check - see plan section 6.
WANT_REFS = {"U1", "U2", "Y1", "C1", "C2", "C3", "C4", "C5", "C6", "C7",
             "R1", "R2", "R3", "R4", "R5", "D1", "D2",
             "J1", "J2", "J3", "J4", "JP1"}

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
        if got != EXPECT[key]:
            print("MISMATCH %-8s plan says %-12s netlist says %s"
                  % (key, EXPECT[key], got))
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
