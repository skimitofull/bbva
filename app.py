import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import black
from io import BytesIO
import base64

# Función para generar el PDF con formato replicado al original

def generar_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margen_izq = 10 * mm
    margen_sup = height - 33 * mm
    altura_linea = 4.3 * mm
    fuente = "Helvetica"
    tamanio_fuente = 6

    columnas = ["OPER", "LIQ", "DESCRIPCIÓN", "REFERENCIA", "CARGOS", "ABONOS", "OPERACIÓN", "LIQUIDACIÓN"]
    posiciones = [14 * mm, 30 * mm, 45 * mm, 87 * mm, 124 * mm, 144 * mm, 164 * mm, 184 * mm]

    def encabezado(y_pos):
        c.setFillColor(black)
        c.setFont(fuente, tamanio_fuente)
        for i, col in enumerate(columnas):
            c.drawString(posiciones[i], y_pos, col)

    def nueva_pagina():
        nonlocal y
        c.showPage()
        y = margen_sup
        encabezado(y)
        y -= altura_linea

    y = margen_sup
    encabezado(y)
    y -= altura_linea

    for index, row in df.iterrows():
        if y < 40 * mm:
            nueva_pagina()

        for k, pos in enumerate(posiciones):
            texto = str(row[k]) if k < len(row) and pd.notna(row[k]) else ""
            c.setFont(fuente, tamanio_fuente)
            c.drawString(pos, y, texto)

        y -= altura_linea

    c.save()
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Generador de Estado de Cuenta Ficticio")
st.write("Sube un archivo Excel con la estructura del estado de cuenta")

archivo = st.file_uploader("Cargar archivo Excel", type=[".xlsx"])

if archivo:
    df = pd.read_excel(archivo, engine="openpyxl")
    pdf_buffer = generar_pdf(df)

    st.download_button(label="Descargar Estado de Cuenta PDF",
                       data=pdf_buffer,
                       file_name="estado_de_cuenta.pdf",
                       mime="application/pdf")

    # Mostrar visor embebido con base64
    base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="700px"
            type="application/pdf">
        </iframe>
    """
    st.markdown("### Vista previa del PDF generado")
    st.components.v1.html(pdf_display, height=700, scrolling=True)
