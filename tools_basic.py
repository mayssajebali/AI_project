# ============================================================
#  tools_basic.py — Personne 2 : Backend & Tools
#  Agent IA de Shopping Intelligent
#  Python pur, aucune bibliothèque externe requise
# ============================================================

import json
import os


# ============================================================
#  HELPER : Charger le catalogue JSON
# ============================================================

def load_catalogue():
    """
    Charge le fichier catalogue.json depuis le même dossier.
    Retourne une liste de dicts produits.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    catalogue_path = os.path.join(base_dir, "catalogue.json")

    with open(catalogue_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "products" in data:
        return data["products"]

    if isinstance(data, list):
        return data

    return []


# ============================================================
#  TOOL 1 : search_products()
#  Recherche des produits selon catégorie, budget, style,
#  genre, couleur, marque et taille
# ============================================================

def search_products(
    category=None,
    budget=None,
    style=None,
    gender=None,
    color=None,
    brand=None,
    size=None,
    in_stock_only=True
):
    """
    Recherche des produits dans le catalogue simulé.

    Paramètres :
        category     (str|None) : ex. "robe", "chaussures", "sac", "haut", "pantalon", "accessoire"
        budget       (int|None) : prix maximum en DT
        style        (str|None) : ex. "chic", "casual", "sport", "boheme", "soiree", "mariage", "travail"
        gender       (str|None) : "femme", "homme", "unisex"
        color        (str|None) : ex. "noir", "blanc", "rouge"
        brand        (str|None) : ex. "Zara", "Nike", "Mango"
        size         (str|None) : ex. "M", "42", "unique"
        in_stock_only (bool)    : ne retourner que les produits en stock (défaut : True)

    Retourne :
        list[dict] : liste de produits correspondants
                     (ou fallback progressif si aucun résultat)
    """
    catalogue = load_catalogue()

    # ── Filtre 0 : stock disponible
    if in_stock_only:
        catalogue = [p for p in catalogue if p.get("stock") is True]

    # ── Filtre 1 : genre
    #    "unisex" correspond à tout le monde
    result = catalogue
    if gender:
        result = [p for p in result if p.get("gender") == gender]

    # ── Filtre 2 : catégorie
    after_category = result
    if category:
        after_category = [p for p in result if p.get("category") == category]

    # ── Filtre 3 : budget (prix <= budget)
    after_budget = after_category
    if budget:
        after_budget = [p for p in after_category if p.get("price", 9999) <= budget]

    # ── Filtre 4 : style (le style demandé est dans la liste styles du produit)
    after_style = after_budget
    if style:
        after_style = [p for p in after_budget if style in p.get("style", [])]

    # ── Filtre 5 : couleur (recherche partielle, insensible à la casse)
    after_color = after_style
    if color:
        color_lower = color.lower()
        after_color = [
            p for p in after_style
            if any(color_lower in c.lower() for c in p.get("colors", []))
        ]

    # ── Filtre 6 : marque (insensible à la casse)
    after_brand = after_color
    if brand:
        brand_lower = brand.lower()
        after_brand = [
            p for p in after_color
            if brand_lower in p.get("brand", "").lower()
        ]

    # ── Filtre 7 : taille
    after_size = after_brand
    if size:
        after_size = [
            p for p in after_brand
            if size in p.get("sizes", [])
        ]

    final = after_size

    # ── Fallback progressif si liste vide ──────────────────
    # Niveau 1 : relâcher la taille
    if not final and size:
        final = after_brand

    # Niveau 2 : relâcher la marque
    if not final and brand:
        final = after_color

    # Niveau 3 : relâcher la couleur
    if not final and color:
        final = after_style

    # Niveau 4 : relâcher le style
    if not final and style:
        final = after_budget

    # Niveau 5 : relâcher le budget
    if not final and budget:
        final = after_category

    # Niveau 6 : relâcher la catégorie
    if not final and category:
        en_stock = [p for p in catalogue if p.get("stock") is True] if in_stock_only else catalogue
        final = en_stock

    # Niveau 7 : tout le catalogue (ultime fallback)
    if not final:
        final = catalogue

    return final


# ============================================================
#  TOOL 2 : compare_prices()
#  Trie et enrichit les produits selon le rapport qualité/prix
# ============================================================

def compare_prices(products=None, budget=None):
    """
    Compare et trie les produits selon le rapport qualité/prix.

    Paramètres :
        products (list[dict]|None) : liste de produits à comparer
                                     (si None → catalogue complet en stock)
        budget   (int|None)        : budget de l'utilisateur en DT

    Retourne :
        list[dict] : produits enrichis et triés
                     Champs ajoutés :
                       - value_score      : score qualité/prix (arrondi à 2 décimales)
                       - in_budget        : True si price <= budget
                       - final_price      : prix après remise éventuelle
                       - savings          : économie réalisée si remise > 0
                       - rank             : position dans le classement final
    """
    if products is None:
        products = load_catalogue()

    # ── Sécurité : filtrer les hors-stock
    produits_valides = [p for p in products if p.get("stock", True) is True]

    # ── Calcul du prix final (après remise)
    def prix_final(p):
        discount = p.get("discount", 0) or 0
        if discount > 0:
            return round(p["price"] * (1 - discount / 100), 2)
        return p["price"]

    # ── Calcul du score qualité/prix
    #    Formule : (rating / final_price) * 100 — plus élevé = meilleur rapport
    def calculer_score(p, fp):
        if fp == 0:
            return 0.0
        return round((p.get("rating", 4.0) / fp) * 100, 2)

    # ── Enrichissement de chaque produit
    produits_enrichis = []
    for p in produits_valides:
        produit = dict(p)                              # copie sans muter l'original
        fp = prix_final(p)
        produit["final_price"]  = fp
        produit["savings"]      = round(p["price"] - fp, 2) if fp < p["price"] else 0
        produit["value_score"]  = calculer_score(p, fp)
        produit["in_budget"]    = (fp <= budget) if budget else True
        produits_enrichis.append(produit)

    # ── Tri principal
    #    1. Produits dans le budget en premier
    #    2. Ensuite par prix final croissant
    #    3. En cas d'égalité de prix : meilleur score en tête
    produits_tries = sorted(
        produits_enrichis,
        key=lambda p: (
            0 if p["in_budget"] else 1,
            -p["value_score"],   # meilleur score en premier
            p["final_price"]     # à égalité, prix croissant
        )
    )

    # ── Ajout du rang final
    for rang, produit in enumerate(produits_tries, start=1):
        produit["rank"] = rang

    return produits_tries


# ============================================================
#  HELPER : get_product_by_id()
#  Récupère un produit unique par son ID
# ============================================================

def get_product_by_id(product_id):
    """
    Retourne un produit par son identifiant unique.

    Paramètres :
        product_id (str) : ex. "001", "042"

    Retourne :
        dict|None : le produit trouvé, ou None
    """
    catalogue = load_catalogue()
    for p in catalogue:
        if p["id"] == str(product_id).zfill(3):
            return p
    return None


# ============================================================
#  HELPER : get_catalogue_stats()
#  Retourne des statistiques sur le catalogue
# ============================================================

def get_catalogue_stats():
    """
    Retourne un résumé statistique du catalogue.

    Retourne :
        dict : {
            total, in_stock, categories, brands, styles,
            price_min, price_max, price_avg
        }
    """
    catalogue = load_catalogue()
    in_stock  = [p for p in catalogue if p.get("stock") is True]
    prices    = [p["price"] for p in catalogue]

    categories = {}
    for p in catalogue:
        cat = p.get("category", "autre")
        categories[cat] = categories.get(cat, 0) + 1

    brands = {}
    for p in catalogue:
        b = p.get("brand", "?")
        brands[b] = brands.get(b, 0) + 1

    all_styles = []
    for p in catalogue:
        all_styles.extend(p.get("style", []))
    style_counts = {}
    for s in all_styles:
        style_counts[s] = style_counts.get(s, 0) + 1

    return {
        "total":      len(catalogue),
        "in_stock":   len(in_stock),
        "categories": categories,
        "brands":     dict(sorted(brands.items(), key=lambda x: -x[1])[:10]),
        "styles":     style_counts,
        "price_min":  min(prices),
        "price_max":  max(prices),
        "price_avg":  round(sum(prices) / len(prices), 2),
    }