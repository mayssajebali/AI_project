# ============================================================
#  orchestrator.py — Personne 1 : L'Orchestrateur
#  Agent IA de Shopping Intelligent
#
#  Rôle de ce fichier :
#  - Recevoir le message utilisateur
#  - Analyser l'intention
#  - Planifier les tools à utiliser
#  - Exécuter les tools
#  - Construire une réponse claire pour l'interface
# ============================================================

import re

from tools_basic import search_products, compare_prices, get_product_by_id, get_catalogue_stats
from tools_bonus import fashion_stylist, outfit_builder, negotiate_deal, generate_outfit_options

import tools_bonus
print("TOOLS_BONUS UTILISÉ :", tools_bonus.__file__)


# ============================================================
#  ÉTAPE 1 : ANALYSER L'INTENTION DE L'UTILISATEUR
# ============================================================

def analyze_intent(message):
    """
    Transforme une phrase utilisateur en informations structurées.
    Exemple :
    "je veux une tenue chic femme 150dt"
    devient :
    style = chic
    gender = femme
    budget = 150
    wants_outfit = True
    """

    msg = message.lower()

    return {
        "wants_styling": bool(re.search(
            r"style|tenue|outfit|look|mariage|casual|chic|élégant|soirée|plage|travail|bureau",
            msg
        )),

        "wants_search": bool(re.search(
            r"cherche|trouve|veux|besoin|acheter|produit|montre|show",
            msg
        )),

        "wants_deal": bool(re.search(
            r"réduction|promo|moins cher|deal|remise|négoci|offre|solde",
            msg
        )),

        # Important : détecte aussi "tenue", "look", "outfit"
        "wants_outfit": bool(re.search(
            r"tenue complète|outfit complet|look complet|assembl|tenue pour|\btenue\b|\boutfit\b|\blook\b",
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
    }


def extract_budget(msg):
    """
    Extrait le budget depuis la phrase.
    Exemple : 150dt → 150
    """

    match = re.search(r"(\d+)\s*(dt|tnd|dinar|€|eur|\$)?", msg)
    return int(match.group(1)) if match else None


def extract_event(msg):
    """
    Détecte l'événement ou l'occasion.
    Si aucun événement clair n'est trouvé, on utilise casual par défaut.
    """

    if re.search(r"mariage|wedding", msg):
        return "mariage"

    if re.search(r"travail|bureau|meeting", msg):
        return "travail"

    if re.search(r"soirée|party|fête|gala", msg):
        return "soirée"

    if re.search(r"plage|beach|piscine", msg):
        return "plage"

    if re.search(r"sport|gym|fitness|running", msg):
        return "sport"

    return None  # pas d'occasion explicite détectée


def extract_style(msg):
    """
    Détecte le style demandé.
    """

    if re.search(r"chic|élégant|classe|luxe", msg):
        return "chic"

    if re.search(r"casual|décontract|simple", msg):
        return "casual"

    if re.search(r"sport|gym|fitness", msg):
        return "sport"

    if re.search(r"bohème|boho|boheme", msg):
        return "boheme"

    if re.search(r"soirée|fête|gala", msg):
        return "soiree"

    if re.search(r"mariage|wedding", msg):
        return "mariage"

    if re.search(r"travail|bureau|professionnel", msg):
        return "travail"

    return None


def extract_category(msg):
    """
    Détecte la catégorie produit.
    """

    if re.search(r"robe", msg):
        return "robe"

    if re.search(r"chaussure|sneaker|basket|escarpin|bott|sandale|mocassin", msg):
        return "chaussures"

    if re.search(r"\bsac\b|bag|clutch|tote|pochette|backpack", msg):
        return "sac"

    if re.search(r"pantalon|jean|jupe|legging|short|cargo", msg):
        return "pantalon"

    if re.search(r"chemise|t-shirt|haut|top|blazer|veste|pull|sweat|manteau|blouson|cardigan|hoodie", msg):
        return "haut"

    if re.search(r"accessoire|ceinture|lunette|bijou|collier|bracelet|chapeau|montre|écharpe|bonnet", msg):
        return "accessoire"

    return None


def extract_gender(msg):
    """
    Détecte homme / femme.
    """

    if re.search(r"\bhomme\b|masculin|mec|garçon|monsieur", msg):
        return "homme"

    if re.search(r"\bfemme\b|féminin|dame|fille|madame", msg):
        return "femme"

    return None


def extract_color(msg):
    """
    Détecte la couleur.
    Correction importante :
    on utilise \\b pour éviter de détecter 'or' dans 'sport'.
    """

    colors = [
        "noir", "blanc", "rouge", "bleu", "vert", "rose", "beige", "gris",
        "marron", "camel", "or", "argent", "nude", "bordeaux", "kaki",
        "marine", "crème", "corail", "jaune", "violet", "lilas",
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
#  ÉTAPE 2 : PLANIFIER LES TOOLS À APPELER
# ============================================================

def plan_steps(intent):
    """
    Crée le plan d'action de l'agent.
    C'est ici qu'on montre que l'agent est autonome :
    il décide quels tools appeler selon la demande.
    """

    steps = []

    # Recherche + comparaison dès qu'il y a une demande shopping ou style
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

    # Conseil styliste
    if intent["wants_styling"]:
        steps.append("fashion_stylist")

    # Construction de tenue complète
    if intent["wants_outfit"]:
        steps.append("outfit_builder")

    # Négociation / deals
    if intent["wants_deal"]:
        steps.append("negotiate_deal")

    # Fallback si rien n'est détecté
    if not steps:
        steps.append("search_products")
        steps.append("compare_prices")

    return steps


# ============================================================
#  ÉTAPE 3 : EXÉCUTER LES TOOLS
# ============================================================

def execute_steps(steps, intent):
    """
    Exécute les tools dans l'ordre prévu par plan_steps().
    """

    results = {}

    for step in steps:
        print(f"  [Agent] ▶ Tool : {step}")

        # ----------------------------------------------------
        # Tool 1 — Recherche produits
        # ----------------------------------------------------
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

            print(f"           → {len(results['products'])} produit(s) trouvé(s)")

        # ----------------------------------------------------
        # Tool 2 — Comparaison prix
        # ----------------------------------------------------
        elif step == "compare_prices":
            results["compared"] = compare_prices(
                products=results.get("products", []),
                budget=intent["budget"]
            )

            print(f"           → {len(results['compared'])} produit(s) classé(s)")

        # ----------------------------------------------------
        # Tool 3 — Fashion stylist
        # ----------------------------------------------------
        elif step == "fashion_stylist":
            results["styling"] = fashion_stylist(
                style=intent["style"],
                event=intent["event"],
                budget=intent["budget"]
            )

        # ----------------------------------------------------
        # Tool 4 — Outfit builder
        # ----------------------------------------------------
        elif step == "outfit_builder":
            products_for_outfit = results.get("compared", results.get("products", []))

            results["outfit"] = outfit_builder(
                event=intent["event"],
                style=intent["style"],
                budget=intent["budget"],
                gender=intent["gender"],
                color=intent["color"],
                products=products_for_outfit
            )

            # Bonus : options alternatives si generate_outfit_options existe
            if generate_outfit_options is not None:
                results["outfit_options"] = generate_outfit_options(
                    event=intent["event"],
                    style=intent["style"],
                    budget=intent["budget"],
                    gender=intent["gender"],
                    color=intent["color"],
                    products=products_for_outfit
                )

        # ----------------------------------------------------
        # Tool 5 — Négociation / deals
        # ----------------------------------------------------
        elif step == "negotiate_deal":
            results["deals"] = negotiate_deal(
                products=results.get("compared", results.get("products", []))
            )

    return results


# ============================================================
#  ÉTAPE 4 : FONCTIONS D'ÉVALUATION IA
# ============================================================

def calculate_simple_score(product, intent):
    """
    Calcule un score IA pour chaque produit.
    Ce score rend la recommandation plus intelligente.
    """

    score = 0

    price = product.get("final_price", product.get("price", 0))
    rating = product.get("rating", 0)
    discount = product.get("discount", 0) or 0

    # Note client
    if rating >= 4.5:
        score += 30
    elif rating >= 4:
        score += 25
    elif rating >= 3.5:
        score += 15

    # Budget respecté
    if intent["budget"] and price <= intent["budget"]:
        score += 25

    # Promotion
    if discount > 0:
        score += min(discount, 20)

    # Proximité au budget : on valorise les produits proches du budget (entre 70% et 100%)
    if intent["budget"]:
        ratio = price / intent["budget"]
        if 0.70 <= ratio <= 1.0:
            score += 20      # très proche du budget → bonus fort
        elif 0.50 <= ratio < 0.70:
            score += 10      # acceptable
        elif ratio < 0.50:
            score += 0       # trop éloigné → pas de bonus
    else:
        # Sans budget précis : légère préférence pour les prix modérés
        if price <= 150:
            score += 10

    # Correspondance catégorie
    if intent["category"] and product.get("category") == intent["category"]:
        score += 10

    # Correspondance genre
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
        reasons.append("il respecte ton budget")

    if rating >= 4:
        reasons.append("il a une bonne note client")

    if discount > 0:
        reasons.append("il est en promotion")

    if intent["category"] and product.get("category") == intent["category"]:
        reasons.append(f"il correspond à la catégorie {intent['category']}")

    if intent["gender"] and product.get("gender") == intent["gender"]:
        reasons.append(f"il est adapté pour {intent['gender']}")

    if not reasons:
        return "Ce produit est recommandé car il correspond globalement à ta recherche."

    return "Ce produit est recommandé car " + ", ".join(reasons) + "."


# ============================================================
#  ÉTAPE 5 : CONSTRUIRE LA RÉPONSE FINALE
# ============================================================

def build_response(results, intent, steps=None):
    """
    Crée la réponse finale affichée à l'utilisateur.
    Cette réponse est organisée pour être claire dans une interface de chat.
    """

    lines = []

    # --------------------------------------------------------
    # Raisonnement visible
    # --------------------------------------------------------
    lines.append("🧠 Raisonnement de l'agent :")
    lines.append(f"   - Style détecté : {intent['style']}")
    lines.append(f"   - Événement détecté : {intent['event']}")

    if intent["budget"]:
        lines.append(f"   - Budget détecté : {intent['budget']} DT")
    else:
        lines.append("   - Budget non précisé")

    if intent["category"]:
        lines.append(f"   - Catégorie détectée : {intent['category']}")

    if intent["gender"]:
        lines.append(f"   - Genre détecté : {intent['gender']}")

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

    lines.append(f"   - Tools utilisés : {', '.join(used_tools)}")
    lines.append("")

    # --------------------------------------------------------
    # Plan d'action
    # --------------------------------------------------------
    if steps:
        lines.append("📋 Plan d'action :")
        for i, step in enumerate(steps, 1):
            lines.append(f"   {i}. {step}")
        lines.append("")

    # --------------------------------------------------------
    # Introduction personnalisée
    # --------------------------------------------------------
    if intent["wants_outfit"]:
        intro = f"Voici une tenue complète pour {intent['event']} (style {intent['style']})"

        if intent["budget"]:
            intro += f" — budget {intent['budget']} DT"

        lines.append(intro + " :\n")

    elif intent["wants_styling"]:
        lines.append(f"Pour un look {intent['style']} ({intent['event']}), voici mes suggestions :\n")

    else:
        intro = "Voici les produits correspondant à ta demande"
        filters = []

        if intent["gender"]:
            filters.append(intent["gender"])

        if intent["category"]:
            filters.append(intent["category"])

        if intent["color"]:
            filters.append("couleur " + intent["color"])

        if intent["brand"]:
            filters.append(intent["brand"])

        if intent["budget"]:
            filters.append(f"budget {intent['budget']} DT")

        if filters:
            intro += f" ({', '.join(filters)})"

        lines.append(intro + " :\n")

    # --------------------------------------------------------
    # Top produits
    # --------------------------------------------------------
    compared = results.get("compared", [])

    # ── Tri affiné pour le top 3 : prioriser les produits proches du budget
    if compared and intent["budget"]:
        budget = intent["budget"]
        # Séparer produits dans le budget vs hors budget
        in_budget  = [p for p in compared if p.get("final_price", p["price"]) <= budget]
        out_budget = [p for p in compared if p.get("final_price", p["price"]) >  budget]

        # Dans le budget : trier par proximité décroissante (les plus chers en premier)
        in_budget.sort(key=lambda p: p.get("final_price", p["price"]), reverse=True)

        # Hors budget : trier par écart croissant (le moins cher hors budget en premier)
        out_budget.sort(key=lambda p: p.get("final_price", p["price"]))

        compared_display = in_budget + out_budget
    else:
        compared_display = compared

    if compared:
        lines.append("🏆 Meilleurs choix :")

        for i, product in enumerate(compared_display[:3]):
            final_price = product.get("final_price", product.get("price", 0))
            savings = product.get("savings", 0)
            discount = product.get("discount", 0) or 0
            promo = f" (promo -{discount}% ✨)" if savings > 0 else ""

            colors = ", ".join(product.get("colors", [])[:2])
            sizes = "/".join(product.get("sizes", [])[:4])
            gender_label = {"femme": "👩", "homme": "👨"}.get(product.get("gender"), "")

            ai_score = calculate_simple_score(product, intent)

            lines.append(
                f"  {i+1}. {gender_label} {product['name']} — {final_price} DT{promo}\n"
                f"     Marque : {product['brand']}  |  Note : {product['rating']}/5  |  Score IA : {ai_score}/100\n"
                f"     Couleurs : {colors}  |  Tailles : {sizes}\n"
                f"     Pourquoi ? {explain_choice(product, intent)}\n"
                f"     🔗 {product['url']}"
            )

        lines.append("")

    # --------------------------------------------------------
    # Conseil styliste
    # --------------------------------------------------------
    styling = results.get("styling")

    if styling:
        lines.append(f"💡 Conseil style : {styling['tip']}\n")
    # --------------------------------------------------------
    # Tenue complète
    # --------------------------------------------------------
    outfit = results.get("outfit")

    if outfit:
        lines.append("👗 Tenue complète :")
        lines.append(f"   Haut        : {outfit['top']}")
        lines.append(f"   Bas         : {outfit['bottom']}")
        lines.append(f"   Chaussures  : {outfit['shoes']}")
        lines.append(f"   Accessoire  : {outfit['accessory']}")
        lines.append(f"   💰 Total estimé : {outfit['total_price']} DT")

        # Si tools_bonus.py n'a pas trouvé toutes les pièces sans dépasser le budget
        if outfit.get("missing_items"):
            lines.append(f"   ⚠️ Tenue incomplète : éléments manquants → {', '.join(outfit['missing_items'])}.")
            lines.append("   Cela arrive parce que l'agent essaie de respecter ton budget.\n")

        # Vérification budget
        if intent["budget"] and outfit["total_price"] > intent["budget"]:
            difference = round(outfit["total_price"] - intent["budget"], 2)
            lines.append(f"   ⚠️ Cette tenue dépasse le budget de {difference} DT.")
            lines.append("   Je recommande d'augmenter le budget ou de retirer un accessoire.")
            lines.append("   💡 Alternative budget : privilégier les produits en promotion ou supprimer l'accessoire.\n")

        elif intent["budget"]:
            remaining = round(intent["budget"] - outfit["total_price"], 2)
            lines.append(f"   ✅ Cette tenue respecte ton budget. Budget restant : {remaining} DT.\n")

        else:
            lines.append("")

    # --------------------------------------------------------
    # Options alternatives
    # --------------------------------------------------------
    outfit_options = results.get("outfit_options", [])

    if outfit_options:
        lines.append("✨ Options alternatives :")

        for option in outfit_options:
            outfit_data = option["outfit"]

            lines.append(f"   {option['label']} — {outfit_data['total_price']} DT")
            lines.append(f"      {option['description']}")
            lines.append(f"      Haut : {outfit_data['top']}")
            lines.append(f"      Bas : {outfit_data['bottom']}")
            lines.append(f"      Chaussures : {outfit_data['shoes']}")
            lines.append(f"      Accessoire : {outfit_data['accessory']}")
            lines.append("")

    # --------------------------------------------------------
    # Deals / promotions
    # --------------------------------------------------------
    deals = results.get("deals", [])

    if deals:
        lines.append("🔥 Meilleures offres du moment :")

        for deal in deals:
            lines.append(
                f"   - {deal['name']} : {deal['original_price']} DT → {deal['discounted_price']} DT"
                f"  (-{deal['discount']}%)"
            )

    # --------------------------------------------------------
    # Aucun résultat
    # --------------------------------------------------------
    if not compared and not outfit and not deals:
        lines.append("😕 Aucun produit trouvé avec ces critères.")
        lines.append("   Essaie d'élargir ton budget ou de changer de style.")

    # --------------------------------------------------------
    # Décision finale
    # --------------------------------------------------------
    lines.append("")
    lines.append("✅ Décision finale de l'agent :")

    if intent["budget"]:
        lines.append("   J'ai privilégié les produits avec le meilleur rapport qualité/prix selon ton budget.")
    else:
        lines.append("   Comme aucun budget précis n'a été donné, j'ai proposé des options variées.")

    if intent["style"]:
        lines.append(f"   Le style principal retenu est : {intent['style']}.")

    lines.append("   La recommandation combine prix, style, note client et promotions disponibles.")

    return "\n".join(lines)


# ============================================================
#  ÉTAPE 6 : INTERACTION DYNAMIQUE
# ============================================================

def detect_missing_info(intent):
    """
    Détecte les informations importantes manquantes.
    On ne bloque pas sur l'occasion car 'casual' peut être une valeur par défaut acceptable.
    """

    missing = []

    # Pour construire une tenue complète, le budget est important.
    if intent["wants_outfit"] and not intent["budget"]:
        missing.append("budget")

    # Pour construire une tenue complète, le genre aide à choisir les bons produits.
    if intent["wants_outfit"] and not intent["gender"]:
        missing.append("genre")

    return missing


# ============================================================
#  ÉTAPE 7 : FONCTION PRINCIPALE DE L'AGENT
# ============================================================

# Contexte persistant entre les tours de conversation
_pending_intent = None


def merge_intents(base, update):
    """
    Fusionne deux intents : garde les valeurs de `base` si `update` ne les fournit pas.
    Les booléens sont combinés avec OR (un True dans l'un suffit).
    """
    merged = {}
    bool_keys = {"wants_styling", "wants_search", "wants_deal", "wants_outfit"}
    for key in base:
        base_val = base[key]
        upd_val  = update.get(key)
        if key in bool_keys:
            merged[key] = base_val or upd_val
        else:
            # Garder la valeur du nouveau message si elle est non-None, sinon celle du précédent
            merged[key] = upd_val if upd_val is not None else base_val

    # Appliquer le fallback "casual" sur event uniquement (style a toujours une valeur)
    if merged.get("event") is None:
        merged["event"] = "casual"

    if merged.get("event") is None:
        merged["event"] = "casual"

    if merged.get("style") is None:
        merged["style"] = "casual"

    return merged


def run_agent(user_message):
    """
    Point d'entrée principal de l'agent.
    """
    global _pending_intent

    print(f"\n{'='*55}")
    print(f"[Agent] Message reçu : {user_message}")
    print(f"{'='*55}")

    # 1. Analyse de l'intention du message courant
    intent = analyze_intent(user_message)

    # 2. Fusionner avec l'intent en attente (si une question de suivi avait été posée)
    if _pending_intent is not None:
        intent = merge_intents(_pending_intent, intent)
        _pending_intent = None  # réinitialiser après fusion
    else:
        # Pas de fusion : appliquer le fallback "casual" sur event uniquement
        if intent.get("event") is None:
            intent["event"] = "casual"

        if intent.get("style") is None:
            intent["style"] = "casual"

    # 3. Interaction dynamique si information importante manquante
    missing = detect_missing_info(intent)

    if "budget" in missing:
        _pending_intent = intent  # sauvegarder l'intent courant pour le prochain tour
        return (
            "Pour construire une tenue complète adaptée, peux-tu préciser ton budget ?\n"
            "Exemples : 100 DT, 150 DT ou 300 DT."
        )

    if "genre" in missing:
        _pending_intent = intent  # sauvegarder l'intent courant pour le prochain tour
        return (
            "Pour mieux choisir les produits, peux-tu préciser si la tenue est pour homme ou femme ?\n"
            "Exemple : tenue chic femme 150dt ou tenue chic homme 150dt."
        )

    # 4. Affichage debug dans le terminal
    print("[Agent] Intention détectée :")
    for key, value in intent.items():
        if value is not None and value is not False:
            print(f"  {key:<18} → {value}")

    # 4. Planification
    steps = plan_steps(intent)

    print(f"\n[Agent] Plan d'action : {steps}")
    print()

    # 5. Exécution des tools
    results = execute_steps(steps, intent)

    # 6. Réponse finale
    final_response = build_response(results, intent, steps)

    return final_response


# ============================================================
#  ÉTAPE 8 : TESTS ET CHAT INTERACTIF
# ============================================================

if __name__ == "__main__":

    tests = [
        (
            "TEST 1 — Robe chic mariage femme 200 DT",
            "je veux une robe chic pour un mariage femme 200dt"
        ),
        (
            "TEST 2 — Tenue complète soirée femme 300 DT",
            "je veux une tenue complète pour une soirée femme 300dt"
        ),
        (
            "TEST 3 — Sneakers sport homme 120 DT",
            "je cherche des sneakers sport pour homme 120dt"
        ),
        (
            "TEST 4 — Sac noir chic femme sans budget",
            "trouve moi un sac noir chic pour femme"
        ),
        (
            "TEST 5 — Réduction pantalon homme 100 DT",
            "cherche une réduction sur un pantalon homme 100dt"
        ),
        (
            "TEST 6 — Blazer Zara femme taille M",
            "je veux un blazer Zara femme taille M"
        ),
        (
            "TEST 7 — Tenue casual homme budget limité 80 DT",
            "tenue casual homme 80dt"
        ),
    ]

    # --------------------------------------------------------
    # Tests automatiques
    # --------------------------------------------------------
    for title, message in tests:
        print(f"\n{'#'*55}")
        print(f"  {title}")
        print(f"{'#'*55}")

        response = run_agent(message)

        print(f"\n{'─'*55}")
        print("  RÉPONSE DE L'AGENT :")
        print(f"{'─'*55}")
        print(response)

    # --------------------------------------------------------
    # Chat interactif en boucle
    # --------------------------------------------------------
    print(f"\n{'#'*55}")
    print("  CHAT INTERACTIF — écris ta propre demande")
    print(f"{'#'*55}")
    print("  Exemples :")
    print("    'je veux une robe casual femme 80dt'")
    print("    'tenue complète soirée femme 250dt'")
    print("    'cherche une réduction sac femme noir'")
    print("    'sneakers homme blanc 110dt'")
    print("    'tenue casual homme 80dt'")
    print("  Tape 'exit' pour quitter.")
    print(f"{'─'*55}")

    while True:
        user_message = input("Toi : ")
 
        if user_message.lower().strip() in ["exit", "quit", "q"]:
            print("Agent : Merci, à bientôt !")
            break

        response = run_agent(user_message)

        print(f"\n{'─'*55}")
        print("  RÉPONSE DE L'AGENT :")
        print(f"{'─'*55}")
        print(response)