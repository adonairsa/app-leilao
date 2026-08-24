import streamlit as st
import pdfplumber
import re
from io import BytesIO

st.set_page_config(
    page_title="PAINEL DO LEILOEIRO PRO",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    .pedigree-box {
        background: rgba(255,255,255,0.08);
        border: 2px solid #FF9800;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        font-size: 18px;
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
    
    for pagina_idx, pagina in enumerate(texto_oe):
        linhas = pagina.split('\n')
        
        for linha_idx, linha in enumerate(linhas):
            linha_limpa = linha.strip()
            
            if not linha_limpa:
                continue
            
            # Ignora linhas de cabeçalho
            if re.search(r"QTD\s+IDADE\s+PESO\s+CATEGORIA\s+PRODUTO", linha_limpa, re.IGNORECASE):
                continue
            
            if re.search(r"O\.E\.\s*LT", linha_limpa, re.IGNORECASE):
                continue
            
            if re.search(r"\d{2}/\d{2}/\d{4}", linha_limpa):
                continue
            
            # PADRÃO PRINCIPAL: Começa com posição (1º, 2º, etc.)
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
                        "linha_completa": linha_limpa
                    }
                    
                    # Extrai campos na ordem
                    if len(parts) >= 1:
                        dados["qtd"] = parts[0]
                    if len(parts) >= 2:
                        dados["idade"] = parts[1]
                    if len(parts) >= 3:
                        dados["peso"] = parts[2]
                    if len(parts) >= 4:
                        dados["categoria"] = parts[3]
                    
                    # Produto: junta as partes do meio
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

# ==================== EXTRAÇÃO DO CATÁLOGO ====================
@st.cache_data
def extrair_catalogo(texto_cat_tuple):
    texto_cat = list(texto_cat_tuple)
    catalogo_info = {}
    
    if not texto_cat:
        return catalogo_info
    
    for pagina_idx, pagina in enumerate(texto_cat):
        linhas = pagina.split('\n')
        
        for linha_idx, linha in enumerate(linhas):
            linha_limpa = linha.strip()
            
            if not linha_limpa:
                continue
            
            m_lote = re.search(r"\b(\d{1,3})\b", linha_limpa)
            
            if m_lote and 1 <= int(m_lote.group(1)) <= 500:
                num_lote = f"{int(m_lote.group(1)):02d}"
                
                inicio = max(0, linha_idx - 5)
                fim = min(len(linhas), linha_idx + 20)
                bloco = [l.strip() for l in linhas[inicio:fim] if l.strip()]
                
                if bloco:
                    nomes = []
                    for texto in bloco:
                        if re.match(r"^[A-ZÀ-Ú\s]+$", texto) and len(texto) > 3:
                            nomes.append(texto)
                    
                    catalogo_info[num_lote] = {
                        "bloco_completo": bloco,
                        "nomes_destaque": nomes,
                        "pagina": pagina_idx + 1,
                        "linha": linha_idx + 1
                    }
    
    return catalogo_info

# ==================== GATILHOS ====================
def gerar_gatilhos(dados_lote, info_catalogo=None):
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
    
    if info_catalogo and info_catalogo.get("nomes_destaque"):
        nomes = info_catalogo["nomes_destaque"]
        if len(nomes) >= 2:
            gatilhos.append(f"PEDIGREE: {nomes[0]} x {nomes[1]} - Cruzamento de elite!")
    
    gatilhos.extend([
        "QUALIDADE: Animal selecionado a dedo!",
        "PROCEDÊNCIA: Origem garantida!",
        "OPORTUNIDADE: Preço imperdível!"
    ])
    
    if dados_lote.get("peso"):
        gatilhos.append(f"PESO: {dados_lote['peso']} de pura produtividade!")
    
    if dados_lote.get("idade"):
        gatilhos.append(f"IDADE: {dados_lote['idade']} - Fase perfeita!")
    
    return gatilhos[:6]

# ==================== INTERFACE PRINCIPAL ====================
st.title("PAINEL DO LEILOEIRO PRO")

# Sidebar
with st.sidebar:
    st.header("Arquivos")
    
    file_oe = st.file_uploader(
        "Ordem de Entrada (PDF)",
        type="pdf",
        key="oe"
    )
    
    if file_oe:
        tamanho_mb = len(file_oe.getvalue()) / (1024 * 1024)
        st.success(f"O.E. carregada! ({tamanho_mb:.1f} MB)")
    
    st.markdown("---")
    st.markdown("**Catálogo (opcional):**")
    
    file_cat = st.file_uploader(
        "Catálogo do Leilão (PDF)",
        type="pdf",
        key="cat"
    )
    
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
        texto_cat_tuple = tuple(texto_cat) if texto_cat else tuple()
else:
    texto_cat = []
    texto_cat_tuple = tuple()

# Extrair dados
sequencia_oe, mapa_oe = extrair_dados_oe(texto_oe_tuple)
catalogo_info = extrair_catalogo(texto_cat_tuple)

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

# Verificar se há lotes
if not lista_lotes:
    st.warning("Carregue a Ordem de Entrada (PDF) para começar!")
    st.info("Clique em VER DEBUG na sidebar para verificar o formato do PDF")
    st.stop()

# Garantir índice válido
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
info_cat_lote = catalogo_info.get(num_lote, {})

# ==================== PAINEL PRINCIPAL ====================
st.markdown(f'<div class="lote-destaque">LOTE {num_lote}<br><span style="font-size: 24px;">{dados_lote.get("posicao", f"{st.session_state.lote_idx + 1}º")} A ENTRAR</span></div>', unsafe_allow_html=True)

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
    
    if info_cat_lote:
        st.markdown("### PEDIGREE DO CATÁLOGO")
        
        if info_cat_lote.get("nomes_destaque"):
            st.markdown("**LINHAGEM:**")
            for nome in info_cat_lote["nomes_destaque"][:6]:
                st.markdown(f'<div class="pedigree-box">{nome}</div>', unsafe_allow_html=True)
        
        if info_cat_lote.get("bloco_completo"):
            with st.expander("Ver pedigree completo"):
                for texto in info_cat_lote["bloco_completo"]:
                    st.write(f"• {texto}")
    
    with st.expander("Ver linha completa da O.E."):
        st.code(dados_lote.get("linha_completa", "-"))
    
    st.markdown("### GATILHOS PARA CANTAR")
    gatilhos = gerar_gatilhos(dados_lote, info_cat_lote)
    
    for gatilho in gatilhos:
        st.markdown(f'<div class="gatilho-card">{gatilho}</div>', unsafe_allow_html=True)

else:
    st.warning(f"Lote {num_lote} não encontrado na extração")
    st.info("Clique em VER DEBUG na sidebar para verificar o formato do PDF")

# Rodapé
st.markdown("---")
st.markdown(f"**Total de lotes: {len(lista_lotes)}**")
