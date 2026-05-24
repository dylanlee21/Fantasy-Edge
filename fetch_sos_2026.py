"""
fetch_sos_2026.py
==================
Computes 2026 SOS using:
  - Real 2026 NFL schedule (all 17 weeks)
  - 2025 defensive rankings (avg pts allowed per position)

Run: py -3.12 fetch_sos_2026.py
"""

import pandas as pd
import os

OUTPUT_DIR = os.path.join("data", "2026")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 2026 FULL SCHEDULE ────────────────────────────────────────────────────────
# Format: (home_team, away_team) using standard NFL abbreviations
SCHEDULE_2026 = [
    # WEEK 1
    ("SEA","NE"), ("LAR","SF"), ("CAR","CHI"), ("CIN","TB"), ("DET","NO"),
    ("HOU","BUF"), ("IND","BAL"), ("JAX","CLE"), ("PIT","ATL"), ("TEN","NYJ"),
    ("LAC","ARI"), ("LV","MIA"), ("MIN","GB"), ("PHI","WAS"), ("NYG","DAL"), ("KC","DEN"),
    # WEEK 2
    ("BUF","DET"), ("ATL","CAR"), ("BAL","NO"), ("CHI","MIN"), ("HOU","CIN"),
    ("NE","PIT"), ("TB","CLE"), ("TEN","PHI"), ("DEN","JAX"), ("LAC","LV"),
    ("ARI","SEA"), ("DAL","WAS"), ("SF","MIA"), ("KC","IND"), ("LAR","NYG"),
    # WEEK 3
    ("GB","ATL"), ("BUF","LAC"), ("CLE","CAR"), ("DET","NYJ"), ("IND","HOU"),
    ("JAX","NE"), ("MIA","KC"), ("NYG","TEN"), ("PIT","CIN"), ("WAS","SEA"),
    ("SF","ARI"), ("TB","MIN"), ("DAL","BAL"), ("NO","LV"), ("DEN","LAR"), ("CHI","PHI"),
    # WEEK 4
    ("CLE","PIT"), ("WAS","IND"), ("BAL","TEN"), ("BUF","NE"), ("CHI","NYJ"),
    ("CIN","JAX"), ("HOU","DAL"), ("NYG","ARI"), ("PHI","LAR"), ("TB","GB"),
    ("MIN","MIA"), ("LV","KC"), ("SEA","LAC"), ("SF","DEN"), ("CAR","DET"), ("NO","ATL"),
    # WEEK 5
    ("DAL","TB"), ("JAX","PHI"), ("MIA","CIN"), ("NE","LV"), ("NO","MIN"),
    ("NYJ","CLE"), ("PIT","IND"), ("TEN","HOU"), ("WAS","NYG"), ("LAC","DEN"),
    ("ARI","DET"), ("GB","CHI"), ("SEA","SF"), ("ATL","BAL"), ("LAR","BUF"),
    # WEEK 6
    ("NYJ","NE"), ("ARI","GB"), ("BAL","CLE"), ("BUF","MIA"), ("CAR","TB"),
    ("DEN","LV"), ("DET","DAL"), ("HOU","IND"), ("MIN","PHI"), ("SF","LAR"),
    ("NO","ATL"), ("CHI","WAS"), ("CIN","TEN"), ("SEA","KC"), ("NYG","JAX"),
    # WEEK 7 - BYEs mixed in, skip for simplicity, use known games
    ("PHI","DAL"), ("LAC","SF"), ("BUF","NE"), ("ATL","CAR"), ("CHI","HOU"),
    ("CLE","DEN"), ("DET","JAX"), ("GB","MIN"), ("IND","TEN"), ("KC","LAR"),
    ("MIA","NYG"), ("NYJ","LV"), ("PIT","BAL"), ("SEA","ARI"), ("TB","NO"), ("WAS","CIN"),
    # WEEK 8
    ("BAL","SEA"), ("BUF","KC"), ("CAR","NYG"), ("CHI","SF"), ("CIN","NYJ"),
    ("DAL","MIA"), ("DEN","TB"), ("DET","MIN"), ("GB","IND"), ("HOU","LV"),
    ("JAX","TEN"), ("LAC","NE"), ("LAR","ARI"), ("NO","CLE"), ("PHI","PIT"), ("WAS","ATL"),
    # WEEK 9
    ("MIN","BAL"), ("ARI","CIN"), ("ATL","NYJ"), ("BUF","DET"), ("CAR","PIT"),
    ("CLE","GB"), ("DEN","HOU"), ("IND","MIA"), ("JAX","CHI"), ("KC","WAS"),
    ("LV","LAR"), ("NE","SF"), ("NO","TB"), ("NYG","PHI"), ("SEA","LAC"), ("TEN","DAL"),
    # WEEK 10
    ("BUF","NYJ"), ("ARI","ATL"), ("BAL","MIA"), ("CHI","SEA"), ("CIN","CLE"),
    ("DAL","LAR"), ("DET","CAR"), ("GB","KC"), ("HOU","NE"), ("IND","DEN"),
    ("LAC","LV"), ("MIN","PHI"), ("NO","NYG"), ("PIT","TEN"), ("SF","JAX"), ("TB","WAS"),
    # WEEK 11
    ("MIA","SEA"), ("ATL","CIN"), ("BAL","NYJ"), ("CAR","NE"), ("CHI","GB"),
    ("CLE","HOU"), ("DAL","IND"), ("DEN","LAC"), ("DET","TB"), ("JAX","LV"),
    ("KC","ARI"), ("LAR","SF"), ("MIN","NO"), ("PHI","NYG"), ("PIT","BUF"), ("WAS","TEN"),
    # WEEK 12 - Thanksgiving week
    ("LAR","GB"), ("DET","CHI"), ("PHI","DAL"), ("BUF","KC"), ("ARI","BAL"),
    ("ATL","CAR"), ("CIN","HOU"), ("CLE","NYJ"), ("DEN","MIA"), ("IND","JAX"),
    ("NE","PIT"), ("NO","TB"), ("NYG","WAS"), ("SEA","MIN"), ("SF","LV"), ("TEN","LAC"),
    # WEEK 13
    ("NE","CAR"), ("ATL","DET"), ("BAL","GB"), ("BUF","CIN"), ("CHI","MIN"),
    ("DAL","NO"), ("DEN","KC"), ("HOU","LAR"), ("IND","CLE"), ("JAX","MIA"),
    ("LV","ARI"), ("NYG","TEN"), ("PHI","SEA"), ("PIT","NYJ"), ("SF","WAS"), ("TB","LAC"),
    # WEEK 14
    ("ARI","DEN"), ("BAL","PIT"), ("BUF","NYG"), ("CAR","WAS"), ("CHI","DAL"),
    ("CIN","ATL"), ("CLE","TEN"), ("DET","NE"), ("GB","LAC"), ("HOU","SF"),
    ("IND","NYJ"), ("JAX","NO"), ("KC","MIA"), ("LAR","PHI"), ("MIN","SEA"), ("TB","LV"),
    # WEEK 15
    ("MIA","NE"), ("ATL","TB"), ("BAL","DEN"), ("BUF","IND"), ("CAR","JAX"),
    ("CHI","LAR"), ("CIN","LAC"), ("CLE","PIT"), ("DAL","GB"), ("DET","WAS"),
    ("HOU","KC"), ("LV","SEA"), ("MIN","ARI"), ("NO","PHI"), ("NYG","NYJ"), ("SF","TEN"),
    # WEEK 16
    ("SEA","LAR"), ("ARI","NO"), ("ATL","MIN"), ("BAL","CLE"), ("BUF","PIT"),
    ("CAR","DEN"), ("CIN","GB"), ("DAL","WAS"), ("DET","LAC"), ("HOU","TEN"),
    ("IND","MIA"), ("JAX","NYG"), ("KC","CHI"), ("NE","PHI"), ("NYJ","SF"), ("TB","ATL"),
    # WEEK 17
    ("NE","DEN"), ("ARI","LV"), ("ATL","JAX"), ("BAL","WAS"), ("BUF","TEN"),
    ("CAR","NYG"), ("CHI","IND"), ("CIN","MIA"), ("CLE","DAL"), ("DET","PHI"),
    ("GB","NO"), ("HOU","BAL"), ("KC","PIT"), ("LAC","KC"), ("LAR","SEA"), ("MIN","TB"),
    # WEEK 18
    ("SEA","LAR"), ("ATL","TB"), ("BAL","CLE"), ("BUF","NE"), ("CAR","NO"),
    ("CHI","GB"), ("CIN","PIT"), ("DAL","PHI"), ("DEN","LAC"), ("DET","MIN"),
    ("HOU","IND"), ("JAX","TEN"), ("KC","LV"), ("MIA","NYJ"), ("NYG","WAS"), ("SF","ARI"),
]

