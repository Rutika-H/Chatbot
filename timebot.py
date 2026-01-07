import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import random
import json
import os
from datetime import datetime, timedelta
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Timebot", layout="centered")
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "chat_history.json"
QUIZ_DELAY_MINUTES = 10  # Quiz after 10 minutes

# ---------------- JSON HELPERS ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"interactions": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"interactions": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_interaction(query, response):
    data = load_data()
    data["interactions"].append({
        "query": query,
        "response": response,
        "time": datetime.now().isoformat()
    })
    save_data(data)

def get_random_query_from_history():
    data = load_data()
    interactions = data.get("interactions", [])
    if not interactions:
        return None
    return random.choice(interactions)["query"]

def generate_quiz():
    """Generate a quiz question from chat history"""
    quiz_source = get_random_query_from_history()
    
    if quiz_source is None:
        st.sidebar.warning("No chat history available to generate a quiz.")
        return
    
    quiz_prompt = (
        "Create a short conceptual quiz question based on the following topic. "
        "Do NOT give the answer.\n\n"
        f"Topic: {quiz_source}"
    )
    
    try:
        quiz_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=quiz_prompt)]
                )
            ]
        )
        st.session_state.quiz_topic = quiz_source
        st.session_state.quiz_question = quiz_response.text
        st.session_state.quiz_shown = True
        st.session_state.evaluation_result = None
    except Exception as e:
        st.sidebar.error(f"Error generating quiz: {e}")

# ---------------- INITIALIZE SESSION STATE ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "quiz_question" not in st.session_state:
    st.session_state.quiz_question = None
if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = None
if "last_message_time" not in st.session_state:
    st.session_state.last_message_time = None
if "quiz_shown" not in st.session_state:
    st.session_state.quiz_shown = False
if "evaluation_result" not in st.session_state:
    st.session_state.evaluation_result = None

# ---------------- MAIN UI ----------------
st.title("Timebot ⏱️")
st.caption(f"Quizzes you {QUIZ_DELAY_MINUTES} minutes after your last message!")

# Check if it's time to show quiz
if (st.session_state.last_message_time is not None 
    and not st.session_state.quiz_shown 
    and datetime.now() - st.session_state.last_message_time >= timedelta(minutes=QUIZ_DELAY_MINUTES)):
    generate_quiz()

# Display chat history
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask anything...")

if user_input:
    # Reset quiz state for new conversation
    st.session_state.last_message_time = datetime.now()
    st.session_state.quiz_shown = False
    st.session_state.quiz_question = None
    st.session_state.evaluation_result = None
    
    # Add user message
    st.session_state.chat.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        # Get Gemini response
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                )
            ]
        )
        reply = response.text

        # Add assistant message
        st.session_state.chat.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

        # Save to JSON
        save_interaction(user_input, reply)
    
    except Exception as e:
        st.error(f"Error: {e}")

# ---------------- TIMER DISPLAY ----------------
if st.session_state.last_message_time and not st.session_state.quiz_shown:
    time_elapsed = (datetime.now() - st.session_state.last_message_time).total_seconds()
    time_remaining = max(0, QUIZ_DELAY_MINUTES - time_elapsed)
    
    if time_remaining > 0:
        st.info(f"⏱️ Quiz will appear in {int(time_remaining)} minutes...")
        # Auto-refresh every minute to update timer
        time.sleep()
        st.rerun()

# ---------------- SIDEBAR ----------------
st.sidebar.header("💬 Saved Chat History")

if st.sidebar.button("Load saved chats"):
    data = load_data()
    if data["interactions"]:
        for item in data["interactions"]:
            st.sidebar.markdown(
                f"**Q:** {item['query']}\n\n"
                f"**A:** {item['response']}\n\n"
                f"⏱ {item['time']}\n---"
            )
    else:
        st.sidebar.info("No chat history yet!")

# ---------------- QUIZ FUNCTIONALITY ----------------
st.sidebar.divider()
st.sidebar.header("📝 Quiz Mode")

if st.sidebar.button("Generate Quiz Now"):
    generate_quiz()

if st.sidebar.button("Clear Quiz"):
    st.session_state.quiz_question = None
    st.session_state.quiz_topic = None
    st.session_state.quiz_shown = False
    st.session_state.evaluation_result = None
    st.rerun()

# Display quiz if one exists
if st.session_state.quiz_question:
    st.sidebar.markdown("### 🧠 Quiz Question")
    st.sidebar.markdown(st.session_state.quiz_question)
    
    # Answer input
    user_answer = st.sidebar.text_area(
        "Your answer:",
        key="quiz_answer_input",
        height=100
    )
    
    if st.sidebar.button("Submit Answer"):
        if user_answer.strip():
            with st.spinner("Evaluating your answer..."):
                evaluation_prompt = (
                    "You are an examiner.\n\n"
                    f"Topic: {st.session_state.quiz_topic}\n\n"
                    f"Question: {st.session_state.quiz_question}\n\n"
                    f"Student Answer: {user_answer}\n\n"
                    "Decide whether the answer is correct or incorrect. "
                    "Start your response with either 'Correct:' or 'Incorrect:' "
                    "and then give a brief explanation."
                )
                
                try:
                    evaluation_response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[types.Part(text=evaluation_prompt)]
                            )
                        ]
                    )
                    st.session_state.evaluation_result = evaluation_response.text
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Evaluation error: {e}")
        else:
            st.sidebar.warning("⚠️ Please enter an answer before submitting.")
    
    # Display evaluation result
    if st.session_state.evaluation_result:
        st.sidebar.divider()
        result_text = st.session_state.evaluation_result
        if result_text.lower().startswith("correct"):
            st.sidebar.success("### ✅ Evaluation Result")
        else:
            st.sidebar.error("### ❌ Evaluation Result")
        st.sidebar.markdown(st.session_state.evaluation_result)