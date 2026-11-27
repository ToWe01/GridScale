# -*- coding: utf-8 -*-
"""
GridScale - Die intelligente Wiegematte: Gehaeuse-Prototyp 15x15 cm (FreeCAD, in der GUI per MCP-Bridge ausfuehren).
Baut Unterteil, Oberteil (Gridfinity-Profil 50 mm) und Referenzteile neu auf, schreibt
Parametertabelle (mit Status/Quelle) und Pruefbericht ins Dokument und speichert nach gehaeuse/modell/, Pruefbericht nach gehaeuse/pruefberichte/.
Status der Parameter: bestaetigt | Norm | Annahme | PLATZHALTER (muss gemessen werden)
"""
import os, math, Part
from FreeCAD import Vector as V
# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
outdir_modell = os.path.join(GEH, "modell")
outdir_bericht = os.path.join(GEH, "pruefberichte")
outdir_schnittstelle = os.path.join(PROJ, "schnittstelle")   # Schnittstelle Gehaeuse <-> Elektronik (fuer alle Teams)

# Variante: "einteilig" = Oberteil aus einem Stueck (M4-Koepfe am Freiende sichtbar im Gridfinity-Steg)
#           "deckel"    = Traeger (an Zellen geschraubt) + aufgesetzter Gridfinity-Deckel, Schrauben verdeckt
# Vor dem exec setzen: VARIANT = "einteilig"; ohne Angabe "deckel" (vom Nutzer gewaehlt, 2026-11-23).
VARIANT = globals().get("VARIANT", "deckel")
assert VARIANT in ("einteilig", "deckel"), VARIANT
SUFFIX = "" if VARIANT == "einteilig" else "_Deckel"
REV = "V2"   # V2: TCA auf der Platte, ESP32 oben, USB vorne, Wickelkammer, Kabelfuehrung
SUFFIX = SUFFIX + "_" + REV

# Parameterliste (Name, Wert, Status, Quelle) steht in params.py daneben. Per exec geladen, damit das Skript
# auch ueber die MCP-Bridge (exec ohne __file__ und ohne sys.path) laeuft.
_params_ns = {}
exec(compile(open(os.path.join(GEH, "skripte", "params.py"), encoding="utf-8").read(), "params.py", "exec"), _params_ns)
PARAMS = _params_ns["PARAMS"]; del _params_ns
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
# V2: Reader-Spalten gegen das 50-mm-Raster verschoben, damit unter dem x-Steg A die Stiftleisten von Spalte 1 und 2 Platz haben
PWX = P['PN_L'] + 2*P['PN_CLR']
PN_CX = [OFF + P['PN_RIM_X'] + PWX/2]
PN_CX.append(PN_CX[0] + PWX + P['PN_STEG_A']); PN_CX.append(PN_CX[1] + PWX + P['PN_STEG_B'])
X_SA = PN_CX[0] + PWX/2 + P['PN_STEG_A']/2; X_SB = PN_CX[1] + PWX/2 + P['PN_STEG_B']/2   # Mitten der x-Stege
RIM_R = OFF + P['PLATE'] - (PN_CX[2] + PWX/2)
def PNC(i, j): return PN_CX[i], 25.0 + 50*j      # Mitte Reader (0-basiert)
# I2C-Kante je Reader (-1 = Kante -x, +1 = Kante +x): Spalte 1 und 2 zum Steg A, Spalte 3 zum Steg B (an den Aussenwaenden ragten die Pins aus dem Modul)
PN_I2C_SIDE = {(i_, j_): (1 if i_ == 1 else -1) for i_ in (1, 2, 3) for j_ in (1, 2, 3)}
PN_I2C_HALF = 6.1 + 0.5   # Leiste ca. -6,1..+4,4 um die Kantenmitte (Foto), symmetrisch angesetzt + 0,5 Luft
Z_PNB = Z_UP + P['PN_Z0']                         # Platinen-Unterseite des Readers (umgedreht: Bestueckung + Stiftleiste darunter)
PN_SEAT = P['PN_Z0'] + P['BRD_T'] + P['PN_SEAT_CLR']   # Taschentiefe bis zur Decke
def pn_spi(i, j):                                 # SPI-Leiste: x-Bereich und y der Loetreihe; lange Kante +-y
    # Lage aus Foto IMG_1762 (Bestueckungsseite): I2C unten, SPI links -> von oben gesehen (umgedreht) SPI auf Seite +s in y
    cx_, cy_ = PNC(i-1, j-1); s_ = PN_I2C_SIDE[(i, j)]
    xa_, xb_ = sorted((cx_ + s_*(P['PN_L']/2 - P['PN_SPI_A']), cx_ - s_*(P['PN_L']/2 - P['PN_SPI_B'])))
    return xa_, xb_, cy_ + s_*(P['PN_W']/2 - P['PN_SPI_IN'])
def pn_pocket_cuts(i, j):                         # V2 Weg 3: Readertasche von der Plattenunterseite bis zur Trennebene + Pin-Aussparungen
    cx_, cy_ = PNC(i-1, j-1); s_ = PN_I2C_SIDE[(i, j)]; pw_ = P['PN_L'] + 2*P['PN_CLR']; pl_ = P['PN_W'] + 2*P['PN_CLR']
    h_ = Z_SPLIT - Z_UP + 0.1; o_ = P['PN_PIN_OVER'] + 0.3
    ex_ = cx_ + s_*P['PN_L']/2; ey_ = cy_ + s_*P['PN_W']/2; sx0_, sx1_, _ = pn_spi(i, j)
    return [box(cx_ - pw_/2, cy_ - pl_/2, Z_UP - 0.1, pw_, pl_, h_),
            box(min(ex_, ex_ + s_*o_), cy_ - PN_I2C_HALF, Z_UP - 0.1, o_, 2*PN_I2C_HALF, h_),            # I2C-Pins (Einlegen von oben)
            box(sx0_ - 0.5, min(ey_, ey_ + s_*o_), Z_UP - 0.1, sx1_ - sx0_ + 1.0, o_, h_)]               # SPI-Pins
def pn_posts(i, j):                               # Eckauflagen bis zur Platinenunterseite
    cx_, cy_ = PNC(i-1, j-1); c_ = P['PN_CLR'] + 0.05; a_ = P['PN_POST'] + c_; L2, W2 = P['PN_L']/2 + c_, P['PN_W']/2 + c_   # 0,05 in die Wand (sauberes Verschmelzen)
    return [box(cx_ + sx*L2 - (a_ if sx > 0 else 0), cy_ + sy*W2 - (a_ if sy > 0 else 0), Z_UP, a_, a_, Z_PNB - Z_UP) for sx in (-1, 1) for sy in (-1, 1)]
def pn_plug(i, j):                                # Druckplatte am Deckel: Trennebene bis 0,2 ueber Platinenrueckseite, Freistich fuer Loetbeine
    cx_, cy_ = PNC(i-1, j-1); z0_ = Z_PNB + P['BRD_T'] + P['PN_SEAT_CLR']
    pg_ = box(cx_ - P['PN_L']/2, cy_ - P['PN_W']/2, z0_, P['PN_L'], P['PN_W'], Z_SPLIT - z0_ + 0.01)
    rx_ = pn_row_x(i, j); sx0_, sx1_, ry_ = pn_spi(i, j)
    pg_ = pg_.cut(box(rx_ - 1.0, cy_ - PN_I2C_HALF, z0_ - 0.1, 2.0, 2*PN_I2C_HALF, Z_SPLIT - z0_ + 0.2))
    return pg_.cut(box(sx0_ - 0.5, ry_ - 1.0, z0_ - 0.1, sx1_ - sx0_ + 1.0, 2.0, Z_SPLIT - z0_ + 0.2))
def pn_row_x(i, j):                               # x der I2C-Lochreihe
    return PNC(i-1, j-1)[0] + PN_I2C_SIDE[(i, j)] * (P['PN_L']/2 - P['PN_I2C_IN'])
COVER_PINS = []; PIN_MISS = []   # wird bei der Trennung Traeger/Deckel neu bestimmt (Passzapfen 24.11.). Frueher: V2 Weg 3: Druckplatten des Deckels in den Readertaschen zentrieren den Deckel, Zapfen entfallen (Steg B waere neben der Pin-Aussparung zu duenn)   # auf den x-Stegen (Stiftleisten liegen unter der Platte, Bohrung oben)

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
def cable_s(c):   # y-Seite des Zellkabels: Blick aufs Festende, Kabel links (CABLE_SIDE=1)
    return P['CABLE_SIDE'] * (1 if c['fixed_left'] else -1) * (-1 if P['CELL_FLIP'] else 1)   # gedreht eingebaut -> Seite gespiegelt
def fix_x(c, d):  # x-Lage im Abstand d vom Festende der Zelle
    return cx0 + d if c['fixed_left'] else cx0 + P['CELL_L'] - d
def sil_zones(c):   # Sperrzonen Silikon (oben, unten, seitlich) + Kabel seitlich + Kabelaustritt hinter dem Festende
    xa_, xb_ = sorted((fix_x(c, P['SIL_X0'] - P['SIL_TOL']), fix_x(c, P['SIL_X1'] + P['SIL_TOL'])))
    w_ = P['CELL_W']; s_ = cable_s(c); side_ = P['SIL_SIDE'] + P['SIL_SIDE_TOL']
    top_ = box(xa_, c['y'] - w_/2, Z_UP, xb_ - xa_, w_, P['SIL_T'])
    bot_ = box(xa_, c['y'] - w_/2, Z_CELL - P['SIL_T'], xb_ - xa_, w_, P['SIL_T'])
    xs0_, xs1_ = sorted((fix_x(c, 0.0), fix_x(c, P['SIL_X1'] + P['SIL_TOL'])))
    ys_ = c['y'] + s_ * w_/2 - (side_ if s_ < 0 else 0)
    side_z = box(xs0_, ys_, Z_CELL, xs1_ - xs0_, side_, CH)
    xe0_, xe1_ = sorted((fix_x(c, 0.0), fix_x(c, -P['CABLE_EXIT_L'])))
    ye0_, ye1_ = sorted((c['y'] + s_ * (w_/2 - 3.0), c['y'] + s_ * (w_/2 + side_)))
    exit_ = box(xe0_, ye0_, FLOOR + 0.5, xe1_ - xe0_, ye1_ - ye0_, Z_CELL + CH/2 - FLOOR - 0.5)
    return top_.fuse([bot_, side_z]).removeSplitter(), exit_
for c in cells:
    px = cx0 if c['fixed_left'] else cx0 + P['CELL_L'] - P['PED_L']
    lower = lower.fuse(box(px, c['y'] - P['CELL_W']/2 - 1.0, FLOOR, P['PED_L'], P['CELL_W'] + 2.0, PED))
    # Verdrehsicherung: zwei Waende beidseitig der Zelle am Festende
    for s in (-1, 1):
        if s == cable_s(c): continue   # 27.11.: Kabelseite frei (Kabel + Silikon laufen dort zum Festende)
        y0 = c['y'] + s * (P['CELL_W']/2 + P['ANTIROT_CLR']) - (P['ANTIROT_T'] if s < 0 else 0)
        w = box(px, y0, FLOOR, P['PED_L'], P['ANTIROT_T'], PED + P['ANTIROT_H'])
        antirot.append(w); lower = lower.fuse(w)
for c in cells:
    for hx in c['fixed_xs']:
        lower = lower.cut(cyl(hx, c['y'], -1, P['CELL_SCREW_D'] + 0.5, Z_CELL + 2))
        lower = lower.cut(cyl(hx, c['y'], -1, P['M4_HEAD_CB'], 1.0 + P['M4_CB_DEPTH']))
    xa_, xb_ = c['fixed_xs']   # Steg zwischen den Senkungen waere nur 0,5 mm -> Langloch
    lower = lower.cut(box(xa_, c['y'] - P['M4_HEAD_CB']/2, -1, xb_ - xa_, P['M4_HEAD_CB'], 1.0 + P['M4_CB_DEPTH']))
    for hx in c['fixed_xs']:   # Opferschichten ueber der Senkung (Druck: Langloch-Decke = Bruecke quer, 9,5 mm): Schicht 1 Schlitz quer, Schicht 2 Quadrat
        d_ = P['CELL_SCREW_D'] + 0.5; t_ = P['SACR_LAYER']; z0_ = P['M4_CB_DEPTH']
        lower = lower.cut(box(hx - d_/2, c['y'] - P['M4_HEAD_CB']/2, z0_ - 0.01, d_, P['M4_HEAD_CB'], t_ + 0.01))
        lower = lower.cut(box(hx - d_/2, c['y'] - d_/2, z0_ + t_ - 0.01, d_, d_, t_ + 0.01))
# Anschlagsockel mit Stiftaufnahme (Ueberlast + seitliche Fuehrung)
Y_SB = max(12.0, OFF + P['USB_BOSS_T'] + 0.2 + P['USB_FL_T'] + 0.5 + P['POST_D']/2)   # 27.11.: Flansch 7,51 dick -> Sockel B weiter nach hinten, 0,5 Luft
stops = [(X_SA, 10), (X_SB, Y_SB), (X_SA, 140), (X_SB, 140)]   # (X_SB|Y_SB): Abstand zum Flansch der USB-Buchse   # V2: Steg-Mitten der verschobenen Reader
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
    "VERTEILER": dict(bx=P['VT_L'], by=P['VT_W'], gap=P['VT_GAP'], hdr=[],
                  holes=[(x, (2 + 0.5)*PITCH, P['TCA_HOLE'], P['VT_STANDOFF_D'], P['TCA_NUB_D']) for x in ((P['HUB_HOLE_K'] + 0.5)*PITCH, P['VT_L'] - (P['HUB_HOLE_K'] + 0.5)*PITCH)]),   # Streifenraster, Streifen laengs x, Kupfer unten
}
# V2: (Name, Typ, Mitte x, Mitte y, Drehung Grad, Montage). "platte" = haengt unter dem Traeger (bewegt sich mit der Wiegeplatte)
boards = [("ESP32_C6", "ESP32", 39.8, 123.0, 180, "unten"), ("HX711_A", "HX711", 24, 24, 0, "unten"), ("HX711_B", "HX711", 76, 24, 0, "unten"),
          ("TCA9548A_A", "TCA9548A", X_SA, 75, 90, "platte"), ("TCA9548A_B", "TCA9548A", X_SB, 75, 90, "platte"),
          ("Loetverteiler", "VERTEILER", 18.0, 50.0, 0, "platte")]   # unter y-Steg 50 links der Zelle 1, zwischen Reader 11 und 12
def org(t, cx, cy): return cx - BOARD_TYPES[t]['bx']/2, cy - BOARD_TYPES[t]['by']/2
def gap_of(t): return BOARD_TYPES[t].get('gap', P['TCA_GAP'])
Z_PT = Z_UP - P['TCA_GAP']; Z_PB = Z_PT - P['BRD_T']   # TCA unter der Platte: Bestueckung zur Platte, Stiftleisten nach unten wie gehabt

def snap_hook(ex, ey, n, wv, w, z_catch, z_base=None, down=False, ov=None):
    """Gedruckter Rasthaken. (ex, ey): Punkt auf der gehaltenen Kante; n: nach innen (ueber die Kante); wv: Breitenrichtung.
    Standard: steht auf dem Boden, Nase ueber z_catch (Platinenoberseite). down=True: haengt von z_base (Platte) nach unten,
    Nase unter z_catch (Platinenunterseite)."""
    clr, t = P['HOOK_CLR'], P['HOOK_T']
    if ov is None: ov = P['HOOK_OVER']
    if z_base is None: z_base = FLOOR
    hc = abs(z_catch - z_base) + 0.1; hn = hc + 0.3; htop = hn + (ov + clr)          # 45-Grad-Einlaufschraege
    sg = -1.0 if down else 1.0
    def pt(u, h): return V(ex + u*n.x, ey + u*n.y, z_base + sg*h)
    arm = Part.Face(Part.makePolygon([pt(-clr - t, -0.1), pt(-clr, -0.1), pt(-clr, hc), pt(ov, hc), pt(ov, hn),
                                      pt(-clr, htop), pt(-clr - t, htop), pt(-clr - t, -0.1)]))
    return arm.extrude(V(wv.x * w, wv.y * w, 0)), hc          # Form, freie Armlaenge
