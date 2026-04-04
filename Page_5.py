import streamlit as st
import google.generativeai as genai
import config
import time
from gemini_utils import generate_text

# Gemini config
api_key = config.API_KEY
genai.configure(api_key=api_key)

st.markdown("# Text Analysis 🔤")
st.sidebar.markdown("# Text Analysis 🔤")
st.sidebar.markdown("Here you can paste text and analyse it into key points to save time and make it more readable.")

text = st.text_area("Enter the text you want to analyse:")
button = st.button("Analyse")

if text and button:
    with st.spinner('Processing your text...'):
        time.sleep(5)
    st.write(
        generate_text(
            "Here is a passage of text, please summarize the transript into bullet points and provide a summary, act as if you are studying and you read through this passage and took notes to learn and extract the key points. Here is the passage: "
            + text,
        )
    )
