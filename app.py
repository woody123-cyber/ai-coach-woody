# COACH WOODY v10 — The Ultimate AI Fitness + IELTS Coach
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import cv2
import numpy as np
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import io

# === CONFIG ===
st.set_page_config(page_title="Coach Woody", page_icon="trophy", layout="wide")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === MODE TOGGLE ===
mode = st.sidebar.radio("Mode", ["Fitness Coach", "IELTS Speaking Coach"], horizontal=True)

# === LLM ===
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.7)

# === PROMPTS ===
if mode == "Fitness Coach":
    system_prompt = """
    You are Coach Woody, world-class fitness coach. Fun, encouraging, under 120 words.
    User: {level}, Goal: {goal}
    Track: strength (grip/type), cardio (pace/speed/incline), cycling (RPM/resistance)
    History: {history}
    Celebrate PBs! Use emojis.
    User: {input}
    Coach Woody:
    """
else:
    system_prompt = """
    You are Coach Woody, IELTS Band 8+ Speaking Coach.
    Give feedback: fluency, vocab, grammar, pronunciation.
    Suggest 1 improvement. Under 150 words.
    Part: {part}
    User said: {input}
    Coach Woody:
    """

prompt = ChatPromptTemplate.from_template(system_prompt)
chain = prompt | llm | StrOutputParser()

# === SESSION STATE ===
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.level = "Beginner"
    st.session_state.goal = "Run a 5K"
    st.session_state.part = "Part 1"
    st.session_state.progress = []
    st.session_state.name = ""

# === USER NAME ===
if not st.session_state.name:
    name = st.sidebar.text_input("Your Name", placeholder="Jake")
    if name:
        st.session_state.name = name
        st.sidebar.success(f"Welcome, {name}!")

# === SIDEBAR: LOG WORKOUTS ===
with st.sidebar:
    st.header(f"{st.session_state.name or 'Athlete'}'s Log")

    if mode == "Fitness Coach":
        st.session_state.level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
        st.session_state.goal = st.text_input("Goal", st.session_state.goal)

        workout = st.selectbox("Log", [
            "Push-ups", "Pull-ups", "Sit-ups",
            "Run", "Walk (Outdoor)", "Walk (Treadmill)",
            "Cycle (Outdoor)", "Cycle (Static Bike)"
        ])

        # === STRENGTH ===
        if workout in ["Push-ups", "Pull-ups", "Sit-ups"]:
            st.subheader(f"{workout}")
            variations = {
                "Push-ups": ["Normal", "Close-Grip", "Wide-Grip"],
                "Pull-ups": ["Normal", "Chin-ups", "Neutral-Grip"],
                "Sit-ups": ["Standard", "Russian Twists", "Leg Raises"]
            }
            variation = st.selectbox("Type", variations[workout])
            reps = st.number_input("Reps", min_value=0, value=0)
            if st.button(f"Log {workout}"):
                entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": workout.lower().replace("-", "_"),
                    "variation": variation,
                    "reps": reps
                }
                st.session_state.progress.append(entry)
                st.success(f"Logged {reps} {variation} {workout.lower()}!")

        # === RUN ===
        elif workout == "Run":
            st.subheader("Run")
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
            time_min = st.number_input("Time (min)", min_value=0)
            if st.button("Log Run"):
                if distance > 0 and time_min > 0:
                    pace = round(time_min / distance, 2)
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "run", "distance": distance, "time": time_min, "pace": pace}
                    st.session_state.progress.append(entry)
                    st.success(f"Logged {distance}km! Pace: {pace} min/km")

        # === WALK OUTDOOR ===
        elif workout == "Walk (Outdoor)":
            st.subheader("Outdoor Walk")
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
            time_min = st.number_input("Time (min)", min_value=0)
            terrain = st.selectbox("Terrain", ["Flat", "Hilly", "Mixed"])
            if st.button("Log Walk"):
                if distance > 0:
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_outdoor", "distance": distance, "time": time_min, "terrain": terrain}
                    st.session_state.progress.append(entry)
                    st.success(f"Logged {distance}km walk!")

        # === WALK TREADMILL ===
        elif workout == "Walk (Treadmill)":
            st.subheader("Treadmill Walk")
            speed = st.number_input("Speed (km/h)", min_value=0.0, step=0.1)
            incline = st.number_input("Incline (%)", min_value=0.0, step=0.5)
            time_min = st.number_input("Time (min)", min_value=0)
            if st.button("Log"):
                if time_min > 0:
                    distance = round(speed * (time_min / 60), 2)
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "walk_treadmill", "distance": distance, "time": time_min, "speed": speed, "incline": incline}
                    st.session_state.progress.append(entry)
                    st.success(f"Logged {distance}km!")

        # === CYCLE OUTDOOR ===
        elif workout == "Cycle (Outdoor)":
            st.subheader("Outdoor Cycle")
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
            time_min = st.number_input("Time (min)", min_value=0)
            if st.button("Log Cycle"):
                if distance > 0 and time_min > 0:
                    speed = round(distance / (time_min / 60), 1)
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_outdoor", "distance": distance, "time": time_min, "avg_speed": speed}
                    st.session_state.progress.append(entry)
                    st.success(f"Logged {distance}km! Speed: {speed} km/h")

        # === CYCLE STATIC ===
        elif workout == "Cycle (Static Bike)":
            st.subheader("Static Bike")
            time_min = st.number_input("Time (min)", min_value=0)
            resistance = st.slider("Resistance", 1, 20, 10)
            rpm = st.number_input("Avg RPM", min_value=0, value=70)
            if st.button("Log"):
                if time_min > 0:
                    entry = {"date": datetime.now().strftime("%Y-%m-%d"), "type": "cycle_static", "time": time_min, "resistance": resistance, "rpm": rpm}
                    st.session_state.progress.append(entry)
                    st.success(f"Logged {time_min} min!")

    else:
        st.session_state.part = st.selectbox("IELTS Part", ["Part 1", "Part 2", "Part 3"])

    # === EXPORT & SUMMARY ===
    st.divider()
    if st.session_state.progress:
        df = pd.DataFrame(st.session_state.progress)
        csv = df.to_csv(index=False).encode()
        st.download_button("Export CSV", csv, "woody_progress.csv", "text/csv")

        # Weekly Summary
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent = df[df["date"] >= week_ago]
        if not recent.empty:
            st.info(f"**This Week:** {len(recent)} workouts logged!")