def rot_shape(s_, cx, cy, rot):
    c_ = s_.copy()
    if rot: c_.rotate(V(cx, cy, 0), V(0, 0, 1), rot)
    return c_
hooks = []
board_support = []; plate_support = []; plate_cuts = []
for (n, t, cx, cy, rot, mount) in boards:
    bt = BOARD_TYPES[t]; ox, oy = org(t, cx, cy); bx, by = bt['bx'], bt['by']
    Z_PT = Z_UP - gap_of(t); Z_PB = Z_PT - P['BRD_T']
    sups = []; hks = []; pcuts = []                      # erst in Lage "0 Grad" bauen, dann um die Boardmitte drehen
    for (hx_, hy_, hd, sd, nd) in bt['holes']:
        if mount == "unten":                             # Stuetze vom Boden + Zapfen nach oben durch das Loch
            st = cyl(ox + hx_, oy + hy_, FLOOR - 0.1, sd, P['BRD_POST'] + 0.1)
            st = st.fuse(cyl(ox + hx_, oy + hy_, Z_B - 0.1, nd, P['BRD_T'] + P['NUB_STAKE'] + 0.1))
        else:                                            # Stuetze von der Platte + Zapfen nach unten durch das Loch
            st = cyl(ox + hx_, oy + hy_, Z_PT, sd, gap_of(t) + 0.1)
            st = st.fuse(cyl(ox + hx_, oy + hy_, Z_PB - P['NUB_STAKE'], nd, P['BRD_T'] + P['NUB_STAKE'] + 0.1))
        sups.append(st)
    if t == "HX711":
        hw = P['HX_HOOK_W']
        for (ey, nv) in ((oy, V(0, 1, 0)), (oy + by, V(0, -1, 0))):
            hk, Lh = snap_hook(cx - hw/2, ey, nv, V(1, 0, 0), hw, Z_BT); hks.append((n + " Langseite", hk, Lh))
    if t in ("TCA9548A", "VERTEILER"):
        hw = P['TCA_HOOK_W']
        for (ex, nv) in ((ox, V(1, 0, 0)), (ox + bx, V(-1, 0, 0))):
            if mount == "unten": hk, Lh = snap_hook(ex, cy - hw/2, nv, V(0, 1, 0), hw, Z_BT)
            else:
                hk, Lh = snap_hook(ex, cy - hw/2, nv, V(0, 1, 0), hw, Z_PB, Z_UP + P['TCA_HOOK_ROOT'], True)
                u0, u1 = -P['HOOK_CLR'] - P['HOOK_T'] - 0.8, -P['HOOK_CLR'] + 0.3          # Freistich: Arm frei im Steg
                xa_s = ex + min(u0*nv.x, u1*nv.x); slot_ = box(xa_s, cy - hw/2 - 0.3, Z_UP - 0.1, abs(u1 - u0), hw + 0.6, P['TCA_HOOK_ROOT'] + 0.1)
                pcuts.append(slot_)
            hks.append((n + " Ende", hk, Lh))
    if t == "ESP32":
        clr = P['BRD_CLR']; w = P['BRD_WALL']; hg = P['BRD_POST'] + 1.4
        for (x0, y0, dx, dy) in [(2.0, 10.0, 6.0, 5.4), (44.0, 6.0, 6.0, 13.4)]:          # Auflagen unter der Platinenmitte
            sups.append(box(ox + x0, oy + y0, FLOOR - 0.1, dx, dy, P['BRD_POST'] + 0.1))
        for (x0, y0, dy) in [(-clr - w, 10.0, 2.8), (bx + clr, 6.0, 13.4)]:                 # Stirnwaende (USB-Ende: nur zwischen den Buchsen, Stecker frei)
            sups.append(box(ox + x0, oy + y0, FLOOR - 0.1, w, dy, hg + 0.1))
        hx0 = P['ESP_HOOK_X'] - P['ESP_HOOK_W']/2
        for y0 in (-clr - w, by + clr):                                                     # Seitenfuehrung USB-Ende
            sups.append(box(ox + 2.0, oy + y0, FLOOR - 0.1, hx0 - 1.0 - 2.0, w, hg + 0.1))
        for (ey, n_) in ((oy, V(0, 1, 0)), (oy + by, V(0, -1, 0))):
            hk, Lh = snap_hook(ox + hx0, ey, n_, V(1, 0, 0), P['ESP_HOOK_W'], Z_BT); hks.append((n + " Langseite", hk, Lh))
        ax0 = ox + bx + P['ESP_ANT_OVER']
        hk, Lh = snap_hook(ax0, cy - P['ANT_HOOK_W']/2, V(-1, 0, 0), V(0, 1, 0), P['ANT_HOOK_W'], Z_BT + P['ESP_ANT_T']); hks.append((n + " Antenne", hk, Lh))
    sups = [rot_shape(q, cx, cy, rot) for q in sups]
    plate_cuts.extend(rot_shape(q, cx, cy, rot) for q in pcuts)
    hks = [(lb, rot_shape(q, cx, cy, rot), Lh) for (lb, q, Lh) in hks]
    tgt = board_support if mount == "unten" else plate_support
    tgt.extend(sups)
    for (lb, q, Lh) in hks:
        hooks.append((lb, n, q, Lh, mount)); tgt.append(q)
    if mount == "unten":
        for q in sups + [h[1] for h in hks]: lower = lower.fuse(q)

Z_PT = Z_UP - P['TCA_GAP']; Z_PB = Z_PT - P['BRD_T']
# V2 Waende: USB-C-Einbaubuchse in der vorderen Wand (y=0) bei x=USB_X, linke Wand geschlossen, rechts Verstaerkung (Modulverbinder spaeter)
wall_h = Z_WALL - FLOOR   # Innenverstaerkung buendig mit Kragen
UX = P['USB_X']
lower = lower.fuse(box(UX - P['USB_WALL_L']/2, OFF, FLOOR, P['USB_WALL_L'], P['WALL'], wall_h))
zc = FLOOR + P['USB_Z0'] + P['USB_H']/2.0
lower = lower.cut(box(UX - P['USB_W']/2, OFF - 1, zc - P['USB_H']/2, P['USB_W'], P['WALL'] + 2, P['USB_H']))
# Flansch liegt INNEN an der Wand (Kragen steckt im Ausschnitt): Tasche in die Verstaerkung, Wand dort = Kragenhoehe
Y_FL = OFF + P['USB_BOSS_T'] + 0.2
lower = lower.cut(box(UX - P['USB_FL_L']/2 - 0.3, Y_FL, zc - P['USB_FL_W']/2 - 0.3, P['USB_FL_L'] + 0.6, P['WALL'] + 1, P['USB_FL_W'] + 0.6))
for sx_ in (-1, 1):
    lower = lower.cut(cyl(UX + sx_*P['USB_SCREW_SP']/2, OFF - 1, zc, P['USB_SCREW_D'], P['WALL'] + 2, V(0, 1, 0)))
    csk_h = (P['USB_CSK_D'] - P['USB_SCREW_D']) / 2   # 90-Grad-Senkung von aussen (ISO 10642 M3)
    lower = lower.cut(Part.makeCone(P['USB_CSK_D']/2 + 0.5, P['USB_SCREW_D']/2, csk_h + 0.5, V(UX + sx_*P['USB_SCREW_SP']/2, OFF - 0.5, zc), V(0, 1, 0)))
xr = OFF + P['PLATE'] - P['WALL']
lower = lower.fuse(box(xr, 75-14, FLOOR, P['WALL'], 28, wall_h))
# --- 27.11. Power-Hub (Elektronik): Streifenraster vorne rechts, Bestueckung nach unten, JP_NFC durch Bodenfenster von unten erreichbar ---
CD = P['CABLE_D']
USB_END_Y = Y_FL + P['USB_LEN'] - P['USB_BOSS_T']              # Ende Knickschutz der Einbaubuchse
esp_ = [b for b in boards if b[0] == "ESP32_C6"][0]; _eo = org("ESP32", esp_[2], esp_[3])
PLUG_Y = 2*esp_[3] - (_eo[1] + (15.0 + 23.8)/2)                # Port (15,0-23,8) nach 180-Grad-Drehung
HX0, HY0, HW, HL = P['HUB_X0'], P['HUB_Y0'], P['HUB_W'], P['HUB_L']
HUB_ZB = FLOOR + P['HUB_POST']; HUB_ZT = HUB_ZB + P['BRD_T']
JP_X0, JP_Y0 = HX0 + 0.0, HY0 + 3*PITCH                        # JP_NFC auf Streifen 1+2 (VBUS_IN -> 5V_NFC), 2. nutzbare Lochreihe
HUB_HOLES = [(HX0 + 2.5*PITCH, HY0 + yh_) for yh_ in ((P['HUB_HOLE_K'] + 0.5)*PITCH, HL - (P['HUB_HOLE_K'] + 0.5)*PITCH)]   # Streifen 3 (GND)
coil_feats = []
for (xh_, yh_) in HUB_HOLES:                                   # 27.11. b: Dome + Zentrierzapfen statt Leisten/Schaumklebeband
    coil_feats.append(cyl(xh_, yh_, FLOOR - 0.1, P['TCA_STANDOFF_D'], HUB_ZB - FLOOR + 0.1).fuse(cyl(xh_, yh_, HUB_ZB - 0.1, P['TCA_NUB_D'], P['BRD_T'] + P['NUB_STAKE'] + 0.1)))
hw_ = P['TCA_HOOK_W']
for (ex_, yc_, nv_) in ((HX0 + HW, HY0 + PITCH, V(-1, 0, 0)), (HX0, HY0 + HL - PITCH, V(1, 0, 0))):   # Rasthaken an den Langseiten im toten Endbereich, diagonal
    hk_, Lh_ = snap_hook(ex_, yc_ - hw_/2, nv_, V(0, 1, 0), hw_, HUB_ZT)                             # (hinten laufen die Delock-Adern ueber die Kante)
    coil_feats.append(hk_); hooks.append(("Power-Hub Langseite", "Power_Hub", hk_, Lh_, "unten"))
jw_ = P['JP_WIN_CLR']
HUB_WIN = box(JP_X0 - jw_, JP_Y0 - jw_, -1, 2*PITCH + 2*jw_, PITCH + 2*jw_, FLOOR + 2)   # Bodenfenster unter JP_NFC
# Kabelgabeln am Boden: Verbindung ESP32 -> Platte (4 Adern, flexible Schlaufe) und HX711 -> ESP32 (Bodenleitungen links)
def fork(x_, y_, gap, h_, d_=2.4, along_x=True):
    o_ = (gap + d_)/2
    p1 = (x_ - o_, y_) if along_x else (x_, y_ - o_); p2 = (x_ + o_, y_) if along_x else (x_, y_ + o_)
    return cyl(p1[0], p1[1], FLOOR - 0.1, d_, h_ + 0.1).fuse(cyl(p2[0], p2[1], FLOOR - 0.1, d_, h_ + 0.1))
LINK_CLIP = (20.0, 64.0)   # V2: Gabel direkt unter dem Loetverteiler, kurze Schlaufe ueber den Waegespalt
coil_feats.append(fork(LINK_CLIP[0], LINK_CLIP[1], 3.8, 9.0))   # 27.11.: 5 Adern (Elektronik) -> Gabel 3,8
for yf in (45.0, 80.0):
    coil_feats.append(fork(10.0, yf, 4.6, 7.0, 2.0))   # V2: Buendel HX711 A+B (8 Litzen)
for q in coil_feats: lower = lower.fuse(q)
lower = lower.cut(HUB_WIN)
# Verbinderfenster im Prototyp geschlossen (Verbinder noch nicht festgelegt); Verstaerkung bleibt zum spaeteren Einschneiden
# Verstaerkungen oberhalb der Schulter auf den Kragen zuruecknehmen (Platz fuer die Schuerze)
lower = lower.cut(footprint(0, Z_SHOULDER, Z_UP - Z_SHOULDER).cut(footprint(C_OUT, Z_SHOULDER - 1, Z_UP - Z_SHOULDER + 2)))
# Gravur auf der Unterseite (von unten lesbar -> in x gespiegelt); ohne Schrift wird sie uebersprungen
ENGRAVE_TXT = "GRIDSCALE  15x15  R3"
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
        px_, py_ = PNC(i, j)
        for q_ in pn_pocket_cuts(i+1, j+1): upper = upper.cut(q_)                                 # V2 Weg 3: Tasche durch den Traeger
        for q_ in pn_posts(i+1, j+1): upper = upper.fuse(q_)                                     # 4 Eckauflagen
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
    # 27.11.: Silikon oben auf der Messzone -> Freistich dort SIL_T tiefer (Luft ueber dem Silikon = CLR_TOP); seitlich bis ueber die Kabelseite
    xa_, xb_ = sorted((fix_x(c, P['SIL_X0'] - P['SIL_TOL']), fix_x(c, P['SIL_X1'] + P['SIL_TOL'])))
    xa_ -= P['CLR_TOP']; xb_ += P['CLR_TOP']
    ext_ = P['SIL_SIDE'] + P['SIL_SIDE_TOL'] + P['CLR_TOP']; s_ = cable_s(c)
    y0_ = c['y'] - P['CELL_W']/2 - (ext_ if s_ < 0 else 1.0); y1_ = c['y'] + P['CELL_W']/2 + (ext_ if s_ > 0 else 1.0)
    upper = upper.cut(box(xa_, y0_, Z_UP - 0.1, xb_ - xa_, y1_ - y0_, P['CLR_TOP'] + P['SIL_T'] + 0.1))
    # seitliches Kabel/Silikon ab Festende reicht bis Z_UP und 2,2 neben die Zelle -> dort ebenfalls Freistich CLR_TOP
    xs0_, xs1_ = sorted((fix_x(c, 0.0), fix_x(c, P['SIL_X1'] + P['SIL_TOL'])))
    ys0_ = c['y'] + P['CELL_W']/2 if s_ > 0 else c['y'] - P['CELL_W']/2 - ext_
    upper = upper.cut(box(xs0_ - P['CLR_TOP'], ys0_, Z_UP - 0.1, xs1_ - xs0_ + 2*P['CLR_TOP'], ext_, P['CLR_TOP'] + 0.1))
    for hx in c['free_xs']:   # M4 DIN 912 von oben durch die Platte ins Zellengewinde, Kopf versenkt im Steg
        z_end = Z_TOP + 0.1 if VARIANT == "einteilig" else Z_SPLIT   # Deckel-Variante: endet an der Trennebene
        upper = upper.cut(cyl(hx, c['y'], Z_UP - 0.1, P['M4_CLR'], z_end - Z_UP + 0.1))
        upper = upper.cut(cyl(hx, c['y'], Z_HEAD_SEAT, P['M4_TOP_CB'], z_end - Z_HEAD_SEAT))
        if VARIANT != "einteilig":   # Traeger kopfueber: Senkungsboden ist Bruecke -> Schicht 1 Schlitz (laengs x, weg von den duennen Waenden in y), Schicht 2 Quadrat
            d_, t_ = P['M4_CLR'], P['SACR_LAYER']
            upper = upper.cut(box(hx - P['M4_TOP_CB']/2, c['y'] - d_/2, Z_HEAD_SEAT - t_, P['M4_TOP_CB'], d_, t_ + 0.01).common(cyl(hx, c['y'], Z_HEAD_SEAT - t_ - 0.1, P['M4_TOP_CB'], t_ + 0.3)))
            upper = upper.cut(box(hx - d_/2, c['y'] - d_/2, Z_HEAD_SEAT - 2*t_, d_, d_, t_ + 0.01))
