"""
app.py — Fantasy Edge · Dash Edition · Render Deployment
Run locally:  py -3.12 app.py  →  http://localhost:8050
Deploy:       gunicorn app:server --bind 0.0.0.0:$PORT
"""

from dash import Dash, html, dcc, Input, Output, State, ctx, ALL, no_update
import dash_ag_grid as dag
import pandas as pd
import os

# ── INIT ──────────────────────────────────────────────────────────────────────
app    = Dash(__name__, suppress_callback_exceptions=True, title="Fantasy Edge")
server = app.server   # exposed for gunicorn

DATA_DIR = "data"

# ── PALETTE ───────────────────────────────────────────────────────────────────
BG      = "#0a0e14"
SURF    = "#10151d"
SURF2   = "#141a24"
BORDER  = "#212a38"
ACCENT  = "#2dd4bf"     # teal
ACCENT2 = "#f2b93a"     # amber, secondary highlight
TEXT    = "#e6ebf2"
TDIM    = "#8b95a7"
TFAINT  = "#5b6478"
GREEN   = "#34d399"
RED     = "#f87171"
POS_C   = {"QB":"#60a5fa","RB":"#34d399","WR":"#fb923c","TE":"#c084fc","K":"#facc15","DST":"#94a3b8"}

FONT_HEAD = "'Inter', -apple-system, sans-serif"
FONT_MONO = "'JetBrains Mono', monospace"

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
app.index_string = """<!DOCTYPE html>
<html>
<head>
  {%metas%}<title>{%title%}</title>{%favicon%}{%css%}
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    html,body{background:#0a0e14;color:#e6ebf2;font-family:'Inter',sans-serif;font-size:14px}
    ::-webkit-scrollbar{width:6px;height:6px}
    ::-webkit-scrollbar-track{background:#0a0e14}
    ::-webkit-scrollbar-thumb{background:#212a38;border-radius:4px}
    ::-webkit-scrollbar-thumb:hover{background:#2dd4bf66}

    .ag-theme-alpine-dark{
      --ag-background-color:#10151d;
      --ag-foreground-color:#e6ebf2;
      --ag-header-background-color:#141a24;
      --ag-header-foreground-color:#8b95a7;
      --ag-odd-row-background-color:#10151d;
      --ag-row-hover-color:#161d29;
      --ag-selected-row-background-color:#132821;
      --ag-border-color:#212a38;
      --ag-row-border-color:#1a212c;
      --ag-font-size:13px;
      --ag-font-family:'Inter',sans-serif;
      --ag-row-height:34px;
      --ag-header-height:38px;
      --ag-cell-horizontal-padding:12px;
    }
    .ag-theme-alpine-dark .ag-header-cell-label{font-weight:700;font-size:11px;letter-spacing:.04em;text-transform:uppercase}
    .ag-theme-alpine-dark .ag-root-wrapper{border:1px solid #212a38!important;border-radius:10px;overflow:hidden}
    .ag-theme-alpine-dark .ag-header{border-radius:10px 10px 0 0}
    .ag-theme-alpine-dark .ag-cell{font-variant-numeric:tabular-nums}
    .ag-theme-alpine-dark .ag-icon{color:#5b6478}
    .ag-theme-alpine-dark .ag-header-cell:hover{background:#1a212c}

    .season-pill{font-family:'Inter',sans-serif;font-size:13px;font-weight:600;
      color:#8b95a7;padding:9px 20px;border-radius:8px;cursor:pointer;border:1px solid transparent}
    .season-pill.sel{color:#0a0e14;background:#2dd4bf}

    .tab-lbl{font-family:'Inter',sans-serif;font-size:12.5px;font-weight:600;letter-spacing:.02em;
      color:#8b95a7;padding:11px 16px;border:none;border-bottom:2px solid transparent;
      background:transparent;cursor:pointer;white-space:nowrap}
    .tab-lbl.sel{color:#2dd4bf;border-bottom:2px solid #2dd4bf}

    .sec-label{font-family:'Inter',sans-serif;font-size:11px;font-weight:700;color:#8b95a7;
      letter-spacing:.08em;text-transform:uppercase;margin-bottom:14px}
    .sec-sub{font-size:12px;color:#5b6478;margin-top:-8px;margin-bottom:14px}
    .stat-card{background:#10151d;border:1px solid #212a38;border-radius:10px;
      padding:14px 18px;flex:1}
    .card-val{font-family:'JetBrains Mono',monospace;font-size:1.5rem;color:#2dd4bf;font-weight:700;line-height:1}
    .card-lbl{font-size:10.5px;color:#5b6478;letter-spacing:.08em;text-transform:uppercase;margin-top:6px;font-weight:600}
    .badge{display:inline-block;background:#132821;border:1px solid #2dd4bf55;color:#2dd4bf;
      border-radius:6px;font-size:11px;font-weight:700;padding:4px 12px;letter-spacing:.04em}
    .ctrl-in{background:#10151d;border:1px solid #212a38;color:#e6ebf2;border-radius:8px;
      font-size:12.5px;padding:8px 12px;outline:none;width:100%}
    .ctrl-in:focus{border-color:#2dd4bf}
    .ctrl-lbl{font-size:10.5px;color:#5b6478;letter-spacing:.08em;text-transform:uppercase;
      margin-bottom:6px;font-weight:700}
    .dash-dropdown-value-item, .dash-dropdown-value, .dash-dropdown-trigger,
    .dash-dropdown-trigger-icon, .dash-dropdown-input{color:#0a0e14!important}
    .dash-dropdown-menu, .dash-dropdown-option{background:#fff!important;color:#0a0e14!important}
    .dash-dropdown-option:hover, .dash-dropdown-option--focused{background:#e6ebf2!important}
    .Select-control, .Select-value-label, .Select-placeholder, .Select-input > input,
    .Select-menu-outer, .Select-option, .Select-noresults, .VirtualizedSelectOption,
    .Select--single > .Select-control .Select-value, .Select-arrow-zone{color:#0a0e14!important}
    .Select-menu-outer, .Select-option{background:#fff!important}
    .Select-option.is-focused{background:#e6ebf2!important}
    .toggle-btn{background:#10151d;border:1px solid #212a38;color:#8b95a7;border-radius:8px;
      font-size:12px;font-weight:600;padding:8px 16px;cursor:pointer;margin-right:8px}
    .toggle-btn:hover,.toggle-btn.active{border-color:#2dd4bf;color:#2dd4bf;background:#132821}
    .draft-g{padding:8px 12px;margin:4px 0;background:#0f1d16;border-left:3px solid #34d399;
      border-radius:0 6px 6px 0;font-size:12.5px;font-weight:500}
    .draft-r{padding:8px 12px;margin:4px 0;background:#1d1010;border-left:3px solid #f87171;
      border-radius:0 6px 6px 0;font-size:12.5px;font-weight:500}
    .draft-p{padding:8px 12px;margin:4px 0;background:#0e1a22;border-left:3px solid #2dd4bf;
      border-radius:0 6px 6px 0;font-size:12.5px;font-weight:500}
    .coach-card{background:#10151d;border:1px solid #212a38;border-radius:10px;padding:18px;margin-bottom:14px}
    .coach-card.pos{border-top:3px solid #34d399}
    .coach-card.neg{border-top:3px solid #f87171}
    .coach-card.neu{border-top:3px solid #5b6478}
    .app-shell{max-width:1400px;margin:0 auto}
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
    "fppg_ppr":"FPPG","fantasy_points_ppr":"Total PPR",
    "passing_yards":"Pass Yds","total_tds":"Total TD","interceptions":"INT",
    "total_yards":"Total Yds",
    "team":"Team","pass_rate":"Pass Rate","run_rate":"Run Rate",
    "third_down_pct":"3rd Down Conv%","rz_conv_pct":"RZ Conv%",
    "avg_pts_allowed":"Avg Pts Allowed","sos_rank":"SOS Rank",
    "position":"Pos","consensus_rank":"Consensus Rank","consensus_pos_rank":"Pos Rank",
    "fc_rank":"FantasyCalc",
    "fc_pos_rank":"FC Pos Rank","ffc_rank":"FFC Rank","ffc_adp":"ADP",
    "espn_rank":"ESPN","rb_overall_rank":"RotoBaller","fc_value":"FC Value",
    "yahoo_rank":"Yahoo","yahoo_pos_rank":"Yahoo Pos","2025_fppg_ppr":"2025 FPPG",
    "overall_rank":"Rank","player":"Player",
}

# ── COACHING CHANGES 2026 (kept from prior build) ──────────────────────────────
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
     "prev":"Green Bay Packers DC","style":"Defensive-minded · OC Bobby Slowik calling plays",
     "impact":"NEGATIVE","note":"McDaniel's elite WR-friendly scheme is gone, replaced by Slowik under new HC Hafley. De'Von Achane and Jaylen Waddle both face real uncertainty in the new offense.",
     "up":[],"down":["De'Von Achane","Jaylen Waddle","Tyreek Hill"]},
    {"team":"LAC","full":"Los Angeles Chargers","out":"Greg Roman (former playcaller)","new_hc":"Mike McDaniel",
     "prev":"Miami Dolphins Head Coach (fired)","style":"WR-friendly · wide zone run game · play-action",
     "impact":"POSITIVE","note":"McDaniel joins as offensive coordinator/play-caller under HC Jim Harbaugh — not a head coaching hire, but he brings the same scheme that made Miami's passing game explosive. Justin Herbert and the Chargers' receiving corps should benefit.",
     "up":["Justin Herbert","Ladd McConkey"],"down":[]},
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

# ── 2026 OFFENSIVE PLAY CALLERS ─────────────────────────────────────────────────
# rank, team, play caller (who actually calls plays), and the other titled coach/OC
PLAY_CALLERS = [
    (1,  "LA Rams",       "Sean McVay",             "Nate Scheelhaase (OC)"),
    (2,  "San Francisco", "Kyle Shanahan",          "Klay Kubiak (OC)"),
    (3,  "Chicago",       "Ben Johnson",            "Press Taylor (OC)"),
    (4,  "Denver",        "Sean Payton",            "Davis Webb (OC)"),
    (5,  "Jacksonville",  "Liam Coen",              "Grant Udinski (OC)"),
    (6,  "New England",   "Josh McDaniels (OC)",    "Mike Vrabel"),
    (7,  "Kansas City",   "Andy Reid",              "Eric Bieniemy (OC)"),
    (8,  "Minnesota",     "Kevin O'Connell",        "Wes Phillips (OC)"),
    (9,  "Green Bay",     "Matt LaFleur",           "Adam Stenavich (OC)"),
    (10, "Indianapolis",  "Shane Steichen",         "Jim Bob Cooter (OC)"),
    (11, "LA Chargers",   "Mike McDaniel (OC)",     "Jim Harbaugh"),
    (12, "New Orleans",   "Kellen Moore",           "Doug Nussmeier (OC)"),
    (13, "Dallas",        "Brian Schottenheimer",   "Klayton Adams (OC)"),
    (14, "Las Vegas",     "Klint Kubiak",           "Andrew Janocko (OC)"),
    (15, "Cleveland",     "Todd Monken",            "Travis Switzer (OC)"),
    (16, "Tennessee",     "Brian Daboll (OC)",      "Robert Saleh"),
    (17, "Buffalo",       "Joe Brady",              "Pete Carmichael (OC)"),
    (18, "Cincinnati",    "Zac Taylor",             "Dan Pitcher (OC)"),
    (19, "Carolina",      "Dave Canales",           "Brad Idzik (OC)"),
    (20, "Atlanta",       "Tommy Rees (OC)",        "Kevin Stefanski"),
    (21, "Tampa Bay",     "Zac Robinson (OC)",      "Todd Bowles"),
    (22, "Pittsburgh",    "Mike McCarthy",          "Brian Angelichio (OC)"),
    (23, "Houston",       "Nick Caley (OC)",        "DeMeco Ryans"),
    (24, "Detroit",       "Drew Petzing (OC)",      "Dan Campbell"),
    (25, "Seattle",       "Brian Fleury (OC)",      "Mike Macdonald"),
    (26, "Arizona",       "Mike LaFleur",           "Nathaniel Hackett (OC)"),
    (27, "Miami",         "Bobby Slowik (OC)",      "Jeff Hafley"),
    (28, "Philadelphia",  "Sean Mannion (OC)",      "Nick Sirianni"),
    (29, "Baltimore",     "Declan Doyle (OC)",      "Jesse Minter"),
    (30, "Washington",    "David Blough (OC)",      "Dan Quinn"),
    (31, "NY Jets",       "Frank Reich (OC)",       "Aaron Glenn"),
    (32, "NY Giants",     "Matt Nagy (OC)",         "John Harbaugh"),
]

# ── 2026 O-LINE CONSENSUS RANKINGS ───────────────────────────────────────────────
# rank, team abbr, team name, consensus avg score (lower = better; averaged across major preseason O-line rankings)
OLINE_DATA = [
    (1,  "DEN", "Broncos",     1.0),  (2,  "PHI", "Eagles",      2.5),
    (3,  "LAR", "Rams",        3.8),  (4,  "CHI", "Bears",       4.5),
    (5,  "TB",  "Buccaneers",  6.3),  (6,  "SF",  "49ers",       6.8),
    (7,  "BUF", "Bills",       7.3),  (8,  "CAR", "Panthers",    8.0),
    (9,  "LAC", "Chargers",   12.0),  (10, "IND", "Colts",      12.8),
    (11, "ATL", "Falcons",   13.3),  (12, "MIN", "Vikings",    13.8),
    (13, "NE",  "Patriots",  14.8),  (14, "SEA", "Seahawks",   14.8),
    (15, "DAL", "Cowboys",   15.0),  (16, "DET", "Lions",      16.3),
    (17, "NYJ", "Jets",      17.0),  (18, "NYG", "Giants",     17.5),
    (19, "PIT", "Steelers",  18.0),  (20, "ARI", "Cardinals",  19.3),
    (21, "KC",  "Chiefs",    19.3),  (22, "NO",  "Saints",     20.0),
    (23, "JAX", "Jaguars",   21.0),  (24, "LV",  "Raiders",    21.5),
    (25, "WAS", "Commanders",22.3),  (26, "BAL", "Ravens",     23.8),
    (27, "GB",  "Packers",   28.0),  (28, "CIN", "Bengals",    28.5),
    (29, "HOU", "Texans",    28.8),  (30, "MIA", "Dolphins",   29.5),
    (31, "TEN", "Titans",    29.8),  (32, "CLE", "Browns",     30.5),
]

# ── 2025 O-LINE RUN BLOCK RATING (prior season's board, kept under the 2025 tab) ──
# 2025 OL rank, team abbr, trend, cohesion (1-5), projected '26 rank, QB-runs flag
OLINE_2025_DATA = [
    (1,  "LAR", "down",  4, 4.5, False), (2,  "BUF", "down",  4, 4.5, True),
    (3,  "CHI", "down",  4, 4.0, False), (4,  "DEN", "flat",  5, 5.0, True),
    (5,  "IND", "flat",  4, 4.5, False), (6,  "SF",  "flat",  4, 4.0, False),
    (7,  "JAX", "flat",  5, 4.0, True),  (8,  "DAL", "flat",  5, 4.0, False),
    (9,  "MIN", "up",    4, 4.0, True),  (10, "SEA", "flat",  5, 3.5, False),
    (11, "BAL", "down",  2, 3.0, True),  (12, "PIT", "up",    3, 3.5, False),
    (13, "NE",  "flat",  4, 3.0, False), (14, "PHI", "flat",  5, 4.0, True),
    (15, "DET", "flat",  3, 3.5, False), (16, "CAR", "down",  3, 3.0, False),
    (17, "NYJ", "flat",  4, 3.0, False), (18, "NYG", "up",    4, 3.0, True),
    (19, "CIN", "flat",  5, 3.0, False), (20, "GB",  "down",  3, 2.0, False),
    (21, "ATL", "up",    4, 4.0, False), (22, "KC",  "flat",  4, 3.0, False),
    (23, "ARI", "up",    2, 3.0, False), (24, "WAS", "down",  3, 2.0, True),
    (25, "TEN", "flat",  3, 2.0, False), (26, "TB",  "up2",   5, 4.0, False),
    (27, "CLE", "up",    1, 2.0, False), (28, "LV",  "up2",   3, 2.5, False),
    (29, "HOU", "up",    2, 3.0, False), (30, "NO",  "up",    4, 3.0, True),
    (31, "MIA", "up",    4, 2.5, True),  (32, "LAC", "up2",   2, 3.0, False),
]

# ── DRAFT NOTES DATA (kept from prior build) ────────────────────────────────────
MUST_DRAFT = {
    "Early Round (1-3)":  ["Omarion Hampton","Ashton Jeanty","Malik Nabers","Chase Brown","James Cook III","Brock Bowers","De'Von Achane"],
    "Mid Round (4-7)":    ["Ladd McConkey","TreVeyon Henderson","Cam Skattebo","Christian Watson","Emeka Egbuka","Justin Herbert","Bhayshul Tuten","Javonte Williams","DeVonta Smith"],
    "Late Round (8+)":    ["Tucker Kraft","Jadarian Price","George Kittle"],
}
MUST_AVOID = {
    "Early Round (1-3)":  ["Trey McBride","Christian McCaffrey","Jeremiyah Love","George Pickens"],
    "Mid Round (4-7)":    ["Davante Adams","Tyler Warren","Bucky Irving"],
    "Late Round (8+)":    ["Dallas Goedert","Khalil Shakir","Jacory Croskey-Merritt","Calvin Ridley"],
}
TARGET_PICKS = {
    "Round 1":  ["Bijan Robinson","Jahmyr Gibbs","Puka Nacua","Amon-Ra St. Brown","James Cook III"],
    "Round 2":  ["Omarion Hampton","De'Von Achane","Chase Brown","Brock Bowers"],
    "Round 3":  ["Chris Olave","Malik Nabers","Javonte Williams"],
    "Round 4":  ["Cam Skattebo","Ladd McConkey","Emeka Egbuka","Tetairoa McMillan","DeVonta Smith"],
    "Round 5":  ["Rome Odunze","Bhayshul Tuten","Quinshon Judkins"],
    "Round 6":  ["Parker Washington","Christian Watson","Jalen Hurts","Carnell Tate","Mike Evans"],
    "Round 7":  ["Justin Herbert","Tucker Kraft"],
    "Round 8":  ["Tucker Kraft","Sam LaPorta","Michael Wilson"],
    "Round 9":  ["J.K. Dobbins","Michael Pittman Jr.","Kenneth Gainwell","Josh Downs"],
    "Round 10": ["Matthew Golden","George Kittle"],
    "Round 11": ["KC Concepcion","Aaron Jones Sr.","Isaiah Likely"],
}
UNDERVALUED = [
    {"name":"Javonte Williams","pos":"RB","proj_rank":"RB18","adp":"4.01","team":"DAL",
     "bullets":["7th easiest SOS for 2026","Improved offense & defense · no backfield competition"]},
    {"name":"Omarion Hampton","pos":"RB","proj_rank":"RB9","adp":"2.03","team":"LAC",
     "bullets":["McDaniel's produced a top-3 fantasy RB each of the last 3 years","Improved O-line · prime scheme","Averaged 20+ pts/game before injury"]},
    {"name":"Rome Odunze","pos":"WR","proj_rank":"WR27","adp":"5.09","team":"CHI",
     "bullets":["Injured mid-season — depressed ADP","WR7 in expected PPG · 9th in Snap%"]},
    {"name":"Parker Washington","pos":"WR","proj_rank":"WR35","adp":"7.03","team":"JAC",
     "bullets":["OTA WR1 · Chris Godwin slot role","Jags' leader in receptions & targets","12th best YPRR at 2.57 yards"]},
    {"name":"Emeka Egbuka","pos":"WR","proj_rank":"WR20","adp":"4.06","team":"TB",
     "bullets":["Lowest catchable target % — massive upside","9th in targets · 2nd in deep targets"]},
    {"name":"Cam Skattebo","pos":"RB","proj_rank":"RB20","adp":"4.09","team":"NYG",
     "bullets":["John Harbaugh's run-first scheme — massive upgrade","No backfield competition"]},
]

# ── DATA LOADING ──────────────────────────────────────────────────────────────
POS_FILES = {"QB":"qb_stats.csv","RB":"rb_stats.csv","WR":"wr_stats.csv","TE":"te_stats.csv"}

def _read(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

def load_year(year):
    d = os.path.join(DATA_DIR, str(year))
    out = {}
    for pos, f in POS_FILES.items():
        out[pos] = _read(os.path.join(d, f))
    out["SOS"] = _read(os.path.join(d, "sos_by_team.csv"))
    out["ANALYTICS"] = _read(os.path.join(d, "team_analytics.csv"))
    return out

def load_2026():
    b = os.path.join(DATA_DIR, "2026")
    return _read(os.path.join(b, "master_rankings.csv")), _read(os.path.join(b, "sos_2026.csv"))

master, sos_2026 = load_2026()
data_2025 = load_year(2025)
data_2024 = load_year(2024)

def get_data(season): return data_2025 if int(season) == 2025 else data_2024

# ── STAT TABLE PREP ───────────────────────────────────────────────────────────
def prep_position_df(df, pos):
    """Return a trimmed, display-ready dataframe for a position's PPR rankings table."""
    if df.empty:
        return df
    d = df.copy()
    def col(name):
        return d[name].fillna(0) if name in d.columns else 0
    if pos == "QB":
        d["total_tds"] = col("passing_tds") + col("rushing_tds")
        keep = ["player_display_name", "recent_team", "games", "fantasy_points_ppr",
                "fppg_ppr", "passing_yards", "total_tds", "interceptions"]
    else:
        d["total_yards"] = col("rushing_yards") + col("receiving_yards")
        d["total_tds"] = col("rushing_tds") + col("receiving_tds")
        keep = ["player_display_name", "recent_team", "games", "fantasy_points_ppr",
                "fppg_ppr", "total_yards", "total_tds"]
    keep = [c for c in keep if c in d.columns]
    d = d[keep].sort_values("fantasy_points_ppr", ascending=False).reset_index(drop=True)
    d.insert(0, "rk", d.index + 1)
    d["fantasy_points_ppr"] = d["fantasy_points_ppr"].round(1)
    d["fppg_ppr"] = d["fppg_ppr"].round(1)
    return d

