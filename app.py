import streamlit as st
import pandas as pd
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
        original = pd.read_excel(archivo_excel, header=None)
        original.columns = [str(i) for i in range(original.shape[1])]

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

        def extraer_bloques(df):
            bloques = []
            i = 0
            while i < len(df):
                bloque = df.iloc[i:i+5]
                if len(bloque) == 5:
                    fecha = parse_fecha_es(bloque.iloc[0]["1"])
                    bloques.append((fecha, bloque.copy()))
                i += 5
            return bloques

        bloques_originales = extraer_bloques(original)

        bancos_mexico = ["BBVA", "CITIBANAMEX", "SANTANDER", "HSBC", "SCOTIABANK", "INBURSA", "BANORTE", "BANREGIO", "AFIRME", "BANCOPPEL"]
        bancos_validos = [b for b in bancos_mexico if b.upper() not in [x.upper() for x in bancos_baneados]]

        nombres_ficticios = ["JUAN PÉREZ", "ANA LÓPEZ", "MARIO RAMÍREZ", "LILIANA GARCÍA", "ALFREDO HERNÁNDEZ"]
        fechas_posibles = pd.date_range(rango_fecha[0], rango_fecha[1], freq="D")

        def generar_bloque(fecha_dt, monto, tipo):
            fecha_txt = fecha_dt.strftime("%d/%b").upper().replace("APR", "ABR")
            banco = random.choice(bancos_validos)
            concepto = "TRANSFERENCIA" if tipo == "cargo" else "BONO RECIBIDO"
            nombre = random.choice(nombres_ficticios)
            fila1 = f"SPEI {'ENVIADO' if tipo == 'cargo' else 'RECIBIDO'} {banco}"
            fila2 = f"{random.randint(1000000000,9999999999)} {random.randint(100,999)} {random.randint(1000000,9999999)}{concepto}"
            fila3 = f"{random.randint(10000000000000000000,99999999999999999999)}"
            fila4 = f"{random.randint(10000000000000000000,99999999999999999999)}"
            fila5 = nombre
            bloque = pd.DataFrame([[fecha_txt, fila1, "", "", monto if tipo == "cargo" else "", monto if tipo == "abono" else "", "", ""] for _ in range(5)], columns=[str(i) for i in range(8)])
            bloque.iloc[1, 1] = fila2
            bloque.iloc[2, 1] = fila3
            bloque.iloc[3, 1] = fila4
            bloque.iloc[4, 1] = fila5
            return (fecha_dt, bloque)

        nuevos_bloques = []

        if movimientos_abonos > 0:
            base = [random.uniform(1, 100) for _ in range(movimientos_abonos)]
            factor = total_abonos / sum(base)
            abonos_valores = [round(f * factor, 2) for f in base]
            for m in abonos_valores:
                fecha = random.choice(fechas_posibles)
                nuevos_bloques.append(generar_bloque(fecha, m, "abono"))

        if movimientos_cargos > 0:
            total_cargos = saldo_inicial + total_abonos - saldo_final
            base = [random.uniform(1, 100) for _ in range(movimientos_cargos)]
            factor = total_cargos / sum(base)
            cargos_valores = [round(f * factor, 2) for f in base]
            for m in cargos_valores:
                fecha = random.choice(fechas_posibles)
                nuevos_bloques.append(generar_bloque(fecha, m, "cargo"))

        # Combinar, ordenar e integrar
        todos_bloques = bloques_originales + nuevos_bloques
        todos_bloques.sort(key=lambda x: x[0])

        df_final = pd.DataFrame()
        saldo_actual = saldo_inicial

        for i, (fecha, bloque) in enumerate(todos_bloques):
            bloque_cargos = pd.to_numeric(bloque["4"], errors="coerce").fillna(0).sum()
            bloque_abonos = pd.to_numeric(bloque["5"], errors="coerce").fillna(0).sum()
            saldo_actual = max(0, saldo_actual - bloque_cargos + bloque_abonos)

            siguiente_fecha = todos_bloques[i+1][0] if i + 1 < len(todos_bloques) else None
            mostrar_saldo = fecha != siguiente_fecha
            bloque["6"] = bloque["7"] = ""
            if mostrar_saldo:
                bloque.iloc[-1, 6] = bloque.iloc[-1, 7] = f"{saldo_actual:,.2f}"

            df_final = pd.concat([df_final, bloque], ignore_index=True)

        archivo_final = "estado_bancario_excel_corregido_final.xlsx"
        df_final.to_excel(archivo_final, index=False, header=False)

        with open(archivo_final, "rb") as f:
            st.download_button("Descargar Excel corregido", f, file_name=archivo_final)

if fase == "2. Convertir Excel a PDF final":
    st.info("Fase aún no integrada en esta versión del agente. Pronto disponible.")
