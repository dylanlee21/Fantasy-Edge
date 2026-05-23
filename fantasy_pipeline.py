"""
fantasy_pipeline.py
====================
2024 data: nfl-data-py (archived but works for 2024)
2025 data: nflreadpy (the new replacement package)
"""

import pandas as pd
import os

OUTPUT_DIR = "data"

def safe_div(a, b, decimals=2):
    return (a / b.where(b != 0)).round(decimals)

def compute_and_save(weekly_raw, snaps_raw, year):
    print(f"\n{'='*50}")
    print(f"  PROCESSING {year} SEASON")
    print(f"{'='*50}")

    year_dir = os.path.join(OUTPUT_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)

    # Regular season only
    weekly = weekly_raw[weekly_raw["season_type"] == "REG"].copy()
    snaps  = snaps_raw[snaps_raw["game_type"] == "REG"].copy() if "game_type" in snaps_raw.columns else snaps_raw.copy()

    print(f"   {len(weekly)} rows · weeks {weekly['week'].min()}–{weekly['week'].max()}")

    # ── AGGREGATION ───────────────────────────────────────────────────────────
    agg_dict = {
        "games":                       ("week", "count"),
        "completions":                 ("completions", "sum"),
        "attempts":                    ("attempts", "sum"),
        "passing_yards":               ("passing_yards", "sum"),
        "passing_tds":                 ("passing_tds", "sum"),
        "interceptions":               ("interceptions", "sum"),
        "passing_air_yards":           ("passing_air_yards", "sum"),
        "sacks":                       ("sacks", "sum"),
        "carries":                     ("carries", "sum"),
        "rushing_yards":               ("rushing_yards", "sum"),
        "rushing_tds":                 ("rushing_tds", "sum"),
        "receptions":                  ("receptions", "sum"),
        "targets":                     ("targets", "sum"),
        "receiving_yards":             ("receiving_yards", "sum"),
        "receiving_tds":               ("receiving_tds", "sum"),
        "receiving_air_yards":         ("receiving_air_yards", "sum"),
        "receiving_yards_after_catch": ("receiving_yards_after_catch", "sum"),
        "target_share":                ("target_share", "mean"),
        "air_yards_share":             ("air_yards_share", "mean"),
        "racr":                        ("racr", "mean"),
        "fantasy_points":              ("fantasy_points", "sum"),
        "fantasy_points_ppr":          ("fantasy_points_ppr", "sum"),
    }
    for w in ["wopr", "wopr_x"]:
        if w in weekly.columns:
            agg_dict["wopr"] = (w, "mean")
            break

    valid_agg = {k: v for k, v in agg_dict.items() if v[0] in weekly.columns}

    # Find name column (varies between packages)
    name_col = next((c for c in ["player_display_name", "player_name"] if c in weekly.columns), None)
    if name_col is None:
        print("❌ Could not find player name column")
        return

    group_cols = ["player_id", name_col, "position", "recent_team"]
    group_cols = [c for c in group_cols if c in weekly.columns]

    agg = weekly.groupby(group_cols).agg(**valid_agg).reset_index()

    # Normalize name column
    if name_col != "player_display_name":
        agg = agg.rename(columns={name_col: "player_display_name"})

    # ── SNAP % ────────────────────────────────────────────────────────────────
    if "offense_pct" in snaps.columns and "player" in snaps.columns and "team" in snaps.columns:
        snap_by_name = (
            snaps.groupby(["player", "team"])
            .agg(avg_snap_pct=("offense_pct", "mean"))
            .reset_index()
            .rename(columns={"player": "player_display_name", "team": "recent_team"})
        )
        agg = agg.merge(snap_by_name, on=["player_display_name", "recent_team"], how="left")

    # ── DERIVED METRICS ───────────────────────────────────────────────────────
    if "rushing_yards" in agg.columns and "carries" in agg.columns:
        agg["ypc"] = safe_div(agg["rushing_yards"], agg["carries"])
    if "receiving_yards" in agg.columns and "targets" in agg.columns:
        agg["yards_per_target"] = safe_div(agg["receiving_yards"], agg["targets"])
    if "receptions" in agg.columns and "targets" in agg.columns:
        agg["catch_rate"] = safe_div(agg["receptions"], agg["targets"], 3)
    if "completions" in agg.columns and "attempts" in agg.columns:
        agg["comp_pct"] = safe_div(agg["completions"], agg["attempts"], 3)
    if "passing_yards" in agg.columns and "attempts" in agg.columns:
        agg["yards_per_attempt"] = safe_div(agg["passing_yards"], agg["attempts"])
    if "passing_tds" in agg.columns and "attempts" in agg.columns:
        agg["td_rate"] = safe_div(agg["passing_tds"], agg["attempts"], 3)
    if "fantasy_points" in agg.columns:
        agg["fppg"] = safe_div(agg["fantasy_points"], agg["games"])
    if "fantasy_points_ppr" in agg.columns:
        agg["fppg_ppr"] = safe_div(agg["fantasy_points_ppr"], agg["games"])
    if "receiving_air_yards" in agg.columns and "targets" in agg.columns:
        agg["adot"] = safe_div(agg["receiving_air_yards"], agg["targets"])
    if "receiving_yards_after_catch" in agg.columns and "receptions" in agg.columns:
        agg["yac_per_rec"] = safe_div(agg["receiving_yards_after_catch"], agg["receptions"])

    # ── SOS ───────────────────────────────────────────────────────────────────
    opp_col = next((c for c in ["opponent_team", "opponent"] if c in weekly.columns), None)
    if opp_col:
        pts_allowed = (
            weekly.groupby([opp_col, "position"])
            .agg(avg_pts_allowed=("fantasy_points_ppr", "mean"))
            .reset_index()
            .rename(columns={opp_col: "team"})
        )
        pts_allowed["sos_rank"] = pts_allowed.groupby("position")["avg_pts_allowed"].rank(
            ascending=False, method="min"
        ).astype(int)
        pts_allowed.to_csv(os.path.join(year_dir, "sos_by_team.csv"), index=False)
        print(f"   ✅ SOS saved")

    # ── TEAM SPLITS ───────────────────────────────────────────────────────────
    team_pass = (
        weekly.groupby("recent_team")
        .agg(pass_attempts=("attempts", "sum"), rush_attempts=("carries", "sum"))
        .reset_index()
    )
    team_pass["total_plays"] = team_pass["pass_attempts"] + team_pass["rush_attempts"]
    team_pass["pass_rate"] = safe_div(team_pass["pass_attempts"], team_pass["total_plays"], 3)
    team_pass["run_rate"]  = safe_div(team_pass["rush_attempts"],  team_pass["total_plays"], 3)
    team_pass.rename(columns={"recent_team": "team"}).sort_values("pass_rate", ascending=False).to_csv(
        os.path.join(year_dir, "team_splits.csv"), index=False
    )
    print(f"   ✅ Team splits saved")

    # ── EXPORT BY POSITION ────────────────────────────────────────────────────
    POSITION_COLS = {
        "QB": ["player_display_name","recent_team","games","passing_yards","passing_tds",
               "interceptions","comp_pct","yards_per_attempt","td_rate","sacks",
               "carries","rushing_yards","rushing_tds","fppg","fppg_ppr"],
        "RB": ["player_display_name","recent_team","games","carries","rushing_yards",
               "rushing_tds","ypc","targets","receptions","receiving_yards","receiving_tds",
               "target_share","catch_rate","yac_per_rec","avg_snap_pct","fppg","fppg_ppr"],
        "WR": ["player_display_name","recent_team","games","targets","receptions",
               "receiving_yards","receiving_tds","target_share","air_yards_share",
               "wopr","racr","adot","catch_rate","yards_per_target","yac_per_rec",
               "avg_snap_pct","fppg","fppg_ppr"],
        "TE": ["player_display_name","recent_team","games","targets","receptions",
               "receiving_yards","receiving_tds","target_share","air_yards_share",
               "wopr","racr","adot","catch_rate","yards_per_target","avg_snap_pct",
               "fppg","fppg_ppr"],
    }
    MIN_GAMES = {"QB": 5, "RB": 3, "WR": 3, "TE": 3}

    print(f"💾 [{year}] Saving position CSVs...")
    for pos, cols in POSITION_COLS.items():
        df = agg[agg["position"] == pos].copy()
        df = df[df["games"] >= MIN_GAMES[pos]]
        available = [c for c in cols if c in df.columns]
        df = df[available].sort_values("fppg_ppr", ascending=False).reset_index(drop=True)
        df.index += 1
        df.index.name = "rank"
        path = os.path.join(year_dir, f"{pos.lower()}_stats.csv")
        df.to_csv(path)
        print(f"   ✅ {pos} {year}: {len(df)} players → {path}")


