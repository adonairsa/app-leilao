import streamlit as st
import pdfplumber
import re
import time

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
</style>
""", unsafe_allow_html=True)

# ==================== PROCESSAMENTO DE PDFS ====================
@st.cache_data(ttl=3600)
def processar_pdf(file):
    """Processa PDF com cache"""
    paginas = []
    if file is not None:
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages[:100]:
                    # Tenta extração com layout primeiro
                    texto = page.extract_text(layout=True)
                    if not texto:
                        # Fallback para extração simples
                        texto = page.extract_text()
                    if texto:
                        paginas.append(texto)
        except Exception as e:
            st.error(f"Erro ao processar PDF: {str(e)}")
    return paginas

# ==================== EXTRAÇÃO CORRIGIDA - FOCO NO CAMPO "LT" ====================
@st.cache_data
def extrair_dados_oe_corrigido(texto_oe_tuple):
    """
    EXTRAÇÃO CORRIGIDA - Reconhece especificamente o campo 'LT' como número do lote
    """
    texto_oe = list(texto_oe_tuple)
    sequencia = []
    dados_por_lote = {}
    
    if not texto_oe:
        return sequencia, dados_por_lote
    
    for pagina_idx, pagina in enumerate(texto_oe):
        linhas = pagina.split('\n')
        
        for linha in linhas:
            linha_limpa = linha.strip()
            
            # ============ PADRÃO PRINCIPAL: Com pipes (|) ============
            if '|' in linha_limpa:
                parts = [p.strip() for p in linha_limpa.split('|') if p.strip()]
                
                if len(parts) >= 2:
                    # PROCURA ESPECÍFICA PELO CAMPO "LT" OU "LOTE"
                    lote_encontrado = None
                    idx_lote = -1
                    
                    for i, part in enumerate(parts):
                        # Verifica se a parte contém "LT" ou "LOTE"
                        if re.search(r"\b(LT|LOTE)\b", part, re.IGNORECASE):
                            # Extrai o número após LT/LOTE
                            m = re.search(r"\b(LT|LOTE)\s*[.:]?\s*(\d{1,3})", part, re.IGNORECASE)
                            if m:
                                lote_encontrado = m.group(2)
                                idx_lote = i
                                break
                            # Tenta encontrar número na mesma parte
                            m = re.search(r"(\d{1,3})", part)
                            if m:
                                lote_encontrado = m.group(1)
                                idx_lote = i
                                break
                    
                    # Se não encontrou "LT" explícito, tenta segunda coluna
                    if not lote_encontrado and len(parts) >= 2:
                        # Assume que a segunda coluna é o lote
                        m = re.search(r"(\d{1,3})", parts[1])
                        if m:
                            lote_encontrado = m.group(1)
                            idx_lote = 1
                    
                    if lote_encontrado and 1 <= int(lote_encontrado) <= 500:
                        lt_num = f"{int(lote_encontrado):02d}"
                        
                        # Adiciona à sequência se não existe
                        if lt_num not in sequencia:
                            sequencia.append(lt_num)
                        
                        # Extrai dados das outras colunas
                        dados_por_lote[lt_num] = {
                            "posicao": f"{len(sequencia)}º A ENTRAR",
                            "lote": lt_num,
                            "categoria": parts[2] if len(parts) > 2 else "-",
                            "produto": parts[3] if len(parts) > 3 else "-",
                            "raca": parts[4] if len(parts) > 4 else "-",
                            "sexo": parts[5] if len(parts) > 5 else "-",
                            "idade": parts[6] if len(parts) > 6 else "-",
                            "peso": parts[7] if len(parts) > 7 else "-",
                            "registro": parts[8] if len(parts) > 8 else "-",
                            "vendedor": parts[11] if len(parts) > 11 else "-"
                        }
            
            # ============ PADRÃO ALTERNATIVO: "LT XX" ou "LOTE XX" ============
            elif re.search(r"\b(LT|LOTE)\s*[.:]?\s*(\d{1,3})", linha_limpa, re.IGNORECASE):
                m = re.search(r"\b(LT|LOTE)\s*[.:]?\s*(\d{1,3})", linha_limpa, re.IGNORECASE)
                lt_num = f"{int(m.group(2)):02d}"
                
                if lt_num not in sequencia:
                    sequencia.append(lt_num)
                
                # Captura descrição após o número
                descricao = linha_limpa[m.end():].strip()
                dados_por_lote[lt_num] = {
                    "posicao": f"{len(sequencia)}º A ENTRAR",
                    "lote": lt_num,
                    "categoria": "A DEFINIR",
                    "produto": descricao if descricao else "-",
                    "raca": "-",
                    "sexo": "-",
                    "idade": "-",
                    "peso": "-",
                    "registro": "-",
                    "vendedor": "-"
                }
            
            # ============ PADRÃO COM TABULAÇÃO ============
            elif '\t' in linha_limpa:
                parts = linha_limpa.split('\t')
                if len(parts) >= 2:
                    # Procura número em qualquer parte
                    for i, part in enumerate(parts):
                        m = re.search(r"\b(LT|LOTE)?\s*(\d{1,3})\b", part, re.IGNORECASE)
                        if m and m.group(2):
                            lt_num = f"{int(m.group(2)):02d}"
                            if lt_num not in sequencia:
                                sequencia.append(lt_num)
                            
                            dados_por_lote[lt_num] = {
                                "posicao": f"{len(sequencia)}º A ENTRAR",
                                "lote": lt_num,
                                "categoria": parts[i+1] if len(parts) > i+1 else "-",
                                "produto": parts[i+2] if len(parts) > i+2 else "-",
                                "raca": "-",
                                "sexo": "-",
                                "idade": "-",
                                "peso": "-",
                                "registro": "-",
                                "vendedor": "-"
                            }
                            break
    
    # Ordena a sequência pela ordem de aparição no PDF
    return sequencia, dados_por_lote

# ==================== DEBUG DA EXTRAÇÃO ====================
def mostrar_debug_extracao(texto_oe, sequencia, dados_por_lote):
    """Mostra informações de debug para ajudar a identificar problemas"""
    with st.expander("🔍 DEBUG - Visualizar extração", expanded=False):
        st.write(f"**Total de páginas:** {len(texto_oe)}")
        st.write(f"**Total de lotes extraídos:** {len(sequencia)}")
        
        if sequencia:
            st.write("**Primeiros 10 lotes na sequência:**")
            st.write(sequencia[:10])
        
        if texto_oe:
            st.write("**Primeiras 5 linhas do PDF:**")
            for i, pagina in enumerate(texto_oe[:2]):
                linhas = pagina.split('\n')
                st.text(f"Página {i+1}:")
                for linha in linhas[:5]:
                    st.text(linha)

# ==================== INTERFACE PRINCIPAL ====================
st.title("🎤 PAINEL DO LEILOEIRO")

# Sidebar
with st.sidebar:
    st.header("📂 Arquivos")
    file_oe = st.file_uploader("📋 Ordem de Entrada (PDF)", type="pdf", key="oe")
    file_cat = st.file_uploader("📚 Catálogo (PDF)", type="pdf", key="cat")
    
    st.markdown("---")
    st.header("⚙️ Ordem dos Lotes")
    
    modo_ordenacao = st.radio(
        "Escolha a ordem:",
        ["🎯 ORDEM DE ENTRADA", "🔢 ORDEM NUMÉRICA"],
        index=0,
        help="ORDEM DE ENTRADA: segue exatamente a sequência do PDF da O.E."
    )

# Processar PDFs
with st.spinner("🔄 Processando arquivos..."):
    if file_oe:
        texto_oe = processar_pdf(file_oe)
        texto_oe_tuple = tuple(texto_oe) if texto_oe else tuple()
    else:
        texto_oe = []
        texto_oe_tuple = tuple()
    
    if file_cat:
        texto_cat = processar_pdf(file_cat)
    else:
        texto_cat = []

# Extrair dados
sequencia_oe, mapa_oe = extrair_dados_oe_corrigido(texto_oe_tuple)

# Mostrar debug se houver problemas
if file_oe and not sequencia_oe:
    st.error("⚠️ Nenhum lote encontrado! Verifique o formato do PDF.")
    mostrar_debug_extracao(texto_oe, sequencia_oe, mapa_oe)

# Definir lista de lotes
if modo_ordenacao == "🎯 ORDEM DE ENTRADA" and sequencia_oe:
    lista_lotes = sequencia_oe.copy()
    ordem_atual = "🎯 ORDEM DE ENTRADA"
    
    # Adiciona lotes do catálogo se existirem
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
            
elif sequencia_oe:
    lista_lotes = sorted(sequencia_oe, key=lambda x: int(x))
    ordem_atual = "🔢 ORDEM NUMÉRICA"
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

# Botões de navegação
col_prev, col_next = st.columns(2)

with col_prev:
    if st.button("⬅️ ANTERIOR", use_container_width=True, key="prev_btn"):
        st.session_state.lote_idx = max(0, st.session_state.lote_idx - 1)
        st.rerun()

with col_next:
    if st.button("PRÓXIMO ➡️", use_container_width=True, key="next_btn"):
        st.session_state.lote_idx = min(len(lista_lotes) - 1, st.session_state.lote_idx + 1)
        st.rerun()

# Selector direto
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

# Informações do lote
if dados_lote:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Informações Básicas")
        st.markdown(f"""
        <div class="info-card">
            <strong>🏷️ Categoria:</strong> {dados_lote.get("categoria", "-")}<br>
            <strong>🐾 Raça:</strong> {dados_lote.get("raca", "-")}<br>
            <strong>⚤ Sexo:</strong> {dados_lote.get("sexo", "-")}<br>
            <strong>📅 Idade:</strong> {dados_lote.get("idade", "-")}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⚖️ Características")
        st.markdown(f"""
        <div class="info-card">
            <strong>⚖️ Peso:</strong> {dados_lote.get("peso", "-")}<br>
            <strong>📜 Registro:</strong> {dados_lote.get("registro", "-")}<br>
            <strong>👨‍🌾 Vendedor:</strong> {dados_lote.get("vendedor", "-")}<br>
            <strong>📝 Status:</strong> {'VENDIDO' if num_lote in st.session_state.lotes_vendidos else 'DISPONÍVEL'}
        </div>
        """, unsafe_allow_html=True)
    
    # Descrição
    if dados_lote.get("produto") and dados_lote["produto"] != "-":
        st.markdown("### 📝 Descrição")
        st.info(dados_lote["produto"])
    
    # Controle de lance
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

else:
    st.warning("⚠️ Dados não encontrados para este lote na Ordem de Entrada")

# ==================== RODAPÉ ====================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📋 Total de Lotes", len(lista_lotes))

with col2:
    st.metric("✅ Vendidos", len(st.session_state.lotes_vendidos))

with col3:
    valor_total = sum(st.session_state.lance_atual.get(lote, 0) for lote in st.session_state.lotes_vendidos)
    st.metric("💰 Total Vendido", f"R$ {valor_total:,.0f}")
