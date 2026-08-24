import streamlit as st
import pdfplumber

# Configuração da página ampla
st.set_page_config(page_title="PAINEL DO LEILOEIRO", layout="wide")

# Estilos visuais para leitura rápida no tablet/celular
st.markdown("""
    <style>
    .big-font { font-size: 28px !important; font-weight: bold; color: #1E3A8A; }
    .card-lote { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 8px solid #1E3A8A; }
    .card-jargao { background-color: #ECFDF5; padding: 12px; border-radius: 8px; border-left: 6px solid #10B981; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎙️ PAINEL DE PISTA — LEILÃO")

# 1. MENU LATERAL
st.sidebar.header("📂 Arquivo do Leilão")
uploaded_file = st.sidebar.file_uploader("Suba o PDF do Catálogo", type="pdf")

if uploaded_file is not None:
    text_content = ""
    try:
        # Extração segura página por página
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
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
        num_lote = st.text_input("Digite o número:", value="12")
        
        st.markdown("---")
        st.metric(label="PARCELA ATUAL", value=f"R$ {valor_parcela:,.2f}")
        st.metric(label="VALOR TOTAL DO LOTE", value=f"R$ {valor_total:,.2f}")

    with col_info:
        st.markdown(f"<div class='card-lote'><span class='big-font'>📌 LOTE {num_lote}</span></div>", unsafe_allow_html=True)
        st.write("")
        
        # Busca inteligente e sem erros
        if text_content:
            linhas = text_content.split('\n')
            # Busca linhas que contêm o número do lote
            linhas_encontradas = [l.strip() for l in linhas if l.strip() and num_lote in l]
            
            if linhas_encontradas:
                st.markdown("### 📋 Dados Encontrados no Catálogo")
                for linha in linhas_encontradas[:5]:
                    st.write(f"• {linha}")
            else:
                st.warning(f"Nenhuma linha com o número '{num_lote}' foi encontrada no texto do PDF.")
        else:
            st.info("Este PDF parece conter apenas imagens de digitalização (sem texto selecionável).")

        st.markdown("---")
        st.markdown("### 🎙️ Gatilhos de Canta para o Microfone")
        st.markdown("<div class='card-jargao'><b>Morfologia:</b> Garupa larga, carcaça coberta e padrão de cabeceira!</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-jargao'><b>Impacto:</b> Matriz pra chancelar a bezerrada e agregar valor no rebanho!</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-jargao'><b>Fechamento:</b> Lote com essa avaliação genética não sobra na pista!</div>", unsafe_allow_html=True)

else:
    st.info("👈 Para começar, suba o PDF do catálogo no menu da esquerda.")
