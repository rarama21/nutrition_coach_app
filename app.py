
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import date
import os
import json

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "nutrition.db"

from openai import OpenAI

app = Flask(__name__)
app.secret_key = "change-this-in-production"

MICRO_KEYS = [
    "fiber_g", "calcium_mg", "iron_mg", "magnesium_mg", "potassium_mg",
    "sodium_mg", "zinc_mg", "vitamin_c_mg", "vitamin_d_mcg",
    "vitamin_b12_mcg", "folate_mcg"
]

DAILY_MICRO_TARGETS = {
    "fiber_g": 30,
    "calcium_mg": 1000,
    "iron_mg": 18,
    "magnesium_mg": 400,
    "potassium_mg": 3500,
    "sodium_mg": 2300,
    "zinc_mg": 11,
    "vitamin_c_mg": 90,
    "vitamin_d_mcg": 15,
    "vitamin_b12_mcg": 2.4,
    "folate_mcg": 400,
}

RECIPES = [
    {
        "name": "Greek Yogurt Berry Oats",
        "meal_type": "Breakfast",
        "diet": "vegetarian",
        "allergens": "dairy",
        "ingredients": "250 g Greek yogurt, 50 g oats, 120 g berries, 15 g walnuts, 1 tsp honey",
        "instructions": "Combine yogurt and oats. Top with berries, walnuts and honey.",
        "calories": 520, "protein_g": 34, "carbs_g": 58, "fat_g": 18,
        "fiber_g": 10, "calcium_mg": 330, "iron_mg": 3.0, "magnesium_mg": 110,
        "potassium_mg": 650, "sodium_mg": 120, "zinc_mg": 3.2, "vitamin_c_mg": 35,
        "vitamin_d_mcg": 1.0, "vitamin_b12_mcg": 1.6, "folate_mcg": 55
    },
    {
        "name": "Egg & Avocado Toast",
        "meal_type": "Breakfast",
        "diet": "vegetarian",
        "allergens": "egg,gluten",
        "ingredients": "2 eggs, 2 slices wholegrain toast, 1/2 avocado, tomato, spinach",
        "instructions": "Toast bread. Cook eggs to preference. Serve with avocado, tomato and spinach.",
        "calories": 510, "protein_g": 25, "carbs_g": 42, "fat_g": 27,
        "fiber_g": 11, "calcium_mg": 180, "iron_mg": 5.0, "magnesium_mg": 105,
        "potassium_mg": 980, "sodium_mg": 550, "zinc_mg": 3.3, "vitamin_c_mg": 28,
        "vitamin_d_mcg": 2.4, "vitamin_b12_mcg": 1.2, "folate_mcg": 130
    },
    {
        "name": "Tofu Protein Scramble",
        "meal_type": "Breakfast",
        "diet": "vegan",
        "allergens": "soy",
        "ingredients": "200 g tofu, peppers, spinach, onion, 2 slices wholegrain toast, nutritional yeast",
        "instructions": "Crumble tofu and saute with vegetables and seasoning. Serve with toast.",
        "calories": 470, "protein_g": 31, "carbs_g": 47, "fat_g": 18,
        "fiber_g": 10, "calcium_mg": 430, "iron_mg": 6.5, "magnesium_mg": 145,
        "potassium_mg": 900, "sodium_mg": 540, "zinc_mg": 3.2, "vitamin_c_mg": 70,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 1.2, "folate_mcg": 125
    },
    {
        "name": "Chicken Rice Power Bowl",
        "meal_type": "Lunch",
        "diet": "omnivore",
        "allergens": "",
        "ingredients": "180 g chicken breast, 180 g cooked rice, broccoli, carrots, olive oil, lemon",
        "instructions": "Grill chicken. Cook rice and vegetables. Assemble and dress with olive oil and lemon.",
        "calories": 690, "protein_g": 58, "carbs_g": 72, "fat_g": 18,
        "fiber_g": 9, "calcium_mg": 120, "iron_mg": 3.6, "magnesium_mg": 120,
        "potassium_mg": 1050, "sodium_mg": 420, "zinc_mg": 4.3, "vitamin_c_mg": 88,
        "vitamin_d_mcg": 0.2, "vitamin_b12_mcg": 0.7, "folate_mcg": 110
    },
    {
        "name": "Lentil Quinoa Bowl",
        "meal_type": "Lunch",
        "diet": "vegan",
        "allergens": "",
        "ingredients": "180 g cooked lentils, 140 g cooked quinoa, cucumber, tomato, spinach, tahini, lemon",
        "instructions": "Combine all ingredients. Mix tahini with lemon and water for dressing.",
        "calories": 640, "protein_g": 29, "carbs_g": 86, "fat_g": 21,
        "fiber_g": 20, "calcium_mg": 230, "iron_mg": 8.2, "magnesium_mg": 210,
        "potassium_mg": 1250, "sodium_mg": 280, "zinc_mg": 4.8, "vitamin_c_mg": 45,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "folate_mcg": 330
    },
    {
        "name": "Tuna Chickpea Salad",
        "meal_type": "Lunch",
        "diet": "pescatarian",
        "allergens": "fish",
        "ingredients": "1 can tuna, 150 g chickpeas, tomato, cucumber, greens, olive oil, lemon",
        "instructions": "Drain tuna and chickpeas. Toss everything together with lemon and olive oil.",
        "calories": 610, "protein_g": 46, "carbs_g": 51, "fat_g": 24,
        "fiber_g": 14, "calcium_mg": 130, "iron_mg": 5.0, "magnesium_mg": 120,
        "potassium_mg": 1100, "sodium_mg": 680, "zinc_mg": 3.5, "vitamin_c_mg": 38,
        "vitamin_d_mcg": 1.8, "vitamin_b12_mcg": 2.6, "folate_mcg": 165
    },
    {
        "name": "Salmon Potato Plate",
        "meal_type": "Dinner",
        "diet": "pescatarian",
        "allergens": "fish",
        "ingredients": "170 g salmon, 300 g potatoes, broccoli, olive oil, herbs",
        "instructions": "Roast potatoes. Bake or pan-sear salmon. Steam broccoli and serve together.",
        "calories": 720, "protein_g": 48, "carbs_g": 62, "fat_g": 31,
        "fiber_g": 11, "calcium_mg": 150, "iron_mg": 3.0, "magnesium_mg": 140,
        "potassium_mg": 1800, "sodium_mg": 390, "zinc_mg": 2.8, "vitamin_c_mg": 90,
        "vitamin_d_mcg": 16, "vitamin_b12_mcg": 5.0, "folate_mcg": 120
    },
    {
        "name": "Turkey Pasta Primavera",
        "meal_type": "Dinner",
        "diet": "omnivore",
        "allergens": "gluten",
        "ingredients": "170 g lean turkey, 90 g dry wholewheat pasta, tomato sauce, zucchini, peppers",
        "instructions": "Cook pasta. Brown turkey. Add vegetables and sauce, then combine.",
        "calories": 740, "protein_g": 55, "carbs_g": 86, "fat_g": 20,
        "fiber_g": 13, "calcium_mg": 160, "iron_mg": 5.5, "magnesium_mg": 125,
        "potassium_mg": 1250, "sodium_mg": 760, "zinc_mg": 5.2, "vitamin_c_mg": 72,
        "vitamin_d_mcg": 0.3, "vitamin_b12_mcg": 2.0, "folate_mcg": 115
    },
    {
        "name": "Tempeh Sweet Potato Bowl",
        "meal_type": "Dinner",
        "diet": "vegan",
        "allergens": "soy",
        "ingredients": "180 g tempeh, 300 g sweet potato, kale, red cabbage, sesame dressing",
        "instructions": "Roast sweet potato. Pan-sear tempeh. Serve over kale and cabbage with dressing.",
        "calories": 710, "protein_g": 36, "carbs_g": 82, "fat_g": 28,
        "fiber_g": 18, "calcium_mg": 310, "iron_mg": 6.8, "magnesium_mg": 190,
        "potassium_mg": 1500, "sodium_mg": 620, "zinc_mg": 3.9, "vitamin_c_mg": 95,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "folate_mcg": 170
    },
    {
        "name": "Apple & Peanut Butter",
        "meal_type": "Snack",
        "diet": "vegan",
        "allergens": "peanut",
        "ingredients": "1 large apple, 30 g peanut butter",
        "instructions": "Slice the apple and serve with peanut butter.",
        "calories": 285, "protein_g": 8, "carbs_g": 35, "fat_g": 14,
        "fiber_g": 7, "calcium_mg": 45, "iron_mg": 1.4, "magnesium_mg": 65,
        "potassium_mg": 420, "sodium_mg": 150, "zinc_mg": 1.0, "vitamin_c_mg": 10,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "folate_mcg": 25
    },
    {
        "name": "Cottage Cheese Fruit Cup",
        "meal_type": "Snack",
        "diet": "vegetarian",
        "allergens": "dairy",
        "ingredients": "200 g cottage cheese, 1 kiwi, 100 g pineapple",
        "instructions": "Add cottage cheese to a bowl and top with fruit.",
        "calories": 260, "protein_g": 28, "carbs_g": 28, "fat_g": 5,
        "fiber_g": 4, "calcium_mg": 190, "iron_mg": 0.8, "magnesium_mg": 38,
        "potassium_mg": 510, "sodium_mg": 720, "zinc_mg": 1.3, "vitamin_c_mg": 82,
        "vitamin_d_mcg": 0.2, "vitamin_b12_mcg": 1.1, "folate_mcg": 35
    },
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        sex TEXT NOT NULL,
        weight_kg REAL NOT NULL,
        height_cm REAL NOT NULL,
        activity REAL NOT NULL,
        goal TEXT NOT NULL,
        diet TEXT NOT NULL,
        allergies TEXT DEFAULT '',
        dislikes TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        diet TEXT NOT NULL,
        allergens TEXT DEFAULT '',
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL,
        calories REAL NOT NULL,
        protein_g REAL NOT NULL,
        carbs_g REAL NOT NULL,
        fat_g REAL NOT NULL,
        fiber_g REAL NOT NULL,
        calcium_mg REAL NOT NULL,
        iron_mg REAL NOT NULL,
        magnesium_mg REAL NOT NULL,
        potassium_mg REAL NOT NULL,
        sodium_mg REAL NOT NULL,
        zinc_mg REAL NOT NULL,
        vitamin_c_mg REAL NOT NULL,
        vitamin_d_mcg REAL NOT NULL,
        vitamin_b12_mcg REAL NOT NULL,
        folate_mcg REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS plans (
        plan_date TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        recipe_id INTEGER NOT NULL,
        PRIMARY KEY(plan_date, meal_type),
        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
    );

    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_date TEXT NOT NULL,
        recipe_id INTEGER NOT NULL,
        servings REAL NOT NULL DEFAULT 1,
        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
    );

    CREATE TABLE IF NOT EXISTS weight_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_date TEXT NOT NULL UNIQUE,
        weight_kg REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ai_plans (
        plan_date TEXT PRIMARY KEY,
        raw_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    count = conn.execute("SELECT COUNT(*) AS n FROM recipes").fetchone()["n"]
    if count == 0:
        cols = list(RECIPES[0].keys())
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT INTO recipes ({','.join(cols)}) VALUES ({placeholders})"
        for item in RECIPES:
            conn.execute(sql, [item[c] for c in cols])
    conn.commit()
    conn.close()

def get_profile():
    conn = db()
    row = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return row

def calc_targets(profile):
    # Mifflin-St Jeor estimate. This is a starting estimate, not medical advice.
    w = profile["weight_kg"]
    h = profile["height_cm"]
    a = profile["age"]
    sex = profile["sex"]
    bmr = 10*w + 6.25*h - 5*a + (5 if sex == "male" else -161 if sex == "female" else -78)
    tdee = bmr * profile["activity"]

    goal = profile["goal"]
    adjustment = {
        "lose": -400,
        "maintain": 0,
        "gain": 300,
        "muscle": 250,
    }.get(goal, 0)

    calories = max(1200, round((tdee + adjustment) / 10) * 10)
    if goal in ("muscle", "gain"):
        protein = round(w * 1.8)
    elif goal == "lose":
        protein = round(w * 1.7)
    else:
        protein = round(w * 1.4)

    fat = round(w * 0.8)
    carbs = max(80, round((calories - protein*4 - fat*9) / 4))
    return {"calories": calories, "protein_g": protein, "carbs_g": carbs, "fat_g": fat}

def allowed_recipe(recipe, profile):
    diet = profile["diet"].lower()
    recipe_diet = recipe["diet"].lower()
    if diet == "vegan" and recipe_diet != "vegan":
        return False
    if diet == "vegetarian" and recipe_diet not in ("vegetarian", "vegan"):
        return False
    if diet == "pescatarian" and recipe_diet not in ("pescatarian", "vegetarian", "vegan"):
        return False

    allergies = [x.strip().lower() for x in profile["allergies"].split(",") if x.strip()]
    allergens = [x.strip().lower() for x in recipe["allergens"].split(",") if x.strip()]
    if any(a in allergens for a in allergies):
        return False

    dislikes = [x.strip().lower() for x in profile["dislikes"].split(",") if x.strip()]
    ingredients = recipe["ingredients"].lower()
    if any(d in ingredients for d in dislikes):
        return False
    return True

def generate_plan(plan_date):
    profile = get_profile()
    if not profile:
        return

    conn = db()
    recipes = conn.execute("SELECT * FROM recipes ORDER BY id").fetchall()
    existing = conn.execute("SELECT COUNT(*) AS n FROM plans WHERE plan_date=?", (plan_date,)).fetchone()["n"]
    if existing:
        conn.close()
        return

    for meal_type in ["Breakfast", "Lunch", "Snack", "Dinner"]:
        candidates = [r for r in recipes if r["meal_type"] == meal_type and allowed_recipe(r, profile)]
        if not candidates:
            # fallback if preference filter leaves no result
            candidates = [r for r in recipes if r["meal_type"] == meal_type]
        if candidates:
            # Rotate by date deterministically.
            idx = sum(ord(c) for c in plan_date + meal_type) % len(candidates)
            chosen = candidates[idx]
            conn.execute(
                "INSERT OR REPLACE INTO plans(plan_date, meal_type, recipe_id) VALUES (?,?,?)",
                (plan_date, meal_type, chosen["id"])
            )
    conn.commit()
    conn.close()

def plan_rows(plan_date):
    conn = db()
    rows = conn.execute("""
        SELECT p.meal_type, r.*
        FROM plans p JOIN recipes r ON r.id = p.recipe_id
        WHERE p.plan_date=?
        ORDER BY CASE p.meal_type
            WHEN 'Breakfast' THEN 1 WHEN 'Lunch' THEN 2 WHEN 'Snack' THEN 3 WHEN 'Dinner' THEN 4 ELSE 5 END
    """, (plan_date,)).fetchall()
    conn.close()
    return rows

def sum_nutrition(rows, servings_key=None):
    keys = ["calories", "protein_g", "carbs_g", "fat_g"] + MICRO_KEYS
    totals = {k: 0.0 for k in keys}
    for r in rows:
        mult = r[servings_key] if servings_key else 1.0
        for k in keys:
            totals[k] += float(r[k]) * mult
    return totals


def recent_progress():
    conn = db()
    rows = conn.execute("""
        SELECT log_date, weight_kg
        FROM weight_logs
        ORDER BY log_date DESC
        LIMIT 14
    """).fetchall()
    conn.close()
    rows = list(reversed(rows))
    result = {
        "entries": [{"date": r["log_date"], "weight_kg": r["weight_kg"]} for r in rows],
        "change_kg": None,
        "trend_per_week_kg": None,
    }
    if len(rows) < 2:
        return result
    first, last = rows[0], rows[-1]
    d1 = date.fromisoformat(first["log_date"])
    d2 = date.fromisoformat(last["log_date"])
    days = max((d2 - d1).days, 1)
    change = float(last["weight_kg"]) - float(first["weight_kg"])
    result["change_kg"] = round(change, 2)
    result["trend_per_week_kg"] = round(change / days * 7, 2)
    return result

def ai_daily_plan(profile, targets, plan_date):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    progress = recent_progress()

    meal_schema = {
        "type": "object",
        "properties": {
            "meal_type": {"type": "string", "enum": ["Breakfast", "Lunch", "Snack", "Dinner"]},
            "name": {"type": "string"},
            "ingredients": {"type": "string"},
            "instructions": {"type": "string"},
            "calories": {"type": "number"},
            "protein_g": {"type": "number"},
            "carbs_g": {"type": "number"},
            "fat_g": {"type": "number"},
            "fiber_g": {"type": "number"},
            "calcium_mg": {"type": "number"},
            "iron_mg": {"type": "number"},
            "magnesium_mg": {"type": "number"},
            "potassium_mg": {"type": "number"},
            "sodium_mg": {"type": "number"},
            "zinc_mg": {"type": "number"},
            "vitamin_c_mg": {"type": "number"},
            "vitamin_d_mcg": {"type": "number"},
            "vitamin_b12_mcg": {"type": "number"},
            "folate_mcg": {"type": "number"},
            "allergens": {"type": "string"},
            "diet": {"type": "string"}
        },
        "required": [
            "meal_type","name","ingredients","instructions","calories","protein_g","carbs_g","fat_g",
            "fiber_g","calcium_mg","iron_mg","magnesium_mg","potassium_mg","sodium_mg","zinc_mg",
            "vitamin_c_mg","vitamin_d_mcg","vitamin_b12_mcg","folate_mcg","allergens","diet"
        ],
        "additionalProperties": False
    }

    schema = {
        "type": "object",
        "properties": {
            "coach_note": {"type": "string"},
            "adjustment_reason": {"type": "string"},
            "meals": {"type": "array", "minItems": 4, "maxItems": 4, "items": meal_schema}
        },
        "required": ["coach_note", "adjustment_reason", "meals"],
        "additionalProperties": False
    }

    prompt = f"""
You are the meal-planning component of a nutrition coaching application.

Generate exactly four meals for {plan_date}: Breakfast, Lunch, Snack, and Dinner.

USER PROFILE
Name: {profile['name']}
Age: {profile['age']}
Sex used for calorie estimate: {profile['sex']}
Weight: {profile['weight_kg']} kg
Height: {profile['height_cm']} cm
Goal: {profile['goal']}
Diet preference: {profile['diet']}
Allergies: {profile['allergies'] or 'none supplied'}
Disliked foods: {profile['dislikes'] or 'none supplied'}

CURRENT DAILY TARGETS
Calories: {targets['calories']} kcal
Protein: {targets['protein_g']} g
Carbs: {targets['carbs_g']} g
Fat: {targets['fat_g']} g

RECENT WEIGHT PROGRESS
{json.dumps(progress)}

RULES
- Never include a listed allergen.
- Respect dietary preference and disliked foods.
- Use common ingredients and realistic quantities.
- Keep the day's calories and protein reasonably close to target.
- Use recent progress only for modest portion adjustments.
- Do not make aggressive changes because of short-term scale fluctuations.
- Nutrient values are estimates, not laboratory measurements.
- Do not diagnose medical conditions or nutrient deficiencies.
- adjustment_reason must briefly explain whether recent progress changed today's plan.
"""

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5"),
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "daily_nutrition_plan",
                "strict": True,
                "schema": schema
            }
        }
    )
    return json.loads(response.output_text)

