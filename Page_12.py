from collections import defaultdict
from datetime import datetime, timezone
import time

import pandas as pd
import requests
import streamlit as st

import config


st.set_page_config(page_title="Flex Team Records", page_icon=":material/emoji_events:")
st.markdown("# League Flex Team Records")
st.sidebar.markdown("# League Flex Team Records")
st.sidebar.markdown("Track flex records across games where at least two tracked players queued together.")


QUEUE_TYPE = "RANKED_FLEX_SR"
QUEUE_ID = 440
PLATFORM_OPTIONS = {
    "Brazil": "br1",
    "Europe Nordic & East": "eun1",
    "Europe West": "euw1",
    "Japan": "jp1",
    "Korea": "kr",
    "Latin America North": "la1",
    "Latin America South": "la2",
    "Middle East": "me1",
    "North America": "na1",
    "Oceania": "oc1",
    "Philippines": "ph2",
    "Russia": "ru",
    "Singapore": "sg2",
    "Thailand": "th2",
    "Turkey": "tr1",
    "Taiwan": "tw2",
    "Vietnam": "vn2",
}
REGIONAL_ROUTING = {
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "na1": "americas",
    "eun1": "europe",
    "euw1": "europe",
    "me1": "europe",
    "ru": "europe",
    "tr1": "europe",
    "jp1": "asia",
    "kr": "asia",
    "oc1": "sea",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}
APP_RATE_LIMIT_SHORT_WINDOW_SECONDS = 1.0
APP_RATE_LIMIT_SHORT_WINDOW_CALLS = 18
APP_RATE_LIMIT_LONG_WINDOW_SECONDS = 120.0
APP_RATE_LIMIT_LONG_WINDOW_CALLS = 90
RIOT_API_KEY = config.RIOT_API_KEY
ROLE_LABELS = {
    "TOP": "Top",
    "JUNGLE": "Jungle",
    "MIDDLE": "Middle",
    "BOTTOM": "Bottom",
    "UTILITY": "Support",
}


st.markdown(
    """
<style>
.record-shell {
    padding: 1rem 1.1rem;
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(19,33,53,0.96), rgba(11,18,32,0.96));
    border: 1px solid rgba(113,168,255,0.28);
    box-shadow: 0 14px 30px rgba(0,0,0,0.18);
    margin-bottom: 0.75rem;
}
.record-label {
    color: #8eb6ff;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.35rem;
}
.record-value {
    color: #f7fbff;
    font-size: 1.45rem;
    font-weight: 700;
    line-height: 1.2;
}
.record-caption {
    color: #aab8d1;
    font-size: 0.92rem;
    margin-top: 0.35rem;
}
.champ-hero {
    display: flex;
    gap: 1rem;
    align-items: center;
    padding: 1rem 1.1rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(30,62,103,0.98), rgba(17,25,42,0.98));
    border: 1px solid rgba(122,195,255,0.32);
    margin: 0.25rem 0 1rem 0;
}
.champ-hero img {
    width: 88px;
    height: 88px;
    border-radius: 18px;
    object-fit: cover;
    box-shadow: 0 10px 24px rgba(0,0,0,0.28);
}
.champ-hero-title {
    color: #9fc4ff;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.champ-hero-name {
    color: #ffffff;
    font-size: 1.55rem;
    font-weight: 800;
    line-height: 1.15;
}
.champ-hero-meta {
    color: #dbe7ff;
    font-size: 0.95rem;
    margin-top: 0.28rem;
}
.section-note {
    color: #9fb0c8;
    font-size: 0.92rem;
    margin-top: -0.2rem;
    margin-bottom: 0.8rem;
}
</style>
""",
    unsafe_allow_html=True,
)


def parse_player_entries(raw_text):
    entries = []
    for line in raw_text.splitlines():
        value = line.strip()
        if not value:
            continue

        if "|" in value:
            accounts_part, person_name_part = value.split("|", 1)
            person_name = person_name_part.strip()
        else:
            accounts_part = value
            person_name = ""

        account_values = [account.strip() for account in accounts_part.split(",") if account.strip()]
        if not account_values:
            continue

        for account_value in account_values:
            entry = {
                "input": account_value,
                "person_name": person_name or account_value,
            }
            if "#" in account_value:
                game_name, tag_line = account_value.split("#", 1)
                entry.update(
                    {
                        "lookup_type": "riot_id",
                        "game_name": game_name.strip(),
                        "tag_line": tag_line.strip(),
                    }
                )
            else:
                entry.update(
                    {
                        "lookup_type": "summoner_name",
                        "summoner_name": account_value,
                    }
                )
            entries.append(entry)
    return entries


