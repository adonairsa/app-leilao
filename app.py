
Clique em "VER DEBUG" na sidebar para verificar
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
info_cat_lote = catalogo_info.get(num_lote, {})

# ==================== PAINEL PRINCIPAL ====================
st.markdown(f"""
<div class="lote-destaque">
🐂 LOTE {num_lote}
<br>
<span style="font-size: 24px;">{dados_lote.get('posicao', f'{st.session_state.lote_idx + 1}º')} A ENTRAR</span>
</div>
""", unsafe_allow_html=True)

if dados_lote:
# Informações principais
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📋 DADOS DO ANIMAL")
    st.markdown(f"""
    <div class="animal-info">
        <strong>🏷️ CATEGORIA:</strong><br>{dados_lote.get("categoria", "-")}<br><br>
        <strong>🐾 RAÇA:</strong><br>{dados_lote.get("raca", "-")}
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### ⚖️ CARACTERÍSTICAS")
    st.markdown(f"""
    <div class="animal-info">
        <strong>⚖️ PESO:</strong><br>{dados_lote.get("peso", "-")}<br><br>
        <strong>📅 IDADE:</strong><br>{dados_lote.get("idade", "-")}
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("### 📦 QUANTIDADE")
    st.markdown(f"""
    <div class="animal-info">
        <strong>🔢 QTD:</strong><br>{dados_lote.get("qtd", "-")}<br><br>
        <strong>👨‍🌾 VENDEDOR:</strong><br>{dados_lote.get("vendedor", "-")}
    </div>
    """, unsafe_allow_html=True)

# Produto/Animal
if dados_lote.get("produto"):
    st.markdown("### 🐄 PRODUTO/ANIMAL")
    st.markdown(f"""
    <div class="animal-info">
        {dados_lote["produto"]}
    </div>
    """, unsafe_allow_html=True)

# Informações do Catálogo
if info_cat_lote:
    st.markdown("### 📚 PEDIGREE DO CATÁLOGO")
    
    if info_cat_lote.get("nomes_destaque"):
        st.markdown("**🧬 LINHAGEM:**")
        for nome in info_cat_lote["nomes_destaque"][:6]:
            st.markdown(f"""
            <div class="pedigree-box">
                {nome}
            </div>
            """, unsafe_allow_html=True)
    
    if info_cat_lote.get("bloco_completo"):
        with st.expander("📖 Ver pedigree completo"):
            for texto in info_cat_lote["bloco_completo"]:
                st.write(f"• {texto}")

# Linha completa da O.E.
with st.expander("📄 Ver linha completa da O.E."):
    st.code(dados_lote.get("linha_completa", "-"))

# Gatilhos
st.markdown("### 🎤 GATILHOS PARA CANTAR")
gatilhos = gerar_gatilhos(dados_lote, info_cat_lote)

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
