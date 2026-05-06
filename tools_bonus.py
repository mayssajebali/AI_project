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
# - Générer plusieurs options : économique, équilibrée, premium
# ============================================================

import json
import os
print("✅ NOUVELLE VERSION tools_bonus.py CHARGÉE")

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
# 2. TOOL 3 : FASHION STYLIST
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

    tips_by_event = {
        "mariage": "Pour un mariage, choisis une tenue élégante avec des couleurs sobres ou pastel. Évite les pièces trop sportives.",
        "soirée": "Pour une soirée, privilégie une pièce forte comme un haut satiné, une robe élégante ou des chaussures habillées.",
        "soiree": "Pour une soirée, privilégie une pièce forte comme un haut satiné, une robe élégante ou des chaussures habillées.",
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
# 3. FONCTIONS UTILES POUR LES PRODUITS
# ============================================================

def get_final_price(product):
    """
    Retourne le prix final d'un produit.

    Si le produit contient déjà final_price, on l'utilise.
    Sinon, on applique la réduction discount au prix initial.
    """

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
        return color in colors

    if isinstance(colors, str):
        return color.lower() in colors.lower()

    return False


def product_style_matches(product, style):
    """
    Vérifie si le style du produit correspond au style demandé.
    """

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

    if gender and product.get("gender") and product.get("gender") != gender:
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

    if event == "soirée" or event == "soiree":
        banned_words = [
            "short de bain", "tongs", "running", "sport"
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
    if price <= 50:
        score += 15
    elif price <= 100:
        score += 10
    elif price <= 200:
        score += 5

    # Pénalité si incohérent avec l'événement
    if is_bad_for_event(product, event):
        score -= 50

    return max(score, 0)


# ============================================================
# 4. SÉLECTION INTELLIGENTE D'UN PRODUIT
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
    - Cela évite une tenue à 311 DT pour un budget de 150 DT.
    """

    candidates = []

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
        key=lambda product: (
            product.get("ai_score", 0),
            -product.get("final_price", 0)
        ),
        reverse=True
    )

    return candidates[0]


# ============================================================
# 5. CHOIX DES CATÉGORIES SELON L'ÉVÉNEMENT
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

    if event == "mariage" and gender == "femme":
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
# 6. TOOL 4 : OUTFIT BUILDER
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
# 7. TOOL 5 : NÉGOCIATION / DEALS
# ============================================================

def negotiate_deal(products=None):
    """
    Simule une négociation.

    Si products est vide, on lit directement catalogue.json.
    Retourne les 3 meilleures offres simulées.
    """

    if not products:
        products = load_catalogue()

    deals = []

    for product in products[:3]:
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
# 8. OPTIONS ALTERNATIVES : ÉCONOMIQUE / ÉQUILIBRÉ / PREMIUM
# ============================================================

def generate_outfit_options(event=None, style=None, budget=None, gender=None, color=None, products=None):
    """
    Génère 3 options de looks :
    - économique
    - équilibré
    - premium

    Correction importante :
    - Économique respecte un budget plus petit.
    - Équilibré respecte le budget utilisateur.
    - Premium peut dépasser un peu, donc strict_budget=False.
    """

    base_budget = budget or 300

    economic_budget = round(base_budget * 0.65)
    balanced_budget = base_budget
    premium_budget = round(base_budget * 1.3)

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

    premium = outfit_builder(
        event=event,
        style=style,
        budget=premium_budget,
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
            "label": "Équilibré",
            "description": "Meilleur équilibre entre style, prix et respect du budget.",
            "outfit": balanced
        },
        {
            "label": "Premium",
            "description": "Option plus complète, avec plus de style, pouvant dépasser légèrement le budget.",
            "outfit": premium
        }
    ]