for (sx, sy) in stops:   # Sackloecher fuer die Zapfen (von unten, Oberflaeche bleibt glatt)
    upper = upper.cut(cyl(sx, sy, Z_UP - 0.1, P['PIN_HOLE'], P['PIN_HOLE_DEPTH'] + 0.1))
# --- V2 Kabelnuten quer durch Stege: fuehren Litzen von Readern ohne eigenen Abgang zum Nachbar-Reader, dessen Abgang frei ist ---
#  Reader 21 -> 11 und 23 -> 13 (x-Steg 50, ausserhalb der Zellbaender), 31 -> 32 und 33 -> 32 (y-Stege bei x=125, rechts der Zellen)
GW, GD, GL = P['GROOVE_W'], P['GROOVE_D'], P['GROOVE_LIP']
pw_, pl_ = P['PN_L'] + 2*P['PN_CLR'], P['PN_W'] + 2*P['PN_CLR']
xs_lo, xs_hi = 50 - (50 - pw_)/2, 50 + (50 - pw_)/2            # x-Steg 50
GROOVES = [("Bus Verteiler -> TCA_A", "x", 50.05, 67.6)]   # 26.11.: TCA_A gedreht (Eagle: JP3 = VCC/GND/SDA/SCL + Kanal 0/1, JP1 = Kanal 2-7) ->
#  Bus muss an die rechte Leiste von TCA_A; kreuzt Steg A quer (kostet kaum Steifigkeit) zwischen TCA-Stuetze (y 62,3) und Reader-Pins (ab y 70,9)
groove_cuts = []
for (nm_, ax_g, gx, gy) in GROOVES:
    st_w = (50 - pw_) if ax_g == "x" else (50 - pl_)
    if ax_g == "x": gcut = box(gx - st_w/2 - 2.0, gy - GW/2, Z_UP - 0.1, st_w + 4.0, GW, GD + 0.1)   # 26.11.: 2 mm in die Taschen (Steg A real 9,0 breit)
    else:           gcut = box(gx - GW/2, gy - st_w/2 - 0.5, Z_UP - 0.1, GW, st_w + 1.0, GD + 0.1)
    groove_cuts.append((nm_, gcut)); upper = upper.cut(gcut)
for (nm_, ax_g, gx, gy) in GROOVES:   # Haltelippen an der Nutoeffnung (Traeger wird kopfueber gedruckt -> kurze Ueberhaenge)
    for sgn in (-1, 1):
        if ax_g == "x": lip = box(gx - 1.5, gy + sgn*(GW/2) - (GL if sgn > 0 else 0), Z_UP, 3.0, GL, 0.8)
        else:           lip = box(gx + sgn*(GW/2) - (GL if sgn > 0 else 0), gy - 1.5, Z_UP, GL, 3.0, 0.8)
        upper = upper.fuse(lip)
# --- V2 PN532-Sicherung: je 2 Rasthaken aus den Stegen, Nase greift unter die Platinenkante (Reader wird von unten eingeschoben) ---
#  Arm liegt in einem Freistich in der Taschenwand (nach unten offen -> zum Loesen von unten mit Schraubendreher aufbiegen)
# V2 umgedreht: Spalte 2 hakt an den x-Kanten (I2C-Kante -x am Steg A), Spalte 1 und 3 an den Laengskanten +-y
#  (Aussenrand nur PN_RIM_X breit, kein Platz fuer einen Freistich). Haken an +-y bleiben neben den Waegezellen.
cell_keep = [box(cx0, c['y'] - P['CELL_W']/2, Z_CELL, P['CELL_L'], P['CELL_W'], CH) for c in cells]
pn_avoid = [g_ for (_, g_) in groove_cuts] + [cyl(hx, c['y'], Z_UP - 0.1, P['M4_TOP_CB'], 10) for c in cells for hx in c['free_xs']] \
           + [cyl(sx, sy, Z_UP - 0.1, P['PIN_HOLE'], 10) for (sx, sy) in stops] + list(plate_cuts)
pn_slots = []; pn_hook_info = []
hwp = P['PN_HOOK_W']; on_y = P['PN_HOOK_ON_Y'] >= 0.5
for i in (range(3) if P['PN_HOOKS'] >= 0.5 else []):
    for j in range(3):
        cx, cy = PNC(i, j)
        on_y = (i != 1)
        for sgn in (-1, 1):
            best = None
            i2c_edge = (not on_y) and sgn == PN_I2C_SIDE[(i+1, j+1)]
            if i2c_edge:   # (Versatz, Breite): breit bevorzugt, schmal (3 mm) nur wenn neben der Leiste nichts anderes passt
                cands = [(dd, ww) for ww in (hwp, 3.0) for dd in (P['PN_HOOK_DY'], -P['PN_HOOK_DY'], 10, -10, 14, -14, 8.1, -8.1, 16, -16) if abs(dd) - ww/2 >= PN_I2C_HALF]
            else:
                cands = [(dd, hwp) for dd in (0, 4, -4, 8, -8, 12, -12)]
            for (d_, hw_c) in cands:
                if on_y: ex, ey, nv, wv = cx + d_ - hw_c/2, cy + sgn*P['PN_W']/2, V(0, -sgn, 0), V(1, 0, 0)
                else:    ex, ey, nv, wv = cx + sgn*P['PN_L']/2, cy + d_ - hw_c/2, V(-sgn, 0, 0), V(0, 1, 0)
                u0, u1 = -P['HOOK_CLR'] - P['HOOK_T'] - 0.8, -P['PN_CLR'] + 0.1
                if on_y:
                    ya_, yb_ = sorted((ey + u0*nv.y, ey + u1*nv.y)); slot_ = box(ex - 0.3, ya_, Z_UP - 0.1, hw_c + 0.6, yb_ - ya_, P['PN_HOOK_ROOT'] + 0.1)
                else:
                    xa_, xb_ = sorted((ex + u0*nv.x, ex + u1*nv.x)); slot_ = box(xa_, ey - 0.3, Z_UP - 0.1, xb_ - xa_, hw_c + 0.6, P['PN_HOOK_ROOT'] + 0.1)
                wall_ = min(slot_.distToShape(a_)[0] for a_ in pn_avoid + pn_slots)
                bb_ = slot_.BoundBox
                wall_ = min(wall_, bb_.XMin - OFF, bb_.YMin - OFF, OFF + P['PLATE'] - bb_.XMax, OFF + P['PLATE'] - bb_.YMax)   # Aussenwand
                if wall_ < 1.2: continue
                hk_t, _ = snap_hook(ex, ey, nv, wv, hw_c, Z_PNB, Z_UP + P['PN_HOOK_ROOT'], True, P['PN_HOOK_OVER'])
                if min(hk_t.distToShape(q_)[0] for q_ in plate_support) < 1.0: continue     # Platz zum Aufbiegen (0,6) neben TCA-Stuetzen/Haken
                if min(hk_t.distToShape(q_)[0] for q_ in cell_keep) < 1.0: continue        # Nase nicht ueber der Waegezelle (Platte senkt sich 0,5)
                best = (d_, ex, ey, nv, wv, slot_, wall_, hw_c); break
            if best is None: raise RuntimeError("PN532_%d%d: kein Platz fuer Rasthaken (Restwand < 1,2)" % (i+1, j+1))
            d_, ex, ey, nv, wv, slot_, wall_, hw_c = best
            hk, Lh = snap_hook(ex, ey, nv, wv, hw_c, Z_PNB, Z_UP + P['PN_HOOK_ROOT'], True, P['PN_HOOK_OVER'])
            pn_slots.append(slot_); plate_cuts.append(slot_); plate_support.append(hk)
            hooks.append(("PN532_%d%d Kante" % (i+1, j+1), "PN532_%d%d" % (i+1, j+1), hk, Lh, "platte"))
            pn_hook_info.append((i+1, j+1, sgn, d_, wall_, hw_c))
for q in plate_cuts:      # Freistichtaschen fuer die TCA-, Verteiler- und PN532-Rasthaken
    upper = upper.cut(q)
for q in plate_support:   # TCA-Halter (Stuetzen, Zapfen, Haken) haengen an der Traegerunterseite
    upper = upper.fuse(q)
upper = upper.removeSplitter()

carrier = cover = None
if VARIANT == "deckel":
    # Trennen: Traeger unterhalb Z_SPLIT, Deckel darueber. Senkungen enden an der Trennebene, der Deckel bleibt geschlossen.
    big = P['MOD'] + 20
    carrier = upper.common(box(-10, -10, Z_UP - 15, big, big, Z_SPLIT - Z_UP + 15))   # V2: inkl. TCA-Halter unter der Platte
    cover = upper.common(box(-10, -10, Z_SPLIT, big, big, Z_TOP - Z_SPLIT + 1))
    cover = chamfer_z(cover.removeSplitter(), Z_SPLIT, P['COVER_SEAM_CH'])
    carrier = chamfer_z(carrier.removeSplitter(), Z_SPLIT, P['COVER_SEAM_CH'])
    for i_ in (1, 2, 3):
        for j_ in (1, 2, 3): cover = cover.fuse(pn_plug(i_, j_))
    LIP_H = Z_SPLIT - (Z_PNB + P['BRD_T'] + P['PN_SEAT_CLR'])           # gleiche Hoehe wie die Druckplatten
    for (y0_, y1_) in ((OFF - 1, OFF + P['COVER_LIP_W']), (OFF + P['PLATE'] - P['COVER_LIP_W'], OFF + P['PLATE'] + 1)):
        cover = cover.fuse(footprint(0, Z_SPLIT - LIP_H, LIP_H + 0.01).common(box(-10, y0_, Z_SPLIT - LIP_H - 1, P['MOD'] + 20, y1_ - y0_, LIP_H + 2)))
    for (y0_, y1_) in ((OFF - 1, OFF + P['COVER_LIP_W'] + P['COVER_LIP_CLR']), (OFF + P['PLATE'] - P['COVER_LIP_W'] - P['COVER_LIP_CLR'], OFF + P['PLATE'] + 1)):
        carrier = carrier.cut(box(-10, y0_, Z_SPLIT - LIP_H, P['MOD'] + 20, y1_ - y0_, LIP_H + 1))
    # V2 (24.11.): Passzapfen Deckel -> Traeger mit Quetschrippen. Laenge = Druckplattenhoehe, damit der Deckel beim Druck
    # gleichzeitig auf Druckplatten, Randleisten und Zapfen steht. Lage automatisch: je Zielpunkt die naechste Stelle,
    # an der die Bohrung + Mindestwand ganz im Traegermaterial liegt (Stege/Rahmen, nicht in Taschen, Senkungen, Stufen).
    PIN_L = LIP_H; PIN_DEPTH = PIN_L + 0.5
    R_CHK = P['COVER_PIN_HOLE']/2 + P['COVER_PIN_WALL']
    slab_ = carrier.common(box(-10, -10, Z_SPLIT - PIN_DEPTH - 0.3, big, big, PIN_DEPTH + 0.3 - 0.01))
    ZS_ = [Z_SPLIT - PIN_DEPTH - 0.25, Z_SPLIT - PIN_DEPTH/2, Z_SPLIT - 0.05]
    RING_ = [(R_CHK * math.cos(math.radians(a_)), R_CHK * math.sin(math.radians(a_))) for a_ in range(0, 360, 20)] + [(0, 0), (R_CHK/2, 0), (-R_CHK/2, 0), (0, R_CHK/2), (0, -R_CHK/2)]
    def pin_ok(x_, y_):   # schnelle Punktabfrage (Ring + Mitte auf 3 Hoehen), danach einmal exakt per Boolean
        for z_ in ZS_:
            for dx_, dy_ in RING_:
                if not slab_.isInside(V(x_ + dx_, y_ + dy_, z_), 1e-4, True): return False
        c_ = cyl(x_, y_, Z_SPLIT - PIN_DEPTH - 0.3, 2*R_CHK, PIN_DEPTH + 0.3 - 0.02)
        return slab_.common(c_).Volume > 0.999 * c_.Volume
    PIN_TARGETS = [(50, 8), (101, 8), (50, 142), (101, 142), (8, 50), (142, 50), (8, 100), (142, 100), (50, 50), (101, 100)]   # Stegenden nahe Rand + 2 Kreuzungen (Aussenrand nur 1,5 mm -> dort kein Platz) (Annahme)
    COVER_PINS = []; PIN_MISS = []
    for tx_, ty_ in PIN_TARGETS:
        cand_ = sorted(((tx_ + dx_*0.5, ty_ + dy_*0.5) for dx_ in range(-12, 13) for dy_ in range(-12, 13)), key=lambda q: (q[0]-tx_)**2 + (q[1]-ty_)**2)
        hit_ = next((q for q in cand_ if all((q[0]-a_)**2 + (q[1]-b_)**2 > (4*R_CHK)**2 for a_, b_ in COVER_PINS) and pin_ok(*q)), None)
        (COVER_PINS if hit_ else PIN_MISS).append(hit_ or (tx_, ty_))
    def rib_hole(x_, y_):
        h_ = cyl(x_, y_, Z_SPLIT - PIN_DEPTH, P['COVER_PIN_HOLE'], PIN_DEPTH + 0.1)
        h_ = h_.fuse(Part.makeCone(P['COVER_PIN_HOLE']/2, P['COVER_PIN_HOLE']/2 + P['COVER_PIN_CH'], P['COVER_PIN_CH'] + 0.01, V(x_, y_, Z_SPLIT - P['COVER_PIN_CH'])))
        for k_ in range(int(P['CRUSH_N'])):
            a_ = math.radians(90 + 360.0 * k_ / P['CRUSH_N'])
            rib_ = box(P['COVER_PIN_D']/2, -P['CRUSH_W']/2, Z_SPLIT - PIN_DEPTH - 0.1, P['COVER_PIN_HOLE']/2 - P['COVER_PIN_D']/2 + 0.2, P['CRUSH_W'], PIN_DEPTH - P['COVER_PIN_CH'] + 0.1)
            rib_.rotate(V(0, 0, 0), V(0, 0, 1), math.degrees(a_)); rib_.translate(V(x_, y_, 0))
            h_ = h_.cut(rib_)
        return h_
    for (px_, py_) in COVER_PINS:
        carrier = carrier.cut(rib_hole(px_, py_))
        pin_ = cyl(px_, py_, Z_SPLIT - PIN_L, P['COVER_PIN_D'], PIN_L + 0.01)
        cover = cover.fuse(pin_)
    carrier = carrier.removeSplitter(); cover = cover.removeSplitter()
    upper = carrier.fuse(cover)   # fuer Spalt- und Bewegungschecks bewegen sich beide gemeinsam

# ---------------- Objekte ----------------
def add(name, shape, color=None, transp=0):
    o = doc.addObject("Part::Feature", name); o.Shape = shape
    if color and App.GuiUp:
        o.ViewObject.ShapeColor = color; o.ViewObject.Transparency = transp
    return o
