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
- **按十二维度检查** — 架构、质量、体验、鲁棒性、可维护性全覆盖
- **改动要可验证** — 优化前后对比，确认效果
- **自动修复优先** — 能自动修的不手动改

## ⚠️ 执行纪律（不可跳过）

- **Step 1 必须并行跑完两路**：左路（分析）和右路（调研：find-skills + 2个外部竞品 agent）都要完成，不能只跑左路就跳 Step 2
- **Step 2 和 Step 3 都有同行评审**：用户确认方案后必须辩论验证，门禁通过后必须辩论最终审查
- **每步完成后对照清单打勾**：所有 `- [ ]` 都必须完成，缺任何一个都要回头补
- **不要因为"用户已经确认"或"门禁已过"就跳过辩论**：同行评审是质量保障的最后一道防线
- **右路调研不是可选的**：竞品调研提供优化方向参考，没有调研的方案是闭门造车

---

## 工作流导航

```
用户输入 → 判断场景 → 进入对应流程

Step 0：确认工作区 → steps/step0-workspace.md
  ✓ 确认目标skill路径  ✓ 询问是否自动配置全部权限  ✓ 检测优化历史

  ↓
Step 1：分析 + 调研（并行） → steps/step1-analyze.md
  左路：✓ analyze_skill.py  ✓ LLM内容评估  ✓ 十二维度检查
  右路：✓ find-skills搜同类skill ✓ 2个agent外部竞品调研  ✓ 竞品矩阵  ✓ 迁移分析  ✓ 体验优化
  合并：✓ 生成完整报告

Step 2：方案确认 → steps/step2-confirm.md
  ✓ 展示报告（问题+调研）  ✓ 给出修改计划  ✓ 用户确认修改范围
  ✓ 同行评审（正反辩论验证方案）

Step 3：执行修改 + 评分验证 → steps/step3-optimize.md
  ✓ dry-run预览  ✓ 执行修复  ✓ 补充缺失组件  ✓ 前后对比
  ✓ 质量门禁评分  ✓ 同行评审（正反辩论最终审查）
  ✓ PASS→交付 / FAIL→回路
```

---

## 全局规则

### 分析维度（十二维度检查）

| 维度 | 检查内容 |
|---|---|
| 模块化分层 | SKILL.md 是否过长？详细内容是否拆到了 steps/？ |
| 内联 checklist | step 文件顶部是否有 ✓ 执行清单？ |
| 熔断机制 | 子 agent 调用失败是否有降级路径？质量不达标是否有熔断？ |
| 确认前置 | 是否先展示结果再检查？ |
| 语义边界 | 触发条件是否基于语义而非机械计数？ |
| 多维审查 | 评分是否覆盖质量和风险两个层面？ |
| 用户选择 | 策略性决策是否交给了用户？ |
| Token 效率 | 参考资料是否是速查表格式？是否有跨文件重复？ |
| 交付格式 | 输出是否清晰易读？ |
| 工作区权限 | 是否有权限配置流程？用户能否一键配好权限？ |
| README | 是否存在？描述是否与实际项目同步？（结构+LLM 双层检查） |
| 经验积累 | 是否有学习/复用机制？是否越用越聪明？ |

### 质量门禁（默认条件）

```
SKILL.md ≤ 200 行
总分 ≥ 75（结构60 + 内容40）
严重问题 = 0
高危问题 ≤ 2
step 文件全部有 checklist
step 文件全部有 frontmatter
```

可通过 `--config gate.json` 自定义。

### 输出规则

- 分析报告用 markdown 表格
- 问题按严重程度排序（架构 > 质量 > 体验）
- 优化建议必须可执行（不是"建议改进"而是"把 X 改成 Y"）
- 优化后展示前后对比

### 工作区权限规则

设计新 skill 时，必须在 SKILL.md 中内置工作区权限配置流程：
- 确认工作区后，询问用户是否自动配置所需工具的权限
- 用户选"是" → 读取 `.claude/settings.json`，合并写入 `permissions.allow`（最小权限，只加实际用到的工具）
- 用户选"否" → 正常逐个确认
- 敏感操作（rm、git push 等）即使有权限也要二次确认
- 详见 `references/skill-design-playbook.md` 的"工作区权限自动配置"章节

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

- `steps/step0-workspace.md` — 确认工作区 + 权限配置
- `steps/step1-analyze.md` — 分析 + 调研（并行）
- `steps/step2-confirm.md` — 方案确认
- `steps/step3-optimize.md` — 执行修改 + 评分验证

### 参考资料（用到才读）

- `references/十二维度检查清单.md` — 逐项检查清单
- `references/LLM评估指南.md` — AI 内容质量评估方法
- `references/skill-design-playbook.md` — Skill 设计手册（文件组织、模板、权限配置、经验积累）
- `references/peer-review-debate.md` — 同行评审辩论模板（正反方 prompt + 评审流程 + 输出格式）
- `references/偏好学习指南.md` — 记录和应用用户修改习惯（未实现，设计文档）

---

## 触发条件

- "优化这个skill"、"改进这个skill"、"审查这个skill"
- "这个skill怎么样"、"看看这个skill有什么问题"
- "帮我检查skill"、"重构这个skill"
- 提供一个 skill 目录并要求分析或改进
