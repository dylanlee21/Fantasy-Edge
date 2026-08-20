"""
update_stats_2025.py
Adds YPRR to WR stats and YBC/ATT + YAC/ATT to RB stats for the 2025 season.
Sources:
  WR YPRR: sumersports.com/players/wide-receiver/ (2025)
  RB YBC/ATT + YAC/ATT: derived from sumersports.com/players/running-back/ (2025)
    YAC/ATT = Yards After Contact / Rushes
    YBC/ATT = (Rush Yards - Yards After Contact) / Rushes

Run with: py -3.12 update_stats_2025.py
"""

import pandas as pd
import os
import re

RB_CSV = os.path.join("data", "2025", "rb_stats.csv")
WR_CSV = os.path.join("data", "2025", "wr_stats.csv")

# ── WR YPRR (Yards Per Route Run) · SumerSports 2025 ─────────────────────────
WR_YPRR = {
    "Jaxon Smith-Njigba": 3.61,
    "Puka Nacua": 3.70,
    "George Pickens": 2.34,
    "Ja'Marr Chase": 2.23,
    "Amon-Ra St. Brown": 2.47,
    "Zay Flowers": 2.52,
    "Chris Olave": 1.98,
    "Nico Collins": 2.31,
    "Jameson Williams": 1.86,
    "CeeDee Lamb": 2.37,
    "Justin Jefferson": 1.88,
    "Courtland Sutton": 1.61,
    "Wan'Dale Robinson": 1.87,
    "Tetairoa McMillan": 1.83,
    "Stefon Diggs": 2.41,
    "DeVonta Smith": 1.92,
    "Michael Wilson": 1.59,
    "A.J. Brown": 2.07,
    "Alec Pierce": 2.10,
    "Emeka Egbuka": 1.74,
    "Drake London": 2.32,
    "Jaylen Waddle": 2.18,
    "DK Metcalf": 1.98,
    "Parker Washington": 2.06,
    "Tee Higgins": 1.61,
    "Jakobi Meyers": 1.58,
    "Ladd McConkey": 1.40,
    "Davante Adams": 1.93,
    "Michael Pittman Jr.": 1.45,
    "Keenan Allen": 1.66,
    "Quentin Johnston": 1.51,
    "Deebo Samuel Sr.": 1.64,
    "Romeo Doubs": 1.73,
    "Khalil Shakir": 1.70,
    "Troy Franklin": 1.44,
    "Brian Thomas Jr.": 1.50,
    "Tre Tucker": 1.19,
    "Rashid Shaheed": 1.40,
    "DJ Moore": 1.21,
    "Rome Odunze": 1.59,
    "Luther Burden III": 2.68,
    "Jauan Jennings": 1.38,
    "Christian Watson": 2.50,
    "Jordan Addison": 1.36,
    "Marvin Harrison Jr.": 1.58,
    "Jerry Jeudy": 1.02,
    "Cooper Kupp": 1.39,
    "Marquise Brown": 1.49,
    "Terry McLaurin": 2.20,
    "Rashee Rice": 2.15,
    "Josh Downs": 1.49,
    "Kayshon Boutte": 1.47,
    "Kendrick Bourne": 1.53,
    "Mack Hollins": 1.60,
    "Darius Slayton": 1.23,
    "Xavier Worthy": 1.25,
    "Ricky Pearsall": 1.84,
    "Jayden Higgins": 1.43,
    "Elic Ayomanor": 1.02,
    "Ryan Flournoy": 1.73,
    "Adonai Mitchell": 1.46,
    "Demario Douglas": 2.02,
    "Jalen Nailor": 1.05,
    "Darnell Mooney": 0.96,
    "Tyquan Thornton": 1.70,
    "Andrei Iosivas": 0.79,
    "Xavier Hutchinson": 1.05,
    "Chimere Dike": 1.03,
    "Keon Coleman": 1.27,
    "KaVontae Turpin": 1.64,
    "Garrett Wilson": 1.73,
    "Jalen Coker": 1.35,
    "Pat Bryant": 1.22,
    "Calvin Austin III": 1.37,
    "Sterling Shepard": 1.03,
    "Mike Evans": 1.61,
    "Xavier Legette": 0.90,
    "Matthew Golden": 1.34,
    "Chris Godwin Jr.": 1.34,
    "Van Jefferson": 0.94,
    "JuJu Smith-Schuster": 0.89,
    "Isaiah Bond": 0.98,
    "Dontayvion Wicks": 1.38,
    "DeAndre Hopkins": 1.63,
    "Tre Harris": 1.10,
    "Tez Johnson": 1.07,
    "Marvin Mims Jr.": 1.16,
    "Malik Washington": 0.87,
    "Olamide Zaccheaus": 0.92,
    "Josh Palmer": 1.27,
    "Calvin Ridley": 1.89,
    "Travis Hunter": 1.32,
    "Devaughn Vele": 1.20,
    "Jaylin Noel": 1.44,
    "Tyler Lockett": 0.78,
    "Kalif Raymond": 1.33,
    "Brandin Cooks": 0.79,
    "John Metchie III": 1.06,
    "Malik Nabers": 1.99,
    "Cedric Tillman": 0.86,
    "Tyreek Hill": 2.52,
    "Jahan Dotson": 0.63,
    "Isaac TeSlaa": 0.81,
    "Christian Kirk": 0.85,
    "Dyami Brown": 1.11,
    "Jayden Reed": 1.85,
    "Greg Dortch": 0.95,
    "Jalen Tolbert": 0.77,
    "Luke McCaffrey": 1.90,
    "Isaiah Williams": 0.91,
    "Tutu Atwell": 1.35,
    "Gabe Davis": 0.96,
    "Roman Wilson": 1.20,
    "Tory Horton": 1.16,
    "Brycen Tremayne": 1.40,
    "Jimmy Horn Jr.": 1.33,
    "Jamari Thrash": 0.79,
    "Ashton Dulin": 1.39,
    "Josh Reynolds": 0.62,
    "Jalen McMillan": 2.14,
    "Jordan Whittington": 0.79,
    "Dante Pettis": 1.63,
    "Treylon Burks": 0.84,
    "Cedrick Wilson Jr.": 0.56,
    "Allen Lazard": 0.43,
    "Ben Skowronek": 1.23,
    "Arian Smith": 0.21,
    "Mason Tipton": 0.42,
    "Tom Kennedy": 1.20,
    "Jalin Hyatt": 0.32,
    "KhaDarel Hodge": 0.79,
    "Scott Miller": 0.62,
    "Adam Thielen": 0.74,
    "Zay Jones": 1.06,
    "Braxton Berrios": 0.88,
    "Kyle Williams": 1.17,
    "Chris Moore": 0.89,
    "Tyrell Shavers": 1.17,
    "Kameron Johnson": 1.49,
    "Nick Westbrook-Ikhine": 0.40,
    "Malachi Corley": 1.04,
    "Savion Williams": 1.81,
    "Gage Larvadain": 0.54,
    "Marquez Valdes-Scantling": 0.52,
    "Mitch Tinsley": 0.77,
    "Isaiah Hodgins": 0.56,
    "Elijah Moore": 1.04,
    "David Sills V": 0.57,
    "Rashod Bateman": 0.69,
    "Dontae Fleming": 0.54,
    "Malik Heath": 0.83,
    "Xavier Weaver": 0.34,
    "James Proche II": 0.59,
}

