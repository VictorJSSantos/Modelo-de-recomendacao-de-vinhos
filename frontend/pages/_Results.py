import streamlit as st

st.set_page_config(initial_sidebar_state="expanded")


import os
import sys
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.wine_recommender import WineRecommender

# Verificar se pode acessar results
if "show_results" not in st.session_state or not st.session_state["show_results"]:
    st.warning("Você precisa preencher o formulário primeiro.")
    st.stop()

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🍷 Vinhos Recomendados ")

db = pd.read_csv("./data/db.csv")
recommender = WineRecommender(db)

recomendacoes = recommender.recommend_wines(
    input_features={
        "fruit_tasting": st.session_state["params"]["fruit_tasting"],
        "sugar_tasting": st.session_state["params"]["sugar_tasting"],
        "acidity_tasting": st.session_state["params"]["acidity_tasting"],
        "tannin_tasting": st.session_state["params"]["tannin_tasting"],
        "harmonizes_with": st.session_state["params"]["harmonizes_with"],
        "technical_sheet_country": st.session_state["params"]["country"],
        "technical_sheet_grapes": "Uvas variadas",
    }
)

results = supabase.table("wine_data").select("*").in_("id", recomendacoes).execute()
st.session_state["wine_results"] = pd.DataFrame(results.data)

# Habilitar detalhes
st.session_state["show_details"] = True

st.markdown("---")
for index, vinho in st.session_state["wine_results"].iterrows():
    with st.container():
        st.subheader(vinho["product_name"])
        st.write(f"🍇 Uva: {vinho['technical_sheet_grapes']}")
        st.write(f"🧀 Harmoniza Com: {vinho['harmonizes_with']}")
        st.write(f"⭐ Tipo do Vinho: {vinho['technical_sheet_wine_type']}")
        st.write(f"🌍 País: {vinho['technical_sheet_country']}")

        if st.button(
            f"Saber mais sobre {vinho['product_name']}", key=f"details_{vinho['id']}"
        ):
            st.session_state["selected_wine_id"] = vinho["id"]
            st.switch_page("pages/_Details.py")

        st.markdown("---")
