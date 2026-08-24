import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="PAINEL DO LEILOEIRO", layout="wide")

st.markdown("""
    <style>
    .big-font { font-size: 28px !important; font-weight: bold; color: #1E3A8A; }
    .card-lote { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 8px solid #1E3A8A; color: #000000 !important; }
    .card-pai { background-color: #E0F2FE; padding: 10px; border-radius: 6px; border-left: 5px solid #0284C7; color: #000 !important; margin-bottom: 5px; font-weight: bold; }
    .card-mae { background-color: #FCE7F3; padding: 10px; border-radius: 6px; border-left: 5px solid #DB2777; color: #000 !important; margin-bottom: 5px; font-weight: bold; }
    .card-avo { background-color: #FEF3C7; padding: 10px; border-radius: 6px; border-left: 5px solid #D97706; color: #000 !important; margin-bottom: 5px; font-weight: bold; }
    .card-jargao { background-color: #ECFDF5; padding: 12px; border-radius: 8px; border-left: 6px solid #10B981; margin-bottom: 8px; color: #000000 !important; font-size: 16px; font-weight: bold; }
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
    st.markdown(f"<div class='card-lote'><span class='big-font'>📌 ARVORE GENEALÓGICA — LOTE {num_lote}</span></div>", unsafe_allow_html=True)
    st.write("")
    
    bloco_lote = []
    if text_content:
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
        texto_bloco = "\n".join(bloco_lote)

        # Variáveis de Linhagem
        pai = "Não identificado"
        mae = "Não identificada"
        avo_pat = "Não identificado"
        avo_mat = "Não identificado"

        # Extração por Padrões Comuns em Catálogos
        for l in bloco_lote:
            l_lower = l.lower()
            if "pai:" in l_lower or "sire:" in l_lower:
                pai = l
            elif "mãe:" in l_lower or "mae:" in l_lower or "dam:" in l_lower:
                mae = l
            elif "avô mat" in l_lower or "a.m." in l_lower or "m3:" in l_lower:
                avo_mat = l
            elif "avô pat" in l_lower or "a.p." in l_lower or "p2:" in l_lower:
                avo_pat = l

        # Exibição Visual Organizada na Tela
        st.markdown(f"<div class='card-pai'>🟦 <b>PAI:</b> {pai}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card-mae'>🟥 <b>MÃE:</b> {mae}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card-avo'>🟨 <b>AVÔ PATERNO:</b> {avo_pat}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card-avo'>🟨 <b>AVÔ MATERNO:</b> {avo_mat}</div>", unsafe_allow_html=True)
        
        with st.expander("📄 Ver bloco completo do texto do PDF"):
            for l in bloco_lote:
                st.write(f"• {l}")
    else:
        st.info("👈 Suba o catálogo no menu da esquerda para visualizar a genealogia.")

    st.markdown("---")
    st.markdown("### 🎙️ Gatilhos para o Microfone")
    st.markdown("<div class='card-jargao'><b>Genética:</b> Sangue aberto, pedigree fechado na cabeceira da raça!</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-jargao'><b>Linhagem Materna:</b> Família consagrada em pista com barriga de ouro!</div>", unsafe_allow_html=True)
