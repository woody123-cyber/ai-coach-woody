import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import plotly.express as px
import pandas as pd
from datetime import datetime, date
import os
import json
from groq import GroqError
import random

# === CONFIG ===
st.set_page_config(page_title="Coach Woody", page_icon="trophy", layout="wide")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === GENDER TOGGLE ===
gender = st.sidebar.radio("Coach Gender", ["Male (Woody)", "Female (Hibiki)"], horizontal=True)
coach_name = "Woody" if gender == "Male (Woody)" else "Hibiki"

# === LLM ===
try:
    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.7)
except Exception as e:
    st.warning("Unable to connect to AI service. Chat features may be limited.")
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.now()}: {str(e)}\n")
    llm = None  # Fallback to no LLM

# === DATA PERSISTENCE ===
DATA_FILE = "user_data.json"

def load_user_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            expected_keys = {
                "messages": list, "level": int, "xp": int, "total_xp": int,
                "progress_fitness": list, "progress_nutrition": list, "name": str,
                "body_weight_kg": float, "weight_unit": str, "weight_goal": str,
                "calorie_goal": int, "macro_goal": dict, "fitness_starters": list,
                "nutrition_starters": list, "onboarded": bool, "quick_prompt": (str, type(None)),
                "xp_history": list, "daily_quests": dict, "last_quest_date": str,
                "user_gender": str, "user_age": int, "height_cm": float, "bmr": int
            }
            valid_data = {}
            for key, expected_type in expected_keys.items():
                if key in data and isinstance(data[key], expected_type):
                    valid_data[key] = data[key]
                else:
                    with open("error_log.txt", "a") as f:
                        f.write(f"{datetime.now()}: Invalid {key} in user_data.json\n")
            return valid_data
    except json.JSONDecodeError as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Failed to decode user_data.json: {str(e)}\n")
        return {}
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Error loading user_data.json: {str(e)}\n")
        return {}

def save_user_data():
    keys_to_save = [
        "messages", "level", "xp", "total_xp", "progress_fitness", "progress_nutrition",
        "name", "body_weight_kg", "weight_unit", "weight_goal", "calorie_goal",
        "macro_goal", "fitness_starters", "nutrition_starters", "onboarded",
        "quick_prompt", "xp_history", "daily_quests", "last_quest_date",
        "user_gender", "user_age", "height_cm", "bmr"
    ]
    data = {k: st.session_state.get(k) for k in keys_to_save if k in st.session_state}
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, default=lambda o: str(o) if not isinstance(o, (str, int, float, bool, list, dict, type(None))) else o)
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Error saving user_data.json: {str(e)}\n")

# Initialize session state
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
        "bmr": 0,
        "daily_quests": {},
        "last_quest_date": "",
        "all_quests_bonus": False
    }
    for key, value in defaults.items():
        try:
            st.session_state[key] = user_data.get(key, value)
        except AttributeError as e:
            with open("error_log.txt", "a") as f:
                f.write(f"{datetime.now()}: AttributeError for key {key}: {str(e)}\n")
            st.session_state[key] = value
    st.session_state["initialized"] = True
    save_user_data()

# === DAILY QUESTS ===
quest_pool = [
    {"task": "Do 20 push-ups", "xp": 10, "type": "push_ups", "reps": 20},
    {"task": "Complete 15 squats", "xp": 10, "type": "squats", "reps": 15},
    {"task": "Run 3 km", "xp": 15, "type": "run", "distance": 3},
    {"task": "Walk 5 km", "xp": 12, "type": "walk_outdoor", "distance": 5},
    {"task": "Hold a 1-minute plank", "xp": 10, "type": "plank", "time_min": 1},
    {"task": "Do 10 pull-ups", "xp": 15, "type": "pull_ups", "reps": 10},
    {"task": "Cycle 10 km", "xp": 15, "type": "cycle_outdoor", "distance": 10},
    {"task": "Perform 20 sit-ups", "xp": 10, "type": "sit_ups", "reps": 20},
    {"task": "Stretch for 10 minutes", "xp": 10, "type": "stretch", "time_min": 10},
    {"task": "Complete a 20-minute HIIT session", "xp": 20, "type": "hiit", "time_min": 20}
]

