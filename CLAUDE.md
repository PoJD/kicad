# kicad — hardware

A container for boards. Successor to the older `eagle` repo; each board gets
its own subdirectory and its own `fab/`.

KiCad 10. Text formats mean readable diffs, and `kicad-cli` can run ERC and DRC
in CI without a GUI — a design error fails in the pull request, not on a
finished board.

The CI container image must track the local major version. KiCad refuses to
open files written by a newer major version, so `kicad/kicad:10.0` in
`.github/workflows/kicad.yml` is not incidental — bump it together with the
installed KiCad, never separately.

There is currently one board: `canfuel/`.

---

## Current state — read this first

**The schematic is drawn and ERC clean. The PCB is an outline and nothing
else.** `canfuel/` holds `canfuel.kicad_pro`, `canfuel.kicad_sch` (complete,
one A3 sheet) and `canfuel.kicad_pcb` (55 × 45 mm outline, no footprints
placed), plus `docs/` and an empty `fab/gerbers/`. `lib/` is empty.

CI is live and green: it finds both files and runs ERC and DRC on them for
real. From here on a red run means something.

Note that this repository's CI had **never** actually passed before
2026-08-08. The two check steps opened with `shopt -s globstar nullglob`, a
bash builtin the container's shell does not have, so both failed on every run
since they were written — including runs where the repo held no design files
and the loops had nothing to do. A step that fails with zero input files is
failing before it reads any; that is what gave it away. Both steps are plain
POSIX shell now. Do not reintroduce bash-isms into them, and do not trust a
description of CI that has not been checked against an actual run.

**ERC is not enough on its own, so there is a second check.** Run it after any
edit to the schematic:

```
python tools/check-netlist.py
```

It exports the netlist and compares all 97 connections against the tables in
`canfuel/docs/implementation-plan.md`, which are transcribed into the script.
Not a formality: swapping the labels on U1 pins 23 and 24 — CANTX and CANRX
crossed at the MCU, a board that would never transmit — passes ERC with
**zero** violations, because both are bidirectional pins and nothing about the
sheet is malformed. `check-netlist.py` catches it. That case was tried, not
assumed.

When the design changes on purpose, update `EXPECT` in the script in the same
commit. That is what the file is for.

