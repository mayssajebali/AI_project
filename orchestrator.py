# -*- coding: utf-8 -*-
# ============================================================
# orchestrator.py — WearWise AI
# ============================================================

import re

from tools_basic import search_products, compare_prices, get_product_by_id, get_catalogue_stats
from tools_bonus import (
    fashion_stylist,
    outfit_builder,
    negotiate_deal,
    generate_outfit_options,
    anti_regret_analyzer
)

try:
    from image_generator import generate_image_for_outfit
    IMAGE_GEN_AVAILABLE = True
except ImportError:
    IMAGE_GEN_AVAILABLE = False
    print("[Orchestrator] ATTENTION : image_generator.py introuvable.")

import tools_bonus
print("TOOLS_BONUS UTILISÉ :", tools_bonus.__file__)


# ============================================================
# 0. HELPERS
# ============================================================

def display_label(value):
    labels = {
        "soiree": "soirée",
        "soutenance": "soutenance",
        "entretien": "entretien",
        "universite": "université",
        "mariage": "mariage",
        "travail": "travail",
        "casual": "casual",
        "sport": "sport",
        "plage": "plage",
        "boheme": "bohème",
        None: "non précisé"
    }
    return labels.get(value, value)


def format_price(value):
    if value is None:
        return "N/A"
    if isinstance(value, float) and value.is_integer():
        return f"{int(value)} DT"
    return f"{value} DT"


def normalize_text(message):
    if not message:
        return ""
    return message.lower().strip()


def event_for_tools(event):
    if event in ["soutenance", "entretien"]:
        return "travail"
    return event


# ============================================================
# 1. WARDROBE TWIN
# ============================================================

def parse_closet_items(closet_text=None):
    """Garde pour compatibilité texte legacy. Retourne liste de strings."""
    if not closet_text:
        return []
    raw_items = closet_text.replace("\n", ",").split(",")
    items = []
    for item in raw_items:
        cleaned = item.strip().lower()
        if cleaned:
            items.append(cleaned)
    return items


# ── Wardrobe match helpers ──────────────────────────────────

def _style_matches(item_style, intent_style, intent_event):
    """Vérifie si le style d'une pièce correspond au style demandé.
    Strict : une pièce soirée ne sort jamais pour casual, et vice-versa.
    Seule exception : style 'autre' = utilisable partout.
    """
    if not item_style or item_style == "autre":
        return True  # "autre" ou non renseigné = universel

    target = intent_style or intent_event or "casual"

    accepted_pieces = {
        "casual":     {"casual"},
        "universite": {"casual"},
        "chic":       {"chic"},
        "travail":    {"travail", "chic"},
        "soutenance": {"travail", "chic"},
        "entretien":  {"travail", "chic"},
        "soiree":     {"soiree"},
        "mariage":    {"mariage", "soiree"},
        "sport":      {"sport"},
        "plage":      {"casual", "sport"},
        "boheme":     {"boheme"},
    }
    allowed = accepted_pieces.get(target, {target})
    return item_style in allowed


def _genre_matches(item_genre, intent_gender):
    if not item_genre or item_genre == "unisex":
        return True
    if not intent_gender:
        return True
    return item_genre == intent_gender


def find_matching_wardrobe_pieces(wardrobe_dicts, intent):
    """
    wardrobe_dicts : liste de dicts structurés depuis get_wardrobe_items()
                     chaque dict a : id, name, category, color, brand, size,
                                     genre, style, use_in_outfit, notes
    Retourne les pièces dont le style ET le genre matchent la demande.
    """
    matched = []
    for item in wardrobe_dicts:
        if not item.get("use_in_outfit", True):
            continue  # exclues explicitement par l'utilisateur
        item_style = item.get("style", "autre")
        item_genre = item.get("genre", "unisex")
        if not _style_matches(item_style, intent.get("style"), intent.get("event")):
            continue
        if not _genre_matches(item_genre, intent.get("gender")):
            continue
        # Construire un label lisible
        label = item["name"]
        if item.get("color"):
            label += f" {item['color']}"
        if item.get("brand"):
            label += f" ({item['brand']})"
        matched.append({
            "name":     label,
            "category": item.get("category", detect_item_category(item["name"])),
            "style":    item_style,
            "genre":    item_genre,
        })
    return matched


def detect_item_category(item):
    item = item.lower()
    if re.search(r"robe", item):
        return "robe"
    if re.search(r"chaussure|sneaker|sneakers|basket|baskets|escarpin|sandale|mocassin|botte|bottine", item):
        return "chaussures"
    if re.search(r"\bsac\b|clutch|pochette|tote|backpack", item):
        return "sac"
    if re.search(r"pantalon|jean|jupe|legging|short|cargo", item):
        return "pantalon"
    if re.search(r"chemise|t-shirt|tee-shirt|haut|top|blazer|veste|pull|sweat|manteau|cardigan|hoodie", item):
        return "haut"
    if re.search(r"ceinture|lunette|bijou|collier|bracelet|chapeau|montre|écharpe|echarpe|bonnet|accessoire", item):
        return "accessoire"
    return "autre"


