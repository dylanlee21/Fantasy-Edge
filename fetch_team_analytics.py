"""
fetch_team_analytics.py
Generates data/{year}/team_analytics.csv with team-level fantasy-relevant stats.
Columns: team, games, pass_rate, run_rate, pass_yds_game, rush_yds_game,
         pts_game, pts_allowed_game, yds_per_play, rz_attempts, rz_conv_pct,
         third_down_pct, sacks_allowed

Run: py -3.12 fetch_team_analytics.py
"""

import pandas as pd
import os

try:
    import nflreadpy as nfl
except ImportError:
    raise SystemExit("pip install nflreadpy --break-system-packages")

YEARS = [2024, 2025]

for year in YEARS:
    print(f"\nProcessing {year}...")
    pbp = nfl.load_pbp([year])
    if hasattr(pbp, 'to_pandas'):
        pbp = pbp.to_pandas()

    # Regular season plays only
    plays = pbp[
        (pbp["season_type"] == "REG") &
        (pbp["play_type"].isin(["run", "pass"])) &
        (pbp["posteam"].notna())
    ].copy()

    pass_plays = plays[plays["play_type"] == "pass"]
    run_plays  = plays[plays["play_type"] == "run"]

    # Scoring: sum posteam_score_post - posteam_score_pre per game per team
    score_df = pbp[
        (pbp["season_type"] == "REG") &
        (pbp["posteam"].notna()) &
        (pbp["posteam_score_post"].notna()) &
        (pbp["posteam_score_pre"].notna())
    ].copy()
    score_df["pts_gained"] = score_df["posteam_score_post"] - score_df["posteam_score_pre"]

    # Points allowed — from defteam perspective
    allowed_df = pbp[
        (pbp["season_type"] == "REG") &
        (pbp["defteam"].notna()) &
        (pbp["posteam_score_post"].notna()) &
        (pbp["posteam_score_pre"].notna())
    ].copy()
    allowed_df["pts_allowed"] = allowed_df["posteam_score_post"] - allowed_df["posteam_score_pre"]

    teams = sorted(plays["posteam"].dropna().unique())
    rows  = []

    for team in teams:
        tp = plays[plays["posteam"] == team]
        pp = pass_plays[pass_plays["posteam"] == team]
        rp = run_plays[run_plays["posteam"] == team]

        total = len(tp)
        if total < 10:
            continue

        games = int(tp["game_id"].nunique())

        # Pass / run rate
        pass_rate = round(len(pp) / total * 100, 1)
        run_rate  = round(len(rp)  / total * 100, 1)

        # Yards per game
        pass_yds = pp["passing_yards"].fillna(0).sum() if "passing_yards" in pp.columns else 0
        rush_yds = rp["rushing_yards"].fillna(0).sum() if "rushing_yards" in rp.columns else 0
        pass_yds_game = round(pass_yds / games, 1)
        rush_yds_game = round(rush_yds / games, 1)

        # Yards per play
        total_yds = pass_yds + rush_yds
        ypp = round(total_yds / total, 2) if total > 0 else 0.0

        # Points scored / allowed per game
        team_pts     = score_df[score_df["posteam"] == team]["pts_gained"].clip(lower=0).sum()
        team_allowed = allowed_df[allowed_df["defteam"] == team]["pts_allowed"].clip(lower=0).sum()
        pts_game     = round(team_pts / games, 1)
        pts_allowed_game = round(team_allowed / games, 1)

        # Red zone (inside 20) conversion %
        rz = tp[tp["yardline_100"] <= 20] if "yardline_100" in tp.columns else pd.DataFrame()
        rz_att = len(rz)
        rz_tds = int(rz["touchdown"].fillna(0).sum()) if ("touchdown" in rz.columns and len(rz) > 0) else 0
        rz_conv_pct = round(rz_tds / rz_att * 100, 1) if rz_att > 0 else 0.0

        # 3rd down conversion %
        if "down" in tp.columns and "first_down" in tp.columns:
            third     = tp[tp["down"] == 3]
            third_conv = third[third["first_down"] == 1]
            third_pct = round(len(third_conv) / len(third) * 100, 1) if len(third) > 0 else 0.0
        else:
            third_pct = 0.0

        # Sacks allowed (team on offense, QB sacked)
        sacks_allowed = int(pp["sack"].fillna(0).sum()) if "sack" in pp.columns else 0

        rows.append({
            "team":              team,
            "games":             games,
            "pass_rate":         pass_rate,
            "run_rate":          run_rate,
            "pass_yds_game":     pass_yds_game,
            "rush_yds_game":     rush_yds_game,
            "total_yds_game":    round(pass_yds_game + rush_yds_game, 1),
            "yds_per_play":      ypp,
            "pts_game":          pts_game,
            "pts_allowed_game":  pts_allowed_game,
            "rz_attempts":       rz_att,
            "rz_conv_pct":       rz_conv_pct,
            "third_down_pct":    third_pct,
            "sacks_allowed":     sacks_allowed,
        })

    df = pd.DataFrame(rows).sort_values("team").reset_index(drop=True)
    out = os.path.join("data", str(year), "team_analytics.csv")
    df.to_csv(out, index=False)
    print(f"✓ {len(df)} teams → {out}")
    print(df[["team","pass_rate","run_rate","pts_game","rz_conv_pct"]].head(8).to_string(index=False))

print("\nDone.")
