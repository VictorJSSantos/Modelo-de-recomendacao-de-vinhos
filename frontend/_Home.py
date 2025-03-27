import streamlit as st

st.set_page_config(initial_sidebar_state="collapsed")


# Configurar estado inicial
if "first_access" not in st.session_state:
    st.session_state["first_access"] = True
    st.session_state["show_results"] = False
    st.session_state["show_details"] = False

st.write("# Bem vindo à primeira página")
st.write("# Quais dos elementos voce gosta num vinho?")

with st.form("wine_form"):
    fruit_tasting = st.slider(
        label="Nível de fruta no gosto",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
    )

    sugar_tasting = st.slider(
        "Nível de açúcar no gosto",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
    )

    acidity_tasting = st.slider(
        "Nível de acidez no gosto",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
    )

    tannin_tasting = st.slider(
        "Nível de tanino no gosto",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
    )

    country = st.text_input(label="Qual país você gosta dos vinhos?")
    grapes = st.text_input(label="Qual uva você gosta?")

    # Botão para submeter o formulário
    submitted = st.form_submit_button("Buscar vinhos")

if submitted:
    st.session_state["params"] = {
        "fruit_tasting": fruit_tasting,
        "sugar_tasting": sugar_tasting,
        "acidity_tasting": acidity_tasting,
        "tannin_tasting": tannin_tasting,
        "country": country,
        "grapes": grapes,
    }
    st.session_state["first_access"] = False
    st.session_state["show_results"] = True
    st.switch_page("pages/_results.py")
