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
st.set_page_config(page_title="Coach Woody RPG", page_icon="Trophy", layout="wide")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === LLM ===
try:
    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.7)
except Exception as e:
    st.warning("Unable to connect to AI service. Chat features may be limited.")
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.now()}: {str(e)}\n")
    llm = None

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
                "all_quests_bonus": bool, "skill_levels": dict, "achievements": list,
                "quest_streak": int, "guild": str, "gear": list
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
        "skill_levels", "achievements", "quest_streak", "guild", "gear"
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
            "meal_log": {"level": 1, "xp": 0},
            "bench_press": {"level": 1, "xp": 0},
            "deadlift": {"level": 1, "xp": 0},
            "shoulder_press": {"level": 1, "xp": 0},
            "bicep_curls": {"level": 1, "xp": 0},
            "tricep_dips": {"level": 1, "xp": 0},
            "leg_press": {"level": 1, "xp": 0},
            "yoga": {"level": 1, "xp": 0},
            "pilates": {"level": 1, "xp": 0},
            "swimming": {"level": 1, "xp": 0},
            "rowing": {"level": 1, "xp": 0},
            "jump_rope": {"level": 1, "xp": 0},
            "burpees": {"level": 1, "xp": 0},
            "mountain_climbers": {"level": 1, "xp": 0},
            "kettlebell_swings": {"level": 1, "xp": 0},
            "battle_ropes": {"level": 1, "xp": 0}
        },
        "achievements": [],
        "quest_streak": 0,
        "guild": "",
        "gear": []
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

# === AVATAR & GEAR SYSTEM ===
def get_avatar_title(level):
    try:
        titles = {
            1: "Novice Warrior",
            3: "Apprentice Fighter",
            5: "Skilled Soldier",
            10: "Master Athlete",
            15: "Legendary Hero"
        }
        for lvl, title in sorted(titles.items(), reverse=True):
            if level >= lvl:
                return title
        return "Novice Warrior"
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Error in get_avatar_title: {str(e)}\n")
        return "Novice Warrior"

def get_avatar_image(level):
    # Simple text-based avatar that "grows muscles" with level
    if level < 3:
        return "Skinny Avatar"
    elif level < 5:
        return "Fit Avatar"
    elif level < 10:
        return "Muscular Avatar"
    elif level < 15:
        return "Buff Avatar"
    else:
        return "Ultra Muscular Hero"

def get_ability(level):
    abilities = {
        5: "Advanced Form: Elbows at 45 degrees for max push-up power!",
        10: "Recovery Hack: Foam roll 10 min post-workout!",
        15: "Nutrition Secret: Pair carbs/protein post-workout!"
    }
    for lvl, ability in sorted(abilities.items(), reverse=True):
        if level >= lvl:
            return ability
    return None

def get_gear(level):
    gear = {
        5: "Iron Boots",
        10: "Steel Gauntlets",
        15: "Mythril Chestplate"
    }
    unlocked = []
    for lvl, item in sorted(gear.items()):
        if level >= lvl and item not in st.session_state.gear:
            st.session_state.gear.append(item)
            st.success(f"Gear Unlocked: {item}! Celebration")
            save_user_data()
        if level >= lvl:
            unlocked.append(item)
    return unlocked

# === DAILY QUESTS ===
quest_pool = [
    {"task": f"Defeat Sloth Beast #{random.randint(100, 999)}: 20 push-ups", "xp": 10, "type": "push_ups", "reps": 20, "desc": "Crush laziness with raw strength!"},
    {"task": f"Conquer Gravity #{random.randint(100, 999)}: 15 squats", "xp": 10, "type": "squats", "reps": 15, "desc": "Stand tall against the pull!"},
    {"task": f"Sprint Wasteland #{random.randint(100, 999)}: 3 km run", "xp": 15, "type": "run", "distance": 3, "desc": "Outrun the desert storms!"},
    {"task": f"Patrol Ruins #{random.randint(100, 999)}: 5 km walk", "xp": 12, "type": "walk_outdoor", "distance": 5, "desc": "Scout the forgotten paths!"},
    {"task": f"Hold Line #{random.randint(100, 999)}: 1-min plank", "xp": 10, "type": "plank", "time_min": 1, "desc": "Fortify your core defenses!"},
    {"task": f"Climb Spire #{random.randint(100, 999)}: 10 pull-ups", "xp": 15, "type": "pull_ups", "reps": 10, "desc": "Ascend to new heights!"},
    {"task": f"Ride Storm #{random.randint(100, 999)}: 10 km cycle", "xp": 15, "type": "cycle_outdoor", "distance": 10, "desc": "Speed through chaos!"},
    {"task": f"Strike Core #{random.randint(100, 999)}: 20 sit-ups", "xp": 10, "type": "sit_ups", "reps": 20, "desc": "Forge an iron midsection!"},
    {"task": f"Mend Body #{random.randint(100, 999)}: 10 min stretch", "xp": 10, "type": "stretch", "time_min": 10, "desc": "Restore your vitality!"},
    {"task": f"Unleash Fury #{random.randint(100, 999)}: 20 min HIIT", "xp": 20, "type": "hiit", "time_min": 20, "desc": "Obliterate all weakness!"}
]

