# -*- coding: utf-8 -*-
# Testdruck-Coupon V2: schneidet Ausschnitte aus den ECHTEN Teilen des V2-Modells (Prototyp_15x15_Deckel_V2.FCStd),
# damit der Coupon genau das prueft, was spaeter gedruckt wird. Aendert das Modell NICHT.
# Vorher build_prototyp_v2.py laufen lassen; der Coupon folgt dann automatisch jedem Modellstand.
# Aufruf (aus der Projektwurzel): freecadcmd -c "exec(open('gehaeuse/skripte/build_coupon.py').read())"
# Ausgabe: gehaeuse/druck/Coupon_*.stl, gehaeuse/pruefberichte/pruefbericht_coupon.txt
import os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V
# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
FCSTD = os.path.join(GEH, "modell", "Prototyp_15x15_Deckel_V2.FCStd")
OUTS = [os.path.join(GEH, "druck") + "/"]

# (Name, Quelle, x0, y0, x1, y1, drehen, Status, Prueft)  -- Ausschnittsfenster in Modellkoordinaten [mm]
COUPONS = [
    ("Coupon_A_Traeger_Ecke", "Traeger", 0.0, 0.0, 53.5, 53.5, True, "Annahme",
     "PN532-Tasche 11 mit Eckauflagen und Pin-Aussparungen, 3 Passzapfen-Bohrungen mit Quetschrippen (50|8) (8|50) (50|50), Randstufe"),
    ("Coupon_B_Deckel_Ecke", "Deckel", 0.0, 0.0, 57.0, 57.0, False, "Annahme",
     "Gegenstueck zu A: 3 Passzapfen, Druckplatte ueber Reader 11, Randleisten, Gridfinity-Feld 1x1 (Behaelter-Sitz). Fenster bis 57 statt 53,5: nimmt 2 mm der Nachbar-Druckplatten (ab 55) mit, damit der Deckelboden wie im echten Teil als Bruecke (ca. 10 mm) gedruckt wird und nicht frei auskragt; die Stummel stehen neben Coupon A, keine Kollision"),
    ("Coupon_C_Traeger_Freiende", "Traeger", 88.0, 39.0, 116.0, 59.0, True, "Annahme",
     "M4-Durchgang 4,6 + Kopfsenkung 7,4 von oben am Zellen-Freiende (Restwand 0,8 zur Readertasche)"),
    ("Coupon_F_Traeger_TCA", "Traeger", 39.0, 57.8, 61.0, 92.2, True, "Annahme",
     "TCA9548A an der Plattenunterseite: 2 Stuetzen D4,0 mit Zentrierzapfen D1,8 (Loch D2,5) und 2 Rasthaken an den Enden"),
    ("Coupon_D_Unterteil_Festende", "Unterteil", 33.0, 37.0, 64.0, 63.0, False, "Annahme",
     "Sockel Festende mit Verdrehsicherung, M4-Loecher mit Senkung fuer Kopf + Scheibe von unten"),
    ("Coupon_E_Unterteil_HX711", "Unterteil", 5.0, 8.5, 43.0, 39.5, False, "Annahme",
     "HX711-Stuetzen mit Zentrierzapfen und 2 Rasthaken (Einrasten, Luft zur Stiftleiste)"),
]
H_MIN_SOLID = 0.05   # Bruchstuecke, die nicht auf dem Bett stehen (ZMin > dies), werden verworfen und gemeldet

d = App.openDocument(FCSTD)
rep = ["PRUEFBERICHT COUPON  (Ausschnitte aus Prototyp_15x15_Deckel_V2.FCStd, Stand %s)" %
       __import__("time").strftime("%Y-%m-%d %H:%M", __import__("time").localtime(os.path.getmtime(FCSTD)))]
tot = 0.0
for name, src, x0, y0, x1, y1, flip, st, what in COUPONS:
    s = d.getObject(src).Shape
    bb = s.BoundBox
    cut = s.common(Part.makeBox(x1 - x0, y1 - y0, bb.ZLength + 2, V(x0, y0, bb.ZMin - 1)))
    if flip: cut.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    b = cut.BoundBox; cut.translate(V(-b.XMin, -b.YMin, -b.ZMin))
    ok_ = [x.BoundBox.ZMin < H_MIN_SOLID and x.Volume > 1.0 for x in cut.Solids]
    keep = [x for x, k in zip(cut.Solids, ok_) if k]; drop = [x for x, k in zip(cut.Solids, ok_) if not k]
    sh = Part.makeCompound(keep) if len(keep) > 1 else keep[0]
    m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.02, AngularDeflection=0.26, Relative=False)
    for o in OUTS: m.write(o + name + ".stl")
    b = sh.BoundBox; tot += sh.Volume
    rep.append("%-28s aus %-9s x %5.1f-%5.1f y %5.1f-%5.1f  %s  -> %5.1f x %5.1f x %5.2f mm, %5.0f mm3, Koerper %d, gueltig %s, STL geschlossen %s%s" % (
        name, src, x0, x1, y0, y1, "umgedreht" if flip else "wie Modell", b.XLength, b.YLength, b.ZLength, sh.Volume, len(keep), sh.isValid(), m.isSolid(),
        ("  VERWORFEN %d Bruchstueck(e) ueber dem Bett (%.0f mm3)" % (len(drop), sum(x.Volume for x in drop))) if drop else ""))
    rep.append("    prueft: " + what)
rep.append("Summe %.0f mm3 = ca. %.0f g PLA als Vollmaterial (mit 3 Waenden/15 %% Infill weniger)" % (tot, tot * 1.24e-3))
App.closeDocument(d.Name)
open(os.path.join(GEH, "pruefberichte", "pruefbericht_coupon.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
print("\n".join(rep))
