from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from itertools import combinations
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
MIN_GAMES_FOR_MEANINGFUL_STATS = 10
MIN_DUO_GAMES_FOR_FUN_STATS = MIN_GAMES_FOR_MEANINGFUL_STATS
MIN_CHAMPION_GAMES_FOR_RIVALRIES = MIN_GAMES_FOR_MEANINGFUL_STATS
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
.award-shell {
    min-height: 150px;
    padding: 1rem;
    border-radius: 16px;
    background: linear-gradient(145deg, rgba(35,30,56,0.98), rgba(16,25,38,0.98));
    border: 1px solid rgba(255,202,87,0.28);
    box-shadow: 0 12px 26px rgba(0,0,0,0.16);
    margin-bottom: 0.75rem;
}
.award-title {
    color: #ffd36b;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.35rem;
}
.award-player {
    color: #ffffff;
    font-size: 1.25rem;
    font-weight: 800;
    line-height: 1.2;
}
.award-detail {
    color: #cbd7eb;
    font-size: 0.9rem;
    margin-top: 0.4rem;
}
.rivalry-tile {
    display: flex;
    gap: 0.8rem;
    align-items: center;
    min-height: 120px;
    padding: 0.9rem;
    border-radius: 16px;
    background: linear-gradient(145deg, rgba(20,58,54,0.98), rgba(16,24,38,0.98));
    border: 1px solid rgba(94,220,181,0.28);
    margin-bottom: 0.75rem;
}
.rivalry-tile img {
    width: 72px;
    height: 72px;
    border-radius: 14px;
    object-fit: cover;
    box-shadow: 0 10px 20px rgba(0,0,0,0.24);
}
.rivalry-title {
    color: #74e2c7;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.rivalry-owner {
    color: #ffffff;
    font-size: 1.15rem;
    font-weight: 800;
    line-height: 1.2;
}
.rivalry-meta {
    color: #d8f7ef;
    font-size: 0.88rem;
    margin-top: 0.25rem;
}
.meter-track {
    width: 100%;
    height: 9px;
    border-radius: 999px;
    background: rgba(255,255,255,0.13);
    overflow: hidden;
    margin-top: 0.5rem;
}
.meter-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #ffcf70, #5ee6bd);
}
.duo-pill {
    display: inline-block;
    padding: 0.24rem 0.55rem;
    border-radius: 999px;
    background: rgba(126,182,255,0.16);
    color: #cfe2ff;
    font-size: 0.82rem;
    margin: 0.1rem 0.2rem 0.1rem 0;
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


def html_escape(value):
    return escape(str(value), quote=True)


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
            "vision": 0,
            "wards_placed": 0,
            "wards_killed": 0,
            "control_wards": 0,
            "cs": 0,
            "objective_damage": 0,
            "damage_taken": 0,
            "solo_kills": 0,
            "first_bloods": 0,
            "kill_participation": 0.0,
            "kill_participation_games": 0,
            "time_played_minutes": 0.0,
            "carry_score": 0.0,
            "pentakills": 0,
            "doublekills": 0,
            "triplekills": 0,
            "quadrakills": 0,
            "roles": defaultdict(lambda: {"games": 0, "wins": 0}),
            "champions": defaultdict(
                lambda: {
                    "games": 0,
                    "wins": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "damage": 0,
                    "gold": 0,
                    "carry_score": 0.0,
                }
            ),
        }
    )
    champion_totals = defaultdict(
        lambda: {
            "games": 0,
            "wins": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "damage": 0,
            "gold": 0,
            "carry_score": 0.0,
            "players": set(),
        }
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
        duration_minutes = safe_divide(info.get("gameDuration", 0), 60)

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
                kills = participant.get("kills", 0)
                deaths = participant.get("deaths", 0)
                assists = participant.get("assists", 0)
                damage = participant.get("totalDamageDealtToChampions", 0)
                gold = participant.get("goldEarned", 0)
                vision = participant.get("visionScore", 0)
                wards_placed = participant.get("wardsPlaced", 0)
                wards_killed = participant.get("wardsKilled", 0)
                cs = participant.get("totalMinionsKilled", 0) + participant.get("neutralMinionsKilled", 0)
                objective_damage = participant.get("damageDealtToObjectives", 0)
                damage_taken = participant.get("totalDamageTaken", 0)
                challenges = participant.get("challenges") or {}
                kill_participation = challenges.get("killParticipation")
                kill_participation_pct = (kill_participation * 100) if kill_participation is not None else 0.0
                solo_kills = challenges.get("soloKills", 0)
                control_wards = challenges.get("controlWardsPlaced", 0)
                first_bloods = int(bool(participant.get("firstBloodKill") or participant.get("firstBloodAssist")))
                kda = calculate_kda(kills, assists, deaths)
                cs_per_minute = safe_divide(cs, duration_minutes)
                carry_score = (
                    (kills * 2.0)
                    + assists
                    - (deaths * 1.35)
                    + (damage / 1000)
                    + (gold / 1500)
                    + (objective_damage / 2500)
                    + (vision / 5)
                    + (solo_kills * 2)
                    + (kill_participation_pct / 18)
                    + (3 if win else 0)
                )

                totals = player_totals[person_name]
                totals["games"] += 1
                totals["wins"] += int(win)
                totals["kills"] += kills
                totals["deaths"] += deaths
                totals["assists"] += assists
                totals["damage"] += damage
                totals["gold"] += gold
                totals["vision"] += vision
                totals["wards_placed"] += wards_placed
                totals["wards_killed"] += wards_killed
                totals["control_wards"] += control_wards
                totals["cs"] += cs
                totals["objective_damage"] += objective_damage
                totals["damage_taken"] += damage_taken
                totals["solo_kills"] += solo_kills
                totals["first_bloods"] += first_bloods
                totals["time_played_minutes"] += duration_minutes
                totals["carry_score"] += carry_score
                if kill_participation is not None:
                    totals["kill_participation"] += kill_participation_pct
                    totals["kill_participation_games"] += 1
                totals["pentakills"] += participant.get("pentaKills", 0)
                totals["doublekills"] += participant.get("doubleKills", 0)
                totals["triplekills"] += participant.get("tripleKills", 0)
                totals["quadrakills"] += participant.get("quadraKills", 0)
                totals["roles"][role_code]["games"] += 1
                totals["roles"][role_code]["wins"] += int(win)

                champion_stats = totals["champions"][champion]
                champion_stats["games"] += 1
                champion_stats["wins"] += int(win)
                champion_stats["kills"] += kills
                champion_stats["deaths"] += deaths
                champion_stats["assists"] += assists
                champion_stats["damage"] += damage
                champion_stats["gold"] += gold
                champion_stats["carry_score"] += carry_score

                collective_stats = champion_totals[champion]
                collective_stats["games"] += 1
                collective_stats["wins"] += int(win)
                collective_stats["kills"] += kills
                collective_stats["deaths"] += deaths
                collective_stats["assists"] += assists
                collective_stats["damage"] += damage
                collective_stats["gold"] += gold
                collective_stats["carry_score"] += carry_score
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
                        "Team ID": participant.get("teamId"),
                        "Player": person_name,
                        "Account": player["display_name"],
                        "Champion": champion,
                        "Role": ROLE_LABELS.get(role_code, role_code.title()),
                        "Result": "Win" if win else "Loss",
                        "Win": int(win),
                        "Kills": kills,
                        "Deaths": deaths,
                        "Assists": assists,
                        "KDA": round(kda, 2),
                        "Damage to Champs": damage,
                        "Gold": gold,
                        "Vision Score": vision,
                        "Wards Placed": wards_placed,
                        "Wards Killed": wards_killed,
                        "Control Wards": control_wards,
                        "CS": cs,
                        "CS / Min": round(cs_per_minute, 2),
                        "Objective Damage": objective_damage,
                        "Damage Taken": damage_taken,
                        "Kill Participation %": round(kill_participation_pct, 1),
                        "Solo Kills": solo_kills,
                        "First Blood": first_bloods,
                        "Game Minutes": round(duration_minutes, 1),
                        "Carry Score": round(carry_score, 2),
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
                            "Kills": kills,
                            "Deaths": deaths,
                            "Assists": assists,
                            "Pentakills": participant.get("pentaKills", 0),
                        }
                    )

            match_rows.append(
                {
                    "Match ID": metadata.get("matchId", match_id),
                    "Played": format_match_timestamp(info.get("gameEndTimestamp") or info.get("gameCreation")),
                    "Team ID": team_participants[0].get("teamId") if team_participants else "",
                    "Tracked Players Together": ", ".join(sorted(tracked_names)),
                    "Players Count": len(tracked_names),
                    "Result": "Win" if team_win else "Loss",
                    "Game Minutes": round(duration_minutes, 1),
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
                "Vision / Game": round(safe_divide(stats["vision"], games), 2),
                "CS / Min": round(safe_divide(stats["cs"], stats["time_played_minutes"]), 2),
                "Objective Damage / Game": round(safe_divide(stats["objective_damage"], games), 0),
                "Damage Taken / Game": round(safe_divide(stats["damage_taken"], games), 0),
                "Avg KP %": round(safe_divide(stats["kill_participation"], stats["kill_participation_games"]), 1),
                "Solo Kills": stats["solo_kills"],
                "First Bloods": stats["first_bloods"],
                "Control Wards / Game": round(safe_divide(stats["control_wards"], games), 2),
                "Carry Score / Game": round(safe_divide(stats["carry_score"], games), 2),
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
                    "Kills / Game": round(safe_divide(champion_stats["kills"], games_played), 2),
                    "Damage / Game": round(safe_divide(champion_stats["damage"], games_played), 0),
                    "Carry Score / Game": round(safe_divide(champion_stats["carry_score"], games_played), 2),
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
                "Kills / Game": round(safe_divide(stats["kills"], games), 2),
                "Damage / Game": round(safe_divide(stats["damage"], games), 0),
                "Carry Score / Game": round(safe_divide(stats["carry_score"], games), 2),
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
                "Vision / Game",
                "CS / Min",
                "Objective Damage / Game",
                "Damage Taken / Game",
                "Avg KP %",
                "Solo Kills",
                "First Bloods",
                "Control Wards / Game",
                "Carry Score / Game",
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
            columns=[
                "Champion",
                "Games",
                "Wins",
                "Win Rate %",
                "KDA",
                "Kills / Game",
                "Damage / Game",
                "Carry Score / Game",
                "Players Used",
                "Played By",
            ],
        ),
        "player_champion_df": pd.DataFrame(
            player_champion_rows,
            columns=[
                "Player",
                "Champion",
                "Games",
                "Wins",
                "Win Rate %",
                "KDA",
                "Kills / Game",
                "Damage / Game",
                "Carry Score / Game",
            ],
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
                "Team ID",
                "Player",
                "Account",
                "Champion",
                "Role",
                "Result",
                "Win",
                "Kills",
                "Deaths",
                "Assists",
                "KDA",
                "Damage to Champs",
                "Gold",
                "Vision Score",
                "Wards Placed",
                "Wards Killed",
                "Control Wards",
                "CS",
                "CS / Min",
                "Objective Damage",
                "Damage Taken",
                "Kill Participation %",
                "Solo Kills",
                "First Blood",
                "Game Minutes",
                "Carry Score",
                "Pentakills",
            ],
        ),
        "match_df": pd.DataFrame(
            match_rows,
            columns=[
                "Match ID",
                "Played",
                "Team ID",
                "Tracked Players Together",
                "Players Count",
                "Result",
                "Game Minutes",
            ],
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
  <div class="record-label">{html_escape(title)}</div>
  <div class="record-value">{html_escape(value)}</div>
  <div class="record-caption">{html_escape(caption)}</div>
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
  <img src="{champion_image_url(row['Champion'])}" alt="{html_escape(row['Champion'])}" />
  <div>
    <div class="champ-hero-title">Best Collective Champion</div>
    <div class="champ-hero-name">{html_escape(row['Champion'])}</div>
    <div class="champ-hero-meta">Win rate: {row['Win Rate %']:.1f}% | Games: {int(row['Games'])} | KDA: {row['KDA']:.2f}</div>
    <div class="champ-hero-meta">Played by: {html_escape(row['Played By'])}</div>
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
            extra_line = f"<div class=\"record-caption\">Player: {html_escape(row['Player'])}</div>"
        elif "Played By" in row.index:
            extra_line = f"<div class=\"record-caption\">Played by: {html_escape(row['Played By'])}</div>"
        with cols[idx % len(cols)]:
            st.image(champion_image_url(row["Champion"]), use_container_width=True)
            st.markdown(
                f"""
<div class="record-shell">
  <div class="record-value" style="font-size:1.1rem;">{html_escape(row['Champion'])}</div>
  <div class="record-caption">{stat_label}: {row['Win Rate %']:.1f}% in {int(row['Games'])} games</div>
  {extra_line}
</div>
""",
                unsafe_allow_html=True,
            )


def render_award_card(title, player, value, detail):
    st.markdown(
        f"""
<div class="award-shell">
  <div class="award-title">{html_escape(title)}</div>
  <div class="award-player">{html_escape(player)}</div>
  <div class="record-value" style="font-size:1.1rem;">{html_escape(value)}</div>
  <div class="award-detail">{html_escape(detail)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def build_awards(player_df):
    if player_df.empty:
        return []

    candidates = player_df[player_df["Games"] >= MIN_GAMES_FOR_MEANINGFUL_STATS]
    if candidates.empty:
        return []

    awards = []

    def add_award(title, row, value, detail):
        if row is not None:
            awards.append(
                {
                    "Title": title,
                    "Player": row["Player"],
                    "Value": value,
                    "Detail": detail,
                }
            )

    best_win_rate = top_record(candidates, ["Win Rate %", "Games", "KDA"], [False, False, False])
    add_award(
        "Lobby Optimizer",
        best_win_rate,
        f"{best_win_rate['Win Rate %']:.1f}% win rate" if best_win_rate is not None else "",
        f"{int(best_win_rate['Wins'])}-{int(best_win_rate['Games'] - best_win_rate['Wins'])} over {int(best_win_rate['Games'])} games"
        if best_win_rate is not None
        else "",
    )

    best_carry_score = top_record(candidates, ["Carry Score / Game", "Games"], [False, False])
    add_award(
        "Main Character Score",
        best_carry_score,
        f"{best_carry_score['Carry Score / Game']:.2f} / game" if best_carry_score is not None else "",
        "Kills, assists, damage, vision, objectives, KP, and wins mashed into one loud number.",
    )

    best_damage = top_record(candidates, ["Damage / Game", "Games"], [False, False])
    add_award(
        "Damage Department",
        best_damage,
        f"{best_damage['Damage / Game']:.0f} / game" if best_damage is not None else "",
        f"KDA {best_damage['KDA']:.2f} across {int(best_damage['Games'])} games" if best_damage is not None else "",
    )

    cleanest = top_record(candidates, ["Deaths / Game", "KDA", "Games"], [True, False, False])
    add_award(
        "Cleanest Hands",
        cleanest,
        f"{cleanest['Deaths / Game']:.2f} deaths / game" if cleanest is not None else "",
        "Best at keeping the grey screen away.",
    )

    limit_tester = top_record(candidates, ["Deaths / Game", "Games"], [False, False])
    add_award(
        "Limit Tester",
        limit_tester,
        f"{limit_tester['Deaths / Game']:.2f} deaths / game" if limit_tester is not None else "",
        "The VOD probably contains several important learning moments.",
    )

    vision_lead = top_record(candidates, ["Vision / Game", "Games"], [False, False])
    add_award(
        "Vision Taxpayer",
        vision_lead,
        f"{vision_lead['Vision / Game']:.2f} vision / game" if vision_lead is not None else "",
        f"{vision_lead['Control Wards / Game']:.2f} control wards / game" if vision_lead is not None else "",
    )

    objective_lead = top_record(candidates, ["Objective Damage / Game", "Games"], [False, False])
    add_award(
        "Objective Caller",
        objective_lead,
        f"{objective_lead['Objective Damage / Game']:.0f} / game" if objective_lead is not None else "",
        "Turrets, dragons, grubs, barons, and anything else with an HP bar.",
    )

    farm_lead = top_record(candidates, ["CS / Min", "Games"], [False, False])
    add_award(
        "Farm Simulator",
        farm_lead,
        f"{farm_lead['CS / Min']:.2f} CS / min" if farm_lead is not None else "",
        f"{farm_lead['Gold / Game']:.0f} gold / game" if farm_lead is not None else "",
    )

    solo_kill_lead = top_record(candidates, ["Solo Kills", "Games"], [False, False])
    if solo_kill_lead is not None and solo_kill_lead["Solo Kills"] > 0:
        add_award(
            "Solo Kill Hunter",
            solo_kill_lead,
            f"{int(solo_kill_lead['Solo Kills'])} solo kills",
            f"{int(solo_kill_lead['Games'])} games sampled",
        )

    first_blood_lead = top_record(candidates, ["First Bloods", "Games"], [False, False])
    if first_blood_lead is not None and first_blood_lead["First Bloods"] > 0:
        add_award(
            "First Blood Button",
            first_blood_lead,
            f"{int(first_blood_lead['First Bloods'])} first bloods",
            "Fastest to turn loading screen confidence into action.",
        )

    return awards


def render_awards(player_df):
    awards = build_awards(player_df)
    if not awards:
        st.info(f"Group awards unlock once at least one player has {MIN_GAMES_FOR_MEANINGFUL_STATS} eligible games.")
        return

    st.markdown("## Group Awards")
    st.markdown(
        '<div class="section-note">Mostly useful, partly unfair, all based on the sampled flex games.</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for idx, award in enumerate(awards[:8]):
        with cols[idx % len(cols)]:
            render_award_card(award["Title"], award["Player"], award["Value"], award["Detail"])


def compare_pair_values(left_value, right_value, higher_is_better=True):
    if left_value == right_value:
        return 0
    if higher_is_better:
        return 1 if left_value > right_value else -1
    return 1 if left_value < right_value else -1


def pair_banter_line(row):
    win_rate = row["Win Rate %"]
    deaths = row["Combined Deaths / Game"]
    games = int(row["Games"])
    if games < MIN_DUO_GAMES_FOR_FUN_STATS:
        return "Small sample. Bring receipts before starting arguments."
    if win_rate >= 70:
        return "Queue together before the spreadsheet gets suspicious."
    if win_rate <= 40:
        return "The numbers suggest a diplomatic lane swap."
    if deaths >= 14:
        return "High-action duo. Great for highlights, stressful for towers."
    if row["Combined KDA"] >= 4:
        return "Efficient pairing. Quietly ruining enemy evenings."
    return "Balanced sample. The blame economy remains open."


def build_pair_stats(participant_df):
    if participant_df.empty:
        return pd.DataFrame()

    pair_totals = {}
    grouped = participant_df.groupby(["Match ID", "Team ID"], dropna=False)

    for _, group in grouped:
        players = group.drop_duplicates("Player").sort_values("Player")
        if len(players) < 2:
            continue

        for left, right in combinations([row for _, row in players.iterrows()], 2):
            key = (left["Player"], right["Player"])
            if key not in pair_totals:
                pair_totals[key] = {
                    "Player A": key[0],
                    "Player B": key[1],
                    "Games": 0,
                    "Wins": 0,
                    "Kills": 0,
                    "Deaths": 0,
                    "Assists": 0,
                    "Damage": 0,
                    "Gold": 0,
                    "Carry Score": 0.0,
                    "A Kill Leads": 0,
                    "B Kill Leads": 0,
                    "A Damage Leads": 0,
                    "B Damage Leads": 0,
                    "A KDA Leads": 0,
                    "B KDA Leads": 0,
                    "A Carry Leads": 0,
                    "B Carry Leads": 0,
                    "Tied Carry Games": 0,
                }

            stats = pair_totals[key]
            stats["Games"] += 1
            stats["Wins"] += int(left["Result"] == "Win")
            stats["Kills"] += left["Kills"] + right["Kills"]
            stats["Deaths"] += left["Deaths"] + right["Deaths"]
            stats["Assists"] += left["Assists"] + right["Assists"]
            stats["Damage"] += left["Damage to Champs"] + right["Damage to Champs"]
            stats["Gold"] += left["Gold"] + right["Gold"]
            stats["Carry Score"] += left.get("Carry Score", 0) + right.get("Carry Score", 0)

            comparisons = [
                ("Kills", "A Kill Leads", "B Kill Leads", True),
                ("Damage to Champs", "A Damage Leads", "B Damage Leads", True),
                ("KDA", "A KDA Leads", "B KDA Leads", True),
                ("Carry Score", "A Carry Leads", "B Carry Leads", True),
            ]
            for metric, left_key, right_key, higher_is_better in comparisons:
                result = compare_pair_values(left.get(metric, 0), right.get(metric, 0), higher_is_better)
                if result > 0:
                    stats[left_key] += 1
                elif result < 0:
                    stats[right_key] += 1
                elif metric == "Carry Score":
                    stats["Tied Carry Games"] += 1

    rows = []
    for stats in pair_totals.values():
        games = stats["Games"]
        a_carry_leads = stats["A Carry Leads"]
        b_carry_leads = stats["B Carry Leads"]
        carry_edge = "Tied"
        if a_carry_leads > b_carry_leads:
            carry_edge = stats["Player A"]
        elif b_carry_leads > a_carry_leads:
            carry_edge = stats["Player B"]

        row = {
            "Duo": f"{stats['Player A']} + {stats['Player B']}",
            "Player A": stats["Player A"],
            "Player B": stats["Player B"],
            "Games": games,
            "Wins": stats["Wins"],
            "Win Rate %": round(safe_divide(stats["Wins"], games) * 100, 1),
            "Combined KDA": round(calculate_kda(stats["Kills"], stats["Assists"], stats["Deaths"]), 2),
            "Combined Kills / Game": round(safe_divide(stats["Kills"], games), 2),
            "Combined Deaths / Game": round(safe_divide(stats["Deaths"], games), 2),
            "Combined Damage / Game": round(safe_divide(stats["Damage"], games), 0),
            "Combined Gold / Game": round(safe_divide(stats["Gold"], games), 0),
            "Combined Carry Score / Game": round(safe_divide(stats["Carry Score"], games), 2),
            "Kill Lead": f"{stats['Player A']} {stats['A Kill Leads']} - {stats['B Kill Leads']} {stats['Player B']}",
            "Damage Lead": f"{stats['Player A']} {stats['A Damage Leads']} - {stats['B Damage Leads']} {stats['Player B']}",
            "KDA Lead": f"{stats['Player A']} {stats['A KDA Leads']} - {stats['B KDA Leads']} {stats['Player B']}",
            "Carry Edge": carry_edge,
            "Carry Lead": f"{stats['Player A']} {a_carry_leads} - {b_carry_leads} {stats['Player B']}",
        }
        row["Read"] = pair_banter_line(row)
        rows.append(row)

    return pd.DataFrame(rows)


def build_duo_winrate_matrix(pair_df, players):
    matrix = pd.DataFrame(index=players, columns=players, dtype=float)
    for player in players:
        matrix.loc[player, player] = None
    for _, row in pair_df.iterrows():
        matrix.loc[row["Player A"], row["Player B"]] = row["Win Rate %"]
        matrix.loc[row["Player B"], row["Player A"]] = row["Win Rate %"]
    return matrix


def build_duo_record_matrix(pair_df, players):
    matrix = pd.DataFrame("-", index=players, columns=players)
    for _, row in pair_df.iterrows():
        value = f"{int(row['Wins'])}-{int(row['Games'] - row['Wins'])} ({row['Win Rate %']:.1f}%)"
        matrix.loc[row["Player A"], row["Player B"]] = value
        matrix.loc[row["Player B"], row["Player A"]] = value
    return matrix


def render_duo_matrix(pair_df, players):
    if pair_df.empty or len(players) < 2:
        return

    st.markdown("### Duo Win Rate Matrix")
    winrate_matrix = build_duo_winrate_matrix(pair_df, players)
    styled_matrix = winrate_matrix.style.format(lambda value: "-" if pd.isna(value) else f"{value:.1f}%").background_gradient(
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
        axis=None,
    )
    st.dataframe(styled_matrix, use_container_width=True)

    with st.expander("Duo record matrix"):
        st.dataframe(build_duo_record_matrix(pair_df, players), use_container_width=True)


def build_duel_summary(participant_df, player_a, player_b):
    if participant_df.empty or player_a == player_b:
        return pd.DataFrame(), pd.DataFrame()

    key_columns = ["Match ID", "Team ID"]
    player_a_games = participant_df[participant_df["Player"] == player_a]
    player_b_games = participant_df[participant_df["Player"] == player_b]
    shared = player_a_games.merge(player_b_games, on=key_columns, suffixes=(" A", " B"))
    if shared.empty:
        return pd.DataFrame(), shared

    metrics = [
        ("Kills", True),
        ("Deaths", False),
        ("Assists", True),
        ("KDA", True),
        ("Damage to Champs", True),
        ("Gold", True),
        ("Vision Score", True),
        ("Objective Damage", True),
        ("Kill Participation %", True),
        ("Carry Score", True),
    ]

    rows = []
    for metric, higher_is_better in metrics:
        left_values = shared[f"{metric} A"]
        right_values = shared[f"{metric} B"]
        left_leads = 0
        right_leads = 0
        ties = 0
        for left_value, right_value in zip(left_values, right_values):
            result = compare_pair_values(left_value, right_value, higher_is_better)
            if result > 0:
                left_leads += 1
            elif result < 0:
                right_leads += 1
            else:
                ties += 1

        edge = "Tied"
        left_average = left_values.mean()
        right_average = right_values.mean()
        average_result = compare_pair_values(left_average, right_average, higher_is_better)
        if average_result > 0:
            edge = player_a
        elif average_result < 0:
            edge = player_b

        rows.append(
            {
                "Metric": metric,
                f"{player_a} Avg": round(left_average, 2),
                f"{player_b} Avg": round(right_average, 2),
                "Edge": edge,
                f"{player_a} Leads": left_leads,
                f"{player_b} Leads": right_leads,
                "Ties": ties,
            }
        )

    return pd.DataFrame(rows), shared


def render_duel_arena(participant_df):
    players = sorted(participant_df["Player"].dropna().unique().tolist()) if not participant_df.empty else []
    if len(players) < 2:
        return

    st.markdown("### Teammate Head-to-Head Arena")
    duel_cols = st.columns(2)
    with duel_cols[0]:
        player_a = st.selectbox("Player A", players, index=0, key="flex_duel_player_a")
    with duel_cols[1]:
        default_b_index = 1 if len(players) > 1 else 0
        player_b = st.selectbox("Player B", players, index=default_b_index, key="flex_duel_player_b")

    if player_a == player_b:
        st.info("Pick two different players to start a teammate argument.")
        return

    duel_df, shared = build_duel_summary(participant_df, player_a, player_b)
    if duel_df.empty:
        st.info("These two do not have same-team games in the current sample.")
        return

    shared_games = len(shared)
    if shared_games < MIN_GAMES_FOR_MEANINGFUL_STATS:
        st.info(
            f"{player_a} and {player_b} have {shared_games} shared same-team games. "
            f"Head-to-head stats need {MIN_GAMES_FOR_MEANINGFUL_STATS} games."
        )
        return

    shared_wins = int(shared["Win A"].sum()) if "Win A" in shared.columns else int((shared["Result A"] == "Win").sum())
    metric_cards = st.columns(3)
    with metric_cards[0]:
        render_record_card(
            "Shared Record",
            f"{shared_wins}-{shared_games - shared_wins}",
            f"{safe_divide(shared_wins, shared_games) * 100:.1f}% across {shared_games} games",
        )
    for idx, metric in enumerate(["Kills", "Carry Score"]):
        row = duel_df[duel_df["Metric"] == metric].iloc[0]
        with metric_cards[idx + 1]:
            render_record_card(
                f"{metric} Edge",
                row["Edge"],
                f"{player_a} {int(row[f'{player_a} Leads'])} - {int(row[f'{player_b} Leads'])} {player_b}",
            )

    chart_df = duel_df.set_index("Metric")[[f"{player_a} Avg", f"{player_b} Avg"]]
    st.bar_chart(chart_df.loc[["Kills", "Deaths", "Assists", "KDA", "Carry Score"]])
    st.dataframe(duel_df, use_container_width=True, hide_index=True)


def build_champion_rivalries(player_champion_df, min_games):
    if player_champion_df.empty:
        return pd.DataFrame()

    contenders = player_champion_df[player_champion_df["Games"] >= min_games].copy()
    rows = []
    for champion, group in contenders.groupby("Champion"):
        if group["Player"].nunique() < 2:
            continue
        ordered = group.sort_values(
            ["Win Rate %", "Games", "KDA", "Carry Score / Game"],
            ascending=[False, False, False, False],
        )
        owner = ordered.iloc[0]
        runner_up = ordered.iloc[1]
        gap = owner["Win Rate %"] - runner_up["Win Rate %"]
        if gap >= 25:
            claim = f"{owner['Player']} owns this pick right now."
        elif gap <= 5:
            claim = "Too close to call. Settle it in flex."
        else:
            claim = f"{owner['Player']} has the lead, but the door is open."
        rows.append(
            {
                "Champion": champion,
                "Current Owner": owner["Player"],
                "Owner WR %": round(owner["Win Rate %"], 1),
                "Owner Games": int(owner["Games"]),
                "Owner KDA": round(owner["KDA"], 2),
                "Owner Carry Score / Game": round(owner["Carry Score / Game"], 2),
                "Runner-up": runner_up["Player"],
                "Runner-up WR %": round(runner_up["Win Rate %"], 1),
                "Runner-up Games": int(runner_up["Games"]),
                "Gap %": round(gap, 1),
                "Contenders": ", ".join(ordered["Player"].tolist()),
                "Claim": claim,
            }
        )

    return pd.DataFrame(rows)


def render_rivalry_tiles(rivalry_df):
    if rivalry_df.empty:
        return

    cols = st.columns(min(3, len(rivalry_df)))
    for idx, (_, row) in enumerate(rivalry_df.head(6).iterrows()):
        fill_width = max(8, min(100, row["Owner WR %"]))
        with cols[idx % len(cols)]:
            st.markdown(
                f"""
<div class="rivalry-tile">
  <img src="{champion_image_url(row['Champion'])}" alt="{html_escape(row['Champion'])}" />
  <div>
    <div class="rivalry-title">{html_escape(row['Champion'])} rights</div>
    <div class="rivalry-owner">{html_escape(row['Current Owner'])}</div>
    <div class="rivalry-meta">{row['Owner WR %']:.1f}% WR, {int(row['Owner Games'])} games, {row['Owner KDA']:.2f} KDA</div>
    <div class="meter-track"><div class="meter-fill" style="width:{fill_width:.1f}%"></div></div>
    <div class="rivalry-meta">Next: {html_escape(row['Runner-up'])} at {row['Runner-up WR %']:.1f}%</div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )


def render_champion_rivalries(player_champion_df):
    if player_champion_df.empty:
        return

    st.markdown("## Champion Claim Court")
    st.markdown(
        '<div class="section-note">For champions played by multiple tracked players: who currently has the best win rate, and who is closest to stealing the pick.</div>',
        unsafe_allow_html=True,
    )

    max_games = int(player_champion_df["Games"].max()) if not player_champion_df.empty else 0
    min_games = MIN_CHAMPION_GAMES_FOR_RIVALRIES
    if max_games >= MIN_CHAMPION_GAMES_FOR_RIVALRIES:
        min_games = st.slider(
            "Minimum games for champion claims",
            min_value=MIN_CHAMPION_GAMES_FOR_RIVALRIES,
            max_value=max_games,
            value=MIN_CHAMPION_GAMES_FOR_RIVALRIES,
            step=1,
            key="flex_champion_claim_min_games",
        )
    rivalry_df = build_champion_rivalries(player_champion_df, min_games)
    if rivalry_df.empty:
        st.info(
            f"No champions have at least {min_games} games from two different tracked players yet."
        )
        return

    rivalry_view = rivalry_df.sort_values(["Owner WR %", "Owner Games", "Gap %"], ascending=[False, False, False])
    render_rivalry_tiles(rivalry_view)

    champion_options = rivalry_view["Champion"].tolist()
    selected_champion = st.selectbox("Inspect contested champion", champion_options, key="flex_contested_champion")
    champion_rows = player_champion_df[
        (player_champion_df["Champion"] == selected_champion) & (player_champion_df["Games"] >= min_games)
    ].sort_values(["Win Rate %", "Games", "KDA"], ascending=[False, False, False])

    st.bar_chart(champion_rows.set_index("Player")[["Win Rate %", "KDA", "Carry Score / Game"]])
    st.dataframe(rivalry_view, use_container_width=True, hide_index=True)

    with st.expander(f"{selected_champion} player breakdown"):
        st.dataframe(champion_rows, use_container_width=True, hide_index=True)

    cursed = player_champion_df[player_champion_df["Games"] >= min_games].sort_values(
        ["Win Rate %", "Games", "KDA", "Carry Score / Game"],
        ascending=[True, False, True, True],
    )
    if not cursed.empty:
        practice_view = cursed.head(10).copy()
        st.markdown("### Needs Practice List")
        st.caption("Low win-rate player/champion samples. Useful for banter, better for finding review targets.")
        st.dataframe(practice_view, use_container_width=True, hide_index=True)


def build_player_form(participant_df):
    if participant_df.empty:
        return pd.DataFrame()

    rows = []
    for player, group in participant_df.sort_values("Played").groupby("Player"):
        results = group["Result"].tolist()
        recent = results[-5:]
        current_result = recent[-1] if recent else ""
        current_streak = 0
        for result in reversed(results):
            if result == current_result:
                current_streak += 1
            else:
                break

        best_win_streak = 0
        best_loss_streak = 0
        active_wins = 0
        active_losses = 0
        for result in results:
            if result == "Win":
                active_wins += 1
                active_losses = 0
            else:
                active_losses += 1
                active_wins = 0
            best_win_streak = max(best_win_streak, active_wins)
            best_loss_streak = max(best_loss_streak, active_losses)

        rows.append(
            {
                "Player": player,
                "Recent Form": "-".join("W" if result == "Win" else "L" for result in recent),
                "Recent WR %": round(safe_divide(sum(result == "Win" for result in recent), len(recent)) * 100, 1),
                "Current Streak": f"{current_streak} {current_result.lower()}s" if current_result else "",
                "Best Win Streak": best_win_streak,
                "Longest Loss Skid": best_loss_streak,
                "Games": len(results),
            }
        )
    return pd.DataFrame(rows)


def build_team_timeline(match_df):
    if match_df.empty:
        return pd.DataFrame()
    timeline = match_df.sort_values("Played").copy()
    timeline["Win"] = (timeline["Result"] == "Win").astype(int)
    timeline["Game"] = range(1, len(timeline) + 1)
    timeline["Cumulative WR %"] = (timeline["Win"].cumsum() / timeline["Game"]) * 100
    return timeline[["Game", "Cumulative WR %"]].set_index("Game")


def render_form_section(participant_df, match_df):
    form_df = build_player_form(participant_df)
    if form_df.empty:
        return
    form_df = form_df[form_df["Games"] >= MIN_GAMES_FOR_MEANINGFUL_STATS]
    if form_df.empty:
        st.info(f"Form check unlocks once a player has {MIN_GAMES_FOR_MEANINGFUL_STATS} eligible games.")
        return

    st.markdown("## Form Check")
    timeline = build_team_timeline(match_df)
    if len(match_df) >= MIN_GAMES_FOR_MEANINGFUL_STATS and not timeline.empty:
        st.line_chart(timeline)

    hot = top_record(form_df, ["Recent WR %", "Best Win Streak", "Games"], [False, False, False])
    cold = top_record(form_df, ["Recent WR %", "Longest Loss Skid", "Games"], [True, False, False])
    cols = st.columns(2)
    with cols[0]:
        render_record_card(
            "Hottest Recent Form",
            f"{hot['Player']} ({hot['Recent Form']})",
            f"{hot['Recent WR %']:.1f}% in last {min(5, int(hot['Games']))} games",
        )
    with cols[1]:
        render_record_card(
            "Review The Skid",
            f"{cold['Player']} ({cold['Recent Form']})",
            f"Longest loss skid: {int(cold['Longest Loss Skid'])}",
        )

    st.dataframe(
        form_df.sort_values(["Recent WR %", "Best Win Streak"], ascending=[False, False]),
        use_container_width=True,
        hide_index=True,
    )


def render_duo_section(participant_df):
    pair_df = build_pair_stats(participant_df)
    if pair_df.empty:
        return

    st.markdown("## Duo Lab")
    st.markdown(
        '<div class="section-note">Pair stats only count games where both players were tracked on the same team.</div>',
        unsafe_allow_html=True,
    )

    duo_view = pair_df[pair_df["Games"] >= MIN_DUO_GAMES_FOR_FUN_STATS].copy()
    if duo_view.empty:
        st.info(f"Duo stats unlock once a pair has {MIN_DUO_GAMES_FOR_FUN_STATS} same-team games.")
        return
    players = sorted(set(duo_view["Player A"]).union(duo_view["Player B"]))

    best_duo = top_record(duo_view, ["Win Rate %", "Games", "Combined KDA"], [False, False, False])
    murder_duo = top_record(duo_view, ["Combined Kills / Game", "Combined Damage / Game"], [False, False])
    chaos_duo = top_record(duo_view, ["Combined Deaths / Game", "Games"], [False, False])

    cols = st.columns(3)
    with cols[0]:
        render_record_card(
            "Best Duo",
            best_duo["Duo"],
            f"{best_duo['Win Rate %']:.1f}% WR across {int(best_duo['Games'])} games",
        )
    with cols[1]:
        render_record_card(
            "Most Violent Pair",
            murder_duo["Duo"],
            f"{murder_duo['Combined Kills / Game']:.2f} kills / game",
        )
    with cols[2]:
        render_record_card(
            "Most Chaotic Pair",
            chaos_duo["Duo"],
            f"{chaos_duo['Combined Deaths / Game']:.2f} deaths / game",
        )

    render_duo_matrix(duo_view, players)
    render_duel_arena(participant_df)

    st.markdown("### Duo Leaderboard")
    st.dataframe(
        duo_view.sort_values(["Win Rate %", "Games", "Combined Carry Score / Game"], ascending=[False, False, False]),
        use_container_width=True,
        hide_index=True,
    )


def render_records(results):
    player_df = results["player_df"]
    participant_df = results["participant_df"]
    match_df = results["match_df"]
    role_df = results["role_df"]
    pentakill_df = results["pentakill_df"]
    collective_champion_df = results["collective_champion_df"]
    player_champion_df = results["player_champion_df"]
    meaningful_player_df = player_df[player_df["Games"] >= MIN_GAMES_FOR_MEANINGFUL_STATS]
    meaningful_role_df = role_df[role_df["Games"] >= MIN_GAMES_FOR_MEANINGFUL_STATS]
    meaningful_collective_champion_df = collective_champion_df[
        collective_champion_df["Games"] >= MIN_GAMES_FOR_MEANINGFUL_STATS
    ]
    meaningful_player_champion_df = player_champion_df[
        player_champion_df["Games"] >= MIN_GAMES_FOR_MEANINGFUL_STATS
    ]
    meaningful_players = set(meaningful_player_df["Player"].tolist())
    meaningful_participant_df = participant_df[participant_df["Player"].isin(meaningful_players)]

    best_kda = top_record(meaningful_player_df, ["KDA", "Games", "Kills / Game"], [False, False, False])
    most_deaths = top_record(meaningful_player_df, ["Deaths / Game", "Games"], [False, False])
    most_kills_game = top_record(meaningful_participant_df, ["Kills", "KDA"], [False, False])
    best_kills_avg = top_record(meaningful_player_df, ["Kills / Game", "Games", "KDA"], [False, False, False])
    best_collective_champion = top_record(
        meaningful_collective_champion_df,
        ["Win Rate %", "Games", "KDA"],
        [False, False, False],
    )
    best_role = top_record(
        meaningful_role_df,
        ["Win Rate %", "Games"],
        [False, False],
    )

    render_champion_spotlight(best_collective_champion)

    st.markdown(
        f'<div class="section-note">Only matches with at least two tracked teammates are included. '
        f'Leaderboard stats below require at least {MIN_GAMES_FOR_MEANINGFUL_STATS} games.</div>',
        unsafe_allow_html=True,
    )

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

    render_awards(player_df)
    render_duo_section(participant_df)
    render_form_section(participant_df, match_df)

    st.markdown("## Player Summary")
    if meaningful_player_df.empty:
        if player_df.empty:
            st.warning("No eligible matches were found after filtering for teams with at least two tracked players.")
        else:
            st.info(f"No player has {MIN_GAMES_FOR_MEANINGFUL_STATS} eligible games yet.")
    else:
        st.dataframe(
            meaningful_player_df.sort_values(["KDA", "Win Rate %", "Games"], ascending=[False, False, False]),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("## Role Win Rates")
    role_view = meaningful_role_df.sort_values(["Role", "Win Rate %", "Games"], ascending=[True, False, False])
    if role_view.empty:
        st.info(f"No role records with at least {MIN_GAMES_FOR_MEANINGFUL_STATS} games yet.")
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
    st.markdown(
        f'<div class="section-note">Shows shared champion performance across the full flex group, including who has piloted each pick. '
        f'Minimum sample: {MIN_GAMES_FOR_MEANINGFUL_STATS} games.</div>',
        unsafe_allow_html=True,
    )
    collective_view = meaningful_collective_champion_df.sort_values(
        ["Win Rate %", "Games", "KDA"],
        ascending=[False, False, False],
    )
    if collective_view.empty:
        st.info(f"No collective champion samples with at least {MIN_GAMES_FOR_MEANINGFUL_STATS} games yet.")
    else:
        render_champion_gallery(collective_view.head(4), "Top Collective Picks", "Win rate")
        st.dataframe(collective_view, use_container_width=True, hide_index=True)

    render_champion_rivalries(player_champion_df)

    st.markdown("## Champion Win Rates By Player")
    member_champion_view = meaningful_player_champion_df.sort_values(
        ["Win Rate %", "Games", "KDA", "Carry Score / Game"],
        ascending=[False, False, False, False],
    )
    if member_champion_view.empty:
        st.info(f"No player/champion combinations with at least {MIN_GAMES_FOR_MEANINGFUL_STATS} games yet.")
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


def results_have_current_schema(results):
    participant_df = results.get("participant_df", pd.DataFrame())
    player_df = results.get("player_df", pd.DataFrame())
    player_champion_df = results.get("player_champion_df", pd.DataFrame())
    required_participant_columns = {
        "Team ID",
        "Win",
        "Vision Score",
        "Objective Damage",
        "Kill Participation %",
        "Carry Score",
    }
    required_player_columns = {
        "Vision / Game",
        "CS / Min",
        "Objective Damage / Game",
        "Carry Score / Game",
    }
    required_champion_columns = {"Carry Score / Game", "Damage / Game"}
    return (
        required_participant_columns.issubset(participant_df.columns)
        and required_player_columns.issubset(player_df.columns)
        and required_champion_columns.issubset(player_champion_df.columns)
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
    if results_have_current_schema(results):
        render_records(results)
    else:
        st.info("The dashboard gained new stat fields. Run Analyse Team Records again to build the expanded views.")

st.caption(
    "This page uses Riot's account, summoner, league-exp, and match endpoints to build records from ranked flex games "
    "where at least two tracked players queued together."
)