def reset_daily_quests():
    today = date.today().strftime("%Y-%m-%d")
    if st.session_state.get("all_quests_bonus") and st.session_state.get("last_quest_date") == (date.today() - pd.Timedelta(days=1)).strftime("%Y-%m-%d"):
        st.session_state.quest_streak = st.session_state.get("quest_streak", 0) + 1
    else:
        st.session_state.quest_streak = 0
    selected_quests = random.sample(quest_pool, 5)
    st.session_state.daily_quests = {
        i: {"task": q["task"], "xp": q["xp"], "completed": False, "type": q["type"],
            "reps": q.get("reps", 0), "distance": q.get("distance", 0), "time_min": q.get("time_min", 0),
            "desc": q["desc"]}
        for i, q in enumerate(selected_quests)
    }
    st.session_state.last_quest_date = today
    st.session_state.all_quests_bonus = False
    save_user_data()

# Always check and reset quests if needed
today = date.today().strftime("%Y-%m-%d")
if st.session_state.get("last_quest_date") != today:
    reset_daily_quests()

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
    "hiit": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
    "bench_press": {"Low": 5.0, "Medium": 7.0, "High": 9.0},
    "deadlift": {"Low": 5.0, "Medium": 7.0, "High": 9.0},
    "shoulder_press": {"Low": 5.0, "Medium": 7.0, "High": 9.0},
    "bicep_curls": {"Low": 4.0, "Medium": 6.0, "High": 8.0},
    "tricep_dips": {"Low": 4.0, "Medium": 6.0, "High": 8.0},
    "leg_press": {"Low": 5.0, "Medium": 7.0, "High": 9.0},
    "yoga": {"Low": 2.5, "Medium": 3.5, "High": 4.5},
    "pilates": {"Low": 3.0, "Medium": 4.0, "High": 5.0},
    "swimming": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
    "rowing": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
    "jump_rope": {"Low": 8.0, "Medium": 10.0, "High": 12.0},
    "burpees": {"Low": 7.0, "Medium": 9.0, "High": 11.0},
    "mountain_climbers": {"Low": 7.0, "Medium": 9.0, "High": 11.0},
    "kettlebell_swings": {"Low": 6.0, "Medium": 8.0, "High": 10.0},
    "battle_ropes": {"Low": 8.0, "Medium": 10.0, "High": 12.0}
}

skill_icons = {
    "push_ups": "Flexed Biceps", "pull_ups": "Lifting Weights", "sit_ups": "Person in Lotus Position", "squats": "Leg",
    "plank": "Hammer and Wrench", "run": "Running", "walk_outdoor": "Walking", "walk_treadmill": "Running Shoe",
    "cycle_outdoor": "Bicyclist", "cycle_static": "Stationary Bike", "stretch": "Gymnastics", "hiit": "Fire",
    "meal_log": "Plate with Cutlery", "bench_press": "Bench Press", "deadlift": "Deadlift",
    "shoulder_press": "Shoulder Press", "bicep_curls": "Bicep Curls", "tricep_dips": "Tricep Dips",
    "leg_press": "Leg Press", "yoga": "Yoga", "pilates": "Pilates", "swimming": "Swimming",
    "rowing": "Rowing", "jump_rope": "Jump Rope", "burpees": "Burpees", "mountain_climbers": "Mountain Climbers",
    "kettlebell_swings": "Kettlebell Swings", "battle_ropes": "Battle Ropes"
}

