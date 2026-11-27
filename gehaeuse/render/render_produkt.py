# -*- coding: utf-8 -*-
# Produktbilder des Prototyps V2 mit Blender (Cycles): Kuechenszene mit Arbeitsplatte, Behaeltern und Tiefenschaerfe.
# Nur Darstellung - Geometrie kommt unveraendert aus FreeCAD (STL + teile.json). Requisiten (Behaelter, Glas, Zitronen) sind frei erfunden.
# Aufruf: /Applications/Blender.app/Contents/MacOS/Blender -b -P cad/render/render_produkt.py -- <eingabe_ordner> <ausgabe_ordner> [samples]
import bpy, bmesh, json, math, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
IN, OUT = args[0], args[1]
SAMPLES = int(args[2]) if len(args) > 2 else 160
FARBE = args[3] if len(args) > 3 else "hell"   # "hell" (Graphit/Salbei/Creme) oder "schwarz"
os.makedirs(OUT, exist_ok=True)
META = json.load(open(os.path.join(IN, "teile.json")))
MM = 0.001
Z_FLOOR, Z_TOP = 29.2, 33.95

# Produktfarben (nur Darstellung): Unterteil Graphit, Traeger als Akzentstreifen Salbei, Deckel Cremeweiss
HOUSING = {"Unterteil": ((0.13, 0.13, 0.14), 0.6), "Traeger": ((0.52, 0.62, 0.52), 0.5), "Deckel": ((0.93, 0.92, 0.88), 0.45)}
if FARBE == "schwarz":   # mattes schwarzes PLA, alle drei Teile
    HOUSING = {"Unterteil": ((0.045, 0.045, 0.05), 0.62), "Traeger": ((0.045, 0.045, 0.05), 0.62), "Deckel": ((0.045, 0.045, 0.05), 0.58)}

def lin(c): return tuple(x ** 2.2 for x in c)
def material(name, rgb, metal=0.0, rough=0.5, coat=0.0, trans=0.0, ior=1.45, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*lin(rgb), 1.0)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if "Coat Weight" in b.inputs: b.inputs["Coat Weight"].default_value = coat
    if "Transmission Weight" in b.inputs: b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    if sss and "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = sss
    return m

def wood_material():
    m = bpy.data.materials.new("Eiche"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N.get("Principled BSDF"); b.inputs["Roughness"].default_value = 0.42
    if "Coat Weight" in b.inputs: b.inputs["Coat Weight"].default_value = 0.15
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.5, 12.0, 1.5)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6.0
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Y"
    wv.inputs["Scale"].default_value = 1.4; wv.inputs["Distortion"].default_value = 3.0; wv.inputs["Detail"].default_value = 3.0
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position, e[0].color = 0.25, (*lin((0.64, 0.47, 0.31)), 1); e[1].position, e[1].color = 0.85, (*lin((0.76, 0.59, 0.40)), 1)
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    L.new(nz.outputs["Color"], wv.inputs["Vector"]); L.new(wv.outputs["Fac"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], b.inputs["Base Color"])
    return m

def kind(name, rgb):
    r = tuple(round(c, 2) for c in rgb)
    if r == (0.85, 0.75, 0.35): return dict(metal=1.0, rough=0.25)
    if r in ((0.75, 0.75, 0.78), (0.8, 0.8, 0.82)): return dict(metal=1.0, rough=0.3)
    if r == (0.85, 0.5, 0.2): return dict(metal=1.0, rough=0.35)
    return dict(metal=0.0, rough=0.35, coat=0.3)

def link_new(name, mesh_obj): return mesh_obj

