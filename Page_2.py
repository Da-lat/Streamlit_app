import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import config
import time

# Gemini config
api_key = config.API_KEY
genai.configure(api_key=api_key)
model = genai.GenerativeModel(config.MODEL)

# State initialisation
if 'pdf' not in st.session_state:
    st.session_state['pdf'] = False
    st.session_state['pdf_text'] = None
    st.session_state['pdf_summary'] = None
    st.session_state.pdf_answer = []
    st.session_state['pdf_q'] = []

# Labelling
st.markdown("# PDF Analysis 📄")
st.sidebar.markdown("# PDF Analysis 📄")
st.sidebar.markdown("Here you can upload a PDF file and analyse the text contents into key points to save time and make it more readable.")

def extract_text_from_pdf(pdf): 
    pdf_reader = PdfReader(pdf) 
    return ''.join(page.extract_text() for page in pdf_reader.pages)

def change_state():
    st.success("File uploaded successfully! Click analyse when you are ready.")
    st.session_state['pdf'] = True

uploaded_file = st.file_uploader("Upload a PDF file to analyse the text contents", type="pdf")

if uploaded_file:
    change_state()

button = st.button("Analyse")

# creating a pdf file object, extacts text and modifies the state
try:
    if uploaded_file and button and st.session_state.pdf == True:
        with st.spinner('Wait for it...'):
            time.sleep(5)
        text = extract_text_from_pdf(uploaded_file)
        response = model.generate_content("Here is a PDF file, please summarize the file into bullet points and provide a summary, act as if you are studying and you went through the file and took notes to learn and extract the key points. Here is the file: " + text)
        st.session_state.pdf_text = text
        st.session_state.pdf_summary = response.text
        st.session_state.pdf_answer = []
except:
    st.error("Invalid file, please try again")

if st.session_state.pdf_summary:
    st.write(st.session_state.pdf_summary)
    st.download_button("Download your summarised PDF text", st.session_state.pdf_summary, file_name="PDF_summary.txt")

q = st.chat_input("Do you have any questions about the PDF?")
messages = st.container()

if q and st.session_state.pdf_text:
    response = model.generate_content(f"I am providing an extracted text passage from a pdf file, please search this information and answer this question. PDF text: {st.session_state.pdf_text}. Question: {q}")
    st.session_state.pdf_answer.append({"role": "user", "content":q})  
    st.session_state.pdf_answer.append({"role": "assistant", "content": response.text})

if st.session_state.pdf_answer:
    for message in st.session_state.pdf_answer:
        with messages.chat_message(message["role"]):
            st.write(message["content"])