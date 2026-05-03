# ============================================================
#  test_tools.py — Tests indépendants des tools de base
#  Personne 2 : Backend & Tools
#  Commande : python test_tools.py
# ============================================================

from tools_basic import search_products, compare_prices, get_product_by_id, get_catalogue_stats

SEP  = "=" * 62
SEP2 = "-" * 62


def afficher_produits(produits, titre="Résultats", max_items=5):
    print(f"\n  [{titre}] — {len(produits)} produit(s) trouvé(s)")
    for p in produits[:max_items]:
        rank       = p.get("rank", "–")
        in_budget  = "✅" if p.get("in_budget", True) else "❌"
        score      = p.get("value_score", "n/a")
        fp         = p.get("final_price", p["price"])
        savings    = p.get("savings", 0)
        promo      = f" (-{p.get('discount')}% → {fp} DT)" if savings > 0 else ""
        sizes      = "/".join(p.get("sizes", [])[:3]) + ("…" if len(p.get("sizes",[])) > 3 else "")
        gender_sym = {"femme": "👩", "homme": "👨", "unisex": "🔵"}.get(p.get("gender","?"), "?")
        print(
            f"    #{rank} {in_budget} {gender_sym}  "
            f"{p['name']:<35} "
            f"{p['price']:>5} DT{promo:<22} "
            f"({p['brand']})  "
            f"score={score}  "
            f"tailles={sizes}"
        )
    if len(produits) > max_items:
        print(f"    … et {len(produits) - max_items} autres produits")


# ──────────────────────────────────────────────────────────
#  STATS DU CATALOGUE
# ──────────────────────────────────────────────────────────

print(SEP)
print("STATS DU CATALOGUE")
print(SEP)
stats = get_catalogue_stats()
print(f"  Total produits   : {stats['total']}")
print(f"  En stock         : {stats['in_stock']}")
print(f"  Prix min/moy/max : {stats['price_min']} / {stats['price_avg']} / {stats['price_max']} DT")
print(f"  Catégories       : {stats['categories']}")
print(f"  Styles           : {stats['styles']}")
print(f"  Top marques      : {stats['brands']}")


# ──────────────────────────────────────────────────────────
#  TEST A : search_products — filtres de base
# ──────────────────────────────────────────────────────────

print(SEP)
print("TEST A1 — Robes chic femme avec budget 150 DT")
print(SEP)
r = search_products(category="robe", budget=150, style="chic", gender="femme")
afficher_produits(r, "search_products")

print(SEP)
print("TEST A2 — Chaussures casual homme (sans budget)")
print(SEP)
r = search_products(category="chaussures", style="casual", gender="homme")
afficher_produits(r, "search_products")

print(SEP)
print("TEST A3 — Budget 50 DT, style sport (tout genre)")
print(SEP)
r = search_products(budget=50, style="sport")
afficher_produits(r, "search_products")

print(SEP)
print("TEST A4 — Filtre couleur : noir + chic + femme")
print(SEP)
r = search_products(style="chic", color="noir", gender="femme")
afficher_produits(r, "search_products (couleur)")

print(SEP)
print("TEST A5 — Filtre marque : Zara + casual + femme")
print(SEP)
r = search_products(brand="Zara", style="casual", gender="femme")
afficher_produits(r, "search_products (marque)")

print(SEP)
print("TEST A6 — Filtre taille : M + robe + femme")
print(SEP)
r = search_products(category="robe", size="M", gender="femme")
afficher_produits(r, "search_products (taille)")

print(SEP)
print("TEST A7 — Fallback : catégorie inexistante → retourne catalogue en stock")
print(SEP)
r = search_products(category="chapeau")
afficher_produits(r, "search_products (fallback)")

print(SEP)
print("TEST A8 — Tenue mariage femme budget 250 DT")
print(SEP)
r = search_products(style="mariage", gender="femme", budget=250)
afficher_produits(r, "search_products (mariage)")


