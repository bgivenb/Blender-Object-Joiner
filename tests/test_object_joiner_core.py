import unittest

from object_joiner_core import summarize_meshes, validate_settings


class ObjectJoinerCoreTests(unittest.TestCase):
    def test_valid_settings(self):
        validate_settings(2, 0.05, 0.35)

    def test_at_least_two_meshes_are_required(self):
        with self.assertRaises(ValueError):
            validate_settings(1, 0.05, 0.35)

    def test_numeric_bounds_are_enforced(self):
        for voxel_size, ratio in ((0, 0.5), (1.1, 0.5), (0.1, 0), (0.1, 1.1)):
            with self.assertRaises(ValueError):
                validate_settings(2, voxel_size, ratio)

    def test_summary_reports_polygon_change(self):
        summary = summarize_meshes([100, 300, 100], 200)
        self.assertEqual(summary.source_objects, 3)
        self.assertEqual(summary.source_polygons, 500)
        self.assertEqual(summary.result_polygons, 200)
        self.assertEqual(summary.change_percent, -60)

    def test_empty_source_does_not_divide_by_zero(self):
        self.assertEqual(summarize_meshes([], 0).change_percent, 0)


if __name__ == "__main__":
    unittest.main()
