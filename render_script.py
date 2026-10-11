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

# 1. Configurar Luz Ambiental Global (World) para evitar fondos o sombras 100% negras
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = (0.1, 0.1, 0.1, 1.0)
bg.inputs['Strength'].default_value = 1.0

# 2. Configurar Cámara en posición estratégica mirando al centro
bpy.ops.object.camera_add(location=(0, -5, 0), rotation=(math.radians(90), 0, 0))
camara = bpy.context.object
bpy.context.scene.camera = camara

# 3. Iluminación frontal de estudio
bpy.ops.object.light_add(type='SUN', location=(0, -10, 10))
luz_sol = bpy.context.object
luz_sol.data.energy = 3.0

bpy.ops.object.light_add(type='AREA', location=(0, -3, 0))
luz_frente = bpy.context.object
luz_frente.data.energy = 500

# 4. Importar y Centrar/Escalar Geometría
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
        # Unir temporalmente o iterar para dar volumen y centrar
        for o in curvas:
            o.data.extrude = 0.05
            o.data.bevel_depth = 0.01
            o.rotation_euler = (math.radians(90), 0, 0)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        
        # Calcular el centro exacto de todo el grupo SVG
        min_x = min(o.location.x for o in curvas)
        max_x = max(o.location.x for o in curvas)
        min_z = min(o.location.z for o in curvas)
        max_z = max(o.location.z for o in curvas)
        
        center_x = (min_x + max_x) / 2
        center_z = (min_z + max_z) / 2
        
        # Calcular escala para encajar en pantalla (tamaño objetivo aprox: 2.5 unidades)
        size_x = max(max_x - min_x, 0.1)
        size_z = max(max_z - min_z, 0.1)
        max_dim = max(size_x, size_z)
        scale_factor = 2.5 / max_dim
        
        # Reposicionar y reescalar cada parte del SVG al centro (0,0,0)
        for o in curvas:
            o.location.x = (o.location.x - center_x) * scale_factor
            o.location.z = (o.location.z - center_z) * scale_factor
            o.scale = (scale_factor, scale_factor, scale_factor)
            
        # Crear un objeto padre nulo en el centro para animar todas las curvas juntas
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        parent_obj = bpy.context.object
        for o in curvas:
            o.parent = parent_obj
        obj = parent_obj

# 5. Aplicar Material Metalizado
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

for o in bpy.data.objects:
    if o.type == 'CURVE' or o.type == 'FONT':
        o.data.materials.append(mat)

# 6. Animación de Rotación 360°
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60  

if efecto == "rotacion" and 'obj' in locals():
    obj.rotation_mode = 'XYZ'
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    obj.rotation_euler[2] = math.radians(360)
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=60)

# 7. Configurar Render Cycles (CPU en baja resolución de muestras para rapidez y estabilidad)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 12
scene.cycles.use_denoising = False

scene.render.image_settings.file_format = 'FFMPEG'
scene.render.filepath = output_path

ffmpeg_settings = getattr(scene.render, 'ffmpeg', getattr(scene, 'ffmpeg', None))
if ffmpeg_settings:
    ffmpeg_settings.format = 'MPEG4'
    ffmpeg_settings.codec = 'H264'

bpy.ops.render.render(animation=True)
