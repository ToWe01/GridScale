# Übergabe: GridScale – Gehäuse-Prototyp (15×15 cm)

Projektname seit 2026-11-26: **GridScale – Die intelligente Wiegematte** (ältere Einträge nennen noch Küchenregalboden / Smart Kitchen Mat). Gravur auf der Unterseite: „GRIDSCALE 15x15 R3“.

> **Ordnerstruktur seit 2026-11-26** (Umbau für ein gemeinsames Repository, Überblick in `../README.md`): `cad/` heißt jetzt `gehaeuse/`. Skripte in `gehaeuse/skripte/`, FCStd in `gehaeuse/modell/`, Prüfberichte und `kabelwege_v2.json` in `gehaeuse/pruefberichte/`, ein Druckpaket in `gehaeuse/druck/`, FEM-Skripte in `gehaeuse/fem/` mit Ergebnissen in `fem/ergebnisse/`, Einzeladern-Skript in `gehaeuse/verdrahtung/`. Datenblätter unter `referenz/`, Bericht/Statusberichte/Bestellung unter `doku/`. Ältere Einträge unten nennen teils noch die alten Pfade.

Stand: 2026-11-23 (Druck-Optimierung Rev. 2). Zuständigkeit des Nutzers: nur Gehäuse/Konstruktion. Elektronik und Firmware machen andere im Team.

## 1. Ziel
Erster Prototyp des "intelligenten Küchenregalbodens" (SmartSystems2, Gridfinity-Raster, Differenzwägung + RFID je Slot) im Maß **150 × 150 mm**, gedruckt in **PLA**. Später werden mehrere Module zusammengesteckt, Verbindungen nur im festen unteren Teil.

Zwei Teile:
- **Oberteil** (gewogene Platte): 3×3 Gridfinity-Slots im **50-mm-Raster**, darunter je eine Tasche für einen PN532-RFID-Reader.
- **Unterteil** (fest): Boden, Sockel für die Wägezellen, Anschläge, Platinen-Rahmen, USB-C-Wand.

## 2. Verbaute Teile
| Teil | Menge | Maße / Hinweis | Quelle |
|---|---|---|---|
| PN532-Reader (Funduino) | 9 | ca. 42,7×40,4 mm, **mit abgewinkelten Dupont-Pins ca. 7 mm hoch** | Nutzer-Messung, Händlerangaben |
| Wägezelle Adafruit 4541 (5 kg) | 2 | 75×12,7×12,7 mm, je Ende **2×M4 im Abstand 10 mm**, erstes Loch 5,5 mm vom Ende | `referenz/externe_modelle/4541.pdf` |
| ESP32-C6-DevKitC-1 | 1 | 51,8×25,4 mm | `referenz/externe_modelle/esp32-c6-devkitc-1-dimensions_v1.2.pdf` |
| SparkFun HX711 (SEN-13879) | 2 | 30,48×22,86 mm | Eagle `.brd` im Ordner |
| Adafruit TCA9548A | 2 | 30,48×17,78 mm, 2 Löcher Ø2,5 bei x=8,89 / y=2,54 und 27,94 | Eagle `.brd` im Ordner |
| USB-C-Einbaubuchse Delock 87824 | 1 | Öffnung ca. 21,5×12,5 mm, Lochabstand ca. 28 mm (Nutzerangabe "ca.") | Nutzer |

**Wichtig:** Alle Boards haben angelötete Header-Pins, die bleiben. Später werden Leitungen an die Pins gelötet, es wird nichts ausgelötet. Die Rahmen im Modell lassen die Pins deshalb frei.

Die Wägezellen sind **zwei** (nicht vier wie in älteren Projektbeschreibungen). Der TCA9548A wird nur für die 9 PN532 gebraucht (alle Adresse 0x24). Die HX711 sind zweidrahtig (Takt/Daten), kein I²C.

## 3. Dateien (Ordner `Projekt_Matte/cad`)
- (seit 2026-11-24 in `gehaeuse/archiv/V1/`, Hauptversion ist V2 `build_prototyp_v2.py`) `build_prototyp.py` – **Quelle der Wahrheit** für V1. Baut das komplette FreeCAD-Modell, schreibt Parametertabelle und Prüfbericht, speichert die FCStd.
- `Prototyp_15x15.FCStd` – Ergebnis des Skripts (Objekte: `Unterteil`, `Oberteil`, `REF_*` Referenzteile, Tabelle `Parameter`, `Pruefbericht`).
- `pruefbericht.txt` – letzter Prüfbericht.
- `../referenz/externe_modelle/` – Datenblätter, ESP32-DXF/PDF, Eagle-Dateien (HX711, TCA9548A). Für PN532 gibt es kein Original-CAD.

Ältere Dateien im Projektordner (Roadmap 18.10., hardware/PCB-Guide, KiCad-Footprint) sind laut Nutzer **veraltet, nicht verwenden**. `referenz/handout_proto/gridfinity-rfid-mat-main` ist ein fremder Referenzentwurf (eigene Platine, 168 mm, 56-mm-Raster); daraus wurden nur mechanische Ideen übernommen.

## 4. Konstruktion (aktueller Stand)
Gesamthöhe **33,95 mm** (Z_UP = 20,1; Oberteil 13,85 mm). Schichtfolge von unten: Boden 2,4 → Sockel 5,0 → Zelle (12,7) → Oberteil liegt direkt auf dem Freiende, über dem Rest der Zelle 0,8 mm Freistich in der Plattenunterseite.

**Gehäuse (Rev. 4, geschlossen, staubgeschützt, Nutzer 2026-11-23):** Unterteil ist eine geschlossene Wanne: Boden 2,4 + umlaufende Wand 2,0 mm bis zur **Schulter** (5,2 mm unter der Platte). Darüber steht ein zurückgesetzter **Kragen** (1,6 mm, innen 45°-Übergang ohne Überhang) bis 1,2 mm unter die Platte. Das Oberteil (Träger) hat eine umlaufende **Schürze** (1,6 mm dick, 3,0 mm hoch), die außen über den Kragen greift: Überdeckung 1,8 mm, waagerecht 0,6 mm Luft (größer als das Zapfenspiel 0,5), senkrecht 1,2 mm zur Schulter und 1,2 mm Kragen–Platte. Die sichtbare Fuge zeigt damit nach unten, Krümel und Staub müssen erst 1,8 mm nach oben durch einen 0,6-mm-Spalt. Schürze nur 3,0 mm hoch, weil der USB-Ausschnitt bis 15,1 mm reicht (Schulter bei 15,9 mm, 0,8 mm Restwand außen, dahinter die 4-mm-Verstärkung). Falls der Flansch der Delock-Buchse außen höher als 2 mm über den Ausschnitt ragt, stößt er an die Schürze → beim Nachmessen prüfen. **Druck:** Träger mit der Oberseite (Trennebene) aufs Bett, Schürze zeigt nach oben, kein Stützmaterial. Fasen 0,4 an Schulter, Kragenoberkante und Schürzenunterkante (außen V-Fuge, innen Einführung). Senkrechte Ecken R4, Unterkante gefast 0,6, Gravur „SMART KITCHEN MAT 15x15 R3“ auf der Unterseite (0,4 tief, gespiegelt). Außenmaß 148,5 × 148,5 × 33,95 mm unverändert. **Bewegungscheck im Prüfbericht:** Platte kippt um die Achse durch die Freienden bis zum Anschlag, senkt sich ab, verschiebt sich um das Zapfenspiel. In keinem Fall berührt sie das Unterteil. Max. Eckabsenkung 0,78 mm < Fuge 1,2.
Ansichten: `gehaeuse/ansichten/*.png`, erzeugt mit `freecadcmd gehaeuse/archiv/V1/render_ansichten.py` (matplotlib, headless; Ansichten von unten erscheinen gespiegelt).

