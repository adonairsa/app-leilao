import streamlit as st
import pdfplumber
import re
import os
import requests
import base64
from io import BytesIO

st.set_page_config(
    page_title="PAINEL DO LEILOEIRO PRO",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# ==================== CSS COM ALTO CONTRASTE ====================
css_code = """
<style>
    #MainMenu {visibility: hidden; display: none;}
    footer {visibility: hidden; display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    .viewerBadge_container__1QSob {display: none !important;}
    a[href*="streamlit"] {display: none !important;}
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    header[data-testid="stHeader"] {display: none;}
    .main {padding: 0;}
    
    .lote-destaque {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        font-size: 55px;
        font-weight: bold;
        margin: 15px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .ordem-indicador {
        background: #4CAF50;
        color: white;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
        font-size: 22px;
    }
    .animal-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
    .prenhez-box {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF4757 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        border: 3px solid #FF0000;
    }
    .inseminacao-box {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        border: 3px solid #FF9800;
    }
    .porcentagem-box {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        font-size: 26px;
        font-weight: bold;
        text-align: center;
        border: 3px solid #FFD700;
    }
    .nome-animal-box {
        background: linear-gradient(135deg, #00BCD4 0%, #0097A7 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
    }
    .ai-consideracoes-box {
        background-color: #1E1B4B !important;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 8px solid #818CF8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .ai-consideracoes-box, .ai-consideracoes-box * {
        color: #FFFFFF !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    .gatilho-card {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 18px;
        border-radius: 15px;
        font-size: 18px;
        margin: 10px 0;
        font-weight: bold;
    }
    .stButton > button {
        min-height: 60px;
        font-size: 20px;
        border-radius: 15px;
        margin: 5px 0;
        touch-action: manipulation;
    }
    .catalogo-header {
        background: #FF9800;
        color: white;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 10px;
    }
</style>
"""

st.markdown(css_code, unsafe_allow_html=True)

# ==================== BUSCA SEGURA DE API KEY ====================
def obter_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except:
        pass
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")

# ==================== PROCESSAMENTO DE PDF ====================
@st.cache_data(ttl=7200, show_spinner=False)
def processar_pdf(file_bytes):
    paginas = []
    if not file_bytes:
        return paginas
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                texto = page.extract_text(layout=True) or page.extract_text()
                if texto:
                    paginas.append(texto)
    except Exception as e:
        st.error(f"Erro ao processar PDF: {str(e)}")
    return paginas

@st.cache_data(show_spinner=False)
def obter_imagem_bytes_pagina(file_bytes, num_pagina):
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            if 0 <= num_pagina < len(pdf.pages):
                img = pdf.pages[num_pagina].to_image(resolution=150).original
                buffer = BytesIO()
                img.save(buffer, format="JPEG")
                return buffer.getvalue()
    except:
        return None
    return None

@st.cache_data
def encontrar_pagina_catalogo(texto_cat_tuple, num_lote):
    texto_cat = list(texto_cat_tuple)
    for idx, pagina in enumerate(texto_cat):
        if re.search(rf"\b(lote|lt)?\s*0*{int(num_lote)}\b", pagina, re.IGNORECASE):
            return idx, pagina
    return -1, ""

# ==================== EXTRAÇÃO DA ORDEM DE ENTRADA ====================
@st.cache_data
def extrair_dados_oe(texto_oe_tuple):
    texto_oe = list(texto_oe_tuple)
    sequencia = []
    dados_por_lote = {}
    
    if not texto_oe:
        return sequencia, dados_por_lote
    
    for pagina in texto_oe:
        for linha in pagina.split('\n'):
            linha_limpa = linha.strip()
            if not linha_limpa or re.search(r"QTD\s+IDADE\s+PESO", linha_limpa, re.IGNORECASE) or re.search(r"O\.E\.\s*LT", linha_limpa, re.IGNORECASE):
                continue
            
            m_posicao = re.match(r"^(\d{1,3})\s*[º°]?\s+(\d{1,3})\s+", linha_limpa)
            if m_posicao:
                posicao = int(m_posicao.group(1))
                numero_lote = int(m_posicao.group(2))
                
                if 1 <= numero_lote <= 500:
                    lt_num = f"{numero_lote:02d}"
                    if lt_num not in sequencia:
                        sequencia.append(lt_num)
                    
                    restante = linha_limpa[m_posicao.end():].strip()
                    parts = restante.split()
                    
                    dados = {
                        "lote": lt_num, "posicao": f"{posicao}º A ENTRAR",
                        "qtd": "", "idade": "", "peso": "", "categoria": "",
                        "produto": "", "vendedor": "", "raca": "", "info_reproducao": "",
                        "tipo_reproducao": "", "nome_animal": "", "porcentagem_venda": "",
                        "linha_completa": linha_limpa
                    }
                    
                    m_porcentagem = re.search(r"(\d+%)\s*de:\s*(.+)", linha_limpa, re.IGNORECASE)
                    if m_porcentagem:
                        dados["porcentagem_venda"] = m_porcentagem.group(1)
                        dados["nome_animal"] = m_porcentagem.group(2).strip()
                    
                    linha_lower = linha_limpa.lower()
                    if "inseminada" in linha_lower:
                        m_insem = re.search(r"inseminada\s+(?:do|de)\s+([^|]+)", linha_limpa, re.IGNORECASE)
                        dados["info_reproducao"] = f"Inseminada do {m_insem.group(1).strip()}" if m_insem else linha_limpa
                        dados["tipo_reproducao"] = "inseminacao"
                    
                    if "prenhe" in linha_lower or "prenha" in linha_lower:
                        m_prenhe = re.search(r"prenhe\s+(?:do|de)\s+([^|]+?)(?:\s*\.\s*prev\.?\s*de\s*parto:?\s*([^|]+))?", linha_limpa, re.IGNORECASE)
                        if m_prenhe:
                            dados["info_reproducao"] = f"Prenhe do {m_prenhe.group(1).strip()}"
                            if m_prenhe.group(2):
                                dados["info_reproducao"] += f" - Prev. parto: {m_prenhe.group(2).strip()}"
                        else:
                            dados["info_reproducao"] = linha_limpa
                        dados["tipo_reproducao"] = "prenhez"
                    
                    if len(parts) >= 1: dados["qtd"] = parts[0]
                    if len(parts) >= 2: dados["idade"] = parts[1]
                    if len(parts) >= 3: dados["peso"] = parts[2]
                    if len(parts) >= 4: dados["categoria"] = parts[3]
                    
                    if len(parts) >= 5:
                        produto_parts, vendedor_encontrado = [], False
                        for part in parts[4:]:
                            if part.lower() in ["nelore", "angus", "girolando", "holandês"]:
                                dados["raca"] = part
                                vendedor_encontrado = True
                                continue
                            if vendedor_encontrado:
                                dados["vendedor"] += " " + part if dados["vendedor"] else part
                            else:
                                produto_parts.append(part)
                        dados["produto"] = " ".join(produto_parts)
                    
                    dados_por_lote[lt_num] = dados
    return sequencia, dados_por_lote

# ==================== ANÁLISE DIRETA VIA REST API (COMPATÍVEL COM CHAVES AQ...) ====================
@st.cache_data(show_spinner=False)
def analisar_lote_com_gemini(img_bytes, num_lote, dados_lote, api_key):
    if not api_key:
        return "⚠️ Chave GEMINI_API_KEY não encontrada nos Secrets do Streamlit."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}
        
        base64_image = base64.b64encode(img_bytes).decode('utf-8')

        prompt = f"""
        Você é um especialista zootecnista e leiloeiro de elite.
        Analise a imagem do LOTE {num_lote} no catálogo e os dados de pista:
        - Nome/Produto: {dados_lote.get('nome_animal') or dados_lote.get('produto', 'N/A')}
        - Venda: {dados_lote.get('porcentagem_venda', '100%')}
        - Reprodução/Touro: {dados_lote.get('info_reproducao', 'N/A')}
        - Categoria/Peso: {dados_lote.get('categoria', 'N/A')} - {dados_lote.get('peso', 'N/A')}

        Forneça uma análise concisa em formato de tópicos:
        1. 🏆 **Destaques da Linhagem & Premiações**: Raçadores e matrizes consagrados da árvore e o valor dessa genética.
        2. 🧬 **Valorização da Reprodução**: Qualidade do touro acasalado e do ventre.
        3. 💡 **Argumento de Pista**: 1 frase marcante de impacto para o microfone.
        """

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()

        if response.status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            err_msg = res_json.get('error', {}).get('message', response.text)
            return f"Erro na requisição ({response.status_code}): {err_msg}"

    except Exception as e:
        return f"Erro ao processar análise da IA: {str(e)}"

