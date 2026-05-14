# ============================================================
# tools_bonus.py — Personne 3 : IA & Raisonnement
# Agent IA de Shopping Intelligent
#
# Rôle de ce fichier :
# - Donner un conseil fashion selon style / événement / budget
# - Construire une tenue complète depuis catalogue.json
# - Respecter le budget autant que possible
# - Éviter les produits incohérents selon l'événement
# - Simuler des réductions / deals
# - Générer plusieurs options de tenues
# - Analyser le risque de regret après achat
# ============================================================

import json
import os


# ============================================================
# 1. CHARGEMENT DU CATALOGUE JSON
# ============================================================

def load_catalogue():
    """
    Charge les produits depuis catalogue.json.

    Le fichier catalogue.json doit être dans le même dossier que :
    - tools_bonus.py
    - orchestrator.py
    - tools_basic.py

    Cette fonction accepte deux formats :
    1. {"products": [...]}
    2. [...]
    """

    current_dir = os.path.dirname(os.path.abspath(__file__))
    catalogue_path = os.path.join(current_dir, "catalogue.json")

    try:
        with open(catalogue_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict) and "products" in data:
            return data["products"]

        if isinstance(data, list):
            return data

        return []

    except FileNotFoundError:
        print("Erreur : catalogue.json introuvable.")
        return []

    except json.JSONDecodeError:
        print("Erreur : catalogue.json contient une erreur JSON.")
        return []


# ============================================================
# 2. NORMALISATION DES VALEURS
# ============================================================

def normalize_event(event):
    """
    Normalise les noms d'événements pour éviter les incohérences.
    Exemple :
    - soirée -> soiree
    - fête -> soiree
    """

    if not event:
        return "casual"

    event = event.lower().strip()

    mapping = {
        "soirée": "soiree",
        "soiree": "soiree",
        "fête": "soiree",
        "fete": "soiree",
        "party": "soiree",
        "mariage": "mariage",
        "wedding": "mariage",
        "travail": "travail",
        "bureau": "travail",
        "meeting": "travail",
        "plage": "plage",
        "sport": "sport",
        "casual": "casual"
    }

    return mapping.get(event, event)


def normalize_style(style):
    """
    Normalise le style pour éviter les différences d'écriture.
    """

    if not style:
        return "casual"

    style = style.lower().strip()

    mapping = {
        "soirée": "soiree",
        "soiree": "soiree",
        "élégant": "chic",
        "elegant": "chic",
        "classe": "chic",
        "travail": "travail",
        "professionnel": "travail",
        "décontracté": "casual",
        "decontracte": "casual"
    }

    return mapping.get(style, style)


# ============================================================
# 3. TOOL 3 : FASHION STYLIST
# ============================================================

def fashion_stylist(style=None, event=None, budget=None):
    """
    Donne un conseil personnalisé selon :
    - le style demandé
    - l'occasion / événement
    - le budget

    Cette fonction ne cherche pas les produits.
    Elle agit comme un conseiller mode.
    """

    event = normalize_event(event)
    style = normalize_style(style)

    tips_by_event = {
        "mariage": "Pour un mariage, choisis une tenue élégante avec des couleurs sobres ou pastel. Évite les pièces trop sportives.",
        "soiree": "Pour une soirée, privilégie une pièce forte comme une robe élégante, un haut satiné ou des chaussures habillées.",
        "travail": "Pour le travail, choisis un look professionnel : blazer, pantalon droit, chemise simple et couleurs neutres.",
        "plage": "Pour la plage, choisis des matières légères comme le lin ou le coton, avec des couleurs claires.",
        "sport": "Pour le sport, privilégie des vêtements confortables, respirants et adaptés au mouvement.",
        "casual": "Pour un look casual, choisis des pièces simples, confortables et faciles à porter au quotidien."
    }

    tips_by_style = {
        "chic": "Le style chic demande des coupes propres, des couleurs élégantes et peu d'accessoires.",
        "casual": "Le style casual doit rester simple, confortable et naturel.",
        "sport": "Le style sport doit mélanger confort, praticité et matières respirantes.",
        "boheme": "Le style bohème fonctionne bien avec des matières fluides, des couleurs douces et des accessoires naturels.",
        "mariage": "Pour un style mariage, il faut viser élégance, harmonie des couleurs et accessoires discrets.",
        "travail": "Pour un style travail, le meilleur choix est une tenue sobre, propre et professionnelle.",
        "soiree": "Pour une soirée, le look doit être élégant, moderne et un peu plus travaillé."
    }

    main_tip = tips_by_event.get(event, tips_by_event["casual"])
    style_tip = tips_by_style.get(style, "")

    if budget is None:
        budget_tip = "Comme le budget n'est pas précisé, je recommande de proposer plusieurs options à prix différents."
    elif budget <= 100:
        budget_tip = "Comme le budget est limité, il faut choisir des pièces simples, polyvalentes et éviter les accessoires trop chers."
    elif budget <= 250:
        budget_tip = "Avec ce budget, on peut construire un look équilibré avec une bonne pièce principale et des accessoires simples."
    else:
        budget_tip = "Avec ce budget confortable, on peut proposer un look plus complet avec meilleure qualité et accessoires assortis."

    return {
        "tip": f"{main_tip} {style_tip} {budget_tip}"
    }


