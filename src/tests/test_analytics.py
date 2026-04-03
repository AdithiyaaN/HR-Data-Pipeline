"""
Tests for the Analytics Engine module.
Properties 12, 13, 14, plus unit test for insufficient salary.
"""
from collections import Counter
import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

from job_pipeline.analytics import compute_analytics
from job_pipeline.models import StructuredRecord

_opt_text = st.one_of(st.none(), st.text(min_size=1))
_skill_strategy = st.lists(st.text(min_size=1).filter(lambda s: s.strip()), min_size=0, max_size=5)


def _records_strategy(min_size=0):
    return st.lists(
        st.builds(
            StructuredRecord,
            role=_opt_text,
            skills=_skill_strategy,
            seniority=st.none(),
            location=st.none(),
            salary=_opt_text,
        ),
        min_size=min_size,
        max_size=15,
    )


# --- Property 12: Analytics top-skills are actually most frequent ---
# Feature: job-description-parser-pipeline, Property 12: Analytics top-skills are most frequent
# Validates: Requirements 8.1
@given(records=_records_strategy())
@settings(max_examples=100)
def test_top_skills_are_most_frequent(records):
    """Top-10 skills are the actual most frequent skills in the dataset."""
    summary = compute_analytics(records)

    # Build expected counter
    counter = Counter()
    for r in records:
        for skill in r.skills:
            if skill:
                counter[skill] += 1

    expected_top = counter.most_common(10)
    assert summary.top_skills == expected_top


# --- Property 13: Role frequency is sorted descending ---
# Feature: job-description-parser-pipeline, Property 13: Role frequency is sorted descending
# Validates: Requirements 8.2
@given(records=_records_strategy())
@settings(max_examples=100)
def test_role_frequency_sorted_descending(records):
    """role_frequency list is sorted in non-increasing order of count."""
    summary = compute_analytics(records)
    counts = [count for _, count in summary.role_frequency]
    assert counts == sorted(counts, reverse=True)


# --- Property 14: Salary stats invariant ---
# Feature: job-description-parser-pipeline, Property 14: Salary stats invariant
# Validates: Requirements 8.3
@given(
    records=st.lists(
        st.builds(
            StructuredRecord,
            role=st.none(),
            skills=st.just([]),
            seniority=st.none(),
            location=st.none(),
            # Generate salary strings with parseable numbers
            salary=st.one_of(
                st.none(),
                st.integers(min_value=1, max_value=999).map(lambda n: f"{n}k"),
            ),
        ),
        min_size=1,
        max_size=20,
    ).filter(lambda rs: any(r.salary is not None for r in rs))
)
@settings(max_examples=100)
def test_salary_stats_invariant(records):
    """When parseable salaries exist: salary_min <= salary_median <= salary_max."""
    summary = compute_analytics(records)
    if not summary.salary_insufficient:
        assert summary.salary_min is not None
        assert summary.salary_max is not None
        assert summary.salary_median is not None
        assert summary.salary_min <= summary.salary_median <= summary.salary_max


# --- Unit test for insufficient salary data ---

def test_salary_insufficient_when_no_numeric_salary():
    """Req 8.4: salary_insufficient=True when no parseable numeric salary."""
    records = [
        StructuredRecord(salary=None),
        StructuredRecord(salary="Competitive"),
        StructuredRecord(salary="Negotiable"),
    ]
    summary = compute_analytics(records)
    assert summary.salary_insufficient is True
    assert summary.salary_min is None
    assert summary.salary_max is None
    assert summary.salary_median is None
