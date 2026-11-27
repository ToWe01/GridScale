# -*- coding: utf-8 -*-
# Exportiert Positionen (Boards, Reader, Zellen, Stiftleisten) und Leitungswege aus build_prototyp_v2.py
# fuer den Lageplan. Baut das Modell headless in ein Temp-Verzeichnis (FCStd und Pruefbericht bleiben unberuehrt).
# Aufruf:  freecadcmd -c "exec(open('gehaeuse/verdrahtung/lageplan_export.py').read())"
import json, os, tempfile
import FreeCAD as App
# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
src = open(os.path.join(GEH, "skripte", "build_prototyp_v2.py"), encoding="utf-8").read()
TMP = tempfile.mkdtemp()
rep = [
    ('outdir_modell = os.path.join(GEH, "modell")\noutdir_bericht = os.path.join(GEH, "pruefberichte")\n', 'outdir_modell = outdir_bericht = TMP\n'),
    ("def tube(pts, d):\n", "def tube(pts, d):\n    _PTS.append([(p[0], p[1]) for p in pts])\n"),
    ("def chain(pts, n, layers=1, z_top=None):", "def chain(pts, n, layers=1, z_top=None):\n    _PTS.append([(p[0], p[1]) for p in pts])\n   "),
    ("plate_wires = []; base_wires = []; loop_wires = []; wire_tab = []\n",
     "plate_wires = []; base_wires = []; loop_wires = []; wire_tab = []\n_PTS.clear()\n"),
    ("def W(lst, name, n, shape, length):\n", "def W(lst, name, n, shape, length):\n    _PATHS[name] = list(_PTS); _PTS.clear()\n"),
]
for a, b in rep:
    assert a in src, a
    src = src.replace(a, b, 1)
_PTS = []; _PATHS = {}
VARIANT = "deckel"
exec(compile(src, "build_prototyp_v2.py", "exec"))

def bb(o):
    b = o.Shape.BoundBox
    return [b.XMin, b.YMin, b.XMax, b.YMax, b.ZMin, b.ZMax]
objs = {o.Name: bb(o) for o in doc.Objects if o.Name.startswith("REF_") and hasattr(o, "Shape") and not o.Shape.isNull()}
out = dict(
    objs=objs,
    wires=[dict(name=n, adern=k, laenge=L, teil=t, pfade=_PATHS.get(n, [])) for (n, k, L, t) in wire_tab],
    i2c_side={"%d%d" % k: v for k, v in PN_I2C_SIDE.items()},
    z_up=Z_UP, link_clip=list(LINK_CLIP),
)
json.dump(out, open(os.path.join(GEH, "verdrahtung", "lageplan_daten.json"), "w"), indent=1)
print("EXPORT OK", len(objs), "Objekte,", len(wire_tab), "Leitungen")
