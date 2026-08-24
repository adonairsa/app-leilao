import streamlit as st
import pdfplumber
import re

# Configuração da página
st.set_page_config(page_title="PAINEL DO LEILOEIRO PRO", layout="wide")

# Estilos CSS de Alta Visibilidade (Letras Pretas)
st.markdown("""
    <style>
    .big-font { font-size: 28px !important; font-weight: bold; color: #1E3A8A; }
    .card-lote { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 8px solid #1E3A8A; color: #000 !important; }
    .card-pai { background-color: #E0F2FE; padding: 10px; border-radius: 6px; border-left: 5px solid #0284C7; color: #000 !important; margin-bottom: 5px; font-weight: bold; }
    .card-mae { background-color: #FCE7F3; padding: 10px; border-radius: 6px; border-left: 5px solid #DB2777; color: #000 !important; margin-bottom: 5px; font-weight: bold; }
    .card-jargao { background-color: #ECFDF5; padding: 12px; border-radius: 8px; border-left: 6px solid #10B981; margin-bottom: 8px; color: #000 !important; font-size: 16px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# FUNÇÃO DE MEMORIZAÇÃO (CACHE) - Isso elimina a lentidão!
@st.cache_data
def processar_pdf(file):
    paginas_texto = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                paginas_texto.append(texto)
    return paginas_texto

st.title("🎙️ PAINEL DE PISTA — LEILÃO DE ELITE")

# 1. MENU LATERAL
st.sidebar.header("📂 Arquivo do Leilão")
uploaded_file = st.sidebar.file_uploader("Suba o PDF do Catálogo", type="pdf")

text_content = []

if uploaded_file is not None:
    # Chama a função otimizada com cache
    text_content = processar_pdf(uploaded_file)
    st.sidebar.success("⚡ Catálogo Memorizado e Pronto!")

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
    st.markdown(f"<div class='card-lote'><span class='big-font'>📌 LINHAGEM GENÉTICA — LOTE {num_lote}</span></div>", unsafe_allow_html=True)
    st.write("")
    
    bloco_lote = []
    if text_content:
        # Busca instantânea nos dados em memória
        for pagina in text_content:
            linhas = pagina.split('\n')
            for i, linha in enumerate(linhas):
                if re.search(rf"\b(lote\s*)?{num_lote}\b", linha, re.IGNORECASE):
                    inicio = max(0, i - 1)
                    fim = min(len(linhas), i + 10)
                    bloco_lote = linhas[inicio:fim]
                    break
            if bloco_lote:
                break

    if bloco_lote:
        # Lógica de extração rápida
        pai = next((l for l in bloco_lote if any(p in l.lower() for p in ["pai:", "sire:"])), "Ver bloco abaixo")
        mae = next((l for l in bloco_lote if any(m in l.lower() for m in ["mãe:", "mae:", "dam:"])), "Ver bloco abaixo")

        st.markdown(f"<div class='card-pai'>🟦 <b>LINHA PATERNA (ESQUERDA):</b> {pai}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card-mae'>🟥 <b>LINHA MATERNA (DIREITA):</b> {mae}</div>", unsafe_allow_html=True)
        
        with st.expander("📄 Ver todas as linhas do Lote no PDF", expanded=True):
            for l in bloco_lote:
                st.write(f"• **{l.strip()}**")
    else:
        st.info("👈 Suba o catálogo no menu da esquerda para carregar as informações.")

    st.markdown("---")
    st.markdown("### 🎙️ Gatilhos Rápidos para o Microfone")
    st.markdown("<div class='card-jargao'><b>Morfologia:</b> Garupa larga, carcaça coberta e padrão de cabeceira!</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-jargao'><b>Pedigree:</b> União de raçadores consagrados na raça Nelore!</div>", unsafe_allow_html=True)
