import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
import base64

# Función para generar el PDF en memoria
def generar_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margen_izq = 20 * mm
    margen_sup = height - 25 * mm
    altura_linea = 6 * mm
    fuente = "Helvetica"
    tamanio_fuente = 7

    columnas = ["OPER", "LIQ", "DESCRIPCIÓN", "REFERENCIA", "CARGOS", "ABONOS", "OPERACIÓN", "LIQUIDACIÓN"]
    posiciones = [margen_izq, margen_izq + 20*mm, margen_izq + 40*mm, margen_izq + 95*mm,
                  margen_izq + 120*mm, margen_izq + 140*mm, margen_izq + 160*mm, margen_izq + 180*mm]

    y = margen_sup

    def nueva_pagina():
        nonlocal y
        c.showPage()
        y = margen_sup
        c.setFont(fuente, tamanio_fuente)
        c.drawString(margen_izq, height - 20 * mm, "Estado de Cuenta")
        for i, col in enumerate(columnas):
            c.drawString(posiciones[i], y, col)
        y -= altura_linea

    c.setFont(fuente, 10)
    c.drawString(margen_izq, height - 20 * mm, "Estado de Cuenta")
    c.setFont(fuente, tamanio_fuente)

    for i, col in enumerate(columnas):
        c.drawString(posiciones[i], y, col)
    y -= altura_linea

    for i in range(1, len(df), 2):
        if y < 40 * mm:
            nueva_pagina()

        c.setFillGray(0.9)
        c.rect(margen_izq - 2, y, width - 2 * margen_izq + 4, 2 * altura_linea, fill=True, stroke=False)
        c.setFillGray(0)

        for j in range(2):
            if i + j >= len(df):
                break
            fila = df.iloc[i + j]
            for k, pos in enumerate(posiciones):
                texto = str(fila[k + 1]) if k + 1 < len(fila) else ""
                c.drawString(pos, y - j * altura_linea, texto)
        y -= 2 * altura_linea

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
