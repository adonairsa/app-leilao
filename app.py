import streamlit as st
import pdfplumber

# Configuração da página para ocupar a tela inteira
st.set_page_config(page_title="PAINEL DO LEILOEIRO", layout="wide")

# Estilo CSS para deixar as fontes e cartões gigantes para leitura rápida
st.markdown("""
    <style>
    .big-font { font-size: 32px !important; font-weight: bold; color: #1E3A8A; }
    .card-lote { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 8px solid #1E3A8A; }
    .card-jargao { background-color: #ECFDF5; padding: 15px; border-radius: 8px; border-left: 6px solid #10B981; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎙️ PAINEL DE PISTA — LEILÃO")

# 1. MENU LATERAL (CONFIGURAÇÕES E ARQUIVOS)
st.sidebar.header("📂 Arquivo do Leilão")
uploaded_file = st.sidebar.file_uploader("Suba o PDF do Catálogo", type="pdf")

if uploaded_file is not None:
    # Extrair texto do PDF
    text_content = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text_content += (page.extract_text() or "") + "\n"

    st.sidebar.success("Catálogo Carregado!")
    
    st.sidebar.markdown("---")
    st.sidebar.header("🧮 Calculadora Rápida")
    qtd_parcelas = st.sidebar.number_input("Número de Parcelas", value=30, step=1)
    valor_parcela = st.sidebar.number_input("Valor da Parcela (R$)", value=500.0, step=50.0)
    valor_total = qtd_parcelas * valor_parcela

    # 2. PAINEL PRINCIPAL (INTERFACE DE PISTA)
    col_lote, col_info = st.columns([1, 2])

    with col_lote:
        st.markdown("<p class='big-font'>NÚMERO DO LOTE</p>", unsafe_allow_html=True)
        num_lote = st.text_input("", value="12", help="Digite o lote e aperte ENTER")
        
        # Placa gigante com os valores calculados
        st.markdown("---")
        st.metric(label="PARCELA ATUAL", value=f"R$ {valor_parcela:,.2f}")
        st.metric(label="VALOR TOTAL DO LOTE", value=f"R$ {valor_total:,.2f}")

    with col_info:
        st.markdown(f"<div class='card-lote'><span class='big-font'>📌 LOTE {num_lote}</span></div>", unsafe_allow_html=True)
        st.write("")
        
        # Leitura e busca de dados no PDF
        linhas_lote = [linha for linha in text_content.split('\n') if f"lote {num_lote}" in linha.lower() or f"{num_lote}" in linha.split()]
        
        if linhas_lote:
            st.markdown("### 📋 Dados do Catálogo")
            for linha in linhas_lote[:4]:
                st.write(f"• **{linha.strip()}**")
        else:
            st.warning("Lote não encontrado no catálogo. Digite outro número.")

        st.markdown("---")
        st.markdown("### 🎙️ Gatilhos de Canta para o Microfone")
        
        st.markdown("<div class='card-jargao'><b>Morfologia:</b> Garupa larga, carcaça coberta e padrão de cabeceira!</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-jargao'><b>Impacto:</b> Matriz pra chancelar a bezerrada e agregar valor no rebanho!</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-jargao'><b>Fechamento:</b> Lote com essa avaliação genética não sobra na pista!</div>", unsafe_allow_html=True)

else:
    st.info("👈 Para abrir a interface gráfica, suba o PDF do leilão no menu da esquerda.")