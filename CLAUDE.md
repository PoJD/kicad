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

There is currently one board: `canfuel/`. Before changing anything electrical,
read **Sourcing hardware facts** below — it governs where every number in this
repository is allowed to come from.

---

## Sourcing hardware facts — manufacturer datasheets only

**Every hardware fact in this repository comes from the manufacturer's
datasheet for the exact part, and from nothing else.** Not forum posts, not
application notes summarised from memory, not "this is what everyone fits", not
a value that worked on a previous project, and not the recollection of whoever
is at the keyboard — including the model's.

When the datasheet does not settle a question, **ask the maintainer**. Do not
fill the gap with a plausible number and move on. A guess that looks like a
specification is worse than an open question, because the next person cannot
tell the two apart.

In practice this means:

- **Quote the source.** Every constraint written into the plan or the schematic
  notes names its document and section — `DS39977C §2.4`, `DS20005167C §1.7.9`.
  A number without a citation is a number nobody can re-check.
- **Keep the datasheet in the repository.** `canfuel/docs/` holds a PDF for
  every active part. If a part has no datasheet on disk, that is the first
  thing to fix, not a detail to note.
- **A conclusion and its justification are checked separately.** A right value
  can rest on a wrong reason, and then it stops being right the moment anything
  around it changes. The 33 pF crystal capacitors were exactly this case: the
  value survived re-derivation, the stated load capacitance did not.
- **Absolute Maximum Ratings outrank the DC characteristics tables**, and both
  outrank what a part is observed to tolerate. A design that works on the bench
  outside absolute maximums is still a broken design.
- **Where the datasheet is deliberately not followed**, say so and say why, in
  the plan, next to the citation. An unexplained deviation is indistinguishable
  from an oversight six months later.

Facts about the *car* — the display's connector pinout, that the bus is already
terminated — are not datasheet questions and are settled by measurement instead.
Those are marked as measured where they appear. The rule above is about parts.

---

## Current state — read this first

**The schematic is finished, checked against the datasheets and ERC clean. The
PCB is an outline with four mounting holes and no footprints placed. Nothing
blocks the layout.** `canfuel/` holds `canfuel.kicad_pro`, `canfuel.kicad_sch`
(complete, one A3 sheet) and `canfuel.kicad_pcb` (55 × 45 mm outline, H1–H4),
plus `docs/` and an empty `fab/gerbers/`. `lib/` is empty.

**All parts are bought.** Nothing is on order and nothing is outstanding.

CI is live and green: it finds both files and runs ERC and DRC on them for
real. From here on a red run means something.

**The schematic was re-reviewed against the datasheets on 2026-08-08** and
three things changed. Do not undo them without reading plan §3.6, §3.2 and
§4.3a first:

- **The LEDs moved from RA1/RA2 to RC0/RC1.** RA1 and RA2 are inside
  PORTA<5:0>, whose absolute maximum is 2 mA sourced or sunk; 1 kΩ from a 5 V
  rail is about 2.2 mA. RA1/RA2 took the escape-header slots RC0/RC1 vacated.
- **MCLR gained R6 470 Ω, C8 100 nF and jumper JP2** — the full Figure 2-2
  network. The old note "no capacitor on this pin" was §2.5 (which is about
  PGC and PGD) misapplied to MCLR.
- **The crystal's load capacitance is 20 pF, not 32 pF.** The 33 pF capacitors
  were right; the reason recorded for them was not, and 32 pF would have
  called for 56 pF.

The MCP2562 had no datasheet in the repository at all until then. It does now.

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

It exports the netlist and compares all 103 connections against the tables in
`canfuel/docs/implementation-plan.md`, which are transcribed into the script.
Not a formality: swapping the labels on U1 pins 23 and 24 — CANTX and CANRX
crossed at the MCU, a board that would never transmit — passes ERC with
**zero** violations, because both are bidirectional pins and nothing about the
sheet is malformed. `check-netlist.py` catches it. That case was tried, not
assumed.

It carries a second load too. This sheet connects everything by global label
and has ERC's *Global label only appears once in the schematic* check switched
off, so a mistyped label would quietly split a net in two without a violation.
`check-netlist.py` is what would catch that.

When the design changes on purpose, update `EXPECT` in the script in the same
commit. That is what the file is for.

