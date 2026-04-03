# HR Data Pipeline — Submission Doc

**Repo:** https://github.com/AdithiyaaN/HR-Data-Pipeline | **Deploy:** `streamlit run src/app.py`

---

## What I Built

Three unstructured-to-structured pipelines in a single Streamlit app:

- **Job Description Parser** — 20 raw job postings → CSV with role, skills, seniority, location, salary extracted via regex/heuristics
- **Candidate Answer Labeller** — 20 unstructured interview answers → CSV annotated by quality (Poor/Fair/Good/Excellent), category (Structured/Anecdotal/Vague/Technical), STAR component scores, and annotation notes
- **Interview Feedback Scorecard** — 15 raw feedback blocks → CSV scorecard with 1–5 scores across Technical, Communication, Problem Solving, and Culture Fit, plus Hire/No Hire/Maybe recommendation

---

## Key Design Decisions

**No LLM dependency.** Originally designed for GPT-4o-mini, but built a full regex/heuristic fallback so the system runs without an API key. Salary uses pattern matching (`\d+-\d+\s?(LPA|k|K)`), location matches against a curated city/country list, role is extracted from headline patterns, seniority from keywords.

**STAR scoring for candidate answers.** Rather than a classifier, the labeller uses keyword lists per STAR component with a weighted formula (word count + component presence + vagueness penalty). Transparent and auditable — logic is documented in the UI.

**Keyword heuristics for scorecards.** Each dimension has curated positive/negative keyword lists; net signal count maps to a 1–5 score. Recommendation extracted from explicit hire/no-hire phrases in the text.

---

## What Broke

- Python version conflict (3.6 global vs 3.11 venv) — solved with a dedicated venv
- Role extraction missed "X wanted/needed" phrasings — fixed by extending the regex pattern
- Skills regex was too greedy, picking up full sentences — fixed with a noise filter
- Windows terminal crashed on `→` character — replaced with `->`

---

## What I'd Improve

- Add GPT-4o-mini with JSON mode for near-perfect role/skills/seniority extraction
- Add confidence scores per field (regex match vs. LLM vs. not found)
- Validate STAR keyword scoring against a human-labelled ground truth set
- Write outputs to a database instead of local CSVs for cross-run querying
