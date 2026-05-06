from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = SKILL_ROOT / "templates"
CATALOG_PATH = SKILL_ROOT / "references" / "experiment_templates.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def recommended_ids(root: Path) -> list[str]:
    data = load_json(root / "paper_output" / "plan" / "model_recommendations.json", {})
    ids = []
    for item in data.get("recommendations", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
    return ids


def parse_ids(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate runnable experiment templates for math-modeling tasks.")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="项目根目录，默认当前目录。")
    parser.add_argument("--types", default="", help="逗号分隔的模板类型；为空则读取模型推荐结果。")
    parser.add_argument("--all", action="store_true", help="生成全部模板。")
    args = parser.parse_args()

    root = args.project.resolve()
    catalog = load_json(CATALOG_PATH, {})
    if args.all:
        selected = list(catalog.keys())
    elif args.types:
        selected = parse_ids(args.types)
    else:
        selected = recommended_ids(root)
        if not selected:
            selected = ["forecasting_regression", "evaluation_ranking", "optimization_scheduling"]

    # Sensitivity analysis is useful for almost every CUMCM-style paper.
    if "sensitivity_analysis" not in selected:
        selected.append("sensitivity_analysis")

    out_dir = root / "paper_output" / "experiments"
    out_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for item in selected:
        meta = catalog.get(item)
        if not meta:
            continue
        src = TEMPLATES_DIR / meta["template"]
        dst = out_dir / meta["template"]
        shutil.copyfile(src, dst)
        copied.append({"type": item, "path": str(dst), "description": meta.get("description", "")})

    manifest = {"generated": copied}
    (out_dir / "experiment_templates_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 实验模板清单", ""]
    for item in copied:
        lines.append(f"- `{Path(item['path']).name}`：{item['description']}")
    (out_dir / "experiment_templates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ 已生成 {len(copied)} 个实验模板到：{out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
