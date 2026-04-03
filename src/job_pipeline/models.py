from dataclasses import dataclass, field
from typing import Optional

SENIORITY_LEVELS = {"Junior", "Mid", "Senior", "Lead"}


@dataclass
class StructuredRecord:
    role: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    seniority: Optional[str] = None   # must be one of SENIORITY_LEVELS or None
    location: Optional[str] = None
    salary: Optional[str] = None


@dataclass
class PipelineConfig:
    input_path: str = "data/raw_jobs.txt"
    output_path: str = "data/structured_jobs.csv"
    openai_model: str = "gpt-4o-mini"
    enable_normalization: bool = False
    skill_alias_map: dict[str, str] = field(default_factory=dict)
    enable_analytics: bool = False
    enable_streamlit: bool = False
    skip_llm: bool = False  # bypass OpenAI; rely entirely on fallback engine


@dataclass
class AnalyticsSummary:
    top_skills: list[tuple[str, int]]       # (skill, count), top 10
    role_frequency: list[tuple[str, int]]   # (role, count), sorted desc
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_median: Optional[float] = None
    salary_insufficient: bool = False
