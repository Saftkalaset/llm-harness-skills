"""3d-print-blender helper library (run inside the live Blender session).

Load once per session (via execute_blender_code):
    exec(open('<skill-directory>/scripts/lib.py').read(), globals())

Design rules:
  * Every function prints ONE compact summary and returns a dict. Never prints per-face lists.
  * Cutters are kept as live Boolean modifier targets; apply only on milestone/export.
  * Cutters are hidden with hide_set(True) and hide_viewport stays False (depsgraph rule).
  * Persist extracted reference measurements in `scene["cad_specs"]` (`save_specs`/`get_specs`)
    and keep-out zones as `KeepOut_*` wireframes in `3_References` to avoid repeat raycasting.
"""
import bpy, bmesh, json, math, os, re, ast, hashlib, zipfile
from xml.sax.saxutils import escape
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CANON = ("1_Printable_Parts", "2_Boolean_Cutters", "3_References")


# ----------------------------------------------------------------- environment
def check_env():
    """Report units and available capabilities; optional addons are not requirements."""
    def available(operator):
        try:
            operator.get_rna_type()
            return True
        except (AttributeError, RuntimeError, KeyError):
            return False
    u = bpy.context.scene.unit_settings
    r = {
        "blender": bpy.app.version_string,
        "units_ok": (u.system == 'METRIC' and abs(u.scale_length - 0.001) < 1e-6
                     and u.length_unit == 'MILLIMETERS'),
        "threemf_export": True,
        "geometry_3mf_export": "builtin_stdlib",
        "native_threemf_export": available(bpy.ops.export_mesh.threemf),
        "print3d_toolbox": available(bpy.ops.mesh.print3d_check_all),
        "filepath": bpy.data.filepath or "(unsaved)",
    }
    bad = [k for k in ("units_ok",) if not r[k]]
    has_specs = "cad_specs" in bpy.context.scene
    has_recipe = "parametric_recipe.py" in bpy.data.texts
    print(f"ENV {r['blender']} | file={r['filepath']} | specs_cached={has_specs} | recipe={has_recipe} | problems={bad or 'none'}")
    return r


def world_bbox(obj):
    """Evaluated world-space bounds, rounded to 2 decimals; source unchanged."""
    if obj.type != 'MESH':
        return None
    bm = evaluated_world_mesh(obj)
    try:
        if not bm.verts:
            return None
        pts = [v.co for v in bm.verts]
        return (round(min(p.x for p in pts), 2), round(max(p.x for p in pts), 2),
                round(min(p.y for p in pts), 2), round(max(p.y for p in pts), 2),
                round(min(p.z for p in pts), 2), round(max(p.z for p in pts), 2))
    finally:
        bm.free()

_world_bbox = world_bbox


def load_recipe(name="parametric_recipe.py"):
    """Explicitly register a definition-only recipe; never rebuild on load.

    This policy prevents accidental top-level modeling, not hostile-code execution.
    Imports/functions must still be trusted by the operator.
    """
    import builtins as _b, inspect as _ins
    txt = bpy.data.texts.get(name)
    if not txt:
        return []
    tree = ast.parse(txt.as_string(), filename=name)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list:
                raise ValueError("Recipe decorators execute on load; remove them")
            for value in list(node.args.defaults) + [v for v in node.args.kw_defaults if v is not None]:
                ast.literal_eval(value)
            args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
            args += [a for a in (node.args.vararg, node.args.kwarg) if a]
            if node.returns or any(a.annotation for a in args):
                raise ValueError("Recipe annotations must be omitted to avoid load-time execution")
            continue
        if isinstance(node, ast.Assign):
            if not all(isinstance(t, ast.Name) for t in node.targets):
                raise ValueError("Recipe constants must use plain names")
            ast.literal_eval(node.value)
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        raise ValueError("Recipe top level permits imports, literal constants and functions only")
    ns = dict(globals())
    exec(compile(tree, name, "exec"), ns, ns)
    sigs = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            fn = ns[node.name]
            setattr(_b, node.name, fn)
            globals()[node.name] = fn
            sigs.append(f"{node.name}{_ins.signature(fn)}")
    print(f"RECIPE registered: {', '.join(sigs) or 'none'}; rebuild not called")
    return sigs


def open_project(project_dir, allow_discard=False, allow_switch=False):
    """Open one unambiguous project and inspect without executing recipes.

    Switching an existing file or populated scene requires explicit allow_switch.
    The dirty flag is not proof of cleanliness for scripted/headless changes.
    Flagged dirty data additionally requires explicit allow_discard.
    Already-open project inspection changes no geometry, selection or text.
    """
    project_dir = os.path.abspath(project_dir)
    cur_path = os.path.abspath(bpy.data.filepath) if bpy.data.filepath else ""
    if os.path.dirname(cur_path) != project_dir:
        populated = any(len(getattr(bpy.data, key)) for key in ('objects', 'meshes', 'curves', 'texts', 'images', 'materials'))
        if (cur_path or populated) and not allow_switch:
            raise RuntimeError("Current file or scene contains data; preserve a checkpoint before explicit allow_switch")
        if bpy.data.is_dirty and not allow_discard:
            raise RuntimeError("Current scene has unsaved changes; save it or explicitly allow_discard")
        preferred = os.path.join(project_dir, os.path.basename(project_dir) + ".blend")
        blends = sorted(os.path.join(project_dir, f) for f in os.listdir(project_dir) if f.endswith(".blend"))
        if os.path.isfile(preferred):
            path = preferred
        elif len(blends) == 1:
            path = blends[0]
        else:
            raise ValueError("Expected exact project-name .blend or one unambiguous .blend file")
        bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
    env = check_env()
    specs = get_specs() if "cad_specs" in bpy.context.scene else {}
    parts, cutters, refs = [], [], []
    for name, output in zip(CANON, (parts, cutters, refs)):
        col = bpy.data.collections.get(name)
        for ob in (col.objects if col else []):
            output.append({"name": ob.name, "bbox": world_bbox(ob), "modifiers": len(ob.modifiers)})
    print(f"PROJECT read-only inspection: parts={len(parts)} cutters={len(cutters)} refs={len(refs)} recipe_stored={'parametric_recipe.py' in bpy.data.texts}")
    return {"env": env, "specs": specs, "recipe_fns": [], "parts": parts, "cutters": cutters, "refs": refs}


