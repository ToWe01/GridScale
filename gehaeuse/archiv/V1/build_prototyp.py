# -*- coding: utf-8 -*-
"""
Gehaeuse-Prototyp Kuechenregalboden 15x15 cm (FreeCAD, in der GUI per MCP-Bridge ausfuehren).
Baut Unterteil, Oberteil (Gridfinity-Profil 50 mm) und Referenzteile neu auf, schreibt
Parametertabelle (mit Status/Quelle) und Pruefbericht ins Dokument und speichert nach cad/.
Status der Parameter: bestaetigt | Norm | Annahme | PLATZHALTER (muss gemessen werden)
"""
import os, math, Part
from FreeCAD import Vector as V

# Variante: "einteilig" = Oberteil aus einem Stueck (M4-Koepfe am Freiende sichtbar im Gridfinity-Steg)
#           "deckel"    = Traeger (an Zellen geschraubt) + aufgesetzter Gridfinity-Deckel, Schrauben verdeckt
# Vor dem exec setzen: VARIANT = "einteilig"; ohne Angabe "deckel" (vom Nutzer gewaehlt, 2026-11-23).
VARIANT = globals().get("VARIANT", "deckel")
assert VARIANT in ("einteilig", "deckel"), VARIANT
SUFFIX = "" if VARIANT == "einteilig" else "_Deckel"

