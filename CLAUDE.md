# kicad — hardware

A container for boards. Successor to the older `eagle` repo; each board gets
its own subdirectory and its own `fab/`.

KiCad 8. Text formats mean readable diffs, and `kicad-cli` can run ERC and DRC
in CI without a GUI — a design error fails in the pull request, not on a
finished board.

There is currently one board: `canfuel/`.

---

## Current state — read this first

**Nothing has been designed yet.** The repo holds requirements and supporting
documents only. `canfuel/` contains `docs/` and an empty `fab/gerbers/`; there
is no `.kicad_pro`, no `.kicad_sch` and no `.kicad_pcb`. `lib/` is empty.

The CI workflow is a working skeleton: it loops over `**/*.kicad_sch` and
`**/*.kicad_pcb`, finds nothing, and passes. The moment the first schematic
lands it starts running ERC and DRC for real, so expect CI to begin failing
usefully rather than staying green.

**KiCad is not installed on this machine** (checked for `kicad-cli.exe` under
Program Files). Installing KiCad 8 is the first prerequisite — `kicad-cli`
also needs to be on PATH to reproduce what CI does.

### Suggested order of work

1. Install KiCad 8, confirm `kicad-cli version` runs.
2. Create the project: `canfuel/canfuel.kicad_pro` plus an empty schematic and
   board. Commit that skeleton on its own so CI going live is a visible step.
3. Draw the schematic against the requirements below. The four things most
   worth double-checking, because they are the ones that quietly kill a board:
   MCP2562 VIO and STBY, no 120 Ω termination fitted, 33 pF crystal loading,
   and both Micro-Fit headers wired in parallel.
4. `kicad-cli sch erc` until clean.
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

- Exact 4-pin connector choice at GME for the car side of the harness.
- Mechanical drawing of the enclosure and how the board mounts in the air vent.
  `canfuel/docs/` has no `mechanical.md` yet.
- Whether the unused-pin escape header ends up worth the board area.

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

Supporting documents: `canfuel/docs/bom-purchase.pdf`,
`canfuel/docs/harness.md`, `canfuel/docs/crystal-datasheet.pdf`.

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