def ensure_collections():
    """Create the three canonical top-level collections if missing."""
    root = bpy.context.scene.collection
    out = {}
    for n in CANON:
        c = bpy.data.collections.get(n) or bpy.data.collections.new(n)
        if c.name not in root.children:
            root.children.link(c)
        out[n] = c
    return out


def hide_cutters():
    """hide_set(True) on every object in 2_Boolean_Cutters; hide_viewport stays False."""
    c = bpy.data.collections.get("2_Boolean_Cutters")
    for o in (c.objects if c else []):
        o.hide_viewport = False
        o.hide_set(True)


# ---------------------------------------------------- persistent in-file specs
def save_specs(target=None, **specs):
    """Merge and persist JSON-serializable CAD measurements into target['cad_specs'] (default: scene)."""
    tgt = target if target is not None else bpy.context.scene
    cur = json.loads(tgt["cad_specs"]) if "cad_specs" in tgt else {}
    cur.update(specs)
    tgt["cad_specs"] = json.dumps(cur, sort_keys=True)
    print(f"SPECS saved on {getattr(tgt, 'name', 'scene')}: keys={list(cur.keys())}")
    return cur


def get_specs(target=None, verbose=False):
    """Read persisted CAD measurements from target['cad_specs'] (default: scene) in one call."""
    tgt = target if target is not None else bpy.context.scene
    cur = json.loads(tgt["cad_specs"]) if "cad_specs" in tgt else {}
    digest = json.dumps(cur) if verbose else f"keys={list(cur)}"
    print(f"SPECS ({getattr(tgt, 'name', 'scene')}): {digest}")
    return cur


