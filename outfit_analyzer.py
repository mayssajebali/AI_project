# ============================================================
#  outfit_analyzer.py — Analyse d'image d'outfit via Groq
#  + Génération d'image du nouvel outfit via Pollinations.AI
# ============================================================

import os, base64, re, json
from groq import Groq
from image_generator import generate_image_for_outfit

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """Tu es WearWise, un styliste IA expert en mode et shopping tunisien.

Quand l'utilisateur t'envoie une photo d'une tenue ou d'un vêtement, tu dois :

1. 🔍 **Analyse visuelle** — Décrire précisément ce que tu vois :
   - Pièces visibles (haut, bas, chaussures, accessoires)
   - Couleurs dominantes et palette globale
   - Style général (casual, chic, sport, soirée…)
   - Points forts et points faibles actuels

2. 💡 **Réponse à la demande** — Selon la requête de l'utilisateur :
   - Si l'utilisateur veut AJOUTER une pièce → propose 2-3 options avec prix estimatif en DT
   - Si l'utilisateur veut REMPLACER une pièce → compare l'actuelle avec les alternatives
   - Si l'utilisateur veut une AMÉLIORATION → donne des conseils précis et actionnables
   - Si l'utilisateur veut une OCCASION SPÉCIFIQUE → adapte la tenue pour cet événement

3. 🛍️ **Suggestions produits** — Pour chaque pièce suggérée :
   - Nom du produit et marque possible
   - Gamme de prix en DT (ex: 80-120 DT)
   - Où trouver en Tunisie (Zara, H&M, Mango, Promod…)

4. ✅ **Verdict final** — Score de style /10 avant/après et conseil clé

Réponds toujours en français. Sois précis, chaleureux et professionnel.
Utilise des émojis et des sections bien structurées avec du markdown.

⚠️ OBLIGATOIRE — À la toute fin de ta réponse, ajoute ce bloc JSON exactement comme ça (sans rien après) :
```outfit_json
{
  "top": "haut exact de la tenue FINALE suggérée (après modification)",
  "bottom": "bas exact de la tenue FINALE suggérée",
  "shoes": "chaussures exactes de la tenue FINALE suggérée",
  "accessory": "accessoire suggéré ou vide si aucun",
  "gender": "homme ou femme",
  "event": "casual ou travail ou soiree ou mariage ou sport ou universite ou soutenance",
  "color": "couleur dominante principale en français"
}
```
Si tu suggères plusieurs options, choisis la MEILLEURE pour ce bloc JSON."""


def _extract_outfit_json(text: str) -> dict | None:
    """Extrait le bloc outfit_json de la réponse."""
    match = re.search(r"```outfit_json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except Exception:
        return None


def _clean_text(text: str) -> str:
    """Supprime le bloc JSON de la réponse affichée."""
    return re.sub(r"```outfit_json.*?```", "", text, flags=re.DOTALL).strip()


def analyze_outfit_image(image_base64: str, image_type: str, user_message: str) -> dict:
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_type};base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT + "\n\nDemande : " + (user_message or "Analyse cette tenue et propose des améliorations.")
                    }
                ]
            }
        ],
        max_tokens=1800
    )

    raw_text = response.choices[0].message.content

    # Extraire le JSON de l'outfit final suggéré
    outfit_json = _extract_outfit_json(raw_text)

    # Nettoyer le texte (retirer le bloc JSON invisible)
    text = _clean_text(raw_text)

    # Extraire les suggestions de prix
    suggestions = []
    for line in text.split("\n"):
        if re.search(r"\d+.*DT", line) and len(line) > 10:
            clean = re.sub(r"[*•\-–#]", "", line).strip()
            if clean:
                suggestions.append(clean)

    # Générer l'image du nouvel outfit
    image_url  = None
    image_data = None

    if outfit_json:
        print(f"[OutfitAnalyzer] JSON extrait : {outfit_json}")

        outfit = {
            "top":       outfit_json.get("top", ""),
            "bottom":    outfit_json.get("bottom", ""),
            "shoes":     outfit_json.get("shoes", ""),
            "accessory": outfit_json.get("accessory", ""),
        }
        intent = {
            "gender":  outfit_json.get("gender", "femme"),
            "event":   outfit_json.get("event", "casual"),
            "color":   outfit_json.get("color", ""),
            "outfit_details": outfit,
        }

        try:
            img_result = generate_image_for_outfit(outfit, intent, save_local=False)
            if img_result.get("success"):
                image_url  = img_result.get("url")
                image_data = img_result.get("image_data_uri")
                print(f"[OutfitAnalyzer] Image générée : {image_url[:60]}...")
            else:
                print(f"[OutfitAnalyzer] Échec génération image : {img_result.get('error')}")
        except Exception as e:
            print(f"[OutfitAnalyzer] Erreur image : {e}")
    else:
        print("[OutfitAnalyzer] Aucun bloc outfit_json trouvé dans la réponse.")

    return {
        "text":               text,
        "suggestions":        suggestions[:6],
        "is_outfit_analysis": True,
        "image_url":          image_url,
        "image":              image_data,
    }