PARAMS = [
    # Name, Wert, Status, Quelle/Hinweis
    ("MOD", 150.0, "Annahme", "Projektvorgabe 15x15 cm, Modulraster"),
    ("PLATE", 148.5, "Annahme", "0,75 mm Luft je Seite zum Nachbarmodul"),
    ("FLOOR", 2.4, "Annahme", "Boden Unterteil, PLA"),
    ("PED", 5.0, "Annahme", "Sockel unter Zellen-Festende = Luft unter Zelle am Freiende; Platz fuer versenkten M4-Kopf DIN 912 + Scheibe"),
    ("CELL_L", 75.0, "bestaetigt", "Adafruit 4541 Produktseite: 75,0 x 12,7 x 12,7 mm (Strain Gauge Load Cell 5 kg)"),
    ("CELL_W", 12.7, "bestaetigt", "Adafruit 4541, Shop"),
    ("CELL_H", 12.7, "bestaetigt", "Adafruit 4541, Shop"),
    ("CELL_HOLE_END", 5.5, "bestaetigt", "Adafruit 4541 Zeichnung: 75 = 5,5 + 10 + 44 + 10 + 5,5 (abgeleitet)"),
    ("CELL_HOLE_PITCH", 10.0, "bestaetigt", "Adafruit 4541 Zeichnung: je Ende 2 Loecher, 10 mm Abstand"),
    ("CELL_SCREW_D", 4.0, "bestaetigt", "Adafruit 4541 Zeichnung: 4x M4"),
    ("PED_L", 22.0, "Annahme", "Laenge Sockel am Festende (deckt beide Loecher ab)"),
    ("M4_HEAD_CB", 9.5, "Annahme", "Senkung fuer Scheibe DIN 125 M4 (D 9,0) unter M4 DIN 912 (Kopf D 7,0); beide Senkungen zu Langloch verbunden"),
    ("WASHER_T", 0.8, "Norm", "Scheibe DIN 125 M4, Dicke 0,8: halbiert Flaechenpressung auf PLA (Kriechen)"),
    ("M4_CB_DEPTH", 5.0, "Annahme", "Senktiefe von unten: Kopf 4,0 + Scheibe 0,8 + 0,2 versenkt; Rest-PLA bis Zelle = FLOOR+PED-M4_CB_DEPTH"),
    ("M4_CLR", 4.6, "Annahme", "Durchgangsloch M4 in der Platte am Freiende (Schraube von oben ins Zellengewinde)"),
    ("M4_TOP_CB", 7.4, "Annahme", "Senkung von oben fuer M4 DIN 912 (Kopf D 7,0) im Steg zwischen zwei Gridfinity-Feldern"),
    ("HEAD_BELOW_GF", 0.0, "Annahme", "Kopfoberkante so weit unter dem Gridfinity-Taschenboden (0 = buendig, Behaelter beruehren den Kopf nicht)"),
    ("COVER_FLOOR", 0.6, "Annahme", "Variante deckel: Boden des Gridfinity-Deckels (3 Schichten); Traegerhaut = SKIN - COVER_FLOOR"),
    ("COVER_PIN_D", 3.8, "Annahme", "Variante deckel: gedruckte Zentrierzapfen am Deckel (4x auf den x-Stegen)"),
    ("COVER_PIN_HOLE", 4.0, "Annahme", "Variante deckel: Bohrung im Traeger fuer Zentrierzapfen (0,1 radial, druckt enger)"),
    ("COVER_PIN_L", 2.5, "Annahme", "Variante deckel: Zapfenlaenge, Bohrung 0,5 tiefer"),
    ("COVER_SEAM_CH", 0.3, "Annahme", "Variante deckel: Fase an beiden Kanten der Trennfuge Traeger/Deckel"),
    ("M4_LEN", 12.0, "Norm", "Einheitliche Schraube M4x12 DIN 912 an Fest- und Freiende (Nutzervorgabe: nur Standard-M4)"),
    ("FREE_CONTACT", 5.0, "Annahme", "Auflage Platte auf Zelle: Freiende-Loecher +- 5 mm"),
    ("CLR_TOP", 0.8, "Annahme", "Freistich in Plattenunterseite ueber Zelle (ausser Auflage am Freiende)"),
    ("PN_L", 42.7, "bestaetigt", "Elechouse PN532 NFC RFID Module User Guide V3 (Hersteller): 42,7 x 40,4 x 4 mm; 2 Befestigungsloecher diagonal"),
    ("PN_W", 40.4, "bestaetigt", "Elechouse User Guide V3 (bemasstes Foto S. 2)"),
    ("PN_T", 7.0, "Annahme", "Nutzerangabe: PN532 mit abgewinkelten Dupont-Pins etwa 7 mm hoch (gemessen ca.)"),
    ("PN_CLR", 0.3, "Annahme", "Spiel je Seite in der Tasche (Reibsitz)"),
    ("PN_DEPTH", 7.5, "Annahme", "PN_T 7,0 + 0,5 Luft; Pin-Seite/Richtung noch offen"),
    ("SKIN", 1.6, "Annahme", "Taschenboden ueber der Antenne"),
    ("GF_TOP", 49.6, "Annahme", "Gridfinity-Profil, auf 50-mm-Raster skaliert"),
    ("GF_C1", 2.15, "Annahme", "Gridfinity-Profil Fase oben"),
    ("GF_V", 1.8, "Annahme", "Gridfinity-Profil senkrecht"),
    ("GF_C2", 0.8, "Annahme", "Gridfinity-Profil Fase unten"),
    ("STOP_GAP", 0.5, "Annahme", "Ueberlastspalt (haengt an Durchbiegung der Zelle, messen)"),
    ("POST_D", 6.0, "Annahme", "Anschlagsockel mit Stiftaufnahme"),
    ("PIN_D", 3.0, "Annahme", "Gedruckter Zapfen auf Anschlagsockel (ersetzt Gewindestift, kein Normteil)"),
    ("PIN_HOLE", 4.0, "Annahme", "Bohrung in Platte, 0,5 mm radial: Stift faengt nur Kippen, keine Fuehrung (kein Kraftnebenschluss)"),
    ("NUB_H", 3.5, "Annahme", "Zapfenhoehe ueber Sockel, Eingriff in Platte = NUB_H - STOP_GAP"),
    ("PIN_HOLE_DEPTH", 5.0, "Annahme", "Tiefe Sackloch in Platte (Luft ueber Zapfen)"),
    ("ANTIROT_T", 1.5, "Annahme", "Verdrehsicherung Wanddicke, wie Handout"),
    ("ANTIROT_CLR", 0.3, "Annahme", "Spiel zur Zelle (PLA druckt enger)"),
    ("ANTIROT_H", 4.0, "Annahme", "Hoehe ueber Zellenunterkante"),
    ("BRD_CLR", 0.4, "Annahme", "Spiel Board zu Fuehrungswaenden (ESP32)"),
    ("BRD_WALL", 1.2, "Annahme", "Fuehrungswand ESP32 (3 Perimeter)"),
    ("HDR_PLASTIC", 2.5, "Norm", "Stiftleiste RM 2,54: Kunststoffkoerper unter der Platine (Pins nach unten, Nutzer)"),
    ("HDR_PIN_BELOW", 6.0, "Norm", "Stiftleiste: Pinlaenge unter dem Kunststoff (Standard 11,5 gesamt)"),
    ("HDR_PIN_ABOVE", 1.4, "Norm", "Stiftleiste: Pinende ueber der Platinenoberseite (3,0 - 1,6)"),
    ("BRD_POST", 9.0, "Annahme", "Abstand Boden - Platinenunterseite: Kunststoff 2,5 + Pin 6,0 + 0,5 Luft"),
    ("HX_HOLE", 3.302, "bestaetigt", "SparkFun Eagle .brd: 4x STAND-OFF Bohrung 3,302 bei (2,54|2,54) (27,94|2,54) (2,54|20,32) (27,94|20,32)"),
    ("HX_STANDOFF_D", 4.2, "Annahme", "Stuetze unter HX711-Loch, 0,6 mm Schulter um Zapfen; Luft zur Stiftleiste JP4/J1 siehe Bericht"),
    ("HX_NUB_D", 2.5, "Annahme", "Gedruckter Zentrierzapfen im HX711-Loch, 0,4 mm radial (druckt dicker), nicht angeschmolzen"),
    ("TCA_HOLE", 2.5, "bestaetigt", "Adafruit Eagle .brd: 2x Montageloch 2,5 auf der Mittellinie, 2,54 vom Ende"),
    ("TCA_STANDOFF_D", 4.0, "Annahme", "Stuetze unter TCA-Loch, schlank: >= 0,5 mm Luft zum Rasthaken-Arm am Ende"),
    ("TCA_NUB_D", 1.8, "Annahme", "Gedruckter Zentrierzapfen im TCA-Loch, 0,35 mm radial, nicht angeschmolzen"),
    ("NUB_STAKE", 0.8, "Annahme", "Zapfenueberstand ueber Platine (nur Zentrierung)"),
    ("HX_HOOK_W", 6.0, "Annahme", "Rasthaken HX711 an beiden Langseiten (dort keine Stiftleiste), Mitte x = 15,24"),
    ("TCA_HOOK_W", 4.0, "Annahme", "Rasthaken TCA9548A an beiden kurzen Enden zwischen den Stiftleisten, greift auf den Lochring"),
    ("ESP_PIN_USB", 12.125, "bestaetigt", "Espressif Dimensions-PDF v1.2: letzter Pin 12,125 vom USB-Ende, 2x16 Pins RM 2,54, Reihen 1,27 vom Rand"),
    ("ESP_ANT_OVER", 6.35, "bestaetigt", "Espressif Dimensions-PDF v1.2: Modul-Antenne ragt 6,35 ueber das Board, Breite 18,0"),
    ("ESP_MOD_H", 3.2, "Annahme", "Hoehe Modul ESP32-C6-WROOM-1 ueber Platine (Datenblatt-Zeichnung nicht lesbar, Wert eher etwas zu hoch = sichere Seite)"),
    ("ESP_MOD_L", 19.2, "Annahme", "Modullaenge auf der Platine (ohne Ueberstand), aus Zeichnung abgegriffen"),
    ("ESP_USB_H", 3.3, "Annahme", "Hoehe USB-C-Buchsen ueber Platine"),
    ("ESP_ANT_T", 0.8, "Annahme", "Dicke Antennenueberstand (Modulplatine WROOM-1); Datenblatt-Seitenansicht nennt 0,8 (Zeichnungstext unvollstaendig lesbar) - nachmessen"),
    ("HOOK_T", 1.2, "Annahme", "Rasthaken ESP32: Armdicke (Biegerichtung), Dehnung siehe Pruefbericht"),
    ("HOOK_OVER", 0.5, "Annahme", "Rasthaken: Ueberdeckung der Nase ueber Platinen- bzw. Antennenkante"),
    ("HOOK_CLR", 0.2, "Annahme", "Rasthaken: Spiel Arm zu Platinenkante und Nase ueber Platinenoberseite (0,1)"),
    ("ESP_HOOK_X", 9.1, "Annahme", "Mitte Rasthaken Langseite vom USB-Ende: Luecke USB-Buchse (bis 7,4) - Stiftleiste (ab 10,86)"),
    ("ESP_HOOK_W", 2.0, "Annahme", "Breite Rasthaken Langseite (Luecke nur 3,45 mm)"),
    ("ANT_HOOK_W", 6.0, "Annahme", "Breite Rasthaken ueber dem Antennenueberstand"),
    ("BRD_T", 1.6, "Annahme", "Platinendicke"),
    ("ESP_X", 51.8, "bestaetigt", "Espressif Dimensions-PDF v1.2 (Laenge)"),
    ("ESP_Y", 25.4, "bestaetigt", "Espressif Dimensions-PDF v1.2 (Breite)"),
    ("HX_X", 30.48, "bestaetigt", "SparkFun Eagle .brd, Umriss Layer 20"),
    ("HX_Y", 22.86, "bestaetigt", "SparkFun Eagle .brd, Umriss Layer 20"),
    ("TCA_X", 30.48, "bestaetigt", "Adafruit Eagle .brd, Umriss (Laenge); Produktseite 2717: 30,6 x 17,6 x 2,7 mm (gerundet, passt)"),
    ("TCA_Y", 17.78, "bestaetigt", "Adafruit Eagle .brd, Umriss (Breite)"),
    ("USB_W", 21.5, "Annahme", "Delock 87824 Einbauoeffnung ca. 21,5 mm (Herstellerseite 'ca.', laengs der Wand)"),
    ("USB_H", 12.5, "Annahme", "Delock 87824 Einbauoeffnung ca. 12,5 mm (Herstellerseite 'ca.', Hoehe)"),
    ("USB_SCREW_SP", 28.0, "bestaetigt", "Delock 87824 Lochabstand 28 mm (Herstellerseite; passt zur Zeichnung 87824_draw_2.pdf: Flansch 36, Augen D6)"),
    ("USB_FL_L", 36.0, "bestaetigt", "Delock-Zeichnung: Flansch 36 +-0,3 lang (laengs der Wand)"),
    ("USB_FL_W", 12.0, "bestaetigt", "Delock-Zeichnung: Flansch 12 +-0,3 breit (Hoehe)"),
    ("USB_FL_HOLE", 3.2, "bestaetigt", "Delock-Zeichnung: Bohrung D3,20 im Flansch (Durchgang M3), Auge D6,00"),
    ("USB_LEN", 31.0, "bestaetigt", "Delock-Zeichnung: Buchse 31 +-0,3 von Stirnflaeche bis Ende Knickschutz"),
    ("USB_FL_T", 5.5, "Annahme", "Flanschdicke, aus Zeichnung abgegriffen (nicht bemasst)"),
    ("USB_BOSS_L", 21.0, "Annahme", "Vorstehender Kragen vorn mit Buchse, steckt im Ausschnitt; aus Zeichnung abgegriffen (~21-23)"),
    ("USB_BOSS_T", 1.8, "Annahme", "Kragen steht ca. 1,8 vor dem Flansch (abgegriffen) -> Wand an der Buchse so duenn, dass Stirnflaeche buendig"),
    ("USB_BODY_W", 13.0, "Annahme", "Gehaeuse hinter dem Flansch ca. 13 x 9 (abgegriffen)"),
    ("USB_BODY_H", 9.0, "Annahme", "Gehaeuse hinter dem Flansch, Hoehe (abgegriffen)"),
    ("USB_STRAIN_D", 7.0, "Annahme", "Knickschutz ca. D7 x 6 (abgegriffen), Kabel-AD 4,3 (Zeichnung Stueckliste)"),
    ("PLUG_L", 39.0, "bestaetigt", "Delock-Zeichnung: Stecker P1 Umspritzung 39 +-0,3, Metall 6,65"),
    ("PLUG_W", 12.2, "bestaetigt", "Delock-Zeichnung: Stecker P1 12,2 +-0,3 breit"),
    ("PLUG_T", 6.5, "bestaetigt", "Delock-Zeichnung: Stecker P1 max. 6,5 dick"),
    ("USB_Z0", 0.2, "Annahme", "Unterkante Ausschnitt ueber Boden (Restwand oben ~1,2 mm, pruefen)"),
    ("USB_WALL_L", 40.0, "Annahme", "Laenge der USB-Wand, damit Schraubenloecher Material haben"),
    ("USB_SCREW_D", 2.5, "PLATZHALTER", "Schraubenloch Einbaubuchse"),
    ("WALL", 4.0, "Annahme", "Verstaerkung innen an USB- und Verbinderwand"),
    ("SHELL_T", 2.0, "Annahme", "Umlaufende Aussenwand Unterteil (5 Perimeter), geschlossenes Gehaeuse"),
    ("CORNER_R", 4.0, "Annahme", "Eckradius senkrechte Aussenkanten beider Teile (Aussenmass 148,5 bleibt)"),
    ("GAP_V", 1.2, "Annahme", "Senkrechte Luft Kragen - Plattenunterseite und Schuerze - Schulter (sichtbare Fuge); > max. Eckabsenkung bis Anschlag"),
    ("SKIRT_H", 3.0, "Annahme", "Schuerze am Oberteil ragt so weit ueber das Unterteil (Staubschutz, Fuge zeigt nach unten); begrenzt durch USB-Ausschnitt"),
    ("SKIRT_T", 1.6, "Annahme", "Wanddicke Schuerze (4 Perimeter)"),
    ("SKIRT_CLR", 0.6, "Annahme", "Waagerechte Luft Schuerze - Kragen; > seitliches Spiel der Platte (Zapfen 0,5)"),
    ("COLLAR_T", 1.6, "Annahme", "Wanddicke Kragen am Unterteil, Uebergang innen 45 Grad (kein Ueberhang)"),
    ("EDGE_CH_BOT", 0.6, "Annahme", "Fase Unterkante Unterteil aussen (Elefantenfuss, Optik)"),
    ("EDGE_CH_GAP", 0.4, "Annahme", "Fase an beiden Kanten der Schattenfuge (V-Fuge, Elefantenfuss Oberteil)"),
    ("ENGRAVE_D", 0.4, "Annahme", "Gravurtiefe Schriftzug Unterseite"),
    ("CONN_W", 14.0, "PLATZHALTER", "Fenster fuer spaeteren Modulverbinder, Breite (im Prototyp NICHT ausgeschnitten, Wand geschlossen)"),
    ("CONN_H", 8.0, "PLATZHALTER", "Fenster fuer spaeteren Modulverbinder, Hoehe (im Prototyp NICHT ausgeschnitten)"),
]
P = {k: v for k, v, _, _ in PARAMS}
FLOOR = P['FLOOR']; PED = P['PED']; CH = P['CELL_H']
Z_CELL = FLOOR + PED
Z_UP = Z_CELL + CH   # Platte liegt direkt auf dem Zellen-Freiende (keine Auflage-Noppen -> Oberteil flach druckbar)
GF_H = P['GF_C1'] + P['GF_V'] + P['GF_C2']
T_UP = P['PN_DEPTH'] + P['SKIN'] + GF_H
Z_TOP = Z_UP + T_UP
OFF = (P['MOD'] - P['PLATE']) / 2.0
Z_SPLIT = Z_UP + P['PN_DEPTH'] + P['SKIN'] - P['COVER_FLOOR']   # Trennebene Traeger/Deckel (nur Variante deckel)
if VARIANT == "einteilig":
    Z_HEAD_SEAT = Z_TOP - GF_H - P['HEAD_BELOW_GF'] - 4.0   # Auflage M4-Kopf (DIN 912, Kopfhoehe 4,0) am Freiende
