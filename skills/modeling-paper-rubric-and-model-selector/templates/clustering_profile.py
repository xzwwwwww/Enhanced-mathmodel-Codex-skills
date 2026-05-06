from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path.cwd()
DATA_DIR = ROOT / "paper_output" / "data_cleaned"
OUT_DIR = ROOT / "paper_output" / "experiments" / "clustering_profile"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_first_dataset() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError("No cleaned CSV files found in paper_output/data_cleaned.")
    return pd.read_csv(files[0])


def kmeans(x: np.ndarray, k: int = 3, max_iter: int = 100) -> np.ndarray:
    rng = np.random.default_rng(42)
    if len(x) < k:
        k = max(1, len(x))
    centers = x[rng.choice(len(x), size=k, replace=False)]
    labels = np.zeros(len(x), dtype=int)
    for _ in range(max_iter):
        dist = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        new_labels = dist.argmin(axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for i in range(k):
            if (labels == i).any():
                centers[i] = x[labels == i].mean(axis=0)
    return labels


def main() -> None:
    df = load_first_dataset()
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        raise ValueError("Need at least two numeric columns for clustering.")
    x = (numeric - numeric.mean()) / numeric.std(ddof=0).replace(0, 1)
    labels = kmeans(x.to_numpy(dtype=float), k=3)
    result = df.copy()
    result["cluster"] = labels
    result.to_csv(OUT_DIR / "clustered_data.csv", index=False, encoding="utf-8-sig")
    result.groupby("cluster")[numeric.columns].mean().to_csv(OUT_DIR / "cluster_profile.csv", encoding="utf-8-sig")
    print(f"Saved clustering outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