def evaluated_world_mesh(obj):
    """Return an owned BMesh with evaluated modifiers and world transforms applied.

    Caller must free it. Diagnostics never modify the source object's mesh.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), depsgraph=dg)
    bm = bmesh.new()
    try:
        bm.from_mesh(me)
        bm.transform(obj.matrix_world)
        bm.normal_update()
        bm.verts.index_update()
        bm.faces.ensure_lookup_table()
        return bm
    except Exception:
        bm.free()
        raise
    finally:
        bpy.data.meshes.remove(me)


def mesh_fingerprint(obj):
    """Hash evaluated world coordinates/topology, units and transform, without rounding."""
    bm = evaluated_world_mesh(obj)
    try:
        payload = {"vertices": [tuple(v.co) for v in bm.verts],
                   "faces": [tuple(v.index for v in f.verts) for f in bm.faces],
                   "unit_scale": bpy.context.scene.unit_settings.scale_length}
        return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()
    finally:
        bm.free()


def record_measurement(key, value, source, frame="world", method="unspecified",
                       uncertainty=None, target=None):
    """Persist a value with explicit provenance; legacy save_specs remains available.

    source may be a mesh object (fingerprinted), a source URL, or user-confirmed text.
    Uncertainty uses the same units as value; None means not established, never exact.
    """
    mesh = source if hasattr(source, "type") and source.type == 'MESH' else None
    record = {"value": value, "source": mesh.name if mesh else str(source),
              "geometry_fingerprint": mesh_fingerprint(mesh) if mesh else None,
              "frame": frame, "method": method, "uncertainty": uncertainty}
    save_specs(target=target, **{key: record})
    return record


def save_recipe(code_str, name="parametric_recipe.py"):
    """Store recipe text without evaluating it. Use load_recipe() explicitly afterwards."""
    ast.parse(code_str, filename=name)
    txt = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    txt.clear()
    txt.write(code_str)
    print(f"RECIPE stored: {name} ({len(code_str.splitlines())} lines); not executed")
    return txt


def get_recipe(name="parametric_recipe.py"):
    """Return and print the parametric rebuild script from bpy.data.texts[name] if present."""
    txt = bpy.data.texts.get(name)
    s = txt.as_string() if txt else ""
    print(f"RECIPE '{name}': {len(s.splitlines())} lines" if txt else f"RECIPE '{name}': (not found)")
    return s


def make_keepout_box(name, x_range, y_range, z_range, collection="3_References"):
    """Create or update a wireframe keep-out box (`KeepOut_<Name>`) in 3_References."""
    full_name = name if name.startswith("KeepOut_") else f"KeepOut_{name}"
    pts = [
        (x_range[0], y_range[0]), (x_range[1], y_range[0]),
        (x_range[1], y_range[1]), (x_range[0], y_range[1]),
    ]
    ob = bpy.data.objects.get(full_name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
    ob = make_extruded_cutter(full_name, pts, z_range[1] - z_range[0], axis='Z',
                              start=z_range[0], collection=collection, hide=False)
    ob.display_type = 'WIRE'
    ob.hide_render = True
    return ob


def make_keepout_cylinder(name, center_xyz, radius, length, axis='Y', segments=64, collection="3_References"):
    """Create or update a wireframe keep-out cylinder (`KeepOut_<Name>`) in 3_References."""
    full_name = name if name.startswith("KeepOut_") else f"KeepOut_{name}"
    axis = axis.upper()
    if axis not in ('X', 'Y', 'Z') or min(radius, length) <= 0 or segments < 8:
        raise ValueError("Require X/Y/Z axis, positive dimensions and >=8 segments")
    cx, cy, cz = center_xyz
    pts = [( (cx if axis != 'X' else cy) + radius * math.cos(2 * math.pi * i / segments),
             (cz if axis in ('X', 'Y') else cy) + radius * math.sin(2 * math.pi * i / segments) )
           for i in range(segments)]
    ob = bpy.data.objects.get(full_name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
    start = (cy if axis == 'Y' else (cx if axis == 'X' else cz)) - 0.5 * length
    ob = make_extruded_cutter(full_name, pts, length, axis=axis,
                              start=start, collection=collection, hide=False)
    ob.display_type = 'WIRE'
    ob.hide_render = True
    return ob


# ------------------------------------------------------------------- mesh care
def cleanup_mesh(obj, dist=0.01):
    """Merge doubles, dissolve degenerate geometry, drop loose edges/verts, fix normals."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    before = (len(bm.verts), len(bm.faces))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)
    loose_e = [e for e in bm.edges if not e.link_faces]
    if loose_e:
        bmesh.ops.delete(bm, geom=loose_e, context='EDGES')
    loose_v = [v for v in bm.verts if not v.link_edges]
    if loose_v:
        bmesh.ops.delete(bm, geom=loose_v, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    after = (len(bm.verts), len(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    r = {"verts": (before[0], after[0]), "faces": (before[1], after[1])}
    print(f"CLEANUP {obj.name}: verts {before[0]}->{after[0]}, faces {before[1]}->{after[1]}")
    return r


def _components(bm):
    seen, n = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        n += 1
        seen.add(v.index)
        stack = [v]
        while stack:
            cur = stack.pop()
            for e in cur.link_edges:
                o = e.other_vert(cur)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
    return n


def _mesh_bounds(bm):
    if not bm.verts:
        raise ValueError("Empty mesh cannot be validated")
    return [(min(v.co[i] for v in bm.verts), max(v.co[i] for v in bm.verts)) for i in range(3)]


def _inside_closed(point, bvh, tolerance=0.01):
    """Parity classification for closed meshes; None means inconsistent rays."""
    near = bvh.find_nearest(point)
    if near[0] is None or near[3] <= tolerance:
        return False  # boundary contact, not strict interior
    votes = []
    for raw in [(1, .371, .173), (.193, 1, .417), (.269, .153, 1)]:
        direction = Vector(raw).normalized()
        origin = point.copy()
        count = 0
        for _ in range(10000):
            hit = bvh.ray_cast(origin, direction)
            if hit[0] is None:
                break
            count += 1
            origin = hit[0] + direction * max(tolerance * .1, 1e-6)
        else:
            return None
        votes.append(bool(count % 2))
    return votes[0] if all(v == votes[0] for v in votes) else None


def mesh_relation(bm_a, bm_b, tolerance=0.01, max_samples=20000):
    """World-space contact/interference screening with containment checks.

    Strict interior is sampled at vertices, edge midpoints and face centres; this
    is not a continuous solid-intersection proof. Open meshes and sample limits
    are reported as unknown instead of silently passing containment.
    """
    if tolerance <= 0 or max_samples < 1:
        raise ValueError("Positive tolerance and sample budget required")
    ba, bb = _mesh_bounds(bm_a), _mesh_bounds(bm_b)
    overlap = [min(a[1], b[1]) - max(a[0], b[0]) for a, b in zip(ba, bb)]
    if min(overlap) < -tolerance:
        return {"status": "clear", "penetration": False, "samples": 0, "surface_pairs": 0}
    av, bv = BVHTree.FromBMesh(bm_a), BVHTree.FromBMesh(bm_b)
    pairs = av.overlap(bv)
    if any(not e.is_manifold for m in (bm_a, bm_b) for e in m.edges):
        return {"status": "unknown_open_mesh", "penetration": None,
                "surface_pairs": len(pairs), "samples": 0}
    # Axis-aligned separating contact plane excludes positive volume overlap.
    if min(overlap) <= tolerance:
        return {"status": "contact" if pairs else "clear", "penetration": False,
                "samples": 0, "surface_pairs": len(pairs)}
    used = 0
    for mesh, own_bvh, other_bvh, bounds in [(bm_a, av, bv, bb), (bm_b, bv, av, ba)]:
        from itertools import chain
        sign = 1 if mesh.calc_volume() >= 0 else -1
        def interior_probes():
            for face in mesh.faces:
                point = face.calc_center_median() - face.normal * sign * (2 * tolerance)
                if _inside_closed(point, own_bvh, tolerance * .1):
                    yield point
        candidates = chain((v.co for v in mesh.verts),
                           ((e.verts[0].co + e.verts[1].co) * .5 for e in mesh.edges),
                           (f.calc_center_median() for f in mesh.faces), interior_probes())
        for point in candidates:
            if not all(lo - tolerance <= point[i] <= hi + tolerance for i, (lo, hi) in enumerate(bounds)):
                continue
            if used >= max_samples:
                return {"status": "unknown_sample_budget", "penetration": None,
                        "samples": used, "surface_pairs": len(pairs)}
            used += 1
            inside = _inside_closed(point, other_bvh, tolerance)
            if inside is None:
                return {"status": "unknown_ray_parity", "penetration": None,
                        "samples": used, "surface_pairs": len(pairs)}
            if inside:
                return {"status": "penetration", "penetration": True,
                        "sample_point": tuple(point), "samples": used, "surface_pairs": len(pairs)}
    return {"status": "contact_or_sampled_clear" if pairs else "sampled_clear",
            "penetration": False, "samples": used, "surface_pairs": len(pairs),
            "scope": "Discrete strict-interior samples; thin crossings may need finer sampling or solid booleans"}


def check_fit(part, reference, tolerance=0.01, allow_contact=True, max_samples=20000):
    """Check final seating separately from insertion; contact is explicit."""
    _require_mm_scene()
    a, b = evaluated_world_mesh(part), evaluated_world_mesh(reference)
    try:
        result = mesh_relation(a, b, tolerance, max_samples)
    finally:
        a.free(); b.free()
    contact = result.get("surface_pairs", 0) > 0
    result["pass"] = result["penetration"] is False and (allow_contact or not contact)
    result["frame"] = "world"
    print(f"FIT {part.name}/{reference.name}: {result['status']} contact_allowed={allow_contact}")
    return result


def _require_mm_scene():
    units = bpy.context.scene.unit_settings
    if units.system != 'METRIC' or abs(units.scale_length - .001) > 1e-9:
        raise ValueError("This diagnostic requires millimetre coordinates (metric scale_length=.001); no silent rescaling")


def audit(obj, overhang_deg=45.0, verbose=False):
    """Audit the EVALUATED mesh (modifiers included) in world space.

    Reports: bbox, volume, shells, non-manifold edges, zero-area faces, overhang area
    steeper than `overhang_deg` from vertical (bed-contact faces excluded), and any
    collisions with `KeepOut_*` meshes in `3_References`.
    Output is one summary line (+ at most 5 worst Z-bands when overhangs exist).
    """
    _require_mm_scene()
    bm = evaluated_world_mesh(obj)
    bm.verts.index_update()
    if not bm.verts:
        bm.free()
        raise ValueError("Empty mesh cannot be audited")
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    zmin = min(zs)
    nz_limit = -math.cos(math.radians(90.0 - overhang_deg))  # 45deg -> -0.7071
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    zero = sum(1 for f in bm.faces if f.calc_area() < 1e-6)
    steep, bands = 0.0, {}
    for f in bm.faces:
        a = f.calc_area()
        if a < 1e-4 or f.normal.z >= nz_limit:
            continue
        if abs(f.calc_center_median().z - zmin) < 0.05 and f.normal.z < -0.99:
            continue  # bed contact
        steep += a
        k = round(f.calc_center_median().z)
        bands[k] = bands.get(k, 0.0) + a

    # Check BVHTree overlap against any KeepOut_* objects and compute min_wall thickness
    bvh_part = BVHTree.FromBMesh(bm, epsilon=0.0)
    ko_hits, ko_unknown = [], []
    ko_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("KeepOut_")]
    for ko in ko_objs:
        bm_k = evaluated_world_mesh(ko)
        try:
            relation = mesh_relation(bm, bm_k)
            if relation['penetration'] or relation.get('surface_pairs'):
                ko_hits.append(ko.name)
            elif relation['penetration'] is None:
                ko_unknown.append(ko.name)
        finally:
            bm_k.free()

    bm.faces.ensure_lookup_table()
    min_wall, min_wall_at = float("inf"), None
    for f in bm.faces:
        if f.calc_area() < 2.0:
            continue
        c = f.calc_center_median()
        hit, hit_no, idx, dist = bvh_part.ray_cast(c - f.normal * 0.02, -f.normal)
        if hit is not None and dist > 0.1 and hit_no.dot(f.normal) < -0.90:
            ring_verts = set(v.index for v in f.verts for e in v.link_edges for v in e.verts)
            if not (ring_verts & set(v.index for v in bm.faces[idx].verts)):
                if dist + 0.02 < min_wall:
                    min_wall = dist + 0.02
                    min_wall_at = tuple(round(x, 1) for x in c)
    min_wall_mm = round(min_wall, 2) if min_wall < float("inf") else None

    r = {
        "name": obj.name,
        "size": (round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2), round(max(zs) - zmin, 2)),
        "volume_cm3": round(bm.calc_volume() / 1000.0, 2),
        "shells": _components(bm),
        "non_manifold": nm,
        "zero_area": zero,
        "overhang_mm2": round(steep, 2),
        "min_wall_mm": min_wall_mm,
        "min_wall_at": min_wall_at,
        "keepout_hits": ko_hits,
        "faces": len(bm.faces),
    }
    ok = nm == 0 and zero == 0 and r["shells"] == 1
    r['checks'] = {"mesh_integrity": "pass" if ok else "fail",
                   "keepouts": "fail" if ko_hits else ("unknown" if ko_unknown else ("sampled_clear" if ko_objs else "not_checked")),
                   "supports": "required" if steep else "no_overhangs_detected",
                   "wall_sample": "estimate_only" if min_wall_mm is not None else "unknown",
                   "mechanical": "not_checked", "physical": "not_checked"}
    r['keepout_unknown'] = ko_unknown
    r['pass_scope'] = 'mesh_integrity_only'
    ko_str = f" keepout_hits={ko_hits or 0}" if ko_objs else ""
    mw_str = f" min_wall={min_wall_mm}mm@{min_wall_at}" if min_wall_mm is not None else ""
    print(f"AUDIT {obj.name}: size={r['size']} vol={r['volume_cm3']}cm3 shells={r['shells']} "
          f"nonmanifold={nm} zero_area={zero} overhang>{overhang_deg:.0f}deg={r['overhang_mm2']}mm2"
          f"{mw_str}{ko_str} faces={r['faces']} mesh={'valid' if ok else 'invalid'} "
          f"keepouts={r['checks']['keepouts']} supports={r['checks']['supports']}")
    if bands:
        top = sorted(bands.items(), key=lambda kv: -kv[1])[:5]
        print("  overhang Z-bands (z_mm: area_mm2): " + ", ".join(f"{z}: {a:.1f}" for z, a in top))
    r["pass"] = ok
    bm.free()
    return r


def audit_cantilever(obj, axis='X', root_pos=None, tip_pos=None, load_n=25.0, e_mpa=900.0, slices=40):
    """Approximate ideal solid-section Euler–Bernoulli beam screening.

    Slices the evaluated mesh along `axis` ('X' or 'Y') from `root_pos` to `tip_pos`,
    computing sampled cross-sectional area A(s), neutral axis zc(s), second moment I(s),
    section modulus Zs(s), peak bending stress (MPa), and Euler-Bernoulli tip sag (mm).
    Assumes homogeneous material, ideal root fixity, uniformly distributed load,
    negligible shear/joint compliance and small deflection. Does not model infill,
    print anisotropy, creep, fatigue, truss joints or foot point loads. No safety pass.
    """
    _require_mm_scene()
    def finite(value):
        try:
            return not isinstance(value, bool) and math.isfinite(value)
        except (TypeError, ValueError):
            return False
    if (not isinstance(axis, str) or axis.upper() not in ('X', 'Y')
            or not isinstance(slices, int) or isinstance(slices, bool) or slices < 2
            or not finite(e_mpa) or e_mpa <= 0 or not finite(load_n) or load_n < 0
            or any(v is not None and not finite(v) for v in (root_pos, tip_pos))):
        raise ValueError("Require X/Y axis, >=2 slices, positive modulus and nonnegative load")
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), depsgraph=dg)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bm.transform(obj.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.normal_update()

    ax = 0 if axis.upper() == 'X' else 1
    ay = 1 if ax == 0 else 0
    coords = [v.co[ax] for v in bm.verts]
    if not coords:
        bm.free()
        raise ValueError("Empty mesh cannot be screened as a beam")
    s0 = root_pos if root_pos is not None else min(coords) + 1.0
    s1 = tip_pos if tip_pos is not None else max(coords) - 1.0
    span = abs(s1 - s0)
    if span <= 1e-9:
        bm.free()
        raise ValueError("Beam span must be positive")
    sign_dir = 1.0 if s1 >= s0 else -1.0
    ds = span / slices

    weak_s, min_zs, min_i, max_stress = s0, float("inf"), float("inf"), 0.0
    min_i_s, max_stress_s = s0, s0
    tip_sag = 0.0
    for k in range(slices):
        s = s0 + sign_dir * (k + 0.5) * ds
        area, qz, iz0 = 0.0, 0.0, 0.0
        zs_slice = []
        for f in bm.faces:
            vs = f.verts
            d = [v.co[ax] - s for v in vs]
            pts = []
            for i in range(3):
                j = (i + 1) % 3
                if (d[i] < 0.0 and d[j] >= 0.0) or (d[i] >= 0.0 and d[j] < 0.0):
                    t = d[i] / (d[i] - d[j])
                    pts.append((vs[i].co[ay] + t * (vs[j].co[ay] - vs[i].co[ay]),
                                vs[i].co.z + t * (vs[j].co.z - vs[i].co.z)))
            if len(pts) == 2:
                (y0, z0), (y1, z1) = pts[0], pts[1]
                ny, nz = f.normal[ay], f.normal.z
                if (z1 - z0) * ny - (y1 - y0) * nz < 0.0:
                    y0, z0, y1, z1 = y1, z1, y0, z0
                dz = z1 - z0
                area += 0.5 * (y0 + y1) * dz
                qz += (0.25 * (y0 + y1) * (z0 + z1) + (y1 - y0) * dz / 12.0) * dz
                iz0 += dz * (y0 * (z0 * z0 / 4.0 + z0 * z1 / 6.0 + z1 * z1 / 12.0)
                             + y1 * (z0 * z0 / 12.0 + z0 * z1 / 6.0 + z1 * z1 / 4.0))
                zs_slice.extend((z0, z1))
        if area > 1e-9 and zs_slice:
            zc = qz / area
            iyy = iz0 - area * zc * zc
            c_max = max(abs(max(zs_slice) - zc), abs(min(zs_slice) - zc))
            if not math.isfinite(iyy) or iyy <= 1e-12 or c_max <= 1e-12:
                bm.free()
                raise ValueError(f"Invalid beam section at {axis}={s}; no artificial stiffness floor applied")
            zs_mod = iyy / c_max
            arm = abs(s1 - s)
            moment = load_n * (arm ** 2) / (2.0 * span)  # total uniformly distributed load
            stress = moment / zs_mod
            tip_sag += (moment / (e_mpa * iyy)) * arm * ds
            if zs_mod < min_zs:
                min_zs, weak_s = zs_mod, s
            if iyy < min_i:
                min_i, min_i_s = iyy, s
            if stress > max_stress:
                max_stress, max_stress_s = stress, s
        else:
            bm.free()
            raise ValueError(f"Missing beam section at {axis}={s}; continuous beam assumption is invalid")
    bm.free()
    r = {
        "axis": axis.upper(), "span_mm": round(span, 1), "weak_pos_mm": round(weak_s, 1),
        "min_I_mm4": round(min_i, 1), "min_Zs_mm3": round(min_zs, 1),
        "min_I_pos_mm": round(min_i_s, 1),
        "weak_pos_scope": "position of minimum sampled section modulus Zs",
        "max_stress_mpa": round(max_stress, 2), "est_tip_sag_mm": round(tip_sag, 2),
        "max_stress_pos_mm": round(max_stress_s, 1),
        "scope": "approximate_ideal_solid_beam", "load_distribution": "uniform",
        "load_n": load_n, "e_mpa": e_mpa, "slices": slices,
        "assumptions": ["ideal root fixity", "homogeneous solid sections", "small deflection",
                        "no infill/anisotropy/creep/fatigue/joint model"],
    }
    if not all(math.isfinite(value) for value in [min_i, min_zs, max_stress, tip_sag]):
        raise ValueError("No usable beam sections; do not interpret this geometry as a valid beam")
    print(f"BEAM ESTIMATE {obj.name} ({r['axis']}={s0:.1f}..{s1:.1f}mm, F={load_n}N, E={e_mpa}MPa): "
          f"weak_{r['axis']}={r['weak_pos_mm']}mm I={r['min_I_mm4']}mm4 Zs={r['min_Zs_mm3']}mm3 "
          f"stress={r['max_stress_mpa']}MPa tip_sag={r['est_tip_sag_mm']}mm")
    return r


def check_insertion(part, moving_obj, path_vec, steps=None, max_step_mm=1.0,
                    final_step_mm=0.1, final_distance_mm=2.0, max_samples=20000,
                    max_positions=2000, tolerance=0.01, allow_seated_contact=True):
    """Sample insertion in WORLD coordinates, including final seating explicitly.

    steps is a compatibility hint, never permission to exceed max_step_mm.
    Intermediate samples reject surface contact; final seating may allow contact.
    This is a discrete path screen, not continuous collision detection.
    """
    _require_mm_scene()
    vector = Vector(path_vec)
    distance = vector.length
    if min(max_step_mm, final_step_mm, tolerance) <= 0 or final_distance_mm < 0 or max_positions < 1:
        raise ValueError("Positive step/tolerance/budget and nonnegative final distance required")
    if steps is not None and steps < 1:
        raise ValueError("steps must be >=1")
    count = max(1, math.ceil(distance / max_step_mm), steps or 0)
    final_count = math.ceil(min(distance, final_distance_mm) / final_step_mm)
    if distance and count + final_count + 1 > max_positions:
        raise ValueError("Insertion position budget exceeded; choose explicit steps/budget for this geometry")
    fractions = {k / count for k in range(count + 1)} if distance else {0.0}
    if distance:
        for k in range(final_count + 1):
            fractions.add(min(distance, k * final_step_mm) / distance)
    a, b = evaluated_world_mesh(part), evaluated_world_mesh(moving_obj)
    failed, unknown, tested = [], [], 0
    seated = None
    try:
        for frac in sorted(fractions, reverse=True):
            moved = b.copy()
            try:
                bmesh.ops.translate(moved, verts=moved.verts, vec=vector * frac)
                relation = mesh_relation(a, moved, tolerance, max_samples)
            finally:
                moved.free()
            tested += 1
            if frac == 0:
                seated = relation
                bad = relation['penetration'] is not False or (not allow_seated_contact and relation.get('surface_pairs', 0))
            else:
                bad = relation['penetration'] is not False or relation.get('surface_pairs', 0)
            if relation['penetration'] is None:
                unknown.append(round(distance * frac, 6))
            if bad:
                failed.append(round(distance * frac, 6))
    finally:
        a.free(); b.free()
    result = {"pass": not failed, "frame": "world", "tested_positions": tested,
              "max_step_mm": distance / count, "final_step_mm": final_step_mm,
              "blocked_offsets_mm": failed, "unknown_offsets_mm": unknown,
              "hit_fracs": [round(d / distance, 6) if distance else 0 for d in failed],
              "seated": seated, "scope": "sampled path + strict-interior final seating screen"}
    print(f"INSERTION {moving_obj.name}/{part.name}: positions={tested} blocked={len(failed)} unknown={len(unknown)} seated={seated['status']}")
    return result


def toolbox_check(obj, details=False):
    """Run an available 3D-Print Toolbox on a temporary evaluated WORLD mesh.

    Restores the caller's active object and selection even on extension errors.
    details=True includes up to five element indices per supported report item.
    """
    try:
        bpy.ops.mesh.print3d_check_all.get_rna_type()
    except (AttributeError, RuntimeError):
        print(f"TOOLBOX {obj.name}: unavailable; use scoped audit results")
        return {"status": "unavailable"}
    bm = evaluated_world_mesh(obj)
    me = bpy.data.meshes.new(obj.name + "_check_mesh")
    try:
        bm.to_mesh(me)
    finally:
        bm.free()
    tmp = bpy.data.objects.new(obj.name + "_chk", me)
    bpy.context.scene.collection.objects.link(tmp)
    prev = bpy.context.view_layer.objects.active
    selected = list(bpy.context.selected_objects)
    try:
        for ob in bpy.context.view_layer.objects:
            ob.select_set(False)
        tmp.select_set(True)
        bpy.context.view_layer.objects.active = tmp
        bpy.ops.mesh.print3d_check_all()
        items = list(bpy.context.scene.print3d_toolbox.get_report())
        counts = {item.name: item.value for item in items}
        print(f"TOOLBOX {obj.name}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
        if not details:
            return counts
        return {"status": "checked", "counts": counts,
                "sample_indices": {item.name: list(getattr(item, 'indices', []))[:5] for item in items}}
    finally:
        bpy.data.objects.remove(tmp, do_unlink=True)
        bpy.data.meshes.remove(me)
        for ob in bpy.context.view_layer.objects:
            ob.select_set(ob in selected)
        bpy.context.view_layer.objects.active = prev


def inspect_ref(obj, top_n=8):
    """Compact world-space summary of a reference mesh (bounds, shells, dominant Z planes)."""
    bm = evaluated_world_mesh(obj)
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    z_planes = {}
    for f in bm.faces:
        if abs(f.normal.z) > 0.95 and f.calc_area() > 10.0:
            z = round(f.calc_center_median().z, 2)
            z_planes[z] = round(z_planes.get(z, 0.0) + f.calc_area(), 1)
    top_z = sorted(z_planes.items(), key=lambda kv: -kv[1])[:top_n]
    r = {
        "x": (round(min(xs), 2), round(max(xs), 2)),
        "y": (round(min(ys), 2), round(max(ys), 2)),
        "z": (round(min(zs), 2), round(max(zs), 2)),
        "shells": _components(bm),
        "top_z_planes": top_z,
    }
    bm.free()
    print(f"REF {obj.name}: X={r['x']} Y={r['y']} Z={r['z']} shells={r['shells']} z_planes={top_z}")
    return r


def quiet_summary(coords, label="POINTS"):
    """Compact 1-line statistical digest (count, X/Y/Z spans, centroid) of vectors/tuples/vertices.

    Use whenever querying vertex or face clusters to prevent flooding LLM context with raw arrays.
    """
    pts = []
    for c in coords:
        if hasattr(c, "co"):
            pts.append(c.co)
        elif hasattr(c, "x") and hasattr(c, "y"):
            pts.append(c)
        elif isinstance(c, (tuple, list)) and len(c) >= 2:
            pts.append(Vector((c[0], c[1], c[2] if len(c) > 2 else 0.0)))
    if not pts:
        print(f"{label}: n=0 (empty)")
        return {"n": 0}
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] if len(p) > 2 else 0.0 for p in pts]
    r = {
        "n": len(pts),
        "x": (round(min(xs), 2), round(max(xs), 2)),
        "y": (round(min(ys), 2), round(max(ys), 2)),
        "z": (round(min(zs), 2), round(max(zs), 2)),
        "centroid": (round(sum(xs) / len(xs), 2), round(sum(ys) / len(ys), 2), round(sum(zs) / len(zs), 2))
    }
    print(f"{label}: n={r['n']} X={r['x']} Y={r['y']} Z={r['z']} centroid={r['centroid']}")
    return r


