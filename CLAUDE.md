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

**The board is finished and `fab/` is generated. ERC, DRC, `check-netlist.py`
and `check-placement.py` are all clean, with zero unconnected items.**
`canfuel/` holds `canfuel.kicad_pro`, `canfuel.kicad_sch` (complete, one A3
sheet) and `canfuel.kicad_pcb` (55 × 45 mm, 24 parts, routed on two layers with
SGND poured on both), plus `docs/` and a populated `fab/`. `lib/` is empty.

**The escape header J4 was removed on 2026-08-09** and the board is 24 parts,
not 25. It is not an oversight — see below before reinstating it.

**The board is ordered. `fab/` is generated and committed — plan section 6 is
done.** `canfuel/fab/` holds nine gerbers, `canfuel-PTH.drl` and
`canfuel-NPTH.drl` with their maps, a `.gbrjob`, `canfuel-bom.csv` and
`canfuel-cpl.csv`. Plan §6 lists every command with the flags actually used and
why each one is there; do not regenerate from the bare `kicad-cli` invocations,
because the defaults are wrong for this board in five places. Section 7, the
purchase list, was done earlier: all parts are bought, the harness fuse and its
holder included. There are no open questions left anywhere in the project.

**Ordered from Gatema PCB on 2026-08-09** — POOL service, 3 pieces, 900 CZK
before VAT, five working days quoted. Their form was misbehaving over the
weekend, so the order was submitted but not yet confirmed; confirmation was
expected Monday 2026-08-10 and delivery in the week after. Plan §6.1 has the
full capability comparison and the exact stack-up ordered. **Nothing in this
repository should change while that order is in flight** — the boards being
made are commit `c06e710`, and an edit now makes `fab/` stop describing them.

**Two things are outstanding on the parts side, and neither blocks the boards:**
two more Molex 43045-0400 (GME 899-192) are needed to populate all three, since
the GME invoice of 2026-08-03 covers four and each board takes two; and the
number of PIC18F25K80 in the drawer has never been recorded anywhere.

**The silkscreen was sized for no process at all until 2026-08-09.** All 25
items were 0.80 mm high with a 0.12 mm stroke; the first fab house looked at,
printed.cz, asks for 1.0 mm and 0.15 mm. They are all 1.0 / 0.15 now, which is
what the project's own `silk_text_*` defaults had always said. `min_text_height`
and `min_text_thickness` were 0.8 and 0.08 — looser than the process, so the
board passed its own rules while failing the fab's — and are now 1.0 and 0.15.

**Tightening the numbers alone would have achieved nothing, and that was
measured.** `text_height` and `text_thickness` ship as *warnings*, and
`kicad-cli pcb drc --exit-code-violations` exits **0** on warnings: with the new
limits and the old 0.80 mm text the report listed all 50 violations and the
command still succeeded. Both are `error` now; the same board then exits 5. Do
not lower them back to warning — that is the third time this repository has
found a check that could not fail, after the globstar bug and the empty-file
list. `silk_overlap`, `silk_over_copper` and `silk_edge_clearance` are still
warnings and still toothless; the board is clean under them at `error`, so
promoting them is free whenever someone wants to. Plan §6.1 has the whole
comparison against printed.cz, including the one number with no margin: the via
annular ring is 0.15 mm, exactly their published minimum.

**The `120R DNF` silkscreen legend was missing until 2026-08-09** and the plan
§6 pre-order check is what found it. R5 is the 120 Ω termination that must
**not** be fitted, and it has a footprint, pads and a value like any other part
— the legend is the only thing on the board that says so. Moving value fields
to F.Fab in the escape-header pass had quietly taken it away, and nothing else
would have caught it: ERC, DRC, `check-netlist.py` and `check-placement.py` are
all indifferent to silkscreen. It is now a board-level `gr_text` at
(93.2, 91.5) rather than a footprint field, so a future change to how fields
are placed cannot take it a second time. Do not delete it.

