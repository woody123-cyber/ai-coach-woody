# COACH WOODY v23 — 60-LEVEL IELTS QUEST (HARD MODE)
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import plotly.express as px
import pandas as pd
from datetime import datetime

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

# === USER NAME ===
if not st.session_state.name:
    name = st.sidebar.text_input("Your Name", placeholder="Jake")
    if name:
        st.session_state.name = name
        st.sidebar.success(f"Welcome, {name}!")

# === BODY WEIGHT & MACRO CALCULATOR (unchanged) ===
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
# TAB 3: 60-LEVEL IELTS QUEST
# ========================================
with tab3:
    st.title(f"{coach_name} — IELTS Speaking Quest")

    # === LEVEL & XP BAR ===
    col1, col2, col3 = st.columns(3)
    col1.metric("Level", st.session_state.level)
    col2.metric("XP", f"{st.session_state.xp}/100")
    col3.metric("Streak", f"{st.session_state.streak} days")

    # Progress bar
    progress = min(st.session_state.xp / 100, 1.0)
    st.progress(progress)
    st.caption(f"**Band {st.session_state.last_band:.1f}** → Next Level: {st.session_state.level + 1}")

    # === LANGUAGE & PART SELECTOR ===
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

    # === DYNAMIC QUESTION BANK (by level) ===
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

    # Get question based on level
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

    # === XP & LEVEL LOGIC ===
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

        # Streak bonus
        if st.session_state.streak > 3:
            xp_gain = int(xp_gain * 1.5)

        st.session_state.xp += xp_gain
        st.session_state.total_xp += xp_gain
        st.session_state.last_band = band_score

        # Level up
        while st.session_state.xp >= 100:
            st.session_state.xp -= 100
            st.session_state.level += 1
            st.balloons()
            st.success(f"**LEVEL UP! → Level {st.session_state.level}**")

        # Level 60 = Victory
        if st.session_state.level >= 60:
            st.success("**CONGRATULATIONS! YOU ARE IELTS 9.0 READY!**")
            st.balloons()

    # === SPEAKING COACH PROMPT ===
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

    # === QUICK START ===
    starters = ["Start speaking practice", "Give me a harder question", "How do I reach Level 60?"]
    st.subheader("Quick Start")
    cols = st.columns(3)
    for i, s in enumerate(starters):
        if cols[i].button(s, key=f"qs_{i}"):
            prompt = s

    # === CHAT ===
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Speak your answer..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Scoring..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                try:
                    response = chain.invoke({"history": history, "input": prompt})
                    # Extract band score
                    import re
                    band_match = re.search(r"Band[\s:]*([0-9]\.[0-9])", response)
                    if band_match:
                        band = float(band_match.group(1))
                        award_xp(band)
                except:
                    response = "Error. Try again."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})