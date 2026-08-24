import streamlit as st
import pdfplumber
import re
from io import BytesIO
import requests
import json
import time
from datetime import datetime, timedelta

st.set_page_config(
    page_title="PAINEL DO LEILOEIRO PRO",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CONFIGURAÇÃO DA API DE IA ====================
# Você pode usar OpenAI, Google Gemini, ou qualquer outra API
API_KEY = st.secrets.get("OPENAI_API_KEY", "")  # Coloque sua API key no secrets.toml
API_URL = "https://api.openai.com/v1/chat/completions"  # Ou outra API

# ==================== SISTEMA DE CACHE ====================
@st.cache_data(ttl=3600)  # Cache por 1 hora
def buscar_premios_ia(nome_animal, pais, raca):
    """
    Busca prêmios e conquistas da linhagem usando IA
    Usa cache para não repetir buscas
    """
    if not API_KEY:
        return []
    
    try:
        # Monta o prompt para a IA
        prompt = f"""
        Busque informações sobre prêmios e conquistas na pecuária para:
        
        Animal: {nome_animal}
        Pais: {pais}
        Raça: {raca}
        
        Retorne uma lista de prêmios relevantes da linhagem, como:
        - Campeonatos
        - Exposições
        - Prêmios de genética
        - Recordes
        
        Formato: Lista simples com bullets
        """
        
        # Chama a API
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Você é um especialista em pecuária e leilões."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            resultado = response.json()
            texto_resposta = resultado["choices"][0]["message"]["content"]
            
            # Converte para lista
            premios = [linha.strip() for linha in texto_resposta.split('\n') if linha.strip()]
            return premios
        else:
            return []
            
    except Exception as e:
        st.warning(f"Erro ao buscar prêmios: {str(e)}")
        return []

# ==================== CACHE LOCAL EM SESSION STATE ====================
if 'cache_premios' not in st.session_state:
    st.session_state.cache_premios = {}

def buscar_premios_com_cache(nome_animal, pais, raca):
    """
    Busca prêmios com cache em session_state
    """
    # Cria chave única para o cache
    chave_cache = f"{nome_animal}_{pais}_{raca}"
    
    # Verifica se já está em cache
    if chave_cache in st.session_state.cache_premios:
        return st.session_state.cache_premios[chave_cache]
    
    # Busca da API
    premios = buscar_premios_ia(nome_animal, pais, raca)
    
    # Salva no cache
    st.session_state.cache_premios[chave_cache] = premios
    
    return premios

# ==================== CSS PARA TABLET ====================
st.markdown("""
<style>
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
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        border: 3px solid #FF0000;
        box-shadow: 0 0 20px rgba(255,0,0,0.5);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .genealogia-box {
        background: rgba(255,255,255,0.05);
        border: 2px solid #4CAF50;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
    }
    .pai-box {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .mae-box {
        background: linear-gradient(135deg, #E91E63 0%, #C2185B 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
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
    .premios-box {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border: 2px solid #FFD700;
    }
    .premio-item {
        background: rgba(255,255,255,0.9);
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        color: #333;
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
                        "prenhez": "",
                        "nome_animal": "",
                        "linha_completa": linha_limpa
                    }
                    
                    if len(parts) >= 1:
                        dados["qtd"] = parts[0]
                    if len(parts) >= 2:
                        dados["idade"] = parts[1]
                    if len(parts) >= 3:
                        dados["peso"] = parts[2]
                    if len(parts) >= 4:
                        dados["categoria"] = parts[3]
                    
                    # Detecta prenhez
                    linha_lower = linha_limpa.lower()
                    if any(k in linha_lower for k in ["prenhe", "prenha", "prenhez", "gestante"]):
                        dados["prenhez"] = "PRENHE"
                    
                    # Produto e nome do animal
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
                        
                        # Tenta extrair nome do animal (geralmente em maiúsculas)
                        for part in parts:
                            if re.match(r"^[A-ZÀ-Ú]{3,}$", part):
                                dados["nome_animal"] = part
                                break
                    
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
        "prenhez": ""
    }
    
    if not texto_cat:
        return genealogia
    
    for pagina in texto_cat:
        linhas = pagina.split('\n')
        
        for i, linha in enumerate(linhas):
            linha_limpa = linha.strip()
            
            if re.search(rf"\b{int(num_lote)}\b", linha_limpa):
                inicio = max(0, i - 10)
                fim = min(len(linhas), i + 30)
                bloco = linhas[inicio:fim]
                
                nomes_maiusculos = []
                for texto in bloco:
                    texto_limpo = texto.strip()
                    if re.match(r"^[A-ZÀ-Ú\s]{4,}$", texto_limpo):
                        nomes_maiusculos.append(texto_limpo)
                
                for idx, linha_bloco in enumerate(bloco):
                    linha_lower = linha_bloco.lower()
                    
                    if any(k in linha_lower for k in ["pai:", "father", "sire", "genitor"]):
                        for j in range(idx, min(idx + 3, len(bloco))):
                            if re.match(r"^[A-ZÀ-Ú\s]{4,}$", bloco[j].strip()):
                                genealogia["pai"] = bloco[j].strip()
                                break
                    
                    if any(k in linha_lower for k in ["mãe:", "mae:", "mother", "dam", "genitora"]):
                        for j in range(idx, min(idx + 3, len(bloco))):
                            if re.match(r"^[A-ZÀ-Ú\s]{4,}$", bloco[j].strip()):
                                genealogia["mae"] = bloco[j].strip()
                                break
                
                if not genealogia["pai"] and len(nomes_maiusculos) >= 2:
                    genealogia["pai"] = nomes_maiusculos[0]
                    genealogia["mae"] = nomes_maiusculos[1]
                
                if len(nomes_maiusculos) >= 4:
                    genealogia["avo_paterno"] = nomes_maiusculos[2]
                    genealogia["avo_paterna"] = nomes_maiusculos[3]
                
                if len(nomes_maiusculos) >= 6:
                    genealogia["avo_materno"] = nomes_maiusculos[4]
                    genealogia["avo_materna"] = nomes_maiusculos[5]
                
                texto_completo = " ".join(bloco).lower()
                if any(k in texto_completo for k in ["prenhe", "prenha", "gestante"]):
                    genealogia["prenhez"] = "PRENHE"
                
                break
    
    return genealogia

# ==================== GATILHOS ====================
def gerar_gatilhos(dados_lote, genealogia=None, premios=None):
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
    
    # Gatilhos para prenhez
    if dados_lote.get("prenhez") or (genealogia and genealogia.get("prenhez")):
        gatilhos.append("PRENHEZ CONFIRMADA: Garantia de produção futura!")
    
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
    
    # Gatilhos baseados na genealogia
    if genealogia:
        if genealogia.get("pai") and genealogia.get("mae"):
            gatilhos.append(f"PEDIGREE: {genealogia['pai']} x {genealogia['mae']} - Cruzamento de elite!")
        elif genealogia.get("pai"):
            gatilhos.append(f"FILHO DE: {genealogia['pai']} - Linhagem consagrada!")
    
    # Gatilhos baseados em prêmios
    if premios:
        gatilhos.append("PREMIADO: Linhagem com histórico de campeonatos!")
    
    gatilhos.extend([
        "QUALIDADE: Animal selecionado a dedo!",
        "PROCEDÊNCIA: Origem garantida!",
        "OPORTUNIDADE: Preço imperdível!"
    ])
    
    if dados_lote.get("peso"):
        gatilhos.append(f"PESO: {dados_lote['peso']} de pura produtividade!")
    
    if dados_lote.get("idade"):
        gatilhos.append(f"IDADE: {dados_lote['idade']} - Fase perfeita!")
    
    return gatilhos[:7]

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
    
    # Configuração da API
    st.markdown("---")
    st.header("Configurações de IA")
    
    usar_ia = st.checkbox("Buscar prêmios com IA", value=False)
    
    if usar_ia and not API_KEY:
        st.warning("Configure a API key no secrets.toml")
        api_key_manual = st.text_input("Ou digite a API key:", type="password")
        if api_key_manual:
            API_KEY = api_key_manual
    
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
st.markdown(f'<div class="ordem-indicador">{ordem_atual} | Lote {st.session_state.lote_idx + 1} de {len(lista_lotes)}</div>', unsafe_allow_html=True)

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

# Extrai genealogia
genealogia = extrair_genealogia(texto_cat, num_lote) if texto_cat else {}

# Busca prêmios com IA (se habilitado)
premios = []
if usar_ia and dados_lote:
    nome_animal = dados_lote.get("nome_animal", "")
    pais = f"{genealogia.get('pai', '')} {genealogia.get('mae', '')}"
    raca = dados_lote.get("raca", "")
    
    if nome_animal or pais.strip():
        with st.spinner("Buscando prêmios da linhagem..."):
            premios = buscar_premios_com_cache(nome_animal, pais, raca)

# ==================== PAINEL PRINCIPAL ====================
st.markdown(f'<div class="lote-destaque">LOTE {num_lote}<br><span style="font-size: 24px;">{dados_lote.get("posicao", f"{st.session_state.lote_idx + 1}º")} A ENTRAR</span></div>', unsafe_allow_html=True)

# Destaque para prenhez
if dados_lote.get("prenhez") or genealogia.get("prenhez"):
    st.markdown(f'<div class="prenhez-box">🐄 PRENHEZ CONFIRMADA! 🐄</div>', unsafe_allow_html=True)

if dados_lote:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### DADOS DO ANIMAL")
        st.markdown(f'<div class="animal-info"><strong>CATEGORIA:</strong><br>{dados_lote.get("categoria", "-")}<br><br><strong>RAÇA:</strong><br>{dados_lote.get("raca", "-")}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### CARACTERÍSTICAS")
        st.markdown(f'<div class="animal-info"><strong>PESO:</strong><br>{dados_lote.get("peso", "-")}<br><br><strong>IDADE:</strong><br>{dados_lote.get("idade", "-")}</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("### QUANTIDADE")
        st.markdown(f'<div class="animal-info"><strong>QTD:</strong><br>{dados_lote.get("qtd", "-")}<br><br><strong>VENDEDOR:</strong><br>{dados_lote.get("vendedor", "-")}</div>', unsafe_allow_html=True)
    
    if dados_lote.get("produto"):
        st.markdown("### PRODUTO/ANIMAL")
        st.markdown(f'<div class="animal-info">{dados_lote["produto"]}</div>', unsafe_allow_html=True)

# Genealogia
if genealogia:
    st.markdown("### 📋 GENEALOGIA COMPLETA")
    
    col_pai, col_mae = st.columns(2)
    
    with col_pai:
        if genealogia.get("pai"):
            st.markdown(f'<div class="pai-box"><strong>PAI:</strong><br>{genealogia["pai"]}</div>', unsafe_allow_html=True)
        
        col_avo_p, col_avo_p2 = st.columns(2)
        with col_avo_p:
            if genealogia.get("avo_paterno"):
                st.markdown(f'<div class="avo-paterno-box"><strong>AVÔ PATERNO:</strong><br>{genealogia["avo_paterno"]}</div>', unsafe_allow_html=True)
        with col_avo_p2:
            if genealogia.get("avo_paterna"):
                st.markdown(f'<div class="avo-paterno-box"><strong>AVÓ PATERNA:</strong><br>{genealogia["avo_paterna"]}</div>', unsafe_allow_html=True)
    
    with col_mae:
        if genealogia.get("mae"):
            st.markdown(f'<div class="mae-box"><strong>MÃE:</strong><br>{genealogia["mae"]}</div>', unsafe_allow_html=True)
        
        col_avo_m, col_avo_m2 = st.columns(2)
        with col_avo_m:
            if genealogia.get("avo_materno"):
                st.markdown(f'<div class="avo-materno-box"><strong>AVÔ MATERNO:</strong><br>{genealogia["avo_materno"]}</div>', unsafe_allow_html=True)
        with col_avo_m2:
            if genealogia.get("avo_materna"):
                st.markdown(f'<div class="avo-materno-box"><strong>AVÓ MATERNA:</strong><br>{genealogia["avo_materna"]}</div>', unsafe_allow_html=True)

# Prêmios da IA
if premios:
    st.markdown("### 🏆 PRÊMIOS DA LINHAGEM")
    st.markdown('<div class="premios-box">', unsafe_allow_html=True)
    for premio in premios:
        if premio.strip():
            st.markdown(f'<div class="premio-item">{premio}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Linha completa
if dados_lote:
    with st.expander("Ver linha completa da O.E."):
        st.code(dados_lote.get("linha_completa", "-"))

# Gatilhos
st.markdown("### GATILHOS PARA CANTAR")
gatilhos = gerar_gatilhos(dados_lote, genealogia, premios)

for gatilho in gatilhos:
    st.markdown(f'<div class="gatilho-card">{gatilho}</div>', unsafe_allow_html=True)

# Rodapé
st.markdown("---")
st.markdown(f"**Total de lotes: {len(lista_lotes)}**")