**Zwei Varianten (Schalter `VARIANT` im Skript, vor dem exec setzen):**
- `einteilig`: Oberteil aus einem Stück, M4-Köpfe am Freiende sitzen sichtbar in Senkungen im Gridfinity-Steg. Ausgabe `Prototyp_15x15.FCStd`, `pruefbericht.txt`.
- `deckel` (**Standard, vom Nutzer für den Prototyp gewählt 2026-11-23**; Schrauben unsichtbar): Oberteil geteilt in **Träger** (8,5 mm, Taschen + 1,0 mm Haut, an die Zellen geschraubt, Kopf bündig mit der Oberseite) und **Gridfinity-Deckel** (5,35 mm, geschlossener Boden 0,6 + Gridfinity-Profil). Haut über PN532 bleibt 1,0 + 0,6 = 1,6 mm. Der Deckel liegt lose auf, wird über 4 gedruckte Zapfen Ø3,8 in Löchern Ø4,0 (bei (50|25) (100|25) (50|125) (100|125)) zentriert und ist abnehmbar. Trennfuge außen mit 0,3-mm-Fasen. Keine zusätzlichen Normteile. Ausgabe `Prototyp_15x15_Deckel.FCStd`, `pruefbericht_deckel.txt`. Druck: Träger mit Unterseite aufs Bett, Deckel mit Boden aufs Bett. Ein Adapter oder Abdeckstopfen wurden verworfen (Stopfen gefallen dem Nutzer nicht).
Ansichten der Deckel-Variante: `gehaeuse/archiv/V1/ansichten/D*.png` (`freecadcmd gehaeuse/archiv/V1/render_ansichten.py`, einteilig mit `VARIANT=einteilig`).

**Druck:** Beide Teile mit der Unterseite aufs Bett, ohne Stützen (Kopfsenkungen Freiende öffnen nach oben). Das Oberteil hat keine überstehenden Noppen mehr, Gridfinity-Seite oben. Brücken: 9× PN532-Taschendecke ca. 41 mm, M4-Senkungen, USB-Ausschnitt.

- **Wägezellen:** 2 Stück auf den Stegen bei y=50 und y=100, gegenläufig ("Windmühle": Zelle 1 links fest, Zelle 2 rechts fest). Festes Ende mit **2×M4×12 DIN 912 + Scheibe DIN 125 von unten** in das Zellengewinde (Senkung Ø9,5 × 5,0 tief, beide Senkungen als Langloch verbunden, Kopf 0,2 versenkt, 2,4 mm PLA geklemmt; max. 15,4 mm lang). Scheibe gegen Kriechen des PLA. **Vorgabe Nutzer: nur Standard-M4-Zylinderkopf, möglichst wenig Normteile (C-Teile) außer an den Wägezellen.** Freies Ende mit **2×M4×12 DIN 912 von oben** durch die Platte (Durchgang Ø4,6) ins Zellengewinde. Der Kopf sitzt in einer Senkung Ø7,4 im Steg zwischen zwei Gridfinity-Feldern, Oberkante bündig mit dem Gridfinity-Taschenboden (Behälter berühren ihn nicht). Klemmlänge PLA 5,1 mm, 6,9 mm Gewinde in der Zelle. Kein Langloch mehr im Boden. **Ausnahme:** Zwischen Senkung und PN532-Tasche bleiben nur 0,8 mm Wand auf 2,4 mm Höhe (Steg y ist 9,0 mm). An beiden Enden dieselbe Schraube: insgesamt **8× M4×12 DIN 912 + 4× Scheibe DIN 125** (nur Festende). Freiende ohne Scheibe, die Ø9 passt nicht in den Steg. Kein Kraftnebenschluss: Luft um die Zelle, Kabel mit Schlaufe.
- **Verdrehsicherung** am festen Ende: zwei Wände 1,5 mm, 0,3 mm Spiel zur Zelle (Idee aus dem Handout).
- **Kippschutz / Überlast:** 4 Anschlagsockel bei (50|100, 10|140), Spalt **0,5 mm** zur Plattenunterseite. Darauf **gedruckte Zapfen Ø3,0** (3,5 hoch, 3,0 Eingriff; ersetzen die früheren M3-Gewindestifte) in Sacklöchern **Ø4,0** im Oberteil (0,5 mm Radialspiel; vorher 0,1, das hätte in PLA gerieben = Kraftnebenschluss). Die Stifte fangen nur Kippen/Verschieben. Oberseite bleibt glatt.
- **Gridfinity-Profil**, auf 50 mm skaliert: oben 49,6 mm, Fase 2,15, senkrecht 1,8, Fase 0,8, Gesamttiefe 4,75 mm. Darunter 1,6 mm Haut, dann PN532-Tasche **7,5 mm tief** (7,0 Modul + 0,5 Luft), 0,3 mm Spiel je Seite.
- **Platinen im Unterteil (Pins nach unten, Nutzer 2026-11-23):** Referenzteile aus den Eagle-Dateien bzw. dem Espressif-PDF, mit Stiftleisten (Kunststoff 2,5 unter der Platine, Pins 6,0 darunter, Pinenden 1,4 oben). Platinenunterseite 9,0 mm über dem Boden, Pinspitzen 0,5 mm über dem Boden. Keine geschlossenen Rahmen mehr, die Seiten bleiben frei zum Anlöten. **HX711** (4 Löcher Ø3,3) und **TCA9548A** (2 Löcher Ø2,5) sitzen auf gedruckten Stützen mit dünnen **Zentrierzapfen** (Ø2,5 bzw. Ø1,8, radial 0,40 / 0,35 mm, nicht angeschmolzen, Nutzerwunsch: gedruckte Zapfen kommen sonst zu dick). Gehalten werden sie von **gedruckten Rasthaken**: HX711 je einer an beiden Langseiten (6 mm breit, Mitte x = 15,24, dort keine Stiftleiste), TCA je einer an beiden kurzen Enden zwischen den Stiftleisten (4 mm breit, TCA-Stütze dafür auf Ø4,0 verschlankt, 0,74 mm Luft zum Arm). Insgesamt **11 Rasthaken**, alle mit Arm 1,2 mm, Dehnung 0,95–1,1 %. **ESP32** (keine Löcher) liegt auf zwei Auflagen unter der Platinenmitte, mit Führungswänden an Stirnseiten und USB-Ende. Gegen Abheben halten ihn **3 gedruckte Rasthaken** (Kabelbinder entfallen, Bodenschlitze geschlossen): je einer an beiden Langseiten in der 3,45-mm-Lücke zwischen USB-Buchse und Stiftleiste (Mitte 9,1 mm vom USB-Ende, 2 mm breit), einer 6 mm breit hinter dem Antennenüberstand. Arm 1,2 mm, Überdeckung 0,5, Spiel 0,2, Dehnung beim Einrasten 0,95–1,1 %. ESP32 von oben einsetzen, rastet ein. Annahme: Antennenüberstand 0,8 mm dick (`ESP_ANT_T`, nachmessen). USB-Ende zeigt nach links zur USB-C-Wand. Luft zum Oberteil mindestens 3,8 mm. Annahmen: JP2 am HX711 bestückt, Unterseite des ESP32 unter dem Modul frei, Lage der USB-C-Buchsen am ESP32 aus der Zeichnung abgegriffen.
- **Delock 87824 nach Herstellerzeichnung (`referenz/unterlagen/87824_draw_2.pdf`, 2026-11-23):** Einbaubuchse mit Flansch 36 × 12 mm, 2 Bohrungen Ø3,2 (Augen Ø6) im Abstand 28 mm, Länge 31 mm von der Stirnfläche bis zum Ende des Knickschutzes. Vorn steht ein Kragen mit der Buchse ca. 1,8 mm vor (abgegriffen), der im Ausschnitt 21,5 × 12,5 steckt. **Der Flansch sitzt innen an der Wand**, außen ragt nichts vor, also auch keine Kollision mit der Schürze (2,25 mm Luft). An der Buchse ist die Wand deshalb auf 2,0 mm gedünnt, mit einer Tasche für den Flansch. Der Stecker am anderen Kabelende ist 39 × 12,2 × 6,5 mm (Umspritzung), das Kabel hat 4,3 mm Außendurchmesser. **KONFLIKT:** Steckt dieser Stecker im ESP32, ragt er bis 9,6 mm an die USB-Wand heran und überschneidet die Einbaubuchse (194 mm³). Außerdem bleibt kein Platz, um das Kabel umzubiegen. Lage von ESP32 und Buchse sowie die Unterbringung der 1 m Kabel klären. Befestigung der Buchse offen: Ø3,2 bedeutet M3 mit Mutter (Normteil) oder eine gedruckte Klemmung.
- **USB-C:** linke Wand (40 mm lang, damit die Schraubenlöcher Material haben), Ausschnitt 21,5×12,5 mm, Unterkante 0,2 mm über Boden, darüber bleiben nur ca. 1,2 mm Wand.
- **Modulverbindung:** rechte Wand im Prototyp **geschlossen** (Nutzer 2026-11-23); die 4-mm-Innenverstärkung bleibt, damit später ein Verbinder (`CONN_W`/`CONN_H`) eingeschnitten werden kann, Plattenrand 0,75 mm Luft je Seite → 1,5 mm Spalt zwischen Modulen. Verbindungen nur im Unterteil.