skill_desc = {
    "push_ups": "Master upper body strength! +10% XP at Level 10.",
    "pull_ups": "Conquer the bar with power! +10% XP at Level 10.",
    "sit_ups": "Forge an iron core! +10% XP at Level 10.",
    "squats": "Build legs of steel! +10% XP at Level 10.",
    "plank": "Fortify your core defenses! +10% XP at Level 10.",
    "run": "Outrun any challenge! +10% XP at Level 10.",
    "walk_outdoor": "Explore the world on foot! +10% XP at Level 10.",
    "walk_treadmill": "March to victory indoors! +10% XP at Level 10.",
    "cycle_outdoor": "Ride through any storm! +10% XP at Level 10.",
    "cycle_static": "Pedal to greatness! +10% XP at Level 10.",
    "stretch": "Stay limber and ready! +10% XP at Level 10.",
    "hiit": "Unleash explosive energy! +10% XP at Level 10.",
    "meal_log": "Fuel your body wisely! +10% XP at Level 10.",
    "bench_press": "Build chest strength! +10% XP at Level 10.",
    "deadlift": "Master back and leg power! +10% XP at Level 10.",
    "shoulder_press": "Strengthen shoulders! +10% XP at Level 10.",
    "bicep_curls": "Grow arm muscles! +10% XP at Level 10.",
    "tricep_dips": "Tone triceps! +10% XP at Level 10.",
    "leg_press": "Power up legs! +10% XP at Level 10.",
    "yoga": "Improve flexibility and balance! +10% XP at Level 10.",
    "pilates": "Core and posture enhancement! +10% XP at Level 10.",
    "swimming": "Full body cardio! +10% XP at Level 10.",
    "rowing": "Back and cardio workout! +10% XP at Level 10.",
    "jump_rope": "High-intensity cardio! +10% XP at Level 10.",
    "burpees": "Full body explosive exercise! +10% XP at Level 10.",
    "mountain_climbers": "Core and cardio burner! +10% XP at Level 10.",
    "kettlebell_swings": "Hip and core power! +10% XP at Level 10.",
    "battle_ropes": "Upper body endurance! +10% XP at Level 10."
}

# === ACHIEVEMENTS ===
achievements = {
    "weekly_warrior": {"name": "Weekly Warrior", "xp": 100, "desc": "Log 3+ workouts in a week"},
    "macro_master": {"name": "Macro Master", "xp": 50, "desc": "Achieve 80%+ balance score"},
    "quest_master": {"name": "Quest Master", "xp": 200, "desc": "Complete all quests 5 days in a row"},
    "skill_pioneer": {"name": "Skill Pioneer", "xp": 150, "desc": "Reach Level 10 in any skill"},
    "epic_questor": {"name": "Epic Questor", "xp": 300, "desc": "Maintain a 10-day quest streak"}
}

# === XP SYSTEM ===
def award_fitness_xp(workout_type, reps=0, distance=0, time_min=0, intensity="Medium", difficulty="Beginner"):
    xp_gain = 10
    intensity_multipliers = {"Low": 1.0, "Medium": 1.5, "High": 2.0}
    difficulty_multipliers = {"Beginner": 1.0, "Intermediate": 1.2, "Advanced": 1.5}
    xp_gain *= intensity_multipliers[intensity] * difficulty_multipliers[difficulty]
    if workout_type in ["push_ups", "pull_ups", "sit_ups", "squats", "plank", "hiit", "stretch", "bench_press", "deadlift", "shoulder_press", "bicep_curls", "tricep_dips", "leg_press", "burpees", "mountain_climbers", "kettlebell_swings", "battle_ropes"]:
        xp_gain += reps // 5 if reps > 0 else time_min // 5
    elif workout_type in ["run", "walk_outdoor", "cycle_outdoor", "swimming", "rowing", "jump_rope"]:
        xp_gain += int(distance * 3)
    elif workout_type in ["walk_treadmill", "cycle_static"]:
        xp_gain += time_min // 5
    if st.session_state.get("guild"):
        xp_gain = int(xp_gain * 1.05)
    st.session_state.xp += xp_gain
    st.session_state.total_xp += xp_gain
    st.session_state.xp_history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": f"{workout_type} ({intensity}, {difficulty})",
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
    if st.session_state.get("guild"):
        xp_gain = int(xp_gain * 1.05)
    st.session_state.xp += xp_gain
    st.session_state.total_xp += xp_gain
    st.session_state.xp_history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": f"Meal Log (Balance: {balance_score:.0f}%)",
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
        st.success(f"LEVEL UP! -> Level {st.session_state.level}: {get_avatar_title(st.session_state.level)}")
        ability = get_ability(st.session_state.level)
        if ability:
            st.info(f"New Ability Unlocked: {ability}")
        get_gear(st.session_state.level)
        save_user_data()

