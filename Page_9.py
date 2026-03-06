import random

import streamlit as st

st.markdown("# League Draft Generator")
st.sidebar.markdown("# League Draft Generator")
st.sidebar.markdown("Randomize candidate pools, then draft Blue vs Red.")

ROLE_ORDER = ["Top", "Jungle", "Middle", "Bottom", "Support"]
TEAMS = ["Blue", "Red"]

ROLE_POOLS = {
    "Top": "Aatrox,Akali,Ambessa,Aurora,Camille,Cassiopeia,Chogath,Darius,DrMundo,Fiora,Galio,Gangplank,Garen,Gnar,Gragas,Gwen,Heimerdinger,Illaoi,Irelia,Jax,Jayce,KSante,Kayle,Kennen,Kled,Malphite,Mordekaiser,Nasus,Nidalee,Olaf,Ornn,Pantheon,Poppy,Quinn,Renekton,Riven,Rumble,Ryze,Sett,Shen,Singed,Sion,Sylas,TahmKench,Teemo,Trundle,Tryndamere,Urgot,Varus,Vayne,Viktor,Vladimir,Volibear,Warwick,MonkeyKing,Yasuo,Yone,Yorick,Zac",
    "Jungle": "Amumu,Belveth,Brand,Briar,Darius,Diana,DrMundo,Ekko,Elise,Evelynn,Fiddlesticks,Gragas,Graves,Gwen,Hecarim,Ivern,JarvanIV,Jax,Karthus,Kayn,Khazix,Kindred,LeeSin,Lillia,MasterYi,Naafiri,Nidalee,Nocturne,Nunu,Pantheon,Poppy,Qiyana,Rammus,RekSai,Rengar,Sejuani,Shaco,Shyvana,Skarner,Taliyah,Talon,Trundle,Udyr,Vi,Viego,Volibear,Warwick,MonkeyKing,XinZhao,Yorick,Zac,Zed,Zyra",
    "Middle": "Ahri,Akali,Akshan,Anivia,Annie,AurelionSol,Aurora,Azir,Brand,Cassiopeia,Chogath,Corki,Diana,Ekko,Fizz,Galio,Garen,Gragas,Hwei,Irelia,Jayce,Kassadin,Katarina,Kayle,Kennen,Leblanc,Lissandra,Lux,Malphite,Malzahar,Mel,Naafiri,Neeko,Orianna,Pantheon,Qiyana,Quinn,Ryze,Smolder,Swain,Sylas,Syndra,Taliyah,Talon,Tristana,TwistedFate,Veigar,Velkoz,Vex,Viktor,Vladimir,Xerath,Yasuo,Yone,Zed,Ziggs,Zoe",
    "Bottom": "Aphelios,Ashe,Caitlyn,Corki,Draven,Ezreal,Hwei,Jhin,Jinx,Kaisa,Kalista,KogMaw,Lucian,Mel,MissFortune,Nilah,Samira,Seraphine,Sivir,Smolder,Swain,Tristana,Twitch,Varus,Vayne,Xayah,Yasuo,Zeri,Ziggs",
    "Support": "Alistar,Annie,Bard,Blitzcrank,Brand,Braum,Elise,Fiddlesticks,Galio,Gragas,Hwei,Janna,Karma,Leona,Lulu,Lux,Maokai,Mel,Milio,Morgana,Nami,Nautilus,Neeko,Pantheon,Poppy,Pyke,Rakan,Rell,Renata,Senna,Seraphine,Shaco,Shen,Sona,Soraka,Swain,Sylas,TahmKench,Taric,Thresh,Velkoz,Xerath,Yuumi,Zilean,Zoe,Zyra",
}


def parse_pool(csv_names):
    return [name.strip() for name in csv_names.split(",") if name.strip()]


def champion_id(name):
    return name.replace(" ", "").replace("'", "").replace(".", "")


def build_champion_roles(role_pools):
    champ_roles = {}
    for role, csv_names in role_pools.items():
        for champ in parse_pool(csv_names):
            champ_roles.setdefault(champ, set()).add(role)
    return champ_roles


@st.cache_data(show_spinner=False)
def get_champion_roles_cached():
    return build_champion_roles(ROLE_POOLS)


def assign_selected_to_roles(selected_champs, role_counts, champ_roles):
    slots = []
    for role, count in role_counts.items():
        for i in range(count):
            slots.append((role, i))

    eligible_slots = {}
    for champ in selected_champs:
        allowed_roles = champ_roles.get(champ, set())
        eligible_slots[champ] = [slot for slot in slots if slot[0] in allowed_roles]
        random.shuffle(eligible_slots[champ])
        if not eligible_slots[champ]:
            return None

    slot_to_champ = {}

    def dfs(champ, seen_slots):
        for slot in eligible_slots[champ]:
            if slot in seen_slots:
                continue
            seen_slots.add(slot)
            if slot not in slot_to_champ or dfs(slot_to_champ[slot], seen_slots):
                slot_to_champ[slot] = champ
                return True
        return False

    shuffled = selected_champs[:]
    random.shuffle(shuffled)
    for champ in shuffled:
        if not dfs(champ, set()):
            return None

    assignments = {role: [] for role in role_counts}
    for (role, _), champ in sorted(slot_to_champ.items(), key=lambda x: (x[0][0], x[0][1])):
        assignments[role].append(champ)
    return assignments


