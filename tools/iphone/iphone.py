# iPhone 15 Pro studio render for the portfolio's case-study screens.
# Run: Blender -b --factory-startup -P iphone.py -- <config.json>
# config: { "out": dir, "jobs": [{"src": png, "name": stem}], "res": [w, h], "samples": n,
#           "shadow": bool, "test": bool, "yaw": deg, "lean": deg }
import bpy, bmesh, math, sys, json, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

cfg = json.load(open(sys.argv[sys.argv.index('--') + 1]))
MM = 0.001

# ---------------- the device: iPhone 15 Pro (matches the 393 x 852 pt screenshots) ----------------
W, H, D = 70.6 * MM, 146.6 * MM, 8.25 * MM
R_BODY = 11.9 * MM            # plan-view corner radius (visual), drawn as a continuous-curvature corner
EDGE = 1.6 * MM               # the contoured edge where the rail meets the front and back glass
GLASS_INSET = 1.05 * MM       # titanium visible round the glass from the front
GLASS_T = 0.7 * MM
GLASS_UP = 0.16 * MM          # the glass stands a hair proud of the rail
SCR_W = 65.1 * MM             # active display, 1179 x 2556 px at 460 ppi
SCR_H = SCR_W * 852 / 393
R_SCR = 55 / 393 * SCR_W      # iOS display corner (55 pt)
PT = SCR_W / 393              # one point on the display, in metres


def corner_curve(cx, cy, r, a0, seg):
    """A continuous-curvature (superellipse, n=3) corner quadrant: the curve meets the straight edges with
    zero curvature, like Apple's corners. r is the visual radius; the curve spans 1.42 r along each edge."""
    n, R = 3.0, 1.42 * r
    pts = []
    for k in range(seg + 1):
        t = math.radians(a0 + 90 * k / seg)
        c, s = math.cos(t), math.sin(t)
        x = math.copysign(abs(c) ** (2 / n), c) * R
        y = math.copysign(abs(s) ** (2 / n), s) * R
        pts.append((cx + x, cy + y))
    return pts


def rrect(w, h, r, seg=28):
    R = 1.42 * r
    pts = []
    pts += corner_curve(w / 2 - R, h / 2 - R, r, 0, seg)
    pts += corner_curve(-w / 2 + R, h / 2 - R, r, 90, seg)
    pts += corner_curve(-w / 2 + R, -h / 2 + R, r, 180, seg)
    pts += corner_curve(w / 2 - R, -h / 2 + R, r, 270, seg)
    return pts


