# ============================================================
#  orchestrator.py — Personne 1 : L'Orchestrateur
#  Agent IA de Shopping Intelligent
#  Branché sur tools_basic.py (Personne 2)
# ============================================================

import re
from tools_basic import search_products, compare_prices, get_product_by_id, get_catalogue_stats


# ============================================================
#  ÉTAPE 1 : Analyser l'intention de l'utilisateur
# ============================================================

def analyze_intent(message):
    msg = message.lower()

    return {
        "wants_styling": bool(re.search(r"style|tenue|outfit|look|mariage|casual|chic|élégant|soirée|plage|travail|bureau", msg)),
        "wants_search":  bool(re.search(r"cherche|trouve|veux|besoin|acheter|produit|montre|show", msg)),
        "wants_deal":    bool(re.search(r"réduction|promo|moins cher|deal|remise|négoci|offre|solde", msg)),
        "wants_outfit":  bool(re.search(r"tenue complète|outfit complet|look complet|assembl|tenue pour", msg)),
        "budget":        extract_budget(msg),
        "event":         extract_event(msg),
        "style":         extract_style(msg),
        "category":      extract_category(msg),
        "gender":        extract_gender(msg),
        "color":         extract_color(msg),
        "brand":         extract_brand(msg),
        "size":          extract_size(msg),
    }


def extract_budget(msg):
    match = re.search(r"(\d+)\s*(dt|tnd|dinar|€|eur|\$)?", msg)
    return int(match.group(1)) if match else None


def extract_event(msg):
    if re.search(r"mariage|wedding",          msg): return "mariage"
    if re.search(r"travail|bureau|meeting",   msg): return "travail"
    if re.search(r"soirée|party|fête|gala",   msg): return "soirée"
    if re.search(r"plage|beach|piscine",      msg): return "plage"
    if re.search(r"sport|gym|fitness|running", msg): return "sport"
    return "casual"


def extract_style(msg):
    if re.search(r"chic|élégant|classe|luxe",  msg): return "chic"
    if re.search(r"casual|décontract|simple",  msg): return "casual"
    if re.search(r"sport|gym|fitness",          msg): return "sport"
    if re.search(r"bohème|boho|boheme",         msg): return "boheme"
    if re.search(r"soirée|fête|gala",           msg): return "soiree"
    if re.search(r"mariage|wedding",            msg): return "mariage"
    if re.search(r"travail|bureau|professionnel",msg): return "travail"
    return "casual"


def extract_category(msg):
    if re.search(r"robe",                        msg): return "robe"
    if re.search(r"chaussure|sneaker|basket|escarpin|bott|sandale|mocassin", msg): return "chaussures"
    if re.search(r"\bsac\b|bag|clutch|tote|pochette|backpack", msg): return "sac"
    if re.search(r"pantalon|jean|jupe|legging|short|cargo", msg): return "pantalon"
    if re.search(r"chemise|t-shirt|haut|top|blazer|veste|pull|sweat|manteau|blouson|cardigan", msg): return "haut"
    if re.search(r"accessoire|ceinture|lunette|bijou|collier|bracelet|chapeau|montre|écharpe|bonnet", msg): return "accessoire"
    return None


def extract_gender(msg):
    if re.search(r"\bhomme\b|masculin|mec|garçon|monsieur", msg): return "homme"
    if re.search(r"\bfemme\b|féminin|dame|fille|madame",    msg): return "femme"
    return None


def extract_color(msg):
    colors = ["noir","blanc","rouge","bleu","vert","rose","beige","gris","marron",
              "camel","or","argent","nude","bordeaux","kaki","marine","crème",
              "corail","jaune","violet","lilas","emeraude","turquoise","champagne"]
    for c in colors:
        if c in msg:
            return c
    return None


def extract_brand(msg):
    brands = ["zara","h&m","mango","nike","adidas","uniqlo","massimo dutti",
              "stradivarius","bershka","pull&bear","jack & jones","selected",
              "only & sons","puma","new balance","converse","vans","pronovias",
              "timberland","birkenstock","columbia","reebok","under armour"]
    for b in brands:
        if b in msg:
            return b.title()
    return None


def extract_size(msg):
    sizes_vetement   = ["xs","s","m","l","xl","xxl"]
    sizes_chaussure  = ["36","37","38","39","40","41","42","43","44","45"]
    for s in sizes_vetement + sizes_chaussure:
        pattern = r"\b" + re.escape(s) + r"\b"
        if re.search(pattern, msg):
            return s.upper() if s in sizes_vetement else s
    return None


# ============================================================
#  ÉTAPE 2 : Planifier les tools à appeler
# ============================================================

def plan_steps(intent):
    steps = []

    # Toujours chercher + comparer si on a une demande produit
    if (intent["wants_search"]
            or intent["budget"]
            or intent["category"]
            or intent["color"]
            or intent["brand"]
            or intent["size"]):
        steps.append("search_products")
        steps.append("compare_prices")

    # Conseil style / styliste (Personne 3)
    if intent["wants_styling"] and "fashion_stylist" not in steps:
        steps.append("fashion_stylist")

    # Tenue complète (Personne 3)
    if intent["wants_outfit"]:
        steps.append("outfit_builder")

    # Deals / réductions (Personne 3)
    if intent["wants_deal"]:
        steps.append("negotiate_deal")

    # Fallback minimal
    if not steps:
        steps.append("search_products")
        steps.append("compare_prices")

    return steps


