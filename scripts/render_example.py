"""Render a reproducible source/result comparison for the README."""

from __future__ import annotations

from pathlib import Path
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "images" / "object-joiner-example.png"


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.5):
    result = bpy.data.materials.new(name)
    result.diffuse_color = color
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    return result


def label(text: str, location: tuple[float, float, float]) -> None:
    bpy.ops.object.text_add(location=location, rotation=(1.5708, 0, 0))
    obj = bpy.context.active_object
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.size = 0.46
    obj.data.extrude = 0.012
    obj.data.materials.append(material(f"{text} Label", (0.75, 0.82, 0.92, 1.0), 0.6))


def main() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sys.path.insert(0, str(ROOT))
    import objectjoiner as addon

    addon.register()
    blue = material("Source Blue", (0.07, 0.38, 0.92, 1.0), 0.38)
    orange = material("Source Orange", (1.0, 0.28, 0.07, 1.0), 0.42)
    joined = material("Joined", (0.12, 0.78, 0.65, 1.0), 0.35)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(-0.75, 0, 0.1), scale=(1.5, 1.25, 1.25))
    first = bpy.context.active_object
    first.name = "Source Sphere"
    first.data.materials.append(blue)
    bpy.ops.mesh.primitive_cube_add(location=(0.65, 0, 0), scale=(1.2, 1.05, 1.05))
    second = bpy.context.active_object
    second.name = "Source Cube"
    second.data.materials.append(orange)
    bevel = second.modifiers.new("Rounded Corners", "BEVEL")
    bevel.width = 0.28
    bevel.segments = 5
    bpy.context.view_layer.objects.active = second
    bpy.ops.object.modifier_apply(modifier=bevel.name)

    first.select_set(True)
    second.select_set(True)
    bpy.context.view_layer.objects.active = first
    props = bpy.context.scene.object_joiner_props
    props.voxel_size = 0.10
    props.target_detail = 0.45
    props.hide_originals = True
    result = bpy.ops.object.join_objects_custom()
    if "FINISHED" not in result:
        raise RuntimeError(f"Object joining failed: {result}")
    output = bpy.context.active_object
    output.data.materials.clear()
    output.data.materials.append(joined)

    first.hide_viewport = False
    first.hide_render = False
    second.hide_viewport = False
    second.hide_render = False
    first.location.x -= 4.1
    second.location.x -= 4.1
    output.location.x += 4.1

    label("SOURCE OBJECTS", (-4.1, 0.25, 2.15))
    label("JOINED RESULT", (4.1, 0.25, 2.15))

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -1.35))
    ground = bpy.context.active_object
    ground.data.materials.append(material("Ground", (0.025, 0.04, 0.07, 1.0), 0.68))

    bpy.ops.object.light_add(type="AREA", location=(-4, -7, 8))
    key = bpy.context.active_object
    key.data.energy = 1_250
    key.data.size = 6
    look_at(key, (0, 0, 0))
    bpy.ops.object.light_add(type="AREA", location=(6, 1, 5))
    fill = bpy.context.active_object
    fill.data.energy = 900
    fill.data.color = (0.34, 0.58, 1.0)
    fill.data.size = 5
    look_at(fill, (0, 0, 0))

    bpy.ops.object.camera_add(location=(0, -17.5, 6.0))
    camera = bpy.context.active_object
    camera.data.lens = 52
    look_at(camera, (0, 0, -0.2))
    bpy.context.scene.camera = camera

    world = bpy.data.worlds.new("Example World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.015, 0.035, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    bpy.context.scene.world = world

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(OUTPUT)
    scene.view_settings.look = "AgX - Medium High Contrast"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {OUTPUT}")


if __name__ == "__main__":
    main()
