# GridScale – Die intelligente Wiegematte (SmartSystems2)

Antworte auf Deutsch.

Modulare Wiegematte 150 × 150 mm: 9 × PN532 (NFC) erkennen Gewürzbehälter, zwei Wägezellen wiegen, ein ESP32-C6 steuert. Gemeinsames Repository von drei Teams. Überblick in `README.md`.

## Ordner und Zuständigkeit
| Ordner | Inhalt | Team |
|---|---|---|
| `gehaeuse/` | FreeCAD-Modell, Prüfberichte, Druckdateien, FEM, Verdrahtungsplan. Eigene Regeln in `gehaeuse/CLAUDE.md` | Gehäuse |
| `elektronik/` | Schaltung, Pinbelegung, Stromversorgung | Elektronik |
| `software/` | Firmware ESP32-C6 | Software |
| `doku/` | Statusberichte, Projektbericht | alle |
| `referenz/` | Datenblätter, Herstellerzeichnungen, Fremdmodelle | alle, **nur lesen** |
| `archiv/` | veraltete erste Ideen (Roadmap 18.10.) | ignorieren |

- Ordner eines anderen Teams nur ändern, wenn dieses Team es ausdrücklich will. Fragen an ein anderes Team als offene Frage notieren, nicht selbst entscheiden.
- Nicht ins Repo (stehen in `.gitignore`): `referenz/handout_proto/`, `referenz/externe_modelle/`, `referenz/unterlagen/`, `doku/bestellung/`, FEM-Rohdaten.

## Git
- Nach jedem abgeschlossenen Arbeitsschritt committen, mit aussagekräftiger Nachricht. Nur eigene Dateien committen.
- **Keine manuellen Archivkopien** wie `skript_vor_..._datum.py`. Alte Stände holt man aus der Git-Historie.
- Pushen nur auf ausdrücklichen Wunsch.
- In Commits die eigene noreply-Adresse verwenden, keine privaten Mailadressen.
- Löschen mit `rm` nur nach Rückfrage und nie mit Wildcards.
