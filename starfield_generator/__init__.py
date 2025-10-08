"""Blender addon for generating high quality star fields."""

bl_info = {
    "name": "Procedural Starfield Generator",
    "author": "OpenAI Assistant",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Starfield",
    "description": "Generate a realistic star field with controllable density, scale and brightness.",
    "category": "Object",
}

import math
import random
from dataclasses import dataclass

import bpy
import bmesh
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from mathutils import Vector


STAR_MESH_NAME = "Starfield_StarMesh"
STAR_MATERIAL_NAME = "Starfield_StarMaterial"


@dataclass
class StarfieldSettings:
    star_count: int
    field_radius: float
    star_size_min: float
    star_size_max: float
    base_brightness: float
    brightness_variation: float
    collection_name: str
    clear_existing: bool
    random_seed: int


def ensure_collection(scene: bpy.types.Scene, name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
    return collection


def clear_collection(collection: bpy.types.Collection) -> None:
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def ensure_star_mesh() -> bpy.types.Mesh:
    mesh = bpy.data.meshes.get(STAR_MESH_NAME)
    if mesh is not None:
        return mesh

    mesh = bpy.data.meshes.new(STAR_MESH_NAME)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    bm.to_mesh(mesh)
    bm.free()
    mesh.use_auto_smooth = False
    return mesh


def ensure_star_material(settings: StarfieldSettings) -> bpy.types.Material:
    material = bpy.data.materials.get(STAR_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(STAR_MATERIAL_NAME)
        material.use_nodes = True

    node_tree = material.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    nodes.clear()

    output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (400, 0)

    emission_node = nodes.new("ShaderNodeEmission")
    emission_node.location = (180, 0)

    object_info_node = nodes.new("ShaderNodeObjectInfo")
    object_info_node.location = (-600, 0)

    brightness_scale_node = nodes.new("ShaderNodeMath")
    brightness_scale_node.operation = 'MULTIPLY'
    brightness_scale_node.inputs[1].default_value = settings.brightness_variation
    brightness_scale_node.location = (-200, -160)

    brightness_add_node = nodes.new("ShaderNodeMath")
    brightness_add_node.operation = 'ADD'
    brightness_add_node.inputs[1].default_value = settings.base_brightness
    brightness_add_node.location = (40, -160)

    color_ramp_node = nodes.new("ShaderNodeValToRGB")
    color_ramp_node.location = (-200, 140)
    color_ramp_node.color_ramp.elements[0].position = 0.0
    color_ramp_node.color_ramp.elements[0].color = (0.8, 0.9, 1.0, 1.0)
    color_ramp_node.color_ramp.elements[1].position = 1.0
    color_ramp_node.color_ramp.elements[1].color = (1.0, 0.95, 0.9, 1.0)
    mid_element = color_ramp_node.color_ramp.elements.new(0.35)
    mid_element.color = (1.0, 0.8, 0.65, 1.0)

    hue_shift_node = nodes.new("ShaderNodeHueSaturation")
    hue_shift_node.inputs['Saturation'].default_value = 1.1
    hue_shift_node.inputs['Value'].default_value = 1.2
    hue_shift_node.location = (-20, 140)

    links.new(object_info_node.outputs['Random'], color_ramp_node.inputs['Fac'])
    links.new(color_ramp_node.outputs['Color'], hue_shift_node.inputs['Color'])
    links.new(hue_shift_node.outputs['Color'], emission_node.inputs['Color'])

    links.new(object_info_node.outputs['Random'], brightness_scale_node.inputs[0])
    links.new(brightness_scale_node.outputs[0], brightness_add_node.inputs[0])
    links.new(brightness_add_node.outputs[0], emission_node.inputs['Strength'])

    links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])

    material.blend_method = 'BLEND'
    if hasattr(material, "shadow_method"):
        material.shadow_method = 'NONE'
    elif hasattr(material, "use_shadow"):
        material.use_shadow = False
    material.use_backface_culling = False

    return material


def random_point_in_sphere(radius: float) -> Vector:
    while True:
        point = Vector((
            random.uniform(-1.0, 1.0),
            random.uniform(-1.0, 1.0),
            random.uniform(-1.0, 1.0),
        ))
        if point.length <= 1.0:
            return point * radius


