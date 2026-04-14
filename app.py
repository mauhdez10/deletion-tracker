import streamlit as st
import json
import base64
import requests
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

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
/* Hide Streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}

/* Rule badge colors */
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
div[data-testid="stCheckbox"] label {font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

# ── GitHub helpers ────────────────────────────────────────────────────────────
GITHUB_TOKEN  = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO   = st.secrets["GITHUB_REPO"]   # e.g. "youruser/deletion-tracker"
DATA_FILE     = "data.json"
GITHUB_API    = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
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
    "checked": {},   # key: "YEAR__PREFIX__MM"  e.g. "2025__NGGTA__03"
    "log": [],
}

@st.cache_data(ttl=30)
def load_data():
    resp = requests.get(GITHUB_API, headers=HEADERS)
    if resp.status_code == 404:
        return DEFAULT_DATA.copy(), None
    resp.raise_for_status()
    j = resp.json()
    content = json.loads(base64.b64decode(j["content"]).decode())
    sha = j["sha"]
    return content, sha

def save_data(data, sha):
    body = json.dumps(data, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(body.encode()).decode()
    payload = {
        "message": f"update data {datetime.utcnow().isoformat()}",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha
    resp = requests.put(GITHUB_API, headers=HEADERS, json=payload)
    resp.raise_for_status()
    load_data.clear()

# ── Business logic ────────────────────────────────────────────────────────────
RULE_DAYS = {
    "2 DIAS": 2, "1 SEMANA": 7, "2 SEMANAS": 14,
    "3 SEMANAS": 21, "4 SEMANAS": 28,
    "1 MES": 30, "2 MES": 60, "3 MES": 90, "3 MESES": 90,
}
RULE_ORDER = list(RULE_DAYS.keys())

RULE_BADGE = {
    "2 DIAS":    "badge-2dias",
    "1 SEMANA":  "badge-1sem",
    "2 SEMANAS": "badge-2sem",
    "3 SEMANAS": "badge-3sem",
    "4 SEMANAS": "badge-4sem",
    "1 MES":     "badge-1mes",
    "2 MES":     "badge-nmes",
    "3 MES":     "badge-nmes",
    "3 MESES":   "badge-nmes",
}

def get_eligible_months(rule: str, today: date) -> list[str]:
    """
    Return the 2 oldest month strings (MM) that are FULLY past the deletion
    window.  A month is eligible only when the entire month has cleared the
    cutoff.  E.g. rule=2 DIAS, today=Apr 14 → cutoff=Apr 12.
    The last complete month before Apr 12 is March (ends Mar 31 < Apr 12) ✓
    February is also eligible.  April is NOT (still ongoing past cutoff).
    """
    days = RULE_DAYS.get(rule, 0)
    cutoff = today - timedelta(days=days)
    # The latest month that is fully past = the month BEFORE cutoff's month
    # (because cutoff.month is still partially in the future relative to cutoff)
    # Actually: a month M is fully past if the first day of the NEXT month <= cutoff
    months = []
    # Walk back from cutoff month - 1 and collect up to 2
    check = date(cutoff.year, cutoff.month, 1) - timedelta(days=1)  # last day of prev month
    while len(months) < 2:
        m_str = check.strftime("%m")
        months.append((check.year, m_str))
        check = date(check.year, check.month, 1) - timedelta(days=1)
    return months  # list of (year, "MM")

def check_key(year: int, prefix: str, mm: str) -> str:
    return f"{year}__{prefix}__{mm}"

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
    # Replace existing entry for same key, then prepend
    data["log"] = [entry] + [e for e in data["log"]
                              if not (e["prefix"] == prefix and e["mm"] == mm and e["year"] == year)]
    data["log"] = data["log"][:500]

# ── App ───────────────────────────────────────────────────────────────────────
today = date.today()

if "data" not in st.session_state:
    d, sha = load_data()
    st.session_state.data = d
    st.session_state.sha  = sha

data = st.session_state.data
channels = list(data["channels"].keys())

# Header
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("## 🗑️ Guía de Borrado")
with col_date:
    st.markdown(f"<p style='text-align:right;color:#888;padding-top:14px'>{today.strftime('%A %d/%m/%Y').capitalize()}</p>",
                unsafe_allow_html=True)

# Tabs: channels + Admin + Log
tab_labels = channels + ["⚙ Admin", "📋 Log"]
tabs = st.tabs(tab_labels)

# ── Channel tabs ──────────────────────────────────────────────────────────────
for i, channel in enumerate(channels):
    with tabs[i]:
        prefixes = data["channels"][channel]

        # Group by rule
        groups: dict[str, list] = {}
        for item in prefixes:
            groups.setdefault(item["rule"], []).append(item)
        sorted_rules = sorted(groups.keys(), key=lambda r: RULE_ORDER.index(r) if r in RULE_ORDER else 99)

        # Progress
        all_ids = [(yr, item["prefix"], mm)
                   for item in prefixes
                   for yr, mm in get_eligible_months(item["rule"], today)]
        done_count = sum(1 for yr, p, mm in all_ids if is_done(data, yr, p, mm))
        total = len(all_ids)
        st.progress(done_count / total if total else 0,
                    text=f"{done_count}/{total} completados")

        changed = False
        for rule in sorted_rules:
            items = groups[rule]
            badge_cls = RULE_BADGE.get(rule, "badge-nmes")
            days = RULE_DAYS.get(rule, 0)
            cutoff = today - timedelta(days=days)

            # Count pending for this rule
            rule_ids = [(yr, it["prefix"], mm)
                        for it in items
                        for yr, mm in get_eligible_months(it["rule"], today)]
            rule_pending = sum(1 for yr, p, mm in rule_ids if not is_done(data, yr, p, mm))

            pending_html = (
                f'<span class="pending-badge">{rule_pending} pendiente{"s" if rule_pending!=1 else ""}</span>'
                if rule_pending else '<span class="done-badge">✓ Completo</span>'
            )
            st.markdown(
                f'<div style="margin:18px 0 8px">'
                f'<span class="rule-header {badge_cls}">{rule}</span>'
                f'<span class="cutoff-text">Borrar anterior a {cutoff.strftime("%d/%m/%Y")}</span>'
                f'&nbsp;&nbsp;{pending_html}</div>',
                unsafe_allow_html=True,
            )

            # Cards in a responsive grid
            cols = st.columns(min(len(items) * 2, 6))
            col_idx = 0
            for item in items:
                eligible = get_eligible_months(item["rule"], today)
                for yr, mm in eligible:
                    label_id = f"{item['prefix']}{mm}"
                    done = is_done(data, yr, item["prefix"], mm)
                    with cols[col_idx % len(cols)]:
                        if done:
                            st.markdown(
                                f'<div style="background:#E1F5EE;border:1px solid #5DCAA5;border-radius:10px;'
                                f'padding:10px 14px;margin-bottom:8px">'
                                f'<span class="id-done">✓ {label_id}</span>'
                                f'<div style="font-size:0.72rem;color:#1D9E75;margin-top:2px">{yr} · {item["rule"]}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            if st.button(f"☐  {label_id}", key=f"chk_{channel}_{yr}_{label_id}",
                                         use_container_width=True):
                                mark_done(data, yr, item["prefix"], mm, item["rule"])
                                changed = True
                    col_idx += 1

        if changed:
            try:
                save_data(data, st.session_state.sha)
                _, new_sha = load_data()
                st.session_state.sha = new_sha
                st.rerun()
            except Exception as e:
                st.error(f"Error guardando: {e}")

# ── Admin tab ─────────────────────────────────────────────────────────────────
with tabs[len(channels)]:
    st.markdown("### ⚙ Administración")
    admin_changed = False

    # ── Manage channels ──
    with st.expander("📺 Canales", expanded=True):
        st.markdown("**Canales actuales**")
        for ch in list(data["channels"].keys()):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"**{ch}** — {len(data['channels'][ch])} prefijos")
            with c3:
                if st.button("🗑 Eliminar", key=f"del_ch_{ch}"):
                    if len(data["channels"]) <= 1:
                        st.warning("Debe haber al menos un canal.")
                    elif st.session_state.get(f"confirm_del_{ch}"):
                        del data["channels"][ch]
                        admin_changed = True
                    else:
                        st.session_state[f"confirm_del_{ch}"] = True
                        st.warning(f"¿Seguro? Presiona de nuevo para confirmar.")

        st.divider()
        st.markdown("**Agregar canal**")
        nc1, nc2 = st.columns([2, 1])
        with nc1:
            new_ch = st.text_input("Nombre del canal", key="new_channel_name").strip().upper()
        with nc2:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button("+ Agregar canal"):
                if new_ch and new_ch not in data["channels"]:
                    data["channels"][new_ch] = []
                    admin_changed = True
                elif new_ch in data["channels"]:
                    st.warning("Ese canal ya existe.")

    # ── Manage prefixes ──
    with st.expander("📝 Prefijos por canal", expanded=True):
        admin_channel = st.selectbox("Canal", list(data["channels"].keys()), key="admin_channel_sel")
        prefix_list = data["channels"][admin_channel]

        # Add new prefix
        st.markdown("**Agregar prefijo**")
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
        st.markdown("**Prefijos actuales**")

        # Group by rule for display
        grp: dict[str, list] = {}
        for item in prefix_list:
            grp.setdefault(item["rule"], []).append(item)
        sorted_r = sorted(grp.keys(), key=lambda r: RULE_ORDER.index(r) if r in RULE_ORDER else 99)

        for rule in sorted_r:
            st.markdown(f"*{rule}*")
            for item in grp[rule]:
                r1, r2, r3, r4 = st.columns([2, 2, 1, 1])
                with r1:
                    st.markdown(f"`{item['prefix']}`")
                with r2:
                    new_r = st.selectbox("", list(RULE_DAYS.keys()),
                                         index=list(RULE_DAYS.keys()).index(item["rule"]),
                                         key=f"rule_{admin_channel}_{item['prefix']}",
                                         label_visibility="collapsed")
                    if new_r != item["rule"]:
                        item["rule"] = new_r
                        admin_changed = True
                with r4:
                    if st.button("✕", key=f"rm_{admin_channel}_{item['prefix']}"):
                        data["channels"][admin_channel] = [
                            p for p in prefix_list if p["prefix"] != item["prefix"]
                        ]
                        admin_changed = True
                        st.rerun()

    if admin_changed:
        try:
            save_data(data, st.session_state.sha)
            _, new_sha = load_data()
            st.session_state.sha = new_sha
            st.success("✓ Guardado")
            st.rerun()
        except Exception as e:
            st.error(f"Error guardando: {e}")

# ── Log tab ───────────────────────────────────────────────────────────────────
with tabs[len(channels) + 1]:
    st.markdown("### 📋 Log de borrados")

    log = data.get("log", [])
    if not log:
        st.info("Sin registros aún.")
    else:
        filter_ch = st.selectbox("Filtrar por canal", ["Todos"] + channels, key="log_filter")
        filter_year = st.selectbox("Filtrar por año", ["Todos"] + sorted({str(e["year"]) for e in log}, reverse=True), key="log_year")

        filtered = log
        if filter_ch != "Todos":
            ch_prefixes = {p["prefix"] for p in data["channels"].get(filter_ch, [])}
            filtered = [e for e in filtered if e["prefix"] in ch_prefixes]
        if filter_year != "Todos":
            filtered = [e for e in filtered if str(e["year"]) == filter_year]

        st.markdown(f"**{len(filtered)} registros**")
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
