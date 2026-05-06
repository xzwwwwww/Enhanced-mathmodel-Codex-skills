from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PLACEHOLDER_PATTERNS = (
    "内容生成中",
    "论文题目缺失",
    "题目背景介绍",
    "具体问题描述",
    "关键词1",
    "此处插入",
    "TODO",
    "TBD",
    "待补充",
    "补充说明",
    "（缺失）",
    "(缺失)",
)


REQUIRED_SECTIONS = (
    "摘要",
    "问题重述",
    "模型假设",
    "符号",
    "数据",
    "模型",
    "结果",
    "检验",
    "结论",
    "参考文献",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def add_failure(report: dict[str, Any], item: str) -> None:
    report["blocking_failures"].append(item)


def add_warning(report: dict[str, Any], item: str) -> None:
    report["warnings"].append(item)


def project_root(start: Path | None) -> Path:
    return (start or Path.cwd()).resolve()


def problem_files(root: Path) -> list[Path]:
    problem_dir = root / "problem_files"
    if not problem_dir.exists():
        return []
    return [p for p in problem_dir.rglob("*") if p.is_file() and not p.name.startswith("~")]


def load_tasks(root: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    tasks_path = root / "paper_output" / "tasks.json"
    if not tasks_path.exists():
        add_failure(report, "缺少 paper_output/tasks.json，不能确认微单元任务清单。")
        return []
    try:
        tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    except Exception as exc:
        add_failure(report, f"tasks.json 读取失败：{exc}")
        return []
    if not isinstance(tasks, list):
        add_failure(report, "tasks.json 必须是数组。")
        return []
    return [task for task in tasks if isinstance(task, dict)]


def audit_problem_dir(root: Path, report: dict[str, Any]) -> None:
    files = problem_files(root)
    report["evidence"]["problem_file_count"] = len(files)
    if not files:
        add_failure(report, "problem_files/ 为空，缺少赛题或附件数据。")


def audit_tasks(root: Path, report: dict[str, Any]) -> None:
    tasks = load_tasks(root, report)
    if not tasks:
        return
    missing_units = []
    short_units = []
    for task in tasks:
        file_path = task.get("file_path")
        if not file_path:
            missing_units.append(str(task.get("id", "unknown")))
            continue
        unit_path = Path(file_path)
        if not unit_path.is_absolute():
            unit_path = root / unit_path
        if not unit_path.exists():
            missing_units.append(str(task.get("id", "unknown")))
            continue
        content = read_text(unit_path).strip()
        if len(content) < 40:
            short_units.append(str(task.get("id", "unknown")))

    report["evidence"]["task_count"] = len(tasks)
    report["evidence"]["missing_micro_units"] = missing_units[:20]
    report["evidence"]["short_micro_units"] = short_units[:20]
    if missing_units:
        add_failure(report, f"缺失 {len(missing_units)} 个微单元文件。")
    if len(short_units) > max(3, len(tasks) // 5):
        add_failure(report, f"过短微单元过多：{len(short_units)}/{len(tasks)}。")
    elif short_units:
        add_warning(report, f"存在 {len(short_units)} 个较短微单元，建议人工复核。")


def audit_final_text(root: Path, report: dict[str, Any]) -> str:
    final_path = root / "paper_output" / "final_paper.md"
    text = read_text(final_path)
    if not text:
        add_failure(report, "缺少 paper_output/final_paper.md。")
        return ""

    report["evidence"]["final_paper_chars"] = len(text)
    if len(text) < 3000:
        add_warning(report, "final_paper.md 篇幅偏短，可能不是完整竞赛论文。")

    placeholders = {p: text.count(p) for p in PLACEHOLDER_PATTERNS if p in text}
    report["evidence"]["placeholders"] = placeholders
    if placeholders:
        add_failure(report, "正文仍包含占位或模板文本：" + ", ".join(placeholders.keys()))

    missing_sections = [section for section in REQUIRED_SECTIONS if section not in text]
    report["evidence"]["missing_required_sections"] = missing_sections
    if missing_sections:
        add_failure(report, "缺少关键章节/关键词：" + "、".join(missing_sections))

    for token in ("问题一", "问题二", "问题三"):
        if token not in text:
            add_warning(report, f"未检测到 {token}，若题目少于三问可忽略。")

    if not re.search(r"基线|对照|baseline|Baseline", text):
        add_failure(report, "未检测到基线/对照实验描述。")
    if not re.search(r"验证|检验|敏感性|鲁棒|误差|回测|交叉验证", text):
        add_failure(report, "未检测到验证、检验、敏感性或误差分析。")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) >= 60]
    counts = Counter(paragraphs)
    repeated = [p[:80] for p, c in counts.items() if c > 1]
    report["evidence"]["repeated_paragraphs"] = repeated[:10]
    if repeated:
        add_failure(report, f"检测到 {len(repeated)} 段重复正文。")

    return text


def audit_data_outputs(root: Path, report: dict[str, Any]) -> None:
    cleaned = [p for p in (root / "paper_output" / "data_cleaned").glob("*.csv")]
    figures = [p for p in (root / "paper_output" / "figures").rglob("*.png")]
    recommendations = root / "paper_output" / "plan" / "model_recommendations.json"
    question_map = root / "paper_output" / "step1" / "question_map.json"
    experiment_manifest = root / "paper_output" / "experiments" / "experiment_templates_manifest.json"
    report["evidence"]["cleaned_data_count"] = len(cleaned)
    report["evidence"]["figure_count"] = len(figures)
    report["evidence"]["model_recommendations_exists"] = recommendations.exists()
    report["evidence"]["question_map_exists"] = question_map.exists()
    report["evidence"]["experiment_templates_exists"] = experiment_manifest.exists()
    if not question_map.exists():
        add_warning(report, "缺少赛题解析结果 paper_output/step1/question_map.json。")
    if not recommendations.exists():
        add_warning(report, "缺少模型推荐结果 paper_output/plan/model_recommendations.json。")
    if not experiment_manifest.exists():
        add_warning(report, "缺少实验模板清单 paper_output/experiments/experiment_templates_manifest.json。")
    if not cleaned:
        add_warning(report, "未检测到清洗后的数据文件；若题目包含附件数据，需补充数据清洗证据。")
    if not figures:
        add_warning(report, "未检测到自动生成图表；若论文需要数据分析图，需补充 paper_output/figures/。")


def audit_images(root: Path, text: str, report: dict[str, Any]) -> None:
    missing = []
    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        raw = match.group(1).strip()
        if raw.startswith(("http://", "https://")):
            continue
        image_path = Path(raw)
        candidates = [
            image_path,
            root / image_path,
            root / "paper_output" / image_path,
        ]
        if not any(path.exists() for path in candidates):
            missing.append(raw)
    report["evidence"]["missing_images"] = missing[:20]
    if missing:
        add_failure(report, f"正文引用了 {len(missing)} 个不存在的图片文件。")


def audit_refs_and_docx(root: Path, report: dict[str, Any], require_docx: bool) -> None:
    ref_path = root / "paper_output" / "ref_check.md"
    ref_text = read_text(ref_path)
    if not ref_text:
        add_warning(report, "缺少 paper_output/ref_check.md，无法检查图表/公式断链报告。")
    elif "断链：" in ref_text:
        add_failure(report, "ref_check.md 报告存在图表/公式引用断链。")

    docx_path = root / "paper_output" / "final_paper.docx"
    direct_docx = root / "paper_output" / "final_paper_direct.docx"
    report["evidence"]["final_paper_docx_exists"] = docx_path.exists() or direct_docx.exists()
    if require_docx and not (docx_path.exists() or direct_docx.exists()):
        add_failure(report, "缺少 final_paper.docx 或 final_paper_direct.docx。")


def write_reports(root: Path, report: dict[str, Any]) -> None:
    output_dir = root / "paper_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "qa_report.json"
    md_path = output_dir / "qa_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# QA 审计报告",
        "",
        f"- 状态：{report['status']}",
        f"- 分数：{report['score']}",
        "",
        "## 阻塞问题",
    ]
    if report["blocking_failures"]:
        lines.extend(f"- {item}" for item in report["blocking_failures"])
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("## 警告")
    if report["warnings"]:
        lines.extend(f"- {item}" for item in report["warnings"])
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("## 证据摘要")
    for key, value in report["evidence"].items():
        lines.append(f"- {key}: {value}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit math-modeling paper outputs.")
    parser.add_argument("--project", type=Path, default=None, help="项目根目录，默认当前目录。")
    parser.add_argument("--no-docx", action="store_true", help="不把 docx 缺失视为阻塞问题。")
    args = parser.parse_args()

    root = project_root(args.project)
    report: dict[str, Any] = {
        "status": "PASS",
        "score": 100,
        "blocking_failures": [],
        "warnings": [],
        "evidence": {"project_root": str(root)},
    }

    audit_problem_dir(root, report)
    audit_tasks(root, report)
    audit_data_outputs(root, report)
    text = audit_final_text(root, report)
    if text:
        audit_images(root, text, report)
    audit_refs_and_docx(root, report, require_docx=not args.no_docx)

    penalty = len(report["blocking_failures"]) * 12 + len(report["warnings"]) * 3
    report["score"] = max(0, 100 - penalty)
    report["status"] = "FAIL" if report["blocking_failures"] else "PASS"
    write_reports(root, report)

    print(f"QA 状态：{report['status']}，分数：{report['score']}")
    if report["blocking_failures"]:
        print("阻塞问题：")
        for item in report["blocking_failures"]:
            print(f"- {item}")
        return 1
    print("✅ QA 审计通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
