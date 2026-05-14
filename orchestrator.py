# -*- coding: utf-8 -*-
# ============================================================
# orchestrator.py — Personne 1 : L'Orchestrateur
# WearWise AI — Smart Closet & Anti-Regret Shopping Agent
#
# Rôle de ce fichier :
# - Recevoir le message utilisateur
# - Analyser l'intention
# - Analyser la garde-robe utilisateur
# - Détecter les pièces manquantes selon l'occasion
# - Planifier les tools à utiliser
# - Exécuter les tools
# - Construire une réponse claire et non encombrée
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

import tools_bonus
print("TOOLS_BONUS UTILISÉ :", tools_bonus.__file__)


# ============================================================
# 0. HELPERS D'AFFICHAGE
# ============================================================

def display_label(value):
    """
    Convertit les valeurs internes en labels plus jolis pour l'utilisateur.
    Exemple : soiree -> soirée
    """

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
    """
    Formate un prix proprement.
    """

    if value is None:
        return "N/A"

    if isinstance(value, float) and value.is_integer():
        return f"{int(value)} DT"

    return f"{value} DT"


def normalize_text(message):
    """
    Normalise le message utilisateur.
    """

    if not message:
        return ""

    return message.lower().strip()


def event_for_tools(event):
    """
    Certains tools ne connaissent pas encore 'soutenance' ou 'entretien'.
    On les traite comme 'travail' pour garder une tenue professionnelle.
    """

    if event in ["soutenance", "entretien"]:
        return "travail"

    return event


# ============================================================
# 1. WARDROBE TWIN — ANALYSE GARDE-ROBE
# ============================================================

def parse_closet_items(closet_text=None):
    """
    Transforme le texte de la garde-robe en liste propre.

    Exemple :
    "chemise blanche, pantalon noir, baskets blanches"

    devient :
    ["chemise blanche", "pantalon noir", "baskets blanches"]
    """

    if not closet_text:
        return []

    raw_items = closet_text.replace("\n", ",").split(",")
    items = []

    for item in raw_items:
        cleaned = item.strip().lower()

        if cleaned:
            items.append(cleaned)

    return items


