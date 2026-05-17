# -*- coding: utf-8 -*-
# ============================================================
# image_generator.py — Générateur d'image d'outfit
# WearWise AI — Smart Closet & Anti-Regret Shopping Agent
#
# API utilisée : Pollinations.AI — 100% GRATUIT, sans clé API
# Endpoint : https://image.pollinations.ai/prompt/{prompt}
#
# Rôle :
# - Construire un prompt visuel à partir de l'outfit proposé
# - Appeler Pollinations.AI pour générer l'image
# - Retourner l'URL directe ou sauvegarder l'image localement
# ============================================================

import re
import time
import urllib.request
import urllib.parse
import urllib.error
import os
import base64


# ============================================================
# 0. CONFIGURATION
# ============================================================

POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"

# Dimensions de l'image générée (ratio portrait pour un outfit)
IMAGE_WIDTH = 284
IMAGE_HEIGHT = 412

# Dossier de sauvegarde des images générées
OUTPUT_DIR = "generated_outfits"


# ============================================================
# 1. CONSTRUCTION DU PROMPT VISUEL
# ============================================================

def build_outfit_prompt(outfit, intent):
    """
    Construit un prompt visuel ultra-détaillé avec TOUS les produits de l'outfit.
    """

    parts = []

    # Style de photo
    parts.append("fashion editorial photo, full body shot, white studio background, professional fashion photography, sharp focus")

    # Genre
    gender = intent.get("gender", "femme")
    if gender == "homme":
        subject = "stylish man, standing straight, full body visible"
    else:
        subject = "elegant woman, standing straight, full body visible"
    parts.append(subject)

    # ✅ Récupérer les détails exacts de l'outfit
    outfit_details = intent.get("outfit_details", {})
    top     = outfit_details.get("top") or outfit.get("top", "")
    bottom  = outfit_details.get("bottom") or outfit.get("bottom", "")
    shoes   = outfit_details.get("shoes") or outfit.get("shoes", "")
    accessory = outfit_details.get("accessory") or outfit.get("accessory", "")

    # ✅ Construire la description pièce par pièce
    wearing_parts = []

    if top and top not in ["Non disponible", "non trouvé", ""]:
        wearing_parts.append(_translate_to_english(top))

    if bottom and bottom not in ["Non disponible", "non trouvé", ""]:
        wearing_parts.append(_translate_to_english(bottom))

    if shoes and shoes not in ["Non disponible", "non trouvé", ""]:
        wearing_parts.append(_translate_to_english(shoes))

    if accessory and accessory not in ["Non disponible", "non trouvé", ""]:
        wearing_parts.append(f"with {_translate_to_english(accessory)}")

    if wearing_parts:
        parts.append("wearing " + ", ".join(wearing_parts))

    # Style / Occasion
    event = intent.get("event", "casual")
    parts.append(_get_style_descriptor(event))

    # Couleur dominante
    color = intent.get("color", "")
    if color:
        parts.append(f"{_translate_color(color)} color palette")

    # Background
    parts.append(_get_background(event))

    # Qualité
    parts.append("complete outfit visible from head to toe, high quality, realistic, 4k, beautiful lighting, all clothing items clearly visible")

    # Négatif implicite
    parts.append("no cropping, no cut off, full body shown")

    return ", ".join(parts)


