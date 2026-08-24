import streamlit as st
import pdfplumber
import re
from io import BytesIO

st.set_page_config(
    page_title="🎤 LEILOEIRO PRO",
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
    .info-card {
        background: rgba(255,255,255,0.08);
        border: 2px solid #4CAF50;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        font-size: 18px;
    }
    .info-destaque {
        background: #2196F3;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-size: 20px;
        font-weight: bold;
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
    .upload-info {
        background: #FF9800;
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: bold;
        font-size: 16px;
    }
    .animal-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== PROCESSAMENTO DE PDF ====================
@st.cache_data(ttl=7200, show_spinner=False)
def processar_pdf_grande(file_bytes, tipo_arquivo):
    """Processa PDFs e extrai texto"""
    paginas = []
    
    if not file_bytes:
        return paginas
    
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            total_paginas = len(pdf.pages)
            
            # Para catálogo, processa primeiras 100 páginas
            if tipo_arquivo == 'cat':
                paginas_processar = min(total_paginas, 100)
            else:
                paginas_processar = total_paginas
            
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, page in enumerate(pdf.pages[:paginas_processar]):
                progress = (i + 1) / paginas_processar
                progress_bar.progress(progress)
                status_text.text(f"📄 Lendo página {i+1} de {paginas_processar}...")
                
                # Extrai texto
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

# ==================== EXTRAÇÃO DE DADOS DO GADO ====================
@st.cache_data
def extrair_dados_gado(texto_oe_tuple):
    """
    Extrai informações detalhadas do gado da Ordem de Entrada
    """
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
            
            # ============ PADRÃO 1: Com pipes (|) ============
            if '|' in linha_limpa:
                parts = [p.strip() for p in linha_limpa.split('|') if p.strip()]
                
                if len(parts) >= 2:
                    lote_encontrado = None
                    
                    # Procura "LT" ou "LOTE"
                    for i, part in enumerate(parts):
                        m = re.search(r"\b(LT|LOTE)\s*[.:]?\s*(\d{1,4})", part, re.IGNORECASE)
                        if m:
                            lote_encontrado = m.group(2)
                            break
                    
                    # Se não achou, pega primeiro número
                    if not lote_encontrado:
                        for i, part in enumerate(parts):
                            m = re.search(r"\b(\d{1,3})\b", part)
                            if m and 1 <= int(m.group(1)) <= 500:
                                lote_encontrado = m.group(1)
                                break
                    
                    if lote_encontrado and 1 <= int(lote_encontrado) <= 500:
                        lt_num = f"{int(lote_encontrado):02d}"
                        
                        if lt_num not in sequencia:
                            sequencia.append(lt_num)
                        
                        # Inicializa dicionário de dados
                        dados = {
                            "lote": lt_num,
                            "posicao": f"{len(sequencia)}º",
                            "categoria": "",
                            "raca": "",
                            "sexo": "",
                            "idade": "",
                            "peso": "",
                            "registro": "",
                            "pai": "",
                            "mae": "",
                            "vendedor": "",
                            "descricao_completa": " | ".join(parts)
                        }
                        
                        # Analisa cada parte para extrair informações
                        for idx, part in enumerate(parts):
                            part_lower = part.lower()
                            
                            # Categoria/Animal
                            if any(k in part_lower for k in ["touro", "vaca", "matriz", "novilha", "bezerro", "garrote", "boi"]):
                                dados["categoria"] = part
                            
                            # Raça
                            elif any(k in part_lower for k in ["nelore", "angus", "girolando", "holandês", "hereford", "braford", "simental"]):
                                dados["raca"] = part
                            
                            # Sexo
                            elif any(k in part_lower for k in ["macho", "fêmea", "femea"]):
                                dados["sexo"] = part
                            
                            # Peso (procura por kg ou @)
                            elif "kg" in part_lower or "@" in part:
                                dados["peso"] = part
                            
                            # Idade
                            elif any(k in part_lower for k in ["ano", "meses", "mes", "dia"]):
                                dados["idade"] = part
                            
                            # Registro
                            elif "reg" in part_lower or "rg" in part_lower:
                                dados["registro"] = part
                            
                            # Vendedor (geralmente última coluna)
                            elif idx == len(parts) - 1:
                                dados["vendedor"] = part
                        
                        dados_por_lote[lt_num] = dados
            
            # ============ PADRÃO 2: "LT XX" ou "LOTE XX" ============
            elif re.search(r"\b(LT|LOTE)\s*[.:]?\s*(\d{1,4})", linha_limpa, re.IGNORECASE):
                m = re.search(r"\b(LT|LOTE)\s*[.:]?\s*(\d{1,4})", linha_limpa, re.IGNORECASE)
                numero = int(m.group(2))
                
                if 1 <= numero <= 500:
                    lt_num = f"{numero:02d}"
                    
                    if lt_num not in sequencia:
                        sequencia.append(lt_num)
                    
                    descricao = linha_limpa[m.end():].strip()
                    
                    dados_por_lote[lt_num] = {
                        "lote": lt_num,
                        "posicao": f"{len(sequencia)}º",
                        "categoria": "",
                        "raca": "",
                        "sexo": "",
                        "idade": "",
                        "peso": "",
                        "registro": "",
                        "pai": "",
                        "mae": "",
                        "vendedor": "",
                        "descricao_completa": descricao
                    }
            
            # ============ PADRÃO 3: Número no início ============
            elif re.match(r"^\s*(\d{1,3})\s*[-.)]?\s*", linha_limpa):
                m = re.match(r"^\s*(\d{1,3})\s*[-.)]?\s*", linha_limpa)
                numero = int(m.group(1))
                
                if 1 <= numero <= 500:
                    lt_num = f"{numero:02d}"
                    
                    if lt_num not in sequencia:
                        sequencia.append(lt_num)
                    
                    descricao = linha_limpa[m.end():].strip()
                    
                    dados_por_lote[lt_num] = {
                        "lote": lt_num,
                        "posicao": f"{len(sequencia)}º",
                        "categoria": "",
                        "raca": "",
                        "sexo": "",
                        "idade": "",
                        "peso": "",
                        "registro": "",
                        "pai": "",
                        "mae": "",
                        "vendedor": "",
                        "descricao_completa": descricao
                    }
    
    return sequencia, dados_por_lote

# ==================== GATILHOS PARA CANTAR ====================
def gerar_gatilhos(dados_lote):
    """Gera gatilhos baseados nas informações do animal"""
    gatilhos = []
    
    if not dados_lote:
        return [
            "⭐ ANIMAL SELECIONADO: Qualidade superior para seu plantel!",
            "📋 DOCUMENTAÇÃO: Registro em dia, procedência garantida!",
            "🔨 OPORTUNIDADE: Preço especial para esse lote!"
        ]
    
    # Junta todas as informações para análise
    info_completa = " ".join([
        dados_lote.get("categoria", ""),
        dados_lote.get("raca", ""),
        dados_lote.get("sexo", ""),
        dados_lote.get("descricao_completa", "")
    ]).lower()
    
    # Gatilhos específicos
    if "touro" in info_completa:
        gatilhos.extend([
            "🐂 TOURO MELHORADOR: Genética superior para revolucionar seu rebanho!",
            "📈 GANHO DE PESO: Bezerros pesados e precoces na desmama!"
        ])
    
    if "matriz" in info_completa or "vaca" in info_completa:
        gatilhos.extend([
            "👑 MATRIZ: Habilidade materna comprovada!",
            "🥛 PRODUÇÃO: Excelente produtividade!"
        ])
    
    if "nelore" in info_completa:
        gatilhos.append("🏆 NELORE: Raça que domina o mercado brasileiro!")
    
    if "angus" in info_completa:
        gatilhos.append("🥩 ANGUS: Carne premium, maciez garantida!")
    
    # Gatilhos genéricos
    gatilhos.extend([
        "⭐ QUALIDADE: Animal selecionado a dedo!",
        "📋 PROCEDÊNCIA: Origem garantida!",
        "🔨 OPORTUNIDADE: Preço imperdível!"
    ])
    
    # Adiciona informações específicas
    if dados_lote.get("peso"):
        gatilhos.append(f"⚖️ PESO: {dados_lote['peso']} de pura produtividade!")
    
    if dados_lote.get("raca"):
        gatilhos.append(f"🧬 GENÉTICA {dados_lote['raca'].upper()}: Linhagem superior!")
    
    if dados_lote.get("idade"):
        gatilhos.append(f"📅 IDADE: {dados_lote['idade']} - Fase perfeita!")
    
    return gatilhos[:5]

# ==================== INTERFACE PRINCIPAL ====================
st.title("🎤 PAINEL DO LEILOEIRO")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📂 Arquivo")
    
    st.markdown("""
    <div class="upload-info">
        📤 Tamanho máximo: 500MB<br>
        💡 Aceita PDFs grandes
    </div>
    """, unsafe_allow_html=True)
    
    file_oe = st.file_uploader(
        "📋 Ordem de Entrada (PDF)",
        type="pdf",
        key="oe",
        help="Carregue o PDF da Ordem de Entrada"
    )
    
    if file_oe:
        tamanho_mb = len(file_oe.getvalue()) / (1024 * 1024)
        st.success(f"✅ Arquivo carregado! ({tamanho_mb:.1f} MB)")
    
    st.markdown("---")
    st.markdown("**📚 Catálogo (opcional):**")
    file_cat = st.file_uploader(
        "Catálogo do Leilão (PDF)",
        type="pdf",
        key="cat",
        help="Opcional - para complementar informações"
    )
    
    if file_cat:
        tamanho_mb = len(file_cat.getvalue()) / (1024 * 1024)
        st.success(f"✅ Catálogo carregado! ({tamanho_mb:.1f} MB)")
    
    st.markdown("---")
    st.header("⚙️ Ordem dos Lotes")
    
    modo_ordenacao = st.radio(
        "Escolha a ordem:",
        ["🎯 ORDEM DE ENTRADA", "🔢 ORDEM NUMÉRICA"],
        index=0
    )
    
    # Debug
    st.markdown("---")
    if st.button("🔍 VER DEBUG", use_container_width=True):
        st.session_state.mostrar_debug = True
    else:
        st.session_state.mostrar_debug = False

# Processar O.E.
if file_oe:
    with st.spinner("🔄 Lendo Ordem de Entrada..."):
        file_bytes = file_oe.getvalue()
        texto_oe = processar_pdf_grande(file_bytes, 'oe')
        texto_oe_tuple = tuple(texto_oe) if texto_oe else tuple()
else:
    texto_oe = []
    texto_oe_tuple = tuple()

# Processar Catálogo (se existir)
if file_cat:
    with st.spinner("🔄 Lendo Catálogo..."):
        file_bytes = file_cat.getvalue()
        texto_cat = processar_pdf_grande(file_bytes, 'cat')
else:
    texto_cat = []

# Extrair dados
sequencia_oe, mapa_oe = extrair_dados_gado(texto_oe_tuple)

# Mostrar debug
if hasattr(st.session_state, 'mostrar_debug') and st.session_state.mostrar_debug and texto_oe:
    with st.expander("🔍 DEBUG - PRIMEIRAS LINHAS DO PDF", expanded=True):
        st.write(f"**Total de páginas:** {len(texto_oe)}")
        st.write(f"**Total de lotes extraídos:** {len(sequencia_oe)}")
        
        if sequencia_oe:
            st.write(f"**Primeiros 20 lotes:** {sequencia_oe[:20]}")
        
        st.write("**Primeiras 20 linhas do PDF:**")
        for i, pagina in enumerate(texto_oe[:3]):
            linhas = pagina.split('\n')
            st.markdown(f"**Página {i+1}:**")
            for linha in linhas[:20]:
                if linha.strip():
                    st.code(linha, language="text")

# Definir lista de lotes
if sequencia_oe:
    if modo_ordenacao == "🎯 ORDEM DE ENTRADA":
        lista_lotes = sequencia_oe.copy()
        ordem_atual = "🎯 ORDEM DE ENTRADA"
    else:
        lista_lotes = sorted(sequencia_oe, key=lambda x: int(x))
        ordem_atual = "🔢 ORDEM NUMÉRICA"
else:
    lista_lotes = []
    ordem_atual = "⚠️ NENHUM LOTE ENCONTRADO"

# Estado da sessão
if 'lote_idx' not in st.session_state:
    st.session_state.lote_idx = 0

# Verificar se há lotes
if not lista_lotes:
    st.warning("📤 Carregue a Ordem de Entrada (PDF) para começar!")
    st.info("""
    **Dicas se nenhum lote foi encontrado:**
    1. Verifique se o PDF tem texto (não é escaneado como imagem)
    2. Clique em "VER DEBUG" na sidebar
    3. Me envie as primeiras linhas do debug
    """)
    st.stop()

# Garantir índice válido
if st.session_state.lote_idx >= len(lista_lotes):
    st.session_state.lote_idx = 0

# ==================== NAVEGAÇÃO ====================
st.markdown(f"""
<div class="ordem-indicador">
    📌 {ordem_atual} | Lote {st.session_state.lote_idx + 1} de {len(lista_lotes)}
</div>
""", unsafe_allow_html=True)

col_prev, col_next = st.columns(2)

with col_prev:
    if st.button("⬅️ ANTERIOR", use_container_width=True, key="prev_btn"):
        st.session_state.lote_idx = max(0, st.session_state.lote_idx - 1)
        st.rerun()

with col_next:
    if st.button("PRÓXIMO ➡️", use_container_width=True, key="next_btn"):
        st.session_state.lote_idx = min(len(lista_lotes) - 1, st.session_state.lote_idx + 1)
        st.rerun()

lote_selecionado = st.selectbox(
    "🎯 Ir para o lote:",
    options=lista_lotes,
    index=st.session_state.lote_idx,
    key="select_lote"
)
st.session_state.lote_idx = lista_lotes.index(lote_selecionado)

num_lote = lista_lotes[st.session_state.lote_idx]
dados_lote = mapa_oe.get(num_lote, {})

# ==================== PAINEL PRINCIPAL ====================
st.markdown(f"""
<div class="lote-destaque">
    🐂 LOTE {num_lote}
    <br>
    <span style="font-size: 24px;">{dados_lote.get('posicao', f'{st.session_state.lote_idx + 1}º')} A ENTRAR</span>
</div>
""", unsafe_allow_html=True)

if dados_lote:
    # Informações principais do animal
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 DADOS DO ANIMAL")
        st.markdown(f"""
        <div class="animal-info">
            <strong>🏷️ CATEGORIA:</strong> {dados_lote.get("categoria", "-")}<br>
            <strong>🐾 RAÇA:</strong> {dados_lote.get("raca", "-")}<br>
            <strong>⚤ SEXO:</strong> {dados_lote.get("sexo", "-")}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⚖️ CARACTERÍSTICAS")
        st.markdown(f"""
        <div class="animal-info">
            <strong>⚖️ PESO:</strong> {dados_lote.get("peso", "-")}<br>
            <strong>📅 IDADE:</strong> {dados_lote.get("idade", "-")}<br>
            <strong>📜 REGISTRO:</strong> {dados_lote.get("registro", "-")}
        </div>
        """, unsafe_allow_html=True)
    
    # Descrição completa
    if dados_lote.get("descricao_completa"):
        st.markdown("### 📝 DESCRIÇÃO COMPLETA")
        st.markdown(f"""
        <div class="info-card">
            {dados_lote["descricao_completa"]}
        </div>
        """, unsafe_allow_html=True)
    
    # Vendedor
    if dados_lote.get("vendedor"):
        st.markdown("### 👨‍🌾 VENDEDOR")
        st.info(dados_lote["vendedor"])
    
    # Gatilhos
    st.markdown("### 🎤 GATILHOS PARA CANTAR")
    gatilhos = gerar_gatilhos(dados_lote)
    
    for i, gatilho in enumerate(gatilhos):
        st.markdown(f"""
        <div class="gatilho-card">
            {gatilho}
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning(f"⚠️ Lote {num_lote} não encontrado na extração")
    st.info("Clique em VER DEBUG na sidebar para verificar o formato do PDF")

# Rodapé simples
st.markdown("---")
st.markdown(f"**📋 Total de lotes: {len(lista_lotes)}**")
