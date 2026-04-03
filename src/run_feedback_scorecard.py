"""CLI entry point for the interview feedback scorecard."""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from job_pipeline.feedback_scorecard import build_scorecards

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

parser = argparse.ArgumentParser(description="Build structured scorecards from raw interview feedback.")
parser.add_argument("--input-path", default="../data/interview_feedback.txt")
parser.add_argument("--output-path", default="../data/interview_scorecards.csv")
args = parser.parse_args()

results = build_scorecards(args.input_path, args.output_path)
print(f"\nDone. {len(results)} scorecards generated -> {args.output_path}")
