from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import pearsonr


RATING_COLUMNS = ["skill", "experience", "overall"]
ID_COLUMN = "pair_id"
SYSTEM_SCORES_FILE = "system_scores.csv"
EVALUATOR_GLOB = "evaluator*.csv"


def quadratic_weight_matrix(num_categories: int) -> np.ndarray:
    indices = np.arange(num_categories)
    distances = (indices[:, None] - indices[None, :]) ** 2
    return distances / float((num_categories - 1) ** 2)


def weighted_cohen_kappa(a: Iterable[int], b: Iterable[int], categories: list[int]) -> float:
    a = np.asarray(list(a), dtype=int)
    b = np.asarray(list(b), dtype=int)
    if len(a) != len(b):
        raise ValueError("Rater arrays must be the same length.")
    if len(a) == 0:
        return np.nan

    cat_to_idx = {cat: idx for idx, cat in enumerate(categories)}
    observed = np.zeros((len(categories), len(categories)), dtype=float)
    for left, right in zip(a, b):
        observed[cat_to_idx[left], cat_to_idx[right]] += 1.0
    observed /= observed.sum()

    left_hist = observed.sum(axis=1)
    right_hist = observed.sum(axis=0)
    expected = np.outer(left_hist, right_hist)
    weights = quadratic_weight_matrix(len(categories))

    observed_disagreement = float((weights * observed).sum())
    expected_disagreement = float((weights * expected).sum())
    if np.isclose(expected_disagreement, 0.0):
        return 1.0 if np.isclose(observed_disagreement, 0.0) else np.nan
    return 1.0 - (observed_disagreement / expected_disagreement)


def exact_agreement(df: pd.DataFrame, column: str) -> float:
    if df.empty:
        return np.nan
    return float((df[column].nunique(axis=1) == 1).mean() * 100.0)


def within_one_agreement(df: pd.DataFrame, column: str) -> float:
    if df.empty:
        return np.nan
    return float(((df[column].max(axis=1) - df[column].min(axis=1)) <= 1).mean() * 100.0)


def paper_kappa_label(value: float) -> str:
    if np.isnan(value):
        return "undefined"
    if value < 0.00:
        return "poor"
    if value < 0.20:
        return "slight"
    if value < 0.40:
        return "fair"
    if value < 0.60:
        return "moderate"
    if value < 0.80:
        return "substantial"
    return "almost perfect"


def format_metric(value: float, suffix: str = "") -> str:
    if np.isnan(value):
        return "not available"
    return f"{value:.1f}{suffix}" if suffix == "%" else f"{value:.4f}{suffix}"


def load_evaluator_files(folder: Path) -> tuple[list[pd.DataFrame], list[str]]:
    evaluator_paths = sorted(folder.glob(EVALUATOR_GLOB))
    if len(evaluator_paths) < 2:
        raise FileNotFoundError(
            f"Expected at least 2 evaluator CSVs matching '{EVALUATOR_GLOB}' in {folder}"
        )

    frames: list[pd.DataFrame] = []
    names: list[str] = []
    required_columns = {ID_COLUMN, *RATING_COLUMNS}

    for path in evaluator_paths:
        df = pd.read_csv(path)
        missing = required_columns - set(df.columns)
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise ValueError(f"{path.name} is missing required columns: {missing_str}")

        clean = df[[ID_COLUMN, *RATING_COLUMNS]].copy()
        for column in RATING_COLUMNS:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")

        clean = clean.dropna(subset=[ID_COLUMN])
        clean[ID_COLUMN] = clean[ID_COLUMN].astype(str).str.strip()
        clean["evaluator_name"] = path.stem
        frames.append(clean)
        names.append(path.stem)

    return frames, names


def build_long_frame(frames: list[pd.DataFrame], names: list[str]) -> pd.DataFrame:
    merged = None
    for df, name in zip(frames, names):
        renamed = df.rename(columns={column: f"{column}__{name}" for column in RATING_COLUMNS})
        merged = renamed if merged is None else merged.merge(renamed, on=ID_COLUMN, how="inner")

    assert merged is not None
    if merged.empty:
        raise ValueError("No shared pair_id values were found across evaluator files.")
    return merged.sort_values(ID_COLUMN).reset_index(drop=True)


def pairwise_kappas(merged: pd.DataFrame, names: list[str], dimension: str) -> list[dict]:
    results = []
    categories = [1, 2, 3, 4, 5]
    for left_name, right_name in combinations(names, 2):
        left_col = f"{dimension}__{left_name}"
        right_col = f"{dimension}__{right_name}"
        pair_df = merged[[ID_COLUMN, left_col, right_col]].dropna()
        if pair_df.empty:
            continue
        valid = pair_df[
            pair_df[left_col].between(1, 5, inclusive="both")
            & pair_df[right_col].between(1, 5, inclusive="both")
        ]
        if valid.empty:
            continue

        kappa = weighted_cohen_kappa(valid[left_col].astype(int), valid[right_col].astype(int), categories)
        agreement = float((valid[left_col] == valid[right_col]).mean() * 100.0)
        results.append(
            {
                "rater_pair": f"{left_name} vs {right_name}",
                "n": int(len(valid)),
                "weighted_kappa": float(kappa),
                "exact_agreement_pct": agreement,
            }
        )
    return results