# Echte Farben der Zukaufteile (nur Anzeige, keine Geometrie)
COL = dict(HX711=(0.75, 0.10, 0.10),        # SparkFun: rote Platine
           TCA9548A=(0.05, 0.20, 0.55),     # Adafruit: dunkelblau
           ESP32=(0.10, 0.10, 0.10),        # Espressif DevKitC: schwarz
           VERTEILER=(0.80, 0.62, 0.35),    # Streifenraster Hartpapier: beige/braun
           PN532=(0.80, 0.08, 0.10),        # Elechouse V3: rot
           KUNSTSTOFF=(0.08, 0.08, 0.08), PIN=(0.85, 0.75, 0.35), METALL=(0.75, 0.75, 0.78),
           KUPFER=(0.85, 0.50, 0.20), BAUTEIL=(0.20, 0.20, 0.22), SILK=(0.92, 0.92, 0.88), ALU=(0.80, 0.80, 0.82))
def add_parts(name, groups):   # groups: [(Suffix, [Formen], Farbe)], leere Gruppen werden uebersprungen
    for suf_, shs_, col_ in groups:
        if not shs_: continue
        sh_ = shs_[0]
        for q_ in shs_[1:]: sh_ = sh_.fuse(q_)
        add(name + suf_, sh_, col_)
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
    add("REF_Waegezelle_%d" % (k+1), cell, COL['ALU'])
sil_refs = {}
for k, c in enumerate(cells):   # 27.11.: Silikon + Zellkabel als Sperrzonen (fest am Unterteil, Luft zum Traeger = kein Kraftnebenschluss)
    sz_, ex_ = sil_zones(c); sil_refs[k] = (sz_, ex_)
    add("REF_Zelle%d_Silikon_Kabel" % (k+1), sz_, (0.85, 0.85, 0.8))
    add("REF_Zelle%d_Kabelaustritt" % (k+1), ex_, (0.85, 0.85, 0.8))
board_refs = {}; pin_refs = []; board_mount = {}
for (n, t, cx, cy, rot, mount) in boards:
    bt = BOARD_TYPES[t]; ox, oy = org(t, cx, cy); bx, by = bt['bx'], bt['by']
    zb_ = Z_B if mount == "unten" else Z_UP - gap_of(t) - P['BRD_T']; zbt_ = zb_ + P['BRD_T']
    pcb = box(ox, oy, zb_, bx, by, P['BRD_T'])
    for (hx_, hy_, hd, sd, nd) in bt['holes']:
        pcb = pcb.cut(cyl(ox + hx_, oy + hy_, zb_ - 1, hd, P['BRD_T'] + 2))
    parts = [pcb]; pins_ = []; g_pl = []; g_pin = []; g_met = []; g_cu = []; g_dk = []
    for (x0, y0, dx, dy) in bt['hdr']:
        parts.append(box(ox + x0, oy + y0, zb_ - P['HDR_PLASTIC'], dx, dy, P['HDR_PLASTIC'])); g_pl.append(parts[-1])   # Kunststoff
        long_x = dx > dy; L_ = dx if long_x else dy
        pin = box(ox + x0 + (0 if long_x else dx/2 - 0.32), oy + y0 + (dy/2 - 0.32 if long_x else 0), zb_ - P['HDR_PLASTIC'] - P['HDR_PIN_BELOW'],
                  L_ if long_x else 0.64, 0.64 if long_x else L_, P['HDR_PIN_BELOW'])                     # Pinreihe unten
        top = box(pin.BoundBox.XMin, pin.BoundBox.YMin, zbt_, pin.BoundBox.XLength, pin.BoundBox.YLength, P['HDR_PIN_ABOVE'])
        parts += [pin, top]; pins_.append(pin); g_pin += [pin, top]
    if t == "VERTEILER":                                                                          # Loetstellen/Abgaenge unter der Kupferseite
        ls_ = box(ox + 1.3, oy, zb_ - P['VT_SOLDER'], bx - 2.6, by, P['VT_SOLDER'])
        for (hx_, hy_, hd, sd, nd) in bt['holes']: ls_ = ls_.cut(cyl(ox + hx_, oy + hy_, zb_ - P['VT_SOLDER'] - 1, hd + 1.0, P['VT_SOLDER'] + 2))   # keine Loetstelle am Montageloch
        parts.append(ls_); g_cu.append(parts[-1])
    if t == "ESP32":
        mw = 18.0
        parts.append(box(ox + bx - P['ESP_MOD_L'], cy - mw/2, zbt_, P['ESP_MOD_L'], mw, P['ESP_MOD_H'])); g_met.append(parts[-1])        # Modul mit Abschirmung
        parts.append(box(ox + bx, cy - mw/2, zbt_, P['ESP_ANT_OVER'], mw, P['ESP_ANT_T'])); g_dk.append(parts[-1])                     # Antennenueberstand
        for (y0, y1) in [(1.0, 9.7), (15.0, 23.8)]:                                                               # 2x USB-C am Ende x=0
            parts.append(box(ox - 0.5, oy + y0, zbt_, 7.9, y1 - y0, P['ESP_USB_H'])); g_met.append(parts[-1])
        for sd_ in ((1, 2) if P['ESP_JMP_SIDE'] == 0 else (P['ESP_JMP_SIDE'],)):                              # 27.11.: abgewinkelter Jumper oben
            jy_ = oy if sd_ == 1 else oy + by - P['ESP_JMP_W']
            parts.append(box(ox + P['ESP_JMP_X'] - P['ESP_JMP_L']/2, jy_, zbt_, P['ESP_JMP_L'], P['ESP_JMP_W'], P['ESP_JMP_H'])); g_pl.append(parts[-1])
    shp = parts[0]
    for q in parts[1:]: shp = shp.fuse(q)
    shp = rot_shape(shp, cx, cy, rot)
    pin_refs.extend(rot_shape(q, cx, cy, rot) for q in pins_)
    board_refs[n] = shp; board_mount[n] = mount
    R_ = lambda L_: [rot_shape(q_, cx, cy, rot) for q_ in L_]
    add_parts("REF_" + n, [("", R_([pcb]), COL[t]), ("_Stiftleisten", R_(g_pl), COL['KUNSTSTOFF']), ("_Pins", R_(g_pin), COL['PIN']),
                           ("_Modul", R_(g_met), COL['METALL']), ("_Antenne", R_(g_dk), COL['BAUTEIL']), ("_Loetseite", R_(g_cu), COL['KUPFER'])])
plate_refs = [board_refs[k] for k in board_refs if board_mount[k] == "platte"]
base_refs = [board_refs[k] for k in board_refs if board_mount[k] == "unten"]
# V2 Reader-Modell Elechouse PN532 V3, umgedreht: Platine oben (Rueckseite an der Taschendecke), darunter Bestueckung und
#  abgewinkelte 4-pol. I2C-Stiftleiste (Wuerth WR-PHD 61300411021), Pins horizontal nach aussen, ca. 4 mm ueber die Kante
pn_hdr = {}; pn_col = {}; pn_brd = {}
def pn_model(i, j):
    cx_, cy_ = PNC(i-1, j-1); s_ = PN_I2C_SIDE[(i, j)]; rx_ = pn_row_x(i, j)
    zb_ = Z_PNB; zt_ = zb_ + P['BRD_T']; ci_ = P['PN_COMP_IN']
    pcb_ = box(cx_ - P['PN_L']/2, cy_ - P['PN_W']/2, zb_, P['PN_L'], P['PN_W'], P['BRD_T'])
    comp_ = box(cx_ - P['PN_L']/2 + ci_, cy_ - P['PN_W']/2 + ci_, zb_ - P['PN_COMP_H'], P['PN_L'] - 2*ci_, P['PN_W'] - 2*ci_, P['PN_COMP_H'] + 0.01)
    dx0_, dx1_ = sorted((cx_ + s_*(P['PN_L']/2 - P['PN_DIP_X0']), cx_ + s_*(P['PN_L']/2 - P['PN_DIP_X1'])))
    dy0_, dy1_ = sorted((cy_ - s_*P['PN_DIP_Y0'], cy_ - s_*P['PN_DIP_Y1']))
    comp_ = comp_.fuse(box(dx0_, dy0_, zb_ - P['PN_DIP_H'], dx1_ - dx0_, dy1_ - dy0_, P['PN_DIP_H'] + 0.01))   # DIP-Schalter neben der I2C-Leiste
    bw_ = 4 * PITCH; zpin = zb_ - P['PN_PIN_Z']; hh_ = P['PN_HDR_H']
    xa_, xb_ = sorted((rx_ + s_*P['HDR_R_BEND'], rx_ + s_*(P['HDR_R_BEND'] + P['HDR_R_BODY'])))
    body_ = box(xa_, cy_ - bw_/2, zb_ - hh_, xb_ - xa_, bw_, hh_ + 0.01)
    tip_ = cx_ + s_*(P['PN_L']/2 + P['PN_PIN_OVER'])
    # SPI-Leiste 8-pol. an der langen Kante +s*y, abgewinkelt nach aussen
    sx0_, sx1_, ry_ = pn_spi(i, j); sm_ = (sx0_ + sx1_)/2; sw_ = 8 * PITCH
    ya_, yb_ = sorted((ry_ + s_*P['HDR_R_BEND'], ry_ + s_*(P['HDR_R_BEND'] + P['HDR_R_BODY'])))
    stip_ = cy_ + s_*(P['PN_W']/2 + P['PN_PIN_OVER'])
    spi_cut_ = "%d%d" % (i, j) in P['PN_SPI_CUT'].split(",")   # 27.11.: SPI-Leiste abgekniffen -> nur senkrechte Stummel
    sbody_ = None if spi_cut_ else box(sm_ - sw_/2, ya_, zb_ - hh_, sw_, yb_ - ya_, hh_ + 0.01)
    hdr_ = body_.fuse(sbody_) if sbody_ else body_.copy()
    for k_ in range(8):
        xk = sm_ + (k_ - 3.5) * PITCH
        ver = box(xk - 0.32, ry_ - 0.32, zpin - 0.32, 0.64, 0.64, zt_ + P['PN_TAIL'] - (zpin - 0.32))
        hdr_ = hdr_.fuse(ver)
        if not spi_cut_:
            hdr_ = hdr_.fuse(box(xk - 0.32, min(ry_ - 0.32, stip_), zpin - 0.32, 0.64, abs(stip_ - ry_) + 0.32, 0.64))
    if sbody_: body_ = body_.fuse(sbody_)
    for k_ in range(4):
        yk = cy_ + (k_ - 1.5) * PITCH
        hor = box(min(rx_ - 0.32, tip_), yk - 0.32, zpin - 0.32, abs(tip_ - rx_) + 0.32, 0.64, 0.64)
        ver = box(rx_ - 0.32, yk - 0.32, zpin - 0.32, 0.64, 0.64, zt_ + P['PN_TAIL'] - (zpin - 0.32))
        hdr_ = hdr_.fuse(hor).fuse(ver)
    pn_hdr[(i, j)] = dict(tip=tip_, row=rx_, side=s_, y=cy_, zpin=zpin, body=(xa_, xb_))
    rim_ = 1.5   # weisser Bestueckungsdruck/Antennenrahmen am Rand, nur Farbe
    inner_ = box(cx_ - P['PN_L']/2 + rim_, cy_ - P['PN_W']/2 + rim_, zb_ - 0.1, P['PN_L'] - 2*rim_, P['PN_W'] - 2*rim_, P['BRD_T'] + 0.2)
    pn_col[(i, j)] = dict(red=pcb_.common(inner_), ring=pcb_.cut(inner_), comp=comp_, body=body_, pins=hdr_.cut(body_), spi=(sm_ - sw_/2, sm_ + sw_/2, ya_, yb_, stip_))
    return pcb_.fuse(comp_), hdr_.removeSplitter()
for i in range(3):
    for j in range(3):
        brd_, hdr_ = pn_model(i+1, j+1)
        c_ = pn_col[(i+1, j+1)]; pn_brd[(i+1, j+1)] = brd_; pn_col[(i+1, j+1)]['hdr'] = hdr_
        add_parts("REF_PN532_%d%d" % (i+1, j+1), [("", [c_['red']], COL['PN532']), ("_Rand", [c_['ring']], COL['SILK']), ("_Bauteile", [c_['comp']], COL['BAUTEIL']),
                                                  ("_Stiftleiste", [c_['body']], COL['KUNSTSTOFF']), ("_Pins", [c_['pins']], COL['PIN'])])
        board_refs["PN532_%d%d" % (i+1, j+1)] = brd_.fuse(hdr_)
        plate_refs.append(board_refs["PN532_%d%d" % (i+1, j+1)])   # Reader bewegen sich mit der Platte -> Bewegungscheck
# Delock 87824 nach Zeichnung, V2 in der vorderen Wand: Kragen im Ausschnitt, Flansch innen, Gehaeuse, Knickschutz (+y)
y_f = Y_FL - P['USB_BOSS_T']
usb = box(UX - P['USB_BOSS_L']/2, y_f, zc - P['USB_BOSS_H']/2, P['USB_BOSS_L'], P['USB_BOSS_T'], P['USB_BOSS_H'])
usb = usb.fuse(box(UX - P['USB_FL_L']/2, Y_FL, zc - P['USB_FL_W']/2, P['USB_FL_L'], P['USB_FL_T'], P['USB_FL_W']))
body_l = P['USB_LEN'] - P['USB_BOSS_T'] - P['USB_FL_T'] - P['USB_STRAIN_L']
usb = usb.fuse(box(UX - P['USB_BODY_W']/2, Y_FL + P['USB_FL_T'], zc - P['USB_BODY_H']/2, P['USB_BODY_W'], body_l, P['USB_BODY_H']))
usb = usb.fuse(cyl(UX, Y_FL + P['USB_FL_T'] + body_l, zc, P['USB_STRAIN_D'], P['USB_STRAIN_L'], V(0, 1, 0)))
add("REF_USB_C_Buchse", usb, (0.12, 0.12, 0.12))
# Stecker P1 im USB-C des ESP32 (ESP um 180 Grad gedreht: USB-Ende zeigt nach +x zur Wickelkammer)
x_usb = 2*esp_[2] - _eo[0]; esp_port_z = Z_BT + P['ESP_USB_H']/2
plug_ref = box(x_usb + 0.5, PLUG_Y - P['PLUG_W']/2, esp_port_z - P['PLUG_T']/2, P['PLUG_L'], P['PLUG_W'], P['PLUG_T'])
add("REF_USB_Stecker_ESP32", plug_ref, COL['METALL'])
# 27.11.: gekuerztes Delock-Kabel in zwei Stuecken (Buchse -> Hub, Hub -> Stecker), Spleiss am Hub; Hub mit JP_NFC und Elko (Referenz)
x_pe = x_usb + 0.5 + P['PLUG_L']
ZCB = FLOOR + CD/2 + 0.1; YSP = HY0 + HL + 4.0                  # Kabel liegt am Boden; Spleiss hinter dem Hub
def tube_(pts, d):
    sh_ = None
    for a_, b_ in zip(pts, pts[1:]):
        va, vb = V(*a_), V(*b_); c_ = Part.makeCylinder(d/2, (vb - va).Length, va, vb - va)
        sh_ = c_ if sh_ is None else sh_.fuse(c_)
    for p_ in pts[1:-1]: sh_ = sh_.fuse(Part.makeSphere(d/2, V(*p_)))
    return sh_.removeSplitter()