def award_skill_xp(skill_type, amount):
    if skill_type not in st.session_state.skill_levels:
        st.session_state.skill_levels[skill_type] = {"level": 1, "xp": 0}
    try:
        xp_gain = int(amount)
        if xp_gain < 0:
            raise ValueError("XP amount cannot be negative")
        current_xp = st.session_state.skill_levels[skill_type]["xp"]
        current_level = st.session_state.skill_levels[skill_type]["level"]
        if current_level >= 10:
            xp_gain = int(xp_gain * 1.1)
        new_xp = current_xp + xp_gain
        required_skill_xp = 100 + 50 * (current_level - 1)
        while new_xp >= required_skill_xp and current_level < 60:
            new_xp -= required_skill_xp
            current_level += 1
            st.balloons()
            st.success(f"{skill_type.replace('_', ' ').title()} SKILL LEVEL UP! -> Level {current_level}")
            if current_level >= 10 and "skill_pioneer" not in st.session_state.achievements:
                st.session_state.achievements.append("skill_pioneer")
                st.session_state.xp += achievements["skill_pioneer"]["xp"]
                st.session_state.total_xp += achievements["skill_pioneer"]["xp"]
                st.success(f"Achievement Unlocked: {achievements['skill_pioneer']['name']}! +{achievements['skill_pioneer']['xp']} XP")
            required_skill_xp = 100 + 50 * (current_level - 1)
        st.session_state.skill_levels[skill_type]["xp"] = new_xp
        st.session_state.skill_levels[skill_type]["level"] = current_level
        save_user_data()
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Error in award_skill_xp for {skill_type}: {str(e)}\n")

def check_achievements():
    df = pd.DataFrame(st.session_state.progress_fitness)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        week_start = datetime.now() - pd.Timedelta(days=datetime.now().weekday())
        week_logs = df[df["date"] >= week_start]
        if len(week_logs["date"].dt.date.unique()) >= 3 and "weekly_warrior" not in st.session_state.achievements:
            st.session_state.achievements.append("weekly_warrior")
            st.session_state.xp += achievements["weekly_warrior"]["xp"]
            st.session_state.total_xp += achievements["weekly_warrior"]["xp"]
            st.success(f"Achievement Unlocked: {achievements['weekly_warrior']['name']}! +{achievements['weekly_warrior']['xp']} XP")
            save_user_data()
            check_level_up()
    if st.session_state.get("quest_streak", 0) >= 5 and "quest_master" not in st.session_state.achievements:
        st.session_state.achievements.append("quest_master")
        st.session_state.xp += achievements["quest_master"]["xp"]
        st.session_state.total_xp += achievements["quest_master"]["xp"]
        st.success(f"Achievement Unlocked: {achievements['quest_master']['name']}! +{achievements['quest_master']['xp']} XP")
        save_user_data()
        check_level_up()
    if st.session_state.get("quest_streak", 0) >= 10 and "epic_questor" not in st.session_state.achievements:
        st.session_state.achievements.append("epic_questor")
        st.session_state.xp += achievements["epic_questor"]["xp"]
        st.session_state.total_xp += achievements["epic_questor"]["xp"]
        st.success(f"Achievement Unlocked: {achievements['epic_questor']['name']}! +{achievements['epic_questor']['xp']} XP")
        save_user_data()
        check_level_up()

# === ONBOARDING ===
if not st.session_state.get("onboarded", False):
    with st.expander("Welcome to the Fitness Wasteland!", expanded=True):
        st.markdown(f"""
        **Hero {st.session_state.name or 'Traveler'}!**  
        Welcome to Coach Woody's RPG!  
        - Battle laziness with workouts to earn XP!  
        - Log meals to fuel your quest!  
        - Complete missions to become a legend!  
        Set your stats in the sidebar to begin. Let’s conquer!  
        """)
        if st.button("Embark on Quest!"):
            st.session_state["onboarded"] = True
            save_user_data()