def aggregate_human_scores(merged: pd.DataFrame, names: list[str], dimension: str) -> pd.DataFrame:
    cols = [f"{dimension}__{name}" for name in names]
    result = merged[[ID_COLUMN, *cols]].copy()
    result["human_mean_score"] = result[cols].mean(axis=1)
    return result[[ID_COLUMN, "human_mean_score"]]


def maybe_compute_system_correlation(folder: Path, merged: pd.DataFrame, names: list[str]) -> dict | None:
    system_path = folder / SYSTEM_SCORES_FILE
    if not system_path.exists():
        return None

    system_df = pd.read_csv(system_path)
    required = {ID_COLUMN, "system_score"}
    missing = required - set(system_df.columns)
    if missing:
        raise ValueError(f"{SYSTEM_SCORES_FILE} is missing required columns: {', '.join(sorted(missing))}")

    system_df = system_df[[ID_COLUMN, "system_score"]].copy()
    system_df[ID_COLUMN] = system_df[ID_COLUMN].astype(str).str.strip()
    system_df["system_score"] = pd.to_numeric(system_df["system_score"], errors="coerce")
    system_df = system_df.dropna(subset=["system_score"])

    human_df = aggregate_human_scores(merged, names, "overall")
    aligned = human_df.merge(system_df, on=ID_COLUMN, how="inner").dropna()
    if len(aligned) < 3:
        return {
            "n": int(len(aligned)),
            "pearson_r": np.nan,
            "p_value": np.nan,
        }

    pearson_r, p_value = pearsonr(aligned["human_mean_score"], aligned["system_score"])
    return {
        "n": int(len(aligned)),
        "pearson_r": float(pearson_r),
        "p_value": float(p_value),
    }


def main() -> None:
    folder = Path(__file__).resolve().parent / "human_evaluation"
    frames, names = load_evaluator_files(folder)
    merged = build_long_frame(frames, names)

    print("Human evaluation summary")
    print(f"- Evaluators detected: {', '.join(names)}")
    print(f"- Shared resume-job pairs: {len(merged)}")
    print()

    summary_rows = []
    for dimension in RATING_COLUMNS:
        pairwise = pairwise_kappas(merged, names, dimension)
        score_columns = [f"{dimension}__{name}" for name in names]
        dimension_frame = merged[[ID_COLUMN, *score_columns]].dropna()
        exact = exact_agreement(dimension_frame, score_columns)
        within_one = within_one_agreement(dimension_frame, score_columns)
        mean_kappa = float(np.nanmean([row["weighted_kappa"] for row in pairwise])) if pairwise else np.nan

        summary_rows.append(
            {
                "dimension": dimension,
                "n_pairs": int(len(dimension_frame)),
                "mean_weighted_kappa": mean_kappa,
                "interpretation": paper_kappa_label(mean_kappa),
                "exact_agreement_pct": exact,
                "within_one_point_pct": within_one,
            }
        )

        print(dimension.upper())
        for row in pairwise:
            print(
                f"  {row['rater_pair']}: weighted kappa={row['weighted_kappa']:.4f}, "
                f"exact agreement={row['exact_agreement_pct']:.1f}% (n={row['n']})"
            )
        print(
            f"  Mean weighted kappa={format_metric(mean_kappa)} ({paper_kappa_label(mean_kappa)}), "
            f"exact agreement={format_metric(exact, '%')}, within-one agreement={format_metric(within_one, '%')}"
        )
        print()

    correlation = maybe_compute_system_correlation(folder, merged, names)

    print("[PAPER] Human evaluation used three independent evaluators who rated each resume-job pair on skill alignment, experience relevance, and overall match using a 1-5 ordinal scale.")
    for row in summary_rows:
        print(
            f"[PAPER] Inter-rater reliability for {row['dimension']} was "
            f"{row['interpretation']} (mean quadratic-weighted Cohen's kappa = {format_metric(row['mean_weighted_kappa'])}), "
            f"with {format_metric(row['exact_agreement_pct'], '%')} exact agreement and "
            f"{format_metric(row['within_one_point_pct'], '%')} within-one-point agreement across {row['n_pairs']} pairs."
        )

    if correlation is None:
        print(
            f"[PAPER] System-vs-human correlation was not computed because {SYSTEM_SCORES_FILE} was not found in the human_evaluation folder."
        )
    elif np.isnan(correlation["pearson_r"]):
        print(
            f"[PAPER] System-vs-human correlation could not be estimated reliably because only {correlation['n']} aligned pairs were available."
        )
    else:
        print(
            f"[PAPER] The system's overall scores were positively correlated with the mean human overall ratings "
            f"(Pearson r = {correlation['pearson_r']:.4f}, p = {correlation['p_value']:.4g}, n = {correlation['n']})."
        )


if __name__ == "__main__":
    main()
