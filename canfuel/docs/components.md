# What each passive does, and the physics that sizes it

`implementation-plan.md` records **what was chosen** for every reference
designator and which datasheet section forced it. This file answers the
question that sits underneath: **why does the physics need a part there at
all**, and why is it that value rather than one an order of magnitude away.

Nothing here overrides the plan. Where the two touch, the plan is the
specification and this is the reasoning; §3.2, §3.5, §4.3a, §4.4 and §9.2 are
the sections it leans on.

**The eight capacitors on this board do six unrelated jobs.** They are not one
family in different sizes. Two of them are not on the supply rail at all, and
one of them is not a bypass capacitor in any sense — it is a regulator's
compensation network. Confusing them is how a board gets a 100 nF part where a
10 µF one was required, which compiles, assembles and fails.

| Ref | Value | Job | Timescale it works on |
|---|---|---|---|
| C3, C4, C5 | 100 nF X7R | supply decoupling | tens of nanoseconds |
| C6 | 10 µF electrolytic | bulk / tank | microseconds to milliseconds |
| C7 | 10 µF X7R | core regulator compensation | the regulator's loop, not a rail |
| C1, C2 | 33 pF C0G | crystal load | 62.5 ns per cycle, continuously |
| C8 | 100 nF X7R | MCLR reset filter | ~1 ms |

---

## 1. The load this board presents, and how fast it changes

Every number below is driven by one fact: **the transceiver's supply current is
not constant, and the step is large compared with everything else on the
board.**

| | typ | max | Source |
|---|---|---|---|
| U1, PIC18F25K80 at FOSC = 16 MHz, VDD = 5 V, regulator enabled | 2.2 mA | 6 mA | DS39977C §31.2, *Supply Current (IDD)*, FOSC = 16 MHz row |
| U2, MCP2562, bus **recessive** | 5 mA | 10 mA | DS20005167C §2.2, *Supply Current*, `VTXD = VDD` |
| U2, MCP2562, bus **dominant** | **45 mA** | **70 mA** | DS20005167C §2.2, `VTXD = 0V` |
| D1 + D2, only with JP1 fitted | 6.4 mA | — | plan, *LED colour is free*: 3.2 mA each at Vf ≈ 1.8 V |
| R1 + R6 across the rail | 0.48 mA | — | 5 V / 10.47 kΩ |

Three totals follow, and they are three different questions:

- **Continuous, in the car** (JP1 off, bus idle between frames): about **8 mA**.
- **Continuous, worst case allowed by the datasheets**: about **16.5 mA**.
- **Instantaneous, while driving a dominant bit**: about **77 mA**.

The last one is the interesting one, because it is not a load — it is a **step**.
Going recessive → dominant, the board's draw rises by **40 mA typical, 60 mA
maximum**, and it does so inside the delay DS20005167C §2.3 parameter 3 bounds
at **70 ns** (`tTXD-BUSON`, TXD low to bus dominant). At 500 kbps that step can
repeat every 2 µs, indefinitely, for as long as the engine runs.

⚠ **Parameter 3 is a propagation delay, not a slew rate.** The datasheet
specifies no rise time for the supply current, so 70 ns is used here as the
window within which the step must have completed — an upper bound on the
timescale, not a measurement of it. A faster real edge only makes the case for
local capacitance stronger, never weaker.

---

## 2. C3, C4, C5 — decoupling, which means nanoseconds

**The physics.** Two relations do all the work in this file:

```
Q = C · V          charge stored in a capacitor
i = C · dV/dt      current is capacitance times rate of change of voltage
```

Read the second one backwards and it becomes the design tool: **a capacitor
asked to supply current `i` for a time `Δt` sags by `ΔV = i·Δt / C`.** That is
the only equation needed for C3–C6.

The counterpart on the supply side is the wire:

```
V = L · di/dt      voltage across an inductance is its rate of change of current
```

A wire is an inductor. It does not object to carrying current; it objects to
**changing** it, and the faster the change the harder it pushes back. That is
what makes a 1.4 m harness useless at nanosecond timescales, however thick the
copper is and however low its DC resistance.

