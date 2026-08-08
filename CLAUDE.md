# kicad — hardware

Kontejner na desky. Nástupce staršího repa `eagle`, každá deska má vlastní
podadresář a vlastní `fab/`.

KiCad 8. Textové formáty znamenají čitelné diffy a `kicad-cli` umí v CI
spustit ERC i DRC bez GUI — chyba v návrhu spadne v pull requestu, ne až
na hotové desce.

Aktuálně je tu jedna deska: `canfuel/`.

---

## Zadání desky canfuel

Převodník spotřeby do VW New Beetle. Sedí v průduchu za displejem MFD15,
napájený 5 V přímo z displeje.

### MCU

- **PIC18F25K80** v PDIP-28, v **úzké patici (7,62 mm)**.
- Krystal 16 MHz, zatěžovací kapacita 32 pF → osadit **33 pF**
  (ověřeno v předchozím projektu, ne 22 pF).

### Transceiver

- **MCP2562-E/P** v DIP-8 patici.
- ⚠ **Pin VIO na VDD, pin STBY na zem.** Jinak zůstane v úsporném režimu
  a nic nepošle. Tohle je nejsnadnější chyba celého návrhu.

### Napájení

- 5 V z konektoru C displeje: **C6 = 5 V, C12 = SensorGround**
  (ověřeno multimetrem).
- Žádný regulátor, žádná ochrana proti přepólování, žádný TVS.
  12V větev z návrhu vypadla.
- Odběr do 30 mA, limit displeje 0,5 A.
- Blokování: 100 nF u každého napájecího pinu, 10 µF na vstupu.

### CAN

- **C7 = CAN-H, C8 = CAN-L.**
- ⚠ **Terminaci 120 Ω neosazovat** — sběrnice je zakončená v autě, třetí
  odpor by ji přetížil. Pájecí jumper pro bench test je v pořádku.

### Konektory

- 2× Molex Micro-Fit 3.0 header **43045-0400** (pravoúhlý, do DPS).
- Oba zapojené **paralelně na tytéž čtyři nety** — CAN-H, CAN-L, 5 V, SGND.

Díky paralelnímu zapojení je záměna kabelů neškodná a deska sama funguje
jako propojka CAN i s vytaženým PICem. To je záměr, ne omyl v návrhu.

### Ostatní

- **LED:** dvě (napájení, stav CAN), aktivní jen s nasazeným debug jumperem
  na RA0. V autě nesvítí nic.
- **ICSP:** 5pinová hlavička 2,54 mm pro PICkit.
- **Záchranná brzda:** nepoužité piny PIC vyvést na lištu 2,54 mm, aby šla
  případná chyba v návrhu opravit drátem.
- **Rozměry:** ~55 × 45 mm, dvouvrstvá, převážně THT.
  Krabička do průduchu 6,5 × 5,5 cm, hloubka max ~3 cm.

---

## Pravidla repa

- `*.kicad_prl` patří do `.gitignore` — je to lokální stav, ne návrh.
- `fab/` se **commituje**, i když je generované. Důvod je dohledatelnost:
  u objednané desky musí jít zpětně zjistit, co přesně se poslalo do výroby.
- Sdílené symboly a pouzdra jdou do `lib/`, ne do adresáře desky.
- `kicad-cli sch erc` a `kicad-cli pcb drc` musí projít **před objednáním**.

---

## Breadboard fáze se přeskakuje

Micro-Fit má rozteč 3,0 mm a na breadboard nesedí. Všechno je v paticích
a jádro firmwaru se testuje na hostu proti reálným logům (repo `canfuel`).

---

## Nákup součástek

Kompletní BOM vypadne až ze schématu, takže **seznam sestavit až po návrhu**,
ne dřív. Kupovat nadvakrát je horší než kupovat později.

- **Ze šuplíku:** PIC18F25K80. Polovodiče v suchu nedegradují.
- **Nové:** krystal, všechny kondenzátory, odpory, konektory, patice, LED.
  Elektrolyty stárnou i bez napětí. U krystalu je hlavní argument, že
  u neoznačeného kusu neznáš zatěžovací kapacitu.
- **Nový nákup:** MCP2562.

Podklady: `canfuel/docs/bom-nakup.pdf`, `canfuel/docs/harness.md`.

⚠ **Datasheet krystalu v repu chybí** — v zadání byl uvedený, ale nebyl mezi
nahranými soubory. Patří do `canfuel/docs/`.

---

## Související repozitáře

- `canfuel` — firmware
- `mfd15` — displej a TRI
