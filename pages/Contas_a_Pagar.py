# pages/Contas_a_Pagar.py
import streamlit as st
import pandas as pd
from datetime import date
import re
from utils import check_auth, get_supabase_client, formatar_moeda

# --- Funções de Utilidade ---
def sanitizar_nome_arquivo(nome_arquivo: str) -> str:
    nome_limpo = re.sub(r'[^\w\.\-]', '_', nome_arquivo)
    return nome_limpo

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Contas a Pagar", layout="wide", page_icon="🧾")
check_auth("a área de Contas a Pagar")
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
def carregar_fornecedores_ativos():
    response = supabase.table('fornecedores').select('*').eq('ativo', True).order('nome_razao_social').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_fornecedores_arquivados():
    response = supabase.table('fornecedores').select('*').eq('ativo', False).order('nome_razao_social').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_obras_ativas():
    response = supabase.table('obras').select('id, nome_obra').eq('ativo', True).order('nome_obra').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=30)
def carregar_contas_a_pagar():
    try:
        supabase.rpc('atualizar_status_parcelas').execute() # Atualiza status de contas a pagar também, se a função for adaptada
    except: pass # Ignora erro se a função não for para contas a pagar
    response = supabase.table('contas_a_pagar').select('*, fornecedores(nome_razao_social), obras(nome_obra)').order('data_vencimento').execute()
    return pd.DataFrame(response.data)

def cadastrar_fornecedor(nome, cpf_cnpj, contato, tipo_servico):
    try:
        supabase.table('fornecedores').insert({'nome_razao_social': nome, 'cpf_cnpj': cpf_cnpj, 'contato_principal': contato, 'tipo_servico': tipo_servico}).execute()
        return True
    except Exception as e: st.error(f"Erro ao cadastrar fornecedor: {e}"); return False

def arquivar_fornecedor(fornecedor_id):
    try:
        supabase.rpc('arquivar_fornecedor', {'p_fornecedor_id': fornecedor_id}).execute(); return True
    except Exception as e: st.error(f"Erro ao arquivar fornecedor: {e}"); return False

def reativar_fornecedor(fornecedor_id):
    try:
        supabase.rpc('reativar_fornecedor', {'p_fornecedor_id': fornecedor_id}).execute(); return True
    except Exception as e: st.error(f"Erro ao reativar fornecedor: {e}"); return False

def registrar_pagamento_conta(conta_id, data_pagamento, comprovante_file):
    # (Esta função e outras lógicas permanecem as mesmas da versão anterior)
    # ... (código omitido por brevidade, mas deve ser mantido como estava)
    pass


# --- Construção da Página ---
st.image("https://placehold.co/1200x200/d9534f/FFFFFF?text=Contas+a+Pagar", use_container_width=True)
st.title("🧾 Gestão de Contas a Pagar")
st.markdown("Cadastre e controle todas as despesas e contas a pagar da construtora.")

tab_painel, tab_lancar, tab_fornecedores = st.tabs(["Painel de Despesas", "Lançar Nova Despesa", "Gerenciar Fornecedores"])

with tab_painel:
    # (Código do Painel de Despesas permanece o mesmo)
    pass

with tab_lancar:
    # (Código para Lançar Despesa permanece o mesmo)
    pass

# <<<<===== AQUI ESTÁ A IMPLEMENTAÇÃO COMPLETA =====>>>>
with tab_fornecedores:
    st.subheader("Gerenciar Cadastro de Fornecedores")
    tab_forn_ativos, tab_forn_arquivados = st.tabs(["Fornecedores Ativos", "Fornecedores Arquivados"])

    with tab_forn_ativos:
        df_fornecedores_ativos = carregar_fornecedores_ativos()
        st.markdown(f"**Total de fornecedores ativos:** {len(df_fornecedores_ativos)}")
        for _, row in df_fornecedores_ativos.iterrows():
            with st.expander(f"{row['nome_razao_social']}"):
                st.write(f"**CPF/CNPJ:** {row.get('cpf_cnpj', 'N/A')}")
                st.write(f"**Contato:** {row.get('contato_principal', 'N/A')}")
                st.write(f"**Tipo de Serviço:** {row.get('tipo_servico', 'N/A')}")
                if st.button("Arquivar Fornecedor", key=f"arquivar_forn_{row['id']}", type="secondary"):
                    arquivar_fornecedor(row['id'])
                    st.success(f"Fornecedor '{row['nome_razao_social']}' arquivado.")
                    st.cache_data.clear(); st.rerun()
    
    with tab_forn_arquivados:
        df_fornecedores_arquivados = carregar_fornecedores_arquivados()
        st.markdown(f"**Total de fornecedores arquivados:** {len(df_fornecedores_arquivados)}")
        for _, row in df_fornecedores_arquivados.iterrows():
            with st.expander(f"{row['nome_razao_social']}"):
                st.write(f"**CPF/CNPJ:** {row.get('cpf_cnpj', 'N/A')}")
                if st.button("Reativar Fornecedor", key=f"reativar_forn_{row['id']}", type="primary"):
                    reativar_fornecedor(row['id'])
                    st.success(f"Fornecedor '{row['nome_razao_social']}' reativado.")
                    st.cache_data.clear(); st.rerun()

    st.markdown("---")
    with st.form("novo_fornecedor_form", clear_on_submit=True):
        st.subheader("Cadastrar Novo Fornecedor")
        c1, c2 = st.columns(2)
        nome_forn = c1.text_input("Nome / Razão Social*")
        cpf_cnpj_forn = c2.text_input("CPF / CNPJ")
        contato_forn = c1.text_input("Contato (Telefone/Email)")
        tipo_servico_forn = c2.text_input("Tipo de Serviço/Material")
        if st.form_submit_button("Salvar Novo Fornecedor", use_container_width=True, type="primary"):
            if not nome_forn:
                st.error("O campo 'Nome / Razão Social' é obrigatório.")
            else:
                if cadastrar_fornecedor(nome_forn, cpf_cnpj_forn, contato_forn, tipo_servico_forn):
                    st.success("Fornecedor cadastrado com sucesso!")
                    st.cache_data.clear()