# Implementation Plan: Job Description Parser Pipeline

## Overview

Implement a Python batch pipeline that reads unstructured job descriptions from a delimited text file, extracts structured fields via the OpenAI API with regex/heuristic fallbacks, and writes a clean CSV dataset. Optional components (Normalizer, Analytics, Streamlit UI) are gated by configuration flags.

## Tasks

- [x] 1. Set up project structure and data models
  - Create the package directory layout: `src/job_pipeline/` with `__init__.py`
  - Define `StructuredRecord`, `PipelineConfig`, and `AnalyticsSummary` dataclasses in `src/job_pipeline/models.py`
  - Define `SENIORITY_LEVELS` constant
  - Create `data/` directory placeholder (`.gitkeep`)
  - Add `requirements.txt` with `openai`, `pandas`, `hypothesis`, `pytest`, `pytest-mock`, `streamlit`
  - _Requirements: 2.5, 4.1, 5.1, 5.2_

- [~] 2. Implement the Parser
  - [x] 2.1 Implement `parse_input_file(file_path: str) -> list[str]` in `src/job_pipeline/parser.py`
    - Read file with UTF-8 encoding, split on `===JOB===`, strip and discard whitespace-only blocks
    - Raise `FileNotFoundError` for missing file; raise `ValueError` for empty/no-valid-blocks result
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 2.2 Write property test for Parser round-trip
    - **Property 1: Parser round-trip**
    - **Validates: Requirements 1.2, 1.6**

  - [ ]* 2.3 Write property test for whitespace block discarding
    - **Property 2: Whitespace blocks are discarded**
    - **Validates: Requirements 1.3**

  - [ ]* 2.4 Write unit tests for Parser error cases
    - Test `FileNotFoundError` raised for missing file (Req 1.4)
    - Test `ValueError` raised for empty file (Req 1.5)
    - _Requirements: 1.4, 1.5_

- [~] 3. Implement the Extractor
  - [x] 3.1 Implement `extract_fields(job_description: str, index: int) -> StructuredRecord` in `src/job_pipeline/extractor.py`
    - Call OpenAI ChatCompletion with model `gpt-4o-mini` and a system prompt requesting JSON with keys `role`, `skills`, `seniority`, `location`, `salary`
    - Parse response as JSON; validate all five keys present; enforce `SENIORITY_LEVELS` (replace invalid with `None`)
    - On HTTP error or JSON parse failure: log error with index and return all-null `StructuredRecord`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [ ]* 3.2 Write property test for extraction key preservation
    - **Property 3: Extraction preserves all five keys**
    - **Validates: Requirements 2.3, 2.4**

  - [ ]* 3.3 Write property test for invalid seniority nulling
    - **Property 4: Invalid seniority is nulled**
    - **Validates: Requirements 2.5**

  - [ ]* 3.4 Write unit tests for Extractor error handling
    - Test all-null record returned on HTTP error (Req 2.7)
    - Test all-null record returned on invalid JSON (Req 2.8)
    - Test API called with model `gpt-4o-mini` (Req 2.1)
    - Test system prompt contains all five required keys (Req 2.2)
    - _Requirements: 2.1, 2.2, 2.7, 2.8_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [~] 5. Implement the Fallback Engine
  - [x] 5.1 Implement `apply_fallbacks(record: StructuredRecord, raw_text: str) -> StructuredRecord` in `src/job_pipeline/fallback.py`
    - Apply salary regex `\d+\s?-\s?\d+\s?(LPA|k|K)` when `salary` is null; set to first match or leave null
    - Apply location heuristics (curated city/country list + `Remote`/`Hybrid` keywords) when `location` is null
    - Never overwrite non-null `salary` or `location` values
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 5.2 Write property test for salary fallback
    - **Property 5: Salary fallback extracts or preserves null**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ]* 5.3 Write property test for location fallback
    - **Property 6: Location fallback extracts or preserves null**
    - **Validates: Requirements 3.4, 3.5, 3.6**

  - [ ]* 5.4 Write property test for fallback non-overwrite
    - **Property 7: Fallback never overwrites non-null fields**
    - **Validates: Requirements 3.7**