def quiet_inspect(obj, z_range=None, min_area=None):
    """World-space filtered digest of vertices/faces on obj matching z_range=(z0, z1) or min_area.

    Prints one summary line instead of raw coordinate loops.
    """
    bm = evaluated_world_mesh(obj)
    verts = bm.verts
    if z_range is not None:
        verts = [v for v in verts if z_range[0] <= v.co.z <= z_range[1]]
    faces = bm.faces
    if z_range is not None:
        faces = [f for f in faces if z_range[0] <= f.calc_center_median().z <= z_range[1]]
    if min_area is not None:
        faces = [f for f in faces if f.calc_area() >= min_area]
    label = f"INSPECT {obj.name}" + (f" Z={z_range}" if z_range else "") + (f" area>={min_area}" if min_area else "")
    res = quiet_summary([v.co for v in verts], label=label)
    res["faces_matching"] = len(faces)
    bm.free()
    return res


# --------------------------------------------------------------------- cutters
def rounded_poly_2d(pts2d, r=3.0, arc_steps=6):
    """Round corners of a 2D polygon `pts2d` with uniform radius `r` or per-vertex radii list/tuple (`r_i <= 0` keeps sharp)."""
    pts = [Vector((p[0], p[1])) for p in pts2d]
    m = len(pts)
    radii = [r] * m if isinstance(r, (int, float)) else list(r)
    area2 = sum(pts[i].x * pts[(i + 1) % m].y - pts[(i + 1) % m].x * pts[i].y for i in range(m))
    if area2 < 0:
        pts.reverse()
        radii.reverse()
    out = []
    for i in range(m):
        ri = radii[i]
        v1 = (pts[(i - 1) % m] - pts[i]).normalized()
        v2 = (pts[(i + 1) % m] - pts[i]).normalized()
        ha = 0.5 * math.acos(max(-1.0, min(1.0, v1.dot(v2))))
        if ri <= 1e-4 or ha < 1e-3 or abs(ha - 0.5 * math.pi) < 1e-3:
            out.append((round(pts[i].x, 3), round(pts[i].y, 3)))
            continue
        dc, dt = ri / math.sin(ha), ri / math.tan(ha)
        c = pts[i] + (v1 + v2).normalized() * dc
        t1, t2 = pts[i] + v1 * dt, pts[i] + v2 * dt
        a1, a2 = math.atan2(t1.y - c.y, t1.x - c.x), math.atan2(t2.y - c.y, t2.x - c.x)
        da = (a2 - a1) % (2.0 * math.pi)
        if da > math.pi:
            da -= 2.0 * math.pi
        for s in range(arc_steps + 1):
            ang = a1 + da * (s / arc_steps)
            out.append((round(c.x + ri * math.cos(ang), 3), round(c.y + ri * math.sin(ang), 3)))
    return out


