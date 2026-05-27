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

# ── OPPORTUNITY SCORE DATA · 2025 · TOP 50 PER POSITION ──────────────────────
# Weekly values: None = BYE week, "S" = suspended
# Columns after weekly: avg_l4 (last 4 avg), avg (season avg), total (season total opp), opp_fpts (actual ppr pts)
_B = None  # BYE sentinel

OPP_SCORE_DATA = {
"RB": [
{"rank":1,"player":"Christian McCaffrey (SF)","w1":29.7,"w2":16.7,"w3":32.6,"w4":30.7,"w5":28.6,"w6":21.5,"w7":24.4,"w8":10.6,"w9":28.4,"w10":17.0,"w11":19.0,"w12":19.9,"w13":23.2,"w14":_B,"avg_l4":19.8,"avg":23.3,"total":302.4,"opp_fpts":286.0},
{"rank":2,"player":"Jonathan Taylor (IND)","w1":15.9,"w2":19.1,"w3":21.6,"w4":15.8,"w5":25.1,"w6":22.0,"w7":16.6,"w8":8.3,"w9":12.8,"w10":24.8,"w11":_B,"w12":14.9,"w13":16.2,"w14":15.9,"avg_l4":18.6,"avg":17.6,"total":228.8,"opp_fpts":291.5},
{"rank":3,"player":"Bijan Robinson (ATL)","w1":17.2,"w2":19.1,"w3":13.2,"w4":15.8,"w5":_B,"w6":20.1,"w7":18.3,"w8":7.9,"w9":18.7,"w10":10.9,"w11":22.3,"w12":11.0,"w13":24.5,"w14":19.3,"avg_l4":17.2,"avg":16.8,"total":218.3,"opp_fpts":236.3},
{"rank":4,"player":"Javonte Williams (DAL)","w1":14.4,"w2":18.5,"w3":13.0,"w4":20.4,"w5":14.5,"w6":21.9,"w7":15.8,"w8":17.4,"w9":12.2,"w10":_B,"w11":14.0,"w12":16.9,"w13":14.4,"w14":21.3,"avg_l4":15.1,"avg":16.5,"total":214.6,"opp_fpts":193.5},
{"rank":5,"player":"De'Von Achane (MIA)","w1":7.9,"w2":16.5,"w3":17.7,"w4":16.5,"w5":16.9,"w6":16.4,"w7":12.1,"w8":21.0,"w9":18.0,"w10":17.8,"w11":25.5,"w12":_B,"w13":18.2,"w14":6.4,"avg_l4":20.5,"avg":16.2,"total":210.8,"opp_fpts":244.4},
{"rank":6,"player":"Jahmyr Gibbs (DET)","w1":17.2,"w2":11.1,"w3":27.1,"w4":13.3,"w5":8.3,"w6":16.0,"w7":13.7,"w8":_B,"w9":7.9,"w10":13.7,"w11":18.3,"w12":23.2,"w13":17.0,"w14":22.4,"avg_l4":18.0,"avg":16.1,"total":209.0,"opp_fpts":278.6},
{"rank":7,"player":"Derrick Henry (BAL)","w1":10.3,"w2":7.3,"w3":12.4,"w4":7.4,"w5":13.9,"w6":17.9,"w7":_B,"w8":17.0,"w9":14.2,"w10":16.9,"w11":20.0,"w12":24.9,"w13":6.2,"w14":27.7,"avg_l4":17.0,"avg":15.1,"total":195.9,"opp_fpts":181.0},
{"rank":8,"player":"Saquon Barkley (PHI)","w1":21.5,"w2":16.8,"w3":22.2,"w4":15.8,"w5":6.3,"w6":13.5,"w7":10.3,"w8":16.7,"w9":_B,"w10":14.5,"w11":18.9,"w12":13.8,"w13":8.8,"w14":16.5,"avg_l4":14.0,"avg":15.1,"total":195.8,"opp_fpts":169.6},
{"rank":9,"player":"Ashton Jeanty (LV)","w1":13.6,"w2":10.0,"w3":8.7,"w4":22.9,"w5":16.5,"w6":21.3,"w7":4.2,"w8":_B,"w9":15.5,"w10":16.9,"w11":11.8,"w12":19.8,"w13":19.8,"w14":13.6,"avg_l4":17.1,"avg":15.0,"total":194.4,"opp_fpts":160.9},
{"rank":10,"player":"James Cook III (BUF)","w1":12.1,"w2":11.8,"w3":14.7,"w4":20.7,"w5":8.7,"w6":8.7,"w7":_B,"w8":9.7,"w9":20.0,"w10":13.8,"w11":11.4,"w12":11.9,"w13":26.5,"w14":23.4,"avg_l4":15.9,"avg":14.9,"total":193.5,"opp_fpts":220.0},
{"rank":11,"player":"Chase Brown (CIN)","w1":17.4,"w2":16.6,"w3":12.3,"w4":8.4,"w5":12.8,"w6":8.5,"w7":14.1,"w8":12.8,"w9":26.7,"w10":_B,"w11":17.9,"w12":14.1,"w13":15.3,"w14":16.4,"avg_l4":15.7,"avg":14.9,"total":193.2,"opp_fpts":160.1},
{"rank":12,"player":"Josh Jacobs (GB)","w1":15.9,"w2":18.6,"w3":21.4,"w4":22.5,"w5":_B,"w6":16.4,"w7":12.9,"w8":13.3,"w9":17.6,"w10":19.0,"w11":8.1,"w12":0,"w13":11.5,"w14":15.8,"avg_l4":9.6,"avg":14.8,"total":192.9,"opp_fpts":192.3},
{"rank":13,"player":"Travis Etienne Jr. (JAC)","w1":11.4,"w2":12.1,"w3":12.1,"w4":14.3,"w5":16.4,"w6":11.6,"w7":7.4,"w8":_B,"w9":25.3,"w10":18.4,"w11":23.9,"w12":12.0,"w13":7.2,"w14":16.5,"avg_l4":15.4,"avg":14.5,"total":188.4,"opp_fpts":176.8},
{"rank":14,"player":"Kyren Williams (LAR)","w1":14.8,"w2":15.0,"w3":19.3,"w4":11.0,"w5":23.9,"w6":10.5,"w7":12.8,"w8":_B,"w9":19.6,"w10":15.6,"w11":10.0,"w12":7.2,"w13":11.2,"w14":12.3,"avg_l4":11.0,"avg":14.1,"total":183.2,"opp_fpts":189.9},
{"rank":15,"player":"Breece Hall (NYJ)","w1":15.8,"w2":8.4,"w3":13.6,"w4":15.4,"w5":16.7,"w6":11.2,"w7":8.9,"w8":18.3,"w9":_B,"w10":13.5,"w11":11.0,"w12":12.5,"w13":15.3,"w14":14.1,"avg_l4":13.1,"avg":13.4,"total":174.8,"opp_fpts":157.8},
{"rank":16,"player":"D'Andre Swift (CHI)","w1":15.8,"w2":11.1,"w3":12.7,"w4":17.1,"w5":_B,"w6":10.4,"w7":15.9,"w8":14.7,"w9":0,"w10":17.1,"w11":13.5,"w12":6.9,"w13":13.1,"w14":20.3,"avg_l4":12.6,"avg":13.0,"total":168.7,"opp_fpts":155.3},
{"rank":17,"player":"Quinshon Judkins (CLE)","w1":0,"w2":8.4,"w3":16.5,"w4":18.5,"w5":19.1,"w6":8.9,"w7":17.9,"w8":7.9,"w9":_B,"w10":14.5,"w11":14.3,"w12":11.6,"w13":15.0,"w14":12.1,"avg_l4":13.8,"avg":12.7,"total":164.7,"opp_fpts":146.0},
{"rank":18,"player":"Rico Dowdle (CAR)","w1":4.8,"w2":7.6,"w3":11.4,"w4":5.7,"w5":19.5,"w6":23.2,"w7":10.9,"w8":4.1,"w9":21.2,"w10":14.2,"w11":19.0,"w12":7.4,"w13":11.4,"w14":_B,"avg_l4":13.0,"avg":12.3,"total":160.2,"opp_fpts":168.8},
{"rank":19,"player":"Woody Marks (HOU)","w1":1.5,"w2":2.6,"w3":5.2,"w4":14.1,"w5":6.4,"w6":_B,"w7":18.9,"w8":10.0,"w9":8.4,"w10":17.3,"w11":13.7,"w12":14.4,"w13":12.5,"w14":30.0,"avg_l4":14.5,"avg":11.9,"total":155.0,"opp_fpts":115.0},
{"rank":20,"player":"Jaylen Warren (PIT)","w1":13.7,"w2":14.9,"w3":20.9,"w4":0,"w5":_B,"w6":7.8,"w7":15.3,"w8":9.9,"w9":15.5,"w10":9.3,"w11":7.3,"w12":12.6,"w13":13.6,"w14":10.8,"avg_l4":10.7,"avg":11.7,"total":151.6,"opp_fpts":143.9},
{"rank":21,"player":"Kenneth Gainwell (PIT)","w1":7.9,"w2":9.7,"w3":4.9,"w4":25.5,"w5":_B,"w6":9.6,"w7":3.7,"w8":4.7,"w9":7.0,"w10":5.7,"w11":21.6,"w12":15.1,"w13":7.5,"w14":26.3,"avg_l4":12.5,"avg":11.5,"total":149.3,"opp_fpts":124.7},
{"rank":22,"player":"Kenneth Walker III (SEA)","w1":10.1,"w2":7.7,"w3":12.7,"w4":11.9,"w5":9.6,"w6":6.2,"w7":8.7,"w8":_B,"w9":11.2,"w10":10.0,"w11":13.2,"w12":14.1,"w13":11.0,"w14":16.0,"avg_l4":12.1,"avg":10.9,"total":142.3,"opp_fpts":128.1},
{"rank":23,"player":"Tony Pollard (TEN)","w1":12.0,"w2":11.3,"w3":17.7,"w4":10.4,"w5":12.1,"w6":7.3,"w7":9.6,"w8":7.8,"w9":12.4,"w10":_B,"w11":8.4,"w12":11.1,"w13":7.3,"w14":14.5,"avg_l4":8.9,"avg":10.9,"total":141.8,"opp_fpts":122.9},
{"rank":24,"player":"TreVeyon Henderson (NE)","w1":9.1,"w2":3.7,"w3":8.9,"w4":9.2,"w5":6.3,"w6":6.8,"w7":1.0,"w8":6.8,"w9":15.4,"w10":13.4,"w11":24.5,"w12":17.7,"w13":15.8,"w14":_B,"avg_l4":17.8,"avg":10.7,"total":138.6,"opp_fpts":132.4},
{"rank":25,"player":"Kareem Hunt (KC)","w1":5.8,"w2":6.9,"w3":7.9,"w4":9.4,"w5":11.5,"w6":4.2,"w7":2.0,"w8":9.8,"w9":14.7,"w10":_B,"w11":10.5,"w12":23.7,"w13":14.5,"w14":16.5,"avg_l4":16.2,"avg":10.6,"total":137.6,"opp_fpts":124.9},
{"rank":26,"player":"Alvin Kamara (NO)","w1":9.5,"w2":20.7,"w3":11.4,"w4":15.5,"w5":13.1,"w6":14.0,"w7":8.9,"w8":5.2,"w9":6.3,"w10":16.2,"w11":_B,"w12":3.7,"w13":0,"w14":0,"avg_l4":6.6,"avg":9.6,"total":124.5,"opp_fpts":84.2},
{"rank":27,"player":"David Montgomery (DET)","w1":10.0,"w2":13.6,"w3":8.9,"w4":9.1,"w5":18.9,"w6":4.2,"w7":9.9,"w8":_B,"w9":13.4,"w10":10.5,"w11":4.2,"w12":7.5,"w13":9.7,"w14":4.2,"avg_l4":8.0,"avg":9.5,"total":124.0,"opp_fpts":133.3},
{"rank":28,"player":"RJ Harvey (DEN)","w1":4.2,"w2":4.7,"w3":4.3,"w4":14.3,"w5":5.3,"w6":5.4,"w7":6.7,"w8":8.8,"w9":6.5,"w10":7.0,"w11":10.6,"w12":_B,"w13":16.2,"w14":27.0,"avg_l4":11.3,"avg":9.3,"total":120.8,"opp_fpts":132.6},
{"rank":29,"player":"Kimani Vidal (LAC)","w1":0,"w2":0,"w3":0,"w4":0,"w5":4.9,"w6":20.1,"w7":11.8,"w8":19.1,"w9":11.4,"w10":15.6,"w11":4.7,"w12":_B,"w13":17.3,"w14":14.6,"avg_l4":12.5,"avg":9.2,"total":119.3,"opp_fpts":102.0},
{"rank":30,"player":"Zach Charbonnet (SEA)","w1":11.3,"w2":9.4,"w3":0,"w4":13.5,"w5":8.5,"w6":12.4,"w7":14.2,"w8":_B,"w9":5.2,"w10":10.6,"w11":9.5,"w12":4.8,"w13":10.6,"w14":8.6,"avg_l4":8.9,"avg":9.1,"total":118.3,"opp_fpts":110.5},
{"rank":31,"player":"Rachaad White (TB)","w1":2.1,"w2":9.0,"w3":3.6,"w4":8.5,"w5":16.7,"w6":13.7,"w7":11.6,"w8":14.0,"w9":_B,"w10":10.6,"w11":8.4,"w12":4.7,"w13":4.3,"w14":11.2,"avg_l4":7.0,"avg":9.1,"total":118.3,"opp_fpts":105.1},
{"rank":32,"player":"Kyle Monangai (CHI)","w1":1.1,"w2":6.8,"w3":5.9,"w4":2.0,"w5":_B,"w6":3.6,"w7":13.3,"w8":5.3,"w9":25.6,"w10":6.4,"w11":10.7,"w12":9.6,"w13":14.0,"w14":12.8,"avg_l4":10.2,"avg":9.0,"total":117.1,"opp_fpts":112.0},
{"rank":33,"player":"J.K. Dobbins (DEN)","w1":12.1,"w2":16.2,"w3":7.8,"w4":9.3,"w5":14.7,"w6":10.0,"w7":10.0,"w8":13.3,"w9":8.7,"w10":10.3,"w11":0,"w12":_B,"w13":0,"w14":0,"avg_l4":3.4,"avg":8.6,"total":112.2,"opp_fpts":110.4},
{"rank":34,"player":"Chuba Hubbard (CAR)","w1":17.1,"w2":14.1,"w3":14.4,"w4":8.4,"w5":0,"w6":0,"w7":12.1,"w8":8.9,"w9":7.8,"w10":2.6,"w11":5.3,"w12":8.3,"w13":10.9,"w14":_B,"avg_l4":6.8,"avg":8.4,"total":109.8,"opp_fpts":98.2},
{"rank":35,"player":"Cam Skattebo (NYG)","w1":4.9,"w2":14.8,"w3":13.8,"w4":23.5,"w5":15.3,"w6":18.8,"w7":14.7,"w8":3.7,"w9":0,"w10":0,"w11":0,"w12":0,"w13":0,"w14":_B,"avg_l4":0,"avg":8.4,"total":109.5,"opp_fpts":115.7},
{"rank":36,"player":"Jordan Mason (MIN)","w1":8.7,"w2":7.9,"w3":13.3,"w4":13.2,"w5":12.7,"w6":_B,"w7":9.4,"w8":3.1,"w9":7.9,"w10":3.1,"w11":3.1,"w12":4.1,"w13":4.2,"w14":14.2,"avg_l4":3.6,"avg":8.1,"total":104.8,"opp_fpts":108.0},
{"rank":37,"player":"Tyler Allgeier (ATL)","w1":8.5,"w2":12.7,"w3":2.7,"w4":13.3,"w5":_B,"w6":7.9,"w7":2.0,"w8":7.7,"w9":1.0,"w10":10.8,"w11":5.4,"w12":7.2,"w13":9.7,"w14":14.7,"avg_l4":8.3,"avg":8.0,"total":103.7,"opp_fpts":101.7},
{"rank":38,"player":"Rhamondre Stevenson (NE)","w1":8.6,"w2":12.8,"w3":7.0,"w4":7.4,"w5":10.9,"w6":11.2,"w7":14.8,"w8":11.0,"w9":0,"w10":0,"w11":0,"w12":8.7,"w13":9.4,"w14":_B,"avg_l4":4.5,"avg":7.8,"total":101.8,"opp_fpts":77.8},
{"rank":39,"player":"Zonovan Knight (ARI)","w1":0,"w2":0,"w3":0,"w4":0,"w5":4.9,"w6":13.0,"w7":14.9,"w8":_B,"w9":11.9,"w10":13.6,"w11":8.6,"w12":14.0,"w13":8.9,"w14":11.8,"avg_l4":11.3,"avg":7.8,"total":101.6,"opp_fpts":82.1},
{"rank":40,"player":"Tyrone Tracy Jr. (NYG)","w1":10.6,"w2":8.0,"w3":6.8,"w4":0,"w5":0,"w6":2.0,"w7":4.6,"w8":10.1,"w9":6.9,"w10":9.3,"w11":14.1,"w12":19.7,"w13":6.2,"w14":_B,"avg_l4":12.3,"avg":7.6,"total":98.3,"opp_fpts":80.7},
{"rank":41,"player":"Jacory Croskey-Merritt (WAS)","w1":7.9,"w2":3.1,"w3":8.6,"w4":5.8,"w5":11.0,"w6":11.5,"w7":10.5,"w8":5.7,"w9":7.2,"w10":7.3,"w11":9.1,"w12":_B,"w13":2.0,"w14":5.3,"avg_l4":6.2,"avg":7.3,"total":95.1,"opp_fpts":86.3},
{"rank":42,"player":"Bucky Irving (TB)","w1":15.7,"w2":15.2,"w3":20.6,"w4":13.1,"w5":0,"w6":0,"w7":0,"w8":0,"w9":_B,"w10":0,"w11":0,"w12":0,"w13":14.3,"w14":10.9,"avg_l4":3.6,"avg":6.9,"total":89.7,"opp_fpts":92.7},
{"rank":43,"player":"Nick Chubb (HOU)","w1":7.7,"w2":10.0,"w3":9.0,"w4":8.8,"w5":10.1,"w6":_B,"w7":5.8,"w8":10.9,"w9":7.3,"w10":3.6,"w11":3.7,"w12":5.9,"w13":6.3,"w14":0.5,"avg_l4":4.9,"avg":6.9,"total":89.7,"opp_fpts":77.0},
{"rank":44,"player":"Omarion Hampton (LAC)","w1":9.8,"w2":13.1,"w3":20.8,"w4":11.6,"w5":14.4,"w6":0,"w7":0,"w8":0,"w9":0,"w10":0,"w11":0,"w12":_B,"w13":0,"w14":19.8,"avg_l4":6.9,"avg":6.9,"total":89.5,"opp_fpts":80.7},
{"rank":45,"player":"Blake Corum (LAR)","w1":1.6,"w2":6.0,"w3":4.1,"w4":9.0,"w5":2.7,"w6":2.6,"w7":12.4,"w8":_B,"w9":6.6,"w10":8.4,"w11":11.4,"w12":3.6,"w13":5.3,"w14":12.4,"avg_l4":7.2,"avg":6.6,"total":85.9,"opp_fpts":83.3},
{"rank":46,"player":"Devin Singletary (NYG)","w1":1.5,"w2":1.6,"w3":2.0,"w4":3.6,"w5":5.2,"w6":1.5,"w7":1.0,"w8":2.1,"w9":10.4,"w10":12.5,"w11":19.6,"w12":8.9,"w13":9.4,"w14":_B,"avg_l4":12.6,"avg":6.1,"total":79.4,"opp_fpts":67.2},
{"rank":47,"player":"Michael Carter (ARI)","w1":0,"w2":0,"w3":0,"w4":0.5,"w5":16.4,"w6":12.5,"w7":5.8,"w8":_B,"w9":0,"w10":3.3,"w11":13.5,"w12":7.5,"w13":9.1,"w14":10.8,"avg_l4":8.3,"avg":6.1,"total":79.2,"opp_fpts":53.9},
{"rank":48,"player":"Aaron Jones Sr. (MIN)","w1":7.4,"w2":3.6,"w3":0,"w4":0,"w5":0,"w6":_B,"w7":0,"w8":6.9,"w9":6.8,"w10":12.9,"w11":14.7,"w12":9.0,"w13":7.4,"w14":10.0,"avg_l4":11.0,"avg":6.0,"total":78.5,"opp_fpts":72.6},
{"rank":49,"player":"Emanuel Wilson (GB)","w1":0.5,"w2":0,"w3":3.1,"w4":7.4,"w5":_B,"w6":2.6,"w7":4.2,"w8":14.1,"w9":8.7,"w10":1.6,"w11":8.4,"w12":21.6,"w13":2.0,"w14":3.3,"avg_l4":8.4,"avg":6.0,"total":77.4,"opp_fpts":70.3},
{"rank":50,"player":"Isiah Pacheco (KC)","w1":5.8,"w2":7.3,"w3":6.2,"w4":9.3,"w5":6.8,"w6":11.1,"w7":13.3,"w8":7.8,"w9":0,"w10":_B,"w11":0,"w12":0,"w13":3.7,"w14":4.6,"avg_l4":1.2,"avg":5.8,"total":75.9,"opp_fpts":62.0},
],
"WR": [
{"rank":1,"player":"Jaxon Smith-Njigba (SEA)","w1":19.2,"w2":14.9,"w3":15.8,"w4":14.2,"w5":18.5,"w6":23.1,"w7":21.2,"w8":_B,"w9":16.2,"w10":13.3,"w11":20.5,"w12":28.2,"w13":2.4,"w14":17.1,"avg_l4":17.1,"avg":17.3,"total":224.6,"opp_fpts":242.9},
{"rank":2,"player":"George Pickens (DAL)","w1":5.9,"w2":17.3,"w3":15.5,"w4":20.9,"w5":8.3,"w6":18.0,"w7":12.7,"w8":14.5,"w9":11.8,"w10":_B,"w11":16.5,"w12":21.0,"w13":17.4,"w14":11.8,"avg_l4":16.7,"avg":14.7,"total":191.6,"opp_fpts":206.9},
{"rank":3,"player":"Puka Nacua (LAR)","w1":18.0,"w2":14.4,"w3":19.0,"w4":24.7,"w5":15.4,"w6":5.8,"w7":0,"w8":_B,"w9":17.5,"w10":5.6,"w11":12.8,"w12":15.3,"w13":12.3,"w14":22.4,"avg_l4":15.7,"avg":14.1,"total":183.2,"opp_fpts":212.4},
{"rank":4,"player":"Davante Adams (LAR)","w1":10.0,"w2":24.8,"w3":16.3,"w4":11.1,"w5":14.9,"w6":14.3,"w7":15.4,"w8":_B,"w9":15.2,"w10":16.2,"w11":8.2,"w12":14.9,"w13":11.5,"w14":9.9,"avg_l4":11.1,"avg":14.1,"total":182.8,"opp_fpts":183.8},
{"rank":5,"player":"Ja'Marr Chase (CIN)","w1":4.6,"w2":23.2,"w3":7.7,"w4":6.1,"w5":16.7,"w6":20.9,"w7":27.4,"w8":16.5,"w9":15.6,"w10":_B,"w11":10.8,"w12":0,"w13":23.8,"w14":7.5,"avg_l4":10.5,"avg":13.9,"total":180.8,"opp_fpts":176.4},
{"rank":6,"player":"Amon-Ra St. Brown (DET)","w1":11.6,"w2":22.9,"w3":15.7,"w4":11.7,"w5":10.4,"w6":14.4,"w7":10.9,"w8":_B,"w9":20.1,"w10":11.3,"w11":11.9,"w12":21.0,"w13":0.6,"w14":10.3,"avg_l4":10.9,"avg":13.3,"total":172.6,"opp_fpts":193.0},
{"rank":7,"player":"Nico Collins (HOU)","w1":6.4,"w2":15.7,"w3":15.1,"w4":9.0,"w5":9.8,"w6":_B,"w7":8.4,"w8":0,"w9":15.7,"w10":30.7,"w11":17.6,"w12":6.1,"w13":15.4,"w14":16.4,"avg_l4":13.9,"avg":12.8,"total":166.3,"opp_fpts":153.6},
{"rank":8,"player":"Chris Olave (NO)","w1":14.1,"w2":13.4,"w3":15.3,"w4":7.6,"w5":13.5,"w6":15.9,"w7":16.2,"w8":14.1,"w9":8.3,"w10":15.9,"w11":_B,"w12":12.8,"w13":11.1,"w14":5.3,"avg_l4":9.7,"avg":12.6,"total":163.6,"opp_fpts":147.8},
{"rank":9,"player":"Tetairoa McMillan (CAR)","w1":12.2,"w2":15.4,"w3":10.4,"w4":9.3,"w5":15.5,"w6":9.7,"w7":5.0,"w8":18.5,"w9":10.6,"w10":10.6,"w11":23.1,"w12":8.4,"w13":4.0,"w14":_B,"avg_l4":11.8,"avg":11.7,"total":152.5,"opp_fpts":147.1},
{"rank":10,"player":"A.J. Brown (PHI)","w1":1.6,"w2":7.5,"w3":18.3,"w4":5.7,"w5":8.3,"w6":16.8,"w7":14.7,"w8":0,"w9":_B,"w10":3.0,"w11":16.4,"w12":17.9,"w13":21.9,"w14":15.3,"avg_l4":17.9,"avg":11.3,"total":147.5,"opp_fpts":146.9},
{"rank":11,"player":"CeeDee Lamb (DAL)","w1":15.8,"w2":19.7,"w3":0,"w4":0,"w5":0,"w6":0,"w7":10.8,"w8":18.1,"w9":15.5,"w10":_B,"w11":15.5,"w12":17.8,"w13":17.8,"w14":15.2,"avg_l4":16.6,"avg":11.2,"total":146.2,"opp_fpts":133.2},
{"rank":12,"player":"Emeka Egbuka (TB)","w1":10.8,"w2":6.4,"w3":12.5,"w4":14.2,"w5":19.9,"w6":4.6,"w7":15.0,"w8":9.9,"w9":_B,"w10":19.9,"w11":9.0,"w12":7.6,"w13":9.3,"w14":6.7,"avg_l4":8.1,"avg":11.2,"total":145.8,"opp_fpts":146.5},
{"rank":13,"player":"Jaylen Waddle (MIA)","w1":6.7,"w2":12.6,"w3":7.8,"w4":10.4,"w5":19.6,"w6":15.5,"w7":4.2,"w8":11.2,"w9":14.9,"w10":13.6,"w11":9.7,"w12":_B,"w13":7.1,"w14":10.7,"avg_l4":9.2,"avg":11.1,"total":144.0,"opp_fpts":148.1},
{"rank":14,"player":"Drake London (ATL)","w1":16.9,"w2":5.3,"w3":9.8,"w4":19.0,"w5":_B,"w6":24.6,"w7":10.5,"w8":0,"w9":27.2,"w10":16.0,"w11":13.9,"w12":0,"w13":0,"w14":0,"avg_l4":3.5,"avg":11.0,"total":143.2,"opp_fpts":147.0},
{"rank":15,"player":"Courtland Sutton (DEN)","w1":13.4,"w2":4.8,"w3":14.9,"w4":8.3,"w5":13.8,"w6":5.2,"w7":17.3,"w8":10.3,"w9":6.9,"w10":5.3,"w11":12.5,"w12":_B,"w13":13.2,"w14":14.0,"avg_l4":13.2,"avg":10.8,"total":139.9,"opp_fpts":137.3},
{"rank":16,"player":"Michael Wilson (ARI)","w1":2.8,"w2":4.1,"w3":1.7,"w4":4.6,"w5":3.4,"w6":8.8,"w7":7.7,"w8":_B,"w9":4.9,"w10":11.6,"w11":29.1,"w12":24.4,"w13":9.1,"w14":27.5,"avg_l4":22.5,"avg":10.7,"total":139.7,"opp_fpts":119.7},
{"rank":17,"player":"Justin Jefferson (MIN)","w1":12.2,"w2":12.3,"w3":8.0,"w4":19.5,"w5":16.6,"w6":_B,"w7":11.8,"w8":10.4,"w9":12.8,"w10":12.5,"w11":9.3,"w12":8.3,"w13":3.1,"w14":2.3,"avg_l4":5.8,"avg":10.7,"total":139.1,"opp_fpts":125.4},
{"rank":18,"player":"Wan'Dale Robinson (NYG)","w1":9.0,"w2":20.9,"w3":5.2,"w4":4.7,"w5":7.8,"w6":8.6,"w7":14.0,"w8":5.8,"w9":10.6,"w10":11.1,"w11":11.0,"w12":23.9,"w13":6.4,"w14":_B,"avg_l4":13.8,"avg":10.7,"total":139.0,"opp_fpts":137.5},
{"rank":19,"player":"DeVonta Smith (PHI)","w1":2.3,"w2":7.7,"w3":16.7,"w4":3.8,"w5":16.5,"w6":6.8,"w7":23.5,"w8":12.9,"w9":_B,"w10":10.9,"w11":3.9,"w12":16.8,"w13":8.3,"w14":8.3,"avg_l4":9.3,"avg":10.6,"total":138.4,"opp_fpts":133.9},
{"rank":20,"player":"Keenan Allen (LAC)","w1":13.4,"w2":10.6,"w3":18.5,"w4":7.5,"w5":11.9,"w6":9.6,"w7":22.3,"w8":7.2,"w9":6.1,"w10":5.1,"w11":8.9,"w12":_B,"w13":8.2,"w14":4.2,"avg_l4":7.1,"avg":10.3,"total":133.7,"opp_fpts":119.9},
{"rank":21,"player":"Zay Flowers (BAL)","w1":13.7,"w2":13.7,"w3":1.7,"w4":11.7,"w5":9.6,"w6":9.6,"w7":0,"w8":14.4,"w9":8.9,"w10":8.4,"w11":10.2,"w12":11.5,"w13":0,"w14":19.0,"avg_l4":10.2,"avg":9.5,"total":132.4,"opp_fpts":129.5},
{"rank":22,"player":"Michael Pittman Jr. (IND)","w1":11.3,"w2":7.0,"w3":7.5,"w4":11.0,"w5":11.7,"w6":2.9,"w7":12.7,"w8":13.6,"w9":18.6,"w10":3.0,"w11":_B,"w12":10.1,"w13":3.9,"w14":14.5,"avg_l4":9.5,"avg":9.8,"total":127.8,"opp_fpts":148.4},
{"rank":23,"player":"Tee Higgins (CIN)","w1":6.1,"w2":11.2,"w3":2.7,"w4":9.9,"w5":8.5,"w6":11.2,"w7":16.7,"w8":5.7,"w9":18.5,"w10":_B,"w11":12.8,"w12":6.4,"w13":0,"w14":17.8,"avg_l4":9.3,"avg":9.8,"total":127.6,"opp_fpts":145.7},
{"rank":24,"player":"Rome Odunze (CHI)","w1":11.3,"w2":20.5,"w3":10.5,"w4":13.1,"w5":_B,"w6":4.1,"w7":5.1,"w8":19.0,"w9":3.4,"w10":16.1,"w11":8.7,"w12":9.4,"w13":6.1,"w14":0,"avg_l4":6.1,"avg":9.8,"total":127.3,"opp_fpts":124.1},
{"rank":25,"player":"Ladd McConkey (LAC)","w1":12.3,"w2":6.9,"w3":8.4,"w4":4.4,"w5":11.3,"w6":16.7,"w7":18.3,"w8":13.3,"w9":6.5,"w10":12.2,"w11":2.3,"w12":_B,"w13":10.9,"w14":3.8,"avg_l4":5.7,"avg":9.8,"total":127.1,"opp_fpts":129.0},
{"rank":26,"player":"Alec Pierce (IND)","w1":7.7,"w2":12.4,"w3":10.1,"w4":0,"w5":0,"w6":6.3,"w7":16.8,"w8":11.1,"w9":18.8,"w10":12.8,"w11":_B,"w12":5.1,"w13":13.1,"w14":11.2,"avg_l4":9.8,"avg":9.6,"total":125.4,"opp_fpts":107.9},
{"rank":27,"player":"Stefon Diggs (NE)","w1":8.8,"w2":5.3,"w3":3.3,"w4":16.1,"w5":18.9,"w6":5.1,"w7":11.7,"w8":9.0,"w9":7.6,"w10":11.0,"w11":15.5,"w12":4.2,"w13":5.0,"w14":_B,"avg_l4":8.2,"avg":9.4,"total":121.6,"opp_fpts":120.5},
{"rank":28,"player":"DK Metcalf (PIT)","w1":6.1,"w2":6.9,"w3":5.1,"w4":8.7,"w5":_B,"w6":12.8,"w7":8.6,"w8":10.6,"w9":5.6,"w10":9.0,"w11":7.7,"w12":7.9,"w13":5.0,"w14":26.9,"avg_l4":11.9,"avg":9.3,"total":120.8,"opp_fpts":138.5},
{"rank":29,"player":"Troy Franklin (DEN)","w1":5.8,"w2":16.2,"w3":3.2,"w4":11.3,"w5":7.9,"w6":4.1,"w7":14.6,"w8":12.7,"w9":10.7,"w10":10.8,"w11":12.1,"w12":_B,"w13":4.3,"w14":4.6,"avg_l4":7.0,"avg":9.1,"total":118.3,"opp_fpts":114.5},
{"rank":30,"player":"Romeo Doubs (GB)","w1":13.1,"w2":6.2,"w3":2.4,"w4":14.9,"w5":_B,"w6":12.4,"w7":12.4,"w8":7.5,"w9":20.3,"w10":3.0,"w11":9.1,"w12":5.9,"w13":8.5,"w14":1.2,"avg_l4":6.2,"avg":9.0,"total":117.0,"opp_fpts":108.7},
{"rank":31,"player":"Marvin Harrison Jr. (ARI)","w1":11.6,"w2":7.9,"w3":8.1,"w4":13.7,"w5":13.5,"w6":4.2,"w7":10.0,"w8":_B,"w9":17.7,"w10":15.2,"w11":0,"w12":0,"w13":11.2,"w14":0,"avg_l4":2.8,"avg":8.7,"total":113.0,"opp_fpts":105.4},
{"rank":32,"player":"Jordan Addison (MIN)","w1":"S","w2":"S","w3":"S","w4":12.1,"w5":10.4,"w6":_B,"w7":27.5,"w8":6.4,"w9":9.1,"w10":12.5,"w11":8.2,"w12":0.6,"w13":11.3,"w14":11.7,"avg_l4":8.0,"avg":11.0,"total":109.9,"opp_fpts":89.1},
{"rank":33,"player":"Jameson Williams (DET)","w1":5.9,"w2":9.5,"w3":6.5,"w4":8.2,"w5":2.4,"w6":6.9,"w7":1.2,"w8":_B,"w9":10.5,"w10":13.0,"w11":12.8,"w12":1.8,"w13":13.8,"w14":14.7,"avg_l4":10.8,"avg":8.2,"total":107.1,"opp_fpts":139.9},
{"rank":34,"player":"Jerry Jeudy (CLE)","w1":11.6,"w2":9.9,"w3":5.1,"w4":11.7,"w5":6.1,"w6":16.2,"w7":4.9,"w8":4.4,"w9":_B,"w10":13.2,"w11":7.2,"w12":4.8,"w13":5.3,"w14":6.9,"avg_l4":6.0,"avg":8.2,"total":107.1,"opp_fpts":78.7},
{"rank":35,"player":"Deebo Samuel Sr. (WAS)","w1":11.5,"w2":5.1,"w3":3.1,"w4":16.2,"w5":16.2,"w6":4.6,"w7":0,"w8":7.8,"w9":6.5,"w10":9.3,"w11":8.2,"w12":_B,"w13":11.2,"w14":5.6,"avg_l4":8.3,"avg":8.1,"total":105.2,"opp_fpts":128.0},
{"rank":36,"player":"Quentin Johnston (LAC)","w1":12.2,"w2":11.6,"w3":16.2,"w4":17.7,"w5":6.3,"w6":0,"w7":10.2,"w8":0,"w9":11.2,"w10":5.8,"w11":3.4,"w12":_B,"w13":7.2,"w14":2.4,"avg_l4":4.3,"avg":8.0,"total":104.3,"opp_fpts":115.0},
{"rank":37,"player":"DJ Moore (CHI)","w1":11.3,"w2":7.4,"w3":9.0,"w4":6.7,"w5":_B,"w6":7.0,"w7":8.2,"w8":11.4,"w9":9.5,"w10":2.4,"w11":4.8,"w12":13.6,"w13":8.5,"w14":3.1,"avg_l4":7.5,"avg":7.9,"total":102.7,"opp_fpts":102.1},
{"rank":38,"player":"Tre Tucker (LV)","w1":7.7,"w2":7.9,"w3":22.6,"w4":2.8,"w5":11.8,"w6":6.2,"w7":3.5,"w8":_B,"w9":4.7,"w10":5.5,"w11":10.7,"w12":8.1,"w13":5.1,"w14":5.4,"avg_l4":7.3,"avg":7.8,"total":101.9,"opp_fpts":114.0},
{"rank":39,"player":"Jauan Jennings (SF)","w1":6.2,"w2":11.0,"w3":0,"w4":8.0,"w5":0,"w6":2.4,"w7":6.8,"w8":10.6,"w9":10.7,"w10":14.6,"w11":10.6,"w12":9.2,"w13":9.7,"w14":_B,"avg_l4":9.8,"avg":7.7,"total":99.8,"opp_fpts":96.3},
{"rank":40,"player":"Brian Thomas Jr. (JAC)","w1":6.5,"w2":17.8,"w3":6.4,"w4":10.1,"w5":12.2,"w6":14.4,"w7":7.5,"w8":_B,"w9":6.6,"w10":0,"w11":0,"w12":0,"w13":3.7,"w14":12.7,"avg_l4":4.1,"avg":7.5,"total":97.9,"opp_fpts":84.6},
{"rank":41,"player":"Parker Washington (JAC)","w1":0,"w2":7.0,"w3":10.9,"w4":2.1,"w5":4.1,"w6":5.1,"w7":14.5,"w8":_B,"w9":15.0,"w10":14.0,"w11":3.5,"w12":13.3,"w13":4.7,"w14":0,"avg_l4":5.4,"avg":7.2,"total":94.2,"opp_fpts":93.2},
{"rank":42,"player":"Marquise Brown (KC)","w1":21.7,"w2":5.7,"w3":7.2,"w4":7.7,"w5":9.9,"w6":9.3,"w7":5.6,"w8":0.6,"w9":10.1,"w10":_B,"w11":5.8,"w12":0.4,"w13":4.8,"w14":5.4,"avg_l4":4.1,"avg":7.2,"total":94.2,"opp_fpts":100.4},
{"rank":43,"player":"Josh Downs (IND)","w1":2.9,"w2":11.2,"w3":5.6,"w4":5.1,"w5":8.6,"w6":14.3,"w7":0,"w8":7.0,"w9":13.7,"w10":1.6,"w11":_B,"w12":5.5,"w13":7.7,"w14":10.3,"avg_l4":7.8,"avg":7.2,"total":93.6,"opp_fpts":77.3},
{"rank":44,"player":"Xavier Worthy (KC)","w1":1.5,"w2":0,"w3":0,"w4":12.5,"w5":12.2,"w6":7.3,"w7":9.0,"w8":7.5,"w9":7.6,"w10":_B,"w11":4.1,"w12":12.9,"w13":9.9,"w14":6.8,"avg_l4":8.4,"avg":7.0,"total":91.3,"opp_fpts":79.2},
{"rank":45,"player":"Rashee Rice (KC)","w1":"S","w2":"S","w3":"S","w4":"S","w5":"S","w6":"S","w7":13.8,"w8":14.9,"w9":12.5,"w10":_B,"w11":10.3,"w12":17.6,"w13":17.3,"w14":4.3,"avg_l4":12.4,"avg":13.0,"total":90.7,"opp_fpts":115.0},
{"rank":46,"player":"Elic Ayomanor (TEN)","w1":5.8,"w2":10.9,"w3":9.9,"w4":8.8,"w5":4.5,"w6":5.4,"w7":4.6,"w8":11.4,"w9":8.6,"w10":_B,"w11":4.0,"w12":0,"w13":3.7,"w14":4.7,"avg_l4":3.1,"avg":6.3,"total":82.3,"opp_fpts":68.3},
{"rank":47,"player":"Kayshon Boutte (NE)","w1":16.8,"w2":4.1,"w3":6.5,"w4":4.0,"w5":6.5,"w6":12.8,"w7":7.6,"w8":11.9,"w9":0.6,"w10":0,"w11":0,"w12":2.7,"w13":8.2,"w14":_B,"avg_l4":3.6,"avg":6.3,"total":81.7,"opp_fpts":98.6},
{"rank":48,"player":"Jayden Higgins (HOU)","w1":5.4,"w2":1.1,"w3":1.2,"w4":3.5,"w5":5.4,"w6":_B,"w7":3.4,"w8":9.8,"w9":1.1,"w10":11.7,"w11":10.1,"w12":13.2,"w13":8.6,"w14":6.3,"avg_l4":9.6,"avg":6.2,"total":80.9,"opp_fpts":80.8},
{"rank":49,"player":"Khalil Shakir (BUF)","w1":13.7,"w2":1.7,"w3":5.6,"w4":4.0,"w5":10.7,"w6":5.1,"w7":0,"w8":5.3,"w9":3.6,"w10":11.0,"w11":1.5,"w12":9.0,"w13":4.6,"w14":4.5,"avg_l4":4.9,"avg":5.7,"total":80.2,"opp_fpts":109.5},
{"rank":50,"player":"Mack Hollins (NE)","w1":1.6,"w2":3.8,"w3":4.9,"w4":2.7,"w5":0,"w6":5.2,"w7":5.9,"w8":12.8,"w9":3.8,"w10":18.2,"w11":9.0,"w12":6.6,"w13":5.2,"w14":_B,"avg_l4":6.9,"avg":6.1,"total":79.6,"opp_fpts":73.9},
],
"TE": [
{"rank":1,"player":"Trey McBride (ARI)","w1":9.3,"w2":10.5,"w3":10.6,"w4":13.0,"w5":7.6,"w6":22.2,"w7":18.9,"w8":_B,"w9":16.0,"w10":21.7,"w11":18.5,"w12":10.8,"w13":13.7,"w14":11.7,"avg_l4":13.7,"avg":14.2,"total":184.6,"opp_fpts":188.2},
{"rank":2,"player":"Jake Ferguson (DAL)","w1":5.2,"w2":12.9,"w3":16.5,"w4":8.0,"w5":9.2,"w6":11.4,"w7":11.0,"w8":0.6,"w9":13.1,"w10":_B,"w11":4.9,"w12":14.7,"w13":6.2,"w14":11.4,"avg_l4":9.3,"avg":9.6,"total":125.0,"opp_fpts":133.0},
{"rank":3,"player":"Tyler Warren (IND)","w1":15.1,"w2":10.1,"w3":2.7,"w4":11.9,"w5":8.2,"w6":14.0,"w7":8.4,"w8":4.6,"w9":11.7,"w10":9.5,"w11":_B,"w12":6.7,"w13":7.6,"w14":10.5,"avg_l4":8.2,"avg":9.3,"total":120.9,"opp_fpts":130.7},
{"rank":4,"player":"Brock Bowers (LV)","w1":10.3,"w2":9.1,"w3":6.9,"w4":6.0,"w5":0,"w6":0,"w7":0,"w8":_B,"w9":26.9,"w10":4.6,"w11":15.8,"w12":11.9,"w13":11.9,"w14":13.2,"avg_l4":13.2,"avg":9.0,"total":116.6,"opp_fpts":126.6},
{"rank":5,"player":"Hunter Henry (NE)","w1":10.1,"w2":4.0,"w3":21.5,"w4":4.6,"w5":9.6,"w6":3.2,"w7":5.0,"w8":2.7,"w9":6.3,"w10":4.0,"w11":9.3,"w12":18.2,"w13":15.7,"w14":_B,"avg_l4":14.4,"avg":8.8,"total":114.3,"opp_fpts":113.5},
{"rank":6,"player":"Travis Kelce (KC)","w1":7.0,"w2":8.3,"w3":4.7,"w4":6.8,"w5":12.4,"w6":11.4,"w7":4.3,"w8":12.0,"w9":11.0,"w10":_B,"w11":10.5,"w12":9.9,"w13":8.3,"w14":2.7,"avg_l4":7.8,"avg":8.4,"total":109.4,"opp_fpts":134.8},
{"rank":7,"player":"Harold Fannin Jr. (CLE)","w1":12.5,"w2":6.0,"w3":2.7,"w4":8.7,"w5":4.9,"w6":12.1,"w7":4.3,"w8":11.9,"w9":_B,"w10":8.0,"w11":7.4,"w12":4.4,"w13":6.8,"w14":15.4,"avg_l4":8.5,"avg":8.1,"total":105.0,"opp_fpts":114.4},
{"rank":8,"player":"Dalton Schultz (HOU)","w1":4.9,"w2":3.9,"w3":8.8,"w4":6.1,"w5":11.7,"w6":_B,"w7":9.8,"w8":3.1,"w9":8.1,"w10":12.6,"w11":10.8,"w12":7.0,"w13":10.5,"w14":3.9,"avg_l4":8.1,"avg":7.8,"total":101.4,"opp_fpts":94.4},
{"rank":9,"player":"Juwan Johnson (NO)","w1":15.9,"w2":8.8,"w3":9.3,"w4":3.4,"w5":6.1,"w6":1.6,"w7":8.5,"w8":9.7,"w9":6.8,"w10":9.2,"w11":_B,"w12":8.9,"w13":7.5,"w14":4.6,"avg_l4":7.0,"avg":7.7,"total":100.4,"opp_fpts":106.4},
{"rank":10,"player":"Zach Ertz (WAS)","w1":7.3,"w2":9.4,"w3":5.6,"w4":6.1,"w5":0.6,"w6":9.2,"w7":8.9,"w8":4.9,"w9":7.2,"w10":10.5,"w11":11.1,"w12":_B,"w13":17.8,"w14":1.7,"avg_l4":10.2,"avg":7.7,"total":100.2,"opp_fpts":101.4},
{"rank":11,"player":"Theo Johnson (NYG)","w1":3.7,"w2":8.1,"w3":2.9,"w4":5.9,"w5":14.9,"w6":4.1,"w7":6.7,"w8":4.4,"w9":6.7,"w10":13.4,"w11":5.9,"w12":15.2,"w13":7.9,"w14":_B,"avg_l4":9.7,"avg":7.7,"total":99.6,"opp_fpts":96.6},
{"rank":12,"player":"Mark Andrews (BAL)","w1":1.0,"w2":6.9,"w3":13.1,"w4":7.5,"w5":3.7,"w6":9.7,"w7":_B,"w8":6.9,"w9":8.0,"w10":6.1,"w11":10.7,"w12":6.9,"w13":9.0,"w14":10.1,"avg_l4":9.2,"avg":7.7,"total":99.6,"opp_fpts":93.6},
{"rank":13,"player":"Kyle Pitts Sr. (ATL)","w1":7.1,"w2":5.9,"w3":5.1,"w4":9.8,"w5":_B,"w6":6.8,"w7":11.0,"w8":9.7,"w9":10.0,"w10":6.0,"w11":2.4,"w12":5.1,"w13":7.2,"w14":12.5,"avg_l4":6.8,"avg":7.6,"total":98.6,"opp_fpts":100.1},
{"rank":14,"player":"Oronde Gadsden II (LAC)","w1":0,"w2":0,"w3":12.8,"w4":3.5,"w5":1.3,"w6":14.5,"w7":21.1,"w8":10.7,"w9":10.4,"w10":8.4,"w11":6.5,"w12":_B,"w13":3.8,"w14":2.5,"avg_l4":4.3,"avg":7.3,"total":95.5,"opp_fpts":83.6},
{"rank":15,"player":"Dallas Goedert (PHI)","w1":8.0,"w2":0,"w3":3.9,"w4":8.7,"w5":7.9,"w6":20.7,"w7":3.2,"w8":7.1,"w9":_B,"w10":7.4,"w11":3.9,"w12":2.4,"w13":4.9,"w14":11.9,"avg_l4":5.8,"avg":6.9,"total":90.2,"opp_fpts":114.1},
{"rank":16,"player":"AJ Barner (SEA)","w1":2.3,"w2":5.9,"w3":2.9,"w4":6.3,"w5":13.6,"w6":6.4,"w7":3.3,"w8":_B,"w9":7.0,"w10":2.3,"w11":14.6,"w12":4.7,"w13":4.6,"w14":7.8,"avg_l4":7.9,"avg":6.3,"total":81.7,"opp_fpts":89.9},
{"rank":17,"player":"Mason Taylor (NYJ)","w1":2.7,"w2":3.8,"w3":4.0,"w4":9.5,"w5":14.2,"w6":0.8,"w7":4.7,"w8":17.1,"w9":_B,"w10":1.6,"w11":5.2,"w12":4.6,"w13":4.1,"w14":6.8,"avg_l4":5.2,"avg":6.1,"total":79.2,"opp_fpts":66.9},
{"rank":18,"player":"T.J. Hockenson (MIN)","w1":3.6,"w2":2.4,"w3":13.2,"w4":6.8,"w5":4.9,"w6":_B,"w7":13.8,"w8":2.1,"w9":5.1,"w10":2.1,"w11":4.5,"w12":5.3,"w13":8.7,"w14":4.5,"avg_l4":5.7,"avg":5.9,"total":76.9,"opp_fpts":78.0},
{"rank":19,"player":"George Kittle (SF)","w1":6.9,"w2":0,"w3":0,"w4":0,"w5":0,"w6":0,"w7":1.2,"w8":8.3,"w9":7.9,"w10":17.7,"w11":12.6,"w12":9.5,"w13":11.9,"w14":_B,"avg_l4":11.3,"avg":5.8,"total":76.0,"opp_fpts":87.8},
{"rank":20,"player":"Colston Loveland (CHI)","w1":1.7,"w2":0.6,"w3":3.7,"w4":0,"w5":_B,"w6":5.1,"w7":6.2,"w8":7.5,"w9":13.2,"w10":7.2,"w11":5.9,"w12":8.9,"w13":6.6,"w14":6.8,"avg_l4":7.0,"avg":5.6,"total":73.3,"opp_fpts":85.0},
{"rank":21,"player":"Cade Otton (TB)","w1":1.7,"w2":6.3,"w3":0,"w4":2.8,"w5":5.8,"w6":5.8,"w7":10.0,"w8":4.6,"w9":_B,"w10":10.6,"w11":7.3,"w12":5.2,"w13":3.8,"w14":5.1,"avg_l4":5.3,"avg":5.3,"total":69.0,"opp_fpts":66.0},
{"rank":22,"player":"Tucker Kraft (GB)","w1":7.2,"w2":14.2,"w3":2.3,"w4":7.1,"w5":_B,"w6":6.0,"w7":12.9,"w8":13.1,"w9":5.2,"w10":0,"w11":0,"w12":0,"w13":0,"w14":0,"avg_l4":0,"avg":5.2,"total":68.0,"opp_fpts":101.2},
{"rank":23,"player":"Evan Engram (DEN)","w1":2.9,"w2":1.7,"w3":0,"w4":9.0,"w5":7.3,"w6":8.0,"w7":4.9,"w8":6.6,"w9":1.7,"w10":5.3,"w11":4.6,"w12":_B,"w13":11.4,"w14":1.4,"avg_l4":5.8,"avg":5.0,"total":64.6,"opp_fpts":61.4},
{"rank":24,"player":"Dalton Kincaid (BUF)","w1":9.0,"w2":6.3,"w3":8.2,"w4":3.1,"w5":12.2,"w6":0,"w7":_B,"w8":3.6,"w9":9.0,"w10":4.9,"w11":0,"w12":0,"w13":0,"w14":7.4,"avg_l4":1.8,"avg":4.9,"total":63.7,"opp_fpts":95.4},
{"rank":25,"player":"Sam LaPorta (DET)","w1":10.8,"w2":3.4,"w3":7.3,"w4":5.8,"w5":8.2,"w6":8.8,"w7":2.9,"w8":_B,"w9":9.3,"w10":5.1,"w11":0,"w12":0,"w13":0,"w14":0,"avg_l4":0,"avg":4.7,"total":61.5,"opp_fpts":86.9},
{"rank":26,"player":"David Njoku (CLE)","w1":5.1,"w2":6.1,"w3":5.7,"w4":4.0,"w5":13.0,"w6":9.8,"w7":0,"w8":7.5,"w9":_B,"w10":2.6,"w11":1.6,"w12":0,"w13":1.4,"w14":2.7,"avg_l4":1.4,"avg":4.6,"total":59.6,"opp_fpts":69.8},
{"rank":27,"player":"Gunnar Helm (TEN)","w1":3.0,"w2":1.0,"w3":2.5,"w4":1.7,"w5":6.4,"w6":4.7,"w7":5.4,"w8":8.0,"w9":2.1,"w10":_B,"w11":5.1,"w12":5.9,"w13":10.6,"w14":0.8,"avg_l4":5.6,"avg":4.4,"total":57.4,"opp_fpts":54.3},
{"rank":28,"player":"Chig Okonkwo (TEN)","w1":2.2,"w2":4.9,"w3":6.1,"w4":2.2,"w5":4.5,"w6":6.3,"w7":1.2,"w8":7.2,"w9":1.4,"w10":_B,"w11":8.1,"w12":5.0,"w13":5.9,"w14":1.3,"avg_l4":5.1,"avg":4.3,"total":56.2,"opp_fpts":63.1},
{"rank":29,"player":"Colby Parkinson (LAR)","w1":3.2,"w2":0,"w3":0,"w4":2.2,"w5":2.6,"w6":0,"w7":6.1,"w8":_B,"w9":3.3,"w10":10.8,"w11":2.7,"w12":7.1,"w13":7.0,"w14":10.1,"avg_l4":6.7,"avg":4.2,"total":55.2,"opp_fpts":57.3},
{"rank":30,"player":"Pat Freiermuth (PIT)","w1":4.1,"w2":7.4,"w3":2.2,"w4":0,"w5":_B,"w6":1.0,"w7":13.5,"w8":3.6,"w9":8.7,"w10":1.9,"w11":0.7,"w12":4.8,"w13":0,"w14":6.0,"avg_l4":2.9,"avg":4.1,"total":53.8,"opp_fpts":68.7},
{"rank":31,"player":"Dawson Knox (BUF)","w1":1.5,"w2":5.3,"w3":0,"w4":0.6,"w5":2.0,"w6":5.4,"w7":_B,"w8":2.2,"w9":3.2,"w10":7.6,"w11":3.7,"w12":2.8,"w13":6.8,"w14":11.7,"avg_l4":6.3,"avg":4.1,"total":52.8,"opp_fpts":52.1},
{"rank":32,"player":"Brenton Strange (JAC)","w1":6.5,"w2":4.1,"w3":8.2,"w4":6.5,"w5":0.3,"w6":0,"w7":0,"w8":_B,"w9":0,"w10":0,"w11":0,"w12":12.0,"w13":6.1,"w14":8.6,"avg_l4":6.7,"avg":4.0,"total":52.4,"opp_fpts":58.4},
{"rank":33,"player":"Cole Kmet (CHI)","w1":5.9,"w2":3.1,"w3":3.8,"w4":12.2,"w5":_B,"w6":0.6,"w7":2.4,"w8":0,"w9":1.9,"w10":3.8,"w11":4.7,"w12":0.8,"w13":4.8,"w14":8.3,"avg_l4":4.7,"avg":4.0,"total":52.3,"opp_fpts":50.3},
{"rank":34,"player":"Isaiah Likely (BAL)","w1":0,"w2":0,"w3":0,"w4":0,"w5":1.9,"w6":2.1,"w7":_B,"w8":3.6,"w9":8.1,"w10":6.1,"w11":4.6,"w12":2.9,"w13":9.6,"w14":11.4,"avg_l4":7.1,"avg":3.9,"total":50.1,"opp_fpts":39.8},
{"rank":35,"player":"Mike Gesicki (CIN)","w1":7.5,"w2":6.2,"w3":2.1,"w4":1.2,"w5":4.3,"w6":0,"w7":0,"w8":0,"w9":0,"w10":_B,"w11":0,"w12":6.8,"w13":8.2,"w14":13.3,"avg_l4":7.1,"avg":3.8,"total":49.5,"opp_fpts":36.1},
{"rank":36,"player":"Darnell Washington (PIT)","w1":0,"w2":0.6,"w3":0,"w4":4.9,"w5":_B,"w6":5.3,"w7":9.0,"w8":0,"w9":13.3,"w10":2.1,"w11":3.9,"w12":2.1,"w13":4.6,"w14":1.0,"avg_l4":2.9,"avg":3.6,"total":47.0,"opp_fpts":48.3},
{"rank":37,"player":"Taysom Hill (NO)","w1":0,"w2":0,"w3":0,"w4":0,"w5":6.9,"w6":1.1,"w7":4.5,"w8":3.1,"w9":4.6,"w10":8.6,"w11":_B,"w12":11.4,"w13":2.3,"w14":3.4,"avg_l4":5.7,"avg":3.5,"total":45.9,"opp_fpts":18.1},
{"rank":38,"player":"Jonnu Smith (PIT)","w1":3.9,"w2":2.5,"w3":2.7,"w4":1.6,"w5":_B,"w6":3.7,"w7":10.2,"w8":2.3,"w9":5.3,"w10":1.6,"w11":1.2,"w12":6.8,"w13":2.9,"w14":0.6,"avg_l4":2.8,"avg":3.5,"total":45.2,"opp_fpts":47.7},
{"rank":39,"player":"Ja'Tavion Sanders (CAR)","w1":4.3,"w2":17.5,"w3":3.3,"w4":0,"w5":0,"w6":0,"w7":3.2,"w8":4.0,"w9":1.2,"w10":4.6,"w11":5.5,"w12":1.2,"w13":0,"w14":_B,"avg_l4":2.2,"avg":3.4,"total":44.8,"opp_fpts":30.1},
{"rank":40,"player":"Noah Fant (CIN)","w1":5.6,"w2":4.7,"w3":4.4,"w4":0,"w5":0,"w6":3.6,"w7":5.9,"w8":3.0,"w9":4.8,"w10":_B,"w11":4.6,"w12":0.7,"w13":3.2,"w14":1.5,"avg_l4":2.5,"avg":3.2,"total":42.0,"opp_fpts":58.8},
{"rank":41,"player":"Jake Tonges (SF)","w1":4.8,"w2":3.5,"w3":3.4,"w4":6.3,"w5":12.3,"w6":6.6,"w7":0,"w8":2.9,"w9":0,"w10":0,"w11":0,"w12":0,"w13":0,"w14":_B,"avg_l4":0,"avg":3.1,"total":39.7,"opp_fpts":59.6},
{"rank":42,"player":"Tyler Higbee (LAR)","w1":0,"w2":3.9,"w3":3.2,"w4":4.7,"w5":0,"w6":7.3,"w7":6.9,"w8":_B,"w9":6.6,"w10":3.0,"w11":3.1,"w12":0,"w13":0,"w14":0,"avg_l4":0.8,"avg":3.0,"total":38.8,"opp_fpts":41.0},
{"rank":43,"player":"Elijah Arroyo (SEA)","w1":1.2,"w2":4.4,"w3":2.6,"w4":8.1,"w5":1.3,"w6":1.6,"w7":9.3,"w8":_B,"w9":3.8,"w10":1.0,"w11":1.2,"w12":0.8,"w13":1.2,"w14":0.6,"avg_l4":0.9,"avg":2.8,"total":37.0,"opp_fpts":29.4},
{"rank":44,"player":"Darren Waller (MIA)","w1":0,"w2":0,"w3":0,"w4":8.8,"w5":11.7,"w6":5.1,"w7":0,"w8":0,"w9":0,"w10":0,"w11":_B,"w12":7.0,"w13":4.0,"w14":0,"avg_l4":3.7,"avg":2.8,"total":36.6,"opp_fpts":48.6},
{"rank":45,"player":"Daniel Bellinger (NYG)","w1":4.3,"w2":0,"w3":1.3,"w4":1.7,"w5":7.6,"w6":0,"w7":11.8,"w8":2.8,"w9":0,"w10":5.4,"w11":0.6,"w12":1.2,"w13":0,"w14":_B,"avg_l4":0.6,"avg":2.8,"total":36.5,"opp_fpts":32.2},
{"rank":46,"player":"Michael Mayer (LV)","w1":6.0,"w2":2.0,"w3":0.6,"w4":0,"w5":0,"w6":7.4,"w7":1.7,"w8":_B,"w9":7.1,"w10":5.9,"w11":2.2,"w12":1.0,"w13":0,"w14":0,"avg_l4":0.8,"avg":2.6,"total":33.9,"opp_fpts":35.2},
{"rank":47,"player":"Austin Hooper (NE)","w1":3.0,"w2":5.0,"w3":3.7,"w4":0.2,"w5":0,"w6":1.0,"w7":4.4,"w8":3.8,"w9":2.4,"w10":0.6,"w11":0,"w12":8.5,"w13":0,"w14":_B,"avg_l4":2.8,"avg":2.5,"total":32.7,"opp_fpts":35.3},
{"rank":48,"player":"Davis Allen (LAR)","w1":4.7,"w2":3.2,"w3":0.6,"w4":0.5,"w5":3.2,"w6":1.4,"w7":0.6,"w8":_B,"w9":7.0,"w10":3.9,"w11":0,"w12":3.6,"w13":2.0,"w14":1.3,"avg_l4":1.7,"avg":2.5,"total":32.0,"opp_fpts":43.3},
{"rank":49,"player":"Tommy Tremble (CAR)","w1":0.6,"w2":3.8,"w3":3.7,"w4":10.7,"w5":1.5,"w6":3.1,"w7":0.6,"w8":0.7,"w9":0.6,"w10":0,"w11":3.7,"w12":0,"w13":1.3,"w14":_B,"avg_l4":1.6,"avg":2.3,"total":30.2,"opp_fpts":34.6},
{"rank":50,"player":"Tanner Hudson (CIN)","w1":0,"w2":0,"w3":0,"w4":0,"w5":0,"w6":7.2,"w7":0,"w8":3.6,"w9":4.1,"w10":_B,"w11":3.2,"w12":1.2,"w13":6.9,"w14":1.2,"avg_l4":3.1,"avg":2.1,"total":27.3,"opp_fpts":30.2},
],
}

