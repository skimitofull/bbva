import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import black
from io import BytesIO
import base64
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Registrar fuente Arial-Narrow desde archivo TTF local
try:
    pdfmetrics.registerFont(TTFont('Arial-Narrow', 'fonts/arialn.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Narrow-Italic', 'fonts/arialni.ttf'))
except Exception as e:
    # Manejo de error al cargar fuentes
    st.error(f"Error al cargar las fuentes Arial Narrow: {e}")
    st.stop()

# Función para generar el PDF con formato replicado al original
def generar_pdf(df):
    filas = []
    bloque = []
    fecha_detectada = lambda r: pd.notna(r[1]) and isinstance(r[1], str) and "/" in r[1]

    for _, row in df.iterrows():
        if fecha_detectada(row) and bloque:
            filas.append(bloque)
            bloque = []
        bloque.append(row)
    if bloque:
        filas.append(bloque)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margen_izq = 10 * mm
    margen_sup = height - 33 * mm
    altura_linea = 3.8 * mm  # Espaciado ajustado
    fuente_regular = "Arial-Narrow"
    fuente_italic = "Arial-Narrow-Italic"

    columnas = ["OPER", "LIQ", "DESCRIPCIÓN", "REFERENCIA", "CARGOS", "ABONOS", "OPERACIÓN", "LIQUIDACIÓN"]
    posiciones = [14 * mm, 30 * mm, 45 * mm, 87 * mm, 124 * mm, 144 * mm, 164 * mm, 184 * mm]

    def encabezado(y_pos):
        c.setFillColor(black)
        c.setFont(fuente_regular, 9.5)
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

    for bloque in filas:
        if y < (len(bloque) + 1) * altura_linea:
            nueva_pagina()
        for i, row in enumerate(bloque):
            fuente_actual = fuente_italic if i > 0 else fuente_regular
            c.setFont(fuente_actual, 9.5)
            for k, pos in enumerate(posiciones):
                texto = str(row[k]) if k < len(row) and pd.notna(row[k]) else ""
                c.drawString(pos, y, texto)
            y -= altura_linea

    c.save()
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Generador de Estado de Cuenta Ficticio")
st.write("Sube un archivo Excel con la estructura original del estado de cuenta")

archivo = st.file_uploader("Cargar archivo Excel", type=[".xlsx"])

if archivo:
    df_raw = pd.read_excel(archivo, engine="openpyxl")

    def transformar_formato_original(df):
        filas = []
        encabezados = df.iloc[0].tolist()
        temp = [None] * len(encabezados)
        for i in range(1, len(df)):
            fila = df.iloc[i]
            if pd.notna(fila[1]):
                if any(pd.notna(v) for v in temp):
                    filas.append(temp)
                temp = fila.tolist()
            else:
                for j in range(len(temp)):
                    if pd.isna(temp[j]) and pd.notna(fila[j]):
                        temp[j] = fila[j]
        if any(pd.notna(v) for v in temp):
            filas.append(temp)
        return pd.DataFrame(filas, columns=encabezados)

    df = transformar_formato_original(df_raw)
    pdf_buffer = generar_pdf(df)

    st.download_button(label="Descargar Estado de Cuenta PDF",
                       data=pdf_buffer,
                       file_name="estado_de_cuenta.pdf",
                       mime="application/pdf")

    base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")
    pdf_display = f'''
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="700px"
            type="application/pdf">
        </iframe>
    '''
    st.markdown("### Vista previa del PDF generado")
    st.components.v1.html(pdf_display, height=700, scrolling=True)