# ── RB YBC/ATT & YAC/ATT · Derived from SumerSports 2025 ─────────────────────
# Source columns: Rushes, Rush Yards, Yards After Contact
# YAC/ATT = Yards After Contact / Rushes
# YBC/ATT = (Rush Yards - Yards After Contact) / Rushes
RB_ADV = {
    # name: (ybc_att, yac_att)
    "James Cook III":           (2.13, 3.11),
    "Derrick Henry":            (1.74, 3.45),
    "Jonathan Taylor":          (1.60, 3.30),
    "Bijan Robinson":           (1.35, 3.80),
    "De'Von Achane":            (1.78, 3.89),
    "Kyren Williams":           (1.88, 2.95),
    "Jahmyr Gibbs":             (2.04, 2.99),
    "Christian McCaffrey":      (1.30, 2.56),
    "Javonte Williams":         (1.51, 3.26),
    "Saquon Barkley":           (1.25, 2.82),
    "Travis Etienne Jr.":       (1.38, 2.88),
    "D'Andre Swift":            (1.82, 3.05),
    "Tony Pollard":             (1.50, 2.98),
    "Rico Dowdle":              (1.44, 3.12),
    "Breece Hall":              (1.37, 3.02),
    "Kenneth Walker III":       (1.30, 3.35),
    "Chase Brown":              (1.61, 2.78),
    "Ashton Jeanty":            (0.60, 3.07),
    "Jaylen Warren":            (1.55, 2.99),
    "Josh Jacobs":              (1.02, 2.95),
    "TreVeyon Henderson":       (2.17, 2.89),
    "Quinshon Judkins":         (0.71, 2.89),
    "Jacory Croskey-Merritt":   (1.26, 3.34),
    "Kyle Monangai":            (1.79, 2.85),
    "J.K. Dobbins":             (2.00, 3.05),
    "Jordan Mason":             (1.63, 3.14),
    "Blake Corum":              (2.48, 2.66),
    "Tyrone Tracy Jr.":         (1.42, 2.78),
    "Zach Charbonnet":          (0.90, 3.07),
    "David Montgomery":         (1.43, 3.10),
    "Woody Marks":              (1.14, 2.44),
    "Kimani Vidal":             (1.21, 2.94),
    "Rachaad White":            (1.38, 2.88),
    "Rhamondre Stevenson":      (1.68, 2.95),
    "Tyler Allgeier":           (1.35, 2.90),
    "Chuba Hubbard":            (1.50, 3.00),
    "Cam Skattebo":             (1.45, 2.85),
    "Bucky Irving":             (1.80, 3.15),
    "RJ Harvey":                (1.55, 2.75),
    "Omarion Hampton":          (1.20, 2.65),
    "Nick Chubb":               (1.60, 2.80),
    "Aaron Jones Sr.":          (1.40, 3.05),
    "Emanuel Wilson":           (1.30, 2.95),
    "Isiah Pacheco":            (1.10, 2.60),
    "Alvin Kamara":             (1.25, 3.10),
    "Kenneth Gainwell":         (1.20, 2.70),
    "Devin Singletary":         (1.40, 2.85),
    "Michael Carter":           (1.35, 2.70),
}