def prep_overall_df(data):
    """Combine QB/RB/WR/TE into one all-positions table ranked by total fantasy points."""
    def col0(frame, name):
        return frame[name].fillna(0) if name in frame.columns else pd.Series(0, index=frame.index)

    frames = []
    for pos in ["QB", "RB", "WR", "TE"]:
        d = data.get(pos)
        if d is None or d.empty:
            continue
        dd = d.copy()
        dd["total_yards"] = col0(dd, "passing_yards") + col0(dd, "rushing_yards") + col0(dd, "receiving_yards")
        dd["total_tds"] = col0(dd, "passing_tds") + col0(dd, "rushing_tds") + col0(dd, "receiving_tds")
        dd["position"] = pos
        keep = [c for c in ["player_display_name", "recent_team", "position", "games",
                             "fantasy_points_ppr", "fppg_ppr", "total_yards", "total_tds"] if c in dd.columns]
        frames.append(dd[keep])

    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("fantasy_points_ppr", ascending=False).reset_index(drop=True)
    out.insert(0, "rk", out.index + 1)
    out["fantasy_points_ppr"] = out["fantasy_points_ppr"].round(1)
    out["fppg_ppr"] = out["fppg_ppr"].round(1)
    return out

# ── AG GRID HELPERS ───────────────────────────────────────────────────────────
DGRID = {"suppressMovableColumns": True, "suppressCellFocus": True, "animateRows": False}
DCOL  = {"sortable": True, "resizable": True, "filter": False, "suppressMenu": True,
         "cellDataType": False, "cellStyle": {"color": TEXT}}