def analyze_closet(closet_items):
    categories = {}
    category_list = []
    for item in closet_items:
        category = detect_item_category(item)
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
        if category not in category_list:
            category_list.append(category)
    return {
        "items": closet_items,
        "categories": category_list,
        "by_category": categories
    }


def get_required_categories_for_event(event, gender=None):
    if event in ["soutenance", "entretien", "travail"]:
        return ["haut", "pantalon", "chaussures", "sac"]
    if event == "mariage" and gender == "femme":
        return ["robe", "chaussures", "sac"]
    if event == "soiree" and gender == "femme":
        return ["robe", "chaussures", "sac"]
    if event == "sport":
        return ["haut", "pantalon", "chaussures"]
    if event == "plage":
        return ["haut", "pantalon", "chaussures", "accessoire"]
    return ["haut", "pantalon", "chaussures", "accessoire"]


def detect_missing_pieces(event, gender, closet_analysis):
    required = get_required_categories_for_event(event, gender)
    owned_categories = closet_analysis.get("categories", [])
    covered = []
    missing = []
    for category in required:
        if category in owned_categories:
            covered.append(category)
        else:
            missing.append(category)
    return {
        "required": required,
        "covered": covered,
        "missing": missing
    }


def attach_closet_to_intent(intent, closet_items=None):
    """
    closet_items peut être :
      - une liste de dicts structurés (depuis get_wardrobe_items)  ← mode principal
      - une string texte legacy                                     ← fallback
    """
    # Normaliser en liste de strings pour closet_analysis (gap analyzer)
    if isinstance(closet_items, list) and closet_items and isinstance(closet_items[0], dict):
        wardrobe_dicts = closet_items
        parsed_items = [
            (it["name"] + (" " + it["color"] if it.get("color") else "")).strip().lower()
            for it in wardrobe_dicts
        ]
    else:
        wardrobe_dicts = []
        parsed_items = parse_closet_items(closet_items)

    intent["closet_items"]    = parsed_items
    intent["closet_analysis"] = None
    intent["gap_analysis"]    = None
    intent["matched_wardrobe"] = []

    if parsed_items and intent.get("wants_outfit"):
        closet_analysis = analyze_closet(parsed_items)
        intent["closet_analysis"] = closet_analysis
        intent["gap_analysis"] = detect_missing_pieces(
            event=intent.get("event"),
            gender=intent.get("gender"),
            closet_analysis=closet_analysis
        )
        # Matching sur les dicts structurés si disponibles, sinon liste vide
        if wardrobe_dicts:
            intent["matched_wardrobe"] = find_matching_wardrobe_pieces(wardrobe_dicts, intent)

    return intent


# ============================================================
# 2. ANALYSER L'INTENTION
# ============================================================

def analyze_intent(message):
    msg = normalize_text(message)
    return {
        "wants_styling": bool(re.search(
            r"style|tenue|outfit|look|mariage|casual|chic|élégant|elegant|soirée|soiree|plage|travail|bureau|soutenance|entretien|université|universite",
            msg
        )),
        "wants_search": bool(re.search(
            r"cherche|trouve|veux|besoin|acheter|produit|montre|show|recommande|propose",
            msg
        )),
        "wants_deal": bool(re.search(
            r"réduction|reduction|promo|moins cher|deal|remise|négoci|negoci|offre|solde",
            msg
        )),
        "wants_outfit": bool(re.search(
            r"tenue|outfit|look|vêtement|vetement|habill|style|porter|mettre|choisir|propose|recommande|cherche|trouve|veux|besoin",
            msg
        )),
        "budget": extract_budget(msg),
        "event": extract_event(msg),
        "style": extract_style(msg),
        "category": extract_category(msg),
        "gender": extract_gender(msg),
        "color": extract_color(msg),
        "brand": extract_brand(msg),
        "size": extract_size(msg),
        "closet_items": [],
        "closet_analysis": None,
        "gap_analysis": None,
    }


def extract_budget(msg):
    match = re.search(r"(\d+)\s*(dt|tnd|dinar|dinars|€|eur|\$)?", msg)
    return int(match.group(1)) if match else None


def extract_event(msg):
    if re.search(r"mariage|wedding", msg):
        return "mariage"
    if re.search(r"soutenance|présentation|presentation|oral|exposé|expose|projet", msg):
        return "soutenance"
    if re.search(r"entretien|interview|stage|recrutement", msg):
        return "entretien"
    if re.search(r"travail|bureau|meeting|réunion|reunion", msg):
        return "travail"
    if re.search(r"soirée|soiree|party|fête|fete|gala", msg):
        return "soiree"
    if re.search(r"université|universite|fac|college|cours|école|ecole", msg):
        return "universite"
    if re.search(r"plage|beach|piscine", msg):
        return "plage"
    if re.search(r"sport|gym|fitness|running", msg):
        return "sport"
    return None


