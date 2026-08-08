# canfuel — implementation plan

How to get from an empty repository to an ordered board. The requirements in
the root `CLAUDE.md` are the input and are treated as settled; this document
turns them into reference designators, nets, pin numbers and a sequence of
commits.

Read the four killer checks in section 3 before drawing anything.

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
| Y1        | 16 MHz crystal, CL = 32 pF  | HC-49/S                                 | new; see `crystal-datasheet.pdf`       |
| C1, C2    | 33 pF C0G                   | 2.54 mm THT                             | **33 pF, not 22 pF**                   |
| C3        | 100 nF X7R                  | 2.54 mm THT                             | U1 VDD (pin 20)                        |
| C4        | 100 nF X7R                  | 2.54 mm THT                             | U2 VDD (pin 3)                         |
| C5        | 100 nF X7R                  | 2.54 mm THT                             | U2 VIO (pin 5)                         |
| C6        | 10 µF electrolytic, 16 V    | 5 mm THT radial                         | supply input; new part, they age       |
| C7        | 10 µF low-ESR ceramic, 16 V | 2.54 mm THT                             | **mandatory** — U1 VDDCORE/VCAP, see 3.5 |
| R1        | 10 kΩ                       | 1/4 W THT                               | MCLR pull-up                           |
| R2        | 10 kΩ                       | 1/4 W THT                               | RA0 pull-down (debug jumper)           |
| R3, R4    | 1 kΩ                        | 1/4 W THT                               | LED series resistors                   |
| R5        | 120 Ω                       | 1/4 W THT                               | **DO NOT FIT** — see 3.3               |
| D1        | LED green                   | 3 mm THT                                | power / heartbeat                      |
| D2        | LED yellow                  | 3 mm THT                                | CAN status                             |
| J1, J2    | Molex Micro-Fit 3.0 43045-0400 | right-angle, board mount             | wired in parallel — see 3.4            |
| J3        | 5-pin header 2.54 mm        | 1×5                                     | ICSP                                   |
| J4        | 2×8 header 2.54 mm          | 2×8                                     | escape hatch — see 5.4                 |
| JP1       | 2-pin header + jumper       | 1×2                                     | debug enable on RA0                    |
| —         | DIP-28 socket, narrow       |                                         | new                                    |
| —         | DIP-8 socket                |                                         | new                                    |

---

## 3. The four things that quietly kill this board

Check each one twice while drawing, and again during the ERC pass. All four
are now on the sheet as drawn, and all four are repeated as numbered notes in
the schematic's own notes panel so they survive without this file.

### 3.1 MCP2562 VIO and STBY

The single easiest mistake in the design. Without these the transceiver sits in
standby and transmits nothing, while everything else measures fine.

MCP2562 DIP-8 pinout:

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

### 3.2 Crystal loading is 33 pF

Y1 has CL = 32 pF, so C1 = C2 = **33 pF**, not the 22 pF that gets fitted by
reflex. Verified on a previous project. Use C0G/NP0, not X7R.

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
  Table 31-4 gives CEFC as min 4.7 µF, typ 10 µF. The datasheet's own example
  part is a TDK C3216X7R1C106K (10 µF X7R 16 V).
- ⚠ **Pin 6 must never be connected to VDD.** That is the regulator's output,
  not an input. Tying it to 5 V destroys the part.
- Keep the trace to the capacitor **under 6 mm** (datasheet: 0.25 inch).

Without C7 the regulator is unstable and the part browns out or never starts —
and because the symptom is intermittent it is a genuinely nasty one to debug.
The 0.1 µF figure that turns up in forum posts is for the LF variant, where the
regulator is disabled. Not this part.

**Available port A pins.** With the crystal on pins 9/10, RA6 and RA7 are gone
and pin 6 is not a port pin, so port A offers exactly four usable pins:
**RA0 (2), RA1 (3), RA2 (4), RA3 (5), RA5 (7)** — five, of which RA0 is the
debug jumper. Port A is tight; do not plan on more.

---

## 4. Schematic — done

One A3 sheet. A4 was tried first and everything collided; the parts count is
low but the label count is not.

### 4.1 Nets

