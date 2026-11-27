# Projekt: GridScale – Die intelligente Wiegematte (SmartSystems2) – Gehäuse-Prototyp

Projektname seit 2026-11-26: **GridScale – Die intelligente Wiegematte** (vorher Smart Kitchen Mat / Küchenmatte / Küchenregalboden).

Antworte auf Deutsch. Der Nutzer (Master-Student) ist hier nur für **Gehäuse/Konstruktion** zuständig, nicht für Elektronik oder Firmware.

## Zuerst lesen
1. `gehaeuse/UEBERGABE.md` – kompletter Stand, Konstruktionsentscheidungen, offene Punkte.
2. `gehaeuse/skripte/build_prototyp_v2.py` – **Quelle der Wahrheit** für das 3D-Modell V2 (Parameter mit Status/Quelle am Anfang).
3. `gehaeuse/pruefberichte/pruefbericht_deckel_v2.txt` – letzter automatischer Prüfbericht V2.

## Was gebaut wird
Zweiteiliger 150×150-mm-Prototyp in PLA: Oberteil (Gridfinity-Raster 50 mm, 9 PN532-Taschen) auf zwei Wägezellen Adafruit 4541, Unterteil mit ESP32-C6, 2× SparkFun HX711, 2× TCA9548A und USB-C-Einbaubuchse (Delock 87824). Später werden mehrere Module zusammengesteckt.

## Ordner (seit 26.11. für ein gemeinsames Repository umgebaut, Überblick in `README.md`)
- `gehaeuse/` – unser Teil. Hier wird gearbeitet.
  - `skripte/` Build-Skripte (Modell, Behälter, Coupon), `modell/` FCStd, `pruefberichte/` Prüfberichte + `kabelwege_v2.json`, `druck/` das eine aktuelle Druckpaket (STLs + `DRUCKHINWEISE.txt`).
  - `fem/` FEM-Skripte, Ergebnisse in `fem/ergebnisse/` (Rohdaten-Unterordner nicht ins Repo).
  - `verdrahtung/` Lageplan, Pintabelle, Einzeladern-Ansicht (`kabelwege_einzeladern.py`). `ansichten/` Bilder. `render/` Blender (`render_produkt.py`, Farbe `hell`/`schwarz`, Eingabe-STLs in `eingabe_stl/`).
  - `archiv/` FreeCAD-Sicherungen, alte Skriptstände, `V1/` (inkl. alter Ansichten; Pfade in den V1-Skripten sind veraltet).
- `elektronik/`, `software/` – Teile der anderen Teams (noch leer, nur README). Nicht ändern.
- `doku/` – `statusberichte/`, `bericht/` (Vorlage, Entwurf, `erzeugung/bericht_bauen.py`), `bestellung/` (Stückliste mit Shop-Links).
- `referenz/` – nur lesen: `externe_modelle/` (Datenblätter, ESP32-DXF/PDF, Eagle HX711/TCA9548A, Wägezellen-PDF), `unterlagen/` (Delock-Zeichnung `87824_draw_2.pdf`, PN532-Foto `IMG_1762.pdf`), `handout_proto/` (fremder Referenzentwurf, 168 mm, 56-mm-Raster, nur Ideenquelle; per `.gitignore` nicht im Repo).
- `archiv/` (Roadmap 18.10., `hardware/` mit KiCad-Footprint) ist **veraltet, ignorieren**.
- Pfade in den Skripten: Projektwurzel aus `MATTE_PROJ`, sonst aktuelles Verzeichnis (wenn Projektwurzel), sonst fester Pfad dieses Macs. Headless-Aufrufe daher aus der Projektwurzel starten.

## Arbeitsregeln
- **Erst fragen, dann bauen:** Fehlen kritische Maße, kurz nachfragen. Darf danach mit markierten Platzhaltern weitergebaut werden.
- **Maße nur im Skript ändern**, in der Liste `PARAMS` (Name, Wert, Status, Quelle). Status: `bestaetigt`, `Norm`, `Annahme`, `PLATZHALTER`. Nie Werte im FreeCAD-Modell von Hand ändern, das Skript baut alles neu.
- **Nach jeder Änderung** das Skript laufen lassen und den Prüfbericht lesen: gültige Körper, keine Kollisionen, Spalte gleich Sollwerten. Nicht nur "lief ohne Fehler" melden.
- Nicht raten, wenn ein Maß aus einer Datei oder vom Nutzer kommen kann. Geschätzte Werte als `Annahme`/`PLATZHALTER` kennzeichnen.
- Alle Boards haben **angelötete Header-Pins, die bleiben**. Später werden Kabel an die Pins gelötet, es wird nichts ausgelötet. Rahmen und Taschen müssen die Pins freilassen. Einzige Ausnahme (Nutzer 27.11.): An Reader 22 und 23 wird die ungenutzte SPI-Leiste abgekniffen (`PN_SPI_CUT`).
- Konstruktion für **FDM-Druck in PLA**: Wand mindestens 1,2 mm, Löcher drucken ca. 0,1–0,2 mm kleiner, M3/M4 als Schneidschrauben direkt ins PLA, Passungen 0,3–0,5 mm. Überhänge vermeiden.
- Wägemechanik nicht durch Kraftnebenschlüsse verfälschen: Luft um die Zelle, Kabel mit Schlaufe, Überlast- und Kippanschläge mit Spalt.