def extract_style(msg):
    if re.search(r"soutenance|présentation|presentation|oral|exposé|expose|entretien|interview|stage|professionnel|travail|bureau", msg):
        return "travail"
    if re.search(r"chic|élégant|elegant|classe|luxe|habillé|habille", msg):
        return "chic"
    if re.search(r"casual|décontract|decontract|simple|quotidien", msg):
        return "casual"
    if re.search(r"sport|gym|fitness|running", msg):
        return "sport"
    if re.search(r"bohème|boho|boheme", msg):
        return "boheme"
    if re.search(r"soirée|soiree|fête|fete|gala|party", msg):
        return "soiree"
    if re.search(r"mariage|wedding", msg):
        return "mariage"
    if re.search(r"université|universite|fac|college|cours", msg):
        return "casual"
    return None


def extract_category(msg):
    if re.search(r"robe", msg):
        return "robe"
    if re.search(r"chaussure|chaussures|sneaker|sneakers|basket|baskets|escarpin|bott|sandale|mocassin", msg):
        return "chaussures"
    if re.search(r"\bsac\b|bag|clutch|tote|pochette|backpack", msg):
        return "sac"
    if re.search(r"pantalon|jean|jupe|legging|short|cargo", msg):
        return "pantalon"
    if re.search(r"chemise|t-shirt|tee-shirt|haut|top|blazer|veste|pull|sweat|manteau|blouson|cardigan|hoodie", msg):
        return "haut"
    if re.search(r"accessoire|ceinture|lunette|bijou|collier|bracelet|chapeau|montre|écharpe|echarpe|bonnet", msg):
        return "accessoire"
    return None


def extract_gender(msg):
    if re.search(r"\bhomme\b|masculin|mec|garçon|garcon|monsieur", msg):
        return "homme"
    if re.search(r"\bfemme\b|féminin|feminin|dame|fille|madame", msg):
        return "femme"
    return None


def extract_color(msg):
    colors = [
        "noir", "blanc", "rouge", "bleu", "vert", "rose", "beige", "gris",
        "marron", "camel", "or", "argent", "nude", "bordeaux", "kaki",
        "marine", "crème", "creme", "corail", "jaune", "violet", "lilas",
        "emeraude", "turquoise", "champagne"
    ]
    for color in colors:
        pattern = r"\b" + re.escape(color) + r"\b"
        if re.search(pattern, msg):
            return color
    return None


def extract_brand(msg):
    brands = [
        "zara", "h&m", "mango", "nike", "adidas", "uniqlo", "massimo dutti",
        "stradivarius", "bershka", "pull&bear", "jack & jones", "selected",
        "only & sons", "puma", "new balance", "converse", "vans", "pronovias",
        "timberland", "birkenstock", "columbia", "reebok", "under armour"
    ]
    for brand in brands:
        if brand in msg:
            return brand.title()
    return None


def extract_size(msg):
    sizes_vetement = ["xs", "s", "m", "l", "xl", "xxl"]
    sizes_chaussure = ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45"]
    for size in sizes_vetement + sizes_chaussure:
        pattern = r"\b" + re.escape(size) + r"\b"
        if re.search(pattern, msg):
            return size.upper() if size in sizes_vetement else size
    return None


# ============================================================
# 3. PLANIFIER LES TOOLS
# ============================================================

def plan_steps(intent):
    steps = []
    if (
        intent["wants_search"]
        or intent["wants_outfit"]
        or intent["wants_styling"]
        or intent["budget"]
        or intent["category"]
        or intent["color"]
        or intent["brand"]
        or intent["size"]
        or intent["gender"]
    ):
        steps.append("search_products")
        steps.append("compare_prices")
    if intent["wants_styling"]:
        steps.append("fashion_stylist")
    if intent["wants_outfit"]:
        steps.append("outfit_builder")
    if intent["wants_deal"]:
        steps.append("negotiate_deal")
    if not steps:
        steps.append("search_products")
        steps.append("compare_prices")
    return steps


# ============================================================
# 4. EXÉCUTER LES TOOLS
# ============================================================