# ============================================================
# 4. FONCTIONS UTILES POUR LES PRODUITS
# ============================================================

def get_final_price(product):
    """
    Retourne le prix final d'un produit.

    Si le produit contient déjà final_price, on l'utilise.
    Sinon, on applique la réduction discount au prix initial.
    """

    if not product:
        return 0

    if "final_price" in product:
        return product["final_price"]

    price = product.get("price", 0)
    discount = product.get("discount", 0) or 0

    return round(price * (1 - discount / 100), 2)


def product_has_color(product, color):
    """
    Vérifie si le produit contient la couleur demandée.
    """

    if not color:
        return True

    colors = product.get("colors", [])

    if isinstance(colors, list):
        color_lower = color.lower()
        return any(color_lower in c.lower() for c in colors)

    if isinstance(colors, str):
        return color.lower() in colors.lower()

    return False


def product_style_matches(product, style):
    """
    Vérifie si le style du produit correspond au style demandé.
    """

    style = normalize_style(style)

    if not style:
        return True

    product_style = product.get("style")

    if not product_style:
        return True

    if isinstance(product_style, list):
        return style in product_style

    if isinstance(product_style, str):
        return style == product_style

    return True


def product_matches(product, category=None, style=None, gender=None, color=None):
    """
    Vérifie si un produit correspond aux critères :
    - catégorie
    - style
    - genre
    - couleur
    """

    if category and product.get("category") != category:
        return False

    # unisex peut être proposé pour homme et femme
    product_gender = product.get("gender")
    if gender and product_gender and product_gender not in [gender, "unisex"]:
        return False

    if color and not product_has_color(product, color):
        return False

    if not product_style_matches(product, style):
        return False

    return True


def is_bad_for_event(product, event):
    """
    Évite les produits incohérents selon l'événement.

    Exemple :
    - Pour travail : éviter short de bain, tongs, lunettes de soleil...
    - Pour mariage : éviter jogging, tongs, hoodie...
    """

    event = normalize_event(event)

    name = product.get("name", "").lower()
    category = product.get("category", "").lower()

    if event == "travail":
        banned_words = [
            "short de bain", "bain", "plage", "tongs", "tong",
            "lunettes de soleil", "aviateur", "hoodie", "jogging",
            "sport", "running"
        ]
        return any(word in name for word in banned_words)

    if event == "mariage":
        banned_words = [
            "sport", "running", "jogging", "hoodie", "tongs",
            "short de bain", "bain", "plage"
        ]
        return any(word in name for word in banned_words)

    if event == "soiree":
        banned_words = [
            "short de bain", "bain", "plage", "tongs", "tong",
            "running", "jogging", "sport", "hoodie"
        ]
        return any(word in name for word in banned_words)

    return False


def calculate_product_score(product, budget=None, event=None):
    """
    Donne un score IA au produit.

    Le score dépend de :
    - note client
    - réduction
    - prix
    - budget
    - cohérence avec l'événement
    """

    score = 0

    rating = product.get("rating", 0)
    discount = product.get("discount", 0) or 0
    price = get_final_price(product)

    # Note client
    if rating >= 4.5:
        score += 30
    elif rating >= 4.0:
        score += 20
    elif rating >= 3.5:
        score += 10

    # Réduction
    if discount > 0:
        score += min(discount, 25)

    # Respect budget
    if budget and price <= budget:
        score += 25

    # Prix raisonnable
    if budget and budget > 0:
        ratio = price / budget
        if 0.6 <= ratio <= 1.0:
            score += 20
        elif ratio < 0.4:
            score += 2

    # Pénalité si incohérent avec l'événement
    if is_bad_for_event(product, event):
        score -= 50

    return max(score, 0)


