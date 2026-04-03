# Requirements Document

## Introduction

This feature implements an end-to-end pipeline that ingests unstructured job description text, extracts structured fields (role, skills, seniority, location, salary) using an LLM with regex/heuristic fallbacks, and outputs a clean CSV/JSON dataset. The pipeline is designed for batch processing of 20+ job descriptions stored in a single delimited text file.

## Glossary

- **Pipeline**: The end-to-end system that reads raw job descriptions, extracts structured data, and writes the output dataset.
- **Job_Description**: A single block of raw, unstructured text describing a job posting.
- **Delimiter**: The string `===JOB===` used to separate individual Job_Descriptions in the input file.
- **Extractor**: The component responsible for calling the OpenAI API to extract structured fields from a Job_Description.
- **Parser**: The component responsible for reading the input file and splitting it into individual Job_Descriptions using the Delimiter.
- **Fallback_Engine**: The regex/heuristic component that attempts to extract salary and location when the Extractor returns null for those fields.
- **Normalizer**: The optional component that maps non-standard skill aliases (e.g., "JS") to canonical names (e.g., "JavaScript").
- **Structured_Record**: A dictionary containing the fields: `role`, `skills`, `seniority`, `location`, `salary`.
- **Dataset**: The collection of all Structured_Records produced by the Pipeline.
- **Output_File**: The CSV file written by the Pipeline containing the Dataset.
- **Seniority_Level**: One of the four enumerated values: `Junior`, `Mid`, `Senior`, `Lead`.

---

## Requirements

### Requirement 1: Input File Parsing

**User Story:** As a data engineer, I want to load job descriptions from a single text file, so that I can process them in batch without manual intervention.

#### Acceptance Criteria

1. THE Parser SHALL read the input file located at `data/raw_jobs.txt` using UTF-8 encoding.
2. WHEN the input file contains one or more Delimiter strings (`===JOB===`), THE Parser SHALL split the file content into individual Job_Description blocks on each Delimiter occurrence.
3. WHEN a Job_Description block contains only whitespace after trimming, THE Parser SHALL discard that block and not include it in the batch.
4. IF the input file does not exist at the expected path, THEN THE Parser SHALL raise a descriptive error identifying the missing file path.
5. IF the input file is empty, THEN THE Parser SHALL raise a descriptive error stating that no Job_Descriptions were found.
6. THE Parser SHALL produce a list of at least one non-empty Job_Description string as output.

---

### Requirement 2: LLM-Based Field Extraction

**User Story:** As a data engineer, I want each job description parsed into structured fields by an LLM, so that I get consistent, semantically accurate extraction without writing hand-crafted rules for every field.

#### Acceptance Criteria

1. WHEN a Job_Description is submitted for extraction, THE Extractor SHALL call the OpenAI ChatCompletion API using model `gpt-4o-mini`.
2. THE Extractor SHALL instruct the model via a system prompt to return a JSON object containing exactly the keys: `role`, `skills`, `seniority`, `location`, `salary`.
3. WHEN the API returns a response, THE Extractor SHALL parse the response body as JSON and validate that all five required keys are present.
4. WHEN the `skills` field is present in the API response, THE Extractor SHALL represent it as a list of strings.
5. WHEN the `seniority` field is present in the API response, THE Extractor SHALL accept only one of the four Seniority_Level values (`Junior`, `Mid`, `Senior`, `Lead`); any other value SHALL be replaced with `null`.
6. WHEN a field cannot be determined from the Job_Description, THE Extractor SHALL set that field's value to `null` in the Structured_Record.
7. IF the OpenAI API returns an HTTP error response, THEN THE Extractor SHALL log the error including the HTTP status code and the affected Job_Description index, and SHALL set all fields to `null` for that record.
8. IF the API response body cannot be parsed as valid JSON, THEN THE Extractor SHALL log a descriptive error and SHALL set all fields to `null` for that record.

---

### Requirement 3: Regex Fallback for Salary and Location

**User Story:** As a data engineer, I want a rule-based fallback for salary and location extraction, so that structured data is recovered even when the LLM returns null for those fields.

#### Acceptance Criteria

