from collections import defaultdict
from itertools import combinations
import time

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

import config


st.set_page_config(page_title="Flex Combo Stats", page_icon=":material/groups:")
st.markdown("# League Flex Combo Stats")
st.sidebar.markdown("# League Flex Combo Stats")
st.sidebar.markdown("Compare ranked flex results for groups of players and find the best combinations.")


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


def parse_player_entries(raw_text):
    entries = []
    for line in raw_text.splitlines():
        value = line.strip()
        if not value:
            continue
        if "#" in value:
            game_name, tag_line = value.split("#", 1)
            entries.append(
                {
                    "input": value,
                    "lookup_type": "riot_id",
                    "game_name": game_name.strip(),
                    "tag_line": tag_line.strip(),
                }
            )
        else:
            entries.append(
                {
                    "input": value,
                    "lookup_type": "summoner_name",
                    "summoner_name": value,
                }
            )
    return entries


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
        "display_name": display_name,
        "puuid": summoner["puuid"],
        "summoner_id": summoner_id,
        "summoner_name": summoner.get("name", display_name),
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
                    "Player": player["display_name"],
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
                "Player": player["display_name"],
                "Tier": entry.get("tier", ""),
                "Division": entry.get("rank", ""),
                "LP": entry.get("leaguePoints", 0),
                "Wins": wins,
                "Losses": losses,
                "Win Rate %": round((wins / total_games) * 100, 1) if total_games else 0.0,
            }
        )
    return pd.DataFrame(rows)


def analyze_combos(match_details, tracked_players):
    tracked_by_puuid = {player["puuid"]: player["display_name"] for player in tracked_players}
    combo_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "matches": 0})
    match_rows = []

    for match_id, match_data in match_details.items():
        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})
        participants = info.get("participants", [])
        if info.get("queueId") != QUEUE_ID:
            continue

        tracked_participants = []
        for participant in participants:
            puuid = participant.get("puuid")
            if puuid not in tracked_by_puuid:
                continue
            tracked_participants.append(
                {
                    "puuid": puuid,
                    "name": tracked_by_puuid[puuid],
                    "team_id": participant.get("teamId"),
                    "win": bool(participant.get("win")),
                }
            )

        teams = defaultdict(list)
        for participant in tracked_participants:
            teams[participant["team_id"]].append(participant)

        for team_members in teams.values():
            if len(team_members) < 2:
                continue

            team_members = sorted(team_members, key=lambda item: item["name"].lower())
            player_names = [member["name"] for member in team_members]
            did_win = team_members[0]["win"]

            match_rows.append(
                {
                    "Match ID": metadata.get("matchId", match_id),
                    "Players Together": ", ".join(player_names),
                    "Combo Size": len(player_names),
                    "Result": "Win" if did_win else "Loss",
                }
            )

            for combo_size in range(2, len(team_members) + 1):
                for combo in combinations(player_names, combo_size):
                    stats = combo_stats[combo]
                    stats["matches"] += 1
                    if did_win:
                        stats["wins"] += 1
                    else:
                        stats["losses"] += 1

    combo_rows = []
    for combo, stats in combo_stats.items():
        matches = stats["matches"]
        combo_rows.append(
            {
                "Combo": ", ".join(combo),
                "Combo Size": len(combo),
                "Wins": stats["wins"],
                "Losses": stats["losses"],
                "Matches": matches,
                "Win Rate %": round((stats["wins"] / matches) * 100, 1) if matches else 0.0,
            }
        )

    combo_df = pd.DataFrame(combo_rows)
    if not combo_df.empty:
        combo_df = combo_df.sort_values(
            by=["Combo Size", "Win Rate %", "Matches", "Wins"],
            ascending=[False, False, False, False],
        ).reset_index(drop=True)

    match_df = pd.DataFrame(match_rows)
    if not match_df.empty:
        match_df = match_df.sort_values(by=["Combo Size", "Result"], ascending=[False, True]).reset_index(drop=True)

    return combo_df, match_df


def combo_chart(combo_df, combo_size, top_n, ascending=False, title_prefix="Best"):
    filtered = combo_df[combo_df["Combo Size"] == combo_size].sort_values(
        by=["Win Rate %", "Matches", "Wins"],
        ascending=[ascending, not ascending, not ascending],
    ).head(top_n)
    if filtered.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, max(3, 0.7 * len(filtered))))
    bar_color = "#2E8B57" if not ascending else "#B22222"
    ax.barh(filtered["Combo"], filtered["Win Rate %"], color=bar_color)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Win Rate %")
    ax.set_title(f"{title_prefix} {combo_size}-Player Flex Combinations")
    ax.invert_yaxis()
    for index, (_, row) in enumerate(filtered.iterrows()):
        label = f"{row['Win Rate %']:.1f}% ({int(row['Matches'])} matches)"
        ax.text(min(row["Win Rate %"] + 1, 97), index, label, va="center")
    fig.tight_layout()
    return fig