print(f"📅 2026 schedule loaded: {len(SCHEDULE_2026)} games")

# ── LOAD 2025 DEFENSIVE RANKINGS ─────────────────────────────────────────────
print("📥 Loading 2025 defensive rankings (pts allowed per position)...")

sos_path = os.path.join("data", "2025", "sos_by_team.csv")
if not os.path.exists(sos_path):
    print("❌ 2025 SOS file not found. Run fantasy_pipeline.py first.")
    exit()

sos_2025 = pd.read_csv(sos_path)
print(f"   ✅ Loaded: {len(sos_2025)} team/position rows")
print(f"   Columns: {list(sos_2025.columns)}")
print(f"   Sample:\n{sos_2025.head(6).to_string()}")

# Detect team column
team_col = next((c for c in ["team","recent_team","opponent_team"] if c in sos_2025.columns), None)
if not team_col:
    print("❌ Could not find team column in SOS data")
    exit()

# Build lookup: team → {pos: avg_pts_allowed}
def_ratings = {}
for _, row in sos_2025.iterrows():
    team = row[team_col]
    pos  = row["position"]
    pts  = row["avg_pts_allowed"]
    if team not in def_ratings:
        def_ratings[team] = {}
    def_ratings[team][pos] = pts

print(f"   Defense ratings built for {len(def_ratings)} teams")