1. WHEN the Extractor returns `null` for the `salary` field, THE Fallback_Engine SHALL apply a regex pattern matching the format `\d+\s?-\s?\d+\s?(LPA|k|K)` against the raw Job_Description text.
2. WHEN the salary regex produces a match, THE Fallback_Engine SHALL set the `salary` field to the first matched substring.
3. WHEN the salary regex produces no match, THE Fallback_Engine SHALL leave the `salary` field as `null`.
4. WHEN the Extractor returns `null` for the `location` field, THE Fallback_Engine SHALL apply heuristic pattern matching (e.g., known city names, country names, "Remote", "Hybrid") against the raw Job_Description text.
5. WHEN the location heuristic produces a match, THE Fallback_Engine SHALL set the `location` field to the matched string.
6. WHEN the location heuristic produces no match, THE Fallback_Engine SHALL leave the `location` field as `null`.
7. WHEN the Extractor returns a non-null value for `salary` or `location`, THE Fallback_Engine SHALL not overwrite those values.

---

### Requirement 4: Batch Processing

**User Story:** As a data engineer, I want all job descriptions processed in a single pipeline run, so that I can produce the full dataset without running the tool once per job.

#### Acceptance Criteria

1. THE Pipeline SHALL process every non-empty Job_Description produced by the Parser in a single execution run.
2. WHEN processing a batch, THE Pipeline SHALL produce one Structured_Record per Job_Description.
3. WHEN one Job_Description fails extraction, THE Pipeline SHALL continue processing the remaining Job_Descriptions and SHALL not abort the batch.
4. THE Pipeline SHALL log the total count of Job_Descriptions processed, the count of successful extractions, and the count of failed extractions upon completion.

---

### Requirement 5: Structured Output

**User Story:** As a data analyst, I want the extracted data written to a CSV file, so that I can load it directly into analysis tools like Excel or pandas.

#### Acceptance Criteria

1. WHEN the Pipeline completes processing, THE Pipeline SHALL write the Dataset to `data/structured_jobs.csv` using the pandas library.
2. THE Output_File SHALL contain exactly the columns: `role`, `skills`, `seniority`, `location`, `salary` in that order.
3. THE Output_File SHALL contain one row per Structured_Record.
4. WHEN the `skills` field contains a list, THE Pipeline SHALL serialize it as a JSON array string in the CSV cell (e.g., `["Python", "SQL"]`).
5. WHEN a field value is `null`, THE Pipeline SHALL write an empty cell for that field in the CSV.
6. IF the output directory `data/` does not exist, THEN THE Pipeline SHALL create it before writing the Output_File.

---

### Requirement 6: Optional Skill Normalization

**WHERE** skill normalization is enabled, **THE** Normalizer **SHALL** map non-standard skill aliases to canonical names using a configurable mapping dictionary before the Structured_Record is written to the Dataset.

#### Acceptance Criteria

1. WHERE skill normalization is enabled, THE Normalizer SHALL apply the alias mapping to every string in the `skills` list of each Structured_Record.
2. WHERE skill normalization is enabled and a skill string matches a key in the mapping dictionary (case-insensitive), THE Normalizer SHALL replace it with the corresponding canonical value.
3. WHERE skill normalization is enabled and a skill string does not match any key in the mapping dictionary, THE Normalizer SHALL preserve the original skill string unchanged.
4. WHERE skill normalization is enabled, THE Normalizer SHALL deduplicate the `skills` list after normalization, preserving the first occurrence of each canonical skill.

---

### Requirement 7: Optional Streamlit UI

**WHERE** the Streamlit UI is enabled, **THE** Pipeline **SHALL** expose an interactive web interface for uploading input files and viewing the Dataset.

#### Acceptance Criteria

1. WHERE the Streamlit UI is enabled, THE Pipeline SHALL allow a user to upload a plain text file as the input source in place of `data/raw_jobs.txt`.
2. WHERE the Streamlit UI is enabled and a file is uploaded, THE Pipeline SHALL display the extracted Dataset as an interactive table in the browser.
3. WHERE the Streamlit UI is enabled, THE Pipeline SHALL provide a download button that exports the Dataset as a CSV file.
4. WHERE the Streamlit UI is enabled and an extraction error occurs, THE Pipeline SHALL display the error message inline without crashing the interface.

---

### Requirement 8: Optional Analytics

**WHERE** analytics are enabled, **THE** Pipeline **SHALL** compute and display summary statistics over the Dataset.

#### Acceptance Criteria

1. WHERE analytics are enabled, THE Pipeline SHALL compute the frequency count of each unique skill across all Structured_Records and display the top 10 skills.
2. WHERE analytics are enabled, THE Pipeline SHALL compute the frequency count of each unique `role` value and display the results sorted by descending frequency.
3. WHERE analytics are enabled and at least one Structured_Record contains a non-null numeric `salary` value, THE Pipeline SHALL compute and display the minimum, maximum, and median salary.
4. WHERE analytics are enabled and no Structured_Record contains a parseable numeric salary, THE Pipeline SHALL display a message stating that salary data is insufficient for analysis.
