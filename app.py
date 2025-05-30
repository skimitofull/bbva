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
        df = pd.read_excel(archivo_excel, header=None)
        df.columns = [str(i) for i in range(df.shape[1])]

        def parse_fecha_es(fecha_txt):
            meses = {"ENE": "JAN", "FEB": "FEB", "MAR": "MAR", "ABR": "APR", "MAY": "MAY", "JUN": "JUN",
                     "JUL": "JUL", "AGO": "AUG", "SEP": "SEP", "OCT": "OCT", "NOV": "NOV", "DIC": "DEC"}
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

        abonos_actuales = df["abonos"].sum()
        cargos_actuales = df["cargos"].sum()

        abonos_faltantes = round(total_abonos - abonos_actuales, 2)
        cargos_faltantes = round((saldo_inicial + total_abonos - saldo_final) - cargos_actuales, 2)

        fecha_base = datetime(2025, 4, 1)

        def fecha_random():
            return (fecha_base + timedelta(days=random.randint(0, 29))).strftime("%d/%b").upper().replace("APR", "ABR")

        def generar_bloque(fecha, monto, tipo):
            nombre = random.choice(["JUAN PÉREZ", "MARÍA LÓPEZ", "CARLOS RAMÍREZ", "ANA HERNÁNDEZ"])
            descripcion = f"SPEI {'RECIBIDO' if tipo == 'abono' else 'ENVIADO'} BBVA"
            cuenta = f"012{random.randint(1000,9999)}{random.randint(10000000,99999999)}"
            referencia = f"{random.randint(100000000000000000,999999999999999999)}"
            concepto = "TRANSFERENCIA ELECTRÓNICA"
            fila1 = [None]*9; fila1[1] = fecha; fila1[2] = descripcion; fila1[5 if tipo=='abono' else 4] = monto
            fila2 = [None]*9; fila2[2] = f"{random.randint(1000000000,9999999999)} 012 0001 {concepto}"
            fila3 = [None]*9; fila3[2] = cuenta
            fila4 = [None]*9; fila4[2] = referencia
            fila5 = [None]*9; fila5[2] = nombre
            return [fila1, fila2, fila3, fila4, fila5]

        nuevos_bloques = []
        restante = abonos_faltantes
        for _ in range(num_abonos - 1):
            monto = round(random.uniform(10000, restante / 2), 2)
            nuevos_bloques.extend(generar_bloque(fecha_random(), monto, "abono"))
            restante -= monto
        nuevos_bloques.extend(generar_bloque(fecha_random(), round(restante, 2), "abono"))

        restante = cargos_faltantes
        for _ in range(num_cargos - 1):
            monto = round(random.uniform(10000, restante / 2), 2)
            nuevos_bloques.extend(generar_bloque(fecha_random(), monto, "cargo"))
            restante -= monto
        nuevos_bloques.extend(generar_bloque(fecha_random(), round(restante, 2), "cargo"))

        df_nuevos = pd.DataFrame(nuevos_bloques, columns=[str(i) for i in range(9)])
        df_comb = pd.concat([df, df_nuevos], ignore_index=True)
        df_comb["fecha_dt"] = df_comb["1"].apply(parse_fecha_es)
        df_comb = df_comb.sort_values(by="fecha_dt", kind="mergesort")

        df_comb.drop(columns=["fecha_dt", "cargos", "abonos"], errors="ignore").to_excel(
            "estado_trabajado_generado.xlsx", index=False, header=False)

        with open("estado_trabajado_generado.xlsx", "rb") as f:
            st.download_button("Descargar Excel trabajado", f, file_name="estado_trabajado_generado.xlsx")
