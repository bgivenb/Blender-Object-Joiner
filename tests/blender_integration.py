"""Real Blender checks for evaluated geometry, originals, and rollback."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import objectjoiner as addon


class BlenderIntegrationTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.mesh.primitive_cube_add(location=(1, 0, 0))
        self.first = bpy.context.active_object
        self.first.scale = (2, 1, 1)
        bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))
        self.second = bpy.context.active_object
        modifier = self.second.modifiers.new("Subdivision", "SUBSURF")
        modifier.levels = 1
        self.first.select_set(True)
        bpy.context.view_layer.objects.active = self.first
        self.props = bpy.context.scene.object_joiner_props
        self.props.voxel_size = 0.3
        self.props.target_detail = 0.6
        bpy.context.view_layer.update()

    def test_join_only_bakes_all_modifiers_and_world_transforms(self):
        self.props.mode = "JOIN"
        material = bpy.data.materials.new("Source material")
        self.second.data.materials.append(material)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        expected = []
        count = 0
        for source in (self.first, self.second):
            evaluated = source.evaluated_get(depsgraph)
            count += len(evaluated.data.polygons)
            expected.extend(
                tuple(round(v, 5) for v in evaluated.matrix_world @ vert.co)
                for vert in evaluated.data.vertices
            )
        self.assertEqual(bpy.ops.object.join_objects_custom(), {"FINISHED"})
        result = bpy.context.active_object
        actual = [
            tuple(round(v, 5) for v in result.matrix_world @ vert.co)
            for vert in result.data.vertices
        ]
        self.assertEqual(sorted(expected), sorted(actual))
        self.assertEqual(len(result.data.polygons), count)
        self.assertEqual(result["source_polygon_count"], count)
        self.assertEqual(len(self.first.data.polygons), 6)
        self.assertEqual(len(self.second.modifiers), 1)
        self.assertEqual(tuple(self.first.scale), (2, 1, 1))
        self.assertIn(material, list(result.data.materials))
        self.assertGreater(len(result.data.uv_layers), 0)
        self.assertEqual(len(result.modifiers), 0)
        self.assertEqual(tuple(result.scale), (1, 1, 1))

    def test_restore_preserves_original_render_visibility(self):
        self.props.mode = "JOIN"
        self.second.hide_render = True
        bpy.ops.object.join_objects_custom()
        self.assertTrue(self.first.hide_get())
        self.assertTrue(self.first.hide_render)
        bpy.ops.object.unhide_object_joiner_originals()
        self.assertFalse(self.first.hide_get())
        self.assertFalse(self.first.hide_render)
        self.assertTrue(self.second.hide_render)
        self.assertNotIn("object_joiner_hidden_original", self.first)

    def test_remesh_has_unit_scale_and_cleans_reference_mesh(self):
        meshes_before = len(bpy.data.meshes)
        self.assertEqual(bpy.ops.object.join_objects_custom(), {"FINISHED"})
        result = bpy.context.active_object
        self.assertGreater(len(result.data.polygons), 0)
        self.assertEqual(tuple(result.scale), (1, 1, 1))
        self.assertEqual(len(bpy.data.meshes), meshes_before + 1)
        self.assertFalse(
            any(
                obj.name.startswith("object_joiner_reference_shell")
                for obj in bpy.data.objects
            )
        )

    def test_failure_cleans_data_and_restores_selection(self):
        counts = (
            len(bpy.data.objects),
            len(bpy.data.meshes),
            len(bpy.data.collections),
        )
        with patch.object(
            addon,
            "_apply_modifier",
            side_effect=RuntimeError("injected modifier failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "injected modifier failure"):
                bpy.ops.object.join_objects_custom()
        self.assertEqual(
            counts,
            (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.collections)),
        )
        self.assertEqual(set(bpy.context.selected_objects), {self.first, self.second})
        self.assertEqual(bpy.context.active_object, self.first)
        self.assertFalse(self.first.hide_render)


addon.register()
try:
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(BlenderIntegrationTests)
    )
finally:
    addon.unregister()
if not result.wasSuccessful():
    raise RuntimeError("Blender integration tests failed")
