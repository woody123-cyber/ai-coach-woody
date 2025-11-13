# coach_woody_app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_confetti import confetti
import random
import time

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Coach Woody: Level Up Your Life",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com',
        'Report a bug': 'https://github.com',
        'About': '# Coach Woody v2.0\n*Your AI-Powered Fitness RPG*'
    }
)

# === CUSTOM CSS ===
st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white;}
    .stButton>button {
        background: #ff6b6b; color: white; border: none; border-radius: 12px;
        padding: 0.6rem 1.2rem; font-weight: bold; font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(255,107,107,0.4);
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-3px); box-shadow: 0 8px 20px rgba(255,107,107,0.6);
    }
    .achievement {
        background: linear-gradient(45deg, #ffd700, #ffb800);
        color: #1a1a1a; padding: 1rem; border-radius: 16px;
        text-align: center; font-weight: bold; margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(255,215,0,0.4);
    }
    .level-badge {
        background: #8b5cf6; color: white; padding: 0.5rem 1rem;
        border-radius: 50px; font-size: 1.3rem; font-weight: bold;
        display: inline-block; margin: 0.5rem 0;
    }
    .stTextInput > div > div > input {
        border-radius: 12px; padding: 0.8rem; font-size: 1.1rem;
    }
    .workout-card {
        background: rgba(255,255,255,0.15); border-radius: 16px;
        padding: 1.2rem; margin: 0.8rem 0; backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    .stMetric {
        background: rgba(255,255,255,0.1); border-radius: 16px;
        padding: 1rem; text-align: center;
    }
    .stMetric label {font-size: 1.1rem !important; color: #a0d8ff !important;}
    .stMetric div {font-size: 2rem !important; font-weight: bold !important;}
</style>
""", unsafe_allow_html=True)

# === DATA FILE ===
DATA_FILE = "coach_woody_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === USER DATA INIT ===
user_id = st.session_state.get("user_id", str(random.randint(1000, 9999)))
if user_id not in st.session_state:
    st.session_state[user_id] = {
        "name": "",
        "level": 1,
        "xp": 0,
        "total_xp": 0,
        "streak": 0,
        "last_workout": None,
        "workouts": [],
        "achievements": [],
        "boss_defeated": 0,
        "weight_unit": "lbs"
    }

user = st.session_state[user_id]
data = load_data()
if user_id not in data:
    data[user_id] = user
    save_data(data)

# === XP & LEVEL SYSTEM ===
def xp_for_level(level):
    return 100 * level * (level + 1) // 2

def add_xp(amount, reason):
    user["xp"] += amount
    user["total_xp"] += amount
    check_level_up()
    log_event(f"+{amount} XP: {reason}")

def check_level_up():
    required = xp_for_level(user["level"])
    if user["xp"] >= required:
        user["xp"] -= required
        user["level"] += 1
        st.balloons()
        confetti()
        st.success(f"LEVEL UP! You're now Level {user['level']}!")

def check_streak():
    today = date.today()
    if user["last_workout"]:
        last = datetime.fromisoformat(user["last_workout"]).date()
        if last == today - timedelta(days=1):
            user["streak"] += 1
        elif last != today:
            user["streak"] = 1
    else:
        user["streak"] = 1
    user["last_workout"] = datetime.now().isoformat()

# === ACHIEVEMENTS ===
ACHIEVEMENTS = [
    {"id": "first_lift", "name": "First Rep", "desc": "Log your first workout", "icon": "💪"},
    {"id": "week_streak", "name": "Week Warrior", "desc": "7-day streak", "icon": "🔥"},
    {"id": "boss_1", "name": "Defeated Benchzilla", "desc": "Lift 1.5x bodyweight", "icon": "👹"},
    {"id": "century", "name": "Century Club", "desc": "100 total workouts", "icon": "💯"},
]

def unlock_achievement(ach_id):
    ach = next((a for a in ACHIEVEMENTS if a["id"] == ach_id), None)
    if ach and ach_id not in user["achievements"]:
        user["achievements"].append(ach_id)
        st.toast(f"🏆 {ach['icon']} {ach['name']} Unlocked!", icon="🎉")

# === LOG EVENT ===
def log_event(msg):
    if "log" not in user:
        user["log"] = []
    user["log"].append({"time": datetime.now().isoformat(), "msg": msg})
    user["log"] = user["log"][-50:]  # Keep last 50

# === SIDEBAR ===
with st.sidebar:
    st.image("https://em-content.zobj.net/source/apple/118/trophy_1f3c6.png", width=80)
    st.title("Coach Woody")

    if not user["name"]:
        name = st.text_input("What's your name, warrior?", placeholder="Enter name...")
        if st.button("Begin Journey"):
            if name.strip():
                user["name"] = name.strip().title()
                add_xp(50, "Joined the gym!")
                unlock_achievement("first_lift")
                st.rerun()
    else:
        st.markdown(f"## Welcome, **{user['name']}**!")
        st.markdown(f"<div class='level-badge'>LV.{user['level']}</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("XP", f"{user['xp']}", f"+{user.get('daily_xp',0)}")
        with col2:
            st.metric("Streak", f"{user['streak']} 🔥")

        xp_needed = xp_for_level(user["level"]) - user["xp"]
        st.progress(user["xp"] / xp_for_level(user["level"]))
        st.caption(f"{xp_needed} XP to Level {user['level']+1}")

        st.markdown("---")
        st.caption("💡 *Log a workout to earn XP!*")

# === MAIN APP ===
if not user["name"]:
    st.title("Coach Woody: Level Up Your Life")
    st.markdown("""
    ### Welcome to the ultimate **Fitness RPG**!
    - Log workouts in **5 seconds**
    - Earn **XP, level up, defeat bosses**
    - Get **AI coaching** from Coach Woody
    - Track **progress with epic charts**
    """)
    st.info("Enter your name in the sidebar to begin!")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["Log Workout", "Dashboard", "AI Coach", "Achievements"])

    # === TAB 1: LOG WORKOUT ===
    with tab1:
        st.header("Log Your Workout")
        with st.form("log_form"):
            exercise = st.text_input("Exercise", placeholder="e.g., Bench Press, Squat, Pull-ups")
            weight = st.number_input(f"Weight ({user['weight_unit']})", min_value=0.0, step=0.5)
            reps = st.number_input("Reps", min_value=1, step=1)
            sets = st.number_input("Sets", min_value=1, step=1, value=3)
            notes = st.text_area("Notes (optional)", placeholder="Felt strong! PR!")

            col1, col2 = st.columns([3,1])
            with col1:
                submitted = st.form_submit_button("Log & Earn XP!", use_container_width=True)
            with col2:
                if st.form_submit_button("Quick Log", use_container_width=True):
                    exercise, weight, reps, sets = "Push-ups", 0, 10, 3

            if submitted or (exercise and weight is not None and reps and sets):
                if not exercise:
                    st.error("Please enter an exercise.")
                else:
                    workout = {
                        "date": datetime.now().isoformat(),
                        "exercise": exercise.strip().title(),
                        "weight": weight,
                        "reps": reps,
                        "sets": sets,
                        "notes": notes,
                        "volume": weight * reps * sets
                    }
                    user["workouts"].append(workout)
                    check_streak()

                    xp_earned = min(50, int(workout["volume"] / 10) + reps + sets)
                    add_xp(xp_earned, f"{exercise} {weight}{user['weight_unit']} x{reps}x{sets}")

                    if len(user["workouts"]) == 1:
                        unlock_achievement("first_lift")
                    if user["streak"] == 7:
                        unlock_achievement("week_streak")
                    if len(user["workouts"]) >= 100:
                        unlock_achievement("century")

                    st.success(f"Logged! +{xp_earned} XP")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()

    # === TAB 2: DASHBOARD ===
    with tab2:
        st.header("Your Progress")

        if user["workouts"]:
            df = pd.DataFrame(user["workouts"])
            df["date"] = pd.to_datetime(df["date"]).dt.date

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Workouts", len(df))
            with col2:
                st.metric("Total Volume", f"{df['volume'].sum():,} {user['weight_unit']}")
            with col3:
                st.metric("Favorite Move", df['exercise'].mode()[0])
            with col4:
                st.metric("Bosses Defeated", user["boss_defeated"])

            # Progress Chart
            chart_df = df.groupby("date")["volume"].sum().reset_index()
            fig = px.area(chart_df, x="date", y="volume", title="Daily Volume Trend")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Top Exercises
            top_ex = df['exercise'].value_counts().head(5)
            fig2 = px.bar(x=top_ex.values, y=top_ex.index, orientation='h', title="Top 5 Exercises")
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("No workouts yet. Log one to see your progress!")

    # === TAB 3: AI COACH ===
    with tab3:
        st.header("Ask Coach Woody")
        prompt = st.text_area("Need advice?", placeholder="e.g., How do I improve my squat? Best post-workout meal?")
        if st.button("Get Coaching"):
            if prompt:
                with st.spinner("Woody is thinking..."):
                    # Mock AI response (replace with Groq in production)
                    responses = [
                        f"Listen up, {user['name']}! To master your squat: feet shoulder-width, chest up, brace core. Film yourself!",
                        "Post-workout? Protein + carbs within 30 mins. Try chicken + rice or a smoothie with banana and whey.",
                        "Want bigger arms? Hit 10–20 sets per week. Add curls, dips, and close-grip bench.",
                        "Rest days are for recovery. Walk, stretch, sleep 8+ hours. No heroics."
                    ]
                    advice = random.choice(responses)
                    st.success(advice)
            else:
                st.warning("Ask me something!")

    # === TAB 4: ACHIEVEMENTS ===
    with tab4:
        st.header("Achievements")
        cols = st.columns(3)
        for i, ach in enumerate(ACHIEVEMENTS):
            with cols[i % 3]:
                unlocked = ach["id"] in user["achievements"]
                if unlocked:
                    st.markdown(f"<div class='achievement'>{ach['icon']} {ach['name']}<br><small>{ach['desc']}</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:rgba(255,255,255,0.1);padding:1rem;border-radius:16px;text-align:center;color:#888;'>{ach['icon']} ???</div>", unsafe_allow_html=True)

    # === SAVE ON EXIT ===
    data[user_id] = user
    save_data(data)