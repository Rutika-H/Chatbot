import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import os
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="SpacedRep", layout="centered")
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "chat_history.json"

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
        "level": 0,
        "last_reviewed": datetime.now().isoformat()
    })
    save_data(data)

# ---------------- SPACED REPETITION LOGIC ----------------
def get_interval_minutes(level):
    if level == 0:
        return 10
    elif level == 1:
        return 60
    elif level == 2:
        return 1440        # 1 day
    else:
        return 4320        # 3 days

def get_due_question():
    data = load_data()
    now = datetime.now()

    for item in data["interactions"]:
        last = datetime.fromisoformat(item["last_reviewed"])
        interval = get_interval_minutes(item["level"])
        if (now - last).total_seconds() >= interval * 60:
            return item
    return None

def update_level(question, correct):
    data = load_data()
    for item in data["interactions"]:
        if item["query"] == question:
            if correct:
                item["level"] = min(item["level"] + 1, 3)
            else:
                item["level"] = 0
            item["last_reviewed"] = datetime.now().isoformat()
            break
    save_data(data)

# ---------------- UI ----------------
st.title("SpacedRep Bot 🤖")
st.caption("Spaced Repetition Learning Bot")

if "chat" not in st.session_state:
    st.session_state.chat = []

if "quiz_question" not in st.session_state:
    st.session_state.quiz_question = None

if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = None

# Display chat
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- CHAT INPUT ----------------
user_input = st.chat_input("Ask anything...")
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

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
    st.session_state.chat.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)

    save_interaction(user_input, reply)

# ---------------- QUIZ MODE ----------------
st.sidebar.header(" Spaced Repetition Quiz")

if st.sidebar.button("Quiz me"):
    due_item = get_due_question()
    if due_item:
        quiz_prompt = (
            "Create a short conceptual quiz question based on the following topic. "
            "Do NOT give the answer.\n\n"
            f"Topic: {due_item['query']}"
        )

        quiz_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=quiz_prompt)]
                )
            ]
        )

        st.session_state.quiz_topic = due_item["query"]
        st.session_state.quiz_question = quiz_response.text
    else:
        st.sidebar.info("No questions due for review right now.")

# ---------------- QUIZ DISPLAY ----------------
if st.session_state.quiz_question:
    st.sidebar.markdown("### 📝 Quiz Question")
    st.sidebar.markdown(st.session_state.quiz_question)

    user_answer = st.sidebar.text_area("Your answer:")

    if st.sidebar.button("Submit answer"):
        evaluation_prompt = (
            "You are an examiner.\n\n"
            f"Topic: {st.session_state.quiz_topic}\n\n"
            f"Question: {st.session_state.quiz_question}\n\n"
            f"Student Answer: {user_answer}\n\n"
            "Decide whether the answer is correct or incorrect. "
            "Start your response with either 'Correct:' or 'Incorrect:' "
            "and then give a brief explanation."
        )

        evaluation_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=evaluation_prompt)]
                )
            ]
        )

        result_text = evaluation_response.text
        st.sidebar.markdown("### Evaluation")
        st.sidebar.markdown(result_text)

        is_correct = result_text.strip().startswith("Correct:")
        update_level(st.session_state.quiz_topic, is_correct)

# ---------------- HISTORY ----------------
st.sidebar.divider()
st.sidebar.header(" Saved Chat History")

if st.sidebar.button("Load saved chats"):
    data = load_data()
    for item in data["interactions"]:
        st.sidebar.markdown(
            f"**Q:** {item['query']}\n\n"
            f"**A:** {item['response']}\n\n"
            f"**Level:** {item['level']}\n"
            f"⏱ {item['last_reviewed']}\n---"
        )