def save_ai_plan(plan_date, plan):
    conn = db()
    conn.execute("DELETE FROM plans WHERE plan_date=?", (plan_date,))
    cols = [
        "name","meal_type","diet","allergens","ingredients","instructions","calories","protein_g",
        "carbs_g","fat_g","fiber_g","calcium_mg","iron_mg","magnesium_mg","potassium_mg",
        "sodium_mg","zinc_mg","vitamin_c_mg","vitamin_d_mcg","vitamin_b12_mcg","folate_mcg"
    ]
    for meal in plan["meals"]:
        q = ",".join(["?"] * len(cols))
        cur = conn.execute(
            f"INSERT INTO recipes ({','.join(cols)}) VALUES ({q})",
            [meal[c] for c in cols]
        )
        conn.execute(
            "INSERT OR REPLACE INTO plans(plan_date, meal_type, recipe_id) VALUES (?,?,?)",
            (plan_date, meal["meal_type"], cur.lastrowid)
        )
    conn.execute(
        "INSERT OR REPLACE INTO ai_plans(plan_date, raw_json) VALUES (?,?)",
        (plan_date, json.dumps(plan))
    )
    conn.commit()
    conn.close()

def get_ai_plan_meta(plan_date):
    conn = db()
    row = conn.execute("SELECT raw_json FROM ai_plans WHERE plan_date=?", (plan_date,)).fetchone()
    conn.close()
    return json.loads(row["raw_json"]) if row else None

