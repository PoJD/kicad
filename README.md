# kicad

Printed circuit boards. A container for all projects, successor to the older
`eagle` repo.

KiCad 10 — text formats, readable diffs, ERC and DRC running in CI through
`kicad-cli` without a GUI. The CI container image tracks the local major
version, because KiCad refuses to open files written by a newer one.

## Boards

| Board | Status | Description |
|---|---|---|
| [`canfuel/`](canfuel/) | **ordered 2026-08-09**, three pieces from Gatema | fuel consumption converter for a VW New Beetle, powered from the MFD15 display |

The `canfuel` board is finished: schematic and PCB complete, ERC and DRC clean
with zero unconnected items, 24 parts on 55 × 45 mm and two layers, `fab/`
generated and committed. **The boards being manufactured are commit
`c06e710`**, so an edit to the board files now makes `fab/` stop describing
them.

## Layout

```
lib/                symbols and footprints shared across projects
<board>/
  *.kicad_pro       project
  *.kicad_sch       schematic
  *.kicad_pcb       board
  fab/              gerbers, BOM, CPL — committed
  docs/             design documents, datasheets, and how to build the harness
```

For the `canfuel` board specifically, `canfuel/docs/` holds:

| File | Contents |
|---|---|
| `harness.md` | **making the loom and wiring it into the car** — a checklist, with the crimping, the connector cavities and the fuse |
| `pinout.md` | one-page reference for all three connectors |
| `harness-*.svg` | the connector and the four nets drawn from the real pad coordinates in `canfuel.kicad_pcb`, so they cannot disagree with the board |
| `implementation-plan.md` | how the board was designed, every number cited to a datasheet |
| `*.pdf` | the manufacturers' datasheets, listed in `NOTICE` as theirs |

`*.kicad_prl` is local state and does not belong in the repo (it is gitignored).

`fab/` is committed deliberately even though it is generated — for an ordered
board it must be possible to find out exactly what was sent to the fab.

## CI

`kicad-cli sch erc` and `kicad-cli pcb drc`. Both must pass before boards are
ordered, and both do — the schematic and the board have been in the repository
since the design landed, so the workflow does real work on every push.

Two project-specific checks run alongside them: `check-netlist.py` and
`check-placement.py`.

## Related repositories

The `canfuel` board is one third of a project that needs all three
repositories. Clone them side by side.

**Building one?** [`canfuel/docs/install.md`](https://github.com/PoJD/canfuel/blob/main/docs/install.md)
is the whole path from three clones to a working device, in the order it has to
happen. Making up the harness — the part that lives in this repository — is
step 3 of seven.

| Repository | What it holds | Go there for |
|---|---|---|
| **`kicad`** (this one) | the converter board | the schematic, the PCB, `fab/`, and **`canfuel/docs/harness.md` — how to make the loom and wire it into the car** |
| [`canfuel`](https://github.com/PoJD/canfuel) | the converter firmware | building and flashing the hex, what the LEDs mean, how the car's frames are decoded |
| [`mfd15`](https://github.com/PoJD/mfd15) | the display configuration | the TRI file the display runs and how to upload it |

**The coupling to `canfuel` is the pin assignment**, and it is one-way: the
firmware is written against the board, not the other way round. It is frozen —
the boards being manufactured are commit `c06e710`, so an edit to the board
files now makes both `fab/` and the firmware stop describing them.

## Licence

[Apache License 2.0](LICENSE). Use it, change it, order the boards, sell them —
the only obligations are to keep the copyright and licence notices and to say
what you changed.

**`NOTICE` lists what is not ours.** The manufacturer datasheets under
`canfuel/docs/` belong to their manufacturers and are redistributed for
reference only; the licence above does not cover them and does not claim to.
Everything else in this repository is covered.

Questions, corrections and pull requests are welcome as issues on any of the
three repositories, or by email to Lubos Housa <luboshousa@gmail.com>.
