import json
import os

import pandas as pd

from .models import StructuredRecord

COLUMN_ORDER = ["role", "skills", "seniority", "location", "salary"]


def write_csv(records: list[StructuredRecord], output_path: str) -> None:
    """
    Creates the output directory if it does not exist.
    Serializes skills lists as JSON array strings.
    Writes null fields as empty cells.
    Column order: role, skills, seniority, location, salary.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    rows = []
    for record in records:
        rows.append({
            "role": record.role if record.role is not None else "",
            "skills": json.dumps(record.skills),
            "seniority": record.seniority if record.seniority is not None else "",
            "location": record.location if record.location is not None else "",
            "salary": record.salary if record.salary is not None else "",
        })

    df = pd.DataFrame(rows, columns=COLUMN_ORDER)
    df.to_csv(output_path, index=False)
