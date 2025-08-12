# pages/1_Relatorios_Financeiros.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from utils import check_auth, get_supabase_client, formatar_moeda

# --- Autenticação e Conexão ---
st.set_page_config(page_title="Relatórios Financeiros", layout="wide", page_icon="📈")
check_auth("os Relatórios Financeiros")
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
@st.cache_data(ttl=300)
def carregar_todos_dados_financeiros(_supabase_client: Client):
    """Carrega todas as transações (a pagar e a receber) de uma vez."""
    parcelas_resp = _supabase_client.table('parcelas').select('*, clientes(nome)').execute()
    contas_resp = _supabase_client.table('contas_a_pagar').select('*, fornecedores(nome_razao_social)').execute()
    return pd.DataFrame(parcelas_resp.data), pd.DataFrame(contas_resp.data)

@st.cache_data(ttl=300)
def carregar_clientes_com_debitos(_supabase_client: Client):
    """Carrega apenas clientes que têm débitos associados."""
    response = _supabase_client.table('clientes').select('id, nome').in_('id', [d['cliente_id'] for d in _supabase_client.table('debitos').select('cliente_id').execute().data]).execute()
    return pd.DataFrame(response.data)

def gerar_extrato_cliente_pdf(df_extrato: pd.DataFrame, cliente_nome: str, totais: dict):
    """Gera um PDF com o extrato financeiro de um cliente."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(72, height - 72, f"Extrato Financeiro - {cliente_nome}")
    p.setFont("Helvetica", 10)
    p.drawString(72, height - 90, f"Gerado em: {date.today().strftime('%d/%m/%Y')}")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(72, height - 120, "Resumo:")
    p.setFont("Helvetica", 11)
    p.drawString(72, height - 135, f"Valor Total dos Débitos: {totais['total_debitos']}")
    p.drawString(72, height - 150, f"Total Pago: {totais['total_pago']}")
    p.drawString(72, height - 165, f"Saldo Devedor: {totais['saldo_devedor']}")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(72, height - 200, "Histórico de Parcelas:")
    
    y = height - 220
    p.setFont("Helvetica-Bold", 9)
    p.drawString(75, y, "Vencimento")
    p.drawString(155, y, "Descrição")
    p.drawString(355, y, "Valor")
    p.drawString(425, y, "Status")
    p.drawString(505, y, "Data Pgto.")
    y -= 15
    
    p.setFont("Helvetica", 9)
    for _, row in df_extrato.iterrows():
        if y < 60: # Adiciona nova página se o conteúdo chegar ao fim
            p.showPage()
            y = height - 72
            p.setFont("Helvetica", 9)
            
        p.drawString(75, y, str(row['Vencimento']))
        p.drawString(155, y, str(row['Descrição']))
        p.drawString(355, y, str(row['Valor']))
        p.drawString(425, y, str(row['Status']))
        p.drawString(505, y, str(row['Data Pagamento']))
        y -= 12
        
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- Construção da Página ---
st.title("📈 Relatórios Financeiros")
st.markdown("Analise o passado, presente e futuro financeiro da sua construtora.")

df_receber_raw, df_pagar_raw = carregar_todos_dados_financeiros(supabase)

tab_painel, tab_fluxo, tab_extrato = st.tabs(["Painel de Controle", "📊 Fluxo de Caixa Realizado", "📄 Extrato por Cliente"])

with tab_painel:
    st.subheader("Resumo Financeiro Instantâneo")
    col1, col2, col3, col4 = st.columns(4)

    total_a_receber = pd.to_numeric(df_receber_raw[df_receber_raw['status'].isin(['Pendente', 'Atrasado'])]['valor_parcela'], errors='coerce').sum()
    col1.metric("💰 Total a Receber", formatar_moeda(total_a_receber))

    recebido_mes_atual = 0
    if not df_receber_raw.empty and 'data_pagamento' in df_receber_raw.columns:
        df_receber_pagas = df_receber_raw.dropna(subset=['data_pagamento'])
        df_receber_pagas['data_pagamento'] = pd.to_datetime(df_receber_pagas['data_pagamento'])
        recebido_mes_atual = pd.to_numeric(df_receber_pagas[(df_receber_pagas['status'] == 'Pago') & (df_receber_pagas['data_pagamento'].dt.month == pd.Timestamp.now().month) & (df_receber_pagas['data_pagamento'].dt.year == pd.Timestamp.now().year)]['valor_parcela']).sum()
    col2.metric("✅ Recebido este Mês", formatar_moeda(recebido_mes_atual))

    total_a_pagar = pd.to_numeric(df_pagar_raw[df_pagar_raw['status'].isin(['Pendente', 'Atrasado'])]['valor'], errors='coerce').sum()
    col3.metric("💸 Total a Pagar", formatar_moeda(total_a_pagar))

    total_atrasado = pd.to_numeric(df_receber_raw[df_receber_raw['status'] == 'Atrasado']['valor_parcela'], errors='coerce').sum()
    col4.metric("⚠️ Recebimentos em Atraso", formatar_moeda(total_atrasado), delta_color="inverse")
    
    # Lógica de vencimentos da semana continua a mesma...

with tab_fluxo:
    st.subheader("Análise de Fluxo de Caixa por Período")
    
    hoje = date.today()
    col_data1, col_data2 = st.columns(2)
    data_inicio = col_data1.date_input("Data de Início", value=hoje.replace(day=1))
    data_fim = col_data2.date_input("Data de Fim", value=hoje)

    if data_inicio > data_fim:
        st.error("A data de início não pode ser posterior à data de fim.")
    else:
        # Filtra os DataFrames pelo período selecionado
        df_receber_periodo = df_receber_raw[pd.to_datetime(df_receber_raw['data_pagamento']).dt.date.between(data_inicio, data_fim)]
        df_pagar_periodo = df_pagar_raw[pd.to_datetime(df_pagar_raw['data_pagamento']).dt.date.between(data_inicio, data_fim)]

        total_recebido_periodo = pd.to_numeric(df_receber_periodo['valor_parcela']).sum()
        total_pago_periodo = pd.to_numeric(df_pagar_periodo['valor']).sum()
        saldo_periodo = total_recebido_periodo - total_pago_periodo

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Recebido no Período", formatar_moeda(total_recebido_periodo))
        c2.metric("Total Pago no Período", formatar_moeda(total_pago_periodo))
        c3.metric("Saldo do Período", formatar_moeda(saldo_periodo))

        # Prepara dados para o gráfico
        df_receber_periodo['data'] = pd.to_datetime(df_receber_periodo['data_pagamento'])
        df_pagar_periodo['data'] = pd.to_datetime(df_pagar_periodo['data_pagamento'])
        
        receitas_mensais = df_receber_periodo.set_index('data').resample('M')['valor_parcela'].sum()
        despesas_mensais = df_pagar_periodo.set_index('data').resample('M')['valor'].sum()
        
        df_fluxo_caixa = pd.DataFrame({'Receitas': receitas_mensais, 'Despesas': despesas_mensais}).fillna(0)
        
        st.markdown("### Evolução Mensal (Receitas vs. Despesas)")
        st.bar_chart(df_fluxo_caixa)


with tab_extrato:
    st.subheader("Extrato Financeiro por Cliente")
    df_clientes_com_debitos = carregar_clientes_com_debitos(supabase)

    if df_clientes_com_debitos.empty:
        st.info("Nenhum cliente com débitos lançados foi encontrado.")
    else:
        clientes_dict = pd.Series(df_clientes_com_debitos.id.values, index=df_clientes_com_debitos.nome).to_dict()
        cliente_selecionado_nome = st.selectbox("Selecione um cliente para gerar o extrato", options=clientes_dict.keys())

        if cliente_selecionado_nome:
            cliente_id = clientes_dict[cliente_selecionado_nome]
            
            # Filtra todas as parcelas daquele cliente
            extrato_df = df_receber_raw[df_receber_raw['clientes'].apply(lambda x: x['id'] if isinstance(x, dict) else -1) == cliente_id]
            extrato_df = extrato_df.sort_values('data_vencimento')

            if extrato_df.empty:
                st.warning("Este cliente não possui parcelas.")
            else:
                # Calcula os totais
                total_debitos = pd.to_numeric(extrato_df['valor_parcela']).sum()
                total_pago = pd.to_numeric(extrato_df[extrato_df['status'] == 'Pago']['valor_parcela']).sum()
                saldo_devedor = total_debitos - total_pago

                st.markdown("---")
                c1, c2, c3 = st.columns(3)
                c1.metric("Valor Total em Débitos", formatar_moeda(total_debitos))
                c2.metric("Total Pago", formatar_moeda(total_pago))
                c3.metric("Saldo Devedor", formatar_moeda(saldo_devedor))

                # Prepara DataFrame para exibição
                df_display = extrato_df.copy()
                df_display['Vencimento'] = pd.to_datetime(df_display['data_vencimento']).dt.strftime('%d/%m/%Y')
                df_display['Valor'] = df_display['valor_parcela'].apply(formatar_moeda)
                df_display['Status'] = df_display['status']
                df_display['Data Pagamento'] = pd.to_datetime(df_display['data_pagamento']).dt.strftime('%d/%m/%Y').fillna('---')
                
                # Busca a descrição do débito
                debitos_cliente_resp = supabase.table('debitos').select('descricao').eq('cliente_id', cliente_id).execute()
                descricoes = [d['descricao'] for d in debitos_cliente_resp.data]
                df_display['Descrição'] = ", ".join(descricoes) if descricoes else "Débito Geral"
                
                st.dataframe(df_display[['Vencimento', 'Descrição', 'Valor', 'Status', 'Data Pagamento']], use_container_width=True, hide_index=True)

                # Botão de Download do PDF
                totais = {
                    "total_debitos": formatar_moeda(total_debitos),
                    "total_pago": formatar_moeda(total_pago),
                    "saldo_devedor": formatar_moeda(saldo_devedor)
                }
                pdf_bytes = gerar_extrato_cliente_pdf(df_display, cliente_selecionado_nome, totais)
                st.download_button(
                    label="📄 Gerar Extrato em PDF",
                    data=pdf_bytes,
                    file_name=f"extrato_{cliente_selecionado_nome.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )