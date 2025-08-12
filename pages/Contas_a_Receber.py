# pages/3_Contas_a_Receber.py
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
from utils import check_auth, get_supabase_client, formatar_moeda

# --- Funções de Utilidade ---
def sanitizar_nome_arquivo(nome_arquivo: str) -> str:
    nome_limpo = re.sub(r'[^\w\.\-]', '_', nome_arquivo)
    return nome_limpo

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Contas a Receber", layout="wide", page_icon="💸")
check_auth("a área de Contas a Receber")
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

# --- Funções de Cache ---
@st.cache_data(ttl=60)
def carregar_clientes():
    response = supabase.table('clientes').select('id, nome').eq('ativo', True).order('nome').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_obras_ativas():
    response = supabase.table('obras').select('id, nome_obra').eq('ativo', True).order('nome_obra').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_debitos():
    response = supabase.table('debitos').select('*, clientes(nome), obras(nome_obra)').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=10)
def carregar_parcelas(debito_id):
    if not debito_id: return pd.DataFrame()
    response = supabase.table('parcelas').select('*').eq('debito_id', debito_id).order('numero_parcela').execute()
    return pd.DataFrame(response.data)

# --- Funções de Lógica ---
def cadastrar_debito(cliente_id, obra_id, descricao, valor_total, n_parcelas, data_inicio, frequencia, forma_pagamento, obs):
    try:
        debito_data = {
            'cliente_id': cliente_id, 'obra_id': obra_id, 'descricao': descricao, 'valor_total': valor_total,
            'n_parcelas': n_parcelas, 'data_inicio': data_inicio.strftime('%Y-%m-%d'),
            'frequencia': frequencia, 'forma_pagamento': forma_pagamento, 'observacoes': obs
        }
        response = supabase.table('debitos').insert(debito_data, count='exact').execute()
        novo_debito_id = response.data[0]['id']
        supabase.rpc('gerar_parcelas', {'debito_id_param': novo_debito_id}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar débito: {e}"); return False

def registrar_pagamento(parcela_id, data_pagamento, comprovante_file):
    try:
        url_comprovante = None
        if comprovante_file:
            nome_sanitizado = sanitizar_nome_arquivo(comprovante_file.name)
            file_path = f"comprovantes/{parcela_id}_{nome_sanitizado}"
            try:
                lista_arquivos = supabase.storage.from_("comprovantes").list(path="comprovantes", options={"search": f"{parcela_id}_"})
                if lista_arquivos:
                    arquivos_para_remover = [f"comprovantes/{arquivo['name']}" for arquivo in lista_arquivos]
                    supabase.storage.from_("comprovantes").remove(arquivos_para_remover)
            except Exception: pass
            supabase.storage.from_("comprovantes").upload(file=comprovante_file.getvalue(), path=file_path, file_options={"content-type": comprovante_file.type})
            url_comprovante = supabase.storage.from_('comprovantes').get_public_url(file_path)
        
        update_data = {'status': 'Pago', 'data_pagamento': data_pagamento.strftime('%Y-%m-%d'),'comprovante_url': url_comprovante}
        supabase.table('parcelas').update(update_data).eq('id', parcela_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar pagamento: {e}"); return False
        
def gerar_recibo_pdf(parcela, cliente_nome, debito_desc):
    # (Esta função permanece a mesma)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "RECIBO DE PAGAMENTO")
    p.drawString(100, 730, "--------------------------------------------------")
    p.drawString(100, 710, f"Recebemos de: {cliente_nome}")
    p.drawString(100, 690, f"O valor de: {formatar_moeda(parcela['valor_parcela'])}")
    p.drawString(100, 670, f"Referente a: Parcela {parcela['numero_parcela']} - {debito_desc}")
    p.drawString(100, 650, f"Data do Pagamento: {pd.to_datetime(parcela['data_pagamento']).strftime('%d/%m/%Y')}")
    p.drawString(100, 610, "_________________________")
    p.drawString(100, 600, "Assinatura (Construtora)")
    p.showPage(); p.save(); buffer.seek(0)
    return buffer

# --- Construção da Página ---
st.image("https://placehold.co/1200x200/529e67/FFFFFF?text=Contas+a+Receber", use_container_width=True)
st.title("💸 Contas a Receber")
st.markdown("Gerencie os débitos de clientes e controle o recebimento das parcelas.")

df_clientes = carregar_clientes()
if df_clientes.empty:
    st.warning("Nenhum cliente ativo cadastrado. Verifique a aba 'Clientes'."); st.stop()
clientes_dict = pd.Series(df_clientes.id.values, index=df_clientes.nome).to_dict()

tab1, tab2 = st.tabs(["🗂️ Visualizar Débitos e Parcelas", "➕ Lançar Novo Débito"])
with tab1:
    st.subheader("Débitos Registrados")
    df_debitos = carregar_debitos()
    if df_debitos.empty:
        st.info("Nenhum débito lançado. Adicione um na aba ao lado.")
    else:
        df_debitos['nome_cliente'] = df_debitos['clientes'].apply(lambda x: x['nome'] if isinstance(x, dict) else 'N/A')
        
        # Adiciona o nome da obra, tratando casos onde não há obra vinculada
        df_debitos['nome_obra'] = df_debitos['obras'].apply(lambda x: x['nome_obra'] if isinstance(x, dict) else None)

        nomes_clientes_debito = ["Todos"] + sorted(df_debitos['nome_cliente'].unique().tolist())
        cliente_filtro = st.selectbox("Filtrar por Cliente:", options=nomes_clientes_debito)
        df_filtrado = df_debitos if cliente_filtro == "Todos" else df_debitos[df_debitos['nome_cliente'] == cliente_filtro]
        
        for _, debito in df_filtrado.iterrows():
            titulo_expander = f"**{debito['nome_cliente']}** - {debito['descricao']} ({formatar_moeda(debito['valor_total'])})"
            if debito['nome_obra']:
                titulo_expander += f" | **Obra:** {debito['nome_obra']}"

            with st.expander(titulo_expander):
                df_parcelas = carregar_parcelas(debito['id'])
                # ... resto da lógica de visualização das parcelas ...
                # (O código interno do expander permanece o mesmo)
                if df_parcelas.empty:
                    st.write("Nenhuma parcela encontrada."); continue
                
                df_parcelas['data_vencimento'] = pd.to_datetime(df_parcelas['data_vencimento'])
                
                for _, parcela in df_parcelas.iterrows():
                    st.markdown("---")
                    cols = st.columns([1, 1, 1, 2, 2])
                    cols[0].markdown(f"**Parcela {parcela['numero_parcela']}**")
                    cols[1].markdown(f"{formatar_moeda(parcela['valor_parcela'])}")
                    cols[2].markdown(f"Vence: {parcela['data_vencimento'].strftime('%d/%m/%Y')}")
                    
                    status = parcela['status']
                    if status == 'Pago':
                        cols[3].success(f"✅ Pago em {pd.to_datetime(parcela['data_pagamento']).strftime('%d/%m/%Y')}")
                        with cols[4]:
                            pdf_recibo = gerar_recibo_pdf(parcela, debito['nome_cliente'], debito['descricao'])
                            st.download_button(label="Gerar Recibo", data=pdf_recibo, file_name=f"recibo_p{parcela['numero_parcela']}_{debito['nome_cliente']}.pdf", mime="application/pdf", use_container_width=True, key=f"recibo_{parcela['id']}")
                            if parcela.get('comprovante_url'):
                                st.link_button("Ver Comprovante", url=parcela['comprovante_url'], use_container_width=True)
                    elif status == 'Atrasado':
                        cols[3].error("🔴 Atrasado")
                    else:
                        cols[3].warning("🟡 Pendente")

                    if status != 'Pago':
                        with cols[4].popover("Registrar Recebimento", use_container_width=True):
                            with st.form(f"form_pagamento_{parcela['id']}", clear_on_submit=True):
                                data_pgto = st.date_input("Data do Recebimento", value=date.today(), key=f"data_{parcela['id']}")
                                comprovante = st.file_uploader("Anexar Comprovante", type=['pdf', 'jpg', 'png', 'jpeg'], key=f"comp_{parcela['id']}")
                                if st.form_submit_button("Confirmar", type="primary"):
                                    if registrar_pagamento(parcela['id'], data_pgto, comprovante):
                                        st.success("Recebimento registrado!"); st.cache_data.clear(); st.rerun()

with tab2:
    st.subheader("Lançar Novo Débito para um Cliente")
    
    df_obras = carregar_obras_ativas()
    obras_dict = pd.Series(df_obras.id.values, index=df_obras.nome_obra).to_dict()

    with st.form("novo_debito_form", clear_on_submit=True):
        cliente_selecionado = st.selectbox("Selecione o Cliente*", options=clientes_dict.keys())
        
        # <<<<===== AQUI ESTÁ A MUDANÇA =====>>>>
        obra_selecionada = st.selectbox("Vincular a obra", options=["Nenhuma"] + list(obras_dict.keys()))

        descricao = st.text_input("Descrição do Débito*", help="Ex: Venda Apto 101, Bloco A")
        valor_total = st.number_input("Valor Total (R$)*", min_value=0.01, format="%.2f")
        n_parcelas = st.number_input("Número de Parcelas*", min_value=1, step=1)
        data_inicio = st.date_input("Data de Início (1º Vencimento)*", value=date.today())
        frequencia = st.selectbox("Frequência*", ["Mensal", "Quinzenal", "Semanal"])
        forma_pagamento = st.text_input("Forma de Pagamento", help="Ex: Boleto, Transferência")
        obs_debito = st.text_area("Observações")
        if st.form_submit_button("Lançar Débito e Gerar Parcelas", type="primary", use_container_width=True):
            if not all([cliente_selecionado, descricao, valor_total, n_parcelas, data_inicio, frequencia]):
                st.error("Preencha todos os campos obrigatórios (*).")
            else:
                cliente_id = clientes_dict[cliente_selecionado]
                obra_id = obras_dict.get(obra_selecionada) # Pega o ID da obra, ou None se "Nenhuma"
                
                if cadastrar_debito(cliente_id, obra_id, descricao, valor_total, n_parcelas, data_inicio, frequencia, forma_pagamento, obs_debito):
                    st.success(f"Débito para '{cliente_selecionado}' lançado com sucesso!"); st.cache_data.clear()