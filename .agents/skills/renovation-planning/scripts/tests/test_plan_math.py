import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("plan_math", Path(__file__).parents[1] / "plan_math.py")
pm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pm)


class PlanMathTests(unittest.TestCase):
    def model(self):
        return {
            "source": {"pixels_per_metre": 100, "scale_status": "dimension-derived", "reference_area_m2": 59},
            "zones": [{"id": "room", "polygon": [[0, 0], [500, 0], [500, 400], [0, 400]]}],
            "fixed_geometry": {"W2": [[400, 0], [400, 200]]},
            "variants": [{"id": "v", "geometry": {"W2": [[400, 0], [400, 200]]},
                          "rectangles": {"run": {"x": 100, "y": 100, "width": 300, "height": 60},
                                         "island": {"x": 215, "y": 245, "width": 185, "height": 80}},
                          "clearances": [{"id": "aisle", "a": "run", "b": "island", "axis": "y",
                                          "minimum_m": .85, "uncertainty_m": .02, "constraint_source": "user"}],
                          "boundaries": [{"id": "W3", "rect": "island", "axis": "y", "edge": "max",
                                          "limit": 300, "relation": "<=", "constraint_source": "user"}]}]
        }

    def test_known_length_and_scan_scale_agree(self):
        known = pm.calibration(pixel_span=1000, length_m=5)
        scan = pm.calibration(dpi=254, denominator=50)
        self.assertEqual(known["pixels_per_metre"], 200)
        self.assertEqual(scan["pixels_per_metre"], 200)

    def test_l_shape_area_is_not_bounding_rectangle(self):
        polygon = [[0, 0], [400, 0], [400, 200], [200, 200], [200, 400], [0, 400]]
        self.assertEqual(pm.polygon_area(polygon), 120000)
        self.assertEqual(pm.polygon_area(list(reversed(polygon))), 120000)

    def test_reference_area_does_not_force_normalization(self):
        report = pm.audit(self.model())
        self.assertEqual(report["zone_sum_m2"], 20)
        self.assertEqual(report["reference_area_m2"], 59)
        self.assertEqual(report["area_difference_m2"], -39)
        self.assertEqual(report["pixels_per_metre"], 100)

    def test_nominal_minimum_does_not_pass_with_uncertainty(self):
        check = pm.audit(self.model())["variants"][0]["clearances"][0]
        self.assertAlmostEqual(check["gap_m"], .85)
        self.assertTrue(check["nominal_pass"])
        self.assertFalse(check["lower_bound_pass"])

    def test_offset_objects_do_not_create_a_working_aisle(self):
        model = self.model()
        model["variants"][0]["rectangles"]["island"]["x"] = 450
        check = pm.audit(model)["variants"][0]["clearances"][0]
        self.assertEqual(check["status"], "not_opposed")
        self.assertIsNone(check["nominal_pass"])

    def test_drift_and_boundary_crossing_remain_visible(self):
        model = self.model()
        model["variants"][0]["geometry"]["W2"] = [[405, 0], [405, 200]]
        report = pm.audit(model)["variants"][0]
        self.assertEqual(report["fixed_geometry"][0]["status"], "changed")
        self.assertAlmostEqual(report["boundaries"][0]["crossing_m"], .25)

    def test_negative_gap_indicates_overlapping_envelopes(self):
        model = self.model()
        model["variants"][0]["rectangles"]["island"]["y"] = 140
        check = pm.audit(model)["variants"][0]["clearances"][0]
        self.assertAlmostEqual(check["gap_m"], -.2)
        self.assertFalse(check["nominal_pass"])

    def test_invalid_dimensions_and_mixed_calibrations_rejected(self):
        with self.assertRaises(ValueError):
            pm.calibration(pixel_span=100, length_m=1, dpi=300)
        for bad in [0, -1, float("nan"), float("inf"), True]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                pm.bounds({"x": 0, "y": 0, "width": bad, "height": 60})


if __name__ == "__main__":
    unittest.main()