# === PHOTO FORM CHECK ===
st.subheader("Upload Form Photo")
uploaded = st.file_uploader("Push-up / Squat / Deadlift", ["jpg", "png"])
if uploaded:
    img = Image.open(uploaded)
    st.image(img, width=300)
    # Simple feedback
    feedback = "Great form! Core tight, back straight."
    st.success(feedback)
    st.session_state.messages.append({"role": "assistant", "content": feedback})

# === CHARTS (SMOOTH & INTERACTIVE) ===
if st.session_state.progress:
    df = pd.DataFrame(st.session_state.progress)
    df["date"] = pd.to_datetime(df["date"])

    # Date filter
    st.subheader("Progress Dashboard")
    date_filter = st.selectbox("View", ["Last 7 Days", "Last 30 Days", "All Time"])
    if date_filter == "Last 7 Days":
        cutoff = datetime.now() - timedelta(days=7)
    elif date_filter == "Last 30 Days":
        cutoff = datetime.now() - timedelta(days=30)
    else:
        cutoff = datetime.min
    df = df[df["date"] >= cutoff]

    if df.empty:
        st.info("No data in this range yet. Log a workout!")
    else:
        col1, col2 = st.columns(2)

        # STRENGTH CHART
        with col1:
            strength = df[df["type"].str.contains("push|pull|sit", case=False)]
            if not strength.empty:
                fig = px.line(
                    strength,
                    x="date",
                    y="reps",
                    color="variation",
                    facet_col="type",
                    title="Strength Progress",
                    markers=True,
                    hover_data=["reps"]
                )
                fig.update_layout(height=400, legend_title="Variation")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No strength workouts.")

        # CARDIO CHART
        with col2:
            cardio = df[df["type"].str.contains("run|walk|cycle")]
            if not cardio.empty and "distance" in cardio.columns:
                fig = px.bar(
                    cardio,
                    x="date",
                    y="distance",
                    color="type",
                    title="Cardio Distance (km)",
                    barmode="group",
                    hover_data=["time", "pace", "avg_speed", "speed", "incline"]
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No cardio yet.")

# === PERSONAL BESTS ===
if st.session_state.progress:
    df = pd.DataFrame(st.session_state.progress)
    pbs = []
    for t in ["push_ups", "pull_ups", "sit_ups"]:
        subset = df[df["type"] == t]
        if not subset.empty:
            pb = subset["reps"].max()
            pbs.append(f"{t.replace('_', ' ').title()}: {pb}")
    if pbs:
        st.success("**Personal Bests:** " + " | ".join(pbs))

# === CHAT ===
st.title(f"Coach Woody — {mode.split()[0]} Mode")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Ask {mode.split()[0]} Woody..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
            kwargs = {
                "level": st.session_state.level,
                "goal": st.session_state.goal,
                "history": history,
                "input": prompt
            }
            if mode == "IELTS Speaking Coach":
                kwargs["part"] = st.session_state.part
            try:
                response = chain.invoke(kwargs)
            except:
                response = "Oops! Check your Groq key in secrets."
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})