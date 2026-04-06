import streamlit as st

API_KEY = str(st.secrets["API_KEY"]).strip()
RIOT_API_KEY = str(st.secrets["RIOT_API_KEY"]).strip()
MODEL = "gemini-2.5-flash"
