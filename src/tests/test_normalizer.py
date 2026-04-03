"""
Tests for the Normalizer module.
Property 11.
"""
from hypothesis import given, settings
import hypothesis.strategies as st

from job_pipeline.normalizer import normalize_skills
from job_pipeline.models import StructuredRecord


# --- Property 11: Normalization replaces matching aliases ---
# Feature: job-description-parser-pipeline, Property 11: Normalization replaces matching aliases
# Validates: Requirements 6.1, 6.2, 6.3, 6.4
@given(
    skills=st.lists(st.text(min_size=1).filter(lambda s: s.strip()), min_size=0, max_size=10),
    alias_map=st.dictionaries(
        st.text(min_size=1).filter(lambda s: s.strip()),
        st.text(min_size=1).filter(lambda s: s.strip()),
        min_size=0,
        max_size=5,
    ),
)
@settings(max_examples=100)
def test_normalization_replaces_matching_aliases(skills, alias_map):
    """After normalization: aliases replaced, non-matching preserved, no duplicates."""
    record = StructuredRecord(skills=skills)
    result = normalize_skills(record, alias_map)

    lower_map = {k.lower(): v for k, v in alias_map.items()}

    # Check each output skill is either a canonical value or an unchanged original
    seen = set()
    for skill in result.skills:
        assert skill not in seen, f"Duplicate skill found: {skill!r}"
        seen.add(skill)

    # Verify no duplicates in canonical space
    assert len(result.skills) == len(set(result.skills))

    # Verify all original skills that don't map to an alias are preserved
    expected_canonical = []
    seen_canonical = set()
    for skill in skills:
        canonical = lower_map.get(skill.lower(), skill)
        if canonical not in seen_canonical:
            seen_canonical.add(canonical)
            expected_canonical.append(canonical)

    assert result.skills == expected_canonical


# --- Unit tests ---

def test_case_insensitive_alias_lookup():
    """Req 6.2: Alias lookup is case-insensitive."""
    record = StructuredRecord(skills=["JS", "js", "Js"])
    result = normalize_skills(record, {"js": "JavaScript"})
    assert result.skills == ["JavaScript"]


def test_non_matching_skills_preserved():
    """Req 6.3: Skills not in alias map are preserved unchanged."""
    record = StructuredRecord(skills=["Python", "SQL"])
    result = normalize_skills(record, {"js": "JavaScript"})
    assert result.skills == ["Python", "SQL"]


def test_deduplication_after_normalization():
    """Req 6.4: Duplicates removed after normalization, first occurrence kept."""
    record = StructuredRecord(skills=["JS", "JavaScript", "js"])
    result = normalize_skills(record, {"js": "JavaScript"})
    assert result.skills == ["JavaScript"]


def test_empty_skills_list():
    """Empty skills list returns empty list."""
    record = StructuredRecord(skills=[])
    result = normalize_skills(record, {"js": "JavaScript"})
    assert result.skills == []
