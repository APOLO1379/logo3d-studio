import bpy
import sys
import os
import math

# Limpiar escena
bpy.ops.wm.read_factory_settings(use_empty=True)

args = sys.argv[sys.argv.index("--") + 1:]
modo = args[0]           
contenido = args[1]      
efecto = args[2]         
material_tipo = args[3]  
output_path = args[4]    

# 1. Configurar Iluminación Mundial (Entorno Brillante para Reflexiones)
world = bpy.data.worlds.new("WorldStudio")
bpy.context.scene.world = world
world.use_nodes = True
nodes_w = world.node_tree.nodes
nodes_w.clear()

node_background = nodes_w.new(type='ShaderNodeBackground')
node_background.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1.0)
node_background.inputs['Strength'].default_value = 1.5

node_output = nodes_w.new(type='ShaderNodeOutputWorld')
world.node_tree.links.new(node_background.outputs['Background'], node_output.inputs['Surface'])

# 2. Configurar Cámara
bpy.ops.object.camera_add(location=(0, -7, 0), rotation=(math.radians(90), 0, 0))
camara = bpy.context.object
bpy.context.scene.camera = camara

# 3. Luces de Estudio
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
luz_sol = bpy.context.object
luz_sol.data.energy = 5.0

bpy.ops.object.light_add(type='AREA', location=(-5, -5, 5))
luz_area = bpy.context.object
luz_area.data.energy = 800

# 4. Importar y Alinear Geometría
if modo == "texto":
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.data.body = contenido
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'CENTER'
    obj.data.extrude = 0.15
    obj.data.bevel_depth = 0.02
    obj.rotation_euler = (math.radians(90), 0, 0)
elif modo == "svg":
    bpy.ops.import_curve.svg(filepath=contenido)
    curvas = [o for o in bpy.context.selected_objects if o.type == 'CURVE']
    
    if curvas:
        for o in curvas:
            o.data.extrude = 0.08
            o.data.bevel_depth = 0.01
            # Orientar correctamente de frente a la cámara
            o.rotation_euler = (math.radians(90), 0, 0)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            
        # Agrupar curvas
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        parent_obj = bpy.context.object
        for o in curvas:
            o.parent = parent_obj
            
        # Centrar el grupo completo frente a la cámara
        parent_obj.location = (0, 0, 0)
        parent_obj.scale = (0.5, 0.5, 0.5)
        obj = parent_obj

# 5. Material Fotorrealista
mat = bpy.data.materials.new(name="MaterialMetalico")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")

if material_tipo == "oro":
    bsdf.inputs['Base Color'].default_value = (1.0, 0.766, 0.055, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.1
elif material_tipo == "cromo":
    bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.02

for o in bpy.data.objects:
    if o.type == 'CURVE' or o.type == 'FONT':
        o.data.materials.append(mat)

# 6. Animación
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60

if efecto == "rotacion" and 'obj' in locals():
    obj.rotation_mode = 'XYZ'
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    obj.rotation_euler[2] = math.radians(360)
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=60)

# 7. Render Cycles CPU con iluminación de reflexión activa
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = False

scene.render.image_settings.file_format = 'FFMPEG'
scene.render.filepath = output_path

ffmpeg_settings = getattr(scene.render, 'ffmpeg', getattr(scene, 'ffmpeg', None))
if ffmpeg_settings:
    ffmpeg_settings.format = 'MPEG4'
    ffmpeg_settings.codec = 'H264'

bpy.ops.render.render(animation=True)
