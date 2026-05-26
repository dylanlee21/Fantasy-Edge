"""
app.py — Fantasy Football Stats Dashboard
Run with: py -3.12 -m streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="FantasyEdge", page_icon="🏈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@400;600;700;900&display=swap');
html, body, [class*="css"] { background-color: #080c10 !important; color: #c8d6e0 !important; font-family: 'Barlow', sans-serif; }
.hero { padding: 2rem 0 1rem 0; border-bottom: 1px solid #2a0a1a; margin-bottom: 1.5rem; }
.hero-title { font-family: 'Share Tech Mono', monospace; font-size: 2.8rem; color: #ff007f; letter-spacing: 0.15em; margin: 0; text-shadow: 0 0 30px rgba(255,0,127,0.4); }
.hero-sub { font-family: 'Share Tech Mono', monospace; font-size: 0.75rem; color: #7a2a5a; letter-spacing: 0.2em; margin-top: 0.25rem; }
.season-badge { display: inline-block; background: #1f0a14; border: 1px solid #ff007f; color: #ff007f; font-family: 'Share Tech Mono', monospace; font-size: 0.7rem; padding: 0.2rem 0.7rem; letter-spacing: 0.15em; margin-top: 0.5rem; }
.stat-card { background: #0d1117; border: 1px solid #2a0a1a; border-left: 3px solid #ff007f; padding: 1rem 1.2rem; margin-bottom: 0.5rem; }
.stat-card-value { font-family: 'Share Tech Mono', monospace; font-size: 1.8rem; color: #ff007f; line-height: 1; }
.stat-card-label { font-size: 0.7rem; color: #7a2a5a; letter-spacing: 0.15em; text-transform: uppercase; margin-top: 0.2rem; }
.stTabs [data-baseweb="tab-list"] { background: #080c10 !important; border-bottom: 1px solid #2a0a1a !important; gap: 0; }
.stTabs [data-baseweb="tab"] { background: #080c10 !important; color: #7a2a5a !important; font-family: 'Share Tech Mono', monospace !important; font-size: 0.85rem !important; letter-spacing: 0.1em !important; border: none !important; border-bottom: 2px solid transparent !important; padding: 0.6rem 1.5rem !important; }
.stTabs [aria-selected="true"] { color: #ff007f !important; border-bottom: 2px solid #ff007f !important; background: #080c10 !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }
.stTextInput input { background: #0d1117 !important; border: 1px solid #2a0a1a !important; border-radius: 0 !important; color: #c8d6e0 !important; font-family: 'Share Tech Mono', monospace !important; font-size: 0.85rem !important; }
.stTextInput input:focus { border-color: #ff007f !important; box-shadow: 0 0 0 1px #ff007f !important; }
.stSelectbox div[data-baseweb="select"] > div { background: #0d1117 !important; border: 1px solid #2a0a1a !important; border-radius: 0 !important; color: #c8d6e0 !important; font-family: 'Share Tech Mono', monospace !important; font-size: 0.8rem !important; }
.section-label { font-family: 'Share Tech Mono', monospace; font-size: 0.7rem; color: #7a2a5a; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.5rem; padding-bottom: 0.3rem; border-bottom: 1px solid #2a0a1a; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.block-container {padding-top: 1rem !important; padding-bottom: 2rem !important;}
</style>
""", unsafe_allow_html=True)

DATA_DIR = "data"