def reset_daily_quests():
    today = date.today().strftime("%Y-%m-%d")
    if st.session_state.get("last_quest_date") != today:
        selected_quests = random.sample(quest_pool, 5)
        st.session_state.daily_quests = {
            i: {"task": q["task"], "xp": q["xp"], "completed": False, "type": q["type"],
                "reps": q.get("reps", 0), "distance": q.get("distance", 0), "time_min": q.get("time_min", 0)}
            for i, q in enumerate(selected_quests)
        }
        st.session_state.last_quest_date = today
        st.session_state.all_quests_bonus = False
        save_user_data()

reset_daily_quests()

# === ONBOARDING ===
if not st.session_state.get("onboarded", False):
    with st.expander("Welcome to Coach Woody!", expanded=True):
        st.markdown(f"""
        **Hi, {st.session_state.name or 'Athlete'}!** 👋  
        Coach Woody helps you with fitness and nutrition in one place!  
        - 🏋️ Log workouts and track calories burned  
        - 🥗 Log meals and monitor macros  
        - 🏆 Complete daily quests for XP  
        Start by setting your details in the sidebar. Let's get moving!  
        """)
        if st.button("Got it!"):
            st.session_state["onboarded"] = True
            save_user_data()

# === TOP BAR ===
col1, col2 = st.columns([1, 3])
with col1:
    st.metric("Level", st.session_state.level)
    required_xp = 100 * st.session_state.level
    st.metric("XP", f"{st.session_state.xp}/{required_xp}")
    st.progress(min(st.session_state.xp / required_xp, 1.0))
    st.metric("Total XP", st.session_state.total_xp)
with col2:
    st.subheader("Daily Quests")
    st.info("Complete 5 fitness quests daily for XP! Resets at midnight.")
    quest_progress = sum(1 for q in st.session_state.daily_quests.values() if q["completed"])
    st.metric("Quests Completed", f"{quest_progress}/5")
    for i, quest in st.session_state.daily_quests.items():
        completed = st.checkbox(f"{quest['task']} (+{quest['xp']} XP)", value=quest["completed"], key=f"quest_{i}")
        if completed and not quest["completed"]:
            quest["completed"] = True
            st.session_state.xp += quest["xp"]
            st.session_state.total_xp += quest["xp"]
            st.session_state.xp_history.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": f"Quest: {quest['task']}",
                "xp": quest["xp"]
            })
            entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": quest["type"], "intensity": "Medium"}
            if quest["reps"] > 0:
                entry["reps"] = quest["reps"]
                entry["variation"] = "Standard"
            if quest["distance"] > 0:
                entry["distance"] = quest["distance"]
                entry["time"] = 0
            if quest["time_min"] > 0:
                entry["time"] = quest["time_min"]
            st.session_state.progress_fitness.append(entry)
            save_user_data()
            st.success(f"Quest '{quest['task']}' completed! +{quest['xp']} XP")
    if quest_progress == 5 and not st.session_state.get("all_quests_bonus", False):
        st.session_state.xp += 50
        st.session_state.total_xp += 50
        st.session_state.xp_history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "All Quests Bonus",
            "xp": 50
        })
        st.session_state.all_quests_bonus = True
        save_user_data()
        st.balloons()
        st.success("All quests completed! +50 XP Bonus!")

# === SIDE BAR ===
with st.sidebar:
    st.subheader("Personal Details")
    if not st.session_state.name:
        name = st.text_input("Your Name", placeholder="Jake")
        if name:
            st.session_state.name = name
            st.success(f"Welcome, {name}!")
            save_user_data()
    st.session_state.user_gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
    st.session_state.user_age = st.number_input("Age", min_value=18, max_value=100, value=st.session_state.user_age)
    st.session_state.height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=st.session_state.height_cm, step=0.1)
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
        if st.session_state.user_gender == "Male":
            bmr = 88.362 + (13.397 * st.session_state.body_weight_kg) + (4.799 * st.session_state.height_cm) - (5.677 * st.session_state.user_age)
        else:
            bmr = 447.593 + (9.247 * st.session_state.body_weight_kg) + (3.098 * st.session_state.height_cm) - (4.330 * st.session_state.user_age)
        st.session_state.bmr = int(bmr)
        maintenance = bmr * 1.55  # Moderate activity
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
    if workout_type in ["push_ups", "pull_ups", "sit_ups", "squats", "plank", "hiit", "stretch"]:
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
    st.session_state.xp_history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": f"{workout_type} ({intensity})",
        "xp": xp_gain
    })
    check_level_up()
    return xp_gain

