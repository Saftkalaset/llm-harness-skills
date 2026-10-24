"""Run only in a fresh process: blender -b --factory-startup --python this_file.

Uses generated meshes and temporary files, never an existing project or live MCP.
"""
import bpy
import bmesh
import json
import math
import pathlib
import tempfile
import unittest
import zipfile
from unittest.mock import patch

if not bpy.app.background or bpy.data.filepath:
    raise RuntimeError("Regression tests require a fresh --background --factory-startup process")

LIB = pathlib.Path(__file__).resolve().parents[1] / "lib.py"
ns = {"__name__": "cad_regression_helpers"}
exec(compile(LIB.read_text(), str(LIB), "exec"), ns, ns)


def cube(name, location=(0, 0, 0), scale=(1, 1, 1)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2)
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    ob.scale = scale
    bpy.context.view_layer.update()
    return ob


class BlenderWorkflowRegression(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        u = bpy.context.scene.unit_settings
        u.system = 'METRIC'
        u.scale_length = .001
        u.length_unit = 'MILLIMETERS'

    def test_store_and_inspect_recipe_have_no_side_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / (pathlib.Path(folder).name + '.blend')
            ns['save_recipe']("bpy.context.scene['executed'] = True\n")
            self.assertNotIn('executed', bpy.context.scene)
            bpy.ops.wm.save_as_mainfile(filepath=str(path))
            ns['open_project'](folder)
            self.assertNotIn('executed', bpy.context.scene)
            with self.assertRaises(ValueError):
                ns['load_recipe']()
            self.assertNotIn('executed', bpy.context.scene)

    def test_recipe_functions_share_constants_and_helpers(self):
        ns['save_recipe']('OFFSET=7\ndef helper(x):\n    return x + OFFSET\ndef build(x=2):\n    return helper(x)\n')
        ns['load_recipe']()
        self.assertEqual(ns['build'](), 9)
        ns['save_recipe']('def bad(x=print("side effect")):\n    return x\n')
        with self.assertRaises(ValueError):
            ns['load_recipe']()

    def test_ambiguous_project_is_not_opened(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ['one.blend', 'two.blend']:
                (pathlib.Path(folder) / name).write_bytes(b'not opened')
            with self.assertRaises(ValueError):
                ns['open_project'](folder, allow_discard=True)

    def test_dirty_scene_cannot_be_discarded(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as other:
            bpy.ops.wm.save_as_mainfile(filepath=str(pathlib.Path(first) / 'first.blend'))
            # Background Blender does not reliably set is_dirty for RNA/operators.
            # Exercise the actual guard with only that external state injected.
            class DirtyData:
                is_dirty = True
                def __getattr__(self, key):
                    return getattr(bpy.data, key)
            class DirtyBpy:
                data = DirtyData()
                def __getattr__(self, key):
                    return getattr(bpy, key)
            with patch.dict(ns, bpy=DirtyBpy()):
                with self.assertRaises(RuntimeError):
                    ns['open_project'](other, allow_switch=True)

    def test_scripted_headless_changes_require_explicit_switch(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as other:
            bpy.ops.wm.save_as_mainfile(filepath=str(pathlib.Path(first) / 'first.blend'))
            part = cube('unsaved_model')
            part.location.x = 123
            # is_dirty may be False here. Existing data alone must protect it.
            with self.assertRaises(RuntimeError):
                ns['open_project'](other)
            self.assertEqual(part.location.x, 123)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        cube('never_saved')
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaises(RuntimeError):
                ns['open_project'](other)

    def test_world_transform_and_containment(self):
        outer = cube('outer', (100, 40, 9), (4, 3, 2))
        outer.rotation_euler.z = .4
        inner = cube('inner', (100, 40, 9), (.2, .2, .2))
        bpy.context.view_layer.update()
        result = ns['check_fit'](outer, inner)
        self.assertFalse(result['pass'])
        self.assertEqual(result['status'], 'penetration')

    def test_intended_contact_and_small_penetration(self):
        a = cube('a')
        b = cube('b', (2, 0, 0))
        self.assertTrue(ns['check_fit'](a, b, tolerance=.001)['pass'])
        self.assertFalse(ns['check_fit'](a, b, allow_contact=False)['pass'])
        b.location.x = 1.99
        bpy.context.view_layer.update()
        self.assertFalse(ns['check_fit'](a, b, tolerance=.001)['pass'])

    def test_coincident_solids_are_not_contact_only(self):
        a, b = cube('a'), cube('b')
        self.assertEqual(ns['check_fit'](a, b)['status'], 'penetration')

    def test_keepout_contains_whole_part(self):
        part = cube('part')
        cube('KeepOut_whole', scale=(10, 10, 10))
        report = ns['audit'](part)
        self.assertTrue(report['pass'])  # Deliberately scoped legacy result.
        self.assertEqual(report['pass_scope'], 'mesh_integrity_only')
        self.assertEqual(report['checks']['keepouts'], 'fail')
        self.assertEqual(report['checks']['mechanical'], 'not_checked')

    def test_open_keepout_is_unknown_not_clear(self):
        part = cube('part', scale=(3, 3, 3))
        mesh = bpy.data.meshes.new('open')
        mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)], [], [(0,1,2,3)])
        ob = bpy.data.objects.new('KeepOut_open', mesh)
        bpy.context.scene.collection.objects.link(ob)
        bpy.context.view_layer.update()
        self.assertEqual(ns['audit'](part)['checks']['keepouts'], 'unknown')

    def test_dense_final_insertion_and_seated_check(self):
        part = cube('floor', (0, 0, -1))
        moving = cube('moving', (0, 0, .8))
        result = ns['check_insertion'](part, moving, (0, 0, 20), max_step_mm=2, final_step_mm=.05)
        self.assertFalse(result['pass'])
        self.assertIn(0., result['blocked_offsets_mm'])
        self.assertTrue(any(0 < d < .2 for d in result['blocked_offsets_mm']))
        moving.location.z = 1
        bpy.context.view_layer.update()
        self.assertTrue(ns['check_insertion'](part, moving, (0, 0, 5))['pass'])
        self.assertTrue(ns['check_insertion'](part, moving, (0, 0, 0), max_positions=1)['pass'])
        with self.assertRaises(ValueError):
            ns['check_insertion'](part, moving, (0, 0, 10000), max_positions=10)

    def test_evaluated_fingerprint_and_provenance(self):
        part = cube('part')
        first = ns['mesh_fingerprint'](part)
        part.location.x = 10
        bpy.context.view_layer.update()
        self.assertNotEqual(first, ns['mesh_fingerprint'](part))
        mod = part.modifiers.new('bevel', 'BEVEL')
        mod.width = .1
        bpy.context.view_layer.update()
        self.assertNotEqual(first, ns['mesh_fingerprint'](part))
        rec = ns['record_measurement']('fit_width', 2, part, method='mesh section', uncertainty=.1)
        self.assertEqual(rec['geometry_fingerprint'], ns['mesh_fingerprint'](part))
        self.assertEqual(rec['uncertainty'], .1)

    def test_keepout_cylinder_axes_use_declared_centres(self):
        for axis, expected in [('X',(7,13,18,22,28,32)), ('Y',(8,12,17,23,28,32)), ('Z',(8,12,18,22,27,33))]:
            ob = ns['make_keepout_cylinder']('test_'+axis, (10,20,30), 2, 6, axis=axis)
            bpy.context.view_layer.update()
            self.assertEqual(ns['world_bbox'](ob), expected)

    def test_neutral_export_has_no_print_settings(self):
        part = cube('portable', (3, 4, -8), (1, 2, 3))
        fingerprint = ns['mesh_fingerprint'](part)
        with tempfile.TemporaryDirectory() as folder:
            dest = pathlib.Path(folder) / 'part.geometry.3mf'
            result = ns['export_geometry_3mf'](part, str(dest))
            self.assertEqual(result['kind'], 'geometry_only')
            with zipfile.ZipFile(dest) as archive:
                self.assertEqual(len(archive.namelist()), 3)
                self.assertNotIn('Metadata/Slic3r_PE.config', archive.namelist())
                import xml.etree.ElementTree as ET
                root = ET.fromstring(archive.read('3D/3dmodel.model'))
                vertices = root.findall('.//{*}vertex')
                self.assertEqual(min(float(v.get('z')) for v in vertices), 0)
            self.assertEqual(fingerprint, ns['mesh_fingerprint'](part))
            with zipfile.ZipFile(dest, 'a') as archive:
                archive.writestr('Metadata/Slic3r_PE.config', '; perimeters = 6')
            with self.assertRaises(ValueError):
                ns['export_geometry_3mf'](part, str(dest))

    def test_invalid_beam_inputs_fail(self):
        part = cube('part')
        for kwargs in [{'axis':'Z'}, {'e_mpa':0}, {'e_mpa':math.inf}, {'load_n':math.nan},
                       {'slices':0}, {'slices':2.5}, {'slices':True}, {'load_n':-1},
                       {'root_pos':math.inf}, {'tip_pos':math.nan}, {'root_pos':1,'tip_pos':1}]:
            with self.assertRaises(ValueError):
                ns['audit_cantilever'](part, **kwargs)

    def test_uniform_rectangular_beam_matches_analytical_solution(self):
        part = cube('beam', location=(5,0,0), scale=(5,1,1))
        report = ns['audit_cantilever'](part, root_pos=0, tip_pos=10,
                                      load_n=1, e_mpa=1000, slices=200)
        # I=b*h^3/12=4/3; delta=F*L^3/(8*E*I)=0.09375 mm.
        self.assertAlmostEqual(report['min_I_mm4'], 4/3, delta=.05)
        self.assertAlmostEqual(report['min_Zs_mm3'], 4/3, delta=.05)
        self.assertAlmostEqual(report['est_tip_sag_mm'], .09375, delta=.005)
        self.assertEqual(report['scope'], 'approximate_ideal_solid_beam')

    def test_beam_minimum_inertia_is_independent_of_minimum_modulus(self):
        part = cube('low_I', location=(2.505,0,0), scale=(2.505,1,1))
        tail = cube('low_Zs', location=(7.495,0,0), scale=(2.505,.2,2))
        union = part.modifiers.new('connected_sections', 'BOOLEAN')
        union.operation = 'UNION'
        union.solver = 'EXACT'
        union.object = tail
        bpy.context.view_layer.update()
        report = ns['audit_cantilever'](part, root_pos=0, tip_pos=10,
                                      load_n=1, e_mpa=1000, slices=40)
        self.assertAlmostEqual(report['min_I_mm4'], 4/3, delta=.05)
        self.assertAlmostEqual(report['min_Zs_mm3'], 1.0666667, delta=.05)
        self.assertLess(report['min_I_pos_mm'], 5)
        self.assertGreater(report['weak_pos_mm'], 5)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BlenderWorkflowRegression))
    if not result.wasSuccessful():
        raise SystemExit(1)