def build_opp_df(rows):
    """Build styled DataFrame for Opportunity Score display."""
    records = []
    for d in rows:
        row = {"RK": d["rank"], "Player": d["player"]}
        for w in range(1, 15):
            val = d.get(f"w{w}")
            if val is None:
                row[f"W{w}"] = "BYE"
            elif val == "S":
                row[f"W{w}"] = "SUS"
            elif val == 0:
                row[f"W{w}"] = "—"
            else:
                row[f"W{w}"] = f"{val:.2f}"
        row["AVG (L4)"] = d["avg_l4"]
        row["AVG OPP"]  = d["avg"]
        row["TOTAL OPP"] = d["total"]
        row["OPP FPTS"]  = d["opp_fpts"]
        records.append(row)
    return pd.DataFrame(records)


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
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=ascending, key=lambda x: pd.to_numeric(x, errors="coerce"))
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

    tabs = st.tabs(["⬡  OVERALL", "⬡  QB", "⬡  RB", "⬡  WR", "⬡  TE", "⬡  SOS 2026", "⬡  MOCK BOARD", "⬡  DRAFT NOTES", "⬡  SOURCE COMPARE"])

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
            st.caption(f"// {len(mb)} players shown · FantasyPros PPR ADP 2026 · 12-team linear draft order")
        else:
            st.warning("Run create_mock_board.py to generate the mock board.")

    with tabs[7]:
        st.markdown('<div class="section-label">// DRAFT NOTES · 2026 SEASON</div>', unsafe_allow_html=True)

        MUST_DRAFT = {
            "Early Round Must Draft (1-3)": [
                "Omarion Hampton", "Ashton Jeanty",
                "Malik Nabers", "Chase Brown", "James Cook III", "Brock Bowers",
                "DeVonta Smith",
            ],
            "Mid Round Must Draft (4-7)": [
                "Ladd McConkey", "TreVeyon Henderson", "Cam Skattebo",
                "Christian Watson", "Emeka Egbuka", "Justin Herbert",
                "Harold Fannin Jr.", "Bhayshul Tuten", "DJ Moore",
            ],
            "Late Round Must Draft (8+)": [
                "Tucker Kraft", "Josh Downs", "Matthew Golden",
                "Jadarian Price", "Kyle Monangai", "George Kittle",
            ],
        }

        MUST_AVOID = {
            "Early Round Must Avoid (1-3)": [
                "Trey McBride", "De'Von Achane", "Christian McCaffrey",
                "Jeremiyah Love", "George Pickens",
            ],
            "Mid Round Must Avoid (4-7)": [
                "Davante Adams", "Tyler Warren", "Bucky Irving",
            ],
            "Late Round Must Avoid (8+)": [
                "Dallas Goedert", "Khalil Shakir",
                "Jacory Croskey-Merritt", "Calvin Ridley",
            ],
        }

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:0.8rem;color:#00cc44;letter-spacing:0.15em;margin-bottom:1rem;">// MUST DRAFTS</div>', unsafe_allow_html=True)
            for category, players in MUST_DRAFT.items():
                st.markdown(f'<div style="font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#7a2a5a;letter-spacing:0.12em;margin-top:1rem;margin-bottom:0.4rem;border-bottom:1px solid #2a0a1a;padding-bottom:0.2rem;">{category.upper()}</div>', unsafe_allow_html=True)
                for p in players:
                    st.markdown(f'<div style="padding:0.4rem 0.6rem;margin:0.2rem 0;background:#0a1f0a;border-left:3px solid #00cc44;font-size:0.85rem;color:#c8d6e0;">✦ {p}</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:0.8rem;color:#ff3333;letter-spacing:0.15em;margin-bottom:1rem;">// MUST AVOIDS</div>', unsafe_allow_html=True)
            for category, players in MUST_AVOID.items():
                st.markdown(f'<div style="font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#7a2a5a;letter-spacing:0.12em;margin-top:1rem;margin-bottom:0.4rem;border-bottom:1px solid #2a0a1a;padding-bottom:0.2rem;">{category.upper()}</div>', unsafe_allow_html=True)
                for p in players:
                    st.markdown(f'<div style="padding:0.4rem 0.6rem;margin:0.2rem 0;background:#1f0a0a;border-left:3px solid #ff3333;font-size:0.85rem;color:#c8d6e0;">✗ {p}</div>', unsafe_allow_html=True)

        st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:0.65rem;color:#7a2a5a;margin-top:1.5rem;">// Numbers in parentheses indicate suggested draft round · PPR scoring</div>', unsafe_allow_html=True)

    with tabs[8]:
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
    tabs = st.tabs(["⬡  QB", "⬡  RB", "⬡  WR", "⬡  TE", "⬡  TEAM SPLITS", "⬡  SOS", "⬡  OPP SCORE", "⬡  PLAYER PROFILE"])

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

    # ── OPP SCORE TAB ─────────────────────────────────────────────────────────
    with tabs[6]:
        st.markdown(f'<div class="section-label">// OPPORTUNITY SCORE · 2025 · TOP 50 PER POSITION</div>', unsafe_allow_html=True)

        if season == 2025:
            st.markdown(
                '<div style="font-family:Share Tech Mono,monospace;font-size:0.65rem;color:#7a2a5a;margin-bottom:1.2rem;line-height:1.8;">'
                '// Opportunity Score = expected PPR pts based on touch quality (RZ targets, routes, snap share). '
                'Higher = more high-value work. Compare AVG OPP vs OPP FPTS to spot over/underperformers.'
                '</div>',
                unsafe_allow_html=True
            )

            opp_pos_tabs = st.tabs(["⬡  RB", "⬡  WR", "⬡  TE"])

            for tab_idx, pos in enumerate(["RB", "WR", "TE"]):
                with opp_pos_tabs[tab_idx]:
                    df_opp = build_opp_df(OPP_SCORE_DATA[pos])

                    # Sort controls
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        sort_col_opp = st.selectbox(
                            "SORT BY",
                            ["AVG OPP", "AVG (L4)", "TOTAL OPP", "OPP FPTS", "RK"],
                            key=f"opp_sort_{pos}"
                        )
                    with c2:
                        asc_opp = st.selectbox("ORDER", ["↓ High→Low", "↑ Low→High"], key=f"opp_asc_{pos}")

                    sort_asc_opp = (asc_opp == "↑ Low→High")
                    df_sorted = df_opp.copy()
                    if sort_col_opp in df_sorted.columns:
                        df_sorted = df_sorted.sort_values(
                            sort_col_opp, ascending=sort_asc_opp,
                            key=lambda x: pd.to_numeric(x, errors="coerce")
                        ).reset_index(drop=True)

                    # Apply color gradient to numeric summary columns (no matplotlib needed)
                    grad_cols = ["AVG (L4)", "AVG OPP", "TOTAL OPP", "OPP FPTS"]

                    def color_opp(val, col_min, col_max):
                        try:
                            v = float(val)
                            ratio = (v - col_min) / (col_max - col_min) if col_max != col_min else 0.5
                            ratio = max(0, min(1, ratio))
                            r = int(255 * (1 - ratio))
                            g = int(200 * ratio)
                            return f"color: rgb({r},{g},80);"
                        except:
                            return ""

                    styled = df_sorted.style.format({c: "{:.2f}" for c in grad_cols})
                    for col in grad_cols:
                        col_min = pd.to_numeric(df_sorted[col], errors="coerce").min()
                        col_max = pd.to_numeric(df_sorted[col], errors="coerce").max()
                        styled = styled.map(lambda v, mn=col_min, mx=col_max: color_opp(v, mn, mx), subset=[col])

                    st.dataframe(styled, use_container_width=True, height=620, hide_index=True)
                    st.caption(
                        f"// Top 50 {pos}s · AVG OPP = season avg opp score · AVG (L4) = last 4 games avg · "
                        f"OPP FPTS = actual PPR pts · BYE = bye week · SUS = suspended · — = did not play"
                    )
        else:
            st.info("Opportunity Score data is only available for the **2025** season. Switch the season selector above to view.")

    # ── PLAYER PROFILE TAB ────────────────────────────────────────────────────
    with tabs[7]:
        st.markdown(f'<div class="section-label">// PLAYER PROFILE · {season} SEASON</div>', unsafe_allow_html=True)

        player_info = load_player_info()
        gamelogs    = load_gamelogs(season)

        all_players = []
        for pos in ["QB","RB","WR","TE"]:
            df_pos = data[pos]
            if not df_pos.empty and "player_display_name" in df_pos.columns:
                all_players.extend(df_pos["player_display_name"].tolist())
        all_players = sorted(set(all_players))

        selected = st.selectbox("SELECT PLAYER", ["— choose a player —"] + all_players, key="profile_player")

        if selected and selected != "— choose a player —":
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
                age = "N/A"
                headshot = None
                if not player_info.empty:
                    info_match = player_info[player_info["player_display_name"] == selected]
                    if not info_match.empty:
                        age_val = info_match.iloc[0].get("age")
                        age = int(age_val) if pd.notna(age_val) else "N/A"
                        headshot = info_match.iloc[0].get("headshot_url")

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
                st.markdown('<div class="section-label">// GAME LOG</div>', unsafe_allow_html=True)

                if not gamelogs.empty:
                    player_log = gamelogs[gamelogs["player_display_name"] == selected].copy()
                    if not player_log.empty:
                        player_log = player_log.sort_values("week").reset_index(drop=True)

                        avg_ppr = fppg
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

                        def color_result(val):
                            if val == "BOOM": return "background-color: #0a2e0a; color: #00cc44; font-weight: bold;"
                            if val == "BUST": return "background-color: #2e0a0a; color: #ff3333; font-weight: bold;"
                            return "color: #c8d6e0;"

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