def generate_candidate_pools(role_counts, champ_roles, max_attempts=500):
    total_slots = sum(role_counts.values())
    all_champs = list(champ_roles.keys())

    if total_slots > len(all_champs):
        return None, "Requested champions exceed the unique champion pool."

    for _ in range(max_attempts):
        selected = random.sample(all_champs, total_slots)
        assignments = assign_selected_to_roles(selected, role_counts, champ_roles)
        if assignments is not None:
            return assignments, None

    return None, "Could not find a valid role assignment. Reduce per-role picks."


def init_state():
    if "draft_state" not in st.session_state:
        st.session_state["draft_state"] = {
            "id": 0,
            "assignments": None,
            "ban_count": 6,
            "bans": {"Blue": [], "Red": []},
            "picks": {
                "Blue": {role: "" for role in ROLE_ORDER},
                "Red": {role: "" for role in ROLE_ORDER},
            },
        }


def create_new_draft(assignments, ban_count):
    draft_id = st.session_state["draft_state"]["id"] + 1
    blue_slots = ban_count // 2
    red_slots = ban_count - blue_slots
    st.session_state["draft_state"] = {
        "id": draft_id,
        "assignments": assignments,
        "ban_count": int(ban_count),
        "bans": {"Blue": [""] * blue_slots, "Red": [""] * red_slots},
        "picks": {
            "Blue": {role: "" for role in ROLE_ORDER},
            "Red": {role: "" for role in ROLE_ORDER},
        },
    }


def reset_current_draft_state():
    ds = st.session_state["draft_state"]
    blue_slots = ds["ban_count"] // 2
    red_slots = ds["ban_count"] - blue_slots
    ds["bans"] = {"Blue": [""] * blue_slots, "Red": [""] * red_slots}
    ds["picks"] = {
        "Blue": {role: "" for role in ROLE_ORDER},
        "Red": {role: "" for role in ROLE_ORDER},
    }


def selected_champs(ds, exclude=None):
    used = set()

    for team in TEAMS:
        for idx, champ in enumerate(ds["bans"][team]):
            if exclude == ("ban", team, idx):
                continue
            if champ:
                used.add(champ)

    for team in TEAMS:
        for role in ROLE_ORDER:
            champ = ds["picks"][team][role]
            if exclude == ("pick", team, role):
                continue
            if champ:
                used.add(champ)

    return used


def enforce_uniqueness(ds):
    seen = set()

    for team in TEAMS:
        for idx, champ in enumerate(ds["bans"][team]):
            if champ in seen:
                ds["bans"][team][idx] = ""
            elif champ:
                seen.add(champ)

    for team in TEAMS:
        for role in ROLE_ORDER:
            champ = ds["picks"][team][role]
            if champ in seen:
                ds["picks"][team][role] = ""
            elif champ:
                seen.add(champ)


