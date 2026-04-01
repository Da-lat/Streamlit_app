import random
import re
from io import BytesIO

import requests
import streamlit as st
from PIL import Image, ImageFilter

MAX_GUESSES = 5
MAX_STRIKES = 3
BLUR_LEVELS = [25, 22, 15, 9, 3]

st.markdown("# Video Game Cover Guessing Game")
st.sidebar.markdown("# Video Game Cover Guessing Game")
st.sidebar.markdown("5 guesses per round. 3 strikes and game over.")


@st.cache_data(ttl=3000, show_spinner=False)
def get_access_token(client_id, client_secret):
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@st.cache_data(ttl=3600, show_spinner=False)
def get_game_candidates(client_id, token):
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}",
    }
    query = "fields id,name,cover; where cover != null & version_parent = null; sort rating_count desc; limit 500;"
    resp = requests.post("https://api.igdb.com/v4/games", headers=headers, data=query, timeout=25)
    resp.raise_for_status()
    return resp.json()


def get_image_id_for_cover(cover_id, headers):
    query = f"fields image_id; where id = {cover_id}; limit 1;"
    resp = requests.post("https://api.igdb.com/v4/covers", headers=headers, data=query, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    if not payload:
        return None
    return payload[0].get("image_id")


def fetch_random_cover_round(client_id, token):
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}",
    }
    candidates = get_game_candidates(client_id, token)
    random.shuffle(candidates)

    for game in candidates:
        name = game.get("name")
        cover_id = game.get("cover")
        if not name or not cover_id:
            continue

        image_id = get_image_id_for_cover(cover_id, headers)
        if not image_id:
            continue

        image_url = f"https://images.igdb.com/igdb/image/upload/t_1080p/{image_id}.jpg"
        image_resp = requests.get(image_url, timeout=25)
        if image_resp.status_code != 200:
            continue

        image = Image.open(BytesIO(image_resp.content)).convert("RGB")
        return {"name": name, "image": image}

    return None


def normalize_name(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def init_state():
    defaults = {
        "score": 0,
        "strikes": 0,
        "guesses_used": 0,
        "round_active": False,
        "target_name": "",
        "target_image": None,
        "round_message": "",
        "round_result": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

client_id = st.secrets.get("TWITCH_CLIENT_ID", "oni6voedqpsh3lucr3ivx6ow0z2ahz")
client_secret = st.secrets.get("TWITCH_CLIENT_SECRET", "qize3dxr9b0i503bpyhk8sqphlcvc0")

if not client_id or not client_secret:
    st.error("Missing Twitch credentials. Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in Streamlit secrets.")
    st.stop()

try:
    guess_token = get_access_token(client_id, client_secret)
    guess_options = sorted(
        {game.get("name") for game in get_game_candidates(client_id, guess_token) if game.get("name")}
    )
except Exception:
    guess_options = []


def start_new_round():
    try:
        token = get_access_token(client_id, client_secret)
        round_data = fetch_random_cover_round(client_id, token)
    except Exception as exc:
        st.error(f"Could not load game cover: {exc}")
        return

    if not round_data:
        st.error("Could not find a valid game cover. Try again.")
        return

    st.session_state["target_name"] = round_data["name"]
    st.session_state["target_image"] = round_data["image"]
    st.session_state["guesses_used"] = 0
    st.session_state["round_active"] = True
    st.session_state["round_message"] = ""
    st.session_state["round_result"] = ""


def reset_game():
    st.session_state["score"] = 0
    st.session_state["strikes"] = 0
    st.session_state["guesses_used"] = 0
    st.session_state["round_active"] = False
    st.session_state["target_name"] = ""
    st.session_state["target_image"] = None
    st.session_state["round_message"] = ""
    st.session_state["round_result"] = ""


status_cols = st.columns(3)
with status_cols[0]:
    st.metric("Score", st.session_state["score"])
with status_cols[1]:
    st.metric("Guesses Left", MAX_GUESSES - st.session_state["guesses_used"] if st.session_state["round_active"] else MAX_GUESSES)
with status_cols[2]:
    strike_marks = " ".join(["X" for _ in range(st.session_state["strikes"])]) or "None"
    st.markdown(f"**Strikes:** :red[{strike_marks}]")

if (
    st.session_state["strikes"] < MAX_STRIKES
    and not st.session_state["round_active"]
    and st.session_state["target_image"] is None
):
    start_new_round()

control_cols = st.columns(2)
with control_cols[0]:
    if (
        st.session_state["strikes"] < MAX_STRIKES
        and not st.session_state["round_active"]
        and st.session_state["target_image"] is not None
    ):
        if st.button("Next Cover", use_container_width=True):
            start_new_round()
            st.rerun()
with control_cols[1]:
    if st.button("Reset Game", use_container_width=True):
        reset_game()
        st.rerun()

if st.session_state["strikes"] >= MAX_STRIKES:
    st.error("Game over. You reached 3 strikes.")
    st.stop()

if st.session_state["round_message"]:
    st.info(st.session_state["round_message"])

if st.session_state["round_active"] and st.session_state["target_image"] is not None:
    blur_index = min(st.session_state["guesses_used"], MAX_GUESSES - 1)
    blur_radius = BLUR_LEVELS[blur_index]
    blurred = st.session_state["target_image"].filter(ImageFilter.GaussianBlur(blur_radius))

    st.caption(f"Attempt {st.session_state['guesses_used'] + 1} of {MAX_GUESSES} - blur radius: {blur_radius}")
    st.image(blurred, use_container_width=True)

    with st.form("guess_form", clear_on_submit=True):
        guess = st.selectbox("Choose your guess", [""] + guess_options, index=0)
        submitted = st.form_submit_button("Submit Guess", use_container_width=True)

    if submitted:
        if not guess.strip():
            st.warning("Select a game before submitting.")
            st.stop()

        if normalize_name(guess) == normalize_name(st.session_state["target_name"]):
            points = MAX_GUESSES - st.session_state["guesses_used"]
            st.session_state["score"] += points
            st.session_state["round_active"] = False
            st.session_state["round_result"] = "win"
            st.session_state["round_message"] = (
                f"Correct: {st.session_state['target_name']} (+{points} points)."
            )
            st.rerun()
        else:
            st.session_state["guesses_used"] += 1
            if st.session_state["guesses_used"] >= MAX_GUESSES:
                st.session_state["strikes"] += 1
                st.session_state["round_active"] = False
                st.session_state["round_result"] = "lose"
                st.session_state["round_message"] = (
                    f"Out of guesses. It was {st.session_state['target_name']}."
                )
            else:
                left = MAX_GUESSES - st.session_state["guesses_used"]
                st.session_state["round_message"] = f"Wrong guess. {left} guess(es) left."
            st.rerun()
elif st.session_state["target_image"] is not None:
    if st.session_state["round_result"] == "win":
        st.success(f"Correct: {st.session_state['target_name']}")
    elif st.session_state["round_result"] == "lose":
        st.error(f"Round lost: {st.session_state['target_name']}")
    st.caption("Full cover reveal")
    st.image(st.session_state["target_image"], use_container_width=True)
else:
    st.write("Loading first cover...")