**The drilling ships as two files, `canfuel-PTH.drl` and `canfuel-NPTH.drl`,
and that is deliberate.** A merged `MixedPlating` Excellon was produced first
and tags every tool correctly, so on paper it loses nothing. But J1/J2 are held
by a split plastic peg in a 3.00 ±0.05 mm hole, and a peg hole plated by
mistake comes out at about 2.90 mm — under Molex's minimum, and the housing
cracks when it is forced. Two files whose names say what they are cannot be
misread. Plan §3.7 has the datasheet numbers and §6.1 the wording to send with
the order. **The order must also say the diameters are finished sizes, not
drill sizes** — Gatema assumes that by default, but 1.02 mm is the one hole
that cannot absorb the error.

**Regenerating `fab/` is cheap and it is the rule after any board change.** The
silkscreen resize proved the point: only `canfuel-F_Silkscreen.gto` and
`canfuel-B_Silkscreen.gbo` changed substantively, everything else differed by
its timestamp line alone — so a stale `fab/` next to an edited board is never
worth the risk of guessing which files matter.

**R1 moved 1.20 mm on 2026-08-09**, after the paper mock-up showed its lead
almost touching C8's. Those two pads are the opposite ends of JP2, so a bridge
would have held the jumper closed for good. Do not move it back — the reasoning
and the widened `ALLOW` entry are below and in plan §5.2a.

**The 5 V feed is fused, in the harness.** SIBA 179120.0.2, 200 mA time-lag T,
in inline holder K23411. It is not on the PCB and there is no F1 on the
schematic; plan §9.2 has the measurement that decided it and `harness.md`
section B has the wiring.

CI is live and green: it finds both files and runs ERC and DRC on them for
real, and since 2026-08-09 it also runs `check-netlist.py` and
`check-placement.py`. From here on a red run means something.

**The schematic was re-reviewed against the datasheets on 2026-08-08** and
three things changed. Do not undo them without reading plan §3.6, §3.2 and
§4.3a first:

- **The LEDs moved from RA1/RA2 to RC0/RC1.** RA1 and RA2 are inside
  PORTA<5:0>, whose absolute maximum is 2 mA sourced or sunk; 1 kΩ from a 5 V
  rail is about 2.2 mA. RA1/RA2 took the escape-header slots RC0/RC1 vacated —
  and when the header itself went, all fourteen of those pins became
  no-connects.
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

**The fix left the same bug wearing the opposite mask, and that is fixed too
(2026-08-09).** The repaired steps printed "no schematic in the repo, skipping"
and *passed* on an empty list. Green would then have meant "checked and clean"
or "found nothing at all", with no way to tell the two apart — which is exactly
the failure the globstar bug taught. Finding zero files is now an error. This
repository will never again be without design files, so a run that opens none
of them is broken, not lucky.

**Reading CI without `gh`:** it is not installed here, but the public REST API
needs no token for run status. `curl -s
https://api.github.com/repos/PoJD/kicad/actions/runs?per_page=3` gives
`head_sha`, `status` and `conclusion`, and `.../actions/runs/<id>/jobs` gives
per-step conclusions. Log *bodies* are a 403 without auth, so verify by
reasoning about the step definitions rather than expecting to read the output.

**ERC is not enough on its own, so there is a second check.** Run it after any
edit to the schematic:

```
python tools/check-netlist.py
```

It exports the netlist and compares all 87 connections against the tables in
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

**The board has the same problem and the same answer.** Run after any edit to
the placement:

```
python tools/check-placement.py
```

DRC proves the board is manufacturable; it does not care where a decoupling
capacitor sits. A part 40 mm from its pin is a legal board and a broken one.
This measures the four DS39977C distance rules and the mounting-hole keepouts,
and carries the tolerated §2.3 shortfalls with their reasons, so an intentional
deviation and a regression never look the same.

**`kicad-cli` cannot sync the board against the sheet** — `kicad-cli pcb`
offers only drc, export, import, render and upgrade, and none of them is
*Update PCB from Schematic*. `python tools/import-footprints.py` does it
headlessly: loads footprints, links them to their symbols by KIID path, assigns
every pad's net. It is safe to re-run — existing parts keep their position,
orientation and side, so hand placement survives.

Both scripts need `pcbnew`, which the stock Windows Python cannot import; they
re-run themselves under KiCad's bundled interpreter, so `python tools/...`
works either way.

