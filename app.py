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

# ==================== ESCONDER MENU E RODAPÉ ====================
st.markdown("""
<style>
    #MainMenu {
        visibility: hidden;
        display: none;
    }
    
    footer {
        visibility: hidden;
        display: none;
    }
    
    [data-testid="stToolbar"] {
        display: none;
    }
    
    [data-testid="stDecoration"] {
        display: none;
    }
    
    .viewerBadge_container__1QSob {
        display: none !important;
    }
    
    a[href*="streamlit"] {
        display: none !important;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    header[data-testid="stHeader"] {
        display: none;
    }
    
    .main {
        padding: 0;
    }
    
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
        box-shadow: 0 0 20px rgba(255,0,0,0.5);
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
        box-shadow: 0 0 20px rgba(255,152,0,0.5);
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
</style>
""", unsafe_allow_html=True)

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
                    
                    if re.search(r"inseminada\s+(?:do|de)\s+(\S+)", linha_lower):
                        m_insem = re.search(r"inseminada\s+(?:do|de)\s+([^|]+)", linha_limpa, re.IGNORECASE)
                        if m_insem:
                            dados["info_reproducao"] = f"Inseminada do {m_insem.group(1).strip()}"
                            dados["tipo_reproducao"] = "inseminacao"
                    
                    if re.search(r"prenhe\s+(?:do|de)\s+(\S+)", linha_lower):
                        m_prenhe = re.search(r"prenhe\s+(?:do|de)\s+([^|]+?)(?:\s*\.\s*prev\.?\s*de\s*parto:?\s*([^|]+))?", linha_limpa, re.IGNORECASE)
                        if m_prenhe:
                            dados["info_reproducao"] = f"Prenhe do {m_prenhe.group(1).strip()}"
                            if m_prenhe.group(2):
                                dados["info_reproducao"] += f" - Prev. de parto: {m_prenhe.group(2).strip()}"
                            dados["tipo_reproducao"] = "prenhez"
                    
                    if not dados["info_reproducao"]:
                        if "inseminada" in linha_lower:
                            dados["info_reproducao"] = linha_limpa
                            dados["tipo_reproducao"] = "inseminacao"
                        elif "prenhe" in linha_lower or "prenha" in linha_lower:
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