def generate_starfield(context: bpy.types.Context, settings: StarfieldSettings) -> None:
    random.seed(settings.random_seed)

    collection = ensure_collection(context.scene, settings.collection_name)

    if settings.clear_existing:
        clear_collection(collection)

    mesh = ensure_star_mesh()
    material = ensure_star_material(settings)

    has_material = any(mat == material for mat in mesh.materials)
    if not has_material:
        mesh.materials.clear()
        mesh.materials.append(material)

    for i in range(settings.star_count):
        star_object = bpy.data.objects.new(f"Star_{i:05d}", mesh)
        star_object.location = random_point_in_sphere(settings.field_radius)

        star_scale = random.uniform(settings.star_size_min, settings.star_size_max)
        star_object.scale = (star_scale, star_scale, star_scale)

        collection.objects.link(star_object)


class STARFIELD_OT_generate(Operator):
    bl_idname = "starfield.generate"
    bl_label = "Generate Star Field"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        props = context.scene.starfield_props
        star_size_min = max(0.0001, props.star_size_min)
        star_size_max = max(star_size_min, props.star_size_max)

        settings = StarfieldSettings(
            star_count=props.star_count,
            field_radius=props.field_radius,
            star_size_min=star_size_min,
            star_size_max=star_size_max,
            base_brightness=props.base_brightness,
            brightness_variation=props.brightness_variation,
            collection_name=props.collection_name,
            clear_existing=props.clear_existing,
            random_seed=props.random_seed,
        )

        generate_starfield(context, settings)

        self.report({'INFO'}, f"Generated {settings.star_count} stars in '{settings.collection_name}' collection")
        return {'FINISHED'}


class STARFIELD_PT_panel(Panel):
    bl_label = "Starfield Generator"
    bl_idname = "STARFIELD_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Starfield"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        props = context.scene.starfield_props

        layout.prop(props, "collection_name")
        layout.prop(props, "clear_existing")
        layout.separator()

        layout.prop(props, "star_count")
        layout.prop(props, "field_radius")
        layout.prop(props, "random_seed")
        layout.separator()

        col = layout.column(align=True)
        col.prop(props, "star_size_min")
        col.prop(props, "star_size_max")
        layout.separator()

        layout.prop(props, "base_brightness")
        layout.prop(props, "brightness_variation")
        layout.separator()

        layout.operator(STARFIELD_OT_generate.bl_idname, icon='PARTICLES')


class StarfieldProperties(PropertyGroup):
    collection_name: StringProperty(
        name="Collection",
        default="Starfield",
        description="Collection to hold the generated stars"
    )

    clear_existing: BoolProperty(
        name="Clear Existing",
        default=True,
        description="Remove existing star objects in the target collection before generating new ones"
    )

    star_count: IntProperty(
        name="Star Count",
        default=2000,
        min=1,
        max=50000,
        description="Number of stars to create"
    )

    field_radius: FloatProperty(
        name="Field Radius",
        default=50.0,
        min=0.1,
        description="Radius of the spherical field in which stars are distributed"
    )

    random_seed: IntProperty(
        name="Random Seed",
        default=0,
        min=0,
        description="Seed for the random generator so results can be reproduced"
    )

    star_size_min: FloatProperty(
        name="Min Star Size",
        default=0.02,
        min=0.001,
        description="Minimum star scale"
    )

    star_size_max: FloatProperty(
        name="Max Star Size",
        default=0.15,
        min=0.001,
        description="Maximum star scale"
    )

    base_brightness: FloatProperty(
        name="Base Brightness",
        default=3.0,
        min=0.0,
        description="Base brightness for all stars"
    )

    brightness_variation: FloatProperty(
        name="Brightness Variation",
        default=8.0,
        min=0.0,
        description="How much the star brightness varies"
    )


def register():
    bpy.utils.register_class(StarfieldProperties)
    bpy.utils.register_class(STARFIELD_OT_generate)
    bpy.utils.register_class(STARFIELD_PT_panel)
    bpy.types.Scene.starfield_props = PointerProperty(type=StarfieldProperties)


def unregister():
    del bpy.types.Scene.starfield_props
    bpy.utils.unregister_class(STARFIELD_PT_panel)
    bpy.utils.unregister_class(STARFIELD_OT_generate)
    bpy.utils.unregister_class(StarfieldProperties)


if __name__ == "__main__":
    register()
