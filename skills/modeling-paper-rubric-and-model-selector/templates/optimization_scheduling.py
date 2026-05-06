from __future__ import annotations

from pathlib import Path

import itertools
import pandas as pd


ROOT = Path.cwd()
OUT_DIR = ROOT / "paper_output" / "experiments" / "optimization_scheduling"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # Replace this demo data with problem-specific costs, benefits, and resource use.
    items = pd.DataFrame(
        {
            "方案": ["A", "B", "C", "D"],
            "收益": [18, 26, 35, 40],
            "成本": [5, 9, 12, 15],
            "资源": [2, 4, 5, 7],
        }
    )
    budget = 25
    capacity = 12

    best = None
    rows = []
    for mask in itertools.product([0, 1], repeat=len(items)):
        selected = items[list(mask) == pd.Series(mask).astype(bool)]
        benefit = float((items["收益"] * mask).sum())
        cost = float((items["成本"] * mask).sum())
        resource = float((items["资源"] * mask).sum())
        feasible = cost <= budget and resource <= capacity
        row = {"选择": "".join(map(str, mask)), "收益": benefit, "成本": cost, "资源": resource, "可行": feasible}
        rows.append(row)
        if feasible and (best is None or benefit > best["收益"]):
            best = row

    pd.DataFrame(rows).to_csv(OUT_DIR / "enumeration_results.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([best or {}]).to_csv(OUT_DIR / "best_solution.csv", index=False, encoding="utf-8-sig")
    print(f"Saved optimization baseline outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