def rect_2d(w, h, cx=0.0, cy=0.0, r=0.0, arc_steps=6):
    """2D rectangle of `(w, h)` centered at `(cx, cy)` with uniform radius `r` or 4-tuple `(r_bl, r_br, r_tr, r_tl)`."""
    hw, hh = 0.5 * w, 0.5 * h
    pts = [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]
    return rounded_poly_2d(pts, r=r, arc_steps=arc_steps) if r else pts


def set_extruded_profile(obj, pts2d, length, axis='Z', start=0.0):
    """Update `obj.data` in-place from a 2D profile extruded along `axis` ('X', 'Y', or 'Z').

    axis='Z': pts2d are (x, y), extruded along +Z from `start` for `length`.
    axis='Y': pts2d are (x, z), extruded along +Y from `start` for `length`.
    axis='X': pts2d are (y, z), extruded along +X from `start` for `length`.
    Also caches the 2D profile metadata in `obj["cutter_def"]`.
    """
    bm = bmesh.new()
    def pt(p, t):
        if axis == 'Z':
            return (p[0], p[1], t)
        return (p[0], t, p[1]) if axis == 'Y' else (t, p[0], p[1])
    a = [bm.verts.new(pt(p, start)) for p in pts2d]
    b = [bm.verts.new(pt(p, start + length)) for p in pts2d]
    n = len(pts2d)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([a[i], b[i], b[j], a[j]])
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj["cutter_def"] = json.dumps({
        "axis": axis, "start": round(start, 3), "length": round(length, 3),
        "pts2d": [[round(p[0], 3), round(p[1], 3)] for p in pts2d],
    })
    return obj


