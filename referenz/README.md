# Referenzunterlagen

Die Datenblätter und Herstellerzeichnungen liegen nur lokal und sind nicht im Repository, weil die Rechte bei den Herstellern liegen. Wer die Skripte nachvollziehen will, lädt sie beim Hersteller herunter und legt sie so ab:

| Lokaler Pfad | Inhalt | Quelle |
|---|---|---|
| `externe_modelle/4541.pdf` | Maßzeichnung Wägezelle 5 kg (Adafruit 4541) | Adafruit, Produkt 4541 |
| `externe_modelle/esp32-c6-devkitc-1-dimensions_v1.2.pdf` / `.dxf` | Maße ESP32-C6-DevKitC-1 | Espressif, Dokumentation ESP32-C6-DevKitC-1 |
| `externe_modelle/Adafruit_TCA9548A/` | Eagle-Dateien TCA9548A-Breakout | Adafruit, GitHub-Repository des TCA9548A-Breakouts |
| `externe_modelle/SparkFun_HX711/` | Eagle-Dateien HX711-Breakout | SparkFun, GitHub-Repository „HX711 Load Cell Amplifier“ |
| `unterlagen/87824_draw_2.pdf` | Zeichnung USB-C-Einbaubuchse Delock 87824 | Delock, Produktseite 87824 |
| `unterlagen/IMG_1762.pdf` | Foto PN532-Modul (eigene Aufnahme) | Team |

Die Maße, die daraus ins Modell übernommen wurden, stehen mit Quelle in `gehaeuse/skripte/build_prototyp_v2.py` (Liste `PARAMS`).

`handout_proto/` (fremder Referenzentwurf) ist ebenfalls nur lokal.
