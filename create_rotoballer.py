"""
Run this once to create the RotoBaller CSV from manually entered rankings.
py -3.12 create_rotoballer.py
"""
import pandas as pd
import os

os.makedirs(os.path.join("data","2026"), exist_ok=True)

rows = []

QB = ["Josh Allen","Lamar Jackson","Jayden Daniels","Drake Maye","Joe Burrow",
      "Jalen Hurts","Caleb Williams","Justin Herbert","Jaxson Dart","Trevor Lawrence",
      "Dak Prescott","Brock Purdy","Patrick Mahomes","Matthew Stafford","Bo Nix",
      "Kyler Murray","Jordan Love","Jared Goff","Baker Mayfield","Malik Willis",
      "Tyler Shough","Sam Darnold","CJ Stroud","Daniel Jones"]

RB = ["Jahmyr Gibbs","Bijan Robinson","Christian McCaffrey","Jonathan Taylor",
      "Devon Achane","James Cook III","Saquon Barkley","Ashton Jeanty",
      "Kenneth Walker III","Derrick Henry","Omarion Hampton","Chase Brown",
      "Jeremiyah Love","Josh Jacobs","Kyren Williams","Travis Etienne Jr",
      "Breece Hall","Javonte Williams","Bucky Irving","Cam Skattebo",
      "D'Andre Swift","Bhayshul Tuten","TreVeyon Henderson","Quinshon Judkins"]

WR = ["Puka Nacua","Ja'Marr Chase","Jaxon Smith-Njigba","CeeDee Lamb",
      "Amon-Ra St. Brown","Justin Jefferson","Drake London","Malik Nabers",
      "Rashee Rice","George Pickens","Nico Collins","Chris Olave",
      "Devonta Smith","Tee Higgins","Tetairoa McMillan","AJ Brown",
      "Garrett Wilson","Davante Adams","Zay Flowers","Luther Burden III",
      "Ladd McConkey","Terry McLaurin","Jameson Williams","Emeka Egbuka"]

TE = ["Trey McBride","Brock Bowers","Colston Loveland","Tyler Warren",
      "Harold Fannin Jr","Tucker Kraft","Sam LaPorta","Kyle Pitts",
      "Dalton Kincaid","Dallas Goedert","Oronde Gadsden II","George Kittle",
      "Jake Ferguson","Travis Kelce","Kenyon Sadiq","Mark Andrews",
      "Hunter Henry","Brenton Strange","Isaiah Likely","Juwan Johnson",
      "TJ Hockerson","Dalton Schultz","Chig Okonkwo","Pat Freiermuth"]

for pos, names in [("QB", QB), ("RB", RB), ("WR", WR), ("TE", TE)]:
    for i, name in enumerate(names, 1):
        rows.append({"player": name, "position": pos, "rb_pos_rank": i})

df = pd.DataFrame(rows)

# Add overall rank within positions weighted by position scarcity
# QBs drafted later, so overall rank: RB/WR first, then TE, then QB
pos_order = {"RB": 0, "WR": 1, "TE": 2, "QB": 3}
df["pos_weight"] = df["position"].map(pos_order)
df = df.sort_values(["pos_weight", "rb_pos_rank"]).reset_index(drop=True)
df["rb_overall_rank"] = range(1, len(df) + 1)
df = df.drop(columns=["pos_weight"])
df = df.rename(columns={"rb_pos_rank": "rb_pos_rank"})

path = os.path.join("data","2026","rotoballer.csv")
df.to_csv(path, index=False)
print(f"✅ Saved {len(df)} players → {path}")
print(df.head(10).to_string())
