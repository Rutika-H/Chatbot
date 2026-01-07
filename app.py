import streamlit as st 
from google import genai
from google.genai import types 
from dotenv import load_dotenv 
import os

st.title("ChatGPT-like clone")

# Set OpenAI API key from Streamlit secrets
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

#Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

#Display assistant response in chat message container
    
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents= [prompt]
           )
        with st.chat_message("assistant"):
            st.markdown(response.text)  #Added response.text as only response is metadata, not just a string
       
    st.session_state.messages.append({"role": "assistant", "content": response.text})