@app.route("/")
def home():
    if not get_profile():
        return redirect(url_for("profile"))
    return redirect(url_for("today"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    existing = get_profile()
    if request.method == "POST":
        data = (
            request.form["name"].strip(),
            int(request.form["age"]),
            request.form["sex"],
            float(request.form["weight_kg"]),
            float(request.form["height_cm"]),
            float(request.form["activity"]),
            request.form["goal"],
            request.form["diet"],
            request.form.get("allergies", "").strip().lower(),
            request.form.get("dislikes", "").strip().lower(),
        )
        conn = db()
        conn.execute("""
            INSERT INTO profile(id,name,age,sex,weight_kg,height_cm,activity,goal,diet,allergies,dislikes)
            VALUES(1,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, age=excluded.age, sex=excluded.sex,
                weight_kg=excluded.weight_kg, height_cm=excluded.height_cm,
                activity=excluded.activity, goal=excluded.goal, diet=excluded.diet,
                allergies=excluded.allergies, dislikes=excluded.dislikes
        """, data)
        # Clear future/current generated plan so it can reflect new profile.
        conn.execute("DELETE FROM plans")
        conn.commit()
        conn.close()
        flash("Profile saved.")
        return redirect(url_for("today"))
    return render_template("profile.html", profile=existing)

@app.route("/today")
def today():
    profile = get_profile()
    if not profile:
        return redirect(url_for("profile"))
    d = request.args.get("date", date.today().isoformat())
    rows = plan_rows(d)
    targets = calc_targets(profile)
    planned = sum_nutrition(rows)
    ai_meta = get_ai_plan_meta(d)
    return render_template("today.html", profile=profile, rows=rows, targets=targets, planned=planned, d=d, ai_meta=ai_meta)


@app.post("/generate-ai-plan")
def generate_ai_plan():
    profile = get_profile()
    if not profile:
        return redirect(url_for("profile"))
    d = request.form.get("date", date.today().isoformat())
    try:
        plan = ai_daily_plan(profile, calc_targets(profile), d)
        save_ai_plan(d, plan)
        flash("AI meal plan generated.")
    except Exception as exc:
        flash(f"AI generation failed: {exc}")
    return redirect(url_for("today", date=d))

@app.route("/progress", methods=["GET", "POST"])
def progress():
    profile = get_profile()
    if not profile:
        return redirect(url_for("profile"))

    if request.method == "POST":
        d = request.form.get("date", date.today().isoformat())
        weight = float(request.form["weight_kg"])
        conn = db()
        conn.execute(
            """INSERT INTO weight_logs(log_date, weight_kg)
               VALUES (?,?)
               ON CONFLICT(log_date) DO UPDATE SET weight_kg=excluded.weight_kg""",
            (d, weight)
        )
        conn.commit()
        conn.close()
        flash("Weight progress saved.")
        return redirect(url_for("progress"))

    conn = db()
    rows = conn.execute("SELECT * FROM weight_logs ORDER BY log_date DESC LIMIT 30").fetchall()
    conn.close()
    return render_template("progress.html", profile=profile, rows=rows, trend=recent_progress())

@app.post("/swap/<meal_type>")
def swap(meal_type):
    profile = get_profile()
    d = request.form.get("date", date.today().isoformat())
    conn = db()
    current = conn.execute("SELECT recipe_id FROM plans WHERE plan_date=? AND meal_type=?", (d, meal_type)).fetchone()
    recipes = conn.execute("SELECT * FROM recipes WHERE meal_type=? ORDER BY id", (meal_type,)).fetchall()
    candidates = [r for r in recipes if allowed_recipe(r, profile)]
    if not candidates:
        candidates = recipes
    if candidates:
        ids = [r["id"] for r in candidates]
        if current and current["recipe_id"] in ids:
            idx = (ids.index(current["recipe_id"]) + 1) % len(ids)
        else:
            idx = 0
        conn.execute("INSERT OR REPLACE INTO plans(plan_date, meal_type, recipe_id) VALUES(?,?,?)",
                     (d, meal_type, ids[idx]))
        conn.commit()
    conn.close()
    return redirect(url_for("today", date=d))

@app.post("/log/<int:recipe_id>")
def log_recipe(recipe_id):
    d = request.form.get("date", date.today().isoformat())
    servings = float(request.form.get("servings", 1))
    conn = db()
    conn.execute("INSERT INTO logs(log_date, recipe_id, servings) VALUES(?,?,?)", (d, recipe_id, servings))
    conn.commit()
    conn.close()
    flash("Meal logged.")
    return redirect(url_for("today", date=d))

@app.route("/summary")
def summary():
    profile = get_profile()
    if not profile:
        return redirect(url_for("profile"))
    d = request.args.get("date", date.today().isoformat())
    conn = db()
    rows = conn.execute("""
        SELECT l.servings, r.*
        FROM logs l JOIN recipes r ON r.id=l.recipe_id
        WHERE l.log_date=?
        ORDER BY l.id
    """, (d,)).fetchall()
    conn.close()
    totals = sum_nutrition(rows, "servings")
    targets = calc_targets(profile)
    percentages = {}
    for k, target in DAILY_MICRO_TARGETS.items():
        percentages[k] = min(999, round((totals[k] / target) * 100)) if target else 0
    return render_template("summary.html", profile=profile, rows=rows, totals=totals,
                           targets=targets, micro_targets=DAILY_MICRO_TARGETS,
                           percentages=percentages, d=d)

@app.post("/delete-log/<int:log_id>")
def delete_log(log_id):
    d = request.form.get("date", date.today().isoformat())
    conn = db()
    conn.execute("DELETE FROM logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("summary", date=d))

@app.context_processor
def helpers():
    def pct(value, target):
        if not target:
            return 0
        return min(100, round(value / target * 100))
    return {"pct": pct}

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
