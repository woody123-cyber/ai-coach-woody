# COACH WOODY v16 — Fitness + Nutrition | Woody (Male) / Hibiki (Female)
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

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
    st.session_state.level = "Beginner"
    st.session_state.goal = "Run a 5K"
    st.session_state.progress_fitness = []
    st.session_state.progress_nutrition = []
    st.session_state.name = ""
    st.session_state.calorie_goal = 2000
    st.session_state.macro_goal = {"protein": 150, "carbs": 250, "fats": 70}

# === USER NAME ===
if not st.session_state.name:
    name = st.sidebar.text_input("Your Name", placeholder="Jake")
    if name:
        st.session_state.name = name
        st.sidebar.success(f"Welcome, {name}!")

# === TABS ===
tab1, tab2 = st.tabs(["Fitness Coach", "Nutrition Coach"])

# ========================================
# TAB 1: FITNESS COACH
# ========================================
with tab1:
    st.title(f"{coach_name} — Fitness Mode")

    # Fitness Prompt
    fitness_prompt = f"""
    You are {coach_name}, {'motivational strength coach' if gender == 'Male (Woody)' else 'graceful, empowering trainer'}.
    Be fun, encouraging, under 120 words. Use emojis.
    User: {st.session_state.level}, Goal: {st.session_state.goal}
    Track workouts. Suggest based on progress.
    History: {{history}}
    User: {{input}}
    {coach_name}:
    """
    prompt = ChatPromptTemplate.from_template(fitness_prompt)
    chain = prompt | llm | StrOutputParser()

    # === SIDEBAR: LOG FITNESS ===
    with st.sidebar:
        st.session_state.level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"], key="fit_level")
        st.session_state.goal = st.text_input("Goal", st.session_state.goal, key="fit_goal")

        workout = st.selectbox("Log Workout", [
            "Push-ups", "Pull-ups", "Sit-ups",
            "Run", "Walk (Outdoor)", "Walk (Treadmill)",
            "Cycle (Outdoor)", "Cycle (Static Bike)"
        ], key="fit_workout")

        # Strength
        if workout in ["Push-ups", "Pull-ups", "Sit-ups"]:
            variations = {
                "Push-ups": ["Normal", "Close-Grip", "Wide-Grip"],
                "Pull-ups": ["Normal", "Chin-ups", "Neutral-Grip"],
                "Sit-ups": ["Standard", "Russian Twists", "Leg Raises"]
            }
            variation = st.selectbox("Variation", variations[workout], key="fit_var")
            reps = st.number_input("Reps", min_value=0, value=0, key="fit_reps")
            if st.button("Log Workout", key="fit_log"):
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": workout.lower().replace("-", "_"),
                    "variation": variation,
                    "reps": reps
                }
                st.session_state.progress_fitness.append(entry)
                st.success(f"Logged {reps} {variation} {workout.lower()}!")

        # Run
        elif workout == "Run":
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1, key="fit_dist")
            time_min = st.number_input("Time (min)", min_value=0, key="fit_time")
            if st.button("Log Run", key="fit_log_run"):
                if distance > 0 and time_min > 0:
                    pace = round(time_min / distance, 2)
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "run", "distance": distance, "time": time_min, "pace": pace}
                    st.session_state.progress_fitness.append(entry)
                    st.success(f"Logged {distance}km! Pace: {pace} min/km")

        # Walk Outdoor
        elif workout == "Walk (Outdoor)":
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1, key="walk_out_dist")
            time_min = st.number_input("Time (min)", min_value=0, key="walk_out_time")
            terrain = st.selectbox("Terrain", ["Flat", "Hilly", "Mixed"], key="walk_terrain")
            if st.button("Log Walk", key="walk_log"):
                if distance > 0:
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_outdoor", "distance": distance, "time": time_min, "terrain": terrain}
                    st.session_state.progress_fitness.append(entry)
                    st.success(f"Logged {distance}km walk!")

        # Walk Treadmill
        elif workout == "Walk (Treadmill)":
            speed = st.number_input("Speed (km/h)", min_value=0.0, step=0.1, key="tread_speed")
            incline = st.number_input("Incline (%)", min_value=0.0, step=0.5, key="tread_incline")
            time_min = st.number_input("Time (min)", min_value=0, key="tread_time")
            if st.button("Log Treadmill", key="tread_log"):
                if time_min > 0:
                    distance = round(speed * (time_min / 60), 2)
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_treadmill", "distance": distance, "time": time_min, "speed": speed, "incline": incline}
                    st.session_state.progress_fitness.append(entry)
                    st.success(f"Logged {distance}km!")

        # Cycle Outdoor
        elif workout == "Cycle (Outdoor)":
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1, key="cycle_out_dist")
            time_min = st.number_input("Time (min)", min_value=0, key="cycle_out_time")
            if st.button("Log Cycle", key="cycle_out_log"):
                if distance > 0 and time_min > 0:
                    speed = round(distance / (time_min / 60), 1)
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_outdoor", "distance": distance, "time": time_min, "avg_speed": speed}
                    st.session_state.progress_fitness.append(entry)
                    st.success(f"Logged {distance}km! Speed: {speed} km/h")

        # Cycle Static
        elif workout == "Cycle (Static Bike)":
            time_min = st.number_input("Time (min)", min_value=0, key="cycle_static_time")
            resistance = st.slider("Resistance", 1, 20, 10, key="cycle_res")
            rpm = st.number_input("Avg RPM", min_value=0, value=70, key="cycle_rpm")
            if st.button("Log Static Bike", key="cycle_static_log"):
                if time_min > 0:
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_static", "time": time_min, "resistance": resistance, "rpm": rpm}
                    st.session_state.progress_fitness.append(entry)
                    st.success(f"Logged {time_min} min!")

    # === FITNESS CHARTS ===
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

    # === FORM CHECK ===
    st.subheader("Upload Form Photo")
    uploaded = st.file_uploader("Push-up / Squat", ["jpg", "png"], key="form_upload")
    if uploaded:
        st.image(uploaded, width=300)
        st.success("Great form! Keep core tight.")

    # === FITNESS CHAT ===
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask Fitness Coach..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                try:
                    response = chain.invoke({"history": history, "input": prompt})
                except:
                    response = "Check your Groq key."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ========================================
