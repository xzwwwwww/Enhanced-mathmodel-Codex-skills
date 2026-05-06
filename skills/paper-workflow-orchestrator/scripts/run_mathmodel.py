from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from skill_paths import ensure_project_dirs, project_root, skill_script


OPTIONAL_MODULES = ("pandas", "numpy", "matplotlib", "seaborn", "docx", "requests")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def has_problem_files(root: Path) -> bool:
    problem_dir = root / "problem_files"
    return problem_dir.exists() and any(p for p in problem_dir.rglob("*") if p.is_file())


def run_step(label: str, script: Path, root: Path, required: bool = True) -> int:
    print(f"\n=== {label} ===")
    result = subprocess.run([sys.executable, str(script)], cwd=str(root), check=False)
    if result.returncode != 0:
        level = "❌" if required else "⚠️"
        print(f"{level} {label} 返回码：{result.returncode}")
        if required:
            return result.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the enhanced math-modeling skill workflow.")
    parser.add_argument("--project", type=Path, default=None, help="项目根目录，默认使用当前目录或父级标记目录。")
    parser.add_argument("--init-only", action="store_true", help="只初始化目录并检查依赖，不运行完整流程。")
    parser.add_argument("--audit-only", action="store_true", help="只运行最终 QA 审计。")
    parser.add_argument("--allow-empty-problem", action="store_true", help="允许 problem_files 为空时继续运行。")
    args = parser.parse_args()

    root = ensure_project_dirs(args.project or os.getcwd())
    os.chdir(root)

    print("=== MathModel Enhanced Runner ===")
    print(f"项目目录：{root}")
    missing = [name for name in OPTIONAL_MODULES if not module_available(name)]
    if missing:
        print("⚠️ 可选依赖缺失：" + ", ".join(missing))
        print("   相关步骤可能降级或失败，请按项目环境安装后重跑。")
    else:
        print("✅ 常用依赖检查通过")

    if args.init_only:
        print("✅ 已初始化 problem_files/、crawled_data/、paper_output/")
        return 0

    if not args.allow_empty_problem and not has_problem_files(root):
        print("❌ problem_files/ 为空。请先把赛题 PDF/Word 和附件数据放进去。")
        return 1

    audit_script = skill_script("quality-assurance-auditor", "scripts/audit_paper.py", root)
    if args.audit_only:
        return run_step("最终 QA 审计", audit_script, root, required=True)

    run_all_script = skill_script("paper-workflow-orchestrator", "scripts/run_all.py", root)
    code = run_step("增强一键全流程", run_all_script, root, required=True)
    if code != 0:
        return code

    return run_step("最终 QA 审计", audit_script, root, required=True)


if __name__ == "__main__":
    raise SystemExit(main())
