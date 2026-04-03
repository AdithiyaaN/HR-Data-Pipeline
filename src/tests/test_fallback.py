"""
Tests for the Fallback Engine module.
Properties 5, 6, and 7.
"""
import re
import pytest
from hypothesis import given, settings, assume
import hypothesis.strategies as st

from job_pipeline.fallback import apply_fallbacks, _SALARY_PATTERN, _KNOWN_LOCATIONS
from job_pipeline.models import StructuredRecord

# Salary pattern for test generation
_SALARY_RE = re.compile(r"\d+\s?-\s?\d+\s?(?:LPA|k|K)")


def _record_with_null_salary(**kwargs) -> StructuredRecord:
    return StructuredRecord(salary=None, **kwargs)


def _record_with_null_location(**kwargs) -> StructuredRecord:
    return StructuredRecord(location=None, **kwargs)


# --- Property 5: Salary fallback extracts or preserves null ---
# Feature: job-description-parser-pipeline, Property 5: Salary fallback extracts or preserves null
# Validates: Requirements 3.1, 3.2, 3.3
@given(raw_text=st.text())
@settings(max_examples=100)
def test_salary_fallback_extracts_or_preserves_null(raw_text):
    """Salary fallback sets salary to first match or leaves it None."""
    record = StructuredRecord(salary=None)
    result = apply_fallbacks(record, raw_text)

    match = _SALARY_PATTERN.search(raw_text)
    if match:
        assert result.salary == match.group(0)
    else:
        assert result.salary is None


# --- Property 6: Location fallback extracts or preserves null ---
# Feature: job-description-parser-pipeline, Property 6: Location fallback extracts or preserves null
# Validates: Requirements 3.4, 3.5, 3.6
@given(raw_text=st.text())
@settings(max_examples=100)
def test_location_fallback_extracts_or_preserves_null(raw_text):
    """Location fallback sets location to matched keyword or leaves it None."""
    from job_pipeline.fallback import _LOCATION_PATTERN
    record = StructuredRecord(location=None)
    result = apply_fallbacks(record, raw_text)

    match = _LOCATION_PATTERN.search(raw_text)
    if match:
        assert result.location == match.group(1)
    else:
        assert result.location is None


# --- Property 7: Fallback never overwrites non-null fields ---
# Feature: job-description-parser-pipeline, Property 7: Fallback never overwrites non-null fields
# Validates: Requirements 3.7
@given(
    salary=st.text(min_size=1),
    location=st.text(min_size=1),
    raw_text=st.text(),
)
@settings(max_examples=100)
def test_fallback_never_overwrites_non_null_fields(salary, location, raw_text):
    """Non-null salary and location are never overwritten by fallback."""
    record = StructuredRecord(salary=salary, location=location)
    result = apply_fallbacks(record, raw_text)
    assert result.salary == salary
    assert result.location == location


# --- Unit tests ---

def test_salary_fallback_matches_lpa():
    """Salary regex matches LPA format."""
    record = StructuredRecord(salary=None)
    result = apply_fallbacks(record, "Offering 10-20 LPA for this role")
    assert result.salary == "10-20 LPA"


def test_salary_fallback_matches_k():
    """Salary regex matches k format."""
    record = StructuredRecord(salary=None)
    result = apply_fallbacks(record, "Salary: 50-80k per year")
    assert result.salary == "50-80k"


def test_location_fallback_matches_remote():
    """Location heuristic matches Remote keyword."""
    record = StructuredRecord(location=None)
    result = apply_fallbacks(record, "This is a Remote position")
    assert result.location == "Remote"


def test_location_fallback_matches_city():
    """Location heuristic matches known city."""
    record = StructuredRecord(location=None)
    result = apply_fallbacks(record, "Office located in London")
    assert result.location == "London"


def test_no_overwrite_when_salary_set():
    """Req 3.7: Existing salary is not overwritten."""
    record = StructuredRecord(salary="existing salary")
    result = apply_fallbacks(record, "Offering 10-20 LPA")
    assert result.salary == "existing salary"
