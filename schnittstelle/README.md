# Schnittstelle Gehäuse ↔ Elektronik

`gehaeuse_elektronik.json` beschreibt, wo im Modul was sitzt und wie die Leitungen laufen:
- Lage, Drehung, Montage („unten“ = fest im Unterteil, „platte“ = unter dem Träger, wird mitgewogen)
- Platinenhülle und Bauraum mit Stiftleisten
- Richtung der Pinleisten
- I²C-/SPI-Kante der Reader
- Wägezellen und Steckverbinder
- Leitungen mit Aderzahl und Modelllänge
- Bandverläufe in 2D

Koordinaten in mm, Ursprung vordere linke untere Ecke, USB-C vorne.

## Zuständigkeit
| Was | Wer | Quelle |
|---|---|---|
| Lage, Ausrichtung, Bauhöhen, Kabelwege und -längen, Lage der Steckverbinder | Gehäuse | `gehaeuse/skripte/params.py` + `build_prototyp_v2.py` |
| Pinbelegung, Netze, GPIOs, I²C-Adressen, TCA-Kanäle, Stromversorgung | Elektronik | `elektronik/VERDRAHTUNG_UND_STROMVERSORGUNG.md` |

## Regeln
- Die JSON-Datei **nicht von Hand ändern**. Sie wird bei jedem Build des Gehäusemodells neu geschrieben. Ihre Quellen bleiben in `gehaeuse/`, dazu gehören die Pintabelle und der Lageplan in `gehaeuse/verdrahtung/` sowie `gehaeuse/pruefberichte/kabelwege_v2.json`.
- Braucht die Elektronik eine andere Lage oder einen anderen Kabelweg, meldet sie das dem Gehäuse-Team. Ändert das Gehäuse etwas, das die Pinbelegung betrifft, meldet es das der Elektronik.
- Die Leitungen sind Platzhalter-Bänder. Die Längen enthalten keine Steigleitung (ca. 2 × 3 mm) und keine Zugabe. Die Zellkabel von der Wägezelle zum HX711 sind nicht modelliert.
- Geprüft wird die Schnittstelle vom Agenten `gehaeuse-pruefer`: Jede Leitung braucht einen Kabelweg, und über jeder Pinleiste muss genug Freiraum sein. Das Elektronik-Team kann zusätzlich die Vorlage `doku/vorlagen/agent_elektronik-pinbelegung.md` nutzen.
