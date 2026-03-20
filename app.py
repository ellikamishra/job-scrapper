"""
Job Scraper — Streamlit UI
Run with: streamlit run app.py
"""
import csv
import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import streamlit as st
import pandas as pd

from companies_db import (
    get_companies_for_location,
    LOCATION_ALIASES,
    COMPANIES_DB,
)
from config import EXPERIENCE_LEVELS
from excel_io import read_companies
from scraper import scrape_company_jobs, discover_companies_from_web

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
VALID_CATEGORIES = ["big_tech", "startup", "quant", "trading", "fintech"]

CATEGORY_LABELS = {
    "big_tech": "🏢 Big Tech",
    "startup":  "🚀 Startups",
    "quant":    "📈 Quant / HFT",
    "trading":  "💹 Trading Firms",
    "fintech":  "💳 Fintech",
}

EXPERIENCE_LABELS = {
    "intern": "🎓 Intern",
    "entry":  "🌱 Entry Level",
    "mid":    "⚡ Mid Level",
    "senior": "🔥 Senior",
    "staff":  "🏆 Staff / Principal",
    "any":    "✨ Any",
}

COMMON_SKILLS = sorted([
    # Languages
    "Python", "C++", "C", "Java", "Go", "Rust", "TypeScript", "JavaScript",
    "Scala", "Kotlin", "Swift", "R", "MATLAB", "Haskell", "OCaml",
    # Systems / Infrastructure
    "Distributed Systems", "System Design", "Low Latency", "High Frequency Trading",
    "Kubernetes", "Docker", "Terraform", "AWS", "GCP", "Azure",
    "Linux", "gRPC", "Kafka", "Redis", "Spark", "Flink",
    # Data / ML / AI
    "Machine Learning", "Deep Learning", "LLM", "NLP", "Computer Vision",
    "PyTorch", "TensorFlow", "JAX", "Reinforcement Learning",
    "Data Engineering", "SQL", "dbt", "Airflow", "Pandas", "NumPy",
    # Quant / Finance
    "Quantitative Research", "Algorithmic Trading", "Market Making",
    "Statistical Modeling", "Time Series", "Options Pricing",
    "Risk Management", "Fixed Income", "Derivatives",
    # Web / Product
    "React", "Next.js", "Node.js", "GraphQL", "REST API",
    "PostgreSQL", "MongoDB", "Elasticsearch",
    # Security
    "Security", "Cryptography", "Penetration Testing",
])

COMMON_JOB_LOCATIONS = sorted([
    "Remote", "New York", "San Francisco", "Seattle", "Austin",
    "Boston", "Chicago", "Los Angeles", "London", "Singapore",
    "Bangalore", "Toronto", "Berlin", "Amsterdam", "Hybrid",
])

CANONICAL_LOCATIONS = sorted(
    [loc.title() for loc in LOCATION_ALIASES.keys()]
)

# Derive unique company location hints from DB for autocomplete
ALL_DB_LOCATIONS = sorted({
    loc.title()
    for _, _, locs, _ in COMPANIES_DB
    for loc in locs
})

CSV_COLUMNS = ["Company Name", "Job Title", "Location", "Experience", "Skills Matched", "Link"]


# ── Helpers ───────────────────────────────────────────────────────────────────
class _StdoutCapture:
    """Redirect stdout to an in-memory list for live progress display."""
    def __init__(self):
        self.lines: list[str] = []
        self._orig = sys.stdout

    def write(self, text: str):
        self._orig.write(text)
        if text.strip():
            self.lines.append(text.rstrip())

    def flush(self):
        self._orig.flush()

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, *_):
        sys.stdout = self._orig


def _jobs_to_df(jobs: list[dict]) -> pd.DataFrame:
    rows = [
        {
            "Company":         j.get("company", ""),
            "Job Title":       j.get("title", ""),
            "Location":        j.get("location", "N/A"),
            "Experience":      j.get("experience", "Not specified"),
            "Skills Matched":  j.get("skills_matched", ""),
            "Link":            j.get("link", ""),
        }
        for j in jobs
    ]
    return pd.DataFrame(rows, columns=["Company", "Job Title", "Location",
                                       "Experience", "Skills Matched", "Link"])


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def _run_scraper(companies, skills, job_locations, exp_levels, delay, log_lines):
    def _scrape_one(company):
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        try:
            return scrape_company_jobs(
                company, skills, job_locations, exp_levels, session
            )
        except Exception as e:
            log_lines.append(f"  [!] Error: {company['name']}: {e}")
            return []

    all_jobs: list[dict] = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_scrape_one, c): c for c in companies}
        for future in as_completed(futures):
            all_jobs.extend(future.result())
    return all_jobs