## 4a. Maßprüfung der Bauteile (2026-11-23)
Abgleich aller Bauteilmaße mit Herstellerquellen. Die Stückliste führt einen Adafruit NAU7802 (4538). Laut Nutzer ist der **defekt**, verbaut wird der **SparkFun HX711** (2×).

| Bauteil | Maß im Modell | Quelle | Ergebnis |
|---|---|---|---|
| Wägezelle Adafruit 4541 | 75 × 12,7 × 12,7, 4× M4, Lochabstand 10 | Adafruit-Produktseite + `4541.pdf` | bestätigt |
| ESP32-C6-DevKitC-1 | 51,8 × 25,4, Pins 12,125 vom USB-Ende, Antenne 6,35 / 18,0 | Espressif-Maßzeichnung v1.2 | bestätigt |
| ESP32-C6-WROOM-1 Modul | Höhe 3,2, Antenne 0,8 dick | Espressif-Datenblatt, Zeichnung nur teilweise lesbar | Annahme (sichere Seite), nachmessen |
| SparkFun HX711 | 30,48 × 22,86, 4× Ø3,302 | SparkFun-Eagle-Dateien (Produktseite ohne Maße) | bestätigt |
| Adafruit TCA9548A (2717) | 30,48 × 17,78, 2× Ø2,5 | Adafruit-Eagle + Produktseite 30,6 × 17,6 × 2,7 | bestätigt |
| PN532 V3 (Funduino = Elechouse-Design) | 42,7 × 40,4, 4 mm hoch ohne Pins | Elechouse User Guide V3 | bestätigt. 2 Löcher diagonal, Lage nur aus Foto (ca. 6–7 mm vom Rand), Ø nicht bemaßt |
| Delock 87824 | Flansch 36 × 12, Ø3,2 / 28, Länge 31, Stecker 39 × 12,2 × 6,5 | Delock-Zeichnung `87824_draw_2.pdf` + Herstellerseite | bestätigt (Flanschdicke/Kragen abgegriffen) |
| Stiftleisten | Kunststoff 2,5, Pins 6,0 / 3,0 | Norm RM 2,54 | übliche Normwerte |

## 4b. Version V2 (2026-11-23): TCA auf der Platte, Kabelführung, USB vorne

V1 (`build_prototyp.py`, `Prototyp_15x15_Deckel.FCStd`) bleibt unverändert und liegt seit 2026-11-24 in `gehaeuse/archiv/V1/`. V2 entsteht aus `build_prototyp_v2.py` und erzeugt `Prototyp_15x15_Deckel_V2.FCStd` sowie `pruefbericht_deckel_v2.txt`. Ansichten liegen unter `ansichten/V2_*.png`.

**Layout**
- ESP32-C6 sitzt hinten bei (42,3 | 123), um 180° gedreht, mit Pins nach unten. Die Stirnwand am USB-Ende ist gekürzt, damit der Stecker frei bleibt.
- Die USB-C-Einbaubuchse (Delock 87824) sitzt in der vorderen Wand bei x = 121,5. Der Flansch liegt innen.
- Ergebnis: Stecker und Einbaubuchse kollidieren nicht mehr (Abstand 79 mm). Die linke Wand ist geschlossen.
- Beide TCA9548A sitzen an der Unterseite des Trägers bei (50 | 75) und (100 | 75), um 90° gedreht, 4,6 mm unter der Platte (geändert von 2,4 mm, damit ein flaches Litzenband über die Pins passt). Sie wiegen also mit.
- Gehalten werden sie von je 2 Rasthaken pro Board. Jeder Haken setzt 5 mm tief in einer Freistichtasche im Steg an. Damit hat der Arm 11,3 mm Länge und die Dehnung liegt bei 0,99 %.
- Der Bewegungscheck mit den TCAs ergibt 0 mm³ Überschneidung.

**Verdrahtung (mit der bestellten Litze LiYv 0,25 löten)**
- Über den Wägespalt laufen nur **4 Adern**: 3V3, GND, SDA und SCL.
  - Sie gehen als lockere Schlaufe von der Kabelgabel im Unterteil (30 | 100) zu TCA_A.
  - Die Schlaufe darf Unterteil und Zellen-Festende nicht berühren, sonst entsteht ein Kraftnebenschluss.
- TCA_A und TCA_B werden über den Lötverteiler versorgt (siehe unten). Für die Adressen braucht TCA_B A0 = 1 (Lötbrücke, Sache des Elektronik-Teams).
- Zuordnung der Kanäle (angepasst an die Leitungswege):
  - TCA_A: Reader 11, 12, 13, 21, 23
  - TCA_B: Reader 22, 31, 32, 33
- Jeder Reader bekommt sein eigenes SDA/SCL-Paar vom TCA-Kanal. VCC und GND laufen als Stichleitung oder Kette von Reader zu Reader.
- Kabelnuten 4 × 3 mm mit Haltelippen an der Plattenunterseite:
  - 21→11 und 23→13 im x-Steg 50
  - 31→32 und 33→32 im y-Steg 50/100 bei x = 125
- Die Leitungszonen links, in der Mitte und rechts haben keinen Kontakt zu Unterteil, Boards oder Zellen (laut Prüfbericht).
- Spannungsverteilung: 9× PN532 brauchen zusammen etwa 9 × 50–100 mA, das liegt nahe an der Grenze des 3,3-V-Reglers auf dem DevKit. **Das Elektronik-Team muss klären**, ob die Reader mit 5 V (VBUS) laufen sollen oder nacheinander aktiviert werden. Gehäuseseitig passt der Querschnitt 0,25 mm² für beide Varianten.

**Lötverteiler statt Durchschleifen an Board-Pins (Entscheidung Nutzer 2026-11-23)**
- Als Lötverteiler dient ein Stück Streifenraster mit 2,54 mm Raster, 22,86 × 15,24 mm groß (6 Streifen × 8 Löcher), selbst zugeschnitten. Die Kupferseite zeigt nach unten.
- Er hängt unter dem y-Steg 50, links von Zelle 1 (Mitte 22 | 50), zwischen Reader 11 und 12.
- Gehalten wird er wie die TCAs: 2 Rasthaken mit Freistich, Dehnung 1,52 %. Er bewegt sich mit der Platte, der Bewegungscheck ergibt 0 mm³.
- Streifenbelegung:
  - 3 Streifen für die Potentiale (5V / 3V3 / GND, Belegung noch offen)
  - 1 Streifen SDA, 1 Streifen SCL
  - 1 Streifen Reserve