def execute_steps(steps, intent):
    """
    Exécute les tools dans l'ordre prévu.
    Retourne toujours un dict results (jamais None).
    """

    results = {}  # ✅ toujours initialisé
    tool_event = event_for_tools(intent["event"])

    for step in steps:
        try:
            print(f"  [Agent] Tool : {step}")

            if step == "search_products":
                results["products"] = search_products(
                    category=intent["category"],
                    budget=intent["budget"],
                    style=intent["style"],
                    gender=intent["gender"],
                    color=intent["color"],
                    brand=intent["brand"],
                    size=intent["size"],
                )
                print(f"           -> {len(results['products'])} produit(s) trouvé(s)")

            elif step == "compare_prices":
                results["compared"] = compare_prices(
                    products=results.get("products", []),
                    budget=intent["budget"]
                )
                print(f"           -> {len(results['compared'])} produit(s) classé(s)")

            elif step == "fashion_stylist":
                results["styling"] = fashion_stylist(
                    style=intent["style"],
                    event=tool_event,
                    budget=intent["budget"]
                )

            elif step == "outfit_builder":
                products_for_outfit = results.get("compared", results.get("products", []))
                results["outfit"] = outfit_builder(
                    event=tool_event,
                    style=intent["style"],
                    budget=intent["budget"],
                    gender=intent["gender"],
                    color=intent["color"],
                    products=products_for_outfit
                )
                if generate_outfit_options is not None:
                    results["outfit_options"] = generate_outfit_options(
                        event=tool_event,
                        style=intent["style"],
                        budget=intent["budget"],
                        gender=intent["gender"],
                        color=intent["color"],
                        products=products_for_outfit
                    )

            elif step == "negotiate_deal":
                results["deals"] = negotiate_deal(
                    products=results.get("compared", results.get("products", []))
                )

        except Exception as e:
            print(f"[Agent] Erreur dans le step '{step}' : {e}")
            continue  # ✅ continue même si un step plante

    # --------------------------------------------------------
    # Génération Image — après tous les steps
    # --------------------------------------------------------
    outfit = results.get("outfit")
    products = results.get("compared", results.get("products", []))

    if outfit:
        # ✅ Outfit disponible → image directe
        results["visual"] = _generate_visuals(outfit, intent)

    elif products:
        # ✅ Pas d'outfit mais des produits → fake outfit pour l'image
        try:
            fake_outfit = {
                "top": products[0].get("name", "Non disponible") if len(products) > 0 else "Non disponible",
                "bottom": products[1].get("name", "Non disponible") if len(products) > 1 else "Non disponible",
                "shoes": products[2].get("name", "Non disponible") if len(products) > 2 else "Non disponible",
                "accessory": "accessoire assorti",
                "total_price": sum(p.get("final_price", p.get("price", 0)) for p in products[:3])
            }
            results["visual"] = _generate_visuals(fake_outfit, intent)
        except Exception as e:
            print(f"[Agent] Impossible de générer l'image pour les produits : {e}")

    return results  # ✅ TOUJOURS retourner results


def _generate_visuals(outfit, intent):
    visual = {
        "image_url": None,
        "image_path": None,
        "prompt": None,
        "image_ok": False,
    }

    if not IMAGE_GEN_AVAILABLE:
        print("[Agent] image_generator non disponible.")
        return visual

    print("\n[Agent] Génération de l'image outfit (Pollinations.AI)...")

    try:
        # ✅ Enrichir l'intent avec les détails exacts de l'outfit
        enriched_intent = dict(intent)
        enriched_intent["outfit_details"] = {
            "top": outfit.get("top", ""),
            "bottom": outfit.get("bottom", ""),
            "shoes": outfit.get("shoes", ""),
            "accessory": outfit.get("accessory", ""),
        }

        image_result = generate_image_for_outfit(
            outfit=outfit,
            intent=enriched_intent,
            save_local=True
        )

        visual["image_url"] = image_result.get("url")
        visual["image_data"] = image_result.get("image_data_uri")
        visual["image_path"] = image_result.get("local_path")
        visual["prompt"] = image_result.get("prompt")
        visual["image_ok"] = bool(image_result.get("url") or image_result.get("image_data_uri"))

        print(f"[Agent] URL image : {visual['image_url']}")

    except Exception as e:
        print(f"[Agent] Erreur génération image : {e}")

    return visual


# ============================================================
# 5. ÉVALUATION IA
# ============================================================

def calculate_simple_score(product, intent):
    score = 0
    price = product.get("final_price", product.get("price", 0))
    rating = product.get("rating", 0)
    discount = product.get("discount", 0) or 0

    if rating >= 4.5:
        score += 30
    elif rating >= 4:
        score += 25
    elif rating >= 3.5:
        score += 15

    if intent["budget"] and price <= intent["budget"]:
        score += 25

    if discount > 0:
        score += min(discount, 20)

    if intent["budget"]:
        ratio = price / intent["budget"]
        if 0.70 <= ratio <= 1.0:
            score += 20
        elif 0.50 <= ratio < 0.70:
            score += 10
    else:
        if price <= 150:
            score += 10

    if intent["category"] and product.get("category") == intent["category"]:
        score += 10
    if intent["gender"] and product.get("gender") == intent["gender"]:
        score += 10

    return min(score, 100)


def explain_choice(product, intent):
    reasons = []
    price = product.get("final_price", product.get("price", 0))
    rating = product.get("rating", 0)
    discount = product.get("discount", 0) or 0

    if intent["budget"] and price <= intent["budget"]:
        reasons.append("respecte ton budget")
    if rating >= 4:
        reasons.append("a une bonne note client")
    if discount > 0:
        reasons.append("est en promotion")
    if intent["category"] and product.get("category") == intent["category"]:
        reasons.append(f"correspond à la catégorie {intent['category']}")
    if intent["gender"] and product.get("gender") == intent["gender"]:
        reasons.append(f"est adapté pour {intent['gender']}")

    if not reasons:
        return "Il correspond globalement à ta recherche."
    return "Il " + ", ".join(reasons) + "."


