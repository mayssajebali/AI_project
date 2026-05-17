# ============================================================
#  database.py — Gestion MongoDB (Auth + Chat History + Wardrobe)
#  Agent IA de Shopping Intelligent
# ============================================================

import bcrypt
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId
import os

# ============================================================
#  CONNEXION
# ============================================================

MONGO_URI = "mongodb+srv://dbuser:dbuser101@fashionai.9e4i4pa.mongodb.net/?appName=FashionAI"

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client["shopping_agent"]


# ============================================================
#  AUTH
# ============================================================

def sign_up(email: str, password: str):
    db = get_db()
    try:
        if db.users.find_one({"email": email}):
            return None, "Cet email est déjà utilisé."
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        result = db.users.insert_one({
            "email": email,
            "password": hashed,
            "created_at": datetime.now(timezone.utc)
        })
        return str(result.inserted_id), None
    except Exception as e:
        return None, str(e)


def sign_in(email: str, password: str):
    db = get_db()
    try:
        user = db.users.find_one({"email": email})
        if not user:
            return None, "Email introuvable."
        if not bcrypt.checkpw(password.encode(), user["password"]):
            return None, "Mot de passe incorrect."
        return str(user["_id"]), None
    except Exception as e:
        return None, str(e)


# ============================================================
#  SESSIONS
# ============================================================

def create_session(user_id: str, title: str):
    db = get_db()
    try:
        result = db.chat_sessions.insert_one({
            "user_id": user_id,
            "title": title[:60],
            "created_at": datetime.now(timezone.utc)
        })
        return str(result.inserted_id)
    except Exception as e:
        print(f"[DB] Erreur create_session: {e}")
        return None


def get_sessions(user_id: str):
    db = get_db()
    try:
        sessions = db.chat_sessions.find({"user_id": user_id}).sort("created_at", -1).limit(50)
        return [{"id": str(s["_id"]), "title": s.get("title", "Conversation")} for s in sessions]
    except Exception as e:
        print(f"[DB] Erreur get_sessions: {e}")
        return []


def delete_session(session_id: str, user_id: str):
    db = get_db()
    try:
        db.messages.delete_many({"session_id": session_id})
        db.chat_sessions.delete_one({"_id": ObjectId(session_id), "user_id": user_id})
        return True
    except Exception as e:
        print(f"[DB] Erreur delete_session: {e}")
        return False


# ============================================================
#  MESSAGES
# ============================================================

def save_message(session_id: str, role: str, content: str, image_url: str = None):
    db = get_db()
    try:
        db.messages.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "image_url": image_url or "",
            "created_at": datetime.now(timezone.utc)
        })
        return True
    except Exception as e:
        print(f"[DB] Erreur save_message: {e}")
        return False


def get_messages(session_id: str):
    db = get_db()
    try:
        msgs = db.messages.find({"session_id": session_id}).sort("created_at", 1)
        return [{"role": m["role"], "content": m["content"], "image_url": m.get("image_url", "")} for m in msgs]
    except Exception as e:
        print(f"[DB] Erreur get_messages: {e}")
        return []


# ============================================================
#  WARDROBE  (nouvelle collection : wardrobe_items)
#
#  Chaque document :
#  {
#    user_id        : str,
#    name           : str,        # ex. "Robe noire Zara"
#    category       : str,        # haut | pantalon | robe | chaussures | sac | accessoire | autre
#    color          : str,        # ex. "noir"
#    brand          : str,        # ex. "Zara"
#    size           : str,        # ex. "M" / "38"
#    genre          : str,        # femme | homme | unisex
#    style          : str,        # casual | chic | sport | soiree | mariage | travail | boheme | autre
#    use_in_outfit  : bool,       # True = l'agent peut utiliser cette pièce dans la génération de tenue
#    notes          : str,        # remarques libres
#    created_at     : datetime
#  }
# ============================================================

WARDROBE_CATEGORIES = ["haut", "pantalon", "robe", "chaussures", "sac", "accessoire", "autre"]
WARDROBE_GENRES     = ["femme", "homme", "unisex"]
WARDROBE_STYLES     = ["casual", "chic", "sport", "soiree", "mariage", "travail", "boheme", "autre"]

def add_wardrobe_item(user_id: str, name: str, category: str,
                      color: str = "", brand: str = "",
                      size: str = "", notes: str = "",
                      genre: str ="", style: str="",
                      use_in_outfit: bool = True):
    db = get_db()
    try:
        if category not in WARDROBE_CATEGORIES:
            category = "autre"
        if genre not in WARDROBE_GENRES:
            genre = "unisex"
        if style not in WARDROBE_STYLES:
            style = "casual"
        result = db.wardrobe_items.insert_one({
            "user_id":       user_id,
            "name":          name.strip()[:100],
            "category":      category,
            "color":         color.strip()[:40],
            "brand":         brand.strip()[:60],
            "size":          size.strip()[:10],
            "genre":         genre,
            "style":         style,
            "use_in_outfit": bool(use_in_outfit),
            "notes":         notes.strip()[:200],
            "created_at":    datetime.now(timezone.utc)
        })
        return str(result.inserted_id), None
    except Exception as e:
        print(f"[DB] Erreur add_wardrobe_item: {e}")
        return None, str(e)


def get_wardrobe_items(user_id: str):
    db = get_db()
    try:
        items = db.wardrobe_items.find({"user_id": user_id}).sort("created_at", -1)
        return [
            {
                "id":           str(i["_id"]),
                "name":         i.get("name", ""),
                "category":     i.get("category", "autre"),
                "color":        i.get("color", ""),
                "brand":        i.get("brand", ""),
                "size":         i.get("size", ""),
                "genre":        i.get("genre", "unisex"),
                "style":        i.get("style", "casual"),
                "use_in_outfit": i.get("use_in_outfit", True),
                "notes":        i.get("notes", ""),
            }
            for i in items
        ]
    except Exception as e:
        print(f"[DB] Erreur get_wardrobe_items: {e}")
        return []


def delete_wardrobe_item(item_id: str, user_id: str):
    db = get_db()
    try:
        db.wardrobe_items.delete_one({
            "_id":     ObjectId(item_id),
            "user_id": user_id
        })
        return True
    except Exception as e:
        print(f"[DB] Erreur delete_wardrobe_item: {e}")
        return False


def get_wardrobe_as_text(user_id: str) -> str:
    """Retourne la garde-robe sous forme de texte CSV pour l'orchestrateur.
    N'inclut que les pièces marquées use_in_outfit=True.
    Format enrichi : nom couleur (marque) [genre/style]
    """
    items = get_wardrobe_items(user_id)
    if not items:
        return ""
    parts = []
    for it in items:
        if not it.get("use_in_outfit", True):
            continue
        label = it["name"]
        if it["color"]:
            label += f" {it['color']}"
        if it["brand"]:
            label += f" ({it['brand']})"
        meta = []
        if it["genre"] and it["genre"] != "unisex":
            meta.append(it["genre"])
        if it["style"] and it["style"] != "casual":
            meta.append(it["style"])
        if meta:
            label += f" [{'/'.join(meta)}]"
        parts.append(label)
    return ", ".join(parts)