COL_LABELS = {
    "player_display_name": "Player", "recent_team": "Team", "games": "GP",
    "fppg": "FPPG", "fppg_ppr": "FPPG (PPR)", "fantasy_points": "Total Pts",
    "fantasy_points_ppr": "Total PPR Pts", "passing_yards": "Pass Yds",
    "passing_tds": "Pass TD", "interceptions": "INT", "comp_pct": "Comp%",
    "yards_per_attempt": "Y/A", "td_rate": "TD Rate", "sacks": "Sacks",
    "carries": "Car", "rushing_yards": "Rush Yds", "rushing_tds": "Rush TD",
    "ypc": "YPC", "targets": "Tgt", "receptions": "Rec",
    "receiving_yards": "Rec Yds", "receiving_tds": "Rec TD",
    "target_share": "Tgt Share", "air_yards_share": "AY Share",
    "wopr": "WOPR", "racr": "RACR", "adot": "aDOT", "catch_rate": "Catch%",
    "yards_per_target": "Y/Tgt", "yac_per_rec": "YAC/Rec", "avg_snap_pct": "Snap%",
    "team": "Team", "pass_rate": "Pass Rate", "run_rate": "Run Rate",
    "total_plays": "Total Plays", "pass_attempts": "Pass Att",
    "rush_attempts": "Rush Att", "avg_pts_allowed": "Avg Pts Allowed",
    "sos_rank": "SOS Rank", "position": "Pos",
    "player": "Player",
    "2025_fppg_ppr": "2025 FPPG (PPR)",
    "fc_rank": "FantasyCalc Rank", "fc_pos_rank": "FC Pos Rank", "fc_value": "FC Value",
    "ffc_adp": "FFC ADP", "ffc_rank": "FFC Rank",
    "fp_rank": "FantasyPros Rank", "fp_pos_rank": "FP Pos Rank",
    "fp_best": "FP Best", "fp_worst": "FP Worst", "fp_stdev": "FP StDev",
    "espn_rank": "ESPN Rank", "consensus_rank": "Consensus Rank",
    "rb_overall_rank": "RotoBaller Rank", "rb_pos_rank": "RotoBaller Pos Rank",
    "yahoo_rank": "Yahoo Rank", "yahoo_pos_rank": "Yahoo Pos Rank",

}

PCT_COLS = {"target_share", "air_yards_share", "catch_rate", "comp_pct", "avg_snap_pct",
            "pass_rate", "run_rate", "opportunity_share", "rz_pass_rate", "rz_run_rate", "rz_conversion_rate"}

@st.cache_data
def load_player_info():
    path = os.path.join(DATA_DIR, "player_info.csv")
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

@st.cache_data
def load_gamelogs(year):
    path = os.path.join(DATA_DIR, f"gamelogs_{year}.csv")
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

@st.cache_data
def load_year(year):
    year_dir = os.path.join(DATA_DIR, str(year))
    files = {"QB": "qb_stats.csv", "RB": "rb_stats.csv", "WR": "wr_stats.csv",
             "TE": "te_stats.csv", "SOS": "sos_by_team.csv", "SPLITS": "team_splits.csv"}
    index_col_map = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "SOS": None, "SPLITS": None}
    data = {}
    for key, fname in files.items():
        path = os.path.join(year_dir, fname)
        data[key] = pd.read_csv(path, index_col=index_col_map[key]) if os.path.exists(path) else pd.DataFrame()
    return data

@st.cache_data
def load_2026():
    base = os.path.join(DATA_DIR, "2026")
    master_path = os.path.join(base, "master_rankings.csv")
    sos_path    = os.path.join(base, "sos_2026.csv")
    mock_path   = os.path.join(base, "mock_board.csv")
    master = pd.read_csv(master_path, index_col=0) if os.path.exists(master_path) else pd.DataFrame()
    sos    = pd.read_csv(sos_path) if os.path.exists(sos_path) else pd.DataFrame()
    mock   = pd.read_csv(mock_path) if os.path.exists(mock_path) else pd.DataFrame()
    return master, sos, mock

def pct_fmt(val):
    return "—" if pd.isna(val) else f"{val:.1%}"

def rename_cols(df):
    return df.rename(columns=COL_LABELS)

def show_table(df, search_query="", sort_col=None, ascending=False):
    if df.empty:
        st.warning("No data found. Run fantasy_pipeline.py first.")
        return
    df = df.copy()
    if search_query:
        mask = df.apply(lambda col: col.astype(str).str.contains(search_query, case=False)).any(axis=1)
        df = df[mask]
    # Sort BEFORE converting pct columns to strings
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=ascending, key=lambda x: pd.to_numeric(x, errors="coerce"))
    # Now format pct columns as strings for display
    for c in PCT_COLS:
        if c in df.columns:
            df[c] = df[c].apply(pct_fmt)
    st.dataframe(rename_cols(df), use_container_width=True, height=600)
    st.caption(f"// {len(df)} players · click any column header to sort")

