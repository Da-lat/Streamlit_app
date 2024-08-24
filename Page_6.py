import streamlit as st
import random
import requests
import json
import pprint as p
import IPython
from requests import post
from PIL import Image, ImageFilter
from io import BytesIO

if "cover" not in st.session_state:
    st.session_state['cover'] = None

st.markdown("# Experimental ")
st.sidebar.markdown("# Experimental ")
st.sidebar.markdown("Experimental")

# IGDB API config

if st.session_state['cover'] == None:
    CLIENT_ID = "oni6voedqpsh3lucr3ivx6ow0z2ahz"
    CLIENT_SECRET = "qize3dxr9b0i503bpyhk8sqphlcvc0"
    Bearer = "3dlmcu4xnou3s5q995rjph0jhfw4sd"

    r = requests.post(f'https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=client_credentials')

    headers = {"Client-ID" : CLIENT_ID, 
            "Authorization": "Bearer" + " " + r.json()['access_token']}


# Get Actual Cover image ID
def get_cover():
    random_cover_request = requests.post(f"https://api.igdb.com/v4/covers", headers=headers, data=f"fields alpha_channel,animated,checksum,game,game_localization,height,image_id,url,width; limit 1; where id = {random_game_id};")
    game_cover = random_cover_request.json()
    try: 
        game_cover_id = game_cover[0]['image_id']
        return game_cover_id
    except:
        game_cover_id = None
        get_cover()

# game_cover_id
if st.session_state['cover'] is None:
    game_cover_request = requests.post(f"https://api.igdb.com/v4/games", headers=headers, data=f"fields name, screenshots.*, url, rating,cover; limit 1; where id = {random.randint(0, 40000)};")
    game_cover = game_cover_request.json()
# game_cover
    random_game_id = game_cover[0]['cover']
    game_cover_id = get_cover()
    url = f"https://images.igdb.com/igdb/image/upload/t_1080p/{game_cover_id}.jpg"
    response = requests.get(url)

    if response.status_code == 200 and game_cover_id and st.session_state['cover'] is None:
        img = Image.open(BytesIO(response.content))
        blur_level = st.selectbox('Select blur level', ['30', '20', '15', '10', '0'])
        blurred_img = img.filter(ImageFilter.GaussianBlur(int(blur_level)))
        st.image(blurred_img, use_column_width="auto", output_format="auto")
        st.session_state['cover'] = img
    else:
        st.error(f"Error downloading image: {response.status_code} {response.reason}")
else: 
    img = st.session_state['cover']
    blur_level = st.selectbox('Select blur level', ['30', '20', '15', '10', '0'])
    blurred_img = img.filter(ImageFilter.GaussianBlur(int(blur_level)))
    st.image(blurred_img, use_column_width="auto", output_format="auto")