CAB_A = [(UX, USB_END_Y, zc), (UX, YSP, ZCB), (HX0 + 3.0, YSP, ZCB)]
XCB = HX0 + HW - 4.0
CAB_B = [(XCB, YSP, ZCB), (XCB, PLUG_Y, ZCB), (x_pe + 14.0, PLUG_Y, esp_port_z), (x_pe, PLUG_Y, esp_port_z)]
cab_usb = tube_(CAB_A, CD); cab_plug = tube_(CAB_B, CD)
add("REF_USB_Kabel_Buchse", cab_usb, (0.15, 0.15, 0.15)); add("REF_USB_Kabel_Stecker", cab_plug, (0.15, 0.15, 0.15))
hub_pcb = box(HX0, HY0, HUB_ZB, HW, HL, P['BRD_T'])
for (xh_, yh_) in HUB_HOLES: hub_pcb = hub_pcb.cut(cyl(xh_, yh_, HUB_ZB - 1, P['TCA_HOLE'], P['BRD_T'] + 2))
jp_ = box(JP_X0, JP_Y0, HUB_ZB - P['JP_H'], 2*PITCH, PITCH, P['JP_H'])
el_ = cyl(HX0 + HW/2, HY0 + HL/2 - P['ELKO_L']/2 + 1.5, FLOOR + 0.2 + P['ELKO_D']/2, P['ELKO_D'], P['ELKO_L'], V(0, 1, 0))
add_parts("REF_Hub", [("", [hub_pcb], COL['PN532']), ("_JP_NFC", [jp_], (0.85, 0.1, 0.1)), ("_Elko", [el_], (0.1, 0.25, 0.6))])
hub_refs = [hub_pcb, jp_, el_]

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
    _v_cc = carrier.common(cover).Volume
    line("Traeger/Deckel gueltig: %s/%s, Volumen %.0f/%.0f mm3, Ueberschneidung %.3f mm3 (Soll 0)" % (carrier.isValid(), cover.isValid(), carrier.Volume, cover.Volume, _v_cc))
    line("Trennebene z=%.2f: Traeger %.2f mm, Deckel %.2f mm (Boden %.2f); ueber den Readern: Deckelboden %.2f + Druckplatte %.2f mm" % (Z_SPLIT, Z_SPLIT - Z_UP, Z_TOP - Z_SPLIT, P['COVER_FLOOR'], P['COVER_FLOOR'], Z_SPLIT - (Z_PNB + P['BRD_T'] + P['PN_SEAT_CLR'])))
    if COVER_PINS:
        line("Passzapfen Deckel->Traeger: %d Stueck D%.1f x %.2f (= Druckplattenhoehe), Bohrung D%.1f tief %.2f mit %d Quetschrippen, Fase %.1f; Lage: %s" % (
            len(COVER_PINS), P['COVER_PIN_D'], PIN_L, P['COVER_PIN_HOLE'], PIN_DEPTH, int(P['CRUSH_N']), P['COVER_PIN_CH'], " ".join("(%.1f|%.1f)" % q for q in COVER_PINS)))
        line("  Zapfen - Quetschrippe min %.2f mm (Soll 0,00 = Nennmass, Presssitz durch Druckschwund), Zapfen - Bohrungswand %.2f radial, Restwand >= %.1f mm geprueft, Luft unter Zapfen 0,50" % (
            min(cyl(px_, py_, Z_SPLIT - PIN_L, P['COVER_PIN_D'], PIN_L).distToShape(carrier)[0] for px_, py_ in COVER_PINS), (P['COVER_PIN_HOLE'] - P['COVER_PIN_D'])/2, P['COVER_PIN_WALL']))
        line("  Druckauflage Deckel: Zapfen, Druckplatten und Randleisten enden alle bei z=%.2f: %s" % (Z_SPLIT - PIN_L, abs(cover.BoundBox.ZMin - (Z_SPLIT - PIN_L)) < 0.01))
    if PIN_MISS: line("  Zielpunkte ohne Platz fuer Passzapfen: %s  <-- pruefen" % " ".join("(%.0f|%.0f)" % q for q in PIN_MISS))
    hidden = all(cover.isInside(V(hx, c['y'], Z_SPLIT + P['COVER_FLOOR']/2), 1e-3, True) for c in cells for hx in c['free_xs'])
    line("Schraubenkoepfe Freiende vom Deckel verdeckt: %s (Kopfoberkante %.2f unter Trennebene)" % (hidden, Z_SPLIT - (Z_HEAD_SEAT + 4.0)))
line("Formen gueltig: Unterteil=%s Oberteil%s=%s" % (lower.isValid(), "" if VARIANT == "einteilig" else " (Traeger+Deckel)", upper.isValid()))
line("Volumen: Unterteil=%.0f mm3, Oberteil=%.0f mm3" % (lower.Volume, upper.Volume))
_v_lu = lower.common(upper).Volume
line("Ueberschneidung Unter/Oberteil: %.3f mm3 (erwartet 0)" % _v_lu)
# ---------------- V2 LEITUNGEN (Platzhalter) ----------------
# Buendel als Rohr (Durchmesser aus Kreispackung der Litzen), in Nuten und unter Spalte 3 / ueber den TCAs als flaches Band.
# Abgang am Reader = Readermitte (PLATZHALTER, Pinseite offen). Strang = durchgeschleifte Versorgung (NP Adern), Daten = SDA+SCL je Reader.
def bd(n): return P['LITZE_D'] * {1: 1.0, 2: 2.0, 3: 2.155, 4: 2.414, 5: 2.701, 6: 3.0, 7: 3.0, 8: 3.304, 9: 3.613, 10: 3.813}.get(n, 4.0)
def tube(pts, d):
    sh_ = None
    for a_, b_ in zip(pts, pts[1:]):
        va, vb = V(*a_), V(*b_); c_ = Part.makeCylinder(d/2, (vb - va).Length, va, vb - va)
        sh_ = c_ if sh_ is None else sh_.fuse(c_)
    for p_ in pts[1:-1]: sh_ = sh_.fuse(Part.makeSphere(d/2, V(*p_)))
    return sh_.removeSplitter()
def plen(pts): return sum((V(*b_) - V(*a_)).Length for a_, b_ in zip(pts, pts[1:]))
NP = int(P['NP_WIRES']); LD = P['LITZE_D']
def ZW(n): return Z_UP - bd(n)/2 - 0.2                      # haengt direkt unter Platte / Reader-Unterseite
ZG0, ZG1 = Z_UP + GL + 0.25, Z_UP + GD - 0.05                  # Band in der Nut ueber den Haltelippen
Z_BAND_TCA = Z_UP - P['TCA_GAP'] + P['HDR_PIN_ABOVE'] + 0.25   # Band ueber den Pinenden der TCAs
ZB1 = Z_UP - 0.2                                               # Unterkante Platte/Reader minus Luft
ZT = 9.5                                                       # Anloethoehe an TCA-Stiftleisten (Pins 5,4-11,4)
def flat(x0, y0, x1, y1, n, layers, z_top):                    # flaches Band zwischen zwei Punkten (achsparallel)
    w_ = math.ceil(n / layers) * LD; h_ = layers * LD
    if abs(y1 - y0) < 1e-6: return box(min(x0, x1), y0 - w_/2, z_top - h_, abs(x1 - x0), w_, h_)
    return box(x0 - w_/2, min(y0, y1), z_top - h_, w_, abs(y1 - y0), h_)
def groove_band_x(gy, n): return box(50 - (50 - pw_)/2, gy - (GW - 0.2)/2, ZG0, 50 - pw_, GW - 0.2, ZG1 - ZG0)       # Nut quer durch x-Steg 50
def groove_band_y(gx, gy, n): return box(gx - (GW - 0.2)/2, gy - (50 - pl_)/2, ZG0, GW - 0.2, 50 - pl_, ZG1 - ZG0)  # Nut quer durch y-Steg
# V2 umgedreht: Litzen an den horizontalen Pins der Stiftleisten (unter der Platte) angeloetet. Baender laufen direkt unter den Pins
#  (Oberkante ZBT), neben den Kunststoffkoerpern vorbei (Daten auf der -y-Seite, Versorgung auf der +y-Seite der Leiste).
#  Waegezellen-Baender (y 43,7..56,4 / 93,7..106,4, x 37,5..112,5) werden links (x 34) und rechts (x 116,3) umgangen.
ZBT = Z_UP - 1.3                                               # Bandoberkante: 0,2 unter den Pins
def apx(i, j): h_ = pn_hdr[(i, j)]; return (h_['tip'] + (h_['body'][1] if h_['side'] > 0 else h_['body'][0])) / 2   # Mitte freie Pinlaenge
def chain(pts, n, layers=1, z_top=None):                       # Folge achsparalleler Baender
    z_top = ZBT if z_top is None else z_top
    sh_ = None; L_ = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        b_ = flat(x0, y0, x1, y1, n, layers, z_top); L_ += abs(x1 - x0) + abs(y1 - y0)
        sh_ = b_ if sh_ is None else sh_.fuse(b_)
    return sh_, L_
def drop(x_, y_, n, x_end):                                    # senkrecht neben der TCA-Platine hinunter zur Stiftleiste (Loethoehe ZT)
    pts_ = [(x_, y_, ZBT - bd(n)/2), (x_, y_, ZT + 1.0), (x_end, y_, ZT)]; return tube(pts_, bd(n)), plen(pts_), (x_end, y_)
plate_wires = []; base_wires = []; loop_wires = []; wire_tab = []
WIRE_PATHS = []   # 26.11.: Bandverlauf (2D) + Ende an der TCA-Stiftleiste, fuer die Einzeladern-Ansicht (gehaeuse/pruefberichte/kabelwege_v2.json)
def W(lst, name, n, shape, length):
    lst.append((name, n, shape)); wire_tab.append((name, n, length, lst is plate_wires and "Platte" or lst is base_wires and "Unterteil" or "Schlaufe"))
def WC(name, n, pts, layers=1, extra=None):
    sh_, L_ = chain(pts, n, layers)
    if extra is not None: sh_ = sh_.fuse(extra[0]); L_ += extra[1]
    W(plate_wires, name, n, sh_, L_)
    WIRE_PATHS.append(dict(name=name, n=n, pts=[list(q) for q in pts], layers=layers, drop=list(extra[2]) if extra is not None and len(extra) > 2 else None))
YD = lambda j: 25 + 50*(j-1) - 7.6; YS = lambda j: 25 + 50*(j-1) + 7.6   # Daten- / Versorgungsseite der Leiste
a11, a21, a31 = apx(1, 1), apx(2, 1), apx(3, 1); a12, a22, a32 = apx(1, 2), apx(2, 2), apx(3, 2); a13, a23, a33 = apx(1, 3), apx(2, 3), apx(3, 3)
XL, XR = 35.3, 116.3                                           # Umgehung der Zellen links / rechts
# 26.11.: links um die Zellen mehr Luft (vorher 0,9 mm zu Zelle 1 / ESP32-Modul). Kanaele in der Traegerunterseite waeren hier wirkungslos:
#  die Engstellen liegen seitlich neben Zelle bzw. Modul, direkt ueber dem Band sitzen die Reader-Pins. Statt dessen Bandlage verschoben.
XL0 = 33.3                                                     # Daten 11+21: links an Zelle 1 (Festende x 37,5, Kabelaustritt + Kleber) vorbei
XL3a, XL3b, Y3J = 36.3, 33.9, 109.0                            # Daten 13+23: neben ESP32-Modul (bis x 33,1) rechts, an Zelle 2 (ab x 37,5) links vorbei, Versatz bei y 109
tA, tB = board_refs["TCA9548A_A"].BoundBox, board_refs["TCA9548A_B"].BoundBox
xAl = tA.XMin - bd(6)/2 - 0.3; xAr = tA.XMax + bd(2)/2 + 0.3; xBr = tB.XMax + bd(4)/2 + 0.3
# --- Daten (SDA+SCL je Reader) ---
WC("Daten 11 + 21 -> TCA_A (links um Zelle 1)", 4, [(a21, YD(1)), (XL0, YD(1)), (XL0, 66.7), (xAl, 66.7)], 2)
WC("Daten 12 + 11/21 -> TCA_A (Loetpunkt links)", 6, [(a12, 73.0), (a12, 66.7), (xAl, 66.7)], 1, drop(xAl, 66.7, 6, tA.XMin + 0.2))
WC("Daten 22 -> TCA_A (Loetpunkt rechts)", 2, [(a22, 73.0), (a22, 67.4), (xAr, 67.4)], 1, drop(xAr, 67.4, 2, tA.XMax - 0.2))
Y3D = max(YD(3), esp_[3] - P['ESP_Y']/2 + P['ESP_JMP_W'] + 0.8 + 1.3)   # 27.11.: Band hinter den ESP32-Jumper (UART-Seite) verlegt, 0,8 Luft
WC("Daten 13 + 23 -> TCA_A (links um Zelle 2)", 4, [(a23, Y3D), (XL3a, Y3D), (XL3a, Y3J), (XL3b, Y3J), (XL3b, 88.0), (xAl, 88.0)], 2, drop(xAl, 88.0, 4, tA.XMin + 0.2))
WC("Daten 31 -> TCA_B (rechts um Zelle 1)", 2, [(a31, YD(1)), (XR, YD(1)), (XR, 67.4), (xBr, 67.4)])
WC("Daten 32 + 31 -> TCA_B (Loetpunkt rechts)", 4, [(a32, 73.0), (a32, 67.4), (xBr, 67.4)], 1, drop(xBr, 67.4, 4, tB.XMax - 0.2))
WC("Daten 33 -> TCA_B (rechts um Zelle 2)", 2, [(a33, YS(3)), (XR, YS(3)), (XR, 82.6), (xBr, 82.6)], 1, drop(xBr, 82.6, 2, tB.XMax - 0.2))
# --- Versorgung (NP Adern, Reihe durchgeschleift) ---
vtb = board_refs["Loetverteiler"].BoundBox; ZVB = vtb.ZMin + 0.3; xv = vtb.XMax - 4.0
pts = [(xv, vtb.YMin + 1.0, ZVB), (xv, vtb.YMin - 2.0, ZBT - bd(NP)/2)]
WC("Strang Reihe 1: Verteiler -> 11 -> 21 -> 31", NP, [(xv, vtb.YMin - 2.0), (xv, YS(1)), (a31, YS(1))], 1, (tube(pts, bd(NP)), plen(pts)))
pts = [(xv, vtb.YMax - 1.0, ZVB), (xv, vtb.YMax + 2.0, ZBT - bd(NP)/2)]
WC("Strang Reihe 2/3: Verteiler -> 12 -> 22 -> 32 (ueber TCA_A/B)", NP, [(xv, vtb.YMax + 2.0), (xv, YS(2)), (a32, YS(2))], 1, (tube(pts, bd(NP)), plen(pts)))
WC("Strang Reihe 3: -> 13 -> 23 -> 33", NP, [(xv, YS(2)), (xv, YS(3)), (a33, YS(3))])
# --- TCA-Versorgung + Bus (4 Adern) ---
# 26.11.: TCA_A gedreht -> Bus an die RECHTE Leiste (JP3). Weg: am Verteiler hoch in die Readertasche 12, flach durch die Nut in Steg A (y 68),
#  in Tasche 22 auf y 63,5 (neben Daten 22) und rechts neben TCA_A hinunter zur Leiste. Kanaele: links JP1 (Kanal 2-7) fuer 11, 12, 13, 21, 23; rechts Kanal 0 fuer 22.
gyB = GROOVES[0][3]; zBus = ZG0 + 0.1; xBd = tA.XMax + 2.5; yBd = 63.5
pts1 = [(vtb.XMax - 0.6, vtb.YMax - 1.0, ZVB), (vtb.XMax + 0.4, 60.0, Z_UP - 0.2), (vtb.XMax + 0.4, gyB, zBus + LD/2)]
fb_ = box(vtb.XMax + 0.4, gyB - 2*LD, zBus, xBd - (vtb.XMax + 0.4), 4*LD, LD)                      # flaches Band 4 Litzen, durch Tasche 12, Nut, Tasche 22
pts2 = [(xBd, gyB, zBus + LD/2), (xBd, yBd, zBus + LD/2), (xBd, yBd, ZT + 0.5), (tA.XMax - 0.2, yBd, ZT)]
W(plate_wires, "Verteiler -> TCA_A (Versorgung + Bus)", 4, tube(pts1, bd(4)).fuse(fb_).fuse(tube(pts2, bd(4))).removeSplitter(), plen(pts1) + (xBd - vtb.XMax - 0.4) + plen(pts2))
WIRE_PATHS.append(dict(name="Verteiler -> TCA_A (Versorgung + Bus)", n=4, pts=[[q[0], q[1]] for q in pts1[:1] + [(vtb.XMax + 0.4, pts1[0][1]), (vtb.XMax + 0.4, gyB), (xBd, gyB), (xBd, yBd), (tA.XMax - 0.2, yBd)]], layers=1, drop=None))
pts = [(tA.XMax - 0.2, 78.0, ZT), (tA.XMax + 2.0, 78.0, 14.5), (tB.XMin - 2.0, 78.0, 14.5), (tB.XMin + 0.2, 78.0, ZT)]
W(plate_wires, "TCA_A -> TCA_B (Versorgung + Bus, unter Reader 22)", 4, tube(pts, bd(4)), plen(pts))
WIRE_PATHS.append(dict(name="TCA_A -> TCA_B (Versorgung + Bus, unter Reader 22)", n=4, pts=[[q[0], q[1]] for q in pts], layers=1, drop=None))
import json as _json
_json.dump(dict(stand=__import__("time").strftime("%Y-%m-%d %H:%M"), NP=NP, LITZE_D=LD, pitch=PITCH, YD=[YD(j) for j in (1, 2, 3)], YS=[YS(j) for j in (1, 2, 3)],
                verteiler=[vtb.XMin, vtb.YMin, vtb.XMax, vtb.YMax], xv=xv, tca={"A": [tA.XMin, tA.YMin, tA.XMax, tA.YMax], "B": [tB.XMin, tB.YMin, tB.XMax, tB.YMax]},
                readers={"%d%d" % k_: dict(cy=h_['y'], tip=h_['tip'], row=h_['row'], side=h_['side'], apx=apx(*k_), pin_y=[h_['y'] + (q_ - 1.5) * PITCH for q_ in range(4)]) for k_, h_ in pn_hdr.items()},
                paths=WIRE_PATHS), open(os.path.join(outdir_bericht, "kabelwege_v2.json"), "w"), indent=1)
