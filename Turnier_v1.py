import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Turnier", layout="wide")

FILE = "turnier.json"

# ---------------- SAVE / LOAD ----------------
def load():
    if os.path.exists(FILE):
        with open(FILE,"r") as f:
            return json.load(f)
    return None

def save(data):
    with open(FILE,"w") as f:
        json.dump(data,f)

# ---------------- INIT ----------------
if "data" not in st.session_state:
    data = load()
    if not data:
        data = {
            "teams": ["Team A","Team B","Team C","Team D","Team E"],
            "matches": [],
        }
    st.session_state.data = data

data = st.session_state.data

st.title("🏐 Einfaches Volleyball Turnier (5 Teams)")

# ---------------- TEAMS ----------------
st.sidebar.header("Teams")
for i in range(5):
    data["teams"][i] = st.sidebar.text_input(f"Team {i+1}", data["teams"][i])

teams = data["teams"]

# ---------------- MATCHES (Jeder gegen jeden) ----------------
if not data["matches"]:
    pairs = [(0,1),(0,2),(0,3),(0,4),
             (1,2),(1,3),(1,4),
             (2,3),(2,4),
             (3,4)]

    for a,b in pairs:
        data["matches"].append({
            "a": a,
            "b": b,
            "sa": 0,
            "sb": 0
        })

save(data)

# ---------------- LIVE SCORING ----------------
st.header("📱 Schiri Eingabe (Live)")

cols = st.columns(2)

for i,m in enumerate(data["matches"]):
    with cols[i % 2]:
        st.subheader(f"{teams[m['a']]} vs {teams[m['b']]}")

        m["sa"] = st.number_input(f"{teams[m['a']]} Punkte", key=f"a{i}", value=m["sa"])
        m["sb"] = st.number_input(f"{teams[m['b']]} Punkte", key=f"b{i}", value=m["sb"])

save(data)

# ---------------- TABLE ----------------
st.header("📊 Tabelle")

table = {t: {"P":0,"Diff":0} for t in teams}

for m in data["matches"]:
    if m["sa"] > m["sb"]:
        table[teams[m["a"]]]["P"] += 2
    elif m["sb"] > m["sa"]:
        table[teams[m["b"]]]["P"] += 2

    table[teams[m["a"]]]["Diff"] += m["sa"] - m["sb"]
    table[teams[m["b"]]]["Diff"] += m["sb"] - m["sa"]

df = pd.DataFrame([
    {"Team":k,"Punkte":v["P"],"Diff":v["Diff"]}
    for k,v in table.items()
]).sort_values(["Punkte","Diff"], ascending=False)

st.dataframe(df, use_container_width=True)

ranked = df["Team"].tolist()

# ---------------- PLAYOFFS AUTOMATISCH ----------------
st.header("🏆 Halbfinale & Finale (automatisch)")

if len(ranked) >= 4:

    hf1 = (ranked[0], ranked[3])
    hf2 = (ranked[1], ranked[2])

    st.subheader("Halbfinale")

    h1a = st.number_input(f"{hf1[0]}", key="h1a")
    h1b = st.number_input(f"{hf1[1]}", key="h1b")

    h2a = st.number_input(f"{hf2[0]}", key="h2a")
    h2b = st.number_input(f"{hf2[1]}", key="h2b")

    winner1 = hf1[0] if h1a > h1b else hf1[1]
    winner2 = hf2[0] if h2a > h2b else hf2[1]

    st.subheader("🏅 Finale")

    f1 = st.number_input(f"{winner1}", key="f1")
    f2 = st.number_input(f"{winner2}", key="f2")

    if f1 > f2:
        st.success(f"🏆 Sieger: {winner1}")
    elif f2 > f1:
        st.success(f"🏆 Sieger: {winner2}")

save(data)