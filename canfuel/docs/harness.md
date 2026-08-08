# Checklist — stavba harnessu a testy před návrhem PCB

Jedna session, ideálně celé odpoledne. Cíl: mít jistotu, že napájení i sběrnice fungují, a odvézt si logy k analýze — teprve pak se kreslí deska.

**Co si připravit:** multimetr, USBtin + notebook, oDSS s novým S-AQY.TRI, nové kleště, sada vypichováků, izolepa/maskovací páska, náhradní ACI piny, náhradní dutinky 43030.

---

## A. Na stole, než sáhneš na auto

- [ ] **A1. Testovací krimp na ACI pin.** Vezmi náhradní pin, nakrimpuj na 0,5 mm² FLRY novými kleštěmi (druhá pozice čelistí, 22–18 AWG). Zatáhni za drát — musí držet. Nasuň žluté těsnění, zasuň do pouzdra, musí cvaknout a červená pojistka musí jít nasadit.
  - ❗ Když neprojde, potřebuješ druhé kleště na vodotěsné konektory. Zjisti to teď, ne s rozebranou palubovkou.
- [ ] **A2. Nastříhat vodiče.** Červená + černá na napájecí běh (auto → plug B), žlutá + bílá na dlouhý CAN běh (budík → průduch). Radši delší, zkrátit jde vždycky.
- [ ] **A3. Zakroutit CAN pár** po celé délce.
- [ ] **A4. Nakrimpovat konce.** ACI piny na stranu do auta, Micro-Fit dutinky 43030 na stranu do pouzder. U každého tah rukou.
- [ ] **A5. Osadit dvě nové dutinky (5 V, SGND) do stávajícího 12pin pouzdra plugu C**, pozice C6 a C12. Do C7/C8 nesahat.
- [ ] **A6. Prozvonit všechno.** Každý vodič konec-konec, a mezi sousedními pozicemi nesmí být zkrat.

## B. Demontáž a natažení

- [ ] **B1. Rozebrat palubovku** (rádio, středový panel).
- [ ] **B2. Natáhnout nový dlouhý CAN běh** od budíku do průduchu tak, aby konektor šel vytáhnout ven z průduchu.
- [ ] **B3. Natáhnout nové napájecí vodiče** z auto-4pinu do plugu B.
- [ ] **B4. Zatím nic nepřemotávat páskou.** Loom až úplně nakonec.

## C. Měření napájení — dřív než cokoliv dalšího

- [ ] **C1. Zapnout zapalování.**
- [ ] **C2. Změřit napětí mezi pozicemi 5 V a SGND** na 4pinu, který jde do převodníku (tj. na konci svazku od plugu C). Čekáš ~5 V.
  - ✅ Sedí → pokračuj.
  - ❌ Nesedí → **stop.** Padá koncepce napájení a musí se řešit dřív, než palubovku zavřeš. Napiš mi naměřené hodnoty.
- [ ] **C3. Pro kontrolu změř i 12 V mezi B5 a B6.**

## D. Test sběrnice a TRI

- [ ] **D1. Propojit CAN-H/L** dvěma dupont drátky mezi oběma 4pinovými konektory, zajistit páskou.
- [ ] **D2. Zapojit MFD15** (plug B i C), zapnout zapalování.
- [ ] **D3. Nahrát nový S-AQY.TRI** přes oDSS.
- [ ] **D4. Kontrola, že se TRI načetlo správně:**
  - DisplayVolt ukazuje reálných ~12–14 V ← tohle je ten hlavní důkaz
  - DisplayTemp ukazuje rozumnou teplotu
  - RPM, Speed, CLT, OilTemp, TankL, AccelG, FuelCntRaw žijí
  - FuelNow, FuelAvg, FuelTank, Range, Torque, Power, VddConv = 0 ← **správně**, převodník neexistuje
  - ❗ Kdyby se soubor nenačetl nebo se objevil senzor jménem „0" → smaž první řádek `info;1.0;...` a nahraj znovu.
- [ ] **D5. Nechat běžet pár minut** a sledovat, jestli hodnoty nevypadávají.

## E. Sniffy

### E1. Trip reset — tohle je ten důležitý

- [ ] Zapojit USBtin na CAN-H/L, spustit záznam
- [ ] Nastartovat, **stát na místě ~30 s** (potřebuju baseline před resetem)
- [ ] **Zapsat si, co ukazuje trip na budíku** (mělo by být pořád 2,1 km)
- [ ] **Zmáčknout trip reset**, záznam nechat běžet
- [ ] **Popojet aspoň 0,1 km** po zahradě, ať trip tikne
- [ ] Zastavit, **zapsat novou hodnotu tripu**, uložit log jako `06_trip_reset.txt`

### E2. Svižný rozjezd — olej vs. IAT

- [ ] Nový záznam, motor zahřátý
- [ ] Rychlý rozjezd na jedničku do ~30 km/h, hned brzdit
- [ ] Uložit jako `07_accel.txt`
- Rozhodne, jestli je 0x420 b3 teplota oleje, nebo nasávaného vzduchu — IAT by při rozjezdu spadl, olej ne.

## F. Uzavření

- [ ] **F1. Teprve když všechno výše prošlo** — přemotat svazky páskou, uklidit vedení
- [ ] **F2. Složit palubovku**
- [ ] **F3. Poslat mi oba logy** + naměřená napětí + co ukazoval trip před a po resetu

---

## Kdy zastavit a napsat

- 5 V na C6 není → mění se napájecí koncepce
- MFD15 po prodloužení nekomunikuje → **nejdřív podezřívej dupont kontakt**, ne délku kabelu; zkus je přesadit
- TRI se nenačte ani po smazání řádku `info;`
- ACI krimp z nových kleští nedrží

Ve všech čtyřech případech nechávej palubovku otevřenou.