- Pro Potentialstreifen gehen 7 von 8 Löchern weg:
  - Zuleitung
  - TCA_A, TCA_B
  - 4 Stränge: 11→21 (Nut y = 38), 12→22, 13→23 (Nut y = 112), 32→31/33 (über die mittlere Zone und TCA_B)
- Auf dem SDA/SCL-Streifen liegen nur die Zuleitung, TCA_A und TCA_B. **Die SDA/SCL-Paare der Reader laufen nicht über den Verteiler**, weil alle PN532 die Adresse 0x24 haben. Jedes Paar kommt einzeln vom eigenen TCA-Kanal.
- Die Kabelgabel für die Schlaufe über den Wägespalt sitzt jetzt bei (20 | 64), direkt unter dem Verteiler. Die Schlaufe hat 4 Adern, bei 5V + 3V3 sind es 5.
- Die Leitungszonen „Schlaufe Gabel → Verteiler“ und „Verteiler → TCA_A / Reader 22 / Strang 32“ sind frei von Unterteil, Boards und Zellen.
- Luftwerte des Verteilers: zum Unterteil 5,57 mm, zu den Zellen 4,07 mm. Die Lötstellen sind mit 1,5 mm unter der Platine angesetzt.

**PN532 umgedreht eingebaut (Entscheidung Nutzer 2026-11-23, ersetzt den vorigen Stand)**
- Grund: Die abgewinkelten I²C-Pins ragen über die Platinenkante. Nach Würth WR-PHD 61300411021 (Lochmitte → Körper 1,5, Körper 2,54, Steckpin 6,0) liegt die Spitze 10,04 mm von der Lochmitte entfernt, bei 6 mm Reihenabstand also **4,04 mm über der Kante**. In der alten Lage (Antenne oben) hätte jede Tasche ca. 5,5 mm Aussparung gebraucht, dafür reichen die Stege nicht.
- Neu: **Antenne, Bestückung und Stiftleiste zeigen nach unten.** Die Platinenrückseite liegt an der Taschendecke. Die horizontalen Pins liegen 0,45 mm unter der Trägerunterseite, eine Aussparung ist nicht nötig.
  - Tasche nur noch 2,3 mm tief (`PN_Z0` 0,5 + Platine 1,6 + `PN_SEAT_CLR` 0,2). Über der Lötbeinreihe ein Freistich 1,7 mm (`PN_TAIL` 1,4 laut Würth).
  - Die Trägerdicke bleibt 8,5 mm (`PN_DEPTH` 7,5), weil die Rasthaken-Arme die Höhe brauchen.
  - **Nachteil:** Die Antenne liegt jetzt 8,6 mm unter dem Behälterboden statt 1,6 mm, dazwischen PLA und die Platine. Die Lesereichweite mit den echten Tags testen. Falls sie nicht reicht: Träger dünner machen (dann kürzere Haken, Umbau).
- **Reader-Modell** im Skript (`pn_model`): Platine 42,7 × 40,4 × 1,6, Bestückung als Block 1,2 mm unter der Platine (3 mm vom Rand, `PN_COMP_H`/`PN_COMP_IN` = Annahme), 4-polige Winkelleiste mit Körper, horizontalen Pins und Lötbeinen. Objekte `REF_PN532_ij` (rot) und `REF_PN532_ij_Stiftleiste` (schwarz).
  - Die Leiste ist symmetrisch um die Kantenmitte modelliert. Laut Foto liegt sie bei −6,1 bis +4,4 mm; der Freiraum ±6,6 mm deckt beides ab.
  - Das Modell ergibt 5,5 mm Gesamthöhe, der Nutzer hatte ca. 7 mm gemessen → `PN_T` nachmessen.
- **I²C-Kante:** Spalte 1 → +x, Spalte 2 und 3 → −x. An den Außenwänden würden die Pins aus dem Modul ragen, deshalb zeigen alle Leisten zu den inneren x-Stegen.
- **Taschen verschoben** (Spalten x = 23,9 / 76,2 / 126,1 statt 25 / 75 / 125, max. 1,2 mm aus der Feldmitte):
  - Steg A (zwischen Spalte 1 und 2) 9,0 mm: Darunter liegen die Leisten beider Reader, die Pinspitzen haben 1,52 mm Abstand.
  - Steg B 6,6 mm, Außenränder 1,5 mm, y-Stege unverändert 9,0 mm.
  - Anschlagzapfen, Deckel-Zentrierzapfen und TCA_A/TCA_B sitzen auf den neuen Steg-Mitten (x 50,05 / 101,15). Der vordere Zapfen am Steg B liegt bei y = 12 statt 10 (1,43 mm Luft zum Flansch der USB-Buchse).
  - ESP32 um 2,5 mm nach links (x 39,8), damit der USB-Stecker nicht unter der Leiste von Reader 33 liegt. Lötverteiler auf x 18.
- **Rasthaken:** Spalte 2 an den x-Kanten (I²C-Kante mit Versatz 10–12 mm neben der Leiste), Spalte 1 und 3 an den Längskanten ±y (der Außenrand ist für einen Freistich zu schmal). Die Haken prüfen jetzt auch den Abstand zur Wägezelle (≥ 1,0) und zur Außenwand.
  - 18 Haken, Arm 7,6 mm, Dehnung 1,87 %, Restwand ≥ 1,85 mm, Luft zu Nachbarteilen ≥ 1,41 mm.
- Einsetzen: Reader mit der Rückseite voran von unten einschieben, bis er einrastet. Lösen: Arm von unten in den Freistich drücken.

**PN532 Weg 3: Reader tiefer im Träger, vom Deckel gehalten (Entscheidung Nutzer 2026-11-24, ersetzt Tasche, Haken und Pin-Maße oben)**
- Echte Maße des Readers (Nutzer, Messschieber und Foto `IMG_1762.pdf`):
  - Platine 1,52 mm. Leiste 4,26 mm unter der Platine (`PN_HDR_H`), Pins in 3,2–3,84 mm Höhe (`PN_PIN_Z` 3,52).
  - Pinüberstand über die Kante ca. 1 mm (`PN_PIN_OVER`, vom Nutzer bestätigt am 2026-11-24).
  - I²C-Leiste mittig an der kurzen Seite, Lötreihe 6 mm innen.
  - SPI-Leiste (8-polig, abgewinkelt) an der langen Seite: 13,11 mm von der I²C-Kante, 8,63 mm von der anderen Kante, Lötreihe 6 mm innen.
  - DIP-Schalter 2,5 mm hoch, neben der I²C-Leiste auf der Seite gegenüber der SPI-Leiste (Lage aus dem Foto, Annahme). Übrige Bestückung ca. 1 mm.
  - Von oben gesehen (Reader umgedreht) liegt die SPI-Leiste auf derselben Vorzeichenseite in y wie die I²C-Leiste in x.
