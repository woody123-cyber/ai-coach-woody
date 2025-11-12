import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pandas as pd
from datetime import datetime, date
import os
import json
from groq import GroqError
import random

# === CONFIG ===
st.set_page_config(page_title="Coach Woody RPG", page_icon="🏆", layout="wide")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

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
                "user_gender": str, "user_age": int, "height_cm": float, "bmr": int,
                "all_quests_bonus": bool, "skill_levels": dict, "achievements": list
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
        "user_gender", "user_age", "height_cm", "bmr", "all_quests_bonus",
        "skill_levels", "achievements"
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
        "all_quests_bonus": False,
        "skill_levels": {
            "push_ups": {"level": 1, "xp": 0},
            "pull_ups": {"level": 1, "xp": 0},
            "sit_ups": {"level": 1, "xp": 0},
            "squats": {"level": 1, "xp": 0},
            "plank": {"level": 1, "xp": 0},
            "run": {"level": 1, "xp": 0},
            "walk_outdoor": {"level": 1, "xp": 0},
            "walk_treadmill": {"level": 1, "xp": 0},
            "cycle_outdoor": {"level": 1, "xp": 0},
            "cycle_static": {"level": 1, "xp": 0},
            "stretch": {"level": 1, "xp": 0},
            "hiit": {"level": 1, "xp": 0},
            "meal_log": {"level": 1, "xp": 0}
        },
        "achievements": []  # New: List of unlocked achievements
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

# Only call reset_daily_quests once per session
if "quests_reset" not in st.session_state:
    reset_daily_quests()
    st.session_state.quests_reset = True

# === CONSTANTS ===
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

# === XP SYSTEM ===
def award_fitness_xp(workout_type, reps=0, distance=0, time_min=0, intensity="Medium"):
    xp_gain = 10
    intensity_multipliers = {"Low": 1.0, "Medium": 1.5, "High": 2.0}
    xp_gain *= intensity_multipliers[intensity]
    if workout_type in ["push_ups", "pull_ups", "sit_ups", "squats", "plank", "hiit", "stretch"]:
        xp_gain += reps // 5 if reps > 0 else time_min // 5
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
        if unique_days >= 3 and "weekly_warrior" not in st.session_state.achievements:
            st.session_state.xp += 100
            st.session_state.total_xp += 100
            st.session_state.achievements.append("weekly_warrior")
            st.balloons()
            st.success("Achievement Unlocked: Weekly Warrior! +100 XP 🥇")
            save_user_data()
            # Play sound
            st.markdown("""
                <audio autoplay>
                    <source src="https://www.orangefreesounds.com/wp-content/uploads/2016/09/Level-up-sound-effect.mp3" type="audio/mpeg">
                </audio>
            """, unsafe_allow_html=True)
    st.session_state.xp += xp_gain
    st.session_state.total_xp += xp_gain
    st.session_state.xp_history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": f"{workout_type} ({intensity})",
        "xp": xp_gain
    })
    save_user_data()
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
        if balance_score >= 80 and "macro_master" not in st.session_state.achievements:
            st.session_state.xp += 50
            st.session_state.total_xp += 50
            st.session_state.achievements.append("macro_master")
            st.balloons()
            st.success("Achievement Unlocked: Macro Master! +50 XP 🥦")
            save_user_data()
            # Play sound
            st.markdown("""
                <audio autoplay>
                    <source src="https://www.orangefreesounds.com/wp-content/uploads/2016/09/Level-up-sound-effect.mp3" type="audio/mpeg">
                </audio>
            """, unsafe_allow_html=True)
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
    save_user_data()
    check_level_up()
    return xp_gain, balance_score