# --- Unterteil (fest): HX711 -> ESP32, ESP32 -> Gabel ---
esp_n, _, ecx, ecy, _, _ = [b for b in boards if b[0] == "ESP32_C6"][0]
yE = ecy - P['ESP_Y']/2 - 1.0
def ZF(n): return FLOOR + bd(n)/2 + 0.1
hxa = [b for b in boards if b[0] == "HX711_A"][0]; hxb = [b for b in boards if b[0] == "HX711_B"][0]
xJa = hxa[2] + P['HX_X']/2 + 1.3; xJb = hxb[2] + P['HX_X']/2 + 1.3; YH = 39.5
pts = [(xJb, hxb[3], 6.0), (xJb, YH, ZF(4)), (xJa + 0.01, YH, ZF(4))]; W(base_wires, "HX711_B -> Sammelpunkt", 4, tube(pts, bd(4)), plen(pts))
pts = [(xJa, hxa[3], 6.0), (xJa, YH, ZF(8))]; W(base_wires, "HX711_A -> Sammelpunkt", 4, tube(pts, bd(4)), plen(pts))
pts = [(xJa, YH, ZF(8)), (10, YH, ZF(8)), (10, 104, ZF(8)), (ecx - 12, yE, 6.0)]; W(base_wires, "HX711_A+B -> ESP32 (Gabeln x10)", 8, tube(pts, bd(8)), plen(pts))
pts = [(ecx - 2, yE, 6.0), (ecx - 2, yE - 6, ZF(4)), (LINK_CLIP[0], LINK_CLIP[1] + 8, ZF(4)), (LINK_CLIP[0], LINK_CLIP[1] + 2.5, 6.5)]
W(base_wires, "ESP32 -> Gabel (Versorgung + Bus)", 4, tube(pts, bd(4)), plen(pts))
pts = [(LINK_CLIP[0], LINK_CLIP[1] + 2.5, 6.5), (LINK_CLIP[0], LINK_CLIP[1] - 3, 8.5), (LINK_CLIP[0], 59.5, 12.0), (LINK_CLIP[0], 56, ZVB)]
W(loop_wires, "Schlaufe Gabel -> Verteiler (ueber den Waegespalt)", 5, tube(pts, bd(5)), plen(pts) + 15)
xh5_ = HX0 + 1.5*PITCH; zf1_ = ZF(1)
pts = [(xh5_, HY0 + HL - 3.0, HUB_ZT + 0.7), (xh5_, YSP + 1.0, HUB_ZT + 0.7), (HX0 - 2.5, YSP + 4.0, 9.5), (HX0 - 2.5, YSP + 10.0, zf1_),
       (HX0 - 2.5, 75.0, zf1_), (34.0, 75.0, zf1_), (LINK_CLIP[0] + 2.0, LINK_CLIP[1] + 4.0, zf1_), (LINK_CLIP[0], LINK_CLIP[1] + 2.5, 6.5)]
W(base_wires, "Hub -> Gabel (5V_NFC, unter den TCAs)", 1, tube(pts, bd(1)), plen(pts))
pts = [(HX0 + 3.0, YSP, ZCB), (HX0 + 3.0, HY0 + HL + 1.2, HUB_ZT + 0.7), (HX0 + 3.0, HY0 + HL - 7.5, HUB_ZT + 0.7), (XCB, HY0 + HL - 7.5, HUB_ZT + 0.7), (XCB, HY0 + HL + 1.2, HUB_ZT + 0.7), (XCB, YSP, ZCB)]
W(base_wires, "Delock-Adern am Hub (VBUS/GND auf Streifen, D+/D- Spleiss)", 4, tube(pts, bd(4)), plen(pts))
for (nm_, n_, sh_) in plate_wires: add("REF_Litze_P_" + nm_.split(" ")[0] + "_%d" % len([o for o in doc.Objects if o.Name.startswith("REF_Litze")]), sh_, (0.95, 0.75, 0.1))
for (nm_, n_, sh_) in base_wires: add("REF_Litze_U_%d" % len([o for o in doc.Objects if o.Name.startswith("REF_Litze")]), sh_, (0.2, 0.55, 0.9))
for (nm_, n_, sh_) in loop_wires: add("REF_Litze_Schlaufe", sh_, (0.85, 0.2, 0.75))
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
line("Silikon/Kabel an der Zelle (Nutzer 27.11.): oben/unten %.1f mm auf %.2f-%.2f mm ab Festende (+-%.1f), seitlich %.1f+%.1f mm auf der Kabelseite ab Festende, Kabelaustritt hinter dem Festende %.0f mm" % (
    P['SIL_T'], P['SIL_X0'], P['SIL_X1'], P['SIL_TOL'], P['SIL_SIDE'], P['SIL_SIDE_TOL'], P['CABLE_EXIT_L']))
line("  Luft Silikon/Kabel - Traeger %.2f (Soll >= %.2f), - Unterteil %.2f, Kabelaustritt - Unterteil %.2f, - Plattenteile (Boards/Leitungen) %.2f mm; Verdrehsicherung nur auf der kabelfreien Seite" % (
    min(sil_refs[k][0].distToShape(upper)[0] for k in sil_refs), P['CLR_TOP'], min(sil_refs[k][0].distToShape(lower)[0] for k in sil_refs),
    min(sil_refs[k][1].distToShape(lower)[0] for k in sil_refs), min(sil_refs[k][q].distToShape(pr_)[0] for k in sil_refs for q in (0, 1) for pr_ in plate_refs)))
line("--- Bewegungscheck Platte bis Anschlag (Kippen um Freiende-Achse, Absenken, Verschieben) ---")
pa = V(sum(cells[0]['free_xs'])/2, cells[0]['y'], Z_UP); pb = V(sum(cells[1]['free_xs'])/2, cells[1]['y'], Z_UP)
ax_ = pb - pa
def sdist(x, y): return ((V(x, y, Z_UP) - pa).cross(ax_)).z / ax_.Length
dpos = max(sdist(x, y) for x, y in stops) + P['POST_D']/2; dneg = -min(sdist(x, y) for x, y in stops) + P['POST_D']/2   # Sockelkante beruehrt zuerst
corner_d = max(abs(sdist(x, y)) for x in (OFF, OFF + P['PLATE']) for y in (OFF, OFF + P['PLATE']))
def mv_rot(sh_, a_): c_ = sh_.copy(); c_.rotate(pa, ax_, a_); return c_
def mv_tr(sh_, v_): c_ = sh_.copy(); c_.translate(v_); return c_
moves = []
for s_, dd in ((1, dpos), (-1, dneg)):
    ang = math.degrees(0.98 * P['STOP_GAP'] / dd)
    moves.append(("Kippen %+.3f Grad" % (s_ * ang), (lambda a__: (lambda sh_: mv_rot(sh_, a__)))(s_ * ang)))
moves.append(("Absenken %.2f" % (0.98 * P['STOP_GAP']), lambda sh_: mv_tr(sh_, V(0, 0, -0.98 * P['STOP_GAP']))))
lat = 0.98 * (P['PIN_HOLE'] - P['PIN_D']) / 2
for v_ in (V(lat, 0, 0), V(-lat, 0, 0), V(0, lat, 0), V(0, -lat, 0)):
    moves.append(("Verschieben (%.2f|%.2f)" % (v_.x, v_.y), (lambda vv: (lambda sh_: mv_tr(sh_, vv)))(v_)))
fixed_refs = [w_[2] for w_ in base_wires] + base_refs + hub_refs + [doc.getObject(k).Shape for k in ("REF_USB_C_Buchse", "REF_USB_Stecker_ESP32", "REF_USB_Kabel_Stecker", "REF_USB_Kabel_Buchse")] + [q_ for k_ in sil_refs for q_ in sil_refs[k_]]
worst = 0.0
for nm_, T_ in moves:
    vol_ = lower.common(T_(upper)).Volume
    who_ = []
    for pn__, pr_ in [(k_, board_refs[k_]) for k_ in board_refs if board_mount.get(k_, "platte") == "platte"] + [(w_[0], w_[2]) for w_ in plate_wires]:
        tp_ = T_(pr_); v__ = lower.common(tp_).Volume + sum(tp_.common(f_).Volume for f_ in fixed_refs)
        vol_ += v__
        if v__ > 0.01: who_.append("%s %.2f" % (pn__, v__))
    worst = max(worst, vol_)
    if vol_ > 0.01: line("  BERUEHRUNG bei %s: %.2f mm3 (%s)" % (nm_, vol_, "; ".join(who_)))
line("Bewegungsfaelle: %d (Platte + Boards/Reader/Leitungen an der Platte), max. Ueberschneidung %.3f mm3 (Soll 0)" % (len(moves), worst))
line("Max. Eckabsenkung bis Anschlag: %.2f mm, Fuge Schuerze-Schulter / Kragen-Platte %.2f mm" % (P['STOP_GAP'] * corner_d / min(dpos, dneg), P['GAP_V']))
shoulder_ = lower.common(box(-10, -10, -1, P['MOD'] + 20, P['MOD'] + 20, Z_SHOULDER + 1.01))
collar_ = lower.common(box(-10, -10, Z_SHOULDER + 0.2, P['MOD'] + 20, P['MOD'] + 20, 20)).common(footprint(0, 0, 40).cut(footprint(C_IN + 0.01, -1, 42)))
line("Staubschutz Schuerze: Ueberdeckung %.1f mm; Luft waagerecht Schuerze-Kragen %.2f (Soll %.2f), senkrecht Schuerze-Schulter %.2f (Soll %.2f), Kragen-Platte %.2f (Soll %.2f)" % (
    P['SKIRT_H'] - P['GAP_V'], skirt.distToShape(collar_)[0], P['SKIRT_CLR'], skirt.distToShape(shoulder_)[0], P['GAP_V'], footprint(P['SKIRT_T'] + 0.01, Z_UP, 1).distToShape(collar_)[0], P['GAP_V']))
line("Verbinderfenster rechts: geschlossen (Wand durchgehend); offen bleibt nur der USB-C-Ausschnitt fuer die Einbaubuchse")
usb_s = doc.getObject("REF_USB_C_Buchse").Shape
line("Delock-Buchse (Masse Nutzer 27.11.): 2x M3-Senkschraube ISO 10642 von aussen durch Wand + Flansch (%.2f), Mutter M3 in der Flanschtasche; Senkung D%.1f, Restwand unter der Senkung %.2f mm -> M3x10" % (
    P['USB_FL_T'], P['USB_CSK_D'], (Y_FL - OFF) - (P['USB_CSK_D'] - P['USB_SCREW_D'])/2))
line("Delock-Buchse (V2: vordere Wand, x=%.1f): Flansch innen, Wand am Kragen %.1f mm, Abstand Buchse-Schuerze %.2f mm, Stirnflaeche %.1f mm hinter Aussenwand, Luft zum Anschlagsockel %.2f mm" % (UX, Y_FL - OFF, usb_s.distToShape(skirt)[0], y_f - OFF, min(usb_s.distToShape(p_)[0] for p_ in posts)))
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
line("Gesamt: 8x M4x%d DIN 912, 4x Scheibe DIN 125 M4 (nur Festende); USB-Buchse 2x M3x10 ISO 10642 (Senkkopf) + 2x Mutter M3 DIN 934" % P['M4_LEN'])
line("--- Platinen (Pins nach unten) ---")
line("Luft Pinreihen - Unterteil, alle Richtungen: min %.2f (Soll >= 0,4; Pinspitze zum Boden %.2f)" % (min(p_.distToShape(lower)[0] for p_ in pin_refs), P['BRD_POST'] - P['HDR_PLASTIC'] - P['HDR_PIN_BELOW']))
line("Luft hoechstes Bauteil (Boards unten) - Plattenunterseite: min %.2f mm" % min(r_.distToShape(upper)[0] for r_ in base_refs))
line("Luft Platinen - Waegezellen: min %.2f mm" % min(r_.distToShape(cell_shapes[k])[0] for r_ in board_refs.values() for k in cell_shapes))
line("Luft Boards - Stuetzen/Fuehrungen: min %.2f mm (gewollt: 0,10 = Rasthaken-Nase, 0,20 = Stirnwand unter Antennen-/USB-Ueberstand)" % min(r_.distToShape(s_)[0] for r_ in base_refs for s_ in board_support if r_.distToShape(s_)[0] > 1e-6))
line("Board-Halterung: alle Boards mit gedruckten Rasthaken (%d Stueck, kein Normteil); HX711/TCA9548A/Loetverteiler/Power-Hub zusaetzlich lose Zentrierzapfen, ESP32 Auflagen + Fuehrungen" % len(hooks))
pn_rows = []
for (nm_, bn_, hk, Lh, mt_) in hooks:
    dfl = (P['PN_HOOK_OVER'] if bn_.startswith("PN532") else P['HOOK_OVER']) + P['HOOK_CLR']; eps = 1.5 * P['HOOK_T'] * dfl / Lh**2 * 100
    if bn_.startswith("PN532"):
        pn_rows.append((hk.distToShape(board_refs[bn_])[0], min(hk.distToShape(s_)[0] for s_ in plate_support if s_ is not hk), Lh, eps)); continue
    others = min(hk.distToShape(s_)[0] for s_ in (board_support if mt_ == "unten" else plate_support) if s_ is not hk)
    line("  Rasthaken %-22s %-6s Abstand Board %.2f, Luft zu Nachbarteilen %.2f, Arm %.1f mm, Dehnung %.2f %% (<= 2 %%)" % (nm_ + ":", mt_, hk.distToShape(board_refs.get(bn_, hub_pcb))[0], others, Lh, eps))
