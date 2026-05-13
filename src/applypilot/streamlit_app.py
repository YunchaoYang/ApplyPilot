"""Interactive job / application tracker (Streamlit).

Install: ``pip install 'applypilot[ui]'``
Run: ``applypilot ui``   or   ``streamlit run …/applypilot/streamlit_app.py``
"""

from __future__ import annotations

import pandas as pd
import streamlit as st  # type: ignore[import-untyped]

from applypilot.config import DB_PATH, ensure_dirs, load_env
from applypilot.database import (
    get_application_tracker_summary,
    get_connection,
    init_db,
    list_jobs_for_tracker,
)
from applypilot.view import tracker_pipeline_key, tracker_pipeline_label


def _bootstrap() -> None:
    load_env()
    ensure_dirs()
    init_db()


_bootstrap()

st.set_page_config(
    page_title="ApplyPilot — Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=15)
def _summary() -> dict:
    return get_application_tracker_summary(get_connection())


@st.cache_data(ttl=15)
def _jobs(limit: int, min_score: int | None) -> pd.DataFrame:
    conn = get_connection()
    rows = list_jobs_for_tracker(conn, limit=limit, min_score=min_score)
    if not rows:
        return pd.DataFrame()
    for r in rows:
        k = tracker_pipeline_key(r)
        r["pipeline"] = tracker_pipeline_label(k)
        r["pipeline_key"] = k
    df = pd.DataFrame(rows)
    cols = [
        "pipeline",
        "title",
        "site",
        "location",
        "fit_score",
        "apply_status",
        "applied_at",
        "apply_error",
        "url",
        "application_url",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]


st.title("ApplyPilot — Application tracker")
st.caption(f"Database: `{DB_PATH}`")


with st.sidebar:
    st.header("Filters")
    if st.button("Refresh data", type="primary"):
        _summary.clear()
        _jobs.clear()
        st.rerun()
    row_limit = st.slider("Max rows", min_value=50, max_value=5000, value=1000, step=50)
    min_score = st.number_input(
        "Min fit score (optional)",
        min_value=0,
        max_value=10,
        value=0,
        help="Use 0 to include jobs with no score. Set ≥1 to filter.",
    )
    min_score_arg = None if min_score == 0 else int(min_score)

sm = _summary()
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("In DB", sm["total"])
c2.metric("Applied", sm["applied"])
c3.metric("Failed", sm["failed"])
c4.metric("Applying", sm["applying"])
c5.metric("Ready", sm["ready_to_apply"])
c6.metric("Scored, no tailor", sm["scored_no_tailor"])

df = _jobs(row_limit, min_score_arg)
if df.empty:
    st.info("No jobs match the current filters.")
    st.stop()

stages = sorted(df["pipeline"].unique().tolist())
pick = st.multiselect("Pipeline stage", options=stages, default=stages)
search = st.text_input("Search (title, site, location, error)", "")

view = df[df["pipeline"].isin(pick)] if pick else df
if search.strip():
    q = search.strip().lower()
    sub = view.fillna("")
    mask = (
        sub["title"].str.lower().str.contains(q, regex=False)
        | sub["site"].str.lower().str.contains(q, regex=False)
        | sub["location"].str.lower().str.contains(q, regex=False)
        | sub["apply_error"].str.lower().str.contains(q, regex=False)
        | sub["pipeline"].str.lower().str.contains(q, regex=False)
    )
    view = view[mask]

if view.empty and not df.empty:
    st.warning("No rows match the stage / search filters.")
    st.stop()

st.write(f"**Showing** {len(view)} **of** {len(df)} loaded rows")

column_config = {
    "url": st.column_config.LinkColumn("Listing", display_text="open"),
    "application_url": st.column_config.LinkColumn("Apply URL", display_text="apply"),
    "apply_error": st.column_config.TextColumn("Error", width="large"),
    "title": st.column_config.TextColumn("Title", width="medium"),
}

st.dataframe(
    view,
    column_config=column_config,
    hide_index=True,
    use_container_width=True,
    height=min(720, 60 + len(view) * 35),
)
