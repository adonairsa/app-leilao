import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="PAINEL DO LEILOEIRO PRO", layout="wide")

# Estilos CSS de Alta Visibilidade para Tablet / Celular
st.markdown("""
    <style>
    .big-lote { font-size: 36px !important; font-weight: bold; color: #1E3A8A; text-align: center; }
    .card-oe { background-color: #FEF3C7; padding: 12px; border-radius: 8px; border-left: 6px solid #D97706; color: #000 !important; font-size: 18px; margin-bottom: 15px; }
    .card-lote { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 8px solid #1E3A8A; color: #000 !important; }
    .card-pai { background-color: #E0F2FE; padding: 12px; border-radius: 6px; border-left: 5px solid #0284C7; color: #000 !important; margin-bottom: 8px; }
    .card-mae { background-color: #FCE7F3; padding: 12px; border-radius: 6px; border-left: 5px solid #DB2777; color: #000 !important; margin-bottom: 8px; }
    .card-jargao { background-color: #ECFDF5; padding: 12px; border-radius: 8px; border-left: 6px solid #10B981; margin-bottom: 8px; color: #000 !important; font-size: 16px; font-weight: bold; }
    .texto-pista { color: #000000 !important; font-weight: bold; font-size: 16px; }
    div[data-testid="stToolbar"] {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# PROCESSAMENTO DE PDFS COM MEMÓRIA (CACHE)
@st.cache_data
def processar_pdf(file):
    paginas = []
    if file is not None:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                texto = page.extract_text(layout=True)
                if texto:
                    paginas.append(texto)
    return paginas

# 1. MENU LATERAL (UPLOADS INDEPENDENTES)
st.sidebar.header("📂 Arquivos do Leilão")
file_oe = st.sidebar.file_uploader("1. Ordem de Entrada (O.E.)", type="pdf")
file_cat = st.sidebar.file_uploader("2. Catálogo do Leilão", type="pdf")

texto_oe = processar_pdf(file_oe)
texto_cat = processar_pdf(file_cat)

# Identificação automática de lotes disponíveis
lotes_detectados = set()
for p in texto_oe + texto_cat:
    encontrados = re.findall(r"\b(?:LOTE|LT)?\s*(\d{1,3})\b", p, re.IGNORECASE)
    for l in encontrados:
        if 1 <= int(l) <= 200:
            lotes_detectados.add(f"{int(l):02d}")

lista_lotes = sorted(list(lotes_detectados), key=lambda x: int(x)) if lotes_detectados else [f"{i:02d}" for i in range(1, 51)]

# Estado da sessão para navegação por botões
if 'lote_idx' not in st.session_state:
    st.session_state.lote_idx = 0

if st.session_state.lote_idx >= len(lista_lotes):
    st.session_state.lote_idx = 0

# 2. BARRA SUPERIOR DE NAVEGAÇÃO DE PISTA
col_prev, col_select, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("◀️ LOTE ANTERIOR", use_container_width=True):
        st.session_state.lote_idx = max(0, st.session_state.lote_idx - 1)

with col_next:
    if st.button("PRÓXIMO LOTE ▶️", use_container_width=True):
        st.session_state.lote_idx = min(len(lista_lotes) - 1, st.session_state.lote_idx + 1)

with col_select:
    lote_selecionado = st.selectbox(
        "Selecionar Lote Direto:", 
        options=lista_lotes, 
        index=st.session_state.lote_idx,
        key="select_lote_box"
    )
    st.session_state.lote_idx = lista_lotes.index(lote_selecionado)

num_lote = lista_lotes[st.session_state.lote_idx]

st.markdown("---")

# 3. PAINEL PRINCIPAL DE PISTA
col_lote, col_info = st.columns([1, 2])

with col_lote:
    st.markdown(f"<p class='big-lote'>LOTE {num_lote}</p>", unsafe_allow_html=True)
    
    # Calculadora de Pista
    st.subheader("🧮 Calculadora de Parcela")
    qtd_parcelas = st.number_input("Nº de Parcelas", value=30, step=1)
    valor_parcela = st.number_input("Valor Parcela (R$)", value=500.0, step=50.0)
    valor_total = qtd_parcelas * valor_parcela
    
    st.metric(label="TOTAL DO LOTE", value=f"R$ {valor_total:,.2f}")

with col_info:
    # A) BUSCA NA ORDEM DE ENTRADA (O.E.)
    dados_oe = []
    if texto_oe:
        for p in texto_oe:
            for linha in p.split('\n'):
                if re.search(rf"\b0*{int(num_lote)}\b", linha):
                    dados_oe.append(linha.strip())
    
    if dados_oe:
        st.markdown(f"<div class='card-oe'>📋 <b>ORDEM DE ENTRADA:</b><br>{'<br>'.join(dados_oe[:3])}</div>", unsafe_allow_html=True)

    # B) BUSCA NO CATÁLOGO (GENEALOGIA)
    bloco_cat = []
    if texto_cat:
        for p in texto_cat:
            linhas = p.split('\n')
            for i, l in enumerate(linhas):
                if re.search(rf"\b(lote|lt)?\s*0*{int(num_lote)}\b", l, re.IGNORECASE):
                    inicio = max(0, i - 2)
                    fim = min(len(linhas), i + 14)
                    bloco_cat = linhas[inicio:fim]
                    break
            if bloco_cat:
                break

    if bloco_cat:
        st.markdown(f"<div class='card-lote'><span class='texto-pista'>📌 PEDIGREE DO CATÁLOGO — LOTE {num_lote}</span></div>", unsafe_allow_html=True)
        st.write("")
        
        esquerdas, direitas = [], []
        for l in bloco_cat:
            if len(l) > 40:
                col_e, col_d = l[:40].strip(), l[40:].strip()
                if col_e: esquerdas.append(col_e)
                if col_d: direitas.append(col_d)
            else:
                if l.strip(): esquerdas.append(l.strip())

        col_p, col_m = st.columns(2)
        with col_p:
            st.markdown("<div class='card-pai'>🟦 <b>LINHA PATERNA (ESQUERDA)</b></div>", unsafe_allow_html=True)
            for item in esquerdas[:5]:
                st.markdown(f"<p class='texto-pista'>• {item}</p>", unsafe_allow_html=True)

        with col_m:
            st.markdown("<div class='card-mae'>🟥 <b>LINHA MATERNA (DIREITA)</b></div>", unsafe_allow_html=True)
            for item in direitas[:5]:
                st.markdown(f"<p class='texto-pista'>• {item}</p>", unsafe_allow_html=True)
    elif not texto_oe and not texto_cat:
        st.info("👈 Dica: Suba a Ordem de Entrada ou o Catálogo no menu da esquerda. Se não tiver nenhum arquivo, use a calculadora e a navegação normalmente!")

    st.markdown("---")
    st.markdown("### 🎙️ Gatilhos Rápidos para o Microfone")
    st.markdown("<div class='card-jargao'><b>Morfologia:</b> Garupa larga, carcaça coberta e padrão de cabeceira!</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-jargao'><b>Oportunidade:</b> Raça pura, avaliação de ponta e liquidez imediata na pista!</div>", unsafe_allow_html=True)
