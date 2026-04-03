"""
Unified Streamlit UI — three pipelines in one interface.
Run with: streamlit run src/app.py
"""
import sys
import os
import tempfile
import json

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from job_pipeline.models import PipelineConfig
from job_pipeline.pipeline import run_pipeline
from job_pipeline.candidate_labeller import label_answers
from job_pipeline.feedback_scorecard import build_scorecards

st.set_page_config(page_title="HR Data Pipelines", page_icon="📋", layout="wide")

st.title("📋 HR Data Pipelines")
st.caption("Unstructured text → structured, queryable datasets. No API key required.")

tab1, tab2, tab3 = st.tabs([
    "🧾 Job Descriptions",
    "🗣️ Candidate Answers",
    "📝 Interview Feedback",
])

# ── Tab 1: Job Descriptions ──────────────────────────────────────────────────
with tab1:
    st.subheader("Job Description Parser")
    st.write("Upload a `.txt` file with job descriptions separated by `===JOB===`. Extracts location and salary via regex/heuristics.")

    col1, col2 = st.columns([2, 1])
    with col1:
        jd_file = st.file_uploader("Upload job descriptions file", type=["txt"], key="jd")
    with col2:
        use_llm = st.checkbox("Use OpenAI LLM (requires API key)", value=False, key="jd_llm")
        if use_llm:
            api_key = st.text_input("OpenAI API Key", type="password", key="jd_key")
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key

    if jd_file:
        try:
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
                tmp.write(jd_file.read())
                tmp_path = tmp.name

            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as out:
                out_path = out.name

            try:
                config = PipelineConfig(
                    input_path=tmp_path,
                    output_path=out_path,
                    skip_llm=not use_llm,
                )
                records = run_pipeline(config)
            finally:
                os.unlink(tmp_path)

            rows = []
            for r in records:
                rows.append({
                    "role": r.role or "",
                    "skills": json.dumps(r.skills) if r.skills else "[]",
                    "seniority": r.seniority or "",
                    "location": r.location or "",
                    "salary": r.salary or "",
                })
            df = pd.DataFrame(rows, columns=["role", "skills", "seniority", "location", "salary"])

            st.success(f"Processed {len(df)} job descriptions")
            st.dataframe(df, use_container_width=True)

            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="structured_jobs.csv",
                mime="text/csv",
            )

            os.unlink(out_path)

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.info("Upload a file to get started. Sample format:\n\n```\nSenior Python Developer in London...\n===JOB===\nJunior Data Analyst, Remote...\n```")

# ── Tab 2: Candidate Answers ─────────────────────────────────────────────────
with tab2:
    st.subheader("Candidate Answer Labeller")
    st.write("Upload a `.txt` file with candidate answers separated by `===ANSWER===`. Labels each by quality and STAR structure.")

    ans_file = st.file_uploader("Upload candidate answers file", type=["txt"], key="ans")

    if ans_file:
        try:
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
                tmp.write(ans_file.read())
                tmp_path = tmp.name

            out_path = tmp_path + "_out.csv"

            try:
                results = label_answers(tmp_path, out_path)
            finally:
                os.unlink(tmp_path)

            df = pd.read_csv(out_path)
            os.unlink(out_path)

            st.success(f"Labelled {len(df)} answers")

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            counts = df["quality_label"].value_counts()
            col1.metric("Excellent", counts.get("Excellent", 0))
            col2.metric("Good", counts.get("Good", 0))
            col3.metric("Fair", counts.get("Fair", 0))
            col4.metric("Poor", counts.get("Poor", 0))

            st.dataframe(
                df[["answer_id", "word_count", "quality_label", "category",
                    "quality_score", "star_components", "annotation_notes"]],
                use_container_width=True,
            )

            with st.expander("View annotation logic"):
                st.markdown("""
**Quality scoring (0–100):**
- Word count: ≥150 words = +30pts, ≥80 = +20pts, ≥30 = +10pts
- STAR components detected: +10pts each (max 40pts)
- Has action signal: +10pts
- Has result/outcome signal: +10pts
- Vague phrases detected: −5pts each (max −20pts)

**Quality labels:** Excellent ≥75 · Good ≥50 · Fair ≥25 · Poor <25

**Categories:** Structured (3–4 STAR components) · Technical (technical keywords + STAR) · Anecdotal (1–2 STAR components) · Vague (0 STAR components)
                """)

            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="labelled_answers.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.info("Upload a file to get started. Sample format:\n\n```\nWhen I was working at my previous company...\n===ANSWER===\nI think I handled it okay...\n```")

# ── Tab 3: Interview Feedback ─────────────────────────────────────────────────
with tab3:
    st.subheader("Interview Feedback Scorecard")
    st.write("Upload a `.txt` file with feedback blocks separated by `===FEEDBACK===`. Scores each candidate across 4 dimensions.")

    fb_file = st.file_uploader("Upload interview feedback file", type=["txt"], key="fb")

    if fb_file:
        try:
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
                tmp.write(fb_file.read())
                tmp_path = tmp.name

            out_path = tmp_path + "_out.csv"

            try:
                results = build_scorecards(tmp_path, out_path)
            finally:
                os.unlink(tmp_path)

            df = pd.read_csv(out_path)
            os.unlink(out_path)

            st.success(f"Generated {len(df)} scorecards")

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            rec_counts = df["overall_recommendation"].value_counts()
            col1.metric("Hire", rec_counts.get("Hire", 0))
            col2.metric("Maybe", rec_counts.get("Maybe", 0))
            col3.metric("No Hire", rec_counts.get("No Hire", 0))

            st.dataframe(
                df[["candidate_id", "technical_score", "communication_score",
                    "problem_solving_score", "culture_fit_score", "overall_score",
                    "overall_recommendation", "strengths", "concerns"]],
                use_container_width=True,
            )

            with st.expander("View scoring logic"):
                st.markdown("""
**Each dimension scored 1–5** based on positive vs negative keyword signals in the feedback text:
- net ≥ +2 → 5 · net +1 → 4 · net 0 → 3 · net −1 → 2 · net ≤ −2 → 1

**Dimensions:** Technical · Communication · Problem Solving · Culture Fit

**Recommendation:** derived from explicit hire/no-hire/maybe phrases in the feedback text.

**Overall score:** average of the four dimension scores.
                """)

            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="interview_scorecards.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.info("Upload a file to get started. Sample format:\n\n```\nCandidate demonstrated strong technical knowledge...\n===FEEDBACK===\nTechnically weak overall...\n```")