# ── Session state init ────────────────────────────────────────────────────────
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if "log_lines" not in st.session_state:
    st.session_state.log_lines = []
if "custom_skills" not in st.session_state:
    st.session_state.custom_skills = []
if "custom_job_locs" not in st.session_state:
    st.session_state.custom_job_locs = []


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Job Scraper")
    st.caption("Scrape jobs from 150+ companies by location, skills & experience")
    st.divider()

    # ── Source mode ───────────────────────────────────────────────────────────
    source_mode = st.radio(
        "Company source",
        ["Auto-generate from location", "Discover from web", "Upload Excel file"],
        index=0,
        help=(
            "**Auto-generate**: uses our curated 150+ company database. "
            "**Discover from web**: dynamically finds companies hiring for your skills via LinkedIn & Google. "
            "**Upload Excel**: provide your own list."
        ),
    )

    st.divider()

    uploaded_file = None
    scrape_location = ""
    selected_categories = list(VALID_CATEGORIES)

    if source_mode == "Auto-generate from location":
        scrape_location = st.selectbox(
            "Location",
            options=["any"] + ALL_DB_LOCATIONS,
            index=0,
            help="Filter companies by their office location. Choose 'any' to include all.",
        )
        selected_categories = st.multiselect(
            "Company categories",
            options=VALID_CATEGORIES,
            default=VALID_CATEGORIES,
            format_func=lambda c: CATEGORY_LABELS[c],
            help="Select which company types to include.",
        )

    elif source_mode == "Discover from web":
        st.info(
            "Companies will be discovered dynamically from LinkedIn & Google "
            "based on your **skills** and **job locations** below. "
            "No pre-existing list needed!"
        )

    else:
        uploaded_file = st.file_uploader(
            "Upload Excel (.xlsx)",
            type=["xlsx"],
            help="Must have columns: Company Name, Domain, Career URL (optional)",
        )

    st.divider()

    # ── Skills ────────────────────────────────────────────────────────────────
    st.subheader("Skills filter")
    selected_skills = st.multiselect(
        "Common skills",
        options=COMMON_SKILLS,
        default=[],
        help="Select skills jobs must mention. Leave empty to match any.",
    )
    custom_skill_input = st.text_input(
        "Add custom skill",
        placeholder="e.g. CUDA, FIX Protocol, Erlang",
        key="custom_skill_input",
    )
    if st.button("➕ Add skill", use_container_width=True):
        skill = custom_skill_input.strip()
        if skill and skill not in st.session_state.custom_skills:
            st.session_state.custom_skills.append(skill)

    if st.session_state.custom_skills:
        st.caption("Custom skills added:")
        cols = st.columns([4, 1])
        for i, sk in enumerate(st.session_state.custom_skills):
            cols[0].markdown(f"• `{sk}`")
        if st.button("🗑 Clear custom skills", use_container_width=True):
            st.session_state.custom_skills = []

    all_skills = selected_skills + st.session_state.custom_skills

    st.divider()

    # ── Job location filter ───────────────────────────────────────────────────
    st.subheader("Job location filter")
    st.caption("Filter job *postings* by location (separate from company HQ)")
    selected_job_locs = st.multiselect(
        "Locations",
        options=COMMON_JOB_LOCATIONS,
        default=[],
        help="Only include postings mentioning these locations. Empty = any.",
    )
    custom_loc_input = st.text_input(
        "Add custom location",
        placeholder="e.g. Hyderabad, Dublin, Zurich",
        key="custom_loc_input",
    )
    if st.button("➕ Add location", use_container_width=True):
        loc = custom_loc_input.strip()
        if loc and loc not in st.session_state.custom_job_locs:
            st.session_state.custom_job_locs.append(loc)

    if st.session_state.custom_job_locs:
        st.caption("Custom locations added:")
        for loc in st.session_state.custom_job_locs:
            st.markdown(f"• `{loc}`")
        if st.button("🗑 Clear custom locations", use_container_width=True):
            st.session_state.custom_job_locs = []

    all_job_locs = selected_job_locs + st.session_state.custom_job_locs

    st.divider()

    # ── Experience ────────────────────────────────────────────────────────────
    st.subheader("Experience level")
    selected_exp = st.multiselect(
        "Levels",
        options=list(EXPERIENCE_LEVELS.keys()),
        default=[],
        format_func=lambda e: EXPERIENCE_LABELS.get(e, e),
        help="Select one or more levels. Empty = any (incl. jobs with no experience info).",
    )

    st.divider()

    # ── Company limit ─────────────────────────────────────────────────────────
    st.subheader("Company limit")
    company_limit = st.number_input(
        "Max companies to scrape",
        min_value=1,
        max_value=500,
        value=50,
        step=10,
        help="How many companies to scrape in one run. Increase for broader results.",
    )

    st.divider()

    # ── Advanced ──────────────────────────────────────────────────────────────
    with st.expander("⚙️ Advanced settings"):
        delay = st.slider(
            "Delay between companies (s)",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.5,
        )

    st.divider()
    run_btn = st.button(
        "🚀 Start Scraping",
        use_container_width=True,
        type="primary",
    )


# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🔍 Job Scraper")

# Active filter summary
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skills", len(all_skills) if all_skills else "Any")
    c2.metric("Job Locations", len(all_job_locs) if all_job_locs else "Any")
    c3.metric("Experience", len(selected_exp) if selected_exp else "Any")
    if source_mode == "Auto-generate from location":
        c4.metric("Companies (DB)", len(get_companies_for_location(
            [scrape_location],
            selected_categories if selected_categories else None,
        )))
    elif source_mode == "Discover from web":
        c4.metric("Source", "Web discovery")
    else:
        c4.metric("Source", "Excel upload")

st.divider()

# ── Run ───────────────────────────────────────────────────────────────────────
if run_btn:
    # Validate inputs
    if source_mode == "Upload Excel file" and uploaded_file is None:
        st.error("Please upload an Excel file.")
        st.stop()
    if source_mode == "Discover from web" and not all_skills:
        st.error("Please add at least one skill so we know what jobs to discover.")
        st.stop()

    # Load companies
    if source_mode == "Auto-generate from location":
        cats = selected_categories if selected_categories else None
        companies = get_companies_for_location([scrape_location], cats)
        if not companies:
            st.warning("No companies found for that location/category combination.")
            st.stop()

    elif source_mode == "Discover from web":
        discover_placeholder = st.empty()
        discover_placeholder.info("Discovering companies from LinkedIn & Google…")
        discover_log = []

        def _discover_progress(msg):
            discover_log.append(msg)
            discover_placeholder.code("\n".join(discover_log[-15:]), language=None)

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        discovered = discover_companies_from_web(
            skills=all_skills,
            locations=all_job_locs,
            max_companies=int(company_limit),
            session=session,
            progress_callback=_discover_progress,
        )
        n_web = len(discovered)

        # Merge with DB companies so users get discovered + known companies
        db_companies = get_companies_for_location(
            all_job_locs if all_job_locs else ["any"], None
        )
        seen_domains = {c["domain"] for c in discovered}
        n_db_added = 0
        for dbc in db_companies:
            if dbc["domain"] not in seen_domains:
                discovered.append(dbc)
                seen_domains.add(dbc["domain"])
                n_db_added += 1

        companies = discovered
        if not companies:
            discover_placeholder.empty()
            st.warning("Could not discover any companies. Try broader skills or locations.")
            st.stop()
        discover_placeholder.success(
            f"Found **{len(companies)}** companies "
            f"({n_web} discovered from web + {n_db_added} from curated DB)"
        )

    else:
        try:
            import tempfile, os
            suffix = ".xlsx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            companies = read_companies(tmp_path)
            os.unlink(tmp_path)
        except Exception as e:
            st.error(f"Failed to read Excel file: {e}")
            st.stop()
        if not companies:
            st.warning("No companies found in the uploaded file.")
            st.stop()

    # Apply limit
    companies = companies[:int(company_limit)]

    exp_levels = selected_exp if selected_exp else []

    st.info(
        f"Scraping **{len(companies)}** companies | "
        f"Skills: **{', '.join(all_skills) if all_skills else 'Any'}** | "
        f"Job locations: **{', '.join(all_job_locs) if all_job_locs else 'Any'}** | "
        f"Experience: **{', '.join(selected_exp) if selected_exp else 'Any'}**"
    )

    # Progress containers
    progress_bar = st.progress(0, text="Starting…")
    log_expander = st.expander("📋 Live scrape log", expanded=True)
    log_placeholder = log_expander.empty()

    all_jobs: list[dict] = []
    log_lines: list[str] = []
    completed_count = 0

    def _scrape_one_company(company):
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        cap = _StdoutCapture()
        jobs = []
        try:
            with cap:
                jobs = scrape_company_jobs(
                    company, all_skills, all_job_locs, exp_levels, session
                )
        except Exception as e:
            cap.lines.append(f"  [!] Error: {e}")
        return company, jobs, cap.lines

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_scrape_one_company, c): c for c in companies}
        for future in as_completed(futures):
            company, jobs, lines = future.result()
            all_jobs.extend(jobs)
            log_lines.extend(lines)
            completed_count += 1
            pct = int((completed_count / len(companies)) * 100)
            progress_bar.progress(pct, text=f"[{completed_count}/{len(companies)}] {company['name']} done")
            log_placeholder.code("\n".join(log_lines[-80:]), language=None)

    progress_bar.progress(100, text="Done!")
    st.session_state.results_df = _jobs_to_df(all_jobs)
    st.session_state.log_lines = log_lines
    st.success(f"✅ Scraping complete — **{len(all_jobs)}** jobs found across {len(companies)} companies")