**KiCad 10.0.5 is installed** at `C:\Program Files\KiCad\10.0`, and
`C:\Program Files\KiCad\10.0\bin\` is on the user PATH. A shell started before
that PATH edit will not see `kicad-cli`; call it by full path rather than
concluding it is missing.

### Resume here — next session

**Next up is the PCB layout, section 5 of the plan. Nothing blocks it.** The
enclosure used to, and there is no longer going to be one — see plan §9.1 for
why, and do not reopen it. The four M3 holes are in the board, they answer to
nothing but themselves, and whatever the board ends up mounted on is designed
around them.

In order:

1. **Read `canfuel/docs/implementation-plan.md` first.** It is the working
   document: reference designators, the full 28-pin PIC pinout, net names, net
   classes, placement plan and the order of commits. This file only summarises
   it.
2. **Check the prerequisites hold**: `kicad-cli version` prints `10.x`, the
   three `canfuel/canfuel.*` files are present, `python tools/check-netlist.py`
   is clean, `kicad-cli pcb drc` is clean.
3. **Net classes first** (plan 5.3), then **placement** (5.2), then routing.
4. **`kicad-cli pcb drc` until clean**, then commit.
5. Then `fab/` and the purchase list — plan sections 6 and 7.

**Placement has four numeric constraints, not one**, and they are the part of
5.2 worth reading twice. All four come from DS39977C:

| Within | What | Section |
| ------ | ---- | ------- |
| 6 mm   | C7 to U1 pin 6 — put it on B.Cu directly under the pin | 2.4 |
| 6 mm   | C3 to U1 pin 20, C4 to U2 pin 3, C5 to U2 pin 5 | 2.2.1 |
| 6 mm   | R1, R6, C8 and JP2 to U1 pin 1 — four parts, the tightest cluster | 2.3 |
| 12 mm  | Y1, C1, C2 to U1 pins 9/10, with a grounded pour around them and nothing on the far side under the crystal | 2.6 |

Do the pin-1 cluster before the escape header, not after — it is the one that
runs out of room.

### Working with the tools here

**Run the checks without asking.** `.claude/settings.local.json` sets
`defaultMode: "dontAsk"`, so `python`, `kicad-cli`, `pdftotext`, headless
Chrome renders and the ordinary shell tools all run unprompted. ERC, DRC,
`check-netlist.py` and an SVG render are meant to be run freely and often —
stopping to ask permission for a verification step is how verification stops
happening.

**`git commit`, `git push`, `gh pr create`, `git rebase` and `git reset --hard`
still stop and ask**, by `ask` rules in the same file. Those are the ones that
leave the machine or throw work away. Everything else does not.

An allowlist of command prefixes was tried first and did not work, for a reason
worth knowing: prefix rules match the start of a command, and most real
invocations here are compound — `SP="..."; cd "$SP" && kicad-cli ... && python
- <<'EOF'`. The variable assignment, the `cd` and the heredoc are not covered
by `Bash(python:*)`, so every new shape prompted anyway. Keeping commands
short and single-purpose helps, but the mode is what actually fixed it.

The file is gitignored, so it is per-machine and none of this is imposed on
anyone else.

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
3. ~~Draw the schematic against the requirements below. The things most worth
   double-checking, because they are the ones that quietly kill a board:
   MCP2562 VIO and STBY, no 120 Ω termination fitted, 33 pF crystal loading,
   both Micro-Fit headers wired in parallel, 10 µF on VDDCORE/VCAP, and the
   LEDs off port A.~~ Done — all of them are on the sheet and repeated in its
   notes panel.
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

- Exact 4-pin connector choice at GME for the car side of the harness. Affects
  the loom only, not this board.

**That is the only one, and it is not about this board.** Everything else is
closed: the escape header goes on (a 2×8 costs about 4 % of the board area),
there is no enclosure, and C6 turned out to be a 105 °C part with life to spare
(plan §7).

### The enclosure was dropped — do not reopen it

Everything around the board in the vent is plastic, so there is nothing to
short against. The vent is closed off by a flap, so no airflow, no meaningful
dust and no water. The board is invisible either way. A box was buying nothing
but mechanical retention, which standoffs buy better.

The space could never be measured properly anyway — the MFD15 is in the way —
and the closest off-the-shelf candidate came out exactly at the estimate on two
axes and 0.1 mm over on the third. Plan §9.1 has the full reasoning.

**Mounting instead:** four nylon M3 standoffs in H1–H4, feet stuck to the floor
of the vent with automotive-grade double-sided tape (3M VHB or equivalent).
Standoffs because the through-hole solder joints must not bear on anything;
VHB because a dashboard reaches 50–60 °C and cheap foam tape lets go there.
**Not** PVC or Tesa tape wrapped round the board — at those temperatures the
adhesive creeps across the board and into the sockets.

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
- 16 MHz crystal, load capacitance **20 pF** (crystal datasheet: 20 pF standard,
  8–33 pF available) → fit **33 pF**, not 22 pF. `C = 2·(CL − Cstray)` with
  about 5 pF of stray gives 30 pF, and 33 pF is the nearest E12 value. No
  series resistor on OSC2. Plan §3.2 has the working.
- ⚠ **Pin 6 is VDDCORE/VCAP, not a port pin** — the 28-pin K80 has no RA4 and
  no ENVREG. The core regulator is permanently enabled on the F (not LF) part
  and needs **10 µF low-ESR to ground within 6 mm of pin 6**. Never tie pin 6
  to VDD. Datasheet DS39977C §2.4 and Table 31-4.
- ⚠ **RA0–RA3 and RA5 can only take 2 mA**, sourced or sunk — DS39977C page
  541, against 25 mA for port B and port C. Nothing that draws current goes on
  those pins. It is why the LEDs are on RC0/RC1 and why the escape header
  labels the port A pins as weak. The DC characteristics table looks like it
  permits 3 mA; absolute maximums win.
- **MCLR** carries the full network of DS39977C Figure 2-2: R1 10 kΩ to +5V,
  R6 470 Ω in series into pin 1, C8 100 nF to ground behind jumper **JP2**.
  JP2 comes off before programming and goes back after — the datasheet asks
  for the capacitor in §2.3 and for the jumper in the same paragraph.

### Transceiver

- **MCP2562-E/P** in a DIP-8 socket.
- ⚠ **Pin VIO to VDD, pin STBY to ground.** Otherwise it stays in standby and
  transmits nothing. This is the easiest mistake to make in the whole design.
  STBY is not neutral when floating: DS20005167C §1.7.9 gives it an internal
  pull-up to VIO, typically 660 kΩ at 5 V, so an unconnected pin 8 reads high
  and §1.1.2 puts the transmitter to sleep. Tie it hard — no pull-down
  resistor that assembly could omit.

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

- **LEDs:** two (power, CAN status) on **RC0 and RC1** through 1 kΩ, active only
  when the debug jumper on RA0 is fitted. Nothing lights up in the car. They
  are on port C rather than port A because of the 2 mA limit above — do not
  move them back.
- **ICSP:** 5-pin 2.54 mm header for a PICkit.
- **Escape hatch:** bring the PIC's unused pins out to a 2.54 mm header so a
  design error can be patched with a wire. RA1, RA2, RA3 and RA5 are on it and
  are the weak 2 mA pins; the silkscreen has to say so.
- **Dimensions:** 55 × 45 mm, two layers, mostly through-hole. Four M3 holes
  4 mm in from the edges, on a 47 × 37 mm pattern. Space available in the vent
  is roughly 6.5 × 5.5 cm; the depth was never measurable because the MFD15 is
  in the way, which is part of why there is no enclosure.

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

- **From the drawer:** PIC18F25K80, the resistors and the LEDs. None of the
  three degrades in dry storage. Meter the resistors before fitting and the
  question is closed — R1 and R6 are current-limiting, not precision, so a few
  percent of drift would not matter even if it existed.
- **New:** crystal, all capacitors, connectors, sockets. The electrolytic ages
  unpowered because its oxide layer does; the crystal because an unmarked part
  has an unknown load capacitance, and that value sets C1/C2 (§3.2 of the plan).
  Those two reasons do not generalise to passives that have neither an
  electrolyte nor a hidden parameter.
- **New purchase:** MCP2562-E/P, and **C7 = Murata GRM32DR71C106KA01L**,
  10 µF X7R 16 V in 1210. That is one of the four parts Microchip lists in
  DS39977C Table 2-1, so nothing about it needs arguing. It is the only SMD
  component on the board and goes on the bottom layer under pin 6. The
  aluminium electrolytic bought for C6 is **not** a substitute — §2.4 allows
  ceramic or tantalum and nothing else — and a dipped tantalum was rejected
  because its datasheet specifies no high-frequency ESR (plan §3.5).

**LED colour is free, within reason.** D1/D2 run off port C through 1 kΩ, so
at Vf ≈ 2 V they draw about 2.3 mA and at Vf ≈ 3.2 V (blue, white, true green)
about 1.1 mA. Both sit far under the 25 mA limit, so any colour is electrically
fine and only brightness changes. Whatever gets fitted, put it in the symbol's
Value field — the BOM is generated from the schematic, so a wrong colour there
becomes a wrong colour in `fab/`.

Supporting documents in `canfuel/docs/`:

- `implementation-plan.md` — the working document for the design
- `harness.md` — building and testing the loom
- `pic18f25k80-datasheet.pdf` — Microchip DS39977C, PIC18F66K80 family
- `mcp2562-datasheet.pdf` — Microchip DS20005167C, MCP2561/2
- `hitano-exr-datasheet.pdf` — Hitano EXR electrolytics, C6
- `crystal-datasheet.pdf` — HC-49U/S DIP quartz crystal resonator, supplied
- `bom-purchase.pdf` — supplied PDF

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