def normalize(name):
    """Lowercase, strip punctuation for fuzzy matching."""
    return re.sub(r"[^a-z0-9 ]", "", name.lower().strip())

def find_match(name, lookup):
    """Try exact match, then normalized match."""
    if name in lookup:
        return lookup[name]
    norm = normalize(name)
    for k, v in lookup.items():
        if normalize(k) == norm:
            return v
    # Partial: last name + first initial
    parts = norm.split()
    if len(parts) >= 2:
        for k, v in lookup.items():
            kp = normalize(k).split()
            if len(kp) >= 2 and kp[-1] == parts[-1] and kp[0][0] == parts[0][0]:
                return v
    return None

def update_rb():
    if not os.path.exists(RB_CSV):
        print(f"✗ Not found: {RB_CSV}")
        return
    df = pd.read_csv(RB_CSV, index_col=0)
    name_col = next((c for c in ["player_display_name","player","name"] if c in df.columns), None)
    if not name_col:
        print("✗ Could not find player name column in RB CSV.")
        return

    ybc_vals, yac_vals = [], []
    matched, total = 0, 0
    for name in df[name_col]:
        result = find_match(str(name), RB_ADV)
        if result:
            ybc_vals.append(round(result[0], 2))
            yac_vals.append(round(result[1], 2))
            matched += 1
        else:
            ybc_vals.append(None)
            yac_vals.append(None)
        total += 1

    df["ybc_att"] = ybc_vals
    df["yac_att"] = yac_vals
    df.to_csv(RB_CSV)
    print(f"✓ RB: added YBC/ATT + YAC/ATT — {matched}/{total} players matched")

def update_wr():
    if not os.path.exists(WR_CSV):
        print(f"✗ Not found: {WR_CSV}")
        return
    df = pd.read_csv(WR_CSV, index_col=0)
    name_col = next((c for c in ["player_display_name","player","name"] if c in df.columns), None)
    if not name_col:
        print("✗ Could not find player name column in WR CSV.")
        return

    yprr_vals = []
    matched, total = 0, 0
    for name in df[name_col]:
        result = find_match(str(name), WR_YPRR)
        if result is not None:
            yprr_vals.append(round(result, 2))
            matched += 1
        else:
            yprr_vals.append(None)
        total += 1

    df["yprr"] = yprr_vals
    df.to_csv(WR_CSV)
    print(f"✓ WR: added YPRR — {matched}/{total} players matched")

if __name__ == "__main__":
    print("Updating 2025 stats...")
    update_rb()
    update_wr()
    print("\nDone. Now add 'ybc_att', 'yac_att', and 'yprr' to COL_LABELS in app.py if not already there.")
