# Página_Inicial.py
import streamlit as st
from supabase import create_client, Client

# --- Funções de Utilidade e Design (Agora dentro de cada arquivo) ---
def load_custom_css():
    st.markdown("""<style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
        :root {
            --primary-color: #2337D9; --background-color: #0F1116; --card-background-color: #1A1C24;
            --text-color: #FAFAFA; --subtle-text-color: #A0A4B8; --border-color: #333748;
        }
        body, .stApp { font-family: 'Source Sans Pro', sans-serif; background-color: var(--background-color); color: var(--text-color); }
        h1, h2, h3 { color: var(--primary-color); font-weight: 700; }
        .st-emotion-cache-1r4qj8v, .st-emotion-cache-1xw8zdv, [data-testid="stExpander"] {
            background-color: var(--card-background-color); border: 1px solid var(--border-color); border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); padding: 1rem;
        }
        [data-testid="stExpander"] > details > summary { font-size: 1.1rem; font-weight: 600; }
        .stButton > button {
            border-radius: 8px; background-color: var(--primary-color); color: white; border: none; transition: background-color 0.2s;
        }
        .stButton > button:hover { background-color: #4A5DF2; }
        .stButton > button:focus { box-shadow: 0 0 0 2px var(--primary-color) !important; }
        [data-testid="stSidebar"] { background-color: var(--card-background-color); border-right: 1px solid var(--border-color); }
        [data-testid="stMetric"] { background-color: var(--card-background-color); border: 1px solid var(--border-color); border-radius: 10px; padding: 1rem; }
        [data-testid="stMetric"] > div > div:first-child { color: var(--subtle-text-color); }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 44px; background-color: transparent; border-radius: 8px; }
        .stTabs [data-baseweb="tab"]:hover { background-color: var(--card-background-color); }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: var(--primary-color); color: white; }
        </style>""", unsafe_allow_html=True)

def conectar_supabase() -> Client:
    try:
        url = st.secrets["supabase_url"]; key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception:
        st.error("🚨 **Erro de Conexão:** Verifique as credenciais do Supabase nos Secrets."); st.stop()

# --- Configuração da Página ---
st.set_page_config(page_title="Gestão de Clientes | Construtora", page_icon="🏗️", layout="centered")
load_custom_css()

# --- Inicialização ---
supabase = conectar_supabase()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- Tela de Login ---
st.title("🏗️ Gestão de Clientes")
st.header("Acesso ao Painel da Construtora")

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
    st.success(f"Login realizado com sucesso! Bem-vindo(a), {st.session_state.user_email}.")
    st.markdown("---")
    st.markdown("👈 **Navegue pelo menu lateral para começar.**")

    if st.sidebar.button("Logout", use_container_width=True):
        supabase.auth.sign_out()
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()