def champion_id(name):
    return name.replace(" ", "").replace("'", "").replace(".", "")


def champion_image_url(name):
    return f"https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/{champion_id(name)}.png"


def throttle_request(state):
    now = time.monotonic()
    short_window = [timestamp for timestamp in state["recent_requests"] if now - timestamp < APP_RATE_LIMIT_SHORT_WINDOW_SECONDS]
    long_window = [timestamp for timestamp in state["recent_requests"] if now - timestamp < APP_RATE_LIMIT_LONG_WINDOW_SECONDS]
    state["recent_requests"] = long_window

    sleep_for = 0.0
    if len(short_window) >= APP_RATE_LIMIT_SHORT_WINDOW_CALLS:
        sleep_for = max(sleep_for, APP_RATE_LIMIT_SHORT_WINDOW_SECONDS - (now - short_window[0]) + 0.05)
    if len(long_window) >= APP_RATE_LIMIT_LONG_WINDOW_CALLS:
        sleep_for = max(sleep_for, APP_RATE_LIMIT_LONG_WINDOW_SECONDS - (now - long_window[0]) + 0.25)

    if sleep_for > 0:
        time.sleep(sleep_for)
        now = time.monotonic()
        state["recent_requests"] = [
            timestamp for timestamp in state["recent_requests"] if now - timestamp < APP_RATE_LIMIT_LONG_WINDOW_SECONDS
        ]

    state["recent_requests"].append(time.monotonic())


@st.cache_data(show_spinner=False, ttl=900)
def riot_get_cached(url, api_key, params_items):
    response = requests.get(
        url,
        params=dict(params_items),
        headers={"X-Riot-Token": api_key},
        timeout=20,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = response.text
    return response.status_code, response.headers.get("Retry-After"), payload


def riot_get(state, url, api_key, params=None, allow_status_codes=None):
    params = params or {}
    allow_status_codes = set(allow_status_codes or [])
    for attempt in range(4):
        throttle_request(state)
        status_code, retry_after, payload = riot_get_cached(
            url,
            api_key,
            tuple(sorted(params.items())),
        )

        if status_code == 429 and attempt < 3:
            delay_seconds = float(retry_after) if retry_after else min(5 * (attempt + 1), 15)
            time.sleep(delay_seconds)
            continue

        if status_code in allow_status_codes:
            return None

        if status_code >= 400:
            raise RuntimeError(f"Riot API error {status_code}: {payload}")

        return payload

    raise RuntimeError("Riot API rate limit retries were exhausted.")


def resolve_player(state, api_key, platform, player_entry):
    regional = REGIONAL_ROUTING[platform]
    if player_entry["lookup_type"] == "riot_id":
        account = riot_get(
            state,
            f"https://{regional}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
            f"{player_entry['game_name']}/{player_entry['tag_line']}",
            api_key,
        )
        summoner = riot_get(
            state,
            f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{account['puuid']}",
            api_key,
        )
        display_name = f"{account.get('gameName', player_entry['game_name'])}#{account.get('tagLine', player_entry['tag_line'])}"
    else:
        summoner = riot_get(
            state,
            f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{player_entry['summoner_name']}",
            api_key,
        )
        display_name = summoner.get("name", player_entry["summoner_name"])

    summoner_id = summoner.get("id") or summoner.get("summonerId")

    return {
        "input": player_entry["input"],
        "person_name": player_entry["person_name"],
        "display_name": display_name,
        "puuid": summoner["puuid"],
        "summoner_id": summoner_id,
    }


def get_flex_entry(state, api_key, platform, puuid, summoner_id):
    entries = riot_get(
        state,
        f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}",
        api_key,
        allow_status_codes={404},
    )
    if entries is None and summoner_id:
        entries = riot_get(
            state,
            f"https://{platform}.api.riotgames.com/lol/league/exp/v4/entries/summoner/{summoner_id}",
            api_key,
            allow_status_codes={404},
        )
    if entries is None:
        return None

    for entry in entries:
        if entry.get("queueType") == QUEUE_TYPE:
            return entry
    return None


