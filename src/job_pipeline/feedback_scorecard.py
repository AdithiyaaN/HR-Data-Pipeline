"""
Interview Feedback Scorecard
------------------------------
Reads raw interviewer feedback blocks from a delimited text file,
extracts structured scorecard fields using keyword/heuristic analysis,
and writes a CSV scorecard.

Delimiter: ===FEEDBACK===
"""
import re
import os
import logging
from dataclasses import dataclass, asdict
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

DELIMITER = "===FEEDBACK==="

# --- Dimension keyword maps ---
# Each entry: (positive_keywords, negative_keywords)
DIMENSION_SIGNALS = {
    "technical": (
        ["strong technical", "excellent technical", "solid understanding", "deep knowledge",
         "impressive", "well-versed", "proficient", "expert", "technically sound",
         "good grasp", "strong foundation", "demonstrated knowledge", "clear understanding"],
        ["lacks technical", "weak technical", "limited knowledge", "struggled with",
         "couldn't explain", "no experience", "unfamiliar", "poor understanding",
         "needs improvement", "basic knowledge only", "surface level"],
    ),
    "communication": (
        ["articulate", "clear communicator", "well-spoken", "explained clearly",
         "good listener", "concise", "structured answers", "easy to follow",
         "communicated well", "confident", "engaging", "coherent"],
        ["unclear", "rambling", "hard to follow", "poor communication", "struggled to explain",
         "verbose", "disorganised", "incoherent", "vague answers", "difficult to understand"],
    ),
    "problem_solving": (
        ["analytical", "structured approach", "methodical", "creative solution",
         "thought through", "broke down the problem", "logical", "systematic",
         "good problem solver", "innovative", "identified the issue", "root cause"],
        ["no clear approach", "jumped to solution", "couldn't solve", "struggled",
         "no structure", "missed the point", "didn't consider", "overlooked"],
    ),
    "culture_fit": (
        ["team player", "collaborative", "positive attitude", "enthusiastic", "motivated",
         "good culture fit", "aligns with values", "adaptable", "open to feedback",
         "growth mindset", "passionate", "proactive"],
        ["poor fit", "negative attitude", "arrogant", "dismissive", "inflexible",
         "not a team player", "difficult", "resistant to feedback", "disengaged"],
    ),
}

HIRE_SIGNALS = ["strong hire", "definitely hire", "recommend", "move forward", "yes hire", "hire", "proceed"]
NO_HIRE_SIGNALS = ["no hire", "do not hire", "reject", "not a fit", "pass", "would not recommend", "decline"]
MAYBE_SIGNALS = ["maybe", "borderline", "on the fence", "could go either way", "potential", "with reservations"]


@dataclass
class Scorecard:
    candidate_id: int
    technical_score: int          # 1-5
    communication_score: int      # 1-5
    problem_solving_score: int    # 1-5
    culture_fit_score: int        # 1-5
    overall_score: float          # average of above
    overall_recommendation: str   # Hire / No Hire / Maybe
    strengths: str                # comma-separated
    concerns: str                 # comma-separated
    raw_feedback: str


def _score_dimension(text: str, positive: list[str], negative: list[str]) -> int:
    """Return a 1-5 score based on positive/negative signal counts."""
    lower = text.lower()
    pos = sum(1 for kw in positive if kw in lower)
    neg = sum(1 for kw in negative if kw in lower)
    net = pos - neg
    if net >= 2:
        return 5
    elif net == 1:
        return 4
    elif net == 0:
        return 3
    elif net == -1:
        return 2
    else:
        return 1


def _extract_recommendation(text: str) -> str:
    lower = text.lower()
    if any(kw in lower for kw in NO_HIRE_SIGNALS):
        return "No Hire"
    if any(kw in lower for kw in HIRE_SIGNALS):
        return "Hire"
    if any(kw in lower for kw in MAYBE_SIGNALS):
        return "Maybe"
    return "Unclear"


def _extract_strengths_concerns(text: str, scores: dict[str, int]) -> tuple[str, str]:
    strengths = [dim for dim, score in scores.items() if score >= 4]
    concerns = [dim for dim, score in scores.items() if score <= 2]

    # Also scan for explicit strength/concern sentences
    for line in text.split("."):
        line = line.strip().lower()
        if any(w in line for w in ["strength", "strong point", "excelled", "stood out"]):
            strengths.append("noted strength")
            break
    for line in text.split("."):
        line = line.strip().lower()
        if any(w in line for w in ["concern", "weakness", "area for improvement", "struggled"]):
            concerns.append("noted concern")
            break

    return (
        ", ".join(sorted(set(strengths))) or "None noted",
        ", ".join(sorted(set(concerns))) or "None noted",
    )


def score_feedback(text: str, candidate_id: int) -> Scorecard:
    scores = {}
    for dim, (pos, neg) in DIMENSION_SIGNALS.items():
        scores[dim] = _score_dimension(text, pos, neg)

    overall = round(sum(scores.values()) / len(scores), 1)
    recommendation = _extract_recommendation(text)
    strengths, concerns = _extract_strengths_concerns(text, scores)

    return Scorecard(
        candidate_id=candidate_id,
        technical_score=scores["technical"],
        communication_score=scores["communication"],
        problem_solving_score=scores["problem_solving"],
        culture_fit_score=scores["culture_fit"],
        overall_score=overall,
        overall_recommendation=recommendation,
        strengths=strengths,
        concerns=concerns,
        raw_feedback=text,
    )


def build_scorecards(input_path: str, output_path: str) -> list[Scorecard]:
    """
    Read feedback blocks from input_path, score each, write CSV to output_path.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, encoding="utf-8") as f:
        raw = f.read()

    blocks = [b.strip() for b in raw.split(DELIMITER)]
    blocks = [b for b in blocks if b]

    if not blocks:
        raise ValueError("No feedback blocks found in input file.")

    results = []
    for i, block in enumerate(blocks):
        card = score_feedback(block, candidate_id=i + 1)
        results.append(card)
        logger.info("Candidate %d: overall=%.1f, recommendation=%s",
                    i + 1, card.overall_score, card.overall_recommendation)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    rows = [asdict(c) for c in results]
    df = pd.DataFrame(rows, columns=[
        "candidate_id", "technical_score", "communication_score",
        "problem_solving_score", "culture_fit_score", "overall_score",
        "overall_recommendation", "strengths", "concerns", "raw_feedback",
    ])
    df.to_csv(output_path, index=False)
    logger.info("Wrote %d scorecards to %s", len(results), output_path)
    return results
