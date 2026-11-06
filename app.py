import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ReverseMilk – Planejamento Reverso",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('''
<style>
    .stApp { background-color: #12161F; color: #E0E6ED; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0A0D14; border-right: 1px solid #1E2638; }
    .kpi-card { background-color: #1A2130; border-radius: 10px; padding: 15px 20px; border-left: 4px solid #1E88E5; box-shadow: 0 4px 12px rgba(0,0,0,0.3); margin-bottom: 10px; }
    .kpi-title { font-size: 0.85rem; color: #94A3B8; font-weight: 600; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #FFFFFF; margin-top: 5px; }
    .kpi-crit { border-left-color: #EF4444; }
    .kpi-success { border-left-color: #10B981; }
    .kpi-warn { border-left-color: #F59E0B; }
</style>
''', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# GERAÇÃO SINTÉTICA DE DADOS
# ------------------------------------------------------------------------------
@st.cache_data
def carregar_dados_sinteticos(n_ordens=40):
    np.random.seed(42)
    produtos = ["Leite Zero Lactose", "Queijo Prato", "Iogurte Natural", "Leite UHT Integral"]
    rotas = {
        "Leite Zero Lactose": [("Liberação", 30, "Recepção"), ("Pasteurização", 45, "Pasteurizador 1"), ("Transferência", 20, "Sistema Pulmão"), ("Hidrólise enzimática", 240, "Tanque hidrólise"), ("Formulação", 60, "Tanque formulação"), ("Qualidade", 90, "Laboratório")],
        "Queijo Prato": [("Liberação", 30, "Recepção"), ("Pasteurização", 45, "Pasteurizador 2"), ("Coagulação e corte", 60, "Tanque Queijo"), ("Prensagem", 120, "Prensa Automática"), ("Salga", 240, "Tanque Salga"), ("Qualidade", 90, "Laboratório")],
        "Iogurte Natural": [("Liberação", 30, "Recepção"), ("Pasteurização", 40, "Pasteurizador 1"), ("Inoculação e Fermentação", 300, "Tanque Fermentação"), ("Resfriamento", 60, "Trocador Placas"), ("Qualidade", 60, "Laboratório")],
        "Leite UHT Integral": [("Liberação", 30, "Recepção"), ("Padronização", 30, "Padronizadora"), ("Tratamento UHT", 45, "Esterilizador UHT"), ("Envasamento Asséptico", 120, "Envasadora"), ("Qualidade", 60, "Laboratório")]
    }
    
    data_base = datetime(2026, 10, 5, 8, 0)
    ordens = []
    
    for i in range(1, n_ordens + 1):
        prod = np.random.choice(produtos)
        rota = rotas[prod]
        duracao_padrao = sum(d for _, d, _ in rota)
        hora_inicio = data_base + timedelta(hours=int(np.random.randint(0, 36)))
        prazo_entrega = hora_inicio + timedelta(minutes=int(duracao_padrao + np.random.choice([30, 60, 90, 120])))
        
        ordens.append({
            "op_id": f"OP-10{i:02d}", "produto": prod,
            "inicio_planejado": hora_inicio,
            "prazo_entrega": prazo_entrega,
            "status": "NORMAL"
        })
        
    return pd.DataFrame(ordens), rotas

# ------------------------------------------------------------------------------
# SIMULAÇÃO DE MONTE CARLO NATIVA (SEM PANDAS QUANTILE - À PROVA DE ERROS)
# ------------------------------------------------------------------------------
def executar_monte_carlo(op_row, rota_etapas, n_simulacoes=1000):
    np.random.seed(42)
    # Garante que as datas são tratadas como objetos de Python puros
    inicio = pd.to_datetime(op_row['inicio_planejado']).to_pydatetime()
    prazo = pd.to_datetime(op_row['prazo_entrega']).to_pydatetime()
    
    duracoes = np.zeros(n_simulacoes)
    for etapa, dur, rec in rota_etapas:
        if "hidrólise" in etapa.lower() or "fermentação" in etapa.lower():
            duracoes += np.random.lognormal(mean=(np.log(dur)-0.03), sigma=0.25, size=n_simulacoes)
        else:
            duracoes += np.random.triangular(left=dur*0.9, mode=dur, right=dur*1.3, size=n_simulacoes)
            
    # Cria uma lista de datas de conclusão
    conclusoes = [inicio + timedelta(minutes=float(d)) for d in duracoes]
    
    # 🟢 A CORREÇÃO: Usar sort() em vez de .quantile(). Nunca dá erro de AttributeError ou TypeError!
    conclusoes_ordenadas = sorted(conclusoes)
    p50_dt = conclusoes_ordenadas[int(n_simulacoes * 0.5)]
    p90_dt = conclusoes_ordenadas[int(n_simulacoes * 0.9)]
    
    atrasos = [(c - prazo).total_seconds() / 60.0 for c in conclusoes]
    prob_atraso = sum(1 for a in atrasos if a > 0) / n_simulacoes * 100.0
    
    return p50_dt, p90_dt, prob_atraso, prazo

# ------------------------------------------------------------------------------
# INTERFACE E LÓGICA PRINCIPAL
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("🥛 ReverseMilk")
    st.markdown("---")
    n_ordens = st.number_input("Nº de ordens (sintéticas)", 10, 100, 40)

df_ordens, rotas = carregar_dados_sinteticos(n_ordens)

st.title("ReverseMilk – Simulação e Planeamento")
tab1, tab2, tab3 = st.tabs(["🚦 Painel Geral", "📊 Simulação Monte Carlo", "⏪ Agendamento Reverso"])

with tab1:
    tot_ativas = len(df_ordens)
    col1, col2 = st.columns(2)
    with col1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">OPS ATIVAS</div><div class="kpi-value">{tot_ativas}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="kpi-card kpi-success"><div class="kpi-title">STATUS DO SISTEMA</div><div class="kpi-value">ONLINE</div></div>', unsafe_allow_html=True)
    st.dataframe(df_ordens, use_container_width=True)

with tab2:
    op_sel_str = st.selectbox("Selecione a Ordem (OP):", df_ordens['op_id'].astype(str) + " - " + df_ordens['produto'])
    op_sel_id = op_sel_str.split(" - ")[0]
    op_row = df_ordens[df_ordens['op_id'] == op_sel_id].iloc[0]
    rota_sel = rotas[op_row['produto']]
    
    # Executa a simulação refatorada
    p50_dt, p90_dt, prob_atraso, prazo_final = executar_monte_carlo(op_row, rota_sel, 1000)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prazo Final", prazo_final.strftime('%d/%m %H:%M'))
    c2.metric("P50 (Provável)", p50_dt.strftime('%d/%m %H:%M'))
    c3.metric("P90 (Seguro)", p90_dt.strftime('%d/%m %H:%M'))
    c4.metric("Probabilidade Atraso", f"{prob_atraso:.1f}%")

with tab3:
    st.header("Cálculo Reverso")
    prod_rev = st.selectbox("Produto", list(rotas.keys()))
    dt = st.date_input("Data Entrega", datetime(2026, 10, 6))
    hr = st.time_input("Hora Entrega", datetime(2026, 10, 6, 18, 0).time())
    
    dt_hr_entrega = datetime.combine(dt, hr)
    dur_total = sum(d for _, d, _ in rotas[prod_rev])
    
    st.success(f"O processo deve começar até: {(dt_hr_entrega - timedelta(minutes=dur_total)).strftime('%d/%m %H:%M')}")