**KiCad 10.0.5 is installed** at `C:\Program Files\KiCad\10.0`, and
`C:\Program Files\KiCad\10.0\bin\` is on the user PATH. A shell started before
that PATH edit will not see `kicad-cli`; call it by full path rather than
concluding it is missing.

### Resume here — next session

**The design is finished, `fab/` is finished, and the boards are ordered.**
Net classes, placement, routing, pours, silkscreen and the fabrication outputs
are all done and committed, every check is green, all parts are bought and there
is not one open question left. Do not go looking for design work to do — there
is none.

**The next thing that happens is three bare boards arriving**, not another
edit. Until they do and have been looked at, the useful work is off this
repository: the loom (`canfuel/docs/harness.md` is a build document now), the
two missing Micro-Fit headers, and the firmware in the sibling `canfuel` repo.
**Do not touch the design while the order is in flight** — what is being
manufactured is `c06e710`, and changing the board now makes `fab/` describe
something that does not exist.

If anything is regenerated anyway, re-run all four checks first and re-read
plan §6 for the exact export commands — they are cheap and they are what stands
between a mistake and an ordered board:

```
python tools/check-netlist.py
python tools/check-placement.py
kicad-cli sch erc --exit-code-violations canfuel/canfuel.kicad_sch
kicad-cli pcb drc --exit-code-violations canfuel/canfuel.kicad_pcb
```

The older step-by-step notes below still apply if any of that has to be redone:

1. **Read `canfuel/docs/implementation-plan.md` first.** It is the working
   document: reference designators, the full 28-pin PIC pinout, net names, net
   classes, the placement as built and the order of commits. This file only
   summarises it.
2. **Check the prerequisites hold**: `kicad-cli version` prints `10.x`,
   `python tools/check-netlist.py` and `python tools/check-placement.py` are
   clean, `kicad-cli pcb drc` reports zero violations.
3. **Route.** The layer split is in plan 5.3 and is not arbitrary — read it
   before laying the first track.
4. **`kicad-cli pcb drc` and `check-placement.py` until both are clean**, then
   commit.
5. Then `fab/` — plan section 6. Section 7, the purchase list, is already done.

**The four numeric constraints are met and are now machine-checked.** Do not
re-derive them by hand; run `python tools/check-placement.py`, which measures
all of them and prints what it measured:

| Within | What | Section | As built |
| ------ | ---- | ------- | -------- |
| 6 mm   | C7 to U1 pin 6, on B.Cu across the package | 2.4 | 2.25 mm |
| 6 mm   | C3/C4/C5 to U1 pin 20, U2 pin 3, U2 pin 5 | 2.2.1 | 5.67 / 5.68 / 4.49 mm |
| 6 mm   | R1, R6, C8, JP2 to U1 pin 1 | 2.3 | **partly — see below** |
| — | no foreign traces in the oscillator guard, none on B.Cu under the crystal | 2.6 | enforced and re-checked |
| 12 mm  | Y1, C1, C2 to their own oscillator pins | 2.6 | 5.35 / 9.79 / 6.98 mm |

**§2.3 cannot be met in full and the shortfall is deliberate.** Four parts
totalling 71 mm² of courtyard do not fit in the ~85 mm² of free area around a
corner pin, whatever footprints are chosen. Rather than get one part wholly
inside, all four hug the pin: nearest edges 1.66 mm (C8), 1.88 mm (JP2),
2.46 mm (R6) and 2.89 mm (R1), worst far corner 8.91 mm. The arrangement was
found by search, not by hand.

**R1 was moved 1.20 mm further out on 2026-08-09, deliberately.** The search
optimised for closeness to pin 1 and left R1's courtyard touching C8's, with
only 1.06 mm of bare board between R1 pad 2 and C8 pad 1 — and those two pads
are `MCLR_RC` and `MCLR_C`, the two ends of JP2. A bridge there would hold the
jumper closed for good, which is exactly what it exists to prevent. The gap is
now 2.26 mm, R1's nearest edge 2.89 mm (the 3 mm rule sized the move) and its
`ALLOW` far corner 8.5 → 9.0. Plan §5.2a has the full account and the two
re-laid tracks.

`tools/check-placement.py` holds the tolerated far corners in `ALLOW` with
their reasons, and asserts every nearest edge stays within 3 mm — that second
check is the one that matters. **If it goes red, something moved. Do not widen
either number to make it green again** — a deliberate move like R1's above is
widened in the same commit that moves the part, with the reason next to the
number, so the two never look alike.

**Two readings of the datasheet matter here.** §2.2.1 and §2.4 limit the *trace
length from pin to capacitor*; §2.3 and §2.6 limit where the *component is
placed*. Different measurements, and the difference is what decides this board.
§2.6 also says "the **respective** oscillator pins", so C1 is measured against
OSC1 and C2 against OSC2.

**R1–R6 stand upright** (`P2.54mm_Vertical`), changed from horizontal
P10.16 mm on 2026-08-09. That is how the maintainer fits axial resistors —
body upright, leads bent to the narrowest spacing — and it is also the only
reason R6 fits inside the 6 mm circle: 3.95 mm reach standing against 11.36 mm
lying down. Do not quietly revert them to horizontal.

### Working with the tools here

**Run the checks without asking.** `.claude/settings.local.json` keeps
`defaultMode: "default"` and an explicit `allow` list covering `python`,
`kicad-cli` (bare and by full path), `pdftotext` and the read-only git and
shell commands, under both `Bash(...)` and `PowerShell(...)`. ERC, DRC,
`check-netlist.py` and an SVG render are meant to be run freely and often —
stopping to ask permission for a verification step is how verification stops
happening. Verified working on 2026-08-09: all four checks run unprompted.

**`git commit`, `git push`, `gh pr create`, `git rebase` and `git reset --hard`
still stop and ask**, by `ask` rules in the same file. Those are the ones that
leave the machine or throw work away. Everything else does not.

**`defaultMode: "dontAsk"` was tried and is worse than it looks — do not put it
back.** It does not widen the `allow` list, and with a list this narrow the
result was that unmatched commands were silently rejected instead of prompting.
A prompt tells you a rule is missing; a silent rejection just looks like the
tool failing, and a whole session went that way before anyone worked out why.

Grow the `allow` list one entry at a time instead. Prefix rules match the start
of a command, so compound invocations — `SP="..."; cd "$SP" && kicad-cli ... &&
python - <<'EOF'` — are not covered by `Bash(python:*)` and will prompt. The
fix is to keep commands short and single-purpose, one tool per call, not to
broaden the mode.

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
5. ~~Lay out the PCB inside ~55 × 45 mm, two layers, mostly through-hole.~~
   Done — 24 parts, routed, poured.
6. ~~`kicad-cli pcb drc` until clean.~~ Done, zero violations.
7. ~~Generate `fab/` (gerbers, BOM, CPL) and commit it.~~ Done — plan §6 has
   the commands and the pre-order checks.
8. ~~Only then assemble the GME purchase list.~~ Done — everything is bought.
   The rule it came from still stands for any future board: the BOM falls out
   of the schematic, so buying earlier means buying twice.
9. ~~Order the boards.~~ Done — Gatema PCB, 2026-08-09, 3 pieces.
   ← **next: the boards arrive and get built**

### Decisions already made

Everything in the requirements section below is settled and measured, not
provisional. In particular the power supply (5 V from display connector C6/C12)
was verified with a multimeter, and the CAN pinout (C7/C8) is confirmed.

### Still open

**Nothing.** The last one was the 4-pin connector for the car side of the
harness, and it is settled: the connector exists and is already fitted, so the
loom is a re-crimp onto longer wires, not a new choice. Everything else was
closed before that: **the escape header came off again** (measured, see below), there is no
enclosure, and C6 turned out to be a 105 °C part with life to spare (plan §7).

### The escape header was removed — do not put it back

It was fitted, and on 2026-08-09 routing showed what it actually cost. Same
router, same placement, same order, with and against:

| | with J4 | without J4 |
| --- | --- | --- |
| connections to route | 39 | 25 |
| **left unroutable** | **8** | **0** |
| DRC | incomplete | **0 violations** |

**Five of those eight failures were not escape signals** — both status LEDs and
the whole ICSP header. J4's fourteen signals congest the channel between U1's
pin rows, which is the only way across a 55 × 45 mm board, and ICSP is what
starves. A header that exists to rescue a design error was stopping the chip
being programmed.

Patching now goes onto the **PDIP socket pins from underneath**; they are
through-hole and reachable, so the escape route survives without the header.

The freed column was inside the 6 mm circle of DS39977C §2.3, so the MCLR
cluster was re-placed into it — worst far corner 10.68 mm → 8.67 mm. Plan §5.4
has the full account.

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
  those pins. It is why the LEDs are on RC0/RC1. The DC characteristics table
  looks like it permits 3 mA; absolute maximums win.
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
- **The 5 V feed is fused, but the fuse is in the harness, not on this board** —
  SIBA 179120.0.2, 200 mA time-lag T, in inline holder K23411. No 5 × 20 holder
  fits on a finished 55 × 45 mm board; plan §9.2 has the free-area measurement
  and `harness.md` section B has the wiring. Nothing about the PCB changes
  because of it.
- Average draw is under 30 mA and the display's limit is 0.5 A — but the
  transceiver alone takes 45 mA typical and 70 mA maximum while it is driving
  a dominant bit (DS20005167C §2.2), so the worst-case instantaneous total is
  about 77 mA. C6 and C7 carry those peaks, which is what lets a fuse with
  2.5 Ω of hot element sit in the feed at all.
- Decoupling: 100 nF at every supply pin, 10 µF at the input. **C6 is
  downstream of the harness fuse** and that is load-bearing, not incidental.

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
- **Escape hatch:** ~~bring the PIC's unused pins out to a 2.54 mm header~~
  **Removed 2026-08-09.** The 2×8 header made both status LEDs and the whole
  ICSP connector unroutable on a board this size; see "The escape header was
  removed" above. The PIC's fourteen unused pins carry no-connect flags, and a
  patch goes onto the PDIP socket pins from underneath instead.
- **Dimensions:** 55 × 45 mm, **1.5 mm thick**, two layers, mostly through-hole.
  It was 1.6 mm until 2026-08-09 and changed only because Gatema's POOL service
  sells fixed stack-ups and every two-layer one is 1.5 mm. Nothing electrical
  or mechanical depends on it — plan §6.1 has the check. The thickness lives in
  `(general (thickness))` at the top of `canfuel.kicad_pcb`, **not** in the
  stackup sum: editing the core alone leaves `GetBoardThickness()` unchanged
  and the `.gbrjob` still declaring the old number. Four M3 holes
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
- `harness.md` — building the loom. The measuring and sniffing steps were
  stripped out on 2026-08-09 once they had all been done; it is a build
  document now, not a test plan.
- `pic18f25k80-datasheet.pdf` — Microchip DS39977C, PIC18F66K80 family
- `mcp2562-datasheet.pdf` — Microchip DS20005167C, MCP2561/2
- `micro-fit-43045-datasheet.pdf` — Molex SD-43045-001, J1/J2. Beware: the text
  is converted to outlines, so `pdftotext` returns nothing at all and no switch
  helps. It has to be read as an image, and nothing on this machine can render
  a PDF — no `pdftoppm`, no Ghostscript, and headless Chrome returns a blank
  page. Ask the maintainer for a screenshot; that is how the numbers in plan
  §3.7 were read.
- `hitano-exr-datasheet.pdf` — Hitano EXR electrolytics, C6
- `crystal-datasheet.pdf` — HC-49U/S DIP quartz crystal resonator, supplied
- `siba-179120-fuse-datasheet.pdf` — SIBA 179120, 5 × 20 glass time-lag fuses,
  the harness fuse. Beware: `pdftotext -layout` shifts its parameter table by
  one row, because it pulls the mV/W/A²s unit header into the first data row.
  `-table` and `-raw` agree with each other and are right. The 200 mA row is
  500 mV, 0.3 W, 0.7 A²s.
- `fuse-holder-5x20-datasheet.pdf` — inline holder K23411, a dimensioned
  drawing with no text layer and no ratings on it
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
