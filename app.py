import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import plotly.express as px
import pandas as pd
from datetime import datetime
import os
import json
from groq import GroqError

# === CONFIG ===
st.set_page_config(page_title="Coach Woody", page_icon="trophy", layout="wide")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === GENDER TOGGLE ===
gender = st.sidebar.radio("Coach Gender", ["Male (Woody)", "Female (Hibiki)"], horizontal=True)
coach_name = "Woody" if gender == "Male (Woody)" else "Hibiki"

# === LLM ===
try:
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_API_KEY, temperature=0.7)
except Exception as e:
    st.error(f"Failed to initialize Groq LLM: {str(e)}")
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.now()}: {str(e)}\n")
    st.stop()

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

# === SESSION STATE ===
if "initialized" not in st.session_state:
    user_data = load_user_data()
    defaults = {
        "messages": [],
        "level": 1,
        "xp": 0,
        "total_xp": 0,
        "progress_fitness": [],
        "progress_nutrition": [],
        "name": "",
        "body_weight_kg": 70.0,
        "weight_unit": "kg",
        "weight_goal": "Maintain",
        "calorie_goal": 2000,
        "macro_goal": {"protein": 150, "carbs": 250, "fats": 70},
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
        "xp_history": [],
        "onboarded": False,
        "quick_prompt": None,
        "user_gender": "Male",
        "user_age": 30,
        "height_cm": 170.0,
        "bmr": 0
    }
    for key, value in defaults.items():
        st.session_state[key] = user_data.get(key, value)
    st.session_state["initialized"] = True

# === USER NAME ===
if not st.session_state.name:
    name = st.sidebar.text_input("Your Name", placeholder="Jake")
    if name:
        st.session_state.name = name
        st.sidebar.success(f"Welcome, {name}!")

# === BODY STATS & BMR ===
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
    st.session_state.user_gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
    st.session_state.user_age = st.number_input("Age", min_value=18, max_value=100, value=st.session_state.user_age)
    st.session_state.height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=st.session_state.height_cm, step=0.1)
    goal = st.selectbox("Weight Goal", ["Lose Weight", "Maintain", "Gain Weight"])
    st.session_state.weight_goal = goal
    if st.button("Calculate Calories & Macros"):
        if st.session_state.user_gender == "Male":
            bmr = 88.362 + (13.397 * st.session_state.body_weight_kg) + (4.799 * st.session_state.height_cm) - (5.677 * st.session_state.user_age)
        else:
            bmr = 447.593 + (9.247 * st.session_state.body_weight_kg) + (3.098 * st.session_state.height_cm) - (4.330 * st.session_state.user_age)
        st.session_state.bmr = int(bmr)
        maintenance = bmr * 1.55  # Assume moderate activity multiplier
        calories = maintenance + (200 if goal == "Gain Weight" else -200 if goal == "Lose Weight" else 0)
        protein = round(st.session_state.body_weight_kg * 2.20462 * 1.25)
        protein_cals = protein * 4
        remaining = max(0, calories - protein_cals)
        carbs = round(remaining * 0.5 / 4)
        fats = round(remaining * 0.5 / 9)
        st.session_state.calorie_goal = int(calories)
        st.session_state.macro_goal = {"protein": protein, "carbs": carbs, "fats": fats}
        st.success(f"Done! BMR: {st.session_state.bmr} cal | Daily Calories: {int(calories)} cal | P{protein}g")
        save_user_data()
    st.divider()
    st.metric("BMR", st.session_state.bmr)
    st.metric("Level", st.session_state.level)
    st.metric("XP", f"{st.session_state.xp}/100")
    st.metric("Total XP", st.session_state.total_xp)
    st.metric("Daily Calories", st.session_state.calorie_goal)
    col1, col2, col3 = st.columns(3)
    col1.metric("Protein", f"{st.session_state.macro_goal['protein']}g")
    col2.metric("Carbs", f"{st.session_state.macro_goal['carbs']}g")
    col3.metric("Fats", f"{st.session_state.macro_goal['fats']}g")

