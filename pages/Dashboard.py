# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
from datetime import timedelta
from utils import check_auth, get_supabase_client, formatar_moeda

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Dashboard", layout="wide", page_icon="📊")
check_auth("o Dashboard")
supabase = get_supabase_client()

# --- Lógica da Sidebar ---
with st.sidebar:
    st.header("Modo de Acesso")
    if st.session_state.get('logged_in'):
        st.success(f"Logado como: {st.session_state.user_email}")
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    st.markdown("---"); st.info("Desenvolvido por @Rogerio Souza")

# --- Funções da Página ---
@st.cache_data(ttl=600)
def carregar_dados_dashboard():
    # Carrega tanto as parcelas a receber quanto as contas a pagar
    parcelas_resp = supabase.table('parcelas').select('valor_parcela, status, data_pagamento, data_vencimento, clientes(nome)').execute()
    contas_resp = supabase.table('contas_a_pagar').select('valor, status, data_pagamento, data_vencimento, fornecedores(nome_razao_social)').execute()
    return pd.DataFrame(parcelas_resp.data), pd.DataFrame(contas_resp.data)

# --- Construção da Página ---
st.title("📊 Painel de Controle")
st.markdown("Visão geral e em tempo real da saúde financeira da sua construtora.")

df_receber, df_pagar = carregar_dados_dashboard()

# --- KPIs Principais ---
st.markdown("### Resumo Financeiro")
col1, col2, col3, col4 = st.columns(4)

total_a_receber = pd.to_numeric(df_receber[df_receber['status'].isin(['Pendente', 'Atrasado'])]['valor_parcela']).sum()
col1.metric("💰 Total a Receber", formatar_moeda(total_a_receber))

recebido_mes_atual = pd.to_numeric(df_receber[(df_receber['status'] == 'Pago') & (pd.to_datetime(df_receber['data_pagamento'], errors='coerce').dt.month == pd.Timestamp.now().month)]['valor_parcela']).sum()
col2.metric("✅ Recebido este Mês", formatar_moeda(recebido_mes_atual))

total_a_pagar = pd.to_numeric(df_pagar[df_pagar['status'].isin(['Pendente', 'Atrasado'])]['valor']).sum()
col3.metric("💸 Total a Pagar", formatar_moeda(total_a_pagar))

total_atrasado = pd.to_numeric(df_receber[df_receber['status'] == 'Atrasado']['valor_parcela']).sum()
col4.metric("⚠️ Recebimentos em Atraso", formatar_moeda(total_atrasado), delta_color="inverse")

st.markdown("---")

# --- Próximos Vencimentos e Parcelas Atrasadas ---
st.markdown("### 🗓️ Vencimentos da Semana")
hoje = pd.Timestamp.now().normalize()
data_fim_semana = hoje + pd.Timedelta(days=7)

# Prepara dados a receber
df_receber['data_vencimento'] = pd.to_datetime(df_receber['data_vencimento'])
venc_receber = df_receber[(df_receber['data_vencimento'] >= hoje) & (df_receber['data_vencimento'] <= data_fim_semana) & (df_receber['status'] == 'Pendente')]
venc_receber['tipo'] = '✅ A Receber'
venc_receber['valor'] = venc_receber['valor_parcela']
venc_receber['interessado'] = venc_receber['clientes'].apply(lambda x: x['nome'] if isinstance(x, dict) else 'N/A')

# Prepara dados a pagar
df_pagar['data_vencimento'] = pd.to_datetime(df_pagar['data_vencimento'])
venc_pagar = df_pagar[(df_pagar['data_vencimento'] >= hoje) & (df_pagar['data_vencimento'] <= data_fim_semana) & (df_pagar['status'] == 'Pendente')]
venc_pagar['tipo'] = '💸 A Pagar'
venc_pagar['interessado'] = df_pagar['fornecedores'].apply(lambda x: x['nome_razao_social'] if isinstance(x, dict) else 'N/A')

# Junta, ordena e exibe
df_vencimentos = pd.concat([venc_receber[['data_vencimento', 'tipo', 'valor', 'interessado']], venc_pagar[['data_vencimento', 'tipo', 'valor', 'interessado']]])
df_vencimentos = df_vencimentos.sort_values('data_vencimento')

if df_vencimentos.empty:
    st.success("Nenhum vencimento (a pagar ou a receber) nos próximos 7 dias.")
else:
    for _, row in df_vencimentos.iterrows():
        st.info(f"{row['tipo']} de **{formatar_moeda(row['valor'])}** - Interessado: **{row['interessado']}** - Vence em: {row['data_vencimento'].strftime('%d/%m/%Y')}")