# Página_Inicial.py
import streamlit as st
from supabase import create_client, Client
from utils import get_supabase_client # Importa a função atualizada

st.set_page_config(page_title="Sistema de Gestão", page_icon="🏗️", layout="centered")

# A função get_supabase_client agora lida com a restauração da sessão
supabase = get_supabase_client()

# A verificação de login agora é mais simples
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

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
    else:
        st.info("Por favor, faça o login para continuar.")
    st.markdown("---")
    st.info("Desenvolvido por @Rogerio Souza")

# --- Tela de Login ---
st.title("🏗️ Sistema de Gestão")
st.header("Acesso ao Painel Principal")

if not st.session_state.logged_in:
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")
        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            with st.spinner("Autenticando..."):
                try:
                    user_session_obj = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.logged_in = True
                    st.session_state.user_email = user_session_obj.user.email
                    # Armazena apenas os tokens da sessão para revalidação
                    st.session_state.user_session = {
                        "access_token": user_session_obj.session.access_token,
                        "refresh_token": user_session_obj.session.refresh_token
                    }
                    st.rerun() 
                except Exception as e:
                    st.error("Falha no login. Verifique seu email e senha.")
else:
    st.success(f"Login realizado com sucesso!")
    st.markdown("---")
    st.markdown("👈 **Navegue pelo menu lateral para começar.**")