def award_nutrition_xp(calories, protein, carbs, fats):
    xp_gain = 10
    balance_score = 100
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
        "source": f"Meal Log (Balance Score: {balance_score:.0f}%)",
        "xp": xp_gain
    })
    check_level_up()
    return xp_gain, balance_score

def check_level_up():
    required_xp = 100 * st.session_state.level
    while st.session_state.xp >= required_xp:
        st.session_state.xp -= required_xp
        st.session_state.level += 1
        required_xp = 100 * st.session_state.level  # Update for new level
        st.balloons()
        st.success(f"**LEVEL UP! → Level {st.session_state.level}**")
    save_user_data()

# === LLM INVOCATION ===
def chain_invoke(chain, history, user_input):
    if not llm:
        return "AI service unavailable. Please try again later."
    try:
        response = chain.invoke({"history": history, "input": user_input})
        return response
    except GroqError as e:
        if "rate_limit" in str(e).lower():
            msg = "Rate limit reached. Please wait and try again."
        elif "authentication" in str(e).lower():
            msg = "Invalid API key. Please contact support."
        else:
            msg = "AI service issue. Please try again."
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: {str(e)}\n")
        return msg
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: {str(e)}\n")
        return "Sorry, I couldn't generate a response. Please try again."

# === MAIN CONTENT ===
st.title(f"{coach_name} — Fitness & Nutrition Coach")

