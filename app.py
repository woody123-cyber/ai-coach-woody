# COACH WOODY v23.2 — 60-LEVEL IELTS QUEST + FULL APP (PROMPTS FIXED)
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import plotly.express as px
import pandas as pd
from datetime import datetime
import re

# === CONFIG ===
st.set_page_config(page_title="Coach Woody", page_icon="trophy", layout="wide")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === GENDER TOGGLE ===
gender = st.sidebar.radio("Coach Gender", ["Male (Woody)", "Female (Hibiki)"], horizontal=True)
coach_name = "Woody" if gender == "Male (Woody)" else "Hibiki"

# === LLM ===
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.7)

# === SESSION STATE ===
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.level = 1
    st.session_state.xp = 0
    st.session_state.total_xp = 0
    st.session_state.last_band = 0.0
    st.session_state.streak = 0
    st.session_state.progress_fitness = []
    st.session_state.progress_nutrition = []
    st.session_state.name = ""
    st.session_state.body_weight_kg = 70.0
    st.session_state.weight_unit = "kg"
    st.session_state.weight_goal = "Maintain"
    st.session_state.calorie_goal = 2000
    st.session_state.macro_goal = {"protein": 150, "carbs": 250, "fats": 70}
    st.session_state.home_lang = "English"
    st.session_state.part = "Part 1"
    st.session_state.fitness_starters = [
        "How do I improve my push-up form?",
        "What's a good 5K training plan?",
        "How to recover after a workout?"
    ]
    st.session_state.nutrition_starters = [
        "How do I find my daily calorie intake?",
        "What are ideal macro splits?",
        "Suggest a high-protein meal under 500 cal.",
        "How do I lose weight quickly?"
    ]

# === USER NAME ===
if not st.session_state.name:
    name = st.sidebar.text_input("Your Name", placeholder="Jake")
    if name:
        st.session_state.name = name
        st.sidebar.success(f"Welcome, {name}!")

# === BODY WEIGHT & MACRO CALCULATOR ===
with st.sidebar:
    st.subheader("Body Stats")
    unit = st.radio("Weight Unit", ["kg", "st/lb"], horizontal=True)
    st.session_state.weight_unit = unit

    if unit == "kg":
        weight = st.number_input("Body Weight (kg)", min_value=30.0, max_value=200.0, value=st.session_state.body_weight_kg, step=0.1)
        st.session_state.body_weight_kg = weight
    else:
        stones = st.number_input("Stones", min_value=4, max_value=30, value=11)
        pounds = st.number_input("Pounds", min_value=0, max_value=13, value=0)
        weight_kg = (stones * 6.35029) + (pounds * 0.453592)
        st.session_state.body_weight_kg = weight_kg
        st.info(f"≈ {weight_kg:.1f} kg")

    goal = st.selectbox("Weight Goal", ["Lose Weight", "Maintain", "Gain Weight"])
    st.session_state.weight_goal = goal

    if st.button("Calculate Calories & Macros"):
        maintenance = st.session_state.body_weight_kg * 2.20462 * 15
        calories = maintenance + (200 if goal == "Gain Weight" else -200 if goal == "Lose Weight" else 0)
        protein = round(st.session_state.body_weight_kg * 2.20462 * 1.25)
        protein_cals = protein * 4
        remaining = max(0, calories - protein_cals)
        carbs = round(remaining * 0.5 / 4)
        fats = round(remaining * 0.5 / 9)

        st.session_state.calorie_goal = int(calories)
        st.session_state.macro_goal = {"protein": protein, "carbs": carbs, "fats": fats}
        st.success(f"Done! {int(calories)} cal | P{protein}g")

    st.divider()
    st.metric("Daily Calories", st.session_state.calorie_goal)
    col1, col2, col3 = st.columns(3)
    col1.metric("Protein", f"{st.session_state.macro_goal['protein']}g")
    col2.metric("Carbs", f"{st.session_state.macro_goal['carbs']}g")
    col3.metric("Fats", f"{st.session_state.macro_goal['fats']}g")

# === TABS ===
tab1, tab2, tab3 = st.tabs(["Fitness Coach", "Nutrition Coach", "Speaking Quest"])

