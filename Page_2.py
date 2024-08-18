import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import config

# Gemini config
api_key = config.API_KEY
genai.configure(api_key=api_key)
model = genai.GenerativeModel(config.MODEL)

# State initialisation
if 'pdf' not in st.session_state:
    st.session_state['pdf'] = False
    st.session_state['text'] = None
    st.session_state['summary'] = None
    st.session_state['answer'] = None

# Labelling
st.markdown("# PDF Analysis ❄️")
st.sidebar.markdown("# PDF Analysis ❄️")
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
        text = extract_text_from_pdf(uploaded_file)
        response = model.generate_content("Here is a PDF file, please summarize the file into bullet points and provide a summary, act as if you are studying and you went through the file and took notes to learn and extract the key points. Here is the file: " + text)
        st.session_state.text = text
        st.session_state.summary = response.text
        st.session_state.answer = None
except:
    st.error("Invalid file, please try again")

if st.session_state.summary:
    st.write(st.session_state.summary)
    st.download_button("Download your summarised PDF text", st.session_state.summary)


q = st.text_input("Do you have any questions about the PDF?")
button = st.button("Ask")

if q and st.session_state.text and button:
    response = model.generate_content(f"I am providing an extracted text passage from a pdf file, please search this information and answer this question. PDF text: {st.session_state.text}. Question: {q}")
    st.session_state.answer = response.text

if st.session_state.answer:
    st.write(st.session_state.answer)
