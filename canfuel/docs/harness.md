# Checklist — building the harness and testing before the PCB design

One session, ideally a whole afternoon. Goal: be certain that both the power
supply and the bus work, and come away with logs to analyse — only then is the
board drawn.

**What to prepare:** multimeter, USBtin and laptop, oDSS with the new
S-AQY.TRI, new crimping pliers, a set of pin extractors, insulating/masking
tape, spare ACI pins, spare 43030 sockets.

---

## A. On the bench, before touching the car

- [ ] **A1. Test crimp on an ACI pin.** Take a spare pin and crimp it onto
  0.5 mm² FLRY with the new pliers (second jaw position, 22–18 AWG). Pull on
  the wire — it must hold. Slide on the yellow seal, insert it into the
  housing; it must click and the red lock must go on.
  - ❗ If it does not pass, you need a second pair of pliers for waterproof
    connectors. Find that out now, not with the dashboard in pieces.
- [ ] **A2. Cut the wires.** Red and black for the power run (car → plug B),
  yellow and white for the long CAN run (cluster → air vent). Err on the long
  side; shortening is always possible.
- [ ] **A3. Twist the CAN pair** along its whole length.
- [ ] **A4. Crimp the ends.** ACI pins on the car side, Micro-Fit 43030 sockets
  on the housing side. Tug each one by hand.
- [ ] **A5. Fit two new sockets (5 V, SGND) into the existing 12-pin housing of
  plug C**, positions C6 and C12. Do not touch C7/C8.
- [ ] **A6. Ring everything out.** Every wire end to end, and no short between
  adjacent positions.

## B. Disassembly and routing

- [ ] **B1. Take the dashboard apart** (radio, centre panel).
- [ ] **B2. Route the new long CAN run** from the cluster to the air vent so
  that the connector can be pulled out of the vent.
- [ ] **B3. Route the new power wires** from the car's 4-pin to plug B.
- [ ] **B4. Do not tape anything up yet.** Loom it right at the end.

## C. Measuring the supply — before anything else

- [ ] **C1. Switch on the ignition.**
- [ ] **C2. Measure the voltage between the 5 V and SGND positions** on the
  4-pin that goes to the converter (i.e. at the end of the loom from plug C).
  Expect ~5 V.
  - ✅ Correct → carry on.
  - ❌ Wrong → **stop.** The power supply concept has failed and must be sorted
    out before the dashboard goes back together. Send me the measured values.
- [ ] **C3. As a cross-check, measure 12 V between B5 and B6 as well.**

## D. Testing the bus and the TRI file

- [ ] **D1. Link CAN-H/L** between the two 4-pin connectors with two DuPont
  jumpers and secure them with tape.
- [ ] **D2. Connect the MFD15** (plug B and plug C) and switch on the ignition.
- [ ] **D3. Upload the new S-AQY.TRI** through oDSS.
- [ ] **D4. Check that the TRI file loaded correctly:**
  - DisplayVolt shows a realistic ~12–14 V ← this is the key piece of evidence
  - DisplayTemp shows a sensible temperature
  - RPM, Speed, CLT, OilTemp, TankL, AccelG, FuelCntRaw are all live
  - FuelNow, FuelAvg, FuelTank, Range, Torque, Power, VddConv = 0 ←
    **correct**, the converter does not exist yet
  - ❗ If the file does not load, or a sensor named "0" appears → delete the
    first `info;1.0;...` line and upload again.
- [ ] **D5. Leave it running for a few minutes** and watch for values dropping out.

## E. Sniffs

### E1. Trip reset — this is the important one

- [ ] Connect the USBtin to CAN-H/L and start recording
- [ ] Start the engine and **stand still for ~30 s** (a baseline before the
  reset is needed)
- [ ] **Write down what the trip meter on the cluster reads** (it should still
  be 2.1 km)
- [ ] **Press the trip reset** and keep the recording running
- [ ] **Drive at least 0.1 km** around the garden so the trip meter ticks
- [ ] Stop, **write down the new trip value**, save the log as `06_trip_reset.txt`

### E2. Brisk pull-away — oil vs. IAT

- [ ] New recording, engine warm
- [ ] Quick pull-away in first gear to ~30 km/h, then brake immediately
- [ ] Save as `07_accel.txt`
- This settles whether 0x420 b3 is oil temperature or intake air temperature —
  IAT would drop during the pull-away, oil would not.

## F. Wrapping up

- [ ] **F1. Only once everything above has passed** — tape up the looms and
  tidy the routing
- [ ] **F2. Reassemble the dashboard**
- [ ] **F3. Send me both logs** plus the measured voltages and what the trip
  meter read before and after the reset

---

## When to stop and write

- There is no 5 V on C6 → the power supply concept changes
- The MFD15 stops communicating after the extension → **suspect the DuPont
  contacts first**, not the cable length; try reseating them
- The TRI file will not load even after deleting the `info;` line
- The ACI crimp from the new pliers does not hold

In all four cases, leave the dashboard open.
