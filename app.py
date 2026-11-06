import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM (DARK EXECUTIVO)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ReverseMilk – Planejamento Reverso e Simulação de Cenários",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Customizada (Dark Executive Theme)
st.markdown('''
<style>
    .stApp { background-color: #12161F; color: #E0E6ED; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0A0D14; border-right: 1px solid #1E2638; }
    .kpi-card { background-color: #1A2130; border-radius: 10px; padding: 15px 20px; border-left: 4px solid #1E88E5; box-shadow: 0 4px 12px rgba(0,0,0,0.3); margin-bottom: 10px; }
    .kpi-title { font-size: 0.85rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #FFFFFF; margin-top: 5px; }
    .kpi-sub { font-size: 0.8rem; color: #38BDF8; margin-top: 3px; }
    .kpi-crit { border-left-color: #EF4444; }
    .kpi-success { border-left-color: #10B981; }
    .kpi-warn { border-left-color: #F59E0B; }
    .stSlider > div > div > div > div { background-color: #1E88E5 !important; }
    .stRadio > label { color: #00E5FF !important; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #0A0D14; padding: 8px; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #1A2130; border-radius: 6px; color: #94A3B8; font-weight: 600; border: none; }
    .stTabs [aria-selected="true"] { background-color: #1E88E5 !important; color: #FFFFFF !important; }
</style>
''', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FUNÇÕES AUXILIARES ROBUSTAS (ZERO ATTRIBUTEERROR)
# ------------------------------------------------------------------------------
def formatar_data_segura(val, formato='%d/%m %H:%M'):
    if val is None or pd.isna(val):
        return "N/A"
    try:
        ts = pd.to_datetime(val)
        return ts.strftime(formato)
    except Exception:
        return str(val)[:16]

def obter_campo_seguro(obj, chave, padrao=None):
    if obj is None: return padrao
    if isinstance(obj, dict): return obj.get(chave, padrao)
    return getattr(obj, chave, padrao)

# ------------------------------------------------------------------------------
# GERAÇÃO E CARREGAMENTO DE DADOS SINTÉTICOS
# ------------------------------------------------------------------------------
@st.cache_data
def carregar_dados_sinteticos(n_ordens=40):
    np.random.seed(42)
    produtos = ["Leite Zero Lactose", "Queijo Prato", "Iogurte Natural", "Leite UHT Integral"]
    
    rotas = {
        "Leite Zero Lactose": [("Liberação da matéria-prima", 30, "Recepção"), ("Pasteurização", 45, "Pasteurizador 1"), ("Transferência", 20, "Sistema Pulmão"), ("Hidrólise enzimática", 240, "Tanque hidrólise"), ("Formulação", 60, "Tanque formulação"), ("Liberação da qualidade", 90, "Laboratório")],
        "Queijo Prato": [("Liberação da matéria-prima", 30, "Recepção"), ("Pasteurização", 45, "Pasteurizador 2"), ("Coagulação e corte", 60, "Tanque Queijo"), ("Prensagem", 120, "Prensa Automática"), ("Salga", 240, "Tanque Salga"), ("Liberação da qualidade", 90, "Laboratório")],
        "Iogurte Natural": [("Liberação da matéria-prima", 30, "Recepção"), ("Pasteurização", 40, "Pasteurizador 1"), ("Inoculação e Fermentação", 300, "Tanque Fermentação"), ("Resfriamento", 60, "Trocador Placas"), ("Liberação da qualidade", 60, "Laboratório")],
        "Leite UHT Integral": [("Liberação da matéria-prima", 30, "Recepção"), ("Padronização", 30, "Padronizadora"), ("Tratamento UHT", 45, "Esterilizador UHT"), ("Envasamento Asséptico", 120, "Envasadora"), ("Liberação da qualidade", 60, "Laboratório")]
    }
    
    data_base = datetime(2026, 10, 5, 8, 0)
    ordens = []
    
    for i in range(1, n_ordens + 1):
        op_id = f"OP-10{i:02d}"
        prod = np.random.choice(produtos)
        rota = rotas[prod]
        duracao_padrao_total = sum(d for _, d, _ in rota)
        
        hora_inicio_planejada = data_base + timedelta(hours=int(np.random.randint(0, 36)))
        prazo_entrega = hora_inicio_planejada + timedelta(minutes=int(duracao_padrao_total + np.random.choice([30, 60, 90, 120])))
        
        fator_desvio = float(np.random.lognormal(mean=0.05, sigma=0.15))
        duracao_real_total = int(duracao_padrao_total * fator_desvio)
        
        atraso_proj = (hora_inicio_planejada + timedelta(minutes=duracao_real_total)) - prazo_entrega
        atraso_min = max(0, int(atraso_proj.total_seconds() / 60))
        
        prob_atraso = min(99.0, max(5.0, (atraso_min / 60.0) * 35.0 + float(np.random.uniform(5, 20))))
        status = "CRÍTICO" if prob_atraso > 70 else ("ATENÇÃO" if prob_atraso > 30 else "NORMAL")
        
        ordens.append({
            "op_id": op_id,
            "produto": prod,
            "inicio_planejado": pd.to_datetime(hora_inicio_planejada),
            "prazo_entrega": pd.to_datetime(prazo_entrega),
            "duracao_padrao_min": duracao_padrao_total,
            "duracao_real_min": duracao_real_total,
            "prob_atraso_pct": round(prob_atraso, 1),
            "status": status,
            "desvio_min": duracao_real_total - duracao_padrao_total,
            "etapas_concluidas": int(np.random.randint(1, len(rota) + 1)),
            "total_etapas": len(rota)
        })
        
    return pd.DataFrame(ordens), rotas

# ------------------------------------------------------------------------------
# SIMULAÇÃO DE MONTE CARLO ROBUSTA
# ------------------------------------------------------------------------------
def executar_monte_carlo(op_row, rota_etapas, n_simulacoes=1000, seed=42):
    np.random.seed(seed)
    
    inicio = pd.to_datetime(op_row['inicio_planejado'])
    prazo = pd.to_datetime(op_row['prazo_entrega'])
    
    duracoes_totais = np.zeros(n_simulacoes)
    for nome_etapa, dur_padrao, recurso in rota_etapas:
        if "hidrólise" in nome_etapa.lower() or "fermentação" in nome_etapa.lower():
            mu = np.log(dur_padrao) - 0.5 * (0.25**2)
            sim_etapa = np.random.lognormal(mean=mu, sigma=0.25, size=n_simulacoes)
        else:
            sim_etapa = np.random.triangular(left=dur_padrao * 0.9, mode=dur_padrao, right=dur_padrao * 1.3, size=n_simulacoes)
        duracoes_totais += sim_etapa
        
    conclusoes_simuladas = [inicio + pd.Timedelta(minutes=float(d)) for d in duracoes_totais]
    
    # 🟢 AQUI ESTÁ A CORREÇÃO ABSOLUTA E DEFINITIVA PARA O ERRO QUANTILE
    fim_s = pd.Series(conclusoes_simuladas)
    p50_dt = fim_s.quantile(0.5)
    p90_dt = fim_s.quantile(0.9)
    
    atrasos = [max(0.0, (c - prazo).total_seconds() / 60.0) for c in conclusoes_simuladas]
    prob_atraso = (sum(1 for a in atrasos if a > 0) / n_simulacoes) * 100.0
    
    return {
        "p50": p50_dt, "p90": p90_dt, "prob_atraso": prob_atraso, "prazo_final": prazo,
        "duracoes_totais_min": duracoes_totais, "conclusoes_dt": conclusoes_simuladas
    }

# ------------------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_column_width=True)
    else: st.title("🥛 ReverseMilk")
    st.markdown("---")
    
    modo_vis = st.radio("Modo de visualização", ["Análise completa", "Operador (simples)"])
    st.subheader("⚙️ Parâmetros Operacionais")
    horario_simulado = st.slider("Horário atual (simulado)", min_value=datetime(2026, 10, 5, 0, 0), max_value=datetime(2026, 10, 7, 0, 0), value=datetime(2026, 10, 6, 7, 0), format="DD/MM HH:mm")
    
    uploaded_file = st.file_uploader("Usar CSV próprio (opcional)", type=["csv"])
    n_ordens = st.number_input("Nº de ordens (dados sintéticos)", min_value=10, max_value=100, value=40)
    tolerancia_etapa = st.slider("Tolerância de atraso por etapa (min)", 0, 120, 30)
    folga_minima = st.slider("Folga mínima para não alertar (min)", 0, 180, 60)
    
    with st.expander("⚙️ Configurações avançadas"):
        n_simulacoes = st.selectbox("Iterações Monte Carlo", [500, 1000, 2000, 5000], index=1)
        seed_val = st.number_input("Semente Aleatória (Seed)", value=42)

if uploaded_file is not None:
    try:
        df_ordens = pd.read_csv(uploaded_file)
        for col in ['inicio_planejado', 'prazo_entrega']:
            if col in df_ordens.columns: df_ordens[col] = pd.to_datetime(df_ordens[col])
        _, rotas = carregar_dados_sinteticos(n_ordens)
    except Exception as e:
        st.sidebar.error(f"Erro ao ler CSV: {e}. Usando dados sintéticos.")
        df_ordens, rotas = carregar_dados_sinteticos(n_ordens)
else:
    df_ordens, rotas = carregar_dados_sinteticos(n_ordens)

if 'inicio_planejado' in df_ordens.columns: df_ordens['inicio_planejado'] = pd.to_datetime(df_ordens['inicio_planejado'])
if 'prazo_entrega' in df_ordens.columns: df_ordens['prazo_entrega'] = pd.to_datetime(df_ordens['prazo_entrega'])

st.title("ReverseMilk – Planejamento Reverso e Simulação")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚦 Visão geral", "📊 Linha do tempo", "⏪ Agendamento reverso", "⚡ Simular atraso", "🔍 Gargalos", "📋 Premissas"])

with tab1:
    st.header("🚦 Painel Executivo & Alertas Preventivos")
    tot_ativas = len(df_ordens)
    tot_criticas = len(df_ordens[df_ordens['status'] == 'CRÍTICO']) if 'status' in df_ordens.columns else 0
    taxa_sucesso = round((len(df_ordens[df_ordens['status'] == 'NORMAL']) / tot_ativas) * 100, 1) if 'status' in df_ordens.columns else 100.0
    desvio_medio = round(df_ordens['desvio_min'].mean(), 1) if 'desvio_min' in df_ordens.columns else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">OPS ATIVAS</div><div class="kpi-value">{tot_ativas}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="kpi-card kpi-crit"><div class="kpi-title">OPS CRÍTICAS</div><div class="kpi-value">{tot_criticas}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="kpi-card kpi-success"><div class="kpi-title">TAXA SUCESSO</div><div class="kpi-value">{taxa_sucesso}%</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="kpi-card kpi-warn"><div class="kpi-title">DESVIO MÉDIO</div><div class="kpi-value">+{desvio_medio} min</div></div>', unsafe_allow_html=True)

with tab2:
    st.header("📊 Acompanhamento Temporizado & Simulação de Monte Carlo")
    op_sel_str = st.selectbox("Selecione a Ordem de Produção (OP):", [f"{row['op_id']} - {row['produto']}" for _, row in df_ordens.iterrows()])
    op_sel_id = op_sel_str.split(" - ")[0]
    op_row = df_ordens[df_ordens['op_id'] == op_sel_id].iloc[0]
    prod_sel = op_row['produto']
    rota_sel = rotas.get(prod_sel, rotas["Leite Zero Lactose"])
    
    df_gantt = []
    curr_t = pd.to_datetime(op_row['inicio_planejado'])
    for etapa, dur, rec in rota_sel:
        fim_t = curr_t + pd.Timedelta(minutes=float(dur))
        df_gantt.append(dict(Task=etapa, Start=curr_t, Finish=fim_t, Resource=rec))
        curr_t = fim_t
    
    fig_gantt = px.timeline(pd.DataFrame(df_gantt), x_start="Start", x_end="Finish", y="Task", color="Resource")
    fig_gantt.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_gantt, use_container_width=True)
    
    res_mc = executar_monte_carlo(op_row, rota_sel, n_simulacoes=n_simulacoes, seed=int(seed_val))
    if res_mc:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prazo Final", formatar_data_segura(res_mc['prazo_final']))
        c2.metric("P50 (Mais provável)", formatar_data_segura(res_mc['p50']))
        c3.metric("P90 (Segurança 90%)", formatar_data_segura(res_mc['p90']))
        c4.metric("Chance de Atraso", f"{float(res_mc['prob_atraso']):.1f}%")

with tab3:
    st.header("⏪ Agendamento Reverso")
    prod_rev = st.selectbox("Produto Final", list(rotas.keys()), index=0)
    dt_entrega = st.date_input("Data Entrega", datetime(2026, 10, 6))
    hr_entrega = st.time_input("Hora Entrega", datetime(2026, 10, 6, 18, 0).time())
    buffer_folga = st.number_input("Folga (min)", 0, 60, 15)
    
    dt_hr_entrega = datetime.combine(dt_entrega, hr_entrega)
    rota_rev = rotas[prod_rev]
    dur_total = sum(d + buffer_folga for _, d, _ in rota_rev)
    
    st.success(f"Início máximo permitido: {(dt_hr_entrega - timedelta(minutes=dur_total)).strftime('%d/%m %H:%M')}")

with tab4:
    st.header("⚡ Simulação de Atrasos (What-If)")
    st.info("Módulo em desenvolvimento.")

with tab5:
    st.header("🔍 Diagnóstico de Gargalos")
    st.info("Módulo em desenvolvimento.")

with tab6:
    st.header("📋 Dados e Premissas")
    st.dataframe(df_ordens, use_container_width=True)
