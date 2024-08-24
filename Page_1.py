import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re
from youtube_transcript_api.formatters import TextFormatter
import config
import google.generativeai as genai
import PyPDF2
import time

# Gemini config
api_key = config.API_KEY
genai.configure(api_key=api_key)
model = genai.GenerativeModel(config.MODEL)

st.set_page_config(
        page_title="Youtube Video Analysis",
        page_icon="🎈",
)

# State initialisation
if 'video' not in st.session_state:
    st.session_state['video'] = False
    st.session_state['yt_text'] = None
    st.session_state['yt_summary'] = None
    st.session_state.yt_answer = []
    st.session_state['yt_q'] = []

# Labelling
st.sidebar.markdown("# Youtube Video Analysis 🎈")
st.sidebar.markdown("Here you can upload a Youtube URL and analyse the transcript into key points to save time and make it more readable.")
st.title("Youtube Video Analysis Tool 🎈")

def change_state():
    """
    Updates the session state to indicate that a video has been selected.

    This function is called when the user enters a YouTube video URL.
    It sets the 'video' key in the session state to True.
    """
    st.session_state['video'] = True

yt_id = 0
transcript_str = ""

yt_video = st.text_input("Enter the URL of the youtube video you want to analyse:", on_change=change_state)

# Extract video ID from YouTube URL
if yt_video:
    yt_id = re.search(r"v=([^&]+)", yt_video).group(1)

button = st.button("Analyse")

# Extract transcript and generate string, send to gemini and summarise, also modifies the state
if yt_id != 0 and button and st.session_state.video == True:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(yt_id)
        st.success("Transcript extracted successfully!")
    except Exception as e:
        print(e)
        transcript = None
        st.error("The youtube video you entered is invalid, it's possible that the video does not have a transcript available or the URL is incorrect.")
    if transcript: 
        with st.spinner('Analysing the transcript...'):
            time.sleep(5)
        transcript_str = ""   
        for item in transcript:
            transcript_str = transcript_str + item['text'] + " "
        
    if transcript_str:
        response = model.generate_content("Here is a youtube transcript, please summarize the transript into bullet points and provide a summary, act as if you are studying and you went through thr video and took notes to learn and extract the key points. Here is the transcript: " + transcript_str)
        st.session_state.yt_text = transcript_str
        st.session_state.yt_summary = response.text
        st.session_state.yt_answer = []

if st.session_state.yt_summary:
    st.write(st.session_state.yt_summary)
    st.download_button("Download your summarised youtube video text", st.session_state.yt_summary, file_name="youtube_summary.txt")

q = st.chat_input("Do you have any questions about the youtube video?")
messages = st.container()

if q and st.session_state.yt_text:
    response = model.generate_content(f"I am providing an extracted text passage from a youtube transcript, please search this information and answer this question. Youtube transcript: {st.session_state.yt_text}. Question: {q}")
    st.session_state.yt_answer.append({"role": "user", "content":q})  
    st.session_state.yt_answer.append({"role": "assistant", "content": response.text})

if st.session_state.yt_answer:
    for message in st.session_state.yt_answer:
        with messages.chat_message(message["role"]):
            st.write(message["content"])


st.write("")
st.write("***")
st.write("")
# Time saver calc
st.write("### How much time did you save by watching youtube at a higher speed? ###")
col1, col2 = st.columns(2)
hours = col1.selectbox("Hours", options=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], index=0)
mins = col2.selectbox("Minutes", options=list(map(str, range(0, 61))))
yt_playback = st.select_slider("What is your playback speed?", options=["1","1.25", "1.5", "1.75", "2", "3"], value="1")
yt_length = (int(hours) * 60) + int(mins)
if hours and mins and yt_playback:
    time_saved = yt_length - (yt_length / float(yt_playback))
    if time_saved > 0:
        st.success(f"You saved {round(time_saved)} minutes which is {round(time_saved / yt_length * 100)}% of the original length of the video.")
    else:
        st.error(f"You saved 0 minutes! Please use the options to select Hours, minutes and playback speed.")