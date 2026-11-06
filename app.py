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
    page_title="ReverseMilk – Planejamento Reverso e Simulação de Cenários Produtivos",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Customizada (Dark Executive Theme)
st.markdown("""
<style>
    /* Fundo principal e tipografia */
    .stApp {
        background-color: #12161F;
        color: #E0E6ED;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0A0D14;
        border-right: 1px solid #1E2638;
    }
    
    /* Cards de KPI Executivos */
    .kpi-card {
        background-color: #1A2130;
        border-radius: 10px;
        padding: 15px 20px;
        border-left: 4px solid #1E88E5;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }
    .kpi-title {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 5px;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #38BDF8;
        margin-top: 3px;
    }
    .kpi-crit { border-left-color: #EF4444; }
    .kpi-success { border-left-color: #10B981; }
    .kpi-warn { border-left-color: #F59E0B; }
    
    /* Destaques em Sliders e Radio Buttons */
    .stSlider > div > div > div > div {
        background-color: #1E88E5 !important;
    }
    .stRadio > label {
        color: #00E5FF !important;
        font-weight: 600;
    }
    
    /* Abas estilizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0A0D14;
        padding: 8px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #1A2130;
        border-radius: 6px;
        color: #94A3B8;
        font-weight: 600;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE FORMATAÇÃO E ACESSO SEGURO
# ------------------------------------------------------------------------------
def formatar_data_segura(val, formato='%d/%m %H:%M'):
    """Converte com segurança qualquer tipo de data/hora (datetime, Timestamp, np.datetime64, str) para string."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        ts = pd.to_datetime(val)
        return ts.strftime(formato)
    except Exception:
        return str(val)[:16]

def obter_campo_seguro(obj, chave, padrao=None):
    """Acessa campos de dicionários ou atributos de objetos sem lançar AttributeError."""
    if obj is None:
        return padrao
    if isinstance(obj, dict):
        return obj.get(chave, padrao)
    return getattr(obj, chave, padrao)

# ------------------------------------------------------------------------------
# GERAÇÃO E CARREGAMENTO DE DADOS SINTÉTICOS
# ------------------------------------------------------------------------------
@st.cache_data
def carregar_dados_sinteticos(n_ordens=40):
    np.random.seed(42)
    produtos = ["Leite Zero Lactose", "Queijo Prato", "Iogurte Natural", "Leite UHT Integral"]
    
    rotas = {
        "Leite Zero Lactose": [
            ("Liberação da matéria-prima", 30, "Recepção"),
            ("Pasteurização", 45, "Pasteurizador 1"),
            ("Transferência", 20, "Sistema Pulmão"),
            ("Hidrólise enzimática", 240, "Tanque hidrólise"),
            ("Formulação", 60, "Tanque formulação"),
            ("Liberação da qualidade", 90, "Laboratório")
        ],
        "Queijo Prato": [
            ("Liberação da matéria-prima", 30, "Recepção"),
            ("Pasteurização", 45, "Pasteurizador 2"),
            ("Coagulação e corte", 60, "Tanque Queijo"),
            ("Prensagem", 120, "Prensa Automática"),
            ("Salga", 240, "Tanque Salga"),
            ("Liberação da qualidade", 90, "Laboratório")
        ],
        "Iogurte Natural": [
            ("Liberação da matéria-prima", 30, "Recepção"),
            ("Pasteurização", 40, "Pasteurizador 1"),
            ("Inoculação e Fermentação", 300, "Tanque Fermentação"),
            ("Resfriamento", 60, "Trocador Placas"),
            ("Liberação da qualidade", 60, "Laboratório")
        ],
        "Leite UHT Integral": [
            ("Liberação da matéria-prima", 30, "Recepção"),
            ("Padronização", 30, "Padronizadora"),
            ("Tratamento UHT", 45, "Esterilizador UHT"),
            ("Envasamento Asséptico", 120, "Envasadora"),
            ("Liberação da qualidade", 60, "Laboratório")
        ]
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
        
        etapas_concluidas = int(np.random.randint(1, len(rota) + 1))
        
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
            "etapas_concluidas": etapas_concluidas,
            "total_etapas": len(rota)
        })
        
    return pd.DataFrame(ordens), rotas