**Applied here.** The 5 V feed reaches the board through roughly 1.4 m of loom
from the display. Taking **1 µH/m** as the inductance of ordinary loom wire —
⚠ **an order-of-magnitude estimate, not a datasheet figure; no document held in
this repository specifies it** — that is about 1.4 µH between the board and its
supply. Asking that inductance to deliver the transceiver's 40 mA step within
70 ns:

```
V = 1.4 µH × 0.04 A / 70 ns ≈ 0.8 V
```

**Most of a volt of collapse, on every dominant bit**, half a million times a
second, on a rail whose total headroom to the transceiver's own minimum is
0.5 V (§3 below). The estimate could be wrong by a factor of three in either
direction and the conclusion would not move: the harness cannot serve this
step, and the fix is not a better harness.

With 100 nF sitting at the pin, the same charge comes out of the capacitor
instead:

```
ΔV = i·Δt / C = 0.04 A × 70 ns / 100 nF ≈ 28 mV        (42 mV at the 60 mA max step)
```

Twenty-eight millivolts against eight hundred. **That is the whole of what a
decoupling capacitor is for** — not storing energy, of which 100 nF has almost
none, but being physically close enough that no inductance stands between the
charge and the pin that needs it.

**Which is why DS39977C §2.2.1 is a placement rule as much as a value rule**:
100 nF, ceramic, low-ESR, and *"the trace length from the pin to the capacitor
is no greater than 0.25 inch (6 mm)"*. Exceed the 6 mm and the capacitor
acquires its own share of the inductance the exercise above was trying to
avoid, and stops being able to do the one thing it was fitted for.
`tools/check-placement.py` measures all three distances for exactly this
reason.

**Why three of them and not one.** §2.2.1 asks for decoupling *on every pair of
supply pins*. The board has three such pins — U1 VDD (pin 20), U2 VDD (pin 3),
U2 VIO (pin 5) — and the copper between any two of them is itself inductance.
One shared capacitor would be within 6 mm of at most one pin.

**Why X7R and not C0G here.** Only the capacitance matters, no frequency is
being set, and X7R gets far more capacitance into a 2.54 mm part than C0G. The
opposite trade-off applies to C1/C2 in §5.

---

## 3. C6 — bulk, which means microseconds

100 nF covers the edge. It cannot cover the **whole dominant bit**, and the
arithmetic says so immediately.

CAN inserts a stuff bit after five identical bits, so in normal traffic the
longest unbroken dominant run is five bit times = **10 µs** at 500 kbps:

```
Q = 40 mA × 10 µs = 400 nC
on 100 nF alone:   ΔV = 400 nC / 100 nF = 4 V      ← impossible
on 10.3 µF:        ΔV = 400 nC / 10.3 µF ≈ 39 mV   ← this is C6
```

That is the division of labour, and it is why one capacitor cannot replace two:
**C4 supplies the edge, C6 supplies the bit.** The short PCB track between them
is what separates their roles — its inductance is negligible over 10 µs and
decisive over 70 ns.

The worst case is not a stuffed frame but an error frame: an error flag is six
dominant bits and superimposed flags can reach twelve, with no stuffing. At
12 bits = 24 µs the same sum gives 960 nC and **93 mV** on 10.3 µF, still
comfortable.

**10.3 µF, not 20 µF.** The capacitance available to the transceiver is C6 plus
the three 100 nF parts. **C7 is not part of it** — it sits on VDDCORE, behind
the on-chip regulator, and a series pass regulator does not deliver charge
backwards into its own input. See §4.

**DS39977C §2.2.2 arrives at the same part from a different direction**: a tank
capacitor is asked for on boards whose power traces run longer than six inches,
sized *"based on the trace resistance ... and the maximum current drawn by the
device"* so as to meet an acceptable sag, with a range of 4.7 µF to 47 µF. A
1.4 m harness is well past six inches, so this is that case, and 10 µF sits in
the lower half of the range because the sums above show the lower half is
enough.

**C6 must stay downstream of the harness fuse, and that is load-bearing.** The
SIBA 179120.0.2 drops 500 mV at its rated 200 mA (plan §9.2), i.e. **2.5 Ω of
hot element**, against 0.51 V of headroom between the 5.01 V measured at the
display connector and the MCP2562's 4.5 V minimum. If the transceiver's 45–70 mA
dominant current had to cross that element, it would cost 110–175 mV of the
0.51 V on every dominant bit. Because C6 is on the board side of it, the fuse
only ever sees the **average**, which is under 30 mA — 75 mV. A bulk capacitor
on the display side of the fuse would not have worked.

