import streamlit as st
import streamlit.components.v1 as components
import json
import base64
import requests
from datetime import date, datetime, timedelta
from html import escape

# ── Page ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Guía de Borrado", page_icon="🗑️", layout="wide")

# ── GitHub ─────────────────────────────────────────────────────────────
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
DATA_FILE = "data.json"

GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

DEFAULT_DATA = {"channels": {}, "checked": {}, "log": []}

@st.cache_data(ttl=30)
def load_data():
    r = requests.get(GITHUB_API, headers=HEADERS)
    if r.status_code == 404:
        return DEFAULT_DATA.copy(), None
    r.raise_for_status()
    j = r.json()
    return json.loads(base64.b64decode(j["content"]).decode()), j["sha"]

def save_data(data, sha):
    encoded = base64.b64encode(json.dumps(data).encode()).decode()
    payload = {"message": "update data", "content": encoded}
    if sha:
        payload["sha"] = sha
    r = requests.put(GITHUB_API, headers=HEADERS, json=payload)
    r.raise_for_status()
    load_data.clear()
    return r.json()["content"]["sha"]

# ── Logic ──────────────────────────────────────────────────────────────
RULE_DAYS = {
    "2 DIAS": 2,
    "1 SEMANA": 7,
    "2 SEMANAS": 14,
    "3 SEMANAS": 21,
    "4 SEMANAS": 28,
    "1 MES": 30,
    "3 MESES": 90,
}

def eligible(rule, today):
    cutoff = today - timedelta(days=RULE_DAYS.get(rule, 0))
    d1 = date(cutoff.year, cutoff.month, 1) - timedelta(days=1)
    d2 = date(d1.year, d1.month, 1) - timedelta(days=1)
    return [(d1.year, d1.strftime("%m")), (d2.year, d2.strftime("%m"))]

def k(y, p, m):
    return f"{y}__{p}__{m}"

def ensure_sel():
    if "selected" not in st.session_state:
        st.session_state.selected = set()

def is_sel(y, p, m):
    ensure_sel()
    return k(y, p, m) in st.session_state.selected

def set_sel(y, p, m, v):
    ensure_sel()
    key = k(y, p, m)
    if v:
        st.session_state.selected.add(key)
    else:
        st.session_state.selected.discard(key)

def commit(data):
    ensure_sel()
    count = 0
    for key in list(st.session_state.selected):
        y, p, m = key.split("__")
        data["checked"][key] = True

        data["log"] = [{
            "id": p + m,
            "prefix": p,
            "year": int(y),
            "mm": m,
            "doneAt": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }] + data["log"]

        st.session_state.selected.discard(key)
        count += 1
    return count

def undo(data, y, p, m):
    data["checked"].pop(k(y, p, m), None)
    data["log"] = [
        e for e in data["log"]
        if not (e["prefix"] == p and e["mm"] == m and e["year"] == y)
    ]

def copy_btn(text, key):
    safe = json.dumps(text)
    key = escape(key)
    components.html(f"""
    <button id="{key}" onclick='
    navigator.clipboard.writeText({safe});
    let b=document.getElementById("{key}");
    let o=b.innerText;
    b.innerText="Copiado";
    b.style.background="#E1F5EE";
    setTimeout(()=>{{b.innerText=o;b.style.background="#eee";}},1000);
    ' style="width:100%;padding:6px;border-radius:6px;border:1px solid #ccc;">
    Copiar
    </button>
    """, height=40)

def action_bar(data):
    ensure_sel()
    c = len(st.session_state.selected)

    col1, col2 = st.columns(2)

    if col1.button(f"Done ({c})"):
        if c > 0:
            new_sha = save_data(data, st.session_state.sha)
            st.session_state.data, _ = load_data()
            st.session_state.sha = new_sha
            st.rerun()

    if col2.button("Clear"):
        st.session_state.selected = set()
        st.rerun()

# ── App ────────────────────────────────────────────────────────────────
today = date.today()

if "data" not in st.session_state:
    d, sha = load_data()
    st.session_state.data = d
    st.session_state.sha = sha

data = st.session_state.data
ensure_sel()

tabs = st.tabs(["Todos"] + list(data["channels"].keys()) + ["Log"])

# ── TODOS ──────────────────────────────────────────────────────────────
with tabs[0]:
    action_bar(data)

    for ch, items in data["channels"].items():
        st.subheader(ch)
        cols = st.columns(3)
        i = 0

        for it in items:
            for y, m in eligible(it["rule"], today):
                if k(y, it["prefix"], m) in data["checked"]:
                    continue

                with cols[i % 3]:
                    val = st.checkbox(
                        f"{it['prefix']}{m}",
                        value=is_sel(y, it["prefix"], m),
                        key=f"t_{y}_{it['prefix']}_{m}"
                    )
                    set_sel(y, it["prefix"], m, val)
                    copy_btn(it["prefix"] + m, f"c_{ch}_{i}")
                i += 1

# ── CHANNELS ───────────────────────────────────────────────────────────
for idx, ch in enumerate(data["channels"].keys(), start=1):
    with tabs[idx]:
        action_bar(data)
        items = data["channels"][ch]
        cols = st.columns(3)
        i = 0

        for it in items:
            for y, m in eligible(it["rule"], today):
                if k(y, it["prefix"], m) in data["checked"]:
                    continue

                with cols[i % 3]:
                    val = st.checkbox(
                        f"{it['prefix']}{m}",
                        value=is_sel(y, it["prefix"], m),
                        key=f"{ch}_{y}_{it['prefix']}_{m}"
                    )
                    set_sel(y, it["prefix"], m, val)
                    copy_btn(it["prefix"] + m, f"{ch}_{i}")
                i += 1

# ── LOG ────────────────────────────────────────────────────────────────
with tabs[-1]:
    st.markdown("### Log")

    for i, e in enumerate(data["log"][:200]):
        c1, c2 = st.columns([3, 1])

        with c1:
            st.write(f"{e['id']}  ({e['doneAt']})")

        with c2:
            if st.button("Recuperar", key=f"undo_{i}"):
                undo(data, e["year"], e["prefix"], e["mm"])
                new_sha = save_data(data, st.session_state.sha)
                st.session_state.data, _ = load_data()
                st.session_state.sha = new_sha
                st.rerun()