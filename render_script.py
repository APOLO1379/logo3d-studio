import bpy
import sys
import os
import math

# 1. Limpiar escena completamente
bpy.ops.wm.read_factory_settings(use_empty=True)

args = sys.argv[sys.argv.index("--") + 1:]
modo = args[0]           
contenido = args[1]      
efecto = args[2]         
material_tipo = args[3]  
output_path = args[4]    

# 2. Configurar Entorno e Iluminación
world = bpy.data.worlds.new("WorldStudio")
bpy.context.scene.world = world
world.use_nodes = True
nodes_w = world.node_tree.nodes
nodes_w.clear()

node_background = nodes_w.new(type='ShaderNodeBackground')
node_background.inputs['Color'].default_value = (0.85, 0.85, 0.85, 1.0)
node_background.inputs['Strength'].default_value = 1.2

node_output = nodes_w.new(type='ShaderNodeOutputWorld')
world.node_tree.links.new(node_background.outputs['Background'], node_output.inputs['Surface'])

# Luz Sol para reflejos
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
luz_sol = bpy.context.object
luz_sol.data.energy = 4.0

# 3. Importar Geometría y Centrar Bounding Box
if modo == "texto":
    bpy.ops.object.text_add(location=(0, 0, 0))
    target_obj = bpy.context.object
    target_obj.data.body = contenido
    target_obj.data.align_x = 'CENTER'
    target_obj.data.align_y = 'CENTER'
    target_obj.data.extrude = 0.15
    target_obj.data.bevel_depth = 0.02
    target_obj.rotation_euler = (math.radians(90), 0, 0)
    
elif modo == "svg":
    bpy.ops.import_curve.svg(filepath=contenido)
    curvas = [o for o in bpy.context.selected_objects if o.type == 'CURVE']
    
    if curvas:
        # Dar extrusión a cada trazado SVG
        for c in curvas:
            c.data.extrude = 0.05
            c.data.bevel_depth = 0.01
            
        # Crear un objeto Padre (Empty) en el centro geométrico del SVG
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        parent_empty = bpy.context.object
        
        # Calcular los límites (bounding box) reales de todas las curvas juntas
        min_x = min([c.location.x for c in curvas])
        max_x = max([c.location.x for c in curvas])
        min_y = min([c.location.y for c in curvas])
        max_y = max([c.location.y for c in curvas])
        
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        
        # Parentar y mover al centro de la escena (0,0,0)
        for c in curvas:
            c.parent = parent_empty
            c.location.x -= center_x
            c.location.y -= center_y
            
        # Rotar de frente a la cámara y escalar a un tamaño estándar (2 unidades)
        parent_empty.rotation_euler = (math.radians(90), 0, 0)
        
        max_size = max(abs(max_x - min_x), abs(max_y - min_y), 0.001)
        scale = 2.5 / max_size
        parent_empty.scale = (scale, scale, scale)
        
        target_obj = parent_empty

# 4. Configurar Cámara en posición fija frontal
bpy.ops.object.camera_add(location=(0, -5, 0), rotation=(math.radians(90), 0, 0))
cam = bpy.context.object
bpy.context.scene.camera = cam

# 5. Aplicar Material Metalizado
mat = bpy.data.materials.new(name="MaterialMetalico")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")

if material_tipo == "oro":
    bsdf.inputs['Base Color'].default_value = (1.0, 0.766, 0.055, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.15
elif material_tipo == "cromo":
    bsdf.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.05

for o in bpy.data.objects:
    if o.type == 'CURVE' or o.type == 'FONT':
        o.data.materials.append(mat)

# 6. Animación de Rotación (360 grados en 60 frames)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60

if efecto == "rotacion" and 'target_obj' in locals():
    target_obj.rotation_mode = 'XYZ'
    target_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    target_obj.rotation_euler[2] = math.radians(360)
    target_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=60)

# 7. Motor Cycles CPU optimizado (8 samples para render súper liviano)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 8
scene.cycles.use_denoising = False

scene.render.image_settings.file_format = 'FFMPEG'
scene.render.filepath = output_path

ffmpeg_settings = getattr(scene.render, 'ffmpeg', getattr(scene, 'ffmpeg', None))
if ffmpeg_settings:
    ffmpeg_settings.format = 'MPEG4'
    ffmpeg_settings.codec = 'H264'

bpy.ops.render.render(animation=True)
