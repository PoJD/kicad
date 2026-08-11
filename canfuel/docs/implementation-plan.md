# canfuel — implementation plan

How to get from an empty repository to an ordered board. The requirements in
the root `CLAUDE.md` are the input and are treated as settled; this document
turns them into reference designators, nets and pin numbers.

Read the killer checks in section 3 before drawing anything.

**This is a design reference, not a progress tracker.** What is left to do in
the project as a whole, and where this car has got to, lives in one place:
[`canfuel/docs/install.md`](https://github.com/PoJD/canfuel/blob/main/docs/install.md).

> ⚠ **This document was written before the board was drawn, and the board is
> now made.** Most of it is still the reference — the pin table in 4.2, the
> footprints in 4.7, the fab commands in 6 — but where the design moved after
> the plan was written, the plan has been corrected in place rather than
> rewritten, with the old text quoted and dated so a decision cannot be mistaken
> for an oversight.
>
> **The big one is the escape header J4**, removed on 2026-08-09 because routing
> put a number on what it cost: eight unroutable connections, five of them
> nothing to do with the escape signals. Section 5.4 is the full account, and
> `canfuel/docs/refuted.md` entry D1 is the short one. Fourteen pins that this
> document originally sent to J4 now go **nowhere**, and driving them low is a
> firmware obligation — see 3.6.
>
> `canfuel/docs/refuted.md` collects every idea in this project that was
> believed and turned out wrong, across all three repositories.

**Every electrical number below is cited to a manufacturer datasheet**, per the
sourcing rule in `CLAUDE.md`. The three documents are in `docs/`:

| Short form   | Document                                              |
| ------------ | ----------------------------------------------------- |
| `DS39977C`   | Microchip, PIC18F66K80 family — `pic18f25k80-datasheet.pdf` |
| `DS20005167C`| Microchip, MCP2561/2 — `mcp2562-datasheet.pdf`        |
| crystal d/s  | HC-49U/S DIP quartz crystal resonator — `crystal-datasheet.pdf` |
| Hitano EXR   | C6's electrolytic — `hitano-exr-datasheet.pdf`        |

Section 10 lists what has actually been read out of them, so the next person
can tell a checked number from an inherited one.

---

## 0. Prerequisites — done

- [x] **KiCad 10.0.5** installed to `C:\Program Files\KiCad\10.0`. The GUI,
      `kicad-cli.exe` and the standard symbol/footprint libraries all come from
      the one installer; there is no separate CLI download.
- [x] **`C:\Program Files\KiCad\10.0\bin\` added to the user PATH by hand.**
      The Windows installer does not do it (KiCad issue #19639), so without
      this `kicad-cli` only works inside the "KiCad Command Prompt" shortcut —
      fine interactively, useless for a script or a git hook. A shell that was
      already open when the PATH was edited still will not see it.
- [x] `kicad-cli version` prints `10.0.5`; `sch erc` and `pcb drc` both accept
      `--exit-code-violations`, which is what CI relies on.

**The major version is load-bearing.** KiCad cannot open files written by a
newer major version, so the CI image in `.github/workflows/kicad.yml` is pinned
to `kicad/kicad:10.0` to match. Upgrading one without the other breaks CI.

---

## 1. Project skeleton — done, its own commit

The project was created with the KiCad GUI (`File → New Project`) so the
generated files carry the correct schema versions; they are not hand-written.

```
canfuel/
  canfuel.kicad_pro
  canfuel.kicad_sch      empty
  canfuel.kicad_pcb      outline only
```

Board Setup, applied before any drawing:

| Setting              | Value                     | Where it lives                     |
| -------------------- | ------------------------- | ---------------------------------- |
| Layers               | 2 (F.Cu, B.Cu)            | `.kicad_pcb` `(layers)`            |
| Copper thickness     | 1 oz / 35 µm              | `.kicad_pcb` `(setup (stackup))`   |
| Board thickness      | 1.6 mm                    | `.kicad_pcb` `(general (thickness))` |
| Minimum track width  | 0.20 mm                   | `.kicad_pro` `design_settings.rules` |
| Minimum clearance    | 0.20 mm                   | same                               |
| Minimum via          | 0.6 mm pad / 0.3 mm drill | same                               |
| Minimum hole/annulus | 0.30 mm / 0.15 mm         | same                               |

**The board outline is in this commit too**, ahead of section 5.1. It has to
be: DRC reports `invalid_outline` as an error on a board with no Edge.Cuts
edges, so without it the skeleton commit could not be CI-green. It is the
settled 55 × 45 mm with R2 corners, origin at (50, 50) on the sheet. The four
M3 mounting holes went in later, once dropping the enclosure (section 9.1) made
their positions ours to choose.

**Definition of done:** CI green on a repository that contains an empty
schematic and a board that is an outline and nothing else. ✔

---

## 2. Parts and reference designators

> **Naming note.** The display's connector pins are called C6, C7, C8, C12 in
> the requirements. Capacitors on this board are also C-something. Below,
> connector pins are always written as **plug C pin 6**, never `C6`.

| Ref       | Part                        | Package / footprint                     | Note                                   |
| --------- | --------------------------- | --------------------------------------- | -------------------------------------- |
| U1        | PIC18F25K80                 | PDIP-28, **narrow 7.62 mm** socket      | from the drawer                        |
| U2        | MCP2562-E/P                 | DIP-8 socket                            | new purchase                           |
| Y1        | 16 MHz crystal, CL = 20 pF  | HC-49/S                                 | new; see 3.2                           |
| C1, C2    | 33 pF C0G                   | 2.54 mm THT                             | **33 pF, not 22 pF** — see 3.2         |
| C3        | 100 nF X7R                  | 2.54 mm THT                             | U1 VDD (pin 20)                        |
| C4        | 100 nF X7R                  | 2.54 mm THT                             | U2 VDD (pin 3)                         |
| C5        | 100 nF X7R                  | 2.54 mm THT                             | U2 VIO (pin 5)                         |
| C6        | 10 µF electrolytic, 16 V    | 5 mm THT radial                         | supply input; new part, they age       |
| C7        | 10 µF X7R, 16 V, **Murata GRM32DR71C106KA01L** | 1210 SMD                 | **mandatory** — U1 VDDCORE/VCAP, see 3.5 |
| C8        | 100 nF X7R                  | 2.54 mm THT                             | MCLR reset hold, behind JP2 — see 4.3a |
| R1        | 10 kΩ                       | 1/4 W THT                               | MCLR pull-up                           |
| R2        | 10 kΩ                       | 1/4 W THT                               | RA0 pull-down (debug jumper)           |
| R3, R4    | 1 kΩ                        | 1/4 W THT                               | LED series resistors — see 3.6         |
| R5        | 120 Ω                       | 1/4 W THT                               | **DO NOT FIT** — see 3.3               |
| R6        | 470 Ω                       | 1/4 W THT                               | MCLR series — see 4.3a                 |
| D1        | LED green                   | 3 mm THT                                | power / heartbeat                      |
| D2        | LED yellow                  | 3 mm THT                                | CAN status                             |
| J1, J2    | Molex Micro-Fit 3.0 43045-0400 | right-angle, board mount             | wired in parallel — see 3.4            |
| J3        | 5-pin header 2.54 mm        | 1×5                                     | ICSP                                   |
| ~~J4~~    | ~~2×8 header 2.54 mm~~      | —                                       | **removed 2026-08-09 — see 5.4**       |
| JP1       | 2-pin header + jumper       | 1×2                                     | debug enable on RA0                    |
| JP2       | 2-pin header + jumper       | 1×2                                     | isolates C8 for programming — see 4.3a |
| —         | DIP-28 socket, narrow       |                                         | new                                    |
| —         | DIP-8 socket                |                                         | new                                    |

---

## 3. The things that quietly kill this board

Check each one twice while drawing, and again during the ERC pass. All of them
are now on the sheet as drawn, and all of them are repeated as numbered notes
in the schematic's own notes panel so they survive without this file.

### 3.1 MCP2562 VIO and STBY

The single easiest mistake in the design. Without these the transceiver sits in
standby and transmits nothing, while everything else measures fine.

**STBY floating is not neutral — it is Standby.** DS20005167C section 1.7.9:
STBY carries an internal MOS pull-up to VIO, typically 660 kΩ at 5 V. An
unconnected pin 8 therefore reads high, and section 1.1.2 says a high on STBY
switches the transmitter off. That is why pin 8 is tied hard to SGND rather
than left to a resistor or a jumper that assembly could skip.

The datasheet's own application circuit (Figure 1-2) drives STBY from an MCU
pin instead, which buys a low-power standby mode. **We deliberately do not**:
the board is powered only while the display is, and total draw is under 30 mA
against a 0.5 A budget, so standby is worth nothing here and a hard ground
removes a whole class of failure.

MCP2562 DIP-8 pinout, from DS20005167C page 1 (package types) and Table 1-2:

| Pin | Name | Connect to                        |
| --- | ---- | --------------------------------- |
| 1   | TXD  | U1 RB2 (CANTX), pin 23            |
| 2   | VSS  | SGND                              |
| 3   | VDD  | +5V (with C4 across pins 3–2)     |
| 4   | RXD  | U1 RB3 (CANRX), pin 24            |
| 5   | VIO  | **+5V** (with C5 to SGND)         |
| 6   | CANL | CANL                              |
| 7   | CANH | CANH                              |
| 8   | STBY | **SGND**                          |

Do not leave pin 8 floating and do not leave pin 5 unconnected on the
assumption it is optional. Tie them hard — no pull-ups, no jumpers, nothing
that could be left off during assembly.

VIO is a supply, not a logic input: DS20005167C 2.2 gives its range as
1.8–5.5 V, and 1.1.2 notes the bus wake-up needs **both** VDD and VIO in range.
Figure 1-2 shows 0.1 µF on each — that is C4 and C5. VDD itself is specified
4.5–5.5 V, so the 5 V rail sits mid-range.

### 3.2 Crystal loading is 33 pF

C1 = C2 = **33 pF** C0G/NP0, not the 22 pF that gets fitted by reflex, and not
X7R.

The number comes out of the crystal datasheet rather than habit. That sheet
gives **Loading Capacitance: 20 pF Std., 8 to 33 pF**, and its own part-number
example for this frequency — `FTX16.000M20S-30/30B` — is a 16.000 MHz part with
CL = 20 pF in the HC49/S package. So:

```
CL = C1·C2/(C1+C2) + Cstray,  and with C1 = C2 = C:
C  = 2·(CL − Cstray) = 2·(20 − 5) = 30 pF  →  33 pF from the E12 row
```

Cstray of about 5 pF is the usual allowance for the pads, tracks and pin
capacitance on a through-hole board of this size.

> **An earlier version of this document said CL = 32 pF.** That figure appears
> nowhere in the crystal datasheet and does not survive the arithmetic above —
> a 32 pF crystal would want about 56 pF, and 33 pF caps would have run it
> fast. The capacitor value was right for the wrong reason, which is exactly
> the failure mode the sourcing rule in `CLAUDE.md` exists to catch.

Two independent confirmations that 33 pF is the right pairing: the calculation
above, and `PoJD/can-pcb` — `CanSwitch.sch` and `CanRelay.sch` both run a
16 MHz HC49/S with 33 pF and have worked for years.

**No series resistor on OSC2.** DS39977C Table 3-3 note 2 says an Rs "may be
required to avoid overdriving crystals with low drive level specification", and
this crystal's drive level is 100 µW typical, 500 µW maximum. Whether it is
actually needed cannot be decided from the datasheets — it takes a measurement
on a built board. The same PIC-family part drives the same crystal without Rs
in `can-pcb`, so none is fitted. If the oscillator misbehaves, a series
resistor has to be tacked in at the socket pins — this used to say "RC0/RC1 and
the rest of J4 are next to it", which stopped being true when J4 was removed
(§5.4).

Microchip's own tables are guidance only and do not cover this case directly:
Table 3-3 (crystals, HS) lists 27 pF at 4 MHz, 22 pF at 8 MHz and 15 pF at
20 MHz with no 16 MHz row, and note 3 defers to the crystal manufacturer for
the right values. That is what the derivation above does.

### 3.3 No 120 Ω termination

The car's bus is already terminated at both ends. A third resistor overloads
it. R5 gets a footprint and silkscreen, and is **not fitted**:

- Place R5 across CANH/CANL near U2. Done — (85.52, 91.5).
- Silkscreen next to it: `120R DNF`. Done — a board-level `gr_text` at
  (93.2, 91.5), added when the 6 pre-order check found it missing. It is not
  part of the R5 footprint, so re-running `import-footprints.py` cannot take it
  away again.
- Mark it `Do not populate` in the symbol's fields so it drops out of the BOM.
  Done — `in_bom no` and `dnp yes`; it is in neither `canfuel-bom.csv` nor
  `canfuel-cpl.csv`.

A separate solder jumper is not worth the area — for a bench test the resistor
has to be soldered in anyway, and an unpopulated footprint is exactly as quick.

### 3.4 Both Micro-Fit headers in parallel

J1 and J2 sit on the same four nets: CANH, CANL, +5V, SGND. Pin *n* of J1 goes
to pin *n* of J2. This is intentional: cables become interchangeable and the
board is a CAN pass-through even with U1 pulled out of its socket.

| Micro-Fit pin | Net  | Harness                             |
| ------------- | ---- | ----------------------------------- |
| 1             | +5V  | plug C pin 6                        |
| 2             | SGND | plug C pin 12 (SensorGround)        |
| 3             | CANH | plug C pin 7                        |
| 4             | CANL | plug C pin 8                        |

Fix this pin order once, here, and keep the harness (`harness.md`) consistent
with it. Getting +5V and CANH swapped is a dead transceiver.

### 3.5 VDDCORE/VCAP needs 10 µF — and pin 6 is not a port pin

Settled against the datasheet (DS39977C, section 2.4 "Voltage Regulator Pins",
section 28.3 and Table 31-4). Two things follow, and both are easy to get
wrong from memory:

**There is no ENVREG pin.** Not on the 28-pin package, not anywhere in the K80
family. On PIC18F parts (as opposed to PIC18**LF**) the on-chip 3.3 V core
regulator is *permanently enabled* — there is nothing to tie and no way to
disable it. VDD stays at 5 V and the I/O is 5 V; only the core runs at 3.3 V.

**Pin 6 is VDDCORE/VCAP, not RA4.** The 28-pin K80 has no RA4 at all. Pin 6
needs C7:

- **10 µF, low-ESR (< 5 Ω)**, ceramic or tantalum, from pin 6 to SGND.
  Table 31-4 gives CEFC as min 4.7 µF, typ 10 µF.

  **The fitted part is a Murata GRM32DR71C106KA01L**, 10 µF X7R 16 V in 1210 —
  one of the four Microchip names in Table 2-1, so no equivalence argument has
  to be made at all. Its ESR is tens of milliohms against a 5 Ω limit, and X7R
  in a 1210 case loses little enough to DC bias at 3.3 V to stay well clear of
  the 4.7 µF minimum.

  It is the only SMD part on the board, which is a deliberate trade. A dipped
  tantalum was the obvious through-hole alternative and was rejected: the CA42
  datasheet gives DF = 6 % at 100 Hz for the 10–68 µF range, which works out at
  9.6 Ω there and **specifies no high-frequency ESR at all**. The real figure
  is probably 2–3 Ω and `PoJD/can-pcb` has run one for years, but "probably"
  is not a specification, and this is the component whose failure mode the rest
  of this section describes as intermittent and nasty to debug. A tantalum
  would also have to become `C_Polarized` with polarity on the silkscreen —
  `can-pcb` drew its as a non-polarised `C-EU`, which worked only because the
  builder knew which way round it went.
- ⚠ **Pin 6 must never be connected to VDD.** That is the regulator's output,
  not an input. Tying it to 5 V destroys the part.
- Keep the trace to the capacitor **under 6 mm** (datasheet: 0.25 inch).

Without C7 the regulator is unstable and the part browns out or never starts —
and because the symptom is intermittent it is a genuinely nasty one to debug.

**The 0.1 µF figure is real but belongs to a different part.** DS39977C 2.4
gives it twice: once for "when the regulator is disabled", and once for the
PIC18**LF**XXKXX devices, which disable the regulator permanently. Our part is
an F, where 2.4 says the regulator is permanently *enabled* and "these devices
require a 10 µF capacitor on the VCAP/VDDCORE pin". Reading the sentence that
applies to the neighbouring part number is how a board ends up with 0.1 µF
there.

**Available port A pins.** With the crystal on pins 9/10, RA6 and RA7 are gone
and pin 6 is not a port pin, so port A offers exactly five usable pins:
**RA0 (2), RA1 (3), RA2 (4), RA3 (5), RA5 (7)** — of which RA0 is the debug
jumper. Port A is tight, and by 3.6 it is also weak; do not plan on more.

### 3.6 Port A can only drive 2 mA — the LEDs are on port C

DS39977C page 541, Absolute Maximum Ratings, splits the ports:

| Pins                              | Max sourced | Max sunk |
| --------------------------------- | ----------- | -------- |
| PORTA<7:6>, any PORTB, any PORTC  | 25 mA       | 25 mA    |
| **PORTA<5:0>**, PORTF, PORTG      | **2 mA**    | **2 mA** |

RA1 and RA2 are inside PORTA<5:0>. An LED at 1 kΩ off a 5 V rail draws about
2.2 mA once VOH is taken as VDD − 0.7 (D090) and Vf as 2.1 V — over the limit,
so **D1 and D2 are on RC0 (pin 11) and RC1 (pin 12)**, and RA1/RA2 were left
unused. R3 and R4 stay at 1 kΩ. (They "went to the escape header instead" until
J4 was removed on 2026-08-09, §5.4; on the manufactured board they go nowhere
and the firmware drives them low.)

Two things make this worth writing down rather than just fixing:

- **The datasheet contradicts itself and the stricter number wins.** D080/D090
  in the DC characteristics specify VOL and VOH for "PORTA, PORTB, PORTC"
  together, at IOL = 8.5 mA and IOH = −3 mA, which reads as permission to pull
  3 mA out of RA1. Absolute Maximum Ratings is a stress rating the manufacturer
  will not stand behind being exceeded; a characterisation table is not a
  licence to exceed it.
- **`can-pcb` was not a precedent for this.** Its status LED hangs off RC1
  through 1 kΩ — port C, 25 mA. The 1 kΩ was inherited from that board without
  the pin, and the pin was the part that mattered.

RA0 is unaffected: it is an input with a pull-down, and sources nothing.

### 3.7 J1/J2 — the Micro-Fit PCB layout, and why the holes are "finished"

`micro-fit-43045-datasheet.pdf` is Molex **SD-43045-001** (rev. 2016/08/23),
*Micro-Fit (3.0) Dual Row Right Angle Thru Hole Header Ass'y*. It was the last
part on the board with no datasheet on disk. Its `PCB LAYOUT: COMPONENT SIDE`
block settles four things that had only ever been taken from the KiCad
footprint:

| Drawing | Value | As built |
| --- | --- | --- |
| contact hole | ⌀ .040±.002 / **1,02±0,05 mm** TYP | 1.02 mm |
| peg hole | ⌀ .118±.002 / **3,00±0,05 mm** TYP | 3.00 mm NPTH |
| pitch | .118±.004 / 3,00±0,10 non-accum | 3.00 mm |
| row spacing | .170±.003 / 4,32±0,08 | ok |
| recommended board thickness | .062 / **1,57 mm** | 1.60 mm |
| mates with | receptacle series **43025** | 43025-0400 bought |

The pin itself is **.025 / 0,64 mm SQ TYP**, so its diagonal is 0.905 mm.

**Note 7 of the drawing is a placement rule and nobody had checked it:** *"To
avoid interference between receptacle and PCB, header must be placed within
.400/(10,16) max. from edge of PCB."* It limits how far the header may be set
back, so the mating receptacle does not foul the board. J1 and J2 courtyards
end **0.33 mm** from the bottom edge — effectively flush, against a 10.16 mm
limit. It passes with room, but it passes by luck rather than by design, so it
is written down now: if these connectors are ever moved inward, this is the
number that decides it.

**The holes must be ordered as finished sizes, not drill sizes.** A fab that
compensates for plating turns a 1.02 mm tool into a 0.92 mm finished hole,
which is below the drawing's 0.97 mm lower limit — out of spec. Asked the other
way the error is benign: a hole 0.1 mm too large loosens the pin and drops the
annular ring to 0.19 mm, still far above any fab's minimum. So "finished" is
both correct and the safe direction. See 6.1.

**The peg hole is the fussy one, and the answer is not a smaller number.** The
plastic peg is split and spreads under the board, so the instinct is to
undersize the hole for grip. Molex already allowed for that: ±0.05 mm is the
band the peg is designed to hold across. Moving the nominal down to 2.95 or
2.97 puts the low end of any normal fab tolerance under 2.95 and out of spec,
and forcing a split LCP peg into an undersized hole is how the housing cracks —
on a right-angle part the peg also carries the plug insertion force.

The real hazard is plating, not the nominal. A **plated** peg hole comes out at
about 2.90 mm, under the 2.95 minimum, which is exactly the "have to force it"
failure; and plating compensation wrongly applied to a hole that is not plated
gives 3.10 mm, where the peg does not grip at all. Both are avoided by shipping
PTH and NPTH as separate drill files and saying which is which — see 6.

---

## 4. Schematic — done

One A3 sheet. A4 was tried first and everything collided; the parts count is
low but the label count is not.

### 4.1 Nets

```
+5V      SGND      CANH      CANL
CAN_TX   CAN_RX    OSC1      OSC2
~MCLR    MCLR_RC   MCLR_C                (the reset network of 4.3a)
PGC      PGD       VCAP
LED_PWR  LED_CAN   DBG_EN                (LED_PWR/LED_CAN are RC0/RC1)
LED_PWR_A          LED_CAN_A             (resistor to LED anode)
CANTX2   CANRX2                          (RC6/RC7, the ECAN alternates)
ESC_RA1  ESC_RA2   ESC_RA3   ESC_RA5
ESC_RC2 … ESC_RC5
ESC_RB0  ESC_RB1   ESC_RB4   ESC_RB5
```

33 nets in total. `SGND` is the ground net name throughout, not `GND` — it is
the display's sensor ground and the harness documentation calls it that.

**The labels are global, not local.** On a single-sheet design either works
electrically, but a local label comes out of the netlist as `/CANH` while the
net classes in section 5.3 are written as `CANH`. A netclass pattern that
silently matches nothing is a bad way to find out that CAN was routed at the
default track width.

### 4.1a Symbol and footprint choices

| Ref     | Symbol                                | Footprint                                                    |
| ------- | ------------------------------------- | ------------------------------------------------------------ |
| U1      | `MCU_Microchip_PIC18:PIC18F25K80_ISS` | `Package_DIP:DIP-28_W7.62mm_Socket`                            |
| U2      | `Interface_CAN_LIN:MCP2562-E-P`       | `Package_DIP:DIP-8_W7.62mm_Socket`                             |
| Y1      | `Device:Crystal`                      | `Crystal:Crystal_HC49-U_Vertical`                              |
| C1–C5   | `Device:C`                            | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm`                   |
| C6      | `Device:C_Polarized`                  | `Capacitor_THT:CP_Radial_D5.0mm_P2.00mm`                       |
| C7      | `Device:C`                            | `Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder`    |
| R1–R5   | `Device:R`                            | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` |
| D1, D2  | `Device:LED`                          | `LED_THT:LED_D3.0mm`                                           |
| J1, J2  | `Connector_Generic:Conn_02x02_Odd_Even` | `Connector_Molex:Molex_Micro-Fit_3.0_43045-0400_2x02_P3.00mm_Horizontal` |
| J3      | `Connector_Generic:Conn_01x05`        | `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical`   |
| ~~J4~~  | ~~`Connector_Generic:Conn_02x08_Odd_Even`~~ | ~~`Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical`~~ — **removed 2026-08-09, see 5.4** |
| JP1     | `Connector_Generic:Conn_01x02`        | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`   |

Two of those deserve a sentence, because both look wrong at a glance:

- **U1 uses the `_ISS` (SSOP-28) symbol with a PDIP-28 footprint.** KiCad ships
  only `_ISS` and `_IML` for this part; there is no SPDIP variant. All three
  28-pin packages share one pinout, and the symbol's pins were checked
  one by one against DS39977C page 6 — including that pin 6 is `Vcap` and that
  there is no RA4. Nothing else in the library needed changing.
- **J1/J2 are `Conn_02x02`, not `Conn_01x04`.** The Micro-Fit 43045-0400 is
  physically two rows of two. Its pads are numbered 1, 2 across the first row
  and 3, 4 across the second, so the plan's pin numbering in 3.4 carries over
  unchanged — but the symbol has to be the two-row one or the pin numbers do
  not line up with the footprint.

### 4.2 U1 — PIC18F25K80, PDIP-28

The full 28-pin SPDIP pinout, taken from DS39977C page 6. Names abbreviated to
the functions that matter here.

| Pin | Name          | Connect to                                                    |
| --- | ------------- | ------------------------------------------------------------- |
| 1   | MCLR/RE3      | R6 (470 Ω) from the R1 node, and J3 pin 1. See 4.3a           |
| 2   | RA0/AN0       | JP1 to +5V, R2 (10 kΩ) to SGND → `DBG_EN`                     |
| 3   | RA1/AN1       | **nothing — see 3.6.** 2 mA pin                                |
| 4   | RA2/AN2       | **nothing — see 3.6.** 2 mA pin                                |
| 5   | RA3/AN3       | **nothing — see 3.6**                                         |
| 6   | **VDDCORE/VCAP** | **C7 (10 µF low-ESR) to SGND. Never to +5V.** See 3.5      |
| 7   | RA5/AN4       | **nothing — see 3.6**                                         |
| 8   | VSS           | SGND                                                          |
| 9   | OSC1/CLKIN/RA7| Y1 + C1                                                       |
| 10  | OSC2/CLKOUT/RA6| Y1 + C2                                                      |
| 11  | RC0/SOSCO     | R3 → D1 (`LED_PWR`) — see 3.6                                 |
| 12  | RC1/SOSCI     | R4 → D2 (`LED_CAN`) — see 3.6                                 |
| 13  | RC2/T1G/CCP2  | **nothing — see 3.6**                                         |
| 14  | RC3/SCL/SCK   | **nothing — see 3.6**                                         |
| 15  | RC4/SDA/SDI   | **nothing — see 3.6**                                         |
| 16  | RC5/SDO       | **nothing — see 3.6**                                         |
| 17  | RC6/**CANTX**/TX1 | **nothing — see 3.6.** Alternate ECAN pin, see below       |
| 18  | RC7/**CANRX**/RX1 | **nothing — see 3.6.** Alternate ECAN pin, see below       |
| 19  | VSS           | SGND                                                          |
| 20  | VDD           | +5V, C3 (100 nF) to SGND, as close as the layout allows       |
| 21  | RB0/INT0      | **nothing — see 3.6**                                         |
| 22  | RB1/INT1      | **nothing — see 3.6**                                         |
| 23  | RB2/**CANTX** | `CAN_TX` → U2 pin 1                                           |
| 24  | RB3/**CANRX** | `CAN_RX` → U2 pin 4                                           |
| 25  | RB4/AN9       | **nothing — see 3.6**                                         |
| 26  | RB5/T0CKI     | **nothing — see 3.6**                                         |
| 27  | RB6/**PGC**   | `PGC` → J3 pin 5                                              |
| 28  | RB7/**PGD**   | `PGD` → J3 pin 4                                              |

**The ECAN module can be remapped.** CANTX/CANRX are available on RB2/RB3
*and* on RC6/RC7.

⚠ **This used to say the alternates land on J4, so a remap would be two wire
links on the escape header. J4 was removed on 2026-08-09 (§5.4), so it is not.**
RC6 and RC7 go nowhere on the manufactured board, and moving the ECAN now means
soldering to the PDIP socket pins from underneath — they are through-hole and
reachable, so the escape route survives, but it is a soldering iron and not a
jumper. That is the single strongest reason to get `CANMX` right the first
time, and it is why the firmware reads the bit out of the built hex rather than
trusting the source.

LEDs, driven by the PIC so nothing lights up in the car:

- D1 anode ← R3 ← RC0 (pin 11) → `LED_PWR`, cathode to SGND
- D2 anode ← R4 ← RC1 (pin 12) → `LED_CAN`, cathode to SGND

Port C, not port A — see 3.6, and do not move them back.

Firmware only drives them when `DBG_EN` reads high, i.e. when the JP1 jumper is
fitted. R2 pulls RA0 down, so an absent jumper is a defined low, not a floating
input.

**Unused pins are a firmware obligation, and since J4 went it is the only
option.** DS39977C 2.7 offers two: unused I/O configured as outputs driven low,
**or** a 1–10 kΩ resistor to VSS. There are no such resistors on this board —
fourteen of them would have cost more area than they were worth — so the first
option is the only one available, and the firmware in the `canfuel` repository
has to drive all fourteen low at start-up: RA1, RA2, RA3, RA5, RC2–RC7, RB0,
RB1, RB4, RB5.

⚠ **This paragraph used to say the fourteen pins "sit at a header with nothing
on the other end".** They did until 2026-08-09; J4 was removed (§5.4) and they
now go nowhere at all. The firmware obligation is unchanged and is if anything
more load-bearing, because software is now the only thing standing between
those pins and floating inputs.

### 4.3 J3 — ICSP

PICkit pin order, 2.54 mm, keep pin 1 square-padded and marked on silkscreen.
Keep the J3-to-U1 traces short; the datasheet (2.5) explicitly rules out
pull-ups, series diodes and capacitors on PGC/PGD because they interfere with
the programmer.

| J3 pin | Signal |
| ------ | ------ |
| 1      | ~MCLR / VPP |
| 2      | +5V    |
| 3      | SGND   |
| 4      | PGD (RB7) |
| 5      | PGC (RB6) |

J3 pin 1 lands on `~MCLR`, the U1 pin itself, not on the RC node behind R6 —
the programmer drives the pin directly and R6 keeps C8 off its back. See 4.3a.

**Not fitted, but recorded:** 2.5 also suggests a series resistor of a few tens
of ohms, never above 100 Ω, on PGC and PGD if the ICSP connector is expected to
see an ESD event. This connector lives in a closed vent cavity behind the
dashboard and is touched perhaps twice in the board's life, so nothing is
fitted. Revisit only if the header is ever brought somewhere reachable.

### 4.3a MCLR — the full network of DS39977C Figure 2-2

```
+5V ──[ R1 10k ]──┬──[ R6 470R ]── MCLR (U1 pin 1) ── J3 pin 1
                  │      nets:  MCLR_RC ──R6──> ~MCLR
                 JP2
                  │   MCLR_C
              [ C8 100n ]
                  │
                SGND
```

Figure 2-1 lists MCLR among the pins that must always be connected, and
Figure 2-2 gives the shape above. Each part earns its place:

- **R1 = 10 kΩ.** Figure 2-2 note 1: "R1 ≤ 10 kΩ is recommended. A suggested
  starting value is 10 kΩ."
- **R6 = 470 Ω.** Figure 2-2 note 2: "R2 ≤ 470 Ω will limit any current flowing
  into MCLR from the external capacitor C, in the event of MCLR pin breakdown,
  due to Electrostatic Discharge (ESD) or Electrical Overstress (EOS)." It sits
  between the RC node and the pin, which is the only position from which it can
  do that.
- **C8 = 100 nF, behind JP2.** 2.3 recommends the capacitor for resistance to
  spurious resets from voltage sags, and in the same breath says it must be
  isolated from the pin during programming and debugging by a jumper, because
  device programmers drive MCLR and need fast edges. JP2 is that jumper.
- **All of it within 6 mm of pin 1.** 2.3: "Any components associated with the
  MCLR pin should be placed within 0.25 inch (6 mm) of the pin." That is a
  placement constraint on R1, R6, C8 and JP2 — see 5.2.

**Pull JP2 before programming, refit it afterwards.** This is the one assembly
step the board cannot enforce, so it is note 11 on the schematic as well.

An earlier version of this plan had only R1 and said "no capacitor on this pin",
reading 2.5 (which is about PGC and PGD) as if it covered MCLR. It does not:
2.3 asks for the capacitor and hands it a jumper. `PoJD/can-pcb` built the full
network — R1 10 kΩ, 470 Ω, 0.1 µF on a jumper — which is what prompted the
re-read.

### 4.4 Power

+5V and SGND enter on J1/J2. C6 (10 µF) across the input, C3/C4/C5 (100 nF) at
each supply pin. No regulator, no reverse-polarity diode, no TVS — that was
decided; the 12 V branch is not on this board. Total draw is under 30 mA
against the display's 0.5 A limit, so there is no thermal question to answer.

Both values are the datasheet's own:

- **100 nF, ceramic, low-ESR, within 6 mm of the pin** — DS39977C 2.2.1, which
  calls decoupling on every supply pin pair *required*, not advisable, and puts
  the same 0.25 inch limit on the track as 2.4 does for C7.
- **C6 = 10 µF is the tank capacitor of 2.2.2**, which asks for one on boards
  whose power traces run longer than six inches and gives a range of 4.7 µF to
  47 µF. The harness from the display connector is well past six inches, so
  this is the case that section describes.

The 28-pin package has no AVDD/AVSS pins — 2.1 insists they always be connected
"regardless of whether any of the analog modules are being used", but the pin
tables put them only on the 64- and 80-pin parts. Nothing is missing here; it
is worth stating so the question is not reopened.

### 4.5 ERC

```
kicad-cli sch erc --severity-all --exit-code-violations canfuel/canfuel.kicad_sch
```

Clean, zero violations at `--severity-all`. Three `PWR_FLAG`s were needed and
are on the sheet: `+5V` and `SGND` are fed by connector pins rather than a
regulator output, and `VCAP` is driven by the regulator inside U1, so ERC has
no power-output pin to find on any of the three. No ERC severity was lowered
and no check was disabled to get there.

### 4.6 Checking the schematic against this document

ERC proves the sheet is electrically well formed. It does not prove RB2 went
to TXD rather than RB3 — that was demonstrated, not assumed: swapping the two
labels produces a board that could never transmit, and ERC reports **zero**
violations on it, because both pins are bidirectional and nothing is
malformed.

So there is a second check, and it is in the repository:

```
python tools/check-netlist.py
```

It exports the netlist and compares every `ref.pin -> net` against the tables
in sections 3 and 4 above — 87 connections, 33 nets, 24 components, no pin in
the netlist unaccounted for and none missing. It catches the RB2/RB3 swap
above. Needs `kicad-cli` on PATH; exits nonzero on any mismatch.

It also carries weight this sheet cannot get from ERC for a second reason: the
project has *Global label only appears once in the schematic* switched off, so
a mistyped label name would produce two half-connected nets and no violation.
Every connection here is made by label, so that check is the one that would
have caught it.

Run it after any edit to the sheet. When the design changes on purpose, update
`EXPECT` in the script in the same commit — keeping the two in step is the
point of the file, not a chore it imposes.

**Definition of done:** ERC clean, netlist matches this document, committed,
CI green. ✔

---

## 5. PCB layout

### 5.1 Outline and constraints

- Board **55 × 45 mm**, 2 layers, corners rounded R2. Outline runs x 50…105,
  y 50…95 on the sheet.
- **Four M3 holes, ⌀3.2 mm non-plated, 4 mm in from each edge** — H1 (54, 54),
  H2 (101, 54), H3 (54, 91), H4 (101, 91), a 47 × 37 mm pattern. Keep copper
  and parts clear of a 7 mm circle around each.
- **There is no enclosure** (section 9), so those positions answer to nothing
  but themselves and are not a respin risk. Whatever the board is eventually
  mounted on adapts to them.
- **The holes live in the PCB only** — there are no `H1`…`H4` symbols on the
  schematic, because a mounting hole carries no net. If you ever run *Update
  PCB from Schematic* in the GUI, leave **Delete footprints with no symbols**
  unticked or they disappear. It is unticked by default.
- Available space in the vent is roughly 65 × 55 mm, depth unknown — the MFD15
  is in the way and cannot be measured around. The board's 55 mm therefore has
  about 10 mm of margin in the direction that was measured, which is the whole
  reason the enclosure was dropped.
- Height budget is generous with no lid to clear: the tallest parts are C6 at
  11 mm and Y1 standing at about 11.4 mm. Nothing needs to be laid down.
- Mostly through-hole; hand assembly. C7 is the one SMD part, on B.Cu.

### 5.2 Placement

```
        55 mm
  ┌───────────────────────────┐
  │  J3 ICSP                  │  ← top edge, reachable with the lid off
  │        (J4 was here, 5.4) │
  │                           │
  │   Y1  C1 C2               │
  │   ┌──────────┐            │  45 mm
  │   │    U1    │   D1  D2   │
  │   │  PIC28   │   JP1      │
  │   └──────────┘            │
  │        ┌──────┐   C6      │
  │   R5   │  U2  │           │
  │  DNF   └──────┘           │
  │   ┌────┐   ┌────┐         │
  └───┤ J1 ├───┤ J2 ├─────────┘  ← bottom edge, harness exits one way
```

Rules behind that sketch. The numeric ones are the datasheet's, and there are
now four of them rather than one — do the placement against this list, not
against the sketch:

- **C7 hard against U1 pin 6, track under 6 mm** — DS39977C 2.4. Place it
  before routing anything else. Being 1210 SMD it goes on **B.Cu directly
  underneath pin 6**, which takes the track from "under 6 mm" to about zero and
  costs no top-side area next to the socket. It is the only part on the bottom
  layer; keep the ground pour clear of it there.
- **C3 within 6 mm of U1 pin 20, C4 within 6 mm of U2 pin 3, C5 within 6 mm of
  U2 pin 5**, each on the same side of the board as its pin — 2.2.1. If a via
  is unavoidable the 6 mm still counts from pin to capacitor.
- **R1, R6, C8 and JP2 all within 6 mm of U1 pin 1** — 2.3, "any components
  associated with the MCLR pin". Four parts inside a 6 mm radius is the
  tightest cluster on the board; lay it out first, before anything that is
  merely convenient. (This said "before the escape header, not after" — in the
  event the cluster won and the header went, 5.4.)
- **The oscillator circuit within 12 mm of pins 9/10**, on the same side of the
  board as U1, with C1 and C2 next to Y1 itself — 2.6.
- **A grounded copper pour around the oscillator**, routed directly to the MCU
  ground pin, with **no signal or power traces run inside it** — 2.6. This is
  stronger than "do not let the pour split the ground under the crystal": the
  pour is a deliberate guard, not a leftover.
- **Nothing on the bottom layer underneath the crystal** — 2.6 says so in as
  many words for a two-sided board, and both of ours are.
- **Keep fast or noisy signals away from pins next to the oscillator** — 2.6
  again. In practice that means the CAN pair and the ICSP lines.
- U2 between U1 and the connectors — CANH/CANL should be short and never cross
  the crystal.
- J1/J2 on the same long edge so the harness leaves in one direction; the vent
  has no room for cables on two sides.
- D1/D2/JP1 grouped where they are visible without disassembling anything, and
  JP2 somewhere a finger and a pair of pliers can reach — it comes out for every
  programming session.
- **Keep parts and copper out of a 7 mm circle around each of H1–H4.** A nylon
  M3 standoff has a 6 mm head and it has to sit flat.

### 5.2a Placement as built — done

Parts are placed and `tools/check-placement.py` is clean. U1 sits across the
middle at rot 270, which puts **pins 1–14 along its top edge running right to
left** and pins 15–28 along the bottom. Everything else follows from that:

| U1 pin       | Faces  | What went next to it                         |
| ------------ | ------ | -------------------------------------------- |
| 1 MCLR       | top right | R6, R1, C8, JP2 in the top-right corner   |
| 6 VCAP       | top    | C7 on B.Cu, under the package                |
| 9/10 OSC     | top    | Y1 mirrored, C1 and C2 standing either side  |
| 20 VDD       | bottom | C3 directly below                            |
| 23/24 CAN    | bottom | U2 below right, then J1/J2                   |
| 27/28 ICSP   | bottom | J3 below left                                |

J1/J2 sit on the bottom edge, cables leaving downwards. D1/D2 and their
resistors run down the left edge where they can be seen. The right-hand column
held J4 until 2026-08-09 and now holds most of the MCLR network instead.

Measured against the datasheet:

| Rule    | Constraint            | Measured                    |
| ------- | --------------------- | --------------------------- |
| 2.4     | C7 → U1.6 ≤ 6 mm      | **2.25 mm**, on B.Cu        |
| 2.2.1   | C3 → U1.20 ≤ 6 mm     | **5.67 mm**                 |
| 2.2.1   | C4 → U2.3 ≤ 6 mm      | **5.68 mm**                 |
| 2.2.1   | C5 → U2.5 ≤ 6 mm      | **4.49 mm**                 |
| 2.6     | Y1/C1/C2 ≤ 12 mm      | **5.35 / 9.79 / 6.98 mm** from the pin each is on |

**Two things about the wording are worth keeping.** §2.2.1 and §2.4 limit the
*trace length from the pin to the capacitor*; §2.3 and §2.6 talk about where the
*components are placed*. Those are not the same measurement and the difference
decides whether this board passes, so `check-placement.py` keeps them apart.
§2.6 also says "close to the **respective** oscillator pins", so C1 is measured
against OSC1 and C2 against OSC2 — the pins they are actually on.

**Where §2.3 is not met, and why.** It asks for R1, R6, C8 and JP2 all inside a
6 mm circle centred on pin 1. Pin 1 is a corner pin, so about three quarters of
that circle is free — roughly 85 mm² — and the four parts are 71 mm² of
courtyard between them. They do not fit, and no choice of footprint changes
that: this is an area problem, not a lead-pitch problem.

What was done instead is to make all four hug the pin rather than get one of
them fully inside. The arrangement was found by search (`mclr_opt.py`, a
throwaway), minimising the worst far corner over every legal position and
rotation:

| | nearest edge | farthest corner |
| --- | --- | --- |
| C8  | 1.66 mm | 7.50 mm |
| JP2 | 1.88 mm | 8.67 mm |
| R1  | 2.89 mm | 8.91 mm |
| R6  | 2.46 mm | 7.63 mm |

Every part is within 3 mm of the pin at its nearest edge, and the far corners
are bodies extending outward, not connections — the pin sees the near end.

**R1 was then moved 1.20 mm further out, on purpose (2026-08-09).** The search
above optimised for distance to the pin and produced an arrangement where R1's
courtyard and C8's touched — 0.03 mm — with R1 pad 2 and C8 pad 1 2.66 mm apart,
1.06 mm of bare board between the copper. Those two pads are `MCLR_RC` and
`MCLR_C`: the two ends of JP2. A solder bridge there would tie the jumper
closed permanently, which is the one failure the jumper exists to prevent, and
it would look like a working board until the first attempt to program it.

Moving R1 west by 1.20 mm opens that gap to 2.26 mm of bare board (courtyards
1.23 mm apart) and costs about 0.9 mm of extra track from R1 to the MCLR node.
R1 is the 10 kΩ static pull-up — the least length-sensitive part of Figure 2-2 —
so that is the right part to spend the distance on. The move was sized by the
nearest-edge rule, not by eye: 1.20 mm is what keeps R1 at 2.89 mm, inside the
3 mm assertion with a little margin. `ALLOW["2.3 R1"]` went from 8.5 to 9.0 to
match, which is where JP2 already sits.

The two tracks that reach R1 were re-laid for it. +5V arrives on B.Cu along
y = 61.4 and used to step down into pad 1 right where pad 2 now sits, so the
step became a longer run west and one 45° diagonal; `MCLR_RC` gained a 45°
diagonal from the new pad 2 up to the existing vertical at x = 92.8. DRC is
clean and there are no unconnected items.

An earlier arrangement had R6 wholly inside at 5.94 mm but C8 out at 10.68 mm.
That was worse: R6 fitting was an accident of it being small, and it left the
reset capacitor — the part §2.3's own Figure 2-2 note is about — furthest away.
The room to improve came from removing J4, whose column was inside the circle
(see 5.4).

`tools/check-placement.py` records the tolerated far corners in `ALLOW` with
their reasons and, more to the point, asserts that every nearest edge stays
within 3 mm. That second check is the one carrying weight. Do not widen either
to make a red run green.

**Standing resistors.** R1–R6 are `R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical`
and C8 is the 2.50 mm disc, changed from the 10.16 mm horizontal parts on
2026-08-09. That is how the maintainer fits axial resistors anyway — body
upright, leads bent to the narrowest spacing — and it is what got R6 inside the
circle at all: upright, a resistor reaches 3.95 mm from its first pad against
11.36 mm lying down.

**C7 is turned across the package, not along it.** Lying along the pin row its
ground pad shorted pin 5; in the empty channel between the two rows it clears
both rows by 0.79 mm and still lands 2.25 mm from pin 6.

### 5.3 Net classes

| Class   | Nets              | Track width | Clearance |
| ------- | ----------------- | ----------- | --------- |
| Default | signals           | 0.25 mm     | 0.20 mm   |
| Power   | +5V, SGND         | 0.80 mm     | 0.20 mm   |
| CAN     | CANH, CANL        | 0.40 mm     | 0.20 mm   |

Route CANH/CANL as a pair, side by side, equal length, no stubs beyond the DNF
R5 pads. Pour SGND on both layers and stitch the pours with vias, but do not
let the pour split the ground under the crystal.

**Done.** The three classes are in `canfuel.kicad_pro`, assigned by netclass
pattern: `+5V` and `SGND` to Power, `CANH` and `CANL` to CAN, everything else
Default. Via sizes stay at KiCad's 0.6/0.3 mm for all three — the table above
sets track width and clearance only, and 0.3 mm drill is inside every fab
house's standard process. That is a manufacturing choice, not a datasheet
number, and nothing in this repository depends on it.

**Routing plan for the layer split**, which falls out of the placement:

- Everything leaving U1's **top row goes down into the channel between the two
  pin rows first**, then out sideways. That keeps the area above the top row
  clear for the oscillator's grounded guard, which §2.6 requires be free of
  signal and power traces.
- **Nothing on B.Cu under the crystal.** §2.6 says so in as many words for a
  two-sided board. The grounded pour there is the guard the same section asks
  for, and is not what "traces" means.

Both are given to the router as keep-out rectangles and re-checked afterwards
by `check-placement.py`, so they cannot quietly rot.

**Done, 0 unconnected items.** Routing was done by a throwaway grid router
(A* per connection over both layers, 0.2 mm grid) rather than by hand — thirty
nets of hand-written waypoints is a lot of arithmetic to get wrong. Two things
it taught, worth knowing if it is ever run again:

- **Net order decides whether it finishes.** Oscillator and VCAP first, then
  the rest alphabetically, routed 32 of 39 with J4 still fitted. Longest-first
  managed 25 and +5V-last managed 27: the 0.8 mm +5V net becomes a wall the
  thin signals cannot cross if it goes early, and cannot reach its own thirteen
  pads if it goes late.
- **A via is 0.6 mm of copper on both layers, not a point.** Treating it as a
  point produced three clearance violations DRC caught afterwards.

### 5.4 The escape hatch was removed — measured, not argued

J4 was a 2×8 header bringing out all 14 unused I/O pins plus power, so a design
error could be patched with a wire rather than a new board. It was fitted, and
on **2026-08-09 it was taken off again.** Do not put it back without reading
this.

**What it cost, measured.** Routing the board with and without it, same router,
same placement, same ordering:

| | with J4 | without J4 |
| --- | --- | --- |
| connections to route | 39 | 25 |
| **left unroutable** | **8** | **0** |
| DRC | incomplete | **0 violations** |

**The part that settles it is which connections failed.** Five of the eight
were not escape signals at all:

- `LED_PWR` and `LED_CAN` — both status LEDs
- `PGD`, `PGC` and `~{MCLR}` — the entire ICSP header

J4 does not only occupy its own area. Its fourteen signals congest the channel
between U1's two pin rows, which is the only way across the board, and the ICSP
and LED nets are what get starved. A header whose whole purpose is to rescue a
design error was preventing the chip from being programmed — which is the
design error it would have had to rescue.

**What replaces it.** Nothing on the board. U1's fourteen unused pins carry
no-connect flags in the schematic. If a patch is ever needed, it goes onto the
**PDIP socket pins from underneath** — they are through-hole and accessible, so
the escape route survives without the header. That was the maintainer's call
and it is a good one: the socket was always the real escape hatch.

**What the space bought.** J4 sat in the right-hand column, which lies inside
the 6 mm circle DS39977C §2.3 draws around U1 pin 1 — so it was also the reason
the MCLR cluster could not be tightened. With it gone the cluster was re-placed
by search (see 5.2a) and the worst far corner fell from 10.68 mm to 8.67 mm,
with every one of the four parts now within 2.5 mm of the pin at its nearest
edge.

The `RA1-RA3,RA5` / `2mA MAX` silkscreen legend went with it; it warned about
the weak port A pins on a header that no longer exists.

Value fields moved to F.Fab in the same pass. At this density the stock field
positions collided with each other and sat over pads; the references are what
a hand-assembler needs on the silkscreen, and the values are in the BOM and on
the fab drawing already.

That left the front silkscreen carrying reference designators and footprint
outlines and nothing else — which is right for every part but one. R5's `120R
DNF` warning went with the values, and stayed missing until the 6 pre-order
check caught it. It is now a board-level text, not a footprint field, so it
cannot be swept up by a change to how fields are placed.

### 5.5 DRC

```
kicad-cli pcb drc --exit-code-violations canfuel/canfuel.kicad_pcb
python tools/check-placement.py
```

**Both are clean: 0 violations, 0 unconnected items.** The board is routed on
two layers with SGND poured on both and stitched through the through-hole pads.

**DRC on its own is not enough, for the same reason ERC was not.** A decoupling
capacitor 40 mm from its pin is a perfectly legal board — it is just a broken
one, and DRC will pass it without complaint. `check-placement.py` is the
board's equivalent of `check-netlist.py`: it re-measures the four distance
rules of 5.2, the mounting-hole keepouts and the §2.6 oscillator guard, and
carries the tolerated §2.3 shortfalls with their reasons so an intentional
deviation never reads as a regression.

**Pads connect to the pours through thermal reliefs** — 0.6 mm spokes, 0.3 mm
gap. The board is hand soldered, and a through-hole ground pin tied straight
into a plane sinks heat faster than an iron replaces it; cold joints on ground
are the usual result. The first attempt used 0.8 mm spokes and two pads came
out with a single spoke each, which DRC flags as `starved_thermal`; narrowing
the spokes let the rest through.

Then, separately from either, do the checks a tool cannot do: run the 3D viewer and confirm the socket, the electrolytic and both
Micro-Fit bodies do not collide, and print the board 1:1 on paper and drop the
real connectors onto it.

**Definition of done:** DRC clean, committed, CI green.

---

## 6. Fabrication outputs — done

Generated into `canfuel/fab/` and **committed** — for an ordered board it must
be possible to recover exactly what was sent.

```
fab/gerbers/    9 gerbers, canfuel-PTH.drl, canfuel-NPTH.drl,
                their two drill maps, canfuel-job.gbrjob
fab/canfuel-bom.csv
fab/canfuel-cpl.csv
```

These are the commands as run, not an outline. Every flag beyond the bare
export is here because the default was wrong for this board:

```
kicad-cli pcb export gerbers --output canfuel/fab/gerbers \
  --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  --check-zones canfuel/canfuel.kicad_pcb
kicad-cli pcb export drill --output canfuel/fab/gerbers \
  --excellon-separate-th --generate-map --map-format gerberx2 \
  canfuel/canfuel.kicad_pcb
kicad-cli sch export bom --output canfuel/fab/canfuel-bom.csv \
  --group-by "Value,Footprint" canfuel/canfuel.kicad_sch
kicad-cli pcb export pos --output canfuel/fab/canfuel-cpl.csv \
  --format csv --units mm --side both --exclude-dnp canfuel/canfuel.kicad_pcb
```

- `--layers` is mandatory in practice: `export gerbers` plots nothing useful
  without it. Both paste layers are included even though only C7 is SMD.
- `--check-zones` refills the pours before plotting, so a stale fill cannot be
  what gets sent. It changes the output, never the board file.
- `--format csv --units mm` on `export pos`: the default is ASCII in inches,
  which would have produced a file named `.csv` that is not one.
- `--exclude-dnp` keeps R5 out of the CPL. It is the one part on the board that
  must not be fitted; a placement file listing it is worse than no file.
- `--excellon-separate-th` splits the drilling into `canfuel-PTH.drl`
  (`TF.FileFunction,Plated,1,2,PTH`, tools 0.30/0.80/0.90/1.00/1.02) and
  `canfuel-NPTH.drl` (`NonPlated,1,2,NPTH`, tools 3.00 and 3.20). A single
  merged `MixedPlating` file was produced first and tags every tool correctly,
  so it loses nothing on paper — but the peg holes of 3.7 fail if they are
  plated by mistake, and two files whose names say what they are cannot be
  misread. That is worth more than one fewer attachment.

The CPL is generated for completeness only — every part here is through-hole
and hand-soldered, so no assembly house will use it.

**Both pre-order checks pass, and one of them needed a fix first.**

- R5 is absent from `canfuel-bom.csv` (23 rows against 24 parts) and from
  `canfuel-cpl.csv`. It carries `in_bom no` and `dnp yes` on the sheet.
- The silk layer **did not** carry the `120R DNF` legend of 3.3 until now. The
  board had no board-level text at all: value fields went to F.Fab in the 5.4
  pass and the R5 footprint only ever put its *reference* on F.SilkS, so the
  silk read `R5` and nothing else. A `120R DNF` `gr_text` was added at
  (93.2, 91.5), F.SilkS — at the 1.0 mm height of 6.1 its extent is
  x 89.31..97.09, y 90.65..92.35, which is 0.45 mm clear of R5 pad 2 and
  0.41 mm clear of the 3.5 mm keepout
  around H4. DRC stays at 0 violations and 0 warnings with `silk_overlap`,
  `silk_over_copper` and `silk_edge_clearance` all enabled, and the plotted
  strokes are in `canfuel-F_Silkscreen.gto`.

  This is exactly why the check is written down as a check. `120R DNF` is the
  only thing on the board that tells an assembler not to fit a part that has a
  footprint, pads and a value — and it was the one legend nothing else would
  have caught.

### 6.0 Ordered — Gatema PCB, 2026-08-09

Three pieces, POOL service, **900 CZK before VAT** (300 CZK each, 1089 CZK
with VAT), five working days at no express surcharge. The stack-up ordered is
their preset *2V Cu 35/35 µm, 1,5 mm, LF HAL, 2x zelená NM, 1x bílý potisk,
Tg 135 °C*, single pieces milled out, min track/gap class ≥150 µm, no assembly
stencil. What was manufactured is commit **`c06e710`**.

Both `Gerbers.zip` and `Odb.zip` were uploaded — the same board from the same
commit, so they cannot disagree, and ODB++ is the format their CAM department
prefers. The gerber package carries a `README.txt` because the configurator has
no comment field and their own handbook accepts a text file for exactly this:
it states that the PTH diameters are finished sizes, that the NPTH ones are not
plated, why the 3.00 mm peg holes in particular must not be plated (3.7), and
that R5 is deliberately unpopulated so its `120R DNF` legend is not read as a
data error.

Three pieces rather than two because the board is the long-lead item: every
other part comes from GME in days. Only two can be populated — the GME invoice
of 2026-08-03 covers four Molex 43045-0400 and each board takes two — so the
third is a bare spare until two more are bought.

### 6.1 printed.cz — capability check

<https://printed.cz/vyroba-dps/>, the first fab house considered. Their
published limits against this board, measured from `canfuel.kicad_pcb`:

| Parameter | printed.cz | canfuel | |
| --- | --- | --- | --- |
| layers | 1–12 | 2 | ok |
| max size | 600 × 600 mm | 55 × 45 mm | ok |
| thickness | 0.2–3.2 mm | 1.6 mm | ok |
| outer copper | 18/35/70/105 µm | 35 µm | ok |
| min track | 0.075 mm (rec. 0.15) | 0.25 mm | ok |
| min spacing | 0.075 mm (rec. 0.15) | 0.20 mm | ok |
| drill range | 0.2–6.3 mm | 0.30–3.20 mm | ok |
| min annular ring | 0.15 mm | 0.15 mm via, 0.24 mm pads | **at the limit** |
| finish | HASL Pb-free, gold, OSP | HASL | ok |
| mask / legend | green… / white, black, yellow | green + white | ok |
| **min text height** | **1 mm** | **was 0.80 mm** | **failed** |
| **min legend stroke** | **0.15 mm** | **was 0.12 mm** | **failed** |
| min order | 1 pc | 1 pc | ok |
| e-test, AOI | free | — | ok |

Track and spacing are not merely inside the limit, they are above the value
the page *recommends* — this board asks for the cheapest process class they
run. Two things are worth recording:

**The legend failed, on every single text.** All 25 silkscreen items — 24
reference designators and the `120R DNF` of 3.3 — were 0.80 mm high with a
0.12 mm stroke, under both minimums. They are now 1.0 mm / 0.15 mm, which is
also what `silk_text_size_h/v` and `silk_text_thickness` in the project
defaults have always said; only the placed items disagreed. Nothing had to
move: DRC reports 0 violations with `silk_overlap`, `silk_over_copper` and
`silk_edge_clearance` raised to `error`, and only the two silkscreen gerbers
changed — copper, mask, paste, drill, edge and the `.gbrjob` are byte-identical
apart from their timestamp line.

**Our own DRC could not have caught it, and now can.** `min_text_height` was
0.8 and `min_text_thickness` 0.08 — looser than the process, so the board
passed its own rules while failing the fab's. Both are now set to the
printed.cz values.

That alone would still have been useless. `text_height` and `text_thickness`
ship as **warnings**, and `kicad-cli pcb drc --exit-code-violations` returns 0
on warnings: with the tightened numbers and the old 0.80 mm text, the report
listed all 50 violations and the command still **exited 0**. That was measured,
not assumed. Both severities are now `error`, which was measured too — the same
board and rules exit 5. A check that cannot fail is not a check; this
repository has already been bitten by that twice, in CI.

`silk_overlap`, `silk_over_copper` and `silk_edge_clearance` are still
warnings and therefore still cannot fail a run. The board is clean under all
three at `error` severity, so promoting them costs nothing — left as a
deliberate open choice rather than changed unasked.

**The via annular ring is exactly at their stated minimum.** 0.15 mm, from a
0.60 mm pad on a 0.30 mm drill, on six vias. It is allowed and they publish it
as manufacturable, but there is no margin. Component pads are 0.24 mm and up,
so it is the vias alone. If they push back, a 0.70 mm via pad gives 0.20 mm;
ask before changing anything.

**Drill diameters must be declared, and Gatema's default is the dangerous
one.** The handbook says outright: *"Pokud nebude žádná poznámka, výrobce DPS
předpokládá, že jde o průměry výsledné"* — with no note, the numbers are read
as finished holes, and a plated hole loses about 0.1 mm to the plating. That
default happens to be what this board wants, and it is still stated explicitly
in the enquiry, because the one hole that cannot absorb the error is J1/J2 at
1.02 mm (3.7). The wording to send:

> Průměry prokovených otvorů (`canfuel-PTH.drl`: 0,30 / 0,80 / 0,90 / 1,00 /
> 1,02 mm) jsou **výsledné** rozměry po prokovení. Otvory v
> `canfuel-NPTH.drl` (3,00 a 3,20 mm) jsou **neprokovené**, vrtaný rozměr =
> výsledný.

**Their standard plated-hole tolerance is wider than Molex's, and it still
passes.** Gatema quotes ±0.08 mm standard (±0.05 mm on request) against the
drawing's ±0.05 mm, so the worst case is a 0.94 mm hole where Molex allows
0.97 mm. It does not matter: the pin is 0.64 mm square, diagonal 0.905 mm, so
even 0.94 mm leaves 0.035 mm of clearance. **Do not pay for the tighter
tolerance class.** The NPTH tolerance is ±0.05 mm, which matches the peg hole's
band exactly, so a 3.00 mm nominal lands inside Molex's 2.95–3.05 at both
extremes.

**The board is 1.5 mm, not 1.6 mm, and it was changed to match the order.**
Gatema's POOL service sells fixed stack-ups and the two-layer ones are all
1.5 mm; the chosen preset is *2V Cu 35/35 µm, 1,5 mm, LF HAL, 2x zelená NM, 1x
bílý potisk, Tg 135 °C*. Nothing on this board depends on the 0.1 mm: the via
aspect ratio goes from 1:5.3 to 1:5.0 against a 1:10 limit, lead-free HAL wants
0.8–2.5 mm, and SD-43045-001 *recommends* 1.57 mm for the Micro-Fit — 1.5 mm is
0.07 mm under it, which is the safe direction for a snap-in peg because the
barb protrudes further below the board.

What did matter is that `canfuel-job.gbrjob` declared `BoardThickness: 1.6`.
Ordering 1.5 mm while shipping a job file that says 1.6 mm is the kind of
contradiction a CAM operator either queries or silently resolves the wrong way,
and it defeats the whole reason `fab/` is committed. So `(general (thickness))`
is 1.5 and the core is 1.41 mm, and the outputs were regenerated. **The number
lives in `(general (thickness))`, not in the stackup sum** — editing only the
core left `GetBoardThickness()` reporting 1.600, which is how the second edit
was found.

**Copper is 35 µm and the reason is not current.** An 18 µm preset was offered
and is cheaper. At 18 µm the 0.80 mm power track still carries about 1.26 A by
IPC-2221 for a 10 °C rise, against this board's 77 mA worst-case peak, so
electrically either would do. It is 35 µm because the board file's stackup and
the `.gbrjob` both declare 35 µm, and a delivered board that disagrees with its
own documentation is the thing `fab/` exists to prevent.

**No assembly stencil.** The POOL configurator offers one and it is the wrong
purchase twice over. It is offered *Pro vrchní stranu*, and `F.Paste` has zero
drawing commands — the top side has no SMD pads at all, so that stencil would
be a blank sheet of steel. Even a bottom one would cover `B.Paste`'s two
flashes, which are C7's pads, on a board that is hand-soldered throughout.

**No surcharges apply.** Construction class 7 (+10 %) starts at 150 µm track or
gap and this board is at 200 µm; the drill-density surcharge starts at 1001
holes/dm² and this board has 97 holes on 0.2475 dm², or 392/dm². Board
thickness 1.6 mm and lead-free HAL are both base price.

**Not published on their page, so ask:** whether a ZIP of the gerbers is
enough and whether Protel extensions are fine, copper-to-edge clearance (this
board holds 0.30 mm against their 0.200 mm for milled outlines), lead times and
price. ODB++ is their preferred format and `kicad-cli pcb export odb` produces
it, so it is worth offering.

---

## 7. Purchase list

Only now, and derived from `fab/canfuel-bom.csv` — not typed out by hand.
Cross-check against `bom-purchase.pdf`.

- **From the drawer:** U1 (PIC18F25K80).
- **Buy new:** MCP2562-E/P, Y1, every capacitor, every resistor, both sockets,
  J1/J2 and their crimp housings, headers, LEDs.
- **For the harness, not the board:** SIBA 179120.0.2 fuse (200 mA, time-lag T,
  5 × 20) and inline holder K23411. These are not in `fab/canfuel-bom.csv` and
  never will be — the BOM comes from the schematic and the fuse is not on it.
  Buy a spare fuse; a blown one behind the dash is worth having a second of.
  See 9.2.

Electrolytics age unpowered and an unmarked crystal has an unknown load
capacitance — both are cheap enough that reusing them is a false economy.
Resistors and LEDs are not in that category and come from the drawer.

**C6 is a 105 °C part and needs no second thought.** It is GME 127-040, a
Hitano `EXR` 10 µF 16 V in 5 × 11 — `hitano-exr-datasheet.pdf`, which gives
−40 to +105 °C and a 2000 hour load life at 105 °C with rated ripple for the
5 mm case. Halving the temperature stress doubles that, so at the 50–60 °C a
closed vent reaches in summer it is tens of thousands of powered hours, and the
board is only powered while the display is. It carries no ripple worth the name
either — total draw is under 30 mA. This was the last open question on the
board and it is closed.

That same datasheet settles §3.5 from the other direction. Its case table gives
this exact part an impedance of **4.70 Ω at 100 kHz**, against the 5 Ω ceiling
DS39977C Table 31-4 puts on the VCAP capacitor. Had the six of them bought for
C6 been pressed into service on pin 6 as well — which is exactly the mistake
the shape of the order invited — the part would have sat at 94 % of the limit
with nothing left for tolerance or temperature.

---

## 8. Committing work on a board

**One rule, and it outlives this board:** every commit leaves CI green. If the
schematic needs several passes, that is fine — but never commit one that fails
ERC, because then a red CI run stops meaning anything.

The commit-by-commit account of how this board was built is git history and is
not duplicated here.

---

## 9. Open questions

**There are none left.** The table that used to be here held one row, the 4-pin
connector for the car side of the harness, and that is settled: the connector
exists and is fitted, so the loom is a re-crimp onto longer wires rather than a
choice to make. C6's temperature class was the other and is settled in section
7: it is a 105 °C part.

Every part is bought, the harness fuse and holder included. **Nothing blocks
the layout, and nothing blocks fabrication either.** The enclosure blocked the
layout once, and there is no longer going to be one.

### 9.1 The enclosure was dropped, and why

It bought nothing here. Everything around the board in the vent is plastic, so
there is no metal to short against; the vent is closed off by a flap, so no
air, no dust worth the name and no water; and the board is invisible either
way. That leaves mechanical retention, which a box is a poor way to buy.

The measurement made it worse rather than better. The available space was only
ever an estimate — the MFD15 sits in the way and the depth cannot be measured
around it — and the closest off-the-shelf candidate, a Hammond 1550Q at
60 × 55 × 30.10 mm, came out exactly at the estimate on two axes and 0.1 mm
over on the third. Its 3 mm die-cast walls would also have forced corner
notches in the board, added an isolation and grounding decision that a plastic
box does not, and required a slot filed through cast aluminium for the
Micro-Fit connectors.

Dropping it inverts the risk that section 9 used to carry. The M3 holes no
longer have to hit anything, so they stopped being the thing that could force a
respin and became cheap insurance instead: any later mounting scheme is
designed around them.

**Mounting, as decided:** four nylon M3 standoffs in the holes, their feet
stuck to the floor of the vent with automotive-grade double-sided tape (3M VHB
or equivalent). Standoffs rather than tape straight onto the board because the
through-hole solder joints must not bear on anything, and VHB rather than
ordinary foam tape because a dashboard reaches 50–60 °C in summer and cheap
adhesive lets go there.

**Rejected:** wrapping the board in PVC or Tesa tape. At dashboard temperatures
the adhesive creeps, ends up smeared across the board, collects dust, works its
way into the sockets and makes any future repair miserable — and the insulation
it provides guards against metal that is not there.

Resolved earlier: the core supply (3.5 — no ENVREG, 10 µF on pin 6), the LED
pin assignment (RC0/RC1, see 3.6) and the escape header — which at the time
resolved as "2×8, it goes on", and was then removed on 2026-08-09 once routing
put a number on what it cost (5.4).

### 9.2 The 5 V feed is fused — in the harness, not on the board

The board takes 5 V straight from the display and has no protection of its own.
A short anywhere on it — a bridged solder joint, a failed electrolytic — is
therefore a short across the MFD15's 5 V rail. Adding a fuse closes that.

**It goes in the loom, not on the PCB, and that is a measured decision.** The
largest free rectangle left on the board is 12.2 × 15.2 mm, at x 92–104.5,
y 72–87.5; a 5 × 20 mm holder lying flat needs about 24 × 7 mm and there is no
rectangle that size anywhere on the board. The alternatives were a vertical
holder standing ~25 mm tall — against a vent depth that has never been
measurable, because the MFD15 is in the way — or soldering the fuse down, which
gives up the one thing a cartridge fuse is for. In the loom it costs the board
nothing: the schematic, the PCB and all four checks are untouched.

Access is the reason a cartridge fuse beats a resettable PTC here, and it comes
from the car, not a datasheet: pulling the MFD15 out of the vent exposes this
part of the loom, so replacing a blown fuse does not mean dismantling the
dashboard.

**The parts.** SIBA **179120.0.2** — 200 mA, 250 V, 5 × 20 mm, glass, time-lag
T to IEC 60127-2/3 (`siba-179120-fuse-datasheet.pdf`, doc G79120-30 Rev. 0) —
in inline cable holder **K23411** (`fuse-holder-5x20-datasheet.pdf`), which
takes a 5.2 × 20 mm fuse and comes with 200 mm of lead. Its body is about
46 mm long and 10.5 mm across, so it needs a straight run of loom that length
and it must not be buried where it cannot be unscrewed.

That drawing is the whole of the holder's datasheet: it carries no ratings. The
6.3 A / 250 V AC figure is from the GME product page, which is a shop listing
and not a manufacturer document — recorded here as such. It does not matter
much either way, since the fuse in it is rated 200 mA and the circuit runs at
5 V.

**Why 200 mA, from the datasheet's own table.** The row for 200 mA gives a
voltage drop of **500 mV** at rated current, 0.3 W dissipation at 1.5 In and a
melting integral of **0.7 A²s**. Both numbers decide something:

- *The drop.* 500 mV at 200 mA is 2.5 Ω while the element is hot, and that is
  not negligible against the 0.51 V of headroom between the 5.01 V measured at
  C6/C12 and the 4.5 V minimum DS20005167C §2.2 puts on the MCP2562's VDD. It
  is survivable because **C6 and C7 are downstream of the fuse**: the 45–70 mA
  the transceiver draws during dominant bits comes out of 20 µF of local
  capacitance, and the fuse only ever sees the average, which is under 30 mA.
  At 30 mA even the hot resistance gives 75 mV. Had the bulk capacitor been
  left on the display side of the fuse, this would not work.
- *The melting integral.* Charging those same 20 µF from 5 V through a loom of
  well under an ohm is an I²t of the order of 10⁻³ A²s, three orders below
  0.7 A²s. Inrush cannot nuisance-blow it, which is what the time-lag
  characteristic was chosen for in the first place.

**Why it protects what it is meant to.** The display's limit is 0.5 A. The
fusing-time limits in the same datasheet, for the 125 mA – 6.3 A group:

| | 1.5 In = 0.30 A | 2.1 In = 0.42 A | 2.75 In = 0.55 A | 4 In = 0.80 A | 10 In = 2.0 A |
| --- | --- | --- | --- | --- | --- |
| min | 1 h | 600 ms | 150 ms | 20 ms | — |
| max | — | 2 min | 10 s | 3 s | 300 ms |

Any fault heavy enough to exceed the display's 0.5 A opens the fuse inside
10 s, and a hard short inside 300 ms. Normal running is 30 mA, 15 % of rating,
nowhere near the 1 hour it is guaranteed not to open at 0.30 A. The band it
does not cover is 0.30–0.42 A sustained — and that is below the display's limit
anyway, so nothing there needs covering.

**What it does not protect.** The fuse sits at the vent end of the loom, where
it is reachable. The run from plug C to the fuse is therefore unfused. That is
deliberate: the fault this exists for is on the board, and that section of loom
lies inside the dashboard without movement. Moving the fuse to the plug C end
would cover the cable too, at the price of the access that made a cartridge
fuse the right choice.

`harness.md` section B has the wiring steps.

---

## 10. What has actually been read out of the datasheets

The sourcing rule in `CLAUDE.md` is only worth anything if it is possible to
tell which numbers were checked and which were inherited. This is the checked
list, as of the re-review on 2026-08-08.

**DS39977C — PIC18F25K80**

| Section / page | What it settles                                      |
| -------------- | ---------------------------------------------------- |
| page 6         | The 28-pin SSOP/SPDIP/SOIC pinout, every pin in 4.2. Pin 6 is VDDCORE/VCAP, there is no RA4, CANTX/CANRX are on RB2/RB3 and again on RC6/RC7 |
| 2.1, Fig 2-1   | The pins that must always be connected; AVDD/AVSS exist only on the larger packages |
| 2.2.1          | 100 nF ceramic low-ESR on every supply pin pair, within 6 mm, same side of the board |
| 2.2.2          | Tank capacitor 4.7–47 µF where power traces exceed six inches — C6 |
| 2.3, Fig 2-2   | The MCLR network of 4.3a: R1 ≤ 10 kΩ, R2 ≤ 470 Ω, C1 on a jumper, all within 6 mm of the pin |
| 2.4, Table 2-1 | VCAP: 10 µF low-ESR (< 5 Ω), ceramic or tantalum, never to VDD, track under 6 mm; the 0.1 µF figure belongs to the LF part; Table 2-1 names the fitted GRM32DR71C106KA01L |
| 2.5            | No pull-ups, series diodes or capacitors on PGC/PGD; optional ≤ 100 Ω series resistor for ESD |
| 2.6            | Oscillator placement: 12 mm, load caps at the crystal, grounded pour with nothing routed inside it, nothing on the far side under the crystal |
| 2.7            | Unused I/O driven low as outputs, or 1–10 kΩ to VSS |
| 3.5, Table 3-3 | Crystal capacitor guidance, and note 3 deferring to the crystal manufacturer; note 2 on Rs for low drive level |
| page 541       | Absolute Maximum Ratings — the 2 mA on PORTA<5:0> behind 3.6 |
| D001           | VDD 1.8–5.5 V for F devices |
| D080, D090     | VOL/VOH, and the contradiction with page 541 discussed in 3.6 |
| Table 31-4     | CEFC 4.7 µF min, 10 µF typ, low-ESR |

**DS20005167C — MCP2561/2**

| Section        | What it settles                                      |
| -------------- | ---------------------------------------------------- |
| page 1         | MCP2562 DIP-8 pinout — the table in 3.1; the MCP2561's pin 5 is SPLIT, ours is VIO |
| 1.1.1, 1.1.2, Table 1-1 | STBY low is Normal, high is Standby |
| 1.7.9          | STBY has an internal MOS pull-up, typ 660 kΩ at 5 V — floating means Standby |
| 1.7.6          | VIO supplies TXD, RXD and STBY |
| Fig 1-2        | Application circuit: 0.1 µF on VDD and on VIO |
| 2.2            | VDD 4.5–5.5 V, VIO 1.8–5.5 V |
| Abs max        | CANH/CANL −58 V to +58 V, transients −150 V to +100 V, ±8 kV IEC 61000-4-2 |

**Crystal datasheet**

| What                     | Value                                            |
| ------------------------ | ------------------------------------------------ |
| Loading capacitance      | 20 pF standard, 8–33 pF available — behind 3.2   |
| Part number example      | `FTX16.000M20S-30/30B`: 16.000 MHz, 20 pF, HC49/S |
| Drive level              | 100 µW typical, 500 µW max                       |
| ESR, 14–40 MHz           | 30 Ω max                                         |
| Dimensions               | 11.40 × 4.80 max, H ≤ 3.5 mm, leads 4.88 ± 0.2 mm |

**Hitano EXR — C6**

| What                     | Value                                            |
| ------------------------ | ------------------------------------------------ |
| Temperature range        | −40 to +105 °C                                   |
| Load life, 5 mm case     | 2000 h at 105 °C with rated ripple               |
| Shelf life               | 1000 h at 105 °C, no voltage applied             |
| 10 µF 16 V, 5 × 11       | impedance 4.70 Ω at 100 kHz, ripple 74 mA rms    |

That last row matters for 5.2: the KiCad footprint is
`Crystal:Crystal_HC49-U_Vertical`, whose pads are 4.88 mm apart and therefore
correct, but whose 3D model is the taller HC-49/U can. The real part is the
shorter /US. The 3D check in 5.5 will show it standing taller than it is —
that is the model, not a clearance problem.

**Not settled by any datasheet, and deliberately so:** the display's connector
pinout (C6/C12/C7/C8) and the fact that the car's bus is already terminated at
both ends. Both were measured on the car. They are noted as measured wherever
they appear.