if pn_rows:
    line("  Rasthaken PN532: %d Stueck (2 je Reader, Kanten %s), Abstand Board min %.2f, Luft zu Nachbarteilen min %.2f, Arm %.1f mm, Dehnung max %.2f %% (<= 2 %%), Nase %.1f unter Platinenkante" % (
        len(pn_rows), "+-x Spalte 2, +-y Spalte 1/3", min(r[0] for r in pn_rows), min(r[1] for r in pn_rows), min(r[2] for r in pn_rows), max(r[3] for r in pn_rows), P['PN_HOOK_OVER']))
    line("  PN532-Freistiche: Restwand zu Nuten/Senkungen/Stiftloechern/anderen Freistichen min %.2f mm (Soll >= 1,2); Versatz aus Readermitte: %s" % (
        min(r[4] for r in pn_hook_info), ", ".join("%d%d%s:%+.1f%s" % (a, b, "+" if s > 0 else "-", d, "" if w == hwp else "(B%.0f)" % w) for (a, b, s, d, _, w) in pn_hook_info)))
line("--- V2 Verdrahtung ---")
line("TCA9548A + Loetverteiler an der Traegerunterseite: Platine %.1f mm unter der Platte, Pinspitzen %.1f mm ueber dem Boden; Luft Plattenboards - Unterteil %.2f mm, - Zellen %.2f mm, - Boards unten %.2f mm; Luft Halter zur Platine %.2f mm" % (
    P['TCA_GAP'], Z_PB - P['HDR_PLASTIC'] - P['HDR_PIN_BELOW'] - FLOOR, min(r_.distToShape(lower)[0] for r_ in plate_refs), min(r_.distToShape(cell_shapes[k])[0] for r_ in plate_refs for k in cell_shapes),
    min(r_.distToShape(b_)[0] for r_ in plate_refs for b_ in base_refs), min(r_.distToShape(s_)[0] for r_ in plate_refs for s_ in plate_support if r_.distToShape(s_)[0] > 1e-6)))
line("Adern ueber den Waegespalt (Unterteil -> Platte): 5 (Elektronik 27.11.: 5V_NFC, 3V3, GND, SDA, SCL) als lockere Schlaufe von der Kabelgabel (%.0f|%.0f) zum Loetverteiler" % LINK_CLIP)
vt_ = board_refs["Loetverteiler"]
line("Loetverteiler (Streifenraster %.2f x %.2f, %d Streifen x %d Loecher, Kupfer unten): Platine %.1f mm unter der Platte, Unterkante Loetstellen %.1f mm ueber dem Boden, Luft zum Unterteil %.2f mm, zu Zellen %.2f mm" % (
    P['VT_L'], P['VT_W'], round(P['VT_W']/PITCH), round(P['VT_L']/PITCH) - 1, P['VT_GAP'], vt_.BoundBox.ZMin - FLOOR, vt_.distToShape(lower)[0], min(vt_.distToShape(cell_shapes[k])[0] for k in cell_shapes)))
line("  Belegung je Potential-Streifen: Zuleitung + TCA_A + TCA_B + 4 Straenge (11-21, 12-22, 13-23, 32-31/33) = 7 von 8 Loechern; SDA/SCL-Streifen: Zuleitung + TCA_A + TCA_B")
line("  Montage Loetverteiler: 2 Loecher D%.1f auf Streifen 3 (Reserve, %.2f vom Ende, Abstand %.2f), Abstandsbund D%.1f von der Platte (legt %.1f mm fest) + Zentrierzapfen + 2 Rasthaken; Streifen 3 behaelt 5 Loecher zwischen den Montageloechern" % (
    P['TCA_HOLE'], (P['HUB_HOLE_K'] + 0.5)*PITCH, P['VT_L'] - 2*(P['HUB_HOLE_K'] + 0.5)*PITCH, P['VT_STANDOFF_D'], P['VT_GAP']))
