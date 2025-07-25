import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px

# -------------------- CONFIGURAÇÕES --------------------

st.set_page_config(page_title="Acompanhamento de Análise", layout="wide")
st.title("📊 Acompanhamento de Análise - Clandestinos MA")

# -------------------- SIDEBAR: UPLOAD --------------------

st.sidebar.title("🔧 Configurações")
arquivos = st.sidebar.file_uploader(
    "📁 Carregue arquivos JSON",
    type="json",
    accept_multiple_files=True
)

# Valida se há arquivos carregados
if not arquivos:
    st.sidebar.warning("Por favor, carregue pelo menos um arquivo JSON.")
    st.stop()

# -------------------- DATAS --------------------

data_hoje = datetime.today()
data_entrega = datetime(2025, 8, 19)
dias_corridos_restantes = (data_entrega - data_hoje).days + 1
dias_uteis_restantes = np.busday_count(data_hoje.date(), data_entrega.date() + timedelta(days=1))

# -------------------- LEITURA DOS JSONS --------------------

items = []

for arquivo in arquivos:
    data = json.load(arquivo)
    for checklist in data.get("checklists", []):
        nome_checklist = checklist.get("name", "Sem nome")

        for item in checklist.get("checkItems", []):
            nome_item = item.get("name", "").strip()
            partes = nome_item.split('\t')

            cidade = partes[0].strip() if len(partes) > 0 else None
            pontos = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 0

            items.append({
                "Checklist": nome_checklist,
                "Cidade": cidade,
                "Pontos": pontos,
                "Concluído": item.get("state") == "complete"
            })

# Criar DataFrame
df = pd.DataFrame(items)

# -------------------- KPIs --------------------

total_pontos = df["Pontos"].sum()
pontos_concluidos = df[df["Concluído"] == True]["Pontos"].sum()
pontos_pendentes = total_pontos - pontos_concluidos
percentual = round((pontos_concluidos / total_pontos) * 100, 1) if total_pontos > 0 else 0

dias_uteis_restantes = max(dias_uteis_restantes, 1)
dias_corridos_restantes = max(dias_corridos_restantes, 1)

pontos_dia_util = int(pontos_pendentes / dias_uteis_restantes)
pontos_dia_corridos = int(pontos_pendentes / dias_corridos_restantes)

# Número fixo de pessoas
num_pessoas = 4

pontos_por_pessoa_corridos = int(pontos_dia_corridos / num_pessoas)
pontos_por_pessoa_uteis = int(pontos_dia_util / num_pessoas)

# -------------------- LAYOUT SUPERIOR --------------------

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("✅ % Concluído", f"{percentual} %")
col2.metric("📅 Data de Entrega", data_entrega.strftime("%d/%m/%Y"))
col3.metric("🗓️ Dias Corridos Restantes", dias_corridos_restantes)
col4.metric("📆 Dias Úteis Restantes", dias_uteis_restantes)
col5.metric("👥 Pessoas Envolvidas", num_pessoas)

# -------------------- TABELA DE MÉDIAS --------------------

st.markdown("### 📌 Pontos por Dia")

col_tabela = st.container()
col_pizza = st.container()

# Corrigido: criar DataFrame corretamente com 2 linhas
df_dias = pd.DataFrame([
    {
        "Base": "Dias Corridos",
        "Pontos Totais": pontos_pendentes,
        "Pontos/dia": pontos_dia_corridos,
        "Pontos por Pessoa/dia": pontos_por_pessoa_corridos
    },
    {
        "Base": "Dias Úteis",
        "Pontos Totais": pontos_pendentes,
        "Pontos/dia": pontos_dia_util,
        "Pontos por Pessoa/dia": pontos_por_pessoa_uteis
    }
])

with col_tabela:
    st.dataframe(df_dias, use_container_width=True, height=120)

# -------------------- GRÁFICO DE PIZZA --------------------

with col_pizza:
    fig_pizza = px.pie(
        names=["Pendente", "Concluído"],
        values=[pontos_pendentes, pontos_concluidos],
        title="Distribuição dos Pontos",
        color_discrete_sequence=["#28a745", "#dc3545"]
    )

    # Mostrar apenas o valor no rótulo, e % no hover
    fig_pizza.update_traces(
        textinfo='value',
        hovertemplate='%{label}: %{value} pontos (%{percent})<extra></extra>'
    )

    st.plotly_chart(fig_pizza, use_container_width=True)

# -------------------- TABELA DETALHADA --------------------

st.markdown("### 📋 Checklist Detalhado")

df_tabela = df[["Cidade", "Pontos", "Concluído"]].sort_values(by="Pontos", ascending=False)
st.dataframe(df_tabela, use_container_width=True, height=400)
