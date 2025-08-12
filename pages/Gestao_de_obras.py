# pages/Gestao_de_Obras.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
from utils import check_auth, get_supabase_client, formatar_moeda

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Gestão de Obras", layout="wide", page_icon="🏗️")
check_auth("a área de Gestão de Obras")
supabase = get_supabase_client()

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
    st.markdown("---"); st.info("Desenvolvido por @Rogerio Souza")

# --- Funções da Página ---
@st.cache_data(ttl=60)
def carregar_obras(_supabase_client: Client) -> pd.DataFrame:
    response = _supabase_client.table('obras').select('*').eq('ativo', True).order('nome_obra').execute()
    return pd.DataFrame(response.data)

def cadastrar_obra(nome, endereco, data_inicio, data_fim_prevista, status, valor, responsavel, obs):
    try:
        obra_data = {
            'nome_obra': nome, 'endereco': endereco, 'data_inicio': data_inicio.strftime('%Y-%m-%d'),
            'data_fim_prevista': data_fim_prevista.strftime('%Y-%m-%d'), 'status': status, 'valor_obra': valor,
            'responsavel_obra': responsavel, 'observacoes': obs
        }
        supabase.table('obras').insert(obra_data).execute(); return True
    except Exception as e:
        st.error(f"Erro ao cadastrar obra: {e}"); return False

# --- Construção da Página ---
st.image("https://placehold.co/1200x200/f0ad4e/FFFFFF?text=Gestão+de+Obras", use_container_width=True)
st.title("🏗️ Gestão de Obras")
st.markdown("Cadastre e acompanhe o andamento de suas obras.")

tab_painel, tab_cadastro = st.tabs(["Painel de Obras", "Cadastrar Nova Obra"])

with tab_painel:
    st.subheader("Lista de Obras Cadastradas")
    
    df_obras = carregar_obras(supabase)

    if df_obras.empty:
        st.info("Nenhuma obra cadastrada. Adicione uma na aba 'Cadastrar Nova Obra'.")
    else:
        for _, row in df_obras.iterrows():
            with st.expander(f"**{row.get('nome_obra', 'N/A')}** | Status: {row.get('status', 'N/A')}"):
                st.markdown(f"**Responsável:** {row.get('responsavel_obra', 'N/A')}")
                st.markdown(f"**Endereço:** {row.get('endereco', 'N/A')}")
                
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"**Início:** {pd.to_datetime(row.get('data_inicio')).strftime('%d/%m/%Y') if row.get('data_inicio') else 'N/A'}")
                col2.markdown(f"**Previsão de Término:** {pd.to_datetime(row.get('data_fim_prevista')).strftime('%d/%m/%Y') if row.get('data_fim_prevista') else 'N/A'}")
                col3.markdown(f"**Valor da Obra:** {formatar_moeda(row.get('valor_obra'))}")
                
                st.markdown("**Observações:**")
                st.info(f"{row.get('observacoes', 'Nenhuma observação.')}")


with tab_cadastro:
    st.subheader("Cadastrar Nova Obra")
    with st.form("nova_obra_form", clear_on_submit=True):
        nome = st.text_input("Nome da Obra*", help="Campo obrigatório")
        endereco = st.text_input("Endereço da Obra")
        responsavel = st.text_input("Responsável pela Obra (Mestre de Obra)")
        
        col_data1, col_data2 = st.columns(2)
        data_inicio = col_data1.date_input("Data de Início", value=date.today())
        data_fim_prevista = col_data2.date_input("Data Prevista de Conclusão", value=date.today() + timedelta(days=365))
        
        col_status, col_valor = st.columns(2)
        status = col_status.selectbox("Status Inicial", ["Planejamento", "Em Andamento", "Pausada", "Finalizada"])
        valor = col_valor.number_input("Valor da Obra (R$)", min_value=0.0, format="%.2f")
        
        obs = st.text_area("Observações")
        
        if st.form_submit_button("Salvar Nova Obra", type="primary", use_container_width=True):
            if not nome: 
                st.error("O campo 'Nome da Obra' é obrigatório.")
            else:
                if cadastrar_obra(nome, endereco, data_inicio, data_fim_prevista, status, valor, responsavel, obs):
                    st.success(f"Obra '{nome}' cadastrada com sucesso!")
                    st.cache_data.clear()