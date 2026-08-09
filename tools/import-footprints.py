#!/usr/bin/env python3
"""Do what the GUI's "Update PCB from Schematic" does, without the GUI.

kicad-cli has no equivalent - `kicad-cli pcb` offers drc, export, import,
render and upgrade, and none of them syncs a board against its sheet. So this
exports the netlist, loads each component's footprint from the stock libraries,
adds anything missing to canfuel.kicad_pcb, links every footprint back to its
schematic symbol by KIID path so a later GUI sync matches rather than
duplicates, and assigns every pad's net.

    python tools/import-footprints.py

Re-running is safe and is the point: existing footprints are matched by
reference and keep their position, orientation and side, so hand placement
survives. Only a footprint whose assignment actually changed in the schematic
is swapped, and it is swapped in place.

Needs kicad-cli on PATH and pcbnew, both of which ship with KiCad. On Windows
the stock interpreter cannot import pcbnew, so the script re-runs itself under
KiCad's bundled Python.

Afterwards, run tools/check-placement.py and kicad-cli pcb drc.
"""

import os
import re
import subprocess
import sys
import tempfile

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
ROOT = os.path.dirname(HERE)
SCH = os.path.join(ROOT, "canfuel", "canfuel.kicad_sch")
PCB = os.path.join(ROOT, "canfuel", "canfuel.kicad_pcb")

# R5 is the 120 R termination. The bus is already terminated in the car, so it
# is deliberately not fitted - plan 3.3. The schematic carries dnp/in_bom no;
# this mirrors that onto the board so fab/ comes out right.
DNP = {"R5"}

STAGE = (120.0, 50.0)     # new footprints land off-board, to be placed by hand


def footprint_libs():
    """Where the stock .pretty libraries live on this machine."""
    for path in (os.environ.get("KICAD10_FOOTPRINT_DIR"),
                 r"C:\Program Files\KiCad\10.0\share\kicad\footprints",
                 "/usr/share/kicad/footprints",
                 "/usr/local/share/kicad/footprints",
                 "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"):
        if path and os.path.isdir(path):
            return path
    sys.exit("cannot find KiCad's footprint libraries")


# --------------------------------------------------------------------------
# netlist reading
# --------------------------------------------------------------------------
_TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse(text):
    toks = _TOK.findall(text)
    pos = 0

    def node():
        nonlocal pos
        pos += 1                                   # consume "("
        out = []
        while toks[pos] != ")":
            if toks[pos] == "(":
                out.append(node())
            else:
                t = toks[pos]
                out.append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\")
                           if t.startswith('"') else t)
                pos += 1
        pos += 1
        return out

    return node()


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def one(node, key, default=None):
    hits = find(node, key)
    return hits[0][1] if hits and len(hits[0]) > 1 else default


def read_netlist():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "canfuel.net")
        r = subprocess.run(["kicad-cli", "sch", "export", "netlist",
                            "--format", "kicadsexpr", "-o", out, SCH],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"kicad-cli sch export netlist failed:\n{r.stderr}{r.stdout}")
        root = parse(open(out, encoding="utf-8").read())

    comps = [{"ref": one(c, "ref"), "value": one(c, "value", ""),
              "footprint": one(c, "footprint"), "tstamp": one(c, "tstamps")}
             for c in find(find(root, "components")[0], "comp")]
    nets = {one(n, "name"): [(one(x, "ref"), one(x, "pin")) for x in find(n, "node")]
            for n in find(find(root, "nets")[0], "net")}
    return comps, nets


def main():
    libs = footprint_libs()
    comps, nets = read_netlist()
    board = pcbnew.LoadBoard(PCB)
    existing = {f.GetReference(): f for f in board.Footprints()}

    stage_y = STAGE[1]
    added = swapped = 0
    for c in comps:
        ref, fpid = c["ref"], c["footprint"]
        if not fpid:
            sys.exit(f"{ref} has no footprint assigned in the schematic")
        lib, name = fpid.split(":", 1)

        def load():
            fp = pcbnew.FootprintLoad(os.path.join(libs, lib + ".pretty"), name)
            if fp is None:
                sys.exit(f"{ref}: footprint {fpid} not found in {lib}")
            # FootprintLoad leaves the library nickname empty; without setting
            # it the board records a bare name and every re-run looks like a
            # change.
            fp.SetFPID(pcbnew.LIB_ID(lib, name))
            return fp

        fp = existing.get(ref)
        if fp is not None and fp.GetFPIDAsString() != fpid:
            where, rot, layer = fp.GetPosition(), fp.GetOrientation(), fp.GetLayer()
            board.Remove(fp)
            fp = load()
            board.Add(fp)
            fp.SetPosition(where)
            fp.SetOrientation(rot)
            if layer != fp.GetLayer():
                fp.Flip(where, pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            print(f"  {ref}: footprint changed to {name}")
            swapped += 1
        elif fp is None:
            fp = load()
            board.Add(fp)
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(STAGE[0]),
                                           pcbnew.FromMM(stage_y)))
            stage_y += 8.0
            print(f"  {ref}: added, staged off-board at "
                  f"({STAGE[0]:.0f},{stage_y - 8:.0f}) - needs placing")
            added += 1

        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["tstamp"]))
        if ref in DNP:
            fp.SetDNP(True)
            fp.SetExcludedFromBOM(True)

    # Build the lookup before removing anything: once board.Remove has been
    # called, iterating Footprints() hands back raw SwigPyObjects.
    by_ref = {f.GetReference(): f for f in board.Footprints()}

    # Footprints the schematic no longer has. H1-H4 are exempt and must stay:
    # a mounting hole carries no net and has no symbol, which is exactly why
    # the GUI's "Delete footprints with no symbols" is left unticked there.
    #
    # The removed objects are parked in `detached` on purpose: board.Remove
    # hands ownership back to Python, and if the footprint is then collected,
    # every later SWIG lookup on the board starts returning bare SwigPyObjects.
    # Holding a reference until the process exits keeps the board usable.
    wanted = {c["ref"] for c in comps}
    detached = []
    for ref in sorted(by_ref):
        if ref in wanted or ref.startswith("H"):
            continue
        print(f"  {ref}: no longer in the schematic, removed from the board")
        fp = by_ref.pop(ref)
        board.Remove(fp)
        detached.append(fp)
    for netname, nodes in nets.items():
        net = board.FindNet(netname)
        if net is None:
            net = pcbnew.NETINFO_ITEM(board, netname)
            board.Add(net)
        for ref, pin in nodes:
            if ref not in by_ref:
                sys.exit(f"net {netname}: no footprint for {ref}")
            pad = by_ref[ref].FindPadByNumber(pin)
            if pad is None:
                sys.exit(f"net {netname}: {ref} has no pad {pin}")
            pad.SetNet(net)

    pcbnew.SaveBoard(PCB, board)

    # read it back and prove every connection the netlist names actually landed
    check = pcbnew.LoadBoard(PCB)
    by_ref = {f.GetReference(): f for f in check.Footprints()}
    bad = 0
    for netname, nodes in nets.items():
        for ref, pin in nodes:
            got = by_ref[ref].FindPadByNumber(pin).GetNetname()
            if got != netname:
                print(f"  MISMATCH {ref}.{pin}: expected {netname}, got {got}")
                bad += 1

    total = sum(len(v) for v in nets.values())
    print(f"{added} added, {swapped} swapped, "
          f"{len(list(check.Footprints()))} footprints on the board, "
          f"{len(nets)} nets, {total} pad connections, {bad} mismatches")
    if added:
        print("new footprints are staged off-board - place them before DRC")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
