"""
app.py — FantasyEdge · Dash Edition · Render Deployment
Run locally:  py -3.12 app.py  →  http://localhost:8050
Deploy:       gunicorn app:server --bind 0.0.0.0:$PORT
"""

from dash import Dash, html, dcc, Input, Output, State, no_update, ctx
import dash_ag_grid as dag
import pandas as pd
import os
import re

# ── INIT ──────────────────────────────────────────────────────────────────────
app    = Dash(__name__, suppress_callback_exceptions=True, title="FantasyEdge")
server = app.server   # exposed for gunicorn

DATA_DIR = "data"

# ── PALETTE ───────────────────────────────────────────────────────────────────
BG      = "#080c10"
SURF    = "#0d1117"
SURF2   = "#111820"
BORDER  = "#1a2030"
ACCENT  = "#ff007f"
ADIM    = "#7a2a5a"
TEXT    = "#c8d6e0"
TDIM    = "#8a9ab0"
GREEN   = "#00cc44"
RED     = "#ff3333"
POS_C   = {"QB":"#4fc3f7","RB":"#81c784","WR":"#ff8a65","TE":"#ce93d8","K":"#fff176","DST":"#90a4ae"}

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
app.index_string = """<!DOCTYPE html>
<html>
<head>
  {%metas%}<title>{%title%}</title>{%favicon%}{%css%}
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    html,body{background:#080c10;color:#c8d6e0;font-family:'Inter',sans-serif;font-size:13px}
    ::-webkit-scrollbar{width:5px;height:5px}
    ::-webkit-scrollbar-track{background:#080c10}
    ::-webkit-scrollbar-thumb{background:#1a2030;border-radius:3px}
    ::-webkit-scrollbar-thumb:hover{background:#ff007f55}

    .ag-theme-alpine-dark{
      --ag-background-color:#0d1117;
      --ag-foreground-color:#c8d6e0;
      --ag-header-background-color:#080c10;
      --ag-header-foreground-color:#7a2a5a;
      --ag-odd-row-background-color:#0d1117;
      --ag-row-hover-color:#111820;
      --ag-selected-row-background-color:#1a0a14;
      --ag-border-color:#1a2030;
      --ag-row-border-color:#1a2030;
      --ag-font-size:12px;
      --ag-font-family:'Inter',sans-serif;
      --ag-row-height:30px;
      --ag-header-height:34px;
      --ag-cell-horizontal-padding:8px;
    }
    .ag-theme-alpine-dark .ag-header-cell-label{font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:.06em}
    .ag-theme-alpine-dark .ag-root-wrapper{border:1px solid #1a2030!important}
    .ag-theme-alpine-dark .ag-cell{font-variant-numeric:tabular-nums}

    .tab-lbl{font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:.1em;
      color:#7a2a5a;padding:10px 16px;border:none;border-bottom:2px solid transparent;
      background:#080c10;cursor:pointer;white-space:nowrap}
    .tab-lbl.sel{color:#ff007f;border-bottom:2px solid #ff007f}

    .sec-label{font-family:'Share Tech Mono',monospace;font-size:9px;color:#7a2a5a;
      letter-spacing:.2em;text-transform:uppercase;border-bottom:1px solid #1a2030;
      padding-bottom:6px;margin-bottom:12px}
    .stat-card{background:#0d1117;border:1px solid #1a2030;border-left:3px solid #ff007f;
      padding:12px 16px;flex:1}
    .card-val{font-family:'Share Tech Mono',monospace;font-size:1.6rem;color:#ff007f;line-height:1}
    .card-lbl{font-size:9px;color:#7a2a5a;letter-spacing:.15em;text-transform:uppercase;margin-top:4px}
    .badge{display:inline-block;background:#1f0a14;border:1px solid #ff007f;color:#ff007f;
      font-family:'Share Tech Mono',monospace;font-size:9px;padding:2px 8px;letter-spacing:.15em}
    .pill{display:inline-block;padding:2px 7px;font-size:10px;font-weight:600;
      font-family:'Share Tech Mono',monospace;border-radius:2px}
    .ctrl-in{background:#0d1117;border:1px solid #1a2030;color:#c8d6e0;
      font-family:'Share Tech Mono',monospace;font-size:11px;padding:5px 9px;outline:none;width:100%}
    .ctrl-in:focus{border-color:#ff007f}
    .ctrl-lbl{font-family:'Share Tech Mono',monospace;font-size:9px;color:#7a2a5a;
      letter-spacing:.2em;text-transform:uppercase;margin-bottom:4px}
    .toggle-btn{background:#0d1117;border:1px solid #1a2030;color:#7a2a5a;
      font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:.1em;
      padding:5px 14px;cursor:pointer;margin-right:4px}
    .toggle-btn:hover,.toggle-btn.active{border-color:#ff007f;color:#ff007f;background:#1f0a14}
    .draft-g{padding:6px 10px;margin:3px 0;background:#0a1f0a;border-left:3px solid #00cc44;font-size:12px}
    .draft-r{padding:6px 10px;margin:3px 0;background:#1f0a0a;border-left:3px solid #ff3333;font-size:12px}
    .draft-p{padding:6px 10px;margin:3px 0;background:#0d1a2e;border-left:3px solid #ff007f;font-size:12px}
    .coach-card{background:#0a1020;border:1px solid #1e2d45;border-radius:4px;padding:16px;margin-bottom:14px}
    .coach-card.pos{border-top:3px solid #00cc44}
    .coach-card.neg{border-top:3px solid #ff3333}
    .coach-card.neu{border-top:3px solid #7a2a5a}
  </style>
</head>
<body>
  {%app_entry%}
  <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>"""

# ── COL LABELS ────────────────────────────────────────────────────────────────
COL_LABELS = {
    "player_display_name":"Player","recent_team":"Team","games":"GP",
    "fppg_ppr":"FPPG (PPR)","fantasy_points_ppr":"Total PPR",
    "passing_yards":"Pass Yds","passing_tds":"Pass TD","interceptions":"INT",
    "comp_pct":"Comp%","yards_per_attempt":"Y/A","sacks":"Sacks",
    "carries":"Car","rushing_yards":"Rush Yds","rushing_tds":"Rush TD","ypc":"YPC",
    "targets":"Tgt","receptions":"Rec","receiving_yards":"Rec Yds","receiving_tds":"Rec TD",
    "target_share":"Tgt Share","wopr":"WOPR","adot":"aDOT","catch_rate":"Catch%",
    "avg_snap_pct":"Snap%","team":"Team","pass_rate":"Pass Rate","run_rate":"Run Rate",
    "total_plays":"Plays","avg_pts_allowed":"Avg Pts Allowed","sos_rank":"SOS Rank",
    "position":"Pos","consensus_rank":"Consensus Rank","fc_rank":"FantasyCalc",
    "fc_pos_rank":"FC Pos Rank","ffc_rank":"FFC Rank","fp_rank":"FantasyPros",
    "fp_pos_rank":"FP Pos Rank","espn_rank":"ESPN","rb_overall_rank":"RotoBaller",
    "yahoo_rank":"Yahoo","yahoo_pos_rank":"Yahoo Pos","2025_fppg_ppr":"2025 FPPG (PPR)",
    "ybc_att":"YBC/ATT","yac_att":"YAC/ATT","yprr":"YPRR",
    "rz_car_20":"RZ Car (20)","rz_car_10":"RZ Car (10)","rz_car_5":"RZ Car (5)",
    "rz_tgt_20":"RZ Tgt (20)","rz_tgt_10":"RZ Tgt (10)","rz_tgt_5":"RZ Tgt (5)",
    # team analytics
    "total_yds_game":"Total Yds/G","pass_yds_game":"Pass Yds/G","rush_yds_game":"Rush Yds/G",
    "pts_game":"Pts/G","pts_allowed_game":"Pts Allowed/G","yds_per_play":"YPP",
    "rz_attempts":"RZ Att","rz_conv_pct":"RZ Conv%","third_down_pct":"3rd Down%",
    "sacks_allowed":"Sacks Allowed",
}
PCT_COLS = {"target_share","catch_rate","comp_pct","avg_snap_pct","pass_rate","run_rate"}

