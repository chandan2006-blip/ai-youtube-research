
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import io
import html

# Backend
from main import (
    REGIONS,
    TREND_WINDOWS,
    get_my_api_key,
    get_selected_api_key,
    validate_api_key,
    trend_finder,
    discover_trending,
    keyword_scanner,
    analyze_channel,
    analyze_competitors,
    extract_topic_signals,
    format_number,
    export_results,
    export_csv,
)

# ============================================================
# BRAND / PAGE
# ============================================================
APP_NAME = "AI YouTube Research"
APP_TAGLINE = "AI-Powered YouTube Research"
DEVELOPER = "Chandan Verma"

st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PREMIUM UI
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #070a11;
    --panel: #0d121b;
    --panel2: #101722;
    --border: rgba(255,255,255,.075);
    --muted: #8490a3;
    --text: #f5f7fb;
    --accent: #7c6cff;
    --accent2: #a78bfa;
    --green: #35d399;
    --red: #ff647c;
}

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 85% -5%, rgba(124,108,255,.18), transparent 27%),
        radial-gradient(circle at -5% 25%, rgba(35,211,238,.06), transparent 25%),
        var(--bg);
    color: var(--text);
}

.block-container {
    max-width: 1480px;
    padding: 1.3rem 2rem 3rem;
}

#MainMenu, footer { visibility: hidden; }

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: #090d15;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.1rem;
}

[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}

[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    opacity: 1 !important;
}

/* Native controls */
.stButton > button {
    min-height: 42px;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,.09);
    background: #111824;
    color: #f5f7fb;
    font-weight: 700;
    transition: .18s ease;
}

.stButton > button:hover {
    border-color: rgba(124,108,255,.7);
    background: #171d2b;
    transform: translateY(-1px);
}

