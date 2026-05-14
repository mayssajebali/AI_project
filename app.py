import streamlit as st
from orchestrator import run_agent

# ---------------------------------------------------
# Configuration page
# ---------------------------------------------------

st.set_page_config(
    page_title="Agent IA Shopping",
    page_icon="🛍️",
    layout="centered"
)

# ---------------------------------------------------
# Titre
# ---------------------------------------------------

st.title("🛍️ Agent IA de Shopping Intelligent")
st.write("Décris la tenue ou le produit que tu recherches.")

# ---------------------------------------------------
# Historique chat
# ---------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------
# Input utilisateur
# ---------------------------------------------------

message = st.chat_input("Exemple : tenue chic femme 150dt")

if message:

    # Ajouter message utilisateur
    st.session_state.messages.append({
        "role": "user",
        "content": message
    })

    # Affichage user
    with st.chat_message("user"):
        st.markdown(message)

    # Réponse agent
    response = run_agent(message)

    # Affichage assistant
    with st.chat_message("assistant"):
        st.markdown(response)

    # Sauvegarder réponse
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })