# app.py
import streamlit as st
from utils import conectar_supabase

st.set_page_config(
    page_title="Gestão de Clientes | Construtora",
    page_icon="🏗️",
    layout="centered"
)

# --- Inicialização ---
supabase = conectar_supabase()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- Tela de Login ---
st.title("🏗️ Sistema de Gestão de Clientes")
st.subheader("Acesso ao Painel da Construtora")

if not st.session_state.logged_in:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            with st.spinner("Autenticando..."):
                try:
                    user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.logged_in = True
                    st.session_state.user_email = user.user.email
                    st.rerun() # Recarrega a página para refletir o estado de login
                except Exception as e:
                    st.error("Falha no login. Verifique seu email e senha.")
                    st.error(e)
else:
    st.success(f"Login realizado com sucesso! Bem-vindo(a), {st.session_state.user_email}.")
    st.markdown("---")
    st.markdown("👈 **Navegue pelo menu lateral para começar.**")

    if st.sidebar.button("Logout", use_container_width=True):
        supabase.auth.sign_out()
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()