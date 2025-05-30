import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

# Registrar fuente Arial Narrow
pdfmetrics.registerFont(TTFont('Arial-Narrow', 'fonts/arialn.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Narrow-Italic', 'fonts/arialni.ttf'))

st.title("Generador de Estado de Cuenta Bancario (PDF Ficticio)")

fase = st.radio("Selecciona la fase del proceso:", ["1. Generar Excel trabajado", "2. Convertir Excel a PDF final"])

if fase == "2. Convertir Excel a PDF final":
    archivo_excel = st.file_uploader("Sube el archivo Excel corregido para convertir a PDF", type=["xlsx"])

    if archivo_excel and st.button("Generar PDF"):
        df = pd.read_excel(archivo_excel, header=None)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 60

        def draw_row(y, row):
            col_positions = [16, 51, 83, 137, 390, 428, 496, 564]  # Ajustado con precisión
            for i in range(len(col_positions)):
                if pd.isna(row[i]):
                    continue
                font = 'Arial-Narrow-Italic' if i == 1 and row.name % 5 == 1 else 'Arial-Narrow'
                c.setFont(font, 9.5)
                c.drawString(col_positions[i], y, str(row[i]))

        for i, row in df.iterrows():
            draw_row(y, row)
            y -= 12
            if y < 60:
                c.showPage()
                y = height - 60

        c.save()
        buffer.seek(0)

        st.download_button("Descargar PDF generado", buffer, file_name="estado_cuenta.pdf")

elif fase == "1. Generar Excel trabajado":
    st.info("Fase ya integrada. Usa este modo para generar Excel antes de convertir.")
