import streamlit as st
import subprocess
import os
import glob
import numpy as np
from PIL import Image

st.set_page_config(page_title="Studio 3D Logos", layout="wide")
st.title("🎬 Creador & Animador de Logos 3D")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. Fuente del Logo")
    tipo_origen = st.radio("Selecciona el origen:", ["Texto Plano", "Imagen PNG (Transparente)"])
    
    contenido = ""
    modo_script = "texto"
    
    if tipo_origen == "Texto Plano":
        contenido = st.text_input("Escribe tu marca/texto:", "MI MARCA")
        modo_script = "texto"
    else:
        file_png = st.file_uploader("Sube tu logo en PNG:", type=["png"])
        if file_png is not None:
            temp_bmp = "temp_input.bmp"
            svg_path = os.path.abspath("temp_logo.svg")
            
            img = Image.open(file_png).convert('RGBA')
            alpha = np.array(img)[:, :, 3]
            silueta = Image.fromarray((alpha > 128).astype(np.uint8) * 255)
            silueta.save(temp_bmp)
            
            subprocess.run(["potrace", temp_bmp, "-s", "-o", svg_path], check=True)
            
            contenido = svg_path
            modo_script = "svg"
            st.image(file_png, caption="Logo cargado", width=200)

    st.subheader("2. Estilo y Animación")
    material = st.selectbox("Acabado 3D:", ["oro", "cromo"])
    animacion = st.selectbox("Efecto de Animación:", ["rotacion"])
    
    btn_generar = st.button("🚀 Renderizar Animación 3D", type="primary", use_container_width=True)

with col_right:
    st.subheader("3. Vista Previa / Resultado")
    if btn_generar and contenido:
        with st.spinner("Blender está renderizando la animación en 3D..."):
            # Limpiar archivos previos
            for f in glob.glob("*.mp4"):
                try: os.remove(f)
                except: pass
                
            output_video = os.path.abspath("logo_3d.mp4")
                
            cmd = [
                "blender", "-b",
                "-P", "render_script.py",
                "--",
                modo_script,
                contenido,
                animacion,
                material,
                output_video
            ]
            
            # Forzar controladores por software para evitar fallos de OpenGL/EGL
            env_vars = os.environ.copy()
            env_vars["GALLIUM_DRIVER"] = "softpipe"
            env_vars["LIBGL_ALWAYS_SOFTWARE"] = "1"
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env_vars)
            
            # Buscar video generado
            archivos_mp4 = glob.glob("*.mp4")
            
            if archivos_mp4 and os.path.getsize(archivos_mp4[0]) > 0:
                video_final = archivos_mp4[0]
                with open(video_final, "rb") as file:
                    video_bytes = file.read()
                    
                st.video(video_bytes)
                st.download_button(
                    label="📥 Descargar Video MP4",
                    data=video_bytes,
                    file_name="logo_3d_animado.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            else:
                st.error("Ocurrió un error en el renderizado.")
                st.code(result.stderr if result.stderr else result.stdout)
