import bpy
import sys
import os
import math

# Limpiar la escena por defecto
bpy.ops.wm.read_factory_settings(use_empty=True)

args = sys.argv[sys.argv.index("--") + 1:]
modo = args[0]           
contenido = args[1]      
efecto = args[2]         
material_tipo = args[3]  
output_path = args[4]    

# 1. Cámara centrada
bpy.ops.object.camera_add(location=(0, -8, 0), rotation=(math.radians(90), 0, 0))
camara = bpy.context.object
bpy.context.scene.camera = camara

# 2. Iluminación
bpy.ops.object.light_add(type='SUN', location=(0, -10, 10))
luz_sol = bpy.context.object
luz_sol.data.energy = 4.0

bpy.ops.object.light_add(type='AREA', location=(0, -5, 0))
luz_frente = bpy.context.object
luz_frente.data.energy = 400

# 3. Importar Geometría y centrar
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
    curvas_importadas = [o for o in bpy.context.selected_objects if o.type == 'CURVE']
    
    for o in curvas_importadas:
        o.data.extrude = 0.08
        o.data.bevel_depth = 0.01
        o.rotation_euler = (math.radians(90), 0, 0)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        o.location = (0, 0, 0)
        
    if curvas_importadas:
        obj = curvas_importadas[0]

# 4. Materiales
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

if 'obj' in locals():
    for o in bpy.context.selected_objects:
        if o.type == 'CURVE':
            o.data.materials.append(mat)

# 5. Animación
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60  

if efecto == "rotacion" and 'obj' in locals():
    for o in bpy.context.selected_objects:
        if o.type == 'CURVE':
            o.rotation_mode = 'XYZ'
            o.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
            o.rotation_euler[2] = math.radians(360)
            o.keyframe_insert(data_path="rotation_euler", index=2, frame=60)

# 6. Selección inteligente del motor de render según la versión exacta de Blender 4.3+
engine_assigned = False
for engine_name in ['BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES']:
    try:
        scene.render.engine = engine_name
        engine_assigned = True
        break
    except Exception:
        continue

# Configuración de salida en formato MP4 FFMPEG
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.filepath = output_path

ffmpeg_settings = getattr(scene.render, 'ffmpeg', getattr(scene, 'ffmpeg', None))
if ffmpeg_settings:
    ffmpeg_settings.format = 'MPEG4'
    ffmpeg_settings.codec = 'H264'

bpy.ops.render.render(animation=True)
