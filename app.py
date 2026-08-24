import streamlit as st
import pdfplumber
import os
from google import genai

# Configuração da página
st.set_page_config(page_title="PAINEL DE PISTA PRO", layout="wide")

# Estilo para botões e caixas de texto com alto contraste
st.markdown("""
    <style>
    .big-font { font-size: 28px !important; font-weight: bold; color: #1E3A8A; }
    .card-lote { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 8px solid #1E3A8A; color: #000 !important; }
    .card-ia { background-color: #EFF6FF; padding: 15px; border-radius: 8px; border-left: 6px solid #3B82F6; color: #000 !important; font-size: 16px; }
    .card-jargao { background-color: #ECFDF5; padding: 12px; border-radius: 8px; border-left: 6px solid #10B981; margin-bottom: 8px; color: #000 !important; font-size: 16px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎙️ PAINEL DE PISTA — LEILÃO DE ELITE WITH AI")

# Configuração da Chave de API (Insira sua API Key na barra lateral)
st.sidebar.header("🔑 Configuração da IA")
api_key = st.sidebar.text_input("Chave da API Gemini", type="password")

st.sidebar.markdown("---")
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
        st.sidebar.error("Erro ao ler o PDF.")

# PAINEL PRINCIPAL
col_lote, col_info = st.columns([1, 2])

with col_lote:
    st.markdown("<p class='big-font'>NÚMERO DO LOTE</p>", unsafe_allow_html=True)
    num_lote = st.text_input("Digite o número do lote:", value="12")
    
    # Calculadora Integrada
    st.markdown("---")
    qtd_parcelas = st.number_input("Número de Parcelas", value=30, step=1)
    valor_parcela = st.number_input("Valor da Parcela (R$)", value=500.0, step=50.0)
    valor_total = qtd_parcelas * valor_parcela
    
    st.metric(label="VALOR TOTAL DO LOTE", value=f"R$ {valor_total:,.2f}")

with col_info:
    st.markdown(f"<div class='card-lote'><span class='big-font'>📌 ANÁLISE GENÉTICA DA IA — LOTE {num_lote}</span></div>", unsafe_allow_html=True)
    st.write("")
    
    if st.button("🤖 Analisar Linhagem e Destaques com IA"):
        if not api_key:
            st.error("Por favor, insira a chave da API Gemini no menu lateral.")
        elif not text_content:
            st.warning("Suba o arquivo PDF do catálogo primeiro.")
        else:
            with st.spinner("IA analisando a árvore genealógica e buscando prêmios..."):
                # Unifica o texto do catálogo para envio
                texto_completo = "\n".join(text_content[:15])
                
                # Prompt instruindo a IA sobre a disposição gráfica (Esquerda = Pai / Direita = Mãe)
                prompt = f"""
                Você é um especialista em zootecnia e leilões de gado Nelore PO.
                Analise o seguinte catálogo de leilão e localize as informações do LOTE {num_lote}.

                Considere o padrão de pedigree:
                - O lado esquerdo representa a LINHA PATERNA (Pai, Avô Paterno, Avó Paterna).
                - O lado direito representa a LINHA MATERNA (Mãe, Avô Materno, Avó Materna).

                Forneça uma resposta estruturada e direta para leitura em voz alta pelo leiloeiro:
                1. PAIRAGEM E GENEALOGIA: Identifique claramente o Pai, Mãe, Avô Paterno e Avô Materno.
                2. DESTAQUES E PRÊMIOS: Identifique os grandes raçadores ou matrizes de destaque presente na árvore (ex: Bitelo da SS, Ludy de Garça, Landau, etc.) e diga resumidamente por que essa linhagem é importante ou premiada.
                3. 2 JARGÕES PRONTOS PARA A CANTA: Frases curtas de impacto para falar no microfone.

                Texto do Catálogo:
                {texto_completo}
                """
                
                try:
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    st.markdown(f"<div class='card-ia'>{response.text}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erro na conexão com a IA: {e}")

    st.markdown("---")
    st.markdown("### 🎙️ Gatilhos Básicos para o Microfone")
    st.markdown("<div class='card-jargao'><b>Morfologia:</b> Garupa larga, carcaça coberta e padrão de cabeceira!</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-jargao'><b>Pedigree:</b> União de raçadores consagrados na raça Nelore!</div>", unsafe_allow_html=True)
