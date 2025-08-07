# utils.py
import streamlit as st
from supabase import create_client, Client
import pandas as pd

def get_supabase_client() -> Client:
    """
    Cria uma conexão na primeira vez ou retorna a conexão já autenticada
    que está guardada na memória da sessão. Esta é a chave da solução.
    """
    if 'supabase_client' in st.session_state:
        return st.session_state.supabase_client

    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        client = create_client(url, key)
        st.session_state.supabase_client = client
        return client
    except Exception:
        st.error("🚨 **Erro de Conexão:** Verifique as credenciais do Supabase nos Secrets.")
        st.stop()

def check_auth(pagina: str = "esta página"):
    """Verifica se o usuário está logado. Se não, para a execução."""
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning(f"🔒 Por favor, faça o login para acessar {pagina}.")
        st.stop()

def formatar_moeda(valor):
    """Formata um número para o padrão de moeda brasileiro."""
    if valor is None: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")