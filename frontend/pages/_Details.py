import streamlit as st

st.set_page_config(initial_sidebar_state="expanded")


# Verificar se pode acessar details
if "show_details" not in st.session_state or not st.session_state["show_details"]:
    st.warning("Você precisa selecionar um vinho primeiro.")
    st.stop()


# Caminho para uma imagem padrão de vinho
DEFAULT_WINE_IMAGE = "https://static.vecteezy.com/system/resources/previews/024/628/614/original/wine-bottle-and-glass-with-a-transparent-background-png.png"

st.title("🍷 Detalhes do Vinho")

# Verificar se os resultados e o vinho selecionado estão na sessão
if "wine_results" not in st.session_state or "selected_wine_id" not in st.session_state:
    st.warning("Nenhum vinho selecionado. Por favor, retorne à página de resultados.")
    st.stop()

# Filtrar o vinho específico
vinho = st.session_state["wine_results"][
    st.session_state["wine_results"]["id"] == st.session_state["selected_wine_id"]
].iloc[0]

# Informações básicas
st.header(vinho["product_name"])

col1, col2 = st.columns(2)

with col1:
    # Usar imagem padrão se não houver URL ou se a URL estiver vazia
    image_url = vinho.get("image_url", DEFAULT_WINE_IMAGE) or DEFAULT_WINE_IMAGE
    st.image(image_url, use_container_width=True)

with col2:
    st.write(f"**🍇 Uva:** {vinho['technical_sheet_grapes']}")
    st.write(f"**⭐ Tipo do Vinho:** {vinho['technical_sheet_wine_type']}")
    st.write(f"**🧀 Harmoniza Com:** {vinho['harmonizes_with']}")
    st.write(f"**🌍 País:** {vinho['technical_sheet_country']}")
    st.write(f"**🏺 Safra:** {vinho.get('technical_sheet_year', 'Não informado')}")

# Descrição detalhada
st.subheader("Descrição")
st.write(vinho.get("description", "Descrição não disponível"))

# Informações técnicas
st.subheader("Informações Técnicas")
st.write(
    f"**Teor Alcoólico:** {vinho.get('technical_sheet_alcohol', 'Não informado')}%"
)
st.write(
    f"**Temperatura de Serviço:** {vinho.get('technical_sheet_service_temperature', 'Não informado')}°C"
)

# Harmonização
st.subheader("Harmonização")
st.write(vinho.get("harmonizes_with", "Sugestões não disponíveis"))

# Links para navegar
col1, col2 = st.columns(2)

with col1:
    if st.button("Voltar para Resultados"):
        st.switch_page("pages/_Results.py")

with col2:
    # Criar subitens para outros vinhos
    if "wine_results" in st.session_state:
        outros_vinhos = st.session_state["wine_results"][
            st.session_state["wine_results"]["id"] != vinho["id"]
        ]

        selecao = st.selectbox(
            "Outros Vinhos",
            outros_vinhos["product_name"].tolist(),
            key="outros_vinhos_select",
        )

        if selecao:
            selected_wine = outros_vinhos[
                outros_vinhos["product_name"] == selecao
            ].iloc[0]
            if st.button("Ir para este vinho"):
                st.session_state["selected_wine_id"] = selected_wine["id"]
                st.experimental_rerun()