- Mit diesen Maßen ging die flache Lage nicht mehr: 7 von 9 Readern stießen an Zellen, Unterteil oder USB-Stecker. Pins kürzen hätte nicht gereicht.
- **Neu:**
  - Die Tasche geht durch den ganzen Träger. Der Reader wird **von oben eingelegt**, Bestückung nach unten.
  - Er liegt mit den Ecken auf 4 Eckauflagen 2,7 × 2,7 mm (`PN_POST`), Platinenunterseite 5,3 mm über der Plattenunterseite (`PN_Z0`). Die Leisten enden 1,04 mm über der Plattenunterseite, also ganz im Träger.
  - Pin-Aussparungen (1,3 mm) in der Taschenwand an I²C- und SPI-Leiste, über die volle Höhe, damit der Reader von oben hineinpasst.
  - Der **Deckel** hat je Reader eine Druckplatte (1,4 mm) mit Freistich für die Lötbeine. Luft zur Platinenrückseite 0,2 mm. Die Druckplatten zentrieren den Deckel, die Deckel-Zentrierzapfen entfallen (`COVER_PINS = []`).
  - Die Reader-Rasthaken entfallen (`PN_HOOKS` = 0), der Arm wäre nur ca. 3 mm lang.
  - Abstand Antenne (Platinenunterseite) zum Behälterboden **3,8 mm** statt 8,6 mm.
- Prüfbericht: gültig, 0 Kollisionen, Bewegung 0 mm³, kein Reader-Konflikt.
  - Leisten zu festen Teilen ≥ 1,12 mm.
  - Restwand zwischen den Taschen ≥ 1,5 mm.
  - **Ausnahme:** Restwand von der Kopfsenkung am Freiende zur Readertasche 0,8 mm auf 4,0 mm Höhe (y-Steg nur 9 mm).
- Leitungen: Die Bänder liegen weiter unter der Platte. Die Steigleitung von ca. 3 mm durch die Aussparung zum Pin ist nicht modelliert.
- Druck:
  - Träger umgedreht drucken. Die Eckauflagen sind kleine Überhänge an den Taschenecken.
  - Deckel stützfrei (2026-11-24): Er hat vorne und hinten eine **Randleiste** von 1,2 × 1,4 mm (`COVER_LIP_W`, `COVER_LIP_CLR` 0,2), der Träger dort eine passende Stufe. Beim Druck steht der Deckel auf 9 Druckplatten und 2 Leisten.
    - Alle hängenden Flächen sind Brücken bis ca. 9,6 mm, an den Steg-Kreuzungen bis ca. 7 mm von der nächsten Auflage entfernt. Links und rechts hängen 1,8 mm frei. Geprüft im 1-mm-Raster.
    - Restwand Stufe zur Readertasche bzw. SPI-Aussparung: 1,35 mm.
    - Am Träger (umgedreht gedruckt) wird die Stufe zu einem Überhang von 1,4 mm vorne und hinten, das ist unkritisch.
- Projektdokumentation mit Schritten und Entscheidungen: Claude-Doc „Smart Kitchen Mat – Gehäuse-Prototyp: Konstruktionsschritte und Entscheidungen“.

**Leitungen als Platzhalter im Modell (`REF_Litze_*`), Stand umgedrehte Reader**
- Farben: gelb = an der Platte, blau = im Unterteil, magenta = Schlaufe über den Wägespalt.
- Die Litzen werden an die horizontalen Pins gelötet (unter der Platte). Flache Bänder laufen 0,2 mm unter den Pins, neben den Kunststoffkörpern vorbei: Daten auf der −y-Seite der Leiste, Versorgung auf der +y-Seite. Die Kabelnuten im Träger entfallen.
- Unter der Platte liegen bei y = 50 und y = 100 die Wägezellen. Leitungen zwischen den Reihen laufen deshalb **links bei x = 35,3 oder rechts bei x = 116,3** an den Zellen vorbei.
- Belegung (Stand 24.11., seit 26.11. geändert, siehe 4d): TCA_A = Reader 11, 12, 13, 21, 22, 23 (6 Kanäle), TCA_B = 31, 32, 33. Die Drähte gehen neben der TCA-Platine senkrecht hinunter zu den Pins (Löthöhe 9,5 mm).
- Versorgung (`NP_WIRES` = 3, Platzhalter): Verteiler → Reihe 1 (11 → 21 → 31), Verteiler → Reihe 2 (12 → 22 → 32, flach über beide TCAs), weiter → Reihe 3 (13 → 23 → 33). Verteiler → TCA_A, TCA_A → TCA_B für Versorgung und Bus.
- Prüfbericht: keine Kollision, Bewegungscheck 0 mm³. Kleinste Luft zu festen Teilen 0,70 mm (Daten 33 über dem Kabel des ESP32-Steckers), Band über den TCAs 0,60 mm.
- Litzenbedarf ca. 3,9 m, mit Zugabe 5,1 m (ohne Zellkabel).
- Nicht modelliert: Zellkabel Wägezelle → HX711. Sie sollen am Festende mit einer Schlaufe geführt werden.

**Delock-Kabel (1 m) in der Wickelkammer**
- Die Wickelkammer liegt im rechten Streifen: hohler Wickelkern, Radius 11,6 mm, 3 Lagen, mit Führungswand, Niederhaltern und Lücke für das Steckerkabel.
- **Die Kammer reicht nicht ganz.** Für 909 mm Kabel braucht es 3,74 Windungen, Platz ist für 3. Es bleiben etwa 180 mm übrig.
- Optionen:
  - (a) ein kürzeres USB-C-Verbindungskabel (0,5 m) zwischen ESP32 und Einbaubuchse verwenden,
  - (b) den Rest außen führen, also mit Kabelbinder/Klett am Stecker,
  - (c) eine vierte Teillage zulassen. Dann sinkt die Luft zur Platte von 3,3 auf etwa –1 mm, deshalb geht das nur ohne Kammerdeckel → nicht empfohlen.
- Den Biegeradius von 11,6 mm (2,7 × Außendurchmesser) gibt Delock nicht an. Bitte am echten Kabel testen.

**Bekannte Restpunkte V2**
- Luft TCA zum Unterteil 1,61 mm. Das ist mehr als die maximale Absenkung von 0,78 mm, aber knapp.
- Neben den Freistichtaschen bleiben 1,25 mm Steg. Zur flachen Zellenfreisparung hin ist es eine offene Stufe, das ist unkritisch.
- Gravur zeigt noch „R3“.

## 4c. Gridfinity-Behälter (2026-11-24)
- Skript `build_behaelter.py`. Es liest das Gridfinity-Profil aus `build_prototyp_v2.py`, baut 1×1, 2×1 und 2×2, prüft die Passung auf der Matte und schreibt `Behaelter.FCStd`, `pruefbericht_behaelter.txt` und `stl/Behaelter_*.stl`.
- Maße:
  - Fuß 0,25 mm je Seite kleiner als die Tasche, steht auf dem Taschenboden. Der Körper liegt 0,2 mm über dem Mattenrand.
  - Höhe 40 mm über der Matte (Annahme), Wand und Boden 1,2 mm.
- RFID-Tag: SAG 440880538-0107201 (NTAG213 Metal Label, DigiKey: Ø25, Bezeichnung „D29“). Unter jedem Fuß liegt eine Mulde Ø29,6 × 1,2 mm (`TAG_T` = PLATZHALTER, Dicke nachmessen).
  - Das Tag kommt unter das Feld, das gelesen werden soll, die **Lesefläche nach unten** (Metall-Label mit Abschirmung auf einer Seite).
- Prüfbericht: gültig, ein Körper, 0 mm³ Überschneidung mit dem Deckel. Vom Tag bis zur Oberseite der Reader-Platine sind es 2,2 mm.
- Druck: aufrecht ohne Stützen. Die Muldendecke ist eine Brücke von 29,6 mm.

