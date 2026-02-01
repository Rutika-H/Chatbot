import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import random
import json
import os
from datetime import datetime, timedelta
from collections import Counter
import time

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="🚀 SmartBot Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "chat_history.json"
STATS_FILE = "user_stats.json"
ACHIEVEMENTS_FILE = "achievements.json"

# ---------------- AI PERSONALITIES ----------------
PERSONALITIES = {
    "🎓 Professor": {
        "prompt": "You are a knowledgeable professor. Be educational, detailed, and use academic language. Include examples and references.",
        "emoji": "🎓"
    },
    "😄 Friendly Buddy": {
        "prompt": "You are a casual, friendly companion. Use simple language, emojis, and be encouraging. Keep it fun and light!",
        "emoji": "😄"
    },
    "🤖 Tech Expert": {
        "prompt": "You are a technical expert. Be precise, use technical terminology, and provide code examples when relevant.",
        "emoji": "🤖"
    },
    "🎭 Creative Writer": {
        "prompt": "You are a creative storyteller. Be imaginative, use vivid descriptions, metaphors, and engage emotionally.",
        "emoji": "🎭"
    },
    "🧘 Zen Master": {
        "prompt": "You are a calm, philosophical guide. Be thoughtful, ask reflective questions, and encourage mindfulness.",
        "emoji": "🧘"
    },
    "🎮 Gaming Buddy": {
        "prompt": "You are an enthusiastic gamer. Use gaming references, be energetic, and relate everything to games!",
        "emoji": "🎮"
    }
}

