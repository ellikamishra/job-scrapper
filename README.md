# Job Scrapper

A multi-strategy job scraping tool with a Streamlit web UI that finds engineering job postings across the web.

## Features

- **Multi-source scraping** — Searches Greenhouse, Lever, Ashby APIs, LinkedIn, Indeed, Simplify, career pages, and Google
- **Smart filtering** — Filter by skills, location, experience level (entry/mid/senior/staff)
- **Technical roles only** — Automatically filters out non-engineering roles (HR, marketing, recruiting, etc.)
- **Dynamic company discovery** — Discovers companies hiring from the web instead of relying on a static list
- **150+ built-in companies** — Curated database across big tech, startups, quant, trading, and fintech categories
- **Parallel scraping** — Scrapes up to 5 companies concurrently for faster results
- **Streamlit UI** — Interactive web interface with live progress, filterable results table, and CSV export

## Quick Start

### Prerequisites

- Python 3.8+

### Installation

```bash
git clone https://github.com/<your-username>/job-scrapper.git
cd job-scrapper
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Web UI

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### Run from CLI

```bash
# Scrape big tech companies in New York for Python/C++ roles
python main.py --scrape-location "New York" --categories big_tech --skills Python C++

# Discover companies from the web hiring for Go + Kubernetes
python main.py --scrape-location remote --categories startup --skills Go Kubernetes

# Use a custom company list from Excel
python main.py --input companies.xlsx --skills "System Design" --experience senior mid
```

## How It Works

The scraper uses an 8-strategy cascade for each company:

1. **Known ATS** — Checks if the company uses a known Greenhouse/Lever/Ashby slug
2. **Generic ATS APIs** — Tries Greenhouse, Lever, and Ashby JSON APIs
3. **LinkedIn** — Searches LinkedIn's public job listings
4. **Career page HTML** — Scrapes the company's career page for job links
5. **Indeed** — Searches Indeed for company job postings
6. **Simplify** — Checks Simplify.jobs API
7. **Google fallback** — Searches Google for job postings

Results are deduplicated, filtered by your criteria, and exported to CSV.

## Configuration

### Experience Levels

| Level  | Years | Keywords                              |
|--------|-------|---------------------------------------|
| Entry  | 0-2   | entry, junior, new grad, associate    |
| Mid    | 2-4   | mid, intermediate                     |
| Senior | 4-8   | senior, lead, principal               |
| Staff  | 8+    | staff, distinguished, fellow          |

### Source Modes (UI)

- **Auto-generate from location** — Uses the built-in company database filtered by location
- **Discover from web** — Dynamically finds companies hiring for your skills from LinkedIn and Google
- **Upload Excel file** — Provide your own company list

## Project Structure

```
job-scrapper/
  app.py           — Streamlit web UI
  main.py          — CLI entry point
  scraper.py       — Multi-strategy job scraper
  config.py        — URL patterns, experience levels, known ATS slugs
  companies_db.py  — Curated company database (~150 companies)
  csv_io.py        — CSV output handling
  excel_io.py      — Excel input handling
  create_sample.py — Helper to create sample companies.xlsx
  requirements.txt — Python dependencies
```

## License

MIT
