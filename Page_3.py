import requests
from bs4 import BeautifulSoup 
import streamlit as st
import config
import google.generativeai as genai
import time
from gemini_utils import generate_text

# Gemini config
api_key = config.API_KEY
genai.configure(api_key=api_key)

st.markdown("# URL Analysis 💻")
st.sidebar.markdown("# URL Analysis 💻")
st.sidebar.markdown("Here you can paste a URL with text content and analyse the text into key points to save time and make it more readable.")

url = st.text_input("Enter the URL of the webpage you want to analyse:")
output= ""
text = ""

button = st.button("Analyse")

try:
    if url and button:
        res = requests.get(url)
        html_page = res.content
        soup = BeautifulSoup(html_page, 'html.parser')
        text = soup.find_all(text=True)   

        output = ''
        blacklist = [
            '[document]',
            'noscript',
            'header',
            'html',
            'meta',
            'head', 
            'input',
            'script',
            'nav',
            'footer',
            'style',
        ]

        for t in text:
            if t.parent.name not in blacklist:
                output += '{} '.format(t) 

except:
    st.error("Invalid URL")

if output:
    with st.spinner('Scraping the URL and analysing'):
        time.sleep(5)
    st.write(
        generate_text(
            "Here is a passage of text extracted from a URL, it might contain images, titles and other metadata. please summarize the main bodies of text into bullet points and provide a summary of the overall message and theming in this article, act as if you are studying and you read through this passage and took notes to learn and extract the key points. Here is the passage: "
            + output,
        )
    )
