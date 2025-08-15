# pages/2_Clientes.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import re
from utils import check_auth, get_supabase_client

# --- Funções de Utilidade Essenciais ---
def sanitizar_nome_arquivo(nome_arquivo: str) -> str:
    """Remove caracteres especiais e espaços de um nome de arquivo."""
    nome_limpo = re.sub(r'[^\w\.\-]', '_', nome_arquivo)
    return nome_limpo

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Clientes", layout="wide", page_icon="👥")
check_auth("a área de Clientes")
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
def carregar_clientes_ativos():
    response = supabase.table('clientes').select('*').eq('ativo', True).order('nome').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_clientes_arquivados():
    response = supabase.rpc('get_clientes_arquivados').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=30)
def carregar_contratos(cliente_id):
    """Carrega os contratos de um cliente específico."""
    response = supabase.table('contratos').select('*').eq('cliente_id', cliente_id).order('data_upload', desc=True).execute()
    return pd.DataFrame(response.data)

# <<<<===== FUNÇÃO ATUALIZADA PARA LIDAR COM O ANEXO JUNTO =====>>>>
def cadastrar_cliente_e_contrato(nome, cpf_cnpj, telefone, email, obs, descricao_contrato, arquivo_contrato):
    try:
        # 1. Insere o cliente primeiro para obter o ID
        cliente_data = {
            'nome': nome, 'cpf_cnpj': cpf_cnpj, 'contato_telefone': telefone,
            'contato_email': email, 'observacoes': obs
        }
        response = supabase.table('clientes').insert(cliente_data, count='exact').execute()
        novo_cliente_id = response.data[0]['id']

        # 2. Se um arquivo de contrato foi enviado, faz o upload e o vincula
        if arquivo_contrato:
            if not descricao_contrato:
                st.error("A descrição é obrigatória ao anexar um contrato.")
                return False

            nome_sanitizado = sanitizar_nome_arquivo(arquivo_contrato.name)
            file_path = f"contratos_clientes/{novo_cliente_id}_{nome_sanitizado}"
            
            supabase.storage.from_("comprovantes").upload(file=arquivo_contrato.getvalue(), path=file_path, file_options={"content-type": arquivo_contrato.type})
            url_contrato = supabase.storage.from_('comprovantes').get_public_url(file_path)
            
            supabase.table('contratos').insert({
                'cliente_id': novo_cliente_id,
                'descricao': descricao_contrato,
                'contrato_url': url_contrato
            }).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar cliente: {e}"); return False

def arquivar_cliente(cliente_id):
    try:
        supabase.rpc('arquivar_cliente', {'p_cliente_id': cliente_id}).execute(); return True
    except Exception as e:
        st.error(f"Erro ao arquivar cliente: {e}"); return False

def reativar_cliente(cliente_id):
    try:
        supabase.rpc('reativar_cliente', {'p_cliente_id': cliente_id}).execute(); return True
    except Exception as e:
        st.error(f"Erro ao reativar cliente: {e}"); return False

# --- Construção da Página ---
st.image("https://placehold.co/1200x200/2337D9/FFFFFF?text=Gestão+de+Clientes", use_container_width=True)
st.title("👥 Gestão de Clientes")
st.markdown("Cadastre, visualize, gerencie clientes e seus contratos.")

tab_principal_1, tab_principal_2 = st.tabs(["📋 Gerenciar Clientes", "➕ Cadastrar Novo Cliente"])

with tab_principal_1:
    tab_ativos, tab_arquivados = st.tabs(["Clientes Ativos", "Clientes Arquivados"])

    with tab_ativos:
        st.subheader("Clientes Ativos")
        df_clientes_ativos = carregar_clientes_ativos()
        if df_clientes_ativos.empty:
            st.info("Nenhum cliente ativo encontrado.")
        else:
            busca = st.text_input("Buscar cliente ativo pelo nome...", key="busca_ativos")
            if busca:
                df_clientes_ativos = df_clientes_ativos[df_clientes_ativos['nome'].str.contains(busca, case=False)]
            for _, row in df_clientes_ativos.iterrows():
                with st.expander(f"**{row['nome']}** (CPF/CNPJ: {row.get('cpf_cnpj', 'N/A')})"):
                    st.markdown(f"**Email:** {row.get('contato_email', 'N/A')}")
                    st.markdown(f"**Telefone:** {row.get('contato_telefone', 'N/A')}")
                    st.markdown("**Observações:**"); st.info(row.get('observacoes', 'Nenhuma observação.'))
                    
                    st.markdown("---")
                    st.subheader("Contratos Anexados")
                    
                    df_contratos = carregar_contratos(row['id'])
                    if df_contratos.empty:
                        st.write("Nenhum contrato anexado para este cliente.")
                    else:
                        for _, contrato in df_contratos.iterrows():
                            cols_contrato = st.columns([3, 1])
                            with cols_contrato[0]:
                                st.write(contrato['descricao'])
                                st.caption(f"Adicionado em: {pd.to_datetime(contrato['data_upload']).strftime('%d/%m/%Y')}")
                            with cols_contrato[1]:
                                st.link_button("Visualizar Contrato", url=contrato['contrato_url'], use_container_width=True)
                    
                    # O popover para anexar foi REMOVIDO daqui e movido para o formulário de cadastro.
                    
                    st.markdown("---")
                    if st.button("Arquivar Cliente", key=f"arquivar_{row['id']}", type="secondary"):
                        if arquivar_cliente(row['id']):
                            st.success(f"Cliente '{row['nome']}' arquivado com sucesso.")
                            st.cache_data.clear(); st.rerun()

    with tab_arquivados:
        st.subheader("Clientes Arquivados")
        df_clientes_arquivados = carregar_clientes_arquivados()
        if df_clientes_arquivados.empty:
            st.info("Nenhum cliente arquivado.")
        else:
            for _, row in df_clientes_arquivados.iterrows():
                with st.expander(f"**{row['nome']}** (CPF/CNPJ: {row.get('cpf_cnpj', 'N/A')})"):
                    st.markdown(f"**Email:** {row.get('contato_email', 'N/A')}")
                    st.markdown(f"**Telefone:** {row.get('contato_telefone', 'N/A')}")
                    st.markdown("---")
                    if st.button("Reativar Cliente", key=f"reativar_{row['id']}", type="primary"):
                        if reativar_cliente(row['id']):
                            st.success(f"Cliente '{row['nome']}' reativado com sucesso."); st.cache_data.clear(); st.rerun()

with tab_principal_2:
    st.subheader("Cadastrar Novo Cliente")
    with st.form("cadastro_cliente_form", clear_on_submit=True):
        st.markdown("##### Dados Cadastrais")
        nome = st.text_input("Nome / Razão Social*", help="Campo obrigatório")
        cpf_cnpj = st.text_input("CPF / CNPJ")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        obs = st.text_area("Observações Gerais")

        st.markdown("---")
        st.markdown("##### Anexo de Contrato (Opcional)")
        
        # <<<<===== CAMPOS DE ANEXO MOVIDOS PARA CÁ =====>>>>
        descricao_contrato = st.text_input("Descrição do Contrato (Ex: Venda Apto 101)")
        arquivo_contrato = st.file_uploader("Selecione o arquivo do contrato (PDF)", type=['pdf'])
        
        if st.form_submit_button("Salvar Novo Cliente", type="primary", use_container_width=True):
            if not nome:
                st.error("O campo 'Nome / Razão Social' é obrigatório.")
            else:
                if cadastrar_cliente_e_contrato(nome, cpf_cnpj, telefone, email, obs, descricao_contrato, arquivo_contrato):
                    st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                    st.cache_data.clear()