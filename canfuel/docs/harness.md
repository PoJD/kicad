# Building the harness

The loom that connects the MFD15 to the car and to the converter board. It
carries two things: the CAN pair from the cluster to the air vent, and 5 V from
the display's own plug C to the converter.

> **Status of the one in this car: built, fitted and measured, 2026-08-10/11.**
> The dashboard came apart, the old loom came out, and a complete new one went
> in — longer 12 V and ground into the MFD15's plug B, the CAN pair and the
> 5 V/SGND run terminating in the Micro-Fit that the converter board will plug
> into. **5.01 V measured at the 4-pin itself**, which is the number that
> matters: it is the supply the board will see, through the fuse and both
> splices, not a reading taken at plug C before the loom existed. The display
> was then run on this loom with the CAN pair on DuPont jumpers in place of the
> board, and it worked.
>
> **What is left in this car is the board**, not the loom. See
> `canfuel/docs/install.md` step 4.
>
> The checkboxes below are deliberately left unticked: this is the procedure
> for building one, and everything learnt while building ours has been folded
> back into the steps rather than recorded as ticks. The one place ours
> deviates from the plan is D2, and it says so there.

**The measuring and the sniffing are done.** The supply was checked at C6/C12
and reads 5.01 V, the TRI file loads and the logs were taken. Everything that
was in this document about proving those points has been removed — what is left
is how to make the loom.

**The car-side 4-pin connector is settled too.** It exists and is already
fitted; this is a re-crimp onto longer wires, not a new connector choice.

**What you need:** crimping pliers, pin extractors, multimeter, spare ACI pins,
spare Micro-Fit 43030 sockets, butt splices with adhesive-lined heat shrink,
cable ties, fabric loom tape.

---

## A. On the bench — making up the loom

- [ ] **A1. Test crimp on an ACI pin first.** Take a spare pin and crimp it
  onto 0.5 mm² FLRY with the pliers (second jaw position, 22–18 AWG). Pull on
  the wire — it must hold. Slide on the yellow seal, insert it into the
  housing; it must click and the red lock must go on.
  - ❗ If it does not hold, you need a second pair of pliers for waterproof
    connectors. Find that out now, on the bench, not with the dashboard in
    pieces.
- [ ] **A2. Cut the new wires.** Red and black for the power run to plug B,
  yellow and white for the long CAN run from the cluster to the air vent. Err
  on the long side — shortening is always possible and this is a re-crimp
  precisely because the first set came out short.
- [ ] **A3. Twist the CAN pair** along its whole length.
- [ ] **A4. Crimp the ends.** ACI pins on the car side, Micro-Fit 43030 sockets
  on the housing side. Tug every one by hand.
- [ ] **A4a. Fit the sockets into the 4-pin Micro-Fit housing (43025-0400) in
  the right cavities.** This was missing here until 2026-08-10 and had to be
  worked out mid-build; the order itself is fixed by plan 3.4 and matches the
  pads of J1/J2 on the board.

  | Micro-Fit circuit | Net  | Wire   | Plug C |
  | ----------------- | ---- | ------ | ------ |
  | 1                 | +5V  | red    | C6     |
  | 2                 | SGND | black  | C12    |
  | 3                 | CANH | white  | C7     |
  | 4                 | CANL | yellow | C8     |

  **Find the cavities from the moulded `1`, not by counting from an end** —
  seen from the wire side the numbering is the mirror of what it is from the
  mating face, so counting is exactly how this gets swapped. Circuits 1 and 2
  are the row the `1` belongs to; 3 and 4 are the other row, with **3 directly
  across from 1** and 4 diagonally opposite it. So the white wire goes across
  from the `1`, the yellow one diagonally from it.

  On the housings actually bought (moulded `MSH`), held wire-side towards you
  with the board header behind, the `1` is the **bottom right** cavity, so:

  ```
      4 CANL yellow    3 CANH white     upper row
      2 SGND  black    1 +5V   red      lower row, nearer the PCB
  ```

  That is the same way round as the board: J1/J2 pad 1 (+5V) is the right-hand
  pad of the row at the board edge and pad 3 (CANH) sits directly behind it,
  because the lower row of a right-angle header is the one nearest the PCB.

  `pinout.md` next to this file is the one-page connector reference for all
  three plugs, drawn the way the MFD15 manual draws its own.
  `harness-connector.svg` draws both — it is generated from
  the pad coordinates in `canfuel.kicad_pcb`, not drawn by hand, so it cannot
  disagree with the board. `harness-nets-on-pcb.svg` is the same four nets
  drawn on the real copper, turned the way up the 1:1 paper print comes out.

  **On a bare board the two pairs can be told apart by eye**: +5V is routed at
  0.8 mm and CANH/CANL at 0.4 mm, so the fattest tracks leaving the connectors
  are the power pair. SGND has no track at all — it is entirely the pour.

  ❗ Swapping CANH and CANL only stops the bus working. Putting a CAN wire in
  circuit 1 or 2 puts **5 V on it** — plan 3.4 calls that a dead transceiver.
  So **ring circuit 1 out to the board's +5V pad before the first power-up**,
  which is also the only check that catches a housing whose numbering does not
  follow the header's.
