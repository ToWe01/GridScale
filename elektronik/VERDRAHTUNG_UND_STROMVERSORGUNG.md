# GridScale V2 – Stromversorgung, Verdrahtung & Pinbelegung (Elektronik)

**Stand:** 27.11.2026 | **Bezug:** Gehäuse-Prototyp V2 (`gehaeuse/UEBERGABE.md`, `gehaeuse/verdrahtung/`)  
**Interaktiver Schaltplan & durchsichtige 150×150-mm-Lageübersicht:** [schaltplan_gridscale.html](schaltplan_gridscale.html) *(im Browser öffnen)*

---

## 1. Überblick & Architektur (1-Kabel-USB-C-Konzept)

Die Elektronik von **GridScale** (`150 × 150 mm`) verbindet einen **ESP32-C6-DevKitC-1**, **2× SparkFun HX711** mit **2× 5-kg-Wägezellen (Adafruit 4541)**, **2× Adafruit TCA9548A** I²C-Multiplexern und **9× PN532 V3** NFC-Readern.

Zentrale Designentscheidungen:
- **1-Kabel-Außenanschluss über gekürzte Delock 87824:** Das 1-m-Kabel der USB-C-Einbaubuchse wird in der Mitte auf **ca. 20–25 cm** gekürzt (Außenbuchse und ESP32-USB-C-Stecker bleiben erhalten). `D+`/`D−` werden direkt wieder verlötet, sodass über die **gleiche äußere Buchse** sowohl versorgt (`5 V / 3 A`) als auch geflasht (Laptop-USB) werden kann.
- **Saubere Trennung von `5V_NFC` und `3,3V`:** Die `9× PN532` werden mit **5 V (`5V_NFC`)** versorgt und nutzen ihre eigenen Onboard-3,3V-LDOs. Der **ESP32-C6**, die **2× TCA9548A** und die **2× HX711** laufen stabil auf **3,3 V** – entkoppelt von den 13,56-MHz-RF-Stromspitzen der Reader.
- **USB-Flash-Schutz ohne Schiebeschalter (`JP_NFC`):** Ein einfacher **2-Pin-Jumper `JP_NFC`** im Unterteil-Hub trennt `5V_NFC` beim Flashen am Laptop vollständig ab.
- **Ersatz-ADC für Waage:** Der ursprünglich vorgesehene NAU7802 (`0x2A`) ist hardwareseitig defekt (Kurzschluss `SDA → 3,3 V`) und wird durch **2× SparkFun HX711** (`SEN-13879`) ersetzt.

---

## 2. Stromversorgung & Leistungsbudget

### 2.1 Strombedarf
| Verbraucher | Einzelstrom | Gesamt (Peak) | Betrieb (sequentielles RF-Aus) |
| :--- | :--- | :--- | :--- |
| **9× PN532 V3 (an `5V_NFC`)** | ~100–150 mA aktiv / ~15–25 mA Idle | **~1,1 – 1,35 A** *(Boot-Peak vor RF-Abschaltung)* | **~200 – 300 mA** *(max. 1 Reader sendet)* |
| **ESP32-C6-DevKitC-1** | ~80 mA Idle / bis ~350 mA Wi-Fi-Peak | **~350 mA** | **~100 – 250 mA** |
| **2× TCA9548A + 2× HX711 + 2× Zellen** | ~2 mA + ~20 mA | **~25 mA** | **~25 mA** |
| **Summe Gesamtsystem** | – | **~1,5 – 1,8 A** | **~0,35 – 0,6 A** |

> **Wichtig:** Der `3,3V`-Onboard-Regler des ESP32-C6 dürfte keinesfalls alle 9 PN532 versorgen (sofortiger Brownout). Über `5V_NFC` direkt ab dem Netzteil bleibt der ESP32-3,3V-Regler auf **~25 mA** begrenzt.

### 2.2 Netzteil-Spezifikation
- **Empfohlenes Netzteil:** Stabilisiertes **USB-C-Netzteil `5 V / 3 A` (15 W)**, z. B. ein klassisches **Raspberry-Pi-4-USB-C-Netzteil (`5,1 V / 3 A`)**.
- *Hinweis:* Kein reines USB-PD-Ladegerät verwenden, das ohne PD-Aushandlung keine `5 V` ausgibt.

### 2.3 Betriebsmodi über Jumper `JP_NFC`
Der Jumper `JP_NFC` sitzt im Unterteil-Hub zwischen **Streifen 1 (`VBUS_IN`)** und **Streifen 2 (`5V_NFC`)**:

| Modus | Kabel außen an Delock | Jumper `JP_NFC` | Was ist versorgt? |
| :--- | :--- | :--- | :--- |
| **Normalbetrieb** | `5 V / 3 A` Netzteil | **gesteckt** | ESP32-C6 + Waage + alle 9× PN532 |
| **Flashen / Serial-Log** | Laptop USB | **abgezogen** | Nur ESP32-C6 + 2× HX711 + 2× TCA9548A (~150 mA, sicher für Laptop-USB!) |
| **Live-Debug mit 9× PN532** | Laptop USB | **abgezogen** | Laptop versorgt ESP32 (`D+/D−` + `3V3`), externes 5V-Netzteil direkt an `5V_NFC` (Streifen 2) + `GND` (Streifen 3) klemmen |

> **Optionaler Puffer-Elko:** Auf Streifen 2 (`5V_NFC`) und Streifen 3 (`GND`) können je 2 Löcher für einen **Elko `220–470 µF / ≥ 10 V`** (`+` an `5V_NFC`, `−` an `GND`) freigehalten werden. Der Aufbau funktioniert zunächst auch ohne Elko; sollte es beim Schalten der RF-Felder zu Brownouts kommen, einfach nachlöten.

---

## 3. Pinbelegung & Schnittstellen

### 3.1 ESP32-C6-DevKitC-1 (Unterteil, fest)
I²C-Pins immer explizit übergeben (`Wire.begin(4, 5, 100000UL); Wire.setTimeOut(50);` **genau einmal in `setup()`**). Keine Strapping-Pins (`GPIO 8, 9, 15`) oder USB-JTAG-Pins (`GPIO 12, 13`) verwenden.

| Signal | ESP32-C6 Pin | Ziel |
| :--- | :--- | :--- |
| **USB `VBUS`, `D+`, `D−`, `GND`** | USB-C-Buchse am DevKit | Gekürztes Delock-Kabel (`VBUS`/`GND` über Unterteil-Hub) |
| **`3V3` Ausgang** | `3V3` | Unterteil-Hub Streifen 4 → `2× HX711` + Schlaufe (`2× TCA9548A`) |
| **`GND`** | `GND` | Unterteil-Hub Streifen 3 (Sternpunkt) |
| **I²C `SDA` / `SCL`** | **`GPIO 4`** / **`GPIO 5`** | Unterteil-Hub Streifen 5 & 6 → Schlaufe → Lötverteiler → `TCA_A` / `TCA_B` |
| **Waage 1 (`HX711_A`)** | **`GPIO 2` (`DAT`)** / **`GPIO 3` (`CLK`)** | `SparkFun HX711_A` (Wägezelle 1) |
| **Waage 2 (`HX711_B`)** | **`GPIO 6` (`DAT`)** / **`GPIO 7` (`CLK`)** | `SparkFun HX711_B` (Wägezelle 2) |

### 3.2 Waage: 2× SparkFun HX711 + 2× Adafruit 4541 (Unterteil, fest)
- Auf beiden HX711-Platinen **`VCC` und `VDD` brücken** und an **`3,3 V`** (Hub Streifen 4) anschließen, damit `DAT`/`CLK` mit 3,3-V-Pegel arbeiten.
- Wägezellen-Anschluss an `HX711_A` (Zelle 1) und `HX711_B` (Zelle 2) laut SparkFun-Aufdruck:
  - `ROT` → `E+` | `SCHWARZ` → `E−` | `WEISS` → `A−` | `GRÜN` → `A+`
- Zellenkabel jeweils am **Festende** in einer lockeren Schlaufe führen (kein Kraftnebenschluss).

### 3.3 Unterteil-Power-Hub (`6 × 8` Streifenraster, `2,54 mm`)
Durchgehendes Streifenraster ohne aufgetrennte Leiterbahnen (Einbauort in der frei gewordenen rechten Kammer `x ≈ 118–142 mm`, Unterseite mit Schaumklebeband isoliert):

| Streifen | Netz | Belegung |
| :---: | :--- | :--- |
| **1** | **`VBUS_IN`** | Delock `+5 V` → ESP32 `USB VBUS` + **`JP_NFC` Pin 1** |
| **2** | **`5V_NFC`** | **`JP_NFC` Pin 2** → Schlaufe hoch (Pin 1) *(+ 2 Löcher opt. Elko `+`)* |
| **3** | **`GND`** | Delock `GND` + ESP32 `GND` + `HX711_A` + `HX711_B` + Schlaufe hoch *(+ opt. Elko `−`)* |
| **4** | **`3,3V`** | ESP32 `3V3` + `HX711_A` + `HX711_B` + Schlaufe hoch |
| **5** | **`SDA`** | ESP32 `GPIO 4` + Schlaufe hoch |
| **6** | **`SCL`** | ESP32 `GPIO 5` + Schlaufe hoch |

