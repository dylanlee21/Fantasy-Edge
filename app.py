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
    "fantasy_points_ppr": "Total Pts (PPR)", "passing_yards": "Pass Yds",
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
}

PCT_COLS = {"target_share", "air_yards_share", "catch_rate", "comp_pct", "avg_snap_pct", "pass_rate", "run_rate"}

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
    path = os.path.join(base, "master_rankings.csv")
    return pd.read_csv(path, index_col=0) if os.path.exists(path) else pd.DataFrame()

def pct_fmt(val):
    return "—" if pd.isna(val) else f"{val:.1%}"

def rename_cols(df):
    return df.rename(columns=COL_LABELS)

def show_table(df, search_query="", sort_col=None, ascending=False):
    if df.empty:
        st.warning("No data found. Run fantasy_pipeline.py first.")
        return
    if search_query:
        mask = df.apply(lambda col: col.astype(str).str.contains(search_query, case=False)).any(axis=1)
        df = df[mask]
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=ascending)
    df = df.copy()
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
    master = load_2026()
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
    rank_cols     = [c for c in ["consensus_rank","fc_rank","ffc_rank","fp_rank","espn_rank"] if not master.empty and c in master.columns]
    pos_rank_cols = [c for c in ["consensus_rank","fc_pos_rank","fp_pos_rank"] if not master.empty and c in master.columns]

    tabs = st.tabs(["⬡  OVERALL", "⬡  QB", "⬡  RB", "⬡  WR", "⬡  TE", "⬡  SOURCE COMPARE"])

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
        st.markdown('<div class="section-label">// SOURCE COMPARISON · WHERE EXPERTS AGREE & DISAGREE</div>', unsafe_allow_html=True)
        if not master.empty:
            pos_f = st.selectbox("POSITION", ["ALL", "QB", "RB", "WR", "TE"], key="src_pos")
            df_src = master.copy() if pos_f == "ALL" else master[master["position"] == pos_f].copy()
            ext_cols = [c for c in ["fc_rank","ffc_rank","fp_rank","espn_rank"] if c in df_src.columns and df_src[c].notna().sum() > 3]
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
    tabs = st.tabs(["⬡  QB", "⬡  RB", "⬡  WR", "⬡  TE", "⬡  TEAM SPLITS", "⬡  SOS"])

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
