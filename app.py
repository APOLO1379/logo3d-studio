import streamlit as st
import subprocess
import os
import cv2
import numpy as np
from PIL import Image
import potrace

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
            # Procesar imagen con Potrace
            img = Image.open(file_png).convert('L')
            data = np.array(img) < 128
            bmp = potrace.Bitmap(data)
            path = bmp.trace()
            
            svg_path = "temp_logo.svg"
            with open(svg_path, "w") as f:
                f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{img.width}" height="{img.height}">')
                for curve in path:
                    f.write('<path d="M ' + ' L '.join([f"{pt.x},{pt.y}" for pt in curve.start_point]) + ' Z" fill="black"/>')
                f.write('</svg>')
            
            contenido = os.path.abspath(svg_path)
            modo_script = "svg"
            st.image(file_png, caption="Logo cargado", width=200)

    st.subheader("2. Estilo y Animación")
    material = st.selectbox("Acabado 3D:", ["oro", "cromo"])
    animacion = st.selectbox("Efecto de Animación:", ["rotacion"])
    
    btn_generar = st.button("🚀 Renderizar Animación 3D", type="primary", use_container_width=True)

with col_right:
    st.subheader("3. Vista Previa / Resultado")
    if btn_generar and contenido:
        with st.spinner("Blender está renderizando la animación en 3D... (Toma unos segundos)"):
            output_video = os.path.abspath("logo_3d.mp4")
            if os.path.exists(output_video):
                os.remove(output_video)
                
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
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if os.path.exists(output_video + "0001-0060.mp4"):
                os.rename(output_video + "0001-0060.mp4", output_video)

            if os.path.exists(output_video):
                st.video(output_video)
                with open(output_video, "rb") as file:
                    st.download_button(
                        label="📥 Descargar Video MP4",
                        data=file,
                        file_name="logo_3d_animado.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
            else:
                st.error("Ocurrió un error durante el renderizado.")
                st.code(result.stderr)
