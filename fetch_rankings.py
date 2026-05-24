"""
fetch_rankings.py
==================
Pulls 2026 PPR fantasy football rankings from:
  1. FantasyCalc  — free API (primary source)
  2. FF Calculator — free ADP API
  3. FantasyPros   — public ECR scrape
  4. ESPN          — unofficial API
"""

import requests
import pandas as pd
import os
import json
import time
import re

OUTPUT_DIR = os.path.join("data", "2026")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
}

# ── 1. FANTASYCALC ────────────────────────────────────────────────────────────
def fetch_fantasycalc():
    print("📥 Fetching FantasyCalc rankings...")
    try:
        url = "https://api.fantasycalc.com/values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        rows = []
        for item in r.json():
            p = item.get("player", {})
            pos = p.get("position", "")
            if pos not in ["QB", "RB", "WR", "TE"]:
                continue
            rows.append({
                "player":      p.get("name", ""),
                "position":    pos,
                "team":        p.get("maybeTeam", ""),
                "fc_rank":     item.get("overallRank"),
                "fc_pos_rank": item.get("positionRank"),
                "fc_value":    item.get("value"),
            })
        df = pd.DataFrame(rows).sort_values("fc_rank").drop_duplicates("player", keep="first")
        print(f"   ✅ FantasyCalc: {len(df)} players")
        return df
    except Exception as e:
        print(f"   ❌ FantasyCalc failed: {e}")
        return pd.DataFrame()

# ── 2. FANTASY FOOTBALL CALCULATOR (ADP) ──────────────────────────────────────
def fetch_ffcalculator():
    print("📥 Fetching Fantasy Football Calculator ADP...")
    try:
        url = "https://fantasyfootballcalculator.com/api/v1/adp/ppr?teams=12&year=2026"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        rows = []
        for p in r.json().get("players", []):
            pos = p.get("position", "")
            if pos not in ["QB", "RB", "WR", "TE"]:
                continue
            rows.append({
                "player":   p.get("name", ""),
                "position": pos,
                "team":     p.get("team", ""),
                "ffc_adp":  p.get("adp"),
                "ffc_rank": p.get("pick"),
            })
        df = pd.DataFrame(rows).sort_values("ffc_adp").drop_duplicates("player", keep="first")
        print(f"   ✅ FF Calculator: {len(df)} players")
        return df
    except Exception as e:
        print(f"   ❌ FF Calculator failed: {e}")
        return pd.DataFrame()

# ── 3. FANTASYPROS ECR ────────────────────────────────────────────────────────
def fetch_fantasypros():
    print("📥 Fetching FantasyPros ECR...")
    try:
        url = "https://www.fantasypros.com/nfl/rankings/ppr-cheatsheets.php"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()

        # Try multiple patterns for the ECR data
        patterns = [
            r"var ecrData = ({.*?});",
            r"ecrData\s*=\s*({.*?});",
            r'"players"\s*:\s*(\[.*?\])\s*[,}]',
        ]
        players = []
        for pattern in patterns:
            match = re.search(pattern, r.text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                    if isinstance(parsed, list):
                        players = parsed
                    elif isinstance(parsed, dict):
                        players = parsed.get("players", [])
                    if players:
                        break
                except Exception:
                    continue

        if not players:
            raise Exception("ECR data not found in page")

        rows = []
        for i, p in enumerate(players, 1):
            pos = p.get("position", p.get("pos", ""))
            if pos not in ["QB", "RB", "WR", "TE"]:
                continue
            rank = p.get("rank_ecr") or p.get("rank") or p.get("overall_rank") or i
            rows.append({
                "player":      p.get("player_name", p.get("name", "")),
                "position":    pos,
                "team":        p.get("player_team_id", p.get("team", "")),
                "fp_rank":     float(rank),
                "fp_pos_rank": p.get("pos_rank", ""),
                "fp_best":     p.get("rank_min", p.get("best", "")),
                "fp_worst":    p.get("rank_max", p.get("worst", "")),
                "fp_stdev":    p.get("rank_std", p.get("std_dev", "")),
            })

        df = pd.DataFrame(rows)
        df = df[df["player"] != ""]
        df = df.sort_values("fp_rank").drop_duplicates("player", keep="first")
        print(f"   ✅ FantasyPros: {len(df)} players")
        return df
    except Exception as e:
        print(f"   ❌ FantasyPros failed: {e}")
        return pd.DataFrame()

# ── 4. ESPN ───────────────────────────────────────────────────────────────────
def fetch_espn():
    print("📥 Fetching ESPN rankings...")
    try:
        rows = []
        # Use ESPN's draft rankings endpoint with proper filters
        for offset in range(0, 600, 100):
            url = (
                "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/players"
                f"?scoringPeriodId=0&view=kona_player_info&offset={offset}&limit=100"
                "&filterRanksForScoringPeriodIds=%7B%22value%22%3A%5B0%5D%7D"
                "&filterRanksForRankTypes=%7B%22value%22%3A%5B%22PPR%22%5D%7D"
                "&filterRanksForSlotIds=%7B%22value%22%3A%5B0%2C2%2C4%2C6%2C17%2C16%2C8%2C9%2C10%2C12%2C13%2C24%5D%7D"
            )
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json",
                "X-Fantasy-Filter": json.dumps({"players": {"filterSlotIds": {"value": [0,2,4,6,17,16,8,9,10,12,13,24]}, "limit": 100, "offset": offset, "sortDraftRanks": {"sortPriority": 2, "sortAsc": True, "value": "PPR"}, "filterRanksForScoringPeriodIds": {"value": [0]}, "filterRanksForRankTypes": {"value": ["PPR"]}}})
            }, timeout=15)
            if r.status_code != 200:
                break
            data = r.json()
            if not data:
                break
            for p in data:
                pos_map = {1: "QB", 2: "RB", 3: "WR", 4: "TE"}
                pos = pos_map.get(p.get("defaultPositionId", 0), "")
                if not pos:
                    continue
                ppr_rank = p.get("draftRanksByRankType", {}).get("PPR", {}).get("rank")
                if not ppr_rank or ppr_rank > 300:
                    continue
                rows.append({
                    "player":    p.get("fullName", ""),
                    "position":  pos,
                    "espn_rank": int(ppr_rank),
                })
            if len(data) < 100:
                break
            time.sleep(0.5)

        if not rows:
            print("   ⚠️ ESPN: no data returned — skipping")
            return pd.DataFrame()

        df = pd.DataFrame(rows).dropna(subset=["espn_rank"])
        df = df.sort_values("espn_rank").drop_duplicates("player", keep="first")
        print(f"   ✅ ESPN: {len(df)} players")
        return df
    except Exception as e:
        print(f"   ❌ ESPN failed: {e}")
        return pd.DataFrame()

