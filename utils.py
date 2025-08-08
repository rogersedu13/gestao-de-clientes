# utils.py
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Esta função agora é responsável por criar um cliente Supabase e
# restaurar a sessão de login, se ela existir.
def get_supabase_client() -> Client:
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    client = create_client(url, key)
    
    # Se uma sessão de usuário estiver salva, restaura ela no cliente
    if 'user_session' in st.session_state:
        try:
            client.auth.set_session(
                st.session_state.user_session['access_token'],
                st.session_state.user_session['refresh_token']
            )
        except Exception as e:
            # Se o token expirar ou der erro, limpa a sessão
            st.warning("Sua sessão expirou. Por favor, faça o login novamente.")
            del st.session_state['user_session']
            del st.session_state['logged_in']
    
    return client

def check_auth(pagina: str = "esta página"):
    """Verifica se o usuário está logado. Se não, para a execução."""
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning(f"🔒 Por favor, faça o login para acessar {pagina}.")
        st.stop()

def formatar_moeda(valor):
    """Formata um número para o padrão de moeda brasileiro."""
    if valor is None: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")