# ── OPP SCORE DATA ─────────────────────────────────────────────────────────────
_B = None
OPP_SCORE_DATA = {
"RB":[
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
"WR":[
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
"TE":[
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

# ── COACHING CHANGES 2026 ─────────────────────────────────────────────────────
COACHING_CHANGES = [
    {"team":"ATL","full":"Atlanta Falcons","out":"Raheem Morris","new_hc":"Kevin Stefanski",
     "prev":"Cleveland Browns HC","style":"Run-heavy · play-action · 12 personnel",
     "impact":"POSITIVE","note":"Stefanski's run-first scheme is a massive upgrade for Bijan Robinson. Strong play-action boosts TE/WR targets across the board.",
     "up":["Bijan Robinson","Kyle Pitts Sr.","Drake London"],"down":[]},
    {"team":"ARI","full":"Arizona Cardinals","out":"Jonathan Gannon","new_hc":"Mike LaFleur",
     "prev":"LA Rams Offensive Coordinator","style":"Spread passing · motion-heavy",
     "impact":"NEUTRAL","note":"LaFleur brings a modern pass-heavy scheme but QB situation is murky post-Murray. Trey McBride and Marvin Harrison Jr. could see elevated targets.",
     "up":["Trey McBride","Marvin Harrison Jr."],"down":["Kyler Murray"]},
    {"team":"BAL","full":"Baltimore Ravens","out":"John Harbaugh (18 seasons)","new_hc":"Jesse Minter",
     "prev":"Michigan Wolverines DC","style":"TBD — defensive background",
     "impact":"NEGATIVE","note":"Harbaugh's departure creates major offensive uncertainty. Lamar Jackson's scheme and targets for Henry/Flowers are all up in the air.",
     "up":[],"down":["Lamar Jackson","Derrick Henry","Zay Flowers"]},
    {"team":"BUF","full":"Buffalo Bills","out":"Sean McDermott","new_hc":"Joe Brady",
     "prev":"Bills OC (promoted)","style":"Run-lean · controlled pace · play-action",
     "impact":"POSITIVE","note":"Brady retains play-calling duties and keeps offensive continuity. Josh Allen and James Cook III are the safest beneficiaries.",
     "up":["Josh Allen","James Cook III","DJ Moore"],"down":[]},
    {"team":"CLE","full":"Cleveland Browns","out":"Kevin Stefanski","new_hc":"Todd Monken",
     "prev":"Georgia HC / Former OC","style":"Pass-first · spread · vertical shots",
     "impact":"POSITIVE","note":"Monken's pass-heavy system could unlock Quinshon Judkins as a receiving threat and boost Harold Fannin Jr.'s target share.",
     "up":["Quinshon Judkins","Harold Fannin Jr.","Jerry Jeudy"],"down":[]},
    {"team":"LV","full":"Las Vegas Raiders","out":"Multiple (Kelly / McMahon)","new_hc":"Klint Kubiak",
     "prev":"Seattle Seahawks OC","style":"Pass-heavy · West Coast · TE-friendly",
     "impact":"POSITIVE","note":"Kubiak's pass-friendly scheme from Seattle elevates Brock Bowers significantly. Ashton Jeanty's receiving role could expand.",
     "up":["Brock Bowers","Ashton Jeanty","Tre Tucker"],"down":[]},
    {"team":"MIA","full":"Miami Dolphins","out":"Mike McDaniel","new_hc":"Jeff Hafley",
     "prev":"Green Bay Packers DC","style":"Defensive-minded · OC TBD",
     "impact":"NEGATIVE","note":"McDaniel's elite WR-friendly scheme is gone. De'Von Achane and Jaylen Waddle both face real uncertainty until a new OC is named.",
     "up":[],"down":["De'Von Achane","Jaylen Waddle","Tyreek Hill"]},
    {"team":"NYG","full":"New York Giants","out":"Brian Daboll","new_hc":"John Harbaugh",
     "prev":"Baltimore Ravens HC (18 seasons)","style":"Run-heavy · physical · 12 personnel",
     "impact":"POSITIVE","note":"Harbaugh's run-first identity is a major boost for Cam Skattebo. Malik Nabers' target share depends on the new OC hire.",
     "up":["Cam Skattebo","Wan'Dale Robinson"],"down":[]},
    {"team":"PIT","full":"Pittsburgh Steelers","out":"Mike Tomlin","new_hc":"Mike McCarthy",
     "prev":"Dallas Cowboys HC","style":"Pass-first · vertical attack · RPO",
     "impact":"POSITIVE","note":"McCarthy's pass-first system unlocks DK Metcalf and gives Jaylen Warren more receiving opportunities in the passing game.",
     "up":["DK Metcalf","Jaylen Warren","Kenneth Gainwell"],"down":[]},
    {"team":"TEN","full":"Tennessee Titans","out":"Brian Callahan","new_hc":"Robert Saleh",
     "prev":"New York Jets HC","style":"Defensive-minded · run-heavy tendencies",
     "impact":"NEUTRAL","note":"Saleh's defensive background leaves Cam Ward's passing game uncertain. Tony Pollard and Tyjae Spears could see run-heavy usage.",
     "up":["Tony Pollard","Tyjae Spears"],"down":["Cam Ward","Carnell Tate"]},
]

# ── DRAFT NOTES DATA ──────────────────────────────────────────────────────────
MUST_DRAFT = {
    "Early Round (1-3)":  ["Omarion Hampton","Ashton Jeanty","Malik Nabers","Chase Brown","James Cook III","Brock Bowers","DeVonta Smith"],
    "Mid Round (4-7)":    ["Ladd McConkey","TreVeyon Henderson","Cam Skattebo","Christian Watson","Emeka Egbuka","Justin Herbert","Harold Fannin Jr.","Bhayshul Tuten","DJ Moore"],
    "Late Round (8+)":    ["Tucker Kraft","Josh Downs","Matthew Golden","Jadarian Price","Kyle Monangai","George Kittle"],
}
MUST_AVOID = {
    "Early Round (1-3)":  ["Trey McBride","De'Von Achane","Christian McCaffrey","Jeremiyah Love","George Pickens"],
    "Mid Round (4-7)":    ["Davante Adams","Tyler Warren","Bucky Irving"],
    "Late Round (8+)":    ["Dallas Goedert","Khalil Shakir","Jacory Croskey-Merritt","Calvin Ridley"],
}
TARGET_PICKS = {
    "Round 1":  ["Bijan Robinson","Jahmyr Gibbs","Puka Nacua","James Cook III"],
    "Round 2":  ["Omarion Hampton","Malik Nabers","Chase Brown","Brock Bowers"],
    "Round 3":  ["Javonte Williams","Tetairoa McMillan","DeVonta Smith"],
    "Round 4":  ["Cam Skattebo","Ladd McConkey","Terry McLaurin","Emeka Egbuka"],
    "Round 5":  ["Rome Odunze","DJ Moore","Bhayshul Tuten","Quinshon Judkins","Mike Evans"],
    "Round 6":  ["Parker Washington","Christian Watson","Jalen Hurts","Carnell Tate"],
    "Round 7":  ["Justin Herbert","Harold Fannin Jr.","Dak Prescott","Tucker Kraft"],
    "Round 8":  ["Tucker Kraft","Sam LaPorta","Michael Wilson"],
    "Round 9":  ["J.K. Dobbins","Michael Pittman Jr.","Kenneth Gainwell","Josh Downs"],
    "Round 10": ["Matthew Golden","George Kittle"],
    "Round 11": ["KC Concepcion","Aaron Jones Sr.","Isaiah Likely"],
}
UNDERVALUED = [
    {"name":"Javonte Williams","pos":"RB","proj_rank":"RB18","adp":"4.01","team":"DAL",
     "bullets":["7th easiest SOS for 2026","Improved offense & defense · no backfield competition"],
     "stats_hdr":"2025 RANKINGS","stats":[("4th","Opp Score"),("7th","Rush TD"),("5th","GL Carries"),("1st","GL Targets"),("10th","Carries"),("7th","Snap%")],"extra_hdr":None,"extra_stats":[]},
    {"name":"Omarion Hampton","pos":"RB","proj_rank":"RB9","adp":"2.03","team":"LAC",
     "bullets":["McDaniel's produced a top-3 fantasy RB each of the last 3 years","Improved O-line · prime scheme","Averaged 20+ pts/game before injury"],
     "stats_hdr":None,"stats":[],"extra_hdr":None,"extra_stats":[]},
    {"name":"Rome Odunze","pos":"WR","proj_rank":"WR27","adp":"5.09","team":"CHI",
     "bullets":["Injured mid-season — depressed ADP","WR7 in expected PPG · 9th in Snap%"],
     "stats_hdr":"WEEKS 1–4","stats":[("19.9","Fantasy PPG"),("8.8","Tgt/Game")],"extra_hdr":None,"extra_stats":[]},
    {"name":"Parker Washington","pos":"WR","proj_rank":"WR35","adp":"7.03","team":"JAC",
     "bullets":["OTA WR1 · Chris Godwin slot role","Jags' leader in receptions & targets","12th best YPRR at 2.57 yards"],
     "stats_hdr":"WEEKS 9+","stats":[("17.4","Fantasy PPG"),("WR6","Pace"),("13th","Overall Skills")],"extra_hdr":None,"extra_stats":[]},
    {"name":"Emeka Egbuka","pos":"WR","proj_rank":"WR20","adp":"4.06","team":"TB",
     "bullets":["Lowest catchable target % — massive upside"],
     "stats_hdr":"2025 RANKINGS","stats":[("9th","Targets"),("15th","YAC"),("2nd","Deep Targets")],
     "extra_hdr":"WEEKS 1–5 (W/O EVANS)","extra_stats":[("17.6","Fantasy PPG"),("WR3","Pace")]},
    {"name":"Cam Skattebo","pos":"RB","proj_rank":"RB20","adp":"4.09","team":"NYG",
     "bullets":["John Harbaugh's run-first scheme — massive upgrade","No backfield competition"],
     "stats_hdr":"8 GAMES IN 2025","stats":[("12.6","Car/Game"),("16","Fantasy PPG"),("6","TDs"),("9th","By RBs")],"extra_hdr":None,"extra_stats":[]},
]

# ── DATA LOADING ──────────────────────────────────────────────────────────────
def load_year(year):
    d = os.path.join(DATA_DIR, str(year))
    files = {"QB":"qb_stats.csv","RB":"rb_stats.csv","WR":"wr_stats.csv",
             "TE":"te_stats.csv","SOS":"sos_by_team.csv","SPLITS":"team_splits.csv",
             "ANALYTICS":"team_analytics.csv"}
    idx = {"QB":0,"RB":0,"WR":0,"TE":0,"SOS":None,"SPLITS":None,"ANALYTICS":None}
    out = {}
    for k, f in files.items():
        p = os.path.join(d, f)
        out[k] = pd.read_csv(p, index_col=idx[k]) if os.path.exists(p) else pd.DataFrame()
    return out

def load_2026():
    b = os.path.join(DATA_DIR, "2026")
    def r(f, i=None): p=os.path.join(b,f); return pd.read_csv(p,index_col=i) if os.path.exists(p) else pd.DataFrame()
    return r("master_rankings.csv",0), r("sos_2026.csv"), r("mock_board.csv")

def load_player_info():
    p = os.path.join(DATA_DIR,"player_info.csv")
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

def load_gamelogs(year):
    p = os.path.join(DATA_DIR,f"gamelogs_{year}.csv")
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

# Load at startup
master, sos_2026, mock_board = load_2026()
data_2025 = load_year(2025)
data_2024 = load_year(2024)
player_info = load_player_info()

def get_data(season): return data_2025 if int(season)==2025 else data_2024

# ── AG GRID HELPERS ───────────────────────────────────────────────────────────
DGRID = {"suppressMovableColumns":True,"suppressCellFocus":True,"animateRows":False}
DCOL  = {"sortable":True,"resizable":True,"filter":False,"suppressMenu":True,
          "cellStyle":{"color":TEXT,"fontSize":"12px"}}

def make_grid(gid, records, col_defs, height=580):
    return dag.AgGrid(id=gid, rowData=records, columnDefs=col_defs,
                      defaultColDef=DCOL, dashGridOptions=DGRID,
                      className="ag-theme-alpine-dark",
                      style={"height":f"{height}px","width":"100%"})

def heat_style(col, lo=0, hi=30):
    return {"function":f"""(function(p){{
        var v=parseFloat(p.value); if(isNaN(v)) return {{}};
        var all=p.api.getRenderedNodes().map(n=>parseFloat(n.data['{col}'])).filter(x=>!isNaN(x));
        var mn=Math.min(...all)||{lo}, mx=Math.max(...all)||{hi};
        var r=(v-mn)/(mx-mn||1); r=Math.max(0,Math.min(1,r));
        var red=Math.round(220*(1-r)), grn=Math.round(170*r);
        return {{color:'rgb('+red+','+grn+',60)',fontWeight:'600'}};
    }})(params)"""}

def pos_style_js():
    c = {k:v for k,v in POS_C.items()}
    return {"function":f"""(function(p){{
        var c={{"QB":"{c['QB']}","RB":"{c['RB']}","WR":"{c['WR']}","TE":"{c['TE']}","DST":"{c.get('DST','#90a4ae')}","K":"{c.get('K','#fff176')}"}};
        return {{color:c[p.value]||"{TEXT}",fontWeight:"600"}};
    }})(params)"""}

def df_to_records(df):
    df = df.copy().rename(columns=COL_LABELS)
    for c in df.columns:
        orig = [k for k,v in COL_LABELS.items() if v==c]
        if orig and orig[0] in PCT_COLS:
            df[c] = df[c].apply(lambda x: f"{float(x):.1%}" if pd.notna(x) and str(x) not in ["—",""] else "—")
    return df.fillna("—").to_dict("records")

def col_defs_from_df(df, heat=None, pin_player=True):
    heat = heat or []
    defs = []
    for c in df.columns:
        d = {"field":c,"headerName":c,"sortable":True,"resizable":True,"minWidth":70}
        if pin_player and c in ["Player","player"]:
            d.update({"pinned":"left","minWidth":180,"cellStyle":{"fontWeight":"600","color":TEXT}})
        elif c in heat:
            d["cellStyle"] = heat_style(c)
        defs.append(d)
    return defs

def build_opp_df(pos):
    rows=[]
    for d in OPP_SCORE_DATA[pos]:
        row={"RK":d["rank"],"Player":d["player"]}
        for w in range(1,15):
            v=d.get(f"w{w}")
            if v is None: row[f"W{w}"]="BYE"
            elif v=="S":  row[f"W{w}"]="SUS"
            elif v==0:    row[f"W{w}"]="—"
            else:         row[f"W{w}"]=f"{v:.2f}"
        row["AVG (L4)"]=d["avg_l4"]; row["AVG OPP"]=d["avg"]
        row["TOTAL OPP"]=d["total"]; row["OPP FPTS"]=d["opp_fpts"]
        rows.append(row)
    return pd.DataFrame(rows)

def opp_col_defs():
    defs=[
        {"field":"RK","headerName":"RK","width":52,"pinned":"left","sortable":True},
        {"field":"Player","headerName":"Player","width":210,"pinned":"left",
         "cellStyle":{"fontWeight":"600","color":TEXT},"sortable":True},
    ]
    for w in range(1,15):
        defs.append({"field":f"W{w}","headerName":f"W{w}","width":66,"sortable":False,
                     "cellStyle":{"function":f"""(function(p){{
                         if(p.value==='BYE') return {{color:'#4fc3f7',fontStyle:'italic',opacity:.7}};
                         if(p.value==='SUS') return {{color:'#ff3333',fontStyle:'italic'}};
                         if(p.value==='—')   return {{color:'#2a3545'}};
                         var v=parseFloat(p.value); if(isNaN(v)) return {{}};
                         var r=Math.max(0,Math.min(1,v/30));
                         var red=Math.round(200*(1-r)),grn=Math.round(160*r);
                         return {{color:'rgb('+red+','+grn+',60)'}};
                     }})(params)"""}})
    for col in ["AVG (L4)","AVG OPP","TOTAL OPP","OPP FPTS"]:
        defs.append({"field":col,"headerName":col,"width":94,"sortable":True,"type":"numericColumn",
                     "valueFormatter":{"function":"params.value.toFixed(2)"},
                     "cellStyle":heat_style(col)})
    return defs

# ── UI HELPERS ────────────────────────────────────────────────────────────────
def sec(txt, mt=16):
    return html.Div(txt, className="sec-label", style={"marginTop":f"{mt}px","marginBottom":"12px"})

def stat_card(val, lbl):
    return html.Div([html.Div(str(val),className="card-val"),html.Div(lbl,className="card-lbl")],
                    className="stat-card")

def tab_style(sel=False):
    base = {"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","letterSpacing":".1em",
            "color": ACCENT if sel else ADIM, "padding":"10px 16px","border":"none",
            "borderBottom":f"2px solid {ACCENT}" if sel else "2px solid transparent",
            "background":BG,"cursor":"pointer","whiteSpace":"nowrap"}
    return base

def ctrl(label, child):
    return html.Div([html.Div(label,className="ctrl-lbl"),child])

def empty_msg(msg="No data — run the pipeline scripts first."):
    return html.Div(msg,style={"color":TDIM,"fontFamily":"Share Tech Mono, monospace",
                               "fontSize":"11px","padding":"32px","textAlign":"center"})

# ── LAYOUT ────────────────────────────────────────────────────────────────────
_ts = lambda: tab_style(False)
_tsa = lambda: tab_style(True)

app.layout = html.Div([
    # Header
    html.Div([
        html.Div("FANTASY_EDGE",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"2.2rem",
                 "color":ACCENT,"letterSpacing":".15em","textShadow":f"0 0 24px {ACCENT}44"}),
        html.Div("// NFL PLAYER ANALYTICS & RANKINGS",style={"fontFamily":"Share Tech Mono, monospace",
                 "fontSize":"9px","color":ADIM,"letterSpacing":".2em","marginTop":"4px"}),
    ], style={"padding":"18px 24px 12px","borderBottom":f"1px solid {BORDER}"}),

    html.Div([
        # Season selector
        dcc.RadioItems(id="season",
            options=[{"label":"2026 RANKINGS","value":"2026"},
                     {"label":"2025","value":"2025"},
                     {"label":"2024","value":"2024"}],
            value="2026", inline=True,
            inputStyle={"marginRight":"4px"},
            labelStyle={"display":"inline-flex","alignItems":"center","gap":"4px","marginRight":"12px",
                        "fontFamily":"Share Tech Mono, monospace","fontSize":"11px","color":ADIM,"cursor":"pointer"},
            style={"marginBottom":"8px"}),

        html.Div(id="badge", style={"marginBottom":"14px"}),
        html.Div(id="stat-cards", style={"display":"flex","gap":"10px","marginBottom":"14px"}),

        # 2026 view
        html.Div(id="v2026", children=[
            dcc.Tabs(id="t2026", value="overall", children=[
                dcc.Tab(label="OVERALL",        value="overall",  style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="QB",             value="qb26",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="RB",             value="rb26",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="WR",             value="wr26",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TE",             value="te26",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="SOS 2026",       value="sos26",    style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="MOCK BOARD",     value="mock",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="DRAFT NOTES",    value="draft",    style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="COACHING",       value="coaching", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="SOURCE COMPARE", value="srccomp",  style=_ts(), selected_style=_tsa()),
            ], colors={"border":BORDER,"primary":ACCENT,"background":BG},
               style={"borderBottom":f"1px solid {BORDER}"}),
            html.Div(id="c2026", style={"paddingTop":"14px"}),
        ]),

        # Historical view
        html.Div(id="vhist", style={"display":"none"}, children=[
            dcc.Tabs(id="thist", value="qb-h", children=[
                dcc.Tab(label="QB",             value="qb-h",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="RB",             value="rb-h",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="WR",             value="wr-h",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TE",             value="te-h",     style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TEAM SPLITS",    value="splits",   style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TEAM ANALYTICS", value="analytics",style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="SOS",            value="sos-h",    style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="OPP SCORE",      value="opp",      style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="PLAYER PROFILE", value="profile",  style=_ts(), selected_style=_tsa()),
            ], colors={"border":BORDER,"primary":ACCENT,"background":BG},
               style={"borderBottom":f"1px solid {BORDER}"}),
            html.Div(id="chist", style={"paddingTop":"14px"}),
        ]),

    ], style={"padding":"12px 24px"}),
], style={"minHeight":"100vh","background":BG})

# ── SEASON TOGGLE ─────────────────────────────────────────────────────────────
@app.callback(
    Output("v2026","style"), Output("vhist","style"),
    Output("badge","children"), Output("stat-cards","children"),
    Input("season","value"),
)
def toggle_season(s):
    if s == "2026":
        badge = html.Span("SZN_2026 · PREDICTIVE RANKINGS", className="badge")
        return {"display":"block"}, {"display":"none"}, badge, []
    badge = html.Span(f"SZN_{s} · REGULAR SEASON", className="badge")
    data = get_data(s)
    cards = [stat_card(len(data[p]) if not data[p].empty else 0, lbl)
             for p,lbl in [("QB","QBs"),("RB","RBs"),("WR","WRs"),("TE","TEs")]]
    return {"display":"none"}, {"display":"block"}, badge, cards

# ── 2026 TABS ─────────────────────────────────────────────────────────────────
@app.callback(Output("c2026","children"), Input("t2026","value"))
def render_2026(tab):

    # Rankings tabs
    if tab in ["overall","qb26","rb26","wr26","te26"]:
        if master.empty: return empty_msg("Run fetch_rankings.py first.")
        pos_map = {"qb26":"QB","rb26":"RB","wr26":"WR","te26":"TE"}
        df = master.copy()
        if tab in pos_map and "position" in df.columns:
            df = df[df["position"] == pos_map[tab]]
        label = {"overall":"ALL POSITIONS"}.get(tab, pos_map.get(tab,""))
        records = df.rename(columns=COL_LABELS).fillna("—").to_dict("records")
        cols = [{"field":c,"headerName":c,"sortable":True,"resizable":True,"minWidth":70,
                 **({"pinned":"left","minWidth":180,"cellStyle":{"fontWeight":"600","color":TEXT}} if c in ["Player","player"] else {})}
                for c in list(df.rename(columns=COL_LABELS).columns)]
        return html.Div([
            sec(f"// 2026 CONSENSUS RANKINGS · PPR · {label}", mt=0),
            make_grid(f"g-{tab}", records, cols, 620),
            html.Div(f"// {len(df)} players · click column header to sort",
                     style={"fontSize":"10px","color":ADIM,"marginTop":"8px",
                            "fontFamily":"Share Tech Mono, monospace"}),
        ])

    if tab == "sos26":
        if sos_2026.empty: return empty_msg("Run fetch_sos_2026.py first.")
        return html.Div([
            sec("// 2026 STRENGTH OF SCHEDULE", mt=0),
            ctrl("POSITION", dcc.Dropdown(id="sos26-pos",
                options=[{"label":p,"value":p} for p in ["RB","WR","QB","TE"]], value="RB",
                clearable=False, style={"width":"120px","background":SURF,"color":TEXT,
                    "border":f"1px solid {BORDER}","borderRadius":"0","fontSize":"11px"})),
            html.Div(id="sos26-c", style={"marginTop":"12px"}),
        ])

    if tab == "mock":
        if mock_board.empty: return empty_msg("Run create_mock_board.py first.")
        mb = mock_board.copy()
        mb["Pick"] = mb.apply(lambda r: f"{int(r['round'])}.{int(r['pick_in_round']):02d}", axis=1)
        return html.Div([
            sec("// MOCK DRAFT BOARD · FANTASYPROS PPR ADP 2026 · 12-TEAM", mt=0),
            html.Div([
                ctrl("SEARCH", dcc.Input(id="mock-s",placeholder="Search...",debounce=True,
                    className="ctrl-in",style={"width":"200px"})),
                ctrl("POSITION", dcc.Dropdown(id="mock-pos",
                    options=[{"label":p,"value":p} for p in ["ALL","QB","RB","WR","TE","K","DST"]],
                    value="ALL",clearable=False,
                    style={"width":"120px","background":SURF,"color":TEXT,
                           "border":f"1px solid {BORDER}","borderRadius":"0","fontSize":"11px"})),
            ], style={"display":"flex","gap":"12px","alignItems":"flex-end","marginBottom":"12px"}),
            html.Div(id="mock-grid"),
        ])

    if tab == "draft":
        return html.Div([
            sec("// DRAFT NOTES · 2026", mt=0),
            html.Div([
                html.Button("Must Drafts & Must Avoids",id="btn-must",n_clicks=0,className="toggle-btn active"),
                html.Button("Target Picks",id="btn-target",n_clicks=0,className="toggle-btn"),
                html.Button("Undervalued Players",id="btn-uv",n_clicks=0,className="toggle-btn"),
            ], style={"marginBottom":"16px"}),
            html.Div(id="draft-c", children=_render_must()),
        ])

    if tab == "coaching":
        return _render_coaching()

    if tab == "srccomp":
        if master.empty: return empty_msg()
        return html.Div([
            sec("// SOURCE COMPARISON · EXPERT CONSENSUS ANALYSIS", mt=0),
            ctrl("POSITION", dcc.Dropdown(id="src-pos",
                options=[{"label":p,"value":p} for p in ["ALL","QB","RB","WR","TE"]],
                value="ALL",clearable=False,
                style={"width":"120px","background":SURF,"color":TEXT,
                       "border":f"1px solid {BORDER}","borderRadius":"0","fontSize":"11px"})),
            html.Div(id="src-c",style={"marginTop":"12px"}),
        ])

    return html.Div()

# ── HISTORICAL TABS ───────────────────────────────────────────────────────────
@app.callback(Output("chist","children"), Input("thist","value"), Input("season","value"))
def render_hist(tab, season_str):
    if season_str == "2026": return html.Div()
    data = get_data(season_str)

    pos_map = {"qb-h":"QB","rb-h":"RB","wr-h":"WR","te-h":"TE"}
    if tab in pos_map:
        pos = pos_map[tab]
        df = data[pos]
        if df.empty: return empty_msg()
        heat_cols = {"FPPG (PPR)","Total PPR","Rush Yds","Rec Yds","Pass Yds","Tgt","Car","YPRR","YBC/ATT","YAC/ATT"}
        rn = df.rename(columns=COL_LABELS)
        records = rn.fillna("—").to_dict("records")
        defs = []
        for c in rn.columns:
            d={"field":c,"headerName":c,"sortable":True,"resizable":True,"minWidth":70}
            if c=="Player": d.update({"pinned":"left","minWidth":180,"cellStyle":{"fontWeight":"600","color":TEXT}})
            if c in heat_cols: d["cellStyle"]=heat_style(c)
            defs.append(d)
        label={"QB":"QUARTERBACK","RB":"RUNNING BACK","WR":"WIDE RECEIVER","TE":"TIGHT END"}[pos]
        return html.Div([
            sec(f"// {label} RANKINGS · {season_str}", mt=0),
            make_grid(f"g-{tab}", records, defs, 620),
            html.Div(f"// {len(df)} players · click column header to sort",
                     style={"fontSize":"10px","color":ADIM,"marginTop":"8px","fontFamily":"Share Tech Mono, monospace"}),
        ])

    if tab == "splits":
        df = data["SPLITS"]
        if df.empty: return empty_msg()
        rn = df.rename(columns=COL_LABELS).fillna("—")
        defs = [{"field":c,"headerName":c,"sortable":True,"resizable":True} for c in rn.columns]
        return html.Div([
            sec(f"// TEAM PASS / RUN RATE · {season_str}", mt=0),
            html.Div([
                html.Div([html.Div("MOST PASS-HEAVY",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","color":ADIM,"marginBottom":"8px"}),
                          make_grid("spl-p", rn.sort_values("Pass Rate" if "Pass Rate" in rn.columns else rn.columns[0], ascending=False).head(10).to_dict("records"), defs, 320)], style={"flex":"1"}),
                html.Div([html.Div("MOST RUN-HEAVY",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","color":ADIM,"marginBottom":"8px"}),
                          make_grid("spl-r", rn.sort_values("Run Rate" if "Run Rate" in rn.columns else rn.columns[0], ascending=False).head(10).to_dict("records"), defs, 320)], style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px"}),
        ])

    if tab == "analytics":
        df = data["ANALYTICS"]
        if df.empty:
            return html.Div([
                sec(f"// TEAM ANALYTICS · {season_str}", mt=0),
                empty_msg("Run fetch_team_analytics.py first to generate team analytics data."),
            ])
        rn = df.rename(columns=COL_LABELS).fillna("—")
        heat_an = {"Pass Yds/G","Rush Yds/G","Total Yds/G","Pts/G","RZ Conv%","3rd Down%","YPP"}
        defs = []
        for c in rn.columns:
            d={"field":c,"headerName":c,"sortable":True,"resizable":True,"minWidth":80}
            if c=="team": d.update({"pinned":"left","headerName":"Team","minWidth":70,"cellStyle":{"fontFamily":"Share Tech Mono, monospace","color":ACCENT,"fontWeight":"600"}})
            if c in heat_an: d["cellStyle"]=heat_style(c)
            defs.append(d)
        # Top stat cards
        def top_team(col, asc=False):
            col_r = COL_LABELS.get(col,col)
            if col_r not in rn.columns: return "—"
            s = rn.sort_values(col_r, ascending=asc)
            return s.iloc[0]["team"] if "team" in s.columns else "—"
        return html.Div([
            sec(f"// TEAM ANALYTICS · {season_str} · FANTASY-RELEVANT METRICS", mt=0),
            html.Div([
                stat_card(top_team("pass_rate"),"Most Pass-Heavy"),
                stat_card(top_team("run_rate"),"Most Run-Heavy"),
                stat_card(top_team("pts_game"),"Most Pts/Game"),
                stat_card(top_team("rz_conv_pct"),"Best RZ Conv%"),
                stat_card(top_team("third_down_pct"),"Best 3rd Down%"),
            ], style={"display":"flex","gap":"10px","marginBottom":"14px"}),
            make_grid("g-analytics", rn.to_dict("records"), defs, 560),
            html.Div(f"// {len(df)} teams · heat-map coloring — green = elite · click any column to sort",
                     style={"fontSize":"10px","color":ADIM,"marginTop":"8px","fontFamily":"Share Tech Mono, monospace"}),
        ])

    if tab == "sos-h":
        df = data["SOS"]
        if df.empty: return empty_msg()
        return html.Div([
            sec(f"// STRENGTH OF SCHEDULE · {season_str}", mt=0),
            ctrl("POSITION", dcc.Dropdown(id="sos-h-pos",
                options=[{"label":p,"value":p} for p in ["RB","WR","QB","TE"]],
                value="RB",clearable=False,
                style={"width":"120px","background":SURF,"color":TEXT,
                       "border":f"1px solid {BORDER}","borderRadius":"0","fontSize":"11px"})),
            html.Div(id="sos-h-c",style={"marginTop":"12px"}),
        ])

    if tab == "opp":
        if int(season_str) != 2025:
            return html.Div("// Opportunity Score data is 2025 only.",
                            style={"fontFamily":"Share Tech Mono, monospace","fontSize":"11px","color":ADIM,"padding":"24px"})
        return html.Div([
            sec("// OPPORTUNITY SCORE · 2025 · TOP 50 PER POSITION", mt=0),
            html.Div("// Opp Score = expected PPR pts based on touch quality. Compare AVG OPP vs OPP FPTS to spot over/underperformers.",
                     style={"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","color":ADIM,"marginBottom":"12px","lineHeight":"1.8"}),
            dcc.Tabs(id="opp-pos", value="opp-rb", children=[
                dcc.Tab(label="RB",value="opp-rb",style=_ts(),selected_style=_tsa()),
                dcc.Tab(label="WR",value="opp-wr",style=_ts(),selected_style=_tsa()),
                dcc.Tab(label="TE",value="opp-te",style=_ts(),selected_style=_tsa()),
            ], colors={"border":BORDER,"primary":ACCENT,"background":BG}),
            html.Div(id="opp-g",style={"paddingTop":"12px"}),
        ])

    if tab == "profile":
        all_p = []
        for pos in ["QB","RB","WR","TE"]:
            df_p = get_data(season_str)[pos]
            if not df_p.empty and "player_display_name" in df_p.columns:
                all_p.extend(df_p["player_display_name"].tolist())
        all_p = sorted(set(all_p))
        return html.Div([
            sec(f"// PLAYER PROFILE · {season_str}", mt=0),
            ctrl("SELECT PLAYER", dcc.Dropdown(id="profile-sel",
                options=[{"label":p,"value":p} for p in all_p],
                placeholder="Choose a player...",clearable=False,
                style={"width":"280px","background":SURF,"color":TEXT,
                       "border":f"1px solid {BORDER}","borderRadius":"0","fontSize":"12px"})),
            html.Div(id="profile-c",style={"marginTop":"14px"}),
        ])

    return html.Div()

# ── OPP GRID ──────────────────────────────────────────────────────────────────
@app.callback(Output("opp-g","children"), Input("opp-pos","value"))
def render_opp(tab):
    pos={"opp-rb":"RB","opp-wr":"WR","opp-te":"TE"}.get(tab,"RB")
    df=build_opp_df(pos)
    return html.Div([
        make_grid(f"opp-{pos}",df.to_dict("records"),opp_col_defs(),620),
        html.Div(f"// Top 50 {pos}s · AVG OPP = season avg · OPP FPTS = actual PPR pts · BYE = bye · SUS = suspended",
                 style={"fontSize":"10px","color":ADIM,"marginTop":"8px","fontFamily":"Share Tech Mono, monospace"}),
    ])

# ── MOCK BOARD ────────────────────────────────────────────────────────────────
@app.callback(Output("mock-grid","children"), Input("mock-s","value"), Input("mock-pos","value"))
def render_mock(search, pos):
    if mock_board.empty: return empty_msg()
    mb = mock_board.copy()
    mb["Pick"] = mb.apply(lambda r: f"{int(r['round'])}.{int(r['pick_in_round']):02d}", axis=1)
    if pos and pos!="ALL": mb=mb[mb["position"]==pos]
    if search: mb=mb[mb["player"].str.contains(search,case=False,na=False)]
    defs=[
        {"field":"Pick","headerName":"Pick","width":68,"pinned":"left","sortable":True,
         "cellStyle":{"fontFamily":"Share Tech Mono, monospace","color":ACCENT}},
        {"field":"player","headerName":"Player","width":200,"pinned":"left","sortable":True,
         "cellStyle":{"fontWeight":"600","color":TEXT}},
        {"field":"position","headerName":"Pos","width":65,"cellStyle":pos_style_js()},
        {"field":"team","headerName":"Team","width":65,"cellStyle":{"color":TDIM}},
        {"field":"adp","headerName":"ADP","width":70,"sortable":True,
         "cellStyle":{"color":TDIM,"fontFamily":"Share Tech Mono, monospace"}},
    ]
    return html.Div([
        make_grid("mock-g",mb[["Pick","player","position","team","adp"]].to_dict("records"),defs,620),
        html.Div(f"// {len(mb)} players · FantasyPros PPR ADP 2026 · 12-team linear order",
                 style={"fontSize":"10px","color":ADIM,"marginTop":"8px","fontFamily":"Share Tech Mono, monospace"}),
    ])

# ── SOS 2026 ──────────────────────────────────────────────────────────────────
@app.callback(Output("sos26-c","children"), Input("sos26-pos","value"))
def render_sos26(pos):
    if sos_2026.empty: return empty_msg()
    df=sos_2026[sos_2026["position"]==pos].sort_values("sos_2026_rank").copy()
    rn={"team":"Team","avg_opp_pts_allowed":"Avg PPR Pts Allowed","sos_2026_rank":"SOS Rank","difficulty":"Difficulty"}
    easy=df.head(8)[list(rn)].rename(columns=rn).to_dict("records")
    hard=df.tail(8).sort_values("sos_2026_rank",ascending=False)[list(rn)].rename(columns=rn).to_dict("records")
    defs=[{"field":c,"headerName":c,"sortable":True,"resizable":True} for c in list(rn.values())]
    return html.Div([
        html.Div([
            html.Div([html.Div(f"EASIEST {pos} SCHEDULES",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","color":GREEN,"marginBottom":"8px"}),
                      make_grid("s26-e",easy,defs,280)],style={"flex":"1"}),
            html.Div([html.Div(f"HARDEST {pos} SCHEDULES",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","color":RED,"marginBottom":"8px"}),
                      make_grid("s26-h",hard,defs,280)],style={"flex":"1"}),
        ],style={"display":"flex","gap":"16px","marginBottom":"16px"}),
        sec("// ALL TEAMS"),
        make_grid("s26-a",df[list(rn)].rename(columns=rn).to_dict("records"),defs,380),
    ])

# ── SOS HISTORICAL ────────────────────────────────────────────────────────────
@app.callback(Output("sos-h-c","children"), Input("sos-h-pos","value"), Input("season","value"))
def render_sos_h(pos, season_str):
    if season_str=="2026": return html.Div()
    df=get_data(season_str)["SOS"]
    if df.empty: return empty_msg()
    tc=next((c for c in ["team","recent_team","opponent_team"] if c in df.columns),df.columns[0])
    sos=df[df["position"]==pos].sort_values("avg_pts_allowed",ascending=False).copy()
    sos["avg_pts_allowed"]=sos["avg_pts_allowed"].round(2)
    cols=[c for c in [tc,"avg_pts_allowed","sos_rank"] if c in sos.columns]
    rn={tc:"Team","avg_pts_allowed":"Avg Pts Allowed","sos_rank":"SOS Rank"}
    records=sos[cols].rename(columns=rn).fillna("—").to_dict("records")
    defs=[{"field":c,"headerName":c,"sortable":True,"resizable":True} for c in list(rn.values()) if c in (records[0] if records else {})]
    return make_grid("sos-h-g",records,defs,500)

# ── SOURCE COMPARE ────────────────────────────────────────────────────────────
@app.callback(Output("src-c","children"), Input("src-pos","value"))
def render_src(pos):
    if master.empty: return empty_msg()
    df=master.copy() if pos=="ALL" else (master[master["position"]==pos].copy() if "position" in master.columns else master.copy())
    ext=[c for c in ["fc_rank","ffc_rank","fp_rank","espn_rank","rb_overall_rank","yahoo_rank"] if c in df.columns and df[c].notna().sum()>3]
    if not ext: return html.Div("Not enough ranking sources.",style={"color":TDIM})
    df["rank_stdev"]=df[ext].apply(pd.to_numeric,errors="coerce").std(axis=1).round(1)
    sc=[c for c in (["player","position","team"] if "player" in df.columns else [])+ext+["rank_stdev"] if c in df.columns]
    rn=df[sc].rename(columns=COL_LABELS).fillna("—")
    defs=[{"field":c,"headerName":c,"sortable":True,"resizable":True} for c in rn.columns]
    last=rn.columns[-1]
    return html.Div([
        html.Div([
            html.Div([html.Div("BIGGEST DISAGREEMENTS",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","color":RED,"marginBottom":"8px"}),
                      make_grid("src-d",rn.sort_values(last,ascending=False).head(15).to_dict("records"),defs,440)],style={"flex":"1"}),
            html.Div([html.Div("STRONGEST CONSENSUS",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","color":GREEN,"marginBottom":"8px"}),
                      make_grid("src-a",rn.sort_values(last).head(15).to_dict("records"),defs,440)],style={"flex":"1"}),
        ],style={"display":"flex","gap":"16px"}),
    ])

# ── DRAFT TOGGLE ──────────────────────────────────────────────────────────────
def _render_must():
    col1=html.Div([
        html.Div("// MUST DRAFTS",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"11px","color":GREEN,"letterSpacing":".15em","marginBottom":"12px"}),
        *[html.Div([
            html.Div(k.upper(),style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".12em","borderBottom":f"1px solid {BORDER}","paddingBottom":"4px","marginTop":"14px","marginBottom":"6px"}),
            *[html.Div(f"✦ {p}",className="draft-g") for p in v]
          ]) for k,v in MUST_DRAFT.items()]
    ], style={"flex":"1"})
    col2=html.Div([
        html.Div("// MUST AVOIDS",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"11px","color":RED,"letterSpacing":".15em","marginBottom":"12px"}),
        *[html.Div([
            html.Div(k.upper(),style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".12em","borderBottom":f"1px solid {BORDER}","paddingBottom":"4px","marginTop":"14px","marginBottom":"6px"}),
            *[html.Div(f"✗ {p}",className="draft-r") for p in v]
          ]) for k,v in MUST_AVOID.items()]
    ], style={"flex":"1"})
    return html.Div([col1,col2],style={"display":"flex","gap":"24px"})

def _render_target():
    items=list(TARGET_PICKS.items()); mid=(len(items)+1)//2
    def col(subset):
        return [html.Div([
            html.Div(r.upper(),style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".12em","borderBottom":f"1px solid {BORDER}","paddingBottom":"4px","marginTop":"14px","marginBottom":"6px"}),
            *[html.Div(f"◆ {p}",className="draft-p") for p in ps]
        ]) for r,ps in subset]
    return html.Div([
        html.Div([html.Div("// FAVORITE PICKS BY ROUND",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"11px","color":ACCENT,"letterSpacing":".15em","marginBottom":"12px"}),*col(items[:mid])],style={"flex":"1"}),
        html.Div(col(items[mid:]),style={"flex":"1","marginTop":"38px"}),
    ],style={"display":"flex","gap":"24px"})

def _render_uv():
    def pills(stats):
        return "".join(
            f'<span style="display:inline-flex;align-items:center;gap:4px;background:#1a2535;'
            f'border:1px solid #2a3545;border-radius:3px;padding:3px 8px;margin:3px 3px 3px 0;'
            f'font-size:.7rem;white-space:nowrap;">'
            f'<span style="color:{ACCENT};font-weight:700;font-family:Share Tech Mono,monospace;">{v}</span>'
            f'<span style="color:{TDIM};">{l}</span></span>'
            for v,l in stats)
    cols=html.Div(id="_uv_inner",style={"display":"flex","gap":"16px","flexWrap":"wrap"})
    cards=[]
    for p in UNDERVALUED:
        pc=POS_C.get(p["pos"],TEXT)
        bullets="".join(f'<div style="display:flex;gap:6px;margin-bottom:5px;"><span style="color:{ACCENT};flex-shrink:0;">◆</span><span style="color:{TEXT};font-size:.82rem;line-height:1.5;">{b}</span></div>' for b in p["bullets"])
        sh=""
        if p.get("stats_hdr") and p.get("stats"):
            sh=(f'<div style="font-family:Share Tech Mono,monospace;font-size:.65rem;color:{ADIM};letter-spacing:.15em;margin:10px 0 6px 0;">// {p["stats_hdr"]}</div>'
                f'<div style="display:flex;flex-wrap:wrap;">{pills(p["stats"])}</div>')
        xh=""
        if p.get("extra_hdr") and p.get("extra_stats"):
            xh=(f'<div style="font-family:Share Tech Mono,monospace;font-size:.65rem;color:{ADIM};letter-spacing:.15em;margin:10px 0 6px 0;">// {p["extra_hdr"]}</div>'
                f'<div style="display:flex;flex-wrap:wrap;">{pills(p["extra_stats"])}</div>')
        card=f"""
<div style="background:#0a1020;border:1px solid #1e2d45;border-top:3px solid {ACCENT};border-radius:4px;padding:16px;margin-bottom:14px;">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px;">
    <div>
      <div style="font-family:Share Tech Mono,monospace;font-size:1.1rem;color:#e8f0f8;font-weight:700;margin-bottom:4px;">{p['name']}</div>
      <span style="background:{pc}22;border:1px solid {pc}55;color:{pc};font-family:Share Tech Mono,monospace;font-size:.65rem;padding:2px 7px;border-radius:2px;font-weight:700;">{p['pos']} · {p['team']}</span>
    </div>
    <div style="text-align:right;">
      <div style="font-family:Share Tech Mono,monospace;font-size:.65rem;color:{ADIM};letter-spacing:.1em;margin-bottom:2px;">PROJ VALUE</div>
      <div style="font-family:Share Tech Mono,monospace;font-size:1rem;color:{ACCENT};font-weight:700;">{p['proj_rank']}</div>
      <div style="font-family:Share Tech Mono,monospace;font-size:.75rem;color:{TDIM};">Rd {p['adp']}</div>
    </div>
  </div>
  <div style="border-top:1px solid #1e2d45;padding-top:10px;">{bullets}</div>
  {sh}{xh}
</div>"""
        cards.append(html.Div(html.Div(dangerously_allow_html=card, id=f"uv-{p['name'].replace(' ','_')}") if False else
                     html.Div([html.Div(f"{p['name']} · {p['proj_rank']} (Rd {p['adp']}) · {p['pos']} {p['team']}",
                               style={"fontFamily":"Share Tech Mono, monospace","fontSize":"11px","color":ACCENT,"marginBottom":"8px","fontWeight":"700"}),
                               *[html.Div(f"◆ {b}",className="draft-p") for b in p["bullets"]],
                               *([html.Div(f"// {p['stats_hdr']}",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".15em","margin":"10px 0 6px 0"})] if p.get("stats_hdr") else []),
                               *[html.Div(f"{v} — {l}",style={"fontSize":"11px","color":TEXT,"margin":"3px 0 3px 12px"}) for v,l in p.get("stats",[])],
                               *([html.Div(f"// {p['extra_hdr']}",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".15em","margin":"10px 0 6px 0"})] if p.get("extra_hdr") else []),
                               *[html.Div(f"{v} — {l}",style={"fontSize":"11px","color":TEXT,"margin":"3px 0 3px 12px"}) for v,l in p.get("extra_stats",[])],
                             ],style={"background":"#0a1020","border":f"1px solid #1e2d45","borderTop":f"3px solid {ACCENT}","borderRadius":"4px","padding":"16px","marginBottom":"14px"}
                     )))
    left  = cards[0::2]
    right = cards[1::2]
    return html.Div([
        html.Div("// UNDERVALUED PLAYERS · 2026 TARGETS",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"11px","color":ACCENT,"letterSpacing":".15em","marginBottom":"14px"}),
        html.Div([html.Div(left,style={"flex":"1"}),html.Div(right,style={"flex":"1"})],style={"display":"flex","gap":"16px"}),
        html.Div("// Projected value = consensus rank · ADP = draft round · PPR scoring",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"marginTop":"8px"}),
    ])

@app.callback(
    Output("draft-c","children"),
    Output("btn-must","className"), Output("btn-target","className"), Output("btn-uv","className"),
    Input("btn-must","n_clicks"), Input("btn-target","n_clicks"), Input("btn-uv","n_clicks"),
    prevent_initial_call=True,
)
def toggle_draft(nm,nt,nu):
    t=ctx.triggered_id
    if t=="btn-target": return _render_target(),"toggle-btn","toggle-btn active","toggle-btn"
    if t=="btn-uv":     return _render_uv(),   "toggle-btn","toggle-btn","toggle-btn active"
    return _render_must(),"toggle-btn active","toggle-btn","toggle-btn"

# ── COACHING CHANGES ──────────────────────────────────────────────────────────
def _render_coaching():
    cards=[]
    for c in COACHING_CHANGES:
        imp=c["impact"]
        border_c = GREEN if imp=="POSITIVE" else (RED if imp=="NEGATIVE" else ADIM)
        imp_c    = GREEN if imp=="POSITIVE" else (RED if imp=="NEGATIVE" else ADIM)
        up_chips = html.Div([
            html.Span(f"↑ {p}",style={"background":GREEN+"18","border":f"1px solid {GREEN}44","color":GREEN,
                "fontFamily":"Share Tech Mono, monospace","fontSize":"9px","padding":"2px 7px",
                "borderRadius":"2px","marginRight":"4px","marginBottom":"4px","display":"inline-block"})
            for p in c["up"]
        ]) if c["up"] else html.Div()
        down_chips = html.Div([
            html.Span(f"↓ {p}",style={"background":RED+"18","border":f"1px solid {RED}44","color":RED,
                "fontFamily":"Share Tech Mono, monospace","fontSize":"9px","padding":"2px 7px",
                "borderRadius":"2px","marginRight":"4px","marginBottom":"4px","display":"inline-block"})
            for p in c["down"]
        ]) if c["down"] else html.Div()
        card=html.Div([
            # Header row
            html.Div([
                html.Div([
                    html.Span(c["team"],style={"fontFamily":"Share Tech Mono, monospace","fontSize":"1.3rem","color":ACCENT,"fontWeight":"700","letterSpacing":".1em","marginRight":"10px"}),
                    html.Span(imp,style={"background":imp_c+"22","border":f"1px solid {imp_c}55","color":imp_c,"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","padding":"2px 8px","borderRadius":"2px","fontWeight":"700"}),
                ], style={"display":"flex","alignItems":"center","marginBottom":"4px"}),
                html.Div(c["full"],style={"color":TDIM,"fontSize":"11px","marginBottom":"10px"}),
            ]),
            # Coach change
            html.Div([
                html.Div("OUT",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".15em","marginBottom":"3px"}),
                html.Div(c["out"],style={"color":RED,"fontSize":"12px","fontWeight":"600","marginBottom":"6px"}),
                html.Div("→",style={"color":ADIM,"fontSize":"14px","marginBottom":"6px"}),
                html.Div("IN",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".15em","marginBottom":"3px"}),
                html.Div(c["new_hc"],style={"color":GREEN,"fontSize":"12px","fontWeight":"600"}),
                html.Div(f"from {c['prev']}",style={"color":TDIM,"fontSize":"10px","marginTop":"2px","marginBottom":"10px"}),
            ]),
            # Style
            html.Div([
                html.Div("// SCHEME",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".15em","marginBottom":"4px"}),
                html.Div(c["style"],style={"color":TEXT,"fontSize":"11px","marginBottom":"10px"}),
            ]),
            # Impact
            html.Div([
                html.Div("// FANTASY IMPACT",style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"letterSpacing":".15em","marginBottom":"4px"}),
                html.Div(c["note"],style={"color":TEXT,"fontSize":"11px","lineHeight":"1.6","marginBottom":"10px"}),
            ]),
            # Players
            up_chips, down_chips,
        ], style={"background":"#0a1020","border":f"1px solid #1e2d45","borderTop":f"3px solid {border_c}",
                  "borderRadius":"4px","padding":"16px"})
        cards.append(card)

    # 2-column grid
    left  = cards[0::2]
    right = cards[1::2]
    return html.Div([
        sec("// 2026 COACHING CHANGES · 10 NEW HEAD COACHES · FANTASY IMPACT", mt=0),
        html.Div("// ↑ = players likely to benefit · ↓ = players facing uncertainty",
                 style={"fontFamily":"Share Tech Mono, monospace","fontSize":"9px","color":ADIM,"marginBottom":"14px"}),
        html.Div([
            html.Div(left, style={"flex":"1","display":"flex","flexDirection":"column","gap":"14px"}),
            html.Div(right,style={"flex":"1","display":"flex","flexDirection":"column","gap":"14px"}),
        ], style={"display":"flex","gap":"14px"}),
    ])

