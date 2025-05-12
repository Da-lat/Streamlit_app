import streamlit as st
import requests
import random
from PIL import Image
import requests
from io import BytesIO

st.markdown("# Random Champs 🎮")
st.sidebar.markdown("# League of Legends Champion Generator 🎮")
st.sidebar.markdown("Here you can generate random champions in each role.")

# Initialize session state
if 'selections' not in st.session_state:
    st.session_state.selections = {}

top = "Aatrox,Akali,Ambessa,Aurora,Camille,Cassiopeia,Chogath,Darius,DrMundo,Fiora,Galio,Gangplank,Garen,Gnar,Gragas,Gwen,Heimerdinger,Illaoi,Irelia,Jax,Jayce,KSante,Kayle,Kennen,Kled,Malphite,Mordekaiser,Nasus,Nidalee,Olaf,Ornn,Pantheon,Poppy,Quinn,Renekton,Riven,Rumble,Ryze,Sett,Shen,Singed,Sion,Sylas,TahmKench,Teemo,Trundle,Tryndamere,Urgot,Varus,Vayne,Viktor,Vladimir,Volibear,Warwick,MonkeyKing,Yasuo,Yone,Yorick,Zac"
jung = "Amumu,Belveth,Brand,Briar,Darius,Diana,DrMundo,Ekko,Elise,Evelynn,Fiddlesticks,Gragas,Graves,Gwen,Hecarim,Ivern,JarvanIV,Jax,Karthus,Kayn,Khazix,Kindred,LeeSin,Lillia,MasterYi,Naafiri,Nidalee,Nocturne,Nunu,Pantheon,Poppy,Qiyana,Rammus,RekSai,Rengar,Sejuani,Shaco,Shyvana,Skarner,Taliyah,Talon,Trundle,Udyr,Vi,Viego,Volibear,Warwick,MonkeyKing,XinZhao,Yorick,Zac,Zed,Zyra"
mid = "Ahri,Akali,Akshan,Anivia,Annie,AurelionSol,Aurora,Azir,Brand,Cassiopeia,Chogath,Corki,Diana,Ekko,Fizz,Galio,Garen,Gragas,Hwei,Irelia,Jayce,Kassadin,Katarina,Kayle,Kennen,Leblanc,Lissandra,Lux,Malphite,Malzahar,Mel,Naafiri,Neeko,Orianna,Pantheon,Qiyana,Quinn,Ryze,Smolder,Swain,Sylas,Syndra,Taliyah,Talon,Tristana,TwistedFate,Veigar,Velkoz,Vex,Viktor,Vladimir,Xerath,Yasuo,Yone,Zed,Ziggs,Zoe"
bot = "Aphelios,Ashe,Caitlyn,Corki,Draven,Ezreal,Hwei,Jhin,Jinx,Kaisa,Kalista,KogMaw,Lucian,Mel,MissFortune,Nilah,Samira,Seraphine,Sivir,Smolder,Swain,Tristana,Twitch,Varus,Vayne,Xayah,Yasuo,Zeri,Ziggs"
sup = "Alistar,Annie,Bard,Blitzcrank,Brand,Braum,Elise,Fiddlesticks,Galio,Gragas,Hwei,Janna,Karma,Leona,Lulu,Lux,Maokai,Mel,Milio,Morgana,Nami,Nautilus,Neeko,Pantheon,Poppy,Pyke,Rakan,Rell,Renata,Senna,Seraphine,Shaco,Shen,Sona,Soraka,Swain,Sylas,TahmKench,Taric,Thresh,Velkoz,Xerath,Yuumi,Zilean,Zoe,Zyra"

def convert_to_champion_id(name):
    """Convert display names to URL-friendly champion IDs"""
    return name.replace(" ", "").replace("'", "").replace(".", "")

def generate_role_champions(role_list, role_name):
    """Generate or retrieve cached champions for a role"""
    if role_name not in st.session_state.selections or st.session_state.regenerate:
        champion_list = [champ.strip() for champ in role_list.split(",")]
        unique_champs = list(set(champion_list))
        
        if len(unique_champs) < 8:
            st.error(f"Need at least 8 unique champions in {role_name} list!")
            return []
        
        # Keep track of all selected champions
        all_selected_champs = []
        for role in st.session_state.selections.values():
            all_selected_champs.extend(role)
        
        # Select unique champions for this role
        selected = []
        while len(selected) < 8:
            champ = random.choice(unique_champs)
            if champ not in all_selected_champs and champ not in selected:
                selected.append(champ)
        
        st.session_state.selections[role_name] = selected
    return st.session_state.selections[role_name]

def combine_all_images():
    """Combine all 40 champions into a single 10x4 grid image"""
    images = []
    for role in ['Top', 'Jungle', 'Mid', 'Bot', 'Support']:
        for champ in st.session_state.selections.get(role, []):
            url = f"https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/{convert_to_champion_id(champ)}.png"
            response = requests.get(url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content)).resize((120, 120))
                images.append(img)
    
    # Create 10 rows of 4 columns (1200px height)
    grid = Image.new('RGB', (4 * 120, 10 * 120))
    for index, img in enumerate(images):
        row = index // 4
        col = index % 4
        grid.paste(img, (col * 120, row * 120))
    return grid

# Regenerate button
if st.button("Regenerate All Champions"):
    st.session_state.regenerate = True
else:
    st.session_state.regenerate = False

# Generate/display champions for each role
roles = {
    'Top': top,
    'Jungle': jung,
    'Middle': mid,
    'Bottom': bot,
    'Support': sup
}

for role_name, role_list in roles.items():
    st.markdown(f"## {role_name} Lane Picks")
    selected_champs = generate_role_champions(role_list, role_name)
    
    if selected_champs:
        with st.container():
            for i in range(0, 8, 4):
                cols = st.columns(4)
                for col_idx in range(4):
                    champ = selected_champs[i + col_idx]
                    with cols[col_idx]:
                        st.image(
                            f"https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/{convert_to_champion_id(champ)}.png",
                            use_container_width=True,
                            caption=champ
                        )

# Download combined image
if st.button("📸 Download All Champions (40)"):
    if len(st.session_state.selections) == 5:
        combined = combine_all_images()
        img_bytes = BytesIO()
        combined.save(img_bytes, format='PNG')
        
        st.download_button(
            label="⬇️ Save Combined Image",
            data=img_bytes.getvalue(),
            file_name="all_champions_grid.png",
            mime="image/png"
        )
    else:
        st.error("Please generate champions for all roles first!")