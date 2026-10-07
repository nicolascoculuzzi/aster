"""Build a small lighthouse scene and save it as a .blend for Compute renders.

Run with the `bpy` Python module (Blender 4.2):
    python make_scene.py out.blend
Frames 1-4 orbit the camera a quarter turn each.
"""
import math
import sys

import bpy

out = sys.argv[-1] if sys.argv[-1].endswith(".blend") else "lighthouse.blend"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name, color, roughness=0.5, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def add(obj_op, mat, **kw):
    obj_op(**kw)
    obj = bpy.context.active_object
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj


white = material("White", (0.9, 0.88, 0.85), 0.4)
red = material("Red", (0.6, 0.04, 0.03), 0.35)
rock = material("Rock", (0.08, 0.07, 0.06), 0.9)
lamp = material("Lamp", (1, 0.8, 0.5), 0.2, emission=(1, 0.75, 0.4), strength=40)

# Ocean
water = material("Water", (0.02, 0.05, 0.08), 0.05)
bpy.ops.mesh.primitive_plane_add(size=400)
bpy.context.active_object.data.materials.append(water)

# Cliff
cliff = add(bpy.ops.mesh.primitive_ico_sphere_add, rock, subdivisions=3, radius=6, location=(0, 0, -2.5))
cliff.scale = (1.6, 1.3, 0.8)
bpy.ops.object.modifier_add(type="DISPLACE")
tex = bpy.data.textures.new("RockNoise", "CLOUDS")
tex.noise_scale = 1.5
cliff.modifiers["Displace"].texture = tex
cliff.modifiers["Displace"].strength = 1.2

# Striped tower
z = 2.0
for i in range(6):
    r = 1.1 - i * 0.07
    add(bpy.ops.mesh.primitive_cylinder_add, red if i % 2 else white,
        vertices=48, radius=r, depth=1.2, location=(0, 0, z + 0.6))
    z += 1.2
add(bpy.ops.mesh.primitive_cylinder_add, red, vertices=48, radius=0.9, depth=0.15, location=(0, 0, z + 0.07))
add(bpy.ops.mesh.primitive_uv_sphere_add, lamp, radius=0.55, location=(0, 0, z + 0.7))
add(bpy.ops.mesh.primitive_cone_add, red, vertices=48, radius1=0.8, depth=0.9, location=(0, 0, z + 1.6))
bpy.ops.object.light_add(type="POINT", location=(0, 0, z + 0.7))
bpy.context.active_object.data.energy = 3000
bpy.context.active_object.data.color = (1, 0.75, 0.45)

# Dusk sky
world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
sky = nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(2)
sky.sun_rotation = math.radians(200)
world.node_tree.links.new(sky.outputs["Color"], nodes["Background"].inputs["Color"])
nodes["Background"].inputs["Strength"].default_value = 0.6

# Orbiting camera, aimed at the tower
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 5)
scene.collection.objects.link(target)
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.lens = 35
scene.camera = cam
track = cam.constraints.new("TRACK_TO")
track.target = target
for frame in range(1, 5):
    a = math.radians(-60 + (frame - 1) * 90)
    cam.location = (22 * math.cos(a), 22 * math.sin(a), 4 + frame)
    cam.keyframe_insert("location", frame=frame)

scene.frame_start, scene.frame_end = 1, 4
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = 128
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"

bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
