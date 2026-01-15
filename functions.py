import json
from typing import Any, Dict, List, Optional

DATA_FILE = "mock_data.json"


def _load_data() -> Dict[str, Any]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_text(s: str) -> str:
    return (s or "").strip().lower()


def _find_food_by_name(data: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    n = _normalize_text(name)
    return next((f for f in data.get("foods", []) if _normalize_text(f.get("food_name", "")) == n), None)


# ---------------------------
# SenioCare helper tools
# ---------------------------

def get_user_profile(user_id: int) -> Dict[str, Any]:
    data = _load_data()
    for u in data.get("users", []):
        if u.get("user_id") == user_id:
            return {"found": True, "user": u}
    return {"found": False, "error": f"user_id {user_id} not found"}


def search_foods(query: str, category: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    data = _load_data()
    q = _normalize_text(query)
    cat = _normalize_text(category) if category else None

    results = []
    for food in data.get("foods", []):
        name = _normalize_text(food.get("food_name", ""))
        fcat = _normalize_text(food.get("category", ""))
        if q in name and (cat is None or cat == fcat):
            results.append(food)

    return {"query": query, "category": category, "count": len(results), "results": results[:limit]}


def check_drug_food_interactions(user_id: int, food_name: str) -> Dict[str, Any]:
    data = _load_data()
    user = next((u for u in data.get("users", []) if u.get("user_id") == user_id), None)
    if not user:
        return {"ok": False, "error": f"user_id {user_id} not found"}

    meds = [m for m in user.get("medications", [])]
    food_n = _normalize_text(food_name)

    matched = []
    for drug in data.get("drugs", []):
        if drug.get("drug_name") in meds:
            avoid = drug.get("avoid_foods", [])
            avoid_norm = [_normalize_text(x) for x in avoid]
            if food_n in avoid_norm:
                matched.append({
                    "drug": drug.get("drug_name"),
                    "food": food_name,
                    "risk": "avoid",
                    "notes": drug.get("notes", "")
                })

    return {
        "ok": True,
        "user_id": user_id,
        "medications": meds,
        "food": food_name,
        "interactions": matched,
        "has_interaction": len(matched) > 0
    }


def suggest_meal_plan_for_user(user_id: int) -> Dict[str, Any]:
    data = _load_data()
    user = next((u for u in data.get("users", []) if u.get("user_id") == user_id), None)
    if not user:
        return {"ok": False, "error": f"user_id {user_id} not found"}

    diseases = user.get("chronic_diseases", [])
    plans = data.get("meal_plans", [])

    for d in diseases:
        plan = next((p for p in plans if _normalize_text(p.get("condition")) == _normalize_text(d)), None)
        if plan:
            return {"ok": True, "user_id": user_id, "matched_condition": d, "meal_plan": plan}

    return {
        "ok": True,
        "user_id": user_id,
        "matched_condition": None,
        "meal_plan": None,
        "note": "No matching meal plan found for user's chronic diseases"
    }


# ---------------------------
# NutriGuide tools (from PDF)
# Names match the PDF so the model can call them
# ---------------------------

def analyze_product(
    product_name: str,
    nutrition_info: Optional[Dict[str, Any]] = None,
    barcode: Optional[str] = None
) -> Dict[str, Any]:
    """
    analyze_product(product_name, nutrition_info?, barcode?)
    - If nutrition_info provided => analyze directly
    - Else => try lookup by product_name in mock foods
    """
    data = _load_data()

    if nutrition_info is None:
        food = _find_food_by_name(data, product_name)
        if not food:
            return {"ok": False, "error": "No nutrition_info provided and product not found in mock foods"}
        nutrition_info = {
            "calories": food.get("calories", 0),
            "total_carbs": food.get("total_carbs", 0),
            "sugars": food.get("sugars", 0),
            "protein": food.get("protein", 0),
            "dietary_fiber": food.get("fiber", 0),
            "fat": food.get("fat", 0),
            "sodium": food.get("sodium", 0)
        }

    total_carbs = float(nutrition_info.get("total_carbs", 0) or 0)
    fiber = float(nutrition_info.get("dietary_fiber", 0) or 0)
    added_sugars = float(nutrition_info.get("added_sugars", 0) or 0)
    sugars = float(nutrition_info.get("sugars", 0) or 0)
    sodium = float(nutrition_info.get("sodium", 0) or 0)

    net_carbs = max(0.0, total_carbs - fiber)

    # Simple heuristics (good enough for mock + testing)
    if added_sugars > 10 or sugars > 20:
        rec = "AVOID"
        reason = "High sugar"
    elif net_carbs > 35:
        rec = "CAUTION"
        reason = "High net carbs"
    elif sodium > 400:
        rec = "CAUTION"
        reason = "High sodium"
    elif fiber >= 3 and net_carbs < 25:
        rec = "RECOMMENDED"
        reason = "Good fiber with moderate carbs"
    else:
        rec = "ACCEPTABLE"
        reason = "Moderate impact"

    return {
        "ok": True,
        "product_name": product_name,
        "barcode": barcode,
        "recommendation": rec,
        "reason": reason,
        "net_carbs": round(net_carbs, 1),
        "key_nutrients": {
            "calories": nutrition_info.get("calories", 0),
            "total_carbs": total_carbs,
            "fiber": fiber,
            "sugars": sugars,
            "added_sugars": added_sugars,
            "protein": nutrition_info.get("protein", 0),
            "sodium": sodium
        }
    }


def compare_products(products: List[Dict[str, Any]], comparison_focus: str = "glycemic_impact") -> Dict[str, Any]:
    """
    compare_products(products, comparison_focus?)
    Each product dict can include:
      name, carbs, fiber, sugars, protein, glycemic_index
    """
    scored = []
    for p in products:
        carbs = float(p.get("carbs", 0) or 0)
        fiber = float(p.get("fiber", 0) or 0)
        sugars = float(p.get("sugars", 0) or 0)
        protein = float(p.get("protein", 0) or 0)
        gi = float(p.get("glycemic_index", 0) or 0)  # may be 0

        net_carbs = max(0.0, carbs - fiber)

        if comparison_focus == "carb_content":
            score = 100 - min(100, net_carbs * 2)
        elif comparison_focus == "overall_nutrition":
            score = (protein * 3) + (fiber * 4) - (net_carbs * 2) - (sugars * 1.5)
        else:  # glycemic_impact
            # GI might be unknown; proxy using net carbs and sugars
            score = 100 - (net_carbs * 2) - (sugars * 1.5) - (gi * 0.3)

        scored.append({
            "name": p.get("name"),
            "score": round(score, 1),
            "net_carbs": round(net_carbs, 1)
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {
        "ok": True,
        "comparison_focus": comparison_focus,
        "best_choice": scored[0]["name"] if scored else None,
        "results": scored
    }


def suggest_alternatives(original_product: str, category: str, preferences: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    suggest_alternatives(original_product, category, preferences?)
    Implementation: return items from foods with same category, filtered by preferences/tags if available.
    """
    data = _load_data()
    cat = _normalize_text(category)
    prefs = [_normalize_text(x) for x in (preferences or [])]

    candidates = []
    for f in data.get("foods", []):
        if _normalize_text(f.get("category")) != cat:
            continue
        tags = [_normalize_text(t) for t in f.get("tags", [])]
        if prefs and not any(p in tags for p in prefs):
            continue

        candidates.append({
            "food_name": f.get("food_name"),
            "tags": f.get("tags", []),
            "calories": f.get("calories", 0),
            "total_carbs": f.get("total_carbs", 0),
            "fiber": f.get("fiber", 0),
            "sugars": f.get("sugars", 0),
            "sodium": f.get("sodium", 0)
        })

    # prefer higher fiber, lower carbs/sugars/sodium
    candidates.sort(key=lambda x: (-(x["fiber"] or 0), (x["total_carbs"] or 0), (x["sugars"] or 0), (x["sodium"] or 0)))
    return {
        "ok": True,
        "original_product": original_product,
        "category": category,
        "preferences": preferences or [],
        "alternatives": candidates[:8]
    }


def calculate_meal_impact(meal_components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    calculate_meal_impact(meal_components)
    meal_components items:
      { "food": "Brown Rice", "carbs": 30 } ...
    """
    total_carbs = sum(float(x.get("carbs", 0) or 0) for x in meal_components)

    # try to estimate sugars from foods by name (optional)
    data = _load_data()
    total_sugars = 0.0
    for x in meal_components:
        fn = _normalize_text(x.get("food", ""))
        f = next((ff for ff in data.get("foods", []) if _normalize_text(ff.get("food_name")) == fn), None)
        if f:
            total_sugars += float(f.get("sugars", 0) or 0)

    if total_carbs >= 60 or total_sugars >= 25:
        impact = "HIGH"
    elif total_carbs >= 30:
        impact = "MODERATE"
    else:
        impact = "LOW"

    return {
        "ok": True,
        "total_carbs": round(total_carbs, 1),
        "estimated_total_sugars": round(total_sugars, 1),
        "meal_impact": impact,
        "tip": "Add protein/fiber to reduce sugar spikes (e.g., yogurt/vegetables)."
    }


def review_cart(cart_items: List[Dict[str, Any]], meal_planning: bool = False) -> Dict[str, Any]:
    """
    review_cart(cart_items, meal_planning?)
    cart_items example:
      [{"name": "White Rice", "quantity": 1}, {"name": "Grilled Fish", "quantity": 2}]
    """
    data = _load_data()

    analyzed = []
    warnings = []
    total_calories = 0.0
    total_carbs = 0.0
    total_sugars = 0.0
    total_protein = 0.0
    total_fiber = 0.0
    total_sodium = 0.0

    for item in cart_items:
        name = item.get("name", "")
        qty = float(item.get("quantity", 1) or 1)

        food = _find_food_by_name(data, name)
        if not food:
            analyzed.append({"name": name, "quantity": qty, "found": False})
            warnings.append(f"Item not found in foods DB: {name}")
            continue

        calories = float(food.get("calories", 0) or 0) * qty
        carbs = float(food.get("total_carbs", 0) or 0) * qty
        sugars = float(food.get("sugars", 0) or 0) * qty
        protein = float(food.get("protein", 0) or 0) * qty
        fiber = float(food.get("fiber", 0) or 0) * qty
        sodium = float(food.get("sodium", 0) or 0) * qty

        total_calories += calories
        total_carbs += carbs
        total_sugars += sugars
        total_protein += protein
        total_fiber += fiber
        total_sodium += sodium

        # simple flags
        tags = food.get("tags", [])
        flags = []
        if sugars >= 20:
            flags.append("high-sugar")
        if carbs >= 60:
            flags.append("high-carb")
        if sodium >= 600:
            flags.append("high-sodium")

        analyzed.append({
            "name": food.get("food_name"),
            "quantity": qty,
            "found": True,
            "category": food.get("category"),
            "tags": tags,
            "macros": {
                "calories": round(calories, 1),
                "carbs": round(carbs, 1),
                "sugars": round(sugars, 1),
                "protein": round(protein, 1),
                "fiber": round(fiber, 1),
                "sodium": round(sodium, 1)
            },
            "flags": flags
        })

    # cart-level warnings
    if total_sugars >= 40:
        warnings.append("Cart sugar is high (estimated).")
    if total_sodium >= 1500:
        warnings.append("Cart sodium is high (estimated).")
    if meal_planning and total_protein < 30:
        warnings.append("Low protein for meal planning (consider adding protein source).")

    return {
        "ok": True,
        "meal_planning": meal_planning,
        "summary": {
            "total_calories": round(total_calories, 1),
            "total_carbs": round(total_carbs, 1),
            "total_sugars": round(total_sugars, 1),
            "total_protein": round(total_protein, 1),
            "total_fiber": round(total_fiber, 1),
            "total_sodium": round(total_sodium, 1)
        },
        "items": analyzed,
        "warnings": warnings
    }


def check_ingredient_concerns(ingredients_list: List[str], product_category: Optional[str] = None) -> Dict[str, Any]:
    """
    check_ingredient_concerns(ingredients_list, product_category?)
    Heuristic mock:
      - flags common risky ingredients for elderly / chronic diseases:
        added sugar, high sodium additives, trans fats, etc.
    """
    ings = [_normalize_text(x) for x in ingredients_list]
    concerns = []

    sugar_terms = {"sugar", "glucose", "fructose", "corn syrup", "high fructose corn syrup", "dextrose"}
    sodium_terms = {"sodium", "msg", "monosodium glutamate", "sodium benzoate", "sodium nitrite"}
    fat_terms = {"hydrogenated", "partially hydrogenated", "trans fat"}

    for ing in ings:
        if any(term in ing for term in sugar_terms):
            concerns.append({"ingredient": ing, "concern": "added_sugar", "severity": "moderate"})
        if any(term in ing for term in sodium_terms):
            concerns.append({"ingredient": ing, "concern": "high_sodium_additive", "severity": "moderate"})
        if any(term in ing for term in fat_terms):
            concerns.append({"ingredient": ing, "concern": "unhealthy_fat", "severity": "high"})

    return {
        "ok": True,
        "product_category": product_category,
        "ingredients_checked": len(ingredients_list),
        "concerns": concerns,
        "has_concerns": len(concerns) > 0
    }


def get_portion_guidance(food_category: str, food_item: str, meal_context: Optional[str] = None) -> Dict[str, Any]:
    """
    get_portion_guidance(food_category, food_item, meal_context?)
    Mock guidance (general senior-friendly suggestions)
    """
    cat = _normalize_text(food_category)
    ctx = _normalize_text(meal_context) if meal_context else None

    guidance_map = {
        "bread": "1 slice per meal (prefer whole grain).",
        "carbs": "1/2 to 1 cup cooked per meal (prefer high-fiber).",
        "protein": "90–120g cooked portion (palm-size).",
        "fruit": "1 medium fruit or 1 cup chopped.",
        "dairy": "1 cup milk/yogurt or 30–40g cheese.",
        "vegetables": "2 cups non-starchy vegetables (more is better).",
        "fast-food": "Occasional; keep portion small and limit sodium."
    }

    base = guidance_map.get(cat, "Use a moderate portion and balance with protein/fiber.")
    extra = ""
    if ctx in {"snack", "between meals"}:
        extra = " For snacks: keep it lighter and avoid high sugar."
    elif ctx in {"dinner"}:
        extra = " For dinner: reduce carbs slightly if possible."

    return {
        "ok": True,
        "food_category": food_category,
        "food_item": food_item,
        "meal_context": meal_context,
        "portion_guidance": base + extra
    }


def log_user_preference(item: str, preference_type: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    log_user_preference(item, preference_type, notes?)
    Mock: store in a local file "user_preferences.json" (simple simulation)
    preference_type examples: like, dislike, avoid, allergy
    """
    pref_file = "user_preferences.json"

    record = {
        "item": item,
        "preference_type": preference_type,
        "notes": notes or ""
    }

    # load existing
    try:
        with open(pref_file, "r", encoding="utf-8") as f:
            prefs = json.load(f)
            if not isinstance(prefs, list):
                prefs = []
    except FileNotFoundError:
        prefs = []
    except json.JSONDecodeError:
        prefs = []

    prefs.append(record)

    with open(pref_file, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)

    return {"ok": True, "saved_to": pref_file, "record": record}