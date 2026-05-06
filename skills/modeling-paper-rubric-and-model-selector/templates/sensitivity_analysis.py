from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
OUT_DIR = ROOT / "paper_output" / "experiments" / "sensitivity_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def objective(weight_a: float, weight_b: float) -> float:
    # Replace with the paper's actual objective or score formula.
    return 100 * weight_a + 80 * weight_b - 20 * abs(weight_a - weight_b)


def main() -> None:
    rows = []
    for delta in [-0.2, -0.1, 0, 0.1, 0.2]:
        weight_a = 0.5 + delta
        weight_b = 1 - weight_a
        rows.append({"delta": delta, "weight_a": weight_a, "weight_b": weight_b, "score": objective(weight_a, weight_b)})
    pd.DataFrame(rows).to_csv(OUT_DIR / "sensitivity_results.csv", index=False, encoding="utf-8-sig")
    print(f"Saved sensitivity outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