def check_level_up():
    required_xp = 100 + 50 * (st.session_state.level - 1)
    if st.session_state.xp >= required_xp:
        st.session_state.xp -= required_xp
        st.session_state.level += 1
        st.balloons()
        st.success(f"**LEVEL UP! → Level {st.session_state.level}**")
        # Play sound
        st.markdown("""
            <audio autoplay>
                <source src="https://www.orangefreesounds.com/wp-content/uploads/2016/09/Level-up-sound-effect.mp3" type="audio/mpeg">
            </audio>
        """, unsafe_allow_html=True)
        save_user_data()

def award_skill_xp(skill_type, amount):
    if skill_type not in st.session_state.skill_levels:
        st.session_state.skill_levels[skill_type] = {"level": 1, "xp": 0}
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Initialized missing skill {skill_type}\n")
    try:
        xp_gain = int(amount)
        if xp_gain < 0:
            raise ValueError("XP amount cannot be negative")
        current_xp = st.session_state.skill_levels[skill_type]["xp"]
        current_level = st.session_state.skill_levels[skill_type]["level"]
        new_xp = current_xp + xp_gain
        required_skill_xp = 100 + 50 * (current_level - 1)
        while new_xp >= required_skill_xp and current_level < 60:
            new_xp -= required_skill_xp
            current_level += 1
            st.balloons()
            st.success(f"**{skill_type.replace('_', ' ').title()} SKILL LEVEL UP! → Level {current_level}**")
            required_skill_xp = 100 + 50 * (current_level - 1)
            # Play sound
            st.markdown("""
                <audio autoplay>
                    <source src="https://www.orangefreesounds.com/wp-content/uploads/2016/09/Level-up-sound-effect.mp3" type="audio/mpeg">
                </audio>
            """, unsafe_allow_html=True)
        st.session_state.skill_levels[skill_type]["xp"] = new_xp
        st.session_state.skill_levels[skill_type]["level"] = current_level
        save_user_data()
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Awarded {xp_gain} XP to {skill_type}. Level: {current_level}, XP: {new_xp}/{required_skill_xp}\n")
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Error in award_skill_xp for {skill_type}: {str(e)}\n")

# === ACHIEVEMENTS SYSTEM ===
achievements = {
    "weekly_warrior": {"name": "Weekly Warrior", "xp": 100, "desc": "3+ workouts in a week"},
    "macro_master": {"name": "Macro Master", "xp": 50, "desc": "80%+ balance score"},
    "quest_master": {"name": "Quest Master", "xp": 200, "desc": "Complete all quests 5 days in a row"},
    "skill_pioneer": {"name": "Skill Pioneer", "xp": 150, "desc": "Reach Level 10 in any skill"}
}

def check_achievements():
    if "weekly_warrior" not in st.session_state.achievements:
        df = pd.DataFrame(st.session_state.progress_fitness)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            week_start = datetime.now() - pd.Timedelta(days=7)
            week_logs = df[df["date"] >= week_start]
            if len(week_logs["date"].dt.date.unique()) >= 3:
                st.session_state.achievements.append("weekly_warrior")
                st.session_state.xp += achievements["weekly_warrior"]["xp"]
                st.session_state.total_xp += achievements["weekly_warrior"]["xp"]
                st.success(f"Achievement Unlocked: {achievements['weekly_warrior']['name']}! +{achievements['weekly_warrior']['xp']} XP - {achievements['weekly_warrior']['desc']}")
                # Play sound
                st.markdown("""
                    <audio autoplay>
                        <source src="https://www.orangefreesounds.com/wp-content/uploads/2016/09/Level-up-sound-effect.mp3" type="audio/mpeg">
                    </audio>
                """, unsafe_allow_html=True)
                save_user_data()
                check_level_up()
    # Add more checks for other achievements (e.g., macro_master in award_nutrition_xp, skill_pioneer in award_skill_xp, etc.)

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

