# ============================================================
#  app_flask.py — Backend Flask
#  Agent IA de Shopping Intelligent
# ============================================================

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os

from orchestrator import run_agent
from database import (
    sign_in, sign_up,
    create_session, get_sessions, delete_session,
    save_message, get_messages,
    # Wardrobe
    add_wardrobe_item, get_wardrobe_items,
    delete_wardrobe_item, get_wardrobe_as_text
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stylist-ai-secret-2024")
app.config["JSON_AS_ASCII"] = False
CORS(app)


# ============================================================
#  PAGE PRINCIPALE
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
#  AUTH
# ============================================================

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data     = request.json
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis."}), 400
    if len(password) < 6:
        return jsonify({"error": "Mot de passe trop court (min. 6 caractères)."}), 400

    user_id, error = sign_up(email, password)
    if error:
        return jsonify({"error": error}), 400

    session["user_id"]    = user_id
    session["user_email"] = email
    return jsonify({"user_id": user_id, "email": email})


@app.route("/api/login", methods=["POST"])
def api_login():
    data     = request.json
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    user_id, error = sign_in(email, password)
    if error:
        return jsonify({"error": error}), 401

    session["user_id"]    = user_id
    session["user_email"] = email
    return jsonify({"user_id": user_id, "email": email})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me")
def api_me():
    if "user_id" not in session:
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in": True,
        "user_id":   session["user_id"],
        "email":     session["user_email"]
    })


# ============================================================
#  SESSIONS DE CHAT
# ============================================================

@app.route("/api/sessions")
def api_sessions():
    if "user_id" not in session:
        return jsonify([])
    return jsonify(get_sessions(session["user_id"]))


@app.route("/api/sessions", methods=["POST"])
def api_create_session():
    if "user_id" not in session:
        return jsonify({"error": "Non connecté"}), 401

    title      = request.json.get("title", "Conversation")
    session_id = create_session(session["user_id"], title)
    return jsonify({"session_id": session_id})


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def api_delete_session(session_id):
    if "user_id" not in session:
        return jsonify({"error": "Non connecté"}), 401

    delete_session(session_id, session["user_id"])
    return jsonify({"ok": True})


@app.route("/api/sessions/<session_id>/messages")
def api_messages(session_id):
    if "user_id" not in session:
        return jsonify([])
    return jsonify(get_messages(session_id))


# ============================================================
#  CHAT — envoyer un message
# ============================================================

@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user_id" not in session:
        return jsonify({"error": "Non connecté"}), 401

    data       = request.json
    user_msg   = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not user_msg:
        return jsonify({"error": "Message vide"}), 400

    # Créer session si besoin
    if not session_id:
        session_id = create_session(session["user_id"], user_msg)

    # Sauvegarder message user
    save_message(session_id, "user", user_msg)

    # Récupérer la garde-robe structurée de l'utilisateur
    wardrobe_items = get_wardrobe_items(session["user_id"])

    # Appel agent avec les dicts structurés (genre + style exploitables directement)
    response = run_agent(user_msg, closet_items=wardrobe_items if wardrobe_items else None)

    if isinstance(response, dict):
        text       = response.get("text", "")
        image_url  = response.get("image_url") or ""
        image_data = response.get("image") or ""
    else:
        text       = response
        image_url  = ""
        image_data = ""

    # Sauvegarder la réponse avec l'URL uniquement
    save_message(session_id, "assistant", text, image_url)

    return jsonify({
        "session_id": session_id,
        "text":       text,
        "image_url":  image_url,
        "image":      image_data
    })


# ============================================================
#  WARDROBE
# ============================================================

@app.route("/api/wardrobe", methods=["GET"])
def api_get_wardrobe():
    if "user_id" not in session:
        return jsonify({"error": "Non connecté"}), 401
    return jsonify(get_wardrobe_items(session["user_id"]))


@app.route("/api/wardrobe", methods=["POST"])
def api_add_wardrobe():
    if "user_id" not in session:
        return jsonify({"error": "Non connecté"}), 401

    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Nom du vêtement requis."}), 400

    item_id, error = add_wardrobe_item(
        user_id      = session["user_id"],
        name         = name,
        category     = data.get("category", "autre"),
        color        = data.get("color", ""),
        brand        = data.get("brand", ""),
        size         = data.get("size", ""),
        notes        = data.get("notes", ""),
        genre        = data.get("genre", "unisex"),
        style        = data.get("style", "casual"),
        use_in_outfit= bool(data.get("use_in_outfit", True)),
    )
    if error:
        return jsonify({"error": error}), 500

    return jsonify({"id": item_id, "ok": True})


@app.route("/api/wardrobe/<item_id>", methods=["DELETE"])
def api_delete_wardrobe(item_id):
    if "user_id" not in session:
        return jsonify({"error": "Non connecté"}), 401

    delete_wardrobe_item(item_id, session["user_id"])
    return jsonify({"ok": True})


# ============================================================
#  LANCEMENT
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)