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

# 1. Configurar Entorno e Iluminación de Fondo
world = bpy.data.worlds.new("WorldStudio")
bpy.context.scene.world = world
world.use_nodes = True
nodes_w = world.node_tree.nodes
nodes_w.clear()

node_background = nodes_w.new(type='ShaderNodeBackground')
node_background.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1.0)
node_background.inputs['Strength'].default_value = 1.0

node_output = nodes_w.new(type='ShaderNodeOutputWorld')
world.node_tree.links.new(node_background.outputs['Background'], node_output.inputs['Surface'])

# 2. Luces
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
luz_sol = bpy.context.object
luz_sol.data.energy = 3.0

# 3. Importar y Normalizar Escala/Posición del Logo
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
        # Seleccionar todas las curvas
        for o in curvas:
            o.data.extrude = 0.05
            o.data.bevel_depth = 0.01
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            
        # Unir todas las curvas del SVG en un solo objeto para control de escala
        bpy.ops.object.join()
        obj = bpy.context.active_object
        
        # Orientar hacia la cámara
        obj.rotation_euler = (math.radians(90), 0, 0)
        
        # Reestablecer origen al centro de la geometría
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        obj.location = (0, 0, 0)
        
        # Ajustar dimensiones a un tamaño estándar (aprox. 2 unidades de ancho)
        max_dim = max(obj.dimensions.x, obj.dimensions.z, 0.0001)
        scale_factor = 2.0 / max_dim
        obj.scale = (scale_factor, scale_factor, scale_factor)

# 4. Configurar Cámara apuntando al centro
bpy.ops.object.camera_add(location=(0, -4.5, 0), rotation=(math.radians(90), 0, 0))
camara = bpy.context.object
bpy.context.scene.camera = camara

# 5. Aplicar Material Metalizado
mat = bpy.data.materials.new(name="MaterialMetalico")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")

if material_tipo == "oro":
    bsdf.inputs['Base Color'].default_value = (1.0, 0.766, 0.055, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.2
elif material_tipo == "cromo":
    bsdf.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.05

if 'obj' in locals():
    obj.data.materials.append(mat)

# 6. Animación
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60

if efecto == "rotacion" and 'obj' in locals():
    obj.rotation_mode = 'XYZ'
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    obj.rotation_euler[2] = math.radians(360)
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=60)

# 7. Render Cycles CPU ultra rápido (4 muestras) para evitar lag en Streamlit Cloud
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 4
scene.cycles.use_denoising = False

scene.render.image_settings.file_format = 'FFMPEG'
scene.render.filepath = output_path

ffmpeg_settings = getattr(scene.render, 'ffmpeg', getattr(scene, 'ffmpeg', None))
if ffmpeg_settings:
    ffmpeg_settings.format = 'MPEG4'
    ffmpeg_settings.codec = 'H264'

bpy.ops.render.render(animation=True)