# ── PLAYER PROFILE ────────────────────────────────────────────────────────────
@app.callback(Output("profile-c","children"), Input("profile-sel","value"), Input("season","value"))
def render_profile(player, season_str):
    if not player or season_str=="2026": return html.Div()
    season=int(season_str); data=get_data(season_str)
    player_row=None; player_pos=None
    for pos in ["QB","RB","WR","TE"]:
        df_p=data[pos]
        if not df_p.empty and "player_display_name" in df_p.columns:
            m=df_p[df_p["player_display_name"]==player]
            if not m.empty: player_row=m.iloc[0]; player_pos=pos; break
    if player_row is None: return html.Div("Player not found.",style={"color":TDIM})

    team=player_row.get("recent_team","—")
    games=int(player_row.get("games",0))
    total=round(float(player_row.get("fantasy_points_ppr",0)),1)
    fppg=round(float(player_row.get("fppg_ppr",0)),2)
    boom_t=round(fppg*1.5,1); bust_t=round(fppg*0.5,1)

    headshot=None
    if not player_info.empty and "player_display_name" in player_info.columns:
        im=player_info[player_info["player_display_name"]==player]
        if not im.empty: headshot=im.iloc[0].get("headshot_url")

    pos_color = POS_C.get(player_pos, TEXT)
    header=html.Div([
        html.Div([
            html.Img(src=headshot,style={"width":"120px","height":"120px","objectFit":"cover","border":f"1px solid {BORDER}"})
            if headshot and pd.notna(headshot)
            else html.Div("🏈",style={"width":"120px","height":"120px","background":SURF,"border":f"1px solid {BORDER}","display":"flex","alignItems":"center","justifyContent":"center","fontSize":"2.5rem"}),
        ],style={"marginRight":"20px"}),
        html.Div([
            html.Div(player,style={"fontFamily":"Share Tech Mono, monospace","fontSize":"1.6rem","color":ACCENT,"fontWeight":"bold"}),
            html.Div([
                html.Span(player_pos,style={"background":pos_color+"22","border":f"1px solid {pos_color}55","color":pos_color,"fontFamily":"Share Tech Mono, monospace","fontSize":"10px","padding":"2px 8px","borderRadius":"2px","fontWeight":"700","marginRight":"8px"}),
                html.Span(team,style={"color":TDIM,"fontSize":"12px"}),
            ],style={"marginTop":"6px","marginBottom":"12px"}),
            html.Div([stat_card(total,"Total PPR"),stat_card(fppg,"FPPG (PPR)"),stat_card(games,"Games")],
                     style={"display":"flex","gap":"10px","maxWidth":"380px"}),
        ]),
    ],style={"display":"flex","alignItems":"flex-start","marginBottom":"20px"})

    gamelogs=load_gamelogs(season)
    if gamelogs.empty or "player_display_name" not in gamelogs.columns:
        return html.Div([header,html.Div("Run build_player_profiles.py to generate game logs.",style={"color":TDIM,"fontFamily":"Share Tech Mono, monospace","fontSize":"11px"})])

    gl=gamelogs[gamelogs["player_display_name"]==player].sort_values("week").copy()
    if gl.empty:
        return html.Div([header,html.Div("No game log data found.",style={"color":TDIM,"fontFamily":"Share Tech Mono, monospace","fontSize":"11px"})])

    gl["result"]=gl["fantasy_points_ppr"].apply(lambda x: "—" if pd.isna(x) else "BOOM" if x>=boom_t else "BUST" if x<=bust_t else "AVG")
    boom_n=(gl["result"]=="BOOM").sum(); bust_n=(gl["result"]=="BUST").sum(); avg_n=(gl["result"]=="AVG").sum()
    boom_r=f"{boom_n/len(gl)*100:.0f}%" if len(gl)>0 else "—"

    boom_cards=html.Div([
        html.Div([html.Div(str(boom_n),style={"fontFamily":"Share Tech Mono, monospace","fontSize":"1.4rem","color":GREEN}),html.Div(f"BOOM (≥{boom_t})",style={"fontSize":"9px","color":ADIM,"letterSpacing":".1em"})],
                 style={"background":SURF,"border":f"1px solid {BORDER}","borderLeft":f"3px solid {GREEN}","padding":"10px 14px","flex":"1"}),
        html.Div([html.Div(str(bust_n),style={"fontFamily":"Share Tech Mono, monospace","fontSize":"1.4rem","color":RED}),html.Div(f"BUST (≤{bust_t})",style={"fontSize":"9px","color":ADIM,"letterSpacing":".1em"})],
                 style={"background":SURF,"border":f"1px solid {BORDER}","borderLeft":f"3px solid {RED}","padding":"10px 14px","flex":"1"}),
        html.Div([html.Div(str(avg_n),style={"fontFamily":"Share Tech Mono, monospace","fontSize":"1.4rem","color":TEXT}),html.Div("AVG GAMES",style={"fontSize":"9px","color":ADIM,"letterSpacing":".1em"})],
                 style={"background":SURF,"border":f"1px solid {BORDER}","borderLeft":f"3px solid {BORDER}","padding":"10px 14px","flex":"1"}),
        html.Div([html.Div(boom_r,style={"fontFamily":"Share Tech Mono, monospace","fontSize":"1.4rem","color":TEXT}),html.Div("BOOM RATE",style={"fontSize":"9px","color":ADIM,"letterSpacing":".1em"})],
                 style={"background":SURF,"border":f"1px solid {BORDER}","borderLeft":f"3px solid {BORDER}","padding":"10px 14px","flex":"1"}),
    ],style={"display":"flex","gap":"10px","marginBottom":"14px"})

    base=["week","opponent_team","fantasy_points_ppr","result"]
    extra={"QB":["completions","attempts","passing_yards","passing_tds","interceptions","carries","rushing_yards"],
           "RB":["carries","rushing_yards","rushing_tds","receptions","targets","receiving_yards","receiving_tds"],
           "WR":["receptions","targets","receiving_yards","receiving_tds"],
           "TE":["receptions","targets","receiving_yards","receiving_tds"]}.get(player_pos,[])
    show=[c for c in base+[c for c in extra if c in gl.columns] if c in gl.columns]
    gld=gl[show].copy()
    if "fantasy_points_ppr" in gld.columns:
        gld["fantasy_points_ppr"]=gld["fantasy_points_ppr"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    lbl={"week":"Wk","opponent_team":"Opp","fantasy_points_ppr":"PPR","result":"Result",
         "completions":"Comp","attempts":"Att","passing_yards":"Pass Yds","passing_tds":"Pass TD",
         "interceptions":"INT","carries":"Car","rushing_yards":"Rush Yds","rushing_tds":"Rush TD",
         "receptions":"Rec","targets":"Tgt","receiving_yards":"Rec Yds","receiving_tds":"Rec TD"}
    gld=gld.rename(columns=lbl)
    gl_defs=[]
    for c in gld.columns:
        d={"field":c,"headerName":c,"sortable":True,"resizable":True,"width":90}
        if c=="Result":
            d["cellStyle"]={"function":f"(function(p){{if(p.value==='BOOM') return {{background:'#0a2e0a',color:'{GREEN}',fontWeight:'600'}};if(p.value==='BUST') return {{background:'#2e0a0a',color:'{RED}',fontWeight:'600'}};return {{color:'{TEXT}'}};}})(params)"}
        elif c=="PPR":
            d["cellStyle"]={"function":f"(function(p){{var v=parseFloat(p.value);if(v>={boom_t}) return {{color:'{GREEN}',fontWeight:'600'}};if(v<={bust_t}) return {{color:'{RED}',fontWeight:'600'}};return {{color:'{TEXT}'}};}})(params)"}
        gl_defs.append(d)

    return html.Div([
        header, boom_cards,
        sec("// GAME LOG"),
        make_grid("profile-g",gld.to_dict("records"),gl_defs,380),
    ])

# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, port=8050)
