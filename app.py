import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="PAINEL DE PISTA PRO", layout="wide")

# CSS COM BLINDAGEM DE CONTRASTE E VISUAL CLEAN
st.markdown("""
    <style>
    .big-lote { font-size: 40px !important; font-weight: bold; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    
    .card-oe, .card-lote, .card-pai, .card-mae, .card-jargao {
        background-color: #FFFFFF !important;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
    }

    .card-oe { border-left: 8px solid #D97706; }
    .card-lote { border-left: 8px solid #1E3A8A; }
    .card-pai { border-left: 6px solid #0284C7; }
    .card-mae { border-left: 6px solid #DB2777; }
    .card-jargao { border-left: 6px solid #10B981; }

    .card-oe *, .card-lote *, .card-pai *, .card-mae *, .card-jargao *, .texto-pista {
        color: #000000 !important;
        font-weight: bold !important;
    }

    div[data-testid="stToolbar"] {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# PROCESSAMENTO DE PDFS COM CACHE
@st.cache_data
def processar_pdf(file):
    paginas = []
    if file is not None:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                texto = page.extract_text(layout=True)
                if texto:
                    paginas.append(texto)
    return paginas

# PARSER EXATO DA ORDEM DE ENTRADA
def buscar_dados_oe_exatos(texto_oe, num_lote_alvo):
    if not texto_oe:
        return None
    
    lote_alvo_int = str(int(num_lote_alvo))
    
    for pagina in texto_oe:
        for linha in pagina.split('\n'):
            if '|' in linha:
                colunas = [c.strip() for c in linha.split('|') if c.strip()]
                if len(colunas) >= 2:
                    lote_col = re.sub(r"\D", "", colunas[1])
                    if lote_col and str(int(lote_col)) == lote_alvo_int:
                        return {
                            "posicao": colunas[0] if len(colunas) > 0 else "-",
                            "lote": colunas[1] if len(colunas) > 1 else "-",
                            "qtd": colunas[2] if len(colunas) > 2 else "-",
                            "idade": colunas[3] if len(colunas) > 3 else "-",
                            "peso": colunas[4] if len(colunas) > 4 else "-",
                            "categoria": colunas[5] if len(colunas) > 5 else "-",
                            "produto": colunas[6] if len(colunas) > 6 else "-",
                            "vendedor": colunas[7] if len(colunas) > 7 else "-"
                        }
            else:
                match = re.search(rf"^(\d+[°º]?)\s+(\d{{1,3}})\s+(\d+)\s+([\d\w]+)\s+([\d\wKg]*)\s+(.+)", linha.strip())
                if match:
                    pos, lt, qtd, idade, peso, resto = match.groups()
                    if str(int(lt)) == lote_alvo_int:
                        return {
                            "posicao": pos, "lote": lt, "qtd": qtd, 
                            "idade": idade, "peso": peso, "categoria": "Lote de Pista", 
                            "produto": resto, "vendedor": "-"
                        }
    return None

# GERADOR DE GATILHOS POR CATEGORIA
def gerar_gatilhos_categoria(texto_completo):
    txt = texto_completo.lower()
    if any(k in txt for k in ["trator", "máquina", "maquina", "colheitadeira", "cv", "horímetro"]):
        return [
            "⚙️ <b>CONSERVAÇÃO:</b> Equipamento revisado, mecânica forte e pronto para ir direto pro trabalho!",
            "🚜 <b>OPORTUNIDADE:</b> Investimento com retorno imediato para a operação da fazenda!",
            "🔨 <b>FECHAMENTO:</b> Preço de ocasião para máquina desse porte!"
        ]
    elif any(k in txt for k in ["cavalo", "égua", "egua", "potro", "mangalarga", "quarto de milha", "marcha"]):
        return [
            "🐴 <b>MORFOLOGIA E MARCHA:</b> Animal de selar impecável, aprumos corretos e ótimo temperamento!",
            "🏆 <b>PEDIGREE:</b> Sanguíneo fechado em campeões de pista, papel de destaque!",
            "🔨 <b>FECHAMENTO:</b> Prontidão total para dar show na pista ou valorizar a tropa!"
        ]
    elif any(k in txt for k in ["leite", "lactação", "girolando", "holandês", "úbere"]):
        return [
            "🥛 <b>PRODUÇÃO:</b> Sistema mamário impecável e alta persistência de lactação!",
            "🧬 <b>GENÉTICA LEITEIRA:</b> Matriz para colocar balde cheio e alavancar a produção!",
            "🔨 <b>FECHAMENTO:</b> Fêmea que se paga no leite, oportunidade certa para o produtor!"
        ]
    else:
        return [
            "OB <b>MORFOLOGIA:</b> Garupa larga, carcaça coberta, costelas bem arqueadas e selo de raça!",
            "🧬 <b>GENÉTICA:</b> Linhagem consagrada para chancelar a cabeceira do rebanho!",
            "🔨 <b>FECHAMENTO:</b> Avaliação genética impecável, oportunidade que não sobra na pista!"
        ]

# 1. MENU LATERAL
st.sidebar.header("📂 Arquivos do Leilão")
file_oe = st.sidebar.file_uploader("1. Ordem de Entrada (O.E.)", type="pdf")
file_cat = st.sidebar.file_uploader("2. Catálogo do Leilão", type="pdf")

texto_oe = processar_pdf(file_oe)
texto_cat = processar_pdf(file_cat)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Sequência dos Lotes")
modo_ordenacao = st.sidebar.radio(
    "Ordenar exibição por:",
    ["Ordem da Ordem de Entrada (1º, 2º...)", "Ordem Numérica (01, 02, 03...)"]
)

# LISTAGEM DE LOTES
lotes_detectados = set()
for p in texto_oe + texto_cat:
    encontrados = re.findall(r"\b(?:LOTE|LT)?\s*(\d{1,3})\b", p, re.IGNORECASE)
    for l in encontrados:
        if 1 <= int(l) <= 200:
            lotes_detectados.add(f"{int(l):02d}")

lista_lotes = sorted(list(lotes_detectados), key=lambda x: int(x)) if lotes_detectados else [f"{i:02d}" for i in range(1, 51)]

if 'lote_idx' not in st.session_state or st.session_state.lote_idx >= len(lista_lotes):
    st.session_state.lote_idx = 0

# 2. NAVEGAÇÃO SUPERIOR
col_prev, col_select, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("◀️ LOTE ANTERIOR", use_container_width=True):
        st.session_state.lote_idx = max(0, st.session_state.lote_idx - 1)

with col_next:
    if st.button("PRÓXIMO LOTE ▶️", use_container_width=True):
        st.session_state.lote_idx = min(len(lista_lotes) - 1, st.session_state.lote_idx + 1)

with col_select:
    lote_selecionado = st.selectbox(
        "Ir Direto ao Lote:", 
        options=lista_lotes, 
        index=st.session_state.lote_idx,
        key="select_lote_box"
    )
    st.session_state.lote_idx = lista_lotes.index(lote_selecionado)

num_lote = lista_lotes[st.session_state.lote_idx]

st.markdown("---")

# 3. PAINEL PRINCIPAL DE PISTA (AMPLIADO)
col_lote, col_info = st.columns([1, 3])

with col_lote:
    st.markdown(f"<p class='big-lote'>LOTE<br>{num_lote}</p>", unsafe_allow_html=True)

with col_info:
    texto_acumulado = ""

    # A) EXIBIÇÃO FORMATADA DA O.E.
    dados_oe = buscar_dados_oe_exatos(texto_oe, num_lote)
    
    if dados_oe:
        texto_acumulado += f"{dados_oe['categoria']} {dados_oe['produto']}"
        
        st.markdown(f"""
        <div class='card-oe'>
            <span class='texto-pista' style='font-size:18px;'>📋 DADOS DA ORDEM DE ENTRADA</span><br><br>
            <span class='texto-pista'>• Posição na Pista:</span> {dados_oe['posicao']} A ENTRAR<br>
            <span class='texto-pista'>• Animal / Produto:</span> {dados_oe['produto']}<br>
            <span class='texto-pista'>• Categoria:</span> {dados_oe['categoria']}<br>
            <span class='texto-pista'>• Peso:</span> {dados_oe['peso']} &nbsp;|&nbsp; <span class='texto-pista'>Idade:</span> {dados_oe['idade']} &nbsp;|&nbsp; <span class='texto-pista'>Qtd:</span> {dados_oe['qtd']}<br>
            <span class='texto-pista'>• Vendedor:</span> {dados_oe['vendedor']}
        </div>
        """, unsafe_allow_html=True)

    # B) BUSCA NO CATÁLOGO (PEDIGREE)
    bloco_cat = []
    if texto_cat:
        for p in texto_cat:
            linhas = p.split('\n')
            for i, l in enumerate(linhas):
                if re.search(rf"\b(lote|lt)?\s*0*{int(num_lote)}\b", l, re.IGNORECASE):
                    inicio = max(0, i - 2)
                    fim = min(len(linhas), i + 14)
                    bloco_cat = linhas[inicio:fim]
                    texto_acumulado += " ".join(bloco_cat)
                    break
            if bloco_cat:
                break

    if bloco_cat:
        st.markdown(f"<div class='card-lote'><span class='texto-pista'>📌 PEDIGREE DO CATÁLOGO — LOTE {num_lote}</span></div>", unsafe_allow_html=True)
        
        esquerdas, direitas = [], []
        for l in bloco_cat:
            if len(l) > 40:
                col_e, col_d = l[:40].strip(), l[40:].strip()
                if col_e: esquerdas.append(col_e)
                if col_d: direitas.append(col_d)
            else:
                if l.strip(): esquerdas.append(l.strip())

        col_p, col_m = st.columns(2)
        with col_p:
            st.markdown("<div class='card-pai'><span class='texto-pista'>🟦 LINHA PATERNA (ESQUERDA)</span></div>", unsafe_allow_html=True)
            for item in esquerdas[:5]:
                st.markdown(f"<p class='texto-pista'>• {item}</p>", unsafe_allow_html=True)

        with col_m:
            st.markdown("<div class='card-mae'><span class='texto-pista'>🟥 LINHA MATERNA (DIREITA)</span></div>", unsafe_allow_html=True)
            for item in direitas[:5]:
                st.markdown(f"<p class='texto-pista'>• {item}</p>", unsafe_allow_html=True)

    # C) GATILHOS AUTOMÁTICOS
    gatilhos = gerar_gatilhos_categoria(texto_acumulado)
    st.markdown("---")
    st.markdown("### 🎙️ Gatilhos para o Microfone")
    for g in gatilhos:
        st.markdown(f"<div class='card-jargao'><span class='texto-pista'>{g}</span></div>", unsafe_allow_html=True)
