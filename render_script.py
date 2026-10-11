import bpy
import sys
import os
import math

bpy.ops.wm.read_factory_settings(use_empty=True)

args = sys.argv[sys.argv.index("--") + 1:]
modo = args[0]           
contenido = args[1]      
efecto = args[2]         
material_tipo = args[3]  
output_path = args[4]    

bpy.ops.object.camera_add(location=(0, -6, 0), rotation=(math.radians(90), 0, 0))
camara = bpy.context.object
bpy.context.scene.camera = camara

bpy.ops.object.light_add(type='AREA', location=(3, -4, 5))
luz_principal = bpy.context.object
luz_principal.data.energy = 500

bpy.ops.object.light_add(type='AREA', location=(-3, -4, 2))
luz_relleno = bpy.context.object
luz_relleno.data.energy = 200

if modo == "texto":
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.data.body = contenido
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'MIDDLE'
    obj.data.extrude = 0.15
    obj.data.bevel_depth = 0.02
    obj.rotation_euler = (math.radians(90), 0, 0)
elif modo == "svg":
    bpy.ops.import_curve.svg(filepath=contenido)
    for o in bpy.context.selected_objects:
        o.data.extrude = 0.1
        o.data.bevel_depth = 0.01
        o.rotation_euler = (math.radians(90), 0, 0)
    obj = bpy.context.selected_objects[0]

mat = bpy.data.materials.new(name="MaterialLogo")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")

if material_tipo == "oro":
    bsdf.inputs['Base Color'].default_value = (1.0, 0.766, 0.055, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.2
elif material_tipo == "cromo":
    bsdf.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.05

obj.data.materials.append(mat)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60  

if efecto == "rotacion":
    obj.rotation_mode = 'XYZ'
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    obj.rotation_euler[2] = math.radians(360)
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=60)

scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'BLENDER_EEVEE_NEXT') else 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'FFMPEG'
scene.ffmpeg.format = 'MPEG4'
scene.ffmpeg.codec = 'H264'
scene.render.filepath = output_path

bpy.ops.render.render(animation=True)