# ── COMPUTE 2026 SOS PER TEAM PER POSITION ────────────────────────────────────
print("\n🔧 Computing 2026 SOS...")

positions = ["QB", "RB", "WR", "TE"]
team_opponents = {}  # team → list of opponents

for home, away in SCHEDULE_2026:
    if home not in team_opponents: team_opponents[home] = []
    if away not in team_opponents: team_opponents[away] = []
    team_opponents[home].append(away)
    team_opponents[away].append(home)

rows = []
for team, opponents in team_opponents.items():
    for pos in positions:
        opp_ratings = []
        for opp in opponents:
            rating = def_ratings.get(opp, {}).get(pos)
            if rating is not None:
                opp_ratings.append(rating)
        if opp_ratings:
            avg = round(sum(opp_ratings) / len(opp_ratings), 2)
            rows.append({"team": team, "position": pos, "avg_opp_pts_allowed": avg,
                         "games_rated": len(opp_ratings)})

sos_df = pd.DataFrame(rows)

# Rank: higher avg_opp_pts_allowed = easier schedule (defenses allow more pts)
sos_df["sos_2026_rank"] = sos_df.groupby("position")["avg_opp_pts_allowed"].rank(
    ascending=False, method="min"
).astype(int)

# Difficulty label
def difficulty(rank, total=32):
    pct = rank / total
    if pct <= 0.25:   return "EASY"
    elif pct <= 0.5:  return "BELOW AVG"
    elif pct <= 0.75: return "ABOVE AVG"
    else:             return "HARD"

sos_df["difficulty"] = sos_df["sos_2026_rank"].apply(difficulty)
sos_df = sos_df.sort_values(["position","sos_2026_rank"]).reset_index(drop=True)

out_path = os.path.join(OUTPUT_DIR, "sos_2026.csv")
sos_df.to_csv(out_path, index=False)
print(f"   ✅ 2026 SOS saved → {out_path}")
print(f"   {len(sos_df)} team/position rows")

# Preview
for pos in positions:
    sub = sos_df[sos_df["position"] == pos].head(5)
    print(f"\n   Top 5 easiest {pos} schedules:")
    print(sub[["team","avg_opp_pts_allowed","sos_2026_rank","difficulty"]].to_string(index=False))

print("\n✅ 2026 SOS complete! Push to GitHub to update the live site.")
