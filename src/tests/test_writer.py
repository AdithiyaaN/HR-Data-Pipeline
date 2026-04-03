"""
Tests for the Output Writer module.
Properties 9 and 10, plus unit tests.
"""
import json
import os
import tempfile
import pytest
import pandas as pd
from hypothesis import given, settings
import hypothesis.strategies as st

from job_pipeline.writer import write_csv, COLUMN_ORDER
from job_pipeline.models import StructuredRecord

# Strategy for generating StructuredRecord-like data
_skill_strategy = st.lists(st.text(min_size=1).filter(lambda s: s.strip()), min_size=0, max_size=5)
_opt_text = st.one_of(st.none(), st.text(min_size=1))


def _records_strategy():
    return st.lists(
        st.builds(
            StructuredRecord,
            role=_opt_text,
            skills=_skill_strategy,
            seniority=st.one_of(st.none(), st.sampled_from(["Junior", "Mid", "Senior", "Lead"])),
            location=_opt_text,
            salary=_opt_text,
        ),
        min_size=0,
        max_size=10,
    )


# --- Property 9: CSV schema invariant ---
# Feature: job-description-parser-pipeline, Property 9: CSV schema invariant
# Validates: Requirements 5.2, 5.3
@given(records=_records_strategy())
@settings(max_examples=100)
def test_csv_schema_invariant(records):
    """CSV has exactly the right columns in order and one row per record."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        write_csv(records, path)
        df = pd.read_csv(path)
        assert list(df.columns) == COLUMN_ORDER
        assert len(df) == len(records)
    finally:
        os.unlink(path)


# --- Property 10: Skills serialization round-trip ---
# Feature: job-description-parser-pipeline, Property 10: Skills serialization round-trip
# Validates: Requirements 5.4
@given(skills=st.lists(st.text(min_size=1).filter(lambda s: s.strip()), min_size=1, max_size=10))
@settings(max_examples=100)
def test_skills_serialization_round_trip(skills):
    """Skills written to CSV and read back as JSON equal the original list."""
    record = StructuredRecord(skills=skills)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        write_csv([record], path)
        df = pd.read_csv(path)
        recovered = json.loads(df.iloc[0]["skills"])
        assert recovered == skills
    finally:
        os.unlink(path)


# --- Unit tests ---

def test_missing_directory_is_created():
    """Req 5.6: Output directory is created if it does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "subdir", "output.csv")
        write_csv([], output_path)
        assert os.path.exists(output_path)


def test_null_fields_written_as_empty_cells():
    """Req 5.5: Null fields are written as empty CSV cells."""
    record = StructuredRecord(role=None, skills=[], seniority=None, location=None, salary=None)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        write_csv([record], path)
        df = pd.read_csv(path)
        row = df.iloc[0]
        assert row["role"] == "" or pd.isna(row["role"]) or str(row["role"]) == ""
        assert row["seniority"] == "" or pd.isna(row["seniority"]) or str(row["seniority"]) == ""
        assert row["location"] == "" or pd.isna(row["location"]) or str(row["location"]) == ""
        assert row["salary"] == "" or pd.isna(row["salary"]) or str(row["salary"]) == ""
    finally:
        os.unlink(path)


def test_column_order():
    """Req 5.2: Columns are in the correct order."""
    record = StructuredRecord(role="Dev", skills=["Python"], seniority="Mid",
                              location="Remote", salary="50-80k")
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        write_csv([record], path)
        df = pd.read_csv(path)
        assert list(df.columns) == ["role", "skills", "seniority", "location", "salary"]
    finally:
        os.unlink(path)
