from .models import StructuredRecord


def normalize_skills(
    record: StructuredRecord,
    alias_map: dict[str, str],
) -> StructuredRecord:
    """
    Case-insensitive alias lookup. Deduplicates after mapping.
    Preserves skills not found in the alias map unchanged.
    """
    # Build a lowercase-keyed lookup for O(1) case-insensitive access
    lower_map: dict[str, str] = {k.lower(): v for k, v in alias_map.items()}

    normalized: list[str] = []
    seen: set[str] = set()

    for skill in record.skills:
        canonical = lower_map.get(skill.lower(), skill)
        if canonical not in seen:
            seen.add(canonical)
            normalized.append(canonical)

    return StructuredRecord(
        role=record.role,
        skills=normalized,
        seniority=record.seniority,
        location=record.location,
        salary=record.salary,
    )
