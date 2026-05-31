---
step: 1
title: 架构分析
---

# Step 1: 架构分析

## 执行清单

- [ ] 确认 skill 目录路径
- [ ] 读取目录结构
- [ ] 读取 SKILL.md（frontmatter + 全文）
- [ ] 运行分析脚本
- [ ] 手动检查关键问题
- [ ] 生成问题清单，展示给用户

---

## 详细操作

### 1. 确认 skill 目录

用户可能提供：
- 直接路径（如 `C:\Users\xxx\.claude\skills\my-skill`）
- skill 名称（需在 `.claude/skills/` 下查找）
- 粘贴 SKILL.md 内容（需推断目录）

### 2. 读取目录结构

列出 skill 目录下的所有文件，了解整体结构：

```
skill-name/
├── SKILL.md
├── steps/
├── references/
├── assets/templates/
├── examples/
└── scripts/
```

### 3. 运行分析脚本

```bash
python scripts/analyze_skill.py <skill目录路径>
```

脚本自动检查：
- SKILL.md 行数
- step 文件是否有执行清单
- 参考资料格式
- 跨文件重复
- frontmatter 完整性
- 工作流导航和触发条件

### 4. 手动补充检查

脚本检查不到的问题，需要手动确认：
- 九原则是否都覆盖了？
- 工作流是否清晰？
- 评分维度是否合理？
- 用户体验是否有明显问题？

### 5. 展示问题清单

用表格展示所有问题，按严重程度排序：

```
| 严重程度 | 类别 | 问题 |
|---|---|---|
| [严重] | 架构 | SKILL.md 有 350 行，应拆到 steps/ |
| [高] | 质量 | 缺少熔断机制 |
| [中] | Token效率 | references/xxx.md 不是速查表格式 |
| [低] | 体验 | 没有 examples/ 目录 |
```

**等用户确认后进入下一步。**
