import google.generativeai as genai
import streamlit as st

import config
from gemini_utils import generate_text

st.markdown("# League Lane Matchup Analyzer")
st.sidebar.markdown("# League Lane Matchup Analyzer")
st.sidebar.markdown("Pick the lane champions, then generate a matchup strategy with Gemini.")

if "matchup_analysis" not in st.session_state:
    st.session_state.matchup_analysis = None

if "matchup_tldr" not in st.session_state:
    st.session_state.matchup_tldr = None

ROLE_POOLS = {
    "Top": "Aatrox,Akali,Ambessa,Aurora,Camille,Cassiopeia,Chogath,Darius,DrMundo,Fiora,Galio,Gangplank,Garen,Gnar,Gragas,Gwen,Heimerdinger,Illaoi,Irelia,Jax,Jayce,KSante,Kayle,Kennen,Kled,Malphite,Mordekaiser,Nasus,Nidalee,Olaf,Ornn,Pantheon,Poppy,Quinn,Renekton,Riven,Rumble,Ryze,Sett,Shen,Singed,Sion,Sylas,TahmKench,Teemo,Trundle,Tryndamere,Urgot,Varus,Vayne,Viktor,Vladimir,Volibear,Warwick,MonkeyKing,Yasuo,Yone,Yorick,Zac",
    "Jungle": "Amumu,Belveth,Brand,Briar,Darius,Diana,DrMundo,Ekko,Elise,Evelynn,Fiddlesticks,Gragas,Graves,Gwen,Hecarim,Ivern,JarvanIV,Jax,Karthus,Kayn,Khazix,Kindred,LeeSin,Lillia,MasterYi,Maokai,Naafiri,Nidalee,Nocturne,Nunu,Pantheon,Poppy,Qiyana,Rammus,RekSai,Rengar,Sejuani,Shaco,Shyvana,Skarner,Taliyah,Talon,Trundle,Udyr,Vi,Viego,Volibear,Warwick,MonkeyKing,XinZhao,Yorick,Zac,Zed,Zyra",
    "Middle": "Ahri,Akali,Akshan,Anivia,Annie,AurelionSol,Aurora,Azir,Brand,Cassiopeia,Chogath,Corki,Diana,Ekko,Fizz,Galio,Garen,Gragas,Hwei,Irelia,Jayce,Kassadin,Katarina,Kayle,Kennen,Leblanc,Lissandra,Lux,Malphite,Malzahar,Mel,Naafiri,Neeko,Orianna,Pantheon,Qiyana,Quinn,Ryze,Smolder,Swain,Sylas,Syndra,Taliyah,Talon,Tristana,TwistedFate,Veigar,Velkoz,Vex,Viktor,Vladimir,Xerath,Yasuo,Yone,Zed,Ziggs,Zoe",
    "Bottom": "Aphelios,Ashe,Caitlyn,Corki,Draven,Ezreal,Hwei,Jhin,Jinx,Kaisa,Kalista,KogMaw,Lucian,Mel,MissFortune,Nilah,Samira,Seraphine,Sivir,Smolder,Swain,Tristana,Twitch,Varus,Vayne,Xayah,Yasuo,Zeri,Ziggs",
    "Support": "Alistar,Annie,Bard,Blitzcrank,Brand,Braum,Elise,Fiddlesticks,Galio,Gragas,Hwei,Janna,Karma,Leona,Lulu,Lux,Maokai,Mel,Milio,Morgana,Nami,Nautilus,Neeko,Pantheon,Poppy,Pyke,Rakan,Rell,Renata,Senna,Seraphine,Shaco,Shen,Sona,Soraka,Swain,Sylas,TahmKench,Taric,Thresh,Velkoz,Xerath,Yuumi,Zilean,Zoe,Zyra",
}


def parse_pool(csv_names):
    return sorted({name.strip() for name in csv_names.split(",") if name.strip()})


ROLE_OPTIONS = {role: parse_pool(pool) for role, pool in ROLE_POOLS.items()}

genai.configure(api_key=config.API_KEY)


def analyze_matchup(role, selections):
    if role in {"Bottom", "Support"}:
        prompt = f"""
You are a high-level League of Legends coach.

Analyze this duo lane matchup and provide a detailed plan to win lane and convert it into a game win.

Lane focus role: {role}
Your team duo:
- Bottom: {selections["your_bottom"]}
- Support: {selections["your_support"]}

Enemy team duo:
- Bottom: {selections["enemy_bottom"]}
- Support: {selections["enemy_support"]}

Structure the answer with these sections:
1. Matchup overview
2. Levels 1-3 plan
3. Trading patterns and ability usage
4. Wave control and recall timings
5. Vision, jungle interaction, and gank setup
6. Key item and summoner spell timings
7. Biggest mistakes to avoid
8. How to transition a lane lead into winning the game

Be specific, practical, and matchup-focused. Do not stay generic.
"""
    else:
        prompt = f"""
You are a high-level League of Legends coach.

Analyze this lane matchup and provide a detailed plan to win lane and convert it into a game win.

Lane role: {role}
Your champion: {selections["your_champion"]}
Opponent champion: {selections["enemy_champion"]}

Structure the answer with these sections:
1. Matchup overview
2. Levels 1-3 plan
3. Trading patterns and ability usage
4. Wave control and recall timings
5. Vision, jungle interaction, and gank setup
6. Key item and summoner spell timings
7. Biggest mistakes to avoid
8. How to transition a lane lead into winning the game

Be specific, practical, and matchup-focused. Do not stay generic.
"""

    return generate_text(prompt)


