# Hardware & PCB Design Guide: 13.56 MHz Custom RFID Grid & Scale

Dieses Dokument enthält die vollständigen Spezifikationen, Berechnungen und Schaltpläne für das **eigene Leiterplattendesign (Full Custom PCB)** der Smart Kitchen Mat.

---

## 1. Modulare PCB-Architektur (4 Quadranten à 150 × 150 mm)

Um Fertigungskosten bei Herstellern wie **JLCPCB**, **AISLER** oder **PCBWay** drastisch zu senken, wird das System aus **4 identischen Quadranten-Platinen** aufgebaut:

* **Platinengröße:** $150 \times 150\text{ mm}$ (2 Lagen, Standard FR4, 1,6 mm Dicke, 1 oz Kupfer = $35\ \mu\text{m}$).
* **Raster pro Board:** $3 \times 3 = 9$ Antennen im 50-mm-Raster.
* **Gesamtsystem:** 4 Boards nebeneinander gelegt ergeben die $300 \times 300\text{ mm}$ Fläche mit 36 Plätzen.
* **Verbindung:** Randkontakte (Castellated Holes oder 2.54 mm Stiftleisten) schleifen `3.3V`, `GND`, `SCK`, `MOSI`, `MISO` und die Schieberegister-Kaskade von Board zu Board durch.

---

## 2. Antennen-Spezifikation & Footprint

Die Antenne wurde exakt auf die Resonanzfrequenz von **13,56 MHz (ISO 14443-A / Mifare / NTAG)** ausgelegt:

| Parameter | Wert | Erläuterung |
| :--- | :--- | :--- |
| **Geometrie** | Planare rechteckige Spirale | $40{,}0 \times 40{,}0\text{ mm}$ Außenmaß (5 mm Randabstand im 50 mm Grid) |
| **Windungszahl ($N$)** | **3 Windungen** | Optimaler Kompromiss aus Induktivität und ohmschem Widerstand |
| **Leiterbahnbreite ($w$)** | **0,60 mm** | Geringer DC-Widerstand ($R_{\text{DC}} \approx 0{,}8\ \Omega$) |
| **Leiterbahnabstand ($s$)** | **0,50 mm** | Standard-Fertigungstoleranz bei allen PCB-Pools |
| **Lagenaufbau** | Top Layer (`F.Cu`) | Spirale auf Top-Layer; Rückführung des inneren Endes auf Bottom (`B.Cu`) via 0,4 mm Vias |
| **Berechnete Induktivität ($L_{\text{ant}}$)** | $\mathbf{1{,}35\ \mu\text{H}}$ | Gemessen / berechnet nach modifizierter Grover/Harold-Formel |

### KiCad-Footprint:
Die fertige Footprint-Datei liegt im Repository unter:  
👉 [`hardware/kicad/RFID_Antenna_40x40_3T_13.56MHz.kicad_mod`](file:///Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/hardware/kicad/RFID_Antenna_40x40_3T_13.56MHz.kicad_mod)  
Das Generator-Skript:  
👉 [`hardware/kicad/generate_antenna.py`](file:///Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/hardware/kicad/generate_antenna.py)

---

## 3. Schaltung des MFRC522 & Anpassnetzwerks (Matching Circuit)

Jede Antenne wird von einem eigenen **MFRC522-IC** (TSSOP-32) angesteuert. Das verhindert Hochfrequenz-Umschaltverluste.

### Schaltplan-Auszug pro Antennen-Knoten:

```
                      EMC-Filter           Matching-Netzwerk
                     ┌─── L0 (560nH) ───┬─── C1 (22pF) ───┐
TX1 (Pin 9)  ───────┤                  │                 ├─── Antenne Pad 1
                     └─── C0 (33pF) ────┤                 │
                                       GND     ┌── C2 (33pF) + Rq (1k)
                                               │         │
RX (Pin 14)  ─── C_rx (1nF) ─── R_rx (1k) ─────┴─────────┤
                                                         ├─── Antenne Pad 2
                     ┌─── C0 (33pF) ────┐                 │
TX2 (Pin 11) ───────┤                  ├─── C1 (22pF) ───┘
                     └─── L0 (560nH) ───┘
```

### Stückliste (BOM) pro Antenneneinheit:
* **IC:** 1× NXP MFRC522 (TSSOP-32, LCSC Part # `C13768` o.ä., ca. 0,60 €)
* **Quarz:** 1× 27,12 MHz Grundwellenquarz (SMD 3225) + 2× 15 pF Kondensatoren
* **EMC-Drosseln ($L_0$):** 2× 560 nH (Bauform SMD 0805, Ferrit/Keramik mit hoher Resonanzfrequenz $> 50\text{ MHz}$)
* **Kondensatoren ($C_0, C_1, C_2$):** Keramik SMD 0603 **C0G / NP0** (Zwingend C0G/NP0-Dielektrikum wegen Temperaturstabilität! Kein X7R/X5R im HF-Pfad verwenden!)
  * $C_0$: $33\text{ pF}$ (2 Stück)
  * $C_1$: $22\text{ pF}$ (2 Stück)
  * $C_2$: $33\text{ pF}$ (2 Stück)
  * $R_Q$: $1{,}0\text{ k}\Omega$ (Dämpfungswiderstand für $Q \approx 20$)
* **RX-Pfad:** $C_{\text{rx}} = 1\text{ nF}$, $R_{\text{rx}} = 1\text{ k}\Omega$, Teiler an `VMID`.

---

## 4. Digitales Multiplexing (SPI-Bus & Schieberegister)

* **Gemeinsamer SPI-Bus:**
  * `SCK`, `MOSI`, `MISO`, `RST` werden an alle 9 MFRC522-Chips parallel geführt.
* **Chip-Select Steuerung:**
  * 2× **74HC595** (8-Bit Schieberegister) pro 150×150 mm Board (steuern bis zu 16 Ausgänge, 9 davon für die MFRC522 `SDA/NSS`-Pins genutzt).
  * Die Schieberegister werden über Kaskadierung (`SER_OUT` $\rightarrow$ `SER_IN`) von Board zu Board weitergereicht.
  * Der ESP32 benötigt somit **nur 3 Steuerleitungen** (`DATA`, `LATCH`, `CLOCK`), um alle 36 Slots im gesamten Regal anzusprechen!

---

## 5. Integration der Wägezellen (KERN CK 10-Y4)

* Auf **Board 1 (Master-Quadrant)** wird die Auswertung der Wägezellen integriert:
  * 4-poliger Steckverbinder (z. B. JST-XH oder Molex Picoblade) für die 4 KERN-Zellen.
  * 1× **HX711 IC** (SOP-16) direkt auf dem PCB platziert.
  * Anbindung an den ESP32 über 2 GPIOs (`HX711_DT`, `HX711_SCK`).
* Die 4 KERN CK 10-Y4 Viertelbrücken werden auf dem PCB direkt als Vollbrücke verdrahtet.

---

## 6. Nächste Schritte im KiCad-Workflow:
1. Footprint-Bibliothek in KiCad anbinden: `hardware/kicad/RFID_Antenna_40x40_3T_13.56MHz.kicad_mod`.
2. Schaltplan mit hierarchischen Blättern erstellen (1 Blatt für den "Antennen-Knoten" anlegen und in KiCad 9× duplizieren!).
3. 2-Lagen-Routing durchführen (Top-Layer für HF-Spulen & Komponenten, Bottom-Layer als durchgehende Massefläche / GND-Plane mit Entlastung unter den Spulen).