## 4d. Träger +1 mm und Passzapfen Deckel–Träger (2026-11-24)
**Anlass:** Die FEM-Studie (`gehaeuse/fem/ergebnisse/pruefbericht_fem.txt`, `gehaeuse/fem/fem_traeger_deckel.py`) zeigt: Der Träger liegt nur auf den zwei Zellen-Freienden auf, die auf einer Diagonalen sitzen, und ist für Ecklasten zu weich. Linear gerechnet überbrückt er die 0,5 mm Anschlagluft schon bei ca. 1,1 kg auf einem Eckfeld (Deckel lose). Die Festigkeit ist unkritisch (Sicherheit 4 bis 30). Deckel und Druckplatte sind ebenfalls unkritisch: 0,04 mm Absenkung, der Reader bleibt lastfrei. Studie `gehaeuse/fem/fem_variante_traeger_plus1.py`: +1 mm bringt ca. 23 % weniger Durchbiegung. Mit vollflächiger Verbindung schafft er ca. 2,8 kg pro Eckfeld, 5 kg auf einem Eckfeld werden auch dann nicht erreicht.

**Entscheidung des Nutzers:** Den Träger 1 mm höher machen und Deckel und Träger verbinden. Als Verbindungsart sollte die genommen werden, die sich am besten drucken lässt.
- `PN_DEPTH` von 7,5 auf 8,5: Träger 9,5 mm, Trennebene bei z = 29,60, Gesamthöhe 34,95 mm. Am Unterteil ändert sich nichts.
- Die Reader-Höhe `PN_Z0` bleibt bei 5,3. Dadurch werden Druckplatten und Randleisten 2,4 mm hoch, und die Antenne liegt 4,8 statt 3,8 mm unter dem Behälterboden. Grund: Die Zapfen dürfen nur so lang sein wie die Druckplatten, weil der Deckel auf Druckplatten, Randleisten und Zapfen zugleich gedruckt wird.
- **8 Passzapfen** Ø3,0 × 2,4 mm am Deckel greifen in Bohrungen Ø3,6 im Träger. Die Bohrungen haben je 3 Quetschrippen, Innenkreis = Zapfendurchmesser (Nennmaß 0, der Presssitz entsteht durch den Druckschwund), dazu eine 0,4-mm-Einführfase. Rasthaken wurden verworfen, weil sie beim Druck in Lage senkrecht stünden und dann quer zu den Schichten biegen würden.
- Die Lage wird automatisch gesucht, mit mindestens 1,2 mm Restwand: (50|8) (50|142) (8|50) (142|50) (8|100) (142|100) (50|50) (101|100). Der Außenrand ist nur 1,5 mm breit, und an Steg B (6,6 mm) ist an den Enden bei y = 8 und y = 142 kein Platz.
- Die Freiend-Schrauben bleiben M4x12. Die Einschraubtiefe in der Zelle sinkt auf 6,5 mm.
- **Testdruck-Coupon (2026-11-25):** `gehaeuse/skripte/build_coupon.py` schneidet 5 Ausschnitte aus den echten Teilen der V2-FCStd (A Träger-Ecke mit PN532-Tasche und 3 Zapfenbohrungen, B passende Deckel-Ecke mit Zapfen und Gridfinity-Feld, C Freiende-Senkung M4, D Festende-Sockel M4 + Scheibe, E HX711-Rasthaken, F TCA9548A mit Zentrierzapfen D1,8 und Endhaken). Er folgt damit automatisch jedem Modellstand. Ausgabe: `Coupon_*.stl` im Druckpaket und in `stl/`, Bericht `gehaeuse/pruefberichte/pruefbericht_coupon.txt`. Die USB-Wand ist nicht enthalten, weil die Buchse noch nicht nachgemessen ist.
- **Coupon-Rückmeldung (2026-11-26):** A+B passen (Presssitz, Reader-Tasche, Gridfinity), E passt, F Zapfenlage passt (Haken bewusst nicht gedruckt). C: Senkungsboden unsauber, 0,8-mm-Wand gedruckt. D: Kabelaustritt mit Silikon an der Wägezelle stößt an die Verdrehsicherung, Silikon auch oben auf der Messzone (Freistich oben nur 0,8 mm) → **Maße der Zelle mit Kleber vom Nutzer offen**.
- **Umgesetzt 26.11.:** Opferschichten (`SACR_LAYER` 0,2) an Freiend- und Festend-Senkungen (Schicht 1 Schlitz, Schicht 2 Quadrat = saubere Brücken). Kabelwege Daten 11+21 (x 33,3) und 13+23 (Versatz bei y 109) neu geführt: Luft 1,8 statt 0,9 mm zu Zelle 1, Zelle 2 und ESP32-Modul. Kabelkanäle im Träger verworfen: Engstellen liegen seitlich unter Readertaschen, darüber die Reader-Pins, kein Trägermaterial. Offen: Strang Reihe 3 nur 1,2 mm über USB-Buchse ESP32 (Lösung: ESP32 tiefer, mit nächster Unterteil-Änderung). Bild `gehaeuse/ansichten/kabelwege_v2.png`. STLs und Coupons neu exportiert.
- **Einzeladern-Ansicht (2026-11-26):** `gehaeuse/verdrahtung/kabelwege_einzeladern.py` → `gehaeuse/ansichten/kabelwege_einzeladern.png`, liest `gehaeuse/pruefberichte/kabelwege_v2.json` (schreibt das Build-Skript: Bandverläufe, Pinlagen). Pinfolge I2C-Leiste PN532 (Foto IMG_1762, bestätigt 27.11.): GND, VCC, SDA, SCL, GND am nächsten zur SPI-Leiste. Spalte 1 (SPI +y): GND bei +y; Spalten 2/3 (SPI −y): GND bei −y. Das Build-Modell ist davon nicht betroffen (Bänder enden in der Readermitte), nur die Einzeladern-Ansicht.
- **Befund TCA9548A-Pinbelegung (Eagle .brd):** JP3 = VCC, GND, SDA, SCL, RST, A0, A1, A2, Kanal 0 SDA/SCL, Kanal 1 SDA/SCL; JP1 = Kanäle 2–7. Je Langseite eine 12-pol. Leiste. Im Modell kommen an TCA_A links Bus + 5 Reader-Paare an, rechts 1 Paar + Bus nach TCA_B → passt nicht zur Belegung (links wären nur 2 Kanäle). Vorschlag: TCA_A um 180° drehen (JP1 mit Kanal 2–7 nach links für 11, 12, 13, 21, 23; JP3 nach rechts für Bus ein/aus, Reader 22 auf Kanal 0). TCA_B passt (Bus links = JP3, Reader 31–33 rechts = JP1).
- **Umgesetzt 26.11. (TCA_A gedreht):** Belegung jetzt TCA_A links JP1 = Reader 11, 12, 13, 21, 23 (Kanäle 2–7), rechts JP3 = Bus ein/aus + Reader 22 auf Kanal 0. Der Bus vom Lötverteiler läuft über eine Querkerbe in Steg A (`GROOVES`, `GROOVE_W` 5,8 × `GROOVE_D` 2,4 mm, Annahme, bei y 67,6, reicht je 2 mm in die Taschen) zur rechten Leiste von TCA_A, dann wie bisher weiter zu TCA_B. Prüfbericht: Körper gültig, 0 Kollisionen, 7 Bewegungsfälle 0 mm³; engste Stellen des Bus 0,26 mm zur Leiste TCA_A, 0,67 mm zu den Pins PN532 12/22. Kanalbelegung muss das Elektronik-Team bestätigen. FEM mit Kerbe neu gerechnet (26.11.): Absenkung am Anschlag steigt um 2–5 % (A Ecke 1,79→1,87, B Ecke 1,39→1,46, C Ecke 0,85→0,88, C verteilt 0,28→0,29 mm), Bewertung unverändert. Alter Stand in `fem/studie_traeger_plus1_vor_kerbe_2026-11-25.txt`. Sicherung vorher: `archiv/build_prototyp_v2_vor_tca_drehung_2026-11-26.py`. STLs (Träger) und Coupons A, C, F neu exportiert, Einzeladern-Bild neu.
- **Offen:** Den Presssitz am Testdruck-Coupon prüfen (`CRUSH_W`, `COVER_PIN_HOLE`). Die STLs liegen seit 26.11. in `gehaeuse/druck/` (vorher doppelt in `druckpaket_2026-11-24b/` und `stl/`). Das alte Paket liegt unter `archiv/druckpaket_2026-11-24_alt`. Die FCStd wurde am 24.11. um 20:01 über die Bridge mit Farben gebaut, der Prüfbericht ist unverändert.
- **FEM auf dem neuen Modell (2026-11-25)**, `gehaeuse/fem/fem_variante_traeger_plus1.py` → `gehaeuse/fem/ergebnisse/studie_traeger_plus1.txt`. Höhen werden jetzt aus dem Modell gelesen, Zapfen aus dem Prüfbericht. Absenkung am Anschlag (Spalt 0,5 mm), in Klammern die lineare Last bis zum Anschlag:
  - A lose: Ecke 5 kg 1,79 mm (1,4 kg), verteilt 10 kg 0,73 mm
  - B nur Zapfen, ohne Kontakt (untere Grenze): Ecke 1,39 mm (1,8 kg), verteilt 0,51 mm
  - C vollflächig verbunden (obere Grenze): Ecke 0,85 mm (2,9 kg), verteilt 0,28 mm (ok)
  - Die Wirklichkeit liegt zwischen B und C. Die Zapfen bringen gegenüber lose 22–30 %. Für 5 kg pro Eckfeld reicht das nicht, größere Hebel: Träger unten schließen (Kastenquerschnitt), Rippen/Auflage ändern oder die Last pro Feld als Anforderung festlegen.