# ============================================================
# 5. SÉLECTION INTELLIGENTE D'UN PRODUIT
# ============================================================

def select_best_product(
    catalogue,
    category,
    style=None,
    gender=None,
    color=None,
    remaining_budget=None,
    event=None,
    strict_budget=True
):
    """
    Sélectionne le meilleur produit d'une catégorie.

    Point important :
    - Si strict_budget=True, on ne choisit jamais un produit qui dépasse le budget restant.
    - Si aucun produit ne respecte le budget, on retourne None.
    - Cela évite une tenue incohérente ou trop chère.
    """

    event = normalize_event(event)
    style = normalize_style(style)

    candidates = []

    # On garde seulement les produits en stock
    catalogue = [p for p in catalogue if p.get("stock", True) is True]

    # Niveau 1 : critères complets
    for product in catalogue:
        if is_bad_for_event(product, event):
            continue

        if product_matches(product, category=category, style=style, gender=gender, color=color):
            price = get_final_price(product)

            if strict_budget and remaining_budget is not None and price > remaining_budget:
                continue

            product_copy = product.copy()
            product_copy["final_price"] = price
            product_copy["ai_score"] = calculate_product_score(
                product_copy,
                budget=remaining_budget,
                event=event
            )
            candidates.append(product_copy)

    # Niveau 2 : on relâche la couleur, mais on garde style + genre + catégorie
    if not candidates:
        for product in catalogue:
            if is_bad_for_event(product, event):
                continue

            if product_matches(product, category=category, style=style, gender=gender, color=None):
                price = get_final_price(product)

                if strict_budget and remaining_budget is not None and price > remaining_budget:
                    continue

                product_copy = product.copy()
                product_copy["final_price"] = price
                product_copy["ai_score"] = calculate_product_score(
                    product_copy,
                    budget=remaining_budget,
                    event=event
                )
                candidates.append(product_copy)

    # Niveau 3 : on relâche le style, mais on garde catégorie + genre
    if not candidates:
        for product in catalogue:
            if is_bad_for_event(product, event):
                continue

            if product_matches(product, category=category, style=None, gender=gender, color=None):
                price = get_final_price(product)

                if strict_budget and remaining_budget is not None and price > remaining_budget:
                    continue

                product_copy = product.copy()
                product_copy["final_price"] = price
                product_copy["ai_score"] = calculate_product_score(
                    product_copy,
                    budget=remaining_budget,
                    event=event
                )
                candidates.append(product_copy)

    if not candidates:
        return None

    # Trier par score élevé, puis prix plus bas
    candidates.sort(
        key=lambda p: (
            -p.get("ai_score", 0),
            p.get("final_price", 0)
        )
    )

    return candidates[0]


# ============================================================
# 6. CHOIX DES CATÉGORIES SELON L'ÉVÉNEMENT
# ============================================================

def get_outfit_categories(event=None, gender=None):
    """
    Détermine les pièces nécessaires pour construire une tenue.

    Exemple femme mariage :
    - robe
    - chaussures
    - sac

    Exemple travail :
    - haut
    - pantalon
    - chaussures
    - sac
    """

    event = normalize_event(event)

    if event == "mariage" and gender == "femme":
        return [
            ("top", "robe"),
            ("shoes", "chaussures"),
            ("accessory", "sac")
        ]

    if event == "soiree" and gender == "femme":
        return [
            ("top", "robe"),
            ("shoes", "chaussures"),
            ("accessory", "sac")
        ]

    if event == "travail":
        return [
            ("top", "haut"),
            ("bottom", "pantalon"),
            ("shoes", "chaussures"),
            ("accessory", "sac")
        ]

    if event == "plage":
        return [
            ("top", "haut"),
            ("bottom", "pantalon"),
            ("shoes", "chaussures"),
            ("accessory", "accessoire")
        ]

    return [
        ("top", "haut"),
        ("bottom", "pantalon"),
        ("shoes", "chaussures"),
        ("accessory", "accessoire")
    ]


# ============================================================
# 7. TOOL 4 : OUTFIT BUILDER
# ============================================================

