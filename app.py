import streamlit as st
import pdfplumber
import re
import time
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
    .debug-box {
        background: #333;
        color: #0f0;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 14px;
        margin: 10px 0;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# ==================== PROCESSAMENTO DE PDF GRANDE ====================
@st.cache_data(ttl=7200, show_spinner=False)  # Cache por 2 horas
def processar_pdf_grande(file_bytes, tipo_arquivo):
    """
    Processa PDFs grandes de forma otimizada
    tipo_arquivo: 'oe' para Ordem de Entrada, 'cat' para Catálogo
    """
    paginas = []
    
    if not file_bytes:
        return paginas
    
    try:
        # Usa BytesIO para processamento em memória
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            total_paginas = len(pdf.pages)
            
            # Para catálogos, processa apenas primeiras 100 páginas
            if tipo_arquivo == 'cat':
                paginas_processar = min(total_paginas, 100)
                st.info(f"📚 Catálogo com {total_paginas} páginas. Processando primeiras {paginas_processar}...")
            else:
                # Para O.E., processa todas as páginas
                paginas_processar = total_paginas
                st.info(f"📋 O.E. com {total_paginas} páginas. Processando todas...")
            
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, page in enumerate(pdf.pages[:paginas_processar]):
                # Atualiza progresso
                progress = (i + 1) / paginas_processar
                progress_bar.progress(progress)
                status_text.text(f"📄 Processando página {i+1} de {paginas_processar}...")
                
                # Extrai texto com múltiplas tentativas
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
                
                # Se não conseguir extrair texto, tenta OCR básico
                if not texto:
                    try:
                        # Verifica se tem imagens (pode ser PDF escaneado)
                        if page.images:
                            paginas.append(f"[PÁGINA {i+1} COM IMAGEM - NECESSITA OCR]")
                            continue
                    except:
                        pass
                
                if texto:
                    paginas.append(texto)
            
            # Limpa barra de progresso
            progress_bar.empty()
            status_text.empty()
            
    except Exception as e:
        st.error(f"Erro ao processar PDF: {str(e)}")
        st.info("""
        **Possíveis soluções:**
        1. O PDF pode estar corrompido
        2. O PDF pode ser muito grande (tente dividir em partes)
        3. O PDF pode estar protegido por senha
        """)
    
    return paginas

# ==================== EXTRAÇÃO FLEXÍVEL ====================
@st.cache_data
def extrair_lotes_flexivel(texto_oe_tuple):
    """
    EXTRAÇÃO FLEXÍVEL - Tenta TODOS os padrões possíveis
    """
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
            
            # ============ PADRÃO 1: Com pipes (|) ============
            if '|' in linha_limpa:
                parts = [p.strip() for p in linha_limpa.split('|') if p.strip()]
                
                if len(parts) >= 2:
                    lote_encontrado = None
                    
                    # Estratégia 1: Procura "LT" ou "LOTE" explícito
                    for i, part in enumerate(parts):
                        m = re.search(r"\b(LT|LOTE)\s*[.:]?\s*(\d{1,4})", part, re.IGNORECASE)
                        if m:
                            lote_encontrado = m.group(2)
                            break
                    
                    # Estratégia 2: Pega o primeiro número de 1-3 dígitos
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
                        
                        dados = {
                            "posicao": f"{len(sequencia)}º A ENTRAR",
                            "lote": lt_num,
                            "categoria": "-",
                            "produto": "-",
                            "raca": "-",
                            "sexo": "-",
                            "idade": "-",
                            "peso": "-",
                            "registro": "-",
                            "vendedor": "-"
                        }
                        
                        # Tenta identificar campos
                        for part in parts:
                            part_lower = part.lower()
                            
                            if any(k in part_lower for k in ["touro", "vaca", "matriz", "novilha", "bezerro"]):
                                dados["categoria"] = part
                            elif any(k in part_lower for k in ["nelore", "angus", "girolando", "holandês"]):
                                dados["raca"] = part
                            elif any(k in part_lower for k in ["macho", "fêmea", "femea"]):
                                dados["sexo"] = part
                            elif "kg" in part_lower or "@" in part:
                                dados["peso"] = part
                            elif any(k in part_lower for k in ["ano", "meses", "mes"]):
                                dados["idade"] = part
                            elif len(part) > 10:
                                dados["produto"] = part
                        
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
                        "posicao": f"{len(sequencia)}º A ENTRAR",
                        "lote": lt_num,
                        "categoria": "-",
                        "produto": descricao if descricao else "-",
                        "raca": "-",
                        "sexo": "-",
                        "idade": "-",
                        "peso": "-",
                        "registro": "-",
                        "vendedor": "-"
                    }
            
            # ============ PADRÃO 3: Número no início da linha ============
            elif re.match(r"^\s*(\d{1,3})\s*[-.)]?\s*", linha_limpa):
                m = re.match(r"^\s*(\d{1,3})\s*[-.)]?\s*", linha_limpa)
                numero = int(m.group(1))
                
                if 1 <= numero <= 500:
                    lt_num = f"{numero:02d}"
                    
                    if lt_num not in sequencia:
                        sequencia.append(lt_num)
                    
                    descricao = linha_limpa[m.end():].strip()
                    
                    dados_por_lote[lt_num] = {
                        "posicao": f"{len(sequencia)}º A ENTRAR",
                        "lote": lt_num,
                        "categoria": "-",
                        "produto": descricao if descricao else "-",
                        "raca": "-",
                        "sexo": "-",
                        "idade": "-",
                        "peso": "-",
                        "registro": "-",
                        "vendedor": "-"
                    }
            
            # ============ PADRÃO 4: Qualquer linha com número ============
            else:
                m = re.search(r"\b(\d{1,3})\b", linha_limpa)
                if m:
                    numero = int(m.group(1))
                    
                    if 1 <= numero <= 500:
                        if len(linha_limpa) > 3:
                            lt_num = f"{numero:02d}"
                            
                            if lt_num not in sequencia:
                                sequencia.append(lt_num)
                            
                            dados_por_lote[lt_num] = {
                                "posicao": f"{len(sequencia)}º A ENTRAR",
                                "lote": lt_num,
                                "categoria": "-",
                                "produto": linha_limpa,
                                "raca": "-",
                                "sexo": "-",
                                "idade": "-",
                                "peso": "-",
                                "registro": "-",
                                "vendedor": "-"
                            }
    
    return sequencia, dados_por_lote

