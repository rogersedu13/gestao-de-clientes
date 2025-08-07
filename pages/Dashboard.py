# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Funções de Utilidade e Design (Agora dentro de cada arquivo) ---
def load_custom_css():
    st.markdown("""<style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
        :root {
            --primary-color: #2337D9; --background-color: #0F1116; --card-background-color: #1A1C24;
            --text-color: #FAFAFA; --subtle-text-color: #A0A4B8; --border-color: #333748;
        }
        body, .stApp { font-family: 'Source Sans Pro', sans-serif; background-color: var(--background-color); color: var(--text-color); }
        h1, h2, h3 { color: var(--primary-color); font-weight: 700; }
        .st-emotion-cache-1r4qj8v, .st-emotion-cache-1xw8zdv, [data-testid="stExpander"] {
            background-color: var(--card-background-color); border: 1px solid var(--border-color); border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); padding: 1rem;
        }
        [data-testid="stExpander"] > details > summary { font-size: 1.1rem; font-weight: 600; }
        .stButton > button {
            border-radius: 8px; background-color: var(--primary-color); color: white; border: none; transition: background-color 0.2s;
        }
        .stButton > button:hover { background-color: #4A5DF2; }
        .stButton > button:focus { box-shadow: 0 0 0 2px var(--primary-color) !important; }
        [data-testid="stSidebar"] { background-color: var(--card-background-color); border-right: 1px solid var(--border-color); }
        [data-testid="stMetric"] { background-color: var(--card-background-color); border: 1px solid var(--border-color); border-radius: 10px; padding: 1rem; }
        [data-testid="stMetric"] > div > div:first-child { color: var(--subtle-text-color); }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 44px; background-color: transparent; border-radius: 8px; }
        .stTabs [data-baseweb="tab"]:hover { background-color: var(--card-background-color); }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: var(--primary-color); color: white; }
        </style>""", unsafe_allow_html=True)

def conectar_supabase() -> Client:
    try:
        url = st.secrets["supabase_url"]; key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception:
        st.error("🚨 **Erro de Conexão:** Verifique as credenciais do Supabase nos Secrets."); st.stop()

def check_auth(pagina: str = "esta página"):
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning(f"🔒 Por favor, faça o login para acessar {pagina}."); st.stop()

def formatar_moeda(valor):
    if valor is None: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Autenticação, Conexão e Design ---
st.set_page_config(page_title="Dashboard", layout="wide", page_icon="📊")
load_custom_css()
check_auth("o Dashboard")
supabase = conectar_supabase()

# --- Funções da Página ---
@st.cache_data(ttl=600)
def carregar_dados_dashboard():
    parcelas_response = supabase.table('parcelas').select('*, clientes(nome)').execute()
    return pd.DataFrame(parcelas_response.data)

# --- Construção da Página ---
st.title("📊 Painel de Controle")
st.markdown("Visão geral e em tempo real da saúde financeira dos seus recebimentos.")

df_parcelas = carregar_dados_dashboard()

if df_parcelas.empty:
    st.info("Ainda não há dados de parcelas para exibir no dashboard."); st.stop()

df_parcelas['valor_parcela'] = pd.to_numeric(df_parcelas['valor_parcela'])
df_parcelas['data_vencimento'] = pd.to_datetime(df_parcelas['data_vencimento'])

st.markdown("### Resumo Financeiro")
col1, col2, col3 = st.columns(3)

total_a_receber = df_parcelas[df_parcelas['status'].isin(['Pendente', 'Atrasado'])]['valor_parcela'].sum()
col1.metric("💰 Total a Receber", formatar_moeda(total_a_receber))

recebido_mes_atual = df_parcelas[
    (df_parcelas['status'] == 'Pago') &
    (pd.to_datetime(df_parcelas['data_pagamento'], errors='coerce').dt.month == pd.Timestamp.now().month) &
    (pd.to_datetime(df_parcelas['data_pagamento'], errors='coerce').dt.year == pd.Timestamp.now().year)
]['valor_parcela'].sum()
col2.metric("✅ Recebido este Mês", formatar_moeda(recebido_mes_atual))

total_atrasado = df_parcelas[df_parcelas['status'] == 'Atrasado']['valor_parcela'].sum()
col3.metric("⚠️ Total em Atraso", formatar_moeda(total_atrasado), delta_color="inverse")

st.markdown("---")
col_venc, col_atraso = st.columns(2)

with col_venc:
    with st.container(border=True):
        st.markdown("### 🗓️ Próximos Vencimentos (7 dias)")
        hoje = pd.Timestamp.now().normalize()
        proximos_vencimentos = df_parcelas[
            (df_parcelas['data_vencimento'] >= hoje) &
            (df_parcelas['data_vencimento'] <= hoje + pd.Timedelta(days=7)) &
            (df_parcelas['status'] == 'Pendente')
        ].sort_values('data_vencimento')
        if proximos_vencimentos.empty:
            st.success("Nenhuma parcela vencendo nos próximos 7 dias.")
        else:
            for _, row in proximos_vencimentos.iterrows():
                nome_cliente = row['clientes']['nome'] if isinstance(row.get('clientes'), dict) else 'Cliente não encontrado'
                st.warning(f"**{nome_cliente}**: {formatar_moeda(row['valor_parcela'])} - Vence em: {row['data_vencimento'].strftime('%d/%m/%Y')}")

with col_atraso:
    with st.container(border=True):
        st.markdown("### 🚫 Parcelas em Atraso")
        parcelas_atrasadas = df_parcelas[df_parcelas['status'] == 'Atrasado'].sort_values('data_vencimento')
        if parcelas_atrasadas.empty:
            st.success("Nenhuma parcela em atraso!")
        else:
            for _, row in parcelas_atrasadas.iterrows():
                nome_cliente = row['clientes']['nome'] if isinstance(row.get('clientes'), dict) else 'Cliente não encontrado'
                st.error(f"**{nome_cliente}**: {formatar_moeda(row['valor_parcela'])} - Venceu em: {row['data_vencimento'].strftime('%d/%m/%Y')}")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 📊 Saldo Devedor por Cliente (Top 10)")
    df_parcelas['nome_cliente'] = df_parcelas['clientes'].apply(lambda x: x['nome'] if isinstance(x, dict) and 'nome' in x else 'Desconhecido')
    top_10_devedores = df_parcelas[df_parcelas['status'] != 'Pago'].groupby('nome_cliente')['valor_parcela'].sum().nlargest(10)
    if not top_10_devedores.empty:
        st.bar_chart(top_10_devedores)
    else:
        st.info("Não há saldos devedores para exibir.")