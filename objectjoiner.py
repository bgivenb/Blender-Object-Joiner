bl_info = {
    "name": "Object Joiner",
    "author": "Given Borthwick",
    "version": (2, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Object Joiner",
    "description": "Non-destructively join, remesh, and reduce selected meshes",
    "category": "Object",
}

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup

try:
    from .object_joiner_core import summarize_meshes, validate_settings
except ImportError:  # Support direct execution from a source checkout.
    from object_joiner_core import summarize_meshes, validate_settings


class ObjectJoinerProperties(PropertyGroup):
    mode: EnumProperty(
        name="Mode",
        default="REMESH",
        items=(
            (
                "REMESH",
                "Sculpting remesh",
                "Fuse and reduce geometry; rebuilds topology",
            ),
            (
                "JOIN",
                "Join only",
                "Combine evaluated meshes without remeshing; keep UVs and materials",
            ),
        ),
    )
    voxel_size: FloatProperty(
        name="Voxel size",
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
    bl_description = (
        "Duplicate selected meshes, join and remesh the copies, then reduce the result"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.object_joiner_props
        source_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        try:
            validate_settings(
                len(source_meshes), props.voxel_size, props.target_detail, props.mode
            )
            if context.mode != "OBJECT":
                raise ValueError("Switch to Object Mode before joining meshes.")
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
        original_selection = list(context.selected_objects)
        original_active = context.view_layer.objects.active
        original_visibility = [
            (
                obj,
                obj.hide_viewport,
                obj.hide_render,
                obj.hide_get(),
                obj.get("object_joiner_hidden_original"),
            )
            for obj in source_meshes
        ]
        source_counts = []
        collection = bpy.data.collections.new("ObjectJoiner Result")
        context.scene.collection.children.link(collection)
        copies = []
        created_meshes = []

        try:
            for source in source_meshes:
                depsgraph = context.evaluated_depsgraph_get()
                evaluated = source.evaluated_get(depsgraph)
                mesh = bpy.data.meshes.new_from_object(
                    evaluated, preserve_all_data_layers=True, depsgraph=depsgraph
                )
                created_meshes.append(mesh)
                source_counts.append(len(mesh.polygons))
                mesh.transform(evaluated.matrix_world)
                if evaluated.matrix_world.determinant() < 0:
                    mesh.flip_normals()
                mesh.update()
                duplicate = bpy.data.objects.new(f"{source.name}_joined_copy", mesh)
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

            if props.mode == "REMESH":
                shell = result.copy()
                shell.data = result.data.copy()
                created_meshes.append(shell.data)
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

                final_shrinkwrap = result.modifiers.new(
                    "Restore Final Surface", "SHRINKWRAP"
                )
                final_shrinkwrap.wrap_method = "NEAREST_SURFACEPOINT"
                final_shrinkwrap.wrap_mode = "ON_SURFACE"
                final_shrinkwrap.target = shell
                _apply_modifier(context, result, final_shrinkwrap)
                bpy.data.objects.remove(shell, do_unlink=True)
                for polygon in result.data.polygons:
                    polygon.use_smooth = True

            if props.hide_originals:
                for source in source_meshes:
                    if "object_joiner_hidden_original" not in source:
                        source["object_joiner_hidden_original"] = [
                            int(source.hide_viewport),
                            int(source.hide_render),
                            int(source.hide_get()),
                        ]
                    source.hide_set(True)
                    source.hide_render = True

            summary = summarize_meshes(source_counts, len(result.data.polygons))
            result["source_object_count"] = summary.source_objects
            result["source_polygon_count"] = summary.source_polygons
            result["result_polygon_count"] = summary.result_polygons
            result["joiner_mode"] = props.mode
            _activate(context, result)
            return result, summary
        except Exception:
            for source, viewport, render, hidden, marker in original_visibility:
                source.hide_viewport = viewport
                source.hide_render = render
                source.hide_set(hidden)
                if marker is None:
                    if "object_joiner_hidden_original" in source:
                        del source["object_joiner_hidden_original"]
                else:
                    source["object_joiner_hidden_original"] = marker
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
            bpy.ops.object.select_all(action="DESELECT")
            for obj in original_selection:
                obj.select_set(True)
            context.view_layer.objects.active = original_active
            raise
        finally:
            for mesh in created_meshes:
                try:
                    if mesh.users == 0:
                        bpy.data.meshes.remove(mesh)
                except ReferenceError:
                    pass  # Blender may already have removed a joined datablock.


class OBJECT_OT_UnhideOriginals(Operator):
    bl_idname = "object.unhide_object_joiner_originals"
    bl_label = "Restore Originals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        originals = [
            obj
            for obj in context.view_layer.objects
            if "object_joiner_hidden_original" in obj
        ]
        for obj in originals:
            state = obj["object_joiner_hidden_original"]
            if isinstance(state, (bool, int)):
                state = (False, False, False)  # Legacy v2.0 visibility marker.
            obj.hide_viewport, obj.hide_render = bool(state[0]), bool(state[1])
            obj.hide_set(bool(state[2]))
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
        layout.prop(props, "mode")
        if props.mode == "REMESH":
            layout.prop(props, "voxel_size")
            layout.prop(props, "target_detail")
        layout.label(text="Uses visible modifiers at the current frame")
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