# ---------------- ACHIEVEMENTS ----------------
ACHIEVEMENTS = {
    "first_chat": {"name": "🎉 First Steps", "desc": "Had your first conversation", "points": 10},
    "chat_5": {"name": "💬 Chatty", "desc": "Had 5 conversations", "points": 25},
    "chat_25": {"name": "🗣️ Conversationalist", "desc": "Had 25 conversations", "points": 50},
    "chat_100": {"name": "🏆 Chat Master", "desc": "Had 100 conversations", "points": 100},
    "streak_3": {"name": "🔥 On Fire", "desc": "3-day streak", "points": 30},
    "streak_7": {"name": "🌟 Dedicated", "desc": "7-day streak", "points": 75},
    "quiz_master": {"name": "🧠 Quiz Master", "desc": "Scored 5 perfect quizzes", "points": 50},
    "night_owl": {"name": "🦉 Night Owl", "desc": "Chatted past midnight", "points": 15},
    "early_bird": {"name": "🌅 Early Bird", "desc": "Chatted before 6 AM", "points": 15},
    "topic_explorer": {"name": "🌍 Explorer", "desc": "Discussed 10+ different topics", "points": 40},
    "long_conversation": {"name": "📖 Deep Thinker", "desc": "Had a 20+ message conversation", "points": 35},
    "personality_switcher": {"name": "🎭 Shapeshifter", "desc": "Tried all AI personalities", "points": 60}
}

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

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {
            "total_messages": 0,
            "quiz_score": 0,
            "quiz_attempts": 0,
            "topics": [],
            "last_chat_date": None,
            "streak_days": 0,
            "personalities_used": [],
            "total_points": 0,
            "level": 1,
            "unlocked_achievements": []
        }
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return load_stats()

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def save_interaction(query, response, topic=None, personality=None):
    data = load_data()
    data["interactions"].append({
        "query": query,
        "response": response,
        "topic": topic,
        "personality": personality,
        "time": datetime.now().isoformat()
    })
    save_data(data)
    
    # Update stats
    stats = load_stats()
    stats["total_messages"] += 1
    
    if topic and topic not in stats["topics"]:
        stats["topics"].append(topic)
    
    if personality and personality not in stats["personalities_used"]:
        stats["personalities_used"].append(personality)
    
    # Update streak
    today = datetime.now().date()
    if stats["last_chat_date"]:
        last_date = datetime.fromisoformat(stats["last_chat_date"]).date()
        if (today - last_date).days == 1:
            stats["streak_days"] += 1
        elif (today - last_date).days > 1:
            stats["streak_days"] = 1
    else:
        stats["streak_days"] = 1
    
    stats["last_chat_date"] = datetime.now().isoformat()
    
    # Calculate level (every 100 points = 1 level)
    stats["level"] = 1 + (stats["total_points"] // 100)
    
    save_stats(stats)
    check_achievements()

def get_random_query_from_history():
    data = load_data()
    interactions = data.get("interactions", [])
    if not interactions:
        return None
    return random.choice(interactions)["query"]

def check_achievements():
    """Check and unlock achievements"""
    stats = load_stats()
    newly_unlocked = []
    
    achievements_to_check = {
        "first_chat": stats["total_messages"] >= 1,
        "chat_5": stats["total_messages"] >= 5,
        "chat_25": stats["total_messages"] >= 25,
        "chat_100": stats["total_messages"] >= 100,
        "streak_3": stats["streak_days"] >= 3,
        "streak_7": stats["streak_days"] >= 7,
        "quiz_master": stats.get("quiz_score", 0) >= 5,
        "topic_explorer": len(stats["topics"]) >= 10,
        "long_conversation": stats["total_messages"] >= 20,
        "personality_switcher": len(stats["personalities_used"]) >= len(PERSONALITIES)
    }
    
    # Time-based achievements
    hour = datetime.now().hour
    if hour >= 0 and hour < 6:
        achievements_to_check["early_bird"] = True
    if hour >= 23 or hour < 2:
        achievements_to_check["night_owl"] = True
    
    for ach_id, condition in achievements_to_check.items():
        if condition and ach_id not in stats["unlocked_achievements"]:
            stats["unlocked_achievements"].append(ach_id)
            stats["total_points"] += ACHIEVEMENTS[ach_id]["points"]
            newly_unlocked.append(ACHIEVEMENTS[ach_id]["name"])
    
    save_stats(stats)
    return newly_unlocked

def extract_topics_from_text(text):
    """Simple topic extraction using keywords"""
    topics = {
        "Science": ["science", "physics", "chemistry", "biology", "experiment"],
        "Technology": ["code", "programming", "computer", "ai", "software", "tech"],
        "Math": ["math", "calculate", "equation", "number", "algebra"],
        "History": ["history", "historical", "past", "ancient", "war"],
        "Art": ["art", "painting", "music", "creative", "design"],
        "Philosophy": ["philosophy", "meaning", "ethics", "existence"],
        "General": []
    }
    
    text_lower = text.lower()
    for topic, keywords in topics.items():
        if any(keyword in text_lower for keyword in keywords):
            return topic
    return "General"

# ---------------- SESSION STATE INIT ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "counter" not in st.session_state:
    st.session_state.counter = 0
if "quiz_question" not in st.session_state:
    st.session_state.quiz_question = None
if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = None
if "personality" not in st.session_state:
    st.session_state.personality = "😄 Friendly Buddy"
if "show_achievements" not in st.session_state:
    st.session_state.show_achievements = False
if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = "Normal"

# ---------------- HEADER ----------------
col1, col2, col3 = st.columns([2, 3, 2])

with col1:
    stats = load_stats()
    st.metric("🎯 Level", stats["level"])
    
with col2:
    st.title("🚀 SmartBot Pro")
    st.caption(f"Using personality: {st.session_state.personality}")

with col3:
    st.metric("⭐ Points", stats["total_points"])

# Progress bar to next level
progress = (stats["total_points"] % 100) / 100
st.progress(progress, text=f"Progress to Level {stats['level'] + 1}")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Settings & Stats")
    
    # Personality selector
    st.subheader("🎭 AI Personality")
    selected_personality = st.selectbox(
        "Choose AI personality:",
        list(PERSONALITIES.keys()),
        index=list(PERSONALITIES.keys()).index(st.session_state.personality)
    )
    if selected_personality != st.session_state.personality:
        st.session_state.personality = selected_personality
        st.success(f"Switched to {selected_personality}!")
    
    st.divider()
    
    # Conversation mode
    st.subheader("💬 Conversation Mode")
    mode = st.radio(
        "Select mode:",
        ["Normal", "Explain Like I'm 5", "Debate Mode", "Story Mode"],
        index=0
    )
    st.session_state.conversation_mode = mode
    
    st.divider()
    
    # Stats display
    st.subheader("📊 Your Stats")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("💬 Messages", stats["total_messages"])
        st.metric("🔥 Streak", f"{stats['streak_days']} days")
    with col_b:
        st.metric("🎯 Quiz Score", f"{stats.get('quiz_score', 0)}/{stats.get('quiz_attempts', 0)}")
        st.metric("🌍 Topics", len(stats["topics"]))
    
    # Show achievements button
    if st.button("🏆 View Achievements"):
        st.session_state.show_achievements = not st.session_state.show_achievements
    
    st.divider()
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    if st.button("🎲 Random Topic Suggestion"):
        topics = ["Explain quantum computing", "What is consciousness?", 
                 "How do black holes work?", "Tell me about ancient civilizations",
                 "Explain machine learning", "What is the meaning of life?"]
        st.info(f"💡 Try: {random.choice(topics)}")
    
    if st.button("📝 Generate Writing Prompt"):
        prompts = [
            "Write a story about a robot learning to feel emotions",
            "Describe a world where gravity works backwards",
            "Create a dialogue between past and future you",
            "Imagine a society where dreams are currency"
        ]
        st.info(f"✍️ {random.choice(prompts)}")
    
    st.divider()
    
    # Chat history
    st.subheader("💾 Chat History")
    if st.button("📜 Load History"):
        data = load_data()
        with st.expander("View Past Chats"):
            for item in data["interactions"][-10:]:  # Last 10
                st.markdown(f"**Q:** {item['query'][:50]}...")
                st.caption(f"⏱ {item['time']}")
                st.divider()
    
    if st.button("🗑️ Clear History"):
        save_data({"interactions": []})
        st.session_state.chat = []
        st.success("History cleared!")
        st.rerun()

# ---------------- ACHIEVEMENTS DISPLAY ----------------
if st.session_state.show_achievements:
    st.subheader("🏆 Achievements")
    
    cols = st.columns(3)
    for idx, (ach_id, ach_data) in enumerate(ACHIEVEMENTS.items()):
        with cols[idx % 3]:
            if ach_id in stats["unlocked_achievements"]:
                st.success(f"✅ {ach_data['name']}")
                st.caption(f"{ach_data['desc']} (+{ach_data['points']} pts)")
            else:
                st.info(f"🔒 {ach_data['name']}")
                st.caption(ach_data['desc'])
    
    st.divider()

# ---------------- MAIN CHAT ----------------
# Display chat history
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "topic" in msg and msg["topic"]:
            st.caption(f"🏷️ Topic: {msg['topic']}")

# ---------------- AUTO QUIZ EVERY 5 MESSAGES ----------------
if st.session_state.counter == 5:
    st.session_state.counter = 0
    quiz_source = get_random_query_from_history()
    
    if quiz_source:
        with st.sidebar:
            st.success("🎉 Auto-Quiz Time!")
            quiz_prompt = (
                "Create a short conceptual quiz question based on the following topic. "
                "Make it challenging but fair. Do NOT give the answer.\n\n"
                f"Topic: {quiz_source}"
            )
            
            quiz_response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[types.Content(role="user", parts=[types.Part(text=quiz_prompt)])]
            )
            
            st.session_state.quiz_topic = quiz_source
            st.session_state.quiz_question = quiz_response.text