line("  Kanal-SDA/SCL der Reader laufen NICHT ueber den Verteiler (alle PN532 Adresse 0x24), sondern einzeln vom TCA-Kanal")
for (nm_, gcut) in groove_cuts:
    gr_ = gcut.common(box(-10, -10, Z_UP, 200, 200, 10))
    holes_ = [cyl(hx, c['y'], Z_UP - 0.1, P['M4_CLR'], 10) for c in cells for hx in c['free_xs']] + [cyl(sx, sy, Z_UP - 0.1, P['PIN_HOLE'], 10) for (sx, sy) in stops]
    line("  Kabelnut %-28s %.1f x %.1f mm, Luft zu Bohrungen %.2f mm, Platz fuer ca. %d Litzen" % (nm_ + ":", GW, GD, min(gr_.distToShape(h_)[0] for h_ in holes_), int((GW // P['LITZE_D']) * (GD // P['LITZE_D']))))
line("--- V2 PN532 umgedreht (Antenne/Bestueckung/Stiftleiste nach unten) ---")
hdr_objs = [pn_col[(i_, j_)]['hdr'] for i_ in (1, 2, 3) for j_ in (1, 2, 3)]
brd_objs = [pn_brd[(i_, j_)] for i_ in (1, 2, 3) for j_ in (1, 2, 3)]
pin_ov = max(h_['tip'] - (PNC(i_-1, j_-1)[0] + h_['side']*P['PN_L']/2) * 1 if h_['side'] > 0 else (PNC(i_-1, j_-1)[0] - P['PN_L']/2) - h_['tip'] for (i_, j_), h_ in pn_hdr.items())
tips_A = min(pn_hdr[(2, j_)]['tip'] - pn_hdr[(1, j_)]['tip'] for j_ in (1, 2, 3))
plugs_ = [pn_plug(i_, j_) for i_ in (1, 2, 3) for j_ in (1, 2, 3)]
posts_ = [q_ for i_ in (1, 2, 3) for j_ in (1, 2, 3) for q_ in pn_posts(i_, j_)]
line("Weg 3: Tasche durch den Traeger (von oben einlegen), Platine auf 4 Eckauflagen %.1f x %.1f in %.2f mm ueber der Plattenunterseite; Stiftleisten-Unterkante %.2f ueber der Plattenunterseite; Pins ragen %.2f mm ueber die Kante (Aussparung %.1f)" % (
    P['PN_POST'], P['PN_POST'], P['PN_Z0'], P['PN_Z0'] - P['PN_HDR_H'], pin_ov, P['PN_PIN_OVER'] + 0.3))
line("Deckel-Druckplatte: Luft zur Platinenrueckseite %.2f (Soll %.2f), zu Loetbeinen %.2f, zur Taschenwand %.2f; Reader - Eckauflage %.2f (Soll 0 = Auflage), Reader - Traeger sonst min %.2f" % (
    min(pl_.distToShape(b_)[0] for pl_ in plugs_ for b_ in brd_objs), P['PN_SEAT_CLR'], min(pl_.distToShape(h_)[0] for pl_ in plugs_ for h_ in hdr_objs),
    min(pl_.distToShape(carrier)[0] for pl_ in plugs_), max(min(b_.distToShape(q_)[0] for q_ in posts_) for b_ in brd_objs),
    min(b_.distToShape(carrier.cut(box(-10, -10, Z_PNB - 0.05, 200, 200, 0.1)))[0] for b_ in brd_objs) if False else min(h_.distToShape(carrier)[0] for h_ in hdr_objs)))
line("Stiftleiste - Traeger min %.2f mm (Loetbeine im Freistich), - Unterteil/Zellen/Boards unten min %.2f mm; Bestueckung - Unterteil/Boards unten min %.2f mm" % (
    min(h_.distToShape(upper)[0] for h_ in hdr_objs), min(h_.distToShape(f_)[0] for h_ in hdr_objs for f_ in [lower] + list(cell_shapes.values()) + base_refs + fixed_refs),
    min(b_.distToShape(f_)[0] for b_ in brd_objs for f_ in [lower] + list(cell_shapes.values()) + base_refs + fixed_refs)))
fx_all_ = [lower] + list(cell_shapes.values()) + base_refs + fixed_refs
pn_bad_ = []
for (i_, j_) in sorted(pn_col):
    hd_ = pn_col[(i_, j_)]['hdr']; dz_ = min(hd_.distToShape(f_)[0] for f_ in fx_all_); du_ = hd_.distToShape(upper)[0]
    dc_ = min(pn_brd[(i_, j_)].distToShape(f_)[0] for f_ in fx_all_)
    vc_ = sum(hd_.common(c__).Volume for c__ in cell_shapes.values()) + sum(pn_brd[(i_, j_)].common(c__).Volume for c__ in cell_shapes.values())
    if dz_ < 0.5 or du_ < 0.1 or dc_ < 0.5: pn_bad_.append((i_, j_))
    line("  Reader %d%d (I2C %s, SPI %s): Leisten/Pins - Zellen/Unterteil/Boards %.2f mm, - Traeger %.2f mm; Bestueckung/DIP - unten %.2f mm; Ueberschneidung mit Zellen %.1f mm3" % (
        i_, j_, "+x" if PN_I2C_SIDE[(i_, j_)] > 0 else "-x", ("+y" if PN_I2C_SIDE[(i_, j_)] > 0 else "-y") + (" abgekniffen" if "%d%d" % (i_, j_) in P['PN_SPI_CUT'].split(",") else ""), dz_, du_, dc_, vc_))
line("Reader mit Konflikt (Luft < 0,5 nach unten oder < 0,1 zum Traeger): %s" % (", ".join("%d%d" % q for q in pn_bad_) if pn_bad_ else "keine"))
line("Abstand Antenne (Platinenunterseite) - Behaelterboden Gridfinity: %.1f mm (vorher Oberseite 1,6 mm unter dem Boden); Reader-Mitten max %.2f mm aus der Feldmitte" % (
    (Z_TOP - GF_H) - Z_PNB, max(abs(PN_CX[i_] - (25 + 50*i_)) for i_ in range(3))))
line("--- V2 Leitungen (Platzhalter, Abgang Reader = Pins in der Taschen-Aussparung, Steigleitung ca. 3 mm vom Band zum Pin nicht modelliert, %d Versorgungsadern je Strang) ---" % NP)
line("  I2C-Kante je Reader (-x/+x): " + ", ".join("%d%d:%s" % (i_, j_, "+x" if PN_I2C_SIDE[(i_, j_)] > 0 else "-x") for i_ in (1, 2, 3) for j_ in (1, 2, 3)))
fixed_all = [lower] + [cell_shapes[k] for k in cell_shapes] + base_refs + [w_[2] for w_ in base_wires] + fixed_refs
for (nm_, n_, sh_) in plate_wires:
    line("  Platte    %-48s %2d Litzen, Luft zu Unterteil/Zellen/Boards/Leitungen unten %.2f mm" % (nm_, n_, min(sh_.distToShape(f_)[0] for f_ in fixed_all)))
plate_all = [upper] + plate_refs + [w_[2] for w_ in plate_wires]
for (nm_, n_, sh_) in base_wires:
    line("  Unterteil %-48s %2d Litzen, Luft zu Platte/Reader/Boards/Leitungen oben %.2f mm" % (nm_, n_, min(sh_.distToShape(f_)[0] for f_ in plate_all)))
for (nm_, n_, sh_) in loop_wires:
    line("  Schlaufe  %-48s %2d Litzen, Luft zu Zellen %.2f, zu Boards unten %.2f mm (beruehrt bewusst Gabel und Verteiler)" % (nm_, n_, min(sh_.distToShape(cell_shapes[k])[0] for k in cell_shapes), min(sh_.distToShape(b_)[0] for b_ in base_refs)))
tca_band_clr = min(w_[2].distToShape(board_refs[k])[0] for w_ in plate_wires if "ueber TCA" in w_[0] for k in ("TCA9548A_A", "TCA9548A_B"))
line("  Band ueber den TCAs: Luft zu TCA-Platine/Pins %.2f mm" % tca_band_clr)
tot_ = sum(n_ * L_ for (_, n_, L_, _) in wire_tab)
line("  Litzenbedarf (Summe Adern x Laenge, ohne Zellkabel): ca. %.1f m, mit 30 %% Zugabe %.1f m" % (tot_/1000, 1.3*tot_/1000))
line("  Nicht modelliert: Zellkabel Waegezelle -> HX711 (am Festende mit Schlaufe fuehren)")
ZONES = []   # V2 umgedreht: Leitungsfreiheit wird je Band oben geprueft
for (zn_, zb__) in ZONES:
    v_ = zb__.common(lower).Volume + sum(zb__.common(r_).Volume for r_ in base_refs) + sum(zb__.common(cell_shapes[k]).Volume for k in cell_shapes)
    line("  Leitungszone %-55s frei von Unterteil/Boards/Zellen: %s (%.2f mm3)" % (zn_ + ":", v_ < 0.01, v_))
cab_in_ = plen(CAB_A) + plen(CAB_B)
cab_tot_ = P['USB_LEN'] + cab_in_ + P['PLUG_L'] + 6.65
line("Delock-Kabel gekuerzt (Elektronik 27.11.): Buchse %.0f + Kabel im Gehaeuse %.0f (Buchse -> Hub %.0f, Hub -> Stecker %.0f) + Stecker %.0f = %.0f mm (Ziel ca. %.0f, Rest = Spleisszugabe %.0f mm)" % (
    P['USB_LEN'], cab_in_, plen(CAB_A), plen(CAB_B), P['PLUG_L'] + 6.65, cab_tot_, P['CABLE_LEN'], P['CABLE_LEN'] - cab_tot_))
hub_all_ = hub_pcb.fuse(jp_).fuse(el_)
line("Power-Hub %.2f x %.2f (6 Streifen x 8 Loecher) bei x %.1f-%.1f, y %.1f-%.1f, Unterseite z=%.1f (Bestueckung unten), Oberseite z=%.1f; auf 2 Domen D%.1f mit Zentrierzapfen in 2 Montageloechern D%.1f (Abstand %.2f) + 2 Rasthaken diagonal an den Langseiten (Endbereich)" % (
    HW, HL, HX0, HX0 + HW, HY0, HY0 + HL, HUB_ZB, HUB_ZT, P['TCA_STANDOFF_D'], P['TCA_HOLE'], HUB_HOLES[1][1] - HUB_HOLES[0][1]))
line("  Luft Hub - Unterteil %.2f, - Delock-Buchse/Kabel %.2f, - Zellen %.2f, - Platte/Reader/Bandleitungen %.2f mm (Oberseite: dort werden Adern angeloetet, Soll >= 2)" % (
    hub_all_.distToShape(lower)[0], min(hub_all_.distToShape(usb)[0], hub_all_.distToShape(cab_usb)[0], hub_all_.distToShape(cab_plug)[0]),
    min(hub_all_.distToShape(cell_shapes[k])[0] for k in cell_shapes), min([hub_all_.distToShape(upper)[0]] + [hub_all_.distToShape(w_[2])[0] for w_ in plate_wires] + [hub_all_.distToShape(r_)[0] for r_ in plate_refs])))
line("  JP_NFC zeigt nach unten: Kappenspitze z=%.1f (Boden 0..%.1f), Bodenfenster %.1f x %.1f mm -> Modul anheben, Jumper von unten ziehen; Elko D%.0f liegend, Luft zum Boden %.2f" % (
    HUB_ZB - P['JP_H'], FLOOR, HUB_WIN.BoundBox.XLength, HUB_WIN.BoundBox.YLength, P['ELKO_D'], el_.BoundBox.ZMin - FLOOR))
line("  Hub-Belegung im Modell: Streifen 1 VBUS_IN, 2 5V_NFC (-> Schlaufe), 3 GND; 3V3/SDA/SCL und HX711-Versorgung direkt am ESP32 (gleiche Netze wie Elektronik-Plan, kuerzere Wege)")
nub_clr = min(((P['HX_HOLE'] - P['HX_NUB_D'])/2, (P['TCA_HOLE'] - P['TCA_NUB_D'])/2))
line("Zentrierzapfen HX711/TCA: radial %.2f / %.2f mm (Soll >= 0,3, Druck wird dicker)" % ((P['HX_HOLE'] - P['HX_NUB_D'])/2, (P['TCA_HOLE'] - P['TCA_NUB_D'])/2))
line("--- Wandstaerken (rechnerisch) ---")
line("Reader-Spalten x = %.2f / %.2f / %.2f (Raster 25/75/125): Rand links %.2f, Steg A %.2f, Steg B %.2f, Rand rechts %.2f mm; Steg y %.2f mm" % (
    PN_CX[0], PN_CX[1], PN_CX[2], PN_CX[0] - PWX/2 - OFF, P['PN_STEG_A'], P['PN_STEG_B'], RIM_R, 50 - pl))
line("Restwand Stiftloch zur Tasche: %.2f mm (Steg B)" % (min(P['PN_STEG_A'], P['PN_STEG_B'])/2 - P['PIN_HOLE']/2))
cb_ = [cyl(hx, c['y'], Z_HEAD_SEAT, P['M4_TOP_CB'], Z_SPLIT - Z_HEAD_SEAT) for c in cells for hx in c['free_xs']]
pk_ = [q_ for i_ in (1, 2, 3) for j_ in (1, 2, 3) for q_ in pn_pocket_cuts(i_, j_)]
line("Restwand Kopfsenkung Freiende zur Readertasche: %.2f mm auf %.1f mm Hoehe (AUSNAHME < 1,2: Steg y nur %.1f)" % (min(a_.distToShape(b_)[0] for a_ in cb_ for b_ in pk_), Z_SPLIT - Z_HEAD_SEAT, 50 - pl))
if VARIANT == "deckel":
    st_ = [box(-10, OFF - 1, Z_UP, P['MOD'] + 20, 1 + P['COVER_LIP_W'] + P['COVER_LIP_CLR'], 20), box(-10, OFF + P['PLATE'] - P['COVER_LIP_W'] - P['COVER_LIP_CLR'], Z_UP, P['MOD'] + 20, 5, 20)]
    line("Deckel-Randleiste vorne/hinten %.1f x %.2f mm (Luft %.1f); Restwand Traeger-Stufe zur Readertasche/Pin-Aussparung: min %.2f mm (Soll >= 1,2)" % (
        P['COVER_LIP_W'], Z_SPLIT - (Z_PNB + P['BRD_T'] + P['PN_SEAT_CLR']), P['COVER_LIP_CLR'], min(a_.distToShape(b_)[0] for a_ in st_ for b_ in pk_)))
line("Restwand Readertaschen untereinander/zur Aussenwand (inkl. Pin-Aussparungen): min %.2f mm" % min([pk_[a].distToShape(pk_[b])[0] for a in range(len(pk_)) for b in range(a+1, len(pk_)) if a//3 != b//3] +
     [min(q_.BoundBox.XMin - OFF, q_.BoundBox.YMin - OFF, OFF + P['PLATE'] - q_.BoundBox.XMax, OFF + P['PLATE'] - q_.BoundBox.YMax) for q_ in pk_]))
ph_ = [k for k, v, st, q in PARAMS if st == "PLATZHALTER"]
line("--- offene PLATZHALTER (%d): %s" % (len(ph_), ", ".join(ph_)))
# ---------------- Zusammenfassung oben im Pruefbericht ----------------
# Harte Pruefungen + jeder Wert mit "(Soll x)", "(Soll >= x)", "(erwartet x)" oder "Dehnung x % (<= y %)" im Text.
# Zeilen mit "<--" sind Hinweise (bekannt, kein Fehler). Die Details darunter bleiben unveraendert.
import re as _re
_TOL = 0.001
_chk = [("Koerper gueltig (Unterteil, Oberteil)", lower.isValid() and upper.isValid()),
        ("Ueberschneidung Unter-/Oberteil 0", _v_lu < _TOL),
        ("Referenzteile ohne Kollision", bad == 0),
        ("Bewegungscheck ohne Ueberschneidung", worst < _TOL),
        ("Reader ohne Konflikt", not pn_bad_),
        ("USB-Stecker ohne Ueberschneidung", v_pl <= 0.01)]
if VARIANT == "deckel":
    _chk.insert(1, ("Traeger/Deckel gueltig, Ueberschneidung 0", carrier.isValid() and cover.isValid() and _v_cc < _TOL))
_rx_soll = _re.compile(r"(-?\d+\.\d+)\s*(?:mm3?\s*)?(?:radial\s*)?\((?:Soll|erwartet)\s*(>=|<=)?\s*(-?\d+(?:[.,]\d+)?)")
_rx_dehn = _re.compile(r"Dehnung (-?\d+\.\d+) % \(<= (\d+(?:[.,]\d+)?) %\)")
_n_soll = 0
for _l in L:
    for _m in _rx_soll.finditer(_l):
        _n_soll += 1
        _v, _op, _s = float(_m.group(1)), _m.group(2), float(_m.group(3).replace(",", "."))
        _ok = _v >= _s - 0.005 if _op == ">=" else (_v <= _s + 0.005 if _op == "<=" else abs(_v - _s) <= 0.005)
        if not _ok: _chk.append(("Sollwert: " + _l.strip()[:110], False))
    for _m in _rx_dehn.finditer(_l):
        _n_soll += 1
        if float(_m.group(1)) > float(_m.group(2).replace(",", ".")) + 0.005: _chk.append(("Dehnung: " + _l.strip()[:110], False))
_fehl = [n_ for n_, ok_ in _chk if not ok_]
_hinw = [l_.strip() for l_ in L if "<--" in l_]
_S = ["ZUSAMMENFASSUNG: %s  (%d Abweichungen; %d harte Pruefungen, %d Sollwerte geprueft; %d Hinweise; %d PLATZHALTER)" % (
      "OK" if not _fehl else "FEHLER", len(_fehl), len([c_ for c_ in _chk if not c_[0].startswith(("Sollwert:", "Dehnung:"))]), _n_soll, len(_hinw), len(ph_))]
_S += ["  FEHLER: " + n_ for n_ in _fehl] + ["  Hinweis: " + h_ for h_ in _hinw]
_S.append("=" * 100)
L[0:0] = _S
report = "\n".join(L)
td = doc.addObject("App::TextDocument", "Pruefbericht"); td.Text = report

# Uebersicht im Modellbaum: Objekte in Ordner sortieren (nur Anzeige, Pruefungen sind schon gelaufen)
def _grp(label, pred):
    objs_ = [o for o in doc.Objects if o.TypeId == "Part::Feature" and pred(o.Name)]
    if not objs_: return
    g_ = doc.addObject("App::DocumentObjectGroup", "Gruppe"); g_.Label = label
    for o in objs_: g_.addObject(o)
    return g_
_grp("1 Gehaeuse (Druckteile)", lambda n: n in ("Unterteil", "Oberteil", "Traeger", "Deckel"))
_grp("2 Waegezellen", lambda n: n.startswith("REF_Waegezelle"))
_rd = []; _bd = []
for i_ in (1, 2, 3):
    for j_ in (1, 2, 3):
        _rd.append(_grp("3 Reader PN532_%d%d" % (i_, j_), (lambda k_: (lambda n: n.startswith(k_)))("REF_PN532_%d%d" % (i_, j_))))
for b_ in ("ESP32_C6", "HX711_A", "HX711_B", "TCA9548A_A", "TCA9548A_B", "Loetverteiler"):
    _bd.append(_grp("4 Board " + b_, (lambda k_: (lambda n: n == k_ or n.startswith(k_ + "_")))("REF_" + b_)))
_grp("5 USB (Buchse, Stecker, Kabel)", lambda n: n.startswith("REF_USB"))
_grp("6 Litzen (Platzhalter)", lambda n: n.startswith("REF_Litze"))
_reader = doc.addObject("App::DocumentObjectGroup", "Gruppe_Reader"); _reader.Label = "3 Reader PN532 (9x)"
for o in _rd: _reader.addObject(o)
_boards = doc.addObject("App::DocumentObjectGroup", "Gruppe_Boards"); _boards.Label = "4 Boards"
for o in _bd: _boards.addObject(o)
doc.recompute()
if App.GuiUp:
    Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
# ---------------- Schnittstelle Gehaeuse <-> Elektronik (schnittstelle/gehaeuse_elektronik.json) ----------------
# Nur Ausgabe, aendert das Modell nicht. Lage/Kabelwege = Gehaeuse (aus diesem Modell), Pinbelegung = Elektronik.
def _r(v_): return round(v_, 2)
def _bb(o_):
    b_ = o_.Shape.BoundBox
    return dict(x=[_r(b_.XMin), _r(b_.XMax)], y=[_r(b_.YMin), _r(b_.YMax)], z=[_r(b_.ZMin), _r(b_.ZMax)])
def _bb_alle(nm_):   # Huelle Platine + Anbauteile (Stiftleisten, Pins, Bestueckung, Jumper ...) = Bauraum
    bs_ = [o_.Shape.BoundBox for k_, o_ in _ref.items() if k_ == nm_ or k_.startswith(nm_ + "_")]
    if not bs_: return None
    return dict(x=[_r(min(q.XMin for q in bs_)), _r(max(q.XMax for q in bs_))], y=[_r(min(q.YMin for q in bs_)), _r(max(q.YMax for q in bs_))],
                z=[_r(min(q.ZMin for q in bs_)), _r(max(q.ZMax for q in bs_))])
_ref = {o.Name: o for o in doc.Objects if o.Name.startswith("REF_") and hasattr(o, "Shape") and not o.Shape.isNull() and not o.Name.startswith("REF_Litze")}
_spi_cut = P['PN_SPI_CUT'].split(",")
_sch = dict(
    stand=__import__("time").strftime("%Y-%m-%d %H:%M"),
    erzeugt_von="gehaeuse/skripte/build_prototyp_v2.py (Masse: gehaeuse/skripte/params.py) - nicht von Hand aendern, wird bei jedem Build neu geschrieben",
    zustaendigkeit={"Lage, Ausrichtung, Bauhoehen, Kabelwege und -laengen, Steckverbinder-Lage": "Gehaeuse (gehaeuse/)",
                    "Pinbelegung, Netze, GPIOs, I2C-Adressen, TCA-Kanaele, Stromversorgung": "Elektronik (elektronik/VERDRAHTUNG_UND_STROMVERSORGUNG.md)"},
    koordinaten="mm; huelle_platine = nur Leiterplatte, bauraum = mit Stiftleisten/Pins/Bestueckung; Ursprung vordere linke untere Ecke des Moduls (150 x 150), x nach rechts, y nach hinten (USB-C vorne bei y=0), z nach oben (Boden z=0)",
    hoehen=dict(boden=_r(FLOOR), platte_unterseite=_r(Z_UP), trennebene_traeger_deckel=_r(Z_SPLIT), oberkante=_r(Z_TOP),
                hinweis="Boards 'unten' stehen fest im Unterteil, 'platte' haengen unter dem Traeger und werden mitgewogen; ueber den Waegespalt nur die Schlaufe"),
    boards=[dict(name=n_, typ=t_, mitte=[_r(x_), _r(y_)], drehung_grad=r_, montage=m_,
                 pinleisten="Pins nach unten (Stiftleisten zum Boden, Kabel werden an die Pins geloetet)" if t_ != "VERTEILER" else "Streifenraster, Kupferseite unten",
                 huelle_platine=_bb(_ref["REF_" + n_]) if "REF_" + n_ in _ref else None, bauraum=_bb_alle("REF_" + n_)) for (n_, t_, x_, y_, r_, m_) in boards]
           + [dict(name="Power_Hub", typ="Streifenraster 6x12", montage="unten", pinleisten="Bestueckung unten, Kupfer oben (Adern oben angeloetet), JP_NFC nach unten im Bodenfenster",
                   huelle_platine=_bb(_ref["REF_Hub"]) if "REF_Hub" in _ref else None, bauraum=_bb_alle("REF_Hub"))],
    reader=[dict(name="PN532_%d%d" % k_, mitte=[_r(PNC(k_[0]-1, k_[1]-1)[0]), _r(PNC(k_[0]-1, k_[1]-1)[1])], montage="platte",
                 lage="umgedreht: Antenne, Bestueckung und Stiftleisten nach unten",
                 i2c_kante="+x" if PN_I2C_SIDE[k_] > 0 else "-x", i2c_pin_y=[_r(pn_hdr[k_]['y'] + (q_ - 1.5) * PITCH) for q_ in range(4)],
                 i2c_pinspitze_x=_r(pn_hdr[k_]['tip']), spi_kante=("+y" if PN_I2C_SIDE[k_] > 0 else "-y"),
                 spi_leiste="abgekniffen (nur Stummel)" if "%d%d" % k_ in _spi_cut else "vorhanden, unbeschaltet",
                 huelle_platine=_bb(_ref["REF_PN532_%d%d" % k_]) if "REF_PN532_%d%d" % k_ in _ref else None, bauraum=_bb_alle("REF_PN532_%d%d" % k_)) for k_ in sorted(pn_hdr)],
    waegezellen=[dict(name=n_[4:], huelle=_bb(o_)) for n_, o_ in sorted(_ref.items()) if _re.match(r"REF_Waegezelle_?\d+$", n_)],
    steckverbinder=[dict(name="USB-C-Einbaubuchse Delock 87824", ort="Vorderwand", huelle=_bb(_ref["REF_USB_C_Buchse"]) if "REF_USB_C_Buchse" in _ref else None),
                    dict(name="Delock-Stecker am ESP32", ort="steckt in der UART-Buchse des ESP32-C6 (mit Software abstimmen)"),
                    dict(name="Modulverbinder", ort="rechte Wand, noch geschlossen", masse="PLATZHALTER CONN_W/CONN_H")],
    leitungen=[dict(name=n_, adern=a_, laenge_modell_mm=_r(l_), bereich=b_) for (n_, a_, l_, b_) in wire_tab],
    leitungen_hinweis="Platzhalter-Baender aus dem Modell; Laenge ohne Steigleitung (ca. 2 x 3 mm) und ohne Zugabe. Zellkabel Waegezelle -> HX711 nicht modelliert.",
    bandverlaeufe_2d=WIRE_PATHS,
)
try:
    os.makedirs(outdir_schnittstelle, exist_ok=True)
    with open(os.path.join(outdir_schnittstelle, "gehaeuse_elektronik.json"), "w", encoding="utf-8") as f_: _json.dump(_sch, f_, indent=1, ensure_ascii=False)
except Exception as e:
    print("[Schnittstelle nicht geschrieben: %s]" % e)
try:
    os.makedirs(outdir_modell, exist_ok=True); os.makedirs(outdir_bericht, exist_ok=True)
    doc.saveAs(os.path.join(outdir_modell, "Prototyp_15x15%s.FCStd" % SUFFIX))
    with open(os.path.join(outdir_bericht, "pruefbericht%s.txt" % SUFFIX.lower()), "w", encoding="utf-8") as f: f.write(report + "\n")
    report += "\n[gespeichert in %s und %s]" % (outdir_modell, outdir_bericht)
except Exception as e:
    report += "\n[Speichern fehlgeschlagen: %s]" % e
print(report)