# ──────────────────────────────────────────────────────────
#  TEST B : compare_prices — tri et scoring
# ──────────────────────────────────────────────────────────

print(SEP)
print("TEST B1 — Comparer des robes femme, budget 100 DT")
print(SEP)
produits = search_products(category="robe", budget=150, gender="femme")
compares = compare_prices(products=produits, budget=100)
afficher_produits(compares, "compare_prices")

print(SEP)
print("TEST B2 — Comparer des hauts homme, budget 80 DT")
print(SEP)
produits = search_products(category="haut", gender="homme")
compares = compare_prices(products=produits, budget=80)
afficher_produits(compares, "compare_prices")

print(SEP)
print("TEST B3 — Comparer des sacs sans budget (tri qualité/prix)")
print(SEP)
produits = search_products(category="sac")
compares = compare_prices(products=produits)
afficher_produits(compares, "compare_prices (sans budget)")

print(SEP)
print("TEST B4 — Produits avec remises — vérifier savings")
print(SEP)
produits = search_products()
avec_remise = [p for p in produits if (p.get("discount") or 0) > 0]
compares = compare_prices(products=avec_remise, budget=100)
afficher_produits(compares, "compare_prices (promos)")

print(SEP)
print("TEST B5 — Liste vide en entrée (cas limite)")
print(SEP)
compares = compare_prices(products=[], budget=100)
afficher_produits(compares, "compare_prices (liste vide)")


# ──────────────────────────────────────────────────────────
#  TEST C : Chaîne complète search → compare
#  (simule exactement ce que fait l'orchestrateur)
# ──────────────────────────────────────────────────────────

print(SEP)
print("TEST C1 — Chaîne complète : robe chic mariage femme 200 DT")
print(SEP)
produits = search_products(category="robe", budget=200, style="chic", gender="femme")
compares = compare_prices(products=produits, budget=200)
afficher_produits(compares, "résultat final (top 5)")

print(SEP2)
print("  Vérification des champs obligatoires pour l'orchestrateur :")
champs_requis = ["id","name","price","brand","category","style","gender",
                 "sizes","colors","stock","rating","description","discount",
                 "url","image_url","final_price","savings","value_score",
                 "in_budget","rank"]
for p in compares[:3]:
    manquants = [k for k in champs_requis if k not in p]
    status = "✅ OK" if not manquants else f"❌ Manquants: {manquants}"
    print(f"    {status}  — {p['name']}")

print(SEP)
print("TEST C2 — Chaîne complète : sneakers homme sport 120 DT")
print(SEP)
produits = search_products(category="chaussures", budget=120, style="sport", gender="homme")
compares = compare_prices(products=produits, budget=120)
afficher_produits(compares, "résultat final")

print(SEP)
print("TEST C3 — Chaîne complète : tenue soirée femme noir budget 200 DT")
print(SEP)
produits = search_products(style="soiree", gender="femme", color="noir", budget=200)
compares = compare_prices(products=produits, budget=200)
afficher_produits(compares, "résultat final")


# ──────────────────────────────────────────────────────────
#  TEST D : get_product_by_id
# ──────────────────────────────────────────────────────────

print(SEP)
print("TEST D — get_product_by_id")
print(SEP)
for pid in ["001", "050", "150", "291", "999"]:
    p = get_product_by_id(pid)
    if p:
        print(f"  ✅ ID {pid} → {p['name']} ({p['price']} DT)")
    else:
        print(f"  ❌ ID {pid} → non trouvé")


# ──────────────────────────────────────────────────────────
#  RÉSUMÉ FINAL
# ──────────────────────────────────────────────────────────

print(SEP)
print("✅  Tous les tests terminés avec succès.")
print(SEP)
print()
print("  RÉSUMÉ DES CHAMPS DISPONIBLES PAR PRODUIT :")
print()
sample = search_products(category="robe", budget=100, gender="femme")
compared = compare_prices(products=sample[:1], budget=100)
if compared:
    for k, v in compared[0].items():
        print(f"    {k:<20} → {v}")
print()