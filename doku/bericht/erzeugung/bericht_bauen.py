# -*- coding: utf-8 -*-
# Fuellt "Bericht Template.docx" mit dem Entwurf. Vorlage bleibt unveraendert, Ausgabe als neue Datei.
import re, os, shutil, zipfile, html
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
S = os.path.join(PROJ, "doku", "bericht", "erzeugung")   # Bilder in S/bilder, Arbeitsordner temporaer
SRC = os.path.join(PROJ, "doku", "bericht", "Bericht Template.docx")
OUT = os.path.join(PROJ, "doku", "bericht", "Bericht_Entwurf_GridScale.docx")
import tempfile
W = os.path.join(tempfile.gettempdir(), "bericht_unpacked")
shutil.rmtree(W, ignore_errors=True); zipfile.ZipFile(SRC).extractall(W)

# ---------------- XML-Bausteine ----------------
def esc(t): return html.escape(t, quote=False)
def run(t, b=False, i=False, color=None, hl=False, sz=None):
    rp = ("<w:b/>" if b else "") + ("<w:i/>" if i else "") + ('<w:color w:val="%s"/>' % color if color else "") + \
         ('<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz) if sz else "") + ('<w:highlight w:val="yellow"/>' if hl else "") + '<w:lang w:val="de-DE"/>'
    return '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rp, esc(t))
def runs(spec, **kw):   # **fett**, [[Platzhalter]]
    out = []
    for part in re.split(r"(\*\*.+?\*\*|\[\[.+?\]\])", spec):
        if not part: continue
        if part.startswith("**"): out.append(run(part[2:-2], **dict(kw, b=True)))
        elif part.startswith("[["): out.append(run("[" + part[2:-2] + "]", hl=True, **kw))
        else: out.append(run(part, **kw))
    return "".join(out)
def P(spec, style=None, bullet=False, keep=False, align=None, after=None, **kw):
    pp = ""
    if style: pp += '<w:pStyle w:val="%s"/>' % style
    if keep: pp += "<w:keepNext/>"
    if bullet: pp += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="90"/></w:numPr>'
    if after is not None: pp += '<w:spacing w:after="%d"/>' % after
    if align: pp += '<w:jc w:val="%s"/>' % align
    return '<w:p><w:pPr>%s<w:rPr><w:lang w:val="de-DE"/></w:rPr></w:pPr>%s</w:p>' % (pp, runs(spec, **kw))
def B(*items): return "".join(P(t, bullet=True, after=40) for t in items)
def CAP(t): return P(t, i=True, color="595959", sz=18, after=200)
def TABLE(rows, widths, header=True):
    tw = sum(widths)
    g = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
    x = ['<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:tblBorders>' % tw +
         "".join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>' % s for s in ("top", "left", "bottom", "right", "insideH", "insideV")) +
         '</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>%s</w:tblGrid>' % g]
    for r, row in enumerate(rows):
        x.append("<w:tr>" + ('<w:trPr><w:tblHeader/></w:trPr>' if r == 0 and header else ""))
        for c, cell in enumerate(row):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="EDEDED"/>' if (r == 0 and header) else ""
            paras = "".join('<w:p><w:pPr><w:spacing w:before="20" w:after="20"/></w:pPr>%s</w:p>' % runs(line, b=(r == 0 and header), sz=18) for line in cell.split("\n"))
            x.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr>%s</w:tc>' % (widths[c], shade, paras))
        x.append("</w:tr>")
    x.append("</w:tbl>")
    return "".join(x) + P("", after=0)
IMG_ID = [900]
def IMG(rid, w_px, h_px, width_in, name):
    cx = int(width_in * 914400); cy = int(cx * h_px / w_px); IMG_ID[0] += 1; n = IMG_ID[0]
    return ('<w:p><w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            '<wp:extent cx="%d" cy="%d"/><wp:docPr id="%d" name="%s"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>') % (cx, cy, n, name, n, name, rid, cx, cy)

# ---------------- Bilder registrieren ----------------
shutil.copy(os.path.join(S, "bilder/abb_explosion.png"), os.path.join(W, "word/media/abb_explosion.png"))
shutil.copy(os.path.join(S, "bilder/abb_lageplan.png"), os.path.join(W, "word/media/abb_lageplan.png"))
relp = os.path.join(W, "word/_rels/document.xml.rels"); rel = open(relp, encoding="utf-8").read()
rel = rel.replace("</Relationships>",
    '<Relationship Id="rId901" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/abb_explosion.png"/>'
    '<Relationship Id="rId902" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/abb_lageplan.png"/></Relationships>')
open(relp, "w", encoding="utf-8").write(rel)

# ---------------- Aufzaehlung (numId 90) ----------------
nump = os.path.join(W, "word/numbering.xml"); num = open(nump, encoding="utf-8").read()
absn = ('<w:abstractNum w:abstractNumId="90"><w:multiLevelType w:val="hybridMultilevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
        '<w:lvlText w:val="–"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>')
i = num.find("<w:num w:numId="); num = num[:i] + absn + num[i:]
num = num.replace("</w:numbering>", '<w:num w:numId="90"><w:abstractNumId w:val="90"/></w:num></w:numbering>')
open(nump, "w", encoding="utf-8").write(num)

# ---------------- Inhalte ----------------
C = {}
C["hinweis"] = P("**Entwurfsstand 24.11.2026.** Gelb markiert = von der Gruppe zu ergänzen oder zu prüfen. Grau kursiv = Leitfragen aus der Vorlage, vor der Abgabe löschen. "
                 "Kapitel zu Gehäuse und Konstruktion sind ausformuliert, die übrigen Kapitel enthalten Stichpunkte als Vorschlag.", color="7F7F7F", sz=18)

C["value"] = (
    P("In vielen Haushalten fehlt der Überblick über die Vorräte: Lebensmittel laufen unbemerkt ab, werden doppelt gekauft oder fehlen beim Kochen. "
      "Bestehende Lösungen setzen auf manuelle Eingabe oder das Scannen von Barcodes und werden im Alltag schnell nicht mehr gepflegt.") +
    P("Die **GridScale** schafft Wert, indem sie den Bestand ohne zusätzlichen Handgriff erfasst: Jeder Behälter wird beim Abstellen über einen RFID-Tag erkannt, "
      "die Wägezellen messen, wie viel darin ist. Im Sinne des Smart Navigators liegt der Wert damit vor allem auf der Achse **Productivity & Efficiency** "
      "(Zeit und Aufwand im Haushalt, weniger Fehlkäufe), als neues Produkt zugleich auf **Growth & Revenue**.") +
    P("Sozioökonomische Trends, aus denen sich der Bedarf ergibt:") +
    B("Vermeidung von Lebensmittelverschwendung und Nachhaltigkeit [[Zahl mit Quelle ergänzen, z. B. Lebensmittelabfälle privater Haushalte in Deutschland]]",
      "Wachsende Verbreitung von Smart-Home-Systemen und vernetzten Haushaltsgeräten",
      "Zeitknappheit und Wunsch nach Komfort im Alltag (automatische Einkaufsliste)",
      "Selbstständiges Wohnen im Alter: Unterstützung beim Überblick über Vorräte [[prüfen, ob die Gruppe diesen Aspekt aufnehmen will]]"))

C["ziel"] = (
    P("**Uniqueness:** Die Matte verbindet zwei Informationen, die bisherige Lösungen getrennt erfassen: **welcher** Behälter auf welchem Stellplatz steht (RFID je Feld) "
      "und **wie viel** darin ist (Gewicht). Das Raster ist zu **Gridfinity** kompatibel, einem offenen, weit verbreiteten Ordnungssystem, für das Behälter selbst gedruckt werden können. "
      "Die Module sind so ausgelegt, dass mehrere zu einer größeren Fläche zusammengesteckt werden können.") +
    P("**Application:** Vorratsschrank und Regalboden in der Küche, z. B. für Gewürze, Nudeln, Reis, Müsli oder Kaffee in wiederverwendbaren Behältern.") +
    P("Im Projekt umgesetzt wird ein funktionsfähiger **Prototyp eines Moduls** (150 × 150 mm, 3 × 3 Stellplätze im 50-mm-Raster) mit:") +
    B("zwei Wägezellen und HX711-Wägeverstärkern für das Gewicht,",
      "neun RFID-Readern PN532 (einer je Stellplatz) und Behältern mit NFC-Tag,",
      "einem ESP32-C6 als Steuerung mit Funkanbindung,",
      "einem dreiteiligen, 3D-gedruckten Gehäuse mit Gridfinity-Deckel,",
      "[[Software-Ziele ergänzen: Datenweitergabe, App/Dashboard, Benachrichtigungen]]") +
    P("[[Messbare Ziele ergänzen, z. B. Genauigkeit der Wägung, sichere Erkennung je Feld, Reaktionszeit]]"))

C["vorgehen"] = (
    P("Technisch beruht das System auf drei Bausteinen (Enabler):") +
    B("**Identifikation:** Unter jedem Behälter klebt ein NFC-Tag (NTAG213). Der PN532 im Feld darunter liest ihn durch den 3D-gedruckten Deckel.",
      "**Menge:** Die gesamte Auflagefläche liegt auf zwei Biegebalken-Wägezellen. Ändert sich das Gewicht beim Abstellen oder Entnehmen, wird die Differenz dem Feld zugeordnet, auf dem sich gleichzeitig der Tag-Zustand ändert.",
      "**Vernetzung:** Der ESP32-C6 liest alle Sensoren aus und gibt die Daten per Funk weiter [[Protokoll und Zielsystem festlegen, z. B. WLAN/MQTT]].") +
    P("Die neun Reader haben dieselbe I²C-Adresse. Sie werden deshalb über zwei I²C-Multiplexer (TCA9548A) einzeln angesprochen. "
      "Das Gehäuse trennt die gewogene Platte mechanisch vollständig vom festen Unterteil, damit keine Kräfte an den Wägezellen vorbeigeleitet werden."))

C["wbs"] = (
    P("Das Projekt gliedert sich in folgende Arbeitspakete [[Verantwortliche eintragen, Pakete mit der Gruppe abgleichen]]:") +
    TABLE([["AP", "Arbeitspaket", "Inhalt", "Verantwortlich"],
           ["1", "Konzept und Anforderungen", "Use Case, Anforderungen, Komponentenauswahl, Bestellung", "[[Gruppe]]"],
           ["2", "Gehäuse und Mechanik", "Wägemechanik, Gehäuse in drei Teilen, Halterungen, Reader-Taschen, Gridfinity-Behälter, Druckvorbereitung", "[[Name]]"],
           ["3", "Elektronik und Verdrahtung", "Schaltplan, Spannungsversorgung, Verdrahtung Reader/TCA/HX711, Inbetriebnahme", "[[Name]]"],
           ["4", "Firmware", "Auslesen der Wägezellen und Reader, Kalibrierung, Ereigniserkennung", "[[Name]]"],
           ["5", "Daten und Anwendung", "Datenübertragung, Bestandslogik, Oberfläche/App", "[[Name]]"],
           ["6", "Integration und Test", "Montage, Lesetest, Wägetest, Funktionstest gesamt", "[[Gruppe]]"],
           ["7", "Dokumentation", "Bericht, Präsentation", "[[Gruppe]]"]],
          [500, 2100, 4960, 1800]))

C["obs"] = (
    P("[[Teamorganisation beschreiben: Rollen, Ansprechpartner, Abstimmungsrhythmus, wie Entscheidungen getroffen wurden]]") +
    B("Gemeinsame Bestellliste mit Budget (Excel) als zentrale Stückliste",
      "Gehäuse als parametrisches Skript (FreeCAD/Python): Maße stehen mit Status und Quelle in einer Parameterliste, dadurch nachvollziehbar und versionierbar",
      "[[weitere Plattformen ergänzen, z. B. GitHub, Messenger, Cloud-Ordner]]",
      "Schnittstelle Gehäuse – Elektronik: Pinbelegung, Kabelwege und Spannungen müssen gemeinsam festgelegt werden [[wie wurde das abgestimmt?]]"))

C["plan"] = (
    P("Am Anfang (Mitte Oktober) stand eine sehr umfangreiche Idee: Kacheln von 30 × 30 cm mit 36 Stellplätzen, eine eigene Platine mit integrierten Antennenspulen und 36 RFID-Chips sowie vier Wägezellen. "
      "Bei der Abschätzung des Aufwands zeigte sich, dass dies im Semester nicht umsetzbar ist. Die Gruppe hat den Umfang deshalb auf einen **Prototyp von 15 × 15 cm aus fertigen Modulen** reduziert. "
      "So kann das Funktionsprinzip RFID plus Gewicht nachgewiesen werden, bevor in eine eigene Platine investiert wird.") +
    P("Meilensteine [[mit der Gruppe vervollständigen]]:") +
    B("Mitte Oktober: erste Ideen und Grobkonzept",
      "Anfang November: Bestellung der Komponenten",
      "23.11.: Gehäuse V1 (einteilig und Deckel-Variante), Maßprüfung aller Kaufteile",
      "23./24.11.: Gehäuse V2 (Multiplexer an der Platte, Kabelführung, USB vorne), Reader-Einbau nach echten Maßen, Druckfreigabe",
      "[[Inbetriebnahme Elektronik, Firmware, Tests, Abgabe]]") +
    P("Was nicht nach Plan lief:") +
    B("Der ursprünglich bestellte Wägeverstärker (NAU7802) war defekt und wurde durch den SparkFun HX711 ersetzt.",
      "Die tatsächlichen Maße der Reader (Stiftleisten, DIP-Schalter, Pinüberstand) passten nicht in die erste Tasche. Der Einbau wurde umgestellt (Reader von oben eingelegt, Abschnitt 3.1).",
      "[[weitere Punkte der Gruppe]]"))

C["agil"] = (
    P("Elemente agiler Entwicklung wurden vor allem an zwei Stellen genutzt:") +
    B("**Reduktion auf ein Minimum Viable Product:** Statt der kompletten Kachel wurde zuerst ein kleines, funktionsfähiges Modul gebaut, um das Prinzip früh zu testen.",
      "**Kurze Iterationen im Gehäuse:** Das Modell wird vollständig aus einem Skript erzeugt. Nach jeder Änderung wird es neu gebaut und automatisch geprüft (gültige Körper, Kollisionen, Spaltmaße, Wandstärken, Bewegung der Platte bis zum Anschlag). "
      "Das entspricht einer Continuous Integration in der Softwareentwicklung. Messungen an den echten Teilen flossen direkt in die nächste Iteration ein.") +
    P("Rückblickend sinnvoll gewesen wären:") +
    B("frühere Maßaufnahme der Kaufteile, bevor konstruiert wird,",
      "ein früh festgelegtes Schnittstellendokument zwischen Gehäuse und Elektronik (Pins, Spannungen, Kabelwege),",
      "[[Sicht der Gruppe ergänzen, z. B. regelmäßige kurze Abstimmungen]]"))

C["produkt"] = (
    P("Dieser Abschnitt beschreibt das physische Produkt, das Gehäuse des Prototyps. [[Abschnitt zur Vernetzung des Produkts ergänzen]]") +
    P("**Aufbau.** Das Modul besteht aus drei Druckteilen aus PLA (FDM-Druck): dem festen **Unterteil** mit Elektronik und Wägezellen, dem **Träger**, der als gewogene Platte auf den Wägezellen liegt "
      "und die Reader aufnimmt, und dem abnehmbaren **Gridfinity-Deckel** mit neun Stellplätzen. Außenmaß 148,5 × 148,5 × 33,95 mm. Alle Teile lassen sich ohne Stützstrukturen drucken.") +
    IMG("rId901", 850, 747, 4.6, "Explosionsansicht") + CAP("Abbildung [[x]]: Explosionsansicht V2 – Unterteil mit Wägezellen, ESP32 und HX711; Träger mit Readern (rot); Gridfinity-Deckel") +
    P("**Wägemechanik.** Zwei Biegebalken-Wägezellen (5 kg) liegen gegenläufig unter der Platte. Das feste Ende ist von unten mit dem Unterteil verschraubt, auf dem freien Ende liegt der Träger. "
      "Damit das Gewicht vollständig über die Zellen läuft, berührt der Träger das Unterteil nirgends: Um die Zellen bleibt Luft, Überlastanschläge haben 0,5 mm Spalt, "
      "Führungszapfen 0,5 mm Spiel, und die Leitungen laufen als lose Schlaufe über den Wägespalt. Ein automatischer Bewegungscheck prüft, dass die Platte auch beim Kippen bis zum Anschlag frei bleibt.") +
    P("**Staubschutz.** Eine umlaufende Schürze am Träger greift außen über einen Kragen des Unterteils (1,8 mm Überdeckung, 0,6 mm Spalt). Die Fuge zeigt nach unten, Krümel fallen nicht in die Elektronik.") +
    P("**RFID-Integration.** Jeder Reader liegt kopfüber in einer durchgehenden Tasche des Trägers auf vier Eckauflagen und wird von einer Druckplatte am Deckel gehalten. "
      "Er wird von oben eingelegt, die Stiftleisten bleiben zum Anlöten frei. Die Antenne liegt 3,8 mm unter dem Behälterboden, das Tag im Behälterfuß etwa 2,2 mm über der Reader-Platine. "
      "Das gedruckte PLA lässt das 13,56-MHz-Feld durch. [[Ergebnis des Lesetests ergänzen]]") +
    P("**Elektronik und Montage.** ESP32, HX711 und Multiplexer werden von **13 gedruckten Rasthaken** gehalten, Schrauben gibt es nur an den Wägezellen (8 × M4 × 12, 4 Scheiben). "
      "Die Multiplexer und ein Lötverteiler sitzen an der Unterseite des Trägers, nahe bei den Readern. Dadurch laufen nur vier Adern über den Wägespalt. "
      "Die Stromversorgung kommt über eine USB-C-Einbaubuchse an der Vorderseite, das Kabel zum ESP32 liegt in einer Wickelkammer.") +
    IMG("rId902", 2136, 1065, 6.4, "Lageplan Verdrahtung") + CAP("Abbildung [[x]]: Lageplan der Verdrahtung, links Unterteil, rechts Unterseite des Trägers (Entwurf)") +
    P("**Gridfinity-Behälter.** Die Behälter haben das Gridfinity-Fußprofil, skaliert auf das 50-mm-Raster. Unter jedem Fuß ist eine Mulde für das NFC-Tag, so liegt das Tag direkt über dem Reader. "
      "Gedruckt wurden Größen 1 × 1, 2 × 1 und 2 × 2.") +
    P("**Modularität.** Die rechte Wand ist für einen späteren Steckverbinder zwischen Modulen vorbereitet. Verbindungen sind nur im festen Unterteil vorgesehen, damit benachbarte Module die Wägung nicht beeinflussen.") +
    P("**Konstruktionsmethode.** Das komplette Modell entsteht aus einem Python-Skript in FreeCAD. Jedes Maß steht mit Status (bestätigt, Norm, Annahme, Platzhalter) und Quelle in einer Parameterliste. "
      "Nach jedem Lauf schreibt das Skript einen Prüfbericht. Für den 3D-Druck gelten feste Regeln: Wandstärke mindestens 1,2 mm, Passungen 0,3–0,5 mm, keine Überhänge."))

C["techdaten"] = P("Die folgenden Abschnitte ordnen das System den vier Technologie-Trends des Smart Navigators zu. [[Aufteilung auf die Teilnehmer festlegen]]")

C["sensors"] = (
    TABLE([["Sensor", "Anzahl", "Aufgabe", "Anbindung"],
           ["Wägezelle Adafruit 4541 (Biegebalken, 5 kg)", "2", "Gesamtgewicht der Platte", "je ein SparkFun HX711 (24 Bit), 2-Draht"],
           ["RFID-Reader PN532 V3 (13,56 MHz)", "9", "Erkennt den Behälter je Stellplatz", "I²C über 2 × TCA9548A"],
           ["NFC-Tag NTAG213 (Metal Label)", "je Behälter", "Kennung des Behälters", "passiv, im Behälterfuß"]],
          [2900, 900, 2800, 2760]) +
    P("**Mechanischer Beitrag:** Lagerung der Zellen ohne Kraftnebenschluss, Überlastschutz, Abstand Antenne – Tag (siehe 3.1). Das Tag hat eine Metallseite, die Leseseite muss nach unten zeigen.") +
    P("[[Kalibrierung, Auflösung und Genauigkeit der Wägung, Ergebnis Lesetest ergänzen]]"))

C["conn"] = (
    B("**Intern:** I²C-Bus vom ESP32 zu zwei Multiplexern TCA9548A. Alle PN532 haben die feste Adresse 0x24, deshalb bekommt jeder Reader einen eigenen Kanal. Die HX711 sind über je zwei Leitungen (Takt, Daten) angeschlossen.",
      "**Extern:** Der ESP32-C6 unterstützt WLAN (Wi-Fi 6), Bluetooth LE und IEEE 802.15.4 (Thread/Zigbee). [[gewähltes Protokoll und Zielsystem beschreiben]]",
      "**Zwischen Modulen:** im Prototyp noch nicht umgesetzt, Steckverbinder im Unterteil vorgesehen."))

C["data"] = (
    B("**Differenzwägung:** Beim Abstellen oder Entnehmen ändert sich das Gesamtgewicht. Die Differenz wird dem Feld zugeordnet, auf dem sich gleichzeitig der Tag-Zustand ändert.",
      "Mit zwei Wägezellen lässt sich der Schwerpunkt nur in einer Richtung bestimmen. Die eindeutige Zuordnung zum Stellplatz übernimmt daher das RFID. [[von der Gruppe prüfen]]",
      "[[Filterung, Kalibrierung, Bestandslogik, Füllstand und Warnschwellen ergänzen]]"))

C["output"] = (
    P("Das Modul selbst hat im Prototyp keine Aktoren. Ausgaben erfolgen digital:") +
    B("[[z. B. Dashboard/App mit Bestand je Behälter]]", "[[z. B. Benachrichtigung bei niedrigem Füllstand, automatische Einkaufsliste]]",
      "Mögliche Erweiterung: LED je Stellplatz, um Behälter anzuzeigen"))

C["orga"] = (
    P("[[Vorschlag für Stichpunkte, mit der Gruppe abstimmen:]]") +
    B("Ein Unternehmen mit diesem Produkt braucht Hardware-, Software- und Service-Kompetenz in einem Team.",
      "Hardware und Software müssen über klare Schnittstellen zusammenarbeiten (im Projekt: Gehäuse – Elektronik – Firmware).",
      "Updates der Firmware über Funk erfordern Prozesse für Pflege und Support."))

C["menschen"] = (
    P("[[Vorschlag für Stichpunkte:]]") +
    B("Akzeptanz: Nutzer müssen ihre Vorräte in Behälter mit Tag umfüllen. Gridfinity ist in der Maker-Community bereits verbreitet.",
      "Datenschutz: Daten zum Verbrauch im Haushalt sind sensibel. Eine lokale Verarbeitung ohne Cloud ist ein Argument.",
      "Bedienung muss ohne Einrichtung im Alltag funktionieren (Behälter abstellen, fertig)."))

C["business"] = (
    P("**Kosten des Prototyps (ein Modul, Elektronik laut Bestellliste):**") +
    TABLE([["Position", "Menge", "Preis je Stück", "Summe"],
           ["ESP32-C6-DevKitC-1", "1", "9,99 €", "9,99 €"],
           ["RFID-Reader PN532 V3", "9", "5,67 €", "51,03 €"],
           ["I²C-Multiplexer TCA9548A", "2", "6,17 €", "12,34 €"],
           ["Wägezelle Adafruit 4541", "2", "3,51 €", "7,02 €"],
           ["SparkFun HX711", "2", "[[Preis]]", "[[Summe]]"],
           ["USB-C-Einbaubuchse Delock 87824", "1", "12,99 €", "12,99 €"],
           ["NFC-Tag NTAG213", "je Behälter", "2,11 €", "–"],
           ["PLA, Litze, Schrauben", "", "", "[[schätzen]]"],
           ["**Summe ohne HX711, Material und Tags**", "", "", "**93,37 €**"]],
          [4200, 1200, 1800, 2160]) +
    P("Das Gehäuse hat zusammen etwa 185 cm³ Volumen (Unterteil, Träger, Deckel), massiv gedruckt also rund 230 g PLA. Mit Füllung ist es weniger.") +
    P("**Serie:** Der größte Kostenblock sind die neun fertigen Reader-Module. Die anfangs verworfene Idee einer eigenen Platine mit integrierten Antennen wäre in Stückzahlen der Weg zu niedrigeren Kosten und einer flacheren Bauform. "
      "Das Gehäuse würde in der Serie im Spritzguss gefertigt. [[Serienkosten, Verkaufspreis, Marge abschätzen]]") +
    P("[[Ideen zur Finanzierung des Ramp-Ups ergänzen, z. B. Crowdfunding in der Maker-Community]]"))

C["service"] = (
    B("Behälter als Zubehör verkaufen oder als Druckdatei bereitstellen, Tags zum Nachrüsten",
      "Einfache Kalibrierung (Tara) durch den Nutzer",
      "[[App, Updates, Support ergänzen]]"))

C["fazit"] = (
    P("[[Abgleich mit den Zielen aus 1.2, sobald Tests vorliegen]]") +
    P("Für ein kommerzielles Produkt wären unter anderem nötig:") +
    B("Material für Lebensmittelkontakt und Reinigung in der Küche (der Prototyp ist aus PLA gedruckt),",
      "Kostensenkung durch eine eigene Platine statt Einzelmodulen,",
      "Funkzulassung und CE-Kennzeichnung,",
      "verlässliche Erkennung und Wägung im Dauerbetrieb, nachgewiesen durch Tests,",
      "[[weitere Punkte der Gruppe]]"))

# ---------------- in die Vorlage einfuegen ----------------
dp = os.path.join(W, "word/document.xml"); x = open(dp, encoding="utf-8").read()
b0 = x.find("<w:body>") + len("<w:body>"); b1 = x.find("</w:body>")
body = x[b0:b1]
ps = re.findall(r"<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>|<w:sectPr.*?</w:sectPr>", body, flags=re.S)
assert "".join(ps) == body, "Body nicht vollstaendig zerlegt"
def text(p): return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
def grey(p):
    p = re.sub(r"<w:r( [^>]*)?><w:rPr>", lambda m: "<w:r%s><w:rPr><w:i/><w:color w:val=\"7F7F7F\"/>" % (m.group(1) or ""), p)
    return re.sub(r"<w:r( [^>]*)?>(?!<w:rPr>)", lambda m: "<w:r%s><w:rPr><w:i/><w:color w:val=\"7F7F7F\"/></w:rPr>" % (m.group(1) or ""), p)
GUIDE = ("Bezug zum Smart Navigator", "Wie wird Wert geschaffen", "Smart Navigator – Uniqueness", "Was wird im Projekt dazu", "Smart Navigator – Enabler",
         "Produkt und Vernetzung: Wie", "In welche Arbeitpakete", "Wie haben Sie sich im Team", "Wie haben Sie die Zeitschiene", "Wo und warum wurden",
         "Beschreibung des Business", "Abgleich mit den initial", "Was muss passieren")
AFTER = [("Wie wird Wert geschaffen", "value", 1), ("Was wird im Projekt dazu", "ziel", 2), ("Produkt und Vernetzung: Wie", "vorgehen", 2),
         ("In welche Arbeitpakete", "wbs", 1), ("Wie haben Sie sich im Team", "obs", 1), ("Wie haben Sie die Zeitschiene", "plan", 1), ("Wo und warum wurden", "agil", 1),
         ("Produkt und Vernetzung", "produkt", 1), ("Technologie und Daten", "techdaten", 1), ("Sensors & Input", "sensors", 1), ("Connectivity", "conn", 1),
         ("Data Analytics", "data", 1), ("Output & Actuators", "output", 1), ("Organisation und Management", "orga", 1), ("Menschen & Kultur", "menschen", 1),
         ("Beschreibung des Business", "business", 1), ("Service & Unterstützung", "service", 1), ("Was muss passieren", "fazit", 1)]
used = set(); new = []; pending = []
for idx, p in enumerate(ps):
    t = text(p).replace("&amp;", "&")
    if t.startswith("Datum:"): p = P("Datum: [[Abgabedatum]]")
    elif t.startswith("Gruppe:"): p = P("Gruppe: Gruppe 1 – GridScale – Die intelligente Wiegematte [[prüfen]]")
    elif t.startswith("Teilnehmer:"): p = P("Teilnehmer: [[Namen]]")
    elif t.startswith("Smart Systems") and idx == 0: new.append(p); new.append(C["hinweis"]); continue
    if any(t.startswith(g) for g in GUIDE): p = grey(p)
    new.append(p)
    for key, name, skip in AFTER:
        if name not in used and t.startswith(key) and not t.startswith("Produkt und Vernetzung:") or (name == "vorgehen" and name not in used and t.startswith(key)):
            if name == "produkt" and "Heading2" not in p: continue
            # Inhalt nach dem Leitfragen-Absatz bzw. nach dem folgenden Bild einfuegen
            pending.append([name, skip]); used.add(name); break
    for q in pending:
        q[1] -= 1
    while pending and pending[0][1] <= 0:
        new.append(C[pending.pop(0)[0]])
assert not pending, pending
missing = set(n for _, n, _ in AFTER) - used
assert not missing, missing
x = x[:b0] + "".join(new) + x[b1:]
open(dp, "w", encoding="utf-8").write(x)
if os.path.exists(OUT): os.remove(OUT)
zf = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
ct = "[Content_Types].xml"; zf.write(os.path.join(W, ct), ct)
for root, dirs, files in os.walk(W):
    for f in files:
        full = os.path.join(root, f); arc = os.path.relpath(full, W)
        if arc != ct: zf.write(full, arc)
zf.close()
print("OK", OUT, "eingefuegt:", sorted(used))
