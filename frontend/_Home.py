import streamlit as st
import sys
import os
import warnings


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from backend.app.core.wine_recommender import WineRecommender


@st.cache_resource  # Isso fará com que o modelo seja carregado apenas uma vez e armazenado em cache
def carregar_modelo():
    warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
    caminho_modelo = "model/wine_recommender_model.pkl"
    if os.path.exists(caminho_modelo):
        return WineRecommender.carregar_modelo(caminho_modelo)
    else:
        st.error("Modelo não encontrado. Por favor, treine o modelo primeiro.")
        return None


st.set_page_config(initial_sidebar_state="collapsed")

modelo = carregar_modelo()

# Configurar estado inicial
if "first_access" not in st.session_state:
    st.session_state["first_access"] = True
    st.session_state["show_results"] = False
    st.session_state["show_details"] = False


st.write("# Bem vindo à primeira página")
st.write("# Quais dos elementos voce gosta num vinho?")

if modelo:

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

        # harmonizes_with =  st.selectbox(
        #   "Qual comida deseja harmonizar com o vinho?",
        #   ["Carnes de caça", "Carnes vermelhas", "Pizzas", "massas de molho vermelho", "Queijos", "Pratos apimentados", "Frutos do mar", "Risoto", "massas de molho branco", "Saladas", "aperitivos", "Carnes brancas", "Sobremesas"]
        # )

        harmonizes_with = st.text_input(
            label="Qual comida deseja harmonizar com o vinho?"
        )
        country = st.text_input(label="Qual país você gosta dos vinhos?")
        grapes = st.text_input(label="Qual uva você gosta?")

        user_input = {
            "fruit_tasting": fruit_tasting,
            "sugar_tasting": sugar_tasting,
            "acidity_tasting": acidity_tasting,
            "tannin_tasting": tannin_tasting,
            "harmonizes_with": harmonizes_with,
            "technical_sheet_country": country,
            "technical_sheet_grapes": grapes,
        }

        # Botão para submeter o formulário
        submitted = st.form_submit_button("Buscar vinhos")

    if submitted:

        st.session_state["params"] = {
            "fruit_tasting": fruit_tasting,
            "sugar_tasting": sugar_tasting,
            "acidity_tasting": acidity_tasting,
            "tannin_tasting": tannin_tasting,
            "harmonizes_with": harmonizes_with,
            "country": country,
            "grapes": grapes,
        }
        recomendacao = modelo.recommend_wines(st.session_state["params"])
        st.session_state["first_access"] = False
        st.session_state["show_results"] = True
        st.switch_page("pages/_results.py")
