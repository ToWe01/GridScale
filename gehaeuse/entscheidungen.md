# Entscheidungslog Gehäuse

Neue Einträge unten anhängen. Je Eintrag: Datum, Entscheidung, Begründung, verworfene Alternativen. Quelle für den Projektbericht. Herausgezogen am 2026-11-27 aus der alten Übergabe (`archiv/UEBERGABE.md`, dort weitere Details und Zahlen).

| Datum | Entscheidung | Begründung | Verworfen |
|---|---|---|---|
| 2026-11-23 | Format 150 × 150 mm, PLA, Gridfinity auf **50 mm** skaliert (3×3 Felder), Platte 148,5 mm (0,75 mm Luft je Seite zum Nachbarmodul) | Projektvorgabe Modulraster; Module später zusammensteckbar, Verbindungen nur im festen Unterteil | Referenzentwurf Handout mit 168 mm / 56-mm-Raster (nur Ideenquelle) |
| 2026-11-23 | **Zwei** Wägezellen Adafruit 4541, gegenläufig („Windmühle“) auf den Stegen y 50/100 | Bestellte Teile; diagonale Anordnung stützt die Platte | Vier Zellen aus älterer Projektbeschreibung |
| 2026-11-23 | SparkFun HX711 (2×) statt Adafruit NAU7802 | NAU7802 laut Nutzer defekt | NAU7802 aus der Stückliste |
| 2026-11-23 | Nur Standard-M4 DIN 912: Festende 2× M4×12 + Scheibe DIN 125 von unten, Freiende 2× M4×12 von oben; möglichst wenig Normteile (C-Teile) | Nutzervorgabe; Scheibe gegen Kriechen des PLA | Gewindestifte, Sonderschrauben |
| 2026-11-23 | Überlast-/Kippschutz: 4 Anschlagsockel, Spalt 0,5 mm, gedruckte Zapfen Ø3,0 in Ø4,0 (0,5 radial) | Kein Kraftnebenschluss (0,1 mm Spiel hätte in PLA gerieben) | M3-Gewindestifte |
| 2026-11-23 | Geschlossenes, staubgeschütztes Gehäuse: Schulter + Kragen am Unterteil, Schürze am Oberteil (Überdeckung 1,8, Luft 0,6) | Krümel/Staub, sichtbare Fuge zeigt nach unten | Offene Fuge |
| 2026-11-23 | Variante **Deckel**: Oberteil = Träger (an Zellen geschraubt) + abnehmbarer Gridfinity-Deckel, Schrauben verdeckt | Schraubenköpfe unsichtbar, Deckel abnehmbar | Einteiliges Oberteil mit sichtbaren Köpfen; Adapter oder Abdeckstopfen (gefielen dem Nutzer nicht) |
| 2026-11-23 | Platinen mit Pins nach unten, Header bleiben; gedruckte Rasthaken + dünne Zentrierzapfen, ESP32 auf Auflagen mit 3 Rasthaken | Später wird an die Pins gelötet, nichts ausgelötet; keine Kabelbinder, keine Normteile | Geschlossene Rahmen, Kabelbinder durch Bodenschlitze, angeschmolzene Zapfen |
| 2026-11-23 | Rechte Wand im Prototyp geschlossen, 4-mm-Innenverstärkung für späteren Modulverbinder (`CONN_W`/`CONN_H`) | Verbinder noch nicht festgelegt | Offenes Verbinderfenster |
| 2026-11-23 | **V2:** TCA9548A an die Trägerunterseite (wiegen mit), USB-C-Buchse in die Vorderwand, ESP32 hinten | V1: Delock-Stecker am ESP32 kollidierte mit der Einbaubuchse (194 mm³), kein Platz zum Kabelbiegen; nur 4–5 Adern über den Wägespalt | V1-Layout (USB links, TCA im Unterteil) |
| 2026-11-23 | Lötverteiler aus Streifenraster (selbst zugeschnitten) unter der Platte | Übersichtliche Versorgung der 9 Reader und 2 TCAs | Durchschleifen an den Board-Pins |
| 2026-11-23 | PN532 umgedreht (Antenne, Bestückung, Stiftleiste nach unten) | Abgewinkelte I²C-Pins ragen 4 mm über die Kante, Stege reichten für Aussparungen nicht | Antenne oben mit ca. 5,5 mm Aussparung je Tasche |
| 2026-11-24 | PN532 **Weg 3**: durchgehende Tasche, Reader von oben auf 4 Eckauflagen, Deckel-Druckplatte hält ihn, keine Reader-Rasthaken | Echte Maße: in flacher Lage stießen 7 von 9 Readern an Zellen/Unterteil/Stecker; Haken-Arm wäre nur ca. 3 mm; Antenne näher am Behälter | Pins kürzen (reichte nicht), Reader-Rasthaken |
| 2026-11-24 | Deckel stützfrei mit Randleiste vorne/hinten, Druck auf Druckplatten und Leisten | Druck ohne Stützmaterial | Deckel mit Stützen |
| 2026-11-24 | Leitungen als flache Bänder unter der Platte, links/rechts an den Zellen vorbei | Zellen liegen bei y 50/100 unter der Platte | Kabelnuten im Träger (Engstellen unter Readertaschen ohne Material) |
| 2026-11-24 | Gridfinity-Behälter mit Tag-Mulde (NTAG213 Metal Label Ø29), Lesefläche nach unten | Tag direkt über dem Reader | – |
| 2026-11-24 | Träger +1 mm (`PN_DEPTH` 8,5) und Deckel über 8 Passzapfen mit Quetschrippen verbunden | FEM: Träger für Ecklasten zu weich (Anschlag schon bei ca. 1,1 kg Ecklast); Verbindung, die sich am besten drucken lässt | Rasthaken Deckel–Träger (stünden beim Druck senkrecht, Biegung quer zu den Schichten) |
| 2026-11-26 | Opferschichten an den M4-Senkungen (`SACR_LAYER`) | Coupon C/D: Senkungsboden unsauber | – |
| 2026-11-26 | TCA_A um 180° gedreht, Bus über Querkerbe in Steg A | Pinbelegung aus Eagle: Kanäle 2–7 an JP1 müssen zu den Readern links zeigen | TCA_A in alter Lage (Belegung passte nicht) |
| 2026-11-27 | Silikon/Kabel der Wägezelle als Sperrzonen, Zellen gedreht (`CELL_FLIP`) | Coupon D: Silikon stieß an Verdrehsicherung; Kabelseite so außen. Folge: Vorzeichen des Signals kehrt sich um | Zellen in alter Lage |
| 2026-11-27 | SPI-Leiste an Reader 22/23 abkneifen (`PN_SPI_CUT`) | Pins lagen über dem Silikon der Zelle, SPI wird nicht genutzt | Reader höher setzen (neue Tasche, neuer Coupon) |
| 2026-11-27 | Delock 87824 mit 2× M3-Senkschraube ISO 10642 + Mutter im Flansch | Gemessene Maße, Flansch 7,51 dick | Gedruckte Klemmung |
| 2026-11-27 | Wickelkammer entfällt, Delock-Kabel auf ca. 21 cm gekürzt; Power-Hub vorne rechts, JP_NFC im Bodenfenster | Stromkonzept des Elektronik-Teams (`elektronik/`, Commit ee8bd84); 1 m Kabel passte nicht in die Kammer | Kammer mit 4. Lage, Rest außen führen, 0,5-m-Kabel |
| 2026-11-27 | Am Hub nur VBUS_IN, 5V_NFC, GND; 3V3/SDA/SCL und HX711-Versorgung direkt am ESP32 | Kürzere Wege, kein 5er-Bündel quer durchs Unterteil (gleiche Netze wie Elektronik-Plan, abzustimmen) | Alle Versorgungen über den Hub |
| 2026-11-27 | Montagelöcher Ø2,5 in Hub und Lötverteiler auf Streifen 3, Hub auf 12 Raster verlängert, Domen statt Schaumklebeband | Feste Lage ohne Klebeband; alle Streifen behalten nutzbare Löcher | Leisten mit Schaumklebeband |
| 2026-11-27 | Arbeitsweise mit Claude Code: Maße in `skripte/params.py`, Stand in `STAND.md`, Entscheidungen hier, Rechte/Hooks/Agenten in `.claude/`; Schnittstelle zur Elektronik als generierte Datei `schnittstelle/gehaeuse_elektronik.json` im Root | Weniger Pflichtlektüre, Regeln technisch durchgesetzt, gemeinsames Repo für drei Teams | Daten der Schnittstelle in `gehaeuse/` lassen; FCStd/STL nicht mehr committen (Nutzer: bleibt wie bisher) |
