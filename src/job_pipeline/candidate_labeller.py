"""
Candidate Response Labeller
----------------------------
Reads unstructured candidate answers from a delimited text file,
annotates each by quality and category using rule-based heuristics,
and writes a structured CSV dataset with annotation logic documented.

Delimiter: ===ANSWER===
"""
import re
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

DELIMITER = "===ANSWER==="

# --- STAR method signal keywords ---
SITUATION_KEYWORDS = ["when", "at my previous", "in my last", "while working", "during", "at the time", "in a project", "we were", "i was working"]
TASK_KEYWORDS = ["my responsibility", "i was tasked", "i needed to", "my role was", "i had to", "the goal was", "we needed to"]
ACTION_KEYWORDS = ["i decided", "i implemented", "i built", "i led", "i created", "i resolved", "i worked with", "i collaborated", "i proposed", "i introduced", "i fixed", "i designed", "i developed"]
RESULT_KEYWORDS = ["as a result", "which resulted in", "this led to", "we achieved", "the outcome was", "successfully", "improved", "reduced", "increased", "saved", "delivered", "completed"]

# --- Quality scoring thresholds ---
WORD_COUNT_POOR = 30
WORD_COUNT_FAIR = 80
WORD_COUNT_GOOD = 150

# --- Category signals ---
TECHNICAL_KEYWORDS = ["algorithm", "code", "software", "system", "database", "api", "architecture", "deploy", "debug", "performance", "scalab", "infrastructure", "framework", "library", "python", "java", "sql", "cloud", "aws", "docker"]
VAGUE_PHRASES = ["i think", "maybe", "sort of", "kind of", "i guess", "not sure", "i don't know", "it depends", "generally speaking", "usually"]


@dataclass
class AnnotatedAnswer:
    answer_id: int
    raw_text: str
    word_count: int
    has_situation: bool
    has_task: bool
    has_action: bool
    has_result: bool
    star_components: int          # 0-4
    has_example: bool             # True if any concrete STAR signal found
    has_outcome: bool             # True if result signal found
    is_technical: bool
    vagueness_count: int
    quality_label: str            # Poor / Fair / Good / Excellent
    category: str                 # Structured / Anecdotal / Vague / Technical
    quality_score: int            # 0-100 internal score
    annotation_notes: str


def _count_signals(text: str, keywords: list[str]) -> int:
    lower = text.lower()
    return sum(1 for kw in keywords if kw in lower)


def _score_answer(text: str) -> AnnotatedAnswer:
    words = text.split()
    word_count = len(words)
    lower = text.lower()

    has_situation = _count_signals(text, SITUATION_KEYWORDS) > 0
    has_task = _count_signals(text, TASK_KEYWORDS) > 0
    has_action = _count_signals(text, ACTION_KEYWORDS) > 0
    has_result = _count_signals(text, RESULT_KEYWORDS) > 0
    star_components = sum([has_situation, has_task, has_action, has_result])

    is_technical = _count_signals(text, TECHNICAL_KEYWORDS) >= 2
    vagueness_count = _count_signals(text, VAGUE_PHRASES)

    # --- Score calculation (0-100) ---
    score = 0

    # Word count contribution (up to 30 pts)
    if word_count >= WORD_COUNT_GOOD:
        score += 30
    elif word_count >= WORD_COUNT_FAIR:
        score += 20
    elif word_count >= WORD_COUNT_POOR:
        score += 10

    # STAR components (up to 40 pts, 10 each)
    score += star_components * 10

    # Specificity bonus (up to 20 pts)
    if has_result:
        score += 10
    if has_action:
        score += 10

    # Vagueness penalty (-5 per vague phrase, max -20)
    score -= min(vagueness_count * 5, 20)

    score = max(0, min(100, score))

    # --- Quality label ---
    if score >= 75:
        quality_label = "Excellent"
    elif score >= 50:
        quality_label = "Good"
    elif score >= 25:
        quality_label = "Fair"
    else:
        quality_label = "Poor"

    # --- Category ---
    if is_technical and star_components >= 2:
        category = "Technical"
    elif star_components >= 3:
        category = "Structured"
    elif star_components >= 1 or word_count >= WORD_COUNT_FAIR:
        category = "Anecdotal"
    else:
        category = "Vague"

    # --- Annotation notes ---
    notes = []
    if word_count < WORD_COUNT_POOR:
        notes.append("Very short response")
    if not has_action:
        notes.append("No clear action described")
    if not has_result:
        notes.append("No outcome mentioned")
    if vagueness_count > 0:
        notes.append(f"{vagueness_count} vague phrase(s) detected")
    if star_components == 4:
        notes.append("Full STAR structure present")
    if not notes:
        notes.append("Adequate response")

    return AnnotatedAnswer(
        answer_id=0,  # set by caller
        raw_text=text,
        word_count=word_count,
        has_situation=has_situation,
        has_task=has_task,
        has_action=has_action,
        has_result=has_result,
        star_components=star_components,
        has_example=star_components >= 1,
        has_outcome=has_result,
        is_technical=is_technical,
        vagueness_count=vagueness_count,
        quality_label=quality_label,
        category=category,
        quality_score=score,
        annotation_notes="; ".join(notes),
    )


def label_answers(input_path: str, output_path: str) -> list[AnnotatedAnswer]:
    """
    Read answers from input_path, annotate each, write CSV to output_path.
    Returns list of AnnotatedAnswer objects.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, encoding="utf-8") as f:
        raw = f.read()

    blocks = [b.strip() for b in raw.split(DELIMITER)]
    blocks = [b for b in blocks if b]

    if not blocks:
        raise ValueError("No candidate answers found in input file.")

    results = []
    for i, block in enumerate(blocks):
        annotation = _score_answer(block)
        annotation.answer_id = i + 1
        results.append(annotation)
        logger.info("Answer %d: quality=%s, category=%s, score=%d",
                    i + 1, annotation.quality_label, annotation.category, annotation.quality_score)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    rows = []
    for a in results:
        d = asdict(a)
        rows.append(d)

    df = pd.DataFrame(rows, columns=[
        "answer_id", "word_count", "quality_label", "category", "quality_score",
        "star_components", "has_situation", "has_task", "has_action", "has_result",
        "has_example", "has_outcome", "is_technical", "vagueness_count",
        "annotation_notes", "raw_text",
    ])
    df.to_csv(output_path, index=False)
    logger.info("Wrote %d annotated answers to %s", len(results), output_path)
    return results
