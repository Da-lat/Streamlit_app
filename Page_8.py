import streamlit as st
import requests
from datetime import datetime
from newsapi import NewsApiClient

st.markdown("# Worldwide news 📆")
st.sidebar.markdown("# Worldwide news 📆")
st.sidebar.markdown("Here you can select some categories and find the top headlines.")

newsapi = NewsApiClient(api_key='c97f53b4282741fc96b019c2c8a31f6f')

categories = ["Health", "Sports", "Business", "Entertainment", "General", "Science", "Technology"]
category = st.selectbox(label="Category",options=categories)
category = category.lower()

layout = st.selectbox(label="Select your layout of the news", options=["Detailed", "Title and URL"])

top_headlines = newsapi.get_top_headlines(category=category,
                                          language='en')

if layout == "Detailed":
    for article in top_headlines["articles"]:
        st.title(article["title"])
        st.text(f"{article['source']['name']} {datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y')}") 
        st.write(article["description"])
        st.link_button(label="Full Article", url=article["url"])
        try:
            st.image(article["urlToImage"])
        except:
            st.write("No image found or invalid format")

elif layout == "Title and URL":
    for article in top_headlines["articles"]:
        st.write(article["title"]) 
        st.link_button(label="Full Article", url=article["url"])






