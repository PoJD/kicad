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
  docs/             supporting documents, datasheets, mechanical notes
```

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

- `canfuel` — firmware
- `mfd15` — display and TRI file

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
