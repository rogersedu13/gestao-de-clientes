# pages/2_Clientes.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Funções de Utilidade Essenciais ---
def conectar_supabase() -> Client:
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception:
        st.error("🚨 **Erro de Conexão:** Verifique as credenciais do Supabase nos Secrets.")
        st.stop()

def check_auth(pagina: str = "esta página"):
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning(f"🔒 Por favor, faça o login para acessar {pagina}.")
        st.stop()

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Clientes", layout="wide", page_icon="👥")
check_auth("a área de Clientes")
supabase = conectar_supabase()

# --- Funções da Página ---
@st.cache_data(ttl=60)
def carregar_clientes():
    response = supabase.table('clientes').select('*').order('nome').execute()
    return pd.DataFrame(response.data)

def cadastrar_cliente(nome, cpf_cnpj, telefone, email, obs):
    try:
        supabase.table('clientes').insert({
            'nome': nome, 'cpf_cnpj': cpf_cnpj, 'contato_telefone': telefone,
            'contato_email': email, 'observacoes': obs
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar cliente: {e}"); return False

# --- Construção da Página ---
st.image("https://placehold.co/1200x200/2337D9/FFFFFF?text=Gestão+de+Clientes", use_container_width=True)
st.title("👥 Gestão de Clientes")
st.markdown("Cadastre, visualize e gerencie todos os seus clientes.")

tab1, tab2 = st.tabs(["📋 Listar Clientes", "➕ Cadastrar Novo Cliente"])

with tab1:
    st.subheader("Clientes Cadastrados")
    df_clientes = carregar_clientes()
    if df_clientes.empty:
        st.info("Nenhum cliente cadastrado. Adicione um na aba ao lado.")
    else:
        busca = st.text_input("Buscar cliente pelo nome...")
        if busca:
            df_clientes = df_clientes[df_clientes['nome'].str.contains(busca, case=False)]
        for _, row in df_clientes.iterrows():
            with st.expander(f"**{row['nome']}** (CPF/CNPJ: {row.get('cpf_cnpj', 'N/A')})"):
                st.markdown(f"**Email:** {row.get('contato_email', 'N/A')}")
                st.markdown(f"**Telefone:** {row.get('contato_telefone', 'N/A')}")
                st.markdown("**Observações:**"); st.info(row.get('observacoes', 'Nenhuma observação.'))

with tab2:
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
                    st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                    st.cache_data.clear()