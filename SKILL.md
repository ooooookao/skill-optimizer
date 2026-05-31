---
name: skill-optimizer
description: >-
  分析和优化 Claude Code skills 的质量。检查架构合理性、内容质量、Token 效率，生成优化建议并执行改进。
  当用户说"优化skill"、"改进skill"、"审查skill"、"这个skill怎么样"时触发。
  当用户提供一个 skill 目录并要求分析、改进、重构时也应触发。
  当用户说"看看这个skill有什么问题"、"帮我检查skill"时也应触发。
  英文触发："optimize skill"、"review skill"、"check skill quality"、"improve this skill"。
---

# Skill 优化器

## 核心原则

- **先诊断再开药** — 不要一上来就改，先搞清楚问题在哪
- **按九原则检查** — 架构、质量、体验、鲁棒性、可维护性全覆盖
- **改动要可验证** — 优化前后对比，确认效果
- **自动修复优先** — 能自动修的不手动改

---

## 工作流导航

```
用户输入 → 判断场景 → 进入对应流程

分析已有 skill → steps/step1-analyze.md
  ✓ 读取目录结构  ✓ 读取 SKILL.md  ✓ 检查架构  ✓ 生成问题清单  ✓ 展示给用户

双通道评分 + 门禁 → steps/step2-score.md
  ✓ 结构分析（脚本） ✓ LLM内容评估  ✓ 合并评分  ✓ 质量门禁  ✓ 展示报告

竞品调研（找优化方向） → steps/step3-research.md
  ✓ 确认范围  ✓ 2个agent并行调研  ✓ 竞品矩阵  ✓ 用户确认  ✓ 迁移分析  ✓ 体验优化  ✓ 整合报告  ✓ 优化方向

执行优化 → steps/step4-optimize.md
  ✓ 确认范围  ✓ dry-run预览  ✓ 执行修复  ✓ 前后对比  ✓ 门禁验证
```

---

## 全局规则

### 分析维度（九原则检查）

| 维度 | 检查内容 |
|---|---|
| 模块化分层 | SKILL.md 是否过长？详细内容是否拆到了 steps/？ |
| 内联 checklist | step 文件顶部是否有 ✓ 执行清单？ |
| 熔断机制 | 子 agent 调用失败是否有降级路径？质量不达标是否有熔断？ |
| 审查前置 | 是否先展示结果再检查？ |
| 语义边界 | 触发条件是否基于语义而非机械计数？ |
| 多维审查 | 评分是否覆盖质量和风险两个层面？ |
| 用户选择 | 策略性决策是否交给了用户？ |
| Token 效率 | 参考资料是否是速查表格式？是否有跨文件重复？ |
| 交付格式 | 输出是否清晰易读？ |

### 质量门禁（默认条件）

```
SKILL.md ≤ 200 行
总分 ≥ 80
严重问题 = 0
高危问题 ≤ 2
step 文件全部有 checklist
```

可通过 `--config gate.json` 自定义。

### 输出规则

- 分析报告用 markdown 表格
- 问题按严重程度排序（架构 > 质量 > 体验）
- 优化建议必须可执行（不是"建议改进"而是"把 X 改成 Y"）
- 优化后展示前后对比

---

## 工具

| 工具 | 用途 | 何时用 |
|---|---|---|
| `scripts/analyze_skill.py` | 自动分析 | 每次分析时 |
| `scripts/quality_gate.py` | 质量门禁 | 评分后、优化后 |
| `scripts/fix_skill.py` | 自动修复 | 确认优化后 |
| `scripts/compare_versions.py` | 版本对比 | 多次优化后 |

---

## 资源索引

### 步骤文件（执行到才读）

- `steps/step1-analyze.md` — 架构分析流程
- `steps/step2-score.md` — 双通道评分 + 质量门禁
- `steps/step3-research.md` — 竞品调研流程
- `steps/step4-optimize.md` — 执行优化流程

### 参考资料（用到才读）

- `references/九原则检查清单.md` — 逐项检查清单
- `references/LLM评估指南.md` — AI 内容质量评估方法
- `references/偏好学习指南.md` — 记录和应用用户修改习惯（未实现，设计文档）

---

## 触发条件

- "优化这个skill"、"改进这个skill"、"审查这个skill"
- "这个skill怎么样"、"看看这个skill有什么问题"
- "帮我检查skill"、"重构这个skill"
- 提供一个 skill 目录并要求分析或改进