# ── Results ───────────────────────────────────────────────────────────────────
if not st.session_state.results_df.empty:
    df = st.session_state.results_df

    st.subheader(f"📊 Results — {len(df)} jobs")

    # ── Filter bar ────────────────────────────────────────────────────────────
    with st.expander("🔎 Filter / search results", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        company_filter = fc1.multiselect(
            "Company",
            options=sorted(df["Company"].unique()),
            default=[],
        )
        exp_filter = fc2.multiselect(
            "Experience",
            options=sorted(df["Experience"].unique()),
            default=[],
        )
        loc_filter = fc3.multiselect(
            "Location",
            options=sorted(df["Location"].unique()),
            default=[],
        )
        title_search = st.text_input("Search in Job Title", placeholder="e.g. engineer, quant, analyst")

    # Apply filters
    filtered = df.copy()
    if company_filter:
        filtered = filtered[filtered["Company"].isin(company_filter)]
    if exp_filter:
        filtered = filtered[filtered["Experience"].isin(exp_filter)]
    if loc_filter:
        filtered = filtered[filtered["Location"].isin(loc_filter)]
    if title_search:
        filtered = filtered[
            filtered["Job Title"].str.contains(title_search, case=False, na=False)
        ]

    st.caption(f"Showing {len(filtered)} of {len(df)} jobs")

    # ── Table ─────────────────────────────────────────────────────────────────
    st.dataframe(
        filtered,
        use_container_width=True,
        height=520,
        column_config={
            "Company":        st.column_config.TextColumn("Company", width="medium"),
            "Job Title":      st.column_config.TextColumn("Job Title", width="large"),
            "Location":       st.column_config.TextColumn("Location", width="medium"),
            "Experience":     st.column_config.TextColumn("Experience", width="medium"),
            "Skills Matched": st.column_config.TextColumn("Skills Matched", width="medium"),
            "Link":           st.column_config.LinkColumn("Apply Link", width="medium", display_text="Apply →"),
        },
        hide_index=True,
    )

    # ── Download ──────────────────────────────────────────────────────────────
    st.divider()
    dl_col1, dl_col2, _ = st.columns([2, 2, 4])

    csv_bytes = _df_to_csv_bytes(filtered)
    dl_col1.download_button(
        label="⬇️ Download filtered CSV",
        data=csv_bytes,
        file_name=f"jobs_{time.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary",
    )
    all_csv_bytes = _df_to_csv_bytes(df)
    dl_col2.download_button(
        label="⬇️ Download all results CSV",
        data=all_csv_bytes,
        file_name=f"jobs_all_{time.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

elif not run_btn:
    st.markdown(
        """
        ### How to use

        1. **Choose a company source** in the sidebar:
           - **Auto-generate**: picks from our curated 150+ company database by location.
           - **Discover from web**: dynamically finds companies hiring for your skills via LinkedIn & Google — no pre-existing list needed!
           - **Upload Excel**: provide your own company list.
        2. **Pick categories** (Big Tech, Startups, Quant firms, Trading, Fintech) — auto-generate mode only.
        3. **Add skills** from the dropdown or type custom ones. Jobs matching **any** skill are included.
        4. **Set job location filter** to narrow postings by city/remote.
        5. **Select experience levels** — intern through staff; leave empty for all.
        6. **Set company limit** — default is 50, increase up to 500 for broader results.
        7. Hit **🚀 Start Scraping** and watch results populate in real time.
        8. **Filter the results table** by company, location, or title, then download CSV.
        """
    )
