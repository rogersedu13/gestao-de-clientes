# Página_Inicial.py
import streamlit as st
from supabase import create_client, Client
from utils import get_supabase_client
from datetime import timedelta

# --- Configuração da Página ---
st.set_page_config(page_title="Sistema de Gestão", page_icon="🏗️", layout="wide")

# --- Conexão e Autenticação ---
supabase = get_supabase_client()

# Lógica para tentar restaurar a sessão a partir do cache do Streamlit
if 'user_session' in st.session_state:
    try:
        supabase.auth.set_session(st.session_state.user_session['access_token'], st.session_state.user_session['refresh_token'])
        st.session_state.logged_in = True
    except Exception:
        st.session_state.logged_in = False
elif 'logged_in' not in st.session_state:
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
        st.info("Por favor, faça o login para acessar o sistema.")
    st.markdown("---")
    st.info("Desenvolvido por @Rogerio Souza")


# --- LÓGICA PRINCIPAL: MOSTRA LOGIN OU MENSAGEM DE BOAS-VINDAS PÓS-LOGIN ---

if not st.session_state.logged_in:
    
    # --- LAYOUT VERTICAL DA TELA DE LOGIN ---
    
    st.markdown("<br>", unsafe_allow_html=True) 

    # Textos de boas-vindas centralizados
    st.markdown("<h1 style='text-align: center;'>Sistema de Gestão</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #808080;'>Gestão de Clientes, Obras e Finanças.</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Centraliza o formulário de login usando colunas
    _ , col_login, _ = st.columns([1, 1.5, 1])

    with col_login:
        with st.container(border=True):
            st.header("Acesso ao Painel")
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
                            st.session_state.user_session = {
                                "access_token": user_session_obj.session.access_token,
                                "refresh_token": user_session_obj.session.refresh_token
                            }
                            st.rerun() 
                        except Exception as e:
                            st.error("Falha no login. Verifique seu email e senha.")
else:
    # <<<<===== AQUI ESTÁ A MUDANÇA =====>>>>
    # Se já estiver logado, a página inicial mostra esta mensagem simples e limpa
    st.title(f"Bem-vindo(a) de volta, {st.session_state.user_email.split('@')[0]}!")
    st.markdown("---")
    st.info("👈 Use o menu na barra lateral para navegar entre as seções do sistema.")
    # A imagem e outros textos foram removidos para deixar a tela mais limpa.