def format_product_block(product, intent, index):
    final_price = product.get("final_price", product.get("price", 0))
    savings = product.get("savings", 0)
    discount = product.get("discount", 0) or 0
    promo = f" · promo -{discount}%" if savings > 0 else ""

    gender_label = {
        "femme": "femme",
        "homme": "homme",
        "unisex": "unisex"
    }.get(product.get("gender"), "")

    ai_score = calculate_simple_score(product, intent)
    anti_regret = anti_regret_analyzer(product=product, intent=intent)

    risk_label = {
        "faible": "OK",
        "moyen": "Moyen",
        "élevé": "Attention"
    }.get(anti_regret["risk"], "OK")

    return (
        f"{index}. **{product.get('name', 'Produit')}** — {format_price(final_price)}{promo}\n"
        f"   - Genre : {gender_label} · Marque : {product.get('brand', 'N/A')} · Note : {product.get('rating', 'N/A')}/5 · Score IA : {ai_score}/100\n"
        f"   - Anti-Regret : {risk_label} · risque {anti_regret['risk']} ({anti_regret['score']}/100)\n"
        f"   - Pourquoi ? {explain_choice(product, intent)}\n"
        f"   - Lien : {product.get('url', 'Lien non disponible')}"
    )


# ============================================================
# 6. CONSTRUIRE LA RÉPONSE FINALE
# ============================================================

