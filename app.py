import streamlit as st
import json
import os
from datetime import datetime
from orchestrator import run_agent

# ============================================================
# app.py — Interface Streamlit
# WearWise AI — Smart Closet & Anti-Regret Visual Shopping Agent
#
# Objectif :
# - Interface moderne et professionnelle
# - Historique persistant avec conversations.json
# - Garde-robe persistante avec wardrobe.json
# - Affichage des réponses en blocs visuels
# - Préparation Visual Outfit Preview
# - Garder le backend existant sans le casser
# ============================================================


# ============================================================
# 0. FICHIERS DE SAUVEGARDE
# ============================================================

CONVERSATION_FILE = "conversations.json"
WARDROBE_FILE = "wardrobe.json"


# ============================================================
# 1. FONCTIONS — HISTORIQUE conversations.json
# ============================================================

def load_messages_from_file():
    """
    Charge les messages sauvegardés depuis conversations.json.
    Si le fichier n'existe pas, retourne une liste vide.
    """

    if not os.path.exists(CONVERSATION_FILE):
        return []

    try:
        with open(CONVERSATION_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict) and "messages" in data:
            return data["messages"]

        if isinstance(data, list):
            return data

        return []

    except json.JSONDecodeError:
        return []


def save_conversations(messages):
    """
    Sauvegarde les messages dans conversations.json.
    """

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": messages
    }

    with open(CONVERSATION_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def clear_conversation_file():
    """
    Vide conversations.json.
    """

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }

    with open(CONVERSATION_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# ============================================================
# 2. FONCTIONS — GARDE-ROBE wardrobe.json
# ============================================================

def parse_wardrobe_text(wardrobe_text):
    """
    Transforme le texte de garde-robe en liste propre.

    Exemple :
    "chemise blanche, pantalon noir"

    devient :
    ["chemise blanche", "pantalon noir"]
    """

    if not wardrobe_text:
        return []

    raw_items = wardrobe_text.replace("\n", ",").split(",")
    items = []

    for item in raw_items:
        cleaned = item.strip().lower()

        if cleaned:
            items.append(cleaned)

    return items


def load_wardrobe_from_file():
    """
    Charge la garde-robe depuis wardrobe.json.
    Retourne un texte simple utilisable dans le text_area.
    """

    if not os.path.exists(WARDROBE_FILE):
        return ""

    try:
        with open(WARDROBE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            items = data.get("items", [])

            if isinstance(items, list):
                return ", ".join(items)

        return ""

    except json.JSONDecodeError:
        return ""


def save_wardrobe_to_file(wardrobe_text):
    """
    Sauvegarde la garde-robe dans wardrobe.json.
    """

    items = parse_wardrobe_text(wardrobe_text)

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items
    }

    with open(WARDROBE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def clear_wardrobe_file():
    """
    Vide wardrobe.json.
    """

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": []
    }

    with open(WARDROBE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# ============================================================
# 3. FONCTIONS D'AFFICHAGE
# ============================================================

def render_markdown(content):
    """
    Affiche le markdown avec de bons retours à la ligne.
    """

    if not content:
        return

    st.markdown(content.replace("\n", "  \n"))


def split_agent_response(content):
    """
    Découpe une réponse de l'agent selon les titres markdown ###.

    Exemple :
    ### Résumé intelligent
    ...
    ### Tenue complète
    ...

    devient une liste de sections :
    [
        {"title": "Résumé intelligent", "body": "..."},
        {"title": "Tenue complète", "body": "..."}
    ]
    """

    if not content:
        return []

    sections = []
    current_title = "Réponse"
    current_body = []

    for line in content.splitlines():
        if line.startswith("### "):
            if current_body:
                sections.append({
                    "title": current_title,
                    "body": "\n".join(current_body).strip()
                })

            current_title = line.replace("### ", "").strip()
            current_body = []
        else:
            current_body.append(line)

    if current_body:
        sections.append({
            "title": current_title,
            "body": "\n".join(current_body).strip()
        })

    return sections


def section_icon(title):
    """
    Donne une icône selon le titre de section.
    """

    title_lower = title.lower()

    if "résumé" in title_lower or "raisonnement" in title_lower:
        return "🧠"

    if "wardrobe" in title_lower or "garde" in title_lower:
        return "👗"

    if "gap" in title_lower or "pièces" in title_lower:
        return "🎯"

    if "produits" in title_lower or "choix" in title_lower:
        return "🛍️"

    if "style" in title_lower:
        return "💡"

    if "tenue" in title_lower:
        return "👔"

    if "option" in title_lower:
        return "✨"

    if "offres" in title_lower or "deal" in title_lower:
        return "🔥"

    if "décision" in title_lower:
        return "✅"

    return "📌"


def render_agent_blocks(content, compact_mode=True):
    """
    Affiche la réponse de l'agent en blocs visuels.
    Cela évite un long texte encombré.
    """

    sections = split_agent_response(content)

    if not sections:
        render_markdown(content)
        return

    for index, section in enumerate(sections):
        title = section["title"]
        body = section["body"]
        icon = section_icon(title)

        # Les premières sections importantes restent ouvertes.
        # Les sections longues sont en expander pour éviter l'encombrement.
        expanded = index == 0 or "tenue" in title.lower() or "produits" in title.lower()

        if compact_mode:
            with st.expander(f"{icon} {title}", expanded=expanded):
                render_markdown(body)
        else:
            st.markdown(
                f"""
                <div class="response-card">
                    <div class="response-card-title">{icon} {title}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            render_markdown(body)


def safe_run_agent(message, closet_items):
    """
    Appelle run_agent avec closet_items si orchestrator.py le supporte.
    Sinon, garde l'ancien comportement run_agent(message).
    """

    try:
        return run_agent(message, closet_items=closet_items)
    except TypeError:
        return run_agent(message)


# ============================================================
# 4. CONFIGURATION DE LA PAGE
# ============================================================

st.set_page_config(
    page_title="WearWise AI",
    page_icon="🛍️",
    layout="wide"
)


# ============================================================
# 5. STYLE CSS — DESIGN PREMIUM EN BLOCS
# ============================================================

st.markdown(
    """
    <style>
    /* =====================================================
       GLOBAL
    ===================================================== */

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(192, 132, 252, 0.22), transparent 27%),
            radial-gradient(circle at top right, rgba(244, 114, 182, 0.18), transparent 28%),
            radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.10), transparent 28%),
            linear-gradient(135deg, #020617 0%, #0F172A 48%, #111827 100%);
        color: #F8FAFC;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1550px;
    }

    h1, h2, h3, h4 {
        color: #F8FAFC !important;
        font-weight: 850 !important;
        letter-spacing: -0.02em;
    }

    p, div, span, label {
        color: #E2E8F0;
    }

    hr {
        border-color: rgba(255,255,255,0.12);
    }

    /* =====================================================
       HERO
    ===================================================== */

    .wearwise-hero {
        background:
            linear-gradient(135deg, rgba(30, 41, 59, 0.97), rgba(76, 29, 149, 0.92), rgba(131, 24, 67, 0.92));
        padding: 34px 38px;
        border-radius: 30px;
        margin-bottom: 28px;
        border: 1px solid rgba(255,255,255,0.16);
        box-shadow: 0 28px 70px rgba(0,0,0,0.42);
        position: relative;
        overflow: hidden;
    }

    .wearwise-hero:before {
        content: "";
        position: absolute;
        width: 300px;
        height: 300px;
        right: -100px;
        top: -120px;
        background: radial-gradient(circle, rgba(255,255,255,0.24), transparent 65%);
    }

    .wearwise-title {
        font-size: 50px;
        font-weight: 950;
        color: #FFFFFF;
        margin-bottom: 12px;
        line-height: 1.05;
    }

    .wearwise-subtitle {
        font-size: 18px;
        line-height: 1.7;
        color: #EDE9FE;
        max-width: 980px;
    }

    .hero-badge {
        display: inline-block;
        margin-top: 18px;
        margin-right: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        color: #FFFFFF;
        font-size: 13px;
        font-weight: 700;
    }

    /* =====================================================
       SIDEBAR
    ===================================================== */

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #0B1120 100%);
        border-right: 1px solid rgba(255,255,255,0.10);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #CBD5E1 !important;
    }

    textarea {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border-radius: 16px !important;
        border: 1px solid rgba(192,132,252,0.55) !important;
    }

    textarea::placeholder {
        color: #64748B !important;
    }

    /* =====================================================
       CARDS
    ===================================================== */

    .feature-card {
        background: linear-gradient(145deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98));
        padding: 22px;
        border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 16px;
        box-shadow: 0 16px 36px rgba(0,0,0,0.28);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .feature-card:hover {
        transform: translateY(-2px);
        border-color: rgba(192,132,252,0.55);
    }

    .feature-title {
        font-size: 20px;
        font-weight: 850;
        color: #FFFFFF;
        margin-bottom: 10px;
    }

    .feature-text {
        font-size: 15px;
        line-height: 1.65;
        color: #CBD5E1;
    }

    .mini-stat {
        background: rgba(15,23,42,0.78);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 16px;
        margin-bottom: 14px;
    }

    .mini-stat-title {
        color: #F8FAFC;
        font-weight: 800;
        font-size: 16px;
        margin-bottom: 6px;
    }

    .mini-stat-text {
        color: #CBD5E1;
        font-size: 14px;
        line-height: 1.55;
    }

    .small-badge {
        display: inline-block;
        padding: 7px 12px;
        margin: 5px 5px 5px 0;
        border-radius: 999px;
        background: rgba(192, 132, 252, 0.18);
        color: #F3E8FF;
        font-size: 13px;
        font-weight: 700;
        border: 1px solid rgba(192, 132, 252, 0.36);
    }

    .response-card {
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 14px 16px;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    .response-card-title {
        color: #FFFFFF;
        font-weight: 850;
        font-size: 17px;
    }

    /* =====================================================
       BUTTONS
    ===================================================== */

    .stButton > button {
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        background: linear-gradient(135deg, #1E293B, #111827) !important;
        color: #F8FAFC !important;
        padding: 0.72rem 1.1rem !important;
        font-weight: 750 !important;
        box-shadow: 0 10px 22px rgba(0,0,0,0.22);
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: #C084FC !important;
        background: linear-gradient(135deg, #312E81, #831843) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }

    /* =====================================================
       CHAT
    ===================================================== */

    .stChatMessage {
        background: rgba(15,23,42,0.74) !important;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 22px !important;
        padding: 14px !important;
        box-shadow: 0 12px 24px rgba(0,0,0,0.18);
    }

    div[data-testid="stChatInput"] {
        background: rgba(15,23,42,0.95);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.10);
    }

    input {
        color: #0F172A !important;
    }

    /* =====================================================
       EXPANDERS
    ===================================================== */

    details {
        background: rgba(15,23,42,0.55) !important;
        border-radius: 18px !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        margin-bottom: 10px;
    }

    summary {
        color: #F8FAFC !important;
        font-weight: 800 !important;
    }

    /* =====================================================
       STREAMLIT FIXES
    ===================================================== */

    .stMarkdown, .stText, .stCaption {
        color: #E2E8F0 !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.12);
    }

    .stSuccess, .stInfo, .stWarning {
        border-radius: 16px !important;
    }

    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        color: #F8FAFC !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 6. INITIALISATION SESSION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = load_messages_from_file()

if "closet_items" not in st.session_state:
    st.session_state.closet_items = load_wardrobe_from_file()

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "compact_mode" not in st.session_state:
    st.session_state.compact_mode = True


# ============================================================
# 7. SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🛍️ WearWise AI")
    st.caption("Smart Closet & Anti-Regret Visual Shopping Agent")

    st.markdown("---")

    st.markdown("### 👗 Ma garde-robe")

    st.session_state.closet_items = st.text_area(
        "Ajoute les pièces que tu possèdes déjà",
        value=st.session_state.closet_items,
        placeholder="Exemple : chemise blanche, pantalon noir, baskets blanches",
        height=135
    )

    wardrobe_items = parse_wardrobe_text(st.session_state.closet_items)

    if wardrobe_items:
        st.success(f"{len(wardrobe_items)} pièce(s) détectée(s)")
    else:
        st.info("Ajoute quelques pièces pour activer le Wardrobe Twin.")

    col_save, col_clear = st.columns(2)

    with col_save:
        if st.button("💾 Save closet"):
            save_wardrobe_to_file(st.session_state.closet_items)
            st.success("Garde-robe sauvegardée")

    with col_clear:
        if st.button("🧹 Clear closet"):
            st.session_state.closet_items = ""
            clear_wardrobe_file()
            st.rerun()

    st.markdown("---")

    st.markdown("### ⚙️ Affichage")
    st.session_state.compact_mode = st.toggle(
        "Mode compact par blocs",
        value=st.session_state.compact_mode
    )

    st.markdown("---")

    st.markdown("### ⚡ Actions")

    if st.button("🧹 Effacer la conversation"):
        st.session_state.messages = []
        clear_conversation_file()
        st.rerun()

    if st.button("💾 Sauvegarder l’historique"):
        save_conversations(st.session_state.messages)
        st.success("Historique sauvegardé")

    st.markdown("---")

    st.markdown("### ✨ Innovations")
    st.markdown(
        """
        <span class="small-badge">🧠 Wardrobe Twin</span>
        <span class="small-badge">🎯 Gap Analyzer</span>
        <span class="small-badge">🖼️ Visual Preview</span>
        <span class="small-badge">😌 Anti-Regret</span>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 8. HEADER
# ============================================================

st.markdown(
    """
    <div class="wearwise-hero">
        <div class="wearwise-title">WearWise AI</div>
        <div class="wearwise-subtitle">
            Un agent IA de shopping mode qui analyse ton budget, ton style,
            l’occasion et ta garde-robe pour recommander des achats utiles,
            visuels, responsables et anti-regret.
        </div>
        <div>
            <span class="hero-badge">🧠 Smart Closet</span>
            <span class="hero-badge">🎯 Gap Analyzer</span>
            <span class="hero-badge">🖼️ Visual Shopping</span>
            <span class="hero-badge">😌 Anti-Regret</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 9. LAYOUT PRINCIPAL
# ============================================================

left_col, right_col = st.columns([2, 1])


# ============================================================
# 10. COLONNE GAUCHE — CHAT
# ============================================================

with left_col:
    st.markdown("### 💬 Chat avec l’agent")
    st.caption("Les réponses sont affichées en blocs pour éviter un long texte encombré.")

    st.markdown("#### Suggestions rapides")

    s1, s2, s3 = st.columns(3)

    with s1:
        if st.button("🎓 Soutenance 150 DT"):
            st.session_state.pending_prompt = "je veux une tenue complete pour une soutenance femme 150dt"

    with s2:
        if st.button("💍 Mariage 250 DT"):
            st.session_state.pending_prompt = "je veux une tenue complete pour un mariage femme 250dt"

    with s3:
        if st.button("💼 Travail homme 200 DT"):
            st.session_state.pending_prompt = "je veux une tenue complete pour le travail homme 200dt"

    s4, s5, s6 = st.columns(3)

    with s4:
        if st.button("👟 Sneakers sport"):
            st.session_state.pending_prompt = "je cherche des sneakers sport homme 120dt"

    with s5:
        if st.button("👜 Sac noir chic"):
            st.session_state.pending_prompt = "trouve moi un sac noir chic pour femme"

    with s6:
        if st.button("💸 Petit budget"):
            st.session_state.pending_prompt = "tenue casual homme 80dt"

    st.markdown("---")

    # Affichage historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_agent_blocks(
                    msg["content"],
                    compact_mode=st.session_state.compact_mode
                )
            else:
                render_markdown(msg["content"])

    # Input utilisateur
    user_input = st.chat_input("Décris ta tenue ou ton produit : ex. tenue chic femme 150dt")

    message = st.session_state.pending_prompt or user_input
    st.session_state.pending_prompt = None

    if message:
        # Sauvegarder automatiquement la garde-robe actuelle
        save_wardrobe_to_file(st.session_state.closet_items)

        # Ajouter message utilisateur
        st.session_state.messages.append({
            "role": "user",
            "content": message
        })

        save_conversations(st.session_state.messages)

        # Afficher utilisateur
        with st.chat_message("user"):
            render_markdown(message)

        # Générer réponse agent
        with st.chat_message("assistant"):
            with st.spinner("WearWise AI analyse ton style, ta garde-robe et le risque de regret..."):
                response = safe_run_agent(
                    message=message,
                    closet_items=st.session_state.closet_items
                )

            render_agent_blocks(
                response,
                compact_mode=st.session_state.compact_mode
            )

        # Sauvegarder assistant
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        save_conversations(st.session_state.messages)


# ============================================================
# 11. COLONNE DROITE — VISUAL PREVIEW
# ============================================================

with right_col:
    st.markdown("### 🖼️ Visual Outfit Preview")

    wardrobe_items = parse_wardrobe_text(st.session_state.closet_items)

    st.markdown(
        f"""
        <div class="mini-stat">
            <div class="mini-stat-title">🧠 Wardrobe Twin</div>
            <div class="mini-stat-text">
                Pièces détectées dans ta garde-robe : <b>{len(wardrobe_items)}</b><br>
                L’agent utilise ces pièces quand tu demandes une tenue complète.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-title">🎯 Closet Gap Analyzer</div>
            <div class="feature-text">
                Pour une tenue complète, l’agent compare ta garde-robe
                avec les pièces nécessaires selon l’occasion.
            </div>
        </div>

        <div class="feature-card">
            <div class="feature-title">😌 Anti-Regret Score</div>
            <div class="feature-text">
                L’agent vérifie si l’achat est utile, cohérent avec ton budget
                et s’il évite un achat regrettable.
            </div>
        </div>

        <div class="feature-card">
            <div class="feature-title">🛍️ Shopping Cards</div>
            <div class="feature-text">
                Prochaine amélioration : afficher les produits recommandés
                sous forme de cartes avec images, prix et score IA.
            </div>
        </div>

        <div class="feature-card">
            <div class="feature-title">👗 AI Lookboard</div>
            <div class="feature-text">
                Prochaine amélioration : générer un lookboard visuel avec
                les pièces proposées dans la tenue complète.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📌 Progression")
    st.progress(70)

    st.success("✅ Anti-Regret Analyzer")
    st.success("✅ Wardrobe Twin connecté")
    st.success("✅ Gap Analyzer connecté")
    st.info("🎨 Interface en blocs activée")
    st.warning("🖼️ Prochaine étape : vraies cartes produits avec images")