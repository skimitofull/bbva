import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import black
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# Registrar fuente Arial-Narrow
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

    saldo_inicial = st.number_input("Saldo inicial:", min_value=0.0, value=0.0)
    movimientos_abonos = st.number_input("Número de abonos a agregar:", min_value=0, value=0)
    movimientos_cargos = st.number_input("Número de cargos a agregar:", min_value=0, value=0)
    total_abonos = st.number_input("Monto total de abonos:", min_value=0.0, value=0.0)
    saldo_final = st.number_input("Saldo final esperado:", min_value=0.0, value=0.0)

    if archivo_excel and st.button("Generar Excel trabajado"):
        df = pd.read_excel(archivo_excel, header=None)
        df.columns = [str(i) for i in range(df.shape[1])]

        def parse_fecha_es(fecha_txt):
            meses = {
                "ENE": "JAN", "FEB": "FEB", "MAR": "MAR", "ABR": "APR", "MAY": "MAY", "JUN": "JUN",
                "JUL": "JUL", "AGO": "AUG", "SEP": "SEP", "OCT": "OCT", "NOV": "NOV", "DIC": "DEC"
            }
            if isinstance(fecha_txt, str):
                for esp, eng in meses.items():
                    if esp in fecha_txt.upper():
                        fecha_txt = fecha_txt.upper().replace(esp, eng)
                        break
                try:
                    return pd.to_datetime(fecha_txt + "/2025", format="%d/%b/%Y")
                except:
                    return pd.NaT
            return pd.NaT

        df["fecha_dt"] = df["1"].apply(parse_fecha_es)
        df["cargos"] = pd.to_numeric(df["4"], errors="coerce").fillna(0)
        df["abonos"] = pd.to_numeric(df["5"], errors="coerce").fillna(0)

        # Reconstrucción por bloques de 5 filas
        bloques = []
        i = 0
        while i < len(df):
            bloque = df.iloc[i:i+5]
            if len(bloque) == 5:
                bloques.append(bloque)
            i += 5

        bloques_info = []
        for idx, b in enumerate(bloques):
            fecha = b.iloc[0]["1"]
            fecha_dt = parse_fecha_es(fecha)
            bloques_info.append((fecha_dt, idx, b))

        bloques_ordenados = sorted(bloques_info, key=lambda x: (x[0], x[1]))

        saldo = saldo_inicial
        filas_finales = []
        for i, (fecha, _, bloque) in enumerate(bloques_ordenados):
            cargos = pd.to_numeric(bloque["4"], errors="coerce").fillna(0).sum()
            abonos = pd.to_numeric(bloque["5"], errors="coerce").fillna(0).sum()
            saldo = max(0, saldo - cargos + abonos)

            siguiente_fecha = bloques_ordenados[i + 1][0] if i + 1 < len(bloques_ordenados) else None
            mostrar_saldo = fecha != siguiente_fecha

            for j in range(len(bloque)):
                fila = bloque.iloc[j].copy()
                fila["6"] = f"{saldo:,.2f}" if mostrar_saldo and j == len(bloque) - 1 else ""
                fila["7"] = fila["6"]
                filas_finales.append(fila)

        df_resultado = pd.DataFrame(filas_finales)
        archivo_final = "estado_bancario_excel_corregido_final.xlsx"
        df_resultado.to_excel(archivo_final, index=False, header=False)

        with open(archivo_final, "rb") as f:
            st.download_button("Descargar Excel corregido", f, file_name=archivo_final)

if fase == "2. Convertir Excel a PDF final":
    st.info("Fase aún no integrada en esta versión del agente. Pronto disponible.")