def build_response(results, intent, steps=None):
    """
    Crée la réponse finale. results est toujours un dict.
    """

    # ✅ Protection contre results None
    if results is None:
        results = {}

    lines = []
    event_label = display_label(intent.get("event"))
    style_label = display_label(intent.get("style"))
    closet_items = intent.get("closet_items", [])
    gap_analysis = intent.get("gap_analysis")
    matched_wardrobe = intent.get("matched_wardrobe", [])

    # --------------------------------------------------------
    # Résumé intelligent
    # --------------------------------------------------------
    lines.append(f"🧠 Style détecté : **{style_label}**")
    lines.append(f"🗓️ Événement détecté : **{event_label}**")

    if intent["budget"]:
        lines.append(f"- Budget détecté : **{intent['budget']} DT**")
    else:
        lines.append("- Budget : **non précisé**")

    if intent["category"]:
        lines.append(f"- Catégorie détectée : **{intent['category']}**")

    if intent["gender"]:
        lines.append(f"- Genre détecté : **{intent['gender']}**")

    used_tools = []
    if "products" in results:
        used_tools.append("Recherche produits")
    if "compared" in results:
        used_tools.append("Comparaison prix")
    if "styling" in results:
        used_tools.append("Fashion stylist")
    if "outfit" in results:
        used_tools.append("Outfit builder")
    if "deals" in results:
        used_tools.append("Négociation / deals")
    if results.get("visual", {}).get("image_ok"):
        used_tools.append("\U0001f5bc\ufe0f Visual Generator")

    lines.append(f"- Tools utilisés : **{', '.join(used_tools)}**")
    lines.append("")

    # --------------------------------------------------------
    # Closet Gap Analyzer
    # --------------------------------------------------------
    if intent["wants_outfit"] and closet_items and gap_analysis:
        required = gap_analysis.get("required", [])
        covered = gap_analysis.get("covered", [])
        missing = gap_analysis.get("missing", [])

        lines.append("📊 Closet Gap Analyzer")
        lines.append(f"Pour **{event_label}**, une tenue cohérente demande : **{', '.join(required)}**.")
        if covered:
            lines.append(f"- Pièces déjà couvertes par ta garde-robe : **{', '.join(covered)}**")
        else:
            lines.append("- Aucune pièce essentielle n'est clairement couverte par ta garde-robe.")
        if missing:
            lines.append(f"- Pièces manquantes à compléter : **{', '.join(missing)}**")
        else:
            lines.append("- Bonne nouvelle : ta garde-robe couvre déjà les pièces principales.")
        lines.append("")

    # --------------------------------------------------------
    # Pièces garde-robe compatibles avec le look
    # --------------------------------------------------------
    if intent["wants_outfit"] and matched_wardrobe:
        lines.append("✨ Pièces de ta garde-robe compatibles avec ce look")
        by_cat = {}
        for p in matched_wardrobe:
            cat = p["category"]
            by_cat.setdefault(cat, []).append(p["name"])
        for cat, names in by_cat.items():
            lines.append(f"- **{cat.capitalize()}** : {', '.join(names[:3])}")
        lines.append("→ Ces pièces peuvent remplacer ou compléter les suggestions du catalogue.")
        lines.append("")

    # --------------------------------------------------------
    # Introduction section principale
    # --------------------------------------------------------
    if intent["wants_outfit"]:
        intro = f"👗 Tenue proposée pour {event_label}"
        if intent["budget"]:
            intro += f" — budget **{intent['budget']} DT**"
        lines.append(intro)
        lines.append("")
    elif intent["wants_styling"]:
        lines.append(f"✨ Suggestions pour un look {style_label} ({event_label})")
        lines.append("")
    else:
        lines.append("🛍️ Produits recommandés")
        lines.append("")

    # --------------------------------------------------------
    # Produits recommandés
    # --------------------------------------------------------
    compared = results.get("compared", [])

    if compared and intent["budget"]:
        budget = intent["budget"]
        in_budget = [p for p in compared if p.get("final_price", p["price"]) <= budget]
        out_budget = [p for p in compared if p.get("final_price", p["price"]) > budget]
        in_budget.sort(key=lambda p: p.get("final_price", p["price"]), reverse=True)
        out_budget.sort(key=lambda p: p.get("final_price", p["price"]))
        compared_display = in_budget + out_budget
    else:
        compared_display = compared

    if compared and not intent["wants_outfit"]:
        lines.append("🏆 Meilleurs choix")
        # Index des catégories déjà couvertes par la garde-robe
        wardrobe_cats = {p["category"] for p in matched_wardrobe}
        for i, product in enumerate(compared_display[:3], start=1):
            block = format_product_block(product, intent, i)
            # Signaler si la garde-robe couvre déjà cette catégorie
            prod_cat = product.get("category", "")
            if prod_cat and prod_cat in wardrobe_cats:
                matching_pieces = [p["name"] for p in matched_wardrobe if p["category"] == prod_cat]
                block += f"\n   - 👗 Garde-robe : tu possèdes déjà **{', '.join(matching_pieces[:2])}** dans cette catégorie"
            lines.append(block)
            lines.append("")

    # --------------------------------------------------------
    # Conseil style
    # --------------------------------------------------------
    styling = results.get("styling")
    if styling:
        lines.append("💡 Conseil style")
        lines.append(styling["tip"])
        lines.append("")

    # --------------------------------------------------------
    # Tenue complète
    # --------------------------------------------------------
    outfit = results.get("outfit")
    if outfit:
        lines.append("👚 Tenue complète")

        # Construire un index des pièces garde-robe par catégorie
        wardrobe_by_cat = {}
        for p in matched_wardrobe:
            wardrobe_by_cat.setdefault(p["category"], []).append(p["name"])

        def outfit_line(label, key, cat):
            catalogue_val = outfit.get(key, "Non disponible")
            owned = wardrobe_by_cat.get(cat, [])
            if owned:
                return (
                    f"- {label} : **{catalogue_val}** "
                    f"*(ou ta garde-robe : {', '.join(owned[:2])})*"
                )
            return f"- {label} : **{catalogue_val}**"

        lines.append(outfit_line("Haut", "top", "haut"))
        lines.append(outfit_line("Bas", "bottom", "pantalon"))
        lines.append(outfit_line("Chaussures", "shoes", "chaussures"))
        lines.append(outfit_line("Accessoire", "accessory", "accessoire"))
        lines.append(f"- Total estimé : **{format_price(outfit['total_price'])}**")

        outfit_regret = anti_regret_analyzer(outfit=outfit, intent=intent)
        lines.append(
            f"- Anti-Regret : **risque {outfit_regret['risk']}** "
            f"({outfit_regret['score']}/100)"
        )
        for reason in outfit_regret["reasons"][:3]:
            lines.append(f"- {reason}")

        if outfit.get("missing_items"):
            missing_catalogue = ", ".join(outfit["missing_items"])
            lines.append(f"- Pièces manquantes dans le catalogue : **{missing_catalogue}**")
            lines.append("- L'agent évite de dépasser ton budget, donc la tenue peut être partielle.")

        if intent["budget"] and outfit["total_price"] > intent["budget"]:
            difference = round(outfit["total_price"] - intent["budget"], 2)
            lines.append(f"- Cette tenue dépasse le budget de **{difference} DT**.")
            lines.append("- Alternative : augmenter légèrement le budget ou retirer une pièce secondaire.")
        elif intent["budget"]:
            remaining = round(intent["budget"] - outfit["total_price"], 2)
            lines.append(f"- Budget restant : **{remaining} DT**")

        lines.append(f"- Conseil : {outfit_regret['advice']}")
        lines.append("")



    # --------------------------------------------------------
    # Options alternatives
    # --------------------------------------------------------
    outfit_options = results.get("outfit_options", [])
    if outfit_options and intent["wants_outfit"]:
        lines.append("🔁 Options alternatives")
        for option in outfit_options:
            outfit_data = option["outfit"]
            missing = outfit_data.get("missing_items", [])
            status = "complète" if not missing else "incomplète"
            lines.append(
                f"- **{option['label']}** — {format_price(outfit_data['total_price'])} ({status})"
            )
            lines.append(
                f"  Haut : {outfit_data['top']} · Bas : {outfit_data['bottom']} · "
                f"Chaussures : {outfit_data['shoes']} · Accessoire : {outfit_data['accessory']}"
            )
        lines.append("")

    # --------------------------------------------------------
    # Deals
    # --------------------------------------------------------
    deals = results.get("deals", [])
    if deals:
        lines.append("💰 Meilleures offres du moment")
        for deal in deals:
            lines.append(
                f"- {deal['name']} : {deal['original_price']} DT -> "
                f"{deal['discounted_price']} DT (-{deal['discount']}%)"
            )
        lines.append("")

    # --------------------------------------------------------
    # Aucun résultat
    # --------------------------------------------------------
    if not compared and not outfit and not deals:
        lines.append("Aucun produit trouvé avec ces critères.")
        lines.append("Essaie d'élargir ton budget, de changer le style ou de préciser l'occasion.")
        lines.append("")

    # --------------------------------------------------------
    # Décision finale
    # --------------------------------------------------------
    lines.append("✅ Conclusion de l'agent")
    if intent["budget"]:
        lines.append("- J'ai privilégié les choix cohérents avec ton budget.")
    else:
        lines.append("- Comme aucun budget précis n'a été donné, j'ai proposé des options variées.")

    if intent["wants_outfit"] and closet_items and gap_analysis:
        missing = gap_analysis.get("missing", [])
        if missing:
            lines.append("- Grâce au Wardrobe Twin, l'agent identifie les pièces déjà possédées et les pièces à compléter.")
        else:
            lines.append("- Grâce au Wardrobe Twin, ta garde-robe couvre déjà les pièces principales.")

    if intent["style"]:
        lines.append(f"- Style principal retenu : **{style_label}**.")

    if intent["wants_outfit"] and outfit and outfit.get("missing_items"):
        lines.append("- La tenue est partielle : l'agent préfère éviter de dépasser ton budget.")
    else:
        lines.append("- La recommandation combine prix, style, garde-robe, note client, promotions et risque de regret.")

    return "\n\n".join(lines)


