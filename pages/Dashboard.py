# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
from utils import check_auth, get_supabase_client, formatar_moeda

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Dashboard", layout="wide", page_icon="📊")
check_auth("o Dashboard")
supabase = get_supabase_client() # Pega a conexão já autenticada

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
    parcelas_response = supabase.table('parcelas').select('*, clientes(nome)').execute()
    return pd.DataFrame(parcelas_response.data)

# --- Construção da Página ---
st.title("📊 Painel de Controle")
st.markdown("Visão geral e em tempo real da saúde financeira dos seus recebimentos.")
df_parcelas = carregar_dados_dashboard()
if df_parcelas.empty:
    st.info("Ainda não há dados de parcelas para exibir no dashboard."); st.stop()

# ... (O resto do código do Dashboard permanece o mesmo)
df_parcelas['valor_parcela'] = pd.to_numeric(df_parcelas['valor_parcela'])
df_parcelas['data_vencimento'] = pd.to_datetime(df_parcelas['data_vencimento'])

st.markdown("### Resumo Financeiro")
col1, col2, col3 = st.columns(3)
total_a_receber = df_parcelas[df_parcelas['status'].isin(['Pendente', 'Atrasado'])]['valor_parcela'].sum()
col1.metric("💰 Total a Receber", formatar_moeda(total_a_receber))
recebido_mes_atual = df_parcelas[(df_parcelas['status'] == 'Pago') & (pd.to_datetime(df_parcelas['data_pagamento'], errors='coerce').dt.month == pd.Timestamp.now().month) & (pd.to_datetime(df_parcelas['data_pagamento'], errors='coerce').dt.year == pd.Timestamp.now().year)]['valor_parcela'].sum()
col2.metric("✅ Recebido este Mês", formatar_moeda(recebido_mes_atual))
total_atrasado = df_parcelas[df_parcelas['status'] == 'Atrasado']['valor_parcela'].sum()
col3.metric("⚠️ Total em Atraso", formatar_moeda(total_atrasado), delta_color="inverse")

st.markdown("---")
col_venc, col_atraso = st.columns(2)
with col_venc:
    st.markdown("### 🗓️ Próximos Vencimentos (7 dias)")
    hoje = pd.Timestamp.now().normalize()
    proximos_vencimentos = df_parcelas[(df_parcelas['data_vencimento'] >= hoje) & (df_parcelas['data_vencimento'] <= hoje + pd.Timedelta(days=7)) & (df_parcelas['status'] == 'Pendente')].sort_values('data_vencimento')
    if proximos_vencimentos.empty:
        st.success("Nenhuma parcela vencendo nos próximos 7 dias.")
    else:
        for _, row in proximos_vencimentos.iterrows():
            nome_cliente = row['clientes']['nome'] if isinstance(row.get('clientes'), dict) else 'Cliente não encontrado'
            st.warning(f"**{nome_cliente}**: {formatar_moeda(row['valor_parcela'])} - Vence em: {row['data_vencimento'].strftime('%d/%m/%Y')}")
with col_atraso:
    st.markdown("### 🚫 Parcelas em Atraso")
    parcelas_atrasadas = df_parcelas[df_parcelas['status'] == 'Atrasado'].sort_values('data_vencimento')
    if parcelas_atrasadas.empty:
        st.success("Nenhuma parcela em atraso!")
    else:
        for _, row in parcelas_atrasadas.iterrows():
            nome_cliente = row['clientes']['nome'] if isinstance(row.get('clientes'), dict) else 'Cliente não encontrado'
            st.error(f"**{nome_cliente}**: {formatar_moeda(row['valor_parcela'])} - Venceu em: {row['data_vencimento'].strftime('%d/%m/%Y')}")

st.markdown("---")
st.markdown("### 📊 Saldo Devedor por Cliente (Top 10)")
df_parcelas['nome_cliente'] = df_parcelas['clientes'].apply(lambda x: x['nome'] if isinstance(x, dict) and 'nome' in x else 'Desconhecido')
top_10_devedores = df_parcelas[df_parcelas['status'] != 'Pago'].groupby('nome_cliente')['valor_parcela'].sum().nlargest(10)
if not top_10_devedores.empty:
    st.bar_chart(top_10_devedores)
else:
    st.info("Não há saldos devedores para exibir.")