- [ ] **A5. Fit two sockets (5 V, SGND) into the existing 12-pin housing of
  plug C**, positions C6 and C12. **Do not touch C7/C8** — those are the
  display's CAN pins and they are already right.
- [ ] **A6. Ring everything out.** Every wire end to end, and no short between
  adjacent positions. Do this before the fuse goes in, so that a later failure
  has only one new thing to blame.

## B. On the bench — the 5 V fuse

The converter takes 5 V straight from the display, so a short on the converter
board is a short across the MFD15's 5 V rail. The fuse ends that. It is in the
loom rather than on the board because no 5 × 20 holder fits on a finished
55 × 45 mm PCB — plan 9.2 has the measurements and the reasoning.

**Parts:** SIBA 179120.0.2, 200 mA 250 V 5 × 20 mm glass, **time-lag T** — not
the fast F version — in inline cable holder K23411, which comes with 200 mm of
lead. The holder body is about 46 mm long and 10.5 mm across, so it needs a
straight run of loom that length and somewhere it can be unscrewed.

- [ ] **B1. Cut the 5 V wire only**, a short way back from the 4-pin connector
  at the air vent end. Leave the ground wire whole. Place the cut so the holder
  ends up in the length of loom that comes out when the MFD15 is pulled — the
  whole point is that the fuse can be changed without dismantling the dash.
- [ ] **B2. Join each cut end to one lead of the holder.** Crimp butt splices
  with adhesive-lined heat shrink are the right way. Soldering is acceptable if
  the joint is then sleeved well past the wick on both sides — a soldered joint
  in a loom that vibrates cracks exactly at the edge of where the solder
  travelled.
- [ ] **B3. Cable-tie the holder to the loom** so it cannot swing and chafe
  against the vent housing.
- [ ] **B4. Ring it out again** — continuity from plug C position C6 through to
  the 4-pin, with the fuse fitted. Then pull the fuse and confirm the circuit
  really does open. That second half is the one worth doing: it proves the fuse
  carries the current and that no splice quietly bypasses it.

## C. In the car — routing

- [ ] **C1. Take the dashboard apart** (radio, centre panel).
- [ ] **C2. Route the long CAN run** from the cluster to the air vent, so that
  the connector can be pulled out of the vent.
- [ ] **C3. Route the power wires** from the car's 4-pin to plug B. **This is
  12 V for the MFD15 itself, not for the converter.** The converter's 5 V comes
  from plug C at C6/C12 and never touches plug B — the 12 V branch was dropped
  from the board design, so nothing in this step feeds the converter.
- [ ] **C4. Do not tape anything up yet.** Loom it right at the end, once
  everything is in place and reaches.

## D. Finishing

- [ ] **D1. Tape up the looms and tidy the routing.** Use **fabric loom tape,
  not PVC insulating tape** — at dashboard temperatures PVC adhesive creeps,
  which is the same reason the board is not taped down either.
- [ ] **D2. ~~Wrap up to the fuse holder and start again after it.~~
  Overridden on the build: the holder is wrapped over as well.** The intent
  was that the fuse could be changed without unwrapping anything. On the
  actual holder one end leaves **bare 5 V exposed**, and bare metal loose
  behind a dashboard was judged the worse of the two risks, so it is taped
  over along with the rest of the loom.

  **What that costs:** changing a fuse now means peeling the tape back and
  re-wrapping it. So **the spare fuse in the car is not enough on its own —
  a roll of the fabric tape has to travel with it**, or the roadside repair
  cannot be finished.

  The alternative, if this is ever rebuilt: sleeve only the exposed end and
  leave the holder body outside the tape, which gets both. Not worth
  dismantling a finished loom for.
- [ ] **D3. Reassemble the dashboard.**

---

## If the fuse blows

The fault is on the converter board, not in the display. Fit one new fuse — and
carry a spare **and a roll of the fabric tape**, because the holder is wrapped
over (see D2) and a blown fuse behind the dash with nothing to hand is a wasted
trip. If the second one goes as well, stop replacing fuses and find
the short. That is what the fuse is telling you.

**What the fuse does not protect:** the run from plug C to the fuse itself.
That is deliberate — it lies inside the dashboard and does not move, and
covering it would mean putting the fuse somewhere you cannot reach.

## If a crimp will not hold

Stop and sort the tool out before going any further. A crimp that needs
persuading on the bench is a crimp that will let go in the car, and everything
downstream of this loom is inside a dashboard.
