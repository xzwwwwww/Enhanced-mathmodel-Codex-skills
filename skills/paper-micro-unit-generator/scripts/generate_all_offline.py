from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path.cwd()
OUTPUT_DIR = BASE_DIR / "paper_output"
TASKS_FILE = OUTPUT_DIR / "tasks.json"
UNITS_DIR = OUTPUT_DIR / "micro_units"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_placeholders() -> dict[str, Any]:
    p = BASE_DIR / "step3_filled_placeholder.py"
    if not p.exists():
        return {}
    ns: dict[str, Any] = {}
    exec(p.read_text(encoding="utf-8"), ns)
    v = ns.get("PLACEHOLDER")
    return v if isinstance(v, dict) else {}


def first_model_plan() -> dict[str, Any]:
    plans = load_json(OUTPUT_DIR / "plan" / "model_recommendations.json", {})
    recommendations = plans.get("recommendations") if isinstance(plans, dict) else None
    if isinstance(recommendations, list) and recommendations:
        first = recommendations[0]
        if isinstance(first, dict):
            return first
    return {
        "label": "通用数学建模",
        "baseline_models": ["可解释基线模型"],
        "improved_models": ["改进模型"],
        "metrics": ["误差指标", "稳定性指标"],
        "validation": ["基线对照", "敏感性分析"],
        "risks": ["数据口径不明", "验证证据不足"],
    }


def data_summary() -> dict[str, Any]:
    cleaned = sorted((OUTPUT_DIR / "data_cleaned").glob("*.csv"))
    figures = sorted((OUTPUT_DIR / "figures").rglob("*.png"))
    return {
        "cleaned_count": len(cleaned),
        "figure_count": len(figures),
        "cleaned_names": [p.name for p in cleaned[:5]],
        "figure_names": [str(p.relative_to(BASE_DIR)) for p in figures[:5]],
    }


def text_list(items: list[Any], fallback: str) -> str:
    values = [str(item) for item in items if str(item).strip()]
    return "、".join(values) if values else fallback


def question_index(unit_id: str) -> str:
    match = re.search(r"MODEL(\d+)", unit_id)
    return match.group(1) if match else ""