def render_champion_tile(champ, is_banned):
    url = f"https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/{champion_id(champ)}.png"
    if is_banned:
        st.markdown(
            f"""
<div style="position:relative; width:100%; max-width:120px; margin:auto;">
  <img src="{url}" style="width:100%; border-radius:8px; filter:grayscale(70%) sepia(50%) hue-rotate(-20deg) saturate(220%) brightness(60%);" />
  <div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#ff2b2b; font-size:44px; font-weight:800; text-shadow:0 0 8px rgba(0,0,0,0.9);">X</div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.image(url, use_container_width=True)


def render_role_pool_with_images(role, champs, banned):
    st.markdown(f"### {role} ({len(champs)})")
    cols_per_row = 5
    for i in range(0, len(champs), cols_per_row):
        cols = st.columns(cols_per_row)
        chunk = champs[i : i + cols_per_row]
        for j, champ in enumerate(chunk):
            with cols[j]:
                render_champion_tile(champ, champ in banned)
                label = f"{champ} (BANNED)" if champ in banned else champ
                st.caption(label)


def render_bans(ds, pool_champs):
    blue_slots = len(ds["bans"]["Blue"])
    red_slots = len(ds["bans"]["Red"])

    st.markdown("## Team Bans")
    st.caption(f"Blue bans: {blue_slots} | Red bans: {red_slots}")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("### Blue Bans")
        for idx in range(blue_slots):
            current = ds["bans"]["Blue"][idx]
            used = selected_champs(ds, exclude=("ban", "Blue", idx))
            options = [""] + [c for c in pool_champs if c not in used]
            if current and current not in options:
                options.append(current)
            key = f"draft_{ds['id']}_ban_Blue_{idx}"
            selected = st.selectbox(
                f"Blue Ban {idx + 1}",
                options,
                index=options.index(current) if current in options else 0,
                key=key,
                format_func=lambda x: "Open" if x == "" else x,
            )
            ds["bans"]["Blue"][idx] = selected

    with cols[1]:
        st.markdown("### Red Bans")
        for idx in range(red_slots):
            current = ds["bans"]["Red"][idx]
            used = selected_champs(ds, exclude=("ban", "Red", idx))
            options = [""] + [c for c in pool_champs if c not in used]
            if current and current not in options:
                options.append(current)
            key = f"draft_{ds['id']}_ban_Red_{idx}"
            selected = st.selectbox(
                f"Red Ban {idx + 1}",
                options,
                index=options.index(current) if current in options else 0,
                key=key,
                format_func=lambda x: "Open" if x == "" else x,
            )
            ds["bans"]["Red"][idx] = selected


def render_picks(ds, pool_champs):
    st.markdown("## Final 5v5 Draft Board")
    st.caption("Selections are stored in session state until you refresh the page or press reset.")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("### Blue Side")
        for role in ROLE_ORDER:
            current = ds["picks"]["Blue"][role]
            used = selected_champs(ds, exclude=("pick", "Blue", role))
            options = [""] + [c for c in pool_champs if c not in used]
            if current and current not in options:
                options.append(current)
            key = f"draft_{ds['id']}_pick_Blue_{role}"
            selected = st.selectbox(
                f"Blue {role}",
                options,
                index=options.index(current) if current in options else 0,
                key=key,
                format_func=lambda x: "Open" if x == "" else x,
            )
            ds["picks"]["Blue"][role] = selected

    with cols[1]:
        st.markdown("### Red Side")
        for role in ROLE_ORDER:
            current = ds["picks"]["Red"][role]
            used = selected_champs(ds, exclude=("pick", "Red", role))
            options = [""] + [c for c in pool_champs if c not in used]
            if current and current not in options:
                options.append(current)
            key = f"draft_{ds['id']}_pick_Red_{role}"
            selected = st.selectbox(
                f"Red {role}",
                options,
                index=options.index(current) if current in options else 0,
                key=key,
                format_func=lambda x: "Open" if x == "" else x,
            )
            ds["picks"]["Red"][role] = selected


def render_team_summary(ds, team):
    st.markdown(f"### {team} Locked")
    for role in ROLE_ORDER:
        champ = ds["picks"][team][role]
        if champ:
            st.image(
                f"https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/{champion_id(champ)}.png",
                caption=f"{role}: {champ}",
                width=90,
            )
        else:
            st.write(f"{role}: Open")


init_state()
champion_roles = get_champion_roles_cached()
total_unique = len(champion_roles)

st.caption(f"Unique champions in pool: {total_unique}")
st.caption("Defaults: 5 picks per role and 6 total bans (3 per side).")

role_counts = {}
count_cols = st.columns(5)
for i, role in enumerate(ROLE_ORDER):
    role_size = len(set(parse_pool(ROLE_POOLS[role])))
    with count_cols[i]:
        role_counts[role] = st.number_input(
            f"{role} picks",
            min_value=1,
            max_value=role_size,
            value=5,
            step=1,
            key=f"count_{role}",
        )

ban_count = st.number_input("Total bans", min_value=0, max_value=20, value=6, step=1)

if st.button("Generate Candidate Pools", use_container_width=True):
    assignments, error = generate_candidate_pools(role_counts, champion_roles)
    if error:
        st.error(error)
    else:
        create_new_draft(assignments, int(ban_count))

state = st.session_state["draft_state"]
if state["assignments"] is not None:
    enforce_uniqueness(state)

    if st.button("Reset Picks And Bans"):
        reset_current_draft_state()

    pool_champs = sorted({champ for champs in state["assignments"].values() for champ in champs})
    render_bans(state, pool_champs)

    active_bans = sorted([c for c in state["bans"]["Blue"] + state["bans"]["Red"] if c])
    if active_bans:
        st.write("Active bans: " + ", ".join(active_bans))

    st.markdown("## Randomized Candidate Pools")
    banned_set = set(active_bans)
    for role in ROLE_ORDER:
        render_role_pool_with_images(role, state["assignments"].get(role, []), banned_set)

    render_picks(state, pool_champs)
    summary_cols = st.columns(2)
    with summary_cols[0]:
        render_team_summary(state, "Blue")
    with summary_cols[1]:
        render_team_summary(state, "Red")