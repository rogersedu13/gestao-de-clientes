# utils.py
import streamlit as st
from supabase import create_client, Client

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