import re
from dataclasses import replace

from .models import StructuredRecord, SENIORITY_LEVELS

# Salary regex: matches patterns like "10-20 LPA", "50 - 80k", "100-150K"
_SALARY_PATTERN = re.compile(r"\d+\s?-\s?\d+\s?(?:LPA|k|K)")

# Seniority: explicit label or keyword in text
_SENIORITY_EXPLICIT = re.compile(
    r"seniority\s*[:\-]\s*(Junior|Mid|Senior|Lead)", re.IGNORECASE
)
_SENIORITY_INLINE = re.compile(
    r"\b(Junior|Mid(?:-level)?|Senior|Lead|Principal)\b", re.IGNORECASE
)
_SENIORITY_MAP = {
    "junior": "Junior", "mid": "Mid", "mid-level": "Mid",
    "senior": "Senior", "lead": "Lead", "principal": "Lead",
}

# Role: explicit label, or first "Job Title — ..." / "We are hiring a X" pattern
_ROLE_EXPLICIT = re.compile(r"role\s*[:\-]\s*(.+)", re.IGNORECASE)
_ROLE_HIRING = re.compile(
    r"(?:we are (?:looking for|hiring) (?:a|an)\s+)([A-Z][^\n.]+?)(?:\s+to\b|\s+for\b|\s+at\b|\.)",
    re.IGNORECASE,
)
_ROLE_HEADLINE = re.compile(
    r"^([A-Z][A-Za-z\s/\-]+(?:Engineer|Developer|Analyst|Scientist|Manager|Designer|Architect|Lead|Specialist|Consultant|Director|Officer|Administrator|QA|DevOps|SRE|Researcher))\b[^.]*?(?:wanted|needed|required|role)?",
    re.MULTILINE | re.IGNORECASE,
)
_ROLE_DASH = re.compile(
    r"^(.+?)\s*[—\-–]\s*(?:Remote|Hybrid|On-site|[A-Z][a-z])",
    re.MULTILINE,
)

# Skills: explicit "Skills:" / "Required skills:" / "using X, Y, Z" / "X, Y expertise"
_SKILLS_EXPLICIT = re.compile(
    r"(?:required\s+)?skills?\s*[:\-]\s*([^\n.]+)", re.IGNORECASE
)
_SKILLS_EXPERTISE = re.compile(
    r"^([A-Za-z0-9\s,/+#.]+?)\s+expertise\s+required",
    re.IGNORECASE | re.MULTILINE,
)
_SKILLS_USING = re.compile(
    r"(?:using|with|experience (?:in|with))\s+([A-Za-z0-9\s,/+#.]+?)(?:\.|,\s+and\b|\n|$)",
    re.IGNORECASE,
)
# Noise phrases to filter out of skill candidates
_SKILLS_NOISE = re.compile(
    r"^(our|the|a|an|and|or|to|for|in|of|with|at|on|is|are|will|you|we|this|that|their|its)\b",
    re.IGNORECASE,
)

# Curated list of known cities and countries for location heuristics
_KNOWN_LOCATIONS = [
    # Cities
    "New York", "San Francisco", "Los Angeles", "Chicago", "Seattle",
    "Boston", "Austin", "Denver", "Atlanta", "Miami",
    "London", "Manchester", "Birmingham", "Edinburgh", "Dublin",
    "Berlin", "Munich", "Hamburg", "Frankfurt", "Amsterdam",
    "Paris", "Lyon", "Madrid", "Barcelona", "Rome", "Milan",
    "Toronto", "Vancouver", "Montreal", "Sydney", "Melbourne",
    "Singapore", "Tokyo", "Seoul", "Shanghai", "Beijing",
    "Bangalore", "Mumbai", "Hyderabad", "Chennai", "Pune", "Delhi",
    "Dubai", "Abu Dhabi", "Zurich", "Stockholm", "Oslo", "Copenhagen",
    # Countries
    "United States", "United Kingdom", "Germany", "France", "Canada",
    "Australia", "India", "Singapore", "Japan", "Netherlands",
    "Spain", "Italy", "Sweden", "Norway", "Denmark", "Switzerland",
    "Brazil", "Mexico", "Poland", "Portugal",
    # Work-mode keywords
    "Remote", "Hybrid", "On-site", "Onsite",
]

# Build a single regex that matches any known location (word-boundary aware)
_LOCATION_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(loc) for loc in _KNOWN_LOCATIONS) + r")\b",
    re.IGNORECASE,
)


def _extract_role(text: str) -> str | None:
    # Try "Role: X" explicit label
    m = _ROLE_EXPLICIT.search(text)
    if m:
        return m.group(1).strip().rstrip(".")

    # Try "We are looking for a X" / "We are hiring a X"
    m = _ROLE_HIRING.search(text)
    if m:
        return m.group(1).strip().rstrip(".")

    # Try "Title — Location" headline pattern (first line)
    first_line = text.strip().splitlines()[0]
    m = _ROLE_DASH.match(first_line)
    if m:
        return m.group(1).strip()

    # Try job title keyword in first line
    m = _ROLE_HEADLINE.search(text)
    if m:
        return m.group(1).strip()

    return None


def _extract_seniority(text: str) -> str | None:
    # Explicit "Seniority: Senior"
    m = _SENIORITY_EXPLICIT.search(text)
    if m:
        return _SENIORITY_MAP.get(m.group(1).lower())

    # Inline keyword — pick first match
    m = _SENIORITY_INLINE.search(text)
    if m:
        return _SENIORITY_MAP.get(m.group(1).lower())

    return None


def _extract_skills(text: str) -> list[str]:
    # Try explicit "Skills: X, Y, Z"
    m = _SKILLS_EXPLICIT.search(text)
    if m:
        raw = m.group(1)
        skills = [s.strip().rstrip(".") for s in re.split(r",\s*|\s+and\s+", raw) if s.strip()]
        return [s for s in skills if len(s) > 1]

    # Try "X, Y expertise required"
    m = _SKILLS_EXPERTISE.search(text)
    if m:
        raw = m.group(1)
        skills = [s.strip().rstrip(".") for s in re.split(r",\s*|\s+and\s+", raw) if s.strip()]
        return [s for s in skills if len(s) > 1]

    # Try "using X, Y and Z" / "experience with X, Y"
    skills = []
    for m in _SKILLS_USING.finditer(text):
        raw = m.group(1)
        parts = [s.strip().rstrip(".") for s in re.split(r",\s*|\s+and\s+", raw) if s.strip()]
        skills.extend(p for p in parts if len(p) > 1 and not _SKILLS_NOISE.match(p))

    return list(dict.fromkeys(skills))  # deduplicate, preserve order


def apply_fallbacks(record: StructuredRecord, raw_text: str) -> StructuredRecord:
    """
    Applies salary regex and location heuristics only when the respective field is null.
    Also extracts role, skills, and seniority via regex when null.
    Never overwrites non-null values.
    Returns a new StructuredRecord with fallback values applied.
    """
    salary = record.salary
    location = record.location
    role = record.role
    skills = record.skills
    seniority = record.seniority

    if salary is None:
        m = _SALARY_PATTERN.search(raw_text)
        if m:
            salary = m.group(0)

    if location is None:
        m = _LOCATION_PATTERN.search(raw_text)
        if m:
            location = m.group(1)

    if role is None:
        role = _extract_role(raw_text)

    if seniority is None:
        seniority = _extract_seniority(raw_text)

    if not skills:
        skills = _extract_skills(raw_text)

    return replace(record, salary=salary, location=location,
                   role=role, skills=skills, seniority=seniority)
