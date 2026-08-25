import streamlit as st
import pdfplumber
import re
from io import BytesIO

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
    .pai-box {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        font-size: 18px;
        font-weight: bold;
    }
    .mae-box {
        background: linear-gradient(135deg, #E91E63 0%, #C2185B 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        font-size: 18px;
        font-weight: bold;
    }
    .avo-paterno-box {
        background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 16px;
        font-weight: bold;
    }
    .avo-materno-box {
        background: linear-gradient(135deg, #F48FB1 0%, #EC407A 100%);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 16px;
        font-weight: bold;
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
                status_text.text(f"Lendo página {i+1} de {total_paginas}...")
                
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

@st.cache_data(show_spinner=False)
def renderizar_pagina_imagem(file_bytes, num_pagina):
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            if 0 <= num_pagina < len(pdf.pages):
                page = pdf.pages[num_pagina]
                return page.to_image(resolution=150).original
    except Exception as e:
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
        linhas = pagina.split('\n')
        for linha in linhas:
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

# ==================== EXTRAÇÃO ESPACIAL DE GENEALOGIA (CORRIGIDA) ====================
@st.cache_data(show_spinner=False)
def extrair_genealogia_espacial(file_bytes, num_pagina):
    genealogia = {
        "pai": "", "mae": "",
        "avo_paterno": "", "avo_paterna": "",
        "avo_materno": "", "avo_materna": ""
    }
    if not file_bytes or num_pagina < 0:
        return genealogia

    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            if num_pagina >= len(pdf.pages):
                return genealogia
            page = pdf.pages[num_pagina]
            width = page.width
            height = page.height
            mid_x = width / 2.0

            words = page.extract_words()
            
            # Extrai apenas palavras dentro do retângulo do pedigree (28% a 82% da altura)
            pedigree_words = [
                w for w in words 
                if height * 0.28 <= w['top'] <= height * 0.82
                and not any(k in w['text'].upper() for k in ["PESO", "PONDERAL", "INSEMINADA", "PRENHE", "PARIDA", "PREV.", "FAZENDA", "TERRA"])
            ]
            
            if not pedigree_words:
                return genealogia

            min_y = min(w['top'] for w in pedigree_words)
            max_y = max(w['bottom'] for w in pedigree_words)
            h_pedigree = max_y - min_y
            
            if h_pedigree <= 0:
                return genealogia

            # Divisão Estrita: Esquerda (Linha Paterna) e Direita (Linha Materna)
            left_words = [w for w in pedigree_words if w['x1'] <= mid_x + 5]
            right_words = [w for w in pedigree_words if w['x0'] >= mid_x - 5]

            def extrair_texto_faixa(words_list, y_min_pct, y_max_pct):
                target_words = [
                    w for w in words_list 
                    if min_y + h_pedigree * y_min_pct <= w['top'] <= min_y + h_pedigree * y_max_pct
                ]
                if not target_words:
                    return ""
                
                target_words.sort(key=lambda w: (round(w['top'] / 7), w['x0']))
                
                linhas = []
                linha_atual = []
                last_top = None
                
                for w in target_words:
                    if last_top is None or abs(w['top'] - last_top) < 7:
                        linha_atual.append(w['text'])
                    else:
                        linhas.append(" ".join(linha_atual))
                        linha_atual = [w['text']]
                    last_top = w['top']
                if linha_atual:
                    linhas.append(" ".join(linha_atual))
                
                return " ".join(linhas).strip()

            # LADO PATERNO (ESQUERDA)
            genealogia["avo_paterno"] = extrair_texto_faixa(left_words, 0.10, 0.35)
            genealogia["pai"] = extrair_texto_faixa(left_words, 0.35, 0.65)
            genealogia["avo_paterna"] = extrair_texto_faixa(left_words, 0.65, 0.90)

            # LADO MATERNO (DIREITA)
            genealogia["avo_materno"] = extrair_texto_faixa(right_words, 0.10, 0.35)
            genealogia["mae"] = extrair_texto_faixa(right_words, 0.35, 0.65)
            genealogia["avo_materna"] = extrair_texto_faixa(right_words, 0.65, 0.90)

    except Exception as e:
        pass

    return genealogia

# ==================== GATILHOS ====================
def gerar_gatilhos(dados_lote, genealogia=None):
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
    
    if genealogia and genealogia.get("pai") and genealogia.get("mae"):
        gatilhos.append(f"PEDIGREE: {genealogia['pai']} x {genealogia['mae']}!")
        
    gatilhos.extend(["PROCEDÊNCIA COMPROVADA!", "LIQUIDEZ IMEDIATA NA PISTA!"])
    return gatilhos[:5]

# ==================== INTERFACE PRINCIPAL ====================
st.title("PAINEL DO LEILOEIRO PRO")

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

pagina_catalogo, texto_pagina_catalogo = encontrar_pagina_catalogo(tuple(texto_cat), num_lote) if texto_cat and mostrar_preview else (-1, "")

# EXTRAÇÃO ESPACIAL DE GENEALOGIA
genealogia = extrair_genealogia_espacial(file_cat.getvalue(), pagina_catalogo) if (file_cat and pagina_catalogo >= 0) else {}

# LAYOUT PRINCIPAL
col_esquerda, col_direita = st.columns([1, 1])

# COLUNA ESQUERDA (DADOS PRINCIPAIS E GENEALOGIA)
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
    
    # GENEALOGIA EXTRAÍDA DE FORMA ESPACIAL
    has_gen = any(v for v in genealogia.values())
    if has_gen:
        st.markdown("### 🧬 GENEALOGIA")
        col_pai, col_mae = st.columns(2)
        
        with col_pai:
            if genealogia.get("pai"):
                st.markdown(f'<div class="pai-box"><strong>PAI:</strong><br>{genealogia["pai"]}</div>', unsafe_allow_html=True)
            col_avop1, col_avop2 = st.columns(2)
            with col_avop1:
                if genealogia.get("avo_paterno"):
                    st.markdown(f'<div class="avo-paterno-box"><strong>AVÔ PAT:</strong><br>{genealogia["avo_paterno"]}</div>', unsafe_allow_html=True)
            with col_avop2:
                if genealogia.get("avo_paterna"):
                    st.markdown(f'<div class="avo-paterno-box"><strong>AVÓ PAT:</strong><br>{genealogia["avo_paterna"]}</div>', unsafe_allow_html=True)
        
        with col_mae:
            if genealogia.get("mae"):
                st.markdown(f'<div class="mae-box"><strong>MÃE:</strong><br>{genealogia["mae"]}</div>', unsafe_allow_html=True)
            col_avom1, col_avom2 = st.columns(2)
            with col_avom1:
                if genealogia.get("avo_materno"):
                    st.markdown(f'<div class="avo-materno-box"><strong>AVÔ MAT:</strong><br>{genealogia["avo_materno"]}</div>', unsafe_allow_html=True)
            with col_avom2:
                if genealogia.get("avo_materna"):
                    st.markdown(f'<div class="avo-materno-box"><strong>AVÓ MAT:</strong><br>{genealogia["avo_materna"]}</div>', unsafe_allow_html=True)

    st.markdown("### 🎙️ GATILHOS")
    gatilhos = gerar_gatilhos(dados_lote, genealogia)
    for g in gatilhos:
        st.markdown(f'<div class="gatilho-card">{g}</div>', unsafe_allow_html=True)

# COLUNA DIREITA (PREVIEW VISUAL DO CATÁLOGO)
with col_direita:
    if mostrar_preview and file_cat and pagina_catalogo >= 0:
        st.markdown(f'<div class="catalogo-header">📖 CATÁLOGO VISUAL - PÁGINA {pagina_catalogo + 1}</div>', unsafe_allow_html=True)
        img_pagina = renderizar_pagina_imagem(file_cat.getvalue(), pagina_catalogo)
        if img_pagina:
            st.image(img_pagina, use_container_width=True)
        else:
            st.info("Não foi possível gerar a foto desta página.")
    elif mostrar_preview and file_cat:
        st.info("Lote não localizado na busca visual do catálogo.")
    elif mostrar_preview and not file_cat:
        st.info("Suba o arquivo do catálogo no menu lateral para abrir o preview visual.")
