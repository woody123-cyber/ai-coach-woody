# app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import plotly.express as px
import random
import time
from streamlit_confetti import confetti

# -------------------------- PAGE CONFIG --------------------------
st.set_page_config(
    page_title="Coach Woody: Level Up Your Life",
    page_icon="Trophy",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "# Coach Woody v2.0\n*Your AI-Powered Fitness RPG*"
    }
)

# -------------------------- CUSTOM CSS --------------------------
st.markdown(
    """
<style>
    .main {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color:white;}
    .stButton>button {
        background:#ff6b6b; color:white; border:none; border-radius:12px;
        padding:0.6rem 1.2rem; font-weight:bold; font-size:1.1rem;
        box-shadow:0 4px 15px rgba(255,107,107,0.4);
        transition:all .3s;
    }
    .stButton>button:hover{transform:translateY(-3px);box-shadow:0 8px 20px rgba(255,107,107,0.6);}
    .level-badge{background:#8b5cf6;color:white;padding:0.5rem 1rem;border-radius:50px;
                 font-size:1.3rem;font-weight:bold;display:inline-block;margin:0.5rem 0;}
    .workout-card{background:rgba(255,255,255,0.15);border-radius:16px;padding:1.2rem;
                  margin:0.8rem 0;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.2);}
    .stMetric{background:rgba(255,255,255,0.1);border-radius:16px;padding:1rem;text-align:center;}
    .stMetric label{font-size:1.1rem !important;color:#a0d8ff !important;}
    .stMetric div{font-size:2rem !important;font-weight:bold !important;}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------- DATA FILE --------------------------
DATA_FILE = "coach_woody_data.json"


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -------------------------- USER INITIALISATION --------------------------
user_id = st.session_state.get("user_id")
if not user_id:
    user_id = str(random.randint(1000, 9999))
    st.session_state.user_id = user_id

# Load global data
global_data = load_data()
if user_id not in global_data:
    global_data[user_id] = {
        "level": 1,
        "xp": 0,
        "total_xp": 0,
        "streak": 0,
        "last_workout": None,
        "workouts": [],
        "achievements": [],
        "boss_defeated": 0,
        "weight_unit": "lbs",
        "log": [],
    }
    save_data(global_data)

user = global_data[user_id]

# -----------------------------------------------------------------
# Helper: XP / Level
def xp_for_level(lvl: int) -> int:
    return 100 * lvl * (lvl + 1) // 2


def add_xp(amount: int, reason: str):
    user["xp"] += amount
    user["total_xp"] += amount
    log_event(f"+{amount} XP: {reason}")
    check_level_up()


def check_level_up():
    required = xp_for_level(user["level"])
    if user["xp"] >= required:
        user["xp"] -= required
        user["level"] += 1
        st.balloons()
        confetti()
        st.success(f"LEVEL UP! You are now **Level {user['level']}**!")


def log_event(msg: str):
    if "log" not in user:
        user["log"] = []
    user["log"].append({"time": datetime.now().isoformat(), "msg": msg})
    user["log"] = user["log"][-50:]


# -----------------------------------------------------------------
# Streak handling
def update_streak():
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


# -----------------------------------------------------------------
# Achievements
ACHIEVEMENTS = [
    {"id": "first_lift", "name": "First Rep", "desc": "Log your first workout", "icon": "Muscle"},
    {"id": "week_streak", "name": "Week Warrior", "desc": "7-day streak", "icon": "Fire"},
    {"id": "century", "name": "Century Club", "desc": "100 total workouts", "icon": "Hundred Points"},
]


def unlock_achievement(aid: str):
    ach = next((a for a in ACHIEVEMENTS if a["id"] == aid), None)
    if ach and aid not in user["achievements"]:
        user["achievements"].append(aid)
        st.toast(f"{ach['icon']} **{ach['name']}** unlocked!", icon="Trophy")


# -----------------------------------------------------------------
# -------------------------- SIDEBAR --------------------------
with st.sidebar:
    st.image(
        "https://em-content.zobj.net/source/apple/118/trophy_1f3c6.png",
        width=80,
    )
    st.title("Coach Woody")

    # ---------- ONBOARDING ----------
    if not st.session_state.get("onboarded", False):
        st.markdown("### Start Your Journey")
        name_input = st.text_input(
            "What's your name, warrior?",
            placeholder="Enter name...",
            key="name_input",  # <-- widget key (do NOT write to it later)
        )

        if st.button("Begin Journey", use_container_width=True):
            if name_input and name_input.strip():
                # Store in a *different* session_state key
                st.session_state.user_name = name_input.strip().title()
                st.session_state.onboarded = True
                add_xp(50, "Joined the gym!")
                unlock_achievement("first_lift")
                st.success(f"Welcome **{st.session_state.user_name}**! Let's crush it!")
                st.rerun()
            else:
                st.error("Please type a name.")
    else:
        # ---------- POST-ONBOARDING ----------
        st.markdown(f"## **{st.session_state.user_name}**")
        st.markdown(
            f"<div class='level-badge'>LV.{user['level']}</div>", unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            st.metric("XP", f"{user['xp']}")
        with c2:
            st.metric("Streak", f"{user['streak']} Fire")

        needed = xp_for_level(user["level"]) - user["xp"]
        st.progress(user["xp"] / xp_for_level(user["level"]))
        st.caption(f"{needed} XP to Level {user['level'] + 1}")

        st.markdown("---")
        st.caption("*Log a workout to earn XP!*")

# -----------------------------------------------------------------
# If still onboarding → show a friendly splash
if not st.session_state.get("onboarded", False):
    st.title("Coach Woody – Level Up Your Life")
    st.markdown(
        """
    - **Log workouts in 5 seconds**  
    - Earn **XP**, level up, defeat bosses  
    - Get **AI coaching** from Coach Woody  
    - Track progress with **epic charts**  
    """
    )
    st.info("Enter your name in the sidebar to start!")
else:
    # -----------------------------------------------------------------
    # -------------------------- MAIN TABS --------------------------
    tab_log, tab_dash, tab_coach, tab_ach = st.tabs(
        ["Log Workout", "Dashboard", "AI Coach", "Achievements"]
    )

    # -------------------------- TAB: LOG WORKOUT --------------------------
    with tab_log:
        st.header("Log Your Workout")
        with st.form("log_form", clear_on_submit=True):
            ex = st.text_input("Exercise", placeholder="Bench Press, Squat…")
            w = st.number_input(f"Weight ({user['weight_unit']})", min_value=0.0, step=0.5)
            r = st.number_input("Reps", min_value=1, step=1)
            s = st.number_input("Sets", min_value=1, step=1, value=3)
            notes = st.text_area("Notes (optional)", placeholder="Felt strong!")

            col_a, col_b = st.columns([3, 1])
            with col_a:
                submit = st.form_submit_button("Log & Earn XP!", use_container_width=True)
            with col_b:
                quick = st.form_submit_button("Quick Log (Push-ups)", use_container_width=True)

            if quick:
                ex, w, r, s = "Push-ups", 0, 10, 3

            if (submit or quick) and ex:
                workout = {
                    "date": datetime.now().isoformat(),
                    "exercise": ex.strip().title(),
                    "weight": w,
                    "reps": r,
                    "sets": s,
                    "notes": notes,
                    "volume": w * r * s,
                }
                user["workouts"].append(workout)
                update_streak()

                xp = min(50, int(workout["volume"] / 10) + r + s)
                add_xp(xp, f"{ex} {w}{user['weight_unit']} ×{r}×{s}")

                if len(user["workouts"]) == 1:
                    unlock_achievement("first_lift")
                if user["streak"] == 7:
                    unlock_achievement("week_streak")
                if len(user["workouts"]) >= 100:
                    unlock_achievement("century")

                st.success(f"Logged! +{xp} XP")
                st.balloons()
                time.sleep(1)
                st.rerun()

    # -------------------------- TAB: DASHBOARD --------------------------
    with tab_dash:
        st.header("Your Progress")
        if user["workouts"]:
            df = pd.DataFrame(user["workouts"])
            df["date"] = pd.to_datetime(df["date"]).dt.date

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Workouts", len(df))
            with c2:
                st.metric("Total Volume", f"{df['volume'].sum():,} {user['weight_unit']}")
            with c3:
                st.metric("Favorite", df["exercise"].mode()[0])
            with c4:
                st.metric("Bosses Defeated", user["boss_defeated"])

            # Volume over time
            vol = df.groupby("date")["volume"].sum().reset_index()
            fig = px.area(vol, x="date", y="volume", title="Daily Volume Trend")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Top exercises
            top = df["exercise"].value_counts().head(5)
            fig2 = px.bar(y=top.index, x=top.values, orientation="h", title="Top 5 Exercises")
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No workouts yet – log one to see the magic!")

    # -------------------------- TAB: AI COACH --------------------------
    with tab_coach:
        st.header("Ask Coach Woody")
        prompt = st.text_area(
            "Need advice?",
            placeholder="How do I improve my squat? Best post-workout meal?",
        )
        if st.button("Get Coaching"):
            if prompt.strip():
                with st.spinner("Woody is thinking…"):
                    # ---- Replace with real Groq call when you have the key ----
                    replies = [
                        f"Listen up, {st.session_state.user_name}! Keep your chest up, brace your core, and drive through the heels on squats.",
                        "Post-workout: 20-30 g protein + fast carbs within 30 min. Try chicken + rice or a banana-protein shake.",
                        "Want bigger arms? 10-20 weekly sets of curls, triceps, and close-grip bench.",
                        "Rest days matter. Walk, stretch, sleep 8+ hours.",
                    ]
                    st.success(random.choice(replies))
            else:
                st.warning("Ask me something!")

    # -------------------------- TAB: ACHIEVEMENTS --------------------------
    with tab_ach:
        st.header("Achievements")
        cols = st.columns(3)
        for i, a in enumerate(ACHIEVEMENTS):
            with cols[i % 3]:
                if a["id"] in user["achievements"]:
                    st.markdown(
                        f"<div style='background:linear-gradient(45deg,#ffd700,#ffb800);color:#1a1a1a;padding:1rem;border-radius:16px;text-align:center;font-weight:bold;box-shadow:0 4px 15px rgba(255,215,0,.4);'>"
                        f"{a['icon']} {a['name']}<br><small>{a['desc']}</small></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='background:rgba(255,255,255,0.1);padding:1rem;border-radius:16px;text-align:center;color:#888;'>"
                        f"{a['icon']} ???</div>",
                        unsafe_allow_html=True,
                    )

# -----------------------------------------------------------------
# Persist everything at the end of the run
global_data[user_id] = user
save_data(global_data)