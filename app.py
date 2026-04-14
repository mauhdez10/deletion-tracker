import streamlit as st
import streamlit.components.v1 as components
import json
import base64
import requests
from datetime import date, datetime, timedelta
from html import escape

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Guía de Borrado",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}

.badge-2dias   {background:#FAECE7;color:#993C1D;border:1px solid #F0997B;}
.badge-1sem    {background:#FAEEDA;color:#854F0B;border:1px solid #EF9F27;}
.badge-2sem    {background:#E6F1FB;color:#185FA5;border:1px solid #85B7EB;}
.badge-3sem    {background:#EEEDFE;color:#534AB7;border:1px solid #AFA9EC;}
.badge-4sem    {background:#EAF3DE;color:#3B6D11;border:1px solid #97C459;}
.badge-1mes    {background:#FBEAF0;color:#993556;border:1px solid #ED93B1;}
.badge-nmes    {background:#F1EFE8;color:#5F5E5A;border:1px solid #B4B2A9;}

.rule-header {
    display:inline-block;
    padding:3px 12px;
    border-radius:6px;
    font-size:0.78rem;
    font-weight:600;
    margin-right:10px;
}
.cutoff-text {font-size:0.78rem; color:#888;}

.log-entry {
    background:#f9f9f9;
    border:1px solid #eee;
    border-radius:8px;
    padding:10px 12px;
    margin-bottom:8px;
}
.log-id {font-family:monospace; font-weight:700; font-size:0.95rem;}
.log-meta  {font-size:0.75rem; color:#888; margin-top:2px;}

.done-badge{
    background:#E1F5EE;color:#0F6E56;
    border:1px solid #5DCAA5;
    border-radius:12px;
    padding:2px 8px;
    font-size:0.72rem;
    font-weight:600;
}
.pending-badge{
    background:#FAECE7;color:#993C1D;
    border:1px solid #F0997B;
    border-radius:12px;
    padding:2px 8px;
    font-size:0.72rem;
    font-weight:600;
}
.action-wrap {
    background:#fafafa;
    border:1px solid #eee;
    border-radius:10px;
    padding:12px 14px;
    margin:4px 0 16px 0;
}
.small-muted {
    color:#888;
    font-size:0.78rem;
}

div[data-testid="stCheckbox"] label {
    font-size: 0.95rem !important;
    font-weight: 500;
}

.copy-btn-wrap {
    margin-top: 0.25rem;
}
.copy-btn-wrap button {
    width: 100%;
    background: #f5f5f5;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 12px;
    line-height: 1.1;
    min-height: 30px;
}

.id-card {
    border: 1px solid #ececec;
    border-radius: 10px;
    padding: 10px 12px 8px 12px;
    background: white;
    margin-bottom: 8px;
}
.id-card.selected {
    border: 1px solid #85B7EB;
    background: #F7FBFF;
}
.id-sub {
    color: #777;
    font-size: 0.73rem;
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── GitHub helpers ────────────────────────────────────────────────────────────
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
DATA_FILE = "data.json"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

DEFAULT_DATA = {
    "channels": {
        "CATV": [
            {"prefix": "TMPN",  "rule": "2 DIAS"},
            {"prefix": "NHM",   "rule": "2 DIAS"},
            {"prefix": "HME",   "rule": "2 DIAS"},
            {"prefix": "ENSV",  "rule": "2 DIAS"},
            {"prefix": "N4SV",  "rule": "2 DIAS"},
            {"prefix": "TCSSV", "rule": "2 DIAS"},
            {"prefix": "TN5",   "rule": "2 DIAS"},
            {"prefix": "IDGT",  "rule": "2 DIAS"},
            {"prefix": "T2SV",  "rule": "2 DIAS"},
            {"prefix": "NVOS",  "rule": "2 DIAS"},
            {"prefix": "DNC",   "rule": "2 DIAS"},
            {"prefix": "NGGTA", "rule": "2 DIAS"},
            {"prefix": "NGGTB", "rule": "2 DIAS"},
            {"prefix": "TCR",   "rule": "2 DIAS"},
            {"prefix": "MISA",  "rule": "1 SEMANA"},
            {"prefix": "VMGT",  "rule": "1 SEMANA"},
            {"prefix": "FFSV",  "rule": "1 SEMANA"},
            {"prefix": "MQN",   "rule": "2 SEMANAS"},
            {"prefix": "FUSV",  "rule": "3 SEMANAS"},
            {"prefix": "FUCR",  "rule": "3 SEMANAS"},
            {"prefix": "FUHN",  "rule": "3 SEMANAS"},
            {"prefix": "LSGT",  "rule": "1 MES"},
            {"prefix": "ATSV",  "rule": "3 MESES"},
            {"prefix": "ESSV",  "rule": "3 MESES"},
            {"prefix": "RESV",  "rule": "3 MESES"},
            {"prefix": "HSLA",  "rule": "3 MESES"},
        ],
        "TVD": [
            {"prefix": "NP",     "rule": "2 DIAS"},
            {"prefix": "CEND",   "rule": "2 DIAS"},
            {"prefix": "NYM",    "rule": "2 DIAS"},
            {"prefix": "NS",     "rule": "2 DIAS"},
            {"prefix": "NF",     "rule": "2 DIAS"},
            {"prefix": "DESPT",  "rule": "1 SEMANA"},
            {"prefix": "SHMD",   "rule": "1 SEMANA"},
            {"prefix": "MANGU",  "rule": "1 SEMANA"},
            {"prefix": "COSA",   "rule": "1 SEMANA"},
            {"prefix": "LUNA-X", "rule": "1 SEMANA"},
            {"prefix": "ENMA",   "rule": "1 SEMANA"},
            {"prefix": "VD",     "rule": "1 SEMANA"},
            {"prefix": "MASR",   "rule": "2 SEMANAS"},
            {"prefix": "TOPI",   "rule": "2 SEMANAS"},
            {"prefix": "ELI",    "rule": "3 SEMANAS"},
            {"prefix": "CON",    "rule": "4 SEMANAS"},
            {"prefix": "NDL",    "rule": "1 MES"},
            {"prefix": "DAPP",   "rule": "1 MES"},
            {"prefix": "ENFA",   "rule": "3 MES"},
        ],
    },
    "checked": {},
    "log": [],
}

@st.cache_data(ttl=30)
def load_data():
    resp = requests.get(GITHUB_API, headers=HEADERS, timeout=30)
    if resp.status_code == 404:
        return DEFAULT_DATA.copy(), None
    resp.raise_for_status()
    j = resp.json()
    content = json.loads(base64.b64decode(j["content"]).decode("utf-8"))
    return content, j["sha"]

def save_data(data, sha):
    body = json.dumps(data, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(body.encode("utf-8")).decode("utf-8")
    payload = {"message": f"update data {datetime.utcnow().isoformat()}", "content": encoded}
    if sha:
        payload["sha"] = sha
    resp = requests.put(GITHUB_API, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    load_data.clear()
    return resp.json()["content"]["sha"]

# ── Logic ─────────────────────────────────────────────────────────────────────
RULE_DAYS = {
    "2 DIAS": 2,
    "1 SEMANA": 7,
    "2 SEMANAS": 14,
    "3 SEMANAS": 21,
    "4 SEMANAS": 28,
    "1 MES": 30,
    "2 MES": 60,
    "3 MES": 90,
    "3 MESES": 90,
}
RULE_ORDER = list(RULE_DAYS.keys())
RULE_BADGE = {
    "2 DIAS": "badge-2dias",
    "1 SEMANA": "badge-1sem",
    "2 SEMANAS": "badge-2sem",
    "3 SEMANAS": "badge-3sem",
    "4 SEMANAS": "badge-4sem",
    "1 MES": "badge-1mes",
    "2 MES": "badge-nmes",
    "3 MES": "badge-nmes",
    "3 MESES": "badge-nmes",
}

def eligible_months(rule, today):
    cutoff = today - timedelta(days=RULE_DAYS.get(rule, 0))
    d1 = date(cutoff.year, cutoff.month, 1) - timedelta(days=1)
    d2 = date(d1.year, d1.month, 1) - timedelta(days=1)
    return [(d1.year, d1.strftime("%m")), (d2.year, d2.strftime("%m"))]

def done_key(year, prefix, mm):
    return f"{year}__{prefix}__{mm}"

def selection_key(year, prefix, mm):
    return f"{year}__{prefix}__{mm}"

def ensure_selected():
    if "selected_ids" not in st.session_state:
        st.session_state.selected_ids = set()

def is_selected(year, prefix, mm):
    ensure_selected()
    return selection_key(year, prefix, mm) in st.session_state.selected_ids

def set_selected(year, prefix, mm, selected):
    ensure_selected()
    key = selection_key(year, prefix, mm)
    if selected:
        st.session_state.selected_ids.add(key)
    else:
        st.session_state.selected_ids.discard(key)

def is_done(data, year, prefix, mm):
    return data["checked"].get(done_key(year, prefix, mm), False)

def get_rule_for_prefix(data, prefix):
    for items in data["channels"].values():
        for item in items:
            if item["prefix"] == prefix:
                return item["rule"]
    return ""

def mark_done(data, year, prefix, mm, rule):
    key = done_key(year, prefix, mm)
    data["checked"][key] = True
    entry = {
        "id": f"{prefix}{mm}",
        "prefix": prefix,
        "year": int(year),
        "mm": mm,
        "rule": rule,
        "doneAt": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    data["log"] = [entry] + [
        e for e in data["log"]
        if not (e["prefix"] == prefix and e["mm"] == mm and e["year"] == int(year))
    ]
    data["log"] = data["log"][:1000]

def commit_selected(data):
    ensure_selected()
    count = 0
    for skey in list(st.session_state.selected_ids):
        year, prefix, mm = skey.split("__")
        if is_done(data, int(year), prefix, mm):
            st.session_state.selected_ids.discard(skey)
            continue
        rule = get_rule_for_prefix(data, prefix)
        mark_done(data, int(year), prefix, mm, rule)
        st.session_state.selected_ids.discard(skey)
        count += 1
    return count

def clear_selection():
    ensure_selected()
    st.session_state.selected_ids = set()

def undo_done(data, year, prefix, mm):
    data["checked"].pop(done_key(year, prefix, mm), None)
    removed = False
    new_log = []
    for entry in data["log"]:
        if (
            not removed
            and entry["prefix"] == prefix
            and entry["year"] == int(year)
            and entry["mm"] == mm
        ):
            removed = True
            continue
        new_log.append(entry)
    data["log"] = new_log

# ── UI helpers ────────────────────────────────────────────────────────────────
def copy_button(text, key):
    safe_text = json.dumps(text)
    safe_key = escape(key)
    html = f"""
    <div class="copy-btn-wrap">
        <button
            id="{safe_key}"
            onclick='
                navigator.clipboard.writeText({safe_text});
                const btn = document.getElementById("{safe_key}");
                const original = btn.innerText;
                btn.innerText = "Copiado";
                btn.style.background = "#E1F5EE";
                btn.style.borderColor = "#5DCAA5";
                btn.style.color = "#0F6E56";
                setTimeout(() => {{
                    btn.innerText = original;
                    btn.style.background = "#f5f5f5";
                    btn.style.borderColor = "#d9d9d9";
                    btn.style.color = "#111";
                }}, 1100);
            '
        >Copiar</button>
    </div>
    """
    components.html(html, height=36, scrolling=False)

def save_and_refresh(data):
    new_sha = save_data(data, st.session_state.sha)
    fresh_data, _ = load_data()
    st.session_state.data = fresh_data
    st.session_state.sha = new_sha
    st.rerun()

def render_action_bar(data, scope):
    ensure_selected()
    selected_count = len(st.session_state.selected_ids)

    st.markdown('<div class="action-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.1, 3.5])

    with c1:
        if st.button(f"Done selected ({selected_count})", key=f"done_{scope}", use_container_width=True):
            if selected_count == 0:
                st.warning("No hay IDs seleccionados.")
            else:
                committed = commit_selected(data)
                if committed > 0:
                    save_and_refresh(data)

    with c2:
        if st.button("Clear selection", key=f"clear_{scope}", use_container_width=True):
            clear_selection()
            st.rerun()

    with c3:
        st.markdown(
            "<div class='small-muted'>"
            "Selecciona los IDs y luego presiona Done selected. "
            "Puedes desmarcarlos antes de guardar."
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

def render_id_card(year, prefix, mm, channel, view_scope):
    label_id = f"{prefix}{mm}"
    widget_key = f"{view_scope}__{channel}__{year}__{prefix}__{mm}"
    current = is_selected(year, prefix, mm)

    if widget_key not in st.session_state:
        st.session_state[widget_key] = current
    else:
        st.session_state[widget_key] = current

    card_class = "id-card selected" if current else "id-card"
    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    cb_col, cp_col = st.columns([3.3, 1])

    with cb_col:
        checked = st.checkbox(
            label_id,
            key=widget_key,
            help=f"{channel} · Año {year}",
            label_visibility="visible",
        )
        set_selected(year, prefix, mm, checked)
        st.markdown(f"<div class='id-sub'>Año {year}</div>", unsafe_allow_html=True)

    with cp_col:
        copy_button(label_id, key=f"copy_{widget_key}")

    st.markdown("</div>", unsafe_allow_html=True)

def sorted_rules(groups):
    return sorted(groups.keys(), key=lambda r: RULE_ORDER.index(r) if r in RULE_ORDER else 999)

def render_channel_blocks(data, channel, today, view_scope):
    prefixes = data["channels"][channel]

    groups = {}
    for item in prefixes:
        groups.setdefault(item["rule"], []).append(item)

    all_ids = [(yr, item["prefix"], mm)
               for item in prefixes
               for yr, mm in eligible_months(item["rule"], today)]
    done_count = sum(1 for yr, p, mm in all_ids if is_done(data, yr, p, mm))
    total = len(all_ids)
    st.progress(done_count / total if total else 0, text=f"{done_count}/{total} completados")

    any_pending = False

    for rule in sorted_rules(groups):
        items = groups[rule]
        badge_cls = RULE_BADGE.get(rule, "badge-nmes")
        days = RULE_DAYS.get(rule, 0)
        cutoff = today - timedelta(days=days)

        by_year = {}
        for item in items:
            for yr, mm in eligible_months(item["rule"], today):
                if not is_done(data, yr, item["prefix"], mm):
                    by_year.setdefault(yr, []).append((item["prefix"], mm))

        rule_pending = sum(len(v) for v in by_year.values())
        pending_html = (
            f'<span class="pending-badge">{rule_pending} pendiente{"s" if rule_pending != 1 else ""}</span>'
            if rule_pending else '<span class="done-badge">✓ Completo</span>'
        )

        st.markdown(
            f'<div style="margin:18px 0 8px">'
            f'<span class="rule-header {badge_cls}">{rule}</span>'
            f'<span class="cutoff-text">Borrar anterior a {cutoff.strftime("%d/%m/%Y")}</span>'
            f'&nbsp;&nbsp;{pending_html}</div>',
            unsafe_allow_html=True,
        )

        if not by_year:
            st.caption("Nada pendiente en esta regla.")
            continue

        any_pending = True
        for yr in sorted(by_year.keys(), reverse=True):
            st.markdown(f"#### {yr}")
            cols = st.columns(3)
            for idx, (prefix, mm) in enumerate(sorted(by_year[yr], key=lambda x: (x[1], x[0]), reverse=True)):
                with cols[idx % 3]:
                    render_id_card(yr, prefix, mm, channel, view_scope)

    if not any_pending:
        st.success("No hay IDs pendientes en este canal.")

def render_all_tab(data, today):
    render_action_bar(data, "todos")
    for channel in data["channels"].keys():
        st.markdown(f"## {channel}")
        render_channel_blocks(data, channel, today, f"todos_{channel}")
        st.divider()

def render_log_tab(data):
    st.markdown("### 📋 Log de borrados")

    log = data.get("log", [])
    if not log:
        st.info("Sin registros aún.")
        return

    all_channels = list(data["channels"].keys())
    all_years = sorted({str(e["year"]) for e in log}, reverse=True)

    f1, f2, f3 = st.columns([1.3, 1.2, 1.2])
    with f1:
        filter_ch = st.selectbox("Canal", ["Todos"] + all_channels, key="log_filter_channel")
    with f2:
        filter_year = st.selectbox("Año", ["Todos"] + all_years, key="log_filter_year")
    with f3:
        sort_mode = st.selectbox(
            "Ordenar",
            ["Más recientes", "Más antiguos", "ID A-Z", "ID Z-A"],
            key="log_sort_mode"
        )

    filtered = log
    if filter_ch != "Todos":
        channel_prefixes = {p["prefix"] for p in data["channels"].get(filter_ch, [])}
        filtered = [e for e in filtered if e["prefix"] in channel_prefixes]
    if filter_year != "Todos":
        filtered = [e for e in filtered if str(e["year"]) == filter_year]

    if sort_mode == "Más antiguos":
        filtered = list(reversed(filtered))
    elif sort_mode == "ID A-Z":
        filtered = sorted(filtered, key=lambda e: (e["id"], -int(e["year"])))
    elif sort_mode == "ID Z-A":
        filtered = sorted(filtered, key=lambda e: (e["id"], -int(e["year"])), reverse=True)

    st.markdown(f"**{len(filtered)} registros**")

    cols = st.columns(3)
    for idx, entry in enumerate(filtered):
        with cols[idx % 3]:
            st.markdown(
                f'<div class="log-entry">'
                f'<span class="log-id">{entry["id"]}</span>'
                f'&nbsp;&nbsp;<span class="done-badge">✓ borrado</span>'
                f'<div class="log-meta">{entry.get("rule","")} · Año {entry["year"]} · {entry["doneAt"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            a1, a2 = st.columns(2)
            with a1:
                copy_button(entry["id"], key=f"log_copy_{idx}_{entry['id']}")
            with a2:
                if st.button(
                    "Recuperar",
                    key=f"undo_{idx}_{entry['year']}_{entry['prefix']}_{entry['mm']}",
                    use_container_width=True
                ):
                    undo_done(data, entry["year"], entry["prefix"], entry["mm"])
                    save_and_refresh(data)

# ── App ───────────────────────────────────────────────────────────────────────
today = date.today()

if "data" not in st.session_state:
    d, sha = load_data()
    st.session_state.data = d
    st.session_state.sha = sha

ensure_selected()
data = st.session_state.data
channels = list(data["channels"].keys())

col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("## 🗑️ Guía de Borrado")
with col_date:
    st.markdown(
        f"<p style='text-align:right;color:#888;padding-top:14px'>{today.strftime('%A %d/%m/%Y').capitalize()}</p>",
        unsafe_allow_html=True,
    )

tabs = st.tabs(["📌 Todos"] + channels + ["📋 Log"])

with tabs[0]:
    render_all_tab(data, today)

for idx, channel in enumerate(channels, start=1):
    with tabs[idx]:
        render_action_bar(data, f"channel_{channel}")
        render_channel_blocks(data, channel, today, f"channel_{channel}")

with tabs[-1]:
    render_log_tab(data)