def get_recent_flex_match_ids(state, api_key, platform, puuid, count):
    regional = REGIONAL_ROUTING[platform]
    return riot_get(
        state,
        f"https://{regional}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids",
        api_key,
        params={"queue": QUEUE_ID, "start": 0, "count": count},
    )


def get_match_details(state, api_key, platform, match_id):
    regional = REGIONAL_ROUTING[platform]
    return riot_get(
        state,
        f"https://{regional}.api.riotgames.com/lol/match/v5/matches/{match_id}",
        api_key,
    )


def build_rank_table(players, flex_entries):
    rows = []
    for player in players:
        entry = flex_entries.get(player["puuid"])
        if entry is None:
            rows.append(
                {
                    "Player": player["person_name"],
                    "Account": player["display_name"],
                    "Tier": "Unranked",
                    "Division": "",
                    "LP": 0,
                    "Wins": 0,
                    "Losses": 0,
                    "Win Rate %": 0.0,
                }
            )
            continue

        wins = entry.get("wins", 0)
        losses = entry.get("losses", 0)
        total_games = wins + losses
        rows.append(
            {
                "Player": player["person_name"],
                "Account": player["display_name"],
                "Tier": entry.get("tier", ""),
                "Division": entry.get("rank", ""),
                "LP": entry.get("leaguePoints", 0),
                "Wins": wins,
                "Losses": losses,
                "Win Rate %": round((wins / total_games) * 100, 1) if total_games else 0.0,
            }
        )
    return pd.DataFrame(rows)


def fetch_flex_bundle(api_key, platform, raw_players, match_count):
    if not api_key:
        raise RuntimeError("Missing Riot API key. Add `RIOT_API_KEY` to Streamlit secrets.")

    player_entries = parse_player_entries(raw_players)
    if len(player_entries) < 2:
        raise RuntimeError("Enter at least two players, one per line.")

    state = {"recent_requests": []}
    players = []
    flex_entries = {}
    all_match_ids = set()
    profile_warnings = []

    for player_entry in player_entries:
        player = resolve_player(state, api_key, platform, player_entry)
        players.append(player)
        flex_entries[player["puuid"]] = get_flex_entry(
            state,
            api_key,
            platform,
            player["puuid"],
            player["summoner_id"],
        )
        if not player["summoner_id"] and flex_entries[player["puuid"]] is None:
            profile_warnings.append(
                f"{player['display_name']}: Riot did not return a summoner ID and no direct PUUID flex entry was found."
            )
        match_ids = get_recent_flex_match_ids(state, api_key, platform, player["puuid"], match_count)
        all_match_ids.update(match_ids)

    match_details = {}
    for match_id in sorted(all_match_ids):
        match_details[match_id] = get_match_details(state, api_key, platform, match_id)

    return {
        "players": players,
        "rank_df": build_rank_table(players, flex_entries),
        "match_details": match_details,
        "profile_warnings": profile_warnings,
        "unique_matches": len(match_details),
    }


def safe_divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def calculate_kda(kills, assists, deaths):
    return (kills + assists) / max(1, deaths)


