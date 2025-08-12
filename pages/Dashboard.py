# pages/Dashboard.py
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

# CORREÇÃO: Verifica se o DataFrame não está vazio antes de calcular
total_a_receber = pd.to_numeric(df_receber['valor_parcela']).sum() if not df_receber.empty else 0
col1.metric("💰 Total a Receber (Bruto)", formatar_moeda(total_a_receber))

recebido_mes_atual = 0
if not df_receber.empty and 'data_pagamento' in df_receber.columns:
    df_receber_pagas = df_receber.dropna(subset=['data_pagamento'])
    df_receber_pagas['data_pagamento'] = pd.to_datetime(df_receber_pagas['data_pagamento'])
    recebido_mes_atual = pd.to_numeric(df_receber_pagas[
        (df_receber_pagas['status'] == 'Pago') &
        (df_receber_pagas['data_pagamento'].dt.month == pd.Timestamp.now().month) &
        (df_receber_pagas['data_pagamento'].dt.year == pd.Timestamp.now().year)
    ]['valor_parcela']).sum()
col2.metric("✅ Recebido este Mês", formatar_moeda(recebido_mes_atual))

total_a_pagar = pd.to_numeric(df_pagar['valor']).sum() if not df_pagar.empty else 0
col3.metric("💸 Total a Pagar (Bruto)", formatar_moeda(total_a_pagar))

total_atrasado = pd.to_numeric(df_receber[df_receber['status'] == 'Atrasado']['valor_parcela']).sum() if not df_receber.empty else 0
col4.metric("⚠️ Recebimentos em Atraso", formatar_moeda(total_atrasado), delta_color="inverse")

st.markdown("---")

# --- Próximos Vencimentos e Parcelas Atrasadas ---
st.markdown("### 🗓️ Vencimentos da Semana")
hoje = pd.Timestamp.now().normalize()
data_fim_semana = hoje + pd.Timedelta(days=7)
df_vencimentos_final = pd.DataFrame()

if not df_receber.empty:
    df_receber['data_vencimento'] = pd.to_datetime(df_receber['data_vencimento'])
    venc_receber = df_receber[(df_receber['data_vencimento'] >= hoje) & (df_receber['data_vencimento'] <= data_fim_semana) & (df_receber['status'] == 'Pendente')]
    if not venc_receber.empty:
        venc_receber['tipo'] = '✅ A Receber'
        venc_receber['valor'] = venc_receber['valor_parcela']
        venc_receber['interessado'] = venc_receber['clientes'].apply(lambda x: x['nome'] if isinstance(x, dict) else 'N/A')
        df_vencimentos_final = pd.concat([df_vencimentos_final, venc_receber[['data_vencimento', 'tipo', 'valor', 'interessado']]])

if not df_pagar.empty:
    df_pagar['data_vencimento'] = pd.to_datetime(df_pagar['data_vencimento'])
    venc_pagar = df_pagar[(df_pagar['data_vencimento'] >= hoje) & (df_pagar['data_vencimento'] <= data_fim_semana) & (df_pagar['status'] == 'Pendente')]
    if not venc_pagar.empty:
        venc_pagar['tipo'] = '💸 A Pagar'
        venc_pagar['interessado'] = venc_pagar['fornecedores'].apply(lambda x: x['nome_razao_social'] if isinstance(x, dict) else 'N/A')
        df_vencimentos_final = pd.concat([df_vencimentos_final, venc_pagar[['data_vencimento', 'tipo', 'valor', 'interessado']]])

if df_vencimentos_final.empty:
    st.success("Nenhum vencimento (a pagar ou a receber) nos próximos 7 dias.")
else:
    df_vencimentos_final = df_vencimentos_final.sort_values('data_vencimento')
    for _, row in df_vencimentos_final.iterrows():
        st.info(f"{row['tipo']} de **{formatar_moeda(row['valor'])}** - Interessado: **{row['interessado']}** - Vence em: {row['data_vencimento'].strftime('%d/%m/%Y')}")