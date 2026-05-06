from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path.cwd()
DATA_DIR = ROOT / "paper_output" / "data_cleaned"
OUT_DIR = ROOT / "paper_output" / "experiments" / "evaluation_ranking"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_first_dataset() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError("No cleaned CSV files found in paper_output/data_cleaned.")
    return pd.read_csv(files[0])


def minmax_normalize(values: pd.DataFrame) -> pd.DataFrame:
    denom = values.max() - values.min()
    denom = denom.replace(0, 1)
    return (values - values.min()) / denom


def entropy_weights(values: pd.DataFrame) -> pd.Series:
    positive = minmax_normalize(values).clip(lower=1e-12)
    p = positive.div(positive.sum(axis=0), axis=1).fillna(0)
    k = 1 / np.log(len(positive)) if len(positive) > 1 else 1
    entropy = -k * (p * np.log(p)).sum(axis=0)
    diversity = 1 - entropy
    if float(diversity.sum()) == 0:
        return pd.Series(np.ones(len(values.columns)) / len(values.columns), index=values.columns)
    return diversity / diversity.sum()


def topsis(values: pd.DataFrame, weights: pd.Series) -> pd.Series:
    norm = values / np.sqrt((values**2).sum(axis=0)).replace(0, 1)
    weighted = norm * weights
    best = weighted.max(axis=0)
    worst = weighted.min(axis=0)
    d_best = np.sqrt(((weighted - best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((weighted - worst) ** 2).sum(axis=1))
    return d_worst / (d_best + d_worst).replace(0, np.nan)


def main() -> None:
    df = load_first_dataset()
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        raise ValueError("Need numeric indicator columns for evaluation/ranking.")
    values = minmax_normalize(numeric)
    weights = entropy_weights(numeric)
    score = topsis(values, weights).fillna(0)
    result = df.copy()
    result["综合得分"] = score
    result["排名"] = result["综合得分"].rank(ascending=False, method="min").astype(int)
    result.sort_values("排名").to_csv(OUT_DIR / "topsis_ranking.csv", index=False, encoding="utf-8-sig")
    weights.rename("weight").to_csv(OUT_DIR / "entropy_weights.csv", encoding="utf-8-sig")
    print(f"Saved TOPSIS ranking outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
