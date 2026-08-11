<<<<<<< HEAD
# NutriCoach AI

This version integrates Google Gemini so meal plans are generated dynamically rather than selected from hardcoded recipes.

## Features

- AI-generated Breakfast / Lunch / Snack / Dinner
- Profile-aware calories and macros
- Allergy, diet preference and disliked-food constraints
- Weight/progress logging
- Recent weight trend included in future planning
- AI plan saved locally in SQLite
- Food logging and daily macro/micronutrient summary

## Run locally

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
```

Activate it, then:

```bash
pip install -r requirements.txt
```

Create a Gemini API key in Google AI Studio: https://aistudio.google.com/apikey. The default model is gemini-3.5-flash-lite, which has a free tier subject to Google usage limits.

Set your API key:

    GEMINI_API_KEY=your_api_key_here

Windows PowerShell:

    $env:GEMINI_API_KEY=your_api_key_here

Optional model override:

    $env:GEMINI_MODEL=gemini-3.5-flash-lite

Run:

```bash
python app.py
```

Open `http://127.0.0.1:5000`.

## Important architecture note

This MVP lets the AI estimate nutrient values for generated recipes so the whole experience works end-to-end. For production, a better design is:

AI generates recipe + exact ingredient amounts -> validated nutrition database calculates nutrients -> app stores calculated totals.

That makes the nutrition database, not the language model, the source of truth for calories and micronutrients.

This app is not medical advice.
=======
# nutrition_coach_app
>>>>>>> origin/main
