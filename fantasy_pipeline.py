"""
fantasy_pipeline.py
====================
2024 data: nfl-data-py
2025 data: nflreadpy
Includes PBP-derived stats: red zone targets, goal line usage, opportunity share
"""

import pandas as pd
import os

OUTPUT_DIR = "data"

def safe_div(a, b, decimals=2):
    return (a / b.where(b != 0)).round(decimals)

def compute_pbp_stats(pbp_raw, year):
    """Extract red zone and goal line stats from play-by-play data."""
    print(f"   📊 Processing PBP for red zone stats...")
    try:
        pbp = pbp_raw[pbp_raw["season_type"] == "REG"].copy()

        # Ensure required columns exist
        required = ["yardline_100", "posteam", "pass_attempt", "rush_attempt",
                    "touchdown", "receiver_player_name", "rusher_player_name"]
        missing = [c for c in required if c not in pbp.columns]
        if missing:
            print(f"   ⚠️ PBP missing columns: {missing}")
            return {}, {}

        pbp["yardline_100"] = pd.to_numeric(pbp["yardline_100"], errors="coerce")
        pbp["pass_attempt"] = pd.to_numeric(pbp["pass_attempt"], errors="coerce").fillna(0)
        pbp["rush_attempt"] = pd.to_numeric(pbp["rush_attempt"], errors="coerce").fillna(0)
        pbp["touchdown"]    = pd.to_numeric(pbp["touchdown"], errors="coerce").fillna(0)

        rz  = pbp[pbp["yardline_100"] <= 20]   # red zone
        gl  = pbp[pbp["yardline_100"] <= 5]    # goal line

        # ── PLAYER STATS ─────────────────────────────────────────────────────
        player_stats = {}

        # Red zone targets (WR/TE)
        rz_pass = rz[rz["pass_attempt"] == 1]
        rz_tgts = rz_pass.groupby("receiver_player_name").size().reset_index(name="rz_targets")
        rz_tgts = rz_tgts.rename(columns={"receiver_player_name": "player_display_name"})

        # Goal line carries (RB)
        gl_rush = gl[gl["rush_attempt"] == 1]
        gl_carries = gl_rush.groupby("rusher_player_name").size().reset_index(name="gl_carries")
        gl_carries = gl_carries.rename(columns={"rusher_player_name": "player_display_name"})

        # Goal line targets (RB)
        gl_pass = gl[gl["pass_attempt"] == 1]
        gl_tgts = gl_pass.groupby("receiver_player_name").size().reset_index(name="gl_targets")
        gl_tgts = gl_tgts.rename(columns={"receiver_player_name": "player_display_name"})

        player_stats["rz_targets"]  = rz_tgts
        player_stats["gl_carries"]  = gl_carries
        player_stats["gl_targets"]  = gl_tgts

        # ── TEAM STATS ───────────────────────────────────────────────────────
        team_stats = {}

        # Red zone pass/run rate
        rz_plays = rz[(rz["pass_attempt"] == 1) | (rz["rush_attempt"] == 1)]
        rz_team = rz_plays.groupby("posteam").agg(
            rz_pass_plays=("pass_attempt", "sum"),
            rz_rush_plays=("rush_attempt", "sum"),
            rz_total_plays=("pass_attempt", "count"),
        ).reset_index()
        rz_team["rz_pass_rate"] = safe_div(rz_team["rz_pass_plays"], rz_team["rz_total_plays"], 3)
        rz_team["rz_run_rate"]  = safe_div(rz_team["rz_rush_plays"],  rz_team["rz_total_plays"], 3)

        # Red zone conversion rate (TD per red zone trip)
        # A red zone trip = first play inside 20 with a new drive sequence
        rz_tds = rz[rz["touchdown"] == 1].groupby("posteam").size().reset_index(name="rz_tds")
        rz_total = rz_plays.groupby("posteam").size().reset_index(name="rz_plays")
        rz_conv = rz_tds.merge(rz_total, on="posteam", how="outer").fillna(0)
        rz_conv["rz_conversion_rate"] = safe_div(rz_conv["rz_tds"], rz_conv["rz_plays"], 3)

        rz_team = rz_team.merge(rz_conv[["posteam","rz_tds","rz_conversion_rate"]], on="posteam", how="left")
        rz_team = rz_team.rename(columns={"posteam": "team"})

        team_stats["rz_team"] = rz_team

        print(f"   ✅ PBP stats computed")
        return player_stats, team_stats

    except Exception as e:
        import traceback
        print(f"   ❌ PBP stats failed: {e}")
        traceback.print_exc()
        return {}, {}