# ==================== GATILHOS ====================
def gerar_gatilhos(dados_lote):
    gatilhos = []
    if not dados_lote:
        return ["ANIMAL SELECIONADO!", "QUALIDADE GARANTIDA!", "OPORTUNIDADE NA PISTA!"]
    
    categoria = dados_lote.get("categoria", "").lower()
    if dados_lote.get("porcentagem_venda"):
        gatilhos.append(f"VENDA DE {dados_lote['porcentagem_venda']}!")
    if dados_lote.get("nome_animal"):
        gatilhos.append(f"ANIMAL: {dados_lote['nome_animal']}!")
    if dados_lote.get("info_reproducao"):
        gatilhos.append(f"REPRODUÇÃO: {dados_lote['info_reproducao']}")
    if "novilha" in categoria or "bezerra" in categoria:
        gatilhos.append("FÊMEA DE CABECEIRA E FUTURO DO REBANHO!")
    if "vaca" in categoria:
        gatilhos.append("MATRIZ COMPROVADA E PRODUTIVA!")
        
    gatilhos.extend(["PROCEDÊNCIA COMPROVADA!", "LIQUIDEZ IMEDIATA NA PISTA!"])
    return gatilhos[:5]

# ==================== INTERFACE PRINCIPAL ====================
st.title("PAINEL DO LEILOEIRO PRO")