def make_extruded_cutter(name, pts2d, length, axis='Z', start=0.0, location=(0, 0, 0),
                         collection="2_Boolean_Cutters", hide=True):
    """One watertight single-shell cutter from a closed 2D profile ('X', 'Y', or 'Z')."""
    me = bpy.data.meshes.new(name + "_Mesh")
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    set_extruded_profile(ob, pts2d, length, axis=axis, start=start)
    ensure_collections()[collection].objects.link(ob)
    ob.hide_viewport = False
    if hide:
        ob.hide_set(True)
    return ob


def make_cylinder_cutter(name, diameter, z0, z1, segments=96, location=(0, 0, 0), **kw):
    """Vertical cylinder cutter. `diameter` is the CAD diameter (not the as-printed one)."""
    r = diameter / 2.0
    pts = [(r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments))
           for i in range(segments)]
    return make_extruded_cutter(name, pts, z1 - z0, 'Z', z0, location, **kw)


def make_slotted_cylinder_cutter(name, bore_dia, channel_w, channel_len, z0, z1,
                                 angle_deg=0.0, flare_r=0.0, segments=64, location=(0, 0, 0), **kw):
    """Watertight single-shell cylinder cutter with an exit slot and optional entry mouth flares."""
    r_bore = bore_dia / 2.0
    hw = channel_w / 2.0
    rad = math.radians(angle_deg)
    ux, uy = math.sin(rad), math.cos(rad)
    nx, ny = uy, -ux
    pts = []
    start_a = math.atan2(-ny, -nx)
    for i in range(segments + 1):
        a = start_a + math.pi * (i / segments)
        pts.append((r_bore * math.cos(a), r_bore * math.sin(a)))
    if flare_r > 0.0:
        pts.append((nx * hw + ux * (channel_len - flare_r), ny * hw + uy * (channel_len - flare_r)))
        for s in range(1, 9):
            ta = math.pi - 0.5 * math.pi * (s / 8)
            pts.append((nx * (hw + flare_r * (1.0 + math.cos(ta))) + ux * (channel_len - flare_r + flare_r * math.sin(ta)),
                        ny * (hw + flare_r * (1.0 + math.cos(ta))) + uy * (channel_len - flare_r + flare_r * math.sin(ta))))
        pts.append((nx * (hw + flare_r) + ux * channel_len, ny * (hw + flare_r) + uy * channel_len))
        pts.append((-nx * (hw + flare_r) + ux * channel_len, -ny * (hw + flare_r) + uy * channel_len))
        for s in range(8, 0, -1):
            ta = 0.5 * math.pi * (s / 8)
            pts.append((-nx * (hw + flare_r * (1.0 - math.cos(ta))) + ux * (channel_len - flare_r + flare_r * math.sin(ta)),
                        -ny * (hw + flare_r * (1.0 - math.cos(ta))) + uy * (channel_len - flare_r + flare_r * math.sin(ta))))
        pts.append((-nx * hw + ux * (channel_len - flare_r), -ny * hw + uy * (channel_len - flare_r)))
    else:
        pts.append((nx * hw + ux * channel_len, ny * hw + uy * channel_len))
        pts.append((-nx * hw + ux * channel_len, -ny * hw + uy * channel_len))
    return make_extruded_cutter(name, pts, z1 - z0, 'Z', z0, location, **kw)