# ==================== EXTRAÇÃO DA GENEALOGIA ====================
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
                inicio = max(0, i - 5)
                fim = min(len(linhas), i + 40)
                bloco = linhas[inicio:fim]
                
                for idx, linha_bloco in enumerate(bloco):
                    linha_limpa_bloco = linha_bloco.strip()
                    linha_lower = linha_limpa_bloco.lower()
                    
                    # PAI
                    if re.search(r"\bPAI\s*:", linha_limpa_bloco, re.IGNORECASE):
                        m = re.search(r"PAI\s*:\s*(.+)", linha_limpa_bloco, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["pai"] = m.group(1).strip()
                        else:
                            for j in range(idx + 1, min(idx + 3, len(bloco))):
                                if bloco[j].strip() and not re.search(r":", bloco[j]):
                                    genealogia["pai"] = bloco[j].strip()
                                    break
                    
                    # MÃE
                    if re.search(r"\bMÃE\s*:|\bMAE\s*:", linha_limpa_bloco, re.IGNORECASE):
                        m = re.search(r"(?:MÃE|MAE)\s*:\s*(.+)", linha_limpa_bloco, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["mae"] = m.group(1).strip()
                        else:
                            for j in range(idx + 1, min(idx + 3, len(bloco))):
                                if bloco[j].strip() and not re.search(r":", bloco[j]):
                                    genealogia["mae"] = bloco[j].strip()
                                    break
                    
                    # AVÔ PATERNO
                    if re.search(r"\bAVÔ\s+PATERNO\s*:|\bAVO\s+PATERNO\s*:", linha_limpa_bloco, re.IGNORECASE):
                        m = re.search(r"(?:AVÔ|AVO)\s+PATERNO\s*:\s*(.+)", linha_limpa_bloco, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_paterno"] = m.group(1).strip()
                        else:
                            for j in range(idx + 1, min(idx + 3, len(bloco))):
                                if bloco[j].strip() and not re.search(r":", bloco[j]):
                                    genealogia["avo_paterno"] = bloco[j].strip()
                                    break
                    
                    # AVÓ PATERNA
                    if re.search(r"\bAVÓ\s+PATERNA\s*:|\bAVO\s+PATERNA\s*:", linha_limpa_bloco, re.IGNORECASE):
                        m = re.search(r"(?:AVÓ|AVO)\s+PATERNA\s*:\s*(.+)", linha_limpa_bloco, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_paterna"] = m.group(1).strip()
                        else:
                            for j in range(idx + 1, min(idx + 3, len(bloco))):
                                if bloco[j].strip() and not re.search(r":", bloco[j]):
                                    genealogia["avo_paterna"] = bloco[j].strip()
                                    break
                    
                    # AVÔ MATERNO
                    if re.search(r"\bAVÔ\s+MATERNO\s*:|\bAVO\s+MATERNO\s*:", linha_limpa_bloco, re.IGNORECASE):
                        m = re.search(r"(?:AVÔ|AVO)\s+MATERNO\s*:\s*(.+)", linha_limpa_bloco, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_materno"] = m.group(1).strip()
                        else:
                            for j in range(idx + 1, min(idx + 3, len(bloco))):
                                if bloco[j].strip() and not re.search(r":", bloco[j]):
                                    genealogia["avo_materno"] = bloco[j].strip()
                                    break
                    
                    # AVÓ MATERNA
                    if re.search(r"\bAVÓ\s+MATERNA\s*:|\bAVO\s+MATERNA\s*:", linha_limpa_bloco, re.IGNORECASE):
                        m = re.search(r"(?:AVÓ|AVO)\s+MATERNA\s*:\s*(.+)", linha_limpa_bloco, re.IGNORECASE)
                        if m and m.group(1).strip():
                            genealogia["avo_materna"] = m.group(1).strip()
                        else:
                            for j in range(idx + 1, min(idx + 3, len(bloco))):
                                if bloco[j].strip() and not re.search(r":", bloco[j]):
                                    genealogia["avo_materna"] = bloco[j].strip()
                                    break
                    
                    # Informações de reprodução
                    if "inseminada" in linha_lower:
                        m_insem = re.search(r"inseminada\s+(?:do|de)\s+([^|]+)", linha_limpa_bloco, re.IGNORECASE)
                        if m_insem:
                            genealogia["info_reproducao"] = f"Inseminada do {m_insem.group(1).strip()}"
                    
                    if "prenhe" in linha_lower or "prenha" in linha_lower:
                        m_prenhe = re.search(r"prenhe\s+(?:do|de)\s+([^|]+?)(?:\s*\.\s*prev\.?\s*de\s*parto:?\s*([^|]+))?", linha_limpa_bloco, re.IGNORECASE)
                        if m_prenhe:
                            genealogia["info_reproducao"] = f"Prenhe do {m_prenhe.group(1).strip()}"
                            if m_prenhe.group(2):
                                genealogia["info_reproducao"] += f" - Prev. de parto: {m_prenhe.group(2).strip()}"
                
                break
    
    return genealogia

# ==================== GATILHOS ====================
def gerar_gatilhos(dados_lote, genealogia=None):
    gatilhos = []
    
    if not dados_lote:
        return [
            "ANIMAL SELECIONADO: Qualidade superior para seu plantel!",
            "DOCUMENTAÇÃO: Registro em dia, procedência garantida!",
            "OPORTUNIDADE: Preço especial para esse lote!"
        ]
    
    categoria = dados_lote.get("categoria", "").lower()
    produto = dados_lote.get("produto", "").lower()
    raca = dados_lote.get("raca", "").lower()
    
    if dados_lote.get("porcentagem_venda"):
        gatilhos.append(f"VENDA DE {dados_lote['porcentagem_venda']}: Oportunidade de investimento!")
    
    if dados_lote.get("nome_animal"):
        gatilhos.append(f"ANIMAL: {dados_lote['nome_animal']} - Destaque da pista!")
    
    if dados_lote.get("info_reproducao"):
        gatilhos.append(f"REPRODUÇÃO: {dados_lote['info_reproducao']}")
    elif genealogia and genealogia.get("info_reproducao"):
        gatilhos.append(f"REPRODUÇÃO: {genealogia['info_reproducao']}")
    
    if "touro" in categoria or "touro" in produto:
        gatilhos.extend([
            "TOURO MELHORADOR: Genética superior para revolucionar seu rebanho!",
            "GANHO DE PESO: Bezerros pesados e precoces na desmama!"
        ])
    
    if "vaca" in categoria or "matriz" in produto:
        gatilhos.extend([
            "MATRIZ: Habilidade materna comprovada!",
            "PRODUÇÃO: Excelente produtividade!"
        ])
    
    if "novilha" in categoria:
        gatilhos.extend([
            "NOVILHA: Futuro da pecuária, genética promissora!",
            "PRECOCIDADE: Pronta para reprodução!"
        ])
    
    if "bezerra" in categoria or "bezerro" in categoria:
        gatilhos.extend([
            "BEZERRA: Genética de elite, futuro garantido!",
            "INVESTIMENTO: Base para um rebanho superior!"
        ])
    
    if "nelore" in raca:
        gatilhos.append("NELORE: Raça que domina o mercado brasileiro!")
    
    if "angus" in raca:
        gatilhos.append("ANGUS: Carne premium, maciez garantida!")
    
    if genealogia:
        if genealogia.get("pai") and genealogia.get("mae"):
            gatilhos.append(f"PEDIGREE: {genealogia['pai']} x {genealogia['mae']} - Cruzamento de elite!")
        elif genealogia.get("pai"):
            gatilhos.append(f"FILHO DE: {genealogia['pai']} - Linhagem consagrada!")
    
    gatilhos.extend([
        "QUALIDADE: Animal selecionado a dedo!",
        "PROCEDÊNCIA: Origem garantida!",
        "OPORTUNIDADE: Preço imperdível!"
    ])
    
    if dados_lote.get("peso"):
        gatilhos.append(f"PESO: {dados_lote['peso']} de pura produtividade!")
    
    if dados_lote.get("idade"):
        gatilhos.append(f"IDADE: {dados_lote['idade']} - Fase perfeita!")
    
    return gatilhos[:8]

# ==================== INTERFACE PRINCIPAL ====================
st.title("PAINEL DO LEILOEIRO PRO")

# Sidebar
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
else:
    texto_cat = []

# Extrair dados
sequencia_oe, mapa_oe = extrair_dados_oe(texto_oe_tuple)

# Debug
if hasattr(st.session_state, 'mostrar_debug') and st.session_state.mostrar_debug:
    with st.expander("DEBUG", expanded=True):
        st.write(f"Total de páginas O.E.: {len(texto_oe)}")
        st.write(f"Total de lotes extraídos: {len(sequencia_oe)}")
        
        if sequencia_oe:
            st.write(f"Primeiros 20 lotes: {sequencia_oe[:20]}")
        
        if texto_oe:
            st.write("Primeiras linhas da O.E.:")
            for i, pagina in enumerate(texto_oe[:2]):
                linhas = pagina.split('\n')
                st.markdown(f"**Página {i+1}:**")
                for linha in linhas[:15]:
                    if linha.strip():
                        st.code(linha)

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

# Estado da sessão
if 'lote_idx' not in st.session_state:
    st.session_state.lote_idx = 0

if not lista_lotes:
    st.warning("Carregue a Ordem de Entrada (PDF) para começar!")
    st.stop()

if st.session_state.lote_idx >= len(lista_lotes):
    st.session_state.lote_idx = 0

# ==================== NAVEGAÇÃO ====================
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

# ==================== PAINEL PRINCIPAL ====================
lote_texto = f"LOTE {num_lote}"
posicao_texto = dados_lote.get("posicao", f"{st.session_state.lote_idx + 1}º")
st.markdown(f'<div class="lote-destaque">{lote_texto}<br><span style="font-size: 24px;">{posicao_texto} A ENTRAR</span></div>', unsafe_allow_html=True)

# Porcentagem de venda
if dados_lote.get("porcentagem_venda"):
    pct_texto = f"VENDA DE {dados_lote['porcentagem_venda']} DO ANIMAL"
    st.markdown(f'<div class="porcentagem-box">{pct_texto}</div>', unsafe_allow_html=True)

# Nome do animal
if dados_lote.get("nome_animal"):
    nome_texto = dados_lote["nome_animal"]
    st.markdown(f'<div class="nome-animal-box">🐂 {nome_texto}</div>', unsafe_allow_html=True)

# Informações de reprodução
if dados_lote.get("info_reproducao"):
    repro_texto = dados_lote["info_reproducao"]
    if dados_lote.get("tipo_reproducao") == "prenhez":
        st.markdown(f'<div class="prenhez-box">{repro_texto}</div>', unsafe_allow_html=True)
    elif dados_lote.get("tipo_reproducao") == "inseminacao":
        st.markdown(f'<div class="inseminacao-box">{repro_texto}</div>', unsafe_allow_html=True)
elif genealogia.get("info_reproducao"):
    repro_texto = genealogia["info_reproducao"]
    if "prenhe" in repro_texto.lower():
        st.markdown(f'<div class="prenhez-box">{repro_texto}</div>', unsafe_allow_html=True)
    elif "inseminada" in repro_texto.lower():
        st.markdown(f'<div class="inseminacao-box">{repro_texto}</div>', unsafe_allow_html=True)

if dados_lote:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### DADOS DO ANIMAL")
        cat_texto = dados_lote.get("categoria", "-")
        raca_texto = dados_lote.get("raca", "-")
        st.markdown(f'<div class="animal-info"><strong>CATEGORIA:</strong><br>{cat_texto}<br><br><strong>RAÇA:</strong><br>{raca_texto}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### CARACTERÍSTICAS")
        peso_texto = dados_lote.get("peso", "-")
        idade_texto = dados_lote.get("idade", "-")
        st.markdown(f'<div class="animal-info"><strong>PESO:</strong><br>{peso_texto}<br><br><strong>IDADE:</strong><br>{idade_texto}</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("### QUANTIDADE")
        qtd_texto = dados_lote.get("qtd", "-")
        vend_texto = dados_lote.get("vendedor", "-")
        st.markdown(f'<div class="animal-info"><strong>QTD:</strong><br>{qtd_texto}<br><br><strong>VENDEDOR:</strong><br>{vend_texto}</div>', unsafe_allow_html=True)
    
    if dados_lote.get("produto"):
        prod_texto = dados_lote["produto"]
        st.markdown("### PRODUTO/ANIMAL")
        st.markdown(f'<div class="animal-info">{prod_texto}</div>', unsafe_allow_html=True)

# Genealogia
if genealogia:
    st.markdown("### GENEALOGIA COMPLETA")
    
    col_pai, col_mae = st.columns(2)
    
    with col_pai:
        if genealogia.get("pai"):
            pai_texto = genealogia["pai"]
            st.markdown(f'<div class="pai-box"><strong>PAI:</strong><br>{pai_texto}</div>', unsafe_allow_html=True)
        
        col_avo_p, col_avo_p2 = st.columns(2)
        with col_avo_p:
            if genealogia.get("avo_paterno"):
                avo_p_texto = genealogia["avo_paterno"]
                st.markdown(f'<div class="avo-paterno-box"><strong>AVÔ PATERNO:</strong><br>{avo_p_texto}</div>', unsafe_allow_html=True)
        with col_avo_p2:
            if genealogia.get("avo_paterna"):
                avo_p2_texto = genealogia["avo_paterna"]
                st.markdown(f'<div class="avo-paterno-box"><strong>AVÓ PATERNA:</strong><br>{avo_p2_texto}</div>', unsafe_allow_html=True)
    
    with col_mae:
        if genealogia.get("mae"):
            mae_texto = genealogia["mae"]
            st.markdown(f'<div class="mae-box"><strong>MÃE:</strong><br>{mae_texto}</div>', unsafe_allow_html=True)
        
        col_avo_m, col_avo_m2 = st.columns(2)
        with col_avo_m:
            if genealogia.get("avo_materno"):
                avo_m_texto = genealogia["avo_materno"]
                st.markdown(f'<div class="avo-materno-box"><strong>AVÔ MATERNO:</strong><br>{avo_m_texto}</div>', unsafe_allow_html=True)
        with col_avo_m2:
            if genealogia.get("avo_materna"):
                avo_m2_texto = genealogia["avo_materna"]
                st.markdown(f'<div
