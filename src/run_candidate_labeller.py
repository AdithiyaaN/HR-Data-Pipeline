"""CLI entry point for the candidate answer labeller."""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from job_pipeline.candidate_labeller import label_answers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

parser = argparse.ArgumentParser(description="Label candidate interview answers by quality and category.")
parser.add_argument("--input-path", default="../data/candidate_answers.txt")
parser.add_argument("--output-path", default="../data/labelled_answers.csv")
args = parser.parse_args()

results = label_answers(args.input_path, args.output_path)
print(f"\nDone. {len(results)} answers labelled → {args.output_path}")