# ==================== GATILHOS ====================
def gerar_gatilhos_simples(dados_lote):
    """Gera gatilhos básicos"""
    gatilhos = []
    
    if not dados_lote:
        return [
            "⭐ ANIMAL SELECIONADO: Qualidade superior!",
            "📋 DOCUMENTAÇÃO: Registro em dia!",
            "🔨 OPORTUNIDADE: Preço especial!"
        ]
    
    produto = dados_lote.get("produto", "").lower()
    categoria = dados_lote.get("categoria", "").lower()
    raca = dados_lote.get("raca", "").lower()
    
    if any(k in produto + categoria for k in ["touro", "macho"]):
        gatilhos.extend([
            "🐂 REPRODUTOR: Genética superior!",
            "📈 GANHO DE PESO: Bezerros pesados!",
            "🔨 FECHAMENTO: Oportunidade única!"
        ])
    elif any(k in produto + categoria for k in ["vaca", "matriz", "fêmea", "femea"]):
        gatilhos.extend([
            "👑 MATRIZ: Habilidade materna!",
            "🥛 PRODUÇÃO: Excelente produtividade!",
            "🔨 FECHAMENTO: Fêmea de elite!"
        ])
    elif any(k in produto + categoria for k in ["cavalo", "égua", "mangalarga"]):
        gatilhos.extend([
            "🐴 MARCHA: Conforto e elegância!",
            "🏇 DESEMPENHO: Pronto para competições!",
            "🔨 FECHAMENTO: Animal diferenciado!"
        ])
    else:
        gatilhos.extend([
            "⭐ QUALIDADE: Animal selecionado!",
            "📋 PROCEDÊNCIA: Origem garantida!",
            "🔨 OPORTUNIDADE: Preço imperdível!"
        ])
    
    if dados_lote.get("peso") and dados_lote["peso"] != "-":
        gatilhos.append(f"⚖️ PESO: {dados_lote['peso']}!")
    
    if dados_lote.get("raca") and dados_lote["raca"] != "-":
        gatilhos.append(f"🧬 GENÉTICA {dados_lote['raca'].upper()}: Linhagem superior!")
    
    return gatilhos[:4]

# ==================== INTERFACE PRINCIPAL ====================
st.title("🎤 PAINEL DO LEILOEIRO")

