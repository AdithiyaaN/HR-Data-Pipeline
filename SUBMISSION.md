# HR Data Pipeline — Submission Doc

## What I Built

An end-to-end Python pipeline that converts unstructured HR text into structured, queryable datasets. Three pipelines in one Streamlit web app:

**1. Job Description Parser**
Takes 20 raw job postings (separated by `===JOB===`) and extracts: role, skills, seniority level, location, and salary into a CSV. Uses regex/heuristics (no API key required) — salary patterns like `80-120k` / `25-35 LPA`, location matched against a curated city/country list, role extracted from headline patterns, seniority from keywords (Junior/Mid/Senior/Lead/Principal).

**2. Candidate Answer Labeller**
Takes 20 unstructured candidate responses to "Tell me about a time you dealt with a difficult team member." Annotates each by quality (Poor/Fair/Good/Excellent) and category (Structured/Anecdotal/Vague/Technical) using a STAR-method scoring framework. Outputs a CSV with word count, STAR component breakdown, vagueness detection, and annotation notes.

**3. Interview Feedback Scorecard**
Takes 15 raw interviewer feedback blocks and produces a structured scorecard per candidate: scores 1–5 across Technical, Communication, Problem Solving, and Culture Fit dimensions, an overall score, a Hire/No Hire/Maybe recommendation, and extracted strengths/concerns.

**Live app:** https://github.com/AdithiyaaN/HR-Data-Pipeline
**Deploy:** Streamlit Community Cloud — main file: `src/app.py`

---

## Key Design Decisions

**No LLM dependency for core extraction.** The original spec called for OpenAI GPT-4o-mini. Without an API key, the system falls back entirely to regex and heuristics. This was a deliberate choice to keep the pipeline runnable without credentials — the `--skip-llm` flag bypasses the extractor entirely and lets the fallback engine handle everything.

**Modular pipeline architecture.** Each component (Parser, Extractor, Fallback, Normalizer, Writer, Analytics) is a standalone module with a single function signature. This made it easy to swap the LLM extractor for heuristics without touching the orchestrator.

**Rule-based STAR scoring for candidate answers.** Rather than training a classifier, the labeller uses keyword lists for each STAR component (Situation/Task/Action/Result) and a weighted scoring formula. Simple, transparent, and auditable — the annotation logic is documented inline and exposed in the UI.

**Keyword/sentiment heuristics for scorecards.** Each dimension (technical, communication, etc.) has curated positive and negative keyword lists. Net signal count maps to a 1–5 score. Recommendation is extracted from explicit hire/no-hire phrases. This avoids any ML dependency while producing consistent, explainable scores.

---

## What Broke Along the Way

- **Python version conflict.** The system had Python 3.6 (used by the global `streamlit` install) and Python 3.11 (where dependencies were installed). Solved by creating a venv with Python 3.11 and running everything through `.venv\Scripts\python`.

- **Role extraction edge cases.** The regex headline pattern missed job descriptions phrased as "X wanted" or "X needed" — it expected title-case job titles at the start of a line. Fixed by extending the pattern to handle those endings. Still misses some edge cases (e.g. "We are looking for a recent graduate" extracts "recent graduate" as the role).

- **Skills extraction noise.** The "using X, Y" regex pattern was too greedy — it picked up full sentences like "our design team to build responsive web applications" as a skill. Fixed by adding a noise filter that rejects candidates starting with common prepositions/articles.

- **Unicode encoding error on Windows.** The `→` character in print statements caused a `charmap` codec error on Windows terminals. Fixed by replacing with `->`.

---

## What I'd Improve With More Time

- **LLM with structured output.** With an API key, replace the heuristic extractor with GPT-4o-mini using JSON mode — role, skills, and seniority would be near-perfect across all job formats, not just well-structured ones.

- **Better role extraction.** Train a small NER model or use spaCy's entity recognition to extract job titles more reliably from varied phrasings.

- **Confidence scores.** Each extracted field should carry a confidence indicator (regex match vs. LLM extraction vs. not found) so downstream users know how much to trust each value.

- **Persistent storage.** Currently outputs are written to local CSV files. A proper deployment would write to a database (SQLite or Postgres) so results are queryable across runs.

- **Annotation validation for candidate labeller.** The STAR keyword lists are hand-curated and brittle. A better approach would be to validate the scoring against a small human-labelled ground truth set and tune the weights accordingly.
