"""
Tests for the Pipeline Orchestrator module.
Property 8, unit test for logging, and integration test.
"""
import json
import logging
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from hypothesis import given, settings
import hypothesis.strategies as st

from job_pipeline.pipeline import run_pipeline
from job_pipeline.models import PipelineConfig, StructuredRecord


def _make_mock_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def _write_input_file(path: str, descriptions: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("===JOB===".join(descriptions))


# --- Property 8: Batch size invariant ---
# Feature: job-description-parser-pipeline, Property 8: Batch size invariant
# Validates: Requirements 4.1, 4.2, 4.3
@given(
    descriptions=st.lists(
        st.text(min_size=1).filter(lambda s: s.strip() and "===JOB===" not in s),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=50)
def test_batch_size_invariant(descriptions):
    """Pipeline produces exactly N records for N input job descriptions."""
    null_payload = json.dumps({"role": None, "skills": [], "seniority": None,
                               "location": None, "salary": None})
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "jobs.txt")
        output_path = os.path.join(tmpdir, "out.csv")
        _write_input_file(input_path, descriptions)

        config = PipelineConfig(input_path=input_path, output_path=output_path)

        with patch("job_pipeline.extractor._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.chat.completions.create.return_value = _make_mock_response(null_payload)
            records = run_pipeline(config)

    assert len(records) == len(descriptions)


# --- Unit test for pipeline completion logging ---

def test_pipeline_logs_counts(caplog):
    """Req 4.4: Pipeline logs total, successful, and failed counts."""
    descriptions = ["Job A", "Job B", "Job C"]
    payload = json.dumps({"role": "Engineer", "skills": ["Python"], "seniority": "Mid",
                          "location": "Remote", "salary": "50-80k"})

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "jobs.txt")
        output_path = os.path.join(tmpdir, "out.csv")
        _write_input_file(input_path, descriptions)

        config = PipelineConfig(input_path=input_path, output_path=output_path)

        with patch("job_pipeline.extractor._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.chat.completions.create.return_value = _make_mock_response(payload)

            with caplog.at_level(logging.INFO, logger="job_pipeline.pipeline"):
                run_pipeline(config)

    log_text = " ".join(caplog.messages)
    assert "total" in log_text.lower() or "3" in log_text


# --- Integration test with mocked OpenAI ---

def test_integration_end_to_end():
    """Req 1.1, 2.1, 4.1, 5.1, 5.2, 5.3: Full pipeline run produces correct CSV."""
    import pandas as pd

    jobs = [
        "Senior Python Developer needed in London. Salary: 80-120k.",
        "Junior Data Analyst role. Remote. Skills: SQL, Excel.",
        "Lead DevOps Engineer. Berlin. 100-150K.",
    ]
    responses = [
        {"role": "Python Developer", "skills": ["Python"], "seniority": "Senior",
         "location": "London", "salary": "80-120k"},
        {"role": "Data Analyst", "skills": ["SQL", "Excel"], "seniority": "Junior",
         "location": "Remote", "salary": None},
        {"role": "DevOps Engineer", "skills": ["Docker", "Kubernetes"], "seniority": "Lead",
         "location": "Berlin", "salary": "100-150K"},
    ]

    call_count = 0

    def mock_create(**kwargs):
        nonlocal call_count
        payload = json.dumps(responses[call_count])
        call_count += 1
        return _make_mock_response(payload)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "jobs.txt")
        output_path = os.path.join(tmpdir, "out.csv")
        _write_input_file(input_path, jobs)

        config = PipelineConfig(input_path=input_path, output_path=output_path)

        with patch("job_pipeline.extractor._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.chat.completions.create.side_effect = mock_create
            records = run_pipeline(config)

        assert len(records) == 3
        df = pd.read_csv(output_path)
        assert list(df.columns) == ["role", "skills", "seniority", "location", "salary"]
        assert len(df) == 3
        assert df.iloc[0]["role"] == "Python Developer"
        assert json.loads(df.iloc[0]["skills"]) == ["Python"]