## 4e. Messwerte Wägezelle und Delock eingebaut (2026-11-27)
- **Silikon und Kabel an der Wägezelle (Nutzer):**
  - **Oben und unten:** 1,5 mm (gemessen 15,12 − 12,7 = 2,42 → 1,21 je Seite, mit 1,5 gerechnet), auf 26,64–45,68 mm ab Festende, je Ende +1,0 Toleranz.
  - **Seitlich:** 1,9 mm (+0,3) auf der Kabelseite, vom Festende bis zum Silikonende. Das Kabel tritt hinten am Festende aus.
  - **Im Modell:** Sperrzonen `REF_Zelle{1,2}_Silikon_Kabel` und `REF_Zelle{1,2}_Kabelaustritt`, die im Bewegungscheck als fest zählen.
  - **Freistich im Träger:** über dem Silikon 2,3 mm tief, über dem seitlichen Kabelband 0,8 mm. Luft Silikon–Träger 0,80 mm.
- **Zellen gedreht (`CELL_FLIP` = 1, Annahme):** beide Zellen um die Längsachse gedreht, Pfeil nach oben.
  - **Grund:** Die Kabelseite liegt so außen. Sonst stößt sie an die Eckauflagen und Pins der mittleren Reader-Reihe.
  - **Folge für die Elektronik:** Das Messsignal kehrt das Vorzeichen um. In der Software ausgleichen oder die Adern A+ und A− tauschen.
- **Verdrehsicherung:** nur noch auf der kabelfreien Seite.
- **Kabelaustritt:** Hinter dem Festende von Zelle 2 sind bis zur Wand der Wickelkammer (x = 115) nur 2,5 mm frei. Daher `CABLE_EXIT_L` = 2,0, das Kabel muss direkt hinter der Zelle abknicken.
- **SPI-Leiste an Reader 22 und 23 abkneifen (`PN_SPI_CUT`, Nutzer 27.11.):**
  - **Problem:** Die abgewinkelten SPI-Pins lagen 1,46 mm über den äußeren 2,5 mm der Zelle, genau über dem Silikon. Die Luft war 0,25 mm, unter Überlast gab es Berührung.
  - **Warum das geht:** SPI wird nicht genutzt, die Reader laufen über I²C.
  - **Ausführung:** Pins am Knick abkneifen, der Kunststoff fällt mit ab. Die senkrechten Stummel bleiben, sie haben 2,42 mm Luft.
  - **Verworfen:** Reader höher setzen. Das hätte eine neue Reader-Tasche und damit einen neuen Coupon bedeutet.
- **Delock 87824 (Nutzer):**
  - Flansch 7,51 dick, Kragen 20,88 × 12,0, 1,9 vor dem Flansch, Gehäuse 6,33 × 6,35, Knickschutz Ø7,11 × 5,86.
  - Befestigung: 2× M3-Senkschraube ISO 10642 M3×10 von außen in die Mutter im Flansch, Senkung Ø6,9 außen in der Wand. Restwand unter der Senkung 0,35 mm, das ist zulässig, weil der Kegel trägt.
  - Der Anschlagsockel B ist wegen des dicken Flanschs von y = 12 auf 13,9 gewandert.
- **Tag-Mulde** im Behälter: 1,2 mm bestätigt, der Testdruck passt.
- **Coupons:** Neu erzeugt haben sich nur A (0,8-mm-Freistich, für die Passprobe egal) und D (Verdrehsicherung auf der Kabelseite entfällt; am gedruckten Coupon einfach abschneiden). Ein Neudruck ist nicht nötig.
- **Offen ESP32:** gemessen 15,12 hoch statt 13,4 im Modell. Grund ist ein abgewinkelter Jumper oben auf der Platine. Lage, Höhe und Überstand fehlen noch.

## 4f. Stromkonzept der Elektronik eingebaut (2026-11-27)
Quelle: `elektronik/VERDRAHTUNG_UND_STROMVERSORGUNG.md` und `schaltplan_gridscale.html` (Commit ee8bd84).
- **Wickelkammer entfällt:** Das Delock-Kabel wird auf ca. 21 cm gekürzt (`CABLE_LEN` 250). Inselring, Führungswände und Niederhalter sind entfernt, `COIL_*` gestrichen.
  - **Kabelwege im Modell:** Buchse → Spleiß hinter dem Hub 18 mm, Hub → ESP32-Stecker 112 mm, am Boden entlang bei x ≈ 139 nach hinten, dann bei y = 116 zum Stecker.
  - **Gesamtlänge:** 207 mm mit Buchse und Stecker, Rest 43 mm als Spleißzugabe.
- **Kabelaustritt** hinter dem Festende wieder 8 mm (`CABLE_EXIT_L`), die Wand bei x = 115 ist weg.
- **Power-Hub** (Streifenraster 6 × 8 = 15,24 × 22,86, `HUB_*`), vorne rechts bei x 127,5–142,7, y 13,5–36,4:
  - **Einbaulage:** Bestückung nach unten, Kupfer oben. Er liegt auf 2 Leisten vorn und hinten mit Schaumklebeband, die Unterseite ist auf z = 10,8.
  - **`JP_NFC`:** zeigt nach unten in ein Bodenfenster (8,1 × 5,5 mm). Zum Flashen das Modul anheben und den Jumper von unten ziehen, ohne das Gehäuse zu öffnen.
  - **Elko:** D8 × 12, liegt unter dem Hub zwischen den Leisten.
  - **Luft:** Hub zu Platte, Reader und Bändern 7,1 mm, zu Delock-Buchse und Kabel 2,75 mm.
- **Belegung im Modell (Abweichung vom Elektronik-Plan, gleiche Netze):**
  - **Am Hub** liegen nur VBUS_IN, 5V_NFC und GND.
  - **Am ESP32** bleiben 3V3, SDA, SCL und die Versorgung der HX711. So werden die Wege kürzer, und es läuft kein 5er-Bündel quer durchs Unterteil.
  - **5V_NFC** läuft als einzelne Litze vom Hub bei y = 75 unter den TCAs hindurch zur Gabel (20|64). Luft zu den TCA-Pins 1,6 mm.
  - **Mit der Elektronik abstimmen.**
