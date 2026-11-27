# Statusbericht: GridScale – Die intelligente Wiegematte (ESP32-C6)

**Datum:** 26.11.2026 | **Verfasser:** [Philipp Flegler, Tomke Wegers]| **Betreuer:** [Prof. Dr.-Ing. Michael Protogerakis]

**Aktueller Stand**  
Die isolierte Entwicklungsumgebung (Docker mit `arduino-cli`, ESP32-Core `3.3.12` und USB-Passthrough) sowie der Build-, Flash- und Monitoring-Workflow für den ESP32-C6 laufen stabil. Der I²C-Hauptbus (`GPIO 4/5`, `100 kHz`) ist elektrisch verifiziert, und der erste I²C-Multiplexer (TCA9548A @ `0x70`) schaltet alle acht Kanäle (`CH0..CH7`) fehlerfrei. Zudem liegt ein getrenntes Versorgungskonzept (USB für Logik, externes 5V-Netzteil ≥ 2 A für die PN532-Reader) vor.

**Hardware-Problem & Maßnahme**  
Der getestete Wägezellen-ADC (NAU7802 @ `0x2A`) verursacht I²C-Timeouts (`status=5`). Abzieh- und Kreuztests an mehreren GPIOs bestätigten einen hardwareseitigen Kurzschluss des `SDA`-Pins nach `3,3 V`. Die defekte Platine wird ausgesondert und durch einen Ersatz-AD-Wandler aus dem Lager ersetzt; die 5-kg-Wägezellen bleiben unberührt.

**Nächste Schritte**
1. Zweiten TCA9548A (`0x71`) parallel einbinden und testen.
2. PN532-NFC-Reader (`0x24`) zunächst einzeln, dann als 9-fach-Aufbau am externen 5V-Netzteil mit sequentieller RF-Abschaltung in Betrieb nehmen.
3. Ersatz-AD-Wandler aus dem Lager holen, an die Wägezellen anbinden und kalibrieren.

---

## Gehäuse und Konstruktion

**Aktueller Stand**  
Der Gehäuse-Prototyp (150 × 150 mm, PLA, FDM) ist als vollständig parametrisches FreeCAD-Modell aufgebaut (Version V2). Alle Maße stehen mit Status und Quelle (`bestätigt`, `Norm`, `Annahme`, `Platzhalter`) in einer Parameterliste im Python-Skript. Jeder Lauf baut das Modell neu und schreibt einen automatischen Prüfbericht: gültige Körper, Kollisionen, Spaltmaße und ein Bewegungscheck der Wägeplatte. Der Aufbau ist dreiteilig:
- Unterteil mit ESP32-C6, 2 AD-Wandler-Boards und USB-C-Einbaubuchse
- Träger auf zwei 5-kg-Wägezellen (Adafruit 4541). Er hält die 9 PN532-Reader in durchgehenden Taschen und die beiden TCA9548A (`0x70`/`0x71`) an der Unterseite.
- Abnehmbarer Deckel mit Gridfinity-Raster (3 × 3 Felder à 50 mm), über 8 Passzapfen im Presssitz aufgesteckt. Er drückt die Reader von oben fest, die Antenne liegt 3,8 mm unter dem Behälterboden.

Die Wägemechanik ist ohne Kraftnebenschluss ausgelegt: Luft um die Zellen, Überlast- und Kippanschläge mit 0,5 mm Spalt, Kabel mit Schlaufe über den Wägespalt. Kabelwege, Lötverteiler und Litzenbündel sind im Modell als Sperrzonen enthalten.

**Problem & Maßnahme**  
Eine FEM-Studie (FreeCAD/CalculiX) zeigte eine zu weiche Trägerplatte: Bei 5 kg auf einem Eckfeld bog sie sich bis 2,3 mm durch und lag am Überlastanschlag (Spalt 0,5 mm) an. Der Träger wurde daraufhin um 1 mm verstärkt und mit dem Deckel verzapft. Die Durchbiegung sinkt damit auf 0,85–1,39 mm, je nachdem, wie stark der Deckel mitträgt. Verteilte 10 kg liegen bei 0,28–0,51 mm. Für 5 kg pro Eckfeld reicht das noch nicht. 

Vor dem Druck der ganzen Teile wurden 6 Testdruck-Coupons gedruckt, Ausschnitte direkt aus dem Modell. Ergebnis:
- Passzapfen, Reader-Tasche, Gridfinity-Sitz, Rasthaken der AD-Wandler-Boards und TCA-Zentrierung passen.
- Die Senkungen für die M4-Schrauben wurden unsauber. Abhilfe: Opferschichten im Modell.
- Der mit Silikon verklebte Kabelaustritt der Wägezelle stößt an die Verdrehsicherung im Sockel.

**Nächste Schritte**
1. Wägezelle mit Kleber und Kabelaustritt ausmessen und in den Sockel einarbeiten.
2. Pinbelegung von TCA9548A und PN532 mit dem Elektronikteam abgleichen und die Kabelführung anpassen.
3. Höchstlast pro Feld festlegen, Steifigkeit des Trägers absichern, danach die Gesamtteile drucken.