def _translate_to_english(text):
    """
    Traduit les mots français courants en anglais pour le prompt visuel.
    Pollinations.AI fonctionne mieux avec des prompts en anglais.
    """

    translations = {
        # Hauts
        "chemise blanche": "white shirt",
        "chemise bleue": "blue shirt",
        "chemise": "shirt",
        "t-shirt blanc": "white t-shirt",
        "t-shirt": "t-shirt",
        "blazer noir": "black blazer",
        "blazer gris": "grey blazer",
        "blazer": "blazer",
        "veste": "jacket",
        "pull": "sweater",
        "sweat": "sweatshirt",
        "manteau": "coat",
        "cardigan": "cardigan",
        "haut": "top",

        # Bas
        "pantalon noir": "black trousers",
        "pantalon gris": "grey trousers",
        "pantalon": "trousers",
        "jean bleu": "blue jeans",
        "jean": "jeans",
        "jupe": "skirt",
        "jupe midi": "midi skirt",
        "short": "shorts",
        "legging": "leggings",

        # Robes
        "robe noire": "black dress",
        "robe blanche": "white dress",
        "robe rouge": "red dress",
        "robe": "dress",

        # Chaussures
        "baskets blanches": "white sneakers",
        "baskets": "sneakers",
        "sneakers blanches": "white sneakers",
        "sneakers": "sneakers",
        "escarpins nude": "nude heels",
        "escarpins noirs": "black heels",
        "escarpins": "heels",
        "sandales": "sandals",
        "mocassins": "loafers",
        "bottines": "ankle boots",
        "bottes": "boots",
        "chaussures": "shoes",

        # Accessoires
        "sac noir": "black bag",
        "sac à main": "handbag",
        "pochette": "clutch bag",
        "sac": "bag",
        "ceinture": "belt",
        "montre": "watch",
        "collier": "necklace",
        "boucles d'oreilles": "earrings",

        # Couleurs
        "noir": "black",
        "blanc": "white",
        "bleu": "blue",
        "rouge": "red",
        "vert": "green",
        "beige": "beige",
        "gris": "grey",
        "rose": "pink",
        "nude": "nude",
        "marine": "navy blue",
        "bordeaux": "burgundy",
        "camel": "camel",
        "or": "gold",
        "argent": "silver",
    }

    text_lower = text.lower().strip()

    # Cherche d'abord les correspondances complètes
    for fr, en in sorted(translations.items(), key=lambda x: -len(x[0])):
        if fr in text_lower:
            text_lower = text_lower.replace(fr, en)

    return text_lower


def _translate_color(color):
    """Traduit une couleur française en anglais."""

    color_map = {
        "noir": "black",
        "blanc": "white",
        "rouge": "red",
        "bleu": "blue",
        "vert": "green",
        "rose": "pink",
        "beige": "beige",
        "gris": "grey",
        "marron": "brown",
        "camel": "camel",
        "or": "gold",
        "argent": "silver",
        "nude": "nude",
        "bordeaux": "burgundy",
        "kaki": "khaki",
        "marine": "navy",
        "crème": "cream",
        "corail": "coral",
        "jaune": "yellow",
        "violet": "purple",
        "lilas": "lilac",
        "turquoise": "turquoise",
    }

    return color_map.get(color.lower(), color)


def _get_style_descriptor(event):
    """
    Retourne un descripteur de style pour le prompt selon l'occasion.
    """

    descriptors = {
        "soutenance": "professional academic presentation style, smart casual, confident",
        "entretien": "professional job interview style, formal, polished",
        "travail": "office professional style, business casual, clean",
        "mariage": "elegant wedding guest outfit, glamorous, sophisticated",
        "soiree": "evening party outfit, chic, stylish, glamorous",
        "universite": "smart casual university student style",
        "plage": "beach casual style, relaxed, summer",
        "sport": "athletic sporty style, activewear",
        "boheme": "boho chic style, relaxed, flowy",
        "casual": "casual everyday style, comfortable, stylish",
    }

    return descriptors.get(event, "stylish casual look")


def _get_background(event):
    """
    Retourne un fond adapté à l'occasion.
    """

    backgrounds = {
        "soutenance": "clean white studio background, minimal",
        "entretien": "clean office background, neutral",
        "travail": "modern office background, neutral tones",
        "mariage": "elegant floral background, soft bokeh",
        "soiree": "dark elegant background, city lights bokeh",
        "universite": "campus background, soft blur",
        "plage": "beach background, ocean, sunny",
        "sport": "gym background, clean, bright",
        "casual": "clean urban background, soft blur",
    }

    return backgrounds.get(event, "clean studio background, neutral")


# ============================================================
# 2. GÉNÉRATION VIA POLLINATIONS.AI
# ============================================================

