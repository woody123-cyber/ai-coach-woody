# app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import plotly.express as px
import random

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Coach Woody: Level Up Your Life",
    page_icon="Trophy",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': '# Coach Woody v2.1\n*Your AI-Powered Fitness RPG*'
    }
)

# === CUSTOM CSS ===
st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); color: #e0e0e0;}
    .stButton>button {
        background: linear-gradient(45deg, #ff6b6b, #f94d6a); color: white; border: none; border-radius: 16px;
        padding: 0.8rem 1.6rem; font-weight: bold; font-size: 1.2rem; width: 100%;
        box-shadow: 0 6px 20px rgba(255,107,107,0.4); transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-4px); box-shadow: 0 12px 30px rgba(255,107,107,0.6);
    }
    .level-badge {
        background: linear-gradient(45deg, #8b5cf6, #6a0dad); color: white; padding: 0.6rem 1.4rem;
        border-radius: 50px; font-size: 1.4rem; font-weight: bold; display: inline-block;
        box-shadow: 0 4px 15px rgba(139,92,246,0.5);
    }
    .workout-card {
        background: rgba(255,255,255,0.12); border-radius: 18px; padding: 1.4rem; margin: 1rem 0;
        backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.2s;
    }
    .workout-card:hover {transform: scale(1.02);}
    .boss-card {
        background: linear-gradient(45deg, #dc2626, #991b1b); color: white; padding: 1.5rem;
        border-radius: 20px; text-align: center; font-weight: bold; margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(220,38,38,0.5);
    }
    .powerup {
        background: linear-gradient(45deg, #10b981, #059669); color: white; padding: 0.8rem 1.2rem;
        border-radius: 12px; font-size: 1rem; display: inline-block; margin: 0.3rem;
    }
    .stMetric {background: rgba(255,255,255,0.1); border-radius: 16px; padding: 1rem;}
    .stMetric label {font-size: 1rem !important; color: #94a3b8 !important;}
    .stMetric div {font-size: 2.2rem !important; font-weight: bold !important; color: #fbbf24 !important;}
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        border-radius: 14px; padding: 0.9rem; font-size: 1.1rem; background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.3); color: white;
    }
</style>
""", unsafe_allow_html=True)

# === DATA FILE ===
DATA_FILE = "coach_woody_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === USER INIT ===
user_id = st.session_state.get("user_id")
if not user_id:
    user_id = f"user_{random.randint(10000, 99999)}"
    st.session_state.user_id = user_id

data = load_data()
if user_id not in data:
    data[user_id] = {
        "name": "",
        "level": 1,
        "xp": 0,
        "total_xp": 0,
        "streak": 0,
        "last_workout": None,
        "workouts": [],
        "achievements": [],
        "boss_defeated": 0,
        "weight_unit": "lbs",
        "powerups": [],
        "daily_boss": None,
        "last_boss_date": None
    }
user = data[user_id]

# === XP SYSTEM ===
def xp_for_level(lvl): 
    return 100 * lvl * (lvl + 1) // 2

def add_xp(amount, reason=""):
    user["xp"] += amount
    user["total_xp"] += amount
    log_event(f"+{amount} XP: {reason}")
    check_level_up()

def check_level_up():
    req = xp_for_level(user["level"])
    if user["xp"] >= req:
        user["xp"] -= req
        user["level"] += 1
        st.balloons()  # Built-in, no error
        st.success(f"LEVEL UP! You're now **Level {user['level']}**!")
        unlock_gear()

def unlock_gear():
    gears = ["Iron Gauntlets", "Titan Belt", "Phoenix Wraps", "Dragon Boots"]
    if user["level"] in [5, 10, 15, 20]:
        gear = gears[(user["level"]//5)-1]
        st.toast(f"UNLOCKED: **{gear}** (+10% strength)", icon="Backpack")

# === STREAK & BOSS ===
def check_streak_and_boss():
    today = date.today().isoformat()
    if user["last_workout"]:
        last = datetime.fromisoformat(user["last_workout"]).date()
        if last == date.today() - timedelta(days=1):
            user["streak"] += 1
        elif last != date.today():
            user["streak"] = 1
    else:
        user["streak"] = 1
    user["last_workout"] = datetime.now().isoformat()

    # Daily Boss
    if user["last_boss_date"] != today:
        user["daily_boss"] = random.choice([
            {"name": "Benchzilla", "task": "3x5 Bench Press @ 1.5x bodyweight", "reward": 150},
            {"name": "Squat Serpent", "task": "3x8 Squat @ 80% 1RM", "reward": 180},
            {"name": "Deadlift Demon", "task": "1x5 Deadlift @ 2x bodyweight", "reward": 200},
        ])
        user["last_boss_date"] = today

# === ACHIEVEMENTS ===
ACHIEVEMENTS = [
    {"id": "first", "name": "First Blood", "desc": "Log your first workout", "icon": "Dagger"},
    {"id": "streak7", "name": "Week Warrior", "desc": "7-day streak", "icon": "Fire"},
    {"id": "boss1", "name": "Boss Slayer", "desc": "Defeat a daily boss", "icon": "Skull"},
    {"id": "volume", "name": "Volume King", "desc": "10,000 lbs in one day", "icon": "Lightning"},
]

def unlock_achievement(aid):
    ach = next((a for a in ACHIEVEMENTS if a["id"] == aid), None)
    if ach and aid not in user["achievements"]:
        user["achievements"].append(aid)
        st.toast(f"{ach['icon']} **{ach['name']}** Unlocked!", icon="Trophy")

# === LOG EVENT ===
def log_event(msg):
    if "log" not in user: 
        user["log"] = []
    user["log"].append({"time": datetime.now().strftime("%H:%M"), "msg": msg})
    user["log"] = user["log"][-30:]

# === SIDEBAR ===
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#fbbf24;'>Trophy Coach Woody</h1>", unsafe_allow_html=True)
    
    if not user["name"]:
        st.markdown("### Sword Begin Your Legend")
        name = st.text_input("Hero Name", placeholder="e.g., Iron Mike", key="name_input")
        col1, col2 = st.columns([1,1])
        with col1:
            unit = st.radio("Unit", ["lbs", "kg"], horizontal=True, index=0 if user["weight_unit"]=="lbs" else 1)
            user["weight_unit"] = unit
        if st.button("Rocket Begin Journey", use_container_width=True, type="primary"):
            if name.strip():
                user["name"] = name.strip().title()
                add_xp(100, "Entered the arena!")
                unlock_achievement("first")
                st.success(f"Welcome, **{user['name']}**! Your journey begins!")
                st.rerun()
            else:
                st.error("Enter a name to begin!")
    else:
        st.markdown(f"## Crown **{user['name']}**")
        st.markdown(f"<div class='level-badge'>LV.{user['level']}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1: st.metric("XP", f"{user['xp']:,}")
        with c2: st.metric("Streak", f"{user['streak']} Fire")
        
        xp_needed = xp_for_level(user["level"]) - user["xp"]
        st.progress(user["xp"] / xp_for_level(user["level"]))
        st.caption(f"**{xp_needed} XP** to Level {user['level']+1}")

        st.markdown("### Backpack Power-Ups")
        if user["powerups"]:
            for p in user["powerups"]:
                st.markdown(f"<span class='powerup'>Sparkles {p}</span>", unsafe_allow_html=True)
        else:
            st.caption("_Earn from streaks!_")

# === MAIN APP ===
if not user["name"]:
    st.markdown("""
    ## Welcome to the Ultimate **Fitness RPG**!
    - Log workouts in **3 clicks**
    - Earn **XP, level up, unlock gear**
    - Defeat **daily bosses**
    - Get **AI coaching** & **power-ups**
    """)
    st.info("Left Arrow Enter your name in the sidebar to begin!")
else:
    check_streak_and_boss()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Sword Log", "Chart Increasing Progress", "Skull Boss", "Trophy Achievements", "Robot Coach"])

    # === LOG WORKOUT ===
    with tab1:
        st.header("Log Your Victory")
        with st.form("log_form", clear_on_submit=True):
            exercise = st.text_input("Exercise", placeholder="Bench Press, Squat, Run...")
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input(f"Weight ({user['weight_unit']})", min_value=0.0, step=0.5, value=0.0)
                sets = st.number_input("Sets", min_value=1, step=1, value=3)
            with col2:
                reps = st.number_input("Reps", min_value=1, step=1, value=10)
                notes = st.text_area("Notes", placeholder="PR! Felt epic!", height=80)
            
            submitted = st.form_submit_button("Explosion LOG & EARN XP", use_container_width=True)
            if submitted:
                if not exercise.strip():
                    st.error("Enter an exercise!")
                else:
                    volume = weight * reps * sets
                    workout = {
                        "date": datetime.now().isoformat(),
                        "exercise": exercise.strip().title(),
                        "weight": weight, "reps": reps, "sets": sets,
                        "volume": volume, "notes": notes
                    }
                    user["workouts"].append(workout)
                    xp = min(80, int(volume / 15) + reps + sets)
                    add_xp(xp, f"{exercise} {weight}{user['weight_unit']}x{reps}x{sets}")
                    
                    if volume >= 10000:
                        unlock_achievement("volume")
                    if user["streak"] == 7:
                        unlock_achievement("streak7")
                        user["powerups"].append("XP Boost +20%")
                    
                    st.success(f"**+{xp} XP** earned!")
                    st.balloons()
                    st.rerun()

    # === PROGRESS ===
    with tab2:
        st.header("Your Legend Grows")
        if user["workouts"]:
            df = pd.DataFrame(user["workouts"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["day"] = pd.to_datetime(df["date"]).dt.strftime("%a")

            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Total Workouts", len(df))
            with col2: st.metric("Total Volume", f"{df['volume'].sum():,} {user['weight_unit']}")
            with col3: st.metric("Bosses Defeated", user["boss_defeated"])

            chart_df = df.groupby("date")["volume"].sum().reset_index()
            fig = px.area(chart_df, x="date", y="volume", title="Daily Volume")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            top = df['exercise'].value_counts().head(6)
            fig2 = px.bar(y=top.index, x=top.values, orientation='h', title="Top Exercises")
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No battles fought yet. Log your first!")

    # === DAILY BOSS ===
    with tab3:
        st.header("Daily Boss Battle")
        boss = user["daily_boss"]
        if boss:
            st.markdown(f"<div class='boss-card'>Skull **{boss['name']}**<br><small>{boss['task']}</small><br>Reward: **+{boss['reward']} XP**</div>", unsafe_allow_html=True)
            if st.button("Sword I DEFEATED THE BOSS!", use_container_width=True):
                add_xp(boss["reward"], f"Defeated {boss['name']}")
                user["boss_defeated"] += 1
                unlock_achievement("boss1")
                user["daily_boss"] = None
                st.success("BOSS SLAIN! Epic loot incoming!")
                st.balloons()
                st.rerun()
        else:
            st.success("Checkmark Boss already defeated today! Rest well, warrior.")

    # === ACHIEVEMENTS ===
    with tab4:
        st.header("Legendary Feats")
        cols = st.columns(3)
        for i, ach in enumerate(ACHIEVEMENTS):
            with cols[i % 3]:
                unlocked = ach["id"] in user["achievements"]
                if unlocked:
                    st.markdown(f"<div style='background:linear-gradient(45deg,#10b981,#059669);color:white;padding:1rem;border-radius:16px;text-align:center;font-weight:bold;'>{ach['icon']} {ach['name']}<br><small>{ach['desc']}</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:rgba(255,255,255,0.1);color:#666;padding:1rem;border-radius:16px;text-align:center;'>{ach['icon']} Locked</div>", unsafe_allow_html=True)

    # === AI COACH ===
    with tab5:
        st.header("Ask Coach Woody")
        prompt = st.text_input("Need wisdom?", placeholder="How do I break a plateau?")
        if st.button("Get Advice"):
            if prompt:
                with st.spinner("Woody is thinking..."):
                    tips = [
                        f"Listen up, {user['name']}! Progressive overload is key. Add 5{user['weight_unit']} next week.",
                        "Rest is a weapon. Sleep 8+ hours. No excuses.",
                        "Form > weight. Film yourself. Fix it. Win.",
                        "Eat protein like it's your job. 1g per lb bodyweight."
                    ]
                    st.success(random.choice(tips))
            else:
                st.warning("Ask me anything!")

    # === SAVE DATA ===
    data[user_id] = user
    save_data(data)