# === TOP BAR (HUD) ===
st.markdown("<h3 style='text-align: center; color: #f0f0f0;'>🏆 Status HUD</h3>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])
with col1:
    st.metric("Level", st.session_state.level, delta=None, delta_color="normal", help="Your overall player level")
    required_xp = 100 + 50 * (st.session_state.level - 1)
    st.metric("XP", f"{st.session_state.xp}/{required_xp}")
    st.progress(min(st.session_state.xp / required_xp, 1.0))
    st.metric("Total XP", st.session_state.total_xp)
with col2:
    st.markdown("**Mission Log**: Track your progress and conquer challenges!", unsafe_allow_html=True)

# === MAIN CONTENT ===
st.markdown("<h1 style='text-align: center; color: #f0f0f0;'>Coach Woody's Fitness RPG</h1>", unsafe_allow_html=True)

# Gaming CSS with grey-based, readable colors
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    body { 
        font-family: 'Press Start 2P', cursive; 
        background-color: #2a2a2a; 
        color: #f0f0f0; 
    }
    .stExpander { 
        border: 2px solid #ffffff; 
        background-color: #3c3c3c; 
        margin-bottom: 15px; 
        border-radius: 8px; 
    }
    .stButton > button { 
        background-color: #4a4a4a; 
        color: #f0f0f0; 
        border: 2px solid #ffffff; 
        padding: 8px 16px; 
        font-family: 'Press Start 2P', cursive; 
        border-radius: 5px; 
    }
    .stButton > button:hover { 
        background-color: #5a5a5a; 
        color: #f0f0f0; 
    }
    .alert-badge { 
        background-color: #b22222; 
        color: #f0f0f0; 
        padding: 4px 8px; 
        border-radius: 12px; 
        font-size: 10px; 
        margin-left: 10px; 
        vertical-align: middle; 
    }
    .stProgress > div > div > div > div { 
        background-color: #4682b4; 
    }
    .stMetric { 
        background-color: #505050; 
        border-radius: 5px; 
        padding: 10px; 
    }
    .stTextInput > div > div > input, .stSelectbox > div > div > select, .stNumberInput > div > div > input {
        background-color: #404040; 
        color: #f0f0f0; 
        border: 1px solid #ffffff; 
        font-family: 'Press Start 2P', cursive; 
    }
    .stSidebar { 
        background-color: #3c3c3c; 
    }
    </style>
""", unsafe_allow_html=True)

# === DAILY QUESTS EXPANDER ===
quest_progress = sum(1 for q in st.session_state.daily_quests.values() if q["completed"])
uncompleted_quests = 5 - quest_progress
quest_label = f"🏆 Daily Quests <span class='alert-badge'>{uncompleted_quests}</span>" if uncompleted_quests > 0 else "🏆 Daily Quests (All Completed!)"
st.markdown(f"<h2 style='color: #f0f0f0;'>{quest_label}</h2>", unsafe_allow_html=True)
with st.expander("", expanded=uncompleted_quests > 0):
    st.info("Complete 5 daily quests to earn XP and unlock a bonus! Resets at midnight. 🌟")
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
            entry = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": quest["type"],
                "intensity": "Medium",
                "calories_burned": 0
            }
            if quest["reps"] > 0:
                entry["reps"] = quest["reps"]
                entry["variation"] = "Standard"
                award_skill_xp(quest["type"], quest["reps"])
            if quest["distance"] > 0:
                entry["distance"] = quest["distance"]
                entry["time"] = 0
                award_skill_xp(quest["type"], quest["distance"])
            if quest["time_min"] > 0:
                entry["time"] = quest["time_min"]
                met = met_values.get(quest["type"], {"Medium": 4.0}).get("Medium", 4.0)
                entry["calories_burned"] = int(met * st.session_state.body_weight_kg * (quest["time_min"] / 60))
                award_skill_xp(quest["type"], quest["time_min"])
            st.session_state.progress_fitness.append(entry)
            save_user_data()
            st.balloons()
            st.success(f"Quest '{quest['task']}' completed! +{quest['xp']} XP | +{quest.get('reps', 0) or quest.get('distance', 0) or quest.get('time_min', 0)} {quest['type'].replace('_', ' ').title()} Skill XP")
            check_level_up()
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
        st.success("All quests completed! +50 XP Bonus! 🎉")
        check_level_up()

# === TRACK FITNESS & NUTRITION EXPANDER ===
with st.expander("🏋️ Track Fitness & Nutrition"):
    # Log Fitness
    st.subheader("Log Fitness")
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
            entry = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": type_lower,
                "variation": variation,
                "reps": reps,
                "intensity": intensity,
                "time": time_min
            }
            met = met_values.get(type_lower, {"Medium": 4.0}).get(intensity, 4.0)
            calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
            entry["calories_burned"] = int(calories_burned)
            st.session_state.progress_fitness.append(entry)
            xp_gain = award_fitness_xp(type_lower, reps=reps, intensity=intensity)
            if reps > 0:
                award_skill_xp(type_lower, reps)
                st.success(f"Logged {reps} {variation} {workout.lower()} ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{reps} {workout} Skill XP")
            else:
                st.warning("Please enter at least 1 rep to earn skill XP.")
            save_user_data()
            check_achievements()
    elif workout == "Plank":
        time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
        if st.button("Log Plank"):
            if time_min > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "plank",
                    "time": time_min,
                    "intensity": intensity
                }
                met = met_values.get("plank", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("plank", time_min=time_min, intensity=intensity)
                award_skill_xp("plank", int(time_min))
                save_user_data()
                st.success(f"Logged {time_min} min plank ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Plank Skill XP")
                check_achievements()
    elif workout == "Run":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Run"):
            if distance > 0 and time_min > 0:
                pace = round(time_min / distance, 2)
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "run",
                    "distance": distance,
                    "time": time_min,
                    "pace": pace,
                    "intensity": intensity
                }
                met = met_values.get("run", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("run", distance=distance, intensity=intensity)
                award_skill_xp("run", int(distance))
                save_user_data()
                st.success(f"Logged {distance}km run ({intensity})! Pace: {pace} min/km | Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(distance)} Run Skill XP")
                check_achievements()
    elif workout == "Walk (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        terrain = st.selectbox("Terrain", ["Flat", "Hilly", "Mixed"])
        if st.button("Log Walk"):
            if distance > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "walk_outdoor",
                    "distance": distance,
                    "time": time_min,
                    "terrain": terrain,
                    "intensity": intensity
                }
                met = met_values.get("walk_outdoor", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_outdoor", distance=distance, intensity=intensity)
                award_skill_xp("walk_outdoor", int(distance))
                save_user_data()
                st.success(f"Logged {distance}km walk ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(distance)} Walk Outdoor Skill XP")
                check_achievements()
    elif workout == "Walk (Treadmill)":
        speed = st.number_input("Speed (km/h)", min_value=0.0, step=0.1)
        incline = st.number_input("Incline (%)", min_value=0.0, step=0.5)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Treadmill"):
            if time_min > 0:
                distance = round(speed * (time_min / 60), 2)
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "walk_treadmill",
                    "distance": distance,
                    "time": time_min,
                    "speed": speed,
                    "incline": incline,
                    "intensity": intensity
                }
                met = met_values.get("walk_treadmill", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_treadmill", time_min=time_min, intensity=intensity)
                award_skill_xp("walk_treadmill", int(time_min))
                save_user_data()
                st.success(f"Logged {distance}km treadmill ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Walk Treadmill Skill XP")
                check_achievements()
    elif workout == "Cycle (Outdoor)":
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time_min = st.number_input("Time (min)", min_value=0)
        if st.button("Log Cycle"):
            if distance > 0 and time_min > 0:
                speed = round(distance / (time_min / 60), 1)
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "cycle_outdoor",
                    "distance": distance,
                    "time": time_min,
                    "avg_speed": speed,
                    "intensity": intensity
                }
                met = met_values.get("cycle_outdoor", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_outdoor", distance=distance, intensity=intensity)
                award_skill_xp("cycle_outdoor", int(distance))
                save_user_data()
                st.success(f"Logged {distance}km cycle ({intensity})! Speed: {speed} km/h | Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(distance)} Cycle Outdoor Skill XP")
                check_achievements()
    elif workout == "Cycle (Static Bike)":
        time_min = st.number_input("Time (min)", min_value=0)
        resistance = st.slider("Resistance", 1, 20, 10)
        rpm = st.number_input("Avg RPM", min_value=0, value=70)
        if st.button("Log Static Bike"):
            if time_min > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "cycle_static",
                    "time": time_min,
                    "resistance": resistance,
                    "rpm": rpm,
                    "intensity": intensity
                }
                met = met_values.get("cycle_static", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_static", time_min=time_min, intensity=intensity)
                award_skill_xp("cycle_static", int(time_min))
                save_user_data()
                st.success(f"Logged {time_min} min static bike ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Cycle Static Skill XP")
                check_achievements()
    elif workout == "Stretch":
        time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
        if st.button("Log Stretch"):
            if time_min > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "stretch",
                    "time": time_min,
                    "intensity": intensity
                }
                met = met_values.get("stretch", {"Medium": 2.5}).get(intensity, 2.5)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("stretch", time_min=time_min, intensity=intensity)
                award_skill_xp("stretch", int(time_min))
                save_user_data()
                st.success(f"Logged {time_min} min stretch ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Stretch Skill XP")
                check_achievements()
    elif workout == "HIIT":
        time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
        if st.button("Log HIIT"):
            if time_min > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "hiit",
                    "time": time_min,
                    "intensity": intensity
                }
                met = met_values.get("hiit", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("hiit", time_min=time_min, intensity=intensity)
                award_skill_xp("hiit", int(time_min))
                save_user_data()
                st.success(f"Logged {time_min} min HIIT ({intensity})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} HIIT Skill XP")
                check_achievements()

    # Log Nutrition
    st.subheader("Log Nutrition")
    meal = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
    calories = st.number_input("Calories", min_value=0, value=0)
    protein = st.number_input("Protein (g)", min_value=0, value=0)
    carbs = st.number_input("Carbs (g)", min_value=0, value=0)
    fats = st.number_input("Fats (g)", min_value=0, value=0)
    if st.button("Log Meal"):
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": meal.lower(),
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fats": fats
        }
        st.session_state.progress_nutrition.append(entry)
        xp_gain, balance_score = award_nutrition_xp(calories, protein, carbs, fats)
        award_skill_xp("meal_log", 1)
        save_user_data()
        st.success(f"Logged {meal}: {calories} cal (Balance: {balance_score:.0f}%)! +{xp_gain} XP | +1 Meal Log Skill XP")

    # Calorie Summary
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

# === PROGRESS EXPANDER ===
with st.expander("📊 Skill Tree"):
    st.subheader("Skills")
    for key, value in st.session_state.skill_levels.items():
        skill_name = key.replace("_", " ").title()
        level = value["level"]
        xp = value["xp"]
        required_xp = 100 + 50 * (level - 1)
        st.markdown(f"**{skill_name}: Level {level}** ({xp}/{required_xp} XP)")
        st.progress(min(xp / required_xp, 1.0))

# === COACH WOODY EXPANDER ===
with st.expander("🤝 Coach Woody"):
    # Quick Start
    st.subheader("Quick Start")
    st.write("Ask about fitness or nutrition! 🌟")
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

    # Ask Coach Woody
    st.subheader("Ask Coach Woody")
    prompt = ChatPromptTemplate.from_template(f"""
    You are {coach_name}, {'motivational strength coach' if gender == 'Male (Woody)' else 'graceful, empowering trainer'}.
    Be fun, encouraging, under 120 words. Use emojis. Answer fitness or nutrition questions. Suggest meals/recipes for nutrition queries.
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

    # Form Check
    st.subheader("Form Check")
    st.info("Describe your form for feedback! 🧠")
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