"""
Streamlit UI for the Job Description Parser Pipeline.
Run with: streamlit run src/job_pipeline/app.py
"""
import tempfile
import os

import pandas as pd

from .models import PipelineConfig
from .pipeline import run_pipeline


def records_to_dataframe(records) -> pd.DataFrame:
    import json

    rows = []
    for r in records:
        rows.append({
            "role": r.role or "",
            "skills": json.dumps(r.skills) if r.skills else "",
            "seniority": r.seniority or "",
            "location": r.location or "",
            "salary": r.salary or "",
        })
    return pd.DataFrame(rows, columns=["role", "skills", "seniority", "location", "salary"])


def main():
    import streamlit as st

    st.title("Job Description Parser Pipeline")

    uploaded_file = st.file_uploader(
        "Upload a plain text file containing job descriptions (delimited by ===JOB===)",
        type=["txt"],
    )

    if uploaded_file is not None:
        try:
            # Save uploaded file to a temp location
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".txt", delete=False
            ) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                config = PipelineConfig(
                    input_path=tmp_path,
                    enable_streamlit=True,
                )
                records = run_pipeline(config)
            finally:
                os.unlink(tmp_path)

            df = records_to_dataframe(records)

            st.subheader("Extracted Dataset")
            st.dataframe(df, use_container_width=True)

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name="structured_jobs.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"Pipeline error: {e}")

if __name__ == "__main__":
    main()
