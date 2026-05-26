"""
create_claude_rankings.py
==========================
Generates Claude's own 2026 PPR fantasy rankings using a multi-factor model:
  1. Consensus opinion     (avg of all external sources)
  2. Receiving upside      (WOPR, RACR, air yards share, adot)
  3. Age / potential       (younger = higher ceiling)
  4. Target share          (volume security)
  5. Team quality          (pass rate, offensive environment)
  6. 2025 perf vs expect   (over/underperformed their ADP)

py -3.12 create_claude_rankings.py
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = "data"
OUTPUT_DIR = os.path.join(DATA_DIR, "2026")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def normalize(series, ascending=True):
    """Normalize a series to 0–100. ascending=True means higher raw = higher score."""
    s = series.copy().astype(float)
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series([50.0] * len(s), index=s.index)
    norm = (s - mn) / (mx - mn) * 100
    return norm if ascending else 100 - norm

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
print("📥 Loading source data...")

# Master rankings (consensus + external ranks)
master_path = os.path.join(OUTPUT_DIR, "master_rankings.csv")
master = pd.read_csv(master_path, index_col=0) if os.path.exists(master_path) else pd.DataFrame()

# 2025 stats per position
stats_dfs = []
for pos in ["QB", "RB", "WR", "TE"]:
    path = os.path.join(DATA_DIR, "2025", f"{pos.lower()}_stats.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0)
        df["position"] = pos
        stats_dfs.append(df)
stats_2025 = pd.concat(stats_dfs, ignore_index=True) if stats_dfs else pd.DataFrame()
stats_2025 = stats_2025.rename(columns={"player_display_name": "player", "recent_team": "team"})

# Player info (age)
player_info_path = os.path.join(DATA_DIR, "player_info.csv")
player_info = pd.read_csv(player_info_path) if os.path.exists(player_info_path) else pd.DataFrame()
if not player_info.empty and "player_display_name" in player_info.columns:
    player_info = player_info.rename(columns={"player_display_name": "player"})

# Team splits (pass rate = team quality proxy)
splits_path = os.path.join(DATA_DIR, "2025", "team_splits.csv")
team_splits = pd.read_csv(splits_path) if os.path.exists(splits_path) else pd.DataFrame()

# FFC ADP (for performance vs expectation)
ffc_path = os.path.join(OUTPUT_DIR, "ffc_adp.csv")
ffc = pd.read_csv(ffc_path) if os.path.exists(ffc_path) else pd.DataFrame()

print(f"   Master: {len(master)} players")
print(f"   2025 stats: {len(stats_2025)} players")
print(f"   Player info: {len(player_info)} players")

# ── BUILD BASE TABLE ──────────────────────────────────────────────────────────
# Start from master (FC-based, clean player list)
if master.empty:
    print("❌ master_rankings.csv not found. Run fetch_rankings.py first.")
    exit()

df = master[["player","position","team"]].copy()

# Merge 2025 stats
stat_cols = ["player","fppg_ppr","target_share","air_yards_share","wopr","racr",
             "adot","avg_snap_pct","opportunity_share","games",
             "fantasy_points_ppr","carries","targets","receiving_yards"]
available_stat_cols = [c for c in stat_cols if c in stats_2025.columns]
df = df.merge(stats_2025[available_stat_cols].drop_duplicates("player"),
              on="player", how="left")

# Merge age
if not player_info.empty and "age" in player_info.columns:
    df = df.merge(player_info[["player","age"]].drop_duplicates("player"),
                  on="player", how="left")
else:
    df["age"] = None

# Merge team pass rate
team_col = next((c for c in ["team","recent_team","posteam"] if not team_splits.empty and c in team_splits.columns), None)
if team_col:
    ts = team_splits[[team_col,"pass_rate"]].rename(columns={team_col:"team","pass_rate":"team_pass_rate"})
    df = df.merge(ts.drop_duplicates("team"), on="team", how="left")
else:
    df["team_pass_rate"] = None

# Merge consensus rank from master
rank_cols_available = [c for c in ["consensus_rank","fc_rank","ffc_rank","espn_rank","rb_overall_rank","yahoo_rank"] if c in master.columns]
df = df.merge(master[["player"] + rank_cols_available].drop_duplicates("player"), on="player", how="left")

# Merge FFC ADP for perf vs expectation
if not ffc.empty and "ffc_adp" in ffc.columns:
    df = df.merge(ffc[["player","ffc_adp"]].drop_duplicates("player"), on="player", how="left")

# ── SCORING MODEL ─────────────────────────────────────────────────────────────
print("\n🔧 Computing Claude score...")

scores = pd.DataFrame(index=df.index)

# ── FACTOR 1: CONSENSUS OPINION (25%) ─────────────────────────────────────────
# Lower rank number = better → invert
if rank_cols_available:
    df["avg_external_rank"] = df[rank_cols_available].mean(axis=1)
    scores["consensus"] = normalize(df["avg_external_rank"], ascending=False) * 0.25
else:
    scores["consensus"] = 50 * 0.25

# ── FACTOR 2: RECEIVING UPSIDE (20%) ──────────────────────────────────────────
# WOPR + RACR + air yards share — best predictors of pass-game ceiling
rec_score = pd.Series(0.0, index=df.index)
count = 0
for col, weight in [("wopr", 0.4), ("racr", 0.35), ("air_yards_share", 0.25)]:
    if col in df.columns:
        rec_score += normalize(df[col].fillna(0)) * weight
        count += 1

# For RBs, use opportunity share as upside proxy instead
rb_mask = df["position"] == "RB"
if "opportunity_share" in df.columns:
    rb_upside = normalize(df["opportunity_share"].fillna(0))
    rec_score[rb_mask] = rec_score[rb_mask] * 0.4 + rb_upside[rb_mask] * 0.6

scores["receiving_upside"] = rec_score * 0.20

# ── FACTOR 3: AGE / POTENTIAL (15%) ───────────────────────────────────────────
# Peak age by position: RB 22-26, WR 23-27, QB 25-32, TE 24-28
# Score peaks at prime age and drops off on both sides
def age_score(row):
    age = row.get("age")
    pos = row.get("position", "WR")
    if pd.isna(age) or age is None:
        return 60  # neutral if unknown

    age = float(age)
    peaks = {"QB": (27, 30), "RB": (22, 25), "WR": (23, 26), "TE": (24, 27)}
    low, high = peaks.get(pos, (23, 27))

    if low <= age <= high:
        return 100  # prime age
    elif age < low:
        # Young — high ceiling but unproven
        years_away = low - age
        return max(70, 100 - years_away * 5)
    else:
        # Older — declining value
        years_past = age - high
        return max(0, 100 - years_past * 12)

df["age_score_raw"] = df.apply(age_score, axis=1)
scores["age_potential"] = df["age_score_raw"] * 0.15

# ── FACTOR 4: TARGET SHARE / VOLUME SECURITY (15%) ────────────────────────────
if "target_share" in df.columns:
    # Receivers: target share. RBs: opportunity share
    vol = df["target_share"].fillna(0).copy()
    if "opportunity_share" in df.columns:
        vol[rb_mask] = df.loc[rb_mask, "opportunity_share"].fillna(0)
    scores["volume"] = normalize(vol) * 0.15
else:
    scores["volume"] = 50 * 0.15

# ── FACTOR 5: TEAM QUALITY / PASS RATE (10%) ──────────────────────────────────
if "team_pass_rate" in df.columns:
    scores["team_quality"] = normalize(df["team_pass_rate"].fillna(df["team_pass_rate"].median())) * 0.10
else:
    scores["team_quality"] = 50 * 0.10

# ── FACTOR 6: 2025 PERFORMANCE VS EXPECTATION (15%) ───────────────────────────
# Compare actual 2025 FPPG to implied expectation from ADP rank
# Positive = outperformed, Negative = underperformed
if "ffc_adp" in df.columns and "fppg_ppr" in df.columns:
    # Expected FPPG based on ADP: higher ADP (drafted earlier) = higher expectation
    # Simple proxy: invert ADP to get expected quality tier
    df["adp_expectation"] = normalize(df["ffc_adp"].fillna(300), ascending=False)
    df["actual_perf"] = normalize(df["fppg_ppr"].fillna(0))
    df["perf_vs_expect"] = df["actual_perf"] - df["adp_expectation"]
    scores["perf_vs_expectation"] = normalize(df["perf_vs_expect"]) * 0.15
else:
    if "fppg_ppr" in df.columns:
        scores["perf_vs_expectation"] = normalize(df["fppg_ppr"].fillna(0)) * 0.15
    else:
        scores["perf_vs_expectation"] = 50 * 0.15

# ── TOTAL CLAUDE SCORE ────────────────────────────────────────────────────────
df["claude_score"] = scores.sum(axis=1).round(2)

# Add factor breakdown for transparency
df["factor_consensus"]     = scores["consensus"].round(1)
df["factor_rec_upside"]    = scores["receiving_upside"].round(1)
df["factor_age"]           = scores["age_potential"].round(1)
df["factor_volume"]        = scores["volume"].round(1)
df["factor_team"]          = scores["team_quality"].round(1)
df["factor_perf"]          = scores["perf_vs_expectation"].round(1)

# ── RANK ──────────────────────────────────────────────────────────────────────
df = df.sort_values("claude_score", ascending=False).reset_index(drop=True)
df["claude_overall_rank"] = range(1, len(df) + 1)
df["claude_pos_rank"] = df.groupby("position")["claude_score"].rank(
    ascending=False, method="min"
).astype(int)

# ── SAVE ──────────────────────────────────────────────────────────────────────
out_cols = ["player","position","team","claude_overall_rank","claude_pos_rank",
            "claude_score","factor_consensus","factor_rec_upside","factor_age",
            "factor_volume","factor_team","factor_perf","fppg_ppr","age"]
out_cols = [c for c in out_cols if c in df.columns]

out_path = os.path.join(OUTPUT_DIR, "claude_rankings.csv")
df[out_cols].to_csv(out_path, index=False)

print(f"\n✅ Claude Rankings saved → {out_path}")
print(f"   {len(df)} players ranked")
print(f"\n   Top 20:")
print(df[["claude_overall_rank","player","position","team","claude_score","age"]].head(20).to_string(index=False))

print(f"\n   Factor weights applied:")
print(f"   Consensus opinion:        25%")
print(f"   Receiving upside:         20%")
print(f"   Age / potential:          15%")
print(f"   Target share / volume:    15%")
print(f"   Team quality:             10%")
print(f"   2025 perf vs expectation: 15%")