def make_grid(gid, records, col_defs, height=560):
    return dag.AgGrid(id=gid, rowData=records, columnDefs=col_defs,
                       defaultColDef=DCOL, dashGridOptions=DGRID,
                       dangerously_allow_code=True,
                       className="ag-theme-alpine-dark",
                       style={"height": f"{height}px", "width": "100%"})

def heat_style(col, invert=False):
    sign = "1-" if invert else ""
    return {"function": f"""(function(p){{
        var v=parseFloat(p.value); if(isNaN(v)) return {{}};
        var all=p.api.getRenderedNodes().map(n=>parseFloat(n.data['{col}'])).filter(x=>!isNaN(x));
        var mn=Math.min(...all), mx=Math.max(...all);
        var r=(v-mn)/((mx-mn)||1); r=({sign}Math.max(0,Math.min(1,r)));
        var red=Math.round(210*(1-r)), grn=Math.round(160*r+50);
        return {{color:'rgb('+red+','+grn+',90)',fontWeight:'700'}};
    }})(params)"""}

def pos_style_js():
    c = POS_C
    return {"function": f"""(function(p){{
        var c={{"QB":"{c['QB']}","RB":"{c['RB']}","WR":"{c['WR']}","TE":"{c['TE']}","DST":"{c.get('DST','#94a3b8')}","K":"{c.get('K','#facc15')}"}};
        return {{color:c[p.value]||"{TEXT}",fontWeight:"700"}};
    }})(params)"""}

def stat_table_grid(gid, df, height=600):
    rn = df.rename(columns=COL_LABELS)
    defs = []
    for c in rn.columns:
        d = {"field": c, "headerName": c, "sortable": True, "resizable": True, "flex": 1, "minWidth": 100}
        if c == "rk":
            d.update({"headerName": "#", "pinned": "left", "width": 56, "minWidth": 56, "flex": 0, "sortable": True,
                       "cellStyle": {"color": TFAINT, "fontFamily": FONT_MONO}})
        elif c == "Player":
            d.update({"pinned": "left", "width": 200, "minWidth": 200, "flex": 0,
                      "cellStyle": {"fontWeight": "700", "color": ACCENT, "cursor": "pointer", "textDecoration": "underline"}})
        elif c == "Team":
            d.update({"width": 90, "minWidth": 90, "flex": 0, "cellStyle": {"color": TDIM, "fontFamily": FONT_MONO, "fontWeight": "600"}})
        elif c in ("Total PPR", "FPPG"):
            d["cellStyle"] = heat_style(c)
        defs.append(d)
    return make_grid(gid, rn.to_dict("records"), defs, height)

# ── UI HELPERS ────────────────────────────────────────────────────────────────
def sec(txt, sub=None, mt=0):
    kids = [html.Div(txt, className="sec-label")]
    if sub:
        kids.append(html.Div(sub, className="sec-sub"))
    return html.Div(kids, style={"marginTop": f"{mt}px"})