## FreeCAD ausführen
FreeCAD läuft auf dem Mac des Nutzers und wird über die **MCP Bridge for FreeCAD** (`execute_python`) gesteuert. Ohne Einstellung "Unrestricted" fragt FreeCAD vor jedem Lauf nach Freigabe, der Job-Token läuft ab.

```python
exec(compile(open("/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/gehaeuse/skripte/build_prototyp_v2.py", encoding="utf-8").read(), "build_prototyp_v2.py", "exec"))
```

**V2 ist die Hauptversion** (Deckel-Variante: Träger + Gridfinity-Deckel): `gehaeuse/skripte/build_prototyp_v2.py` → `gehaeuse/modell/Prototyp_15x15_Deckel_V2.FCStd`, `gehaeuse/pruefberichte/pruefbericht_deckel_v2.txt`. TCA an der Platte, USB vorne, Power-Hub vorne rechts (seit 27.11., Wickelkammer entfallen). Details in `gehaeuse/UEBERGABE.md` Abschnitte 4b, 4e, 4f, 4g (Montagelöcher Hub/Lötverteiler). Das Skript löscht alle Objekte in seinem Dokument, baut neu auf, speichert die FCStd und schreibt den Prüfbericht. Ausgabepfade `outdir_modell`/`outdir_bericht` hängen an der Projektwurzel.

**V1** liegt in `gehaeuse/archiv/V1/` (`VARIANT = "einteilig"` oder `"deckel"`). Nur noch zum Nachschlagen, Pfade dort nicht nachgezogen.

Läuft Claude Code direkt auf dem Mac, geht es auch ohne Bridge: aus der Projektwurzel `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "import FreeCAD as App; exec(compile(open('gehaeuse/skripte/build_prototyp_v2.py', encoding='utf-8').read(), 'build_prototyp_v2.py', 'exec'))"` (getestet, ca. 2,5 min). Ohne GUI fehlen in der FCStd die Farben, für den Nutzer daher am Ende einmal über die Bridge bauen. Ansichten: über die Bridge per Screenshot; die alten matplotlib-Ansichten (`gehaeuse/archiv/V1/render_ansichten.py`) gelten nur für V1. Produktbilder: `Blender -b -P gehaeuse/render/render_produkt.py -- gehaeuse/render/eingabe_stl <ausgabe> [samples] [hell|schwarz]`.

## Offene Punkte (Kurzfassung, Details in `gehaeuse/UEBERGABE.md`)
1. PN532: In V2 umgedreht und nach Weg 3 eingebaut: von oben in eine durchgehende Tasche gelegt, liegt auf 4 Eckauflagen, Deckel-Druckplatte hält ihn, keine Reader-Rasthaken mehr. Reader-Modell mit echten Maßen (I²C- und SPI-Leiste, DIP-Schalter). Antenne 3,8 mm unter dem Behälterboden. Pinüberstand 1 mm bestätigt. SPI-Leiste an 22/23 abgekniffen (lag über dem Silikon der Zellen). Offen: Lesereichweite testen.
2. Kabelführung: Bänder in V2 unter der Platte, an den Zellen links/rechts vorbei. Stromkonzept der Elektronik (27.11.) eingebaut: Wickelkammer weg, Power-Hub vorne rechts mit JP_NFC im Bodenfenster, `NP_WIRES` = 2, Schlaufe 5 Adern. ESP32-Jumper unter der UART-Buchse (links), Band Daten 13+23 dahinter verlegt; Delock-Stecker in UART.
3. USB-C-Buchse vermessen (27.11., M3-Senkschrauben). Offen: Modulverbinder festlegen (`CONN_W`, `CONN_H`).
4. Testdruck-Coupon: `gehaeuse/skripte/build_coupon.py` (STLs `Coupon_*` in `gehaeuse/druck/`). Erste Runde gedruckt (26.11.). Messwerte Wägezelle (Silikon, Kabel) und Delock (M3-Senkschrauben) am 27.11. eingebaut, Zellen gedreht (`CELL_FLIP`, Pfeil nach oben). Kein Neudruck nötig. ESP32-Jumper (15,12 Gesamthöhe) eingebaut.
