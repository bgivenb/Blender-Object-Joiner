bl_info = {
    "name": "Object Joiner",
    "author": "Given Borthwick",
    "version": (2, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Object Joiner",
    "description": "Non-destructively join, remesh, and reduce selected meshes",
    "category": "Object",
}

import bpy
from bpy.props import BoolProperty, FloatProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup

from object_joiner_core import summarize_meshes, validate_settings


class ObjectJoinerProperties(PropertyGroup):
    voxel_size: FloatProperty(
        name="Voxel size (m)",
        description="Smaller values preserve more detail but cost more memory and time",
        default=0.05,
        min=0.0001,
        max=1.0,
    )
    target_detail: FloatProperty(
        name="Decimate ratio",
        description="Approximate fraction of remeshed polygons to retain",
        default=0.35,
        min=0.01,
        max=1.0,
    )
    hide_originals: BoolProperty(name="Hide original objects", default=True)


def _activate(context, obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    context.view_layer.objects.active = obj


def _apply_modifier(context, obj, modifier):
    _activate(context, obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


class OBJECT_OT_JoinObjects(Operator):
    bl_idname = "object.join_objects_custom"
    bl_label = "Build Joined Mesh"
    bl_description = "Duplicate selected meshes, join and remesh the copies, then reduce the result"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.object_joiner_props
        source_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        try:
            validate_settings(len(source_meshes), props.voxel_size, props.target_detail)
            result, summary = self._build(context, source_meshes, props)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Created {result.name}: {summary.source_polygons:,} → "
            f"{summary.result_polygons:,} polygons ({summary.change_percent:+.1f}% change)",
        )
        return {"FINISHED"}

    def _build(self, context, source_meshes, props):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")

        source_counts = [len(obj.data.polygons) for obj in source_meshes]
        original_visibility = [(obj, obj.hide_viewport, obj.hide_render) for obj in source_meshes]
        collection = bpy.data.collections.new("ObjectJoiner Result")
        context.scene.collection.children.link(collection)
        copies = []

        try:
            for source in source_meshes:
                duplicate = source.copy()
                duplicate.data = source.data.copy()
                collection.objects.link(duplicate)
                copies.append(duplicate)

            bpy.ops.object.select_all(action="DESELECT")
            for duplicate in copies:
                duplicate.select_set(True)
            context.view_layer.objects.active = copies[0]
            bpy.ops.object.join()
            result = context.active_object
            result.name = "object_joiner_result"
            result["object_joiner_result"] = True

            shell = result.copy()
            shell.data = result.data.copy()
            shell.name = "object_joiner_reference_shell"
            collection.objects.link(shell)

            remesh = result.modifiers.new("Voxel Remesh", "REMESH")
            remesh.mode = "VOXEL"
            remesh.voxel_size = props.voxel_size
            _apply_modifier(context, result, remesh)

            shrinkwrap = result.modifiers.new("Restore Surface", "SHRINKWRAP")
            shrinkwrap.wrap_method = "NEAREST_SURFACEPOINT"
            shrinkwrap.wrap_mode = "ON_SURFACE"
            shrinkwrap.target = shell
            _apply_modifier(context, result, shrinkwrap)

            if props.target_detail < 1:
                decimate = result.modifiers.new("Reduce Geometry", "DECIMATE")
                decimate.ratio = props.target_detail
                _apply_modifier(context, result, decimate)

            final_shrinkwrap = result.modifiers.new("Restore Final Surface", "SHRINKWRAP")
            final_shrinkwrap.wrap_method = "NEAREST_SURFACEPOINT"
            final_shrinkwrap.wrap_mode = "ON_SURFACE"
            final_shrinkwrap.target = shell
            _apply_modifier(context, result, final_shrinkwrap)

            bpy.data.objects.remove(shell, do_unlink=True)
            for polygon in result.data.polygons:
                polygon.use_smooth = True

            if props.hide_originals:
                for source in source_meshes:
                    source["object_joiner_hidden_original"] = True
                    source.hide_viewport = True
                    source.hide_render = True

            summary = summarize_meshes(source_counts, len(result.data.polygons))
            result["source_object_count"] = summary.source_objects
            result["source_polygon_count"] = summary.source_polygons
            result["result_polygon_count"] = summary.result_polygons
            _activate(context, result)
            return result, summary
        except Exception:
            for source, viewport, render in original_visibility:
                source.hide_viewport = viewport
                source.hide_render = render
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
            raise


class OBJECT_OT_UnhideOriginals(Operator):
    bl_idname = "object.unhide_object_joiner_originals"
    bl_label = "Unhide Originals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        originals = [obj for obj in bpy.data.objects if obj.get("object_joiner_hidden_original")]
        for obj in originals:
            obj.hide_viewport = False
            obj.hide_render = False
            del obj["object_joiner_hidden_original"]
        self.report({"INFO"}, f"Unhid {len(originals)} original object(s)")
        return {"FINISHED"}


class OBJECTJOINER_PT_MainPanel(Panel):
    bl_label = "Object Joiner"
    bl_idname = "OBJECTJOINER_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Object Joiner"

    def draw(self, context):
        layout = self.layout
        props = context.scene.object_joiner_props
        layout.prop(props, "voxel_size")
        layout.prop(props, "target_detail")
        layout.prop(props, "hide_originals")
        layout.operator("object.join_objects_custom", icon="AUTOMERGE_ON")
        layout.operator("object.unhide_object_joiner_originals", icon="HIDE_OFF")


CLASSES = (
    ObjectJoinerProperties,
    OBJECT_OT_JoinObjects,
    OBJECT_OT_UnhideOriginals,
    OBJECTJOINER_PT_MainPanel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.object_joiner_props = PointerProperty(type=ObjectJoinerProperties)


def unregister():
    del bpy.types.Scene.object_joiner_props
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