# ---------------- USER INPUT ----------------
user_input = st.chat_input("💭 Ask anything or start a conversation...")

if user_input:
    st.session_state.counter += 1
    
    # Detect topic
    topic = extract_topics_from_text(user_input)
    
    # Add user message
    st.session_state.chat.append({"role": "user", "content": user_input, "topic": topic})
    with st.chat_message("user"):
        st.markdown(user_input)
        st.caption(f"🏷️ Topic: {topic}")
    
    # Build enhanced prompt with personality and mode
    personality_prompt = PERSONALITIES[st.session_state.personality]["prompt"]
    
    mode_instructions = {
        "Normal": "",
        "Explain Like I'm 5": "Explain this in the simplest way possible, as if talking to a 5-year-old child. Use simple words and fun examples.",
        "Debate Mode": "Take a thoughtful opposing viewpoint and present a counter-argument. Be respectful but challenge the premise.",
        "Story Mode": "Turn your response into an engaging story or narrative. Make it interesting and memorable."
    }
    
    full_prompt = f"{personality_prompt}\n\n{mode_instructions[st.session_state.conversation_mode]}\n\nUser: {user_input}"
    
    # Generate response with typing effect placeholder
    with st.chat_message("assistant"):
        with st.spinner(f"{PERSONALITIES[st.session_state.personality]['emoji']} Thinking..."):
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[types.Content(role="user", parts=[types.Part(text=full_prompt)])]
            )
            
            reply = response.text
            st.markdown(reply)
            st.caption(f"🏷️ Topic: {topic}")
    
    # Add assistant message
    st.session_state.chat.append({"role": "assistant", "content": reply, "topic": topic})
    
    # Save interaction
    save_interaction(user_input, reply, topic, st.session_state.personality)
    
    # Check for new achievements
    new_achievements = check_achievements()
    if new_achievements:
        for ach in new_achievements:
            st.balloons()
            st.success(f"🎉 Achievement Unlocked: {ach}")
            time.sleep(0.5)

