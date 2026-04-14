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

.id-done   {color:#0F6E56; font-family:monospace; font-size:1rem; font-weight:700;}
.id-pending{color:#111;    font-family:monospace; font-size:1rem; font-weight:700;}

.log-entry {
    background:#f9f9f9;
    border:1px solid #eee;
    border-radius:8px;
    padding:8px 12px;
    margin-bottom:6px;
}
.log-id    {font-family:monospace; font-weight:700; font-size:0.9rem;}
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
.copy-btn-wrap {
    margin-top: 0.25rem;
}
.stCheckbox label {
    font-size:0.92rem;
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

    if resp.status_code == 403:
        raise Exception(
            "GitHub rechazó la lectura. Verifica que el token tenga acceso al repositorio y permisos de Contents."
        )

    resp.raise_for_status()
    j = resp.json()
    content = json.loads(base64.b64decode(j["content"]).decode("utf-8"))
    sha = j["sha"]
    return content, sha

def save_data(data, sha):
    body = json.dumps(data, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(body.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"update data {datetime.utcnow().isoformat()}",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(GITHUB_API, headers=HEADERS, json=payload, timeout=30)

    if resp.status_code == 403:
        raise Exception(
            "GitHub rechazó la escritura. Revisa que el token tenga Contents: Read and write en este repo."
        )
    if resp.status_code == 409:
        raise Exception(
            "Hubo un conflicto de versión con data.json. Recarga la app y vuelve a intentar."
        )

    resp.raise_for_status()
    result = resp.json()
    load_data.clear()
    return result["content"]["sha"]

# ── Business logic ────────────────────────────────────────────────────────────
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

def get_eligible_months(rule: str, today: date):
    days = RULE_DAYS.get(rule, 0)
    cutoff = today - timedelta(days=days)

    months = []
    check = date(cutoff.year, cutoff.month, 1) - timedelta(days=1)

    while len(months) < 2:
        months.append((check.year, check.strftime("%m")))
        check = date(check.year, check.month, 1) - timedelta(days=1)

    return months

def check_key(year: int, prefix: str, mm: str) -> str:
    return f"{year}__{prefix}__{mm}"

def selection_key(year: int, prefix: str, mm: str) -> str:
    return f"sel__{year}__{prefix}__{mm}"

def parse_selection_key(key: str):
    _, year, prefix, mm = key.split("__", 3)
    return int(year), prefix, mm

def is_done(data: dict, year: int, prefix: str, mm: str) -> bool:
    return data["checked"].get(check_key(year, prefix, mm), False)

def mark_done(data: dict, year: int, prefix: str, mm: str, rule: str):
    key = check_key(year, prefix, mm)
    data["checked"][key] = True

    entry = {
        "id": f"{prefix}{mm}",
        "prefix": prefix,
        "year": year,
        "mm": mm,
        "rule": rule,
        "doneAt": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    data["log"] = [entry] + [
        e for e in data["log"]
        if not (e["prefix"] == prefix and e["mm"] == mm and e["year"] == year)
    ]
    data["log"] = data["log"][:1000]

def get_selected_keys():
    return [k for k, v in st.session_state.items() if k.startswith("sel__") and v]

def clear_all_selected():
    for key in list(st.session_state.keys()):
        if key.startswith("sel__"):
            st.session_state[key] = False

def get_rule_for_prefix(data: dict, prefix: str):
    for channel_items in data["channels"].values():
        for item in channel_items:
            if item["prefix"] == prefix:
                return item["rule"]
    return ""

def commit_selected(data):
    selected_keys = get_selected_keys()
    committed = 0

    for key in selected_keys:
        year, prefix, mm = parse_selection_key(key)
        if is_done(data, year, prefix, mm):
            st.session_state[key] = False
            continue

        rule = get_rule_for_prefix(data, prefix)
        mark_done(data, year, prefix, mm, rule)
        st.session_state[key] = False
        committed += 1

    return committed

def copy_button(text: str, key: str):
    safe_text = json.dumps(text)
    html = f"""
    <div class="copy-btn-wrap">
        <button
            onclick='navigator.clipboard.writeText({safe_text})'
            style="
                width:100%;
                background:#f5f5f5;
                border:1px solid #d9d9d9;
                border-radius:8px;
                padding:6px 10px;
                cursor:pointer;
                font-size:12px;
            ">
            Copiar
        </button>
    </div>
    """
    components.html(html, height=42, scrolling=False)

def render_action_bar(data, button_prefix: str):
    selected_count = len(get_selected_keys())

    st.markdown('<div class="action-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.2, 3])

    with c1:
        if st.button(f"Done selected ({selected_count})", key=f"{button_prefix}_done", use_container_width=True):
            if selected_count == 0:
                st.warning("No hay IDs seleccionados.")
            else:
                committed = commit_selected(data)
                if committed > 0:
                    try:
                        new_sha = save_data(data, st.session_state.sha)
                        fresh_data, _ = load_data()
                        st.session_state.data = fresh_data
                        st.session_state.sha = new_sha
                        st.success(f"{committed} ID(s) guardados.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando: {e}")
                else:
                    st.info("No hubo cambios para guardar.")

    with c2:
        if st.button("Clear selection", key=f"{button_prefix}_clear", use_container_width=True):
            clear_all_selected()
            st.rerun()

    with c3:
        st.markdown(
            "<div class='small-muted'>"
            "Selecciona los IDs que borraste. Puedes desmarcarlos antes de presionar Done."
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

def render_id_card(data, year: int, prefix: str, mm: str, channel: str, view_scope: str):
    label_id = f"{prefix}{mm}"
    sel_key = selection_key(year, prefix, mm)
    widget_key = f"{view_scope}__{sel_key}"

    if widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state.get(sel_key, False)

    c1, c2 = st.columns([3, 1])
    with c1:
        checked = st.checkbox(
            f"{label_id}   ·   {year}",
            key=widget_key,
            help=f"{channel} | {label_id}"
        )
        st.session_state[sel_key] = checked
    with c2:
        copy_button(label_id, key=f"copy_{view_scope}_{channel}_{year}_{label_id}")

def render_channel_content(
    data,
    channel: str,
    today: date,
    button_prefix: str,
    show_header=True,
    show_actions=True,
    view_scope=None,
):
    prefixes = data["channels"][channel]

    if view_scope is None:
        view_scope = button_prefix

    if show_header:
        st.markdown(f"### {channel}")

    if show_actions:
        render_action_bar(data, button_prefix)

    groups = {}
    for item in prefixes:
        groups.setdefault(item["rule"], []).append(item)

    sorted_rules = sorted(groups.keys(), key=lambda r: RULE_ORDER.index(r) if r in RULE_ORDER else 99)

    all_ids = [
        (yr, item["prefix"], mm)
        for item in prefixes
        for yr, mm in get_eligible_months(item["rule"], today)
    ]
    done_count = sum(1 for yr, p, mm in all_ids if is_done(data, yr, p, mm))
    total = len(all_ids)

    st.progress(done_count / total if total else 0, text=f"{done_count}/{total} completados")

    any_pending = False

    for rule in sorted_rules:
        items = groups[rule]
        badge_cls = RULE_BADGE.get(rule, "badge-nmes")
        days = RULE_DAYS.get(rule, 0)
        cutoff = today - timedelta(days=days)

        rule_ids = [
            (yr, it["prefix"], mm)
            for it in items
            for yr, mm in get_eligible_months(it["rule"], today)
        ]
        rule_pending = sum(1 for yr, p, mm in rule_ids if not is_done(data, yr, p, mm))

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

        pending_items = []
        for item in items:
            for yr, mm in get_eligible_months(item["rule"], today):
                if not is_done(data, yr, item["prefix"], mm):
                    pending_items.append((yr, item["prefix"], mm))

        if pending_items:
            any_pending = True
            cols = st.columns(3)
            for idx, (yr, prefix, mm) in enumerate(pending_items):
                with cols[idx % 3]:
                    render_id_card(data, yr, prefix, mm, channel, view_scope=view_scope)
        else:
            st.caption("Nada pendiente en esta regla.")

    if not any_pending:
        st.success("No hay IDs pendientes en este canal.")
def render_all_channels_tab(data, today: date):
    render_action_bar(data, "all_channels")

    channels = list(data["channels"].keys())
    for channel in channels:
        st.markdown(f"## {channel}")
        render_channel_content(
            data,
            channel,
            today,
            button_prefix=f"all_{channel}",
            show_header=False,
            show_actions=False,
            view_scope=f"alltab_{channel}",
        )
        st.divider()

# ── App ───────────────────────────────────────────────────────────────────────
today = date.today()

if "data" not in st.session_state:
    d, sha = load_data()
    st.session_state.data = d
    st.session_state.sha = sha

data = st.session_state.data
channels = list(data["channels"].keys())

# Header
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("## 🗑️ Guía de Borrado")
with col_date:
    st.markdown(
        f"<p style='text-align:right;color:#888;padding-top:14px'>{today.strftime('%A %d/%m/%Y').capitalize()}</p>",
        unsafe_allow_html=True,
    )

# Tabs
tab_labels = ["📌 Todos"] + channels + ["⚙ Admin", "📋 Log"]
tabs = st.tabs(tab_labels)

# ── All channels tab ──────────────────────────────────────────────────────────
with tabs[0]:
    render_all_channels_tab(data, today)

# ── Channel tabs ──────────────────────────────────────────────────────────────
for i, channel in enumerate(channels, start=1):
    with tabs[i]:
        render_channel_content(
    data,
    channel,
    today,
    button_prefix=f"channel_{channel}",
    show_header=True,
    show_actions=True,
    view_scope=f"channeltab_{channel}",
)

# ── Admin tab ─────────────────────────────────────────────────────────────────
with tabs[len(channels) + 1]:
    st.markdown("### ⚙ Administración")
    admin_changed = False

    with st.expander("📺 Canales", expanded=True):
        st.markdown("Canales actuales")
        for ch in list(data["channels"].keys()):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"{ch} — {len(data['channels'][ch])} prefijos")
            with c2:
                if st.button("Eliminar", key=f"del_ch_{ch}"):
                    if len(data["channels"]) <= 1:
                        st.warning("Debe haber al menos un canal.")
                    else:
                        del data["channels"][ch]
                        admin_changed = True
                        st.rerun()

        st.divider()
        nc1, nc2 = st.columns([2, 1])
        with nc1:
            new_ch = st.text_input("Agregar canal", key="new_channel_name").strip().upper()
        with nc2:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button("+ Agregar canal"):
                if new_ch and new_ch not in data["channels"]:
                    data["channels"][new_ch] = []
                    admin_changed = True
                elif new_ch in data["channels"]:
                    st.warning("Ese canal ya existe.")

    with st.expander("📝 Prefijos por canal", expanded=True):
        admin_channel = st.selectbox("Canal", list(data["channels"].keys()), key="admin_channel_sel")
        prefix_list = data["channels"][admin_channel]

        st.markdown("Agregar prefijo")
        ap1, ap2, ap3 = st.columns([2, 2, 1])
        with ap1:
            new_pfx = st.text_input("Prefijo", key="new_pfx").strip().upper()
        with ap2:
            new_rule = st.selectbox("Regla", list(RULE_DAYS.keys()), key="new_pfx_rule")
        with ap3:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button("+ Agregar"):
                if new_pfx:
                    if any(p["prefix"] == new_pfx for p in prefix_list):
                        st.warning("Ese prefijo ya existe en este canal.")
                    else:
                        prefix_list.append({"prefix": new_pfx, "rule": new_rule})
                        admin_changed = True

        st.divider()
        st.markdown("Prefijos actuales")

        grp = {}
        for item in prefix_list:
            grp.setdefault(item["rule"], []).append(item)
        sorted_r = sorted(grp.keys(), key=lambda r: RULE_ORDER.index(r) if r in RULE_ORDER else 99)

        for rule in sorted_r:
            st.markdown(f"{rule}")
            for item in grp[rule]:
                r1, r2, r3 = st.columns([2, 2, 1])

                with r1:
                    st.code(item["prefix"])

                with r2:
                    new_r = st.selectbox(
                        "Regla",
                        list(RULE_DAYS.keys()),
                        index=list(RULE_DAYS.keys()).index(item["rule"]),
                        key=f"rule_{admin_channel}_{item['prefix']}",
                        label_visibility="collapsed",
                    )
                    if new_r != item["rule"]:
                        item["rule"] = new_r
                        admin_changed = True

                with r3:
                    if st.button("Quitar", key=f"rm_{admin_channel}_{item['prefix']}"):
                        data["channels"][admin_channel] = [
                            p for p in prefix_list if p["prefix"] != item["prefix"]
                        ]
                        admin_changed = True
                        st.rerun()

    if admin_changed:
        try:
            new_sha = save_data(data, st.session_state.sha)
            fresh_data, _ = load_data()
            st.session_state.data = fresh_data
            st.session_state.sha = new_sha
            st.success("Guardado")
            st.rerun()
        except Exception as e:
            st.error(f"Error guardando: {e}")

# ── Log tab ───────────────────────────────────────────────────────────────────
with tabs[len(channels) + 2]:
    st.markdown("### 📋 Log de borrados")

    log = data.get("log", [])
    if not log:
        st.info("Sin registros aún.")
    else:
        filter_ch = st.selectbox("Filtrar por canal", ["Todos"] + channels, key="log_filter")
        filter_year = st.selectbox(
            "Filtrar por año",
            ["Todos"] + sorted({str(e["year"]) for e in log}, reverse=True),
            key="log_year"
        )

        filtered = log
        if filter_ch != "Todos":
            ch_prefixes = {p["prefix"] for p in data["channels"].get(filter_ch, [])}
            filtered = [e for e in filtered if e["prefix"] in ch_prefixes]
        if filter_year != "Todos":
            filtered = [e for e in filtered if str(e["year"]) == filter_year]

        st.markdown(f"{len(filtered)} registros")

        cols = st.columns(3)
        for idx, entry in enumerate(filtered):
            with cols[idx % 3]:
                st.markdown(
                    f'<div class="log-entry">'
                    f'<span class="log-id">{entry["id"]}</span>'
                    f'&nbsp;&nbsp;<span class="done-badge">✓ borrado</span>'
                    f'<div class="log-meta">{entry["rule"]} · Año {entry["year"]} · {entry["doneAt"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                copy_button(entry["id"], key=f"log_copy_{idx}")