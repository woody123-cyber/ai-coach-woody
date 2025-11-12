# app.py
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# === YOUR SECRET KEY GOES HERE ===
# We'll get this in Step 4

# === The AI Brain ===
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=st.secrets["GROQ_API_KEY"], temperature=0.7)

# === What the Coach Says ===
template = """
You are Coach Woody, a friendly fitness coach.
The user is a beginner learning push-ups.
Be kind, clear, and fun. Answer in 2-3 sentences.

User said: {input}
Previous chat: {history}

Coach Alex:
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | llm | StrOutputParser()

# === The Chat App ===
st.title("Coach Alex – Your Push-Up Buddy")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hi! I'm Coach Alex. How many push-ups can you do right now?"})

# Show old messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get new message
if user_input := st.chat_input("Type here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            response = chain.invoke({"input": user_input, "history": history})
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})