else:
    Z_HEAD_SEAT = Z_SPLIT - 4.0                             # Kopf buendig mit Traegeroberseite, Deckel verdeckt ihn
COVER_PINS = [(50, 25), (100, 25), (50, 125), (100, 125)]   # auf den x-Stegen, weg von Schrauben und Anschlagzapfen

def box(x, y, z, dx, dy, dz): return Part.makeBox(dx, dy, dz, V(x, y, z))
def rbox(x, y, z, dx, dy, dz, r):
    b = Part.makeBox(dx, dy, dz, V(x, y, z))
    ed = [e for e in b.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    return b.makeFillet(r, ed) if r > 0 else b
def footprint(inset, z0, h):
    """Gerundeter Grundriss des Moduls (Aussenmass PLATE), nach innen versetzt um inset."""
    return rbox(OFF + inset, OFF + inset, z0, P['PLATE'] - 2*inset, P['PLATE'] - 2*inset, h, max(P['CORNER_R'] - inset, 0.5))
def chamfer_z(shape, z, d):
    ed = [e for e in shape.Edges if abs(e.BoundBox.ZMin - z) < 1e-6 and abs(e.BoundBox.ZMax - z) < 1e-6]
    return shape.makeChamfer(d, ed)
def cyl(x, y, z, d, h, axis=V(0, 0, 1)): return Part.makeCylinder(d / 2.0, h, V(x, y, z), axis)
def frustum(cx, cy, z0, a_bot, a_top, h):
    def sq(a, z):
        h2 = a / 2.0
        return Part.makePolygon([V(cx-h2, cy-h2, z), V(cx+h2, cy-h2, z), V(cx+h2, cy+h2, z), V(cx-h2, cy+h2, z), V(cx-h2, cy-h2, z)])
    return Part.makeLoft([sq(a_bot, z0), sq(a_top, z0 + h)], True)

DOCNAME = "Kuechenregalboden_Prototyp" + SUFFIX
doc = App.ActiveDocument if (App.ActiveDocument and App.ActiveDocument.Name == DOCNAME) else App.newDocument(DOCNAME)
for o in list(doc.Objects): doc.removeObject(o.Name)

cx0 = P['MOD'] / 2.0 - P['CELL_L'] / 2.0
def hole_xs(left):
    e, p, L_ = P['CELL_HOLE_END'], P['CELL_HOLE_PITCH'], P['CELL_L']
    return ([cx0 + e, cx0 + e + p] if left else [cx0 + L_ - e - p, cx0 + L_ - e])
cells = [dict(y=50.0, fixed_xs=hole_xs(True), free_xs=hole_xs(False), fixed_left=True),
         dict(y=100.0, fixed_xs=hole_xs(False), free_xs=hole_xs(True), fixed_left=False)]

# ---------------- UNTERTEIL ----------------
# Labyrinth gegen Staub: Aussenwand bis zur Schulter, darueber ein zurueckgesetzter Kragen, ueber den die Schuerze des Oberteils greift
Z_WALL = Z_UP - P['GAP_V']                         # Oberkante Kragen
Z_SHOULDER = Z_UP - P['SKIRT_H'] - P['GAP_V']      # Schulter = Unterkante der sichtbaren Fuge
C_OUT = P['SKIRT_T'] + P['SKIRT_CLR']; C_IN = C_OUT + P['COLLAR_T']
def outline(inset, z):
    f = footprint(inset, z, 1.0)
    return [fc for fc in f.Faces if abs(fc.BoundBox.ZMax - z) < 1e-6 and abs(fc.BoundBox.ZMin - z) < 1e-6][0].OuterWire
shell = chamfer_z(chamfer_z(footprint(0, 0, Z_SHOULDER), 0, P['EDGE_CH_BOT']), Z_SHOULDER, P['EDGE_CH_GAP'])
collar = chamfer_z(footprint(C_OUT, Z_SHOULDER - 0.5, Z_WALL - Z_SHOULDER + 0.5), Z_WALL, P['EDGE_CH_GAP'])
shell = shell.fuse(collar)
Z_TR = Z_SHOULDER - (C_IN - P['SHELL_T'])          # innen 45-Grad-Uebergang von Wand auf Kragen
inner = footprint(P['SHELL_T'], FLOOR, Z_TR - FLOOR)
inner = inner.fuse(Part.makeLoft([outline(P['SHELL_T'], Z_TR), outline(C_IN, Z_SHOULDER)], True))
inner = inner.fuse(footprint(C_IN, Z_SHOULDER - 0.01, Z_WALL - Z_SHOULDER + 1))
lower = shell.cut(inner).removeSplitter()   # geschlossene Wanne: Boden + umlaufende Wand + Kragen
antirot = []
for c in cells:
    px = cx0 if c['fixed_left'] else cx0 + P['CELL_L'] - P['PED_L']
    lower = lower.fuse(box(px, c['y'] - P['CELL_W']/2 - 1.0, FLOOR, P['PED_L'], P['CELL_W'] + 2.0, PED))
    # Verdrehsicherung: zwei Waende beidseitig der Zelle am Festende
    for s in (-1, 1):
        y0 = c['y'] + s * (P['CELL_W']/2 + P['ANTIROT_CLR']) - (P['ANTIROT_T'] if s < 0 else 0)
        w = box(px, y0, FLOOR, P['PED_L'], P['ANTIROT_T'], PED + P['ANTIROT_H'])
        antirot.append(w); lower = lower.fuse(w)
for c in cells:
    for hx in c['fixed_xs']:
        lower = lower.cut(cyl(hx, c['y'], -1, P['CELL_SCREW_D'] + 0.5, Z_CELL + 2))
        lower = lower.cut(cyl(hx, c['y'], -1, P['M4_HEAD_CB'], 1.0 + P['M4_CB_DEPTH']))
    xa_, xb_ = c['fixed_xs']   # Steg zwischen den Senkungen waere nur 0,5 mm -> Langloch
    lower = lower.cut(box(xa_, c['y'] - P['M4_HEAD_CB']/2, -1, xb_ - xa_, P['M4_HEAD_CB'], 1.0 + P['M4_CB_DEPTH']))
# Anschlagsockel mit Stiftaufnahme (Ueberlast + seitliche Fuehrung)
stops = [(50, 10), (100, 10), (50, 140), (100, 140)]
posts = []; nubs = []
Z_POST = Z_UP - P['STOP_GAP']
for (sx, sy) in stops:
    p = cyl(sx, sy, FLOOR, P['POST_D'], Z_POST - FLOOR)
    posts.append(p); lower = lower.fuse(p)
    nb = cyl(sx, sy, Z_POST - 0.1, P['PIN_D'], P['NUB_H'] + 0.1)   # gedruckter Zapfen statt Gewindestift
    nubs.append(nb); lower = lower.fuse(nb)

Z_B = FLOOR + P['BRD_POST']        # Platinenunterseite
Z_BT = Z_B + P['BRD_T']            # Platinenoberseite
PITCH = 2.54
# Boards in lokalen Koordinaten (Ursprung linke untere Ecke, x laengs). Quelle: Eagle .brd bzw. Espressif-PDF.
#  hdr: Stiftleisten als (x0, y0, dx, dy) Kunststoff-Grundflaeche; holes: (x, y, Bohrung, Stuetze, Zapfen)
esp_pin_x0 = P['ESP_PIN_USB'] - PITCH/2; esp_pin_len = 16 * PITCH
BOARD_TYPES = {
    "ESP32": dict(bx=P['ESP_X'], by=P['ESP_Y'], holes=[],
                  hdr=[(esp_pin_x0, 0, esp_pin_len, PITCH), (esp_pin_x0, P['ESP_Y'] - PITCH, esp_pin_len, PITCH)]),
    "HX711": dict(bx=P['HX_X'], by=P['HX_Y'],
                  holes=[(x, y, P['HX_HOLE'], P['HX_STANDOFF_D'], P['HX_NUB_D']) for x in (2.54, 27.94) for y in (2.54, 20.32)],
                  hdr=[(0, 5.08, PITCH, 5*PITCH), (P['HX_X'] - PITCH, 5.08, PITCH, 5*PITCH), (20.32, 7.62, PITCH, 2*PITCH)]),   # JP4, J1, JP2 (JP2 bestueckt: Annahme)
    "TCA9548A": dict(bx=P['TCA_X'], by=P['TCA_Y'],
                  holes=[(x, 8.89, P['TCA_HOLE'], P['TCA_STANDOFF_D'], P['TCA_NUB_D']) for x in (2.54, 27.94)],
                  hdr=[(0, 0, P['TCA_X'], PITCH), (0, P['TCA_Y'] - PITCH, P['TCA_X'], PITCH)]),
}
boards = [("ESP32_C6", "ESP32", 75, 75), ("HX711_A", "HX711", 24, 24), ("HX711_B", "HX711", 76, 24),
          ("TCA9548A_A", "TCA9548A", 24, 126), ("TCA9548A_B", "TCA9548A", 76, 126)]
def org(t, cx, cy): return cx - BOARD_TYPES[t]['bx']/2, cy - BOARD_TYPES[t]['by']/2

def snap_hook(ex, ey, n, wv, w, z_catch):
    """Gedruckter Rasthaken, steht auf dem Boden. (ex, ey): Punkt auf der Kante, die gehalten wird;
    n: Einheitsvektor nach innen (ueber die Kante), wv: Breitenrichtung; z_catch: Oberkante des gehaltenen Teils."""
    clr, t, ov = P['HOOK_CLR'], P['HOOK_T'], P['HOOK_OVER']
    zc = z_catch + 0.1; zn = zc + 0.3; ztop = zn + (ov + clr)          # 45-Grad-Einlaufschraege
    def pt(u, z): return V(ex + u*n.x, ey + u*n.y, z)
    arm = Part.Face(Part.makePolygon([pt(-clr - t, FLOOR - 0.1), pt(-clr, FLOOR - 0.1), pt(-clr, zc), pt(ov, zc), pt(ov, zn),
                                      pt(-clr, ztop), pt(-clr - t, ztop), pt(-clr - t, FLOOR - 0.1)]))
    return arm.extrude(V(wv.x * w, wv.y * w, 0)), (zc - FLOOR)          # Form, freie Armlaenge
hooks = []

board_support = []
for (n, t, cx, cy) in boards:
    bt = BOARD_TYPES[t]; ox, oy = org(t, cx, cy)
    for (hx_, hy_, hd, sd, nd) in bt['holes']:       # Stuetze + gedruckter Zapfen durch das Montageloch
        st = cyl(ox + hx_, oy + hy_, FLOOR - 0.1, sd, P['BRD_POST'] + 0.1)
        st = st.fuse(cyl(ox + hx_, oy + hy_, Z_B - 0.1, nd, P['BRD_T'] + P['NUB_STAKE'] + 0.1))
        board_support.append(st); lower = lower.fuse(st)
    # Rasthaken gegen Abheben (Zapfen zentrieren nur)
    new_hooks = []
    if t == "HX711":
        hw = P['HX_HOOK_W']
        for (ey, nv) in ((oy, V(0, 1, 0)), (oy + bt['by'], V(0, -1, 0))):
            hk, Lh = snap_hook(cx - hw/2, ey, nv, V(1, 0, 0), hw, Z_BT); new_hooks.append((n + " Langseite", n, hk, Lh))
    if t == "TCA9548A":
        hw = P['TCA_HOOK_W']
        for (ex, nv) in ((ox, V(1, 0, 0)), (ox + bt['bx'], V(-1, 0, 0))):
            hk, Lh = snap_hook(ex, cy - hw/2, nv, V(0, 1, 0), hw, Z_BT); new_hooks.append((n + " Ende", n, hk, Lh))
    for h_ in new_hooks:
        hooks.append(h_); board_support.append(h_[2]); lower = lower.fuse(h_[2])
    if t == "ESP32":
        bx, by = bt['bx'], bt['by']; clr = P['BRD_CLR']; w = P['BRD_WALL']; hg = P['BRD_POST'] + 1.4
        # Auflagen unter der Platinenmitte (ausserhalb der Stiftleisten und USB-Beinchen)
        for (x0, y0, dx, dy) in [(2.0, 10.0, 6.0, 5.4), (44.0, 6.0, 6.0, 13.4)]:
            pad = box(ox + x0, oy + y0, FLOOR - 0.1, dx, dy, P['BRD_POST'] + 0.1); board_support.append(pad); lower = lower.fuse(pad)
        # Fuehrungswaende an den Stirnseiten bis 0,2 unter Platinenoberseite (Antennenueberstand liegt darueber)
        for (x0, y0, dy) in [(-clr - w, 10.5, 4.4), (bx + clr, 6.0, 13.4)]:
            wl = box(ox + x0, oy + y0, FLOOR - 0.1, w, dy, hg + 0.1); board_support.append(wl); lower = lower.fuse(wl)
        # Seitenfuehrung am USB-Ende (dort keine Stiftleiste), endet 1 mm vor dem Rasthaken
        hx0 = P['ESP_HOOK_X'] - P['ESP_HOOK_W']/2
        for y0 in (-clr - w, by + clr):
            wl = box(ox + 2.0, oy + y0, FLOOR - 0.1, hx0 - 1.0 - 2.0, w, hg + 0.1); board_support.append(wl); lower = lower.fuse(wl)
        # Rasthaken statt Kabelbinder: 2x Langseite am USB-Ende (greift ueber Platinenkante), 1x ueber den Antennenueberstand
        for (ey, n_) in ((oy, V(0, 1, 0)), (oy + by, V(0, -1, 0))):
            hk, Lh = snap_hook(ox + hx0, ey, n_, V(1, 0, 0), P['ESP_HOOK_W'], Z_BT); hooks.append((n + " Langseite", n, hk, Lh))
        ax0 = ox + bx + P['ESP_ANT_OVER']
        hk, Lh = snap_hook(ax0, cy - P['ANT_HOOK_W']/2, V(-1, 0, 0), V(0, 1, 0), P['ANT_HOOK_W'], Z_BT + P['ESP_ANT_T']); hooks.append((n + " Antenne", n, hk, Lh))
        for (_, _, hk, _) in hooks[-3:]:
            board_support.append(hk); lower = lower.fuse(hk)

# Waende: links USB-C-Einbaubuchse, rechts Fenster fuer spaeteren Modulverbinder
wall_h = Z_WALL - FLOOR   # Innenverstaerkung buendig mit Aussenwand
lower = lower.fuse(box(OFF, 75-P['USB_WALL_L']/2, FLOOR, P['WALL'], P['USB_WALL_L'], wall_h))
zc = FLOOR + P['USB_Z0'] + P['USB_H']/2.0
lower = lower.cut(box(OFF-1, 75 - P['USB_W']/2, zc - P['USB_H']/2, P['WALL']+2, P['USB_W'], P['USB_H']))
# Flansch liegt INNEN an der Wand (Kragen steckt im Ausschnitt): Tasche in die Verstaerkung, Wand dort = Kragenhoehe
X_FL = OFF + P['USB_BOSS_T'] + 0.2   # Innenseite Wand = Anlage Flansch; Stirnflaeche 0,2 hinter der Aussenflaeche
lower = lower.cut(box(X_FL, 75 - P['USB_FL_L']/2 - 0.3, zc - P['USB_FL_W']/2 - 0.3, P['WALL'] + 1, P['USB_FL_L'] + 0.6, P['USB_FL_W'] + 0.6))
for sy in (-1, 1):
    lower = lower.cut(cyl(OFF-1, 75 + sy*P['USB_SCREW_SP']/2, zc, P['USB_SCREW_D'], P['WALL']+2, V(1, 0, 0)))
xr = OFF + P['PLATE'] - P['WALL']
lower = lower.fuse(box(xr, 75-14, FLOOR, P['WALL'], 28, wall_h))
# Verbinderfenster im Prototyp geschlossen (Verbinder noch nicht festgelegt); Verstaerkung bleibt zum spaeteren Einschneiden
# Verstaerkungen oberhalb der Schulter auf den Kragen zuruecknehmen (Platz fuer die Schuerze)
lower = lower.cut(footprint(0, Z_SHOULDER, Z_UP - Z_SHOULDER).cut(footprint(C_OUT, Z_SHOULDER - 1, Z_UP - Z_SHOULDER + 2)))
# Gravur auf der Unterseite (von unten lesbar -> in x gespiegelt); ohne Schrift wird sie uebersprungen
ENGRAVE_TXT = "SMART KITCHEN MAT  15x15  R3"
engrave_info = "keine"
try:
    font = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    ws = Part.makeWireString(ENGRAVE_TXT, font, 4.0, 0.3)
    faces = []
    for ch in ws:
        if ch: faces.append(Part.Face(Part.Wire(ch[0])) if len(ch) == 1 else Part.makeFace(ch, "Part::FaceMakerBullseye"))
    txt = faces[0].fuse(faces[1:]) if len(faces) > 1 else faces[0]
    bb = txt.BoundBox
    txt.translate(V(-bb.Center.x, -bb.Center.y, 0)); txt = txt.mirror(V(0, 0, 0), V(1, 0, 0))
    txt.translate(V(75, 128, -0.01))
    lower = lower.cut(txt.extrude(V(0, 0, P['ENGRAVE_D'] + 0.01)))
    engrave_info = "'%s' %.0fx%.0f mm, %.1f tief" % (ENGRAVE_TXT, bb.XLength, bb.YLength, P['ENGRAVE_D'])
except Exception as e_:
    engrave_info = "uebersprungen (%s)" % e_
lower = lower.removeSplitter()

# ---------------- OBERTEIL (Gridfinity 50 mm) ----------------
skirt = footprint(0, Z_UP - P['SKIRT_H'], P['SKIRT_H'] + 0.5).cut(footprint(P['SKIRT_T'], Z_UP - P['SKIRT_H'] - 1, P['SKIRT_H'] + 1))
skirt = chamfer_z(skirt, Z_UP - P['SKIRT_H'], P['EDGE_CH_GAP'])   # Fase aussen (V-Fuge) und innen (Einfuehrung)
upper = footprint(0, Z_UP, T_UP).fuse(skirt).removeSplitter()    # Platte mit umlaufender Schuerze nach unten
pw, pl = P['PN_L'] + 2*P['PN_CLR'], P['PN_W'] + 2*P['PN_CLR']
a0 = P['GF_TOP']; a1 = a0 - 2*P['GF_C1']; a2 = a1 - 2*P['GF_C2']
for i in range(3):
    for j in range(3):
        cx, cy = 25 + 50*i, 25 + 50*j
        upper = upper.cut(box(cx - pw/2, cy - pl/2, Z_UP, pw, pl, P['PN_DEPTH']))
        upper = upper.cut(frustum(cx, cy, Z_TOP - P['GF_C1'], a1, a0, P['GF_C1']))
        upper = upper.cut(box(cx - a1/2, cy - a1/2, Z_TOP - P['GF_C1'] - P['GF_V'], a1, a1, P['GF_V']))
        upper = upper.cut(frustum(cx, cy, Z_TOP - GF_H, a2, a1, P['GF_C2']))
def relief_x(c):
    """x-Bereich des Freistichs ueber der Zelle: alles ausser der Auflage am Freiende."""
    xa, xb = c['free_xs']
    if c['fixed_left']: return cx0 - 1.0, xa - P['FREE_CONTACT']
    return xb + P['FREE_CONTACT'], cx0 + P['CELL_L'] + 1.0
for c in cells:
    rx0, rx1 = relief_x(c)
    upper = upper.cut(box(rx0, c['y'] - P['CELL_W']/2 - 1.0, Z_UP - 0.1, rx1 - rx0, P['CELL_W'] + 2.0, P['CLR_TOP'] + 0.1))
    for hx in c['free_xs']:   # M4 DIN 912 von oben durch die Platte ins Zellengewinde, Kopf versenkt im Steg
        z_end = Z_TOP + 0.1 if VARIANT == "einteilig" else Z_SPLIT   # Deckel-Variante: endet an der Trennebene
        upper = upper.cut(cyl(hx, c['y'], Z_UP - 0.1, P['M4_CLR'], z_end - Z_UP + 0.1))
        upper = upper.cut(cyl(hx, c['y'], Z_HEAD_SEAT, P['M4_TOP_CB'], z_end - Z_HEAD_SEAT))
for (sx, sy) in stops:   # Sackloecher fuer die Zapfen (von unten, Oberflaeche bleibt glatt)
    upper = upper.cut(cyl(sx, sy, Z_UP - 0.1, P['PIN_HOLE'], P['PIN_HOLE_DEPTH'] + 0.1))
upper = upper.removeSplitter()

carrier = cover = None
if VARIANT == "deckel":
    # Trennen: Traeger unterhalb Z_SPLIT, Deckel darueber. Senkungen enden an der Trennebene, der Deckel bleibt geschlossen.
    big = P['MOD'] + 20
    carrier = upper.common(box(-10, -10, Z_UP - P['SKIRT_H'] - 1, big, big, Z_SPLIT - Z_UP + P['SKIRT_H'] + 1))
    cover = upper.common(box(-10, -10, Z_SPLIT, big, big, Z_TOP - Z_SPLIT + 1))
    cover = chamfer_z(cover.removeSplitter(), Z_SPLIT, P['COVER_SEAM_CH'])
    carrier = chamfer_z(carrier.removeSplitter(), Z_SPLIT, P['COVER_SEAM_CH'])
    for (px_, py_) in COVER_PINS:
        carrier = carrier.cut(cyl(px_, py_, Z_SPLIT - P['COVER_PIN_L'] - 0.5, P['COVER_PIN_HOLE'], P['COVER_PIN_L'] + 0.6))
        cover = cover.fuse(cyl(px_, py_, Z_SPLIT - P['COVER_PIN_L'], P['COVER_PIN_D'], P['COVER_PIN_L'] + 0.01))
    carrier = carrier.removeSplitter(); cover = cover.removeSplitter()
    upper = carrier.fuse(cover)   # fuer Spalt- und Bewegungschecks bewegen sich beide gemeinsam

# ---------------- Objekte ----------------
def add(name, shape, color=None, transp=0):
    o = doc.addObject("Part::Feature", name); o.Shape = shape
    if color and App.GuiUp:
        o.ViewObject.ShapeColor = color; o.ViewObject.Transparency = transp
    return o
add("Unterteil", lower, (0.75, 0.75, 0.78))
if VARIANT == "einteilig":
    add("Oberteil", upper, (0.55, 0.7, 0.9), 10)
else:
    add("Traeger", carrier, (0.55, 0.7, 0.9), 10)
    add("Deckel", cover, (0.25, 0.35, 0.5))
cell_shapes = {}
for k, c in enumerate(cells):
    cell = box(cx0, c['y'] - P['CELL_W']/2, Z_CELL, P['CELL_L'], P['CELL_W'], CH)
    for hx in c['fixed_xs'] + c['free_xs']:
        cell = cell.cut(cyl(hx, c['y'], Z_CELL - 1, P['CELL_SCREW_D'], CH + 2))
    cell_shapes[k] = cell
    add("REF_Waegezelle_%d" % (k+1), cell, (0.85, 0.65, 0.2))
board_refs = {}; pin_refs = []
for (n, t, cx, cy) in boards:
    bt = BOARD_TYPES[t]; ox, oy = org(t, cx, cy); bx, by = bt['bx'], bt['by']
    pcb = box(ox, oy, Z_B, bx, by, P['BRD_T'])
    for (hx_, hy_, hd, sd, nd) in bt['holes']:
        pcb = pcb.cut(cyl(ox + hx_, oy + hy_, Z_B - 1, hd, P['BRD_T'] + 2))
    parts = [pcb]
    for (x0, y0, dx, dy) in bt['hdr']:
        parts.append(box(ox + x0, oy + y0, Z_B - P['HDR_PLASTIC'], dx, dy, P['HDR_PLASTIC']))            # Kunststoff
        long_x = dx > dy; L_ = dx if long_x else dy
        pin = box(ox + x0 + (0 if long_x else dx/2 - 0.32), oy + y0 + (dy/2 - 0.32 if long_x else 0), Z_B - P['HDR_PLASTIC'] - P['HDR_PIN_BELOW'],
                  L_ if long_x else 0.64, 0.64 if long_x else L_, P['HDR_PIN_BELOW'])                     # Pinreihe unten
        top = box(pin.BoundBox.XMin, pin.BoundBox.YMin, Z_BT, pin.BoundBox.XLength, pin.BoundBox.YLength, P['HDR_PIN_ABOVE'])
        parts += [pin, top]; pin_refs.append(pin)
    if t == "ESP32":
        mw = 18.0
        parts.append(box(ox + bx - P['ESP_MOD_L'], cy - mw/2, Z_BT, P['ESP_MOD_L'], mw, P['ESP_MOD_H']))        # Modul mit Abschirmung
        parts.append(box(ox + bx, cy - mw/2, Z_BT, P['ESP_ANT_OVER'], mw, P['ESP_ANT_T']))                     # Antennenueberstand (blanke Modulplatine)
        for (y0, y1) in [(1.0, 9.7), (15.0, 23.8)]:                                                               # 2x USB-C am Ende x=0
            parts.append(box(ox - 0.5, oy + y0, Z_BT, 7.9, y1 - y0, P['ESP_USB_H']))
    shp = parts[0]
    for q in parts[1:]: shp = shp.fuse(q)
    board_refs[n] = shp
    add("REF_" + n, shp, (0.1, 0.5, 0.2))
for i in range(3):
    for j in range(3):
        add("REF_PN532_%d%d" % (i+1, j+1), box(25+50*i - P['PN_L']/2, 25+50*j - P['PN_W']/2, Z_UP + P['PN_DEPTH'] - P['PN_T'], P['PN_L'], P['PN_W'], P['PN_T']), (0.8, 0.1, 0.1))
# Delock 87824 nach Zeichnung: Kragen im Ausschnitt, Flansch innen an der Wand, Gehaeuse, Knickschutz
x_f = X_FL - P['USB_BOSS_T']
usb = box(x_f, 75 - P['USB_BOSS_L']/2, zc - (P['USB_H'] - 0.5)/2, P['USB_BOSS_T'], P['USB_BOSS_L'], P['USB_H'] - 0.5)
usb = usb.fuse(box(X_FL, 75 - P['USB_FL_L']/2, zc - P['USB_FL_W']/2, P['USB_FL_T'], P['USB_FL_L'], P['USB_FL_W']))
body_l = P['USB_LEN'] - P['USB_BOSS_T'] - P['USB_FL_T'] - 6.0
usb = usb.fuse(box(X_FL + P['USB_FL_T'], 75 - P['USB_BODY_W']/2, zc - P['USB_BODY_H']/2, body_l, P['USB_BODY_W'], P['USB_BODY_H']))
usb = usb.fuse(cyl(X_FL + P['USB_FL_T'] + body_l, 75, zc, P['USB_STRAIN_D'], 6.0, V(1, 0, 0)))
add("REF_USB_C_Buchse", usb, (0.2, 0.2, 0.2))
# Stecker P1 des Delock-Kabels im USB-C des ESP32 (Umspritzung ragt Richtung USB-Wand)
eo = org("ESP32", 75, 75); esp_port_y = eo[1] + (15.0 + 23.8)/2; esp_port_z = Z_BT + P['ESP_USB_H']/2
plug_ref = box(eo[0] - 0.5 - P['PLUG_L'], esp_port_y - P['PLUG_W']/2, esp_port_z - P['PLUG_T']/2, P['PLUG_L'], P['PLUG_W'], P['PLUG_T'])
add("REF_USB_Stecker_ESP32", plug_ref, (0.3, 0.3, 0.3))

# ---------------- Parametertabelle ----------------
sh = doc.addObject('Spreadsheet::Sheet', 'Parameter')
sh.set('A1', 'Name'); sh.set('B1', 'Wert'); sh.set('C1', 'Status'); sh.set('D1', 'Quelle / Hinweis')
for r, (k, v, st, q) in enumerate(PARAMS, start=2):
    sh.set('A%d' % r, k); sh.set('B%d' % r, str(v)); sh.set('C%d' % r, st); sh.set('D%d' % r, q)

# ---------------- Pruefbericht ----------------
L = []
def line(s): L.append(s)
line("PRUEFBERICHT  Variante %s  (Z_UP=%.2f, Gesamthoehe=%.2f mm)" % (VARIANT, Z_UP, Z_TOP))
if VARIANT == "deckel":
    line("Traeger/Deckel gueltig: %s/%s, Volumen %.0f/%.0f mm3, Ueberschneidung %.3f mm3 (Soll 0)" % (carrier.isValid(), cover.isValid(), carrier.Volume, cover.Volume, carrier.common(cover).Volume))
    line("Trennebene z=%.2f: Traeger %.2f mm, Deckel %.2f mm (Boden %.2f); Haut ueber PN532 %.2f + %.2f = %.2f mm" % (Z_SPLIT, Z_SPLIT - Z_UP, Z_TOP - Z_SPLIT, P['COVER_FLOOR'], Z_SPLIT - Z_UP - P['PN_DEPTH'], P['COVER_FLOOR'], P['SKIN']))
    line("Zentrierzapfen Deckel: min Abstand zum Traeger %.2f mm (Soll %.2f radial)" % (min(cyl(px_, py_, Z_SPLIT - P['COVER_PIN_L'], P['COVER_PIN_D'], P['COVER_PIN_L']).distToShape(carrier)[0] for px_, py_ in COVER_PINS), (P['COVER_PIN_HOLE'] - P['COVER_PIN_D'])/2))
    hidden = all(cover.isInside(V(hx, c['y'], Z_SPLIT + P['COVER_FLOOR']/2), 1e-3, True) for c in cells for hx in c['free_xs'])
    line("Schraubenkoepfe Freiende vom Deckel verdeckt: %s (Kopfoberkante %.2f unter Trennebene)" % (hidden, Z_SPLIT - (Z_HEAD_SEAT + 4.0)))
line("Formen gueltig: Unterteil=%s Oberteil%s=%s" % (lower.isValid(), "" if VARIANT == "einteilig" else " (Traeger+Deckel)", upper.isValid()))
line("Volumen: Unterteil=%.0f mm3, Oberteil=%.0f mm3" % (lower.Volume, upper.Volume))
line("Ueberschneidung Unter/Oberteil: %.3f mm3 (erwartet 0)" % lower.common(upper).Volume)
bad = 0
for o in doc.Objects:
    if not o.Name.startswith("REF_"): continue
    v_lo = o.Shape.common(lower).Volume; v_up = o.Shape.common(upper).Volume
    if v_lo > 0.01 or v_up > 0.01:
        bad += 1; line("  KOLLISION %s: Unterteil %.2f, Oberteil %.2f mm3" % (o.Name, v_lo, v_up))
line("Referenzteile mit Kollision: %d (erwartet 0)" % bad)
line("--- Spalte (mm) ---")
line("Ueberlastspalt Sockel-Platte: min %.2f (Soll %.2f)" % (min(p.distToShape(upper)[0] for p in posts), P['STOP_GAP']))
line("Zapfen-Bohrung: min %.2f (Soll %.2f radial), Eingriff %.2f mm" % (min(n_.distToShape(upper)[0] for n_ in nubs), (P['PIN_HOLE']-P['PIN_D'])/2, P['NUB_H'] - P['STOP_GAP']))
line("Zelle-Verdrehsicherung: min %.2f (Soll %.2f)" % (min(cell_shapes[k].distToShape(w)[0] for k in cell_shapes for w in antirot), P['ANTIROT_CLR']))
gap_free = []
for c in cells:   # Zelle ausserhalb des Sockels (frei schwingender Teil) gegen Unterteil
    d_ = PED + 1.0   # Abstand zur Sockelkante > Sollspalt, damit nur der senkrechte Spalt gemessen wird
    fx0 = cx0 + P['PED_L'] + d_ if c['fixed_left'] else cx0
    seg = box(fx0, c['y'] - P['CELL_W']/2, Z_CELL, P['CELL_L'] - P['PED_L'] - d_, P['CELL_W'], CH)
    gap_free.append(seg.distToShape(lower)[0])
line("Luft freier Zellenteil - Unterteil, alle Richtungen: min %.2f (Soll >= 2,0; unten zum Boden %.2f)" % (min(gap_free), PED))
gap_rel = []; gap_contact = []
for k, c in enumerate(cells):
    rx0, rx1 = relief_x(c)
    sx0 = max(rx0, cx0) + (0 if c['fixed_left'] else 2.0); sx1 = min(rx1, cx0 + P['CELL_L']) - (2.0 if c['fixed_left'] else 0)
    seg = box(sx0, c['y'] - P['CELL_W']/2, Z_CELL, sx1 - sx0, P['CELL_W'], CH)   # 2 mm vor der Auflagekante
    gap_rel.append(seg.distToShape(upper)[0]); gap_contact.append(cell_shapes[k].distToShape(upper)[0])
line("Luft Zelle - Plattenunterseite ausserhalb Auflage: min %.2f (Soll %.2f)" % (min(gap_rel), P['CLR_TOP']))
line("Auflage Platte auf Zellen-Freiende: Abstand %.2f (Soll 0 = Kontakt)" % max(gap_contact))
line("--- Bewegungscheck Platte bis Anschlag (Kippen um Freiende-Achse, Absenken, Verschieben) ---")
pa = V(sum(cells[0]['free_xs'])/2, cells[0]['y'], Z_UP); pb = V(sum(cells[1]['free_xs'])/2, cells[1]['y'], Z_UP)
ax_ = pb - pa
def sdist(x, y): return ((V(x, y, Z_UP) - pa).cross(ax_)).z / ax_.Length
dpos = max(sdist(x, y) for x, y in stops) + P['POST_D']/2; dneg = -min(sdist(x, y) for x, y in stops) + P['POST_D']/2   # Sockelkante beruehrt zuerst
corner_d = max(abs(sdist(x, y)) for x in (OFF, OFF + P['PLATE']) for y in (OFF, OFF + P['PLATE']))
moves = []
for s_, dd in ((1, dpos), (-1, dneg)):
    ang = math.degrees(0.98 * P['STOP_GAP'] / dd)
    u_ = upper.copy(); u_.rotate(pa, ax_, s_ * ang); moves.append(("Kippen %+.3f Grad" % (s_ * ang), u_))
u_ = upper.copy(); u_.translate(V(0, 0, -0.98 * P['STOP_GAP'])); moves.append(("Absenken %.2f" % (0.98 * P['STOP_GAP']), u_))
lat = 0.98 * (P['PIN_HOLE'] - P['PIN_D']) / 2
for v_ in (V(lat, 0, 0), V(-lat, 0, 0), V(0, lat, 0), V(0, -lat, 0)):
    u_ = upper.copy(); u_.translate(v_); moves.append(("Verschieben (%.2f|%.2f)" % (v_.x, v_.y), u_))
worst = 0.0
for nm_, u_ in moves:
    vol_ = lower.common(u_).Volume; worst = max(worst, vol_)
    if vol_ > 0.01: line("  BERUEHRUNG bei %s: %.2f mm3" % (nm_, vol_))
line("Bewegungsfaelle: %d, max. Ueberschneidung %.3f mm3 (Soll 0)" % (len(moves), worst))
line("Max. Eckabsenkung bis Anschlag: %.2f mm, Fuge Schuerze-Schulter / Kragen-Platte %.2f mm" % (P['STOP_GAP'] * corner_d / min(dpos, dneg), P['GAP_V']))
shoulder_ = lower.common(box(-10, -10, -1, P['MOD'] + 20, P['MOD'] + 20, Z_SHOULDER + 1.01))
collar_ = lower.common(box(-10, -10, Z_SHOULDER + 0.2, P['MOD'] + 20, P['MOD'] + 20, 20)).common(footprint(0, 0, 40).cut(footprint(C_IN + 0.01, -1, 42)))
line("Staubschutz Schuerze: Ueberdeckung %.1f mm; Luft waagerecht Schuerze-Kragen %.2f (Soll %.2f), senkrecht Schuerze-Schulter %.2f (Soll %.2f), Kragen-Platte %.2f (Soll %.2f)" % (
    P['SKIRT_H'] - P['GAP_V'], skirt.distToShape(collar_)[0], P['SKIRT_CLR'], skirt.distToShape(shoulder_)[0], P['GAP_V'], footprint(P['SKIRT_T'] + 0.01, Z_UP, 1).distToShape(collar_)[0], P['GAP_V']))
line("Verbinderfenster rechts: geschlossen (Wand durchgehend); offen bleibt nur der USB-C-Ausschnitt fuer die Einbaubuchse")
usb_s = doc.getObject("REF_USB_C_Buchse").Shape
line("Delock-Buchse: Flansch innen, Wand am Kragen %.1f mm, Abstand Buchse-Schuerze %.2f mm (nichts ragt aussen vor), Stirnflaeche %.1f mm hinter Aussenwand" % (X_FL - OFF, usb_s.distToShape(skirt)[0], x_f - OFF))
v_pl = usb_s.common(plug_ref).Volume
line("Stecker am ESP32 (Umspritzung 39 mm) gegen Einbaubuchse: Ueberschneidung %.0f mm3, Abstand %.2f mm  %s" % (v_pl, usb_s.distToShape(plug_ref)[0], "<-- KONFLIKT, Lage Buchse/ESP32 klaeren" if v_pl > 0.01 else "ok"))
line("Gravur Unterseite: %s" % engrave_info)
line("--- Schrauben ---")
cb_top = P['M4_CB_DEPTH']; clamp = Z_CELL - cb_top; head_seat = cb_top - P['WASHER_T']
m4_max = Z_UP - head_seat - 0.5
line("Festende 4x M4 DIN 912 + 4x Scheibe DIN 125 von unten: Klemmlaenge PLA %.1f mm, Kopf %.1f mm versenkt, Laenge max %.1f mm (Spitze unter Zellenoberkante) -> M4x12" % (clamp, head_seat - 4.0, m4_max))
clamp_f = Z_HEAD_SEAT - Z_UP; eng_f = P['M4_LEN'] - clamp_f; tip_f = Z_HEAD_SEAT - P['M4_LEN']
line("Freiende 4x M4x%d DIN 912 von oben: Klemmlaenge PLA %.1f mm, Einschraubtiefe Zelle %.1f mm, Spitze %.1f mm ueber Zellenunterkante" % (P['M4_LEN'], clamp_f, eng_f, tip_f - Z_CELL))
if VARIANT == "einteilig":
    line("Kopfoberkante Freiende %.2f mm unter Gridfinity-Taschenboden (Soll >= 0)" % ((Z_TOP - GF_H) - (Z_HEAD_SEAT + 4.0)))
line("Gesamt: 8x M4x%d DIN 912, 4x Scheibe DIN 125 M4 (nur Festende)" % P['M4_LEN'])
line("--- Platinen (Pins nach unten) ---")
line("Luft Pinreihen - Unterteil, alle Richtungen: min %.2f (Soll >= 0,4; Pinspitze zum Boden %.2f)" % (min(p_.distToShape(lower)[0] for p_ in pin_refs), P['BRD_POST'] - P['HDR_PLASTIC'] - P['HDR_PIN_BELOW']))
line("Luft hoechstes Bauteil - Plattenunterseite: min %.2f mm" % min(r_.distToShape(upper)[0] for r_ in board_refs.values()))
line("Luft Platinen - Waegezellen: min %.2f mm" % min(r_.distToShape(cell_shapes[k])[0] for r_ in board_refs.values() for k in cell_shapes))
line("Luft Boards - Stuetzen/Fuehrungen: min %.2f mm (gewollt: 0,10 = Rasthaken-Nase ueber ESP32, 0,20 = Stirnwand unter Antennen-/USB-Ueberstand)" % min(r_.distToShape(s_)[0] for r_ in board_refs.values() for s_ in board_support if r_.distToShape(s_)[0] > 1e-6) if board_support else 0)
line("Board-Halterung: alle Boards mit gedruckten Rasthaken (%d Stueck, kein Normteil); HX711/TCA9548A zusaetzlich lose Zentrierzapfen, ESP32 Auflagen + Fuehrungen" % len(hooks))
for (nm_, bn_, hk, Lh) in hooks:
    dfl = P['HOOK_OVER'] + P['HOOK_CLR']; eps = 1.5 * P['HOOK_T'] * dfl / Lh**2 * 100
    others = min(hk.distToShape(s_)[0] for s_ in board_support if s_ is not hk)
    line("  Rasthaken %-22s Abstand Board %.2f, Luft zu Nachbarteilen %.2f, Arm %.1f mm, Dehnung %.2f %% (<= 2 %%)" % (nm_ + ":", hk.distToShape(board_refs[bn_])[0], others, Lh, eps))
nub_clr = min(((P['HX_HOLE'] - P['HX_NUB_D'])/2, (P['TCA_HOLE'] - P['TCA_NUB_D'])/2))
line("Zentrierzapfen HX711/TCA: radial %.2f / %.2f mm (Soll >= 0,3, Druck wird dicker)" % ((P['HX_HOLE'] - P['HX_NUB_D'])/2, (P['TCA_HOLE'] - P['TCA_NUB_D'])/2))
line("--- Wandstaerken (rechnerisch) ---")
line("Steg zwischen PN532-Taschen: x %.2f, y %.2f mm" % (50 - pw, 50 - pl))
line("Restwand Stiftloch zur Tasche: %.2f mm" % ((50 - pw)/2 - P['PIN_HOLE']/2))
line("Restwand Kopfsenkung Freiende zur Tasche: %.2f mm auf %.1f mm Hoehe (AUSNAHME < 1,2: Steg y nur %.1f)" % ((50 - pl)/2 - P['M4_TOP_CB']/2, max(0.0, Z_UP + P['PN_DEPTH'] - Z_HEAD_SEAT), 50 - pl))
ph_ = [k for k, v, st, q in PARAMS if st == "PLATZHALTER"]
line("--- offene PLATZHALTER (%d): %s" % (len(ph_), ", ".join(ph_)))
report = "\n".join(L)
td = doc.addObject("App::TextDocument", "Pruefbericht"); td.Text = report

doc.recompute()
if App.GuiUp:
    Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
try:
    outdir = "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/cad/archiv/V1"   # V1 archiviert 2026-11-24
    os.makedirs(outdir, exist_ok=True)
    doc.saveAs(os.path.join(outdir, "Prototyp_15x15%s.FCStd" % SUFFIX))
    with open(os.path.join(outdir, "pruefbericht%s.txt" % SUFFIX.lower()), "w", encoding="utf-8") as f: f.write(report + "\n")
    report += "\n[gespeichert in %s]" % outdir
except Exception as e:
    report += "\n[Speichern fehlgeschlagen: %s]" % e
print(report)
