# Building the harness

The loom that connects the MFD15 to the car and to the converter board. It
carries two things: the CAN pair from the cluster to the air vent, and 5 V from
the display's own plug C to the converter.

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
- [ ] **D2. Wrap up to the fuse holder and start again after it.** The holder
  stays outside the tape and stays openable.
- [ ] **D3. Reassemble the dashboard.**

---

## If the fuse blows

The fault is on the converter board, not in the display. Fit one new fuse — and
carry a spare, because a blown one behind the dash with no replacement to hand
is a wasted trip. If the second one goes as well, stop replacing fuses and find
the short. That is what the fuse is telling you.

**What the fuse does not protect:** the run from plug C to the fuse itself.
That is deliberate — it lies inside the dashboard and does not move, and
covering it would mean putting the fuse somewhere you cannot reach.

## If a crimp will not hold

Stop and sort the tool out before going any further. A crimp that needs
persuading on the bench is a crimp that will let go in the car, and everything
downstream of this loom is inside a dashboard.
