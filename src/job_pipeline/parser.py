from typing import List

DELIMITER = "===JOB==="


def parse_input_file(file_path: str) -> List[str]:
    """
    Returns a list of non-empty job description strings.
    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if no non-empty job descriptions are found.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError("Input file not found: {}".format(file_path))

    return parse_input_file_from_string(content)


def parse_input_file_from_string(content: str) -> List[str]:
    """
    Same logic as parse_input_file but accepts raw string content directly.
    Used by property-based tests to avoid file I/O.
    Raises ValueError if no non-empty job descriptions are found.
    """
    blocks = [block.strip() for block in content.split(DELIMITER)]
    valid = [block for block in blocks if block]

    if not valid:
        raise ValueError("No job descriptions found in the provided content.")

    return valid