# === SIDE BAR ===
with st.sidebar:
    st.subheader("Hero Stats")
    if not st.session_state.name:
        name = st.text_input("Your Name", placeholder="Jake")
        if name:
            st.session_state.name = name
            st.success(f"Welcome, {name}!")
            save_user_data()
    st.markdown(f"**Avatar**: {get_avatar_title(st.session_state.level)}")
    st.markdown(f"**Appearance**: {get_avatar_image(st.session_state.level)}")
    if st.session_state.gear:
        st.markdown(f"**Gear**: {', '.join(st.session_state.gear)}")
    else:
        st.markdown("**Gear**: None")
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
        st.info(f"Approximately {weight_kg:.1f} kg")
    goal = st.selectbox("Weight Goal", ["Lose Weight", "Maintain", "Gain Weight"])
    st.session_state.weight_goal = goal
    if st.button("Calculate Calories & Macros"):
        if st.session_state.user_gender == "Male":
            bmr = 88.362 + (13.397 * st.session_state.body_weight_kg) + (4.799 * st.session_state.height_cm) - (5.677 * st.session_state.user_age)
        else:
            bmr = 447.593 + (9.247 * st.session_state.body_weight_kg) + (3.098 * st.session_state.height_cm) - (4.330 * st.session_state.user_age)
        st.session_state.bmr = int(bmr)
        maintenance = bmr * 1.55
        calories = maintenance + (200 if goal == "Gain Weight" else -200 if goal == "Lose Weight" else 0)
        protein = round(st.session_state.body_weight_kg * 2.20462 * 1.25)
        protein_cals = protein * 4
        remaining = max(0, calories - protein_cals)
        carbs = round(remaining * 0.5 / 4)
        fats = round(remaining * 0.5 / 9)
        st.session_state.calorie_goal = int(calories)
        st.session_state.macro_goal = {"protein": protein, "carbs": carbs, "fats": fats}
        st.success(f"Done! BMR: {st.session_state.bmr} cal | Daily Calories: {int(calories)} cal")
        save_user_data()
    st.divider()
    st.subheader("Guild")
    guilds = ["", "Strength Warriors", "Endurance Runners", "Flexibility Mages"]
    st.session_state.guild = st.selectbox("Join a Guild (+5% XP)", guilds)
    if st.session_state.guild:
        st.info(f"Guild: {st.session_state.guild}")
    save_user_data()
    st.divider()
    st.subheader("Achievements")
    for ach in st.session_state.achievements:
        st.markdown(f"**{achievements[ach]['name']}**: {achievements[ach]['desc']} (+{achievements[ach]['xp']} XP)")
    if not st.session_state.achievements:
        st.info("No achievements yet. Complete quests to earn some!")
    # Progress bars for some achievements
    if "weekly_warrior" not in st.session_state.achievements:
        df = pd.DataFrame(st.session_state.progress_fitness)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            week_start = datetime.now() - pd.Timedelta(days=datetime.now().weekday())
            week_logs = df[df["date"] >= week_start]
            current_week_workouts = len(week_logs["date"].dt.date.unique())
            st.markdown("Weekly Warrior Progress")
            st.progress(current_week_workouts / 3)
    if "quest_master" not in st.session_state.achievements:
        current_streak = st.session_state.get("quest_streak", 0)
        st.markdown("Quest Master Progress")
        st.progress(current_streak / 5)
    if "epic_questor" not in st.session_state.achievements:
        current_streak = st.session_state.get("quest_streak", 0)
        st.markdown("Epic Questor Progress")
        st.progress(current_streak / 10)

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
col1, col2 = st.columns([1, 3])
with col1:
    try:
        level = int(st.session_state.level)
    except (ValueError, TypeError) as e:
        level = 1
        st.session_state.level = 1
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Invalid level value: {str(e)}\n")
    st.metric(label="Level", value=level)
    st.caption(f"Title: {get_avatar_title(level)}")
    required_xp = 100 + 50 * (level - 1)
    st.metric(label="XP", value=st.session_state.xp, delta=f"{st.session_state.xp}/{required_xp}")
    st.progress(min(st.session_state.xp / required_xp, 1.0))
    st.metric(label="Total XP", value=st.session_state.total_xp)
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
with col2:
    st.markdown(f"**Mission Log**: Streak: {st.session_state.get('quest_streak', 0)} Days Fire")

# === MAIN CONTENT ===
st.markdown("# Coach Woody's Fitness RPG")

