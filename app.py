"""
app.py — Fantasy Edge · Dash Edition · Render Deployment
Run locally:  py -3.12 app.py  →  http://localhost:8050
Deploy:       gunicorn app:server --bind 0.0.0.0:$PORT
"""

from dash import Dash, html, dcc, Input, Output, ctx
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
    "position":"Pos","consensus_rank":"Consensus Rank","fc_rank":"FantasyCalc",
    "fc_pos_rank":"FC Pos Rank","ffc_rank":"FFC Rank","ffc_adp":"FFC ADP",
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

# ── DRAFT NOTES DATA (kept from prior build) ────────────────────────────────────
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
    if pos == "QB":
        d["total_tds"] = d.get("passing_tds", 0).fillna(0) + d.get("rushing_tds", 0).fillna(0)
        keep = ["player_display_name", "recent_team", "games", "fantasy_points_ppr",
                "fppg_ppr", "passing_yards", "total_tds", "interceptions"]
    else:
        d["total_yards"] = d.get("rushing_yards", 0).fillna(0) + d.get("receiving_yards", 0).fillna(0)
        d["total_tds"] = d.get("rushing_tds", 0).fillna(0) + d.get("receiving_tds", 0).fillna(0)
        keep = ["player_display_name", "recent_team", "games", "fantasy_points_ppr",
                "fppg_ppr", "total_yards", "total_tds"]
    keep = [c for c in keep if c in d.columns]
    d = d[keep].sort_values("fantasy_points_ppr", ascending=False).reset_index(drop=True)
    d.insert(0, "rk", d.index + 1)
    d["fantasy_points_ppr"] = d["fantasy_points_ppr"].round(1)
    d["fppg_ppr"] = d["fppg_ppr"].round(1)
    return d

# ── AG GRID HELPERS ───────────────────────────────────────────────────────────
DGRID = {"suppressMovableColumns": True, "suppressCellFocus": True, "animateRows": False}
DCOL  = {"sortable": True, "resizable": True, "filter": False, "suppressMenu": True,
         "cellDataType": False, "cellStyle": {"color": TEXT}}

def make_grid(gid, records, col_defs, height=560):
    return dag.AgGrid(id=gid, rowData=records, columnDefs=col_defs,
                       defaultColDef=DCOL, dashGridOptions=DGRID,
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
            d.update({"pinned": "left", "width": 200, "minWidth": 200, "flex": 0, "cellStyle": {"fontWeight": "700", "color": TEXT}})
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
                dcc.Tab(label="QB", value="qb26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="RB", value="rb26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="WR", value="wr26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TE", value="te26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="SOS", value="sos26", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Draft Notes", value="draft", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Coaching", value="coaching", style=_ts(), selected_style=_tsa()),
            ], colors={"border": BORDER, "primary": ACCENT, "background": "transparent"},
               style={"borderBottom": f"1px solid {BORDER}"}),
            html.Div(id="c2026", style={"paddingTop": "18px"}),
        ]),

        # Historical view (2025 / 2024)
        html.Div(id="vhist", style={"display": "none"}, children=[
            dcc.Tabs(id="thist", value="qb-h", children=[
                dcc.Tab(label="QB", value="qb-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="RB", value="rb-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="WR", value="wr-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="TE", value="te-h", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="Team Splits", value="splits", style=_ts(), selected_style=_tsa()),
                dcc.Tab(label="SOS", value="sos-h", style=_ts(), selected_style=_tsa()),
            ], colors={"border": BORDER, "primary": ACCENT, "background": "transparent"},
               style={"borderBottom": f"1px solid {BORDER}"}),
            html.Div(id="chist", style={"paddingTop": "18px"}),
        ]),

    ], className="app-shell", style={"padding": "0 24px 60px"}),
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
    if tab in pos_map:
        if master.empty: return empty_msg()
        pos = pos_map[tab]
        df = master.copy()
        if "position" in df.columns:
            df = df[df["position"] == pos]
        keep = [c for c in ["overall_rank", "player", "team", "consensus_rank", "ffc_adp"] if c in df.columns]
        df = df[keep].sort_values("overall_rank")
        rn = df.rename(columns=COL_LABELS)
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

    if tab == "coaching":
        return _render_coaching()

    return html.Div()

# ── HISTORICAL TABS ───────────────────────────────────────────────────────────
@app.callback(Output("chist", "children"), Input("thist", "value"), Input("season", "value"))
def render_hist(tab, season_str):
    if season_str == "2026": return html.Div()
    data = get_data(season_str)

    pos_map = {"qb-h": "QB", "rb-h": "RB", "wr-h": "WR", "te-h": "TE"}
    if tab in pos_map:
        pos = pos_map[tab]
        df = prep_position_df(data[pos], pos)
        if df.empty: return empty_msg()
        label = {"QB": "Quarterback", "RB": "Running Back", "WR": "Wide Receiver", "TE": "Tight End"}[pos]
        return html.Div([
            sec(f"{label} PPR Rankings · {season_str}", sub="Click a column header to sort — click again to reverse."),
            stat_table_grid(f"g-{tab}", df, 600),
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

    return html.Div()

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
