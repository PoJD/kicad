# kicad

Printed circuit boards. A container for all projects, successor to the older
`eagle` repo.

KiCad 8 — text formats, readable diffs, ERC and DRC running in CI through
`kicad-cli` without a GUI.

## Boards

| Board | Status | Description |
|---|---|---|
| [`canfuel/`](canfuel/) | design not started | fuel consumption converter for a VW New Beetle, powered from the MFD15 display |

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
ordered.

The workflow currently runs as a skeleton — while the repo contains no
`.kicad_sch`, it passes doing nothing. Once a schematic lands, it starts checking.

## Related repositories

- `canfuel` — firmware
- `mfd15` — display and TRI file

## Licence

Not decided yet.
