import streamlit as st
import streamlit.components.v1 as components
import json
import base64
import requests
from datetime import date, datetime, timedelta
from html import escape

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Guía de Borrado",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}

.badge-2dias  {background:#FAECE7;color:#993C1D;border:1px solid #F0997B;}
.badge-1sem   {background:#FAEEDA;color:#854F0B;border:1px solid #EF9F27;}
.badge-2sem   {background:#E6F1FB;color:#185FA5;border:1px solid #85B7EB;}
.badge-3sem   {background:#EEEDFE;color:#534AB7;border:1px solid #AFA9EC;}
.badge-4sem   {background:#EAF3DE;color:#3B6D11;border:1px solid #97C459;}
.badge-1mes   {background:#FBEAF0;color:#993556;border:1px solid #ED93B1;}
.badge-nmes   {background:#F1EFE8;color:#5F5E5A;border:1px solid #B4B2A9;}

.rule-header {
    display:inline-block;
    padding:3px 12px;
    border-radius:6px;
    font-size:0.78rem;
    font-weight:600;
    margin-right:10px;
}
.cutoff-text {font-size:0.78rem; color:#888;}

.done-badge {
    background:#E1F5EE;color:#0F6E56;
    border:1px solid #5DCAA5;
    border-radius:12px;
    padding:2px 8px;
    font-size:0.72rem;
    font-weight:600;
}
.pending-badge {
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
.small-muted {color:#888; font-size:0.78rem;}

.log-entry {
    background:#f9f9f9;
    border:1px solid #eee;
    border-radius:8px;
    padding:10px 12px;
    margin-bottom:8px;
}
.log-id  {font-family:monospace; font-weight:700; font-size:0.95rem;}
.log-meta{font-size:0.75rem; color:#888; margin-top:2px;}

/* ID button cards — override Streamlit button styles */
div[data-testid="stButton"] button.id-pending {
    background: white !important;
    border: 1.5px solid #ddd !important;
    border-radius: 10px !important;
    color: #111 !important;
    font-family: monospace !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    text-align: left !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: border-color .15s, background .15s !important;
    min-height: 62px !important;
}
div[data-testid="stButton"] button.id-pending:hover {
    border-color: #85B7EB !important;
    background: #F7FBFF !important;
}
div[data-testid="stButton"] button.id-selected {
    background: #EBF5FF !important;
    border: 1.5px solid #378ADD !important;
    border-radius: 10px !important;
    color: #185FA5 !important;
    font-family: monospace !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    padding: 10px 14px !important;
    text-align: left !important;
    width: 100% !important;
    min-height: 62px !important;
}
div[data-testid="stButton"] button.id-done {
    background: #E1F5EE !important;
    border: 1.5px solid #5DCAA5 !important;
    border-radius: 10px !important;
    color: #0F6E56 !important;
    font-family: monospace !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    text-align: left !important;
    width: 100% !important;
    cursor: default !important;
    min-height: 62px !important;
}
.copy-wrap {
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# ── GitHub ─────────────────────────────────────────────────────────────────────
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO  = st.secrets["GITHUB_REPO"]
DATA_FILE    = "data.json"
GITHUB_API   = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
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

# ── Data loading / saving ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_from_github():
    resp = requests.get(GITHUB_API, headers=HEADERS, timeout=30)
    if resp.status_code == 404:
        return DEFAULT_DATA.copy(), None
    resp.raise_for_status()
    j = resp.json()
    content = json.loads(base64.b64decode(j["content"]).decode("utf-8"))
    return content, j["sha"]

def save_to_github(data, sha):
    body = json.dumps(data, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(body.encode("utf-8")).decode("utf-8")
    payload = {"message": f"update {datetime.utcnow().isoformat()}", "content": encoded}
    if sha:
        payload["sha"] = sha
    resp = requests.put(GITHUB_API, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    fetch_from_github.clear()
    return resp.json()["content"]["sha"]

def load_into_session():
    d, sha = fetch_from_github()
    st.session_state.data = d
    st.session_state.sha = sha

def save_and_rerun(data):
    with st.spinner("Guardando…"):
        new_sha = save_to_github(data, st.session_state.sha)
    st.session_state.sha = new_sha
    st.session_state.selected_ids = set()
    st.rerun()

# ── Business logic ─────────────────────────────────────────────────────────────
RULE_DAYS = {
    "2 DIAS": 2, "1 SEMANA": 7, "2 SEMANAS": 14,
    "3 SEMANAS": 21, "4 SEMANAS": 28,
    "1 MES": 30, "2 MES": 60, "3 MES": 90, "3 MESES": 90,
}
RULE_ORDER = list(RULE_DAYS.keys())
RULE_BADGE = {
    "2 DIAS": "badge-2dias", "1 SEMANA": "badge-1sem",
    "2 SEMANAS": "badge-2sem", "3 SEMANAS": "badge-3sem",
    "4 SEMANAS": "badge-4sem", "1 MES": "badge-1mes",
    "2 MES": "badge-nmes", "3 MES": "badge-nmes", "3 MESES": "badge-nmes",
}

def eligible_months(rule, today):
    cutoff = today - timedelta(days=RULE_DAYS.get(rule, 0))
    d1 = date(cutoff.year, cutoff.month, 1) - timedelta(days=1)
    d2 = date(d1.year, d1.month, 1) - timedelta(days=1)
    return [(d1.year, d1.strftime("%m")), (d2.year, d2.strftime("%m"))]

def done_key(year, prefix, mm):
    return f"{year}__{prefix}__{mm}"

def sel_key(year, prefix, mm):
    return f"{year}__{prefix}__{mm}"

def is_done(data, year, prefix, mm):
    return bool(data["checked"].get(done_key(year, prefix, mm)))

def is_selected(year, prefix, mm):
    return sel_key(year, prefix, mm) in st.session_state.selected_ids

def toggle_selected(year, prefix, mm):
    k = sel_key(year, prefix, mm)
    if k in st.session_state.selected_ids:
        st.session_state.selected_ids.discard(k)
    else:
        st.session_state.selected_ids.add(k)

def get_rule_for_prefix(data, prefix):
    for items in data["channels"].values():
        for item in items:
            if item["prefix"] == prefix:
                return item["rule"]
    return ""

def mark_done(data, year, prefix, mm, rule):
    data["checked"][done_key(year, prefix, mm)] = True
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

def undo_done(data, year, prefix, mm):
    data["checked"].pop(done_key(year, prefix, mm), None)
    data["log"] = [
        e for e in data["log"]
        if not (e["prefix"] == prefix and e["year"] == int(year) and e["mm"] == mm)
    ]

def commit_selected(data):
    count = 0
    for skey in list(st.session_state.selected_ids):
        year, prefix, mm = skey.split("__")
        if not is_done(data, int(year), prefix, mm):
            rule = get_rule_for_prefix(data, prefix)
            mark_done(data, int(year), prefix, mm, rule)
            count += 1
    return count

# ── UI components ──────────────────────────────────────────────────────────────
def copy_button(text, key):
    safe_text = json.dumps(text)
    safe_key = escape(key)
    html = f"""
    <div class="copy-wrap">
        <button id="{safe_key}" onclick='
            navigator.clipboard.writeText({safe_text});
            const b=document.getElementById("{safe_key}");
            const orig=b.innerText;
            b.innerText="✓ Copiado";
            b.style.cssText="background:#E1F5EE;border:1px solid #5DCAA5;color:#0F6E56;border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;width:100%";
            setTimeout(()=>{{b.innerText=orig;b.style.cssText="background:#f5f5f5;border:1px solid #ddd;color:#555;border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;width:100%"}},1200);
        ' style="background:#f5f5f5;border:1px solid #ddd;color:#555;border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;width:100%">📋 Copiar</button>
    </div>
    """
    components.html(html, height=36, scrolling=False)

def render_action_bar(data, scope):
    n = len(st.session_state.selected_ids)
    with st.container():
        st.markdown('<div class="action-wrap">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.4, 1.2, 4])
        with c1:
            label = f"✓ Done ({n} seleccionados)" if n else "✓ Done selected"
            if st.button(label, key=f"done_btn_{scope}", use_container_width=True,
                         type="primary" if n else "secondary"):
                if n == 0:
                    st.toast("Selecciona al menos un ID primero.", icon="⚠️")
                else:
                    committed = commit_selected(data)
                    if committed:
                        save_and_rerun(data)
        with c2:
            if st.button("✕ Limpiar selección", key=f"clear_btn_{scope}", use_container_width=True):
                st.session_state.selected_ids = set()
                st.rerun()
        with c3:
            st.markdown(
                "<div class='small-muted' style='padding-top:8px'>"
                "Haz clic en los IDs para seleccionar, luego presiona Done."
                "</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

def render_id_card(data, year, prefix, mm, channel, scope):
    label_id = f"{prefix}{mm}"
    btn_key = f"idbtn__{scope}__{channel}__{year}__{prefix}__{mm}"
    copy_key = f"copy__{scope}__{channel}__{year}__{prefix}__{mm}"

    done = is_done(data, year, prefix, mm)
    selected = is_selected(year, prefix, mm)

    left, right = st.columns([4, 1])

    with left:
        if done:
            st.markdown(
                f'<div style="background:#E1F5EE;border:1.5px solid #5DCAA5;border-radius:10px;'
                f'padding:10px 14px;margin-bottom:8px;font-family:monospace;font-size:0.95rem;'
                f'font-weight:600;color:#0F6E56;">✓ {label_id}'
                f'<div style="font-size:0.72rem;color:#1D9E75;font-family:sans-serif;margin-top:2px">Año {year}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            indicator = "☑" if selected else "☐"
            btn_label = f"{indicator}  {label_id}\nAño {year}"
            if st.button(btn_label, key=btn_key, use_container_width=True):
                toggle_selected(year, prefix, mm)
                st.rerun()

            class_name = "id-selected" if selected else "id-pending"
            st.markdown(
                f"""
                <style>
                div[data-testid="stButton"] button[kind][data-testid="baseButton-secondary"] {{
                    }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <script>
                </script>
                """,
                unsafe_allow_html=True,
            )

    with right:
        copy_button(label_id, copy_key)

def render_channel_blocks(data, channel, today, scope):
    prefixes = data["channels"][channel]
    groups = {}
    for item in prefixes:
        groups.setdefault(item["rule"], []).append(item)

    all_ids = [(yr, it["prefix"], mm) for it in prefixes for yr, mm in eligible_months(it["rule"], today)]
    done_count = sum(1 for yr, p, mm in all_ids if is_done(data, yr, p, mm))
    total = len(all_ids)
    st.progress(done_count / total if total else 0, text=f"{done_count}/{total} completados")

    any_pending = False
    for rule in sorted(groups.keys(), key=lambda r: RULE_ORDER.index(r) if r in RULE_ORDER else 999):
        items = groups[rule]
        badge_cls = RULE_BADGE.get(rule, "badge-nmes")
        cutoff = today - timedelta(days=RULE_DAYS.get(rule, 0))

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
            st.caption("Nada pendiente.")
            continue

        any_pending = True
        for yr in sorted(by_year.keys(), reverse=True):
            if len(groups) > 1:
                st.caption(f"Año {yr}")
            cols = st.columns(4)
            for idx, (prefix, mm) in enumerate(sorted(by_year[yr], key=lambda x: (x[1], x[0]), reverse=True)):
                with cols[idx % 4]:
                    render_id_card(data, yr, prefix, mm, channel, scope)

    if not any_pending:
        st.success("✓ No hay IDs pendientes en este canal.")

# ── Admin ──────────────────────────────────────────────────────────────────────
def render_admin(data):
    st.markdown("### ⚙ Administración")
    admin_changed = False

    with st.expander("📺 Canales", expanded=True):
        for ch in list(data["channels"].keys()):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{ch}** — {len(data['channels'][ch])} prefijos")
            with c2:
                confirm_key = f"confirm_del_ch_{ch}"
                if st.button("🗑", key=f"del_ch_{ch}", help=f"Eliminar {ch}"):
                    st.session_state[confirm_key] = True
                if st.session_state.get(confirm_key):
                    st.warning(f"¿Eliminar canal {ch}? Esta acción no se puede deshacer.")
                    y1, y2 = st.columns(2)
                    with y1:
                        if st.button("Sí, eliminar", key=f"yes_del_{ch}"):
                            if len(data["channels"]) <= 1:
                                st.error("Debe haber al menos un canal.")
                            else:
                                del data["channels"][ch]
                                st.session_state.pop(confirm_key, None)
                                admin_changed = True
                    with y2:
                        if st.button("Cancelar", key=f"no_del_{ch}"):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()

        st.divider()
        nc1, nc2 = st.columns([3, 1])
        with nc1:
            new_ch = st.text_input("Nombre del nuevo canal", key="new_channel_name").strip().upper()
        with nc2:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button("+ Agregar canal"):
                if not new_ch:
                    st.warning("Ingresa un nombre.")
                elif new_ch in data["channels"]:
                    st.warning("Canal ya existe.")
                else:
                    data["channels"][new_ch] = []
                    admin_changed = True

    with st.expander("📝 Prefijos", expanded=True):
        admin_ch = st.selectbox("Canal", list(data["channels"].keys()), key="admin_ch_sel")
        prefix_list = data["channels"][admin_ch]

        st.markdown("**Agregar prefijo**")
        ap1, ap2, ap3 = st.columns([2, 2, 1])
        with ap1:
            new_pfx = st.text_input("Prefijo", key="new_pfx_input").strip().upper()
        with ap2:
            new_rule = st.selectbox("Regla", list(RULE_DAYS.keys()), key="new_pfx_rule")
        with ap3:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button("+ Agregar"):
                if not new_pfx:
                    st.warning("Ingresa un prefijo.")
                elif any(p["prefix"] == new_pfx for p in prefix_list):
                    st.warning("Prefijo ya existe en este canal.")
                else:
                    prefix_list.append({"prefix": new_pfx, "rule": new_rule})
                    admin_changed = True

        st.divider()
        st.markdown("**Prefijos actuales**")
        grp = {}
        for item in prefix_list:
            grp.setdefault(item["rule"], []).append(item)
        for rule in sorted(grp.keys(), key=lambda r: RULE_ORDER.index(r) if r in RULE_ORDER else 999):
            st.markdown(f"*{rule}*")
            for item in grp[rule]:
                r1, r2, r3 = st.columns([2, 3, 0.5])
                with r1:
                    st.markdown(f"`{item['prefix']}`")
                with r2:
                    new_r = st.selectbox(
                        "", list(RULE_DAYS.keys()),
                        index=list(RULE_DAYS.keys()).index(item["rule"]),
                        key=f"rule_sel_{admin_ch}_{item['prefix']}",
                        label_visibility="collapsed",
                    )
                    if new_r != item["rule"]:
                        item["rule"] = new_r
                        admin_changed = True
                with r3:
                    if st.button("✕", key=f"rm_{admin_ch}_{item['prefix']}", help="Eliminar"):
                        data["channels"][admin_ch] = [
                            p for p in prefix_list if p["prefix"] != item["prefix"]
                        ]
                        admin_changed = True
                        st.rerun()

    if admin_changed:
        save_and_rerun(data)

# ── Log ────────────────────────────────────────────────────────────────────────
def render_log(data):
    st.markdown("### 📋 Log de borrados")
    log = data.get("log", [])
    if not log:
        st.info("Sin registros aún.")
        return

    f1, f2, f3 = st.columns([1.3, 1.2, 1.2])
    with f1:
        filter_ch = st.selectbox("Canal", ["Todos"] + list(data["channels"].keys()), key="lf_ch")
    with f2:
        filter_yr = st.selectbox("Año", ["Todos"] + sorted({str(e["year"]) for e in log}, reverse=True), key="lf_yr")
    with f3:
        sort_mode = st.selectbox("Ordenar", ["Más recientes", "Más antiguos", "ID A-Z", "ID Z-A"], key="lf_sort")

    filtered = log
    if filter_ch != "Todos":
        ch_pfx = {p["prefix"] for p in data["channels"].get(filter_ch, [])}
        filtered = [e for e in filtered if e["prefix"] in ch_pfx]
    if filter_yr != "Todos":
        filtered = [e for e in filtered if str(e["year"]) == filter_yr]
    if sort_mode == "Más antiguos":
        filtered = list(reversed(filtered))
    elif sort_mode == "ID A-Z":
        filtered = sorted(filtered, key=lambda e: e["id"])
    elif sort_mode == "ID Z-A":
        filtered = sorted(filtered, key=lambda e: e["id"], reverse=True)

    st.markdown(f"**{len(filtered)} registros**")
    cols = st.columns(3)
    for idx, e in enumerate(filtered):
        with cols[idx % 3]:
            st.markdown(
                f'<div class="log-entry">'
                f'<span class="log-id">{e["id"]}</span>&nbsp;&nbsp;'
                f'<span class="done-badge">✓ borrado</span>'
                f'<div class="log-meta">{e.get("rule","")} · Año {e["year"]} · {e["doneAt"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            la, lb = st.columns(2)
            with la:
                copy_button(e["id"], key=f"log_copy_{idx}")
            with lb:
                if st.button("↩ Recuperar", key=f"undo_{idx}_{e['year']}_{e['prefix']}_{e['mm']}",
                             use_container_width=True):
                    undo_done(data, e["year"], e["prefix"], e["mm"])
                    save_and_rerun(data)

# ── Main ───────────────────────────────────────────────────────────────────────
today = date.today()

if "data" not in st.session_state:
    load_into_session()
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = set()

data = st.session_state.data
channels = list(data["channels"].keys())

# Header
hc1, hc2 = st.columns([3, 1])
with hc1:
    st.markdown("## 🗑️ Guía de Borrado")
with hc2:
    st.markdown(
        f"<p style='text-align:right;color:#888;padding-top:14px'>"
        f"{today.strftime('%A %d/%m/%Y').capitalize()}</p>",
        unsafe_allow_html=True,
    )

tabs = st.tabs(["📌 Todos"] + channels + ["⚙ Admin", "📋 Log"])

with tabs[0]:
    render_action_bar(data, "all")
    for ch in channels:
        st.markdown(f"### {ch}")
        render_channel_blocks(data, ch, today, f"all_{ch}")
        st.divider()

for i, ch in enumerate(channels, start=1):
    with tabs[i]:
        render_action_bar(data, f"ch_{ch}")
        render_channel_blocks(data, ch, today, f"ch_{ch}")

with tabs[len(channels) + 1]:
    render_admin(data)

with tabs[len(channels) + 2]:
    render_log(data)