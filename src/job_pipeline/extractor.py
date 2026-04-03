import json
import logging
from openai import OpenAI, APIStatusError

from .models import StructuredRecord, SENIORITY_LEVELS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a job description parser. Extract structured information from the job description "
    "and return ONLY a JSON object with exactly these keys: "
    '"role", "skills", "seniority", "location", "salary". '
    "The value for \"skills\" must be a list of strings. "
    "If a field cannot be determined, set its value to null. "
    "Return only the JSON object, no additional text."
)

REQUIRED_KEYS = {"role", "skills", "seniority", "location", "salary"}

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _null_record() -> StructuredRecord:
    return StructuredRecord(role=None, skills=[], seniority=None, location=None, salary=None)


def extract_fields(job_description: str, index: int) -> StructuredRecord:
    """
    Calls gpt-4o-mini with a system prompt requesting JSON output.
    On API error or JSON parse failure: logs the error and returns a null record.
    """
    client = _get_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": job_description},
            ],
        )
    except APIStatusError as e:
        logger.error(
            "HTTP error extracting job index %d: status=%s, message=%s",
            index,
            e.status_code,
            str(e),
        )
        return _null_record()
    except Exception as e:
        logger.error("Unexpected API error extracting job index %d: %s", index, str(e))
        return _null_record()

    raw_content = response.choices[0].message.content or ""

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse JSON response for job index %d: %s. Raw content: %r",
            index,
            str(e),
            raw_content,
        )
        return _null_record()

    # Validate and fill missing keys
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        logger.warning("API response for job index %d missing keys: %s", index, missing)

    role = data.get("role")
    skills_raw = data.get("skills")
    seniority = data.get("seniority")
    location = data.get("location")
    salary = data.get("salary")

    # Enforce skills as list[str]
    if isinstance(skills_raw, list):
        skills = [str(s) for s in skills_raw]
    else:
        skills = []

    # Enforce seniority must be one of SENIORITY_LEVELS
    if seniority not in SENIORITY_LEVELS:
        seniority = None

    return StructuredRecord(
        role=role if isinstance(role, str) else None,
        skills=skills,
        seniority=seniority,
        location=location if isinstance(location, str) else None,
        salary=salary if isinstance(salary, str) else None,
    )