def add_live_boolean(target, cutter, name=None, operation='DIFFERENCE', solver='MANIFOLD'):
    """Attach `cutter` to `target` as a live Boolean modifier (reusable, editable)."""
    m = target.modifiers.new(name or f"B_{cutter.name}", 'BOOLEAN')
    m.object = cutter
    m.operation = operation
    m.solver = solver
    return m


def apply_modifiers(obj):
    """Bake all modifiers into the mesh (milestone/export only). Context independent (no bpy.ops)."""
    if not obj.modifiers:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), depsgraph=dg)
    old = obj.data
    new.name = old.name
    obj.modifiers.clear()
    obj.data = new
    if old.users == 0:
        bpy.data.meshes.remove(old)


# ------------------------------------------------------------ versioning/export
def next_version(project_dir):
    """Next unused positive integer across history/*_v<N>.blend|.3mf (ignores .blend1 backups)."""
    hist = os.path.join(project_dir, "history")
    nums = [0]
    if os.path.isdir(hist):
        for f in os.listdir(hist):
            m = re.search(r"_v(\d+)(?:[-_][^./\\]+)?\.(?:blend|(?:geometry\.)?3mf)$", f, re.I)
            if m:
                nums.append(int(m.group(1)))
    return max(nums) + 1


def _bake_copy(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), depsgraph=dg)
    tmp = bpy.data.objects.new(obj.name + "_export", me)
    tmp.matrix_world = obj.matrix_world
    bpy.context.scene.collection.objects.link(tmp)
    return tmp