def render_unit(task: dict[str, Any], ph: dict[str, Any], model: dict[str, Any], data: dict[str, Any]) -> str:
    section = str(task.get("section", ""))
    unit_id = str(task.get("id", ""))
    header = f"【{section}｜{unit_id}】\n"

    title = str(ph.get("论文题目", "数学建模问题研究"))
    model_label = str(model.get("label", "通用数学建模"))
    baselines = text_list(model.get("baseline_models", []), "可解释基线模型")
    improvements = text_list(model.get("improved_models", []), "改进模型")
    metrics = text_list(model.get("metrics", []), "误差与稳定性指标")
    validations = text_list(model.get("validation", []), "基线对照与敏感性分析")
    risks = text_list(model.get("risks", []), "数据口径与验证不足")
    cleaned_count = data.get("cleaned_count", 0)
    figure_count = data.get("figure_count", 0)

    if section == "摘要":
        lines = [
            f"本文围绕“{title}”展开研究，将题目要求拆解为可计算任务，并建立面向结果解释的数学模型。",
            f"针对核心任务，本文首先构建{baselines}作为基线，再引入{improvements}作为改进路线。",
            f"在数据处理方面，本文完成附件与外部数据的清洗、标准化与探索性分析，当前形成清洗数据 {cleaned_count} 个、候选图表 {figure_count} 张。",
            f"在模型检验方面，本文采用{metrics}评价结果，并通过{validations}验证模型稳定性与可信度。",
            f"研究结果表明，该路线能够形成“题意拆解、模型建立、求解验证、结论建议”的闭环，为问题求解提供可复现依据。关键词：数学建模；{model_label}；模型检验；敏感性分析",
        ]
        idx = max(1, min(len(lines), int(unit_id.split("-")[-1]) if "-" in unit_id else 1))
        return header + lines[idx - 1] + "\n"

    if section == "问题重述":
        lines = [
            f"题目要求围绕{title}给出定量分析与决策依据，其本质是把实际场景转化为输入、输出、约束和评价指标明确的数学任务。",
            "从数据条件看，附件数据与可能的外部公开数据共同构成模型输入；在建模前必须统一字段口径、单位、时间范围和缺失异常处理规则。",
            "从求解目标看，论文需要逐问给出可量化结论，并说明每个结论对应的模型、数据证据和验证方式。",
        ]
        idx = max(1, min(len(lines), int(unit_id.split("-")[-1]) if "-" in unit_id else 1))
        return header + lines[idx - 1] + "\n"

    if section == "模型假设":
        if unit_id.endswith("-1"):
            return header + "假设一：题目给出的附件数据具有代表性，经过缺失值、异常值与单位口径处理后可用于后续建模。该假设保证模型输入与赛题场景一致。\n假设二：短期内外部环境与关键参数保持相对稳定，模型在题目规定范围内外推有效，超出范围时需重新校准。\n"
        return header + "假设三：影响结果的主要因素已经由题面、附件数据或外部公开数据覆盖，未观测因素的影响通过误差项和敏感性分析体现。若敏感性分析显示结果对某变量高度依赖，应在结论中明确其风险。\n"

    if section == "符号说明":
        return (
            header
            + "| 符号 | 含义 | 单位/说明 |\n|---|---|---|\n"
            + "| x_i | 第 i 个样本或对象的特征向量 | 由数据字段定义 |\n"
            + "| y_i | 第 i 个样本的目标值或评价结果 | 按题目输出定义 |\n"
            + "| w_j | 第 j 个指标权重或模型参数 | 无量纲或按指标单位 |\n"
            + "| f(·) | 建立的数学模型或映射关系 | 由模型路线确定 |\n"
            + "| L | 损失函数或目标函数 | 越小/越大按问题定义 |\n"
            + "| S | 综合评价得分或方案收益 | 用于排序或决策 |\n"
        )

    if section == "数据预处理":
        if unit_id.endswith("-1"):
            return header + f"本文扫描 `problem_files/` 与 `crawled_data/` 中的数据文件，执行空行空列删除、数值列识别、缺失值填补与重复记录处理，清洗结果统一写入 `paper_output/data_cleaned/`，当前已形成 {cleaned_count} 个清洗数据文件。\n"
        if unit_id.endswith("-2"):
            return header + "对数值变量，本文采用分布图、箱线图和相关性热力图识别异常值、偏态分布与强相关变量；对分类变量，采用频数统计识别长尾类别和异常编码。\n"
        if unit_id.endswith("-3"):
            return header + f"为保证论文图表可追溯，所有可视化文件统一写入 `paper_output/figures/`，当前生成候选图表 {figure_count} 张。正文只引用该目录下的图表，避免图文断链。\n"
        return header + "预处理后的数据将作为模型求解和结果分析的唯一输入版本，原始附件保持不变；所有清洗规则在论文的数据说明与附录中同步记录，以保证复现性。\n"

    q_idx = question_index(unit_id)
    if q_idx:
        if unit_id.endswith("-1"):
            return header + f"问题{q_idx}首先被判定为“{model_label}”相关任务。本文选择{baselines}作为最小可用基线，原因是其结构清晰、参数含义明确，能够为后续改进模型提供对照。\n"
        if unit_id.endswith("-2"):
            return header + f"在基线基础上，本文引入{improvements}作为改进路线，重点处理非线性、约束耦合、噪声扰动或多指标权衡等基线模型难以覆盖的问题。\n"
        if unit_id.endswith("-3"):
            return header + "模型变量由题面要求和数据字段共同确定：输入变量来自清洗数据，输出变量对应题目要求的预测值、评价值、分类结果或优化方案，约束条件由题目边界和实际可行域共同给出。\n"
        if unit_id.endswith("-4"):
            return header + "求解流程包括数据输入、参数估计、目标函数计算、约束检查和结果输出五个环节。若采用启发式或迭代算法，应记录随机种子、参数设置和收敛条件。\n"
        if unit_id.endswith("-5"):
            return header + f"结果评价采用{metrics}，并将基线模型与改进模型放在同一数据口径下比较，避免因样本划分、指标定义或单位转换不同导致虚假提升。\n"
        if unit_id.endswith("-6"):
            return header + f"模型可靠性通过{validations}进行检验。若关键参数小幅扰动即导致结论反转，则需要在结论中降低确定性表述，并给出稳健区间或备选方案。\n"
        if unit_id.endswith("-7"):
            return header + f"本问的主要风险包括{risks}。为降低风险，本文在数据说明、模型假设、参数敏感性和结果解释中分别给出约束，保证模型不会脱离题意。\n"
        return header + f"综上，问题{q_idx}形成“基线模型—改进模型—验证分析—风险说明”的闭环，既满足可解释性，也为最终结论提供可复现证据。\n"

    if section == "结果分析":
        if unit_id.endswith("-1"):
            return header + "结果分析首先比较不同问题、不同模型和不同参数设定下的核心指标，确认主要结论是否稳定，并解释指标变化背后的实际含义。\n"
        if unit_id.endswith("-2"):
            return header + "对比实验用于说明改进模型相对基线的收益，若收益有限，则优先保留结构更简单、解释更清楚的模型作为论文主模型。\n"
        if unit_id.endswith("-3"):
            return header + "敏感性分析关注权重、参数、样本扰动和约束边界变化对结论的影响，用于识别最关键的不确定因素和风险来源。\n"
        if unit_id.endswith("-4"):
            return header + "图表解释遵循“先说明横纵轴和指标口径，再解释趋势和异常点，最后回到题目结论”的顺序，避免只展示图形而不回答问题。\n"
        return header + "综合各项结果，本文将每一问的输出与题目要求逐项对应，确保结论不是泛泛描述，而是能够直接服务于赛题决策或解释目标。\n"

    if section == "模型评价":
        if unit_id.endswith("-1"):
            return header + f"本文模型的优点在于保留{baselines}的可解释性，同时通过{improvements}增强对复杂关系和约束条件的刻画能力，适合在竞赛论文中形成清晰证据链。\n"
        if unit_id.endswith("-2"):
            return header + f"模型不足主要来自{risks}。这些不足不会否定主结论，但提示在数据扩充、参数校准和外部验证方面仍有改进空间。\n"
        return header + "模型具有一定推广性：只要能够重新定义输入变量、输出指标和约束条件，同一建模框架可迁移到相似的预测、评价、优化或仿真问题中。\n"

    if section == "结论":
        if unit_id.endswith("-1"):
            return header + f"针对题目各问，本文建立了以{model_label}为核心的建模路线，给出了基线模型、改进模型、评价指标和验证方案，形成可复现的求解流程。\n"
        return header + "最终建议是：在实际应用中优先采用经过验证且解释清楚的模型方案；当数据条件改善或约束变化时，可在本文框架下重新训练、校准或优化模型。\n"

    if section == "参考文献":
        return (
            header
            + "[1] 全国大学生数学建模竞赛相关赛题与附件数据。\n"
            + "[2] Hastie T, Tibshirani R, Friedman J. The Elements of Statistical Learning. Springer.\n"
            + "[3] Winston W L. Operations Research: Applications and Algorithms. Cengage Learning.\n"
            + "[4] Montgomery D C, Runger G C. Applied Statistics and Probability for Engineers. Wiley.\n"
        )

    if section == "附录":
        if unit_id.endswith("-1"):
            return header + "附录列出主要脚本入口：数据清洗与可视化、模型推荐、任务清单生成、微单元生成、全文合并和 QA 审计。所有脚本均以项目根目录为工作目录运行。\n"
        return header + "附录还应保留关键参数设置、随机种子、数据字段说明和额外图表，方便评审或复现实验时核对模型结果。\n"

    return header + f"本单元用于支撑{section}部分，围绕题意、数据、模型、结果或验证展开，并与全文的评分点对齐表保持一致。\n"


def main() -> int:
    if not TASKS_FILE.exists():
        print(f"❌ 未找到任务清单：{TASKS_FILE}")
        return 1

    tasks = load_json(TASKS_FILE, [])
    if not isinstance(tasks, list):
        print("❌ tasks.json 格式不正确")
        return 1

    ph = load_placeholders()
    model = first_model_plan()
    data = data_summary()
    UNITS_DIR.mkdir(parents=True, exist_ok=True)
    log = []

    for task in tasks:
        file_path = task.get("file_path") or str(UNITS_DIR / f"{task.get('id', 'unit')}.txt")
        fp = Path(str(file_path))
        if not fp.is_absolute():
            fp = BASE_DIR / fp
        text = render_unit(task, ph, model, data)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(text, encoding="utf-8")
        log.append({"id": task.get("id"), "len": len(text), "file": str(fp)})

    (OUTPUT_DIR / "generate_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已生成 {len(tasks)} 个微单元：{UNITS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
