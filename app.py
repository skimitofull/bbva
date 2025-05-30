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
from datetime import datetime, timedelta
import random

# Registrar fuente Arial-Narrow desde archivo TTF local
try:
    pdfmetrics.registerFont(TTFont('Arial-Narrow', 'fonts/arialn.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Narrow-Italic', 'fonts/arialni.ttf'))
except Exception as e:
    st.error(f"Error al cargar las fuentes Arial Narrow: {e}")
    st.stop()

st.title("Generador de Estado de Cuenta Bancario (PDF Ficticio)")

fase = st.radio("Selecciona la fase del proceso:", ["1. Generar Excel trabajado", "2. Convertir Excel a PDF final"])

if fase == "1. Generar Excel trabajado":
    archivo_excel = st.file_uploader("Sube el archivo Excel original", type=["xlsx"])
    saldo_inicial = st.number_input("Saldo inicial", min_value=0.0, format="%.2f")
    num_abonos = st.number_input("Número de movimientos de abonos a agregar", min_value=0, step=1)
    num_cargos = st.number_input("Número de movimientos de cargos a agregar", min_value=0, step=1)
    total_abonos = st.number_input("Total deseado de abonos (incluye originales + nuevos)", min_value=0.0, format="%.2f")
    saldo_final = st.number_input("Saldo final esperado", min_value=0.0, format="%.2f")

    if archivo_excel and st.button("Generar Excel trabajado"):
        st.success("Parámetros recibidos. Iniciaremos el procesamiento del archivo.")
        # Aquí se insertará el código para generar el Excel trabajado según los parámetros
        # Este código se implementará en los siguientes pasos del desarrollo

elif fase == "2. Convertir Excel a PDF final":
    archivo_final = st.file_uploader("Sube el archivo Excel trabajado para convertir a PDF", type=["xlsx"])

    if archivo_final and st.button("Generar PDF final"):
        df = pd.read_excel(archivo_final, header=None)
        pdf_buffer = generar_pdf(df)
        st.success("PDF generado correctamente.")
        st.download_button("Descargar PDF", data=pdf_buffer, file_name="estado_cuenta_final.pdf", mime="application/pdf")

# Función para generar el PDF con formato replicado al original
def generar_pdf(df):
    def es_nueva_linea_movimiento(row):
        return pd.notna(row[1]) or pd.notna(row[2])  # FECHA OPER o LIQ

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

    saldo = 262776.23  # Saldo inicial fijo
    movimientos_por_fecha = {}

    for bloque in filas:
        fecha = bloque[0][1]  # FECHA OPER
        movimientos_por_fecha.setdefault(fecha, []).append(bloque)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margen_izq = 10 * mm
    margen_sup = height - 33 * mm
    altura_linea = 3.8 * mm  # Espaciado ajustado
    fuente_regular = "Arial-Narrow"
    fuente_italic = "Arial-Narrow-Italic"

    columnas = ["OPER", "LIQ", "DESCRIPCIÓN", "REFERENCIA", "CARGOS", "ABONOS", "OPERACIÓN", "LIQUIDACIÓN"]
    posiciones = [5.658 * mm, 17.967 * mm, 29.069 * mm, 0 * mm, 137.904 * mm, 151.354 * mm, 175.228 * mm, 199.118 * mm]

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

    for fecha in sorted(movimientos_por_fecha.keys()):
        bloques = movimientos_por_fecha[fecha]
        for idx, bloque in enumerate(bloques):
            if y < (len(bloque) + 1) * altura_linea:
                nueva_pagina()
            for i, row in enumerate(bloque):
                fuente_actual = fuente_italic if i == 1 else fuente_regular
                c.setFont(fuente_actual, 9.5)

                cargo = float(row[4]) if pd.notna(row[4]) else 0
                abono = float(row[5]) if pd.notna(row[5]) else 0
                saldo = max(0, saldo - cargo + abono)  # nunca negativo

                for k, pos in enumerate(posiciones):
                    texto = ""
                    if k < len(row) and pd.notna(row[k]) and str(row[k]).lower() != "nan":
                        texto = str(row[k])
                    if (idx == len(bloques) - 1) and (i == len(bloque) - 1) and k in [6, 7]:
                        texto = f"{saldo:,.2f}"
                    c.drawString(pos, y, texto)
                y -= altura_linea

    c.save()
    buffer.seek(0)
    return buffer