def export_geometry_3mf(obj, filepath, on_bed=True):
    """Write neutral geometry-only 3MF, never a printer-configured project.

    Applies world transforms/modifiers, converts scene units to millimetres,
    and optionally translates only export geometry to Z=0. Source is unchanged.
    """
    units = bpy.context.scene.unit_settings
    if units.system != 'METRIC' or units.scale_length <= 0:
        raise ValueError("Declare metric scene units before export")
    filepath = os.path.abspath(filepath)
    if os.path.exists(filepath):
        with zipfile.ZipFile(filepath) as old:
            names = old.namelist()
            if any(n in names for n in ('Metadata/Slic3r_PE.config', 'Metadata/project_settings.config')):
                raise ValueError("Refusing to overwrite a configured project with neutral geometry")
    bm = evaluated_world_mesh(obj)
    try:
        if (not bm.verts or any(not e.is_manifold for e in bm.edges) or _components(bm) != 1
                or abs(bm.calc_volume()) == 0 or any(f.calc_area() == 0 for f in bm.faces)):
            raise ValueError("Geometry export requires one nonempty closed mesh shell")
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bm.verts.index_update()
        factor = units.scale_length * 1000.0
        offset = -min(v.co.z for v in bm.verts) if on_bed else 0.0
        vertices = [(v.co.x * factor, v.co.y * factor, (v.co.z + offset) * factor) for v in bm.verts]
        triangles = [tuple(v.index for v in f.verts) for f in bm.faces]
    finally:
        bm.free()
    text = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
            '<metadata name="Title">' + escape(obj.name) + ' geometry only</metadata>',
            '<resources><object id="1" type="model"><mesh><vertices>']
    text += [f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>' for x, y, z in vertices]
    text += ['</vertices><triangles>']
    text += [f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles]
    text += ['</triangles></mesh></object></resources><build><item objectid="1"/></build></model>']
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    temp_path = filepath + '.tmp'
    try:
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
            archive.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
            archive.writestr('3D/3dmodel.model', ''.join(text))
        os.replace(temp_path, filepath)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    result = {"path": filepath, "kind": "geometry_only", "units": "millimeter",
              "print_config": False, "vertices": len(vertices), "triangles": len(triangles),
              "assembly_to_print_z_mm": offset * factor, "source_fingerprint": mesh_fingerprint(obj)}
    print(f"GEOMETRY 3MF {obj.name}: vertices={len(vertices)} triangles={len(triangles)}; printer configuration absent")
    return result


def snapshot_and_export(project_dir, obj, project_name=None, suffix="", export=True,
                        log_msg=None, export_path=None):
    """Save an immutable .blend milestone and optional NEUTRAL geometry-only 3MF.

    A configured slicer project is a separate artifact produced/verified by the
    slicer workflow. Default neutral name is <name>.geometry.3mf; an existing
    configured root <name>.3mf is never overwritten by this helper.
    """
    aud = audit(obj)
    if export and not aud['pass']:
        raise RuntimeError("Geometry export blocked by mesh integrity failure")
    project_dir = os.path.abspath(project_dir)
    os.makedirs(os.path.join(project_dir, 'history'), exist_ok=True)
    root_name = project_name or (os.path.splitext(os.path.basename(bpy.data.filepath))[0]
                                if bpy.data.filepath else os.path.basename(project_dir))
    if any(char in root_name + suffix for char in ('/', chr(92))) or root_name in ('.', '..'):
        raise ValueError("Project names/suffixes must be filename components")
    if suffix and (suffix[0] not in '-_' or '.' in suffix):
        raise ValueError("Version suffix must start with '-' or '_' and contain no dots")
    version = next_version(project_dir)
    # Geometry-only suffixes are not version seeds; .blend remains authoritative.
    tag = f"{root_name}_v{version}{suffix}"
    hist_blend = os.path.join(project_dir, 'history', tag + '.blend')
    if os.path.exists(hist_blend):
        raise FileExistsError(hist_blend)
    bpy.ops.wm.save_as_mainfile(filepath=hist_blend, copy=True)
    out = {"version": version, "blend": hist_blend, "audit": aud,
           "artifact_kind": "geometry_only" if export else "blend_only",
           "root_blend_updated": False, "root_export_updated": False}
    if bpy.data.filepath and os.path.dirname(os.path.abspath(bpy.data.filepath)) == project_dir:
        bpy.ops.wm.save_mainfile()
        out['root_blend_updated'] = True
    if export:
        dest = os.path.abspath(export_path) if export_path else os.path.join(project_dir, root_name + '.geometry.3mf')
        result = export_geometry_3mf(obj, dest)
        history_dest = os.path.join(project_dir, 'history', tag + '.geometry.3mf')
        if os.path.exists(history_dest):
            raise FileExistsError(history_dest)
        import shutil
        shutil.copy2(dest, history_dest)
        out.update({"3mf": dest, "history_3mf": history_dest,
                    "geometry_export": result, "root_export_updated": export_path is None})
    print(f"SNAPSHOT v{version}: root_blend_updated={out['root_blend_updated']} geometry_export_updated={out['root_export_updated']}; configured project not produced")
    if log_msg:
        log(project_dir, f"**v{version}** ({tag}): {log_msg}")
    return out


def log(project_dir, text):
    """Append one line to the append-only LOG.md (never rewrite PROJECT.md for history)."""
    import datetime
    p = os.path.join(project_dir, "LOG.md")
    new = not os.path.exists(p)
    with open(p, "a") as f:
        if new:
            f.write("# Project Log (append-only)\n\n")
        f.write(f"- {datetime.date.today().isoformat()} - {text}\n")
    print(f"LOG +1 line -> {p}")


# Persist helpers and core modules in builtins so a single session bootstrap makes them available across all MCP calls
import builtins as _builtins
for _k, _v in list(globals().items()):
    if not _k.startswith("_") and (callable(_v) or _k in ("bmesh", "json", "math", "os", "re", "CANON")):
        setattr(_builtins, _k, _v)