button[kind="primary"] {
    background: linear-gradient(135deg,#6d5dfc,#8d67ff) !important;
    border: none !important;
    box-shadow: 0 10px 30px rgba(124,108,255,.18);
}

.stTextInput input,
.stTextArea textarea,
div[data-baseweb="select"] > div {
    background: #0f151f !important;
    color: #f5f7fb !important;
    border: 1px solid rgba(255,255,255,.09) !important;
    border-radius: 10px !important;
}

label {
    color: #98a3b6 !important;
    font-size: .78rem !important;
    font-weight: 650 !important;
}

.stSlider [data-baseweb="slider"] {
    padding-top: .3rem;
}

/* Sidebar */
.side-logo {
    display:flex;
    align-items:center;
    gap:10px;
    padding: 4px 2px 20px;
}
.logo-mark {
    width:39px;
    height:39px;
    border-radius:11px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:linear-gradient(135deg,#6557ef,#9b72ff);
    box-shadow:0 9px 28px rgba(124,108,255,.25);
    font-size:18px;
}
.logo-name {
    font-weight:800;
    font-size:1.08rem;
    letter-spacing:-.035em;
}
.logo-sub {
    color:#69758a;
    font-size:.65rem;
    margin-top:2px;
}

.sidebar-heading {
    color:#69758a;
    font-size:.63rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:.15em;
    margin:18px 0 8px;
}

.connection {
    padding:12px 13px;
    border-radius:11px;
    background:rgba(53,211,153,.055);
    border:1px solid rgba(53,211,153,.12);
    color:#b9c4d5;
    font-size:.72rem;
    line-height:1.5;
}
.connection-dot {
    display:inline-block;
    width:7px;
    height:7px;
    border-radius:50%;
    background:#35d399;
    box-shadow:0 0 12px rgba(53,211,153,.7);
    margin-right:7px;
}

/* Topbar */
.topbar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:20px;
    margin-bottom:16px;
}
.brand-row {
    display:flex;
    align-items:center;
    gap:12px;
}
.brand-title {
    font-size:1.15rem;
    font-weight:800;
    letter-spacing:-.035em;
}
.brand-desc {
    color:#727e92;
    font-size:.72rem;
    margin-top:2px;
}
.live-pill {
    border:1px solid rgba(255,255,255,.08);
    background:rgba(255,255,255,.035);
    padding:7px 10px;
    border-radius:999px;
    color:#aeb8c9;
    font-size:.69rem;
}
.live-dot {
    display:inline-block;
    width:6px;
    height:6px;
    border-radius:50%;
    background:#35d399;
    margin-right:6px;
}

/* Hero */
.hero {
    position:relative;
    overflow:hidden;
    border:1px solid var(--border);
    border-radius:22px;
    padding:30px 31px;
    background:
        linear-gradient(125deg,rgba(124,108,255,.16),rgba(255,255,255,.025) 52%),
        var(--panel);
    box-shadow:0 24px 70px rgba(0,0,0,.22);
}
.hero:after {
    content:"";
    position:absolute;
    width:230px;
    height:230px;
    right:-90px;
    top:-100px;
    border-radius:50%;
    background:rgba(124,108,255,.10);
    filter:blur(10px);
}
.hero-kicker {
    color:#a99fff;
    font-size:.67rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:.17em;
}
.hero h1 {
    margin:8px 0 8px;
    font-size:2.35rem;
    line-height:1.04;
    letter-spacing:-.06em;
}
.hero p {
    max-width:720px;
    color:#8e99ab;
    line-height:1.65;
    margin:0;
    font-size:.86rem;
}
.hero-tags {
    display:flex;
    gap:7px;
    flex-wrap:wrap;
    margin-top:18px;
}
.tag {
    border:1px solid rgba(255,255,255,.08);
    background:rgba(255,255,255,.035);
    color:#adb7c8;
    border-radius:999px;
    padding:6px 9px;
    font-size:.66rem;
    font-weight:700;
}

/* Section */
.section-head {
    display:flex;
    align-items:flex-end;
    justify-content:space-between;
    gap:15px;
    margin:23px 0 11px;
}
.section-title {
    font-size:1rem;
    font-weight:800;
    letter-spacing:-.025em;
}
.section-desc {
    color:#687489;
    font-size:.68rem;
    margin-top:3px;
}

/* KPI */
.kpi {
    border:1px solid var(--border);
    border-radius:15px;
    background:var(--panel);
    padding:16px 17px;
    min-height:105px;
}
.kpi-label {
    color:#778399;
    font-size:.67rem;
    font-weight:650;
}
.kpi-value {
    margin-top:7px;
    font-size:1.45rem;
    font-weight:800;
    letter-spacing:-.045em;
}
.kpi-note {
    color:#687489;
    font-size:.65rem;
    margin-top:5px;
}

/* Tool header */
.tool-header {
    border:1px solid var(--border);
    background:var(--panel);
    border-radius:16px;
    padding:18px 20px;
}
.tool-title {
    font-size:1.15rem;
    font-weight:800;
}
.tool-desc {
    color:#7d899c;
    font-size:.73rem;
    margin-top:5px;
}

/* Topic cards */
.topic {
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:14px;
    padding:15px;
    min-height:115px;
}
.topic-rank {
    color:#69758a;
    font-size:.61rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:.1em;
}
.topic-name {
    margin:8px 0;
    font-size:.92rem;
    font-weight:800;
}
.topic-meta {
    color:#7f8a9c;
    font-size:.67rem;
}
.progress {
    height:5px;
    background:#1b2230;
    border-radius:99px;
    overflow:hidden;
    margin-top:10px;
}
.progress > span {
    display:block;
    height:100%;
    background:linear-gradient(90deg,#6b5df5,#a78bfa);
    border-radius:99px;
}

/* Video */
.video {
    border:1px solid var(--border);
    border-radius:14px;
    background:var(--panel);
    padding:15px;
    margin-bottom:9px;
}
.video-title {
    font-size:.83rem;
    font-weight:750;
    line-height:1.4;
}
.video-channel {
    color:#69758a;
    font-size:.66rem;
    margin-top:4px;
}
.video-stats {
    color:#9ba6b8;
    font-size:.66rem;
    margin-top:10px;
}
.watch {
    display:inline-block;
    margin-top:10px;
    padding:6px 9px;
    border:1px solid rgba(124,108,255,.2);
    background:rgba(124,108,255,.07);
    color:#bcb5ff !important;
    text-decoration:none !important;
    border-radius:8px;
    font-size:.64rem;
    font-weight:750;
}
.score-label {
    color:#717d90;
    font-size:.62rem;
    margin-top:9px;
}
.score-value {
    color:#c5beff;
    font-weight:800;
}

/* Footer */
.footer {
    border-top:1px solid rgba(255,255,255,.05);
    margin-top:35px;
    padding-top:17px;
    display:flex;
    justify-content:space-between;
    gap:15px;
    color:#515d70;
    font-size:.62rem;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius:11px;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border:1px solid var(--border);
    border-radius:13px;
    overflow:hidden;
}

.niche-banner {
    margin: 18px 0 10px;
    padding: 13px 16px;
    border: 1px solid rgba(124,108,255,.28);
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(124,108,255,.14), rgba(35,211,238,.05));
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:16px;
}
.niche-banner strong {
    color:#f5f7fb;
    font-size:1rem;
}
.niche-banner-meta {
    color:#8f9bb0;
    font-size:.72rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def selected_key(source, own_key):
    return get_selected_api_key(source, own_key)


def window_hours(window):
    return TREND_WINDOWS.get(window, 24)


def show_kpis(df):
    if df is None or df.empty:
        vals = [
            ("Videos", "0", "No results"),
            ("Total views", "0", "No results"),
            ("Views / hour", "0", "No results"),
            ("Engagement", "0%", "No results"),
            ("Breakout signals", "0", "Opportunity ≥ 80"),
        ]
    else:
        total_views = int(df["views"].sum())
        avg_vph = float(df["views_per_hour"].mean())
        avg_eng = float(df["engagement"].mean())
        breakouts = int((df["opportunity"] >= 80).sum())
        vals = [
            ("Videos", format_number(len(df)), "Analyzed"),
            ("Total views", format_number(total_views), "Result set"),
            ("Views / hour", format_number(avg_vph), "Velocity"),
            ("Engagement", f"{avg_eng:.1f}%", "Likes + comments"),
            ("Breakout signals", format_number(breakouts), "Research signal"),
        ]

    cols = st.columns(5)
    for col, (label, value, note) in zip(cols, vals):
        with col:
            st.markdown(
                f"""<div class="kpi">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-note">{note}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def show_topics(df):
    topics = extract_topic_signals(df, limit=10) if df is not None and not df.empty else pd.DataFrame()
    if topics.empty:
        st.info("No topic signals available yet.")
        return

    cols = st.columns(min(5, len(topics)))
    max_mentions = max(int(topics["mentions"].max()), 1)

    for i, (_, row) in enumerate(topics.head(5).iterrows()):
        with cols[i]:
            width = int((row["mentions"] / max_mentions) * 100)
            st.markdown(
                f"""<div class="topic">
                    <div class="topic-rank">#{i+1} Topic signal</div>
                    <div class="topic-name">{str(row["topic"]).title()}</div>
                    <div class="topic-meta">{int(row["mentions"])} title mentions</div>
                    <div class="progress"><span style="width:{width}%"></span></div>
                </div>""",
                unsafe_allow_html=True,
            )


def show_videos(df, limit=10, title_prefix=""):
    """Render video cards directly in the dashboard with clickable YouTube links."""
    if df is None or df.empty:
        st.info("No videos found for this section.")
        return

    sort_cols = [c for c in ["opportunity", "views_per_hour", "views"] if c in df.columns]
    rows = df.sort_values(sort_cols, ascending=False).head(limit) if sort_cols else df.head(limit)

    for _, row in rows.iterrows():
        score = int(float(row.get("opportunity", row.get("trend_score", 0)) or 0))
        link = str(row.get("link", "#"))
        title = html.escape(str(row.get("title", "Untitled")))
        channel = html.escape(str(row.get("channel", "Unknown")))
        country = html.escape(str(row.get("channel_country", "Unknown")))
        lang = html.escape(str(row.get("language", "Unknown")))
        niche = html.escape(str(row.get("niche", "Other")))

        views = format_number(row.get("views", 0))
        vph = format_number(row.get("views_per_hour", 0))
        likes = format_number(row.get("likes", 0))
        comments = format_number(row.get("comments", 0))
        engagement = float(row.get("engagement", 0) or 0)

        st.markdown(
            f"""<div class="video">
                <div class="video-title">{title}</div>
                <div class="video-channel">📺 {channel} &nbsp; · &nbsp; 🏷️ {niche} &nbsp; · &nbsp; 🌎 {country} &nbsp; · &nbsp; 🔤 {lang}</div>
                <div class="video-stats">
                    👁 {views}
                    &nbsp;&nbsp; ⚡ {vph}/hr
                    &nbsp;&nbsp; ❤️ {likes}
                    &nbsp;&nbsp; 💬 {comments}
                    &nbsp;&nbsp; 📊 {engagement:.1f}%
                </div>
                <div class="score-label">Trend score <span class="score-value">{score}/100</span></div>
                <div class="progress"><span style="width:{min(max(score,0),100)}%"></span></div>
                <a class="watch" href="{html.escape(link, quote=True)}" target="_blank" rel="noopener noreferrer">▶ Watch directly on YouTube ↗</a>
            </div>""",
            unsafe_allow_html=True,
        )


def show_videos_by_niche(df, limit_per_niche=10, section_title="Videos by niche"):
    """Group discovered videos by detected niche and render each niche inline."""
    if df is None or df.empty or "niche" not in df.columns:
        st.info("No niche-level videos available.")
        return

    st.markdown(
        f'<div class="section-head"><div><div class="section-title">🏷️ {section_title}</div><div class="section-desc">Each niche is shown separately with its trending videos and direct YouTube links.</div></div></div>',
        unsafe_allow_html=True,
    )

    grouped = df.groupby("niche", dropna=False)
    order = (
        grouped["views_per_hour"].mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    for niche in order:
        group = df[df["niche"].fillna("Other") == niche].copy()
        total_views = int(group["views"].sum()) if "views" in group else 0
        avg_vph = float(group["views_per_hour"].mean()) if "views_per_hour" in group else 0

        st.markdown(
            f"""<div class="niche-banner">
                <div><strong>🔥 {html.escape(str(niche))}</strong></div>
                <div class="niche-banner-meta">{len(group)} videos · {format_number(total_views)} total views · {format_number(avg_vph)} avg views/hour</div>
            </div>""",
            unsafe_allow_html=True,
        )
        show_videos(group, limit_per_niche)


def show_requested_niche_results(results_by_niche, limit_per_niche=20):
    """Render Niche Finder results grouped by the exact niche the user scanned."""
    if not results_by_niche:
        st.info("No videos found for the selected niches.")
        return

    st.markdown(
        '<div class="section-head"><div><div class="section-title">🎯 Videos found inside each niche</div><div class="section-desc">Every scanned niche has its own video list. Click any button to open the video directly on YouTube.</div></div></div>',
        unsafe_allow_html=True,
    )

    for niche, group in results_by_niche:
        if group is None or group.empty:
            continue

        total_views = int(group["views"].sum()) if "views" in group else 0
        avg_vph = float(group["views_per_hour"].mean()) if "views_per_hour" in group else 0
        st.markdown(
            f"""<div class="niche-banner">
                <div><strong>🎯 {html.escape(str(niche))}</strong></div>
                <div class="niche-banner-meta">{len(group)} videos · {format_number(total_views)} total views · {format_number(avg_vph)} avg views/hour</div>
            </div>""",
            unsafe_allow_html=True,
        )
        show_videos(group, limit_per_niche)


def export_buttons(df, prefix="signalforge_results"):
    if df is None or df.empty:
        return

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    xlsx_buffer = io.BytesIO()
    df.to_excel(xlsx_buffer, index=False)
    xlsx_buffer.seek(0)

    c1, c2, _ = st.columns([1, 1, 5])
    with c1:
        st.download_button(
            "⬇ CSV",
            csv_bytes,
            file_name=f"{prefix}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇ Excel",
            xlsx_buffer.getvalue(),
            file_name=f"{prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ============================================================
# SIDEBAR — KEEP THESE THREE AREAS STABLE
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="side-logo">
        <div class="logo-mark">⚡</div>
        <div>
            <div class="logo-name">AI YouTube Research</div>
            <div class="logo-sub">AI-Powered YouTube Research</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------- DATA SOURCE --------
    st.markdown('<div class="sidebar-heading">🔐 Data Source</div>', unsafe_allow_html=True)

    data_source = st.radio(
        "Data source",
        ["My API Key", "Use my own API key"],
        key="data_source",
        label_visibility="collapsed",
    )

    own_api_key = ""
    if data_source == "Use my own API key":
        own_api_key = st.text_input(
            "Your YouTube API key",
            type="password",
            placeholder="Paste your API key",
            key="own_api_key",
            help="Used for the current app session.",
        )
        if own_api_key:
            st.markdown(
                '<div class="connection"><span class="connection-dot"></span>Your API key is ready</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="connection">🔑 Enter your own API key to continue.</div>',
                unsafe_allow_html=True,
            )
    else:
        if get_my_api_key():
            st.markdown(
                '<div class="connection"><span class="connection-dot"></span>My API Key connected</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="connection">🔴 My API Key not configured</div>',
                unsafe_allow_html=True,
            )

    # -------- TARGET REGION --------
    st.markdown('<div class="sidebar-heading">🌎 Target Region</div>', unsafe_allow_html=True)

    region = st.selectbox(
        "Region",
        list(REGIONS.keys()),
        key="region",
        index=0,
    )

    # -------- ANALYSIS MODE --------
    st.markdown('<div class="sidebar-heading">🔎 Analysis Mode</div>', unsafe_allow_html=True)

    mode = st.selectbox(
        "Choose tool",
        [
            "Dashboard",
            "Niche Finder",
            "Trend Finder",
            "Keyword Scanner",
            "Channel Analyzer",
            "Competitor Analyzer",
        ],
        key="analysis_mode",
    )

    # -------- COMMON TREND WINDOW --------
    st.markdown('<div class="sidebar-heading">⏱ Trend Window</div>', unsafe_allow_html=True)

    window = st.selectbox(
        "Trend window",
        ["1 Hour", "4 Hours", "24 Hours", "7 Days", "1 Month"],
        key="trend_window",
        index=2,
    )

    results_limit = st.slider(
        "Results",
        min_value=10,
        max_value=50,
        value=30,
        step=5,
        key="results_limit",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Developer: {DEVELOPER}")


# ============================================================
# TOPBAR
# ============================================================
st.markdown(
    f"""<div class="topbar">
        <div class="brand-row">
            <div class="logo-mark">⚡</div>
            <div>
                <div class="brand-title">{APP_NAME}</div>
                <div class="brand-desc">{APP_TAGLINE}</div>
            </div>
        </div>
        <div class="live-pill"><span class="live-dot"></span>Workspace ready</div>
    </div>""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""<div class="hero">
        <div class="hero-kicker">Creator intelligence workspace</div>
        <h1>Turn YouTube signals into decisions.</h1>
        <p>Discover rising topics, analyze video velocity, inspect channels and compare competitors across your selected market and time window.</p>
        <div class="hero-tags">
            <span class="tag">🌎 {region}</span>
            <span class="tag">⏱ {window}</span>
            <span class="tag">⚡ Velocity</span>
            <span class="tag">🚀 Breakout signals</span>
            <span class="tag">🔗 Direct YouTube links</span>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

# ============================================================
# DASHBOARD
# ============================================================
if mode == "Dashboard":
    df = st.session_state.get("last_df", pd.DataFrame())

    st.markdown(
        '<div class="section-head"><div><div class="section-title">Workspace overview</div><div class="section-desc">Your latest analysis snapshot.</div></div></div>',
        unsafe_allow_html=True,
    )
    show_kpis(df)

    st.markdown(
        '<div class="section-head"><div><div class="section-title">📈 Emerging topics</div><div class="section-desc">Frequent title terms from the current result set.</div></div></div>',
        unsafe_allow_html=True,
    )
    show_topics(df)

    if not df.empty:
        st.markdown(
            '<div class="section-head"><div><div class="section-title">🚀 Top opportunities</div><div class="section-desc">Velocity and engagement research signals.</div></div></div>',
            unsafe_allow_html=True,
        )
        show_videos(df, 6)

        st.markdown(
            '<div class="section-head"><div><div class="section-title">⚡ Velocity chart</div></div></div>',
            unsafe_allow_html=True,
        )
        chart = df[["title", "views_per_hour"]].copy()
        chart["title"] = chart["title"].str.slice(0, 32)
        chart = chart.sort_values("views_per_hour", ascending=False).head(10).set_index("title")
        st.bar_chart(chart, height=300)

# ============================================================
# NICHE FINDER
# ============================================================
elif mode == "Niche Finder":
    st.markdown(
        '<div class="tool-header"><div class="tool-title">🔎 Niche Finder</div><div class="tool-desc">Scan niches and immediately see the videos found inside each niche — with direct YouTube links.</div></div>',
        unsafe_allow_html=True,
    )

    niches = st.text_area(
        "Niches to scan — one per line",
        value="AI tools\nPersonal finance\nInvesting\nSide hustle\nGaming\nFitness",
        height=150,
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        scan = st.button("🚀 Scan Niches", type="primary", use_container_width=True)
    with c2:
        st.caption("Each niche gets its own video list + direct YouTube links.")

    if scan:
        api_key = selected_key(data_source, own_api_key)
        valid, message = validate_api_key(api_key)

        if not valid:
            st.error(message)
        else:
            niche_list = list(dict.fromkeys(
                [x.strip() for x in niches.splitlines() if x.strip()]
            ))[:6]

            rows = []
            video_groups = []
            progress = st.progress(0)

            for i, niche in enumerate(niche_list):
                with st.spinner(f"Scanning {niche}…"):
                    data, error = trend_finder(
                        niche,
                        api_key,
                        region,
                        window,
                        min(results_limit, 50),
                    )

                if error:
                    st.error(f"{niche}: {error}")
                elif data is not None and not data.empty:
                    group = data.copy()
                    group["niche_query"] = niche
                    # Keep the requested niche visible while preserving the automatically detected niche.
                    group["niche"] = niche
                    video_groups.append((niche, group))
                    rows.append({
                        "Niche": niche,
                        "Videos found": len(group),
                        "Total views": int(group["views"].sum()),
                        "Avg views/hour": float(group["views_per_hour"].mean()),
                        "Avg engagement": float(group["engagement"].mean()),
                        "Opportunity": float(group["opportunity"].mean()),
                    })

                progress.progress((i + 1) / max(len(niche_list), 1))

            if rows:
                result = pd.DataFrame(rows).sort_values(
                    "Avg views/hour",
                    ascending=False,
                )
                st.session_state.last_df = pd.concat(
                    [g for _, g in video_groups], ignore_index=True
                ) if video_groups else pd.DataFrame()

                st.markdown('<div class="section-title">📊 Niche comparison</div>', unsafe_allow_html=True)
                display = result.copy()
                display["Total views"] = display["Total views"].map(format_number)
                display["Avg views/hour"] = display["Avg views/hour"].map(format_number)
                display["Avg engagement"] = display["Avg engagement"].map(lambda x: f"{x:.1f}%")
                display["Opportunity"] = display["Opportunity"].map(lambda x: f"{x:.0f}/100")
                st.dataframe(display, use_container_width=True, hide_index=True)

                chart = result.set_index("Niche")[["Avg views/hour"]]
                st.bar_chart(chart, height=300)

                # IMPORTANT: render all videos directly on the dashboard.
                show_requested_niche_results(video_groups, min(results_limit, 50))
            else:
                st.warning("No videos were found for the selected niches in the current region/time window.")

# ============================================================
# TREND FINDER / TREND DISCOVERY
# ============================================================
elif mode == "Trend Finder":
    st.markdown(
        '<div class="tool-header"><div class="tool-title">🔥 Trend Discovery</div><div class="tool-desc">Select a region and time window to discover recent high-velocity YouTube videos — no keyword required.</div></div>',
        unsafe_allow_html=True,
    )

    st.info(
        f"Scanning **{region}** for videos published in the last **{window}**. "
        "Results are ranked using views, views/hour, engagement, recency and channel-relative performance."
    )

    if st.button("🔥 Find Trending Videos", type="primary", use_container_width=True):
        api_key = selected_key(data_source, own_api_key)
        valid, message = validate_api_key(api_key)

        if not valid:
            st.error(message)
        else:
            with st.spinner(f"Finding {region} trends from the last {window}…"):
                df, error = discover_trending(
                    api_key,
                    region,
                    window,
                    results_limit,
                )

            if error:
                st.error(error)
            else:
                st.session_state.last_df = df
                st.success(f"{len(df)} trending videos found.")
                show_kpis(df)

                if not df.empty:
                    # Trending niche/topic signals
                    st.markdown(
                        '<div class="section-head"><div><div class="section-title">🏷️ Trending niches / topics</div><div class="section-desc">Detected from the titles and descriptions in the result set.</div></div></div>',
                        unsafe_allow_html=True,
                    )
                    show_topics(df)

                    if "niche" in df.columns:
                        niche_summary = (
                            df.groupby("niche", dropna=False)
                            .agg(Videos=("title", "count"), Total_Views=("views", "sum"), Avg_Views_Hour=("views_per_hour", "mean"))
                            .sort_values(["Videos", "Avg_Views_Hour"], ascending=False)
                            .reset_index()
                            .head(10)
                        )
                        st.markdown('<div class="section-head"><div><div class="section-title">🏷️ Niche breakdown</div><div class="section-desc">Detected niche for each discovered video.</div></div></div>', unsafe_allow_html=True)
                        ns = niche_summary.copy()
                        ns["Total_Views"] = ns["Total_Views"].map(format_number)
                        ns["Avg_Views_Hour"] = ns["Avg_Views_Hour"].map(format_number)
                        ns = ns.rename(columns={"niche":"Niche", "Videos":"Videos", "Total_Views":"Total views", "Avg_Views_Hour":"Avg views/hour"})
                        st.dataframe(ns, use_container_width=True, hide_index=True)

                    # Show the actual videos under each detected niche, not only the summary table.
                    show_videos_by_niche(df, min(results_limit, 10), "Trending videos by niche")

                    st.markdown(
                        '<div class="section-head"><div><div class="section-title">🔥 All trending videos</div><div class="section-desc">Complete result set sorted by the research trend score. Every card has a direct YouTube link.</div></div></div>',
                        unsafe_allow_html=True,
                    )
                    show_videos(df, results_limit)


# ============================================================
# KEYWORD SCANNER
# ============================================================
elif mode == "Keyword Scanner":
    st.markdown(
        '<div class="tool-header"><div class="tool-title">🔑 Keyword Scanner</div><div class="tool-desc">Inspect visible YouTube results around a keyword and identify high-velocity videos.</div></div>',
        unsafe_allow_html=True,
    )

    keyword = st.text_input(
        "Keyword",
        value="personal finance",
    )

    if st.button("🔎 Scan Keyword", type="primary"):
        api_key = selected_key(data_source, own_api_key)
        valid, message = validate_api_key(api_key)

        if not valid:
            st.error(message)
        else:
            with st.spinner("Scanning keyword…"):
                df, error = keyword_scanner(
                    keyword,
                    api_key,
                    region,
                    results_limit,
                )

            if error:
                st.error(error)
            else:
                st.session_state.last_df = df
                show_kpis(df)
                show_topics(df)

# ============================================================
# CHANNEL ANALYZER
# ============================================================
elif mode == "Channel Analyzer":
    st.markdown(
        '<div class="tool-header"><div class="tool-title">👤 Channel Analyzer</div><div class="tool-desc">Inspect a channel&#39;s returned videos and compare velocity, engagement and opportunity signals.</div></div>',
        unsafe_allow_html=True,
    )

    channel = st.text_input(
        "Channel name",
        placeholder="Enter channel name",
    )

    if st.button("👤 Analyze Channel", type="primary"):
        if not channel.strip():
            st.warning("Enter a channel name.")
        else:
            api_key = selected_key(data_source, own_api_key)
            valid, message = validate_api_key(api_key)

            if not valid:
                st.error(message)
            else:
                with st.spinner("Analyzing channel…"):
                    df, error = analyze_channel(
                        channel,
                        api_key,
                        results_limit,
                        window,
                    )

                if error:
                    st.error(error)
                else:
                    st.session_state.last_df = df
                    show_kpis(df)
                    show_videos(df, min(10, results_limit))

# ============================================================
# COMPETITOR ANALYZER
# ============================================================
elif mode == "Competitor Analyzer":
    st.markdown(
        '<div class="tool-header"><div class="tool-title">⚔️ Competitor Analyzer</div><div class="tool-desc">Compare up to 5 competitor channels using the same performance signals.</div></div>',
        unsafe_allow_html=True,
    )

    competitor_text = st.text_area(
        "Competitor channels — one per line",
        placeholder="Channel A\nChannel B\nChannel C",
        height=140,
    )

    videos_per_channel = st.slider(
        "Videos per competitor",
        5, 20, 10, 5,
    )

    if st.button("⚔️ Compare Competitors", type="primary"):
        names = [
            x.strip()
            for x in competitor_text.splitlines()
            if x.strip()
        ][:5]

        if not names:
            st.warning("Enter at least one competitor channel.")
        else:
            api_key = selected_key(data_source, own_api_key)
            valid, message = validate_api_key(api_key)

            if not valid:
                st.error(message)
            else:
                with st.spinner("Comparing competitor channels…"):
                    videos, summary, error = analyze_competitors(
                        names,
                        api_key,
                        videos_per_channel,
                        window,
                    )

                if error:
                    st.error(error)
                else:
                    st.session_state.last_df = videos

                    st.markdown('<div class="section-title">📊 Comparison</div>', unsafe_allow_html=True)

                    a, b, c, d = st.columns(4)
                    a.metric("Channels", len(summary))
                    b.metric("Videos", len(videos))
                    c.metric(
                        "Highest avg views/hr",
                        format_number(summary["average_views_per_hour"].max()),
                    )
                    d.metric(
                        "Highest avg engagement",
                        f'{summary["average_engagement"].max():.1f}%',
                    )

                    chart = summary.set_index("competitor")[["average_views_per_hour"]]
                    st.bar_chart(chart, height=300)

                    display = summary.copy()
                    display["total_views"] = display["total_views"].map(format_number)
                    display["average_views"] = display["average_views"].map(format_number)
                    display["average_views_per_hour"] = display["average_views_per_hour"].map(format_number)
                    display["average_engagement"] = display["average_engagement"].map(lambda x: f"{x:.1f}%")
                    display["average_opportunity"] = display["average_opportunity"].map(lambda x: f"{x:.0f}/99")

                    st.dataframe(
                        display,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.markdown('<div class="section-title">🎬 Competitor videos</div>', unsafe_allow_html=True)
                    show_videos(videos, 15)

# ============================================================
# EXPORT / FOOTER
# ============================================================
last_df = st.session_state.get("last_df", pd.DataFrame())

if not last_df.empty:
    st.markdown('<div class="section-head"><div><div class="section-title">📥 Export</div><div class="section-desc">Download the current result set.</div></div></div>', unsafe_allow_html=True)
    export_buttons(last_df)

st.markdown(
    f"""<div class="footer">
        <span>{APP_NAME} · {APP_TAGLINE}</span>
        <span>Developed by <b>{DEVELOPER}</b></span>
    </div>""",
    unsafe_allow_html=True,
)