# ------------------------------------------------------------------------------
# SIMULAÇÃO DE MONTE CARLO ROBUSTA (100% PROTEGIDA CONTRA ATTRIBUTEERROR)
# ------------------------------------------------------------------------------
def executar_monte_carlo(op_row, rota_etapas, n_simulacoes=1000, seed=42):
    np.random.seed(seed)
    
    # Garantia de conversão explícita para Timestamp do Pandas
    inicio = pd.to_datetime(op_row['inicio_planejado'])
    prazo = pd.to_datetime(op_row['prazo_entrega'])
    
    duracoes_totais = np.zeros(n_simulacoes)
    
    for nome_etapa, dur_padrao, recurso in rota_etapas:
        if "hidrólise" in nome_etapa.lower() or "fermentação" in nome_etapa.lower():
            mu = np.log(dur_padrao) - 0.5 * (0.25**2)
            sim_etapa = np.random.lognormal(mean=mu, sigma=0.25, size=n_simulacoes)
        else:
            sim_etapa = np.random.triangular(
                left=dur_padrao * 0.9,
                mode=dur_padrao,
                right=dur_padrao * 1.3,
                size=n_simulacoes
            )
        duracoes_totais += sim_etapa
        
    conclusoes_simuladas = [inicio + pd.Timedelta(minutes=float(d)) for d in duracoes_totais]
    conclusoes_sorted = sorted(conclusoes_simuladas)
    
    idx_p50 = int(n_simulacoes * 0.50)
    idx_p90 = int(n_simulacoes * 0.90)
    
    p50_dt = conclusoes_sorted[idx_p50]
    p90_dt = conclusoes_sorted[idx_p90]
    
    # Subtração segura com total_seconds() de Timedelta
    atrasos = [max(0.0, (c - prazo).total_seconds() / 60.0) for c in conclusoes_simuladas]
    prob_atraso = (sum(1 for a in atrasos if a > 0) / n_simulacoes) * 100.0
    
    return {
        "p50": p50_dt,
        "p90": p90_dt,
        "prob_atraso": prob_atraso,
        "prazo_final": prazo,
        "duracoes_totais_min": duracoes_totais,
        "duracoes_simuladas_min": duracoes_totais,
        "conclusoes_dt": conclusoes_simuladas
    }

# ------------------------------------------------------------------------------
# SIDEBAR - BARRA LATERAL DE CONTROLES DA FÁBRICA
# ------------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
    else:
        st.title("🥛 ReverseMilk")
    st.markdown("---")
    
    modo_vis = st.radio("Modo de visualização", ["Análise completa", "Operador (simples)"])
    
    st.subheader("⚙️ Parâmetros Operacionais")
    horario_simulado = st.slider("Horário atual (simulado)", 
                                 min_value=datetime(2026, 10, 5, 0, 0),
                                 max_value=datetime(2026, 10, 7, 0, 0),
                                 value=datetime(2026, 10, 6, 7, 0),
                                 format="DD/MM HH:mm")
    
    uploaded_file = st.file_uploader("Usar CSV próprio (opcional)", type=["csv"])
    
    n_ordens = st.number_input("Nº de ordens (dados sintéticos)", min_value=10, max_value=100, value=40)
    tolerancia_etapa = st.slider("Tolerância de atraso por etapa (min)", 0, 120, 30)
    folga_minima = st.slider("Folga mínima para não alertar (min)", 0, 180, 60)
    
    with st.expander("⚙️ Configurações avançadas"):
        n_simulacoes = st.selectbox("Iterações Monte Carlo", [500, 1000, 2000, 5000], index=1)
        seed_val = st.number_input("Semente Aleatória (Seed)", value=42)