def summarize_matchup_for_pregame(analysis):
    prompt = f"""
You are helping a League of Legends player who is already in champion select or loading screen.

Summarize the analysis below into a very short pre-game cheat sheet.

Rules:
- Keep it concise and scannable.
- Use bullet points only.
- Focus only on the highest-value actions before and during early lane.
- Include: win condition, levels 1-3 plan, trading pattern, wave tip, biggest danger, and first key item/spell timing.
- Maximum 6 bullets.
- Each bullet should be short.

Analysis:
{analysis}
"""

    return generate_text(prompt)


def duo_lane_selector(selected_role):
    is_bottom_focus = selected_role == "Bottom"
    your_primary_label = "Your Bottom" if is_bottom_focus else "Your Support"
    your_secondary_label = "Your Support" if is_bottom_focus else "Your Bottom"
    enemy_primary_label = "Enemy Bottom"
    enemy_secondary_label = "Enemy Support"

    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown("### Your Side")
        your_bottom = st.selectbox(
            your_primary_label if is_bottom_focus else your_secondary_label,
            [""] + ROLE_OPTIONS["Bottom"],
            format_func=lambda value: "Select champion" if value == "" else value,
            key=f"{selected_role}_your_bottom",
        )
        your_support = st.selectbox(
            your_secondary_label if is_bottom_focus else your_primary_label,
            [""] + ROLE_OPTIONS["Support"],
            format_func=lambda value: "Select champion" if value == "" else value,
            key=f"{selected_role}_your_support",
        )

    with right_col:
        st.markdown("### Enemy Side")
        enemy_bottom = st.selectbox(
            enemy_primary_label,
            [""] + ROLE_OPTIONS["Bottom"],
            format_func=lambda value: "Select champion" if value == "" else value,
            key=f"{selected_role}_enemy_bottom",
        )
        enemy_support = st.selectbox(
            enemy_secondary_label,
            [""] + ROLE_OPTIONS["Support"],
            format_func=lambda value: "Select champion" if value == "" else value,
            key=f"{selected_role}_enemy_support",
        )

    return {
        "your_bottom": your_bottom,
        "your_support": your_support,
        "enemy_bottom": enemy_bottom,
        "enemy_support": enemy_support,
    }


def solo_lane_selector(selected_role):
    options = ROLE_OPTIONS[selected_role]
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("### Your Side")
        your_champion = st.selectbox(
            "Your Champion",
            [""] + options,
            format_func=lambda value: "Select champion" if value == "" else value,
            key=f"{selected_role}_your_champion",
        )

    with right_col:
        st.markdown("### Enemy Side")
        enemy_champion = st.selectbox(
            "Opponent Champion",
            [""] + options,
            format_func=lambda value: "Select champion" if value == "" else value,
            key=f"{selected_role}_enemy_champion",
        )

    return {
        "your_champion": your_champion,
        "enemy_champion": enemy_champion,
    }


def all_fields_filled(selections):
    return all(value.strip() for value in selections.values())


selected_role = st.selectbox(
    "Select role",
    ["Top", "Jungle", "Middle", "Bottom", "Support"],
)

st.write("")
if selected_role in {"Bottom", "Support"}:
    st.caption("Bot lane roles use full duo-lane inputs on both sides.")
    current_selections = duo_lane_selector(selected_role)
else:
    current_selections = solo_lane_selector(selected_role)

st.write("")
if st.button("Analyse", use_container_width=True):
    if not all_fields_filled(current_selections):
        st.warning("Fill in every champion dropdown before running the analysis.")
    else:
        with st.spinner("Analyzing matchup with Gemini..."):
            try:
                analysis = analyze_matchup(selected_role, current_selections)
            except Exception as exc:
                st.error(f"Gemini request failed: {exc}")
            else:
                st.session_state.matchup_analysis = analysis
                st.session_state.matchup_tldr = None

if st.session_state.matchup_analysis:
    st.markdown("## Strategy")
    st.write(st.session_state.matchup_analysis)

    if st.button("TL:DR", use_container_width=True):
        with st.spinner("Summarizing the key points for pre-game..."):
            try:
                st.session_state.matchup_tldr = summarize_matchup_for_pregame(
                    st.session_state.matchup_analysis
                )
            except Exception as exc:
                st.error(f"Gemini request failed: {exc}")

if st.session_state.matchup_tldr:
    st.markdown("## TL:DR")
    st.write(st.session_state.matchup_tldr)
