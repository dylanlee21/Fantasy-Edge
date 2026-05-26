"""
build_player_profiles.py
=========================
Saves two files used for player profiles:
  1. data/player_info.csv   — name, position, team, age, headshot_url
  2. data/gamelogs_2025.csv — per-week game stats for every player
  3. data/gamelogs_2024.csv — per-week game stats for every player

Run after fantasy_pipeline.py:
  py -3.12 build_player_profiles.py
"""

import pandas as pd
import os
from datetime import date

DATA_DIR = "data"
today = date.today()

# ── PLAYER INFO ───────────────────────────────────────────────────────────────
print("📥 Loading player info (birth dates, headshots)...")
try:
    import nfl_data_py as nfl_old

    players_df = nfl_old.import_players()
    print(f"   Columns: {list(players_df.columns[:20])}")

    # Keep relevant columns
    keep = [c for c in [
        "display_name", "short_name", "position", "position_group",
        "current_team_id", "birth_date", "years_of_experience",
        "headshot_url", "gsis_id", "draft_year", "draft_round", "draft_number",
        "height", "weight", "college_name",
    ] if c in players_df.columns]

    info = players_df[keep].copy()

    # Compute age from birth_date
    if "birth_date" in info.columns:
        info["birth_date"] = pd.to_datetime(info["birth_date"], errors="coerce")
        info["age"] = info["birth_date"].apply(
            lambda dob: (today - dob.date()).days // 365 if pd.notna(dob) else None
        )

    # Rename for consistency
    info = info.rename(columns={
        "display_name":    "player_display_name",
        "current_team_id": "team",
    })

    info.to_csv(os.path.join(DATA_DIR, "player_info.csv"), index=False)
    print(f"   ✅ Player info saved: {len(info)} players")
    print(f"   Sample: {info[['player_display_name','position','team','age']].head(3).to_string()}")

except Exception as e:
    import traceback
    print(f"   ❌ Player info failed: {e}")
    traceback.print_exc()

# ── GAME LOGS ─────────────────────────────────────────────────────────────────
print("\n📥 Building game logs...")

def build_gamelogs(weekly_raw, year):
    weekly = weekly_raw[weekly_raw["season_type"] == "REG"].copy()

    name_col = next((c for c in ["player_display_name","player_name"] if c in weekly.columns), None)
    if not name_col:
        print(f"   ❌ No name column found for {year}")
        return

    cols = [c for c in [
        name_col, "position", "recent_team", "opponent_team", "week",
        "fantasy_points", "fantasy_points_ppr",
        "completions", "attempts", "passing_yards", "passing_tds", "interceptions",
        "carries", "rushing_yards", "rushing_tds",
        "receptions", "targets", "receiving_yards", "receiving_tds",
        "sacks",
    ] if c in weekly.columns]

    logs = weekly[cols].copy()
    if name_col != "player_display_name":
        logs = logs.rename(columns={name_col: "player_display_name"})

    logs = logs.sort_values(["player_display_name","week"]).reset_index(drop=True)

    path = os.path.join(DATA_DIR, f"gamelogs_{year}.csv")
    logs.to_csv(path, index=False)
    print(f"   ✅ {year} game logs saved: {len(logs)} player-week rows → {path}")

# 2024
try:
    import nfl_data_py as nfl_old
    print("   Loading 2024 weekly data...")
    weekly_2024 = nfl_old.import_weekly_data([2024])
    build_gamelogs(weekly_2024, 2024)
except Exception as e:
    print(f"   ❌ 2024 gamelogs failed: {e}")

# 2025
try:
    import nflreadpy as nfl_new
    print("   Loading 2025 weekly data...")
    weekly_2025 = nfl_new.load_player_stats([2025]).to_pandas()
    col_renames = {
        "team": "recent_team",
        "passing_interceptions": "interceptions",
        "sacks_suffered": "sacks",
        "rushing_attempts": "carries",
        "receiving_targets": "targets",
        "receiving_receptions": "receptions",
    }
    weekly_2025 = weekly_2025.rename(columns={k:v for k,v in col_renames.items() if k in weekly_2025.columns})
    if "fantasy_points_ppr" not in weekly_2025.columns and "fantasy_points" in weekly_2025.columns:
        rec = weekly_2025.get("receptions", 0)
        weekly_2025["fantasy_points_ppr"] = weekly_2025["fantasy_points"] + rec * 0.5
    build_gamelogs(weekly_2025, 2025)
except Exception as e:
    import traceback
    print(f"   ❌ 2025 gamelogs failed: {e}")
    traceback.print_exc()

print("\n✅ Done! Push to GitHub:")
print("  git add data/player_info.csv data/gamelogs_2024.csv data/gamelogs_2025.csv -f")
print("  git commit -m 'add player profiles and game logs'")
print("  git push")