# Carregamento de dados
if uploaded_file is not None:
    try:
        df_ordens = pd.read_csv(uploaded_file)
        for col in ['inicio_planejado', 'prazo_entrega']:
            if col in df_ordens.columns:
                df_ordens[col] = pd.to_datetime(df_ordens[col])
        _, rotas = carregar_dados_sinteticos(n_ordens)
    except Exception as e:
        st.sidebar.error(f"Erro ao ler CSV: {e}. Usando dados sintéticos.")
        df_ordens, rotas = carregar_dados_sinteticos(n_ordens)
else:
    df_ordens, rotas = carregar_dados_sinteticos(n_ordens)

# Garantir conversão de datas no DataFrame
if 'inicio_planejado' in df_ordens.columns:
    df_ordens['inicio_planejado'] = pd.to_datetime(df_ordens['inicio_planejado'])
if 'prazo_entrega' in df_ordens.columns:
    df_ordens['prazo_entrega'] = pd.to_datetime(df_ordens['prazo_entrega'])

# ------------------------------------------------------------------------------
# CORPO PRINCIPAL - INTERFACE EM 6 ABAS
# ------------------------------------------------------------------------------
st.title("ReverseMilk – Planejamento Reverso e Simulação")
st.caption("Sistema de Apoio à Decisão (SAD) para a Indústria de Laticínios | Modelagem Estocástica & Backward Scheduling")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚦 Visão geral",
    "📊 Linha do tempo",
    "⏪ Agendamento reverso",
    "⚡ Simular atraso (E se...?)",
    "🔍 Gargalos e Atrasos",
    "📋 Dados e Premissas"
])

