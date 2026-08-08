# canfuel — implementation plan

How to get from an empty repository to an ordered board. The requirements in
the root `CLAUDE.md` are the input and are treated as settled; this document
turns them into reference designators, nets, pin numbers and a sequence of
commits.

Read the killer checks in section 3 before drawing anything.

**Every electrical number below is cited to a manufacturer datasheet**, per the
sourcing rule in `CLAUDE.md`. The three documents are in `docs/`:

| Short form   | Document                                              |
| ------------ | ----------------------------------------------------- |
| `DS39977C`   | Microchip, PIC18F66K80 family — `pic18f25k80-datasheet.pdf` |
| `DS20005167C`| Microchip, MCP2561/2 — `mcp2562-datasheet.pdf`        |
| crystal d/s  | HC-49U/S DIP quartz crystal resonator — `crystal-datasheet.pdf` |

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
M3 mounting holes are *not* in it — their positions depend on the enclosure
measurement, which is still open (section 9).

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
| J4        | 2×8 header 2.54 mm          | 2×8                                     | escape hatch — see 5.4                 |
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
in `can-pcb`, so none is fitted. If the oscillator misbehaves, RC0/RC1 and the
rest of J4 are next to it and a series resistor can be tacked in.

Microchip's own tables are guidance only and do not cover this case directly:
Table 3-3 (crystals, HS) lists 27 pF at 4 MHz, 22 pF at 8 MHz and 15 pF at
20 MHz with no 16 MHz row, and note 3 defers to the crystal manufacturer for
the right values. That is what the derivation above does.

### 3.3 No 120 Ω termination

The car's bus is already terminated at both ends. A third resistor overloads
it. R5 gets a footprint and silkscreen, and is **not fitted**:

