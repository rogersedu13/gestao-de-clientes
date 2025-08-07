# utils.py
import streamlit as st
from supabase import create_client, Client

# NOVA FUNÇÃO DE DESIGN
def load_custom_css():
    """Carrega um CSS customizado para dar um look & feel profissional."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

        /* Variaveis de Cor */
        :root {
            --primary-color: #2337D9; /* Azul principal */
            --background-color: #0F1116; /* Fundo escuro */
            --card-background-color: #1A1C24; /* Fundo dos cards */
            --text-color: #FAFAFA; /* Texto principal */
            --subtle-text-color: #A0A4B8; /* Texto sutil */
            --border-color: #333748;
        }

        /* Estilo Geral */
        body, .stApp {
            font-family: 'Source Sans Pro', sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
        }

        /* Títulos */
        h1, h2, h3 {
            color: var(--primary-color);
            font-weight: 700;
        }

        /* Cards e Containers */
        .st-emotion-cache-1r4qj8v, .st-emotion-cache-1xw8zdv, [data-testid="stExpander"] {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            padding: 1rem;
        }
        
        [data-testid="stExpander"] > details > summary {
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        /* Botões */
        .stButton > button {
            border-radius: 8px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            transition: background-color 0.2s;
        }
        .stButton > button:hover {
            background-color: #4A5DF2;
        }
        .stButton > button:focus {
            box-shadow: 0 0 0 2px var(--primary-color) !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: var(--card-background-color);
            border-right: 1px solid var(--border-color);
        }

        /* Métricas no Dashboard */
        [data-testid="stMetric"] {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
        }
        [data-testid="stMetric"] > div > div:first-child {
            color: var(--subtle-text-color); /* Label da métrica */
        }
        
        /* Abas (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 44px;
            background-color: transparent;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--card-background-color);
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: var(--primary-color);
            color: white;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


def conectar_supabase() -> Client:
    """Conecta ao Supabase e retorna o objeto do cliente."""
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception:
        st.error("🚨 **Erro de Conexão:** Verifique as credenciais do Supabase nos Secrets.")
        st.stop()

def check_auth(pagina: str = "esta página"):
    """Verifica se o usuário está logado. Se não, para a execução e mostra mensagem."""
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning(f"🔒 Por favor, faça o login para acessar {pagina}.")
        st.stop()

def formatar_moeda(valor):
    """Formata um número para o padrão de moeda brasileiro."""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")