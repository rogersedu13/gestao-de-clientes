# pages/Gestao_de_Obras.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
from utils import check_auth, get_supabase_client, formatar_moeda

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Gestão de Obras", layout="wide", page_icon="🏗️")
check_auth("a área de Gestão de Obras")
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

# <<<<===== CORREÇÃO APLICADA AQUI =====>>>>
@st.cache_data(ttl=60)
def carregar_obras(_supabase_client: Client) -> pd.DataFrame:
    # A função agora recebe o cliente supabase como argumento
    response = _supabase_client.table('obras').select('*').eq('ativo', True).order('nome_obra').execute()
    return pd.DataFrame(response.data)

# <<<<===== CORREÇÃO APLICADA AQUI =====>>>>
@st.cache_data(ttl=60)
def carregar_receitas_por_obra(_supabase_client: Client) -> pd.Series:
    response = _supabase_client.table('debitos').select('obra_id, valor_total').not_('obra_id', 'is', None).execute()
    df = pd.DataFrame(response.data)
    if df.empty or 'obra_id' not in df.columns or df['obra_id'].isnull().all():
        return pd.Series(dtype='float64')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce').fillna(0)
    return df.groupby('obra_id')['valor_total'].sum()

# <<<<===== CORREÇÃO APLICADA AQUI =====>>>>
@st.cache_data(ttl=60)
def carregar_custos_por_obra(_supabase_client: Client) -> pd.Series:
    response = _supabase_client.table('contas_a_pagar').select('obra_id, valor').not_('obra_id', 'is', None).execute()
    df = pd.DataFrame(response.data)
    if df.empty or 'obra_id' not in df.columns or df['obra_id'].isnull().all():
        return pd.Series(dtype='float64')
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    return df.groupby('obra_id')['valor'].sum()

def cadastrar_obra(nome, endereco, data_inicio, data_fim, status, valor, responsavel, obs):
    try:
        obra_data = {
            'nome_obra': nome, 'endereco': endereco, 'data_inicio': data_inicio.strftime('%Y-%m-%d'),
            'data_fim_prevista': data_fim.strftime('%Y-%m-%d'), 'status': status, 'valor_obra': valor,
            'responsavel_obra': responsavel, 'observacoes': obs
        }
        supabase.table('obras').insert(obra_data).execute(); return True
    except Exception as e:
        st.error(f"Erro ao cadastrar obra: {e}"); return False

# --- Construção da Página ---
st.image("https://placehold.co/1200x200/f0ad4e/FFFFFF?text=Gestão+de+Obras", use_container_width=True)
st.title("🏗️ Gestão de Obras")
st.markdown("Cadastre e acompanhe o andamento e a lucratividade de suas obras.")

tab_painel, tab_cadastro = st.tabs(["Painel de Obras", "Cadastrar Nova Obra"])

with tab_painel:
    st.subheader("Painel Geral das Obras")
    
    # <<<<===== CORREÇÃO APLICADA AQUI =====>>>>
    # Passamos o objeto 'supabase' como argumento para as funções
    df_obras = carregar_obras(supabase)
    df_receitas = carregar_receitas_por_obra(supabase)
    df_custos = carregar_custos_por_obra(supabase)

    # Junta as receitas
    if not df_receitas.empty:
        df_obras = df_obras.merge(df_receitas.rename('receita_total'), left_on='id', right_index=True, how='left')
    df_obras['receita_total'] = df_obras.get('receita_total', 0).fillna(0)
    
    # Junta os custos
    if not df_custos.empty:
        df_obras = df_obras.merge(df_custos.rename('custo_total'), left_on='id', right_index=True, how='left')
    df_obras['custo_total'] = df_obras.get('custo_total', 0).fillna(0)
    
    # Calcula a lucratividade
    df_obras['lucratividade'] = df_obras['receita_total'] - df_obras['custo_total']

    # Indicadores Rápidos
    col1, col2 = st.columns(2)
    if 'status' in df_obras.columns:
        obras_em_andamento = df_obras[df_obras['status'] == 'Em Andamento'].shape[0]
        col1.metric("Obras em Andamento", obras_em_andamento)
    else:
        col1.metric("Obras em Andamento", "N/A", help="Coluna 'status' não encontrada.")

    lucratividade_total = df_obras['lucratividade'].sum()
    col2.metric("Lucratividade Total Prevista", formatar_moeda(lucratividade_total))

    st.markdown("---")
    st.subheader("Lista de Obras")

    if df_obras.empty:
        st.info("Nenhuma obra cadastrada.")
    else:
        for _, row in df_obras.iterrows():
            with st.expander(f"**{row.get('nome_obra', 'N/A')}** | Status: {row.get('status', 'N/A')}"):
                st.markdown(f"**Responsável:** {row.get('responsavel_obra', 'N/A')}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Receita Prevista", formatar_moeda(row.get('receita_total')))
                c2.metric("Custos Lançados", formatar_moeda(row.get('custo_total')))
                c3.metric("Lucro Previsto", formatar_moeda(row.get('lucratividade')))
                
                if row.get('receita_total', 0) > 0:
                    percentual_custo = (row.get('custo_total', 0) / row.get('receita_total', 1)) * 100
                    st.progress(int(percentual_custo), text=f"{percentual_custo:.1f}% dos custos em relação à receita")

with tab_cadastro:
    st.subheader("Cadastrar Nova Obra")
    with st.form("nova_obra_form", clear_on_submit=True):
        nome = st.text_input("Nome da Obra*", help="Campo obrigatório")
        endereco = st.text_input("Endereço da Obra")
        responsavel = st.text_input("Responsável pela Obra (Mestre de Obra)")
        col_data1, col_data2 = st.columns(2)
        data_inicio = col_data1.date_input("Data de Início", value=date.today())
        data_fim_prevista = col_data2.date_input("Data Prevista de Conclusão", value=date.today() + timedelta(days=365))
        col_status, col_valor = st.columns(2)
        status = col_status.selectbox("Status Inicial", ["Planejamento", "Em Andamento", "Pausada", "Finalizada"])
        valor = col_valor.number_input("Valor da Obra (R$)", min_value=0.0, format="%.2f")
        obs = st.text_area("Observações")
        if st.form_submit_button("Salvar Nova Obra", type="primary", use_container_width=True):
            if not nome: st.error("O campo 'Nome da Obra' é obrigatório.")
            else:
                if cadastrar_obra(nome, endereco, data_inicio, data_fim_prevista, status, valor, responsavel, obs):
                    st.success(f"Obra '{nome}' cadastrada com sucesso!"); st.cache_data.clear()