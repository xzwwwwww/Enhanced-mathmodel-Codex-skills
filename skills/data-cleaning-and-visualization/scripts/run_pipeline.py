from __future__ import annotations

import os
import importlib.util
import subprocess
import sys
from pathlib import Path


def missing_modules() -> list[str]:
    return [name for name in ("pandas", "numpy", "matplotlib", "seaborn") if importlib.util.find_spec(name) is None]


def main() -> int:
    root_dir = Path.cwd().resolve()
    os.chdir(root_dir)
    scripts_dir = Path(__file__).resolve().parent

    missing = missing_modules()
    if missing:
        print("⚠️ 数据清洗与可视化依赖缺失：" + ", ".join(missing))
        print("   已跳过该步骤；后续流程会继续，但数据证据和图表可能不足。")
        return 2

    print("🚀 === Step 1: 数据清洗 (Data Cleaning) ===")
    clean_script = scripts_dir / "clean_data.py"
    r1 = subprocess.run([sys.executable, str(clean_script)], cwd=str(root_dir), check=False)
    if r1.returncode != 0:
        print("❌ 数据清洗步骤失败，停止执行。")
        return r1.returncode

    print("\n🚀 === Step 2: 数据可视化 (Data Visualization) ===")
    viz_script = scripts_dir / "visualize_data.py"
    r2 = subprocess.run([sys.executable, str(viz_script)], cwd=str(root_dir), check=False)
    if r2.returncode != 0:
        print("❌ 数据可视化步骤失败。")
        return r2.returncode

    print("\n🎉 === 全流程执行完毕 (All Done) ===")
    print("请查看 paper_output/ 目录获取结果。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