### 3.4 Lötverteiler am Träger (`6 × 8` Streifenraster, beweglich)
Hängt unter dem Träger links (`x = 6,57..29,43 mm`, `y = 42,38..57,62 mm`):

| Streifen | Netz | Belegung (von 8 Löchern) |
| :---: | :--- | :--- |
| **1** | **`5V_NFC`** | Zuleitung (Schlaufe), Strang Reihe 1 (`11`), Strang Reihe 2 (`12`), Strang Reihe 3 (`13`) *(4/8)* |
| **2** | **`GND`** | Zuleitung (Schlaufe), `TCA_A`, Strang Reihe 1, Strang Reihe 2, Strang Reihe 3 *(5/8)* |
| **3** | **`3,3V`** | Zuleitung (Schlaufe), `TCA_A VIN` *(2/8)* |
| **4** | **`SDA`** | Zuleitung (Schlaufe), `TCA_A SDA` *(2/8)* |
| **5** | **`SCL`** | Zuleitung (Schlaufe), `TCA_A SCL` *(2/8)* |
| **6** | **Reserve** | Frei (z. B. optionaler `100 nF`-Kerko oder `TCA_RST`) |

### 3.5 TCA9548A-Multiplexer & 9× PN532 V3 (`0x24`, Träger)
- **`TCA_A` (Adresse `0x70`, `A0/A1/A2` offen, um 180° gedreht eingebaut: `JP1` links, `JP3` rechts):**
  - `JP3` (rechts): Bus vom Lötverteiler + Weiterleitung zu `TCA_B` (`VIN=3,3V, GND, SDA, SCL`) + **`CH0` = Reader `22`** *(CH1 frei)*
  - `JP1` (links): **`CH2` = Reader `11`**, **`CH3` = Reader `21`**, **`CH4` = Reader `12`**, **`CH5` = Reader `13`**, **`CH6` = Reader `23`** *(CH7 frei)*
- **`TCA_B` (Adresse `0x71`, Lötbrücke `A0 ↔ VIN` setzen!):**
  - `JP3` (links): Bus von `TCA_A` *(CH0, CH1 frei)*
  - `JP1` (rechts): **`CH2` = Reader `31`**, **`CH3` = Reader `32`**, **`CH4` = Reader `33`** *(CH5–CH7 frei)*
- **9× PN532 V3 (`0x24`):**
  - DIP-Schalter vor Einbau auf I²C stellen (`SEL0 = ON`, `SEL1 = OFF`).
  - Bestätigte 4-Pin-Leiste (Draufsicht auf Bestückungsseite): **`SCL | SDA | VCC | GND`**.
  - **Wichtig beim Löten:** Im Träger sitzen die Reader über Kopf; **Spalte 2 (`21, 22, 23`) und Spalte 3 (`31, 32, 33`) sind gegenüber Spalte 1 (`11, 12, 13`) um 180° gedreht**. Pinaufdruck beim Löten immer direkt am Board ablesen!
  - Reihenketten `5V_NFC + GND`: Reihe 1 (`11→21→31`), Reihe 2 (`12→22→32`), Reihe 3 (`13→23→33`).

---

## 4. Kabelführung & Rückmeldung ans Gehäuse-Team

Folgende bisher offene Punkte aus `gehaeuse/UEBERGABE.md` und `gehaeuse/verdrahtung/verdrahtung_v2.yml` sind damit **elektronikseitig festgelegt**:

1. **`NP_WIRES` = 2 Adern (`5V_NFC`, `GND`)** pro Reader-Versorgungsstrang (statt 3 Platzhalter-Adern). Das reduziert das Bündel von Reihe 3 über dem ESP32-Stecker.
2. **`W_SCHLAUFE` = 5 Adern (`5V_NFC`, `3,3V`, `GND`, `SDA`, `SCL`)** als sehr weiche, flache Silikon-S-Schlaufe über den Wägespalt (kein Kraftnebenschluss).
3. **Delock 87824 gekürzt (~25 cm):** Die rechte Wickelkammer (`REF_USB_Kabelwickel`) wird **nicht mehr benötigt** und kann im nächsten CAD-Stand entfallen oder als Einbauraum (`x = 118–142 mm`) für das `6×8`-Unterteil-Raster genutzt werden.
4. **`TCA_A`-Drehung & Kanalzuordnung** (Stand 26.11.: `TCA_A` mit `CH0, CH2..6`; `TCA_B` mit `CH2..4`) ist bestätigt.
5. **ESP32-Pins (Platzhalter in `verdrahtung_v2.yml`):** `SDA = GPIO 4`, `SCL = GPIO 5`, `HXA_DAT = GPIO 2`, `HXA_CLK = GPIO 3`, `HXB_DAT = GPIO 6`, `HXB_CLK = GPIO 7`.

---

## 5. Materialliste (inkl. Leitungsquerschnitte)

### Vorhandene Hauptkomponenten
- `1×` ESP32-C6-DevKitC-1, `2×` SparkFun HX711, `2×` Wägezelle Adafruit 4541 (5 kg), `2×` Adafruit TCA9548A, `9×` Funduino/Elechouse PN532 V3, `1×` Delock 87824 USB-C-Einbaubuchse

### Leitungen & Querschnitte
| Einsatzbereich | Typ & Querschnitt | Bedarf | Hinweise |
| :--- | :--- | :--- | :--- |
| **Feste & Träger-Verdrahtung** | Litze **`LiYv 0,25 mm²`** *(oder `AWG 24`)* | **ca. 6–7 m gesamt** *(~1–1,5 m je Farbe)* | Passt zu den CAD-Bündeln; Spannungsabfall bei 150 mA < 5 mV |
| **Wägespalt-Schlaufe (5 Adern)** | Sehr weiche **Silikonlitze `0,14–0,25 mm²`** *(`AWG 26–24`)* oder **5er-Dupont-Flachband** | **5× ca. 15 cm** *(~0,75 m)* | Möglichst flexibel als lockeren S-Bogen legen |

### Laborbedarf & Netzteil
- `2×` Streifenrasterplatine `2,54 mm`, zugeschnitten auf **`6 Streifen × 8 Löcher`** (≈ `23 × 16 mm`)
- `1×` 2-polige Stiftleiste `2,54 mm` + `1×` Jumper-Kappe *(für `JP_NFC`)*
- *(Optional für steckbare Schlaufe)* `1×` 5-polige Stiftleiste `2,54 mm` (abgewinkelt) + 5er-Dupont-Buchsenblock
- Schrumpfschlauch (`Ø 1,5–2 mm` und `Ø 6 mm`) oder Isolierband *(für gekürztes `D+/D−`-Stück)*
- Doppelseitiges Schaumklebeband *(Isolation & Montage Unterteil-Hub)*, Lötzinn, kleine Kabelbinder
- *(Optional)* `1–2×` Elko **`220–470 µF / ≥ 10 V`**
- `1×` **USB-C-Netzteil `5 V / 3 A` (stabilisiert)**

---

## 6. Inbetriebnahme- & Sicherheits-Checkliste (vor dem ersten Einschalten)

1. **Einmaliger Pegeltest am einzelnen PN532:** 1× PN532 V3 (DIP auf I²C: `SEL0=ON, SEL1=OFF`) **allein** an `5 V` + `GND` anschließen (ohne ESP32/TCA) und mit dem Multimeter `SDA → GND` und `SCL → GND` messen → muss **ca. `3,3 V`** ergeben.
2. **Lötbrücken setzen & prüfen:** `VCC ↔ VDD` an beiden HX711; `A0 ↔ VIN` an `TCA_B` (`0x71`).
3. **Durchgangs- und Kurzschlussprüfung:**
   - `5V_NFC ↔ GND` und `3,3V ↔ GND` müssen hochohmig sein (kein Kurzschluss).
   - Bei **abgezogenem `JP_NFC`** darf keine Verbindung zwischen `VBUS_IN` (Streifen 1) und `5V_NFC` (Streifen 2) bestehen.
4. **Schrittweiser Hardware-Test (`JP_NFC` beim Flashen abziehen!):**
   - Flash + Test ESP32 + `TCA_A` (`0x70`) + `TCA_B` (`0x71`).
   - Test `1× PN532` an `TCA_A`, danach alle `9× PN532` mit `JP_NFC` gesteckt am `5 V / 3 A`-Netzteil (sequentielles RF-Abschalten in Firmware aktiv).
   - Test & Kalibrierung der `2× HX711` + `2× 5-kg-Wägezellen`.
