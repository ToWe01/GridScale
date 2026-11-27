# -*- coding: utf-8 -*-
# Gerenderte Ansichten des Prototyps V2 mit Blender (Cycles).
# Eingabe: STL je Teil + teile.json (Name, Farbe, Hub fuer die Explosion), exportiert aus FreeCAD ueber die Bridge.
# Aufruf: /Applications/Blender.app/Contents/MacOS/Blender -b -P cad/render/render_blender.py -- <eingabe_ordner> <ausgabe_ordner>
import bpy, bmesh, json, math, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
IN, OUT = args[0], args[1]
os.makedirs(OUT, exist_ok=True)
META = json.load(open(os.path.join(IN, "teile.json")))

def lin(c): return tuple(x ** 2.2 for x in c)
def material(name, rgb, metal=0.0, rough=0.5, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*lin(rgb), 1.0)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if "Coat Weight" in b.inputs: b.inputs["Coat Weight"].default_value = coat
    return m

def kind(name, rgb):
    r = tuple(round(c, 2) for c in rgb)
    if name in ("Unterteil", "Traeger", "Deckel"): return dict(metal=0.0, rough=0.55)            # PLA, leicht matt
    if r == (0.85, 0.75, 0.35): return dict(metal=1.0, rough=0.25)                              # Pins vergoldet
    if r in ((0.75, 0.75, 0.78), (0.8, 0.8, 0.82)): return dict(metal=1.0, rough=0.3)            # Metall, Alu-Waegezelle
    if r == (0.85, 0.5, 0.2): return dict(metal=1.0, rough=0.35)                                # Kupfer
    return dict(metal=0.0, rough=0.35, coat=0.3)                                                # Platinen, Bauteile

def build(exploded):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    objs = []
    for t in META:
        bpy.ops.wm.stl_import(filepath=os.path.join(IN, t["file"]), global_scale=0.001)
        o = bpy.context.selected_objects[0]; o.name = t["name"]
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(o.data); bm.free()
        try:
            bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
        except Exception:
            pass
        o.data.materials.append(material(t["name"], t["color"], **kind(t["name"], t["color"])))
        if exploded and t["lift"]: o.location.z += t["lift"] * 0.001
        objs.append(o)
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (lo + hi) / 2; diag = (hi - lo).length
    # Boden mit Schatten
    bpy.ops.mesh.primitive_plane_add(size=60.0, location=(ctr.x, ctr.y, lo.z - 0.0002))
    bpy.context.active_object.data.materials.append(material("Boden", (0.97, 0.97, 0.97), rough=0.8))
    # Welt + Licht
    w = bpy.data.worlds.new("Welt"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    def area(loc, energy, size):
        bpy.ops.object.light_add(type="AREA", location=loc); L = bpy.context.active_object
        L.data.energy = energy; L.data.size = size
        L.rotation_euler = (ctr - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    area((ctr.x - 0.35, ctr.y - 0.45, ctr.z + 0.6), 120, 0.6)   # Hauptlicht vorne links oben
    area((ctr.x + 0.5, ctr.y + 0.1, ctr.z + 0.35), 40, 0.8)     # Aufhellung rechts
    area((ctr.x + 0.1, ctr.y + 0.6, ctr.z + 0.4), 35, 0.8)      # Kante hinten
    return ctr, diag

def camera(ctr, diag, direction, lens, res, fill=1.15):
    sc = bpy.context.scene
    d = Vector(direction).normalized()
    cam_data = bpy.data.cameras.new("Kamera"); cam_data.lens = lens
    cam = bpy.data.objects.new("Kamera", cam_data); sc.collection.objects.link(cam); sc.camera = cam
    fov = 2 * math.atan(cam_data.sensor_width / (2 * lens)) * min(1.0, res[0] / res[1]) if res[0] < res[1] else 2 * math.atan(cam_data.sensor_width / (2 * lens)) * res[1] / res[0]
    dist = diag * fill / (2 * math.tan(fov / 2))
    cam.location = ctr - d * dist
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()   # Kamera: Blick -Z, oben +Y (ergibt Welt-Z oben)
    sc.render.resolution_x, sc.render.resolution_y = res

def render(fn):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "METAL"; prefs.get_devices()
        for dv in prefs.devices: dv.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU nicht verfuegbar:", e)
    sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = -0.3
    sc.render.film_transparent = False
    sc.render.filepath = os.path.join(OUT, fn); bpy.ops.render.render(write_still=True); print("gerendert", fn)

ctr, diag = build(exploded=False)
camera(ctr, diag, (-0.506, 0.723, -0.469), 70, (2400, 1600), fill=1.0)
render("render_zusammengebaut.png")
ctr, diag = build(exploded=True)
camera(ctr, diag, (-0.539, 0.770, -0.342), 70, (2000, 2400), fill=0.95)
render("render_explosion.png")