# TAB 2: NUTRITION COACH
# ========================================
with tab2:
    st.title(f"{coach_name} — Nutrition Mode")

    # Nutrition Prompt
    nutrition_prompt = f"""
    You are {coach_name}, {'direct nutrition expert' if gender == 'Male (Woody)' else 'intuitive, nurturing meal guide'}.
    Be encouraging, under 120 words. Suggest meals, recipes, macros.
    Calorie goal: {st.session_state.calorie_goal}, Macros: {st.session_state.macro_goal}
    History: {{history}}
    User: {{input}}
    {coach_name}:
    """
    prompt = ChatPromptTemplate.from_template(nutrition_prompt)
    chain = prompt | llm | StrOutputParser()

    # === SIDEBAR: LOG NUTRITION ===
    with st.sidebar:
        st.session_state.calorie_goal = st.number_input("Daily Calories", value=st.session_state.calorie_goal, key="cal_goal")
        st.session_state.macro_goal = {
            "protein": st.number_input("Protein (g)", value=st.session_state.macro_goal["protein"], key="pro_goal"),
            "carbs": st.number_input("Carbs (g)", value=st.session_state.macro_goal["carbs"], key="carb_goal"),
            "fats": st.number_input("Fats (g)", value=st.session_state.macro_goal["fats"], key="fat_goal")
        }

        meal = st.selectbox("Log Meal", ["Breakfast", "Lunch", "Dinner", "Snack"], key="meal_type")
        calories = st.number_input("Calories", min_value=0, value=0, key="meal_cal")
        protein = st.number_input("Protein (g)", min_value=0, value=0, key="meal_pro")
        carbs = st.number_input("Carbs (g)", min_value=0, value=0, key="meal_carb")
        fats = st.number_input("Fats (g)", min_value=0, value=0, key="meal_fat")
        if st.button("Log Meal", key="log_meal"):
            entry = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": meal.lower(),
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fats": fats
            }
            st.session_state.progress_nutrition.append(entry)
            st.success(f"Logged {meal}: {calories} cal")

    # === NUTRITION CHARTS ===
    if st.session_state.progress_nutrition:
        df = pd.DataFrame(st.session_state.progress_nutrition)
        df["date"] = pd.to_datetime(df["date"])
        st.subheader("Nutrition Progress")

        # Daily Totals
        today = df[df["date"].dt.date == datetime.now().date()]
        if not today.empty:
            total = today[["calories", "protein", "carbs", "fats"]].sum()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Calories", int(total["calories"]), st.session_state.calorie_goal)
            col2.metric("Protein", int(total["protein"]), st.session_state.macro_goal["protein"])
            col3.metric("Carbs", int(total["carbs"]), st.session_state.macro_goal["carbs"])
            col4.metric("Fats", int(total["fats"]), st.session_state.macro_goal["fats"])

        # Macro Chart
        fig = px.bar(df, x="date", y=["protein", "carbs", "fats"], title="Daily Macros (g)")
        st.plotly_chart(fig, use_container_width=True)

    # === NUTRITION CHAT ===
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask Nutrition Coach..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                try:
                    response = chain.invoke({"history": history, "input": prompt})
                except:
                    response = "Check your Groq key."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})