def outfit_builder(
    event=None,
    style=None,
    budget=None,
    gender=None,
    color=None,
    products=None,
    strict_budget=True
):
    """
    Construit une tenue complète à partir des vrais produits.

    Fonctionnement :
    1. Prend les produits envoyés par orchestrator.py
    2. Sinon charge catalogue.json
    3. Sélectionne les pièces une par une
    4. Respecte le budget restant
    5. Si une pièce dépasse le budget, elle est ignorée
    6. Retourne aussi les pièces manquantes
    """

    event = normalize_event(event)
    style = normalize_style(style)

    if products:
        catalogue = products
    else:
        catalogue = load_catalogue()

    outfit_items = {}
    total_price = 0
    missing_items = []

    categories = get_outfit_categories(event=event, gender=gender)

    for key, category in categories:
        remaining_budget = None

        if budget is not None:
            remaining_budget = budget - total_price

        selected = select_best_product(
            catalogue=catalogue,
            category=category,
            style=style,
            gender=gender,
            color=color,
            remaining_budget=remaining_budget,
            event=event,
            strict_budget=strict_budget
        )

        if selected:
            outfit_items[key] = selected
            total_price += get_final_price(selected)
        else:
            missing_items.append(category)

    return {
        "top": outfit_items.get("top", {}).get("name", "Non trouvé"),
        "bottom": outfit_items.get("bottom", {}).get("name", "—"),
        "shoes": outfit_items.get("shoes", {}).get("name", "Non trouvé"),
        "accessory": outfit_items.get("accessory", {}).get("name", "Non trouvé"),
        "total_price": round(total_price, 2),
        "source": "catalogue.json",
        "details": outfit_items,
        "missing_items": missing_items,
        "is_complete": len(missing_items) == 0
    }


# ============================================================
# 8. TOOL 5 : NÉGOCIATION / DEALS
# ============================================================

def negotiate_deal(products=None):
    """
    Simule une négociation.

    Si products est vide, on lit directement catalogue.json.
    Retourne les 3 meilleures offres simulées.

    Correction :
    - On utilise les produits déjà filtrés par l'orchestrateur.
    - On évite les produits sans stock.
    - On privilégie les vrais produits avec réduction ou prix intéressant.
    """

    if not products:
        products = load_catalogue()

    valid_products = [
        p for p in products
        if p.get("stock", True) is True
    ]

    # Trier pour éviter des deals incohérents :
    # produits déjà en promo d'abord, puis meilleur rapport qualité/prix
    valid_products.sort(
        key=lambda p: (
            -(p.get("discount", 0) or 0),
            -p.get("rating", 0),
            get_final_price(p)
        )
    )

    deals = []

    for product in valid_products[:3]:
        price = product.get("price", 0)
        existing_discount = product.get("discount", 0) or 0

        if price >= 200:
            extra_discount = 15
        elif price >= 100:
            extra_discount = 10
        else:
            extra_discount = 5

        total_discount = min(existing_discount + extra_discount, 40)
        discounted_price = round(price * (1 - total_discount / 100), 2)

        deals.append({
            "name": product.get("name", "Produit inconnu"),
            "original_price": price,
            "discounted_price": discounted_price,
            "discount": total_discount
        })

    return deals


# ============================================================
# 9. OPTIONS ALTERNATIVES : ÉCONOMIQUE / RECOMMANDÉ / STYLÉE
# ============================================================

def generate_outfit_options(event=None, style=None, budget=None, gender=None, color=None, products=None):
    """
    Génère 3 options de looks :
    - Économique : respecte un budget plus petit.
    - Recommandé : respecte le budget utilisateur.
    - Alternative stylée : peut utiliser un budget plus large.

    Remarque :
    On évite le mot "Premium", car parfois l'option stylée peut coûter moins cher
    si le catalogue contient une meilleure combinaison moins chère.
    """

    event = normalize_event(event)
    style = normalize_style(style)

    base_budget = budget or 300

    economic_budget = round(base_budget * 0.65)
    balanced_budget = base_budget
    stylish_budget = round(base_budget * 1.3)

    economic = outfit_builder(
        event=event,
        style=style,
        budget=economic_budget,
        gender=gender,
        color=color,
        products=products,
        strict_budget=True
    )

    balanced = outfit_builder(
        event=event,
        style=style,
        budget=balanced_budget,
        gender=gender,
        color=color,
        products=products,
        strict_budget=True
    )

    stylish = outfit_builder(
        event=event,
        style=style,
        budget=stylish_budget,
        gender=gender,
        color=color,
        products=products,
        strict_budget=False
    )

    return [
        {
            "label": "Économique",
            "description": "Option la moins chère possible. Certaines pièces peuvent manquer si le budget est trop serré.",
            "outfit": economic
        },
        {
            "label": "Recommandé",
            "description": "Meilleur équilibre entre style, prix et respect du budget.",
            "outfit": balanced
        },
        {
            "label": "Alternative stylée",
            "description": "Option plus stylée selon les meilleurs produits disponibles, pas forcément la plus chère.",
            "outfit": stylish
        }
    ]