# ---------------- QUIZ SECTION ----------------
st.sidebar.divider()
st.sidebar.header("🧠 Quiz Zone")

if st.sidebar.button("🎯 Generate Quiz"):
    quiz_source = get_random_query_from_history()
    
    if quiz_source is None:
        st.sidebar.warning("No chat history available. Chat more to unlock quizzes!")
    else:
        quiz_prompt = (
            "Create a challenging quiz question based on this topic. "
            "Make it thought-provoking. Do NOT give the answer.\n\n"
            f"Topic: {quiz_source}"
        )
        
        quiz_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[types.Content(role="user", parts=[types.Part(text=quiz_prompt)])]
        )
        
        st.session_state.quiz_topic = quiz_source
        st.session_state.quiz_question = quiz_response.text

if st.session_state.quiz_question:
    with st.sidebar:
        st.markdown("### 🎯 Quiz Question")
        st.info(st.session_state.quiz_question)
        
        user_answer = st.text_area("Your answer:", key="quiz_answer", height=100)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Submit"):
                if user_answer.strip():
                    evaluation_prompt = (
                        "You are an examiner.\n\n"
                        f"Topic: {st.session_state.quiz_topic}\n\n"
                        f"Question: {st.session_state.quiz_question}\n\n"
                        f"Student Answer: {user_answer}\n\n"
                        "Evaluate if the answer is correct. Be fair and encouraging. "
                        "Start with 'Correct:' or 'Incorrect:' then explain why."
                    )
                    
                    evaluation = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[types.Content(role="user", parts=[types.Part(text=evaluation_prompt)])]
                    )
                    
                    st.markdown("### 📊 Evaluation")
                    st.markdown(evaluation.text)
                    
                    # Update stats
                    stats = load_stats()
                    stats["quiz_attempts"] = stats.get("quiz_attempts", 0) + 1
                    if evaluation.text.lower().startswith("correct"):
                        stats["quiz_score"] = stats.get("quiz_score", 0) + 1
                        st.balloons()
                    save_stats(stats)
                    
                else:
                    st.warning("Please enter an answer!")
        
        with col2:
            if st.button("⏭️ Skip"):
                st.session_state.quiz_question = None
                st.rerun()

# ---------------- FOOTER ----------------
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"💬 Messages this session: {len(st.session_state.chat)}")
with col2:
    st.caption(f"🔥 Current streak: {stats['streak_days']} days")
with col3:
    st.caption(f"🎭 Personality: {st.session_state.personality}")