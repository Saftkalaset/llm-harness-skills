import importlib.util
import math
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from validate_gcode import validate_gcode, arc_points
from verify_3mf import inspect_3mf, package_project, load_config, config_from_gcode, config_mismatches

PREFIX = 'G90\nM83\nG0 X5 Y5 Z0.2\n;TYPE:Perimeter\n'


def fixture_3mf(path, unit='millimeter', transform='', faces=None, components=None, config=None):
    faces = faces if faces is not None else [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
    mesh = '<object id="1" type="model"><mesh><vertices>' + ''.join(
        f'<vertex x="{x}" y="{y}" z="{z}"/>' for x,y,z in [(0,0,0),(1,0,0),(0,1,0),(0,0,1)])
    mesh += '</vertices><triangles>'+''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in faces)+'</triangles></mesh></object>'
    extra = '' if components is None else '<object id="2" type="model"><components>'+components+'</components></object>'
    ident = '1' if components is None else '2'
    model = f'<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="{unit}"><resources>{mesh}{extra}</resources><build><item objectid="{ident}" transform="{transform}"/></build></model>'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Id="r1"/></Relationships>')
        z.writestr('3D/3dmodel.model',model)
        if config is not None:z.writestr('Metadata/Slic3r_PE.config',config)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def check_gcode(self, text, **kwargs):
        path=self.root/'part.gcode';path.write_text(text)
        return validate_gcode(path, bed=(20,20,20), **kwargs)

    def test_straight_modes_and_retraction(self):
        r=self.check_gcode(PREFIX+'G1 X6 E1\nG1 E-1\nG1 E1\nG91\nG1 X2 E.5\n')
        self.assertTrue(r['pass']);self.assertEqual(r['deposition_commands'],{'G1':2})
        self.assertEqual(r['bounds_mm']['Perimeter'][0],[5,8])

    def test_tool_parameter_is_not_another_command(self):
        r=self.check_gcode('M204 P7000 R2500 T7000\nM104 T0 S170\n'+PREFIX+'G1 X6 E1\n')
        self.assertTrue(r['pass'],r['issues'])

    def test_absolute_e_reset(self):
        r=self.check_gcode('G90\nM82\nG0 X5 Y5 Z.2\nG92 E0\nG1 X6 E1\nG92 E0\nG1 X7 E1\nG1 X8 E.5\n')
        self.assertTrue(r['pass']);self.assertEqual(r['deposition_commands']['G1'],2)

    def test_xyz_reset_preserves_machine_coordinates(self):
        r=self.check_gcode(PREFIX+'G92 X0\nG1 X2 E1\n')
        self.assertTrue(r['pass']);self.assertEqual(r['bounds_mm']['Perimeter'][0],[5,7])

    def test_inch_units(self):
        r=self.check_gcode('G20\nG90\nM83\nG0 X.1 Y.1 Z.01\nG1 X.2 E.1\n')
        self.assertTrue(r['pass']);self.assertAlmostEqual(r['bounds_mm']['unclassified'][0][1],5.08)

    def test_arc_extremum_outside_even_when_endpoints_inside(self):
        text='G90\nM83\nG0 X1 Y2 Z.2\n;TYPE:Perimeter\nG2 X1 Y8 I0 J3 E1\n'
        r=self.check_gcode(text)
        self.assertFalse(r['pass']);self.assertAlmostEqual(r['bounds_mm']['Perimeter'][0][0],-2)

    def test_full_circle_with_only_e_and_center(self):
        r=self.check_gcode(PREFIX+'G2 I2 J0 E1\n')
        self.assertTrue(r['pass']);self.assertEqual(r['bounds_mm']['Perimeter'][0],[5,9])
        self.assertEqual(r['bounds_mm']['Perimeter'][1],[3,7])

    def test_radius_and_absolute_center_arcs(self):
        minor=arc_points([1,0,0],[0,1,1],{'R':1},False)
        major=arc_points([1,0,0],[0,1,1],{'R':-1},False)
        self.assertLessEqual(len(minor),len(major));self.assertTrue(any(p[0]>1.5 for p in major))
        r=self.check_gcode(PREFIX+'G90.1\nG3 X7 Y7 I5 J7 E1\n')
        self.assertTrue(r['pass'])

    def test_unsupported_not_silently_passed(self):
        for suffix in ['G18\nG2 X7 Z1 I1 K0 E1\n','G5 X7 E1\n','G1 Xnan Y7 E1\n','G1 X1 X2 E1\n',
                       'G1 X6 A999 E1\n','G3 X7 Y7 I0 J2 P2 E1\n']:
            with self.subTest(suffix=suffix):
                r=self.check_gcode(PREFIX+suffix);self.assertEqual(r['status'],'unsupported')

    def test_missing_modes_and_empty_file(self):
        self.assertEqual(self.check_gcode('G1 X1 Y1 Z1 E1')['status'],'unsupported')
        self.assertEqual(self.check_gcode('')['status'],'unsupported')

    def test_margin_and_bead_width(self):
        self.assertFalse(self.check_gcode(PREFIX+'G1 X19.9 E1\n',bead_radius=.2)['pass'])
        self.assertFalse(self.check_gcode(PREFIX+'G1 X19.5 E1\n',margin=1)['pass'])

    def test_purge_exception_is_explicit_and_startup_only(self):
        box=[0,20,-3,0,0,1]
        text='G90\nM83\nG0 X5 Y-2 Z.2\n;TYPE:Custom\nG1 X6 E1\nG0 X5 Y5\n;LAYER_CHANGE\n;TYPE:Perimeter\nG1 X6 E1\n'
        self.assertFalse(self.check_gcode(text)['pass'])
        self.assertTrue(self.check_gcode(text,startup_exceptions=[box])['pass'])
        late=text+';TYPE:Custom\nG0 X5 Y-2\nG1 X6 E1\n'
        self.assertFalse(self.check_gcode(late,startup_exceptions=[box])['pass'])

    def test_3mf_units_transforms_and_components(self):
        path=self.root/'part.3mf'
        fixture_3mf(path,unit='inch',transform='1 0 0 0 1 0 0 0 1 2 0 0')
        r=inspect_3mf(path);self.assertTrue(r['pass']);self.assertAlmostEqual(r['bounds_mm'][0][0],50.8);self.assertAlmostEqual(r['bounds_mm'][0][1],76.2)
        fixture_3mf(path,components='<component objectid="1" transform="1 0 0 0 1 0 0 0 1 3 0 0"/>')
        self.assertEqual(inspect_3mf(path)['bounds_mm'][0],[3,4])

    def test_missing_units_graph_and_bad_mesh_fail(self):
        path=self.root/'part.3mf'
        for kwargs in [{'unit':'furlong'},{'components':'<component objectid="2"/>'},
                       {'components':'<component objectid="99"/>'}, {'faces':[(0,2,1)]},
                       {'faces':[(0,2,1),(0,1,3),(0,3,2),(1,2,99)]}]:
            with self.subTest(kwargs=kwargs):
                fixture_3mf(path,**kwargs);self.assertFalse(inspect_3mf(path)['pass'])

    def test_geometry_is_not_configured_project(self):
        path=self.root/'part.3mf';fixture_3mf(path)
        self.assertTrue(inspect_3mf(path)['pass'])
        self.assertFalse(inspect_3mf(path,require_config=True)['pass'])

    def test_duplicate_object_ids_and_singular_transforms(self):
        path=self.root/'duplicate.3mf';fixture_3mf(path)
        with zipfile.ZipFile(path) as z:members={n:z.read(n) for n in z.namelist()}
        text=members['3D/3dmodel.model'].decode().replace('</resources>','<object id="1" type="model"/></resources>')
        members['3D/3dmodel.model']=text.encode()
        with zipfile.ZipFile(path,'w') as z:
            for n,b in members.items():z.writestr(n,b)
        self.assertFalse(inspect_3mf(path)['pass'])

    def test_unknown_required_extension_rejected(self):
        path=self.root/'extension.3mf';fixture_3mf(path)
        with zipfile.ZipFile(path) as z:members={n:z.read(n) for n in z.namelist()}
        members['3D/3dmodel.model']=members['3D/3dmodel.model'].replace(b'<model ',b'<model xmlns:unknown="urn:unknown" requiredextensions="unknown" ')
        with zipfile.ZipFile(path,'w') as z:
            for n,b in members.items():z.writestr(n,b)
        self.assertFalse(inspect_3mf(path)['pass'])
        fixture_3mf(path,transform='0 0 0 0 0 0 0 0 0 0 0 0')
        self.assertFalse(inspect_3mf(path)['pass'])

    def test_package_and_reload_configuration(self):
        src=self.root/'geometry.3mf';fixture_3mf(src)
        cfg=self.root/'settings.ini';cfg.write_text('perimeters = 6\nnozzle_diameter = .4\nprinthost_apikey = secret\n')
        out=self.root/'project.3mf';before=src.read_bytes()
        self.assertTrue(package_project(src,cfg,out)['pass'])
        r=inspect_3mf(out,True,{'perimeters':6,'nozzle_diameter':'.40'})
        self.assertTrue(r['pass']);self.assertNotIn('printhost_apikey',r['config'])
        self.assertEqual(src.read_bytes(),before)
        with self.assertRaises(ValueError):package_project(src,cfg,out)

    def test_gcode_configuration_and_incomplete_block(self):
        path=self.root/'slice.gcode'
        path.write_text('; prusaslicer_config = begin\n; perimeters = 6\n; start_gcode = G90\\nM83\n; prusaslicer_config = end\n')
        self.assertEqual(config_from_gcode(path)['start_gcode'],'G90\\nM83')
        path.write_text('; prusaslicer_config = begin\n; perimeters = 6\n')
        with self.assertRaises(ValueError):config_from_gcode(path)

    def test_ini_comments_and_unresolved_presets(self):
        path=self.root/'settings.ini';path.write_text('; perimeters = 2\nperimeters = 6\n')
        self.assertEqual(load_config(path)['perimeters'],'6')
        path.write_text('inherits = old preset\nperimeters = 6\n')
        with self.assertRaises(ValueError):load_config(path)
        self.assertFalse(config_mismatches({'nozzle_diameter':'0.4'},{'nozzle_diameter':'.4'}))


if __name__=='__main__':unittest.main()