# === XP SYSTEM ===
def award_fitness_xp(workout_type, reps=0, distance=0, time_min=0, intensity="Medium"):
    xp_gain = 10
    intensity_multipliers = {"Low": 1.0, "Medium": 1.5, "High": 2.0}
    xp_gain *= intensity_multipliers[intensity]
    if workout_type in ["push_ups", "pull_ups", "sit_ups"]:
        xp_gain += reps // 5
    elif workout_type in ["run", "walk_outdoor", "cycle_outdoor"]:
        xp_gain += int(distance * 3)
    elif workout_type in ["walk_treadmill", "cycle_static"]:
        xp_gain += time_min // 5
    df = pd.DataFrame(st.session_state.progress_fitness)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        week_start = datetime.now() - pd.Timedelta(days=datetime.now().weekday())
        week_logs = df[df["date"] >= week_start]
        unique_days = len(week_logs["date"].dt.date.unique())
        if unique_days >= 3:
            xp_gain += 50
    st.session_state.xp += xp_gain
    st.session_state.total_xp += xp_gain
    # Log XP source
    st.session_state.xp_history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": f"{workout_type} ({intensity})",
        "xp": xp_gain
    })
    check_level_up()
    return xp_gain

def award_nutrition_xp(calories, protein, carbs, fats):
    xp_gain = 10
    if calories > 0:
        protein_diff = abs(protein - st.session_state.macro_goal["protein"]) / st.session_state.macro_goal["protein"]
        carbs_diff = abs(carbs - st.session_state.macro_goal["carbs"]) / st.session_state.macro_goal["carbs"]
        fats_diff = abs(fats - st.session_state.macro_goal["fats"]) / st.session_state.macro_goal["fats"]
        balance_score = max(0, 100 - (protein_diff + carbs_diff + fats_diff) * 100 / 3)
        xp_gain += int(balance_score * 0.15)
    df = pd.DataFrame(st.session_state.progress_nutrition)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        last_7_days = df[df["date"] >= datetime.now() - pd.Timedelta(days=7)]
        daily_totals = last_7_days.groupby(last_7_days["date"].dt.date)["calories"].sum()
        goal_hits = sum(1 for c in daily_totals if abs(c - st.session_state.calorie_goal) <= 0.1 * st.session_state.calorie_goal)
        if goal_hits >= 3:
            xp_gain += 20
        today = df[df["date"].dt.date == datetime.now().date()]
        if len(today) >= 3:
            xp_gain += 10
    st.session_state.xp += xp_gain
    st.session_state.total_xp += xp_gain
    st.session_state.xp_history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "Meal Log (Balance Score: {:.0f}%)".format(balance_score) if calories > 0 else "Meal Log",
        "xp": xp_gain
    })
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
def chain_invoke(chain, history, user_input):
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
tab1, tab2 = st.tabs(["Fitness Coach", "Nutrition Coach"])

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
    # MET values for calories burned
    met_values = {
        "push_ups": {"Low": 3.8, "Medium": 5.0, "High": 7.0},
        "pull_ups": {"Low": 3.8, "Medium": 5.0, "High": 7.0},
        "sit_ups": {"Low": 3.8, "Medium": 5.0, "High": 7.0},
        "run": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
        "walk_outdoor": {"Low": 3.0, "Medium": 4.0, "High": 5.0},
        "walk_treadmill": {"Low": 3.0, "Medium": 4.0, "High": 5.0},
        "cycle_outdoor": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
        "cycle_static": {"Low": 6.0, "Medium": 8.0, "High": 10.0}
    }
    workout = st.selectbox("Log Workout", [
        "Push-ups", "Pull-ups", "Sit-ups",
        "Run", "Walk (Outdoor)", "Walk (Treadmill)",
        "Cycle (Outdoor)", "Cycle (Static Bike)"
    ])
    intensity = st.selectbox("Intensity", ["Low", "Medium", "High"])
    if workout in ["Push-ups", "Pull-ups", "Sit-ups"]:
        variations = {
            "Push-ups": ["Normal", "Close-Grip", "Wide-Grip"],
            "Pull-ups": ["Normal", "Chin-ups", "Neutral-Grip"],
            "Sit-ups": ["Standard", "Russian Twists", "Leg Raises"]
        }
        variation = st.selectbox("Variation", variations[workout])
        reps = st.number_input("Reps", min_value=0, value=0)
        time_min = st.number_input("Estimated Time (min)", min_value=0.0, value=5.0, step=0.1)  # New: Time for calories
        if st.button("Log Workout"):
            type_lower = workout.lower().replace("-", "_")
            entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": type_lower, "variation": variation, "reps": reps, "intensity": intensity, "time": time_min}
            met = met_values.get(type_lower, {"Medium": 4.0}).get(intensity, 4.0)
            calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
            entry["calories_burned"] = int(calories_burned)
            st.session_state.progress_fitness.append(entry)
            xp_gain = award_fitness_xp(type_lower, reps=reps, intensity=intensity)
            save_user_data()
            st.success(f"Logged {reps} {variation} {workout.lower()} ({intensity})! Calories Burned: {entry['calories_burned']} +{xp_gain} XP")
    elif workout == "Run":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Run"):
            if distance > 0 and time_min > 0:
                pace = round(time_min / distance, 2)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "run", "distance": distance, "time": time_min, "pace": pace, "intensity": intensity}
                met = met_values.get("run", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("run", distance=distance, intensity=intensity)
                save_user_data()
                st.success(f"Logged {distance}km! Pace: {pace} min/km Calories Burned: {entry['calories_burned']} +{xp_gain} XP")
    elif workout == "Walk (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        terrain = st.selectbox("Terrain", ["Flat", "Hilly", "Mixed"])
        if st.button("Log Walk"):
            if distance > 0:
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_outdoor", "distance": distance, "time": time_min, "terrain": terrain, "intensity": intensity}
                met = met_values.get("walk_outdoor", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_outdoor", distance=distance, intensity=intensity)
                save_user_data()
                st.success(f"Logged {distance}km walk! Calories Burned: {entry['calories_burned']} +{xp_gain} XP")
    elif workout == "Walk (Treadmill)":
        speed = st.number_input("Speed (km/h)", min_value=0.0, step=0.1)
        incline = st.number_input("Incline (%)", min_value=0.0, step=0.5)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Treadmill"):
            if time_min > 0:
                distance = round(speed * (time_min / 60), 2)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_treadmill", "distance": distance, "time": time_min, "speed": speed, "incline": incline, "intensity": intensity}
                met = met_values.get("walk_treadmill", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_treadmill", time_min=time_min, intensity=intensity)
                save_user_data()
                st.success(f"Logged {distance}km! Calories Burned: {entry['calories_burned']} +{xp_gain} XP")
    elif workout == "Cycle (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Cycle"):
            if distance > 0 and time_min > 0:
                speed = round(distance / (time_min / 60), 1)
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_outdoor", "distance": distance, "time": time_min, "avg_speed": speed, "intensity": intensity}
                met = met_values.get("cycle_outdoor", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_outdoor", distance=distance, intensity=intensity)
                save_user_data()
                st.success(f"Logged {distance}km! Speed: {speed} km/h Calories Burned: {entry['calories_burned']} +{xp_gain} XP")
    elif workout == "Cycle (Static Bike)":
        time_min = st.number_input("Time (min)", min_value=0)
        resistance = st.slider("Resistance", 1, 20, 10)
        rpm = st.number_input("Avg RPM", min_value=0, value=70)
        if st.button("Log Static Bike"):
            if time_min > 0:
                entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_static", "time": time_min, "resistance": resistance, "rpm": rpm, "intensity": intensity}
                met = met_values.get("cycle_static", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_static", time_min=time_min, intensity=intensity)
                save_user_data()
                st.success(f"Logged {time_min} min! Calories Burned: {entry['calories_burned']} +{xp_gain} XP")
    if st.session_state.progress_fitness:
        df = pd.DataFrame(st.session_state.progress_fitness)
        df["date"] = pd.to_datetime(df["date"])
        today = df[df["date"].dt.date == datetime.now().date()]
        total_burned_workouts = today["calories_burned"].sum() if "calories_burned" in today.columns else 0
        total_burned = st.session_state.bmr + total_burned_workouts
        st.metric("Workouts Burned Today", int(total_burned_workouts))
        st.metric("Total Burned Today", int(total_burned))
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
                response = chain_invoke(chain, history, user_prompt)
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
        today = df[df["date"].dt.date == datetime.now().date()]
        total_consumed = today["calories"].sum() if not today.empty else 0
        net_calories = total_consumed - (st.session_state.bmr + total_burned_workouts)
        st.metric("Consumed Today", int(total_consumed))
        st.metric("Net Calories Today", int(net_calories))
        df = df[df["date"] >= datetime.now() - pd.Timedelta(days=30)]
        st.subheader("Nutrition Progress")
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
            title="Daily Macros (g)"
)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Quick Start")
    cols = st.columns(4)
    for i, starter in enumerate(st.session_state.nutrition_starters):
        if cols[i].button(starter, key=f"nut_start_{i}"):
            st.session_state.quick_prompt = starter
    user_prompt = st.chat_input("Ask Nutrition Coach...")
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                response = chain_invoke(chain, history, user_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_user_data()

# === TABS ===
tab1, tab2 = st.tabs(["Fitness Coach", "Nutrition Coach"])

# (Rest of the code remains the same as previous, with the additions integrated)