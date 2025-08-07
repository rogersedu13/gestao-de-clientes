# pages/3_Contas_a_Receber.py
import streamlit as st
import pandas as pd
from datetime import date
from utils import check_auth, conectar_supabase, formatar_moeda
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# --- Autenticação e Conexão ---
check_auth("a área de Contas a Receber")
supabase = conectar_supabase()

# --- Funções de Cache ---
@st.cache_data(ttl=60)
def carregar_clientes():
    response = supabase.table('clientes').select('id, nome').order('nome').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def carregar_debitos():
    response = supabase.table('debitos').select('*, clientes(nome)').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=10)
def carregar_parcelas(debito_id):
    if not debito_id: return pd.DataFrame()
    response = supabase.table('parcelas').select('*').eq('debito_id', debito_id).order('numero_parcela').execute()
    return pd.DataFrame(response.data)

# --- Funções de Lógica ---
def cadastrar_debito(cliente_id, descricao, valor_total, n_parcelas, data_inicio, frequencia, forma_pagamento, obs):
    try:
        debito_data = {
            'cliente_id': cliente_id,
            'descricao': descricao,
            'valor_total': valor_total,
            'n_parcelas': n_parcelas,
            'data_inicio': data_inicio.strftime('%Y-%m-%d'),
            'frequencia': frequencia,
            'forma_pagamento': forma_pagamento,
            'observacoes': obs
        }
        response = supabase.table('debitos').insert(debito_data).execute()
        novo_debito_id = response.data[0]['id']
        
        # Chama a função SQL para gerar as parcelas
        supabase.rpc('gerar_parcelas', {'debito_id_param': novo_debito_id}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar débito: {e}")
        return False

def registrar_pagamento(parcela_id, data_pagamento, comprovante_file):
    try:
        url_comprovante = None
        if comprovante_file:
            # Lógica de Upload para o Supabase Storage
            file_path = f"comprovantes/{parcela_id}_{comprovante_file.name}"
            supabase.storage.from_("comprovantes").upload(file=comprovante_file.getvalue(), path=file_path, file_options={"content-type": comprovante_file.type})
            # Pega a URL pública do arquivo
            response_url = supabase.storage.from_('comprovantes').get_public_url(file_path)
            url_comprovante = response_url
            
        update_data = {
            'status': 'Pago',
            'data_pagamento': data_pagamento.strftime('%Y-%m-%d'),
            'comprovante_url': url_comprovante
        }
        supabase.table('parcelas').update(update_data).eq('id', parcela_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar pagamento: {e}")
        return False
        
def gerar_recibo_pdf(parcela, cliente_nome, debito_desc):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.drawString(100, height - 100, f"RECIBO DE PAGAMENTO")
    p.drawString(100, height - 120, f"--------------------------------------------------")
    p.drawString(100, height - 140, f"Recebemos de: {cliente_nome}")
    p.drawString(100, height - 160, f"O valor de: {formatar_moeda(parcela['valor_parcela'])}")
    p.drawString(100, height - 180, f"Referente a: Parcela {parcela['numero_parcela']} - {debito_desc}")
    p.drawString(100, height - 200, f"Data do Pagamento: {pd.to_datetime(parcela['data_pagamento']).strftime('%d/%m/%Y')}")
    p.drawString(100, height - 240, f"_________________________")
    p.drawString(100, height - 250, f"Assinatura (Construtora)")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- Construção da Página ---
st.set_page_config(page_title="Contas a Receber", layout="wide")
st.image("https://placehold.co/1200x200/529e67/FFFFFF?text=Contas+a+Receber", use_column_width=True)
st.title("💸 Contas a Receber")
st.markdown("Gerencie os débitos de clientes e controle o recebimento das parcelas.")

df_clientes = carregar_clientes()
if df_clientes.empty:
    st.warning("Nenhum cliente cadastrado. Por favor, cadastre um cliente primeiro na aba 'Clientes'.")
    st.stop()

clientes_dict = pd.Series(df_clientes.id.values, index=df_clientes.nome).to_dict()

tab1, tab2 = st.tabs(["🗂️ Visualizar Débitos e Parcelas", "➕ Lançar Novo Débito"])

with tab1:
    st.subheader("Débitos Ativos")
    df_debitos = carregar_debitos()
    
    if df_debitos.empty:
        st.info("Nenhum débito lançado. Adicione um na aba ao lado.")
    else:
        # Extrai o nome do cliente do dicionário aninhado
        df_debitos['nome_cliente'] = df_debitos['clientes'].apply(lambda x: x['nome'] if isinstance(x, dict) else 'N/A')
        
        # Filtro por cliente
        nomes_clientes_debito = ["Todos"] + df_debitos['nome_cliente'].unique().tolist()
        cliente_filtro = st.selectbox("Filtrar por Cliente:", options=nomes_clientes_debito)
        
        df_filtrado = df_debitos if cliente_filtro == "Todos" else df_debitos[df_debitos['nome_cliente'] == cliente_filtro]
        
        for _, debito in df_filtrado.iterrows():
            with st.expander(f"**{debito['nome_cliente']}** - {debito['descricao']} ({formatar_moeda(debito['valor_total'])})"):
                df_parcelas = carregar_parcelas(debito['id'])
                if df_parcelas.empty:
                    st.write("Nenhuma parcela encontrada para este débito.")
                    continue
                
                df_parcelas['data_vencimento'] = pd.to_datetime(df_parcelas['data_vencimento'])
                
                for _, parcela in df_parcelas.iterrows():
                    st.markdown("---")
                    cols = st.columns([1, 1, 1, 2, 2])
                    cols[0].markdown(f"**Parcela {parcela['numero_parcela']}**")
                    cols[1].markdown(f"{formatar_moeda(parcela['valor_parcela'])}")
                    cols[2].markdown(f"Vence: {parcela['data_vencimento'].strftime('%d/%m/%Y')}")
                    
                    if parcela['status'] == 'Pago':
                        cols[3].success(f"✅ Pago em {pd.to_datetime(parcela['data_pagamento']).strftime('%d/%m/%Y')}")
                        if parcela.get('comprovante_url'):
                            cols[4].link_button("Ver Comprovante", url=parcela['comprovante_url'])
                        
                        # Botão para gerar recibo
                        pdf_recibo = gerar_recibo_pdf(parcela, debito['nome_cliente'], debito['descricao'])
                        cols[4].download_button(
                            label="Gerar Recibo",
                            data=pdf_recibo,
                            file_name=f"recibo_parcela_{parcela['numero_parcela']}_{debito['nome_cliente']}.pdf",
                            mime="application/pdf"
                        )
                            
                    elif parcela['status'] == 'Atrasado':
                        cols[3].error("🔴 Atrasado")
                    else: # Pendente
                        cols[3].warning("🟡 Pendente")

                    if parcela['status'] != 'Pago':
                        with cols[4].popover("Registrar Recebimento", use_container_width=True):
                            with st.form(f"form_pagamento_{parcela['id']}", clear_on_submit=True):
                                data_pgto = st.date_input("Data do Recebimento", value=date.today(), key=f"data_{parcela['id']}")
                                comprovante = st.file_uploader("Anexar Comprovante", type=['pdf', 'jpg', 'png', 'jpeg'], key=f"comp_{parcela['id']}")
                                if st.form_submit_button("Confirmar", type="primary"):
                                    if registrar_pagamento(parcela['id'], data_pgto, comprovante):
                                        st.success("Recebimento registrado!")
                                        st.cache_data.clear()
                                        st.rerun()

with tab2:
    st.subheader("Lançar Novo Débito para um Cliente")
    with st.form("novo_debito_form", clear_on_submit=True):
        cliente_selecionado = st.selectbox("Selecione o Cliente*", options=clientes_dict.keys())
        descricao = st.text_input("Descrição do Débito*", help="Ex: Venda Apto 101, Bloco A")
        valor_total = st.number_input("Valor Total (R$)*", min_value=0.01, format="%.2f")
        n_parcelas = st.number_input("Número de Parcelas*", min_value=1, step=1)
        data_inicio = st.date_input("Data de Início (1º Vencimento)*", value=date.today())
        frequencia = st.selectbox("Frequência*", ["Mensal", "Quinzenal", "Semanal"])
        forma_pagamento = st.text_input("Forma de Pagamento", help="Ex: Boleto, Transferência")
        obs_debito = st.text_area("Observações")
        
        submitted_debito = st.form_submit_button("Lançar Débito e Gerar Parcelas", type="primary")
        
        if submitted_debito:
            if not all([cliente_selecionado, descricao, valor_total, n_parcelas, data_inicio, frequencia]):
                st.error("Por favor, preencha todos os campos obrigatórios (*).")
            else:
                cliente_id = clientes_dict[cliente_selecionado]
                if cadastrar_debito(cliente_id, descricao, valor_total, n_parcelas, data_inicio, frequencia, forma_pagamento, obs_debito):
                    st.success(f"Débito para '{cliente_selecionado}' lançado com sucesso e parcelas geradas!")
                    st.cache_data.clear()
                # O formulário é limpo automaticamente