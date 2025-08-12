# pages/6_Contas_a_Pagar.py
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
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
def carregar_obras_ativas():
    response = supabase.table('obras').select('id, nome_obra').eq('ativo', True).order('nome_obra').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=30)
def carregar_contas_a_pagar():
    response = supabase.table('contas_a_pagar').select('*, fornecedores(nome_razao_social), obras(nome_obra)').order('data_vencimento').execute()
    return pd.DataFrame(response.data)

def registrar_pagamento_conta(conta_id, data_pagamento, comprovante_file):
    try:
        url_comprovante = None
        if comprovante_file:
            nome_sanitizado = sanitizar_nome_arquivo(comprovante_file.name)
            file_path = f"comprovantes_pagar/{conta_id}_{nome_sanitizado}"
            supabase.storage.from_("comprovantes").upload(file=comprovante_file.getvalue(), path=file_path, file_options={"content-type": comprovante_file.type})
            url_comprovante = supabase.storage.from_('comprovantes').get_public_url(file_path)
        
        update_data = {
            'status': 'Paga', 'data_pagamento': data_pagamento.strftime('%Y-%m-%d'),
            'comprovante_url': url_comprovante
        }
        supabase.table('contas_a_pagar').update(update_data).eq('id', conta_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar pagamento: {e}"); return False

# --- Construção da Página ---
st.image("https://placehold.co/1200x200/d9534f/FFFFFF?text=Contas+a+Pagar", use_container_width=True)
st.title("🧾 Gestão de Contas a Pagar")
st.markdown("Cadastre e controle todas as despesas e contas a pagar da construtora.")

tab_painel, tab_lancar, tab_fornecedores = st.tabs(["Painel de Despesas", "Lançar Nova Despesa", "Gerenciar Fornecedores"])

with tab_painel:
    st.subheader("Painel Geral de Despesas")
    df_contas = carregar_contas_a_pagar()

    if df_contas.empty:
        st.info("Nenhuma conta a pagar registrada.")
    else:
        df_contas['nome_fornecedor'] = df_contas['fornecedores'].apply(lambda x: x['nome_razao_social'] if isinstance(x, dict) else 'N/A')
        df_contas['nome_obra'] = df_contas['obras'].apply(lambda x: x['nome_obra'] if isinstance(x, dict) else 'N/A')
        
        # Filtros
        status_filtro = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Paga", "Atrasado"])
        if status_filtro != "Todos":
            df_contas = df_contas[df_contas['status'] == status_filtro]
        
        for _, conta in df_contas.iterrows():
            cor = "blue"
            if conta['status'] == 'Paga': cor = "green"
            if conta['status'] == 'Atrasado': cor = "red"
            st.markdown(f"<hr style='border: 1px solid {cor};'>", unsafe_allow_html=True)
            
            cols = st.columns([3, 2, 1, 2])
            cols[0].markdown(f"**Descrição:** {conta['descricao']}")
            cols[0].caption(f"**Fornecedor:** {conta['nome_fornecedor']} | **Obra:** {conta.get('nome_obra', 'N/A')}")
            cols[1].markdown(f"**Valor:** {formatar_moeda(conta['valor'])}")
            cols[2].markdown(f"**Vencimento:** {pd.to_datetime(conta['data_vencimento']).strftime('%d/%m/%Y')}")

            if conta['status'] == 'Paga':
                cols[3].success(f"✅ Pago em {pd.to_datetime(conta['data_pagamento']).strftime('%d/%m/%Y')}")
                if conta.get('comprovante_url'):
                    cols[3].link_button("Ver Comprovante", url=conta['comprovante_url'])
            elif conta['status'] == 'Atrasado':
                cols[3].error("🔴 Atrasado")
            else: # Pendente
                cols[3].warning("🟡 Pendente")
            
            if conta['status'] != 'Paga':
                with cols[3].popover("Registrar Pagamento", use_container_width=True):
                    with st.form(key=f"form_pgto_{conta['id']}", clear_on_submit=True):
                        st.markdown(f"Pagando: **{conta['descricao']}**")
                        data_pgto = st.date_input("Data do Pagamento", date.today())
                        comp = st.file_uploader("Anexar Comprovante", type=['pdf', 'jpg', 'png'])
                        if st.form_submit_button("Confirmar Pagamento", type="primary"):
                            registrar_pagamento_conta(conta['id'], data_pgto, comp)
                            st.success("Pagamento registrado!")
                            st.cache_data.clear(); st.rerun()

with tab_lancar:
    st.subheader("Lançar Nova Despesa")
    df_fornecedores = carregar_fornecedores_ativos()
    df_obras = carregar_obras_ativas()

    if df_fornecedores.empty:
        st.warning("É necessário cadastrar um fornecedor primeiro na aba 'Gerenciar Fornecedores'.")
    else:
        fornecedores_dict = pd.Series(df_fornecedores.id.values, index=df_fornecedores.nome_razao_social).to_dict()
        obras_dict = pd.Series(df_obras.id.values, index=df_obras.nome_obra).to_dict()

        with st.form("nova_conta_form", clear_on_submit=True):
            descricao = st.text_input("Descrição da Despesa*")
            valor = st.number_input("Valor Total (R$)*", min_value=0.01, format="%.2f")
            data_vencimento = st.date_input("Data de Vencimento*", date.today())
            
            c1, c2 = st.columns(2)
            fornecedor_selecionado = c1.selectbox("Fornecedor*", options=fornecedores_dict.keys())
            obra_selecionada = c2.selectbox("Vincular à Obra (Opcional)", options=["Nenhuma"] + list(obras_dict.keys()))
            
            categoria = st.selectbox("Categoria", ["Material", "Mão de Obra", "Impostos", "Maquinário", "Marketing", "Outros"])
            nota_fiscal = st.file_uploader("Anexar Nota Fiscal/Boleto", type=['pdf', 'jpg', 'png'])

            if st.form_submit_button("Lançar Despesa", use_container_width=True, type="primary"):
                if not all([descricao, valor, data_vencimento, fornecedor_selecionado]):
                    st.error("Preencha os campos obrigatórios (*).")
                else:
                    fornecedor_id = fornecedores_dict.get(fornecedor_selecionado)
                    obra_id = obras_dict.get(obra_selecionada) # Será None se 'Nenhuma'
                    
                    url_nf = None
                    if nota_fiscal:
                        path_nf = f"notas_fiscais/{fornecedor_id}_{sanitizar_nome_arquivo(nota_fiscal.name)}"
                        supabase.storage.from_("comprovantes").upload(file=nota_fiscal.getvalue(), path=path_nf, file_options={"content-type": nota_fiscal.type})
                        url_nf = supabase.storage.from_('comprovantes').get_public_url(path_nf)

                    conta_data = {
                        'descricao': descricao, 'valor': valor, 'data_vencimento': data_vencimento.strftime('%Y-%m-%d'),
                        'fornecedor_id': fornecedor_id, 'obra_id': obra_id, 'categoria': categoria,
                        'nota_fiscal_url': url_nf
                    }
                    try:
                        supabase.table('contas_a_pagar').insert(conta_data).execute()
                        st.success("Nova conta a pagar lançada com sucesso!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro ao lançar conta: {e}")

with tab_fornecedores:
    # A lógica de Gerenciar Fornecedores (CRUD, Arquivar/Reativar) pode ser implementada aqui.
    # Por simplicidade, esta parte é similar à de Gerenciar Clientes e pode ser adicionada depois.
    st.info("A funcionalidade completa de gerenciar fornecedores (arquivar, reativar) será adicionada em uma próxima versão.")
    st.subheader("Cadastrar Novo Fornecedor")
    # Adicionar um formulário simples para cadastro rápido