def fetch_analysis(api_key, platform, raw_players, match_count):
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

    rank_df = build_rank_table(players, flex_entries)
    combo_df, match_df = analyze_combos(match_details, players)

    return {
        "players": players,
        "rank_df": rank_df,
        "combo_df": combo_df,
        "match_df": match_df,
        "profile_warnings": profile_warnings,
        "unique_matches": len(match_details),
    }


platform_label_options = list(PLATFORM_OPTIONS.keys())
default_platform_index = platform_label_options.index("Europe West")

with st.form("flex_combo_form"):
    selected_platform_label = st.selectbox("Platform routing", platform_label_options, index=default_platform_index)
    match_count = st.slider("Recent ranked flex matches per player", min_value=10, max_value=100, value=30, step=10)
    min_matches_2 = st.slider("Minimum shared matches for 2-player combos", min_value=1, max_value=100, value=40, step=1)
    min_matches_3 = st.slider("Minimum shared matches for 3-player combos", min_value=1, max_value=100, value=20, step=1)
    min_matches_4 = st.slider("Minimum shared matches for 4-player combos", min_value=1, max_value=100, value=10, step=1)
    min_matches_5 = st.slider("Minimum shared matches for 5-player combos", min_value=1, max_value=100, value=5, step=1)
    raw_players = st.text_area(
        "Players",
        value="",
        height=180,
        placeholder="One player per line\nExamples:\nHide on bush#KR1\nDoublelift#NA1\nLegacySummonerName",
        help="Use Riot IDs with `name#tag` when possible. Plain summoner names are kept as a fallback.",
    )
    submitted = st.form_submit_button("Analyse Flex Combinations", use_container_width=True)

st.caption("Riot requests are throttled and cached to stay under the 20 requests/1 second and 100 requests/2 minutes limits.")


if submitted:
    with st.spinner("Pulling ranked flex stats and match history from Riot..."):
        try:
            results = fetch_analysis(
                api_key=RIOT_API_KEY,
                platform=PLATFORM_OPTIONS[selected_platform_label],
                raw_players=raw_players,
                match_count=match_count,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.session_state["flex_combo_results"] = results


results = st.session_state.get("flex_combo_results")
if results:
    st.markdown("## Ranked Flex Profiles")
    st.dataframe(results["rank_df"], use_container_width=True, hide_index=True)
    for warning in results.get("profile_warnings", []):
        st.caption(warning)
    st.caption(f"Loaded {results['unique_matches']} unique ranked flex matches across the selected players.")

    combo_df = results["combo_df"]
    if combo_df.empty:
        st.warning("No shared ranked flex matches were found for these players in the sampled history.")
    else:
        min_matches_by_size = {
            2: min_matches_2,
            3: min_matches_3,
            4: min_matches_4,
            5: min_matches_5,
        }

        st.markdown("## Best Combinations")
        available_sizes = sorted(combo_df["Combo Size"].unique(), reverse=True)
        tabs = st.tabs([f"{size}-Player" for size in available_sizes])

        for tab, combo_size in zip(tabs, available_sizes):
            with tab:
                min_matches_required = min_matches_by_size.get(combo_size, 1)
                best_rows = combo_df[
                    (combo_df["Combo Size"] == combo_size) & (combo_df["Matches"] >= min_matches_required)
                ].reset_index(drop=True)
                if best_rows.empty:
                    st.info(f"No {combo_size}-player combinations met the minimum of {min_matches_required} shared matches.")
                else:
                    st.dataframe(best_rows, use_container_width=True, hide_index=True)
                    best_chart_col, worst_chart_col = st.columns(2)
                    with best_chart_col:
                        best_figure = combo_chart(best_rows, combo_size, top_n=min(10, len(best_rows)), ascending=False, title_prefix="Best")
                        if best_figure is not None:
                            st.pyplot(best_figure)
                    with worst_chart_col:
                        worst_figure = combo_chart(best_rows, combo_size, top_n=min(10, len(best_rows)), ascending=True, title_prefix="Worst")
                        if worst_figure is not None:
                            st.pyplot(worst_figure)

        st.markdown("## Shared Match Breakdown")
        st.dataframe(results["match_df"], use_container_width=True, hide_index=True)

st.caption(
    "This page uses Riot's account, summoner, league-exp, and match endpoints to measure how tracked players perform together in ranked flex."
)
