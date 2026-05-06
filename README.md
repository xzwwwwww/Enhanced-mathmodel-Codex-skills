# Liuhuan MathModel Codex Skills

增强版数学建模 Codex skills 套件。

## Skills

- `authoritative-data-harvester`: 外部权威数据获取配置与执行。
- `context-memory-keeper`: 项目记忆与阶段状态管理。
- `data-cleaning-and-visualization`: 附件数据清洗与 EDA 图表生成。
- `modeling-paper-rubric-and-model-selector`: 模型方法库、模型推荐和实验模板。
- `paper-micro-unit-generator`: 微单元论文生成与合并。
- `paper-workflow-orchestrator`: 一键总流程入口。
- `problem-doc-model-selector`: 赛题解析与问题映射。
- `quality-assurance-auditor`: 任务清单生成与最终 QA 审计。

## Global Codex Usage

本套件只使用全局 Codex skills 路径：

```bash
~/.codex/skills
```

项目目录只放赛题、附件和输出，不需要项目内 `.trae/skills` 或 `.codex/skills`。

一键启动：

```bash
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py
```

初始化项目目录：

```bash
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py --init-only
```

只做最终审计：

```bash
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py --audit-only
```

## Workflow

赛题解析 -> 外部数据需求检查 -> 模型推荐 -> 实验模板生成 -> 数据清洗/可视化 -> QA 任务清单 -> 微单元生成 -> 合并论文 -> Word -> 最终 QA。

## Install

把 `skills/*` 复制到：

```bash
~/.codex/skills/
```

重启 Codex 后生效。
