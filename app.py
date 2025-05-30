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
    if archivo_excel:
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
        df["es_ultima"] = (df["fecha_dt"] != df["fecha_dt"].shift(-1)) & df["fecha_dt"].notna()

        saldo = 262776.23
        saldos = []
        for i, row in df.iterrows():
            saldo = saldo - row["cargos"] + row["abonos"]
            saldo = max(0, saldo)
            saldos.append(saldo if row["es_ultima"] else "")

        df["6"] = [f"{s:,.2f}" if isinstance(s, float) else "" for s in saldos]
        df["7"] = df["6"]

        archivo_final = "estado_bancario_excel_corregido_final.xlsx"
        df.drop(columns=["fecha_dt", "cargos", "abonos", "es_ultima"]).to_excel(archivo_final, index=False, header=False)

        with open(archivo_final, "rb") as f:
            st.download_button("Descargar Excel corregido", f, file_name=archivo_final)

if fase == "2. Convertir Excel a PDF final":
    st.info("Fase aún no integrada en esta versión del agente. Pronto disponible.")
