# Elektronik

Platz für das Elektronik-Team: Schaltplan, Pinbelegung (ESP32-C6, TCA9548A `0x70`/`0x71`, PN532 `0x24`, AD-Wandler der Wägezellen), Versorgungskonzept, Messungen.

## Dokumente in diesem Ordner
- **[VERDRAHTUNG_UND_STROMVERSORGUNG.md](VERDRAHTUNG_UND_STROMVERSORGUNG.md)** – Komplette Dokumentation (1-Kabel-USB-C-Konzept, `JP_NFC`-Jumper, Pinbelegung, Materialliste inkl. Querschnitten, Sicherheits-Checkliste).
- **[schaltplan_gridscale.html](schaltplan_gridscale.html)** – Interaktiver Pin-zu-Pin-Schaltplan & durchsichtige Oben/Unten-Überlagerung im 150×150-mm-Maßstab (im Browser öffnen).

## Schnittstellen & bestätigte Rückmeldungen an das Gehäuse-Team
- Lage der Boards und Kabelwege aus dem Modell: `../gehaeuse/verdrahtung/` (Lageplan, Pintabelle) und `../gehaeuse/ansichten/kabelwege_einzeladern.png`.
- **Bestätigte Festlegungen (Stand 27.11.2026):**
  - `TCA9548A`-Kanalbelegung & `TCA_A`-Drehung (Stand 26.11.): `TCA_A (0x70)` auf `CH0` (22) und `CH2..CH6` (`11, 21, 12, 13, 23`); `TCA_B (0x71, A0 ↔ VIN)` auf `CH2..CH4` (`31, 32, 33`).
  - `NP_WIRES = 2` Adern (`5V_NFC`, `GND`) pro Reader-Strang; `W_SCHLAUFE = 5` Adern (`5V_NFC`, `3,3V`, `GND`, `SDA`, `SCL`) als weiche Silikon-S-Schlaufe über den Wägespalt.
  - Delock 87824 wird in der Mitte auf ~25 cm gekürzt (`D+/D−` + `VBUS` weiter an ESP32) → rechte Wickelkammer entfällt und nimmt stattdessen den `6×8`-Unterteil-Power-Hub (`x ≈ 118–142 mm`) mit `JP_NFC` auf.
  - ESP32-C6-Pins: `SDA = GPIO 4`, `SCL = GPIO 5`, `HXA_DAT = GPIO 2`, `HXA_CLK = GPIO 3`, `HXB_DAT = GPIO 6`, `HXB_CLK = GPIO 7`.
  - PN532 I²C-Leiste (Draufsicht Bestückungsseite): `SCL | SDA | VCC | GND`; Spalte 2 & 3 liegen im Träger gegenüber Spalte 1 um 180° gedreht.
