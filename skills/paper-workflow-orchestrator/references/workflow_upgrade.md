# 数学建模增强工作流

用途：当用户希望“更强的完整论文流水线”、一键生成、分阶段验收、或从开源 Agent 思路增强现有流程时读取。

## 增强版阶段

1. 赛题解析：调用 `problem-doc-model-selector`，输出 A/B/C/D 和外部数据需求。
2. 模型路线：调用 `modeling-paper-rubric-and-model-selector`，读取 `references/model_library.md`，形成基线 + 改进 + 验证。
3. 实验模板：调用 `generate_experiment_templates.py`，生成预测、评价、优化、聚类、敏感性或蒙特卡洛模板。
4. 数据准备：调用 `data-cleaning-and-visualization`，生成清洗数据、数据字典、EDA 图表。
5. 外部数据：若存在 `data_requirements.json` 且 `active=true`，调用 `authoritative-data-harvester`，并记录来源。
6. 阶段 QA：调用 `quality-assurance-auditor`，读取 `references/qa_checklist.md`，失败则修复后重审。
7. 微单元生成：调用 `paper-micro-unit-generator`，按任务清单生成正文片段。
8. 合并与 Word：生成 `final_paper.md` 和 `final_paper.docx`。
9. 最终 QA：检查题意覆盖、图表链、公式变量、参考文献、docx 是否存在。

## 增强版产物

- `paper_output/step1/`: 题意解析、模型路线、评分点对齐。
- `paper_output/plan/`: 论文大纲、实验计划、图表计划。
- `paper_output/experiments/`: 可运行实验模板和实验结果。
- `paper_output/data_cleaned/`: 清洗数据。
- `paper_output/figures/`: 所有论文图表。
- `paper_output/tasks.json`: 微单元任务清单。
- `paper_output/micro_units/`: 微单元正文。
- `paper_output/final_paper.md`: 合并稿。
- `paper_output/final_paper.docx`: 最终 Word。
- `paper_output/ref_check.md`: 引用与编号检查。
- `paper_output/qa_report.md`: 最终 QA 报告。

## 质量门禁

- 赛题解析未覆盖所有子问题：不得进入写作。
- `problem_files/` 为空：不得启动完整流程。
- `tasks.json` 不存在：不得生成微单元。
- 关键模型没有基线或验证指标：不得合并最终稿。
- `final_paper.docx` 不存在：不得宣称最终交付完成。

## 一键模式与分步模式

- 一键模式：用户说“生成论文/跑完全流程/一键完成”时，由 `paper-workflow-orchestrator` 统筹。
- 分步模式：用户只要求解析、清洗、建模、写作或审计时，只运行对应 skill，并把阶段产物写入 `paper_output/`。
- 两种模式都必须更新 `memoryskill.md`，记录当前阶段、关键结论、未解决风险。