# ========================================
# TAB 1: FITNESS COACH
# ========================================
with tab1:
    st.title(f"{coach_name} — Fitness Mode")

    fitness_prompt = f"""
    You are {coach_name}, {'motivational strength coach' if gender == 'Male (Woody)' else 'graceful, empowering trainer'}.
    Be fun, encouraging, under 120 words. Use emojis.
    Body weight: {st.session_state.body_weight_kg:.1f}kg
    History: {{history}}
    User: {{input}}
    {coach_name}:
    """
    prompt = ChatPromptTemplate.from_template(fitness_prompt)
    chain = prompt | llm | StrOutputParser()

    # Log Workouts
    workout = st.selectbox("Log Workout", [
        "Push-ups", "Pull-ups", "Sit-ups",
        "Run", "Walk (Outdoor)", "Walk (Treadmill)",
        "Cycle (Outdoor)", "Cycle (Static Bike)"
    ])

    if workout in ["Push-ups", "Pull-ups", "Sit-ups"]:
        variations = {
            "Push-ups": ["Normal", "Close-Grip", "Wide-Grip"],
            "Pull-ups": ["Normal", "Chin-ups", "Neutral-Grip"],
            "Sit-ups": ["Standard", "Russian Twists", "Leg Raises"]
        }
        variation = st.selectbox("Variation", variations[workout])
        reps = st.number_input("Reps", min_value=0, value=0)
        if st.button("Log Workout"):
            entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": workout.lower().replace("-", "_"), "variation": variation, "reps": reps}
            st.session_state.progress_fitness.append(entry)
            st.success(f"Logged {reps} {variation} {workout.lower()}!")

    elif workout == "Run":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Run"):
            if distance > 0 and time_min > 0:
                pace = round(time_min / distance, 2)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "run", "distance": distance, "time": time_min, "pace": pace}
                st.session_state.progress_fitness.append(entry)
                st.success(f"Logged {distance}km! Pace: {pace} min/km")

    elif workout == "Walk (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        terrain = st.selectbox("Terrain", ["Flat", "Hilly", "Mixed"])
        if st.button("Log Walk"):
            if distance > 0:
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_outdoor", "distance": distance, "time": time_min, "terrain": terrain}
                st.session_state.progress_fitness.append(entry)
                st.success(f"Logged {distance}km walk!")

    elif workout == "Walk (Treadmill)":
        speed = st.number_input("Speed (km/h)", min_value=0.0, step=0.1)
        incline = st.number_input("Incline (%)", min_value=0.0, step=0.5)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Treadmill"):
            if time_min > 0:
                distance = round(speed * (time_min / 60), 2)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_treadmill", "distance": distance, "time": time_min, "speed": speed, "incline": incline}
                st.session_state.progress_fitness.append(entry)
                st.success(f"Logged {distance}km!")

    elif workout == "Cycle (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Cycle"):
            if distance > 0 and time_min > 0:
                speed = round(distance / (time_min / 60), 1)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_outdoor", "distance": distance, "time": time_min, "avg_speed": speed}
                st.session_state.progress_fitness.append(entry)
                st.success(f"Logged {distance}km! Speed: {speed} km/h")

    elif workout == "Cycle (Static Bike)":
        time_min = st.number_input("Time (min)", min_value=0)
        resistance = st.slider("Resistance", 1, 20, 10)
        rpm = st.number_input("Avg RPM", min_value=0, value=70)
        if st.button("Log Static Bike"):
            if time_min > 0:
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_static", "time": time_min, "resistance": resistance, "rpm": rpm}
                st.session_state.progress_fitness.append(entry)
                st.success(f"Logged {time_min} min!")

    # Fitness Charts
    if st.session_state.progress_fitness:
        df = pd.DataFrame(st.session_state.progress_fitness)
        df["date"] = pd.to_datetime(df["date"])
        st.subheader("Fitness Progress")
        col1, col2 = st.columns(2)
        with col1:
            strength = df[df["type"].str.contains("push|pull|sit")]
            if not strength.empty:
                fig = px.line(strength, x="date", y="reps", color="variation", facet_col="type", markers=True)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            cardio = df[df["type"].str.contains("run|walk|cycle")]
            if not cardio.empty and "distance" in cardio.columns:
                cardio_dist = cardio.dropna(subset=["distance"])
                if not cardio_dist.empty:
                    fig = px.bar(cardio_dist, x="date", y="distance", color="type", barmode="group")
                    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Form Check")
    st.info("Describe your form — I’ll give feedback!")

    # Quick Start Buttons
    st.subheader("Quick Start")
    cols = st.columns(3)
    for i, starter in enumerate(st.session_state.fitness_starters):
        if cols[i].button(starter, key=f"fit_start_{i}"):
            user_prompt = starter
            break
    else:
        user_prompt = st.chat_input("Ask Fitness Coach...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                try:
                    response = chain.invoke({"history": history, "input": user_prompt})
                except:
                    response = "Check your Groq key."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ========================================
# TAB 2: NUTRITION COACH
# ========================================
with tab2:
    st.title(f"{coach_name} — Nutrition Mode")

    nutrition_prompt = f"""
    You are {coach_name}, {'direct nutrition expert' if gender == 'Male (Woody)' else 'intuitive, nurturing meal guide'}.
    Be encouraging, under 120 words. Suggest meals, recipes.
    Calorie goal: {st.session_state.calorie_goal}, Macros: P{st.session_state.macro_goal['protein']}g C{st.session_state.macro_goal['carbs']}g F{st.session_state.macro_goal['fats']}g
    History: {{history}}
    User: {{input}}
    {coach_name}:
    """
    prompt = ChatPromptTemplate.from_template(nutrition_prompt)
    chain = prompt | llm | StrOutputParser()

    meal = st.selectbox("Log Meal", ["Breakfast", "Lunch", "Dinner", "Snack"])
    calories = st.number_input("Calories", min_value=0, value=0)
    protein = st.number_input("Protein (g)", min_value=0, value=0)
    carbs = st.number_input("Carbs (g)", min_value=0, value=0)
    fats = st.number_input("Fats (g)", min_value=0, value=0)
    if st.button("Log Meal"):
        entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": meal.lower(), "calories": calories, "protein": protein, "carbs": carbs, "fats": fats}
        st.session_state.progress_nutrition.append(entry)
        st.success(f"Logged {meal}: {calories} cal")

    if st.session_state.progress_nutrition:
        df = pd.DataFrame(st.session_state.progress_nutrition)
        df["date"] = pd.to_datetime(df["date"])
        st.subheader("Nutrition Progress")
        today = df[df["date"].dt.date == datetime.now().date()]
        if not today.empty:
            total = today[["calories", "protein", "carbs", "fats"]].sum()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Calories", int(total["calories"]), st.session_state.calorie_goal)
            col2.metric("Protein", int(total["protein"]), st.session_state.macro_goal["protein"])
            col3.metric("Carbs", int(total["carbs"]), st.session_state.macro_goal["carbs"])
            col4.metric("Fats", int(total["fats"]), st.session_state.macro_goal["fats"])
        fig = px.bar(df, x="date", y=["protein", "carbs", "fats"], title="Daily Macros (g)")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Quick Start")
    cols = st.columns(4)
    for i, starter in enumerate(st.session_state.nutrition_starters):
        if cols[i].button(starter, key=f"nut_start_{i}"):
            user_prompt = starter
            break
    else:
        user_prompt = st.chat_input("Ask Nutrition Coach...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                try:
                    response = chain.invoke({"history": history, "input": user_prompt})
                except:
                    response = "Check your Groq key."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ========================================
# TAB 3: 60-LEVEL IELTS SPEAKING QUEST
# ========================================
with tab3:
    st.title(f"{coach_name} — IELTS Speaking Quest")

    # Level & XP Display
    col1, col2, col3 = st.columns(3)
    col1.metric("Level", st.session_state.level)
    col2.metric("XP", f"{st.session_state.xp}/100")
    col3.metric("Streak", f"{st.session_state.streak} days")

    progress = min(st.session_state.xp / 100, 1.0)
    st.progress(progress)
    st.caption(f"**Band {st.session_state.last_band:.1f}** → Next Level: {st.session_state.level + 1}")

    # Language & Part
    languages = {
        "English": "English", "中文": "Chinese", "Español": "Spanish", "हिन्दी": "Hindi",
        "العربية": "Arabic", "Português": "Portuguese", "বাংলা": "Bengali", "Русский": "Russian",
        "日本語": "Japanese", "Deutsch": "German", "Français": "French", "한국어": "Korean"
    }
    st.session_state.home_lang = st.selectbox(
        "Home Language", options=list(languages.keys()),
        format_func=lambda x: f"{x} ({languages[x]})",
        index=list(languages.keys()).index(st.session_state.home_lang) if st.session_state.home_lang in languages else 0
    )
    native_lang = languages[st.session_state.home_lang]

    st.session_state.part = st.selectbox("IELTS Part", ["Part 1", "Part 2", "Part 3"])

    # Dynamic Questions by Level
    questions = {
        "Part 1": {
            1: ["Tell me about your name.", "Do you work or study?"],
            10: ["What do you do in your free time?", "Do you like your hometown?"],
            30: ["How has technology changed daily life?", "Should students wear uniforms?"],
            50: ["How does advertising affect consumer behavior?", "Is climate change the biggest global challenge?"]
        },
        "Part 2": {
            1: "Describe your favorite food.",
            10: "Describe a person you admire.",
            30: "Describe a time you helped someone.",
            50: "Describe a law that should be changed."
        },
        "Part 3": {
            1: "Do you like food?",
            10: "Why do people admire others?",
            30: "How important is helping others in society?",
            50: "Should governments prioritize economic growth over environmental protection?"
        }
    }

    def get_question(part, level):
        bank = questions[part]
        if level <= 10:
            return bank[1][0] if part == "Part 1" else bank[1]
        elif level <= 30:
            return bank[10][0] if part == "Part 1" else bank[10]
        elif level <= 50:
            return bank[30][0] if part == "Part 1" else bank[30]
        else:
            return bank[50][0] if part == "Part 1" else bank[50]

    current_q = get_question(st.session_state.part, st.session_state.level)
    st.write(f"**Question:** {current_q}")

    # XP System
    def award_xp(band_score):
        xp_gain = 0
        if band_score >= 8.5:
            xp_gain = 25
        elif band_score >= 7.5:
            xp_gain = 18
        elif band_score >= 6.5:
            xp_gain = 12
        elif band_score >= 5.5:
            xp_gain = 8
        elif band_score >= 4.5:
            xp_gain = 5
        else:
            xp_gain = 2

        if st.session_state.streak > 3:
            xp_gain = int(xp_gain * 1.5)

        st.session_state.xp += xp_gain
        st.session_state.total_xp += xp_gain
        st.session_state.last_band = band_score

        while st.session_state.xp >= 100:
            st.session_state.xp -= 100
            st.session_state.level += 1
            st.balloons()
            st.success(f"**LEVEL UP! → Level {st.session_state.level}**")

        if st.session_state.level >= 60:
            st.success("**IELTS 9.0 READY! YOU ARE A MASTER!**")
            st.balloons()

    # Speaking Prompt
    speaking_prompt = f"""
    You are {coach_name}, a strict but fair IELTS Speaking examiner.
    User is at **Level {st.session_state.level}** (Band ~{min(9.0, st.session_state.level / 10):.1f}).
    Question: {current_q}
    User home language: {native_lang}

    INSTRUCTIONS:
    1. Ask the question in {native_lang}.
    2. After user answers (in English):
       - Give **Band Score** (0.5 increments, 1.0–9.0)
       - 1 **Strength**
       - 1 **Improvement**
       - **Example Answer** (Band 8.5+)
    3. Be **stricter at higher levels** (Level 50+ = expect near-native).
    4. Keep under 180 words.

    History: {{history}}
    User: {{input}}
    {coach_name}:
    """
    prompt = ChatPromptTemplate.from_template(speaking_prompt)
    chain = prompt | llm | StrOutputParser()

    # Quick Start
    starters = ["Start speaking practice", "Give me a harder question", "How do I reach Level 60?"]
    st.subheader("Quick Start")
    cols = st.columns(3)
    for i, s in enumerate(starters):
        if cols[i].button(s, key=f"qs_{i}"):
            user_prompt = s
            break
    else:
        user_prompt = st.chat_input("Speak your answer...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Scoring..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                try:
                    response = chain.invoke({"history": history, "input": user_prompt})
                    band_match = re.search(r"Band[\s:]*([0-9]\.[0-9])", response)
                    if band_match:
                        band = float(band_match.group(1))
                        award_xp(band)
                except:
                    response = "Error. Try again."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})