- [~] 6. Implement the Output Writer
  - [x] 6.1 Implement `write_csv(records: list[StructuredRecord], output_path: str) -> None` in `src/job_pipeline/writer.py`
    - Use pandas to write CSV with column order `role, skills, seniority, location, salary`
    - Serialize `skills` list as JSON array string; write null fields as empty cells
    - Create output directory with `os.makedirs(exist_ok=True)` if it does not exist
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 6.2 Write property test for CSV schema invariant
    - **Property 9: CSV schema invariant**
    - **Validates: Requirements 5.2, 5.3**

  - [ ]* 6.3 Write property test for skills serialization round-trip
    - **Property 10: Skills serialization round-trip**
    - **Validates: Requirements 5.4**

  - [ ]* 6.4 Write unit tests for Output Writer
    - Test missing output directory is created (Req 5.6)
    - Test null fields written as empty CSV cells (Req 5.5)
    - _Requirements: 5.5, 5.6_

- [~] 7. Implement the Pipeline Orchestrator and batch processing
  - [x] 7.1 Implement `run_pipeline(config: PipelineConfig) -> list[StructuredRecord]` in `src/job_pipeline/pipeline.py`
    - Orchestrate Parser → Extractor → Fallback → (Normalizer) → Output Writer
    - Continue processing on per-record failures; log total processed, successful, and failed counts
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 7.2 Write property test for batch size invariant
    - **Property 8: Batch size invariant**
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ]* 7.3 Write unit test for pipeline completion logging
    - Test that total, successful, and failed counts are logged (Req 4.4)
    - _Requirements: 4.4_

- [x] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [~] 9. Implement the Normalizer (optional component)
  - [x] 9.1 Implement `normalize_skills(record: StructuredRecord, alias_map: dict[str, str]) -> StructuredRecord` in `src/job_pipeline/normalizer.py`
    - Case-insensitive alias lookup; replace matching skills with canonical values; preserve non-matching skills
    - Deduplicate the resulting skills list, preserving first occurrence
    - Wire into `run_pipeline` when `config.enable_normalization` is `True`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 9.2 Write property test for normalization
    - **Property 11: Normalization replaces matching aliases**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [~] 10. Implement the Analytics Engine (optional component)
  - [x] 10.1 Implement `compute_analytics(records: list[StructuredRecord]) -> AnalyticsSummary` in `src/job_pipeline/analytics.py`
    - Compute top-10 skills by frequency, role frequency sorted descending, and salary min/max/median
    - Set `salary_insufficient=True` when no parseable numeric salary exists; do not raise
    - Wire into `run_pipeline` when `config.enable_analytics` is `True`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 10.2 Write property test for top-skills correctness
    - **Property 12: Analytics top-skills are actually most frequent**
    - **Validates: Requirements 8.1**

  - [ ]* 10.3 Write property test for role frequency ordering
    - **Property 13: Role frequency is sorted descending**
    - **Validates: Requirements 8.2**

  - [ ]* 10.4 Write property test for salary stats invariant
    - **Property 14: Salary stats invariant**
    - **Validates: Requirements 8.3**

  - [ ]* 10.5 Write unit test for insufficient salary data
    - Test `salary_insufficient=True` returned when no numeric salary present (Req 8.4)
    - _Requirements: 8.4_

- [~] 11. Implement the Streamlit UI (optional component)
  - [x] 11.1 Create `src/job_pipeline/app.py` with Streamlit interface
    - File uploader widget replacing `data/raw_jobs.txt` as input source
    - Display extracted dataset as interactive `st.dataframe` table
    - CSV download button using `st.download_button`
    - Inline error display on extraction failure without crashing
    - Wire to `run_pipeline` when `config.enable_streamlit` is `True`
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [~] 12. Integration wiring and end-to-end test
  - [x] 12.1 Create `src/job_pipeline/__main__.py` entry point that builds `PipelineConfig` from CLI args/env and calls `run_pipeline`
    - _Requirements: 4.1, 5.1_

  - [ ]* 12.2 Write integration test with mocked OpenAI responses
    - Create a small sample `data/raw_jobs.txt` fixture with 3+ job descriptions
    - Mock OpenAI API responses; run full pipeline; assert output CSV is correct
    - _Requirements: 1.1, 2.1, 4.1, 5.1, 5.2, 5.3_

- [x] 13. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use `pytest` + `hypothesis` with `@given` decorators (min 100 iterations each)
- Unit tests use `pytest` + `pytest-mock` for OpenAI API mocking
- All per-record errors are non-fatal; only file-level errors abort the run
