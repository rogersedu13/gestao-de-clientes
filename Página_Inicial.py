# Página_Inicial.py
import streamlit as st
from supabase import create_client, Client
from utils import get_supabase_client

# --- Configuração da Página ---
# Usamos layout="wide" para aproveitar melhor o espaço das colunas
st.set_page_config(page_title="Gestão de Clientes | Construtora", page_icon="🏗️", layout="wide")

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
    
    # --- NOVO LAYOUT DA TELA DE LOGIN ---
    
    st.markdown("<br><br>", unsafe_allow_html=True) # Espaçamento vertical
    
    col1, col2 = st.columns([0.8, 1])

    with col1:
        st.image("https://placehold.co/400x200/FFFFFF/000000?text=Logo+da+Empresa", use_column_width=True)
        st.title("Sistema de Gestão")
        st.subheader("Construtora")
        st.markdown("---")
        st.markdown("""
        Bem-vindo ao portal de gestão. 
        Por favor, faca o login para acessar o painel.
        """)

    with col2:
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
    # Se já estiver logado, a página inicial mostra uma mensagem simples
    st.title(f"Bem-vindo(a) de volta, {st.session_state.user_email.split('@')[0]}!")
    st.markdown("---")
    st.info("👈 Use o menu na barra lateral para navegar entre as seções do sistema.")
    st.image("https://images.unsplash.com/photo-1581092446347-a70c323f412c?q=80&w=2070&auto=format&fit=crop",
             caption="O controle de suas obras e finanças em um só lugar.",
             use_column_width=True)