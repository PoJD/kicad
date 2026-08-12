# Ideas for a revision B

**There is no revision B, and nothing here is scheduled.** The board is
finished, ordered and frozen at commit `c06e710`; `CLAUDE.md` says not to touch
the design while the order is in flight and that still holds. This file is
where an idea goes that is worth keeping but must not turn into an edit.

The rule from `CLAUDE.md` applies here as everywhere: every number below cites
its datasheet, and anything that is a judgement rather than a specification
says so.

---

## B1 — Hold-up supply and shutdown detection

**What it would buy: the converter would lose nothing at all when the ignition
is switched off.** Today it loses up to twenty seconds of accumulated fuel and
distance, every single time.

### The problem, which is a firmware problem the board could solve

The firmware keeps its trip accumulators in RAM and copies them to the PIC's
EEPROM every `PERSIST_INTERVAL_MS` — 20 s since 2026-08-12, 60 s before that.
When the ignition goes off the RAM goes with it, so everything since the last
copy is gone: uniformly 0 to 20 s, ten on average, **every shutdown**. It is
not a fault, it is what a periodic write means, and `canfuel/src/persist.h` has
the full account including why it is invisible on the display (FuelAvg is a
ratio and both halves shrink together, so the error lands at about 0.17 %).

Writing more often shrinks it but never removes it, and each write costs 48 ms
of blocked CPU. The only thing that removes it is knowing the shutdown is
coming and writing once, at that moment. That needs two things this board does
not have:

1. **Warning** — some signal that the supply is going away, *before* it has.
2. **Hold-up** — enough energy left to finish a twelve-byte record afterwards.

### Why the current board cannot do it

- **5 V comes straight from the display's connector C6/C12.** There is no
  regulator, no series element and no local energy store beyond C6 (10 µF) and
  the 100 nF decoupling. When the display's rail goes, ours goes with it.
- **Nothing senses the upstream side.** The firmware does measure its own VDD
  through the band gap (`hal_sys_vdd_c()`), but that is the *same* rail: by the
  time it reads low there is nothing left to write with. The measurement has to
  be of a supply the board is no longer drawing from.

### What it would take

Three parts, none of them exotic:

| | What | Why |
| --- | --- | --- |
| **D3** | Schottky in series with the 5 V feed | separates "the display's 5 V" from "our 5 V", so the bulk capacitor holds only us up and does not try to power the display |
| **C9** | bulk electrolytic on the board side of D3 | the energy that finishes the record |
| **sense** | divider or direct link from the *display* side of D3 to a spare PIC input | the warning |

The firmware side is small: poll the sense pin in the main loop — it runs 7,400
to 20,000 times a second, so no interrupt is needed and none should be added —
and on a low, call `persist_save_now()` immediately and then spin. `RB0/INT0`
exists (DS39977C §10, external interrupts on RB0/INT0, RB1/INT1) if a future
design wants an edge instead, but polling matches how the rest of that firmware
is built.

### The arithmetic

`C = I · t / ΔV`.

**Current, with the LEDs dark as they are in the car** (the `DBG_EN` jumper is
not fitted):

| | typ | max | source |
| --- | --- | --- | --- |
| PIC18F25K80, 16 MHz, VDD = 5 V, PRI_RUN | 2.2 mA | 6 mA | DS39977C Table 31-5, Supply Current IDD. The 16 MHz row's test condition is a 4 MHz EC oscillator with PLL rather than our HS1 crystal — it is the closest figure the datasheet gives, and it is quoted as such. |
| MCP2562, recessive | 5 mA | 10 mA | DS20005167C, DC Characteristics, VDD pin: `IDD -- 5 10 mA Recessive; VTXD = VDD`. The dominant figure of 45/70 mA does not apply — nothing is transmitted during a shutdown write. |
| **total** | **7.2 mA** | **16 mA** | |

**Time**: twelve bytes at 4 ms each is 48 ms (DS39977C Table 31-1, D122).
⚠ **D122 is a typical with no maximum at all**, and §8.4 says the write time
"will vary with voltage and temperature, as well as from chip-to-chip". A
hold-up design cannot be sized on a typical, so double it: **96 ms**.

**Voltage**: the brown-out trip is the floor, not the EEPROM's. `BORV = 0` in
`canfuel/src/pic_config.h` sets 3.0 V, chosen because the A/D's twelve-bit
resolution is only specified for VREF ≥ 3.0 V (DS39977C Table 31-25, A01/A50).
D121 allows EEPROM writes down to 1.8 V, so the CPU resets long before the
memory would object. With a Schottky drop of about 0.3 V the board starts at
4.7 V, giving **ΔV = 1.7 V**.

| Assumption | C required | Fit |
| --- | --- | --- |
| 16 mA max, 48 ms | 452 µF | 470 µF |
| 16 mA max, 96 ms (D122 doubled) | 904 µF | **1000 µF** |
| transceiver in standby first, 6 mA, 96 ms | 339 µF | 470 µF |

The third row is the interesting one and it needs a fourth change: **STBY would
have to come off ground and onto a pin.** On this board it is hard-wired low
(`CLAUDE.md`, Transceiver), which is right for a board that always talks. A
revision that can shut the transceiver up at the moment of the warning needs
less than half the capacitance — and 5 µA of standby current (DS20005167C,
IDDS) is nothing at all.

### Three things that would have to be checked, and one to do first

- **Measure the display's rail first, before choosing any capacitor.** How fast
  the MFD15's 5 V collapses at ignition-off is unknown and nobody has looked. If
  it decays over a hundred milliseconds under our load, most of the hold-up
  already exists and C9 could be small or unnecessary. If it snaps off in a
  millisecond, the table above stands. **This is a measurement, not a design
  decision, and it is cheap** — a scope on C6 while somebody turns the key.
- **The MCP2562 is out of specification below 4.5 V** (DS20005167C, VDD Voltage
  Range 4.5–5.5 V). During the hold-up the rail crosses that on its way to 3.0,
  so the transceiver's behaviour is undefined for the last part of the write.
  It does not matter if nothing is being transmitted, and it is another argument
  for putting it in standby rather than leaving it to guess.
- **Inrush against the fuse and the display.** C9 would be fifty to a hundred
  times C6. The feed is a SIBA 179120.0.2, 200 mA time-lag (0.7 A²s per its
  datasheet), and the display's own limit is 0.5 A — the peak charging current
  into 1000 µF is set by nothing but ESR and wiring resistance. A series
  resistor, an NTC, or accepting a slower start would all work; what would not
  work is fitting the capacitor and hoping.

### What it does not buy

Nothing else. The trip accumulators are the only state that has to survive a
power cycle, the display never shows them as absolutes, and FuelAvg is already
within a sixth of one digit. **This is a completeness fix, not a fault fix**,
and that is why it sits in this file rather than in a plan.