- Place R5 across CANH/CANL near U2.
- Silkscreen next to it: `120R DNF`.
- Mark it `Do not populate` in the symbol's fields so it drops out of the BOM.

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
so **D1 and D2 are on RC0 (pin 11) and RC1 (pin 12)** and RA1/RA2 went to the
escape header instead. R3 and R4 stay at 1 kΩ.

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
| J4      | `Connector_Generic:Conn_02x08_Odd_Even` | `Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical`  |
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
| 3   | RA1/AN1       | J4 (escape) — 2 mA pin, see 3.6                               |
| 4   | RA2/AN2       | J4 (escape) — 2 mA pin, see 3.6                               |
| 5   | RA3/AN3       | J4 (escape)                                                   |
| 6   | **VDDCORE/VCAP** | **C7 (10 µF low-ESR) to SGND. Never to +5V.** See 3.5      |
| 7   | RA5/AN4       | J4 (escape)                                                   |
| 8   | VSS           | SGND                                                          |
| 9   | OSC1/CLKIN/RA7| Y1 + C1                                                       |
| 10  | OSC2/CLKOUT/RA6| Y1 + C2                                                      |
| 11  | RC0/SOSCO     | R3 → D1 (`LED_PWR`) — see 3.6                                 |
| 12  | RC1/SOSCI     | R4 → D2 (`LED_CAN`) — see 3.6                                 |
| 13  | RC2/T1G/CCP2  | J4 (escape)                                                   |
| 14  | RC3/SCL/SCK   | J4 (escape)                                                   |
| 15  | RC4/SDA/SDI   | J4 (escape)                                                   |
| 16  | RC5/SDO       | J4 (escape)                                                   |
| 17  | RC6/**CANTX**/TX1 | J4 (escape) — alternate ECAN pin, see below               |
| 18  | RC7/**CANRX**/RX1 | J4 (escape) — alternate ECAN pin, see below               |
| 19  | VSS           | SGND                                                          |
| 20  | VDD           | +5V, C3 (100 nF) to SGND, as close as the layout allows       |
| 21  | RB0/INT0      | J4 (escape)                                                   |
| 22  | RB1/INT1      | J4 (escape)                                                   |
| 23  | RB2/**CANTX** | `CAN_TX` → U2 pin 1                                           |
| 24  | RB3/**CANRX** | `CAN_RX` → U2 pin 4                                           |
| 25  | RB4/AN9       | J4 (escape)                                                   |
| 26  | RB5/T0CKI     | J4 (escape)                                                   |
| 27  | RB6/**PGC**   | `PGC` → J3 pin 5                                              |
| 28  | RB7/**PGD**   | `PGD` → J3 pin 4                                              |

**The ECAN module can be remapped.** CANTX/CANRX are available on RB2/RB3
*and* on RC6/RC7. Both alternates land on J4, so if RB2/RB3 turn out to be
wrong — wrong config bit, damaged pin, anything — the fix is two wire links on
the escape header rather than a new board. Worth knowing before ordering.

LEDs, driven by the PIC so nothing lights up in the car:

- D1 anode ← R3 ← RC0 (pin 11) → `LED_PWR`, cathode to SGND
- D2 anode ← R4 ← RC1 (pin 12) → `LED_CAN`, cathode to SGND

Port C, not port A — see 3.6, and do not move them back.

Firmware only drives them when `DBG_EN` reads high, i.e. when the JP1 jumper is
fitted. R2 pulls RA0 down, so an absent jumper is a defined low, not a floating
input.

**Unused pins are a firmware obligation, not just a header.** DS39977C 2.7:
unused I/O should be configured as outputs driven low, or given a 1–10 kΩ
resistor to VSS. The fourteen pins on J4 sit at a header with nothing on the
other end, so the firmware in the `canfuel` repository has to drive them low at
start-up. There is no resistor for this on the board — fourteen of them would
cost more area than the header.

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
see an ESD event. This connector lives inside a closed enclosure behind a
dashboard and is touched perhaps twice in the board's life, so nothing is
fitted. Revisit only if the header is ever brought outside the case.

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
in sections 3 and 4 above — 103 connections, 33 nets, 25 components, no pin in
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

- Board **55 × 45 mm**, 2 layers, corners rounded R2 — already drawn in the
  skeleton commit (section 1). Four M3 mounting holes inset 4 mm from the
  corners still to add, and see section 9 before trusting those positions.
- Enclosure is 65 × 55 mm with max ~30 mm depth, so the tallest part
  (C6 electrolytic, or J4 with a cable on it) sets the height budget. Keep
  everything under ~20 mm to leave room for the lid and the harness bend.
- Mostly through-hole; hand assembly.

### 5.2 Placement

```
        55 mm
  ┌───────────────────────────┐
  │  J3 ICSP        J4 escape │  ← top edge, both reachable with the lid off
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
  tightest cluster on the board; lay it out before the escape header, not after.
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
  JP2 reachable with the lid off — it has to come out for every programming
  session.

### 5.3 Net classes

| Class   | Nets              | Track width | Clearance |
| ------- | ----------------- | ----------- | --------- |
| Default | signals           | 0.25 mm     | 0.20 mm   |
| Power   | +5V, SGND         | 0.80 mm     | 0.20 mm   |
| CAN     | CANH, CANL        | 0.40 mm     | 0.20 mm   |

Route CANH/CANL as a pair, side by side, equal length, no stubs beyond the DNF
R5 pads. Pour SGND on both layers and stitch the pours with vias, but do not
let the pour split the ground under the crystal.

### 5.4 J4 — escape hatch

The unused pins, brought out so a design error can be patched with a wire
rather than a new board. A 2×8 header is 20 × 5 mm — about 4 % of the board
area, which settles the open question in `CLAUDE.md` in favour of fitting it.

Bring out all 14 unused I/O pins, plus power, which fits a 2×8 header exactly:

| Row | J4 pins   | Signals                                                   |
| --- | --------- | --------------------------------------------------------- |
| A   | 1,3,…,15  | RA1 (3), RA2 (4), RA3 (5), RA5 (7), RC2 (13), RC3 (14), RC4 (15), RC5 (16) |
| B   | 2,4,…,16  | RC6 (17), RC7 (18), RB0 (21), RB1 (22), RB4 (25), RB5 (26), +5V, SGND |

There is no RA4 on this package (pin 6 is VDDCORE/VCAP), so it is not in the
list. RC0 and RC1 are not either — they drive the LEDs, and RA1/RA2 took their
place here when the LEDs moved (3.6). Row A runs in pin order so it can be read
off in a hurry, which is the header's entire purpose.

**Mark the weak pins on the silkscreen.** RA1, RA2, RA3 and RA5 are the 2 mA
pins of 3.6; someone patching a wire onto this header a year from now will not
remember that. Print `RA1 2mA` and so on, or a shared legend.

Put RC6/RC7 next to each other and label them `CANTX2`/`CANRX2` — they are the
ECAN alternates from 4.2.

### 5.5 DRC

```
kicad-cli pcb drc --exit-code-violations canfuel/canfuel.kicad_pcb
```

Iterate until it exits 0. Then, separately from DRC, do the checks a tool
cannot do: run the 3D viewer and confirm the socket, the electrolytic and both
Micro-Fit bodies do not collide, and print the board 1:1 on paper and drop the
real connectors onto it.

**Definition of done:** DRC clean, committed, CI green.

---

## 6. Fabrication outputs

Generated into `canfuel/fab/` and **committed** — for an ordered board it must
be possible to recover exactly what was sent.

```
fab/gerbers/    gerbers + drill files
fab/canfuel-bom.csv
fab/canfuel-cpl.csv
```

```
kicad-cli pcb export gerbers --output canfuel/fab/gerbers canfuel/canfuel.kicad_pcb
kicad-cli pcb export drill   --output canfuel/fab/gerbers canfuel/canfuel.kicad_pcb
kicad-cli sch export bom     --output canfuel/fab/canfuel-bom.csv canfuel/canfuel.kicad_sch
kicad-cli pcb export pos     --output canfuel/fab/canfuel-cpl.csv canfuel/canfuel.kicad_pcb
```

The CPL is generated for completeness only — every part here is through-hole
and hand-soldered, so no assembly house will use it.

Check before ordering: R5 must be absent from the BOM, and the gerber silk
layer must actually carry the `120R DNF` legend.

---

## 7. Purchase list

Only now, and derived from `fab/canfuel-bom.csv` — not typed out by hand.
Cross-check against `bom-purchase.pdf`.

- **From the drawer:** U1 (PIC18F25K80).
- **Buy new:** MCP2562-E/P, Y1, every capacitor, every resistor, both sockets,
  J1/J2 and their crimp housings, headers, LEDs.

Electrolytics age unpowered and an unmarked crystal has an unknown load
capacitance — both are cheap enough that reusing them is a false economy.

---

## 8. Sequence of commits

1. `Add KiCad project skeleton for canfuel` — CI goes live
2. `Draw canfuel schematic` — ERC clean
3. `Lay out canfuel PCB` — DRC clean
4. `Add canfuel fabrication outputs`
5. `Add canfuel purchase list`

Each commit should leave CI green. If step 2 needs several passes, that is
fine — but do not commit a schematic that fails ERC, because then a red CI run
stops meaning anything.

---

## 9. Open questions

| Question                                    | Blocks       | Owner    |
| ------------------------------------------- | ------------ | -------- |
| 4-pin connector for the car side at GME     | harness only | not this board |
| Enclosure drawing and how the board mounts  | mounting holes | needs `docs/mechanical.md` |

Resolved while writing this: the core supply (3.5 — no ENVREG, 10 µF on pin 6),
the LED pin assignment (RC0/RC1, see 3.6) and the escape header (2×8, it goes
on).

The last one is the only one that can force a board respin: the M3 hole
positions in 5.1 are a guess until the enclosure is measured. Measure it before
ordering, not after.

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

That last row matters for 5.2: the KiCad footprint is
`Crystal:Crystal_HC49-U_Vertical`, whose pads are 4.88 mm apart and therefore
correct, but whose 3D model is the taller HC-49/U can. The real part is the
shorter /US. The 3D check in 5.5 will show it standing taller than it is —
that is the model, not a clearance problem.

**Not settled by any datasheet, and deliberately so:** the display's connector
pinout (C6/C12/C7/C8) and the fact that the car's bus is already terminated at
both ends. Both were measured on the car. They are noted as measured wherever
they appear.