# ============================================================
#  ÉTAPE 3 : Exécuter les tools selon le plan
# ============================================================

def execute_steps(steps, intent):
    results = {}

    for step in steps:
        print(f"  [Agent] ▶ Tool : {step}")

        # ── Tools Personne 2 (implémentés) ──────────────────

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

        elif step == "compare_prices":
            results["compared"] = compare_prices(
                products=results.get("products", []),
                budget=intent["budget"]
            )
            print(f"           → {len(results['compared'])} produit(s) classé(s)")

        # ── Tools Personne 3 (mocks — à remplacer) ──────────

        elif step == "fashion_stylist":
            # from tools_bonus import fashion_stylist  ← décommenter quand Personne 3 livre
            results["styling"] = _mock_fashion_stylist(
                style=intent["style"],
                event=intent["event"],
                budget=intent["budget"]
            )

        elif step == "outfit_builder":
            # from tools_bonus import outfit_builder  ← décommenter quand Personne 3 livre
            results["outfit"] = _mock_outfit_builder(
                event=intent["event"],
                style=intent["style"],
                budget=intent["budget"]
            )

        elif step == "negotiate_deal":
            # from tools_bonus import negotiate_deal  ← décommenter quand Personne 3 livre
            results["deals"] = _mock_negotiate_deal(
                products=results.get("compared", results.get("products", []))
            )

    return results


# ============================================================
#  ÉTAPE 4 : Assembler la réponse finale
# ============================================================

def build_response(results, intent):
    lines = []

    # ── Intro personnalisée ──────────────────────────────────
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
        if intent["gender"]:   filters.append(intent["gender"])
        if intent["category"]: filters.append(intent["category"])
        if intent["color"]:    filters.append("couleur " + intent["color"])
        if intent["brand"]:    filters.append(intent["brand"])
        if intent["budget"]:   filters.append(f"budget {intent['budget']} DT")
        if filters:
            intro += f" ({', '.join(filters)})"
        lines.append(intro + " :\n")

    # ── Top 3 produits comparés ──────────────────────────────
    compared = results.get("compared", [])
    if compared:
        lines.append("🏆 Meilleurs choix :")
        for i, p in enumerate(compared[:3]):
            fp      = p.get("final_price", p["price"])
            savings = p.get("savings", 0)
            promo   = f" (promo -{p.get('discount')}% ✨)" if savings > 0 else ""
            colors  = ", ".join(p.get("colors", [])[:2])
            sizes   = "/".join(p.get("sizes", [])[:4])
            gender_label = {"femme": "👩", "homme": "👨"}.get(p.get("gender"), "")
            lines.append(
                f"  {i+1}. {gender_label} {p['name']} — {fp} DT{promo}\n"
                f"     Marque : {p['brand']}  |  Note : {p['rating']}/5\n"
                f"     Couleurs : {colors}  |  Tailles : {sizes}\n"
                f"     🔗 {p['url']}"
            )
        lines.append("")

    # ── Conseil du styliste (Personne 3) ────────────────────
    styling = results.get("styling")
    if styling:
        lines.append(f"💡 Conseil style : {styling['tip']}\n")

    # ── Outfit complet (Personne 3) ─────────────────────────
    outfit = results.get("outfit")
    if outfit:
        lines.append("👗 Tenue complète :")
        lines.append(f"   Haut        : {outfit['top']}")
        lines.append(f"   Bas         : {outfit['bottom']}")
        lines.append(f"   Chaussures  : {outfit['shoes']}")
        lines.append(f"   Accessoire  : {outfit['accessory']}")
        lines.append(f"   💰 Total estimé : {outfit['total_price']} DT\n")

    # ── Deals / promotions (Personne 3) ─────────────────────
    deals = results.get("deals", [])
    if deals:
        lines.append("🔥 Meilleures offres du moment :")
        for d in deals:
            lines.append(
                f"   - {d['name']} : {d['original_price']} DT → {d['discounted_price']} DT"
                f"  (-{d['discount']}%)"
            )

    # ── Message si aucun résultat ────────────────────────────
    if not compared and not outfit and not deals:
        lines.append("😕 Aucun produit trouvé avec ces critères.")
        lines.append("   Essaie d'élargir ton budget ou de changer de style.")

    return "\n".join(lines)


# ============================================================
#  FONCTION PRINCIPALE — point d'entrée de l'agent
# ============================================================

def run_agent(user_message):
    print(f"\n{'='*55}")
    print(f"[Agent] Message reçu : {user_message}")
    print(f"{'='*55}")

    # Étape 1 : analyser l'intention
    intent = analyze_intent(user_message)
    print(f"[Agent] Intention détectée :")
    for k, v in intent.items():
        if v is not None and v is not False:
            print(f"  {k:<18} → {v}")

    # Étape 2 : planifier les tools
    steps = plan_steps(intent)
    print(f"\n[Agent] Plan d'action : {steps}")
    print()

    # Étape 3 : exécuter les tools
    results = execute_steps(steps, intent)

    # Étape 4 : assembler la réponse
    final_response = build_response(results, intent)

    return final_response