# ── RUN ALL ───────────────────────────────────────────────────────────────────
print("\n🏈 Fetching 2026 rankings from all sources...\n")

fc   = fetch_fantasycalc()
ffc  = fetch_ffcalculator()
fp   = fetch_fantasypros()
espn = fetch_espn()

for name, df in {"fantasycalc": fc, "ffc_adp": ffc, "fantasypros": fp, "espn": espn}.items():
    if not df.empty:
        df.to_csv(os.path.join(OUTPUT_DIR, f"{name}.csv"), index=False)
        print(f"   💾 Saved {name}")

# ── LOAD ROTOBALLER (manually entered) ───────────────────────────────────────
def load_rotoballer():
    path = os.path.join(OUTPUT_DIR, "rotoballer.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"   ✅ RotoBaller: {len(df)} players loaded from CSV")
        return df
    print("   ⚠️ RotoBaller CSV not found — run create_rotoballer.py first")
    return pd.DataFrame()

rb_data = load_rotoballer()

# ── MASTER TABLE ──────────────────────────────────────────────────────────────
print("\n🔧 Building master rankings table...")

# Use FantasyCalc as the base — it has the most complete vetted player list
if not fc.empty:
    master = fc[["player", "position", "team", "fc_rank", "fc_pos_rank", "fc_value"]].copy()

    if not ffc.empty:
        master = master.merge(ffc[["player", "ffc_adp", "ffc_rank"]], on="player", how="left")
    if not fp.empty:
        master = master.merge(fp[["player", "fp_rank", "fp_pos_rank", "fp_best", "fp_worst", "fp_stdev"]], on="player", how="left")
    if not espn.empty:
        master = master.merge(espn[["player", "espn_rank"]], on="player", how="left")
    if not rb_data.empty:
        master = master.merge(rb_data[["player", "rb_overall_rank", "rb_pos_rank"]], on="player", how="left")

    # Add 2025 FPPG from our pipeline data for context
    try:
        pos_dfs = []
        for pos in ["QB", "RB", "WR", "TE"]:
            path = os.path.join("data", "2025", f"{pos.lower()}_stats.csv")
            if os.path.exists(path):
                df = pd.read_csv(path, index_col=0)[["player_display_name", "fppg_ppr"]].copy()
                df = df.rename(columns={"player_display_name": "player", "fppg_ppr": "2025_fppg_ppr"})
                pos_dfs.append(df)
        if pos_dfs:
            stats_df = pd.concat(pos_dfs).drop_duplicates("player", keep="first")
            master = master.merge(stats_df, on="player", how="left")
    except Exception as e:
        print(f"   ⚠️ Could not merge 2025 stats: {e}")

    # Deduplicate
    master = master.drop_duplicates("player", keep="first")

    # Consensus rank — average only external sources
    rank_cols = [c for c in ["fc_rank", "ffc_rank", "fp_rank", "espn_rank", "rb_overall_rank"] if c in master.columns]
    master["consensus_rank"] = master[rank_cols].mean(axis=1).round(1)
    master = master.sort_values("consensus_rank").reset_index(drop=True)
    master.index += 1
    master.index.name = "overall_rank"

    master.to_csv(os.path.join(OUTPUT_DIR, "master_rankings.csv"))
    print(f"   ✅ Master: {len(master)} players · sources: {', '.join(rank_cols)}")

print("\n✅ 2026 rankings complete!")
