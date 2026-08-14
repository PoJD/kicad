# Car-side wiring — what each wire in the loom is

A reference for the loom that was actually built into the reference vehicle:
which colour carries what, and where each one is tapped in the car. Kept
because none of it is legible from the wire itself once the dashboard is back
together.

> **This is a record of the car, not of a part.** It was written down while the
> wires were in hand and is transcribed here as recorded — the sourcing rule in
> the top-level `CLAUDE.md` settles facts about the car by observation, and
> this is one of them. Nothing here is derived from a datasheet and nothing in
> the board design depends on it.

⚠ **This page is about the 4-pin between the car and the MFD15's own harness —
the 12 V one.** It is *not* the converter plug. The converter plug is a
different connector, on different nets, with a different circuit order, and it
is in `pinout.md`. The two are easy to confuse and the colours actively
mislead: **black is ground on one and +12 V on the other.**

---

## Car side of the 4-pin

| Circuit | Signal | Wire         | Tapped onto |
| ------- | ------ | ------------ | ----------- |
| 1       | ground | brown        | — |
| 2       | power (12 V) | black  | black/violet wire, pin 1 of the cluster's **blue** connector |
| 3       | CAN H  | grey         | orange/black wire, pin 19 of the cluster's **green** connector |
| 4       | CAN L  | yellow/green | orange wire, pin 20 of the cluster's **green** connector |

## MFD15 side of the same 4-pin — the CANchecked cable

The lead supplied with the display
(<https://www.canchecked.de/mfd15-gen2-52mm-can-bus-anzeige/>).

| Circuit | Signal | Wire   |
| ------- | ------ | ------ |
| 1       | ground | black  |
| 2       | power (12 V) | red |
| 3       | CAN H  | white  |
| 4       | CAN L  | yellow |

Circuit for circuit the two halves agree; only the colours differ, which is why
both columns are worth having written down.

---

## How this relates to the rest of the project

- **The 12 V in circuit 2 powers the display, not the converter.** The
  converter's 5 V comes off plug C at C6/C12 and never touches this connector —
  see `harness.md` C3 and `pinout.md`.
- **The CAN pair here is the same pair the converter listens to**, carried on
  to the air vent as the white/yellow run in `harness.md` A2.
- **The circuit order is not the converter plug's order.** Here circuit 1 is
  ground and 2 is power; on the converter plug circuit 1 is +5V and 2 is SGND.
  Do not carry one layout over to the other.

## See also

- `pinout.md` — the three connectors this project's own loom touches
- `harness.md` — building the loom
