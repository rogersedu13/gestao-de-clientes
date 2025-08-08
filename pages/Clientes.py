# pages/2_Clientes.py
import streamlit as st
import pandas as pd
from utils import check_auth, get_supabase_client

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Clientes", layout="wide", page_icon="👥")
supabase = get_supabase_client() # Pega/cria a conexão e restaura a sessão
check_auth("a área de Clientes")

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

# ... (O resto do código de Clientes permanece o mesmo)
@st.cache_data(ttl=60)
def carregar_clientes_ativos():
    response = supabase.table('clientes').select('*').eq('ativo', True).order('nome').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_clientes_arquivados():
    response = supabase.rpc('get_clientes_arquivados').execute()
    return pd.DataFrame(response.data)

def cadastrar_cliente(nome, cpf_cnpj, telefone, email, obs):
    try:
        supabase.table('clientes').insert({'nome': nome, 'cpf_cnpj': cpf_cnpj, 'contato_telefone': telefone, 'contato_email': email, 'observacoes': obs}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar cliente: {e}"); return False

def arquivar_cliente(cliente_id):
    try:
        supabase.rpc('arquivar_cliente', {'p_cliente_id': cliente_id}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao arquivar cliente: {e}"); return False

def reativar_cliente(cliente_id):
    try:
        supabase.rpc('reativar_cliente', {'p_cliente_id': cliente_id}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao reativar cliente: {e}"); return False

st.image("https://placehold.co/1200x200/2337D9/FFFFFF?text=Gestão+de+Clientes", use_container_width=True)
st.title("👥 Gestão de Clientes")
st.markdown("Cadastre, visualize e gerencie todos os seus clientes.")

tab_principal_1, tab_principal_2 = st.tabs(["📋 Gerenciar Clientes", "➕ Cadastrar Novo Cliente"])
with tab_principal_1:
    tab_ativos, tab_arquivados = st.tabs(["Clientes Ativos", "Clientes Arquivados"])
    with tab_ativos:
        st.subheader("Clientes Ativos")
        df_clientes_ativos = carregar_clientes_ativos()
        if df_clientes_ativos.empty:
            st.info("Nenhum cliente ativo encontrado.")
        else:
            busca = st.text_input("Buscar cliente ativo pelo nome...", key="busca_ativos")
            if busca:
                df_clientes_ativos = df_clientes_ativos[df_clientes_ativos['nome'].str.contains(busca, case=False)]
            for _, row in df_clientes_ativos.iterrows():
                with st.expander(f"**{row['nome']}** (CPF/CNPJ: {row.get('cpf_cnpj', 'N/A')})"):
                    st.markdown(f"**Email:** {row.get('contato_email', 'N/A')}")
                    st.markdown(f"**Telefone:** {row.get('contato_telefone', 'N/A')}")
                    st.markdown("**Observações:**"); st.info(row.get('observacoes', 'Nenhuma observação.'))
                    st.markdown("---")
                    if st.button("Arquivar Cliente", key=f"arquivar_{row['id']}", type="secondary"):
                        if arquivar_cliente(row['id']):
                            st.success(f"Cliente '{row['nome']}' arquivado com sucesso.")
                            st.cache_data.clear(); st.rerun()
    with tab_arquivados:
        st.subheader("Clientes Arquivados")
        df_clientes_arquivados = carregar_clientes_arquivados()
        if df_clientes_arquivados.empty:
            st.info("Nenhum cliente arquivado.")
        else:
            busca_arq = st.text_input("Buscar cliente arquivado pelo nome...", key="busca_arquivados")
            if busca_arq:
                df_clientes_arquivados = df_clientes_arquivados[df_clientes_arquivados['nome'].str.contains(busca_arq, case=False)]
            for _, row in df_clientes_arquivados.iterrows():
                with st.expander(f"**{row['nome']}** (CPF/CNPJ: {row.get('cpf_cnpj', 'N/A')})"):
                    st.markdown(f"**Email:** {row.get('contato_email', 'N/A')}")
                    st.markdown(f"**Telefone:** {row.get('contato_telefone', 'N/A')}")
                    st.markdown("**Observações:**"); st.info(row.get('observacoes', 'Nenhuma observação.'))
                    st.markdown("---")
                    if st.button("Reativar Cliente", key=f"reativar_{row['id']}", type="primary"):
                        if reativar_cliente(row['id']):
                            st.success(f"Cliente '{row['nome']}' reativado com sucesso.")
                            st.cache_data.clear(); st.rerun()
with tab_principal_2:
    st.subheader("Cadastrar Novo Cliente")
    with st.form("cadastro_cliente_form", clear_on_submit=True):
        nome = st.text_input("Nome / Razão Social*", help="Campo obrigatório")
        cpf_cnpj = st.text_input("CPF / CNPJ")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        obs = st.text_area("Observações")
        if st.form_submit_button("Cadastrar Cliente", type="primary", use_container_width=True):
            if not nome:
                st.error("O campo 'Nome / Razão Social' é obrigatório.")
            else:
                if cadastrar_cliente(nome, cpf_cnpj, telefone, email, obs):
                    st.success(f"Cliente '{nome}' cadastrado com sucesso!"); st.cache_data.clear()