# === DAILY QUESTS EXPANDER ===
quest_progress = sum(1 for q in st.session_state.daily_quests.values() if q["completed"])
uncompleted_quests = 5 - quest_progress
quest_label = f"Quest Board ({uncompleted_quests} left)" if uncompleted_quests > 0 else "Quest Board (All Missions Cleared!)"
st.markdown(f"## {quest_label}")
with st.expander("Mission Briefing", expanded=uncompleted_quests > 0):
    st.info("Complete 5 daily missions to earn XP and glory! Resets at midnight.")
    st.metric(label="Missions Completed", value=quest_progress, delta=f"{quest_progress}/5")
    for i, quest in st.session_state.daily_quests.items():
        st.markdown(f"**{quest['task']}** (+{quest['xp']} XP) - {quest['desc']}")
        completed = st.checkbox("Mark as Completed", value=quest["completed"], key=f"quest_{i}")
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
            if quest["distance"] > 0:
                entry["distance"] = quest["distance"]
                entry["time"] = 0
            if quest["time_min"] > 0:
                entry["time"] = quest["time_min"]
                met = met_values.get(quest["type"], {"Medium": 4.0}).get("Medium", 4.0)
                entry["calories_burned"] = int(met * st.session_state.body_weight_kg * (quest["time_min"] / 60))
            st.session_state.progress_fitness.append(entry)
            skill_xp = quest.get("reps", 0) or quest.get("distance", 0) or quest.get("time_min", 0)
            award_skill_xp(quest["type"], skill_xp)
            save_user_data()
            st.balloons()
            st.success(f"Mission '{quest['task']}' cleared! +{quest['xp']} XP | +{skill_xp} {quest['type'].replace('_', ' ').title()} Skill XP")
            check_level_up()
            check_achievements()
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
        st.success("All missions cleared! +50 XP Bonus! Celebration")
        check_level_up()
        check_achievements()