def controls(pos, df):
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        search = st.text_input("🔍  SEARCH PLAYER", placeholder="e.g. CMC, Jefferson...", key=f"search_{pos}")
    with c2:
        opts = ["fppg_ppr"] + [c for c in df.columns if c not in ["player_display_name", "recent_team", "fppg_ppr"]]
        sort_col = st.selectbox("SORT BY", opts, key=f"sort_{pos}", format_func=lambda x: COL_LABELS.get(x, x))
    with c3:
        asc = st.selectbox("ORDER", ["↓ High→Low", "↑ Low→High"], key=f"asc_{pos}")
    return search, sort_col, asc == "↑ Low→High"

def show_2026_table(df, pos_filter=None, search="", sort_col=None, ascending=True):
    if df.empty:
        st.warning("Run fetch_rankings.py first to generate 2026 rankings.")
        return
    df = df.copy()
    if pos_filter:
        df = df[df["position"] == pos_filter]
    if search:
        mask = df.apply(lambda col: col.astype(str).str.contains(search, case=False)).any(axis=1)
        df = df[mask]
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=ascending)
    st.dataframe(rename_cols(df), use_container_width=True, height=600)
    st.caption(f"// {len(df)} players · click column header to sort")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-title">FANTASY_EDGE</div>
    <div class="hero-sub">// NFL PLAYER ANALYTICS & RANKINGS</div>
