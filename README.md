# GridScale – Die intelligente Wiegematte (SmartSystems2)

Modulare Wiegematte im Format 150 × 150 mm. Sie erkennt Gewürzbehälter per NFC (9 × PN532) und wiegt sie über zwei Wägezellen. Gesteuert wird sie von einem ESP32-C6.

## Ordner

| Ordner | Inhalt | Zuständig |
|---|---|---|
| `gehaeuse/` | Gehäuse und Konstruktion: parametrisches FreeCAD-Modell, Prüfberichte, Druckdateien, FEM, Verdrahtungsplan | Gehäuse |
| `elektronik/` | Schaltung, Pinbelegung, Messungen | Elektronik |
| `software/` | Firmware ESP32-C6, Entwicklungsumgebung | Software |
| `doku/` | Statusberichte, Projektbericht, Bestellung/Stückliste | alle |
| `referenz/` | Datenblätter, Herstellerzeichnungen, Fremdmodelle (nur lesen) | alle |
| `archiv/` | veraltete erste Ideen (Roadmap 18.10.) | – |

### `gehaeuse/` im Detail

```
gehaeuse/
  UEBERGABE.md      Stand, Konstruktionsentscheidungen, offene Punkte
  skripte/          build_prototyp_v2.py (Quelle der Wahrheit), build_behaelter.py, build_coupon.py
  modell/           FreeCAD-Dateien (werden von den Skripten erzeugt)
  pruefberichte/    automatische Prüfberichte, kabelwege_v2.json
  druck/            aktuelles Druckpaket: STLs + DRUCKHINWEISE.txt
  fem/              FEM-Skripte, Ergebnisse in fem/ergebnisse/
  verdrahtung/      Lageplan, Pintabelle, Einzeladern-Ansicht
  ansichten/        Bilder des Modells
  render/           Blender-Produktbilder
  archiv/           alte Stände (V1, Sicherungen)
```

## Gehäuse bauen

Alle Maße stehen in `gehaeuse/skripte/build_prototyp_v2.py` in der Liste `PARAMS`, jeweils mit Status und Quelle. Das Modell wird nie von Hand geändert: Das Skript baut es jedes Mal komplett neu und schreibt dabei einen Prüfbericht (gültige Körper, Kollisionen, Spaltmaße, Bewegungscheck).

Getestet mit FreeCAD 1.1.4. Die Befehle laufen aus der Projektwurzel:

```bash
FC=/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
$FC -c "import FreeCAD as App; exec(compile(open('gehaeuse/skripte/build_prototyp_v2.py', encoding='utf-8').read(), 'build_prototyp_v2.py', 'exec'))"
$FC -c "exec(open('gehaeuse/skripte/build_coupon.py').read())"
$FC -c "exec(open('gehaeuse/verdrahtung/kabelwege_einzeladern.py').read())"
```

- **Projektwurzel:** Die Skripte finden sie über die Umgebungsvariable `MATTE_PROJ`. Ist sie nicht gesetzt, nehmen sie das aktuelle Verzeichnis, sonst einen festen Standardpfad.
- **Farben:** Headless gebaute FCStd-Dateien haben keine Farben. Mit Farben wird in der FreeCAD-Oberfläche gebaut.
- **STLs:** `gehaeuse/skripte/export_stl.py` exportiert Unterteil, Träger und Deckel in Druckorientierung nach `gehaeuse/druck/`, die Coupons erzeugt `build_coupon.py`.
