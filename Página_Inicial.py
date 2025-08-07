# Página_Inicial.py
import streamlit as st
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

# --- Configuração da Página ---
st.set_page_config(
    page_title="Gestão de Clientes",
    page_icon="🏗️",
    layout="centered"
)

# --- Inicialização ---
supabase = conectar_supabase()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- Lógica da Sidebar ---
with st.sidebar:
    st.header("Modo de Acesso")
    if st.session_state.logged_in:
        st.success(f"Logado como: {st.session_state.user_email}")
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    else:
        st.info("Por favor, faça o login para continuar.")
    
    # --- Créditos no Rodapé da Sidebar ---
    st.markdown("---")
    st.info("Desenvolvido por @Rogerio Souza")


# --- Tela de Login ---
st.title("🏗️ Sistema de Gestão de Clientes")
st.header("Acesso ao Painel")

if not st.session_state.logged_in:
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")
        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            with st.spinner("Autenticando..."):
                try:
                    user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.logged_in = True
                    st.session_state.user_email = user.user.email
                    st.rerun() 
                except Exception as e:
                    st.error("Falha no login. Verifique seu email e senha.")
else:
    st.success(f"Login realizado com sucesso!")
    st.markdown("---")
    st.markdown("👈 **Navegue pelo menu lateral para começar.**")