def generate_outfit_image_url(outfit, intent):
    """
    Génère l'URL de l'image de l'outfit via Pollinations.AI.

    Pollinations.AI :
    - 100% gratuit
    - Pas de clé API requise
    - URL directe : https://image.pollinations.ai/prompt/{prompt}?width=512&height=768&nologo=true

    Retourne :
    - L'URL directe de l'image (peut être utilisée dans <img> ou st.image())
    - None si erreur
    """

    if not outfit:
        return None

    prompt = build_outfit_prompt(outfit, intent)

    # Encoder le prompt pour l'URL
    encoded_prompt = urllib.parse.quote(prompt)

    # Construire l'URL avec paramètres
    url = (
        f"{POLLINATIONS_BASE_URL}/{encoded_prompt}"
        f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
        f"&nologo=true"
        f"&enhance=true"
        f"&model=flux"
        f"&seed={_generate_seed(outfit)}"
    )

    return url


def fetch_image_data_uri(url):
    if not url:
        return None
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            mime = resp.headers.get_content_type() or "image/jpeg"
            encoded = base64.b64encode(data).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    except Exception as e:
        print(f"[ImageGen] Erreur fetch_image_data_uri : {e}")
        return None


def download_outfit_image(outfit, intent, filename=None):
    """
    Télécharge l'image générée et la sauvegarde localement.

    Retourne :
    - Le chemin local du fichier image
    - None si erreur
    """

    url = generate_outfit_image_url(outfit, intent)

    if not url:
        return None

    # Créer le dossier si nécessaire
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Nom du fichier
    if not filename:
        timestamp = int(time.time())
        filename = f"outfit_{timestamp}.png"

    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        print(f"[ImageGen] Génération de l'image via Pollinations.AI...")
        print(f"[ImageGen] Prompt : {build_outfit_prompt(outfit, intent)[:80]}...")

        # Télécharger l'image
        urllib.request.urlretrieve(url, filepath)

        print(f"[ImageGen] Image sauvegardée : {filepath}")
        return filepath

    except urllib.error.URLError as e:
        print(f"[ImageGen] Erreur réseau : {e}")
        return None

    except Exception as e:
        print(f"[ImageGen] Erreur : {e}")
        return None


def _generate_seed(outfit):
    """
    Génère un seed stable basé sur le contenu de l'outfit.
    Même outfit = même image (reproductible).
    """

    content = str(outfit.get("top", "")) + str(outfit.get("bottom", "")) + str(outfit.get("shoes", ""))
    return abs(hash(content)) % 999999


# ============================================================
# 3. FONCTION PRINCIPALE D'INTÉGRATION
# ============================================================

def generate_image_for_outfit(outfit, intent, save_local=True):
    """
    Fonction principale appelée par orchestrator.py.

    Retourne un dict avec :
    - url : URL directe Pollinations (pour affichage en ligne)
    - local_path : chemin local si save_local=True
    - prompt : le prompt utilisé
    - success : bool
    """

    if not outfit or outfit.get("top") == "Non disponible":
        return {
            "url": None,
            "local_path": None,
            "prompt": None,
            "success": False,
            "error": "Outfit incomplet ou non disponible"
        }

    prompt = build_outfit_prompt(outfit, intent)
    url = generate_outfit_image_url(outfit, intent)

    result = {
        "url": url,
        "local_path": None,
        "prompt": prompt,
        "success": True,
        "error": None,
        "image_data_uri": fetch_image_data_uri(url)
    }

    if save_local:
        timestamp = int(time.time())
        filename = f"outfit_{timestamp}.png"
        local_path = download_outfit_image(outfit, intent, filename)
        result["local_path"] = local_path

        if local_path is None:
            result["success"] = False
            result["error"] = "Échec du téléchargement de l'image"

    return result


# ============================================================
# 4. TEST STANDALONE
# ============================================================

if __name__ == "__main__":
    test_outfit = {
        "top": "chemise blanche",
        "bottom": "pantalon noir",
        "shoes": "escarpins nude",
        "accessory": "sac noir",
        "total_price": 145
    }

    test_intent = {
        "event": "soutenance",
        "gender": "femme",
        "style": "travail",
        "budget": 150,
        "color": "noir"
    }

    print("=== TEST IMAGE GENERATOR ===")
    print(f"\nPrompt construit :\n{build_outfit_prompt(test_outfit, test_intent)}")

    result = generate_image_for_outfit(test_outfit, test_intent, save_local=True)

    print(f"\nRésultat :")
    print(f"  URL    : {result['url'][:80]}..." if result['url'] else "  URL    : None")
    print(f"  Local  : {result['local_path']}")
    print(f"  Succès : {result['success']}")