# ============================================================
# 10. TOOL 6 : ANTI-REGRET ANALYZER
# ============================================================

def anti_regret_analyzer(product=None, outfit=None, intent=None):
    """
    Analyse le risque de regret après achat.

    L'objectif :
    - éviter les achats inutiles
    - vérifier le budget
    - favoriser les pièces réutilisables
    - pénaliser les tenues incomplètes
    - expliquer la décision de l'agent

    Retourne :
    {
        "risk": "faible" | "moyen" | "élevé",
        "score": int,
        "reasons": list[str],
        "advice": str
    }
    """

    reasons = []
    score = 100

    budget = None
    event = None
    style = None

    if intent:
        budget = intent.get("budget")
        event = normalize_event(intent.get("event"))
        style = normalize_style(intent.get("style"))

    # --------------------------------------------------------
    # Cas 1 : analyse d'un produit seul
    # --------------------------------------------------------
    if product:
        price = get_final_price(product)

        # Budget
        if budget:
            if price > budget:
                score -= 35
                reasons.append("le produit dépasse ton budget")
            else:
                reasons.append("le produit respecte ton budget")

        # Note client / qualité
        rating = product.get("rating", 0)
        if rating >= 4.3:
            reasons.append("il a une bonne note client")
        elif rating < 3.8:
            score -= 15
            reasons.append("sa note client est moyenne")

        # Réutilisation estimée selon catégorie
        category = product.get("category", "")
        reusable_categories = ["haut", "pantalon", "chaussures", "sac", "accessoire"]

        if category in reusable_categories:
            reasons.append("c'est une pièce facile à réutiliser")
        elif category == "robe" and event in ["mariage", "soiree"]:
            score -= 10
            reasons.append("cette pièce peut être moins réutilisable après l'événement")

        # Cohérence avec l'événement
        if event and is_bad_for_event(product, event):
            score -= 30
            reasons.append("le produit n'est pas très adapté à l'occasion")

        # Cohérence avec le style
        if style and not product_style_matches(product, style):
            score -= 10
            reasons.append("le style ne correspond pas parfaitement à ta demande")

    # --------------------------------------------------------
    # Cas 2 : analyse d'une tenue complète
    # --------------------------------------------------------
    if outfit:
        total_price = outfit.get("total_price", 0)

        # Budget total
        if budget:
            if total_price > budget:
                score -= 30
                reasons.append("la tenue dépasse le budget total")
            else:
                reasons.append("la tenue respecte le budget total")

        # Tenue complète ou incomplète
        missing_items = outfit.get("missing_items", [])

        if missing_items:
            missing_count = len(missing_items)
            score -= 25 * missing_count
            reasons.append("la tenue est incomplète car certaines pièces manquent")
        else:
            reasons.append("la tenue est complète")

        # Cohérence globale du look
        details = outfit.get("details", {})
        if len(details) >= 2:
            reasons.append("les pièces peuvent être combinées ensemble dans un look cohérent")

    # --------------------------------------------------------
    # Sécurité score entre 0 et 100
    # --------------------------------------------------------
    score = max(0, min(score, 100))

    # --------------------------------------------------------
    # Niveau de risque
    # --------------------------------------------------------
    if outfit and outfit.get("missing_items"):
        risk = "moyen" if score >= 50 else "élevé"
        advice = "Achat partiel : la base est intéressante, mais il manque encore une pièce pour compléter le look."
    elif score >= 75:
        risk = "faible"
        advice = "Achat recommandé : le choix est cohérent, utile et peu risqué."
    elif score >= 50:
        risk = "moyen"
        advice = "Achat acceptable, mais il faut vérifier s'il sera vraiment réutilisable."
    else:
        risk = "élevé"
        advice = "Achat à éviter ou à remplacer par une option plus polyvalente."

    if not reasons:
        reasons.append("analyse basée sur le budget, la cohérence et la réutilisation")

    return {
        "risk": risk,
        "score": score,
        "reasons": reasons,
        "advice": advice
    }