api_key = obter_api_key()

with st.sidebar:
    st.header("Arquivos")
    file_oe = st.file_uploader("Ordem de Entrada (PDF)", type="pdf", key="oe")
    file_cat = st.file_uploader("Catálogo do Leilão (PDF)", type="pdf", key="cat")
    
    st.markdown("---")
    modo_ordenacao = st.radio("Escolha a ordem:", ["ORDEM DE ENTRADA", "ORDEM NUMÉRICA"], index=0)
    mostrar_preview = st.checkbox("MOSTRAR PREVIEW VISUAL DO CATÁLOGO", value=True)

texto_oe = processar_pdf(file_oe.getvalue()) if file_oe else []
texto_cat = processar_pdf(file_cat.getvalue()) if file_cat else []

sequencia_oe, mapa_oe = extrair_dados_oe(tuple(texto_oe))

if sequencia_oe:
    lista_lotes = sequencia_oe.copy() if modo_ordenacao == "ORDEM DE ENTRADA" else sorted(sequencia_oe, key=lambda x: int(x))
    ordem_atual = modo_ordenacao
else:
    lista_lotes = []
    ordem_atual = "NENHUM LOTE ENCONTRADO"

if 'lote_idx' not in st.session_state:
    st.session_state.lote_idx = 0

if not lista_lotes:
    st.warning("Carregue a Ordem de Entrada (PDF) para começar!")
    st.stop()

if st.session_state.lote_idx >= len(lista_lotes):
    st.session_state.lote_idx = 0

# BARRA DE NAVEGAÇÃO
ordem_texto = f"{ordem_atual} | Lote {st.session_state.lote_idx + 1} de {len(lista_lotes)}"
st.markdown(f'<div class="ordem-indicador">{ordem_texto}</div>', unsafe_allow_html=True)

col_prev, col_next = st.columns(2)
with col_prev:
    if st.button("ANTERIOR", use_container_width=True, key="prev_btn"):
        st.session_state.lote_idx = max(0, st.session_state.lote_idx - 1)
        st.rerun()

with col_next:
    if st.button("PRÓXIMO", use_container_width=True, key="next_btn"):
        st.session_state.lote_idx = min(len(lista_lotes) - 1, st.session_state.lote_idx + 1)
        st.rerun()