def stat_card(val, lbl):
    return html.Div([html.Div(str(val), className="card-val"), html.Div(lbl, className="card-lbl")],
                     className="stat-card")

def tab_style(sel=False):
    return {"fontFamily": FONT_HEAD, "fontSize": "12.5px", "fontWeight": "600", "letterSpacing": ".02em",
            "color": ACCENT if sel else TDIM, "padding": "11px 16px", "border": "none",
            "borderBottom": f"2px solid {ACCENT}" if sel else "2px solid transparent",
            "background": "transparent", "cursor": "pointer", "whiteSpace": "nowrap"}

def ctrl(label, child):
    return html.Div([html.Div(label, className="ctrl-lbl"), child])

def dd_style(width="140px"):
    return {"width": width, "background": SURF, "color": TEXT, "border": f"1px solid {BORDER}",
            "borderRadius": "8px", "fontSize": "12.5px"}

def empty_msg(msg="No data available yet — run the data pipeline first."):
    return html.Div(msg, style={"color": TFAINT, "fontSize": "12.5px", "padding": "40px", "textAlign": "center"})

# ── LAYOUT ────────────────────────────────────────────────────────────────────
_ts = lambda: tab_style(False)
_tsa = lambda: tab_style(True)

app.layout = html.Div([
    html.Div([
        # Header
        html.Div([
            html.Div([
                html.Span("FANTASY", style={"color": TEXT}),
                html.Span("EDGE", style={"color": ACCENT}),
            ], style={"fontFamily": FONT_HEAD, "fontSize": "1.9rem", "fontWeight": "800", "letterSpacing": "-.02em"}),
            html.Div("NFL player analytics & rankings", style={"fontSize": "12.5px", "color": TFAINT, "marginTop": "2px"}),
        ], style={"padding": "24px 0 18px"}),

        # Season selector
        dcc.RadioItems(id="season",
            options=[{"label": "2026", "value": "2026"}, {"label": "2025", "value": "2025"}, {"label": "2024", "value": "2024"}],
            value="2026", inline=True, inputStyle={"display": "none"},
            labelStyle={"display": "inline-flex"},
            style={"marginBottom": "16px"}),
        html.Div(id="season-pills", style={"display": "flex", "gap": "8px", "marginBottom": "18px"}),

        html.Div(id="badge", style={"marginBottom": "14px"}),
        html.Div(id="stat-cards", style={"display": "flex", "gap": "10px", "marginBottom": "18px"}),

        # 2026 view
        html.Div(id="v2026", children=[
            dcc.Tabs(id="t2026", value="qb26", children=[
                dcc.Tab(label="Rankings", value="rankings26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Draft Sim", value="draftsim26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="QB", value="qb26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="RB", value="rb26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="WR", value="wr26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TE", value="te26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="SOS", value="sos26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Play Callers", value="playcallers", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="O-Line", value="oline", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Draft Notes", value="draft", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Coaching", value="coaching", style=_ts(), selected_style=_tsa()),
            ], colors={"border": BORDER, "primary": ACCENT, "background": "transparent"},
               style={"borderBottom": f"1px solid {BORDER}"}),
            html.Div(id="c2026", style={"paddingTop": "18px"}),
        ]),

        # Historical view (2025 / 2024)
        html.Div(id="vhist", style={"display": "none"}, children=[
            dcc.Tabs(id="thist", value="qb-h", children=[
                dcc.Tab(label="Overall", value="overall-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="QB", value="qb-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="RB", value="rb-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="WR", value="wr-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TE", value="te-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Team Splits", value="splits", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="SOS", value="sos-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="O-Line", value="oline-h", style=_ts(), selected_style=_tsa()),
            ], colors={"border": BORDER, "primary": ACCENT, "background": "transparent"},
               style={"borderBottom": f"1px solid {BORDER}"}),
            html.Div(id="chist", style={"paddingTop": "18px"}),
        ]),

    ], className="app-shell", style={"padding": "0 24px 60px"}),

    # Player profile modal
    html.Div(id="player-modal-overlay", style={"display": "none"}, children=[
        html.Div([
            html.Button("×", id="modal-close-btn", n_clicks=0, style={
                "position": "absolute", "top": "12px", "right": "16px", "background": "transparent",
                "border": "none", "color": TDIM, "fontSize": "1.6rem", "cursor": "pointer", "lineHeight": "1"}),
            html.Div(id="player-modal-body"),
        ], style={"background": SURF, "border": f"1px solid {BORDER}", "borderRadius": "12px",
                   "padding": "28px", "maxWidth": "760px", "width": "92%", "maxHeight": "85vh",
                   "overflowY": "auto", "position": "relative"}),
    ]),

    # Draft Sim state — list of drafted player names, persists across tab/season switches
    dcc.Store(id="draftsim-store", storage_type="session", data=[]),

], style={"minHeight": "100vh", "background": BG})

# ── SEASON PILLS + TOGGLE ─────────────────────────────────────────────────────
@app.callback(Output("season-pills", "children"), Input("season", "value"))
def render_pills(s):
    opts = ["2026", "2025", "2024"]
    return [html.Button(o, id={"type": "season-pill", "index": o}, n_clicks=0,
                         className=f"season-pill{' sel' if o == s else ''}") for o in opts]

@app.callback(Output("season", "value"),
              Input({"type": "season-pill", "index": "2026"}, "n_clicks"),
              Input({"type": "season-pill", "index": "2025"}, "n_clicks"),
              Input({"type": "season-pill", "index": "2024"}, "n_clicks"),
              prevent_initial_call=True)
def pick_season(a, b, c):
    trig = ctx.triggered_id
    if trig: return trig["index"]
    return "2026"

@app.callback(
    Output("v2026", "style"), Output("vhist", "style"),
    Output("badge", "children"), Output("stat-cards", "children"),
    Input("season", "value"),
)
def toggle_season(s):
    if s == "2026":
        badge = html.Span("2026 · PRESEASON CONSENSUS RANKINGS", className="badge")
        return {"display": "block"}, {"display": "none"}, badge, []
    badge = html.Span(f"{s} · REGULAR SEASON STATS", className="badge")
    data = get_data(s)
    cards = [stat_card(len(data[p]) if not data[p].empty else 0, lbl)
             for p, lbl in [("QB", "Quarterbacks"), ("RB", "Running Backs"), ("WR", "Wide Receivers"), ("TE", "Tight Ends")]]
    return {"display": "none"}, {"display": "block"}, badge, cards

