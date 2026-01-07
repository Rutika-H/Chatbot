# 🤖 LLM-Based Chatbot Applications

This repository contains three Python-based chatbot applications built using a Large Language Model (LLM).  
Each chatbot explores a different concept such as stateless interaction, persistent chat memory, and quiz generation based on user behavior or time.

---

##  Project Overview

### 📄 app.py — Basic LLM Chatbot
`app.py` implements a simple chatbot where users can ask questions to the AI and receive answers in real time.

**Features:**
- Direct question–answer interaction with the AI
- Lightweight and easy to run
- No additional logic or storage involved

**Limitation:**
- Chat history is **not stored**
- All conversations are lost when the app is refreshed or restarted

---

### 📄 counterbot.py — Chatbot with Memory and Quiz Generation
`counterbot.py` enhances the basic chatbot by saving chat history locally and tracking user queries.

**Features:**
- Stores chat history locally
- Counts the number of user queries
- Generates a **quiz after every 5 questions**
- Quiz is based on the user’s previous queries, making it contextual and personalized

---

### 📄 timebot.py — Time-Based Quiz Chatbot
`timebot.py` introduces a time-based learning mechanism while also storing chat history locally.

**Features:**
- Saves all chat interactions locally
- After a query is asked, the bot waits for **10 minutes**
- Generates a quiz related to that specific query after the time delay
- Encourages delayed recall and learning reinforcement

---

## ⚙️ Setup Instructions

Follow the steps below to run any of the chatbot applications.

---

### 1. Create and Activate a Virtual Environment

```bash
python -m venv venv
```
Activate it
```bash
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```
### 2.Install required libraries
Add requiremnets.txt to your project folder and run 
```bash
pip install -r requirements.txt
```
### 3.Add Gemini API key
Create a .streamlit folder under the project and add secrets.toml, add the following
```toml
GEMINI_API_KEY = "your_api_key_here"
```
### 4.Run the application
```bash
streamlit run project_name.py
```