# ============================================================
#  MOCKS TEMPORAIRES Personne 3
#  À remplacer par : from tools_bonus import ...
# ============================================================

def _mock_fashion_stylist(style=None, event=None, budget=None):
    tips = {
        "mariage":  "Optez pour une robe longue dans des tons pastel ou ivoire.",
        "soirée":   "Un haut satiné avec un pantalon tailleur fera toujours son effet.",
        "soiree":   "Un haut satiné avec un pantalon tailleur fera toujours son effet.",
        "travail":  "Un blazer structuré sur une tenue basique : élégance garantie.",
        "casual":   "Misez sur le confort avec des pièces en coton naturel.",
        "plage":    "Léger, coloré et respirant — la robe en lin est idéale.",
        "sport":    "Privilégiez des matières techniques respirantes et un fit ajusté.",
    }
    return {"tip": tips.get(event, tips["casual"])}


def _mock_outfit_builder(event=None, style=None, budget=None):
    outfits = {
        "mariage":  {"top": "Robe longue en dentelle ivoire", "bottom": "—", "shoes": "Escarpins dorés", "accessory": "Collier de perles", "total_price": 385},
        "soirée":   {"top": "Top satiné noir", "bottom": "Pantalon tailleur noir", "shoes": "Escarpins nude", "accessory": "Sac clutch argent", "total_price": 290},
        "soiree":   {"top": "Top satiné noir", "bottom": "Pantalon tailleur noir", "shoes": "Escarpins nude", "accessory": "Sac clutch argent", "total_price": 290},
        "travail":  {"top": "Blazer camel", "bottom": "Jean slim noir", "shoes": "Mocassins en cuir", "accessory": "Sac cabas beige", "total_price": 330},
        "plage":    {"top": "Top bandeau imprimé", "bottom": "Short en jean", "shoes": "Sandales plates", "accessory": "Panier osier", "total_price": 145},
        "sport":    {"top": "Brassière de sport", "bottom": "Legging taille haute", "shoes": "Sneakers blanches", "accessory": "Sac de sport", "total_price": 185},
        "casual":   {"top": "T-shirt en coton", "bottom": "Jean slim", "shoes": "Sneakers blanches", "accessory": "Tote bag canvas", "total_price": 175},
    }
    return outfits.get(event, outfits["casual"])


def _mock_negotiate_deal(products=None):
    if not products:
        return []
    deals = []
    for p in products[:2]:
        existing_discount = p.get("discount", 0) or 0
        extra = 10
        total_discount = min(existing_discount + extra, 40)
        deals.append({
            "name":             p["name"],
            "original_price":   p["price"],
            "discounted_price": round(p["price"] * (1 - total_discount / 100)),
            "discount":         total_discount,
        })
    return deals


# ============================================================
#  LANCEMENT DES TESTS
# ============================================================

if __name__ == "__main__":

    tests = [
        ("TEST 1 — Robe chic mariage femme 200 DT",
         "je veux une robe chic pour un mariage femme 200dt"),

        ("TEST 2 — Tenue complète soirée femme 300 DT",
         "je veux une tenue complète pour une soirée femme 300dt"),

        ("TEST 3 — Sneakers sport homme 120 DT",
         "je cherche des sneakers sport pour homme 120dt"),

        ("TEST 4 — Sac noir chic femme sans budget",
         "trouve moi un sac noir chic pour femme"),

        ("TEST 5 — Réduction pantalon homme 100 DT",
         "cherche une réduction sur un pantalon homme 100dt"),

        ("TEST 6 — Blazer Zara femme taille M",
         "je veux un blazer Zara femme taille M"),

        ("TEST 7 — Tenue casual homme budget limité 80 DT",
         "tenue casual homme 80dt"),
    ]

    for titre, message in tests:
        print(f"\n{'#'*55}")
        print(f"  {titre}")
        print(f"{'#'*55}")
        reponse = run_agent(message)
        print(f"\n{'─'*55}")
        print("  RÉPONSE DE L'AGENT :")
        print(f"{'─'*55}")
        print(reponse)

    # ── Test interactif ──────────────────────────────────────
    print(f"\n{'#'*55}")
    print("  TEST INTERACTIF — écris ta propre demande")
    print(f"{'#'*55}")
    print("  Exemples :")
    print("    'je veux une robe casual femme 80dt'")
    print("    'tenue complète soirée femme 250dt'")
    print("    'cherche une réduction sac femme noir'")
    print("    'sneakers homme blanc 110dt'")
    print(f"{'─'*55}")
    mon_message = input("Toi : ")
    reponse = run_agent(mon_message)
    print(f"\n{'─'*55}")
    print("  RÉPONSE DE L'AGENT :")
    print(f"{'─'*55}")
    print(reponse)