# ============================================================
# 7. INTERACTION DYNAMIQUE
# ============================================================

def detect_missing_info(intent):
    missing = []
    if intent["wants_outfit"] and not intent["budget"]:
        missing.append("budget")
    if intent["wants_outfit"] and not intent["gender"]:
        missing.append("genre")
    if intent["wants_outfit"] and not intent["event"] and not intent["style"]:
        missing.append("occasion")
    return missing


# ============================================================
# 8. FONCTION PRINCIPALE
# ============================================================

_pending_intent = None


def merge_intents(base, update):
    merged = {}
    bool_keys = {"wants_styling", "wants_search", "wants_deal", "wants_outfit"}
    for key in base:
        base_val = base[key]
        upd_val = update.get(key)
        if key in bool_keys:
            merged[key] = base_val or upd_val
        else:
            merged[key] = upd_val if upd_val is not None else base_val
    return merged


def apply_defaults(intent):
    if intent.get("event") is None:
        intent["event"] = "casual"
    if intent.get("style") is None:
        intent["style"] = "casual"
    if intent.get("gender") is None:
        intent["gender"] = "femme"
    return intent


def is_off_topic(message, intent):
    """Retourne True si le message n'a aucun signal lié à la mode/shopping."""
    msg = normalize_text(message)

    # Salutations et messages sociaux
    if re.search(r"^(bonjour|bonsoir|salut|coucou|hello|hi|hey|slt|bjr|bsr|cc)[\s!?.]*$", msg):
        return True

    # Messages hors-sujet évidents
    if re.search(r"météo|weather|foot|football|sport\s*(score|match|résultat)|politique|nouvelles|news|blague|joke|qui\s+es\s+tu|comment\s+tu\s+t'appelles|merci|thank|ok\s*$|d'accord|super\s*$|parfait\s*$|cool\s*$", msg):
        return True

    # Aucun signal mode/shopping détecté
    has_fashion_signal = (
        intent["wants_styling"]
        or intent["wants_search"]
        or intent["wants_outfit"]
        or intent["wants_deal"]
        or intent["budget"]
        or intent["event"]
        or intent["style"]
        or intent["category"]
        or intent["gender"]
        or intent["color"]
        or intent["brand"]
        or intent["size"]
    )
    return not has_fashion_signal


