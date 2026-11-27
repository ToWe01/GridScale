# -*- coding: utf-8 -*-
# Exportiert Unterteil, Traeger und Deckel aus der V2-FCStd als STL in Druckorientierung nach gehaeuse/druck/.
# Traeger wird umgedreht (Oberseite aufs Bett). Aendert das Modell nicht. Vorher build_prototyp_v2.py laufen lassen.
# Aufruf (aus der Projektwurzel): freecadcmd -c "exec(open('gehaeuse/skripte/export_stl.py').read())"
import os
import FreeCAD as App, MeshPart
from FreeCAD import Vector as V
# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
OUT = os.path.join(GEH, "druck"); os.makedirs(OUT, exist_ok=True)
d = App.openDocument(os.path.join(GEH, "modell", "Prototyp_15x15_Deckel_V2.FCStd"))
def export(name, fn, flip):
    s = d.getObject(name).Shape.copy()
    if flip: s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    bb = s.BoundBox; s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.26, Relative=False)
    m.write(os.path.join(OUT, fn))
    bb = s.BoundBox
    print("%-18s %6.1f x %6.1f x %5.2f mm  Dreiecke %6d  geschlossen %s  Volumen %.0f mm3" % (fn, bb.XLength, bb.YLength, bb.ZLength, m.CountFacets, m.isSolid(), m.Volume))
export("Unterteil", "V2_Unterteil.stl", False)
export("Traeger", "V2_Traeger.stl", True)
export("Deckel", "V2_Deckel.stl", False)
App.closeDocument(d.Name)
