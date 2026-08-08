# kicad

Desky plošných spojů. Kontejner na všechny projekty, nástupce staršího repa
`eagle`.

KiCad 8 — textové formáty, čitelné diffy, ERC i DRC běží v CI přes
`kicad-cli` bez GUI.

## Desky

| Deska | Stav | Popis |
|---|---|---|
| [`canfuel/`](canfuel/) | návrh nezačat | převodník spotřeby do VW New Beetle, napájený z displeje MFD15 |

## Struktura

```
lib/                sdílené symboly a pouzdra napříč projekty
<deska>/
  *.kicad_pro       projekt
  *.kicad_sch       schéma
  *.kicad_pcb       deska
  fab/              gerbery, BOM, CPL — commituje se
  docs/             podklady, datasheety, mechanika
```

`*.kicad_prl` je lokální stav a do repa nepatří (je v `.gitignore`).

`fab/` se commituje schválně, i když je generované — u objednané desky musí
jít zpětně zjistit, co přesně se poslalo do výroby.

## CI

`kicad-cli sch erc` a `kicad-cli pcb drc`. Obojí musí projít před objednáním
desek.

Workflow zatím běží v režimu skeletonu — dokud v repu není žádný `.kicad_sch`,
projde bez práce. Jakmile schéma přibude, začne kontrolovat.

## Související repozitáře

- `canfuel` — firmware
- `mfd15` — displej a TRI

## Licence

Zatím neurčeno.