# ── 2024 via nfl-data-py ──────────────────────────────────────────────────────
print("📦 Loading 2024 data via nfl-data-py...")
import nfl_data_py as nfl_old
weekly_2024 = nfl_old.import_weekly_data([2024])
snaps_2024  = nfl_old.import_snap_counts([2024])
compute_and_save(weekly_2024, snaps_2024, 2024)

# ── 2025 via nflreadpy ────────────────────────────────────────────────────────
print("\n📦 Loading 2025 data via nflreadpy...")
try:
    import nflreadpy as nfl_new
    weekly_2025 = nfl_new.load_player_stats([2025]).to_pandas()
    print(f"   2025 weekly columns: {list(weekly_2025.columns[:20])}...")

    # nflreadpy uses different column names — normalize to match nfl-data-py
    col_renames = {
        "team":                  "recent_team",
        "passing_interceptions": "interceptions",
        "sacks_suffered":        "sacks",
        "rushing_attempts":      "carries",
        "receiving_targets":     "targets",
        "receiving_receptions":  "receptions",
    }
    weekly_2025 = weekly_2025.rename(columns={k: v for k, v in col_renames.items() if k in weekly_2025.columns})

    # Drop duplicate columns if any caused by renaming
    weekly_2025 = weekly_2025.loc[:, ~weekly_2025.columns.duplicated()]

    # Add PPR points if missing
    if "fantasy_points_ppr" not in weekly_2025.columns and "fantasy_points" in weekly_2025.columns:
        rec = weekly_2025["receptions"] if "receptions" in weekly_2025.columns else 0
        weekly_2025["fantasy_points_ppr"] = weekly_2025["fantasy_points"] + rec * 0.5

    print(f"   Normalized columns: {list(weekly_2025.columns[:20])}...")

    # Load snap counts for 2025
    try:
        snaps_2025 = nfl_new.load_snap_counts([2025]).to_pandas()
    except Exception as snap_err:
        print(f"   snap counts unavailable: {snap_err}")
        snaps_2025 = pd.DataFrame()

    compute_and_save(weekly_2025, snaps_2025, 2025)

except Exception as e:
    import traceback
    print(f"nflreadpy error: {e}")
    traceback.print_exc()

print("\n🏈 All done!")
