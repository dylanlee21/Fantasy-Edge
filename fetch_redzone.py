"""
fetch_redzone.py
Computes red zone rushing & receiving stats for RBs (inside 20, 10, 5)
from 2025 play-by-play data via nflreadpy.

Removes old goal_line columns and replaces with:
  rz_car_20, rz_car_10, rz_car_5   (rush attempts)
  rz_tgt_20, rz_tgt_10, rz_tgt_5   (receiving targets)

Run: py -3.12 fetch_redzone.py
"""

import pandas as pd
import os

try:
    import nflreadpy as nfl
except ImportError:
    raise SystemExit("Install nflreadpy first:  pip install nflreadpy --break-system-packages")

RB_CSV  = os.path.join("data", "2025", "rb_stats.csv")
WR_CSV  = os.path.join("data", "2025", "wr_stats.csv")
TE_CSV  = os.path.join("data", "2025", "te_stats.csv")

OLD_GL_COLS = ["gl_carries", "gl_targets", "gl_car", "gl_tgt",
               "rz_carries", "rz_targets", "rz_car", "rz_tgt"]

def drop_old_cols(df):
    return df.drop(columns=[c for c in OLD_GL_COLS if c in df.columns], errors="ignore")

print("Loading 2025 play-by-play data...")
pbp = nfl.load_pbp([2025])

# Filter to regular season pass/rush plays with valid yardline
plays = pbp[
    (pbp["season_type"] == "REG") &
    (pbp["play_type"].isin(["run", "pass"])) &
    (pbp["yardline_100"].notna())
].copy()

# ── RB RED ZONE CARRIES (rush attempts) ──────────────────────────────────────
rush_plays = plays[
    (plays["play_type"] == "run") &
    (plays["rusher_player_id"].notna()) &
    (plays["rusher_player_name"].notna())
].copy()

def rz_carries(df, yard_line):
    rz = df[df["yardline_100"] <= yard_line]
    return rz.groupby("rusher_player_name").size().reset_index(name=f"rz_car_{yard_line}")

car_20 = rz_carries(rush_plays, 20)
car_10 = rz_carries(rush_plays, 10)
car_5  = rz_carries(rush_plays, 5)

rb_rz = car_20.merge(car_10, on="rusher_player_name", how="outer") \
              .merge(car_5,  on="rusher_player_name", how="outer") \
              .fillna(0)
rb_rz.columns = ["player_display_name", "rz_car_20", "rz_car_10", "rz_car_5"]
rb_rz[["rz_car_20","rz_car_10","rz_car_5"]] = \
    rb_rz[["rz_car_20","rz_car_10","rz_car_5"]].astype(int)

# ── RB / WR / TE RED ZONE TARGETS (receiving targets) ────────────────────────
pass_plays = plays[
    (plays["play_type"] == "pass") &
    (plays["receiver_player_id"].notna()) &
    (plays["receiver_player_name"].notna())
].copy()

def rz_targets(df, yard_line):
    rz = df[df["yardline_100"] <= yard_line]
    return rz.groupby("receiver_player_name").size().reset_index(name=f"rz_tgt_{yard_line}")

tgt_20 = rz_targets(pass_plays, 20)
tgt_10 = rz_targets(pass_plays, 10)
tgt_5  = rz_targets(pass_plays, 5)

recv_rz = tgt_20.merge(tgt_10, on="receiver_player_name", how="outer") \
               .merge(tgt_5,  on="receiver_player_name", how="outer") \
               .fillna(0)
recv_rz.columns = ["player_display_name", "rz_tgt_20", "rz_tgt_10", "rz_tgt_5"]
recv_rz[["rz_tgt_20","rz_tgt_10","rz_tgt_5"]] = \
    recv_rz[["rz_tgt_20","rz_tgt_10","rz_tgt_5"]].astype(int)

# ── MERGE INTO CSVs ──────────────────────────────────────────────────────────
def merge_and_save(csv_path, new_data, label):
    if not os.path.exists(csv_path):
        print(f"  ✗ Not found: {csv_path}")
        return
    df = pd.read_csv(csv_path, index_col=0)
    df = drop_old_cols(df)
    name_col = next((c for c in ["player_display_name","player","name"] if c in df.columns), None)
    if not name_col:
        print(f"  ✗ No name column in {csv_path}")
        return
    # PBP names are short (e.g. "J.Taylor"); try direct merge then fallback
    before = len(df)
    merged = df.merge(new_data.rename(columns={"player_display_name": name_col}),
                      on=name_col, how="left")
    merged.to_csv(csv_path)
    added = [c for c in new_data.columns if c != "player_display_name"]
    matched = merged[added[0]].notna().sum()
    print(f"  ✓ {label}: added {added} — {matched}/{before} players matched")

print("\nUpdating RB stats (carries + targets)...")
rb_both = rb_rz.merge(recv_rz, on="player_display_name", how="outer").fillna(0)
rb_both[["rz_car_20","rz_car_10","rz_car_5",
          "rz_tgt_20","rz_tgt_10","rz_tgt_5"]] = \
    rb_both[["rz_car_20","rz_car_10","rz_car_5",
              "rz_tgt_20","rz_tgt_10","rz_tgt_5"]].astype(int)
merge_and_save(RB_CSV, rb_both, "RB")

print("Updating WR stats (targets only)...")
merge_and_save(WR_CSV, recv_rz, "WR")

print("Updating TE stats (targets only)...")
merge_and_save(TE_CSV, recv_rz, "TE")

print("\nDone. New columns:")
print("  RB: rz_car_20, rz_car_10, rz_car_5, rz_tgt_20, rz_tgt_10, rz_tgt_5")
print("  WR: rz_tgt_20, rz_tgt_10, rz_tgt_5")
print("  TE: rz_tgt_20, rz_tgt_10, rz_tgt_5")
