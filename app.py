import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import plotly.express as px
import pandas as pd
from datetime import datetime
import re
import json
import os
from groq import GroqError

# === CONFIG ===
st.set_page_config(page_title="Coach Woody", page_icon="trophy", layout="wide")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === GENDER TOGGLE ===
gender = st.sidebar.radio("Coach Gender", ["Male (Woody)", "Female (Hibiki)"], horizontal=True)
coach_name = "Woody" if gender == "Male (Woody)" else "Hibiki"

# === LLM ===
llm = ChatGroq(model="llama3-70b-8192", api_key=GROQ_API_KEY, temperature=0.7, max_tokens=1024)

# === DATA PERSISTENCE ===
DATA_FILE = "user_data.json"

def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state, f, default=str)

# Initialize session state
if "initialized" not in st.session_state:
    user_data = load_user_data()
    defaults = {
        "messages": [],
        "level": 1,
        "xp": 0,
        "total_xp": 0,
        "last_band": 0.0,
        "streak": 0,
        "progress_fitness": [],
        "progress_nutrition": [],
        "name": "",
        "body_weight_kg": 70.0,
        "weight_unit": "kg",
        "weight_goal": "Maintain",
        "calorie_goal": 2000,
        "macro_goal": {"protein": 150, "carbs": 250, "fats": 70},
        "home_lang": "English",
        "part": "Part 1",
        "fitness_starters": [
            "How do I improve my push-up form?",
            "What's a good 5K training plan?",
            "How to recover after a workout?"
        ],
        "nutrition_starters": [
            "How do I find my daily calorie intake?",
            "What are ideal macro splits?",
            "Suggest a high-protein meal under 500 cal.",
            "How do I lose weight quickly?"
        ],
        "question_history": [],
        "onboarded": False,
        "quick_prompt": None
    }
    for key, value in defaults.items():
        st.session_state[key] = user_data.get(key, value)
    st.session_state["initialized"] = True

# === ONBOARDING ===
if not st.session_state.get("onboarded", False):
    with st.expander("Welcome to Coach Woody!", expanded=True):
        st.markdown(f"""
        **Hi, {st.session_state.name or 'Athlete'}!** 👋  
        Coach Woody helps you:  
        - 🏋️ Log workouts and get fitness tips  
        - 🥗 Track meals and macros  
        - 🗣️ Practice IELTS Speaking with a 60-level quest  
        Start by setting your **name** and **body stats** in the sidebar. Choose a tab to begin!  
        """)
        if st.button("Got it!"):
            st.session_state["onboarded"] = True
            save_user_data()

# === USER NAME ===
if not st.session_state.name:
    name = st.sidebar.text_input("Your Name", placeholder="Jake")
    if name:
        st.session_state.name = name
        st.sidebar.success(f"Welcome, {name}!")
        save_user_data()

# === BODY WEIGHT & MACRO CALCULATOR ===
with st.sidebar:
    st.subheader("Body Stats")
    st.info("Enter your weight and goal to calculate daily calories and macros.")
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
        save_user_data()
    st.divider()
    st.metric("Level", st.session_state.level)
    st.metric("XP", f"{st.session_state.xp}/100")
    st.metric("Total XP", st.session_state.total_xp)
    st.metric("Daily Calories", st.session_state.calorie_goal)
    col1, col2, col3 = st.columns(3)
    col1.metric("Protein", f"{st.session_state.macro_goal['protein']}g")
    col2.metric("Carbs", f"{st.session_state.macro_goal['carbs']}g")
    col3.metric("Fats", f"{st.session_state.macro_goal['fats']}g")

# === XP SYSTEM ===
def award_fitness_xp(workout_type, reps=0, distance=0, time_min=0):
    xp_gain = 5
    if workout_type in ["push_ups", "pull_ups", "sit_ups"]:
        xp_gain += reps // 10
    elif workout_type in ["run", "walk_outdoor", "cycle_outdoor"]:
        xp_gain += int(distance * 2)
    elif workout_type in ["walk_treadmill", "cycle_static"]:
        xp_gain += time_min // 10
    st.session_state.xp += xp_gain
    st.session_state.total_xp += xp_gain
    check_level_up()
    return xp_gain

def award_nutrition_xp(calories, protein, carbs, fats):
    xp_gain = 5
    if (abs(protein - st.session_state.macro_goal["protein"]) <= 0.1 * st.session_state.macro_goal["protein"] and
        abs(carbs - st.session_state.macro_goal["carbs"]) <= 0.1 * st.session_state.macro_goal["carbs"] and
        abs(fats - st.session_state.macro_goal["fats"]) <= 0.1 * st.session_state.macro_goal["fats"]):
        xp_gain += 10
    st.session_state.xp += xp_gain
    st.session_state.total_xp += xp_gain
    check_level_up()
    return xp_gain