def box(name, x0, y0, z0, sx, sy, sz, mat, bevel=0.0, hollow=None):
    """Quader in mm (Ecke x0,y0,z0). hollow = (Wand, Boden) -> offener Behaelter."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + sx / 2) * MM, (y0 + sy / 2) * MM, (z0 + sz / 2) * MM))
    o = bpy.context.active_object; o.name = name; o.scale = (sx * MM, sy * MM, sz * MM)
    bpy.ops.object.transform_apply(scale=True)
    if hollow:
        w, fl = hollow
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + sx / 2) * MM, (y0 + sy / 2) * MM, (z0 + fl + sz / 2) * MM))
        c = bpy.context.active_object; c.scale = ((sx - 2 * w) * MM, (sy - 2 * w) * MM, sz * MM); bpy.ops.object.transform_apply(scale=True)
        if bevel: bv = c.modifiers.new("b", "BEVEL"); bv.width = max(bevel - w, 0.5) * MM; bv.segments = 6; bv.limit_method = "ANGLE"
        bm_ = o.modifiers.new("hohl", "BOOLEAN"); bm_.object = c; bm_.operation = "DIFFERENCE"; bm_.solver = "EXACT"
        if bevel:
            # Aussenkanten zuerst runden, dann aushoehlen
            bv = o.modifiers.new("b", "BEVEL"); bv.width = bevel * MM; bv.segments = 8; bv.limit_method = "ANGLE"
            o.modifiers.move(len(o.modifiers) - 1, 0)
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.data.objects.remove(c, do_unlink=True)
    elif bevel:
        bv = o.modifiers.new("b", "BEVEL"); bv.width = bevel * MM; bv.segments = 8; bv.limit_method = "ANGLE"
    o.data.materials.clear(); o.data.materials.append(mat)   # Boolean bringt leere Slots des Schneidkoerpers mit
    for poly in o.data.polygons: poly.material_index = 0
    bpy.ops.object.shade_smooth()
    return o

def cyl(name, x, y, z0, r, h, mat, verts=96, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * MM, depth=h * MM, location=(x * MM, y * MM, (z0 + h / 2) * MM))
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mat)
    if bevel: bv = o.modifiers.new("b", "BEVEL"); bv.width = bevel * MM; bv.segments = 4; bv.limit_method = "ANGLE"
    bpy.ops.object.shade_smooth()
    return o

def gridfinity_bin(name, i, j, nx, ny, h, rgb):
    """Behaelter auf Feld (i,j) [0..2], nx x ny Felder, Hoehe h ueber Deckeloberkante. Fuss greift ins Profil."""
    x0, y0 = 50 * i, 50 * j; m = material(name, rgb, rough=0.5)
    box(name + "_Fuss", x0 + 4.25, y0 + 4.25, Z_FLOOR, 50 * nx - 8.5, 50 * ny - 8.5, Z_TOP - Z_FLOOR + 0.6, m, bevel=2.0)
    return box(name, x0 + 0.5, y0 + 0.5, Z_TOP + 0.5, 50 * nx - 1.0, 50 * ny - 1.0, h, m, bevel=3.75, hollow=(1.4, 2.5))

def props():
    # Hinten links: Vorratsglas mit Linsen und Bambusdeckel (1x1)
    glas = material("Glas", (0.97, 0.98, 0.98), rough=0.03, trans=1.0, ior=1.5)
    cyl("Glas", 25, 125, Z_FLOOR + 0.2, 21.5, 88, glas, bevel=1.5)
    cyl("Linsen", 25, 125, Z_FLOOR + 2.0, 19.8, 56, material("Linsen", (0.78, 0.40, 0.18), rough=0.85))
    cyl("Deckel_Glas", 25, 125, Z_FLOOR + 88.0, 22.3, 9, material("Bambus", (0.80, 0.64, 0.42), rough=0.55), bevel=1.2)
    # Hinten Mitte/rechts: Terrakotta-Behaelter 2x1 mit Zitronen
    gridfinity_bin("Box_Terrakotta", 1, 2, 2, 1, 42, (0.78, 0.45, 0.33))
    zit = material("Zitrone", (0.95, 0.80, 0.18), rough=0.45, sss=0.1)
    for k, (x, y, rz) in enumerate(((79, 123, 15), (120, 127, -25))):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(x * MM, y * MM, (Z_TOP + 3 + 18) * MM))
        o = bpy.context.active_object; o.name = "Zitrone%d" % k; o.scale = (26 * MM, 19 * MM, 18 * MM); o.rotation_euler = (0, 0, math.radians(rz))
        o.data.materials.append(zit); bpy.ops.object.shade_smooth()
        d = o.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new("narben%d" % k, "CLOUDS"); tx.noise_scale = 0.08; d.texture = tx; d.strength = 0.012
    # Mitte links: Salbei-Behaelter 1x1 mit drei Gewuerzdosen
    gridfinity_bin("Box_Salbei", 0, 1, 1, 1, 34, (0.62, 0.70, 0.60))
    dose = material("Dose", (0.85, 0.86, 0.88), metal=1.0, rough=0.22)
    etik = [material("Etikett%d" % k, c, rough=0.6) for k, c in enumerate(((0.20, 0.25, 0.32), (0.85, 0.30, 0.18), (0.92, 0.90, 0.84)))]
    for k, (x, y) in enumerate(((16, 66), (34, 70), (24, 86))):
        cyl("Dose%d" % k, x, y, Z_TOP + 3.0, 8.5, 62, dose, bevel=0.8)
        cyl("Etikett%d" % k, x, y, Z_TOP + 15.0, 8.6, 30, etik[k])

def build(exploded, with_props):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    objs = []
    for t in META:
        bpy.ops.wm.stl_import(filepath=os.path.join(IN, t["file"]), global_scale=MM)
        o = bpy.context.selected_objects[0]; o.name = t["name"]
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(o.data); bm.free()
        try:
            bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
        except Exception:
            pass
        if t["name"] in HOUSING:
            rgb, rough = HOUSING[t["name"]]; mat = material(t["name"], rgb, rough=rough, coat=0.05)
        else:
            mat = material(t["name"], t["color"], **kind(t["name"], t["color"]))
        o.data.materials.append(mat)
        if exploded and t["lift"]: o.location.z += t["lift"] * MM
        objs.append(o)
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    if with_props: props()
    ctr = (lo + hi) / 2; diag = (hi - lo).length
    # Arbeitsplatte Eiche (0,9 x 0,6 m) und Wand mit weicher Hohlkehle dahinter
    bpy.ops.mesh.primitive_plane_add(size=1, location=(ctr.x, ctr.y + 0.12, lo.z - 0.0002))
    tp = bpy.context.active_object; tp.scale = (1.4, 0.8, 1); tp.data.materials.append(wood_material())
    bpy.ops.mesh.primitive_plane_add(size=1, location=(ctr.x, ctr.y + 0.26, lo.z + 0.5))
    wall = bpy.context.active_object; wall.scale = (2.0, 1.0, 1); wall.rotation_euler = (math.radians(90), 0, 0)
    wall.data.materials.append(material("Wand", (0.86, 0.82, 0.76), rough=0.9))
    # Welt + Licht (warm von links wie ein Fenster, kuehle Aufhellung, Kante von hinten)
    w = bpy.data.worlds.new("Welt"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (*lin((0.95, 0.93, 0.90)), 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    def area(loc, energy, size, rgb=(1, 1, 1)):
        bpy.ops.object.light_add(type="AREA", location=loc); L = bpy.context.active_object
        L.data.energy = energy; L.data.size = size; L.data.color = rgb
        L.rotation_euler = (ctr - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    area((ctr.x - 0.55, ctr.y - 0.10, ctr.z + 0.45), 38, 0.9, (1.0, 0.92, 0.82))   # Fenster links, warm
    area((ctr.x + 0.45, ctr.y - 0.45, ctr.z + 0.25), 7, 0.8, (0.88, 0.93, 1.0))     # Aufhellung rechts vorne, kuehl
    area((ctr.x + 0.15, ctr.y + 0.22, ctr.z + 0.30), 14, 0.4, (1.0, 0.97, 0.92))     # Kantenlicht hinten
    return ctr, diag

def camera(target, dist, azim, elev, lens, res, fstop=None):
    sc = bpy.context.scene
    d = Vector((math.cos(math.radians(elev)) * math.sin(math.radians(azim)), math.cos(math.radians(elev)) * math.cos(math.radians(azim)), -math.sin(math.radians(elev))))
    cd = bpy.data.cameras.new("Kamera"); cd.lens = lens
    cam = bpy.data.objects.new("Kamera", cd); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = target - d * dist
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if fstop:
        cd.dof.use_dof = True; cd.dof.focus_distance = dist; cd.dof.aperture_fstop = fstop
    sc.render.resolution_x, sc.render.resolution_y = res

def render(fn):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "METAL"; prefs.get_devices()
        for dv in prefs.devices: dv.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU nicht verfuegbar:", e)
    sc.view_settings.view_transform = "AgX"
    try: sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception as e: print("Look:", e)
    sc.view_settings.exposure = -0.2
    sc.render.filepath = os.path.join(OUT, fn); bpy.ops.render.render(write_still=True); print("gerendert", fn)

V = Vector
SUF = "" if FARBE == "hell" else "_" + FARBE
# 1) Hauptbild: Matte mit Behaeltern auf der Arbeitsplatte, Blick von vorne rechts, flach, Tiefenschaerfe
ctr, diag = build(exploded=False, with_props=True)
camera(V((0.075, 0.085, 0.040)), 0.62, azim=-28, elev=24, lens=70, res=(2400, 1600), fstop=7.0)
render("produkt_hauptbild%s.png" % SUF)
# 2) Leere Matte von oben schraeg (Raster sichtbar)
ctr, diag = build(exploded=False, with_props=False)
camera(V((0.075, 0.075, 0.017)), 0.55, azim=-35, elev=38, lens=70, res=(2400, 1600), fstop=8.0)
render("produkt_leer%s.png" % SUF)
# 3) Explosion vor derselben Wand
ctr, diag = build(exploded=True, with_props=False)
camera(V((0.075, 0.075, 0.085)), 0.70, azim=-34, elev=20, lens=60, res=(2000, 2400), fstop=11.0)
render("produkt_explosion%s.png" % SUF)
