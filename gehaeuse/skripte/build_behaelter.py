# -*- coding: utf-8 -*-
# Gridfinity-Behaelter fuer GridScale (50-mm-Raster), mit Mulde fuer das RFID-Tag unter jedem Fuss.
# Gridfinity-Profil wird aus params.py (Parameter von build_prototyp_v2.py) gelesen (gleiche Werte wie die Matte).
# Ausgabe: gehaeuse/modell/Behaelter.FCStd, gehaeuse/pruefberichte/pruefbericht_behaelter.txt, gehaeuse/druck/Behaelter_<n>x<m>.stl
import os, re, math, Part, Mesh
import FreeCAD as App
from FreeCAD import Vector as V

# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
src = open(os.path.join(GEH, "skripte", "params.py"), encoding="utf-8").read()   # Matten-Parameter (seit 27.11. ausgelagert)
def mat_param(name):
    return float(re.search(r'\("%s",\s*([0-9.]+)' % name, src).group(1))

PARAMS = [
    # (Name, Wert, Status, Quelle)
    ("GF_TOP", mat_param("GF_TOP"), "Annahme", "aus build_prototyp_v2.py: Oeffnung der Mattentasche oben"),
    ("GF_C1", mat_param("GF_C1"), "Annahme", "aus build_prototyp_v2.py: Fase oben"),
    ("GF_V", mat_param("GF_V"), "Annahme", "aus build_prototyp_v2.py: senkrecht"),
    ("GF_C2", mat_param("GF_C2"), "Annahme", "aus build_prototyp_v2.py: Fase unten"),
    ("GRID", 50.0, "bestaetigt", "Raster der Matte"),
    ("BIN_CLR", 0.25, "Norm", "Gridfinity: Fuss 0,25 je Seite kleiner als die Tasche (42 -> 41,5)"),
    ("BIN_GAP", 0.5, "Norm", "Gridfinity: Behaelter 0,5 kleiner als das Raster (Luft zum Nachbarn)"),
    ("BIN_LIFT", 0.2, "Annahme", "Behaelterkoerper 0,2 ueber dem Mattenrand, Fuss steht auf dem Taschenboden (wie Gridfinity 4,75 vs 4,65)"),
    ("BIN_H", 40.0, "Annahme", "Hoehe ueber der Mattenoberkante (Nutzer hat keine Hoehe genannt)"),
    ("BIN_WALL", 1.2, "Annahme", "Wand (PLA-Regel >= 1,2)"),
    ("BIN_FLOOR", 1.2, "Annahme", "Boden innen ueber den Fuessen"),
    ("BIN_R", 4.0, "Annahme", "Eckradius aussen (Gridfinity 3,75 bei 42 -> ca. 4)"),
    ("TAG_D", 29.6, "Annahme", "Mulde fuer RFID-Tag SAG 440880538-0107201 (NTAG213 Metal Label): DigiKey nennt D 25,00, Bezeichnung 'D29' -> 29 + 0,6 Luft"),
    ("TAG_T", 1.2, "bestaetigt", "Muldentiefe = Tag-Dicke + Kleber; Nutzer 27.11.: Testdruck 1x1-Behaelter passt"),
]
P = {n: v for (n, v, s, q) in PARAMS}
SIZES = [(1, 1), (2, 1), (2, 2)]
GF_H = P['GF_C1'] + P['GF_V'] + P['GF_C2']
a0 = P['GF_TOP']; a1 = a0 - 2*P['GF_C1']; a2 = a1 - 2*P['GF_C2']   # Mattentasche: oben, nach Fase oben, Boden
c = P['BIN_CLR']; b0, b1, b2 = a0 - 2*c, a1 - 2*c, a2 - 2*c        # Fuss entsprechend kleiner

def frustum(cx, cy, z0, a_bot, a_top, h):
    def sq(a, z):
        h2 = a / 2.0
        return Part.makePolygon([V(cx-h2, cy-h2, z), V(cx+h2, cy-h2, z), V(cx+h2, cy+h2, z), V(cx-h2, cy+h2, z), V(cx-h2, cy-h2, z)])
    return Part.makeLoft([sq(a_bot, z0), sq(a_top, z0 + h)], True)