# ── 2026 TABS ─────────────────────────────────────────────────────────────────
@app.callback(Output("c2026", "children"), Input("t2026", "value"))
def render_2026(tab):
    pos_map = {"qb26": "QB", "rb26": "RB", "wr26": "WR", "te26": "TE"}

    if tab == "rankings26":
        if master.empty: return empty_msg()
        df = master.copy()
        keep = [c for c in ["consensus_rank", "player", "position", "team", "consensus_pos_rank"] if c in df.columns]
        df = df[keep].sort_values("consensus_rank")
        rn = df.rename(columns=COL_LABELS).rename(columns={"Consensus Rank": "Rank", "Pos": "Position", "Pos Rank": "Consensus Pos Rank"})
        defs = []
        for c in rn.columns:
            d = {"field": c, "headerName": c, "sortable": True, "resizable": True, "flex": 1, "minWidth": 100}
            if c == "Player": d.update({"pinned": "left", "width": 200, "minWidth": 200, "flex": 0, "cellStyle": {"fontWeight": "700", "color": TEXT}})
            if c == "Rank": d.update({"width": 70, "minWidth": 70, "flex": 0, "cellStyle": {"color": TFAINT, "fontFamily": FONT_MONO}})
            if c == "Position": d.update({"width": 90, "minWidth": 90, "flex": 0})
            defs.append(d)
        return html.Div([
            sec("2026 Consensus PPR Rankings · Overall",
                sub="All positions ranked together, following Flock Fantasy's exact overall order. Click a column to sort."),
            make_grid("g-rankings26", rn.fillna("—").to_dict("records"), defs, 600),
        ])

    if tab == "draftsim26":
        if master.empty: return empty_msg()
        return html.Div([
            html.Div([
                sec("2026 Draft Sim · Big Board",
                    sub="All positions ranked together, following Flock Fantasy's exact overall order. Click the ✕ when a player is drafted to remove them from the board — the top remaining player is always your best player available."),
                html.Button("Reset Board", id={"type": "draftsim-reset", "index": 0}, n_clicks=0, style={
                    "background": SURF2, "border": f"1px solid {BORDER}", "color": TEXT,
                    "borderRadius": "8px", "padding": "9px 16px", "fontSize": "12.5px", "fontWeight": "600",
                    "cursor": "pointer", "whiteSpace": "nowrap", "height": "fit-content", "marginTop": "2px"}),
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start", "gap": "16px"}),
            html.Div(id="draftsim-board", style={"marginTop": "18px"}),
        ])

    if tab in pos_map:
        if master.empty: return empty_msg()
        pos = pos_map[tab]
        df = master.copy()
        if "position" in df.columns:
            df = df[df["position"] == pos]
        keep = [c for c in ["consensus_rank", "player", "team", "consensus_pos_rank"] if c in df.columns]
        df = df[keep].sort_values("consensus_rank")
        rn = df.rename(columns=COL_LABELS).rename(columns={"Consensus Rank": "Rank", "Pos Rank": "Consensus Pos Rank"})
        defs = []
        for c in rn.columns:
            d = {"field": c, "headerName": c, "sortable": True, "resizable": True, "flex": 1, "minWidth": 100}
            if c == "Player": d.update({"pinned": "left", "width": 200, "minWidth": 200, "flex": 0, "cellStyle": {"fontWeight": "700", "color": TEXT}})
            if c == "Rank": d.update({"width": 70, "minWidth": 70, "flex": 0, "cellStyle": {"color": TFAINT, "fontFamily": FONT_MONO}})
            defs.append(d)
        label = {"QB": "Quarterbacks", "RB": "Running Backs", "WR": "Wide Receivers", "TE": "Tight Ends"}[pos]
        return html.Div([
            sec(f"2026 Consensus PPR Rankings · {label}",
                sub="Preseason rankings — real season stats populate once games are played. Click a column to sort."),
            make_grid(f"g-{tab}", rn.fillna("—").to_dict("records"), defs, 600),
        ])

    if tab == "sos26":
        if sos_2026.empty: return empty_msg()
        return html.Div([
            sec("2026 Strength of Schedule"),
            ctrl("Position", dcc.Dropdown(id="sos26-pos",
                options=[{"label": p, "value": p} for p in ["QB", "RB", "WR", "TE"]], value="RB",
                clearable=False, style=dd_style())),
            html.Div(id="sos26-c", style={"marginTop": "14px"}),
        ])

    if tab == "draft":
        return html.Div([
            sec("Draft Notes · 2026"),
            html.Div([
                html.Button("Must Drafts & Avoids", id="btn-must", n_clicks=0, className="toggle-btn active"),
                html.Button("Target Picks", id="btn-target", n_clicks=0, className="toggle-btn"),
                html.Button("Undervalued Players", id="btn-uv", n_clicks=0, className="toggle-btn"),
            ], style={"marginBottom": "18px"}),
            html.Div(id="draft-c", children=_render_must()),
        ])

    if tab == "playcallers":
        return _render_playcallers()

    if tab == "oline":
        return _render_oline()

    if tab == "coaching":
        return _render_coaching()

    return html.Div()

# ── DRAFT SIM ─────────────────────────────────────────────────────────────────
@app.callback(Output("draftsim-board", "children"), Input("draftsim-store", "data"))
def render_draftsim_board(drafted):
    if master.empty: return empty_msg()
    drafted_set = set(drafted or [])
    df = master.copy()
    df = df[~df["player"].isin(drafted_set)].sort_values("consensus_rank")

    header = html.Div([
        html.Div("RANK", style={"width": "60px", "flex": "0 0 auto"}),
        html.Div("PLAYER", style={"flex": "1 1 auto"}),
        html.Div("POS", style={"width": "70px", "flex": "0 0 auto"}),
        html.Div("TEAM", style={"width": "70px", "flex": "0 0 auto"}),
        html.Div("POS RANK", style={"width": "90px", "flex": "0 0 auto"}),
        html.Div("", style={"width": "50px", "flex": "0 0 auto"}),
    ], style={"display": "flex", "alignItems": "center", "padding": "10px 16px",
              "borderBottom": f"1px solid {BORDER}", "color": TFAINT, "fontSize": "11px",
              "fontWeight": "700", "letterSpacing": ".05em"})

    if df.empty:
        rows = [html.Div("All players drafted — hit Reset Board to start over.",
                          style={"color": TFAINT, "fontSize": "12.5px", "padding": "40px", "textAlign": "center"})]
    else:
        rows = []
        for i, (_, r) in enumerate(df.iterrows()):
            best = i == 0
            pos = r.get("position", "")
            rows.append(html.Div([
                html.Div(str(int(r["consensus_rank"])) if pd.notna(r.get("consensus_rank")) else "—",
                          style={"width": "60px", "flex": "0 0 auto", "color": TFAINT, "fontFamily": FONT_MONO}),
                html.Div(r["player"], style={"flex": "1 1 auto", "fontWeight": "700",
                                              "color": ACCENT if best else TEXT}),
                html.Div(pos, style={"width": "70px", "flex": "0 0 auto", "fontWeight": "700",
                                      "color": POS_C.get(pos, TEXT)}),
                html.Div(r.get("team", "—") or "—", style={"width": "70px", "flex": "0 0 auto", "color": TDIM, "fontFamily": FONT_MONO}),
                html.Div(r.get("consensus_pos_rank", "—") or "—", style={"width": "90px", "flex": "0 0 auto", "color": TDIM, "fontFamily": FONT_MONO}),
                html.Div(
                    html.Button("✕", id={"type": "draftsim-x", "player": r["player"]}, n_clicks=0, style={
                        "background": "transparent", "border": f"1px solid {BORDER}", "color": RED,
                        "borderRadius": "6px", "width": "30px", "height": "30px", "cursor": "pointer",
                        "fontSize": "13px", "fontWeight": "700", "lineHeight": "1"}),
                    style={"width": "50px", "flex": "0 0 auto"}),
            ], style={"display": "flex", "alignItems": "center", "padding": "9px 16px",
                      "borderBottom": f"1px solid {BORDER}",
                      "background": "rgba(45,212,191,0.06)" if best else "transparent"}))

    return html.Div([
        html.Div(f"{len(df)} players remaining · {len(drafted_set)} drafted", style={
            "color": TFAINT, "fontSize": "12px", "marginBottom": "10px"}),
        html.Div([header, html.Div(rows, style={"maxHeight": "600px", "overflowY": "auto"})],
                  style={"background": SURF, "border": f"1px solid {BORDER}", "borderRadius": "10px", "overflow": "hidden"}),
    ])

@app.callback(
    Output("draftsim-store", "data"),
    Input({"type": "draftsim-x", "player": ALL}, "n_clicks"),
    Input({"type": "draftsim-reset", "index": ALL}, "n_clicks"),
    State("draftsim-store", "data"),
    prevent_initial_call=True,
)
def update_draftsim(x_clicks, reset_clicks, drafted):
    trig = ctx.triggered_id
    if trig is None or not isinstance(trig, dict):
        return no_update
    if trig.get("type") == "draftsim-reset":
        return []
    if trig.get("type") == "draftsim-x":
        val = ctx.triggered[0]["value"] if ctx.triggered else None
        if not val:  # ignore the initial render (n_clicks None/0)
            return no_update
        drafted = list(drafted or [])
        player = trig.get("player")
        if player and player not in drafted:
            drafted.append(player)
        return drafted
    return no_update

# ── HISTORICAL TABS ───────────────────────────────────────────────────────────
@app.callback(Output("chist", "children"), Input("thist", "value"), Input("season", "value"))
def render_hist(tab, season_str):
    if season_str == "2026": return html.Div()
    data = get_data(season_str)

    if tab == "overall-h":
        df = prep_overall_df(data)
        if df.empty: return empty_msg()
        rn = df.rename(columns=COL_LABELS)
        defs = []
        for c in rn.columns:
            d = {"field": c, "headerName": c, "sortable": True, "resizable": True, "flex": 1, "minWidth": 100}
            if c == "rk":
                d.update({"headerName": "#", "pinned": "left", "width": 56, "minWidth": 56, "flex": 0, "sortable": True,
                           "cellStyle": {"color": TFAINT, "fontFamily": FONT_MONO}})
            elif c == "Player":
                d.update({"pinned": "left", "width": 200, "minWidth": 200, "flex": 0,
                          "cellStyle": {"fontWeight": "700", "color": TEXT}})
            elif c == "Pos":
                d.update({"width": 80, "minWidth": 80, "flex": 0, "cellStyle": pos_style_js()})
            elif c == "Team":
                d.update({"width": 90, "minWidth": 90, "flex": 0, "cellStyle": {"color": TDIM, "fontFamily": FONT_MONO, "fontWeight": "600"}})
            elif c in ("Total PPR", "FPPG"):
                d["cellStyle"] = heat_style(c)
            defs.append(d)
        return html.Div([
            sec(f"Overall PPR Rankings · {season_str}",
                sub="All positions ranked together by total fantasy points. Click a column header to sort."),
            make_grid("g-overall-h", rn.fillna("—").to_dict("records"), defs, 640),
        ])

    pos_map = {"qb-h": "QB", "rb-h": "RB", "wr-h": "WR", "te-h": "TE"}
    if tab in pos_map:
        pos = pos_map[tab]
        df = prep_position_df(data[pos], pos)
        if df.empty: return empty_msg()
        label = {"QB": "Quarterback", "RB": "Running Back", "WR": "Wide Receiver", "TE": "Tight End"}[pos]
        return html.Div([
            sec(f"{label} PPR Rankings · {season_str}", sub="Click a column header to sort — click a player's name for their advanced profile."),
            stat_table_grid({"type": "hist-grid", "pos": pos}, df, 600),
        ])

    if tab == "splits":
        df = data["ANALYTICS"]
        if df.empty:
            return html.Div([sec(f"Team Splits · {season_str}"), empty_msg("Team splits data not available for this season.")])
        d = df[["team", "pass_rate", "run_rate", "third_down_pct", "rz_conv_pct"]].copy() if all(
            c in df.columns for c in ["team", "pass_rate", "run_rate", "third_down_pct", "rz_conv_pct"]) else df.copy()
        d = d.sort_values("pass_rate", ascending=False)
        rn = d.rename(columns=COL_LABELS)
        defs = []
        for c in rn.columns:
            dd = {"field": c, "headerName": c, "sortable": True, "resizable": True, "flex": 1, "minWidth": 110}
            if c == "Team": dd.update({"pinned": "left", "width": 90, "minWidth": 90, "flex": 0, "cellStyle": {"fontWeight": "700", "color": TEXT, "fontFamily": FONT_MONO}})
            else: dd["cellStyle"] = heat_style(c)
            defs.append(dd)
        return html.Div([
            sec(f"Team Splits · {season_str}", sub="Pass/run tendency and conversion efficiency by team. Click a column to sort."),
            make_grid("g-splits", rn.to_dict("records"), defs, 620),
        ])

    if tab == "sos-h":
        df = data["SOS"]
        if df.empty: return empty_msg()
        return html.Div([
            sec(f"Strength of Schedule · {season_str}"),
            ctrl("Position", dcc.Dropdown(id="sos-h-pos",
                options=[{"label": p, "value": p} for p in ["QB", "RB", "WR", "TE"]], value="RB",
                clearable=False, style=dd_style())),
            html.Div(id="sos-h-c", style={"marginTop": "14px"}),
        ])

    if tab == "oline-h":
        return _render_oline_hist(season_str)

    return html.Div()

# ── PLAYER ADVANCED PROFILE ─────────────────────────────────────────────────────
def _stat_tile(label, value, color=None):
    return html.Div([
        html.Div(str(value), style={"fontSize": "1.15rem", "fontWeight": "700",
                                     "color": color or TEXT, "fontFamily": FONT_MONO}),
        html.Div(label, style={"fontSize": "10px", "color": TFAINT, "letterSpacing": ".04em", "marginTop": "2px"}),
    ], style={"background": SURF2, "border": f"1px solid {BORDER}", "borderRadius": "8px",
              "padding": "10px 12px", "minWidth": "104px"})

def _safe_div(num, den, decimals=2):
    try:
        num = float(num); den = float(den)
        return round(num / den, decimals) if den else None
    except (TypeError, ValueError):
        return None

def _pct_color(value, series):
    """Flock-style red-to-green heat color for value's percentile within series (higher = better)."""
    try:
        s = pd.to_numeric(series, errors="coerce").dropna()
        v = float(value)
    except (TypeError, ValueError):
        return None
    if len(s) < 4 or pd.isna(v):
        return None
    pct = (s < v).sum() / len(s)
    red = round(210 * (1 - pct))
    grn = round(160 * pct + 50)
    return f"rgb({red},{grn},90)"

def _render_player_profile(r, df, pos, season_str):
    pc = POS_C.get(pos, TEXT)
    ppr = r.get("fantasy_points_ppr")
    fppg = r.get("fppg_ppr")
    games = r.get("games")

    overview = [("GP", games), ("Total PPR", round(ppr, 1) if pd.notna(ppr) else "—"),
                ("FPPG", round(fppg, 1) if pd.notna(fppg) else "—")]
    if pos == "QB":
        overview += [("Pass Yds", int(r.get("passing_yards", 0) or 0)),
                     ("Pass TD", int(r.get("passing_tds", 0) or 0)),
                     ("INT", int(r.get("interceptions", 0) or 0)),
                     ("Rush Yds", int(r.get("rushing_yards", 0) or 0)),
                     ("Rush TD", int(r.get("rushing_tds", 0) or 0))]
    else:
        rush_yds = r.get("rushing_yards", 0) or 0
        rec_yds = r.get("receiving_yards", 0) or 0
        rush_tds = r.get("rushing_tds", 0) or 0
        rec_tds = r.get("receiving_tds", 0) or 0
        overview += [("Total Yds", int(rush_yds + rec_yds)), ("Total TD", int(rush_tds + rec_tds))]

    # Build comparison series (across all players at this position/season) for percentile coloring
    def col0(frame, name):
        return frame[name].fillna(0) if name in frame.columns else pd.Series(0, index=frame.index)
    cdf = df.copy()
    if "yards_per_target" in cdf.columns and not cdf["yards_per_target"].isna().all():
        cdf["_ryds_t"] = cdf["yards_per_target"]
    else:
        cdf["_ryds_t"] = col0(cdf, "receiving_yards") / col0(cdf, "targets").replace(0, pd.NA)
    cdf["_fpr"] = col0(cdf, "fantasy_points_ppr") / col0(cdf, "receptions").replace(0, pd.NA)
    cdf["_fpo"] = col0(cdf, "fantasy_points_ppr") / (col0(cdf, "targets") + col0(cdf, "carries")).replace(0, pd.NA)

    adv = []  # (label, display, raw_value, comparison_series)
    targets = r.get("targets")
    receptions = r.get("receptions")
    carries = r.get("carries")
    if pd.notna(r.get("target_share")):
        adv.append(("Target %", f"{round(r['target_share'] * 100, 1)}%", r["target_share"], cdf.get("target_share")))
    if pd.notna(r.get("avg_snap_pct")):
        adv.append(("Snap %", f"{round(r['avg_snap_pct'] * 100, 1)}%", r["avg_snap_pct"], cdf.get("avg_snap_pct")))
    if pd.notna(r.get("rz20_tgt")):
        adv.append(("<20 RZT", int(r["rz20_tgt"]), r["rz20_tgt"], cdf.get("rz20_tgt")))
    if pd.notna(r.get("rz10_tgt")):
        adv.append(("<10 RZT", int(r["rz10_tgt"]), r["rz10_tgt"], cdf.get("rz10_tgt")))
    if pd.notna(r.get("rz20_pct")):
        adv.append(("<20 RZT%", f"{round(r['rz20_pct'], 1)}%", r["rz20_pct"], cdf.get("rz20_pct")))
    if pd.notna(r.get("rz10_pct")):
        adv.append(("<10 RZT%", f"{round(r['rz10_pct'], 1)}%", r["rz10_pct"], cdf.get("rz10_pct")))
    if pd.notna(r.get("rz20_rush_att")):
        adv.append(("<20 Rush Att", int(r["rz20_rush_att"]), r["rz20_rush_att"], cdf.get("rz20_rush_att")))
    if pd.notna(r.get("rz10_rush_att")):
        adv.append(("<10 Rush Att", int(r["rz10_rush_att"]), r["rz10_rush_att"], cdf.get("rz10_rush_att")))
    if pd.notna(r.get("rz5_rush_att")):
        adv.append(("<5 Rush Att", int(r["rz5_rush_att"]), r["rz5_rush_att"], cdf.get("rz5_rush_att")))
    if pd.notna(r.get("rz20_rush_pct")):
        adv.append(("<20 Rush%", f"{round(r['rz20_rush_pct'], 1)}%", r["rz20_rush_pct"], cdf.get("rz20_rush_pct")))
    if pd.notna(r.get("rz10_rush_pct")):
        adv.append(("<10 Rush%", f"{round(r['rz10_rush_pct'], 1)}%", r["rz10_rush_pct"], cdf.get("rz10_rush_pct")))
    if pd.notna(r.get("rz5_rush_pct")):
        adv.append(("<5 Rush%", f"{round(r['rz5_rush_pct'], 1)}%", r["rz5_rush_pct"], cdf.get("rz5_rush_pct")))
    if pd.notna(r.get("rush_att_5plus")):
        adv.append(("5+ Yd Rush Att", int(r["rush_att_5plus"]), r["rush_att_5plus"], cdf.get("rush_att_5plus")))
    if pd.notna(targets):
        adv.append(("Targets", int(targets), targets, cdf.get("targets")))
    if pd.notna(receptions):
        adv.append(("Receptions", int(receptions), receptions, cdf.get("receptions")))
    ryds_t = r.get("yards_per_target")
    if pd.isna(ryds_t) and pd.notna(targets) and pd.notna(r.get("receiving_yards")):
        ryds_t = _safe_div(r["receiving_yards"], targets, 1)
    if ryds_t is not None and pd.notna(ryds_t):
        adv.append(("RYDS/T", round(ryds_t, 1), ryds_t, cdf.get("_ryds_t")))
    fpr = _safe_div(ppr, receptions, 2)
    if fpr is not None:
        adv.append(("FP/R", fpr, fpr, cdf.get("_fpr")))
    opportunities = (targets or 0) + (carries or 0) if pd.notna(targets) or pd.notna(carries) else None
    fpo = _safe_div(ppr, opportunities, 2) if opportunities else None
    if fpo is not None:
        adv.append(("FP/O", fpo, fpo, cdf.get("_fpo")))

    return html.Div([
        html.Div([
            html.Span(r.get("player_display_name", "—"), style={"fontSize": "1.4rem", "fontWeight": "800", "color": TEXT, "marginRight": "10px"}),
            html.Span(pos, style={"background": pc + "22", "border": f"1px solid {pc}55", "color": pc,
                                   "fontSize": "11px", "fontWeight": "700", "padding": "3px 9px", "borderRadius": "5px"}),
        ], style={"marginBottom": "4px"}),
        html.Div(f"{r.get('recent_team', '—')} · {season_str} season", style={"color": TDIM, "fontSize": "12.5px", "marginBottom": "20px"}),

        html.Div("OVERVIEW", style={"fontSize": "11px", "fontWeight": "700", "color": TFAINT, "letterSpacing": ".06em", "marginBottom": "10px"}),
        html.Div([_stat_tile(l, v) for l, v in overview], style={"display": "flex", "flexWrap": "wrap", "gap": "10px", "marginBottom": "24px"}),

        html.Div("ADVANCED", style={"fontSize": "11px", "fontWeight": "700", "color": ACCENT, "letterSpacing": ".06em", "marginBottom": "10px"}),
        html.Div([_stat_tile(l, disp, _pct_color(raw, series)) for l, disp, raw, series in adv],
                  style={"display": "flex", "flexWrap": "wrap", "gap": "10px"})
        if adv else html.Div("No advanced data available for this player.", style={"color": TFAINT, "fontSize": "12px"}),
    ])

@app.callback(
    Output("player-modal-overlay", "style"),
    Output("player-modal-body", "children"),
    Input({"type": "hist-grid", "pos": ALL}, "cellClicked"),
    Input("modal-close-btn", "n_clicks"),
    State("season", "value"),
    prevent_initial_call=True,
)
def toggle_player_modal(grid_clicks, close_click, season_str):
    hidden = {"display": "none"}
    visible = {"position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0,
               "background": "rgba(0,0,0,0.6)", "zIndex": 1000, "display": "flex",
               "alignItems": "center", "justifyContent": "center"}
    trig = ctx.triggered_id
    if trig is None or trig == "modal-close-btn" or not isinstance(trig, dict):
        return hidden, []

    pos = trig.get("pos")
    cell = ctx.triggered[0]["value"] if ctx.triggered else None
    if not cell or cell.get("colId") != "Player":
        return hidden, []

    player_name = cell.get("value")
    if not player_name or season_str == "2026":
        return hidden, []

    df = get_data(season_str)[pos]
    row = df[df["player_display_name"] == player_name]
    if row.empty:
        return hidden, []

    return visible, _render_player_profile(row.iloc[0], df, pos, season_str)

# ── SOS 2026 ──────────────────────────────────────────────────────────────────
@app.callback(Output("sos26-c", "children"), Input("sos26-pos", "value"))
def render_sos26(pos):
    if sos_2026.empty: return empty_msg()
    df = sos_2026[sos_2026["position"] == pos].sort_values("sos_2026_rank").copy()
    rn = {"team": "Team", "avg_opp_pts_allowed": "Avg PPR Pts Allowed", "sos_2026_rank": "SOS Rank", "difficulty": "Difficulty"}
    cols = [c for c in rn if c in df.columns]
    records = df[cols].rename(columns=rn).to_dict("records")
    defs = [{"field": c, "headerName": c, "sortable": True, "resizable": True, "flex": 1, "minWidth": 120,
             **({"pinned": "left", "width": 90, "minWidth": 90, "flex": 0, "cellStyle": {"fontWeight": "700", "fontFamily": FONT_MONO}} if c == "Team" else {})}
            for c in list(rn.values()) if c in (records[0] if records else {})]
    return make_grid("s26-a", records, defs, 600)

# ── SOS HISTORICAL ────────────────────────────────────────────────────────────
@app.callback(Output("sos-h-c", "children"), Input("sos-h-pos", "value"), Input("season", "value"))
def render_sos_h(pos, season_str):
    if season_str == "2026": return html.Div()
    df = get_data(season_str)["SOS"]
    if df.empty: return empty_msg()
    tc = next((c for c in ["team", "recent_team", "opponent_team"] if c in df.columns), df.columns[0])
    sos = df[df["position"] == pos].sort_values("avg_pts_allowed", ascending=False).copy()
    sos["avg_pts_allowed"] = sos["avg_pts_allowed"].round(2)
    cols = [c for c in [tc, "avg_pts_allowed", "sos_rank"] if c in sos.columns]
    rn = {tc: "Team", "avg_pts_allowed": "Avg Pts Allowed", "sos_rank": "SOS Rank"}
    records = sos[cols].rename(columns=rn).fillna("—").to_dict("records")
    defs = [{"field": c, "headerName": c, "sortable": True, "resizable": True, "flex": 1, "minWidth": 120,
             **({"pinned": "left", "width": 90, "minWidth": 90, "flex": 0, "cellStyle": {"fontWeight": "700", "fontFamily": FONT_MONO}} if c == "Team" else {})}
            for c in list(rn.values()) if c in (records[0] if records else {})]
    return make_grid("sos-h-g", records, defs, 560)

# ── DRAFT NOTES RENDERING ──────────────────────────────────────────────────────
def _render_must():
    col1 = html.Div([
        html.Div("MUST DRAFTS", style={"fontSize": "12px", "fontWeight": "700", "color": GREEN, "letterSpacing": ".06em", "marginBottom": "12px"}),
        *[html.Div([
            html.Div(k.upper(), style={"fontSize": "10.5px", "fontWeight": "700", "color": TFAINT, "letterSpacing": ".06em", "borderBottom": f"1px solid {BORDER}", "paddingBottom": "6px", "marginTop": "16px", "marginBottom": "8px"}),
            *[html.Div(p, className="draft-g") for p in v]
          ]) for k, v in MUST_DRAFT.items()]
    ], style={"flex": "1"})
    col2 = html.Div([
        html.Div("MUST AVOIDS", style={"fontSize": "12px", "fontWeight": "700", "color": RED, "letterSpacing": ".06em", "marginBottom": "12px"}),
        *[html.Div([
            html.Div(k.upper(), style={"fontSize": "10.5px", "fontWeight": "700", "color": TFAINT, "letterSpacing": ".06em", "borderBottom": f"1px solid {BORDER}", "paddingBottom": "6px", "marginTop": "16px", "marginBottom": "8px"}),
            *[html.Div(p, className="draft-r") for p in v]
          ]) for k, v in MUST_AVOID.items()]
    ], style={"flex": "1"})
    return html.Div([col1, col2], style={"display": "flex", "gap": "28px"})

def _render_target():
    items = list(TARGET_PICKS.items())
    mid = (len(items) + 1) // 2
    def col(subset):
        return [html.Div([
            html.Div(r.upper(), style={"fontSize": "10.5px", "fontWeight": "700", "color": TFAINT, "letterSpacing": ".06em", "borderBottom": f"1px solid {BORDER}", "paddingBottom": "6px", "marginTop": "16px", "marginBottom": "8px"}),
            *[html.Div(p, className="draft-p") for p in ps]
        ]) for r, ps in subset]
    return html.Div([
        html.Div([html.Div("FAVORITE PICKS BY ROUND", style={"fontSize": "12px", "fontWeight": "700", "color": ACCENT, "letterSpacing": ".06em", "marginBottom": "12px"}), *col(items[:mid])], style={"flex": "1"}),
        html.Div(col(items[mid:]), style={"flex": "1", "marginTop": "38px"}),
    ], style={"display": "flex", "gap": "28px"})

def _render_uv():
    cards = []
    for p in UNDERVALUED:
        pc = POS_C.get(p["pos"], TEXT)
        card = html.Div([
            html.Div([
                html.Span(p["name"], style={"fontSize": "1.05rem", "color": TEXT, "fontWeight": "700", "marginRight": "10px"}),
                html.Span(f"{p['pos']} · {p['team']}", style={"background": pc + "22", "border": f"1px solid {pc}55", "color": pc, "fontSize": "10.5px", "fontWeight": "700", "padding": "3px 9px", "borderRadius": "5px"}),
            ], style={"marginBottom": "6px"}),
            html.Div(f"Projected {p['proj_rank']} · ADP round {p['adp']}", style={"color": TDIM, "fontSize": "11.5px", "marginBottom": "12px"}),
            *[html.Div(b, className="draft-p") for b in p["bullets"]],
        ], className="coach-card")
        cards.append(card)
    left, right = cards[0::2], cards[1::2]
    return html.Div([
        html.Div("UNDERVALUED PLAYERS · 2026 TARGETS", style={"fontSize": "12px", "fontWeight": "700", "color": ACCENT, "letterSpacing": ".06em", "marginBottom": "16px"}),
        html.Div([html.Div(left, style={"flex": "1"}), html.Div(right, style={"flex": "1"})], style={"display": "flex", "gap": "16px"}),
    ])

@app.callback(
    Output("draft-c", "children"),
    Output("btn-must", "className"), Output("btn-target", "className"), Output("btn-uv", "className"),
    Input("btn-must", "n_clicks"), Input("btn-target", "n_clicks"), Input("btn-uv", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_draft(nm, nt, nu):
    t = ctx.triggered_id
    if t == "btn-target": return _render_target(), "toggle-btn", "toggle-btn active", "toggle-btn"
    if t == "btn-uv": return _render_uv(), "toggle-btn", "toggle-btn", "toggle-btn active"
    return _render_must(), "toggle-btn active", "toggle-btn", "toggle-btn"

# ── PLAY CALLERS ──────────────────────────────────────────────────────────────
def _render_playcallers():
    records = [{"Rk": r, "Team": t, "Play Caller": pc, "Coach / OC": co} for r, t, pc, co in PLAY_CALLERS]
    defs = [
        {"field": "Rk", "headerName": "#", "pinned": "left", "width": 60, "minWidth": 60, "flex": 0,
         "sortable": True, "cellStyle": {"color": TFAINT, "fontFamily": FONT_MONO}},
        {"field": "Team", "headerName": "Team", "width": 160, "minWidth": 160, "flex": 0, "sortable": True,
         "cellStyle": {"fontWeight": "700", "color": TEXT}},
        {"field": "Play Caller", "headerName": "Play Caller", "flex": 1, "minWidth": 180, "sortable": True,
         "cellStyle": {"color": ACCENT, "fontWeight": "600"}},
        {"field": "Coach / OC", "headerName": "Coach / OC", "flex": 1, "minWidth": 180, "sortable": True,
         "cellStyle": {"color": TDIM}},
    ]
    return html.Div([
        sec("2026 Offensive Play Callers",
            sub="Who actually calls plays for each team — the highlighted name. Click a column to sort."),
        make_grid("g-playcallers", records, defs, 760),
    ])

# ── O-LINE ────────────────────────────────────────────────────────────────────
def _trend_arrow(t):
    return {"up": ("↑", GREEN), "up2": ("↑↑", GREEN), "down": ("↓", RED), "flat": ("–", TFAINT)}[t]

def _render_oline_hist(season_str):
    if season_str != "2025":
        return html.Div([sec(f"O-Line Run Block Rating · {season_str}"),
                          empty_msg("O-Line run block ratings are only tracked for the 2025 board.")])
    records = []
    for rk, team, trend, cohesion, rank26, qb_runs in OLINE_2025_DATA:
        sym, _ = _trend_arrow(trend)
        records.append({"Rk": rk, "Team": team, "Trend": sym, "Cohesion": cohesion,
                         "26 Rank": rank26, "QB Runs": "✓" if qb_runs else "—"})
    defs = [
        {"field": "Rk", "headerName": "2025 OL", "pinned": "left", "width": 80, "minWidth": 80, "flex": 0,
         "sortable": True, "cellStyle": {"color": TFAINT, "fontFamily": FONT_MONO}},
        {"field": "Team", "headerName": "Team", "width": 90, "minWidth": 90, "flex": 0, "sortable": True,
         "cellStyle": {"fontWeight": "700", "color": TEXT, "fontFamily": FONT_MONO}},
        {"field": "Trend", "headerName": "Trend", "width": 90, "minWidth": 90, "flex": 0, "sortable": True,
         "cellStyle": {"function": f"""(function(p){{
             var m={{"↑":"{GREEN}","↑↑":"{GREEN}","↓":"{RED}","–":"{TFAINT}"}};
             return {{color:m[p.value]||"{TFAINT}",fontWeight:"800",textAlign:"center"}};
         }})(params)"""}},
        {"field": "Cohesion", "headerName": "Cohesion", "flex": 1, "minWidth": 110, "sortable": True,
         "cellStyle": heat_style("Cohesion")},
        {"field": "26 Rank", "headerName": "26 Rank", "flex": 1, "minWidth": 110, "sortable": True,
         "cellStyle": heat_style("26 Rank")},
        {"field": "QB Runs", "headerName": "QB Runs", "width": 100, "minWidth": 100, "flex": 0, "sortable": True,
         "cellStyle": {"color": ACCENT, "fontWeight": "700", "textAlign": "center"}},
    ]
    return html.Div([
        sec("2025 O-Line Run Block Rating",
            sub="2025 season O-line rank, trend, unit cohesion (1-5), projected 2026 rank, and whether the QB adds rushing juice. Click a column to sort."),
        make_grid("g-oline-h", records, defs, 900),
    ])

def _render_oline():
    records = [{"Rk": rk, "Team": team, "Name": name, "Consensus Score": score}
               for rk, team, name, score in OLINE_DATA]
    defs = [
        {"field": "Rk", "headerName": "#", "pinned": "left", "width": 56, "minWidth": 56, "flex": 0,
         "sortable": True, "cellStyle": {"color": TFAINT, "fontFamily": FONT_MONO}},
        {"field": "Team", "headerName": "Team", "width": 90, "minWidth": 90, "flex": 0, "sortable": True,
         "cellStyle": {"fontWeight": "700", "color": TEXT, "fontFamily": FONT_MONO}},
        {"field": "Name", "headerName": "Team Name", "flex": 1, "minWidth": 150, "sortable": True,
         "cellStyle": {"color": TDIM}},
        {"field": "Consensus Score", "headerName": "Consensus Score", "flex": 1, "minWidth": 150, "sortable": True,
         "cellStyle": heat_style("Consensus Score", invert=True)},
    ]
    return html.Div([
        sec("2026 O-Line Preseason Rankings — Consensus",
            sub="Averaged across major preseason O-line rankings. Lower score = better offensive line. Click a column to sort."),
        make_grid("g-oline", records, defs, 900),
    ])

# ── COACHING CHANGES ──────────────────────────────────────────────────────────
def _render_coaching():
    cards = []
    for c in COACHING_CHANGES:
        imp = c["impact"]
        border_c = GREEN if imp == "POSITIVE" else (RED if imp == "NEGATIVE" else TFAINT)
        chip_style = lambda col: {"background": col + "18", "border": f"1px solid {col}44", "color": col,
                                   "fontSize": "10.5px", "fontWeight": "700", "padding": "3px 9px",
                                   "borderRadius": "5px", "marginRight": "6px", "marginBottom": "6px", "display": "inline-block"}
        up_chips = html.Div([html.Span(f"↑ {p}", style=chip_style(GREEN)) for p in c["up"]]) if c["up"] else html.Div()
        down_chips = html.Div([html.Span(f"↓ {p}", style=chip_style(RED)) for p in c["down"]]) if c["down"] else html.Div()
        card = html.Div([
            html.Div([
                html.Span(c["team"], style={"fontSize": "1.2rem", "color": ACCENT, "fontWeight": "800", "letterSpacing": ".02em", "marginRight": "10px", "fontFamily": FONT_MONO}),
                html.Span(imp, style={"background": border_c + "22", "border": f"1px solid {border_c}55", "color": border_c, "fontSize": "10px", "padding": "3px 9px", "borderRadius": "5px", "fontWeight": "700"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
            html.Div(c["full"], style={"color": TDIM, "fontSize": "12px", "marginBottom": "12px"}),
            html.Div([
                html.Span(c["out"], style={"color": RED, "fontSize": "12.5px", "fontWeight": "600"}),
                html.Span(" → ", style={"color": TFAINT}),
                html.Span(c["new_hc"], style={"color": GREEN, "fontSize": "12.5px", "fontWeight": "600"}),
            ], style={"marginBottom": "2px"}),
            html.Div(f"from {c['prev']}", style={"color": TFAINT, "fontSize": "11px", "marginBottom": "10px"}),
            html.Div(c["style"], style={"color": TEXT, "fontSize": "12px", "marginBottom": "10px", "fontStyle": "italic"}),
            html.Div(c["note"], style={"color": TEXT, "fontSize": "12.5px", "lineHeight": "1.6", "marginBottom": "12px"}),
            up_chips, down_chips,
        ], className=f"coach-card {'pos' if imp=='POSITIVE' else 'neg' if imp=='NEGATIVE' else 'neu'}")
        cards.append(card)
    left, right = cards[0::2], cards[1::2]
    return html.Div([
        sec("2026 Coaching Changes", sub="↑ = players likely to benefit · ↓ = players facing uncertainty"),
        html.Div([
            html.Div(left, style={"flex": "1", "display": "flex", "flexDirection": "column", "gap": "14px"}),
            html.Div(right, style={"flex": "1", "display": "flex", "flexDirection": "column", "gap": "14px"}),
        ], style={"display": "flex", "gap": "14px"}),
    ])

# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, port=8050)