**KiCad 10.0.5 is installed** at `C:\Program Files\KiCad\10.0`, and
`C:\Program Files\KiCad\10.0\bin\` is on the user PATH. A shell started before
that PATH edit will not see `kicad-cli`; call it by full path rather than
concluding it is missing.

### Resume here — next session

Next up is the PCB layout, section 5 of the plan.

**Say this before starting: the layout cannot be finished until the enclosure
is measured.** The four M3 mounting holes are deliberately not in the board,
because their positions are a guess until then, and they are the one thing
that can force a respin. Placement and routing can all be done first — just do
not generate `fab/` or order anything off a board whose holes are invented.

Then, in order:

1. **Read `canfuel/docs/implementation-plan.md` first.** It is the working
   document: reference designators, the full 28-pin PIC pinout, net names, net
   classes, placement plan and the order of commits. This file only summarises
   it.
2. **Check the prerequisites hold**: `kicad-cli version` prints `10.x`, the
   three `canfuel/canfuel.*` files are present, `python tools/check-netlist.py`
   is clean.
3. **Net classes first** (plan 5.3), then **placement** (5.2), then routing.
   C7 goes against U1 pin 6 before anything else is routed — the datasheet caps
   that track at 6 mm and it is the only part with a numeric constraint.
4. **`kicad-cli pcb drc` until clean**, then commit.
5. Then `fab/` and the purchase list — plan sections 6 and 7.

### Working with the tools here

Things that cost time to work out the first time:

- **`kicad-cli` is at `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`.** That
  directory is on the user PATH, but a shell started before the PATH was edited
  will not see it. Call it by full path rather than concluding it is missing.
- **Its console output is localised** — on this machine it reports in Czech
  ("Nalezeno 0 porušení"). Do not parse it; use the exit code, which
  `--exit-code-violations` makes meaningful, or `--format json`.
- **It drops `*-erc.rpt` / `*-drc.rpt` next to the working directory** unless
  `-o` points elsewhere. Gitignored, but pass `-o` to a temp path anyway.
- **The schematic is edited in the KiCad GUI from here on.** It was originally
  emitted by a throwaway generator script, which is deliberately *not* in the
  repo: re-running it would silently overwrite hand edits. `canfuel.kicad_sch`
  is the source of truth.
- **To look at a sheet or board without the GUI**, export SVG and render it:
  `kicad-cli sch export svg`, then headless Chrome with `--screenshot` on a
  one-line HTML wrapper around the SVG. Worth doing — the first A4 draft was
  ERC-clean and visually unreadable, with note text straight through the parts.
- **The PIC datasheet** is at `canfuel/docs/pic18f25k80-datasheet.pdf`
  (DS39977C; the 28-pin diagram is on page 6). It is text based, so
  `pdftotext -layout` works. Settle any pin question there, not from memory —
  though note the KiCad symbol's pinout has now been checked against it and
  agrees, including pin 6 being `Vcap` and there being no RA4.

### Suggested order of work

The detailed version — reference designators, pin numbers, net classes and the
order of commits — is in `canfuel/docs/implementation-plan.md`. The outline:

1. ~~Install KiCad, confirm `kicad-cli version` runs.~~ Done — 10.0.5.
2. ~~Create the project: `canfuel/canfuel.kicad_pro` plus an empty schematic and
   board, committed on its own so CI going live is a visible step.~~ Done.
3. ~~Draw the schematic against the requirements below. The five things most
   worth double-checking, because they are the ones that quietly kill a board:
   MCP2562 VIO and STBY, no 120 Ω termination fitted, 33 pF crystal loading,
   both Micro-Fit headers wired in parallel, and 10 µF on VDDCORE/VCAP.~~
   Done — all five are on the sheet and repeated in its notes panel.
4. ~~`kicad-cli sch erc` until clean.~~ Done, zero violations.
5. Lay out the PCB inside ~55 × 45 mm, two layers, mostly through-hole.
6. `kicad-cli pcb drc` until clean.
7. Generate `fab/` (gerbers, BOM, CPL) and commit it.
8. Only then assemble the GME purchase list — the BOM falls out of the
   schematic, so buying earlier means buying twice.

### Decisions already made

Everything in the requirements section below is settled and measured, not
provisional. In particular the power supply (5 V from display connector C6/C12)
was verified with a multimeter, and the CAN pinout (C7/C8) is confirmed.

### Still open

- **Blocking the layout: the enclosure.** No mechanical drawing, no
  `canfuel/docs/mechanical.md`, no measurements of how the board mounts in the
  air vent. The four M3 mounting holes are therefore not in the board yet. This
  is the only open question that can force a respin, and it now sits directly
  in front of the next piece of work — measure before ordering, not after.
- Exact 4-pin connector choice at GME for the car side of the harness. Affects
  the loom only, not this board.

The escape header is no longer open — a 2×8 header costs about 4 % of the board
area, so it goes on.

---

## Language

**Everything in this repository is written in English** — documentation,
comments, CI step names, commit messages and file names. Conversation with the
maintainer may be in Czech; nothing written to disk ever is.

Note that `canfuel/docs/bom-purchase.pdf` and `canfuel/docs/crystal-datasheet.pdf`
are supplied PDFs whose contents are not in English and cannot be translated
in place.

---

## Requirements for the canfuel board

A fuel consumption converter for a VW New Beetle. It sits in the air vent
behind the MFD15 display, powered by 5 V taken straight from the display.

### MCU

- **PIC18F25K80** in PDIP-28, in a **narrow socket (7.62 mm)**.
- 16 MHz crystal, load capacitance 32 pF → fit **33 pF** (verified on a
  previous project, not 22 pF).
- ⚠ **Pin 6 is VDDCORE/VCAP, not a port pin** — the 28-pin K80 has no RA4 and
  no ENVREG. The core regulator is permanently enabled on the F (not LF) part
  and needs **10 µF low-ESR to ground within 6 mm of pin 6**. Never tie pin 6
  to VDD. Datasheet DS39977C §2.4 and Table 31-4.

### Transceiver

- **MCP2562-E/P** in a DIP-8 socket.
- ⚠ **Pin VIO to VDD, pin STBY to ground.** Otherwise it stays in standby and
  transmits nothing. This is the easiest mistake to make in the whole design.

### Power

- 5 V from the display's connector C: **C6 = 5 V, C12 = SensorGround**
  (verified with a multimeter).
- No regulator, no reverse-polarity protection, no TVS. The 12 V branch was
  dropped from the design.
- Draw is under 30 mA; the display's limit is 0.5 A.
- Decoupling: 100 nF at every supply pin, 10 µF at the input.

### CAN

- **C7 = CAN-H, C8 = CAN-L.**
- ⚠ **Do not fit the 120 Ω termination** — the bus is already terminated in the
  car and a third resistor would overload it. A solder jumper for bench testing
  is fine.

### Connectors

- 2× Molex Micro-Fit 3.0 header **43045-0400** (right-angle, board mount).
- Both wired **in parallel onto the same four nets** — CAN-H, CAN-L, 5 V, SGND.

Wiring them in parallel means swapping the cables is harmless and the board
itself acts as a CAN pass-through even with the PIC removed. That is
intentional, not an oversight.

### Everything else

- **LEDs:** two (power, CAN status), active only when the debug jumper on RA0
  is fitted. Nothing lights up in the car.
- **ICSP:** 5-pin 2.54 mm header for a PICkit.
- **Escape hatch:** bring the PIC's unused pins out to a 2.54 mm header so a
  design error can be patched with a wire.
- **Dimensions:** ~55 × 45 mm, two layers, mostly through-hole. Enclosure for
  the air vent 6.5 × 5.5 cm, depth max ~3 cm.

---

## Repository rules

- `*.kicad_prl` is gitignored — it is local state, not design.
- `fab/` **is committed**, even though it is generated. The reason is
  traceability: for an ordered board it must be possible to find out exactly
  what was sent to the fab.
- Shared symbols and footprints go in `lib/`, not in a board's directory.
- `kicad-cli sch erc` and `kicad-cli pcb drc` must pass **before ordering**.

---

## The breadboard phase is skipped

Micro-Fit has a 3.0 mm pitch and does not fit a breadboard. Everything is
socketed and the firmware core is tested on the host against real logs (repo
`canfuel`).

---

## Buying parts

The complete BOM only falls out of the schematic, so **put the list together
after the design**, not before. Buying twice is worse than buying later.

- **From the drawer:** PIC18F25K80. Semiconductors do not degrade when kept dry.
- **New:** crystal, all capacitors, resistors, connectors, sockets, LEDs.
  Electrolytics age even without voltage. For the crystal the main argument is
  that an unmarked part has an unknown load capacitance.
- **New purchase:** MCP2562.

Supporting documents in `canfuel/docs/`:

- `implementation-plan.md` — the working document for the design
- `harness.md` — building and testing the loom
- `pic18f25k80-datasheet.pdf` — Microchip DS39977C, PIC18F66K80 family
- `crystal-datasheet.pdf`, `bom-purchase.pdf` — supplied PDFs

---

## Related repositories

Two siblings sit next to this one, with separate toolchains and separate GitHub
remotes under `PoJD/`. The directory above them is deliberately not a git repo,
so always run git inside one of the three.

- `canfuel` — the firmware that runs on this board
- `mfd15` — display configuration; its TRI file is final and verified on
  hardware

Neither of them constrains this board's design. The coupling in this project is
between `canfuel` and `mfd15` (the layout of CAN frames 0x600–0x602), not here.
What this repo owes them is only that the pinout in the requirements above —
C6/C12 for power, C7/C8 for CAN — matches the harness described in
`canfuel/docs/harness.md`.