lote_selecionado = st.selectbox("Ir para o lote:", options=lista_lotes, index=st.session_state.lote_idx, key="select_lote")
st.session_state.lote_idx = lista_lotes.index(lote_selecionado)

num_lote = lista_lotes[st.session_state.lote_idx]
dados_lote = mapa_oe.get(num_lote, {})

pagina_catalogo, _ = encontrar_pagina_catalogo(tuple(texto_cat), num_lote) if texto_cat and mostrar_preview else (-1, "")
img_pagina_bytes = obter_imagem_bytes_pagina(file_cat.getvalue(), pagina_catalogo) if (file_cat and pagina_catalogo >= 0) else None

# LAYOUT PRINCIPAL
col_esquerda, col_direita = st.columns([1, 1])

# COLUNA ESQUERDA (DADOS PRINCIPAIS, CONSIDERAÇÕES DA IA E GATILHOS)
with col_esquerda:
    lote_texto = f"LOTE {num_lote}"
    posicao_texto = dados_lote.get("posicao", f"{st.session_state.lote_idx + 1}º")
    st.markdown(f'<div class="lote-destaque">{lote_texto}<br><span style="font-size: 24px;">{posicao_texto}</span></div>', unsafe_allow_html=True)
    
    if dados_lote.get("porcentagem_venda"):
        st.markdown(f'<div class="porcentagem-box">VENDA DE {dados_lote["porcentagem_venda"]} DO ANIMAL</div>', unsafe_allow_html=True)
    
    if dados_lote.get("nome_animal"):
        st.markdown(f'<div class="nome-animal-box">🐂 {dados_lote["nome_animal"]}</div>', unsafe_allow_html=True)
    
    if dados_lote.get("info_reproducao"):
        css_repro = "prenhez-box" if dados_lote.get("tipo_reproducao") == "prenhez" else "inseminacao-box"
        st.markdown(f'<div class="{css_repro}">{dados_lote["info_reproducao"]}</div>', unsafe_allow_html=True)
    
    if dados_lote:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="animal-info"><strong>CATEGORIA:</strong><br>{dados_lote.get("categoria","-")}<br><br><strong>RAÇA:</strong><br>{dados_lote.get("raca","-")}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="animal-info"><strong>PESO:</strong><br>{dados_lote.get("peso","-")}<br><br><strong>IDADE:</strong><br>{dados_lote.get("idade","-")}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="animal-info"><strong>QTD:</strong><br>{dados_lote.get("qtd","-")}<br><br><strong>VENDEDOR:</strong><br>{dados_lote.get("vendedor","-")}</div>', unsafe_allow_html=True)
    
    # 🤖 CONSIDERAÇÕES DA IA
    if img_pagina_bytes:
        with st.spinner("🤖 Gemini analisando a linhagem genética e reprodução..."):
            analise_ia = analisar_lote_com_gemini(img_pagina_bytes, num_lote, dados_lote, api_key)
            st.markdown(f'''
            <div class="ai-consideracoes-box">
                <h3 style="margin-top:0; color:#818CF8;">🤖 CONSIDERAÇÕES DA IA (LINHAGEM & REPRODUÇÃO)</h3>
                <div>{analise_ia}</div>
            </div>
            ''', unsafe_allow_html=True)

    # 🎙️ GATILHOS
    st.markdown("### 🎙️ GATILHOS PARA O MICROFONE")
    gatilhos = gerar_gatilhos(dados_lote)
    for g in gatilhos:
        st.markdown(f'<div class="gatilho-card">{g}</div>', unsafe_allow_html=True)

# COLUNA DIREITA (PREVIEW VISUAL DO CATÁLOGO)
with col_direita:
    if mostrar_preview and img_pagina_bytes:
        st.markdown(f'<div class="catalogo-header">📖 CATÁLOGO VISUAL - PÁGINA {pagina_catalogo + 1}</div>', unsafe_allow_html=True)
        st.image(img_pagina_bytes, use_container_width=True)
    elif mostrar_preview and file_cat:
        st.info("Lote não localizado na busca visual do catálogo.")
    elif mostrar_preview and not file_cat:
        st.info("Suba o arquivo do catálogo no menu lateral para abrir o preview visual.")