# === TRAINING GROUNDS EXPANDER ===
with st.expander("Training Grounds"):
    st.subheader("Forge Your Strength")
    workout = st.selectbox("Workout Type", [
        "Push-ups", "Pull-ups", "Sit-ups", "Squats", "Plank", "Run",
        "Walk (Outdoor)", "Walk (Treadmill)", "Cycle (Outdoor)", "Cycle (Static Bike)",
        "Stretch", "HIIT", "Bench Press", "Deadlift", "Shoulder Press", "Bicep Curls",
        "Tricep Dips", "Leg Press", "Yoga", "Pilates", "Swimming", "Rowing",
        "Jump Rope", "Burpees", "Mountain Climbers", "Kettlebell Swings", "Battle Ropes"
    ])
    intensity = st.selectbox("Intensity", ["Low", "Medium", "High"])
    difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
    if workout in ["Push-ups", "Pull-ups", "Sit-ups", "Squats", "Bench Press", "Deadlift", "Shoulder Press", "Bicep Curls", "Tricep Dips", "Leg Press", "Burpees", "Mountain Climbers", "Kettlebell Swings", "Battle Ropes"]:
        variations = {
            "Push-ups": ["Normal", "Close-Grip", "Wide-Grip"],
            "Pull-ups": ["Normal", "Chin-ups", "Neutral-Grip"],
            "Sit-ups": ["Standard", "Russian Twists", "Leg Raises"],
            "Squats": ["Bodyweight", "Goblet", "Sumo"],
            "Bench Press": ["Barbell", "Dumbbell", "Incline"],
            "Deadlift": ["Conventional", "Sumo", "Romanian"],
            "Shoulder Press": ["Overhead", "Seated", "Arnold"],
            "Bicep Curls": ["Barbell", "Dumbbell", "Hammer"],
            "Tricep Dips": ["Bench", "Parallel Bars", "Ring"],
            "Leg Press": ["Standard", "Single Leg", "Wide Stance"],
            "Burpees": ["Standard", "With Push-up", "Box Jump"],
            "Mountain Climbers": ["Standard", "Cross Body", "Slow Tempo"],
            "Kettlebell Swings": ["Two-Handed", "Single-Handed", "American"],
            "Battle Ropes": ["Waves", "Slams", "Circles"]
        }
        variation = st.selectbox("Variation", variations.get(workout, ["Standard"]))
        reps = st.number_input("Reps", min_value=0, value=0)
        time_min = st.number_input("Time (min)", min_value=0.0, value=5.0, step=0.1)
        if st.button("Log Training"):
            type_lower = workout.lower().replace(" ", "_")
            entry = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": type_lower,
                "variation": variation,
                "reps": reps,
                "intensity": intensity,
                "difficulty": difficulty,
                "time": time_min
            }
            met = met_values.get(type_lower, {"Medium": 4.0}).get(intensity, 4.0)
            calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
            entry["calories_burned"] = int(calories_burned)
            st.session_state.progress_fitness.append(entry)
            xp_gain = award_fitness_xp(type_lower, reps=reps, intensity=intensity, difficulty=difficulty)
            if reps > 0:
                award_skill_xp(type_lower, reps)
                st.success(f"Trained {reps} {variation} {workout.lower()} ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{reps} {workout} Skill XP")
            else:
                st.warning("Enter at least 1 rep to earn skill XP.")
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
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("plank", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("plank", time_min=time_min, intensity=intensity, difficulty=difficulty)
                award_skill_xp("plank", int(time_min))
                save_user_data()
                st.success(f"Trained {time_min} min plank ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Plank Skill XP")
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
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("run", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("run", distance=distance, intensity=intensity, difficulty=difficulty)
                award_skill_xp("run", int(distance))
                save_user_data()
                st.success(f"Trained {distance}km run ({intensity}, {difficulty})! Pace: {pace} min/km | Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(distance)} Run Skill XP")
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
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("walk_outdoor", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_outdoor", distance=distance, intensity=intensity, difficulty=difficulty)
                award_skill_xp("walk_outdoor", int(distance))
                save_user_data()
                st.success(f"Trained {distance}km walk ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(distance)} Walk Outdoor Skill XP")
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
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("walk_treadmill", {"Medium": 4.0}).get(intensity, 4.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("walk_treadmill", time_min=time_min, intensity=intensity, difficulty=difficulty)
                award_skill_xp("walk_treadmill", int(time_min))
                save_user_data()
                st.success(f"Trained {distance}km treadmill ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Walk Treadmill Skill XP")
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
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("cycle_outdoor", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_outdoor", distance=distance, intensity=intensity, difficulty=difficulty)
                award_skill_xp("cycle_outdoor", int(distance))
                save_user_data()
                st.success(f"Trained {distance}km cycle ({intensity}, {difficulty})! Speed: {speed} km/h | Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(distance)} Cycle Outdoor Skill XP")
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
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("cycle_static", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("cycle_static", time_min=time_min, intensity=intensity, difficulty=difficulty)
                award_skill_xp("cycle_static", int(time_min))
                save_user_data()
                st.success(f"Trained {time_min} min static bike ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Cycle Static Skill XP")
                check_achievements()
    elif workout == "Stretch":
        time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
        if st.button("Log Stretch"):
            if time_min > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "stretch",
                    "time": time_min,
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("stretch", {"Medium": 2.5}).get(intensity, 2.5)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("stretch", time_min=time_min, intensity=intensity, difficulty=difficulty)
                award_skill_xp("stretch", int(time_min))
                save_user_data()
                st.success(f"Trained {time_min} min stretch ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Stretch Skill XP")
                check_achievements()
    elif workout == "HIIT":
        time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
        if st.button("Log HIIT"):
            if time_min > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "hiit",
                    "time": time_min,
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("hiit", {"Medium": 8.0}).get(intensity, 8.0)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("hiit", time_min=time_min, intensity=intensity, difficulty=difficulty)
                award_skill_xp("hiit", int(time_min))
                save_user_data()
                st.success(f"Trained {time_min} min HIIT ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} HIIT Skill XP")
                check_achievements()
    elif workout == "Yoga":
        time_min = st.number_input("Time (min)", min_value=0.0, step=0.1)
        if st.button("Log Yoga"):
            if time_min > 0:
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "yoga",
                    "time": time_min,
                    "intensity": intensity,
                    "difficulty": difficulty
                }
                met = met_values.get("yoga", {"Medium": 3.5}).get(intensity, 3.5)
                calories_burned = met * st.session_state.body_weight_kg * (time_min / 60)
                entry["calories_burned"] = int(calories_burned)
                st.session_state.progress_fitness.append(entry)
                xp_gain = award_fitness_xp("yoga", time_min=time_min, intensity=intensity, difficulty=difficulty)
                award_skill_xp("yoga", int(time_min))
                save_user_data()
                st.success(f"Trained {time_min} min yoga ({intensity}, {difficulty})! Burned: {entry['calories_burned']} cal | +{xp_gain} XP | +{int(time_min)} Yoga Skill XP")
                check_achievements()
    # Add similar blocks for other new activities like Pilates, Swimming, etc.

    # Log Nutrition
    st.subheader("Refuel Your Body")
    meal = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
    calories = st.number_input("Calories", min_value=0, value=0, step=10)
    protein = st.number_input("Protein (g)", min_value=0, value=0, step=10)
    carbs = st.number_input("Carbs (g)", min_value=0, value=0, step=10)
    fats = st.number_input("Fats (g)", min_value=0, value=0, step=10)
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
        if balance_score >= 80 and "macro_master" not in st.session_state.achievements:
            st.session_state.achievements.append("macro_master")
            st.session_state.xp += achievements["macro_master"]["xp"]
            st.session_state.total_xp += achievements["macro_master"]["xp"]
            st.success(f"Achievement Unlocked: {achievements['macro_master']['name']}! +{achievements['macro_master']['xp']} XP")
        award_skill_xp("meal_log", 1)
        save_user_data()
        st.success(f"Refueled with {meal}: {calories} cal (Balance: {balance_score:.0f}%)! +{xp_gain} XP | +1 Meal Log Skill XP")
        check_achievements()

    # Calorie Summary
    if st.session_state.progress_fitness or st.session_state.progress_nutrition:
        st.subheader("Energy Matrix")
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Consumed Today", value=int(total_consumed))
        col2.metric(label="Burned Today", value=int(total_burned))
        col3.metric(label="Net Calories", value=int(net_calories))

# === SKILL TREE EXPANDER ===
with st.expander("Skill Matrix"):
    st.subheader("Your Abilities")
    categories = {
        "Cardio": ["run", "walk_outdoor", "walk_treadmill", "cycle_outdoor", "cycle_static", "hiit", "swimming", "rowing", "jump_rope", "burpees", "mountain_climbers", "battle_ropes"],
        "Strength": ["push_ups", "pull_ups", "sit_ups", "squats", "plank", "bench_press", "deadlift", "shoulder_press", "bicep_curls", "tricep_dips", "leg_press", "kettlebell_swings"],
        "Stretching": ["stretch", "yoga", "pilates"]
    }
    for cat, skills in categories.items():
        st.markdown(f"### {cat}")
        for key in skills:
            if key in st.session_state.skill_levels:
                value = st.session_state.skill_levels[key]
                skill_name = key.replace("_", " ").title()
                level = value["level"]
                xp = value["xp"]
                required_xp = 100 + 50 * (level - 1)
                badge = " Master" if level >= 10 else ""
                st.markdown(f"**{skill_icons.get(key, 'Star')} {skill_name}: Level {level}{badge}** ({xp}/{required_xp} XP)")
                st.progress(min(xp / required_xp, 1.0))

# === COACH WOODY EXPANDER ===
with st.expander("Command Center"):
    st.subheader("Quick Start")
    st.write("Launch a mission query!")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Combat Training")
        for i, starter in enumerate(st.session_state.fitness_starters):
            if st.button(starter):
                st.session_state.quick_prompt = starter
    with col2:
        st.write("Resource Management")
        for i, starter in enumerate(st.session_state.nutrition_starters):
            if st.button(starter):
                st.session_state.quick_prompt = starter
    st.subheader("Consult Coach")
    coach_name = "Woody" if st.session_state.user_gender == "Male" else "Hibiki"
    prompt = ChatPromptTemplate.from_template(f"""
    You are {coach_name}, {'motivational strength coach' if st.session_state.user_gender == 'Male' else 'graceful, empowering trainer'}.
    Be fun, encouraging, under 120 words. Use emojis. Answer fitness or nutrition questions. Suggest meals/recipes for nutrition queries.
    Body weight: {st.session_state.body_weight_kg:.1f}kg
    Calorie goal: {st.session_state.calorie_goal}, Macros: P{st.session_state.macro_goal['protein']}g C{st.session_state.macro_goal['carbs']}g F{st.session_state.macro_goal['fats']}g
    History: {{history}}
    User: {{input}}
    {coach_name}:
    """)
    chain = prompt | llm | StrOutputParser() if llm else None
    user_prompt = st.chat_input("Query the commander...")
    if st.session_state.quick_prompt:
        user_prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Transmitting..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                response = chain_invoke(chain, history, user_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_user_data()
    else:
        tips = [
            "Keep shoulders back during push-ups for max power!",
            "Try grilled chicken with quinoa for a balanced meal!",
            "Warm up for 5 min to prevent injuries!",
            "Snack on apples with peanut butter for quick energy!"
        ]
        st.info(f"Coach Tip: {random.choice(tips)}")
    st.subheader("Form Analysis")
    st.info("Upload your form data for review!")
    form_prompt = st.text_area("Form Data", placeholder="E.g., My push-up form feels off...")
    if st.button("Analyze Form"):
        if form_prompt:
            prompt = ChatPromptTemplate.from_template(f"""
            You are {coach_name}, {'motivational strength coach' if st.session_state.user_gender == 'Male' else 'graceful, empowering trainer'}.
            Be fun, encouraging, under 120 words. Use emojis.
            User: {form_prompt}
            {coach_name}:
            """)
            chain = prompt | llm | StrOutputParser() if llm else None
            with st.spinner("Scanning..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                response = chain_invoke(chain, history, form_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "user", "content": form_prompt})
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_user_data()