```
+5V      SGND      CANH      CANL
CAN_TX   CAN_RX    OSC1      OSC2
~MCLR    PGC       PGD       VCAP
LED_PWR  LED_CAN   DBG_EN
LED_PWR_A          LED_CAN_A            (resistor to LED anode)
CANTX2   CANRX2                         (RC6/RC7, the ECAN alternates)
ESC_RA3  ESC_RA5   ESC_RC0 … ESC_RC5
ESC_RB0  ESC_RB1   ESC_RB4   ESC_RB5
```

31 nets in total. `SGND` is the ground net name throughout, not `GND` — it is
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
| C6      | `Device:C_Polarized`                  | `Capacitor_THT:CP_Radial_D5.0mm_P2.50mm`                       |
| C7      | `Device:C`                            | `Capacitor_THT:C_Disc_D7.5mm_W5.0mm_P5.00mm`                   |
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
| 1   | MCLR/RE3      | R1 (10 kΩ) to +5V, and J3 pin 1. **No capacitor on this pin.** |
| 2   | RA0/AN0       | JP1 to +5V, R2 (10 kΩ) to SGND → `DBG_EN`                     |
| 3   | RA1/AN1       | R3 → D1 (`LED_PWR`)                                           |
| 4   | RA2/AN2       | R4 → D2 (`LED_CAN`)                                           |
| 5   | RA3/AN3       | J4 (escape)                                                   |
| 6   | **VDDCORE/VCAP** | **C7 (10 µF low-ESR) to SGND. Never to +5V.** See 3.5      |
| 7   | RA5/AN4       | J4 (escape)                                                   |
| 8   | VSS           | SGND                                                          |
| 9   | OSC1/CLKIN/RA7| Y1 + C1                                                       |
| 10  | OSC2/CLKOUT/RA6| Y1 + C2                                                      |
| 11  | RC0/SOSCO     | J4 (escape)                                                   |
| 12  | RC1/SOSCI     | J4 (escape)                                                   |
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

- D1 anode ← R3 ← RA1 (pin 3) → `LED_PWR`, cathode to SGND
- D2 anode ← R4 ← RA2 (pin 4) → `LED_CAN`, cathode to SGND

Firmware only drives them when `DBG_EN` reads high, i.e. when the JP1 jumper is
fitted. R2 pulls RA0 down, so an absent jumper is a defined low, not a floating
input.

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

### 4.4 Power

+5V and SGND enter on J1/J2. C6 (10 µF) across the input, C3/C4/C5 (100 nF) at
each supply pin. No regulator, no reverse-polarity diode, no TVS — that was
decided; the 12 V branch is not on this board. Total draw is under 30 mA
against the display's 0.5 A limit, so there is no thermal question to answer.

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
in sections 3 and 4 above — 97 connections, 31 nets, 22 components, no pin in
the netlist unaccounted for and none missing. It catches the RB2/RB3 swap
above. Needs `kicad-cli` on PATH; exits nonzero on any mismatch.

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

Rules behind that sketch:

- Y1 with C1/C2 as close to U1 pins 9/10 as physically possible, ground the
  crystal case, and keep the CAN nets away from it.
- U2 between U1 and the connectors — CANH/CANL should be short and never cross
  the crystal.
- C3/C4/C5 each within a few millimetres of the pin they decouple, on the same
  side as the pin.
- **C7 hard against U1 pin 6** — the datasheet caps that trace at 6 mm. Place
  it before routing anything else; it is the one component with a numeric
  placement constraint.
- J1/J2 on the same long edge so the harness leaves in one direction; the vent
  has no room for cables on two sides.
- D1/D2/JP1 grouped where they are visible without disassembling anything.

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

| Row | Pins                                                        |
| --- | ----------------------------------------------------------- |
| A   | RA3 (5), RA5 (7), RC0 (11), RC1 (12), RC2 (13), RC3 (14), RC4 (15), RC5 (16) |
| B   | RC6 (17), RC7 (18), RB0 (21), RB1 (22), RB4 (25), RB5 (26), +5V, SGND |

There is no RA4 on this package (pin 6 is VDDCORE/VCAP), so it is not in the
list. Put RC6/RC7 next to each other and label them `CANTX2`/`CANRX2` on the
silkscreen — they are the ECAN alternates from 4.2 and the whole point of the
header is that someone finds them in a hurry.

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
the LED pin assignment (RA1/RA2) and the escape header (2×8, it goes on).

The last one is the only one that can force a board respin: the M3 hole
positions in 5.1 are a guess until the enclosure is measured. Measure it before
ordering, not after.
