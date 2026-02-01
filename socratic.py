import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import json
import os
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="SocraticBot", layout="centered")
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")

DATA_FILE = "chat_history.json"

# ---------------- SOCRATIC SYSTEM PROMPT ----------------
SOCRATIC_PROMPT = """You are a Socratic tutor. Your primary method is asking questions, not giving answers.

Core principles:
1. NEVER give direct answers unless explicitly asked "just tell me the answer"
2. Guide through questions that build on previous responses
3. Ask ONE focused question at a time
4. Wait for the student to think and respond
5. If they're stuck, ask a simpler question about fundamentals

Example flow:
Student: "What is photosynthesis?"
You: "Great question. Let's start here - what do you already know about how plants get energy?"

Student: "I don't know, they use sunlight?"
You: "Good start! So if plants use sunlight for energy, what do you think they might need to convert that sunlight into a usable form?"

Keep responses SHORT (2-3 sentences max). Be genuinely curious about their thinking."""

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

def build_messages_for_gemini():
    """
    Builds properly formatted message history for Gemini API
    """
    data = load_data()
    messages = []
    
    # Get last 20 interactions (10 exchanges)
    recent = data["interactions"][-20:]
    
    for item in recent:
        role = "user" if item["role"] == "user" else "model"
        messages.append({
            "role": role,
            "parts": [item["content"]]
        })
    
    return messages

# ---------------- UI ----------------
st.title("🧠 Socratic Tutor Bot")
st.caption("Learning through questions, not answers")

# Initialize session state
if "chat" not in st.session_state:
    st.session_state.chat = []

# Display chat history
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- USER INPUT ----------------
user_input = st.chat_input("Ask a question or explain your thinking...")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat.append({"role": "user", "content": user_input})
    
    # Save user message to history
    data = load_data()
    data["interactions"].append({
        "role": "user",
        "content": user_input,
        "time": datetime.now().isoformat()
    })
    save_data(data)
    
    # Build conversation with system prompt
    messages = build_messages_for_gemini()
    
    # Create chat with system instruction
    chat = model.start_chat(
        history=messages
    )
    
    # Generate response with system instruction as first message
    response = chat.send_message(
        f"{SOCRATIC_PROMPT}\n\nRespond to: {user_input}",
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=200,  # Force short responses
        )
    )
    
    reply = response.text.strip()
    
    # Display and save assistant response
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.chat.append({"role": "assistant", "content": reply})
    
    data["interactions"].append({
        "role": "assistant",
        "content": reply,
        "time": datetime.now().isoformat()
    })
    save_data(data)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("📜 Conversation History")
    
    if st.button("🔄 Load Full History"):
        data = load_data()
        for item in data["interactions"]:
            role_emoji = "👤" if item["role"] == "user" else "🤖"
            st.markdown(f"{role_emoji} **{item['role'].title()}:** {item['content']}")
            st.caption(f"⏱️ {item['time']}")
            st.divider()
    
    if st.button("🗑️ Clear History"):
        save_data({"interactions": []})
        st.session_state.chat = []
        st.rerun()