def rbox(x, y, z, dx, dy, dz, r):
    b = Part.makeBox(dx, dy, dz, V(x, y, z))
    ed = [e for e in b.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    return b.makeFillet(r, ed) if r > 0 else b

def foot(cx, cy):   # z = 0 ist der Taschenboden der Matte
    f = frustum(cx, cy, 0, b2, b1, P['GF_C2'])
    f = f.fuse(Part.makeBox(b1, b1, P['GF_V'], V(cx - b1/2, cy - b1/2, P['GF_C2'])))
    f = f.fuse(frustum(cx, cy, P['GF_C2'] + P['GF_V'], b1, b0, P['GF_C1']))
    f = f.fuse(Part.makeBox(b0, b0, P['BIN_LIFT'] + 0.01, V(cx - b0/2, cy - b0/2, GF_H)))
    return f

def make_bin(nx, ny):
    z_body = GF_H + P['BIN_LIFT']; z_top = GF_H + P['BIN_H']
    W, D = nx*P['GRID'] - P['BIN_GAP'], ny*P['GRID'] - P['BIN_GAP']
    x0, y0 = P['BIN_GAP']/2, P['BIN_GAP']/2
    body = rbox(x0, y0, z_body, W, D, z_top - z_body, P['BIN_R'])
    t = P['BIN_WALL']
    body = body.cut(rbox(x0 + t, y0 + t, z_body + P['BIN_FLOOR'], W - 2*t, D - 2*t, z_top, P['BIN_R'] - t))
    tags = []
    for i in range(nx):
        for j in range(ny):
            cx, cy = 25 + 50*i, 25 + 50*j
            body = body.fuse(foot(cx, cy))
            tags.append(Part.makeCylinder(P['TAG_D']/2, P['TAG_T'], V(cx, cy, -0.01)))
    for q in tags: body = body.cut(q)
    return body.removeSplitter()

DOCNAME = "Gridfinity_Behaelter"
doc = App.getDocument(DOCNAME) if DOCNAME in App.listDocuments() else App.newDocument(DOCNAME)
for o in list(doc.Objects): doc.removeObject(o.Name)
rep = []; line = rep.append
line("PRUEFBERICHT  Gridfinity-Behaelter (50-mm-Raster, Profil aus build_prototyp_v2.py)")
line("Fuss: oben %.2f, nach Fase %.2f, unten %.2f mm (Tasche %.2f / %.2f / %.2f), Hoehe %.2f + %.2f" % (b0, b1, b2, a0, a1, a2, GF_H, P['BIN_LIFT']))

# Matte laden fuer den Passungscheck (Deckel mit Gridfinity-Taschen, Reader)
mat = App.openDocument(os.path.join(GEH, "modell", "Prototyp_15x15_Deckel_V2.FCStd"), True) if os.path.exists(os.path.join(GEH, "modell", "Prototyp_15x15_Deckel_V2.FCStd")) else None
cover = mat.getObject("Deckel").Shape if mat else None
Z_TOP = cover.BoundBox.ZMax if cover else 33.95
Z_FLOOR = Z_TOP - GF_H
reader = [o.Shape for o in mat.Objects if mat and re.match(r"REF_PN532_\d\d$", o.Name)] if mat else []

shift = 0.0; os.makedirs(os.path.join(GEH, "druck"), exist_ok=True)
for (nx, ny) in SIZES:
    b = make_bin(nx, ny)
    name = "Behaelter_%dx%d" % (nx, ny)
    o = doc.addObject("Part::Feature", name); o.Shape = b
    o.Placement.Base = V(shift, 0, 0); shift += nx*50 + 20
    if App.GuiUp: o.ViewObject.ShapeColor = (0.95, 0.6, 0.15)
    line("%s: %.1f x %.1f x %.2f mm, gueltig=%s, ein Koerper=%s, Volumen %.0f mm3 (ca. %.0f g PLA massiv)" % (
        name, b.BoundBox.XLength, b.BoundBox.YLength, b.BoundBox.ZLength, b.isValid(), len(b.Solids) == 1, b.Volume, b.Volume * 1.24e-3))
    if cover:
        on_mat = b.copy(); on_mat.translate(V(0, 0, Z_FLOOR))
        ov = on_mat.common(cover).Volume
        d_side = on_mat.distToShape(cover)[0]
        line("  auf der Matte (Feld 1|1): Ueberschneidung mit Deckel %.3f mm3 (Soll 0), steht auf dem Taschenboden: %s, Koerper %.2f ueber dem Rand" % (
            ov, abs(on_mat.BoundBox.ZMin - Z_FLOOR) < 1e-6, P['BIN_LIFT']))
        if reader:
            line("  Abstand Tag-Unterseite - Reader-Platinenoberseite darunter: %.2f mm (Tag buendig mit Fussunterseite; Deckelboden + Druckplatte + Luft)" % min(Z_FLOOR - r.BoundBox.ZMax for r in reader if r.BoundBox.XMin < 50 and r.BoundBox.YMin < 50))
    Mesh.export([o], os.path.join(GEH, "druck", name + ".stl"))
line("Tag-Mulde: Durchmesser %.1f, Tiefe %.1f mm (bestaetigt, Testdruck), unter jedem Fuss -> Tag unter das Feld kleben, das gelesen werden soll; Lesefläche (nicht die Metallseite) nach unten" % (P['TAG_D'], P['TAG_T']))
line("Rest Fussboden um die Mulde: %.1f mm je Seite; Muldendecke = Bruecke %.1f mm beim Druck" % ((b2 - P['TAG_D'])/2, P['TAG_D']))
line("Druck: aufrecht auf den Fuessen, keine Stuetzen (Fasen 45 Grad, Muldendecke als Bruecke)")
ph = [n for (n, v, s, q) in PARAMS if s == "PLATZHALTER"]
line("--- offene PLATZHALTER (%d): %s" % (len(ph), ", ".join(ph)))
if mat: App.closeDocument(mat.Name)
doc.recompute()
doc.saveAs(os.path.join(GEH, "modell", "Behaelter.FCStd"))
open(os.path.join(GEH, "pruefberichte", "pruefbericht_behaelter.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
print("\n".join(rep))
