import streamlit as st
import pdfplumber
import re
from io import BytesIO
import base64

st.set_page_config(
    page_title="PAINEL DO LEILOEIRO PRO",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# ==================== CSS ====================
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
        font-size: 60px;
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
        font-size: 24px;
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
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        border: 3px solid #FF9800;
    }
    .pai-box {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        font-size: 18px;
    }
    .mae-box {
        background: linear-gradient(135deg, #E91E63 0%, #C2185B 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        font-size: 18px;
    }
    .avo-paterno-box {
        background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 16px;
    }
    .avo-materno-box {
        background: linear-gradient(135deg, #F48FB1 0%, #EC407A 100%);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 16px;
    }
    .porcentagem-box {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        font-size: 28px;
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
    .gatilho-card {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 18px;
        border-radius: 15px;
        font-size: 18px;
        margin: 10px 0;
        min-height: 80px;
    }
    .stButton > button {
        min-height: 60px;
        font-size: 20px;
        border-radius: 15px;
        margin: 5px 0;
        touch-action: manipulation;
    }
    .catalogo-preview {
        background: rgba(0,0,0,0.05);
        border: 2px solid #FF9800;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        max-height: 600px;
        overflow-y: auto;
    }
    .catalogo-header {
        background: #FF9800;
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 10px;
    }
</style>
"""

st.markdown(css_code, unsafe_allow_html=True)

# ==================== PROCESSAMENTO DE PDF ====================
@st.cache_data(ttl=7200, show_spinner=False)
def processar_pdf(file_bytes):
    paginas = []
    
    if not file_bytes:
        return paginas
    
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            total_paginas = len(pdf.pages)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, page in enumerate(pdf.pages):
                progress = (i + 1) / total_paginas
                progress_bar.progress(progress)
                status_text.text(f"Lendo pagina {i+1} de {total_paginas}...")
                
                texto = None
                try:
                    texto = page.extract_text(layout=True)
                except:
                    pass
                
                if not texto:
                    try:
                        texto = page.extract_text()
                    except:
                        pass
                
                if texto:
                    paginas.append(texto)
            
            progress_bar.empty()
            status_text.empty()
            
    except Exception as e:
        st.error(f"Erro ao processar PDF: {str(e)}")
    
    return paginas

# ==================== ENCONTRAR PÁGINA DO LOTE NO CATÁLOGO ====================
@st.cache_data
def encontrar_pagina_catalogo(texto_cat_tuple, num_lote):
    """Encontra a página do catálogo onde o lote aparece"""
    texto_cat = list(texto_cat_tuple)
    
    for idx, pagina in enumerate(texto_cat):
        if re.search(rf"\b{int(num_lote)}\b", pagina):
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
        linhas = pagina.split('\n')
        
        for linha in linhas:
            linha_limpa = linha.strip()
            
            if not linha_limpa:
                continue
            
            if re.search(r"QTD\s+IDADE\s+PESO\s+CATEGORIA\s+PRODUTO", linha_limpa, re.IGNORECASE):
                continue
            
            if re.search(r"O\.E\.\s*LT", linha_limpa, re.IGNORECASE):
                continue
            
            if re.search(r"\d{2}/\d{2}/\d{4}", linha_limpa):
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
                        "lote": lt_num,
                        "posicao": f"{posicao}º A ENTRAR",
                        "qtd": "",
                        "idade": "",
                        "peso": "",
                        "categoria": "",
                        "produto": "",
                        "vendedor": "",
                        "raca": "",
                        "info_reproducao": "",
                        "tipo_reproducao": "",
                        "nome_animal": "",
                        "porcentagem_venda": "",
                        "linha_completa": linha_limpa
                    }
                    
                    # Porcentagem de venda
                    m_porcentagem = re.search(r"(\d+%)\s*de:\s*(.+)", linha_limpa, re.IGNORECASE)
                    if m_porcentagem:
                        dados["porcentagem_venda"] = m_porcentagem.group(1)
                        dados["nome_animal"] = m_porcentagem.group(2).strip()
                    
                    # Informações de reprodução
                    linha_lower = linha_limpa.lower()
                    
                    if "inseminada" in linha_lower:
                        m_insem = re.search(r"inseminada\s+(?:do|de)\s+([^|]+)", linha_limpa, re.IGNORECASE)
                        if m_insem:
                            dados["info_reproducao"] = f"Inseminada do {m_insem.group(1).strip()}"
                            dados["tipo_reproducao"] = "inseminacao"
                        else:
                            dados["info_reproducao"] = linha_limpa
                            dados["tipo_reproducao"] = "inseminacao"
                    
                    if "prenhe" in linha_lower or "prenha" in linha_lower:
                        m_prenhe = re.search(r"prenhe\s+(?:do|de)\s+([^|]+?)(?:\s*\.\s*prev\.?\s*de\s*parto:?\s*([^|]+))?", linha_limpa, re.IGNORECASE)
                        if m_prenhe:
                            dados["info_reproducao"] = f"Prenhe do {m_prenhe.group(1).strip()}"
                            if m_prenhe.group(2):
                                dados["info_reproducao"] += f" - Prev. de parto: {m_prenhe.group(2).strip()}"
                            dados["tipo_reproducao"] = "prenhez"
                        else:
                            dados["info_reproducao"] = linha_limpa
                            dados["tipo_reproducao"] = "prenhez"
                    
                    # Campos padrão
                    if len(parts) >= 1:
                        dados["qtd"] = parts[0]
                    if len(parts) >= 2:
                        dados["idade"] = parts[1]
                    if len(parts) >= 3:
                        dados["peso"] = parts[2]
                    if len(parts) >= 4:
                        dados["categoria"] = parts[3]
                    
                    # Produto e raça
                    if len(parts) >= 5:
                        produto_parts = []
                        vendedor_encontrado = False
                        
                        for part in parts[4:]:
                            part_lower = part.lower()
                            
                            if part_lower in ["nelore", "angus", "girolando", "holandês", "hereford", "braford", "simental"]:
                                dados["raca"] = part
                                vendedor_encontrado = True
                                continue
                            
                            if vendedor_encontrado:
                                if not dados["vendedor"]:
                                    dados["vendedor"] = part
                                else:
                                    dados["vendedor"] += " " + part
                            else:
                                produto_parts.append(part)
                        
                        dados["produto"] = " ".join(produto_parts)
                    
                    # Análise adicional
                    for part in parts:
                        part_lower = part.lower()
                        
                        if "kg" in part_lower:
                            dados["peso"] = part
                        
                        if "m" in part_lower and re.search(r"\d+m", part_lower):
                            dados["idade"] = part
                        
                        if any(k in part_lower for k in ["touro", "vaca", "matriz", "novilha", "bezerra", "bezerro", "garrote"]):
                            dados["categoria"] = part
                        
                        if any(k in part_lower for k in ["nelore", "angus", "girolando", "holandês"]):
                            dados["raca"] = part
                    
                    dados_por_lote[lt_num] = dados
    
    return sequencia, dados_por_lote

# ==================== EXTRAÇÃO DA GENEALOGIA (CORRIGIDA) ====================
def extrair_genealogia(texto_cat, num_lote):
    genealogia = {
        "pai": "",
        "mae": "",
        "avo_paterno": "",
        "avo_paterna": "",
        "avo_materno": "",
        "avo_materna": "",
        "info_reproducao": ""
    }
    
    if not texto_cat:
        return genealogia
    
    for pagina in texto_cat:
        linhas = pagina.split('\n')
        
        for i, linha in enumerate(linhas):
            linha_limpa = linha.strip()
            
            if re.search(rf"\b{int(num_lote)}\b", linha_limpa):
                inicio = max(0, i - 3)
                fim = min(len(linhas), i + 50)
                bloco = linhas[inicio:fim]
                
                for idx in range(len(bloco)):
                    linha_atual = bloco[idx].strip()
                    linha_upper = linha_atual.upper()
                    
                    if "PAI" in linha_upper and ":" in linha_atual:
                        m = re.search(r"PAI\s*:\s*(.+)", linha_atual, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["pai"] = m.group(1).strip()
                        elif idx + 1 < len(bloco):
                            proxima = bloco[idx + 1].strip()
                            if proxima and ":" not in proxima:
                                genealogia["pai"] = proxima
                    
                    elif "MAE" in linha_upper and ":" in linha_atual:
                        m = re.search(r"MAE\s*:\s*(.+)", linha_atual, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["mae"] = m.group(1).strip()
                        elif idx + 1 < len(bloco):
                            proxima = bloco[idx + 1].strip()
                            if proxima and ":" not in proxima:
                                genealogia["mae"] = proxima
                    
                    elif "AVO PATERNO" in linha_upper or "AVÔ PATERNO" in linha_upper:
                        m = re.search(r"AV[OÔ]\s+PATERNO\s*:\s*(.+)", linha_atual, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_paterno"] = m.group(1).strip()
                        elif idx + 1 < len(bloco):
                            proxima = bloco[idx + 1].strip()
                            if proxima and ":" not in proxima:
                                genealogia["avo_paterno"] = proxima
                    
                    elif "AVO PATERNA" in linha_upper or "AVÓ PATERNA" in linha_upper:
                        m = re.search(r"AV[OÓ]\s+PATERNA\s*:\s*(.+)", linha_atual, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_paterna"] = m.group(1).strip()
                        elif idx + 1 < len(bloco):
                            proxima = bloco[idx + 1].strip()
                            if proxima and ":" not in proxima:
                                genealogia["avo_paterna"] = proxima
                    
                    elif "AVO MATERNO" in linha_upper or "AVÔ MATERNO" in linha_upper:
                        m = re.search(r"AV[OÔ]\s+MATERNO\s*:\s*(.+)", linha_atual, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_materno"] = m.group(1).strip()
                        elif idx + 1 < len(bloco):
                            proxima = bloco[idx + 1].strip()
                            if proxima and ":" not in proxima:
                                genealogia["avo_materno"] = proxima
                    
                    elif "AVO MATERNA" in linha_upper or "AVÓ MATERNA" in linha_upper:
                        m = re.search(r"AV[OÓ]\s+MATERNA\s*:\s*(.+)", linha_atual, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_materna"] = m.group(1).strip()
                        elif idx + 1 < len(bloco):
                            proxima = bloco[idx + 1].strip()
                            if proxima and ":" not in proxima:
                                genealogia["avo_materna"] = proxima
                
                break
    
    return genealogia

# ==================== GATILHOS ====================
def gerar_gatilhos(dados_lote, genealogia=None):
    gatilhos = []
    
    if not dados_lote:
        return ["ANIMAL SELECIONADO!", "DOCUMENTAÇÃO EM DIA!", "OPORTUNIDADE!"]
    
    categoria = dados_lote.get("categoria", "").lower()
    raca = dados_lote.get("raca", "").lower()
    
    if dados_lote.get("porcentagem_venda"):
        gatilhos.append(f"VENDA DE {dados_lote['porcentagem_venda']}!")
    
    if dados_lote.get("nome_animal"):
        gatilhos.append(f"ANIMAL: {dados_lote['nome_animal']}!")
    
    if dados_lote.get("info_reproducao"):
        gatilhos.append(f"REPRODUÇÃO: {dados_lote['info_reproducao']}")
    
    if "touro" in categoria:
        gatilhos.append("TOURO MELHORADOR!")
    if "vaca" in categoria or "matriz" in dados_lote.get("produto", "").lower():
        gatilhos.append("MATRIZ COMPROVADA!")
    if "novilha" in categoria:
        gatilhos.append("NOVILHA DE ELITE!")
    if "bezerra" in categoria:
        gatilhos.append("BEZERRA PROMISSORA!")
    if "nelore" in raca:
        gatilhos.append("NELORE DOMINANTE!")
    
    if genealogia and genealogia.get("pai") and genealogia.get("mae"):
        gatilhos.append(f"PEDIGREE: {genealogia['pai']} x {genealogia['mae']}!")
    
    gatilhos.extend(["QUALIDADE GARANTIDA!", "PROCEDÊNCIA COMPROVADA!", "PREÇO IMPERDÍVEL!"])
    
    return gatilhos[:6]

# ==================== INTERFACE PRINCIPAL ====================
st.title("PAINEL DO LEILOEIRO PRO")

with st.sidebar:
    st.header("Arquivos")
    
    file_oe = st.file_uploader("Ordem de Entrada (PDF)", type="pdf", key="oe")
    
    if file_oe:
        tamanho_mb = len(file_oe.getvalue()) / (1024 * 1024)
        st.success(f"O.E. carregada! ({tamanho_mb:.1f} MB)")
    
    st.markdown("---")
    st.markdown("**Catálogo (opcional):**")
    
    file_cat = st.file_uploader("Catálogo do Leilão (PDF)", type="pdf", key="cat")
    
    if file_cat:
        tamanho_mb = len(file_cat.getvalue()) / (1024 * 1024)
        st.success(f"Catálogo carregado! ({tamanho_mb:.1f} MB)")
    
    st.markdown("---")
    st.header("Ordem dos Lotes")
    
    modo_ordenacao = st.radio(
        "Escolha a ordem:",
        ["ORDEM DE ENTRADA", "ORDEM NUMÉRICA"],
        index=0
    )
    
    st.markdown("---")
    mostrar_preview = st.checkbox("MOSTRAR PREVIEW DO CATÁLOGO", value=True)
    
    st.markdown("---")
    if st.button("VER DEBUG", use_container_width=True):
        st.session_state.mostrar_debug = True
    else:
        st.session_state.mostrar_debug = False

# Processar arquivos
if file_oe:
    with st.spinner("Lendo Ordem de Entrada..."):
        file_bytes = file_oe.getvalue()
        texto_oe = processar_pdf(file_bytes)
        texto_oe_tuple = tuple(texto_oe) if texto_oe else tuple()
else:
    texto_oe = []
    texto_oe_tuple = tuple()

if file_cat:
    with st.spinner("Lendo Catálogo..."):
        file_bytes = file_cat.getvalue()
        texto_cat = processar_pdf(file_bytes)
        texto_cat_tuple = tuple(texto_cat) if texto_cat else tuple()
else:
    texto_cat = []
    texto_cat_tuple = tuple()

# Extrair dados
sequencia_oe, mapa_oe = extrair_dados_oe(texto_oe_tuple)

# Definir lista de lotes
if sequencia_oe:
    if modo_ordenacao == "ORDEM DE ENTRADA":
        lista_lotes = sequencia_oe.copy()
        ordem_atual = "ORDEM DE ENTRADA"
    else:
        lista_lotes = sorted(sequencia_oe, key=lambda x: int(x))
        ordem_atual = "ORDEM NUMÉRICA"
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

# Navegação
ordem_texto = f"{ordem_atual} | Lote {st.session_state.lote_idx + 1} de {len(lista_lotes)}"
st.markdown(f'<div class="ordem-indicador">{ordem_texto}</div>', unsafe_allow_html=True)

col_prev, col_next = st.columns(2)

with col_prev:
    if st.button("ANTERIOR", use_container_width=True, key="prev_btn"):
        st.session_state.lote_idx = max(0, st.session_state.lote_idx - 1)
        st.rerun()

with col_next:
    if st.button("PROXIMO", use_container_width=True, key="next_btn"):
        st.session_state.lote_idx = min(len(lista_lotes) - 1, st.session_state.lote_idx + 1)
        st.rerun()

lote_selecionado = st.selectbox(
    "Ir para o lote:",
    options=lista_lotes,
    index=st.session_state.lote_idx,
    key="select_lote"
)
st.session_state.lote_idx = lista_lotes.index(lote_selecionado)

num_lote = lista_lotes[st.session_state.lote_idx]
dados_lote = mapa_oe.get(num_lote, {})
genealogia = extrair_genealogia(texto_cat, num_lote) if texto_cat else {}

# Encontrar página do catálogo
pagina_catalogo = -1
texto_pagina_catalogo = ""
if texto_cat and mostrar_preview:
    pagina_catalogo, texto_pagina_catalogo = encontrar_pagina_catalogo(texto_cat_tuple, num_lote)

# ==================== LAYOUT PRINCIPAL (2 COLUNAS) ====================
if mostrar_preview and texto_cat and pagina_catalogo >= 0:
    col_esquerda, col_direita = st.columns([3, 2])
else:
    col_esquerda, col_direita = st.columns([1, 1])

# ==================== COLUNA ESQUERDA (INFORMAÇÕES) ====================
with col_esquerda:
    lote_texto = f"LOTE {num_lote}"
    posicao_texto = dados_lote.get("posicao", f"{st.session_state.lote_idx + 1}º")
    st.markdown(f'<div class="lote-destaque">{lote_texto}<br><span style="font-size: 24px;">{posicao_texto} A ENTRAR</span></div>', unsafe_allow_html=True)
    
    # Porcentagem
    if dados_lote.get("porcentagem_venda"):
        pct_texto = f"VENDA DE {dados_lote['porcentagem_venda']} DO ANIMAL"
        st.markdown(f'<div class="porcentagem-box">{pct_texto}</div>', unsafe_allow_html=True)
    
    # Nome do animal
    if dados_lote.get("nome_animal"):
        nome_texto = dados_lote["nome_animal"]
        st.markdown(f'<div class="nome-animal-box">🐂 {nome_texto}</div>', unsafe_allow_html=True)
    
    # Reprodução
    if dados_lote.get("info_reproducao"):
        repro_texto = dados_lote["info_reproducao"]
        if dados_lote.get("tipo_reproducao") == "prenhez":
            st.markdown(f'<div class="prenhez-box">{repro_texto}</div>', unsafe_allow_html=True)
        elif dados_lote.get("tipo_reproducao") == "inseminacao":
            st.markdown(f'<div class="inseminacao-box">{repro_texto}</div>', unsafe_allow_html=True)
    
    if dados_lote:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### DADOS")
            cat_texto = dados_lote.get("categoria", "-")
            raca_texto = dados_lote.get("raca", "-")
            st.markdown(f'<div class="animal-info"><strong>CATEGORIA:</strong><br>{cat_texto}<br><br><strong>RACA:</strong><br>{raca_texto}</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("### MEDIDAS")
            peso_texto = dados_lote.get("peso", "-")
            idade_texto = dados_lote.get("idade", "-")
            st.markdown(f'<div class="animal-info"><strong>PESO:</strong><br>{peso_texto}<br><br><strong>IDADE:</strong><br>{idade_texto}</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown("### INFO")
            qtd_texto = dados_lote.get("qtd", "-")
            vend_texto = dados_lote.get("vendedor", "-")
            st.markdown(f'<div class="animal-info"><strong>QTD:</strong><br>{qtd_texto}<br><br><strong>VENDEDOR:</strong><br>{vend_texto}</div>', unsafe_allow_html=True)
    
    # Genealogia
    if genealogia:
        st.markdown("### GENEALOGIA")
        
        col_pai, col_mae = st.columns(2)
        
        with col_pai:
            if genealogia.get("pai"):
                pai_texto = genealogia["pai"]
                st.markdown(f'<div class="pai-box"><strong>PAI:</strong><br>{pai_texto}</div>', unsafe_allow_html=True)
            
            col_avop1, col_avop2 = st.columns(2)
            with col_avop1:
                if genealogia.get("avo_paterno"):
                    texto_avop = genealogia["avo_paterno"]
                    st.markdown(f'<div class="avo-paterno-box"><strong>AVO PATERNO:</strong><br>{texto_avop}</div>', unsafe_allow_html=True)
            with col_avop2:
                if genealogia.get("avo_paterna"):
                    texto_avop2 = genealogia["avo_paterna"]
                    st.markdown(f'<div class="avo-paterno-box"><strong>AVO PATERNA:</strong><br>{texto_avop2}</div>', unsafe_allow_html=True)
        
        with col_mae:
            if genealogia.get("mae"):
                mae_texto = genealogia["mae"]
                st.markdown(f'<div class="mae-box"><strong>MAE:</strong><br>{mae_texto}</div>', unsafe_allow_html=True)
            
            col_avom1, col_avom2 = st.columns(2)
            with col_avom1:
                if genealogia.get("avo_materno"):
                    texto_avom = genealogia["avo_materno"]
                    st.markdown(f'<div class="avo-materno-box"><strong>AVO MATERNO:</strong><br>{texto_avom}</div>', unsafe_allow_html=True)
            with col_avom2:
                if genealogia.get("avo_materna"):
                    texto_avom2 = genealogia["avo_materna"]
                    st.markdown(f'<div class="avo-materno-box"><strong>AVO MATERNA:</strong><br>{texto_avom2}</div>', unsafe_allow_html=True)
    
    # Gatilhos
    st.markdown("### GATILHOS")
    gatilhos = gerar_gatilhos(dados_lote, genealogia)
    
    for gatilho in gatilhos:
        st.markdown(f'<div class="gatilho-card">{gatilho}</div>', unsafe_allow_html=True)

# ==================== COLUNA DIREITA (PREVIEW DO CATÁLOGO) ====================
with col_direita:
    if mostrar_preview and texto_cat and pagina_catalogo >= 0:
        st.markdown(f'<div class="catalogo-header">📖 CATÁLOGO - PÁGINA {pagina_catalogo + 1}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="catalogo-preview">{texto_pagina_catalogo}</div>', unsafe_allow_html=True)
    elif mostrar_preview and texto_cat:
        st.info("Lote não encontrado no catálogo")
    elif mostrar_preview and not texto_cat:
        st.info("Carregue o catálogo para ver o preview")

st.markdown("---")
st.markdown(f"**Total de lotes: {len(lista_lotes)}**")
