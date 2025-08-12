# pages/4_Corretores.py
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re

# --- Funções de Utilidade Essenciais (Copiadas para autossuficiência) ---
def conectar_supabase() -> Client:
    try:
        url = st.secrets["supabase_url"]; key = st.secrets["supabase_key"]
        return create_client(url, key)
    except Exception:
        st.error("🚨 **Erro de Conexão:** Verifique as credenciais do Supabase nos Secrets."); st.stop()

def check_auth(pagina: str = "esta página"):
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning(f"🔒 Por favor, faça o login para acessar {pagina}."); st.stop()

def formatar_moeda(valor):
    if valor is None: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def sanitizar_nome_arquivo(nome_arquivo: str) -> str:
    nome_limpo = re.sub(r'[^\w\.\-]', '_', nome_arquivo)
    return nome_limpo

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Corretores", layout="wide", page_icon="🤝")
check_auth("a área de Corretores")
supabase = create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])
if 'user_session' in st.session_state:
    supabase.auth.set_session(st.session_state.user_session['access_token'], st.session_state.user_session['refresh_token'])

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
    st.markdown("---")
    st.info("Desenvolvido por @Rogerio Souza")

# --- Funções Específicas da Página ---
@st.cache_data(ttl=60)
def carregar_corretores():
    response = supabase.table('corretores').select('*').eq('ativo', True).order('nome').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_comissoes():
    response = supabase.table('comissoes').select('*, corretores(nome)').order('criado_em', desc=True).execute()
    return pd.DataFrame(response.data)

def gerar_recibo_comissao_pdf(comissao, corretor_nome):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    p.drawString(100, height - 100, "RECIBO DE PAGAMENTO DE COMISSÃO")
    p.drawString(100, height - 120, "--------------------------------------------------")
    p.drawString(100, height - 140, f"Pagamos a: {corretor_nome}")
    p.drawString(100, height - 160, f"O valor de: {formatar_moeda(comissao['valor_comissao'])}")
    p.drawString(100, height - 180, f"Referente a: Comissão da venda - {comissao['descricao_venda']}")
    p.drawString(100, height - 200, f"Data do Pagamento: {pd.to_datetime(comissao['data_pagamento']).strftime('%d/%m/%Y')}")
    p.drawString(100, height - 240, "_________________________")
    p.drawString(100, height - 250, "Assinatura (Construtora)")
    p.showPage(); p.save(); buffer.seek(0)
    return buffer

# --- Construção da Página ---
st.title("🤝 Gestão de Corretores e Comissões")

tab_comissoes, tab_gerenciar_corretores = st.tabs([" Lançar e Visualizar Comissões", " Cadastrar e Gerenciar Corretores"])

with tab_comissoes:
    st.subheader("Lançar Nova Comissão")
    df_corretores = carregar_corretores()

    if df_corretores.empty:
        st.warning("Nenhum corretor ativo cadastrado. Cadastre um corretor na aba 'Cadastrar e Gerenciar Corretores' para começar.")
    else:
        corretores_dict = pd.Series(df_corretores.id.values, index=df_corretores.nome).to_dict()
        with st.form("nova_comissao_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                corretor_selecionado = st.selectbox("Selecione o Corretor*", options=corretores_dict.keys())
                valor_venda = st.number_input("Valor da Venda (R$)*", min_value=0.01, format="%.2f")
                percentual = st.number_input("Percentual da Comissão (%)*", min_value=0.01, max_value=100.0, format="%.2f")
            with col2:
                descricao = st.text_area("Descrição da Venda*", help="Ex: Venda Apto 101 para o cliente João Silva")
            
            submitted = st.form_submit_button("Lançar Comissão", type="primary", use_container_width=True)
            if submitted:
                if not all([corretor_selecionado, valor_venda, percentual, descricao]):
                    st.error("Preencha todos os campos obrigatórios (*).")
                else:
                    corretor_id = corretores_dict[corretor_selecionado]
                    valor_comissao = valor_venda * (percentual / 100)
                    nova_comissao = {
                        "corretor_id": corretor_id, "descricao_venda": descricao,
                        "valor_venda": valor_venda, "percentual_comissao": percentual,
                        "valor_comissao": valor_comissao, "status": "Pendente"
                    }
                    try:
                        supabase.table('comissoes').insert(nova_comissao).execute()
                        st.success(f"Comissão de {formatar_moeda(valor_comissao)} para {corretor_selecionado} lançada com sucesso!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro ao lançar comissão: {e}")

    st.markdown("---")
    st.subheader("Histórico de Comissões")
    
    df_comissoes = carregar_comissoes()
    if df_comissoes.empty:
        st.info("Nenhuma comissão foi lançada ainda.")
    else:
        df_comissoes['nome_corretor'] = df_comissoes['corretores'].apply(lambda x: x['nome'] if isinstance(x, dict) else 'N/A')
        
        filtro_status = st.selectbox("Filtrar por Status:", ["Todas", "Pendente", "Paga"])
        df_filtrado = df_comissoes
        if filtro_status != "Todas":
            df_filtrado = df_comissoes[df_comissoes['status'] == filtro_status]
        
        for _, row in df_filtrado.iterrows():
            with st.expander(f"**{row['nome_corretor']}** - {row['descricao_venda']} - Valor: **{formatar_moeda(row['valor_comissao'])}**"):
                cols = st.columns(2)
                cols[0].markdown(f"**Status:** {row['status']}")
                if row['status'] == 'Paga':
                    cols[0].markdown(f"**Data Pagamento:** {pd.to_datetime(row['data_pagamento']).strftime('%d/%m/%Y')}")
                    
                    with cols[1]:
                        pdf_recibo = gerar_recibo_comissao_pdf(row, row['nome_corretor'])
                        st.download_button(label="Gerar Recibo", data=pdf_recibo, file_name=f"recibo_comissao_{row['id']}.pdf", mime="application/pdf", use_container_width=True, key=f"recibo_{row['id']}")
                        if row.get('comprovante_url'):
                            st.link_button("Ver Comprovante", url=row['comprovante_url'], use_container_width=True)
                
                if row['status'] == 'Pendente':
                    with cols[1].popover("Registrar Pagamento", use_container_width=True):
                        with st.form(f"form_pgto_comissao_{row['id']}", clear_on_submit=True):
                            data_pgto = st.date_input("Data do Pagamento", value=date.today(), key=f"data_pgto_{row['id']}")
                            comprovante = st.file_uploader("Anexar Comprovante", type=['pdf', 'jpg', 'png', 'jpeg'], key=f"comp_{row['id']}")
                            if st.form_submit_button("Confirmar Pagamento", type="primary"):
                                update_data = {'status': 'Paga', 'data_pagamento': data_pgto.strftime('%Y-%m-%d')}
                                if comprovante:
                                    nome_sanitizado = sanitizar_nome_arquivo(comprovante.name)
                                    file_path = f"comprovantes_comissao/{row['id']}_{nome_sanitizado}"
                                    supabase.storage.from_("comprovantes").upload(file=comprovante.getvalue(), path=file_path, file_options={"content-type": comprovante.type})
                                    update_data['comprovante_url'] = supabase.storage.from_('comprovantes').get_public_url(file_path)
                                
                                try:
                                    supabase.table('comissoes').update(update_data).eq('id', row['id']).execute()
                                    st.success("Pagamento registrado!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao registrar pagamento: {e}")

with tab_gerenciar_corretores:
    st.info("Funcionalidade de arquivar e reativar corretores será adicionada em uma próxima versão.")
    # A lógica de CRUD de corretores pode ser adicionada aqui, similar à página de Clientes.