</div>
""", unsafe_allow_html=True)

# ── SEASON SELECTOR ───────────────────────────────────────────────────────────
col_s, col_sp = st.columns([3, 7])
with col_s:
    season = st.radio("SEASON", ["2026 RANKINGS", 2025, 2024], horizontal=True, label_visibility="collapsed")

show_2026 = season == "2026 RANKINGS"

if show_2026:
    master, sos_2026, mock_board = load_2026()
    st.markdown('<div class="season-badge">SZN_2026 · PREDICTIVE RANKINGS</div>', unsafe_allow_html=True)
else:
    data = load_year(season)
    st.markdown(f'<div class="season-badge">SZN_{season} · REGULAR_SEASON</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── STAT CARDS (historical only) ──────────────────────────────────────────────
if not show_2026:
    c1, c2, c3, c4 = st.columns(4)
    for col, pos, label in [(c1,"QB","Quarterbacks"),(c2,"RB","Running Backs"),(c3,"WR","Wide Receivers"),(c4,"TE","Tight Ends")]:
        with col:
            count = len(data[pos]) if not data[pos].empty else 0
            st.markdown(f'<div class="stat-card"><div class="stat-card-value">{count}</div><div class="stat-card-label">{label}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── 2026 VIEW ─────────────────────────────────────────────────────────────────
if show_2026:
    rank_cols     = [c for c in ["consensus_rank","fc_rank","ffc_rank","fp_rank","espn_rank","rb_overall_rank","yahoo_rank"] if not master.empty and c in master.columns]
    pos_rank_cols = [c for c in ["consensus_rank","fc_pos_rank","fp_pos_rank","rb_pos_rank","yahoo_pos_rank"] if not master.empty and c in master.columns]

    tabs = st.tabs(["⬡  OVERALL", "⬡  QB", "⬡  RB", "⬡  WR", "⬡  TE", "⬡  SOS 2026", "⬡  MOCK BOARD", "⬡  SOURCE COMPARE"])

    with tabs[0]:
        st.markdown('<div class="section-label">// 2026 CONSENSUS RANKINGS · PPR · ALL POSITIONS</div>', unsafe_allow_html=True)
        if not master.empty:
            s = st.text_input("🔍  SEARCH PLAYER", key="s_all", placeholder="e.g. Bijan, Jefferson...")
            c1, c2 = st.columns([2, 1])
            with c1:
                sort_opt = st.selectbox("SORT BY", rank_cols, key="sort_all",
                                        format_func=lambda x: COL_LABELS.get(x, x))
            with c2:
                asc = st.selectbox("ORDER", ["↑ Low→High (best rank)", "↓ High→Low"], key="asc_all")
            show_2026_table(master, search=s, sort_col=sort_opt, ascending=(asc == "↑ Low→High (best rank)"))

    for i, pos in enumerate(["QB", "RB", "WR", "TE"]):
        with tabs[i + 1]:
            st.markdown(f'<div class="section-label">// 2026 {pos} RANKINGS · PPR · CONSENSUS</div>', unsafe_allow_html=True)
            if not master.empty:
                s = st.text_input("🔍  SEARCH", key=f"s_{pos}", placeholder=f"Search {pos}s...")
                c1, c2 = st.columns([2, 1])
                with c1:
                    opts = pos_rank_cols if pos_rank_cols else rank_cols
                    sort_opt = st.selectbox("SORT BY", opts, key=f"sort_{pos}26",
                                            format_func=lambda x: COL_LABELS.get(x, x))
                with c2:
                    asc = st.selectbox("ORDER", ["↑ Low→High (best rank)", "↓ High→Low"], key=f"asc_{pos}26")
                show_2026_table(master, pos_filter=pos, search=s,
                                sort_col=sort_opt, ascending=(asc == "↑ Low→High (best rank)"))

    with tabs[5]:
        st.markdown('<div class="section-label">// 2026 STRENGTH OF SCHEDULE · BASED ON 2025 DEFENSIVE RANKINGS</div>', unsafe_allow_html=True)
        if not sos_2026.empty:
            pos_f = st.selectbox("POSITION", ["RB","WR","QB","TE"], key="sos26_pos")
            sos_f = sos_2026[sos_2026["position"] == pos_f].copy()
            sos_f = sos_f.sort_values("sos_2026_rank").reset_index(drop=True)

            DIFF_COLORS = {"EASY": "#00ff88", "BELOW AVG": "#88ff00", "ABOVE AVG": "#ffaa00", "HARD": "#ff4444"}

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Easiest {pos_f} Schedules** (face weakest defenses)")
                easy = sos_f.head(8)[["team","avg_opp_pts_allowed","sos_2026_rank","difficulty","games_rated"]]
                st.dataframe(easy.rename(columns={
                    "team":"Team","avg_opp_pts_allowed":"Avg PPR Pts Allowed vs Position",
                    "sos_2026_rank":"SOS Rank","difficulty":"Difficulty","games_rated":"Games Rated"
                }), use_container_width=True, hide_index=True)
            with c2:
                st.markdown(f"**Hardest {pos_f} Schedules** (face strongest defenses)")
                hard = sos_f.tail(8).sort_values("sos_2026_rank", ascending=False)[["team","avg_opp_pts_allowed","sos_2026_rank","difficulty","games_rated"]]
                st.dataframe(hard.rename(columns={
                    "team":"Team","avg_opp_pts_allowed":"Avg PPR Pts Allowed vs Position",
                    "sos_2026_rank":"SOS Rank","difficulty":"Difficulty","games_rated":"Games Rated"
                }), use_container_width=True, hide_index=True)

            st.markdown('<div class="section-label" style="margin-top:1.5rem">// ALL TEAMS</div>', unsafe_allow_html=True)
            st.dataframe(sos_f.rename(columns={
                "team":"Team","avg_opp_pts_allowed":"Avg PPR Pts Allowed vs Position",
                "sos_2026_rank":"SOS Rank","difficulty":"Difficulty","games_rated":"Games Rated"
            }), use_container_width=True, hide_index=True)
            st.caption("// Avg PPR fantasy pts allowed by each opponent defense vs that position in 2025 · Higher = easier schedule")
        else:
            st.warning("Run fetch_sos_2026.py to generate 2026 SOS data.")

    with tabs[6]:
        st.markdown('<div class="section-label">// 2026 ESPN MOCK DRAFT BOARD · 12-TEAM PPR · ADP ORDER</div>', unsafe_allow_html=True)
        if not mock_board.empty:
            pos_options = ["ALL", "QB", "RB", "WR", "TE", "K", "DST"]
            c1, c2 = st.columns([2, 1])
            with c1:
                mock_search = st.text_input("🔍  SEARCH PLAYER", key="mock_search", placeholder="e.g. Josh Allen, CMC...")
            with c2:
                mock_pos = st.selectbox("FILTER BY POSITION", pos_options, key="mock_pos")

            mb = mock_board.copy()
            mb["pick_label"] = mb.apply(lambda r: f"{int(r['round'])}.{int(r['pick_in_round']):02d}", axis=1)
            if mock_pos != "ALL":
                mb = mb[mb["position"] == mock_pos]
            if mock_search:
                mask = mb.apply(lambda col: col.astype(str).str.contains(mock_search, case=False)).any(axis=1)
                mb = mb[mask]

            # Color code by position
            POS_COLORS = {
                "QB": "#4fc3f7", "RB": "#81c784", "WR": "#ff8a65",
                "TE": "#ce93d8", "K": "#fff176", "DST": "#90a4ae",
            }

            def style_pos(val):
                color = POS_COLORS.get(val, "#c8d6e0")
                return f"color: {color}; font-weight: bold;"

            display = mb[["pick_label","player","position","team"]].rename(columns={
                "pick_label": "Pick", "player": "Player",
                "position": "Pos", "team": "Team"
            })

            st.dataframe(
                display.style.map(style_pos, subset=["Pos"]),
                use_container_width=True, height=700, hide_index=True
            )
            st.caption(f"// {len(mb)} players shown · ESPN Mock Draft 10-team PPR · formatted as 12-team")
        else:
            st.warning("Run create_mock_board.py to generate the mock board.")

    with tabs[7]:
        st.markdown('<div class="section-label">// SOURCE COMPARISON · WHERE EXPERTS AGREE & DISAGREE</div>', unsafe_allow_html=True)
        if not master.empty:
            pos_f = st.selectbox("POSITION", ["ALL", "QB", "RB", "WR", "TE"], key="src_pos")
            df_src = master.copy() if pos_f == "ALL" else master[master["position"] == pos_f].copy()
            ext_cols = [c for c in ["fc_rank","ffc_rank","fp_rank","espn_rank","rb_overall_rank","yahoo_rank"] if c in df_src.columns and df_src[c].notna().sum() > 3]
            if ext_cols:
                st.markdown("**Sources:** " + " · ".join([COL_LABELS.get(c, c) for c in ext_cols]))
                df_src["rank_stdev"] = df_src[ext_cols].std(axis=1).round(1)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Biggest disagreements**")
                    disp = df_src.sort_values("rank_stdev", ascending=False).head(15)
                    show_c = [c for c in ["player","position","team"] + ext_cols + ["rank_stdev"] if c in disp.columns]
                    st.dataframe(disp[show_c].rename(columns=COL_LABELS), use_container_width=True, hide_index=True)
                with c2:
                    st.markdown("**Strongest consensus picks**")
                    disp = df_src.sort_values("rank_stdev").head(15)
                    show_c = [c for c in ["player","position","team"] + ext_cols + ["rank_stdev"] if c in disp.columns]
                    st.dataframe(disp[show_c].rename(columns=COL_LABELS), use_container_width=True, hide_index=True)

# ── 2024 / 2025 VIEW ──────────────────────────────────────────────────────────
else:
    tabs = st.tabs(["⬡  QB", "⬡  RB", "⬡  WR", "⬡  TE", "⬡  TEAM SPLITS", "⬡  SOS", "⬡  PLAYER PROFILE"])

    with tabs[0]:
        st.markdown(f'<div class="section-label">// QUARTERBACK RANKINGS · {season} · MIN 5 GAMES</div>', unsafe_allow_html=True)
        df = data["QB"].copy()
        if not df.empty:
            search, sort_col, ascending = controls("QB", df)
            show_table(df, search, sort_col, ascending)

    with tabs[1]:
        st.markdown(f'<div class="section-label">// RUNNING BACK RANKINGS · {season} · MIN 3 GAMES</div>', unsafe_allow_html=True)
        df = data["RB"].copy()
        if not df.empty:
            search, sort_col, ascending = controls("RB", df)
            show_table(df, search, sort_col, ascending)

    with tabs[2]:
        st.markdown(f'<div class="section-label">// WIDE RECEIVER RANKINGS · {season} · MIN 3 GAMES</div>', unsafe_allow_html=True)
        df = data["WR"].copy()
        if not df.empty:
            search, sort_col, ascending = controls("WR", df)
            show_table(df, search, sort_col, ascending)

    with tabs[3]:
        st.markdown(f'<div class="section-label">// TIGHT END RANKINGS · {season} · MIN 3 GAMES</div>', unsafe_allow_html=True)
        df = data["TE"].copy()
        if not df.empty:
            search, sort_col, ascending = controls("TE", df)
            show_table(df, search, sort_col, ascending)

    with tabs[4]:
        st.markdown(f'<div class="section-label">// TEAM PASS / RUN RATE · {season}</div>', unsafe_allow_html=True)
        df = data["SPLITS"].copy()
        if not df.empty:
            team_col = next((c for c in ["team","recent_team","posteam"] if c in df.columns), df.columns[0])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Most Pass-Heavy Teams**")
                top = df.sort_values("pass_rate", ascending=False).head(10).copy()
                for c in ["pass_rate","run_rate"]: top[c] = top[c].apply(pct_fmt)
                show_c = [x for x in [team_col,"pass_rate","run_rate","total_plays"] if x in top.columns]
                st.dataframe(rename_cols(top[show_c]), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("**Most Run-Heavy Teams**")
                top = df.sort_values("run_rate", ascending=False).head(10).copy()
                for c in ["pass_rate","run_rate"]: top[c] = top[c].apply(pct_fmt)
                show_c = [x for x in [team_col,"run_rate","pass_rate","total_plays"] if x in top.columns]
                st.dataframe(rename_cols(top[show_c]), use_container_width=True, hide_index=True)
            st.markdown('<div class="section-label" style="margin-top:1.5rem">// ALL TEAMS</div>', unsafe_allow_html=True)
            all_s = df.copy()
            for c in ["pass_rate","run_rate"]: all_s[c] = all_s[c].apply(pct_fmt)
            st.dataframe(rename_cols(all_s), use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown(f'<div class="section-label">// STRENGTH OF SCHEDULE · PTS ALLOWED BY DEFENSE · {season}</div>', unsafe_allow_html=True)
        df = data["SOS"].copy()
        if not df.empty:
            team_col = next((c for c in ["team","recent_team","opponent_team"] if c in df.columns), df.columns[0])
            pos_filter = st.selectbox("POSITION", ["RB","WR","QB","TE"], key="sos_pos")
            sos_df = df[df["position"] == pos_filter].copy()
            sos_df["avg_pts_allowed"] = sos_df["avg_pts_allowed"].round(2)
            sos_df = sos_df.sort_values("avg_pts_allowed", ascending=False).reset_index(drop=True)
            sos_df.index += 1
            sos_df.index.name = "rank"
            show_c = [x for x in [team_col,"avg_pts_allowed","sos_rank"] if x in sos_df.columns]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Easiest vs {pos_filter}** (most pts allowed)")
                st.dataframe(rename_cols(sos_df.head(10)[show_c]), use_container_width=True)
            with c2:
                st.markdown(f"**Toughest vs {pos_filter}** (fewest pts allowed)")
                st.dataframe(rename_cols(sos_df.tail(10)[show_c].sort_values("avg_pts_allowed")), use_container_width=True)
            st.markdown('<div class="section-label" style="margin-top:1.5rem">// ALL TEAMS</div>', unsafe_allow_html=True)
            st.dataframe(rename_cols(sos_df), use_container_width=True)

    with tabs[6]:
        st.markdown(f'<div class="section-label">// PLAYER PROFILE · {season} SEASON</div>', unsafe_allow_html=True)

        player_info = load_player_info()
        gamelogs    = load_gamelogs(season)

        # Get all players from position CSVs
        all_players = []
        for pos in ["QB","RB","WR","TE"]:
            df_pos = data[pos]
            if not df_pos.empty and "player_display_name" in df_pos.columns:
                all_players.extend(df_pos["player_display_name"].tolist())
        all_players = sorted(set(all_players))

        selected = st.selectbox("SELECT PLAYER", ["— choose a player —"] + all_players, key="profile_player")

        if selected and selected != "— choose a player —":
            # Find player in position CSVs
            player_row = None
            player_pos = None
            for pos in ["QB","RB","WR","TE"]:
                df_pos = data[pos]
                if not df_pos.empty and "player_display_name" in df_pos.columns:
                    match = df_pos[df_pos["player_display_name"] == selected]
                    if not match.empty:
                        player_row = match.iloc[0]
                        player_pos = pos
                        break

            if player_row is not None:
                # Get age from player_info
                age = "N/A"
                headshot = None
                if not player_info.empty:
                    info_match = player_info[player_info["player_display_name"] == selected]
                    if not info_match.empty:
                        age_val = info_match.iloc[0].get("age")
                        age = int(age_val) if pd.notna(age_val) else "N/A"
                        headshot = info_match.iloc[0].get("headshot_url")

                # ── PROFILE HEADER ────────────────────────────────────────────
                col_img, col_info = st.columns([1, 3])
                with col_img:
                    if headshot and pd.notna(headshot):
                        st.image(headshot, width=140)
                    else:
                        st.markdown('<div style="width:140px;height:140px;background:#1a2a1a;border:1px solid #ff007f;display:flex;align-items:center;justify-content:center;font-size:2rem">🏈</div>', unsafe_allow_html=True)

                with col_info:
                    team  = player_row.get("recent_team","N/A")
                    games = int(player_row.get("games", 0))
                    total_pts = round(player_row.get("fantasy_points_ppr", 0), 1)
                    fppg      = round(player_row.get("fppg_ppr", 0), 2)

                    st.markdown(f"""
