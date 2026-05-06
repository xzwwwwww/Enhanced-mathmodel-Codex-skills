from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


RULES_PATH = Path(__file__).resolve().parents[1] / "references" / "model_rules.json"


def read_input(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.text:
        parts.append(args.text)
    if args.file:
        for path in args.file:
            p = Path(path)
            if p.exists():
                parts.append(p.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


def score_rule(text: str, rule: dict[str, Any]) -> tuple[int, list[str]]:
    hits: list[str] = []
    score = 0
    for trigger in rule.get("triggers", []):
        count = len(re.findall(re.escape(trigger), text, flags=re.IGNORECASE))
        if count:
            hits.append(trigger)
            score += count
    return score, hits


def recommend(text: str, top_k: int) -> dict[str, Any]:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    ranked = []
    for rule in rules.get("task_types", []):
        score, hits = score_rule(text, rule)
        if score:
            item = dict(rule)
            item["score"] = score
            item["matched_triggers"] = hits
            ranked.append(item)

    ranked.sort(key=lambda x: (-x["score"], x["label"]))
    if not ranked:
        ranked = [
            {
                "id": "general_modeling",
                "label": "通用数学建模",
                "score": 0,
                "matched_triggers": [],
                "baseline_models": ["线性模型", "规范化评价", "可解释优化模型"],
                "improved_models": ["树模型", "多目标优化", "敏感性分析"],
                "metrics": ["误差指标", "目标函数值", "稳定性"],
                "validation": ["基线对照", "敏感性分析", "边界情景检查"],
                "risks": ["任务类型不明确", "数据口径不明", "验证证据不足"],
            }
        ]

    return {
        "source": str(RULES_PATH),
        "recommendations": ranked[:top_k],
        "combination_patterns": rules.get("combination_patterns", []),
    }


def write_markdown(result: dict[str, Any], output_path: Path) -> None:
    lines = ["# 模型推荐报告", ""]
    for idx, item in enumerate(result["recommendations"], start=1):
        lines.extend(
            [
                f"## {idx}. {item['label']}",
                "",
                f"- 匹配词：{', '.join(item.get('matched_triggers', [])) or '无，使用通用路线'}",
                f"- 基线模型：{', '.join(item.get('baseline_models', []))}",
                f"- 改进模型：{', '.join(item.get('improved_models', []))}",
                f"- 验证指标：{', '.join(item.get('metrics', []))}",
                f"- 验证方式：{', '.join(item.get('validation', []))}",
                f"- 风险点：{', '.join(item.get('risks', []))}",
                "",
            ]
        )

    lines.append("## 可组合路线")
    for pattern in result.get("combination_patterns", []):
        lines.append(f"- {pattern['label']}：" + "；".join(pattern.get("workflow", [])))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend math-modeling routes from problem text.")
    parser.add_argument("--text", default="", help="题面或关键词文本。")
    parser.add_argument("--file", action="append", default=[], help="题面文本文件，可重复。")
    parser.add_argument("--top-k", type=int, default=3, help="输出前 K 个任务类型。")
    parser.add_argument("--output", type=Path, default=Path("paper_output/plan/model_recommendations.md"))
    parser.add_argument("--json-output", type=Path, default=Path("paper_output/plan/model_recommendations.json"))
    args = parser.parse_args()

    text = read_input(args)
    result = recommend(text, max(1, args.top_k))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result, args.output)
    print(f"✅ 模型推荐已生成：{args.output}")
    print(f"✅ JSON 结果已生成：{args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
