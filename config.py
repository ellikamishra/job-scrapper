"""
Default configuration for the job scraper.
Users can override these via CLI arguments.
"""

# Common career page URL patterns to try for a company
CAREER_URL_PATTERNS = [
    "https://www.{domain}/careers",
    "https://www.{domain}/jobs",
    "https://careers.{domain}",
    "https://jobs.{domain}",
    "https://www.{domain}/en/careers",
    "https://www.{domain}/about/careers",
    "https://www.{domain}/company/careers",
    "https://www.{domain}/career",
    "https://www.{domain}/join-us",
    "https://www.{domain}/work-with-us",
]

# Greenhouse / Lever / Workday board patterns
ATS_PATTERNS = [
    "https://boards.greenhouse.io/{slug}",
    "https://jobs.lever.co/{slug}",
    "https://jobs.smartrecruiters.com/{slug}",
    "https://{slug}.workday.com",
]

# Request settings
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Keywords that indicate a link is a job posting
JOB_LINK_KEYWORDS = [
    "job", "position", "opening", "career", "role", "apply",
    "vacancy", "opportunity", "posting", "requisition",
]

# Keywords in URLs that indicate career/job pages
CAREER_PATH_KEYWORDS = [
    "career", "job", "position", "opening", "work",
    "join", "hiring", "talent", "recruit", "apply",
    "opportunities", "vacancies",
]

# Experience level mappings
# "keywords" are plain-text phrases; year matching is done with regex in scraper.py
EXPERIENCE_LEVELS = {
    "intern": {
        "keywords": ["intern", "internship", "trainee", "co-op", "coop", "student"],
        "year_range": (0, 0),
    },
    "entry": {
        "keywords": [
            "entry level", "entry-level", "junior", "associate", "new grad",
            "new graduate", "graduate", "fresh", "jr.", "jr ", "no experience",
            "no prior experience", "recent graduate", "university graduate",
            "college graduate",
        ],
        "year_range": (0, 2),
    },
    "mid": {
        "keywords": [
            "mid level", "mid-level", "intermediate", "mid-senior",
        ],
        "year_range": (2, 4),   # 2–4 years
    },
    "senior": {
        "keywords": [
            "senior", "sr.", "sr ", "lead", "principal",
            "experienced", "seasoned",
        ],
        "year_range": (4, 8),   # 4–8 years
    },
    "staff": {
        "keywords": [
            "staff", "distinguished", "fellow", "architect",
            "director", "vp of engineering", "engineering manager",
        ],
        "year_range": (8, 99),  # 8+ years
    },
    "any": {
        "keywords": [],
        "year_range": (0, 99),
    },
}

# Known ATS slug overrides for popular companies
KNOWN_ATS_SLUGS = {
    # Greenhouse
    "stripe.com":         {"platform": "greenhouse", "slug": "stripe"},
    "cloudflare.com":     {"platform": "greenhouse", "slug": "cloudflare"},
    "datadog.com":        {"platform": "greenhouse", "slug": "datadog"},
    "figma.com":          {"platform": "greenhouse", "slug": "figma"},
    "discord.com":        {"platform": "greenhouse", "slug": "discord"},
    "notion.so":          {"platform": "greenhouse", "slug": "notion"},
    "plaid.com":          {"platform": "greenhouse", "slug": "plaid"},
    "mongodb.com":        {"platform": "greenhouse", "slug": "mongodb"},
    "reddit.com":         {"platform": "greenhouse", "slug": "reddit"},
    "instacart.com":      {"platform": "greenhouse", "slug": "instacart"},
    "coinbase.com":       {"platform": "greenhouse", "slug": "coinbase"},
    "ramp.com":           {"platform": "greenhouse", "slug": "ramp"},
    "airtable.com":       {"platform": "greenhouse", "slug": "airtable"},
    "databricks.com":     {"platform": "greenhouse", "slug": "databricks"},
    "rivian.com":         {"platform": "greenhouse", "slug": "rivian"},
    "pinterest.com":      {"platform": "greenhouse", "slug": "pinterestcareers"},
    "brex.com":           {"platform": "greenhouse", "slug": "brex"},
    "canva.com":          {"platform": "greenhouse", "slug": "canva"},
    "scale.com":          {"platform": "greenhouse", "slug": "scaleai"},
    "retool.com":         {"platform": "greenhouse", "slug": "retool"},
    "rippling.com":       {"platform": "greenhouse", "slug": "rippling"},
    "lattice.com":        {"platform": "greenhouse", "slug": "lattice"},
    "gusto.com":          {"platform": "greenhouse", "slug": "gusto"},
    "deel.com":           {"platform": "greenhouse", "slug": "deel"},
    "grammarly.com":      {"platform": "greenhouse", "slug": "grammarly"},
    "duolingo.com":       {"platform": "greenhouse", "slug": "duolingo"},
    "coursera.org":       {"platform": "greenhouse", "slug": "coursera"},
    "sentry.io":          {"platform": "greenhouse", "slug": "sentry"},
    "snyk.io":            {"platform": "greenhouse", "slug": "snyk"},
    "wiz.io":             {"platform": "greenhouse", "slug": "wiz"},
    "asana.com":          {"platform": "greenhouse", "slug": "asana"},
    "amplitude.com":      {"platform": "greenhouse", "slug": "amplitude"},
    "cockroachlabs.com":  {"platform": "greenhouse", "slug": "cockroachdb"},
    "temporal.io":        {"platform": "greenhouse", "slug": "temporal"},
    "pinecone.io":        {"platform": "greenhouse", "slug": "pinecone"},
    "loom.com":           {"platform": "greenhouse", "slug": "loom"},
    "vercel.com":         {"platform": "greenhouse", "slug": "vercel"},
    "wandb.ai":           {"platform": "greenhouse", "slug": "wandb"},
    # Lever
    "netflix.com":        {"platform": "lever", "slug": "netflix"},
    "spotify.com":        {"platform": "lever", "slug": "spotify"},
    "openai.com":         {"platform": "lever", "slug": "openai"},
    "anthropic.com":      {"platform": "lever", "slug": "anthropic"},
    "doordash.com":       {"platform": "lever", "slug": "doordash"},
    "chime.com":          {"platform": "lever", "slug": "chime"},
    "robinhood.com":      {"platform": "lever", "slug": "robinhood"},
    "affirm.com":         {"platform": "lever", "slug": "affirm"},
    "sofi.com":           {"platform": "lever", "slug": "sofi"},
    "miro.com":           {"platform": "lever", "slug": "miro"},
    "linear.app":         {"platform": "lever", "slug": "linear"},
    # Ashby
    "cursor.sh":          {"platform": "ashby", "slug": "cursor"},
    "perplexity.ai":      {"platform": "ashby", "slug": "perplexityai"},
    "together.ai":        {"platform": "ashby", "slug": "together"},
    "neon.tech":          {"platform": "ashby", "slug": "neon"},
    "motherduck.com":     {"platform": "ashby", "slug": "motherduck"},
    "anyscale.com":       {"platform": "ashby", "slug": "anyscale"},
    "replit.com":         {"platform": "ashby", "slug": "replit"},
}
