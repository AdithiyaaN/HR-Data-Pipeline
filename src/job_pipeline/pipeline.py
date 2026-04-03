import logging

from .models import PipelineConfig, StructuredRecord
from .parser import parse_input_file
from .extractor import extract_fields
from .fallback import apply_fallbacks
from .writer import write_csv

logger = logging.getLogger(__name__)


def run_pipeline(config: PipelineConfig) -> list[StructuredRecord]:
    """
    Orchestrates Parser → Extractor → Fallback → (Normalizer) → Output Writer.
    Logs total processed, successful, and failed extraction counts.
    Continues processing on per-record failures.
    """
    # Step 1: Parse input file
    job_descriptions = parse_input_file(config.input_path)

    total = len(job_descriptions)
    successful = 0
    failed = 0
    records: list[StructuredRecord] = []

    # Step 2: Extract + Fallback per record
    for index, raw_text in enumerate(job_descriptions):
        try:
            record = StructuredRecord() if config.skip_llm else extract_fields(raw_text, index)
            record = apply_fallbacks(record, raw_text)

            # Determine if extraction was successful (at least one non-null field)
            if any([record.role, record.skills, record.seniority, record.location, record.salary]):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error("Unexpected error processing job index %d: %s", index, str(e))
            record = StructuredRecord()
            failed += 1

        records.append(record)

    # Step 3: Optional normalization
    if config.enable_normalization:
        try:
            from .normalizer import normalize_skills
            records = [normalize_skills(r, config.skill_alias_map) for r in records]
        except ImportError:
            logger.warning("Normalization enabled but normalizer module is not available.")

    # Step 4: Write output
    write_csv(records, config.output_path)

    # Step 5: Optional analytics
    if config.enable_analytics:
        try:
            from .analytics import compute_analytics
            summary = compute_analytics(records)
            logger.info("Analytics summary: %s", summary)
        except ImportError:
            logger.warning("Analytics enabled but analytics module is not available.")

    # Req 4.4: Log counts
    logger.info(
        "Pipeline complete — total: %d, successful: %d, failed: %d",
        total,
        successful,
        failed,
    )

    return records
