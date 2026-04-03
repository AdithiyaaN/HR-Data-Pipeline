"""
Tests for the Extractor module.
Properties 3 and 4, plus unit tests for error handling.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from hypothesis import given, settings
import hypothesis.strategies as st

from job_pipeline.extractor import extract_fields, SYSTEM_PROMPT
from job_pipeline.models import SENIORITY_LEVELS, StructuredRecord

VALID_SENIORITY = sorted(SENIORITY_LEVELS)


def _make_mock_response(content: str):
    """Build a mock OpenAI response object."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


# --- Property 3: Extraction preserves all five keys ---
# Feature: job-description-parser-pipeline, Property 3: Extraction preserves all five keys
# Validates: Requirements 2.3, 2.4
@given(
    role=st.text(min_size=1),
    skills=st.lists(st.text(min_size=1), min_size=0, max_size=5),
    seniority=st.sampled_from(VALID_SENIORITY),
    location=st.text(min_size=1),
    salary=st.text(min_size=1),
)
@settings(max_examples=100)
def test_extraction_preserves_all_five_keys(role, skills, seniority, location, salary):
    """Valid JSON with all five keys produces a fully-populated StructuredRecord."""
    payload = json.dumps({
        "role": role,
        "skills": skills,
        "seniority": seniority,
        "location": location,
        "salary": salary,
    })
    with patch("job_pipeline.extractor._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(payload)
        record = extract_fields("some job description", 0)

    assert record.role == role
    assert record.skills == [str(s) for s in skills]
    assert record.seniority == seniority
    assert record.location == location
    assert record.salary == salary
    assert isinstance(record.skills, list)


# --- Property 4: Invalid seniority is nulled ---
# Feature: job-description-parser-pipeline, Property 4: Invalid seniority is nulled
# Validates: Requirements 2.5
@given(
    seniority=st.text().filter(lambda s: s not in SENIORITY_LEVELS),
)
@settings(max_examples=100)
def test_invalid_seniority_is_nulled(seniority):
    """Any seniority value not in SENIORITY_LEVELS is replaced with None."""
    payload = json.dumps({
        "role": "Engineer",
        "skills": [],
        "seniority": seniority,
        "location": "Remote",
        "salary": "50-80k",
    })
    with patch("job_pipeline.extractor._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(payload)
        record = extract_fields("some job description", 0)

    assert record.seniority is None


# --- Unit tests for error handling ---

def test_api_called_with_correct_model():
    """Req 2.1: API is called with model gpt-4o-mini."""
    payload = json.dumps({"role": "Dev", "skills": [], "seniority": "Mid",
                          "location": "NYC", "salary": "100k"})
    with patch("job_pipeline.extractor._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(payload)
        extract_fields("job desc", 0)

    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs.kwargs.get("model") == "gpt-4o-mini" or \
           call_kwargs.args[0] if call_kwargs.args else False or \
           mock_client.chat.completions.create.call_args[1].get("model") == "gpt-4o-mini"


def test_system_prompt_contains_required_keys():
    """Req 2.2: System prompt contains all five required keys."""
    for key in ("role", "skills", "seniority", "location", "salary"):
        assert key in SYSTEM_PROMPT, f"System prompt missing key: {key}"


def test_http_error_returns_null_record():
    """Req 2.7: HTTP error returns all-null StructuredRecord."""
    from openai import APIStatusError
    import httpx

    with patch("job_pipeline.extractor._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.headers = {}
        mock_client.chat.completions.create.side_effect = APIStatusError(
            "Server error", response=mock_response, body={}
        )
        record = extract_fields("job desc", 0)

    assert record.role is None
    assert record.skills == []
    assert record.seniority is None
    assert record.location is None
    assert record.salary is None


def test_invalid_json_returns_null_record():
    """Req 2.8: Invalid JSON response returns all-null StructuredRecord."""
    with patch("job_pipeline.extractor._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("not valid json {{{")
        record = extract_fields("job desc", 0)

    assert record.role is None
    assert record.skills == []
    assert record.seniority is None
    assert record.location is None
    assert record.salary is None