---

## 4. C7 — a regulator's compensation capacitor, and nothing else

**Pin 6 is not a supply pin.** The 28-pin PIC18F25K80 has no RA4 and no ENVREG:
pin 6 is VDDCORE/VCAP, the **output** of an on-chip regulator that makes the
core rail from VDD. DS39977C §2.4 requires *"a low-ESR (< 5 Ω) capacitor ... to
stabilize the voltage regulator output voltage"*, of **10 µF**, and states
outright that the pin *"must not be connected to VDD"*.

**Stability, not storage.** A linear regulator is a feedback loop: it compares
its output against an internal reference and drives a pass device to correct
the difference. Every feedback loop has a phase margin, and the output
capacitor is part of the network that sets it. Too little capacitance, or too
much series resistance in it, and the loop's phase margin goes negative — the
regulator oscillates instead of regulating, and the core rail the CPU runs on
develops ripple that no amount of decoupling elsewhere can remove. This is why
§2.4 specifies both a value **and** an ESR ceiling, and why Figure 2-3 plots
ESR against frequency: the capacitor here is a circuit element inside a control
loop, not a reservoir.

Three consequences, all visible on the board:

- **Ceramic, not electrolytic.** An aluminium electrolytic's ESR is typically
  ohms, which is where §2.4's 5 Ω ceiling lives. §2.4 admits ceramic or tantalum
  and nothing else, and Table 2-1 names four ceramic parts outright — one of
  which, `GRM32DR71C106KA01L`, is what is fitted. C6 being the same nominal
  10 µF makes it look like a substitute. It is not.
- **The only SMD part on the board, on the bottom, under pin 6.** §2.4 puts the
  same 6 mm limit on this trace as §2.2.1 does on decoupling, for the same
  reason: inductance between the capacitor and the pin is inductance inside the
  control loop. As built it is 2.25 mm.
- **It cannot help the 5 V rail.** Charge in C7 is on the regulator's output
  side. It will hold the *core* up briefly while VDD sags, which is real but
  invisible, because the brown-out detector on VDD trips first (§5). It
  contributes nothing to the transceiver's dominant-bit current and nothing to
  ride-through of the 5 V rail.

---

## 5. How long the board survives a supply interruption

This is the question C6 gets asked most often, and its honest answer is
**shorter than intuition suggests, and it is not what C6 is for.**

The equation is the same one as everywhere else, rearranged for time:

```
Δt = C · ΔV / i
```

**The floor is not obvious, because there are two of them, and the higher one
belongs to the transceiver:**

- **4.5 V — the MCP2562 leaves its specified range.** DS20005167C §2.2 gives
  VDD as 4.5 V to 5.5 V. Below that the part is not guaranteed to do anything
  in particular; its own POR comparator does not trip until VPORL, 3.4–4.0 V,
  so there is an unspecified band in between.
- **3.18 V — the PIC resets.** `BORV<1:0> = 00` selects a brown-out trip of
  **2.82 / 3.0 / 3.18 V** min/typ/max (DS39977C parameter D005). The worst case
  is the one to design against, so 3.18 V.

So the transceiver falls out of specification **well before** the microcontroller
notices anything is wrong. With C = 10.3 µF and starting from 5.0 V:

| Floor | ΔV | at 8 mA | at 16.5 mA |
|---|---|---|---|
| 4.5 V — everything still in specification | 0.5 V | **640 µs** | **310 µs** |
| 3.18 V — the PIC is still executing | 1.82 V | 2.3 ms | 1.1 ms |

**Hundreds of microseconds, not milliseconds.** Turning that into 3 ms of
ride-through at 20 mA down to 4.5 V would take `C = i·Δt/ΔV` = **120 µF**, a
part with no place on this board and no purpose on it either.

**Which is the point: C6 is not a hold-up capacitor and was never sized as
one.** §2.2.2 sizes a tank capacitor for *sag under load steps across a long
supply run*, which §2 and §3 above are the working for. Ride-through is a
by-product. It also could not be otherwise: the 5 V comes from the display,
which has its own supply and its own bulk capacitance, so an interruption long
enough to exhaust 10 µF on this board has already taken down the device these
numbers are being computed for.