- **Schlaufe** mit 5 Adern (5V_NFC, 3V3, GND, SDA, SCL), die Gabel ist auf 3,8 mm geweitet. `NP_WIRES` = 2 ist bestätigt.
- **Coupons** sind unverändert. Das Unterteil hat 79 479 mm³ (vorher 85 595).
- **ESP32-Jumper (Nutzer 27.11.):** Er sitzt unter der UART-Buchse. Die UART-Buchse liegt links, wenn die Bauteile oben sind und die Buchsen zum Betrachter zeigen (`ESP_JMP_SIDE` = 2).
  - **Folge für die Bänder:** Das Band „Daten 13 + 23 → TCA_A“ läuft jetzt bei y = 121,3 hinter dem Jumper. Die Luft ist 0,80 mm, der Bewegungscheck zeigt 0 mm³.
  - **Stecker:** Der Delock-Stecker steckt im Modell in der UART-Buchse. Dafür muss die Software nichts umstellen, das noch mit dem Software-Team abstimmen.

## 4g. Montagelöcher in den Lochrasterplatinen (2026-11-27)
Nutzer 27.11.: Hub und Lötverteiler bekommen Montagelöcher. Ein vorhandenes Rasterloch auf Streifen 3, das zweite von jedem Ende (3,81 mm vom Rand), wird auf 2,5 mm aufgebohrt (`HUB_HOLE_K`, wie `TCA_HOLE`). Das trennt nur Streifen 3, die Nachbarstreifen bleiben 0,3 mm frei.
- **Power-Hub:** 15,24 × 30,48 (12 Raster, `HUB_L`), damit alle 6 Streifen 8 nutzbare Löcher behalten. Er liegt jetzt auf 2 Domen Ø 4 mit Zentrierzapfen (Lochabstand 22,86) statt auf Leisten mit Schaumklebeband. Gehalten wird er von 2 Rasthaken diagonal an den Langseiten im Endbereich (Arm 10,1, Dehnung 1,24 %). An den kurzen Enden laufen hinten die Delock-Adern über die Kante. Diese Adern liegen jetzt 7,5 mm vor der Hinterkante auf der Platine. `JP_NFC` und das Bodenfenster sind um 2 Raster nach hinten gerückt, der Hub reicht jetzt bis y 44,0.
- **Lötverteiler:** Er bleibt bei 22,86 × 15,24 (`VT_L`), denn länger geht nicht: Links liegt die Unterteilwand, rechts das Band Daten 0 am Rasthaken. Die Löcher liegen auf dem Reserve-Streifen 3, Abstand 15,24. Ein Abstandsbund Ø 3,4 (`VT_STANDOFF_D`) von der Platte legt die 2,4 mm fest, ein Zapfen zentriert, die Rasthaken bleiben. Streifen 3 behält 5 Löcher.
- **Prüfbericht:** 0 Kollisionen, Bewegungscheck 0 mm³. Coupon F (TCA) gilt für Zapfen und Haken mit.

## 5. Parameter und Status
Alle Maße stehen in `PARAMS` am Anfang von `build_prototyp.py` mit Status (`bestaetigt` / `Annahme` / `PLATZHALTER` / `Norm`) und Quelle. Dieselbe Liste wird als Tabelle `Parameter` ins FreeCAD-Dokument geschrieben. **Neue Maße immer dort ändern, nie im Modell von Hand.**

Offene Platzhalter (Stand 27.11.): `CONN_W`, `CONN_H` (Verbinder noch nicht festgelegt).
Als "Annahme" nachmessen oder im Testdruck prüfen: `M4_PILOT` 3,4, `M4_HEAD_CB` 8,5, `STOP_GAP` 0,5 (hängt an der Durchbiegung der Zelle), PN532-Maße 42,7×40,4, Passungen (0,3–0,5 mm), USB-Ausschnitt.

## 6. Prüfbericht (letzter Lauf)
Unter-/Oberteil gültige Körper, **0 mm³ Überschneidung**, **0 Kollisionen** mit den Referenzteilen. Spalte: Überlast 0,50, Zapfen radial 0,50, Verdrehsicherung 0,30, Luft unter freiem Zellenteil 5,00 (seitlich zum ESP32-Rahmen 4,35), Freistich Zelle–Platte 0,80, Auflage am Freiende 0 (Kontakt). Steg zwischen PN532-Taschen 6,7 mm (x) und 9,0 mm (y), Restwand um Stiftloch 1,35 mm. Beide Teile flache Unterseite, je ein Körper. Skript läuft auch headless: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "import FreeCAD as App; exec(...)"`.

## 7. So wird gearbeitet (FreeCAD per MCP-Bridge)
- FreeCAD läuft auf dem Mac des Nutzers, Steuerung über **MCP Bridge for FreeCAD** (`execute_python`). Ohne Einstellung "Unrestricted" fragt FreeCAD vor jedem Lauf nach, der Job-Token läuft ab.
- Skript ausführen: `exec(compile(open("<Pfad>/cad/build_prototyp.py", encoding="utf-8").read(), "build_prototyp.py", "exec"))`. Es löscht alle Objekte im Dokument `Kuechenregalboden_Prototyp` und baut neu auf.
- Pfad im Skript (`outdir`) ist auf den Mac des Nutzers festgelegt, bei anderer Umgebung anpassen.
- Aus der Cloud-Umgebung zum Mac: `device_commit_files` kam **bei Änderungen oft zuerst mit dem alten Stand** an. Danach die Größe der Datei auf dem Mac prüfen und notfalls erneut committen.
- Regeln: erst Maße abfragen, dann mit markierten Platzhaltern bauen. Immer den Prüfbericht lesen, nicht nur den Lauf als erfolgreich ansehen.

## 8. Offene Punkte / nächste Schritte
1. **PN532 sichern.** Frage an den Nutzer offen: Hat das Board Befestigungslöcher (Ø, Abstand zum Rand)? Auf welcher Seite sitzt die Pinleiste, zeigen die abgewinkelten Pins nach unten oder zur Seite? Wegen der Vorgabe (wenig Normteile, nur Standard-M4) bevorzugt eine **gedruckte Halterung ohne Schrauben**, z. B. Halteklammer oder Rahmen mit Federarmen; dafür Bauteillage am Board-Rand klären. Eine einfache Rastnase am Taschenrand funktioniert nicht, weil das Board oben an der Taschendecke liegt und 5–6 mm Bauteile darunter hängen.
2. **Kabelführung der 9 Reader.** Weitgehend erledigt: Taschen sind nach unten offen, Kabel gehen direkt in den Raum zwischen den Teilen (ca. 11 mm über den Boards). Schlaufen vorsehen.
2a. **Delock 87824 ist ein 1-m-Kabel** (Einbaubuchse + Stecker). Unterbringung offen: Kabelkammer/Wickel im Unterteil oder außen führen. Stecker am ESP32-USB-Ende braucht Platz (ca. 44 mm bis zur USB-Wand).
3. **USB-C-Buchse** nachmessen (Ausschnitt, Lochabstand, Schraubendurchmesser, ob rechteckig).
4. **Modulverbinder** festlegen (Fenster `CONN_W`/`CONN_H`).
5. **Testdruck** eines Coupons: M4-Kernloch, Senkung, Stiftloch Ø3,2, PN532-Tasche, USB-Wand.
6. Optional: schlankere Variante (PN532 in die Zellenschicht hängen, ca. −5 mm), Kantenfase, Orientierung des ESP32-USB-Ports zur USB-C-Wand.
7. Skill `cad-konstruktion-freecad` wurde vorgeschlagen (Workflow, PLA-Regeln, Parameter-Status). Er soll um Parameter-Status-Taxonomie und automatischen Prüfbericht ergänzt werden, falls noch nicht gespeichert.
