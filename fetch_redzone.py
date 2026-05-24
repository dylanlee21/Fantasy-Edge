"""
fetch_redzone.py
=================
Pulls red zone and goal line stats from 2025 PBP data.
Handles the abbreviated name format (A.Barner → Aaron Barner).

Run after fantasy_pipeline.py:
  py -3.12 fetch_redzone.py
"""

import pandas as pd
import os

DATA_DIR = "data"

def safe_div(a, b, decimals=3):
    return (a / b.where(b != 0)).round(decimals)

def build_name_map(year):
    """Build a map from PBP abbreviated names (A.Hill) to full names (Tyreek Hill)."""
    name_map = {}
    for pos in ["QB", "RB", "WR", "TE"]:
        path = os.path.join(DATA_DIR, str(year), f"{pos.lower()}_stats.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, index_col=0)
        if "player_display_name" not in df.columns:
            continue
        for full_name in df["player_display_name"].dropna():
            parts = full_name.strip().split()
            if len(parts) >= 2:
                abbr = parts[0][0] + "." + parts[-1]
                # Map abbreviated → full (keep first match if collision)
                if abbr not in name_map:
                    name_map[abbr] = full_name
    print(f"   Built name map: {len(name_map)} entries")
    return name_map

def extract_and_patch(year):
    print(f"\n{'='*50}")
    print(f"  RED ZONE STATS FOR {year}")
    print(f"{'='*50}")

    year_dir = os.path.join(DATA_DIR, str(year))

    # ── LOAD PBP ──────────────────────────────────────────────────────────────
    try:
        import nflreadpy as nfl_new
        print(f"📥 Loading {year} PBP data...")
        pbp = nfl_new.load_pbp([year]).to_pandas()
        pbp = pbp[pbp["season_type"] == "REG"].copy()
        print(f"   ✅ {len(pbp)} regular season plays")
    except Exception as e:
        print(f"   ❌ PBP load failed: {e}")
        return

    # ── CONVERT NUMERIC COLUMNS ───────────────────────────────────────────────
    for col in ["yardline_100", "pass_attempt", "rush_attempt", "touchdown"]:
        if col in pbp.columns:
            pbp[col] = pd.to_numeric(pbp[col], errors="coerce").fillna(0)

    # ── FILTER ZONES ──────────────────────────────────────────────────────────
    rz = pbp[pbp["yardline_100"] <= 20].copy()  # Red zone
    gl = pbp[pbp["yardline_100"] <= 5].copy()   # Goal line

    # ── BUILD NAME MAP ────────────────────────────────────────────────────────
    name_map = build_name_map(year)

    def resolve_name(abbr):
        if pd.isna(abbr):
            return None
        return name_map.get(abbr, abbr)  # Fall back to abbr if not found

    # ── PLAYER STATS ──────────────────────────────────────────────────────────
    # Red zone targets (all positions)
    rz_pass = rz[rz["pass_attempt"] == 1]
    rz_tgts = rz_pass.groupby("receiver_player_name").size().reset_index(name="rz_targets")
    rz_tgts["player_display_name"] = rz_tgts["receiver_player_name"].apply(resolve_name)
    rz_tgts = rz_tgts.dropna(subset=["player_display_name"])
    rz_tgts = rz_tgts.groupby("player_display_name")["rz_targets"].sum().reset_index()

    # Goal line carries (RBs)
    gl_rush = gl[gl["rush_attempt"] == 1]
    gl_car = gl_rush.groupby("rusher_player_name").size().reset_index(name="gl_carries")
    gl_car["player_display_name"] = gl_car["rusher_player_name"].apply(resolve_name)
    gl_car = gl_car.dropna(subset=["player_display_name"])
    gl_car = gl_car.groupby("player_display_name")["gl_carries"].sum().reset_index()

    # Goal line targets (RBs)
    gl_pass = gl[gl["pass_attempt"] == 1]
    gl_tgts = gl_pass.groupby("receiver_player_name").size().reset_index(name="gl_targets")
    gl_tgts["player_display_name"] = gl_tgts["receiver_player_name"].apply(resolve_name)
    gl_tgts = gl_tgts.dropna(subset=["player_display_name"])
    gl_tgts = gl_tgts.groupby("player_display_name")["gl_targets"].sum().reset_index()

    print(f"   RZ targets: {len(rz_tgts)} players")
    print(f"   GL carries: {len(gl_car)} players")
    print(f"   GL targets: {len(gl_tgts)} players")

    # ── PATCH POSITION CSVS ───────────────────────────────────────────────────
    for pos in ["RB", "WR", "TE"]:
        path = os.path.join(year_dir, f"{pos.lower()}_stats.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, index_col=0)

        # Remove stale columns
        for col in ["rz_targets","gl_carries","gl_targets"]:
            if col in df.columns:
                df = df.drop(columns=[col])

        if pos == "RB":
            df = df.merge(gl_car, on="player_display_name", how="left")
            df = df.merge(gl_tgts, on="player_display_name", how="left")
            df["gl_carries"] = df["gl_carries"].fillna(0).astype(int)
            df["gl_targets"] = df["gl_targets"].fillna(0).astype(int)

            # Opportunity share (carries + targets / team total)
            if "carries" in df.columns and "targets" in df.columns and "recent_team" in df.columns:
                df["opportunities"] = df["carries"] + df["targets"]
                team_opp = df.groupby("recent_team")["opportunities"].sum().reset_index()
                team_opp.columns = ["recent_team", "team_opp"]
                df = df.merge(team_opp, on="recent_team", how="left")
                df["opportunity_share"] = safe_div(df["opportunities"], df["team_opp"], 3)
                df = df.drop(columns=["opportunities", "team_opp"], errors="ignore")

        if pos in ["WR", "TE"]:
            df = df.merge(rz_tgts, on="player_display_name", how="left")
            df["rz_targets"] = df["rz_targets"].fillna(0).astype(int)

        # Ensure rank index starts at 1
        df = df.reset_index(drop=True)
        df.index += 1
        df.index.name = "rank"
        df.to_csv(path)
        print(f"   ✅ {pos} {year} patched → {path}")

    # ── TEAM RED ZONE STATS ───────────────────────────────────────────────────
    rz_plays = rz[(rz["pass_attempt"] == 1) | (rz["rush_attempt"] == 1)]
    team_rz = rz_plays.groupby("posteam").agg(
        rz_pass_plays=("pass_attempt", "sum"),
        rz_rush_plays=("rush_attempt", "sum"),
        rz_total_plays=("pass_attempt", "count"),
        rz_tds=("touchdown", "sum"),
    ).reset_index().rename(columns={"posteam": "team"})

    team_rz["rz_pass_rate"]       = safe_div(team_rz["rz_pass_plays"], team_rz["rz_total_plays"])
    team_rz["rz_run_rate"]        = safe_div(team_rz["rz_rush_plays"],  team_rz["rz_total_plays"])
    team_rz["rz_conversion_rate"] = safe_div(team_rz["rz_tds"],         team_rz["rz_total_plays"])

    splits_path = os.path.join(year_dir, "team_splits.csv")
    if os.path.exists(splits_path):
        splits = pd.read_csv(splits_path)
        for col in ["rz_pass_plays","rz_rush_plays","rz_total_plays","rz_tds",
                    "rz_pass_rate","rz_run_rate","rz_conversion_rate"]:
            if col in splits.columns:
                splits = splits.drop(columns=[col])

        team_col = next((c for c in ["team","recent_team","posteam"] if c in splits.columns), None)
        if team_col:
            merge_rz = team_rz.rename(columns={"team": team_col})
            splits = splits.merge(merge_rz, on=team_col, how="left")
            splits.to_csv(splits_path, index=False)
            print(f"   ✅ Team splits patched with RZ stats")


# ── MAIN ──────────────────────────────────────────────────────────────────────
print("🏈 Fetching red zone stats...\n")
extract_and_patch(2025)
print("\n✅ Done! Relaunch the app to see new columns.")
print("Then push to GitHub to update the live site:")
print("  git add data/ -f && git commit -m 'add red zone stats' && git push")