**Deliberate loss of the supply is a different problem and has a different
answer.** Ignition-off is not a transient to be ridden out; it is an event the
firmware would want to be told about, so it can write its accumulators before
the rail goes. That is a hold-up supply plus a sense line, three parts and a
sense pin, and it is written up in `revision-b.md`. It is not this capacitor
made bigger.

---

## 6. C1, C2 — not a supply job at all

These belong to the oscillator. A Pierce oscillator presents the crystal with a
capacitive load, and **a quartz crystal only runs at its marked frequency when
it sees the load capacitance it was cut for.** Load it differently and it still
oscillates, at a slightly different frequency — which matters here because CAN
bit timing is derived from it, and every node on the bus has to agree.

The two capacitors appear in series as seen by the crystal, plus whatever the
pins and tracks contribute:

```
CL = C1·C2/(C1+C2) + Cstray
```

With C1 = C2 = C this inverts to `C = 2·(CL − Cstray)`. The crystal specifies
**CL = 20 pF**, and with about 5 pF of stray:

```
C = 2 · (20 − 5) = 30 pF   →  33 pF, the nearest E12 value
```

**Not the 22 pF that gets fitted from habit.** DS39977C Table 3-3 lists 27 pF at
4 MHz, 22 pF at 8 MHz and 15 pF at 20 MHz with no 16 MHz row at all, and its
note 3 defers to the crystal manufacturer — so the table cannot settle it and
the crystal does. Plan §3.2 has the full derivation, including why an earlier
belief that CL was 32 pF was wrong and what it would have implied.

**C0G/NP0 dielectric here, where C3–C5 are X7R.** X7R's capacitance moves by
tens of percent with temperature and DC bias. On a decoupling capacitor that is
tolerable; on the load capacitance that sets an oscillator's frequency, in a
part that lives behind a dashboard vent, it is not.

---

## 7. C8, R1, R6 — filtering a reset, not a supply

The MCLR network is DS39977C Figure 2-2 in full: R1 10 kΩ pull-up, R6 470 Ω in
series into pin 1, C8 100 nF to ground behind jumper JP2.

**R1 and C8 are a low-pass filter with a time constant of about 1 ms**
(`τ = R·C` = 10 kΩ × 100 nF). §2.3 asks for the capacitor to increase *"the
application's resistance to spurious Resets from voltage sags"* — a transient
shorter than τ cannot pull the pin far enough to be seen as a reset, while a
genuine sag lasting longer than that still resets the part, which is the wanted
behaviour.

**R6 is not part of the filter.** Figure 2-2 note 2: *"R2 ≤ 470 Ω will limit any
current flowing into MCLR from the external capacitor C, in the event of MCLR
pin breakdown, due to Electrostatic Discharge (ESD) or Electrical Overstress
(EOS)."* C8 stores charge; if the pin ever breaks down, that charge would
otherwise dump into the die through a short. R6 has to sit between the RC node
and the pin — anywhere else it cannot do this — which is exactly where the
schematic puts it.

**And the same paragraph is why JP2 exists.** A programmer drives MCLR and needs
fast edges on it; 100 nF with 1 ms of time constant is precisely what stops
that working, so §2.3 asks for the capacitor and hands it a jumper in the same
breath. JP2 comes off before programming and goes back afterwards.

---

## 8. What in this file is not from a datasheet

Per the sourcing rule in `CLAUDE.md`, everything above is either cited or is
listed here:

- **1 µH/m of harness inductance** (§2) — an order-of-magnitude estimate. No
  document held here specifies it, and the harness wire is a commodity part with
  no datasheet. It is used only to show that the harness cannot serve a 70 ns
  current step; the conclusion survives an error of several times in either
  direction, and the design does not depend on the value.
- **~5 pF of stray capacitance** at the oscillator pins (§6) — the same estimate
  the plan §3.2 uses, carried here unchanged rather than re-derived.
- **Treating parameter 3's 70 ns as the current step's timescale** (§1) — the
  datasheet bounds a propagation delay, not a supply-current slew rate. Used as
  an upper bound, which is the conservative direction.
- **The three current totals** (§1) — arithmetic on the cited rows, not figures
  read anywhere.

Everything else names its document and section.