<div style="font-family:'Share Tech Mono',monospace;">
  <div style="font-size:1.8rem;color:#ff007f;font-weight:bold;">{selected}</div>
  <div style="font-size:0.9rem;color:#c8d6e0;margin-top:0.3rem;">
    {player_pos} · {team} · Age: {age}
  </div>
  <div style="display:flex;gap:2rem;margin-top:1rem;">
    <div>
      <div style="font-size:1.4rem;color:#ff007f;">{total_pts}</div>
      <div style="font-size:0.65rem;color:#7a2a5a;letter-spacing:0.15em;">TOTAL PPR PTS</div>
    </div>
    <div>
      <div style="font-size:1.4rem;color:#ff007f;">{fppg}</div>
      <div style="font-size:0.65rem;color:#7a2a5a;letter-spacing:0.15em;">FPPG (PPR)</div>
    </div>
    <div>
      <div style="font-size:1.4rem;color:#ff007f;">{games}</div>
      <div style="font-size:0.65rem;color:#7a2a5a;letter-spacing:0.15em;">GAMES PLAYED</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── GAME LOG ──────────────────────────────────────────────────
                st.markdown('<div class="section-label">// GAME LOG</div>', unsafe_allow_html=True)

                if not gamelogs.empty:
                    player_log = gamelogs[gamelogs["player_display_name"] == selected].copy()
                    if not player_log.empty:
                        player_log = player_log.sort_values("week").reset_index(drop=True)

                        # ── BOOM/BUST THRESHOLDS (player-relative) ────────────
                        avg_ppr = fppg  # player's season FPPG
                        boom_threshold = avg_ppr * 1.5
                        bust_threshold = avg_ppr * 0.5

                        def classify(pts):
                            if pd.isna(pts): return "—"
                            if pts >= boom_threshold: return "BOOM"
                            if pts <= bust_threshold: return "BUST"
                            return "AVG"

                        player_log["result"] = player_log["fantasy_points_ppr"].apply(classify)

                        boom_count = (player_log["result"] == "BOOM").sum()
                        bust_count = (player_log["result"] == "BUST").sum()
                        avg_count  = (player_log["result"] == "AVG").sum()

                        # ── BOOM/BUST SUMMARY CARDS ───────────────────────────
                        bc1, bc2, bc3, bc4 = st.columns(4)
                        with bc1:
                            st.markdown(f'<div class="stat-card" style="border-left-color:#00cc44"><div class="stat-card-value" style="color:#00cc44">{boom_count}</div><div class="stat-card-label">BOOM games (≥{boom_threshold:.1f} pts)</div></div>', unsafe_allow_html=True)
                        with bc2:
                            st.markdown(f'<div class="stat-card" style="border-left-color:#ff3333"><div class="stat-card-value" style="color:#ff3333">{bust_count}</div><div class="stat-card-label">BUST games (≤{bust_threshold:.1f} pts)</div></div>', unsafe_allow_html=True)
                        with bc3:
                            st.markdown(f'<div class="stat-card"><div class="stat-card-value">{avg_count}</div><div class="stat-card-label">AVG games</div></div>', unsafe_allow_html=True)
                        with bc4:
                            boom_rate = f"{boom_count/len(player_log)*100:.0f}%" if len(player_log) > 0 else "—"
                            st.markdown(f'<div class="stat-card"><div class="stat-card-value">{boom_rate}</div><div class="stat-card-label">BOOM rate</div></div>', unsafe_allow_html=True)

                        st.markdown(f'<div style="font-family:Share Tech Mono,monospace;font-size:0.65rem;color:#7a2a5a;margin-bottom:0.5rem;">// BOOM = ≥1.5x avg ({boom_threshold:.1f} pts) · BUST = ≤0.5x avg ({bust_threshold:.1f} pts) · based on {avg_ppr:.1f} FPPG season avg</div>', unsafe_allow_html=True)

                        # ── BUILD DISPLAY TABLE ───────────────────────────────
                        base_cols = ["week","opponent_team","fantasy_points_ppr","result"]
                        if player_pos == "QB":
                            extra = ["completions","attempts","passing_yards","passing_tds",
                                     "interceptions","carries","rushing_yards","rushing_tds","sacks"]
                        elif player_pos == "RB":
                            extra = ["carries","rushing_yards","rushing_tds",
                                     "receptions","targets","receiving_yards","receiving_tds"]
                        else:
                            extra = ["receptions","targets","receiving_yards","receiving_tds"]

                        show_cols = base_cols + [c for c in extra if c in player_log.columns]
                        display_log = player_log[[c for c in show_cols if c in player_log.columns]].copy()
                        # Format PPR pts to 2 decimal places as string
                        if "fantasy_points_ppr" in display_log.columns:
                            display_log["fantasy_points_ppr"] = display_log["fantasy_points_ppr"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")

                        gl_labels = {
                            "week":"Week","opponent_team":"Opp","fantasy_points_ppr":"PPR Pts",
                            "result":"Result","completions":"Comp","attempts":"Att",
                            "passing_yards":"Pass Yds","passing_tds":"Pass TD","interceptions":"INT",
                            "carries":"Car","rushing_yards":"Rush Yds","rushing_tds":"Rush TD",
                            "receptions":"Rec","targets":"Tgt","receiving_yards":"Rec Yds",
                            "receiving_tds":"Rec TD","sacks":"Sacks",
                        }
                        display_log = display_log.rename(columns=gl_labels)

                        # Color code the Result column
                        def color_result(val):
                            if val == "BOOM": return "background-color: #0a2e0a; color: #00cc44; font-weight: bold;"
                            if val == "BUST": return "background-color: #2e0a0a; color: #ff3333; font-weight: bold;"
                            return "color: #c8d6e0;"

                        # Color code PPR Pts column (works with string values too)
                        def color_pts(val):
                            try:
                                v = float(str(val).replace("—",""))
                                if v >= boom_threshold: return "color: #00cc44; font-weight: bold;"
                                if v <= bust_threshold: return "color: #ff3333; font-weight: bold;"
                            except: pass
                            return "color: #c8d6e0;"

                        styled = display_log.style
                        if "Result" in display_log.columns:
                            styled = styled.map(color_result, subset=["Result"])
                        if "PPR Pts" in display_log.columns:
                            styled = styled.map(color_pts, subset=["PPR Pts"])

                        st.dataframe(styled, use_container_width=True, hide_index=True)
                        st.caption(f"// {len(player_log)} games · Season total PPR: {player_log['fantasy_points_ppr'].sum():.1f}")
                    else:
                        st.info("No game log data found for this player.")
                else:
                    st.warning("Run build_player_profiles.py to generate game logs.")
