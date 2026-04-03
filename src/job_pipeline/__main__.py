"""
Entry point for the job_pipeline package.

Run as:
    python -m job_pipeline
    python -m job_pipeline --input-path data/raw_jobs.txt --output-path data/out.csv
"""
import argparse
import logging
import os

from .models import PipelineConfig
from .pipeline import run_pipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="job_pipeline",
        description="Parse unstructured job descriptions into a structured CSV dataset.",
    )
    parser.add_argument(
        "--input-path",
        default=os.environ.get("INPUT_PATH", "data/raw_jobs.txt"),
        help="Path to the raw job descriptions file (env: INPUT_PATH)",
    )
    parser.add_argument(
        "--output-path",
        default=os.environ.get("OUTPUT_PATH", "data/structured_jobs.csv"),
        help="Path for the output CSV file (env: OUTPUT_PATH)",
    )
    parser.add_argument(
        "--openai-model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI model to use for extraction (env: OPENAI_MODEL)",
    )
    parser.add_argument(
        "--enable-normalization",
        action="store_true",
        default=os.environ.get("ENABLE_NORMALIZATION", "").lower() in ("1", "true", "yes"),
        help="Enable skill alias normalization (env: ENABLE_NORMALIZATION)",
    )
    parser.add_argument(
        "--enable-analytics",
        action="store_true",
        default=os.environ.get("ENABLE_ANALYTICS", "").lower() in ("1", "true", "yes"),
        help="Enable analytics summary output (env: ENABLE_ANALYTICS)",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        default=os.environ.get("SKIP_LLM", "").lower() in ("1", "true", "yes"),
        help="Skip OpenAI extraction; use regex/heuristic fallbacks only (env: SKIP_LLM)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    args = _parse_args()

    config = PipelineConfig(
        input_path=args.input_path,
        output_path=args.output_path,
        openai_model=args.openai_model,
        enable_normalization=args.enable_normalization,
        enable_analytics=args.enable_analytics,
        skip_llm=args.skip_llm,
    )

    run_pipeline(config)


if __name__ == "__main__":
    main()
