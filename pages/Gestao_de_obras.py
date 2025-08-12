# pages/5_Gestao_de_Obras.py
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
def carregar_obras():
    response = supabase.table('obras').select('*').eq('ativo', True).order('nome_obra').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_receita_obras():
    # Esta função calcula a receita total vinculada a cada obra
    response = supabase.table('debitos').select('obra_id, valor_total').execute()
    df = pd.DataFrame(response.data)
    if df.empty or 'obra_id' not in df.columns or df['obra_id'].isnull().all():
        return pd.Series(dtype='float64')
    
    # Converte para numérico, tratando erros
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce').fillna(0)
    
    return df.groupby('obra_id')['valor_total'].sum()

def cadastrar_obra(nome, endereco, data_inicio, data_fim, status, valor, responsavel, obs):
    try:
        obra_data = {
            'nome_obra': nome, 'endereco': endereco, 'data_inicio': data_inicio.strftime('%Y-%m-%d'),
            'data_fim_prevista': data_fim.strftime('%Y-%m-%d'), 'status': status, 'valor_obra': valor,
            'responsavel_obra': responsavel, 'observacoes': obs
        }
        supabase.table('obras').insert(obra_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar obra: {e}"); return False

# --- Construção da Página ---
st.image("https://placehold.co/1200x200/f0ad4e/FFFFFF?text=Gestão+de+Obras", use_container_width=True)
st.title("🏗️ Gestão de Obras")
st.markdown("Cadastre e acompanhe o andamento e os indicadores de suas obras.")

tab_painel, tab_cadastro = st.tabs(["Painel de Obras", "Cadastrar Nova Obra"])

with tab_painel:
    st.subheader("Painel Geral das Obras")
    
    df_obras = carregar_obras()
    df_receitas = carregar_receita_obras()

    # Junta as receitas com os dados das obras
    if not df_receitas.empty:
        df_obras = df_obras.merge(df_receitas.rename('receita_total'), left_on='id', right_index=True, how='left')
        df_obras['receita_total'] = df_obras['receita_total'].fillna(0)
    else:
        df_obras['receita_total'] = 0

    # Indicadores Rápidos
    col1, col2 = st.columns(2)
    obras_em_andamento = df_obras[df_obras['status'] == 'Em Andamento'].shape[0]
    col1.metric("Obras em Andamento", obras_em_andamento)
    
    orcamento_total = df_obras['valor_obra'].sum()
    col2.metric("Valor Total das Obras", formatar_moeda(orcamento_total))

    st.markdown("---")
    st.subheader("Lista de Obras")

    if df_obras.empty:
        st.info("Nenhuma obra cadastrada. Adicione uma na aba 'Cadastrar Nova Obra'.")
    else:
        for _, row in df_obras.iterrows():
            with st.expander(f"**{row['nome_obra']}** | Status: {row['status']}"):
                cols = st.columns(4)
                cols[0].markdown(f"**Responsável:**<br>{row.get('responsavel_obra', 'N/A')}", unsafe_allow_html=True)
                cols[1].markdown(f"**Início:**<br>{pd.to_datetime(row['data_inicio']).strftime('%d/%m/%Y') if row.get('data_inicio') else 'N/A'}", unsafe_allow_html=True)
                cols[2].markdown(f"**Valor da Obra:**<br>{formatar_moeda(row.get('valor_obra'))}", unsafe_allow_html=True)
                cols[3].markdown(f"**Receita Vinculada:**<br>{formatar_moeda(row.get('receita_total'))}", unsafe_allow_html=True)
                # O botão "Ver Detalhes" pode ser implementado no futuro
                # st.button("Ver Detalhes", key=f"detalhes_{row['id']}")

with tab_cadastro:
    st.subheader("Cadastrar Nova Obra")
    with st.form("nova_obra_form", clear_on_submit=True):
        nome = st.text_input("Nome da Obra*", help="Campo obrigatório")
        
        # AQUI ESTAVA O ERRO DE DIGITAÇÃO
        endereco = st.text_input("Endereço da Obra") # Corrigido de "esdereco" para "endereco"
        
        responsavel = st.text_input("Responsável pela Obra (Mestre de Obra)")
        
        col_data1, col_data2 = st.columns(2)
        data_inicio = col_data1.date_input("Data de Início", value=date.today())
        data_fim = col_data2.date_input("Data Prevista de Conclusão", value=date.today() + timedelta(days=365))
        
        col_status, col_valor = st.columns(2)
        status = col_status.selectbox("Status Inicial", ["Planejamento", "Em Andamento", "Pausada", "Finalizada"])
        valor = col_valor.number_input("Valor da Obra (R$)", min_value=0.0, format="%.2f")
        
        obs = st.text_area("Observações")
        
        if st.form_submit_button("Salvar Nova Obra", type="primary", use_container_width=True):
            if not nome:
                st.error("O campo 'Nome da Obra' é obrigatório.")
            else:
                if cadastrar_obra(nome, endereco, data_inicio, data_fim, status, valor, responsavel, obs):
                    st.success(f"Obra '{nome}' cadastrada com sucesso!")
                    st.cache_data.clear()