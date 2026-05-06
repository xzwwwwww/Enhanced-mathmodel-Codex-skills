from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path.cwd()
OUT_DIR = ROOT / "paper_output" / "experiments" / "monte_carlo_simulation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    rng = np.random.default_rng(42)
    n = 10000
    demand = rng.normal(loc=100, scale=15, size=n)
    capacity = rng.normal(loc=115, scale=10, size=n)
    shortage = np.maximum(demand - capacity, 0)
    result = pd.DataFrame({"demand": demand, "capacity": capacity, "shortage": shortage})
    summary = pd.DataFrame(
        [
            {
                "shortage_probability": float((shortage > 0).mean()),
                "expected_shortage": float(shortage.mean()),
                "p95_shortage": float(np.quantile(shortage, 0.95)),
            }
        ]
    )
    result.to_csv(OUT_DIR / "monte_carlo_samples.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(OUT_DIR / "monte_carlo_summary.csv", index=False, encoding="utf-8-sig")
    print(f"Saved Monte Carlo outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