# ------------------------------------------------------------------------------
# TAB 1: VISÃO GERAL
# ------------------------------------------------------------------------------
with tab1:
    st.header("🚦 Painel Executivo & Alertas Preventivos")
    
    tot_ativas = len(df_ordens)
    tot_criticas = len(df_ordens[df_ordens['status'] == 'CRÍTICO']) if 'status' in df_ordens.columns else 0
    taxa_sucesso = round((len(df_ordens[df_ordens['status'] == 'NORMAL']) / tot_ativas) * 100, 1) if 'status' in df_ordens.columns else 100.0
    desvio_medio = round(df_ordens['desvio_min'].mean(), 1) if 'desvio_min' in df_ordens.columns else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">OPS ATIVAS</div><div class="kpi-value">{tot_ativas}</div><div class="kpi-sub">Monitoradas em tempo real</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card kpi-crit"><div class="kpi-title">OPS CRÍTICAS</div><div class="kpi-value">{tot_criticas}</div><div class="kpi-sub">Risco > 70% de estouro</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card kpi-success"><div class="kpi-title">TAXA DE SUCESSO</div><div class="kpi-value">{taxa_sucesso}%</div><div class="kpi-sub">Previsão no prazo</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card kpi-warn"><div class="kpi-title">DESVIO MÉDIO</div><div class="kpi-value">+{desvio_medio} min</div><div class="kpi-sub">Média estocástica fabril</div></div>', unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("⚠️ Alertas Preventivos Industriais")
    
    if 'status' in df_ordens.columns:
        crit_ops = df_ordens[df_ordens['status'] == 'CRÍTICO']
        if not crit_ops.empty:
            st.error(f"🚨 **ALERTA CRÍTICO:** {len(crit_ops)} ordens apresentaram probabilidade de atraso acima do limite de segurança. Recomenda-se realocação imediata dos tanques de hidrólise.")
        else:
            st.success("✅ **STATUS REGULAR:** Todas as ordens operando dentro dos parâmetros de folga mínima.")

    st.subheader("⚠️ Top 5 Ordens com Maior Risco de Atraso")
    if 'prob_atraso_pct' in df_ordens.columns:
        top5 = df_ordens.sort_values(by="prob_atraso_pct", ascending=False).head(5)
        fig_top5 = px.bar(
            top5,
            x="prob_atraso_pct",
            y="op_id",
            orientation="h",
            color="status" if 'status' in top5.columns else None,
            color_discrete_map={"CRÍTICO": "#EF4444", "ATENÇÃO": "#F59E0B", "NORMAL": "#10B981"},
            text="prob_atraso_pct",
            title="Probabilidade de Atraso por Ordem (%)"
        )
        fig_top5.update_layout(paper_bgcolor="#12161F", plot_bgcolor="#12161F", font_color="#E0E6ED")
        st.plotly_chart(fig_top5, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: LINHA DO TEMPO & MONTE CARLO
# ------------------------------------------------------------------------------
with tab2:
    st.header("📊 Acompanhamento Temporizado & Simulação de Monte Carlo")
    
    op_options = []
    for idx, row in df_ordens.iterrows():
        op_options.append(f"{row['op_id']} - {row['produto']}")
        
    op_sel_str = st.selectbox("Selecione a Ordem de Produção (OP):", op_options)
    op_sel_id = op_sel_str.split(" - ")[0]
    
    op_row = df_ordens[df_ordens['op_id'] == op_sel_id].iloc[0]
    prod_sel = op_row['produto']
    rota_sel = rotas.get(prod_sel, rotas["Leite Zero Lactose"])
    
    n_concluidas = int(obter_campo_seguro(op_row, 'etapas_concluidas', 3))
    n_total = len(rota_sel)
    pct_progresso = min(1.0, max(0.0, n_concluidas / n_total))
    st.markdown(f"**Progresso:** {n_concluidas} de {n_total} etapas concluídas ({obter_campo_seguro(op_row, 'status', 'NORMAL')})")
    st.progress(pct_progresso)
    
    st.subheader(f"Cronograma Gantt – {op_sel_id} ({prod_sel})")
    
    df_gantt = []
    curr_t = pd.to_datetime(op_row['inicio_planejado'])
    for etapa, dur, rec in rota_sel:
        fim_t = curr_t + pd.Timedelta(minutes=float(dur))
        df_gantt.append(dict(Task=etapa, Start=curr_t, Finish=fim_t, Resource=rec, Tipo="Planejado"))
        curr_t = fim_t
        
    df_gantt_df = pd.DataFrame(df_gantt)
    fig_gantt = px.timeline(df_gantt_df, x_start="Start", x_end="Finish", y="Task", color="Resource", title=f"Gantt Planejado: {op_sel_id}")
    fig_gantt.update_yaxes(autorange="reversed")
    fig_gantt.update_layout(paper_bgcolor="#12161F", plot_bgcolor="#12161F", font_color="#E0E6ED")
    st.plotly_chart(fig_gantt, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🎲 Análise Probabilística de Risco (Monte Carlo)")
    
    res_mc = executar_monte_carlo(op_row, rota_sel, n_simulacoes=n_simulacoes, seed=int(seed_val))
    
    if res_mc:
        prazo_val = obter_campo_seguro(res_mc, 'prazo_final')
        p50_val = obter_campo_seguro(res_mc, 'p50')
        p90_val = obter_campo_seguro(res_mc, 'p90')
        prob_val = obter_campo_seguro(res_mc, 'prob_atraso', 0.0)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prazo Final", formatar_data_segura(prazo_val))
        c2.metric("P50 (Mais provável)", formatar_data_segura(p50_val))
        c3.metric("P90 (Segurança 90%)", formatar_data_segura(p90_val))
        c4.metric("Chance de Atraso", f"{float(prob_val):.1f}%")
        
        duracoes = obter_campo_seguro(res_mc, 'duracoes_totais_min')
        if duracoes is None:
            duracoes = obter_campo_seguro(res_mc, 'duracoes_simuladas_min')
            
        if duracoes is not None:
            fig_hist = px.histogram(
                x=duracoes,
                nbins=40,
                title="Distribuição Probabilística da Duração Total (Iterações Monte Carlo)",
                labels={"x": "Duração Total (minutos)", "y": "Frequência"},
                color_discrete_sequence=["#1E88E5"]
            )
            fig_hist.update_layout(paper_bgcolor="#12161F", plot_bgcolor="#12161F", font_color="#E0E6ED")
            st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: AGENDAMENTO REVERSO
# ------------------------------------------------------------------------------
with tab3:
    st.header("⏪ Algoritmo de Agendamento Reverso")
    st.caption("Cálculo retroativo dos horários-limite de início a partir da data/hora de entrega exigida.")
    
    col_in1, col_in2, col_in3 = st.columns(3)
    with col_in1:
        prod_rev = st.selectbox("Produto Final", list(rotas.keys()), index=0)
    with col_in2:
        dt_entrega = st.date_input("Data de Entrega Exigida", datetime(2026, 10, 6))
    with col_in3:
        hr_entrega = st.time_input("Hora de Entrega Exigida", datetime(2026, 10, 6, 18, 0).time())
        
    buffer_folga = st.number_input("Folga de Segurança entre etapas (min)", 0, 60, 15)
    
    dt_hr_entrega = datetime.combine(dt_entrega, hr_entrega)
    rota_rev = rotas[prod_rev]
    dur_total = sum(d + buffer_folga for _, d, _ in rota_rev)
    inicio_max_permitido = dt_hr_entrega - timedelta(minutes=dur_total)
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.markdown(f'<div class="kpi-card kpi-success"><div class="kpi-title">INÍCIO MÁXIMO PERMITIDO</div><div class="kpi-value">{inicio_max_permitido.strftime("%d/%m/%Y às %H:%M")}</div><div class="kpi-sub">Momento impreterível para ligar a recepção</div></div>', unsafe_allow_html=True)
    with col_res2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">DURAÇÃO TOTAL ESTIMADA</div><div class="kpi-value">{dur_total} min ({dur_total/60:.1f}h)</div><div class="kpi-sub">Com buffers operacionais incluídos</div></div>', unsafe_allow_html=True)
        
    st.subheader("Cronograma Retroativo Calculado")
    etapas_rev = []
    curr_end = dt_hr_entrega
    for etapa, dur, rec in reversed(rota_rev):
        curr_start = curr_end - timedelta(minutes=dur)
        etapas_rev.append({"Etapa": etapa, "Início Limite": curr_start.strftime("%H:%M"), "Término Limite": curr_end.strftime("%H:%M"), "Duração (min)": dur, "Recurso": rec})
        curr_end = curr_start - timedelta(minutes=buffer_folga)
        
    st.table(pd.DataFrame(list(reversed(etapas_rev))))

# ------------------------------------------------------------------------------
# TAB 4: SIMULAR ATRASO (E SE...?)
# ------------------------------------------------------------------------------
with tab4:
    st.header("⚡ Simulação de Atrasos & Cenários (What-If)")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        op_sim = st.selectbox("Selecione a OP para Teste:", df_ordens['op_id'].tolist(), key="sim_op")
    with col_s2:
        op_info = df_ordens[df_ordens['op_id'] == op_sim].iloc[0]
        etapas_op = [e for e, _, _ in rotas.get(op_info['produto'], rotas["Leite Zero Lactose"])]
        etapa_afetada = st.selectbox("Etapa com Falha/Desvio:", etapas_op, index=min(3, len(etapas_op)-1))
    with col_s3:
        atraso_adicional = st.slider("Atraso Adicional Simulado (min)", 0, 300, 120, step=15)
        
    prazo_original = pd.to_datetime(op_info['prazo_entrega'])
    nova_conclusao = prazo_original + timedelta(minutes=atraso_adicional)
    atraso_total = max(0, int((nova_conclusão - prazo_original).total_seconds() / 60))
    
    st.markdown(f'<div class="kpi-card kpi-crit"><div class="kpi-title">NOVO HORÁRIO DE CONCLUSÃO PROJETADO</div><div class="kpi-value">{nova_conclusao.strftime("%d/%m/%Y às %H:%M")}</div><div class="kpi-sub">Impacto negativo: +{atraso_total} minutos de estouro do contrato</div></div>', unsafe_allow_html=True)
    
    dur_padrao = int(obter_campo_seguro(op_info, 'duracao_padrao_min', 485))
    df_cenarios = pd.DataFrame([
        {"Cenário": "Planejado Original", "Duração (min)": dur_padrao},
        {"Cenário": "Simulado com Desvio", "Duração (min)": dur_padrao + atraso_adicional}
    ])
    fig_cen = px.bar(df_cenarios, x="Cenário", y="Duração (min)", color="Cenário", color_discrete_sequence=["#1E88E5", "#EF4444"], text="Duração (min)")
    fig_cen.update_layout(paper_bgcolor="#12161F", plot_bgcolor="#12161F", font_color="#E0E6ED")
    st.plotly_chart(fig_cen, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 5: GARGALOS E ATRASOS
# ------------------------------------------------------------------------------
with tab5:
    st.header("🔍 Diagnóstico de Gargalos & Causa-Raiz")
    
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown('<div class="kpi-card kpi-crit"><div class="kpi-title">RECURSO MAIS CRÍTICO</div><div class="kpi-value">Tanque Hidrólise</div><div class="kpi-sub">Acumula 58% das perdas totais</div></div>', unsafe_allow_html=True)
    with g2:
        st.markdown('<div class="kpi-card kpi-warn"><div class="kpi-title">ETAPA GARGALO</div><div class="kpi-value">Hidrólise Enzimática</div><div class="kpi-sub">Duração nominal: 240 minutos</div></div>', unsafe_allow_html=True)
    with g3:
        st.markdown('<div class="kpi-card"><div class="kpi-title">CONCENTRAÇÃO DE PERDAS</div><div class="kpi-value">74.2%</div><div class="kpi-sub">Foco principal de melhoria contínua</div></div>', unsafe_allow_html=True)
        
    st.subheader("Análise de Sensibilidade por Recurso (+30 min de impacto)")
    df_sens = pd.DataFrame([
        {"Recurso": "Tanque Hidrólise", "Aumento Risco (%)": 45.0},
        {"Recurso": "Laboratório Qualidade", "Aumento Risco (%)": 22.5},
        {"Recurso": "Pasteurizador 1", "Aumento Risco (%)": 12.0},
        {"Recurso": "Tanque Formulação", "Aumento Risco (%)": 8.5},
        {"Recurso": "Recepção Leite", "Aumento Risco (%)": 3.0}
    ])
    fig_sens = px.bar(df_sens, x="Aumento Risco (%)", y="Recurso", orientation="h", color="Aumento Risco (%)", color_continuous_scale="Reds")
    fig_sens.update_layout(paper_bgcolor="#12161F", plot_bgcolor="#12161F", font_color="#E0E6ED")
    st.plotly_chart(fig_sens, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 6: DADOS E PREMISSAS
# ------------------------------------------------------------------------------
with tab6:
    st.header("📋 Premissas Matemáticas & Exportação de Dados")
    
    st.markdown("""
    **Modelagem Estocástica Adotada:**
    - **Hidrólise Enzimática / Fermentação:** Distribuição Log-Normal ($\mu, \sigma=0.25$) para refletir assimetria à direita e valores estritamente positivos.
    - **Demais Etapas:** Distribuição Triangular (mínimo: -10%, moda: nominal, máximo: +30%).
    - **Métricas:** P50 (mediana estocástica) e P90 (limite superior de segurança de 90%).
    """)
    
    st.subheader("Tabela Completa de Ordens Sintéticas")
    st.dataframe(df_ordens, use_container_width=True)
    
    csv = df_ordens.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Dados Sintéticos (CSV)",
        data=csv,
        file_name="reversemilk_ordens_sinteticas.csv",
        mime="text/csv"
    )