def format_match_timestamp(timestamp_ms):
    if not timestamp_ms:
        return ""
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def build_flex_team_dataset(match_details, tracked_players):
    tracked_by_puuid = {player["puuid"]: player for player in tracked_players}
    player_totals = defaultdict(
        lambda: {
            "games": 0,
            "wins": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "damage": 0,
            "gold": 0,
            "pentakills": 0,
            "doublekills": 0,
            "triplekills": 0,
            "quadrakills": 0,
            "roles": defaultdict(lambda: {"games": 0, "wins": 0}),
            "champions": defaultdict(lambda: {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0}),
        }
    )
    champion_totals = defaultdict(
        lambda: {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0, "players": set()}
    )
    participant_rows = []
    pentakill_rows = []
    match_rows = []
    role_rows = []

    eligible_match_count = 0

    for match_id, match_data in match_details.items():
        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})
        if info.get("queueId") != QUEUE_ID:
            continue

        teams = defaultdict(list)
        for participant in info.get("participants", []):
            puuid = participant.get("puuid")
            if puuid in tracked_by_puuid:
                teams[participant.get("teamId")].append(participant)

        for team_participants in teams.values():
            unique_people = {}
            for participant in team_participants:
                player = tracked_by_puuid[participant["puuid"]]
                unique_people[player["person_name"]] = (player, participant)

            if len(unique_people) < 2:
                continue

            eligible_match_count += 1
            tracked_names = []
            team_win = False

            for person_name, (player, participant) in sorted(unique_people.items()):
                champion = participant.get("championName", "Unknown")
                role_code = participant.get("teamPosition") or participant.get("individualPosition") or "UNKNOWN"
                win = bool(participant.get("win"))
                team_win = win

                totals = player_totals[person_name]
                totals["games"] += 1
                totals["wins"] += int(win)
                totals["kills"] += participant.get("kills", 0)
                totals["deaths"] += participant.get("deaths", 0)
                totals["assists"] += participant.get("assists", 0)
                totals["damage"] += participant.get("totalDamageDealtToChampions", 0)
                totals["gold"] += participant.get("goldEarned", 0)
                totals["pentakills"] += participant.get("pentaKills", 0)
                totals["doublekills"] += participant.get("doubleKills", 0)
                totals["triplekills"] += participant.get("tripleKills", 0)
                totals["quadrakills"] += participant.get("quadraKills", 0)
                totals["roles"][role_code]["games"] += 1
                totals["roles"][role_code]["wins"] += int(win)

                champion_stats = totals["champions"][champion]
                champion_stats["games"] += 1
                champion_stats["wins"] += int(win)
                champion_stats["kills"] += participant.get("kills", 0)
                champion_stats["deaths"] += participant.get("deaths", 0)
                champion_stats["assists"] += participant.get("assists", 0)

                collective_stats = champion_totals[champion]
                collective_stats["games"] += 1
                collective_stats["wins"] += int(win)
                collective_stats["kills"] += participant.get("kills", 0)
                collective_stats["deaths"] += participant.get("deaths", 0)
                collective_stats["assists"] += participant.get("assists", 0)
                collective_stats["players"].add(person_name)

                tracked_names.append(person_name)
                role_rows.append(
                    {
                        "Player": person_name,
                        "Role": ROLE_LABELS.get(role_code, role_code.title()),
                        "Games": 1,
                        "Wins": int(win),
                    }
                )
                participant_rows.append(
                    {
                        "Match ID": metadata.get("matchId", match_id),
                        "Played": format_match_timestamp(info.get("gameEndTimestamp") or info.get("gameCreation")),
                        "Player": person_name,
                        "Account": player["display_name"],
                        "Champion": champion,
                        "Role": ROLE_LABELS.get(role_code, role_code.title()),
                        "Result": "Win" if win else "Loss",
                        "Kills": participant.get("kills", 0),
                        "Deaths": participant.get("deaths", 0),
                        "Assists": participant.get("assists", 0),
                        "KDA": round(
                            calculate_kda(
                                participant.get("kills", 0),
                                participant.get("assists", 0),
                                participant.get("deaths", 0),
                            ),
                            2,
                        ),
                        "Damage to Champs": participant.get("totalDamageDealtToChampions", 0),
                        "Gold": participant.get("goldEarned", 0),
                        "Pentakills": participant.get("pentaKills", 0),
                    }
                )

                if participant.get("pentaKills", 0):
                    pentakill_rows.append(
                        {
                            "Player": person_name,
                            "Account": player["display_name"],
                            "Champion": champion,
                            "Match ID": metadata.get("matchId", match_id),
                            "Played": format_match_timestamp(info.get("gameEndTimestamp") or info.get("gameCreation")),
                            "Result": "Win" if win else "Loss",
                            "Kills": participant.get("kills", 0),
                            "Deaths": participant.get("deaths", 0),
                            "Assists": participant.get("assists", 0),
                            "Pentakills": participant.get("pentaKills", 0),
                        }
                    )

            match_rows.append(
                {
                    "Match ID": metadata.get("matchId", match_id),
                    "Played": format_match_timestamp(info.get("gameEndTimestamp") or info.get("gameCreation")),
                    "Tracked Players Together": ", ".join(sorted(tracked_names)),
                    "Players Count": len(tracked_names),
                    "Result": "Win" if team_win else "Loss",
                }
            )

    player_rows = []
    role_summary_rows = []
    player_champion_rows = []
    collective_champion_rows = []

    for person_name, stats in player_totals.items():
        games = stats["games"]
        wins = stats["wins"]
        kills = stats["kills"]
        deaths = stats["deaths"]
        assists = stats["assists"]
        player_rows.append(
            {
                "Player": person_name,
                "Games": games,
                "Wins": wins,
                "Win Rate %": round(safe_divide(wins, games) * 100, 1),
                "Kills / Game": round(safe_divide(kills, games), 2),
                "Deaths / Game": round(safe_divide(deaths, games), 2),
                "Assists / Game": round(safe_divide(assists, games), 2),
                "KDA": round(calculate_kda(kills, assists, deaths), 2),
                "Damage / Game": round(safe_divide(stats["damage"], games), 0),
                "Gold / Game": round(safe_divide(stats["gold"], games), 0),
                "Pentakills": stats["pentakills"],
                "Double Kills": stats["doublekills"],
                "Triple Kills": stats["triplekills"],
                "Quadra Kills": stats["quadrakills"],
            }
        )

        for role_code, role_stats in stats["roles"].items():
            role_summary_rows.append(
                {
                    "Player": person_name,
                    "Role": ROLE_LABELS.get(role_code, role_code.title()),
                    "Games": role_stats["games"],
                    "Wins": role_stats["wins"],
                    "Win Rate %": round(safe_divide(role_stats["wins"], role_stats["games"]) * 100, 1),
                }
            )

        for champion, champion_stats in stats["champions"].items():
            games_played = champion_stats["games"]
            player_champion_rows.append(
                {
                    "Player": person_name,
                    "Champion": champion,
                    "Games": games_played,
                    "Wins": champion_stats["wins"],
                    "Win Rate %": round(safe_divide(champion_stats["wins"], games_played) * 100, 1),
                    "KDA": round(
                        calculate_kda(
                            champion_stats["kills"],
                            champion_stats["assists"],
                            champion_stats["deaths"],
                        ),
                        2,
                    ),
                }
            )

    for champion, stats in champion_totals.items():
        games = stats["games"]
        collective_champion_rows.append(
            {
                "Champion": champion,
                "Games": games,
                "Wins": stats["wins"],
                "Win Rate %": round(safe_divide(stats["wins"], games) * 100, 1),
                "KDA": round(calculate_kda(stats["kills"], stats["assists"], stats["deaths"]), 2),
                "Players Used": len(stats["players"]),
                "Played By": ", ".join(sorted(stats["players"])),
            }
        )

    return {
        "eligible_match_count": eligible_match_count,
        "player_df": pd.DataFrame(
            player_rows,
            columns=[
                "Player",
                "Games",
                "Wins",
                "Win Rate %",
                "Kills / Game",
                "Deaths / Game",
                "Assists / Game",
                "KDA",
                "Damage / Game",
                "Gold / Game",
                "Pentakills",
                "Double Kills",
                "Triple Kills",
                "Quadra Kills",
            ],
        ),
        "role_df": pd.DataFrame(
            role_summary_rows,
            columns=["Player", "Role", "Games", "Wins", "Win Rate %"],
        ),
        "collective_champion_df": pd.DataFrame(
            collective_champion_rows,
            columns=["Champion", "Games", "Wins", "Win Rate %", "KDA", "Players Used", "Played By"],
        ),
        "player_champion_df": pd.DataFrame(
            player_champion_rows,
            columns=["Player", "Champion", "Games", "Wins", "Win Rate %", "KDA"],
        ),
        "pentakill_df": pd.DataFrame(
            pentakill_rows,
            columns=[
                "Player",
                "Account",
                "Champion",
                "Match ID",
                "Played",
                "Result",
                "Kills",
                "Deaths",
                "Assists",
                "Pentakills",
            ],
        ),
        "participant_df": pd.DataFrame(
            participant_rows,
            columns=[
                "Match ID",
                "Played",
                "Player",
                "Account",
                "Champion",
                "Role",
                "Result",
                "Kills",
                "Deaths",
                "Assists",
                "KDA",
                "Damage to Champs",
                "Gold",
                "Pentakills",
            ],
        ),
        "match_df": pd.DataFrame(
            match_rows,
            columns=["Match ID", "Played", "Tracked Players Together", "Players Count", "Result"],
        ),
    }


