import streamlit as st
import PyPDF2
from PyPDF2 import PdfReader
import google.generativeai as genai
import config
import pandas as pd
import matplotlib.pyplot as plt

# Gemini config
api_key = config.API_KEY
genai.configure(api_key=api_key)
model = genai.GenerativeModel(config.MODEL)

st.markdown("# CSV Analysis 📈")
st.sidebar.markdown("# CSV Analysis 📈")
st.sidebar.markdown("Here you can upload a CSV file and analyse the contents in a dataframe with visualisations.")

csv_upload = st.file_uploader("Upload a CSV file to analyse the contents", type="csv")

if csv_upload is not None:
    df = pd.read_csv(csv_upload)

    st.subheader("Data Preview")
    st.write(df.head(10))

    st.subheader("Data Summary")
    st.write(df.describe())

    st.subheader("Filter Data")
    columns = df.columns.tolist()
    selected_column = st.selectbox("Select column to filter by", columns)
    unique_values = df[selected_column].unique()
    selected_value = st.selectbox("Select value", unique_values)

    filtered_df = df[df[selected_column] == selected_value]
    st.write(filtered_df)

    st.subheader("Plot Data")
    x_column = st.selectbox("Select x-axis column", columns)
    y_column = st.selectbox("Select y-axis column", columns)

    if st.button("Generate Plot"):
        st.line_chart(filtered_df.set_index(x_column)[y_column])
else:
    st.write("Waiting on file upload...")