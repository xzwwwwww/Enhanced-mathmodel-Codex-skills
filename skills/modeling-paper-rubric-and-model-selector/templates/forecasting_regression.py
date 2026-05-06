from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path.cwd()
DATA_DIR = ROOT / "paper_output" / "data_cleaned"
OUT_DIR = ROOT / "paper_output" / "experiments" / "forecasting_regression"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_first_dataset() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError("No cleaned CSV files found in paper_output/data_cleaned.")
    return pd.read_csv(files[0])


def main() -> None:
    df = load_first_dataset()
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        raise ValueError("Need at least two numeric columns: features and target.")

    target = numeric.columns[-1]
    features = [c for c in numeric.columns if c != target]
    x = numeric[features].to_numpy(dtype=float)
    y = numeric[target].to_numpy(dtype=float)
    x_design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(x_design, y, rcond=None)
    pred = x_design @ coef

    rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
    mae = float(np.mean(np.abs(y - pred)))
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0

    result = pd.DataFrame({"actual": y, "predicted": pred, "residual": y - pred})
    result.to_csv(OUT_DIR / "baseline_linear_regression_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [{"target": target, "features": ",".join(features), "rmse": rmse, "mae": mae, "r2": r2}]
    ).to_csv(OUT_DIR / "metrics.csv", index=False, encoding="utf-8-sig")
    print(f"Saved forecasting baseline outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
