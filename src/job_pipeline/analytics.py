import re
import statistics
from collections import Counter
from typing import Optional

from .models import AnalyticsSummary, StructuredRecord


def _parse_salary_numbers(salary: Optional[str]) -> list[float]:
    """Extract all numeric values from a salary string (handles k/K suffix)."""
    if not salary:
        return []
    # Find all numbers, optionally followed by k/K (thousands)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*([kK])?", salary)
    values = []
    for digits, suffix in matches:
        val = float(digits)
        if suffix:
            val *= 1000
        values.append(val)
    return values


def compute_analytics(records: list[StructuredRecord]) -> AnalyticsSummary:
    """
    Computes top-10 skills, role frequency, and salary stats (min/max/median).
    Handles the case where no parseable numeric salary exists.
    """
    # Req 8.1: skill frequency — top 10
    skill_counter: Counter = Counter()
    for record in records:
        for skill in record.skills:
            if skill:
                skill_counter[skill] += 1
    top_skills = skill_counter.most_common(10)

    # Req 8.2: role frequency — sorted descending
    role_counter: Counter = Counter()
    for record in records:
        if record.role:
            role_counter[record.role] += 1
    role_frequency = role_counter.most_common()

    # Req 8.3 / 8.4: salary stats
    salary_values: list[float] = []
    for record in records:
        nums = _parse_salary_numbers(record.salary)
        salary_values.extend(nums)

    if salary_values:
        salary_min: Optional[float] = min(salary_values)
        salary_max: Optional[float] = max(salary_values)
        salary_median: Optional[float] = statistics.median(salary_values)
        salary_insufficient = False
    else:
        salary_min = None
        salary_max = None
        salary_median = None
        salary_insufficient = True

    return AnalyticsSummary(
        top_skills=top_skills,
        role_frequency=role_frequency,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_median=salary_median,
        salary_insufficient=salary_insufficient,
    )