# === FITNESS SECTION ===
st.subheader("Log Fitness")
met_values = {
    "push_ups": {"Low": 3.8, "Medium": 5.0, "High": 7.0},
    "pull_ups": {"Low": 3.8, "Medium": 5.0, "High": 7.0},
    "sit_ups": {"Low": 3.8, "Medium": 5.0, "High": 7.0},
    "squats": {"Low": 3.8, "Medium": 5.0, "High": 7.0},
    "plank": {"Low": 3.0, "Medium": 4.0, "High": 5.0},
    "run": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
    "walk_outdoor": {"Low": 3.0, "Medium": 4.0, "High": 5.0},
    "walk_treadmill": {"Low": 3.0, "Medium": 4.0, "High": 5.0},
    "cycle_outdoor": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
    "cycle_static": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
    "stretch": {"Low": 2.0, "Medium": 2.5, "High": 3.0},
    "hiit": {"Low": 6.0, "Medium": 8.0, "High": 10.0}
}
workout = st.selectbox("Workout Type", [
    "Push-ups", "Pull-ups", "Sit-ups", "Squats", "Plank", "Run",
    "Walk (Outdoor)", "Walk (Treadmill)", "Cycle (Outdoor)", "Cycle (Static Bike)",
    "Stretch", "HIIT"
])
intensity = st.selectbox("Intensity", ["Low", "Medium", "High"])
if workout in ["Push-ups", "Pull-ups", "Sit-ups", "Squats"]:
    variations = {
        "Push-ups": ["Normal", "Close-Grip", "Wide-Grip"],
        "Pull-ups": ["Normal", "Chin-ups", "Neutral-Grip"],
        "Sit-ups": ["Standard", "Russian Twists", "Leg Raises"],
        "Squats": ["Bodyweight", "Goblet", "Sumo"]
    }
    variation = st.selectbox("Variation", variations[workout])
    reps = st.number_input("Reps", min_value=0, value=0)
    time_min = st.number_input("Time (min)", min_value=0.0, value=5.0, step=0.1)
    if st.button("Log Workout"):
        type_lower = workout.lower().replace(" ", "_")
        entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": type_lower, "variation": variation, "reps": reps, "intensity": intensity, "time": time_min}
        met = met_values.get(type_lower, {"Medium": 4.0}).get(intensity, 4.0)
        calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
        entry["calories_burned"] = int(calories_burned)
        st.session_state.progress_fitness.append(entry)
        xp_gain = award_fitness_xp(type_lower, reps=reps, intensity=intensity)
        save_user_data()
        st.success(f"Logged {reps} {variation} {workout.lower()} ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
elif workout == "Plank":
    time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
    if st.button("Log Plank"):
        if time_min > 0:
            entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "plank", "time": time_min, "intensity": intensity}
            met = met_values.get("plank", {"Medium": 4.0}).get(intensity, 4.0)
            calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
            entry["calories_burned"] = int(calories_burned)
            st.session_state.progress_fitness.append(entry)
            xp_gain = award_fitness_xp("plank", time_min=time_min, intensity=intensity)
            save_user_data()
            st.success(f"Logged {time_min} min plank ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
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
            st.success(f"Logged {distance}km run ({intensity})! Pace: {pace} min/km | Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
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
            st.success(f"Logged {distance}km walk ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
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
            st.success(f"Logged {distance}km treadmill ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
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
            st.success(f"Logged {distance}km cycle ({intensity})! Speed: {speed} km/h | Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
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
            st.success(f"Logged {time_min} min static bike ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
elif workout == "Stretch":
    time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
    if st.button("Log Stretch"):
        if time_min > 0:
            entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "stretch", "time": time_min, "intensity": intensity}
            met = met_values.get("stretch", {"Medium": 2.5}).get(intensity, 2.5)
            calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
            entry["calories_burned"] = int(calories_burned)
            st.session_state.progress_fitness.append(entry)
            xp_gain = award_fitness_xp("stretch", time_min=time_min, intensity=intensity)
            save_user_data()
            st.success(f"Logged {time_min} min stretch ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP")
elif workout == "HIIT":
    time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
    if st.button("Log HIIT"):
        if time_min > 0:
            entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "hiit", "time": time_min, "intensity": intensity}
            met = met_values.get("hiit", {"Medium": 8.0}).get(intensity, 8.0)
            calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
            entry["calories_burned"] = int(calories_burned)
            st.session_state.progress_fitness.append(entry)
            xp_gain = award_fitness_xp("hiit", time_min=time_min, intensity=intensity)
            save_user_data()
            st.success(f"Logged {time_min} min HIIT ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP")

# === NUTRITION SECTION ===
st.subheader("Log Nutrition")
meal = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
calories = st.number_input("Calories", min_value=0, value=0)
protein = st.number_input("Protein (g)", min_value=0, value=0)
carbs = st.number_input("Carbs (g)", min_value=0, value=0)
fats = st.number_input("Fats (g)", min_value=0, value=0)
if st.button("Log Meal"):
    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": meal.lower(), "calories": calories, "protein": protein, "carbs": carbs, "fats": fats}
    st.session_state.progress_nutrition.append(entry)
    xp_gain, balance_score = award_nutrition_xp(calories, protein, carbs, fats)
    save_user_data()
    st.success(f"Logged {meal}: {calories} cal (Balance: {balance_score:.0f}%)! +{xp_gain} XP")

# === CALORIE SUMMARY ===
if st.session_state.progress_fitness or st.session_state.progress_nutrition:
    fitness_df = pd.DataFrame(st.session_state.progress_fitness)
    nutrition_df = pd.DataFrame(st.session_state.progress_nutrition)
    if not fitness_df.empty:
        fitness_df["date"] = pd.to_datetime(fitness_df["date"])
    if not nutrition_df.empty:
        nutrition_df["date"] = pd.to_datetime(nutrition_df["date"])
    today_fitness = fitness_df[fitness_df["date"].dt.date == datetime.now().date()] if not fitness_df.empty else pd.DataFrame()
    today_nutrition = nutrition_df[nutrition_df["date"].dt.date == datetime.now().date()] if not nutrition_df.empty else pd.DataFrame()
    total_burned_workouts = today_fitness["calories_burned"].sum() if "calories_burned" in today_fitness.columns else 0
    total_burned = st.session_state.bmr + total_burned_workouts
    total_consumed = today_nutrition["calories"].sum() if not today_nutrition.empty else 0
    net_calories = total_consumed - total_burned
    st.subheader("Calorie Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Consumed Today", int(total_consumed))
    col2.metric("Burned Today", int(total_burned))
    col3.metric("Net Calories", int(net_calories))

# === PROGRESS SECTION ===
st.subheader("Progress")
if st.session_state.progress_fitness:
    fitness_df = pd.DataFrame(st.session_state.progress_fitness)
    fitness_df["date"] = pd.to_datetime(fitness_df["date"])
    fitness_df = fitness_df[fitness_df["date"] >= datetime.now() - pd.Timedelta(days=30)]
    col1, col2 = st.columns(2)
    with col1:
        strength = fitness_df[fitness_df["type"].str.contains("push|pull|sit|squat|plank|hiit|stretch")]
        if not strength.empty and "reps" in strength.columns:
            strength = strength.dropna(subset=["reps"])
            if not strength.empty:
                fig = px.line(strength, x="date", y="reps", color="variation", facet_col="type", markers=True, title="Strength Progress")
                fig.update_layout(font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)
    with col2:
        cardio = fitness_df[fitness_df["type"].str.contains("run|walk|cycle")]
        if not cardio.empty and "distance" in cardio.columns:
            cardio_dist = cardio.dropna(subset=["distance"])
            if not cardio_dist.empty:
                fig = px.bar(cardio_dist, x="date", y="distance", color="type", barmode="group", title="Cardio Progress")
                fig.update_layout(font=dict(size=14))
                st.plotly_chart(fig, use_container_width=True)

if st.session_state.progress_nutrition:
    nutrition_df = pd.DataFrame(st.session_state.progress_nutrition)
    nutrition_df["date"] = pd.to_datetime(nutrition_df["date"])
    nutrition_df = nutrition_df[nutrition_df["date"] >= datetime.now() - pd.Timedelta(days=30)]
    fig = px.bar(
        nutrition_df,
        x="date",
        y=["protein", "carbs", "fats"],
        title="Daily Macros (g)",
        color_discrete_map={"protein": "#1f77b4", "carbs": "#2ca02c", "fats": "#d62728"}
    )
    fig.update_layout(font=dict(size=14))
    st.plotly_chart(fig, use_container_width=True)
    daily_calories = nutrition_df.groupby(nutrition_df["date"].dt.date)["calories"].sum().reset_index()
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

if st.session_state.xp_history:
    xp_df = pd.DataFrame(st.session_state.xp_history)
    xp_df["date"] = pd.to_datetime(xp_df["date"])
    xp_df = xp_df[xp_df["date"] >= datetime.now() - pd.Timedelta(days=30)]
    fig = px.bar(xp_df, x="date", y="xp", color="source", title="XP Gains Over Time")
    fig.update_layout(font=dict(size=14))
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("XP History"):
        st.dataframe(xp_df[["date", "source", "xp"]], use_container_width=True)

# === FORM CHECK ===
st.subheader("Form Check")
st.info("Describe your form for feedback!")
form_prompt = st.text_area("Form Description", placeholder="E.g., My push-up form feels off...")
if st.button("Check Form"):
    if form_prompt:
        prompt = ChatPromptTemplate.from_template(f"""
        You are {coach_name}, {'motivational strength coach' if gender == 'Male (Woody)' else 'graceful, empowering trainer'}.
        Be fun, encouraging, under 120 words. Use emojis.
        User: {form_prompt}
        {coach_name}:
        """)
        chain = prompt | llm | StrOutputParser() if llm else None
        with st.spinner("Analyzing..."):
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
            response = chain_invoke(chain, history, form_prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "user", "content": form_prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_user_data()

# === QUICK START ===
st.subheader("Quick Start")
st.write("Ask about fitness or nutrition!")
col1, col2 = st.columns(2)
with col1:
    st.write("Fitness Questions")
    for i, starter in enumerate(st.session_state.fitness_starters):
        if st.button(starter, key=f"fit_start_{i}"):
            st.session_state.quick_prompt = starter
with col2:
    st.write("Nutrition Questions")
    for i, starter in enumerate(st.session_state.nutrition_starters):
        if st.button(starter, key=f"nut_start_{i}"):
            st.session_state.quick_prompt = starter

# === CHAT ===
st.subheader("Ask Coach Woody")
prompt = ChatPromptTemplate.from_template(f"""
You are {coach_name}, {'motivational strength coach' if gender == 'Male (Woody)' else 'graceful, empowering trainer'}.
Be fun, encouraging, under 120 words. Answer fitness or nutrition questions. Suggest meals/recipes for nutrition queries.
Body weight: {st.session_state.body_weight_kg:.1f}kg
Calorie goal: {st.session_state.calorie_goal}, Macros: P{st.session_state.macro_goal['protein']}g C{st.session_state.macro_goal['carbs']}g F{st.session_state.macro_goal['fats']}g
History: {{history}}
User: {{input}}
{coach_name}:
""")
chain = prompt | llm | StrOutputParser() if llm else None
user_prompt = st.chat_input("Ask about fitness or nutrition...")
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