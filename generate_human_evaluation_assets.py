from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "human_evaluation"
SOURCE_FILE = ROOT / "fairxai_kaggle_processed.csv"
NUM_PAIRS = 30


def build_snippet(text: str, word_limit: int = 30) -> str:
    words = str(text).split()
    return " ".join(words[:word_limit])


def scale_system_score(raw_score: float) -> float:
    return round(1.0 + 4.0 * float(raw_score), 2)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(SOURCE_FILE)
    subset = df.head(NUM_PAIRS).copy()
    subset["pair_id"] = [f"P{idx:03d}" for idx in range(1, len(subset) + 1)]
    subset["job_role"] = subset["job_category"].astype(str)
    subset["resume_snippet"] = subset["clean_text"].apply(build_snippet)

    evaluator_template = subset[["pair_id", "job_role", "resume_snippet"]].copy()
    evaluator_template["skill"] = ""
    evaluator_template["experience"] = ""
    evaluator_template["overall"] = ""
    evaluator_template["notes"] = ""

    for idx in range(1, 4):
        evaluator_template.to_csv(OUTPUT_DIR / f"evaluator{idx}.csv", index=False)

    sample_filled = evaluator_template.copy()
    sample_values = [
        ("5", "4", "5", "Strong direct fit."),
        ("3", "2", "2", "Some overlap, but role focus differs."),
        ("4", "4", "4", "Relevant background overall."),
        ("2", "2", "2", "Weak alignment to the target role."),
        ("5", "5", "5", "Excellent shortlist candidate."),
    ]
    for row_idx, values in enumerate(sample_values):
        sample_filled.loc[row_idx, ["skill", "experience", "overall", "notes"]] = values
    sample_filled.to_csv(OUTPUT_DIR / "sample_filled_evaluator.csv", index=False)

    rubric = pd.DataFrame(
        [
            {"score": 1, "meaning": "Very poor match", "skill_alignment": "Skills are mostly unrelated to the role.", "experience_relevance": "Prior work is not relevant to the job.", "overall_match": "Resume should not be shortlisted."},
            {"score": 2, "meaning": "Weak match", "skill_alignment": "Some overlap, but major required skills are missing.", "experience_relevance": "Limited relevant experience.", "overall_match": "Unlikely fit without major training."},
            {"score": 3, "meaning": "Moderate match", "skill_alignment": "Several relevant skills are present.", "experience_relevance": "Partially relevant experience.", "overall_match": "Possible fit, but not a strong one."},
            {"score": 4, "meaning": "Strong match", "skill_alignment": "Most required skills are present.", "experience_relevance": "Clearly relevant experience.", "overall_match": "Good candidate for shortlist."},
            {"score": 5, "meaning": "Excellent match", "skill_alignment": "Skills align very closely with the role.", "experience_relevance": "Highly relevant experience.", "overall_match": "Excellent candidate for shortlist."},
        ]
    )
    rubric.to_csv(OUTPUT_DIR / "rubric.csv", index=False)

    system_scores = subset[["pair_id", "prediction_score"]].copy()
    system_scores["system_score"] = system_scores["prediction_score"].apply(scale_system_score)
    system_scores[["pair_id", "system_score"]].to_csv(OUTPUT_DIR / "system_scores.csv", index=False)

    print(f"Created assets in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