def check_level_up():
    while st.session_state.xp >= 100:
        st.session_state.xp -= 100
        st.session_state.level += 1
        st.balloons()
        st.success(f"**LEVEL UP! → Level {st.session_state.level}**")
    save_user_data()

# === LLM INVOCATION ===
@st.cache_data(ttl=3600)
def cached_chain_invoke(chain, history, user_input):
    try:
        response = chain.invoke({"history": history, "input": user_input})
        return response
    except GroqError as e:
        if "rate_limit" in str(e).lower():
            return "Rate limit reached. Please wait and try again."
        elif "authentication" in str(e).lower():
            return "Invalid Groq API key. Please check your key."
        else:
            return f"Groq API error: {str(e)}"
    except ConnectionError:
        return "Network issue. Please check your connection."
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: {str(e)}\n")
        return "Unexpected error. Please try again."

# === TABS ===
tab1, tab2, tab3 = st.tabs(["Fitness Coach", "Nutrition Coach", "Speaking Quest"])

# ========================================
# TAB 1: FITNESS COACH
# ========================================
with tab1:
    st.title(f"{coach_name} — Fitness Mode# Fitness Coach")
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
            xp_gain = award_fitness_xp(workout.lower().replace("-", "_"), reps=reps)
            save_user_data()
            st.success(f"Logged {reps} {variation} {workout.lower()}! +{xp_gain} XP")
    elif workout == "Run":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Run"):
            if distance > 0 and time_min > 0:
                pace = round(time_min / distance, 2)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "run", "distance": distance, "time": time_min, "pace": pace}
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("run", distance=distance)
                save_user_data()
                st.success(f"Logged {distance}km! Pace: {pace} min/km! +{xp_gain} XP")
    elif workout == "Walk (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        terrain = st.selectbox("Terrain", ["Flat", "Hilly", "Mixed"])
        if st.button("Log Walk"):
            if distance > 0:
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_outdoor", "distance": distance, "time": time_min, "terrain": terrain}
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_outdoor", distance=distance)
                save_user_data()
                st.success(f"Logged {distance}km walk! +{xp_gain} XP")
    elif workout == "Walk (Treadmill)":
        speed = st.number_input("Speed (km/h)", min_value=0.0, step=0.1)
        incline = st.number_input("Incline (%)", min_value=0.0, step=0.5)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Treadmill"):
            if time_min > 0:
                distance = round(speed * (time_min / 60), 2)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_treadmill", "distance": distance, "time": time_min, "speed": speed, "incline": incline}
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_treadmill", time_min=time_min)
                save_user_data()
                st.success(f"Logged {distance}km! +{xp_gain} XP")
    elif workout == "Cycle (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Cycle"):
            if distance > 0 and time_min > 0:
                speed = round(distance / (time_min / 60), 1)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_outdoor", "distance": distance, "time": time_min, "avg_speed": speed}
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_outdoor", distance=distance)
                save_user_data()
                st.success(f"Logged {distance}km! Speed: {speed} km/h! +{xp_gain} XP")
    elif workout == "Cycle (Static Bike)":
        time_min = st.number_input("Time (min)", min_value=0)
        resistance = st.slider("Resistance", 1, 20, 10)
        rpm = st.number_input("Avg RPM", min_value=0, value=70)
        if st.button("Log Static Bike"):
            if time_min > 0:
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_static", "time": time_min, "resistance": resistance, "rpm": rpm}
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_static", time_min=time_min)
                save_user_data()
                st.success(f"Logged {time_min} min! +{xp_gain} XP")
    if st.session_state.progress_fitness:
        df = pd.DataFrame(st.session_state.progress_fitness)
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= datetime.now() - pd.Timedelta(days=30)]
        st.subheader("Fitness Progress")
        col1, col2 = st.columns(2)
        with col1:
            strength = df[df["type"].str.contains("push|pull|sit")]
            if not strength.empty:
                fig = px.line(strength, x="date", y="reps", color="variation", facet_col="type", markers=True)
                fig.update_layout(font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            cardio = df[df["type"].str.contains("run|walk|cycle")]
            if not cardio.empty and "distance" in cardio.columns:
                cardio_dist = cardio.dropna(subset=["distance"])
                if not cardio_dist.empty:
                    fig = px.bar(cardio_dist, x="date", y="distance", color="type", barmode="group")
                    fig.update_layout(font=dict(size=14))
                    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Form Check")
    st.info("Describe your form — I’ll give feedback!")
    st.subheader("Quick Start")
    cols = st.columns(3)
    for i, starter in enumerate(st.session_state.fitness_starters):
        if cols[i].button(starter, key=f"fit_start_{i}"):
            st.session_state.quick_prompt = starter
    user_prompt = st.chat_input("Ask Fitness Coach...", key="fitness_chat")
    if st.session_state.quick_prompt:
        user_prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                response = cached_chain_invoke(chain, history, user_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_user_data()

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
        xp_gain = award_nutrition_xp(calories, protein, carbs, fats)
        save_user_data()
        st.success(f"Logged {meal}: {calories} cal! +{xp_gain} XP")
    if st.session_state.progress_nutrition:
        df = pd.DataFrame(st.session_state.progress_nutrition)
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= datetime.now() - pd.Timedelta(days=30)]
        st.subheader("Nutrition Progress")
        today = df[df["date"].dt.date == datetime.now().date()]
        if not today.empty:
            total = today[["calories", "protein", "carbs", "fats"]].sum()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Calories", int(total["calories"]), st.session_state.calorie_goal)
            col2.metric("Protein", int(total["protein"]), st.session_state.macro_goal["protein"])
            col3.metric("Carbs", int(total["carbs"]), st.session_state.macro_goal["carbs"])
            col4.metric("Fats", int(total["fats"]), st.session_state.macro_goal["fats"])
        fig = px.bar(
            df,
            x="date",
            y=["protein", "carbs", "fats"],
            title="Daily Macros (g)",
            color_discrete_map={"protein": "#1f77b4", "carbs": "#2ca02c", "fats": "#d62728"}
        )
        fig.update_layout(font=dict(size=14))
        st.plotly_chart(fig, use_container_width=True)
        daily_calories = df.groupby(df["date"].dt.date)["calories"].sum().reset_index()
        daily_calories["goal"] = st.session_state.calorie_goal
        fig = px.line(
            daily_calories,
            x="date",
            y=["calories", "goal"],
            title="Daily Calories vs. Goal",
            labels={"value": "Calories", "variable": "Type"},
            markers=True
        )
        fig.update_traces(line=dict(color="#1f77b4"), selector=dict(name="calories"))
        fig.update_traces(line=dict(color="#ff7f0e", dash="dash"), selector=dict(name="goal"))
        fig.update_layout(font=dict(size=14))
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Quick Start")
    cols = st.columns(4)
    for i, starter in enumerate(st.session_state.nutrition_starters):
        if cols[i].button(starter, key=f"nut_start_{i}"):
            st.session_state.quick_prompt = starter
    user_prompt = st.chat_input("Ask Nutrition Coach...", key="nutrition_chat")
    if st.session_state.quick_prompt:
        user_prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                response = cached_chain_invoke(chain, history, user_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_user_data()

# ========================================
# TAB 3: 60-LEVEL IELTS SPEAKING QUEST
# ========================================
with tab3:
    st.title(f"{coach_name} — IELTS Speaking Quest")
    col1, col2, col3 = st.columns(3)
    col1.metric("Level", st.session_state.level)
    col2.metric("XP", f"{st.session_state.xp}/100")
    col3.metric("Streak", f"{st.session_state.streak} days")
    progress = min(st.session_state.xp / 100, 1.0)
    st.progress(progress)
    st.caption Says: st.caption(f"**Band {st.session_state.last_band:.1f}** → Next Level: {st.session_state.level + 1}")
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
    practice_mode = st.checkbox("Practice Mode (No Scoring)")
    st.write(f"**{'Practice ' if practice_mode else ''}Question:** {current_q}")
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
        check_level_up()
        if st.session_state.level >= 60:
            st.success("**IELTS 9.0 READY! YOU ARE A MASTER!**")
            st.balloons()
        return xp_gain
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
    starters = ["Start speaking practice", "Give me a harder question", "How do I reach Level 60?"]
    st.subheader("Quick Start")
    cols = st.columns(3)
    for i, s in enumerate(starters):
        if cols[i].button(s, key=f"qs_{i}"):
            st.session_state.quick_prompt = s
    user_prompt = st.chat_input("Speak your answer...", key="ielts_chat")
    if st.session_state.quick_prompt:
        user_prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Scoring..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                response = cached_chain_invoke(chain, history, user_prompt)
                if not practice_mode:
                    band_match = re.search(r"Band[\s:]*([0-9]\.[0-9])", response)
                    band = float(band_match.group(1)) if band_match else 0.0
                    xp_gain = award_xp(band)
                    response += f"\n**+{xp_gain} XP**"
                st.session_state.question_history.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "question": current_q,
                    "answer": user_prompt,
                    "band": band if not practice_mode else None
                })
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_user_data()
    with st.expander("Past Questions"):
        if st.session_state.question_history:
            df = pd.DataFrame(st.session_state.question_history)
            st.dataframe(df[["date", "question", "band"]], use_container_width=True)
    if st.session_state.question_history:
        df = pd.DataFrame(st.session_state.question_history)
        df = df[df["band"].notnull()]
        if not df.empty:
            fig = px.line(df, x="date", y="band", title="Band Score Progress", markers=True)
            fig.update_layout(font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)