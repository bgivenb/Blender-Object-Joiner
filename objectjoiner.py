bl_info = {
    "name": "Object Joiner",
    "author": "Given Borthwick",
    "version": (1, 1),
    "blender": (3, 6, 0),
    "location": "View3D > Tool Shelf > Object Joiner",
    "description": "Joins selected objects with customizable voxel size and target detail.",
    "warning": "",
    "wiki_url": "https://github.com/bgivenb/Blender-Object-Joiner",
    "category": "Object",
}

import bpy
from bpy.props import FloatProperty, PointerProperty, BoolProperty
from bpy.types import Operator, Panel, PropertyGroup


class ObjectJoinerProperties(PropertyGroup):
    voxel_size: FloatProperty(
        name="Voxel Size (m)",
        description="Smaller values yield more detailed meshes (may increase computation time)",
        default=0.01,
        min=0.0001,
        max=1.0,
    )
    target_detail: FloatProperty(
        name="Target Detail",
        description="Lower values result in fewer polygons (between 0 and 1)",
        default=0.1,
        min=0.01,
        max=1.0,
    )
    hide_original: BoolProperty(
        name="Hide Original Objects",
        description="Hide the original objects after joining",
        default=True,
    )


class OBJECT_OT_JoinObjects(Operator):
    bl_idname = "object.join_objects_custom"
    bl_label = "Join Objects"
    bl_description = "Joins selected objects with specified voxel size and target detail"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.object_joiner_props
        voxel_size = props.voxel_size
        target_detail = props.target_detail
        hide_original = props.hide_original

        # Duplicate selected objects and move to a new collection
        selected_objs = context.selected_objects
        if not selected_objs:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}

        new_collection = bpy.data.collections.new("ObjectJoiner_Collection")
        context.scene.collection.children.link(new_collection)

        duplicated_objs = []
        for obj in selected_objs:
            dup = obj.copy()
            dup.data = obj.data.copy()
            new_collection.objects.link(dup)
            duplicated_objs.append(dup)

        # Hide original objects if the option is enabled
        if hide_original:
            for obj in selected_objs:
                obj.hide_viewport = True
                obj.hide_render = True

        bpy.ops.object.select_all(action='DESELECT')
        for obj in duplicated_objs:
            obj.select_set(True)
        context.view_layer.objects.active = duplicated_objs[0]

        # Join duplicated objects
        bpy.ops.object.join()
        joined_obj = context.active_object
        joined_obj.name = "objectjoiner_joined"

        # Duplicate joined object to create shell
        shell_obj = joined_obj.copy()
        shell_obj.data = joined_obj.data.copy()
        shell_obj.name = "objectjoiner_shell"
        new_collection.objects.link(shell_obj)

        # Apply Remesh Modifier (Voxel)
        remesh_mod = joined_obj.modifiers.new(name="Remesh", type='REMESH')
        remesh_mod.mode = 'VOXEL'
        remesh_mod.voxel_size = voxel_size
        remesh_mod.adaptivity = 0.001
        bpy.context.view_layer.objects.active = joined_obj
        bpy.ops.object.modifier_apply(modifier=remesh_mod.name)

        # First Shrinkwrap Modifier
        shrinkwrap1 = joined_obj.modifiers.new(name="Shrinkwrap1", type='SHRINKWRAP')
        shrinkwrap1.wrap_method = 'NEAREST_SURFACEPOINT'
        shrinkwrap1.wrap_mode = 'ON_SURFACE'
        shrinkwrap1.target = shell_obj
        bpy.ops.object.modifier_apply(modifier=shrinkwrap1.name)

        # Decimate Modifier
        decimate = joined_obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate.decimate_type = 'COLLAPSE'
        decimate.ratio = target_detail
        bpy.ops.object.modifier_apply(modifier=decimate.name)

        # Second Shrinkwrap Modifier
        shrinkwrap2 = joined_obj.modifiers.new(name="Shrinkwrap2", type='SHRINKWRAP')
        shrinkwrap2.wrap_method = 'NEAREST_SURFACEPOINT'
        shrinkwrap2.wrap_mode = 'ON_SURFACE'
        shrinkwrap2.target = shell_obj
        bpy.ops.object.modifier_apply(modifier=shrinkwrap2.name)

        # Delete shell object
        bpy.data.objects.remove(shell_obj, do_unlink=True)

        self.report({'INFO'}, "Objects joined successfully.")
        return {'FINISHED'}


class OBJECT_OT_UnhideOriginals(Operator):
    bl_idname = "object.unhide_originals"
    bl_label = "Unhide Original Objects"
    bl_description = "Unhides the original objects that were hidden by Object Joiner"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        original_collection = bpy.data.collections.get("ObjectJoiner_Collection")
        if not original_collection:
            self.report({'WARNING'}, "No ObjectJoiner_Collection found.")
            return {'CANCELLED'}

        # Iterate through all objects in the original collection and unhide them
        for obj in original_collection.objects:
            obj.hide_viewport = False
            obj.hide_render = False

        self.report({'INFO'}, "Original objects have been unhidden.")
        return {'FINISHED'}


class OBJECTJOINER_PT_MainPanel(Panel):
    bl_label = "Object Joiner"
    bl_idname = "OBJECTJOINER_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Object Joiner'

    def draw(self, context):
        layout = self.layout
        props = context.scene.object_joiner_props

        layout.prop(props, "voxel_size")
        layout.prop(props, "target_detail")
        layout.prop(props, "hide_original")
        layout.operator("object.join_objects_custom", icon='AUTOMERGE_ON')
        if props.hide_original:
            layout.separator()
            layout.operator("object.unhide_originals", text="Unhide Original Objects", icon='HIDE_OFF')
        
        # Branding
        layout.separator()
        layout.label(text="Created by Given Borthwick", icon='INFO')


def register():
    bpy.utils.register_class(ObjectJoinerProperties)
    bpy.utils.register_class(OBJECT_OT_JoinObjects)
    bpy.utils.register_class(OBJECT_OT_UnhideOriginals)
    bpy.utils.register_class(OBJECTJOINER_PT_MainPanel)
    bpy.types.Scene.object_joiner_props = PointerProperty(type=ObjectJoinerProperties)


def unregister():
    bpy.utils.unregister_class(ObjectJoinerProperties)
    bpy.utils.unregister_class(OBJECT_OT_JoinObjects)
    bpy.utils.unregister_class(OBJECT_OT_UnhideOriginals)
    bpy.utils.unregister_class(OBJECTJOINER_PT_MainPanel)
    del bpy.types.Scene.object_joiner_props


if __name__ == "__main__":
    register()