# Sidebar
with st.sidebar:
    st.header("📂 Arquivos")
    
    st.markdown("""
    <div class="upload-info">
        📤 Tamanho máximo: 500MB<br>
        💡 Arquivos grandes podem levar alguns minutos
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
        st.success(f"✅ O.E. carregada! ({tamanho_mb:.1f} MB)")
    
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
    if st.button("🔍 VER DEBUG DA EXTRAÇÃO", use_container_width=True):
        st.session_state.mostrar_debug = True
    else:
        st.session_state.mostrar_debug = False

# Processar O.E.
if file_oe:
    with st.spinner("🔄 Processando Ordem de Entrada... (pode demorar para arquivos grandes)"):
        file_bytes = file_oe.getvalue()
        texto_oe = processar_pdf_grande(file_bytes, 'oe')
        texto_oe_tuple = tuple(texto_oe) if texto_oe else tuple()
else:
    texto_oe = []
    texto_oe_tuple = tuple()

# Processar Catálogo (se existir)
if file_cat:
    with st.spinner("🔄 Processando Catálogo... (pode demorar para arquivos grandes)"):
        file_bytes = file_cat.getvalue()
        texto_cat = processar_pdf_grande(file_bytes, 'cat')
else:
    texto_cat = []

# Extrair dados
sequencia_oe, mapa_oe = extrair_lotes_flexivel(texto_oe_tuple)

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
    
    # Adiciona lotes do catálogo
    if texto_cat:
        lotes_cat = set()
        for p in texto_cat:
            encontrados = re.findall(r"\b(?:LOTE|LT)?\s*(\d{1,3})\b", p, re.IGNORECASE)
            for l in encontrados:
                if 1 <= int(l) <= 500:
                    lotes_cat.add(f"{int(l):02d}")
        
        lotes_faltantes = sorted([l for l in lotes_cat if l not in sequencia_oe])
        if lotes_faltantes:
            lista_lotes.extend(lotes_faltantes)
else:
    lista_lotes = []
    ordem_atual = "⚠️ NENHUM LOTE ENCONTRADO"

# Estado da sessão
if 'lote_idx' not in st.session_state:
    st.session_state.lote_idx = 0
if 'lance_atual' not in st.session_state:
    st.session_state.lance_atual = {}
if 'lotes_vendidos' not in st.session_state:
    st.session_state.lotes_vendidos = []

# Verificar se há lotes
if not lista_lotes:
    st.warning("📤 Carregue a Ordem de Entrada (PDF) para começar!")
    st.info("""
    **Dicas se nenhum lote foi encontrado:**
    1. Verifique se o PDF tem texto (não é escaneado como imagem)
    2. Clique em "VER DEBUG DA EXTRAÇÃO" na sidebar
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
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Informações")
        st.markdown(f"""
        <div class="info-card">
            <strong>🏷️ Categoria:</strong> {dados_lote.get("categoria", "-")}<br>
            <strong>🐾 Raça:</strong> {dados_lote.get("raca", "-")}<br>
            <strong>⚤ Sexo:</strong> {dados_lote.get("sexo", "-")}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⚖️ Detalhes")
        st.markdown(f"""
        <div class="info-card">
            <strong>⚖️ Peso:</strong> {dados_lote.get("peso", "-")}<br>
            <strong>📅 Idade:</strong> {dados_lote.get("idade", "-")}<br>
            <strong>📜 Registro:</strong> {dados_lote.get("registro", "-")}
        </div>
        """, unsafe_allow_html=True)
    
    if dados_lote.get("produto") and dados_lote["produto"] != "-":
        st.markdown("### 📝 Descrição")
        st.info(dados_lote["produto"])
    
    st.markdown("### 💰 Controle de Lance")
    col_lance, col_vender = st.columns([2, 1])
    
    with col_lance:
        if num_lote not in st.session_state.lance_atual:
            st.session_state.lance_atual[num_lote] = 0
        
        novo_lance = st.number_input(
            "Valor do lance (R$):",
            min_value=0.0,
            value=float(st.session_state.lance_atual.get(num_lote, 0)),
            step=100.0,
            key=f"lance_{num_lote}",
            format="%.2f"
        )
        st.session_state.lance_atual[num_lote] = novo_lance
    
    with col_vender:
        st.markdown("")
        st.markdown("")
        if st.button("✅ VENDIDO", use_container_width=True, type="primary", key=f"vender_{num_lote}"):
            if num_lote not in st.session_state.lotes_vendidos:
                st.session_state.lotes_vendidos.append(num_lote)
                st.balloons()
                st.success(f"🎉 Lote {num_lote} VENDIDO!")
                time.sleep(1)
                st.rerun()
    
    st.markdown("### 🎤 Gatilhos para Cantar")
    gatilhos = gerar_gatilhos_simples(dados_lote)
    
    for i, gatilho in enumerate(gatilhos):
        st.markdown(f"""
        <div class="gatilho-card">
            {gatilho}
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning(f"⚠️ Lote {num_lote} não encontrado na extração")

# Rodapé
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📋 Total de Lotes", len(lista_lotes))

with col2:
    st.metric("✅ Vendidos", len(st.session_state.lotes_vendidos))

with col3:
    valor_total = sum(st.session_state.lance_atual.get(lote, 0) for lote in st.session_state.lotes_vendidos)
    st.metric("💰 Total", f"R$ {valor_total:,.0f}")
