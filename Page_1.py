import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re
from youtube_transcript_api.formatters import TextFormatter
import config
import google.generativeai as genai
import PyPDF2


# Gemini config
api_key = config.API_KEY
genai.configure(api_key=api_key)
model = genai.GenerativeModel(config.MODEL)

st.set_page_config(
        page_title="Youtube Video Analysis",
        page_icon="🎈",
)

st.sidebar.markdown("# Youtube Video Analysis 🎈")
st.sidebar.markdown("Here you can upload a Youtube URL and analyse the transcript into key points to save time and make it more readable.")
st.title("Youtube Video Analysis Tool 🎈")

yt_id = 0
transcript_str = ""

yt_video = st.text_input("Enter the URL of the youtube video you want to analyse:")

if yt_video:
    yt_id = re.search(r"v=([^&]+)", yt_video).group(1)

button = st.button("Analyse")

if yt_id != 0 and button:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(yt_id)
    except:
        transcript = None
        st.error("The youtube video you entered is invalid, it's possible that the video does not have a transcript available or the URL is incorrect.")
    if transcript: 
        transcript_str = ""   
        for item in transcript:
            transcript_str = transcript_str + item['text'] + " "

        # st.write(transcript_str)
    

if transcript_str:
    response = model.generate_content("Here is a youtube transcript, please summarize the transript into bullet points and provide a summary, act as if you are studying and you went through thr video and took notes to learn and extract the key points. Here is the transcript: " + transcript_str)
    st.write(response.text)


# pdf_button = st.button("Click here If you would like to analyze a PDF file instead")

# if pdf_button:
#     st.switch_page("Page_2.py")