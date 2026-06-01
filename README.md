# Skill Optimizer

分析和优化 Claude Code skills 的质量。检查架构合理性、内容质量、Token 效率，生成优化建议并自动执行改进。

核心理念：**先诊断再开药，改动要可验证，自动修复优先**。

## 功能特点

- **十二维度检查**：从架构、质量、体验、鲁棒性、可维护性等 12 个维度全面评估（含工作区权限、README同步度、经验积累）
- **双通道评分**：脚本结构分析 + LLM 内容评估，合并打分
- **质量门禁**：自动检查 SKILL.md 行数、总分、严重问题数等硬性指标
- **竞品调研**：2 个 agent 并行调研同类 skill，生成竞品矩阵和优化方向
- **自动修复**：能自动修的问题不手动改，dry-run 预览后执行
- **前后对比**：优化后自动对比原版本，确认效果
- **版本追踪**：自动保存优化历史，支持回滚

## 适用场景

- 用户想检查一个 skill 有没有问题
- 用户想优化已有 skill 的质量和效率
- 用户想对比两个版本的 skill
- 用户说"优化 skill"、"改进 skill"、"审查 skill"、"这个 skill 怎么样"

## 安装

本 skill 已安装在本地。如需重新安装：

```bash
git clone <repo-url> ~/.claude/skills/skill-optimizer
```

## 使用方式

```
帮我检查一下 ~/.claude/skills/auto-tuner 这个 skill 有什么问题
```

```
优化这个 skill，让它更高效
```

```
这个 skill 怎么样？有没有改进空间？
```

## 工作流程

```
Step 0：确认工作区（step0-workspace.md）
  ✓ 确认目标skill路径  ✓ 询问是否自动配置全部权限  ✓ 检测优化历史
  │
Step 1：分析 + 调研（并行）（step1-analyze.md）
  左路：✓ analyze_skill.py  ✓ LLM 内容评估  ✓ 十二维度检查
  右路：✓ find-skills搜同类skill ✓ 2个agent外部竞品调研  ✓ 竞品矩阵  ✓ 迁移分析  ✓ 体验优化
  合并：✓ 生成完整报告
  │
Step 2：方案确认（step2-confirm.md）
  ✓ 展示报告（问题 + 调研）  ✓ 给出修改计划  ✓ 用户确认修改范围
  ✓ 同行评审（正反辩论验证方案）
  │
Step 3：执行修改 + 评分验证（step3-optimize.md）
  ✓ dry-run 预览  ✓ 执行修复  ✓ 补充缺失组件  ✓ 前后对比
  ✓ 质量门禁评分  ✓ 同行评审  ✓ PASS → 交付 / FAIL → 回路
```

## 十二维度检查

| 维度 | 检查内容 |
|------|----------|
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
| README | 是否存在？描述是否与实际项目同步？ |
| 经验积累 | 是否有学习/复用机制？是否越用越聪明？ |

## 质量门禁

默认通过条件：

```
SKILL.md ≤ 200 行
总分 ≥ 75（结构60 + 内容40）
严重问题 = 0
高危问题 ≤ 2
step 文件全部有 checklist
step 文件全部有 frontmatter
```

可通过 `--config gate.json` 自定义。

## 文件结构

```
skill-optimizer/
├── SKILL.md                            ← 入口：核心原则 + 工作流导航 + 十二维度检查
├── steps/
│   ├── step0-workspace.md              ← 确认工作区 + 权限配置
│   ├── step1-analyze.md                ← 分析 + 调研（并行）
│   ├── step2-confirm.md                ← 方案确认
│   └── step3-optimize.md               ← 执行修改 + 评分验证
├── scripts/
│   ├── analyze_skill.py                ← 自动分析 skill 结构
│   ├── quality_gate.py                 ← 质量门禁检查
│   ├── fix_skill.py                    ← 自动修复问题
│   └── compare_versions.py             ← 版本对比
├── references/
│   ├── 十二维度检查清单.md                ← 逐项检查清单
│   ├── LLM评估指南.md                  ← AI 内容质量评估方法
│   ├── skill-design-playbook.md        ← Skill 设计手册
│   ├── peer-review-debate.md           ← 同行评审辩论模板
│   └── 偏好学习指南.md                  ← 用户修改习惯记录（设计文档）
├── evals/
│   └── evals.json                      ← 测试用例
└── .optimizer_history/                 ← 优化历史记录
```

## 工具说明

| 工具 | 用途 | 命令 |
|------|------|------|
| `analyze_skill.py` | 自动分析 skill 目录结构和内容 | `python scripts/analyze_skill.py <skill-path>` |
| `quality_gate.py` | 检查是否满足质量门禁 | `python scripts/quality_gate.py <skill-path>` |
| `fix_skill.py` | 自动修复发现的问题 | `python scripts/fix_skill.py <skill-path>` |
| `compare_versions.py` | 对比两次修复的差异 | `python scripts/compare_versions.py <skill-path>` |

## 与其他 skill 的关系

- **skill-creator**：从零创建新 skill
- **skill-optimizer**：分析和优化已有 skill
- **auto-tuner**：被优化的 skill 之一

## License

MIT
