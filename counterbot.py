import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import random
import json
import os
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="CounterBot", layout="centered")
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
        # File exists but is empty or corrupted
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
#----------QUIZ JSON FUNCTION--------
def get_random_query_from_history():
    data = load_data()
    interactions = data.get("interactions", [])

    if not interactions:
        return None

    return random.choice(interactions)["query"]

# ---------------- UI ----------------
st.title("Counterbot 🤖")
st.caption("Quizzes you every 5 interactions!")

if "chat" not in st.session_state:
    st.session_state.chat = []

if "quiz_question" not in st.session_state:
    st.session_state.quiz_question = None

if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = None

# Display current session chat
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask anything...")
if user_input:
    if "counter" not in st.session_state:
        st.session_state.counter = 0
    st.session_state.counter += 1
    if st.session_state.counter == 5:
        st.session_state.counter = 0
        quiz_source = get_random_query_from_history()

        if quiz_source is None:
            st.sidebar.warning("No chat history available to generate a quiz.")
        else:
            quiz_prompt = (
                "Create a short conceptual quiz question based on the following topic. "
                "Do NOT give the answer.\n\n"
                f"Topic: {quiz_source}"
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

            st.session_state.quiz_topic = quiz_source
            st.session_state.quiz_question = quiz_response.text
        if st.session_state.quiz_question:
            st.sidebar.markdown("### 🧠 Quiz Question")
            st.sidebar.markdown(st.session_state.quiz_question)

            user_answer = st.sidebar.text_area(
                "Your answer:",
                key="quiz_answer"
            )

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

                st.sidebar.markdown("### Evaluation")
                st.sidebar.markdown(evaluation_response.text)


if user_input:
    # User message
    st.session_state.chat.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)


    # Gemini response
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

    # Assistant message
    st.session_state.chat.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

    # Save to JSON
    save_interaction(user_input, reply)

# ---------------- SIDEBAR ----------------
st.sidebar.header("Saved Chat History")

if st.sidebar.button("Load saved chats"):
    data = load_data()
    for item in data["interactions"]:
        st.sidebar.markdown(
            f"**Q:** {item['query']}\n\n"
            f"**A:** {item['response']}\n\n"
            f"⏱ {item['time']}\n---"
        )
# --------------QUIZ FUNCTIONALITY---------
st.sidebar.divider()
st.sidebar.header("📝 Quiz Mode")

if st.sidebar.button("Quiz me"):
    quiz_source = get_random_query_from_history()

    if quiz_source is None:
        st.sidebar.warning("No chat history available to generate a quiz.")
    else:
        quiz_prompt = (
            "Create a short conceptual quiz question based on the following topic. "
            "Do NOT give the answer.\n\n"
            f"Topic: {quiz_source}"
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

        st.session_state.quiz_topic = quiz_source
        st.session_state.quiz_question = quiz_response.text
if st.session_state.quiz_question:
    st.sidebar.markdown("### 🧠 Quiz Question")
    st.sidebar.markdown(st.session_state.quiz_question)

    user_answer = st.sidebar.text_area(
        "Your answer:",
        key="quiz_answer"
    )

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

        st.sidebar.markdown("### Evaluation")
        st.sidebar.markdown(evaluation_response.text)