def compute_and_save(weekly_raw, snaps_raw, year, pbp_raw=None):
    print(f"\n{'='*50}")
    print(f"  PROCESSING {year} SEASON")
    print(f"{'='*50}")

    year_dir = os.path.join(OUTPUT_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)

    weekly = weekly_raw[weekly_raw["season_type"] == "REG"].copy()
    snaps  = snaps_raw[snaps_raw["game_type"] == "REG"].copy() if "game_type" in snaps_raw.columns else snaps_raw.copy()
    print(f"   {len(weekly)} rows · weeks {weekly['week'].min()}–{weekly['week'].max()}")

    # ── PBP STATS ─────────────────────────────────────────────────────────────
    player_pbp, team_pbp = {}, {}
    if pbp_raw is not None:
        player_pbp, team_pbp = compute_pbp_stats(pbp_raw, year)

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
    name_col = next((c for c in ["player_display_name", "player_name"] if c in weekly.columns), None)
    if name_col is None:
        print("❌ Could not find player name column")
        return

    group_cols = [c for c in ["player_id", name_col, "position", "recent_team"] if c in weekly.columns]
    agg = weekly.groupby(group_cols).agg(**valid_agg).reset_index()
    if name_col != "player_display_name":
        agg = agg.rename(columns={name_col: "player_display_name"})

    # ── OPPORTUNITY SHARE ─────────────────────────────────────────────────────
    # Compute from weekly data: (carries + targets) / team total per week
    if "carries" in weekly.columns and "targets" in weekly.columns:
        wk = weekly.copy()
        team_col = "recent_team" if "recent_team" in wk.columns else None
        if team_col:
            wk["opportunities"] = wk["carries"].fillna(0) + wk["targets"].fillna(0)
            team_opp = wk.groupby([team_col, "week"])["opportunities"].sum().reset_index()
            team_opp = team_opp.rename(columns={"opportunities": "team_opp"})
            wk = wk.merge(team_opp, on=[team_col, "week"], how="left")
            wk["opp_share_wk"] = wk["opportunities"] / wk["team_opp"].replace(0, float("nan"))

            name_wk = name_col if name_col in wk.columns else "player_display_name"
            opp_share = wk.groupby(name_wk)["opp_share_wk"].mean().reset_index()
            opp_share.columns = ["player_display_name", "opportunity_share"]
            opp_share["opportunity_share"] = opp_share["opportunity_share"].round(3)
            agg = agg.merge(opp_share, on="player_display_name", how="left")

    # ── SNAP % ────────────────────────────────────────────────────────────────
    if "offense_pct" in snaps.columns and "player" in snaps.columns and "team" in snaps.columns:
        snap_by_name = (
            snaps.groupby(["player", "team"])
            .agg(avg_snap_pct=("offense_pct", "mean"))
            .reset_index()
            .rename(columns={"player": "player_display_name", "team": "recent_team"})
        )
        agg = agg.merge(snap_by_name, on=["player_display_name", "recent_team"], how="left")

    # ── MERGE PBP PLAYER STATS ────────────────────────────────────────────────
    if player_pbp.get("rz_targets") is not None:
        agg = agg.merge(player_pbp["rz_targets"], on="player_display_name", how="left")
    if player_pbp.get("gl_carries") is not None:
        agg = agg.merge(player_pbp["gl_carries"], on="player_display_name", how="left")
    if player_pbp.get("gl_targets") is not None:
        agg = agg.merge(player_pbp["gl_targets"], on="player_display_name", how="left")

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
    team_splits = team_pass.rename(columns={"recent_team": "team"}).sort_values("pass_rate", ascending=False)

    # Merge red zone team stats if available
    if team_pbp.get("rz_team") is not None:
        team_splits = team_splits.merge(team_pbp["rz_team"], on="team", how="left")

    team_splits.to_csv(os.path.join(year_dir, "team_splits.csv"), index=False)
    print(f"   ✅ Team splits saved")

    # ── EXPORT BY POSITION ────────────────────────────────────────────────────
    POSITION_COLS = {
        "QB": ["player_display_name","recent_team","games","fantasy_points_ppr","fppg_ppr",
               "passing_yards","passing_tds","interceptions","comp_pct","yards_per_attempt",
               "td_rate","sacks","carries","rushing_yards","rushing_tds","fppg"],
        "RB": ["player_display_name","recent_team","games","fantasy_points_ppr","fppg_ppr",
               "carries","rushing_yards","rushing_tds","ypc","targets","receptions",
               "receiving_yards","receiving_tds","target_share","opportunity_share",
               "gl_carries","gl_targets","catch_rate","yac_per_rec","avg_snap_pct"],
        "WR": ["player_display_name","recent_team","games","fantasy_points_ppr","fppg_ppr",
               "targets","receptions","receiving_yards","receiving_tds","rz_targets",
               "target_share","air_yards_share","wopr","racr","adot","catch_rate",
               "yards_per_target","yac_per_rec","avg_snap_pct"],
        "TE": ["player_display_name","recent_team","games","fantasy_points_ppr","fppg_ppr",
               "targets","receptions","receiving_yards","receiving_tds","rz_targets",
               "target_share","air_yards_share","wopr","racr","adot","catch_rate",
               "yards_per_target","avg_snap_pct"],
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

print("📥 Loading 2024 PBP data...")
try:
    pbp_2024 = nfl_old.import_pbp_data([2024], columns=[
        "season_type","yardline_100","posteam","pass_attempt","rush_attempt",
        "touchdown","receiver_player_name","rusher_player_name","play_type"
    ])
    print(f"   ✅ PBP 2024: {len(pbp_2024)} plays")
except Exception as e:
    print(f"   ⚠️ PBP 2024 unavailable: {e}")
    pbp_2024 = None

compute_and_save(weekly_2024, snaps_2024, 2024, pbp_2024)

# ── 2025 via nflreadpy ────────────────────────────────────────────────────────
print("\n📦 Loading 2025 data via nflreadpy...")
try:
    import nflreadpy as nfl_new
    weekly_2025 = nfl_new.load_player_stats([2025]).to_pandas()
    col_renames = {
        "team": "recent_team", "passing_interceptions": "interceptions",
        "sacks_suffered": "sacks", "rushing_attempts": "carries",
        "receiving_targets": "targets", "receiving_receptions": "receptions",
    }
    weekly_2025 = weekly_2025.rename(columns={k: v for k, v in col_renames.items() if k in weekly_2025.columns})
    weekly_2025 = weekly_2025.loc[:, ~weekly_2025.columns.duplicated()]
    if "fantasy_points_ppr" not in weekly_2025.columns and "fantasy_points" in weekly_2025.columns:
        rec = weekly_2025["receptions"] if "receptions" in weekly_2025.columns else 0
        weekly_2025["fantasy_points_ppr"] = weekly_2025["fantasy_points"] + rec * 0.5

    try:
        snaps_2025 = nfl_new.load_snap_counts([2025]).to_pandas()
    except Exception:
        snaps_2025 = pd.DataFrame()

    print("📥 Loading 2025 PBP data...")
    try:
        pbp_2025 = nfl_new.load_pbp([2025]).to_pandas()
        print(f"   ✅ PBP 2025: {len(pbp_2025)} plays")
    except Exception as e:
        print(f"   ⚠️ PBP 2025 unavailable: {e}")
        pbp_2025 = None

    compute_and_save(weekly_2025, snaps_2025, 2025, pbp_2025)

except Exception as e:
    import traceback
    print(f"nflreadpy error: {e}")
    traceback.print_exc()

print("\n🏈 All done!")
