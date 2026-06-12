import streamlit as st
import pandas as pd
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Turnier", layout="wide")

FILE = "turnier.json"
PASSWORD = "KALLA coden"

# ---------------- SAVE / LOAD ----------------
def load():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return json.load(f)
    return None

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

# ---------------- ROUND ROBIN ----------------
def generate_rounds(n):
    teams = list(range(n))

    if n % 2 == 1:
        teams.append(-1)
        n += 1

    rounds = []

    for _ in range(n - 1):
        round_matches = []

        for i in range(n // 2):
            a = teams[i]
            b = teams[n - 1 - i]

            if a != -1 and b != -1:
                round_matches.append((a, b))

        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        rounds.append(round_matches)

    return rounds

# ---------------- INIT ----------------
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
        }

    if "rounds" not in data:

        raw_rounds = generate_rounds(len(data["teams"]))

        data["rounds"] = []
        data["matches"] = []

        for r, round_matches in enumerate(raw_rounds):

            round_list = []

            for a, b in round_matches:
                match = {
                    "a": a,
                    "b": b,
                    "sa": 0,
                    "sb": 0,
                    "r": r,
                    "done": False
                }

                data["matches"].append(match)
                round_list.append(match)

            data["rounds"].append(round_list)

    # KO INIT
    data["ko"] = {
        "hf1": {"a": "", "b": "", "sa": 0, "sb": 0},
        "hf2": {"a": "", "b": "", "sa": 0, "sb": 0},
        "final": {"a": "", "b": "", "sa": 0, "sb": 0},
        "active": False
    }

    st.session_state.data = data

data = st.session_state.data

# ---------------- TIMER INIT ----------------
if "timers" not in st.session_state:
    st.session_state.timers = {
        i: {
            "running": False,
            "start_time": None,
            "duration": 15 * 60
        }
        for i in range(5)
    }

# ---------------- PASSWORD ----------------
st.sidebar.header("🔐 Zugriff")

password_input = st.sidebar.text_input("Passwort", type="password")
auth = password_input == PASSWORD

if auth:
    st.sidebar.success("✔ Zugriff erlaubt")
else:
    st.sidebar.warning("❌ Kein Zugriff zum Speichern")

st.title("🏐 Volleyball Turnier")

# ---------------- TEAMS ----------------
st.header("👥 Teams")

cols = st.columns(len(data["teams"]))

for i, team in enumerate(data["teams"]):

    with cols[i]:

        st.subheader(f"Team {i+1}")

        updated = []

        for j, p in enumerate(team):
            val = st.text_input(
                f"Spieler {j+1}",
                p,
                key=f"p_{i}_{j}"
            )
            if val:
                updated.append(val)

        new_p = st.text_input(
            "➕ Spieler hinzufügen",
            key=f"new_{i}"
        )

        if new_p:
            updated.append(new_p)

        data["teams"][i] = updated

st.divider()

teams = data["teams"]

# ---------------- TIMER ----------------
def render_timer(round_index):

    timer = st.session_state.timers[round_index]

    if timer["running"]:
        st_autorefresh(interval=1000, key=f"refresh_{round_index}")

        elapsed = time.time() - timer["start_time"]
        remaining = timer["duration"] - elapsed

        if remaining <= 0:
            timer["running"] = False
            remaining = 0

        mins = int(remaining // 60)
        secs = int(remaining % 60)

        st.markdown(f"## ⏱️ {mins:02d}:{secs:02d}")

    else:
        st.markdown("## ⏱️ 15:00 bereit")

    if st.button(f"▶️ Timer Start Runde {round_index + 1}", key=f"start_{round_index}"):
        if auth:
            timer["running"] = True
            timer["start_time"] = time.time()
        else:
            st.error("Passwort erforderlich!")

# ---------------- SCHIRI LIGA ----------------
st.header("Spielplan")

for r_index, round_matches in enumerate(data["rounds"]):

    st.subheader(f"🏁 Runde {r_index + 1}")

    # TIMER PRO RUNDE
    render_timer(r_index)

    cols = st.columns(3)

    if st.button(f"💾 Runde {r_index + 1} speichern"):

        if not auth:
            st.error("❌ Passwort erforderlich!")
        else:
            for m in round_matches:

                if m["done"]:
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

            if r_index == 4:
                data["ko"]["active"] = True

            save(data)
            st.success(f"Runde {r_index + 1} gespeichert!")

    for j, m in enumerate(round_matches):

        with cols[j % 3]:

            st.write(f"**Team {m['a']+1} vs Team {m['b']+1}**")

            m["sa"] = st.number_input(
                f"Team {m['a']+1}",
                key=f"a_{r_index}_{j}",
                value=m["sa"]
            )

            m["sb"] = st.number_input(
                f"Team {m['b']+1}",
                key=f"b_{r_index}_{j}",
                value=m["sb"]
            )

# ---------------- KO PHASE ----------------
if data["ko"]["active"]:

    st.divider()
    st.header("🔥 K.O. Phase")

    ko = data["ko"]

    def render_match(title, match, key):

        st.markdown(f"### {title}")

        colA, colB = st.columns(2)

        with colA:
            match["a"] = st.text_input("Team A", match["a"], key=f"{key}_a")

        with colB:
            match["b"] = st.text_input("Team B", match["b"], key=f"{key}_b")

        st.markdown(
            f"<div style='text-align:center;font-size:22px;font-weight:800'>{match['a']} vs {match['b']}</div>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:
            match["sa"] = st.number_input("Score A", key=f"{key}_sa", value=match["sa"], min_value=0)

        with col2:
            match["sb"] = st.number_input("Score B", key=f"{key}_sb", value=match["sb"], min_value=0)

        st.markdown(
            f"<div style='text-align:center;font-size:30px;font-weight:900'>{match['sa']} : {match['sb']}</div>",
            unsafe_allow_html=True
        )

    st.subheader("🏆 Halbfinale")

    col1, col2 = st.columns(2)

    with col1:
        render_match("HF1", ko["hf1"], "hf1")

    with col2:
        render_match("HF2", ko["hf2"], "hf2")

    st.subheader("🏅 Finale")

    render_match("Finale", ko["final"], "final")

    if st.button("💾 KO speichern"):
        if auth:
            save(data)
            st.success("K.O. gespeichert!")
        else:
            st.error("Passwort erforderlich!")

# ---------------- AUTO SAVE ----------------
if auth:
    save(data)

# ---------------- TABELLE ----------------
st.sidebar.header("🏆 Tabelle")

table = {
    i: {"P": 0, "Diff": 0, "GF": 0, "GA": 0}
    for i in range(len(teams))
}

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