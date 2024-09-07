import streamlit as st
import requests
from datetime import datetime

st.markdown("# Timezone Converter 📆")
st.sidebar.markdown("# Timezone Converter 📆")
st.sidebar.markdown("Here you can convert timezones to your local time.")

timezones = requests.get("https://timeapi.io/api/timezone/availabletimezones")

st.write("### Select your source time and timezone ###")
col1, col2 = st.columns(2)

from_zone = col1.selectbox("Select your source timezone", timezones.json(), index=527)
from_date = col2.date_input("Select your source date", value="default_value_today")
from_time = col1.time_input("Select your source time", value="now")

st.write("***")
st.write("### Select your destination time and timezone ###")
to_zone = st.selectbox("Select your destination timezone", timezones.json(), index=358)

url = "https://timeapi.io/api/conversion/converttimezone"
# Set headers for content type and acceptance
headers = {
"Accept": "application/json",
"Content-Type": "application/json"
}
# Define the data to be sent in the request body
data = {
"fromTimeZone": f"{from_zone}",
"dateTime": f"{from_date} {from_time}",
"toTimeZone": f"{to_zone}",
"dstAmbiguity": ""
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    container = st.container(border=True)
    data = response.json()

    dt = datetime.fromisoformat(data['conversionResult']['dateTime'])
    formatted_date = dt.strftime("%d %B %Y")

    container.markdown(f"### :rainbow[Time]: {data['conversionResult']['time']} ###")
    container.markdown(f"### :rainbow[Date]: {formatted_date} ###")

    container.success("Conversion Successful")