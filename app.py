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
import random

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
    rango_fecha = st.date_input("Rango de fechas para los movimientos agregados", value=(datetime(2025, 4, 1), datetime(2025, 4, 30)))
    bancos_baneados = st.text_area("Lista de bancos a excluir (uno por línea)").splitlines()

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

        bancos_mexico = ["BBVA", "CITIBANAMEX", "SANTANDER", "HSBC", "SCOTIABANK", "INBURSA", "BANORTE", "BANREGIO", "AFIRME", "BANCOPPEL"]
        bancos_validos = [b for b in bancos_mexico if b.upper() not in [x.upper() for x in bancos_baneados]]

        def generar_bloque(fecha, monto, tipo):
            banco = random.choice(bancos_validos)
            concepto = "TRANSFERENCIA" if tipo == "cargo" else "BONO RECIBIDO"
            nombre = random.choice(["JUAN PÉREZ", "ANA LÓPEZ", "MARIO RAMÍREZ", "LILIANA GARCÍA", "ALFREDO HERNÁNDEZ"])
            fila1 = f"SPEI {'ENVIADO' if tipo == 'cargo' else 'RECIBIDO'} {banco}"
            fila2 = f"{random.randint(1000000000,9999999999)} {random.randint(100,999)} {random.randint(1000000,9999999)}{concepto}"
            fila3 = f"{random.randint(10000000000000000000,99999999999999999999)}"
            fila4 = f"{random.randint(10000000000000000000,99999999999999999999)}"
            fila5 = nombre
            bloque = pd.DataFrame([[fecha, fila1, "", "", monto if tipo == "cargo" else "", monto if tipo == "abono" else "", "", ""] for _ in range(5)], columns=[str(i) for i in range(8)])
            bloque.iloc[1, 1] = fila2
            bloque.iloc[2, 1] = fila3
            bloque.iloc[3, 1] = fila4
            bloque.iloc[4, 1] = fila5
            return bloque

        # Generar bloques simulados
        fechas_posibles = pd.date_range(rango_fecha[0], rango_fecha[1], freq="D")
        nuevos_bloques = []

        if movimientos_abonos > 0:
            montos_abonos = sorted(random.sample(range(10000, int(total_abonos)), movimientos_abonos - 1))
            montos_abonos = [montos_abonos[0]] + [j - i for i, j in zip(montos_abonos[:-1], montos_abonos[1:])] + [int(total_abonos) - montos_abonos[-1]]
            for monto in montos_abonos:
                fecha = random.choice(fechas_posibles).strftime("%d/%b").upper().replace("APR", "ABR")
                nuevos_bloques.append(generar_bloque(fecha, f"{monto:,.2f}", "abono"))

        if movimientos_cargos > 0:
            total_cargos = saldo_inicial + total_abonos - saldo_final
            montos_cargos = sorted(random.sample(range(10000, int(total_cargos)), movimientos_cargos - 1))
            montos_cargos = [montos_cargos[0]] + [j - i for i, j in zip(montos_cargos[:-1], montos_cargos[1:])] + [int(total_cargos) - montos_cargos[-1]]
            for monto in montos_cargos:
                fecha = random.choice(fechas_posibles).strftime("%d/%b").upper().replace("APR", "ABR")
                nuevos_bloques.append(generar_bloque(fecha, f"{monto:,.2f}", "cargo"))

        # Insertar nuevos movimientos y ordenar
        for bloque in nuevos_bloques:
            df = pd.concat([df, bloque], ignore_index=True)

        df["fecha_dt"] = df["1"].apply(parse_fecha_es)
        df.sort_values("fecha_dt", inplace=True)
        df.reset_index(drop=True, inplace=True)

        df["cargos"] = pd.to_numeric(df["4"], errors="coerce").fillna(0)
        df["abonos"] = pd.to_numeric(df["5"], errors="coerce").fillna(0)
        df["es_ultima"] = (df["fecha_dt"] != df["fecha_dt"].shift(-1)) & df["fecha_dt"].notna()

        saldo = saldo_inicial
        saldos = []
        for i, row in df.iterrows():
            saldo = saldo - row["cargos"] + row["abonos"]
            saldo = max(0, saldo)
            saldos.append(saldo if row["es_ultima"] else "")

        df["6"] = [f"{s:,.2f}" if isinstance(s, float) else "" for s in saldos]
        df["7"] = df["6"]

        archivo_final = "estado_bancario_excel_corregido_final.xlsx"
        df.drop(columns=["fecha_dt", "cargos", "abonos", "es_ultima"], errors="ignore").to_excel(archivo_final, index=False, header=False)

        with open(archivo_final, "rb") as f:
            st.download_button("Descargar Excel corregido", f, file_name=archivo_final)

if fase == "2. Convertir Excel a PDF final":
    st.info("Fase aún no integrada en esta versión del agente. Pronto disponible.")
