# Gehäuse (CAD) – Regeln für Claude

Der Nutzer ist hier für **Gehäuse/Konstruktion** zuständig, nicht für Elektronik oder Firmware.

## Zuerst lesen
1. `gehaeuse/STAND.md` – aktueller Stand, offene Punkte, nächster Schritt (eine Seite).
2. `gehaeuse/skripte/params.py` – alle Maße mit Status und Quelle.

Das Build-Skript `gehaeuse/skripte/build_prototyp_v2.py` (Geometrie und Prüfungen, ca. 1000 Zeilen) **nicht ganz lesen**, sondern gezielt per `grep` nach Parametername oder Bauteil. Begründungen früherer Entscheidungen: `gehaeuse/entscheidungen.md`. Alte Übergabe mit allen Details: `gehaeuse/archiv/UEBERGABE.md` (nur bei Bedarf).

## Was gebaut wird
Zweiteiliger 150×150-mm-Prototyp in PLA: Oberteil (Träger + Gridfinity-Deckel, 50-mm-Raster, 9 PN532-Taschen) auf zwei Wägezellen Adafruit 4541, Unterteil mit ESP32-C6, 2× SparkFun HX711, Power-Hub und USB-C-Einbaubuchse (Delock 87824); 2× TCA9548A und Lötverteiler hängen unter dem Träger. Später werden mehrere Module zusammengesteckt.

## Ordner
`skripte/` Build-Skripte (Modell, Behälter, Coupon, STL-Export), `modell/` FCStd (nur vom Skript erzeugt), `pruefberichte/` Prüfberichte + `kabelwege_v2.json`, `druck/` aktuelles Druckpaket, `fem/` FEM-Skripte (Rohdaten in `fem/ergebnisse/*/` nicht lesen), `verdrahtung/` Lageplan, Pintabelle, Einzeladern-Ansicht, `ansichten/` Bilder, `render/` Blender, `archiv/` alte Stände inkl. `V1/` (nicht lesen).

## Arbeitsregeln
- **Erst fragen, dann bauen:** Fehlen kritische Maße, kurz nachfragen. Danach darf mit markierten Platzhaltern weitergebaut werden.
- **Maße nur in `params.py` ändern** (Name, Wert, Status, Quelle). Status: `bestaetigt`, `Norm`, `Annahme`, `PLATZHALTER`. Quelle nie leer. Nie Werte im FreeCAD-Modell von Hand ändern, das Skript baut alles neu.
- **Nach jeder Änderung bauen** (`/bauen`) und den Prüfbericht lesen: gültige Körper, keine Kollisionen, Spalte gleich Sollwerten. Nicht nur „lief ohne Fehler“ melden.
- Nicht raten, wenn ein Maß aus einer Datei oder vom Nutzer kommen kann. Geschätzte Werte als `Annahme`/`PLATZHALTER` kennzeichnen.
- Alle Boards haben **angelötete Header-Pins, die bleiben**. Kabel werden an die Pins gelötet, nichts wird ausgelötet. Rahmen und Taschen lassen die Pins frei. Einzige Ausnahme (Nutzer 27.11.): an Reader 22 und 23 wird die ungenutzte SPI-Leiste abgekniffen (`PN_SPI_CUT`).
- **FDM-Druck in PLA:** Wand mindestens 1,2 mm, Löcher drucken ca. 0,1–0,2 mm kleiner, M3/M4 als Schneidschrauben direkt ins PLA, Passungen 0,3–0,5 mm, Überhänge vermeiden.
- **Wägemechanik** nicht durch Kraftnebenschlüsse verfälschen: Luft um die Zelle, Kabel mit Schlaufe, Überlast- und Kippanschläge mit Spalt.
- Neue Entscheidungen in `entscheidungen.md` anhängen, `STAND.md` überschreiben (offene Punkte nur dort).

## FreeCAD ausführen
**Headless** (aus der Projektwurzel, ca. 2,5 min, ohne Farben in der FCStd):
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "import FreeCAD as App; exec(compile(open('gehaeuse/skripte/build_prototyp_v2.py', encoding='utf-8').read(), 'build_prototyp_v2.py', 'exec'))"
```
**Über die MCP Bridge for FreeCAD** (`execute_python`, mit Farben; für den Nutzer am Ende einmal so bauen). Ohne Einstellung „Unrestricted“ fragt FreeCAD vor jedem Lauf nach Freigabe, der Job-Token läuft ab.
```python
exec(compile(open("/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/gehaeuse/skripte/build_prototyp_v2.py", encoding="utf-8").read(), "build_prototyp_v2.py", "exec"))
```
- Projektwurzel in den Skripten: `MATTE_PROJ`, sonst aktuelles Verzeichnis (wenn Projektwurzel), sonst fester Pfad dieses Macs. `params.py` wird über diese Wurzel geladen, das Skript läuft deshalb auch per `exec` ohne `__file__`.
- Das Skript löscht alle Objekte in seinem Dokument, baut neu auf, speichert `modell/Prototyp_15x15_Deckel_V2.FCStd` und schreibt `pruefberichte/pruefbericht_deckel_v2.txt`.
- Ansichten: über die Bridge per Screenshot. Produktbilder: `Blender -b -P gehaeuse/render/render_produkt.py -- gehaeuse/render/eingabe_stl <ausgabe> [samples] [hell|schwarz]`.
- V1 liegt in `gehaeuse/archiv/V1/` (Pfade dort veraltet), nur zum Nachschlagen.
