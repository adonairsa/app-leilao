import streamlit as st
import pdfplumber
import re

# Configuração da página
st.set_page_config(page_title="PAINEL DO LEILOEIRO", layout="wide")

# Estilos CSS com contraste corrigido (Letras PRETAS para leitura fácil)
st.markdown("""
    <style>
    .big-font { font-size: 28px !important; font-weight: bold; color: #1E3A8A; }
    .card-lote { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 8px solid #1E3A8A; color: #000000 !important; }
    .card-genetica { background-color: #FEF3C7; padding: 15px; border-radius: 8px; border-left: 6px solid #F59E0B; margin-bottom: 15px; color: #000000 !important; }
    .card-jargao { 
        background-color: #ECFDF5; 
        padding: 14px; 
        border-radius: 8px; 
        border-left: 6px solid #10B981; 
        margin-bottom: 10px; 
        color: #000000 !important; 
        font-size: 18px;
        font-weight: 500;
    }
    .card-jargao b { color: #000000 !important; font-weight: bold; }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎙️ PAINEL DE PISTA — LEILÃO DE ELITE")

# 1. MENU LATERAL
st.sidebar.header("📂 Arquivo do Leilão")
uploaded_file = st.sidebar.file_uploader("Suba o PDF do Catálogo", type="pdf")

text_content = []

if uploaded_file is not None:
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        st.sidebar.success("Catálogo Carregado!")
    except Exception as e:
        st.sidebar.error("Erro ao ler o arquivo PDF.")

st.sidebar.markdown("---")
st.sidebar.header("🧮 Calculadora Rápida")
qtd_parcelas = st.sidebar.number_input("Número de Parcelas", value=30, step=1)
valor_parcela = st.sidebar.number_input("Valor da Parcela (R$)", value=500.0, step=50.0)
valor_total = qtd_parcelas * valor_parcela

# 2. PAINEL PRINCIPAL
col_lote, col_info = st.columns([1, 2])

with col_lote:
    st.markdown("<p class='big-font'>NÚMERO DO LOTE</p>", unsafe_allow_html=True)
    num_lote = st.text_input("Digite o número do lote:", value="12")
    
    st.markdown("---")
    st.metric(label="PARCELA ATUAL", value=f"R$ {valor_parcela:,.2f}")
    st.metric(label="VALOR TOTAL DO LOTE", value=f"R$ {valor_total:,.2f}")

with col_info:
    st.markdown(f"<div class='card-lote'><span class='big-font'>📌 FICHA TÉCNICA — LOTE {num_lote}</span></div>", unsafe_allow_html=True)
    st.write("")
    
    # BUSCA AVANÇADA POR BLOCO DE LOTE
    bloco_encontrado = []
    
    if text_content:
        # Percorre todas as páginas do catálogo
        for pagina in text_content:
            linhas = pagina.split('\n')
            for i, linha in enumerate(linhas):
                # Procura termos como "LOTE 12", "LOTE: 12" ou "12" no início da linha
                if re.search(rf"\b(lote\s*)?{num_lote}\b", linha, re.IGNORECASE):
                    # Pega a linha do lote e até 8 linhas abaixo (onde fica a linhagem/família)
                    inicio = max(0, i - 1)
                    fim = min(len(linhas), i + 9)
                    bloco_encontrado = linhas[inicio:fim]
                    break
            if bloco_encontrado:
                break
        
        if bloco_encontrado:
            st.markdown("### 🧬 Dados Genéticos & Ficha do Animal")
            conteudo_bloco = "<br>".join([f"• <b>{l.strip()}</b>" for l in bloco_encontrado if l.strip()])
            st.markdown(f"<div class='card-genetica'><div class='texto-preto'>{conteudo_bloco}</div></div>", unsafe_allow_html=True)
        else:
            st.warning(f"Lote {num_lote} não localizado no texto do PDF.")
    else:
        st.info("👈 Suba o PDF do catálogo no menu lateral para extrair a genealogia dos animais.")

    st.markdown("---")
    st.markdown("### 🎙️ Gatilhos de Canta para o Microfone")
    
    st.markdown("<div class='card-jargao'><b>Morfologia:</b> Garupa larga, carcaça coberta e padrão de cabeceira!</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-jargao'><b>Genética:</b> Linhagem consagrada, raça pura PO e avaliação de ponta!</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-jargao'><b>Fechamento:</b> Lote com essa avaliação genética não sobra na pista!</div>", unsafe_allow_html=True)
