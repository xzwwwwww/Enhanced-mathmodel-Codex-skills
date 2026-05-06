from __future__ import annotations

import shutil
import importlib.util
import subprocess
import sys
from pathlib import Path

from skill_paths import ensure_project_dirs, skill_script

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


def run_script(label: str, script: Path, root: Path, required: bool = True) -> int:
    print(f"=== {label} ===")
    result = subprocess.run([sys.executable, str(script)], cwd=str(root), check=False)
    if result.returncode == 0:
        return 0
    if required:
        print(f"❌ {label} 执行失败。")
        return result.returncode
    print(f"⚠️ {label} 未成功执行，流程继续。")
    return 0


def maybe_run_harvester(root: Path) -> None:
    data_config = root / "data_requirements.json"
    if not data_config.exists():
        print("   未检测到 data_requirements.json，跳过外部数据获取。")
        return
    missing = [name for name in ("requests", "pandas") if importlib.util.find_spec(name) is None]
    if missing:
        print("   外部数据获取依赖缺失：" + ", ".join(missing))
        print("   已保留 data_requirements.json，请补齐依赖后单独运行 authoritative-data-harvester。")
        return
    try:
        harvester_script = skill_script("authoritative-data-harvester", "scripts/run.py", root)
    except FileNotFoundError:
        print("   未检测到外部数据获取脚本，跳过。")
        return
    print("   正在检查外部数据源...")
    subprocess.run([sys.executable, str(harvester_script)], cwd=str(root), check=False)


def maybe_parse_problem(root: Path) -> None:
    output_json = root / "paper_output" / "step1" / "question_map.json"
    if output_json.exists():
        print("=== Step-Pre 赛题解析 ===")
        print("   已存在赛题解析结果，跳过。")
        return
    try:
        parser_script = skill_script("problem-doc-model-selector", "scripts/parse_problem.py", root)
    except FileNotFoundError:
        print("=== Step-Pre 赛题解析 ===")
        print("   未检测到赛题解析脚本，跳过。")
        return
    print("=== Step-Pre 赛题解析 ===")
    subprocess.run(
        [sys.executable, str(parser_script), "--project", str(root), "--write-data-requirements"],
        cwd=str(root),
        check=False,
    )


def readable_problem_files(root: Path) -> list[Path]:
    problem_dir = root / "problem_files"
    if not problem_dir.exists():
        return []
    suffixes = {".txt", ".md", ".csv", ".tsv"}
    files = []
    for path in problem_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in suffixes and not path.name.startswith("~"):
            files.append(path)
    return sorted(files)


def maybe_recommend_models(root: Path) -> None:
    output_json = root / "paper_output" / "plan" / "model_recommendations.json"
    if output_json.exists():
        print("=== Step-A 模型推荐 ===")
        print("   已存在模型推荐结果，跳过。")
        return

    files = readable_problem_files(root)
    if not files:
        print("=== Step-A 模型推荐 ===")
        print("   未发现可直接读取的题面文本文件，使用通用建模路线。")
        text_arg = "数学建模 预测 评价 优化 验证 敏感性分析"
        file_args: list[str] = []
    else:
        text_arg = ""
        file_args = []
        for path in files[:5]:
            file_args.extend(["--file", str(path)])

    try:
        recommender = skill_script(
            "modeling-paper-rubric-and-model-selector",
            "scripts/recommend_models.py",
            root,
        )
    except FileNotFoundError:
        print("   未检测到模型推荐脚本，跳过。")
        return

    command = [
        sys.executable,
        str(recommender),
        "--output",
        str(root / "paper_output" / "plan" / "model_recommendations.md"),
        "--json-output",
        str(output_json),
    ]
    if text_arg:
        command.extend(["--text", text_arg])
    command.extend(file_args)
    subprocess.run(command, cwd=str(root), check=False)


def maybe_generate_experiment_templates(root: Path) -> None:
    manifest = root / "paper_output" / "experiments" / "experiment_templates_manifest.json"
    if manifest.exists():
        print("=== Step-B 实验模板生成 ===")
        print("   已存在实验模板清单，跳过。")
        return
    try:
        generator = skill_script(
            "modeling-paper-rubric-and-model-selector",
            "scripts/generate_experiment_templates.py",
            root,
        )
    except FileNotFoundError:
        print("=== Step-B 实验模板生成 ===")
        print("   未检测到实验模板生成脚本，跳过。")
        return
    print("=== Step-B 实验模板生成 ===")
    subprocess.run([sys.executable, str(generator), "--project", str(root)], cwd=str(root), check=False)


def copy_direct_docx(root: Path) -> bool:
    direct_docx = root / "paper_output" / "final_paper_direct.docx"
    final_docx = root / "paper_output" / "final_paper.docx"
    if not direct_docx.exists():
        return False
    try:
        shutil.copyfile(direct_docx, final_docx)
        print(f"✅ 已直接生成 Word 文档：{final_docx}")
        print("   注：此版本由脚本直接构建，公式保留为 LaTeX 源码。")
        return True
    except Exception as exc:
        print(f"⚠️ Word 文件复制失败：{exc}")
        return False


def try_pandoc_docx(root: Path) -> None:
    final_docx = root / "paper_output" / "final_paper.docx"
    md_path = root / "paper_output" / "final_paper.md"
    if final_docx.exists() or not md_path.exists():
        return
    try:
        subprocess.run(["pandoc", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ 未检测到 pandoc，跳过 Pandoc 兜底转换。")
        return

    reference_doc = root / "reference.docx"
    command = ["pandoc", str(md_path), "-o", str(final_docx)]
    if reference_doc.exists():
        command.append(f"--reference-doc={reference_doc}")
    subprocess.run(command, cwd=str(root), check=False)
    if final_docx.exists():
        print(f"✅ 已通过 Pandoc 生成 Word 文档：{final_docx}")
    else:
        print("⚠️ Word 转换失败：pandoc 执行后未生成文件。")


def main() -> int:
    root = ensure_project_dirs()

    maybe_parse_problem(root)

    print("=== Step-Optional 外部资源获取 ===")
    maybe_run_harvester(root)

    maybe_recommend_models(root)

    maybe_generate_experiment_templates(root)

    code = run_script(
        "Step-0 数据清洗与可视化",
        skill_script("data-cleaning-and-visualization", "scripts/run_pipeline.py", root),
        root,
        required=False,
    )
    if code != 0:
        return code

    calc_script = root / "step2_calc_results.py"
    if calc_script.exists():
        code = run_script("Step-1 自定义结果计算与出图", calc_script, root, required=False)
        if code != 0:
            return code
    else:
        print("ℹ️ 未找到 step2_calc_results.py，跳过自定义计算步骤。")

    code = run_script(
        "Step-2 质量审计与任务清单",
        skill_script("quality-assurance-auditor", "scripts/pipeline.py", root),
        root,
        required=True,
    )
    if code != 0:
        return code

    code = run_script(
        "Step-3 微单元离线生成",
        skill_script("paper-micro-unit-generator", "scripts/generate_all_offline.py", root),
        root,
        required=True,
    )
    if code != 0:
        return code

    code = run_script(
        "Step-4 合并",
        skill_script("paper-micro-unit-generator", "scripts/merge.py", root),
        root,
        required=True,
    )
    if code != 0:
        return code

    print("=== Step-5 转换为 Word (docx) ===")
    if not copy_direct_docx(root):
        try_pandoc_docx(root)

    print("✅ 全流程结束。最终产物：")
    print("   - Markdown: paper_output/final_paper.md")
    if (root / "paper_output" / "final_paper.docx").exists():
        print("   - Word:     paper_output/final_paper.docx")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