def slab(name, pts, z0, z1, bevel_w, bevel_seg, mat, smooth=True):
    """Extrude a closed outline between z0 and z1, then round its top and bottom rims."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    n = len(pts)
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if bevel_w > 0:
        bv = ob.modifiers.new('rim', 'BEVEL')
        bv.width = bevel_w; bv.segments = bevel_seg; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
        bv.profile = 0.5; bv.harden_normals = True; bv.miter_outer = 'MITER_ARC'
    if smooth:
        for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    return ob


def flat(name, pts, z, mat, uv=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in pts]
    f = bm.faces.new(vs)
    if uv:
        lay = bm.loops.layers.uv.new('UVMap')
        for loop in f.loops:
            x, y, _ = loop.vert.co
            loop[lay].uv = ((x + uv[0] / 2) / uv[0], (y + uv[1] / 2) / uv[1])
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def principled(name, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    for k, v in kw.items():
        p.inputs[k].default_value = v
    return m


# ---------------- materials ----------------
titanium = principled('BlackTitanium', **{'Base Color': (0.118, 0.118, 0.124, 1), 'Metallic': 1.0, 'Roughness': 0.3,
                                          'Anisotropic': 0.35})
antenna = principled('Antenna', **{'Base Color': (0.05, 0.05, 0.055, 1), 'Roughness': 0.55})
glass_black = principled('FrontGlass', **{'Base Color': (0.004, 0.004, 0.005, 1), 'Roughness': 0.02, 'IOR': 1.52,
                                          'Coat Weight': 0.6, 'Coat Roughness': 0.015})
back_glass = principled('BackGlass', **{'Base Color': (0.06, 0.06, 0.065, 1), 'Roughness': 0.45})
lens_mat = principled('Lens', **{'Base Color': (0.004, 0.005, 0.012, 1), 'Roughness': 0.05, 'Coat Weight': 1.0,
                                 'Coat Roughness': 0.01})
lens_core = principled('LensCore', **{'Base Color': (0.0, 0.0, 0.0, 1), 'Roughness': 0.08, 'Coat Weight': 1.0,
                                      'Coat Roughness': 0.01, 'Thin Film Thickness': 250.0, 'Thin Film IOR': 1.4})

# the display: the screenshot shines through the cover glass (emission under a clear coat)
screen_mat = bpy.data.materials.new('Screen'); screen_mat.use_nodes = True
nt = screen_mat.node_tree
p = nt.nodes['Principled BSDF']
p.inputs['Base Color'].default_value = (0, 0, 0, 1)
p.inputs['Roughness'].default_value = 0.02
p.inputs['Coat Weight'].default_value = 1.0
p.inputs['Coat Roughness'].default_value = 0.012
p.inputs['Specular IOR Level'].default_value = 0.0
p.inputs['Emission Strength'].default_value = 1.0
tex = nt.nodes.new('ShaderNodeTexImage'); tex.interpolation = 'Cubic'; tex.extension = 'CLIP'
mapping = nt.nodes.new('ShaderNodeMapping')
coord = nt.nodes.new('ShaderNodeTexCoord')
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
mix.inputs['A'].default_value = (0, 0, 0, 1)
nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
nt.links.new(tex.outputs['Alpha'], mix.inputs['Factor'])
nt.links.new(tex.outputs['Color'], mix.inputs['B'])
nt.links.new(mix.outputs['Result'], p.inputs['Emission Color'])

# ---------------- build ----------------
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
root = bpy.data.objects.new('iPhone', None); bpy.context.collection.objects.link(root)
parts = []
body = slab('Body', rrect(W, H, R_BODY), -D / 2, D / 2, EDGE, 10, titanium); parts.append(body)
gpts = rrect(W - GLASS_INSET * 2, H - GLASS_INSET * 2, R_BODY - GLASS_INSET)
gz1 = D / 2 + GLASS_UP
glass = slab('Glass', gpts, gz1 - GLASS_T, gz1, 0.32 * MM, 5, glass_black); parts.append(glass)
screen = flat('Screen', rrect(SCR_W, SCR_H, R_SCR), gz1 + 0.012 * MM, screen_mat, uv=(SCR_W, SCR_H)); parts.append(screen)
# front camera, at the right end of the Dynamic Island (island: 125 x 37 pt, 11 pt from the top)
isl_cy = SCR_H / 2 - (11 + 18.5) * PT
if cfg.get('island'):                                     # for screenshots exported without the Dynamic Island
    island_mat = principled('Island', **{'Base Color': (0.0, 0.0, 0.0, 1), 'Roughness': 0.1, 'Coat Weight': 1.0, 'Coat Roughness': 0.012})
    parts.append(flat('Island', rrect(125 * PT, 37 * PT, 18.5 * PT / 1.42 * 0.999, 16), gz1 + 0.016 * MM, island_mat))
    parts[-1].location.y = isl_cy
for nm, rad, mat, dz in (('Lens', 4.6 * PT, lens_mat, 0.02), ('LensCore', 2.2 * PT, lens_core, 0.03)):
    circ = [(44 * PT + rad * math.cos(2 * math.pi * k / 48), isl_cy + rad * math.sin(2 * math.pi * k / 48)) for k in range(48)]
    parts.append(flat(nm, circ, gz1 + dz * MM, mat))


def button(name, side, top_mm, len_mm):
    """A pill-shaped button standing 0.5 mm proud of the rail."""
    L, T, P = len_mm * MM, 2.5 * MM, 1.3 * MM
    cy = H / 2 - (top_mm + len_mm / 2) * MM
    pts = rrect(T, L, T / 2 / 1.42 * 0.999, 12)            # a stadium in the side's plane
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    xs = (W / 2 - P + 0.5 * MM) if side > 0 else (-W / 2 + P - 0.5 * MM)
    x0, x1 = (xs - P, xs) if side > 0 else (xs, xs + P)
    outer, inner = (x1, x0) if side > 0 else (x0, x1)
    a = [bm.verts.new((inner, cy + ly, lz)) for lz, ly in pts]
    b = [bm.verts.new((outer, cy + ly, lz)) for lz, ly in pts]
    n = len(pts)
    bm.faces.new(b if side > 0 else list(reversed(b))); bm.faces.new(list(reversed(a)) if side > 0 else a)
    for i in range(n):
        j = (i + 1) % n
        q = (a[i], a[j], b[j], b[i]) if side > 0 else (b[i], b[j], a[j], a[i])
        bm.faces.new(q)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    bv = ob.modifiers.new('round', 'BEVEL'); bv.width = 0.42 * MM; bv.segments = 6; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40); bv.harden_normals = True
    for pg in me.polygons: pg.use_smooth = True
    me.materials.append(titanium)
    return ob


parts += [button('Action', -1, 28.0, 8.0), button('VolUp', -1, 41.0, 12.5), button('VolDown', -1, 56.0, 12.5),
          button('Side', 1, 40.5, 20.0)]


def antenna_line(name, side, from_top_mm):
    """A thin plastic band across the flat of the rail."""
    y = H / 2 - from_top_mm * MM
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    x = (W / 2 + 0.012 * MM) if side > 0 else (-W / 2 - 0.012 * MM)
    hz = D / 2 - EDGE
    vs = [bm.verts.new((x, y - 0.35 * MM, -hz)), bm.verts.new((x, y + 0.35 * MM, -hz)),
          bm.verts.new((x, y + 0.35 * MM, hz)), bm.verts.new((x, y - 0.35 * MM, hz))]
    f = bm.faces.new(vs if side > 0 else list(reversed(vs)))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    me.materials.append(antenna)
    return ob


parts += [antenna_line('AntR1', 1, 21.0), antenna_line('AntR2', 1, H / MM - 22.0),
          antenna_line('AntL1', -1, 18.5), antenna_line('AntL2', -1, H / MM - 24.0)]
for ob in parts: ob.parent = root

# ---------------- pose: standing on its bottom edge, leaning back a touch, turned to show the right rail ----------------
lean, yaw = math.radians(cfg.get('lean', 7)), math.radians(cfg.get('yaw', 24))
root.rotation_euler = (math.radians(90) - lean, 0, -yaw)
bpy.context.view_layer.update()
ws = [root.matrix_world @ (c.matrix_local @ v.co) for c in parts if c.type == 'MESH' and c.name in ('Body',) for v in c.data.vertices]
minz = min(v.z for v in ws); root.location.z -= minz
bpy.context.view_layer.update()
ws = [root.matrix_world @ (body.matrix_local @ v.co) for v in body.data.vertices]
maxy = max(v.y for v in ws)
centre = sum(ws, Vector()) / len(ws)

# ---------------- set: a floor and a wall that only catch shadows ----------------
def catcher(name, size, loc, rot):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    ob = bpy.context.active_object; ob.name = name; ob.is_shadow_catcher = True
    return ob


# one seamless sweep, the floor curving up into the wall like a photo studio's cove, so no corner line shows
def cove(name, wall_y, r=0.09):
    prof = [(-0.9, 0.0)]
    for k in range(25):
        a = math.radians(-90 + 90 * k / 24)
        prof.append((wall_y - r + r * math.cos(a), r + r * math.sin(a)))   # centre (wall_y - r, r): from (wall_y - r, 0) to (wall_y, r)
    prof.append((wall_y, 1.2))
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    xs = (-1.0, 1.0)
    rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in xs]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    bm.to_mesh(me); bm.free()
    for pg in me.polygons: pg.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.is_shadow_catcher = True
    return ob


floor = cove('Cove', maxy + 0.0005, cfg.get('cove_r', 0.012))
wall = floor

# ---------------- light: a studio, big soft key from the upper left, a strip for the rail, a top fill ----------------
world = bpy.data.worlds.new('Studio'); bpy.context.scene.world = world; world.use_nodes = True
bgn = world.node_tree.nodes['Background']
g = cfg.get('world', 0.3); bgn.inputs['Color'].default_value = (g, g, g * 1.02, 1); bgn.inputs['Strength'].default_value = 1.0


def area(name, size, loc, target, energy, shape='RECTANGLE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.shape = shape; ld.size = size
    if size_y: ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(ob); ob.location = loc
    d = Vector(target) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


L = cfg.get('lights', {})
off = Vector(centre)
# key: high on the upper left, out of the screen's mirror line, so the glass never blows out; it casts the shadow
area('Key', L.get('key_size', 0.5), off + Vector(L.get('key_pos', (-0.32, -0.38, 0.62))), centre, L.get('key', 40))
# a tall strip behind on the right: the line of light down the titanium rail
area('Rail', L.get('rail_w', 0.25), off + Vector(L.get('rail_pos', (0.32, 0.28, 0.05))), centre, L.get('rail', 0.8), size_y=0.6)
# a strip overhead for the top edge
area('Top', 0.6, off + Vector((0.0, 0.05, 0.45)), centre, L.get('top', 6), size_y=0.08)
# a big dim card where the screen looks: a soft sheen across the glass
area('Sheen', 0.8, off + Vector(L.get('sheen_pos', (-0.62, -0.55, 0.05))), centre, L.get('sheen', 1.2), size_y=0.5)
# a low fill from the camera side, so the front lip of the rail reads
area('Fill', 0.8, off + Vector((0.15, -0.8, 0.0)), centre, L.get('fill', 3))

# ---------------- camera ----------------
cam_d = bpy.data.cameras.new('Cam'); cam_d.lens = cfg.get('lens', 85)
cam = bpy.data.objects.new('Cam', cam_d); bpy.context.collection.objects.link(cam)
ctr = Vector((centre.x + cfg.get('aim_x', 0.012), centre.y, centre.z))
cam.location = ctr + Vector((0, -cfg.get('dist', 0.62), cfg.get('cam_up', 0.03)))
cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------------- render settings ----------------
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.refresh_devices()
for dv in prefs.devices: dv.use = dv.type == 'METAL'
sc.cycles.device = 'GPU'
sc.cycles.samples = cfg.get('samples', 192); sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.01
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 6
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = cfg.get('res', [1100, 1600])
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
fmt = cfg.get('format', 'WEBP')
sc.render.image_settings.file_format = fmt
sc.render.image_settings.color_mode = 'RGBA'
if fmt in ('WEBP', 'AVIF', 'JPEG'): sc.render.image_settings.quality = cfg.get('quality', 88)

SCREEN_ASPECT = SCR_W / SCR_H


def load_screen(path):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'sRGB'; img.alpha_mode = 'STRAIGHT'
    tex.image = img
    a = img.size[0] / img.size[1]
    if a < SCREEN_ASPECT:      # taller than the display: show its top
        k = a / SCREEN_ASPECT
        mapping.inputs['Scale'].default_value = (1, k, 1); mapping.inputs['Location'].default_value = (0, 1 - k, 0)
    else:                       # wider: centre it
        k = SCREEN_ASPECT / a
        mapping.inputs['Scale'].default_value = (k, 1, 1); mapping.inputs['Location'].default_value = ((1 - k) / 2, 0, 0)


os.makedirs(cfg['out'], exist_ok=True)
ext = {'WEBP': 'webp', 'AVIF': 'avif', 'PNG': 'png', 'JPEG': 'jpg'}[fmt]

# where the phone lands in the frame (for laying the renders out on the page)
bpy.context.view_layer.update()
pts2 = [world_to_camera_view(sc, cam, root.matrix_world @ (body.matrix_local @ v.co)) for v in body.data.vertices]
meta = {'res': [sc.render.resolution_x, sc.render.resolution_y],
        'phone': [min(p.x for p in pts2), 1 - max(p.y for p in pts2), max(p.x for p in pts2), 1 - min(p.y for p in pts2)]}
json.dump(meta, open(os.path.join(cfg['out'], 'meta.json'), 'w'))

# phones: no set, just the device
floor.hide_render = wall.hide_render = True
for job in cfg['jobs']:
    load_screen(job['src'])
    sc.render.filepath = os.path.join(cfg['out'], job['name'] + '.' + ext)
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.filepath, flush=True)

# shadow: the set only; the phone is invisible to the camera but still casts its shadow
if cfg.get('shadow'):
    floor.hide_render = False
    for ob in parts: ob.visible_camera = False
    raw = os.path.join(cfg['out'], 'shadow-raw.png')
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '16'
    sc.render.filepath = raw
    bpy.ops.render.render(write_still=True)
    # fade the shadow out well before the frame's edges, so it never ends in a line on the page
    import numpy as np
    im = bpy.data.images.load(raw); w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * cfg.get('fade_cx', 0.5), h * cfg.get('fade_cy', 0.5)
    d = ((xx - cx) / (w * 0.5)) ** 2 + ((yy - cy) / (h * 0.5)) ** 2
    m = np.clip((1 - d) / 0.45, 0, 1); m = m * m * (3 - 2 * m)
    px[..., 3] *= m; px[..., :3] = 0
    out = bpy.data.images.new('shadow', w, h, alpha=True, float_buffer=False)
    out.pixels[:] = px.ravel()
    out.filepath_raw = os.path.join(cfg['out'], 'shadow.' + ext); out.file_format = fmt
    sc.render.image_settings.file_format = fmt; sc.render.image_settings.color_mode = 'RGBA'
    out.save_render(out.filepath_raw, scene=sc)
    print('RENDERED', out.filepath_raw, flush=True)

# a preview: the shadow and the first phone over the page colour, as they'll sit on the site
if cfg.get('preview') and cfg['jobs']:
    import numpy as np
    def load(path):
        im = bpy.data.images.load(path); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); return a
    bg = np.array([0xEE, 0xED, 0xEA], dtype=np.float32) / 255.0
    out = np.ones((sc.render.resolution_y, sc.render.resolution_x, 4), dtype=np.float32); out[..., :3] = bg
    sp = os.path.join(cfg['out'], 'shadow.' + ext)
    if os.path.exists(sp):
        sh = load(sp); out[..., :3] *= (1 - sh[..., 3:4])
    ph = load(os.path.join(cfg['out'], cfg['jobs'][0]['name'] + '.' + ext))
    out[..., :3] = ph[..., :3] * ph[..., 3:4] + out[..., :3] * (1 - ph[..., 3:4])
    pv = bpy.data.images.new('preview', sc.render.resolution_x, sc.render.resolution_y, alpha=False)
    pv.pixels[:] = out.ravel(); pv.filepath_raw = os.path.join(cfg['out'], 'preview.png'); pv.file_format = 'PNG'; pv.save()
    print('PREVIEW', pv.filepath_raw, flush=True)

if cfg.get('blend'):
    for ob in parts: ob.visible_camera = True
    bpy.ops.wm.save_as_mainfile(filepath=cfg['blend'])
