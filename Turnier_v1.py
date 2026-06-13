import streamlit as st
import pandas as pd
import json
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Turnier", layout="wide")
st.autorefresh(interval=5000, key="refresh")

FILE = "turnier.json"

PASSWORD_ADMIN = "KALLA coden"
PASSWORD_SCHIRI = "SCHIRI"

# ---------------- SAVE / LOAD ----------------
def load():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return json.load(f)
    return None

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

# ---------------- INIT ----------------
if "role" not in st.session_state:
    st.session_state.role = None

if "data" not in st.session_state:
    data = load()

    if not data:
        data = {
            "teams": [
                ["Spieler 1", "Spieler 2"],
                ["Spieler 3", "Spieler 4"],
                [],
                [],
                [],
            ],
            "matches": [],
            "rounds": [],
            "ko": {
                "hf1": {"a": "", "b": "", "sa": 0, "sb": 0},
                "hf2": {"a": "", "b": "", "sa": 0, "sb": 0},
                "final": {"a": "", "b": "", "sa": 0, "sb": 0},
                "active": False
            }
        }

    st.session_state.data = data

data = st.session_state.data

# ---------------- LOGIN ----------------
st.sidebar.header("🔐 Zugriff")

password_input = st.sidebar.text_input("Passwort", type="password")

if password_input == PASSWORD_ADMIN:
    st.session_state.role = "admin"
    st.sidebar.success("✔ Admin eingeloggt")

elif password_input == PASSWORD_SCHIRI:
    st.session_state.role = "schiri"
    st.sidebar.success("✔ Schiri eingeloggt")

elif st.session_state.role is None:
    st.sidebar.warning("❌ Kein Zugriff")

role = st.session_state.role

st.title("🏐 Volleyball Turnier")

# ---------------- TEAMS ----------------
st.header("👥 Teams")

cols = st.columns(len(data["teams"]))

for i, team in enumerate(data["teams"]):

    with cols[i]:

        st.subheader(f"Team {i+1}")

        updated = []

        for j, p in enumerate(team):
            val = st.text_input(f"Spieler {j+1}", p, key=f"p_{i}_{j}")
            if val:
                updated.append(val)

        new_p = st.text_input("➕ Spieler hinzufügen", key=f"new_{i}")

        if st.button(f"Hinzufügen Team {i+1}", key=f"btn_{i}"):
            if new_p.strip():
                updated.append(new_p.strip())
                data["teams"][i] = updated
                save(data)
                st.rerun()

        data["teams"][i] = updated

st.divider()

teams = data["teams"]

# ---------------- SPIELPLAN ----------------
st.header("Spielplan")

# Dummy rounds wenn leer
if not data["rounds"]:
    # einfache Paarungen erzeugen
    n = len(teams)
    rounds = []
    matches = []

    for r in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            a = i
            b = n - 1 - i

            match = {
                "a": a,
                "b": b,
                "sa": 0,
                "sb": 0,
                "done": False,
                "submitted": False
            }

            matches.append(match)
            round_matches.append(match)

        rounds.append(round_matches)

    data["rounds"] = rounds
    data["matches"] = matches
    save(data)

# ---------------- RUNDEN ----------------
for r_index, round_matches in enumerate(data["rounds"]):

    st.subheader(f"🏁 Runde {r_index + 1}")

    # ---------------- SCHIRI SPEICHERT ----------------
    if st.button(f"💾 Runde {r_index + 1} speichern (Schiri)"):

        if role is None:
            st.error("❌ Kein Zugriff")
        else:
            for m in round_matches:
                m["submitted"] = True
                m["approved"] = False

            save(data)
            st.success("📩 Ergebnisse gespeichert (wartet auf Admin)")
            st.rerun()

    # ---------------- ADMIN FREIGABE ----------------
    if role == "admin":
        if st.button(f"✅ Runde {r_index + 1} freigeben & auswerten"):

            for m in round_matches:

                if not m.get("submitted"):
                    continue

                if m.get("done"):
                    continue

                sa = m["sa"]
                sb = m["sb"]

                if sa > sb:
                    m["winner"] = m["a"]
                elif sb > sa:
                    m["winner"] = m["b"]
                else:
                    m["winner"] = None

                m["done"] = True
                m["approved"] = True

            save(data)
            st.success("🏆 Runde freigegeben & ausgewertet!")
            st.rerun()

    cols = st.columns(3)

    for j, m in enumerate(round_matches):

        with cols[j % 3]:

            if m.get("done"):
                status = "🟢 ausgewertet"
            elif m.get("submitted"):
                status = "🟡 wartet auf Admin"
            else:
                status = "⚪ offen"

            st.write(status)
            st.write(f"**Team {m['a']+1} vs Team {m['b']+1}**")

            m["sa"] = st.number_input(
                f"Team {m['a']+1}",
                key=f"a_{r_index}_{j}",
                value=m.get("sa", 0)
            )

            m["sb"] = st.number_input(
                f"Team {m['b']+1}",
                key=f"b_{r_index}_{j}",
                value=m.get("sb", 0)
            )

# ---------------- AUTO SAVE ----------------
if role == "admin":
    save(data)

# ---------------- TABELLE ----------------
st.sidebar.header("🏆 Tabelle")

table = {i: {"P": 0, "Diff": 0, "GF": 0, "GA": 0} for i in range(len(teams))}

for m in data["matches"]:

    if not m.get("done"):
        continue

    a, b = m["a"], m["b"]
    sa, sb = m["sa"], m["sb"]

    table[a]["GF"] += sa
    table[a]["GA"] += sb
    table[b]["GF"] += sb
    table[b]["GA"] += sa

    if sa > sb:
        table[a]["P"] += 3
    elif sb > sa:
        table[b]["P"] += 3
    else:
        table[a]["P"] += 1
        table[b]["P"] += 1

    table[a]["Diff"] += sa - sb
    table[b]["Diff"] += sb - sa

df = pd.DataFrame([
    {
        "Team": f"Team {i+1}",
        "Punkte": table[i]["P"],
        "Diff": table[i]["Diff"],
        "Tore": table[i]["GF"],
    }
    for i in range(len(teams))
])

df = df.sort_values(["Punkte", "Diff", "Tore"], ascending=False).reset_index(drop=True)
df.insert(0, "Rang", range(1, len(df) + 1))

st.sidebar.dataframe(df, use_container_width=True)
