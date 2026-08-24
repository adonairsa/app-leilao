import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

# Configuração para tablet
st.set_page_config(
    page_title="🎤 LEILOEIRO PRO",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed",  # Sidebar recolhida para economizar espaço
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': 'Painel do Leiloeiro - Versão Tablet'
    }
)

# ==================== CSS PARA TABLET ====================
st.markdown("""
<style>
    /* Ajustes gerais para touch */
    * {
        -webkit-tap-highlight-color: transparent;
    }
    
    /* Botões maiores para touch */
    .stButton > button {
        min-height: 60px;
        font-size: 20px;
        border-radius: 15px;
        margin: 5px 0;
        touch-action: manipulation;
    }
    
    /* Inputs maiores */
    .stTextInput > div > div > input {
        min-height: 50px;
        font-size: 20px;
    }
    
    .stSelectbox > div > div {
        min-height: 50px;
        font-size: 20px;
    }
    
    .stNumberInput > div > div > input {
        min-height: 50px;
        font-size: 20px;
    }
    
    .stTextArea > div > div > textarea {
        font-size: 18px;
    }
    
    /* Lote em destaque */
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
    
    /* Indicador de ordem */
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
    
    /* Cards de informação */
    .info-card {
        background: rgba(255,255,255,0.08);
        border: 2px solid #4CAF50;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        font-size: 18px;
    }
    
    /* Gatilhos */
    .gatilho-card {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 18px;
        border-radius: 15px;
        font-size: 18px;
        margin: 10px 0;
        min-height: 80px;
    }
    
    /* Esconde elementos desnecessários no tablet */
    @media (max-width: 768px) {
        .lote-destaque {
            font-size: 40px;
            padding: 15px;
        }
        
        .stButton > button {
            min-height: 50px;
            font-size: 18px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==================== PROCESSAMENTO DE PDFS (OTIMIZADO) ====================
@st.cache_data(ttl=3600)  # Cache por 1 hora
def processar_pdf(file):
    """Processa PDF com cache otimizado para cloud"""
    paginas = []
    if file is not None:
        try:
            with pdfplumber.open(file) as pdf:
                # Limita processamento para não travar
                for i, page in enumerate(pdf.pages[:100]):  # Máximo 100 páginas
                    texto = page.extract_text(layout=True)
                    if texto:
                        paginas.append(texto)
        except Exception as e:
            st.error(f"Erro ao processar PDF: {str(e)}")
    return paginas

# ==================== EXTRAÇÃO ROBUSTA ====================
@st.cache_data
def extrair_dados_oe_robusto(texto_oe_tuple):
    """Extração robusta com cache (recebe tuple para ser hashable)"""
    texto_oe = list(texto_oe_tuple)
    sequencia = []
    dados_por_lote = {}
    ordem_original = []
    
    if not texto_oe:
        return sequencia, dados_por_lote, ordem_original
    
    for pagina_idx, pagina in enumerate(texto_oe):
        linhas = pagina.split('\n')
        
        for linha_idx, linha in enumerate(linhas):
            linha_original = linha.strip()
            
            # PADRÃO 1: Com pipes
            if '|' in linha:
                parts = [p.strip() for p in linha.split('|') if p.strip()]
                if len(parts) >= 2:
                    lote_encontrado = None
                    
                    for i, part in enumerate(parts):
                        m_lote = re.search(r"\b(\d{1,3})\b", part)
                        if m_lote and i >= 1 and not lote_encontrado:
                            lote_encontrado = m_lote.group(1)
                            break
                    
                    if lote_encontrado and 1 <= int(lote_encontrado) <= 500:
                        lt_num = f"{int(lote_encontrado):02d}"
                        
                        if lt_num not in sequencia:
                            sequencia.append(lt_num)
                            ordem_original.append({
                                'posicao': len(sequencia),
                                'lote': lt_num,
                            })
                        
                        dados_por_lote[lt_num] = {
                            "posicao": f"{len(sequencia)}º",
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
            
            # PADRÃO 2: "LOTE XX"
            elif re.search(r"\b(LOTE|LT)\s*[:.]?\s*(\d{1,3})\b", linha, re.IGNORECASE):
                m = re.search(r"\b(LOTE|LT)\s*[:.]?\s*(\d{1,3})\b", linha, re.IGNORECASE)
                lt_num = f"{int(m.group(2)):02d}"
                
                if lt_num not in sequencia:
                    sequencia.append(lt_num)
                    ordem_original.append({
                        'posicao': len(sequencia),
                        'lote': lt_num,
                    })
                
                descricao = linha.replace(m.group(0), '').strip()
                dados_por_lote[lt_num] = {
                    "posicao": f"{len(sequencia)}º",
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
    
    return sequencia, dados_por_lote, ordem_original

@st.cache_data
def extrair_lotes_catalogo(texto_cat_tuple):
    """Extrai lotes do catálogo com cache"""
    texto_cat = list(texto_cat_tuple)
    lotes_cat = set()
    
    if not texto_cat:
        return lotes_cat
    
    for pagina in texto_cat:
        padroes = [
            r"\bLOTE\s*[:.]?\s*(\d{1,3})\b",
            r"\bLT\s*[:.]?\s*(\d{1,3})\b",
        ]
        
        for padrao in padroes:
            encontrados = re.findall(padrao, pagina, re.IGNORECASE)
            for l in encontrados:
                if 1 <= int(l) <= 500:
                    lotes_cat.add(f"{int(l):02d}")
    
    return lotes_cat

# ==================== GATILHOS OTIMIZADOS ====================
@st.cache_data
def gerar_gatilhos_avancados(categoria, produto, raca, sexo, peso, registro, vendedor):
    """Gera gatilhos com cache baseado em parâmetros simples"""
    gatilhos = []
    txt = f"{categoria} {produto} {raca} {sexo}".lower()
    
    # Gado de Corte
    if any(k in txt for k in ["nelore", "angus", "corte", "touro", "boi", "carcaça"]):
        gatilhos.extend([
            "🐂 TOURO MELHORADOR: Genética de ponta para revolucionar seu rebanho!",
            "📈 GANHO DE PESO: Conversão alimentar excepcional!",
            "🔨 FECHAMENTO: Oportunidade única de genética premiada!"
        ])
        
        if "touro" in produto or "macho" in produto:
            gatilhos.append("🏆 REPRODUTOR: Pronto para cobrir, fertilidade garantida!")
        elif "matriz" in produto or "fêmea" in produto or "vaca" in produto:
            gatilhos.append("👑 MATRIZ: Habilidade materna excepcional!")
    
    # Gado Leiteiro
    elif any(k in txt for k in ["leite", "girolando", "holandês", "lactação"]):
        gatilhos.extend([
            "🥛 PRODUÇÃO LEITEIRA: Pico de lactação impressionante!",
            "📊 CONTROLE LEITEIRO: Produção acima da média!",
            "💎 GENÉTICA LEITEIRA: Touros provados na linhagem!"
        ])
    
    # Cavalos
    elif any(k in txt for k in ["cavalo", "égua", "mangalarga", "quarto de milha"]):
        gatilhos.extend([
            "🐴 MARCHA BATIDA: Sela macia e confortável!",
            "🏇 DESEMPENHO: Pronto para provas!",
            "💪 MORFOLOGIA: Aprumos perfeitos!"
        ])
    
    # Ovinos/Caprinos
    elif any(k in txt for k in ["ovino", "caprino", "ovelha", "cordeiro"]):
        gatilhos.extend([
            "🐑 PRECOCIDADE: Pronto para abate ou reprodução!",
            "📈 PROLIFICIDADE: Partos múltiplos comprovados!",
            "💎 GENÉTICA: Padrão racial impecável!"
        ])
    
    # Genéricos
    else:
        gatilhos.extend([
            "⭐ QUALIDADE SUPERIOR: Animal selecionado!",
            "📋 DOCUMENTAÇÃO: Registro em dia!",
            "🔨 OPORTUNIDADE: Preço abaixo do mercado!"
        ])
    
    # Específicos
    if peso and peso not in ["-", ""]:
        gatilhos.append(f"⚖️ PESO: {peso} kg de produtividade!")
    
    if registro and registro not in ["-", ""]:
        gatilhos.append(f"📜 REGISTRO: {registro} - Genealogia garantida!")
    
    if vendedor and vendedor not in ["-", ""]:
        gatilhos.append(f"🤝 VENDEDOR: {vendedor} - Criador de confiança!")
    
    return gatilhos[:4]  # Limita a 4 para não sobrecarregar

# ==================== INTERFACE PRINCIPAL ====================
st.title("🎤 PAINEL DO LEILOEIRO")
st.markdown("---")

# Sidebar com configurações
with st.sidebar:
    st.header("📂 Arquivos")
    
    # Upload com feedback visual
    file_oe = st.file_uploader(
        "📋 Ordem de Entrada (PDF)",
        type="pdf",
        key="oe",
        help="Carregue o PDF da Ordem de Entrada"
    )
    
    file_cat = st.file_uploader(
        "📚 Catálogo (PDF)",
        type="pdf",
        key="cat",
        help="Carregue o PDF do Catálogo"
    )
    
    # Status do processamento
    if file_oe:
        st.success("✅ O.E. carregada!")
    if file_cat:
        st.success("✅ Catálogo carregado!")
    
    st.markdown("---")
    st.header("⚙️ Ordem dos Lotes")
    
    modo_ordenacao = st.radio(
        "Escolha a ordem:",
        ["🎯 ORDEM DE ENTRADA", "🔢 ORDEM NUMÉRICA"],
        index=0,
        help="A Ordem de Entrada segue exatamente o PDF da O.E."
    )
    
    # Mostrar contagem de lotes
    if 'lista_lotes' in locals() or 'lista_lotes' in globals():
        st.info(f"📊 {len(lista_lotes)} lotes disponíveis")

# Processar PDFs
with st.spinner("🔄 Processando arquivos..."):
    if file_oe:
        texto_oe = processar_pdf(file_oe)
        # Converter para tuple para cache
        texto_oe_tuple = tuple(texto_oe) if texto_oe else tuple()
    else:
        texto_oe = []
        texto_oe_tuple = tuple()
    
    if file_cat:
        texto_cat = processar_pdf(file_cat)
        texto_cat_tuple = tuple(texto_cat) if texto_cat else tuple()
    else:
        texto_cat = []
        texto_cat_tuple = tuple()

# Extrair dados
sequencia_oe, mapa_oe, _ = extrair_dados_oe_robusto(texto_oe_tuple)
lotes_cat = extrair_lotes_catalogo(texto_cat_tuple)

# Definir lista de lotes
if modo_ordenacao == "🎯 ORDEM DE ENTRADA" and sequencia_oe:
    lista_lotes = sequencia_oe.copy()
    ordem_atual = "🎯 ORDEM DE ENTRADA"
    
    # Adiciona lotes faltantes do catálogo
    if lotes_cat:
        lotes_faltantes = sorted([l for l in lotes_cat if l not in sequencia_oe])
        if lotes_faltantes:
            lista_lotes.extend(lotes_faltantes)
            
elif sequencia_oe or lotes_cat:
    todos_lotes = set(sequencia_oe).union(lotes_cat)
    lista_lotes = sorted(list(todos_lotes), key=lambda x: int(x))
    ordem_atual = "🔢 ORDEM NUMÉRICA"
else:
    lista_lotes = [f"{i:02d}" for i in range(1, 31)]
    ordem_atual = "⚠️ ORDEM PADRÃO"

# Estado da sessão
if 'lote_idx' not in st.session_state:
    st.session_state.lote_idx = 0
if 'lance_atual' not in st.session_state:
    st.session_state.lance_atual = {}
if 'lotes_vendidos' not in st.session_state:
    st.session_state.lotes_vendidos = []

# Garantir índice válido
if st.session_state.lote_idx >= len(lista_lotes):
    st.session_state.lote_idx = 0

# ==================== NAVEGAÇÃO OTIMIZADA PARA TOUCH ====================
st.markdown(f"""
<div class="ordem-indicador">
    📌 {ordem_atual} | Lote {st.session_state.lote_idx + 1} de {len(lista_lotes)}
</div>
""", unsafe_allow_html=True)

# Botões grandes de navegação
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

# Informações do lote em cards
if dados_lote:
    # Grid responsivo (2 colunas no tablet)
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
        peso = dados_lote.get("peso", "-")
        st.markdown(f"""
        <div class="info-card">
            <strong>⚖️ Peso:</strong> {peso if peso != '-' else '-'}<br>
            <strong>📜 Registro:</strong> {dados_lote.get("registro", "-")}<br>
            <strong>👨‍🌾 Vendedor:</strong> {dados_lote.get("vendedor", "-")}<br>
            <strong>📝 Status:</strong> {'VENDIDO' if num_lote in st.session_state.lotes_vendidos else 'DISPONÍVEL'}
        </div>
        """, unsafe_allow_html=True)
    
    # Descrição
    if dados_lote.get("produto") and dados_lote["produto"] != "-":
        st.markdown("### 📝 Descrição")
        st.info(dados_lote["produto"])
    
    # Controle de lances simplificado
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
    
    # Gatilhos
    st.markdown("### 🎤 Gatilhos para Cantar")
    
    gatilhos = gerar_gatilhos_avancados(
        dados_lote.get("categoria", ""),
        dados_lote.get("produto", ""),
        dados_lote.get("raca", ""),
        dados_lote.get("sexo", ""),
        dados_lote.get("peso", ""),
        dados_lote.get("registro", ""),
        dados_lote.get("vendedor", "")
    )
    
    # Mostrar gatilhos em grid
    for i, gatilho in enumerate(gatilhos):
        st.markdown(f"""
        <div class="gatilho-card">
            {gatilho}
        </div>
        """, unsafe_allow_html=True)
    
    # Texto pronto para falar
    st.markdown("### 📢 Texto Pronto")
    
    texto_fala = f"🎤 LOTE {num_lote}! "
    if dados_lote.get("categoria") and dados_lote["categoria"] != "-":
        texto_fala += f"{dados_lote['categoria']} "
    if dados_lote.get("produto") and dados_lote["produto"] != "-":
        texto_fala += f"{dados_lote['produto']} "
    if dados_lote.get("raca") and dados_lote["raca"] != "-":
        texto_fala += f"da raça {dados_lote['raca']} "
    texto_fala += "EM PISTA!"
    
    st.text_area(
        "Copie e cole:",
        value=texto_fala,
        height=120,
        key=f"texto_fala_{num_lote}"
    )

else:
    st.warning("⚠️ Lote não encontrado na Ordem de Entrada")

# ==================== RODAPÉ ====================
st.markdown("---")

# Estatísticas rápidas
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📋 Lotes", len(lista_lotes))

with col2:
    st.metric("✅ Vendidos", len(st.session_state.lotes_vendidos))

with col3:
    valor_total = sum(st.session_state.lance_atual.get(lote, 0) for lote in st.session_state.lotes_vendidos)
    st.metric("💰 Total", f"R$ {valor_total:,.0f}")

# Próximos lotes (visual compacto)
st.markdown("### 📊 Próximos Lotes")
colunas = st.columns(5)
idx_atual = st.session_state.lote_idx

for i, col in enumerate(colunas):
    idx_proximo = idx_atual + i + 1
    if idx_proximo < len(lista_lotes):
        lote = lista_lotes[idx_proximo]
        status = "✅" if lote in st.session_state.lotes_vendidos else "⏳"
        with col:
            st.markdown(f"**{status} {lote}**")
            if st.button(f"Ir para {lote}", key=f"goto_{lote}", use_container_width=True):
                st.session_state.lote_idx = idx_proximo
                st.rerun()
