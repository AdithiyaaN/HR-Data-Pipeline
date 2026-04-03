"""
Tests for the Parser module.
Properties 1 and 2, plus unit tests for error cases.
"""
import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

from job_pipeline.parser import parse_input_file, parse_input_file_from_string

DELIMITER = "===JOB==="


# --- Property 1: Parser round-trip ---
# Feature: job-description-parser-pipeline, Property 1: Parser round-trip
# Validates: Requirements 1.2, 1.6
@given(st.lists(
    st.text(min_size=1).filter(lambda s: s.strip() and DELIMITER not in s),
    min_size=1,
))
@settings(max_examples=100)
def test_parser_round_trip(job_descriptions):
    """Joining descriptions with delimiter and parsing recovers the original list."""
    joined = DELIMITER.join(job_descriptions)
    result = parse_input_file_from_string(joined)
    assert result == [jd.strip() for jd in job_descriptions]


# --- Property 2: Whitespace blocks are discarded ---
# Feature: job-description-parser-pipeline, Property 2: Whitespace blocks are discarded
# Validates: Requirements 1.3
@given(
    st.lists(
        st.text(min_size=1).filter(lambda s: s.strip() and DELIMITER not in s),
        min_size=1,
    ),
    st.lists(st.text(alphabet=" \t\n\r"), min_size=0, max_size=5),
)
@settings(max_examples=100)
def test_whitespace_blocks_discarded(valid_blocks, whitespace_blocks):
    """Parser output contains no empty or whitespace-only strings."""
    all_blocks = valid_blocks + whitespace_blocks
    # Shuffle isn't needed; just join all blocks with delimiter
    joined = DELIMITER.join(all_blocks)
    result = parse_input_file_from_string(joined)
    for block in result:
        assert block.strip() != "", f"Whitespace-only block found: {block!r}"


# --- Unit tests for error cases ---

def test_file_not_found_raises():
    """Req 1.4: FileNotFoundError raised for missing file."""
    with pytest.raises(FileNotFoundError):
        parse_input_file("nonexistent_path_xyz.txt")


def test_empty_file_raises():
    """Req 1.5: ValueError raised when no valid job descriptions found."""
    with pytest.raises(ValueError):
        parse_input_file_from_string("")


def test_only_whitespace_raises():
    """Req 1.5: ValueError raised when all blocks are whitespace-only."""
    with pytest.raises(ValueError):
        parse_input_file_from_string("   ===JOB===   ===JOB===   ")


def test_single_job_description():
    """Basic parsing of a single job description."""
    result = parse_input_file_from_string("Software Engineer at Acme Corp")
    assert result == ["Software Engineer at Acme Corp"]


def test_multiple_job_descriptions():
    """Req 1.2: Multiple descriptions split correctly."""
    content = "Job A===JOB===Job B===JOB===Job C"
    result = parse_input_file_from_string(content)
    assert result == ["Job A", "Job B", "Job C"]
