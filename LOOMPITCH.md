# Loom Walkthrough Script — HR Data Pipeline

**Target duration:** 5–8 minutes

---

## 0:00 — Open with the problem (30 sec)

"HR teams deal with three types of unstructured text constantly — job descriptions, candidate interview answers, and interviewer feedback. None of it is queryable. You can't filter it, sort it, or analyse it. This system fixes that. I'll show you three pipelines that take raw messy text and turn it into structured data — live, right now."

---

## 0:30 — Show the input files (1 min)

Open `data/raw_jobs.txt` in the editor.

"This is real input — 20 job descriptions scraped from job boards, separated by a delimiter. No cleaning, no formatting. Just raw text the way it comes."

Scroll through a few — point out that some have explicit salary labels, some don't. Some have skills listed, some buried in sentences.

Open `data/candidate_answers.txt` briefly.

"Same idea here — 20 candidate responses to a behavioural interview question. Some are detailed and structured, some are one-liners with zero substance."

Open `data/interview_feedback.txt`.

"And 15 blocks of raw interviewer notes. No consistent format, no scoring rubric — just whatever the interviewer typed."

---

## 1:30 — Launch the app (30 sec)

Switch to terminal. Run:

```
.venv\Scripts\streamlit run src/app.py
```

Open browser at `http://localhost:8501`.

"This is the Streamlit UI — three tabs, one per pipeline. Everything runs locally, no API key needed."

---

## 2:00 — Tab 1: Job Description Parser (2 min)

Click Tab 1. Upload `data/raw_jobs.txt`.

"Watch what happens — it parses all 20 jobs in under a second."

Point at the output table:

- "Role extracted from the headline — Senior Python Developer, Lead DevOps Engineer."
- "Skills pulled from the Skills: label where it exists, or from 'using X, Y, Z' patterns in the text."
- "Seniority mapped to one of four levels — Junior, Mid, Senior, Lead."
- "Salary matched with a regex — handles LPA, k, K formats."
- "Location matched against a curated list of 60+ cities and countries."

Point at a row where salary or skills is blank — "This one didn't have a parseable salary in the text, so it stays null rather than guessing."

Click Download CSV. "Fully queryable output — load it into pandas, Excel, whatever."

---

## 4:00 — Tab 2: Candidate Answer Labeller (1.5 min)

Click Tab 2. Upload `data/candidate_answers.txt`.

Point at the summary metrics — Excellent / Good / Fair / Poor counts.

"The scoring is based on STAR method signals. I'll show you two extremes."

Point at a high-scoring row — "This one has all four STAR components, 76 words, a concrete outcome. Scores 70, labelled Good, category Structured."

Point at a Poor row — "This one is 27 words, four vague phrases like 'I think' and 'I guess', no action described, no outcome. Scores 0."

Click the annotation logic expander — "The scoring formula is fully transparent. Word count, component presence, vagueness penalty. No black box."

---

## 5:30 — Tab 3: Interview Feedback Scorecard (1 min)

Click Tab 3. Upload `data/interview_feedback.txt`.

Point at the Hire/Maybe/No Hire counts at the top.

"Each candidate gets scored 1–5 across four dimensions based on keyword signals in the feedback text. The recommendation is extracted from explicit phrases — 'strong hire', 'do not hire', 'borderline'."

Point at a strong candidate row — "Overall 4.8, all dimensions green, Hire."

Point at a weak candidate row — "Overall 1.2, communication and problem solving flagged as concerns, No Hire."

"15 feedback blocks processed in milliseconds. Consistent scorecard every time."

---

## 6:30 — Close (30 sec)

"Three pipelines, three structured datasets, no API key, no manual work. The whole thing is open source at github.com/AdithiyaaN/HR-Data-Pipeline. You can upload your own files and get structured output immediately."

---

## Tips for recording

- Run `streamlit run src/app.py` before hitting record so the app is already open
- Have all three input files ready to drag in — don't fumble with file picker
- Keep the browser and editor side by side so you can show input and output together
- Speak to the data, not the code — the audience cares about the transformation, not the implementation