OFF_TOPIC_RESPONSES = [
    (
        "👋 Bonjour ! Je suis ton **styliste IA personnel**.\n\n"
        "Je ne peux pas t'aider sur ce sujet, mais je peux te proposer :\n"
        "- Une tenue complète adaptée à ton occasion\n"
        "- Les meilleures offres du moment\n"
        "- Des conseils style personnalisés\n\n"
        "Essaie : **tenue chic femme 150 DT** ou **look casual homme 100 DT** 👗"
    ),
    (
        "👗 La mode, c'est mon domaine !\n\n"
        "Je ne suis pas fait pour ça, mais je peux t'aider à trouver **le look parfait** pour aujourd'hui.\n\n"
        "Quelques idées pour commencer :\n"
        "- **tenue casual femme 100 DT** — pour un look quotidien\n"
        "- **outfit chic homme 150 DT** — pour une occasion spéciale\n"
        "- **look soirée 200 DT** — pour sortir ce soir\n\n"
        "Dis-moi ce dont tu as besoin 👆"
    ),
    (
        "✨ Mon domaine c'est la mode, pas ça !\n\n"
        "Mais je serais ravi de t'aider à composer ta tenue du jour.\n\n"
        "Par exemple, dis-moi :\n"
        "- Quelle est l'occasion ? *(travail, soirée, université…)*\n"
        "- Ton budget ?\n"
        "- Homme ou femme ?\n\n"
        "Je m'occupe du reste 🛍️"
    ),

]

_off_topic_counter = 0

def get_off_topic_response():
    global _off_topic_counter
    response = OFF_TOPIC_RESPONSES[_off_topic_counter % len(OFF_TOPIC_RESPONSES)]
    _off_topic_counter += 1
    return {"text": response}


    if intent.get("event") is None:
        intent["event"] = "casual"
    if intent.get("style") is None:
        intent["style"] = "casual"
    if intent.get("gender") is None:
        intent["gender"] = "femme"
    return intent


def run_agent(user_message, closet_items=None):
    global _pending_intent

    print(f"\n{'=' * 55}")
    print(f"[Agent] Message reçu : {user_message}")
    print(f"{'=' * 55}")

    intent = analyze_intent(user_message)

    # ── Détection hors-sujet ──────────────────────────────
    if is_off_topic(user_message, intent):
        _pending_intent = None  # reset tout contexte en cours
        return get_off_topic_response()

    if _pending_intent is not None:
        intent = merge_intents(_pending_intent, intent)
        _pending_intent = None

    missing = detect_missing_info(intent)

    if "budget" in missing:
        _pending_intent = intent
        return {
            "text": (
                "Pour construire une tenue complète adaptée, peux-tu préciser ton budget ?\n\n"
                "Exemples : **100 DT**, **150 DT** ou **300 DT**."
            )
        }

    if "genre" in missing:
        _pending_intent = intent
        return {
            "text": (
                "Pour mieux choisir les produits, peux-tu préciser si la tenue est pour **homme** ou **femme** ?\n\n"
                "Exemple : **tenue chic femme 150dt** ou **tenue chic homme 150dt**."
            )
        }

    if "occasion" in missing:
        _pending_intent = intent
        return {
            "text": (
                "Pour éviter une tenue trop générique, peux-tu préciser l'occasion ?\n\n"
                "Exemples : **soutenance**, **mariage**, **soirée**, **travail**, **université** ou **casual**."
            )
        }

    intent = apply_defaults(intent)
    intent = attach_closet_to_intent(intent, closet_items)

    print("[Agent] Intention détectée :")
    for key, value in intent.items():
        if key in ["closet_analysis", "gap_analysis"]:
            continue
        if value is not None and value is not False:
            print(f"  {key:<18} -> {value}")

    steps = plan_steps(intent)
    print(f"\n[Agent] Plan d'action : {steps}\n")

    results = execute_steps(steps, intent)

    # ✅ Protection finale
    if results is None:
        results = {}

    final_response = build_response(results, intent, steps)
    visual = results.get("visual", {})
    image_url = visual.get("image_url", "")
    image_inline = visual.get("image_data") or image_url
    return {
        "text": final_response,
        "image": image_inline,
        "image_url": image_url
    }


# ============================================================
# 9. TESTS
# ============================================================

if __name__ == "__main__":
    tests = [
        ("TEST 1 - Sneakers homme", "je cherche sneakers homme 150 dt", "chemise blanche, pantalon noir"),
        ("TEST 2 - Soutenance femme", "je veux une tenue complete pour une soutenance femme 150dt", "chemise blanche, pantalon noir, baskets blanches"),
        ("TEST 3 - Soirée femme", "je veux une tenue complete pour une soirée femme 250dt", "robe noire, escarpins nude"),
        ("TEST 4 - Tenue homme", "je veux une tenue pour homme 170dt", "jean bleu, baskets blanches"),
    ]

    for title, message, closet in tests:
        print(f"\n{'#' * 55}\n  {title}\n{'#' * 55}")
        response = run_agent(message, closet_items=closet)
        response_text = response['text'] if isinstance(response, dict) else response
        print(f"\n{'-' * 55}\n  RÉPONSE :\n{'-' * 55}\n{response_text}")

    while True:
        user_message = input("\nToi : ")
        if user_message.lower().strip() in ["exit", "quit", "q"]:
            print("Agent : Merci, à bientôt !")
            break
        closet = input("Ta garde-robe (optionnel) : ")
        response = run_agent(user_message, closet_items=closet)
        response_text = response['text'] if isinstance(response, dict) else response
        print(f"\n{'-' * 55}\n{response_text}")