def detect_item_category(item):
    """
    Détecte la catégorie d'une pièce de garde-robe.
    """

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
    """
    Analyse la garde-robe et retourne :
    - liste des items
    - catégories détectées
    - mapping catégorie -> items
    """

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
    """
    Donne les catégories nécessaires selon l'occasion.
    Cette fonction sert au Gap Analyzer.
    """

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
    """
    Compare les pièces nécessaires avec la garde-robe existante.
    """

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
    Ajoute la garde-robe dans l'intent.

    Correction importante :
    - Pour une recherche simple, ex : "je cherche sneakers homme 150dt",
      on ne déclenche PAS Wardrobe Twin / Gap Analyzer.
    - Pour une tenue complète, ex : "tenue soutenance femme 150dt",
      on déclenche Wardrobe Twin / Gap Analyzer.
    """

    parsed_items = parse_closet_items(closet_items)

    intent["closet_items"] = parsed_items
    intent["closet_analysis"] = None
    intent["gap_analysis"] = None

    if parsed_items and intent.get("wants_outfit"):
        closet_analysis = analyze_closet(parsed_items)

        intent["closet_analysis"] = closet_analysis
        intent["gap_analysis"] = detect_missing_pieces(
            event=intent.get("event"),
            gender=intent.get("gender"),
            closet_analysis=closet_analysis
        )

    return intent


# ============================================================
# 2. ÉTAPE 1 : ANALYSER L'INTENTION DE L'UTILISATEUR
# ============================================================

def analyze_intent(message):
    """
    Transforme une phrase utilisateur en informations structurées.
    """

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
            r"tenue complète|tenue complete|outfit complet|look complet|assembl|tenue pour|\btenue\b|\boutfit\b|\blook\b",
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
    """
    Extrait le budget depuis la phrase.
    Exemple : 150dt -> 150
    """

    match = re.search(r"(\d+)\s*(dt|tnd|dinar|dinars|€|eur|\$)?", msg)
    return int(match.group(1)) if match else None


def extract_event(msg):
    """
    Détecte l'événement ou l'occasion.
    """

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
    """
    Détecte le style demandé.
    """

    if re.search(
        r"soutenance|présentation|presentation|oral|exposé|expose|entretien|interview|stage|professionnel|travail|bureau",
        msg
    ):
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
    """
    Détecte la catégorie produit.
    """

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
    """
    Détecte homme / femme.
    """

    if re.search(r"\bhomme\b|masculin|mec|garçon|garcon|monsieur", msg):
        return "homme"

    if re.search(r"\bfemme\b|féminin|feminin|dame|fille|madame", msg):
        return "femme"

    return None


def extract_color(msg):
    """
    Détecte la couleur.
    """

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
    """
    Détecte la marque.
    """

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
    """
    Détecte la taille.
    """

    sizes_vetement = ["xs", "s", "m", "l", "xl", "xxl"]
    sizes_chaussure = ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45"]

    for size in sizes_vetement + sizes_chaussure:
        pattern = r"\b" + re.escape(size) + r"\b"

        if re.search(pattern, msg):
            return size.upper() if size in sizes_vetement else size

    return None


# ============================================================
# 3. ÉTAPE 2 : PLANIFIER LES TOOLS À APPELER
# ============================================================

def plan_steps(intent):
    """
    Crée le plan d'action de l'agent.
    """

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
# 4. ÉTAPE 3 : EXÉCUTER LES TOOLS
# ============================================================

def execute_steps(steps, intent):
    """
    Exécute les tools dans l'ordre prévu.
    """

    results = {}
    tool_event = event_for_tools(intent["event"])

    for step in steps:
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

    return results


# ============================================================
# 5. ÉTAPE 4 : FONCTIONS D'ÉVALUATION IA
# ============================================================

def calculate_simple_score(product, intent):
    """
    Calcule un score IA simple pour chaque produit.
    """

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
    """
    Explique pourquoi un produit est recommandé.
    """

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
    """
    Format compact pour un produit.
    """

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
# 6. ÉTAPE 5 : CONSTRUIRE LA RÉPONSE FINALE
# ============================================================

def build_response(results, intent, steps=None):
    """
    Crée une réponse claire, professionnelle et moins encombrée.
    """

    lines = []

    event_label = display_label(intent.get("event"))
    style_label = display_label(intent.get("style"))

    closet_items = intent.get("closet_items", [])
    gap_analysis = intent.get("gap_analysis")

    # --------------------------------------------------------
    # Résumé intelligent
    # --------------------------------------------------------
    lines.append("### Résumé intelligent")
    lines.append(f"- Style détecté : **{style_label}**")
    lines.append(f"- Événement détecté : **{event_label}**")

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

    lines.append(f"- Tools utilisés : **{', '.join(used_tools)}**")
    lines.append("")

    # --------------------------------------------------------
    # Wardrobe Twin : seulement pour une tenue complète
    # --------------------------------------------------------
    if intent["wants_outfit"] and closet_items:
        lines.append("### Wardrobe Twin")
        lines.append("L'agent a détecté les pièces que tu possèdes déjà :")

        for item in closet_items[:8]:
            lines.append(f"- {item}")

        if len(closet_items) > 8:
            lines.append(f"- ... et {len(closet_items) - 8} autre(s) pièce(s)")

        lines.append("")

    # --------------------------------------------------------
    # Closet Gap Analyzer : seulement pour une tenue complète
    # --------------------------------------------------------
    if intent["wants_outfit"] and closet_items and gap_analysis:
        required = gap_analysis.get("required", [])
        covered = gap_analysis.get("covered", [])
        missing = gap_analysis.get("missing", [])

        lines.append("### Closet Gap Analyzer")
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
    # Introduction
    # --------------------------------------------------------
    if intent["wants_outfit"]:
        intro = f"### Tenue proposée pour {event_label}"

        if intent["budget"]:
            intro += f" — budget **{intent['budget']} DT**"

        lines.append(intro)
        lines.append("")

    elif intent["wants_styling"]:
        lines.append(f"### Suggestions pour un look {style_label} ({event_label})")
        lines.append("")

    else:
        lines.append("### Produits recommandés")
        lines.append("")

    # --------------------------------------------------------
    # Produits recommandés
    # --------------------------------------------------------
    compared = results.get("compared", [])

    if compared and intent["budget"]:
        budget = intent["budget"]

        in_budget = [
            p for p in compared
            if p.get("final_price", p["price"]) <= budget
        ]

        out_budget = [
            p for p in compared
            if p.get("final_price", p["price"]) > budget
        ]

        in_budget.sort(key=lambda p: p.get("final_price", p["price"]), reverse=True)
        out_budget.sort(key=lambda p: p.get("final_price", p["price"]))

        compared_display = in_budget + out_budget

    else:
        compared_display = compared

    # Recherche simple : afficher les produits
    # Tenue complète : ne pas afficher cette longue liste pour éviter l'encombrement
    if compared and not intent["wants_outfit"]:
        lines.append("### Meilleurs choix")

        for i, product in enumerate(compared_display[:3], start=1):
            lines.append(format_product_block(product, intent, i))
            lines.append("")

    # --------------------------------------------------------
    # Conseil style
    # --------------------------------------------------------
    styling = results.get("styling")

    if styling:
        lines.append("### Conseil style")
        lines.append(styling["tip"])
        lines.append("")

    # --------------------------------------------------------
    # Tenue complète
    # --------------------------------------------------------
    outfit = results.get("outfit")

    if outfit:
        lines.append("### Tenue complète")
        lines.append(f"- Haut : **{outfit['top']}**")
        lines.append(f"- Bas : **{outfit['bottom']}**")
        lines.append(f"- Chaussures : **{outfit['shoes']}**")
        lines.append(f"- Accessoire : **{outfit['accessory']}**")
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
    # Options alternatives compactes
    # --------------------------------------------------------
    outfit_options = results.get("outfit_options", [])

    if outfit_options and intent["wants_outfit"]:
        lines.append("### Options alternatives")

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
    # Deals / promotions
    # --------------------------------------------------------
    deals = results.get("deals", [])

    if deals:
        lines.append("### Meilleures offres du moment")

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
    lines.append("### Décision finale de l'agent")

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
# 7. ÉTAPE 6 : INTERACTION DYNAMIQUE
# ============================================================

def detect_missing_info(intent):
    """
    Détecte les informations importantes manquantes.
    """

    missing = []

    if intent["wants_outfit"] and not intent["budget"]:
        missing.append("budget")

    if intent["wants_outfit"] and not intent["gender"]:
        missing.append("genre")

    if intent["wants_outfit"] and not intent["event"] and not intent["style"]:
        missing.append("occasion")

    return missing


# ============================================================
# 8. ÉTAPE 7 : FONCTION PRINCIPALE DE L'AGENT
# ============================================================

_pending_intent = None


def merge_intents(base, update):
    """
    Fusionne deux intents : garde les valeurs précédentes si le nouveau message ne les fournit pas.
    """

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
    """
    Applique des valeurs par défaut seulement quand c'est nécessaire.
    """

    if intent.get("event") is None:
        intent["event"] = "casual"

    if intent.get("style") is None:
        intent["style"] = "casual"

    return intent


def run_agent(user_message, closet_items=None):
    """
    Point d'entrée principal de l'agent.
    Compatible avec :
    - run_agent(message)
    - run_agent(message, closet_items="chemise blanche, pantalon noir")
    """

    global _pending_intent

    print(f"\n{'=' * 55}")
    print(f"[Agent] Message reçu : {user_message}")
    print(f"{'=' * 55}")

    intent = analyze_intent(user_message)

    if _pending_intent is not None:
        intent = merge_intents(_pending_intent, intent)
        _pending_intent = None

    # Interaction dynamique avant d'appliquer les valeurs par défaut.
    missing = detect_missing_info(intent)

    if "budget" in missing:
        _pending_intent = intent
        return (
            "Pour construire une tenue complète adaptée, peux-tu préciser ton budget ?\n\n"
            "Exemples : **100 DT**, **150 DT** ou **300 DT**."
        )

    if "genre" in missing:
        _pending_intent = intent
        return (
            "Pour mieux choisir les produits, peux-tu préciser si la tenue est pour **homme** ou **femme** ?\n\n"
            "Exemple : **tenue chic femme 150dt** ou **tenue chic homme 150dt**."
        )

    if "occasion" in missing:
        _pending_intent = intent
        return (
            "Pour éviter une tenue trop générique, peux-tu préciser l'occasion ?\n\n"
            "Exemples : **soutenance**, **mariage**, **soirée**, **travail**, **université** ou **casual**."
        )

    intent = apply_defaults(intent)
    intent = attach_closet_to_intent(intent, closet_items)

    print("[Agent] Intention détectée :")
    for key, value in intent.items():
        if key in ["closet_analysis", "gap_analysis"]:
            continue

        if value is not None and value is not False:
            print(f"  {key:<18} -> {value}")

    steps = plan_steps(intent)

    print(f"\n[Agent] Plan d'action : {steps}")
    print()

    results = execute_steps(steps, intent)

    final_response = build_response(results, intent, steps)

    return final_response


# ============================================================
# 9. ÉTAPE 8 : TESTS ET CHAT INTERACTIF
# ============================================================

if __name__ == "__main__":

    tests = [
        (
            "TEST 1 - Recherche simple sneakers",
            "je cherche sneakers homme 150 dt",
            "chemise blanche, pantalon noir"
        ),
        (
            "TEST 2 - Tenue soutenance avec garde-robe",
            "je veux une tenue complete pour une soutenance femme 150dt",
            "chemise blanche, pantalon noir, baskets blanches"
        ),
        (
            "TEST 3 - Tenue soirée femme",
            "je veux une tenue complete pour une soirée femme 250dt",
            "robe noire, escarpins nude"
        ),
        (
            "TEST 4 - Demande vague",
            "je veux une tenue pour homme 170dt",
            "jean bleu, baskets blanches"
        ),
    ]

    for title, message, closet in tests:
        print(f"\n{'#' * 55}")
        print(f"  {title}")
        print(f"{'#' * 55}")

        response = run_agent(message, closet_items=closet)

        print(f"\n{'-' * 55}")
        print("  RÉPONSE DE L'AGENT :")
        print(f"{'-' * 55}")
        print(response)

    print(f"\n{'#' * 55}")
    print("  CHAT INTERACTIF — écris ta propre demande")
    print(f"{'#' * 55}")
    print("  Tape 'exit' pour quitter.")
    print(f"{'-' * 55}")

    while True:
        user_message = input("Toi : ")

        if user_message.lower().strip() in ["exit", "quit", "q"]:
            print("Agent : Merci, à bientôt !")
            break

        closet = input("Ta garde-robe actuelle (optionnel) : ")

        response = run_agent(user_message, closet_items=closet)

        print(f"\n{'-' * 55}")
        print("  RÉPONSE DE L'AGENT :")
        print(f"{'-' * 55}")
        print(response)