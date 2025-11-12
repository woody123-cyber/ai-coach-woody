# app.py
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import cv2
import numpy as np
from PIL import Image
import plotly.express as px
import pandas as pd
from datetime import datetime

# === CONFIG ===
st.set_page_config(page_title="Coach Woody", page_icon="💪", layout="centered")

# === SECRETS ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === MODE TOGGLE ===
mode = st.sidebar.selectbox("Mode", ["Fitness Coach", "IELTS Speaking Coach"])

# === LLM ===
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.7)

# === PROMPTS ===
if mode == "Fitness Coach":
    system_prompt = """
    You are Coach Woody, a world-class fitness coach.
    Be fun, encouraging, and under 120 words.
    User level: {level}
    Goal: {goal}
    History: {history}
    User: {input}
    Coach Woody:
    """
else:
    system_prompt = """
    You are Coach Woody, an expert IELTS Speaking coach (Band 8+).
    Give feedback on fluency, vocab, grammar, pronunciation.
    Suggest improvements. Under 150 words.
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

# === SIDEBAR ===
with st.sidebar:
    st.header("Coach Woody")
    if mode == "Fitness Coach":
        st.session_state.level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
        st.session_state.goal = st.text_input("Goal", "Run a 5K")
        reps = st.number_input("Log Push-ups", min_value=0, value=0)
        if st.button("Log"):
            st.session_state.progress.append({"date": datetime.now().strftime("%Y-%m-%d"), "pushups": reps})
            st.success(f"Logged {reps} push-ups!")
    else:
        st.session_state.part = st.selectbox("IELTS Part", ["Part 1", "Part 2", "Part 3"])

    st.divider()
    if st.session_state.progress:
        df = pd.DataFrame(st.session_state.progress)
        fig = px.line(df, x="date", y="pushups", title="Push-up Progress")
        st.plotly_chart(fig, use_container_width=True)

# === PHOTO FORM CHECK ===
st.subheader("Upload Form Photo")
uploaded_file = st.file_uploader("Snap a push-up/squat", type=["jpg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Your form")
    
    # Edge detection feedback
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    feedback = "Great form! Keep core tight."
    if lines is not None and len(lines) < 5:
        feedback = "Warning: Your back might be sagging. Keep a straight line!"
    elif lines is not None and len(lines) > 15