def top_record(df, sort_columns, ascending):
    if df.empty:
        return None
    return df.sort_values(sort_columns, ascending=ascending).iloc[0]


def render_record_card(title, value, caption):
    st.markdown(
        f"""
<div class="record-shell">
  <div class="record-label">{title}</div>
  <div class="record-value">{value}</div>
  <div class="record-caption">{caption}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_champion_spotlight(row):
    if row is None:
        return
    st.markdown(
        f"""
<div class="champ-hero">
  <img src="{champion_image_url(row['Champion'])}" alt="{row['Champion']}" />
  <div>
    <div class="champ-hero-title">Best Collective Champion</div>
    <div class="champ-hero-name">{row['Champion']}</div>
    <div class="champ-hero-meta">Win rate: {row['Win Rate %']:.1f}% | Games: {int(row['Games'])} | KDA: {row['KDA']:.2f}</div>
    <div class="champ-hero-meta">Played by: {row['Played By']}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_champion_gallery(df, title, stat_label):
    if df.empty:
        return
    st.markdown(f"### {title}")
    cols = st.columns(min(4, len(df)))
    for idx, (_, row) in enumerate(df.iterrows()):
        extra_line = ""
        if "Player" in row.index:
            extra_line = f"<div class=\"record-caption\">Player: {row['Player']}</div>"
        elif "Played By" in row.index:
            extra_line = f"<div class=\"record-caption\">Played by: {row['Played By']}</div>"
        with cols[idx % len(cols)]:
            st.image(champion_image_url(row["Champion"]), use_container_width=True)
            st.markdown(
                f"""
<div class="record-shell">
  <div class="record-value" style="font-size:1.1rem;">{row['Champion']}</div>
  <div class="record-caption">{stat_label}: {row['Win Rate %']:.1f}% in {int(row['Games'])} games</div>
  {extra_line}
</div>
""",
                unsafe_allow_html=True,
            )


def render_records(results):
    player_df = results["player_df"]
    participant_df = results["participant_df"]
    role_df = results["role_df"]
    pentakill_df = results["pentakill_df"]
    collective_champion_df = results["collective_champion_df"]
    player_champion_df = results["player_champion_df"]

    best_kda = top_record(player_df, ["KDA", "Games", "Kills / Game"], [False, False, False])
    most_deaths = top_record(player_df, ["Deaths / Game", "Games"], [False, False])
    most_kills_game = top_record(participant_df, ["Kills", "KDA"], [False, False])
    best_kills_avg = top_record(player_df, ["Kills / Game", "Games", "KDA"], [False, False, False])
    best_collective_champion = top_record(
        collective_champion_df[collective_champion_df["Games"] >= 2],
        ["Win Rate %", "Games", "KDA"],
        [False, False, False],
    )
    best_role = top_record(
        role_df[role_df["Games"] >= 2],
        ["Win Rate %", "Games"],
        [False, False],
    )

    render_champion_spotlight(best_collective_champion)

    st.markdown('<div class="section-note">Only matches with at least two tracked teammates are included in these records.</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if best_kda is not None:
            render_record_card(
                "Best Overall KDA",
                f"{best_kda['Player']} ({best_kda['KDA']:.2f})",
                f"{int(best_kda['Games'])} games",
            )
        if best_kills_avg is not None:
            render_record_card(
                "Most Kills / Game",
                f"{best_kills_avg['Player']} ({best_kills_avg['Kills / Game']:.2f})",
                f"KDA {best_kills_avg['KDA']:.2f}",
            )
    with col2:
        if most_deaths is not None:
            render_record_card(
                "Most Deaths / Game",
                f"{most_deaths['Player']} ({most_deaths['Deaths / Game']:.2f})",
                f"{int(most_deaths['Games'])} games",
            )
        if most_kills_game is not None:
            render_record_card(
                "Most Kills In One Game",
                f"{most_kills_game['Player']} ({int(most_kills_game['Kills'])} kills)",
                f"{most_kills_game['Champion']} in {most_kills_game['Match ID']}",
            )
    with col3:
        render_record_card(
            "Team Pentakills",
            str(int(pentakill_df["Pentakills"].sum()) if not pentakill_df.empty else 0),
            f"{len(pentakill_df)} pentakill games",
        )
        if best_role is not None:
            render_record_card(
                "Best Role Sample",
                f"{best_role['Player']} {best_role['Role']}",
                f"{best_role['Win Rate %']:.1f}% win rate across {int(best_role['Games'])} games",
            )

    if best_role is not None:
        st.caption(
            f"Best role sample so far: {best_role['Player']} in {best_role['Role']} at "
            f"{best_role['Win Rate %']:.1f}% across {int(best_role['Games'])} games."
        )

    st.markdown("## Player Summary")
    if player_df.empty:
        st.warning("No eligible matches were found after filtering for teams with at least two tracked players.")
    else:
        st.dataframe(
            player_df.sort_values(["KDA", "Win Rate %", "Games"], ascending=[False, False, False]),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("## Role Win Rates")
    role_view = role_df[role_df["Games"] >= 2].sort_values(["Role", "Win Rate %", "Games"], ascending=[True, False, False])
    if role_view.empty:
        st.info("No role records with at least 2 games yet.")
    else:
        st.dataframe(role_view, use_container_width=True, hide_index=True)

    st.markdown("## Pentakill Log")
    if pentakill_df.empty:
        st.info("No pentakills found in the sampled flex games.")
    else:
        st.dataframe(
            pentakill_df.sort_values(["Played", "Player"], ascending=[False, True]),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("## Collective Champion Records")
    st.markdown('<div class="section-note">Shows shared champion performance across the full flex group, including who has piloted each pick.</div>', unsafe_allow_html=True)
    collective_view = collective_champion_df[collective_champion_df["Games"] >= 2].sort_values(
        ["Win Rate %", "Games", "KDA"],
        ascending=[False, False, False],
    )
    if collective_view.empty:
        st.info("No collective champion samples with at least 2 games yet.")
    else:
        render_champion_gallery(collective_view.head(4), "Top Collective Picks", "Win rate")
        st.dataframe(collective_view, use_container_width=True, hide_index=True)

    st.markdown("## Champion Win Rates By Player")
    member_champion_view = player_champion_df[player_champion_df["Games"] >= 2].sort_values(
        ["Player", "Win Rate %", "Games"],
        ascending=[True, False, False],
    )
    if member_champion_view.empty:
        st.info("No player/champion combinations with at least 2 games yet.")
    else:
        render_champion_gallery(member_champion_view.head(4), "Hot Hand Champions", "Win rate")
        st.dataframe(member_champion_view, use_container_width=True, hide_index=True)

    with st.expander("Eligible Match Breakdown"):
        st.dataframe(
            results["match_df"].sort_values(["Played", "Players Count"], ascending=[False, False]),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Per-Game Player Log"):
        st.dataframe(
            participant_df.sort_values(["Played", "Kills"], ascending=[False, False]),
            use_container_width=True,
            hide_index=True,
        )


platform_label_options = list(PLATFORM_OPTIONS.keys())
default_platform_index = platform_label_options.index("Europe West")

with st.form("flex_team_records_form"):
    selected_platform_label = st.selectbox("Platform routing", platform_label_options, index=default_platform_index)
    match_count = st.slider("Recent ranked flex matches per player", min_value=10, max_value=100, value=40, step=10)
    raw_players = st.text_area(
        "Players",
        value="",
        height=260,
        placeholder=(
            "One person per line\n"
            "Single account:\n"
            "Wyn#EUW | Wyn\n\n"
            "Multiple accounts for one person:\n"
            "Welshy#CYMRU, Petez#Wales | Pete"
        ),
        help="Format each line as `account1, account2 | Person Name`. Only matches with at least two tracked people on the same team are counted.",
    )
    submitted = st.form_submit_button("Analyse Team Records", use_container_width=True)

st.caption("Riot requests are throttled and cached to stay under the 20 requests/1 second and 100 requests/2 minutes limits.")


if submitted:
    with st.spinner("Pulling flex match history and building team records..."):
        try:
            bundle = fetch_flex_bundle(
                api_key=RIOT_API_KEY,
                platform=PLATFORM_OPTIONS[selected_platform_label],
                raw_players=raw_players,
                match_count=match_count,
            )
            st.session_state["flex_team_records_results"] = {
                **bundle,
                **build_flex_team_dataset(bundle["match_details"], bundle["players"]),
            }
        except Exception as exc:
            st.error(str(exc))


results = st.session_state.get("flex_team_records_results")
if results:
    st.markdown("## Ranked Flex Profiles")
    st.dataframe(results["rank_df"], use_container_width=True, hide_index=True)
    for warning in results.get("profile_warnings", []):
        st.caption(warning)
    st.caption(
        f"Loaded {results['unique_matches']} unique flex matches from Riot. "
        f"{results['eligible_match_count']} matches contained at least two tracked players on the same team."
    )
    render_records(results)

st.caption(
    "This page uses Riot's account, summoner, league-exp, and match endpoints to build records from ranked flex games "
    "where at least two tracked players queued together."
)
