# Stand Gehäuse (wird überschrieben, nicht ergänzt)

Stand: 2026-11-27. Einzige Stelle für offene Punkte des Gehäuses. Begründungen und verworfene Varianten: `entscheidungen.md`. Alte Übergabe (bis 27.11.): `archiv/UEBERGABE.md`.

## Konstruktion V2 (Hauptversion)
- **Quelle:** `skripte/params.py` (alle Maße mit Status und Quelle) + `skripte/build_prototyp_v2.py` (Geometrie, Prüfungen) → `modell/Prototyp_15x15_Deckel_V2.FCStd`, `pruefberichte/pruefbericht_deckel_v2.txt` (Zusammenfassung oben) und `../schnittstelle/gehaeuse_elektronik.json`. Bauen mit `/bauen`.
- **Aufbau:** 148,5 × 148,5 × 34,95 mm, PLA. Unterteil (Wanne mit Schulter und Kragen) + Oberteil aus **Träger** (9,5 mm, auf zwei Wägezellen Adafruit 4541 „Windmühle“ bei y 50/100) und **Gridfinity-Deckel** (50-mm-Raster, 8 Passzapfen mit Quetschrippen).
- **Reader:** 9× PN532 umgedreht, von oben in durchgehende Taschen gelegt, auf 4 Eckauflagen, Deckel-Druckplatte hält sie. Antenne 4,8 mm unter dem Behälterboden. SPI-Leiste an Reader 22/23 abgekniffen.
- **Unterteil:** ESP32-C6 hinten (Pins unten, Jumper unter der UART-Buchse), 2× HX711, Power-Hub vorne rechts (JP_NFC im Bodenfenster), Delock 87824 in der Vorderwand (2× M3-Senkschraube). Delock-Kabel auf ca. 21 cm gekürzt.
- **Platte (wiegt mit):** 2× TCA9548A und Lötverteiler an der Trägerunterseite, Bänder unter der Platte an den Zellen vorbei. Über den Wägespalt 5 Adern als Schlaufe.
- **Letzter Prüfbericht:** ZUSAMMENFASSUNG OK (0 Abweichungen, 1 bekannter Hinweis: kein Platz für Passzapfen bei (101|8)/(101|142)); alle Körper gültig, 0 Kollisionen, Bewegungscheck 0 mm³, Unterteil 79452 mm³, Träger/Deckel 55124/63593 mm³. Offene Platzhalter: `CONN_W`, `CONN_H`.
- **Druck:** Paket in `druck/` (STLs + `DRUCKHINWEISE.txt`). Coupons Runde 1 gedruckt (26.11.), Messwerte eingebaut, kein Neudruck nötig.

## Offene Punkte
1. **Lesereichweite PN532** mit echten Tags testen (Antenne 4,8 mm unter Behälterboden). Reicht sie nicht: Träger dünner (kürzere Haken, Umbau).
2. **Modulverbinder** festlegen (`CONN_W`, `CONN_H`, rechte Wand bisher geschlossen).
3. **Mit Elektronik abstimmen:** Hub-Belegung (nur VBUS_IN, 5V_NFC, GND; 3V3/SDA/SCL/HX711 am ESP32), TCA-Kanalbelegung, Vorzeichen Wägesignal (`CELL_FLIP`), TCA_B A0 = 1.
4. **Mit Software abstimmen:** Delock-Stecker steckt in der UART-Buchse des ESP32.
5. **Steifigkeit Träger** (FEM 25./26.11.): 5 kg pro Eckfeld werden nicht erreicht. Last pro Feld als Anforderung festlegen oder Träger unten schließen/Rippen.
6. **Nachmessen/Testdruck:** Presssitz Deckelzapfen (`CRUSH_W`, `COVER_PIN_HOLE`), `STOP_GAP` 0,5 an der echten Zellendurchbiegung, `PN_T`, `ESP_ANT_T`.
7. Knapp, aber im Soll: Strang Reihe 3 1,2 mm über der USB-Buchse des ESP32, Luft TCA–Unterteil 1,61 mm, Restwand Kopfsenkung Freiende 0,8 mm (Ausnahme).
8. Gravur zeigt noch „R3“.
9. **Arbeitsumgebung (Umbau 27.11.):** Hooks in Claude Code mit einer kleinen Teständerung auslösen lassen (Nutzer). FCStd einmal über die FreeCAD-Bridge mit Farben neu bauen, wenn sich das Modell ändert (headless fehlen die Farben).

## Nächster Schritt
Gesamtteil drucken (Paket `druck/`), Reader und Zellen einbauen, Lesereichweite und Überlastanschlag am echten Teil prüfen.
