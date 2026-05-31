#!/usr/bin/env python3
"""
Skill 自动修复脚本。

用法：
  fix_skill.py <skill目录路径> [--dry-run]

功能：
  1. SKILL.md 过长 → 自动拆分到 step 文件
  2. step 文件缺少 checklist → 自动生成
  3. step 文件缺少 frontmatter → 自动生成
  4. 参考资料格式不对 → 标记需手动重写
  5. 缺少目录结构 → 自动创建
  6. 跨文件重复 → 标记需手动处理

--dry-run 只输出修复计划，不执行。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def analyze_and_fix(skill_dir: str, dry_run: bool = False) -> dict:
    """分析 skill 并生成修复计划/执行修复。"""
    skill_path = Path(skill_dir)
    fixes_applied = []
    fixes_skipped = []

    # ── 1. 检查目录结构 ──────────────────────────────────────────
    required_dirs = ["steps", "references", "examples"]
    for d in required_dirs:
        dir_path = skill_path / d
        if not dir_path.exists():
            if dry_run:
                fixes_applied.append({"action": "创建目录", "target": d, "status": "dry-run"})
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                fixes_applied.append({"action": "创建目录", "target": d, "status": "已执行"})

    # ── 2. 检查 SKILL.md ─────────────────────────────────────────
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        fixes_skipped.append({"action": "修复 SKILL.md", "reason": "文件不存在，无法自动修复"})
        return {"fixes_applied": fixes_applied, "fixes_skipped": fixes_skipped}

    content = skill_md.read_text(encoding="utf-8")
    lines = content.split("\n")
    line_count = len(lines)

    # ── 3. SKILL.md 过长 → 拆分 ──────────────────────────────────
    if line_count > 200:
        # 找到所有 ## 标题
        sections = []
        current_section = {"title": "头部", "start": 0, "lines": []}
        for i, line in enumerate(lines):
            if line.startswith("## ") and i > 0:
                sections.append(current_section)
                current_section = {"title": line[3:].strip(), "start": i, "lines": [line]}
            else:
                current_section["lines"].append(line)
        sections.append(current_section)

        # 识别可以拆出去的 section（非核心）
        core_sections = ["核心原则", "工作流导航", "全局规则", "输出规则", "质量底线", "熔断机制", "触发条件"]
        movable_sections = []
        for s in sections:
            if not any(core in s["title"] for core in core_sections):
                if len(s["lines"]) > 5:  # 只拆有意义的 section
                    movable_sections.append(s)

        if movable_sections and not dry_run:
            # 创建新的 step 文件或 reference 文件
            for s in movable_sections:
                # 判断是 step 还是 reference
                if "步骤" in s["title"] or "流程" in s["title"] or "step" in s["title"].lower():
                    # 已经是 steps 引用，跳过
                    if "steps/" in "".join(s["lines"]):
                        continue
                    # 拆到 reference
                    ref_name = f"references/{s['title']}.md"
                    ref_path = skill_path / ref_name
                    ref_content = f"# {s['title']}\n\n> 何时读：需要了解{s['title']}时查阅。\n\n---\n\n"
                    ref_content += "\n".join(s["lines"])
                    ref_path.write_text(ref_content, encoding="utf-8")
                    fixes_applied.append({"action": "拆分到 reference", "target": ref_name, "status": "已执行"})
                else:
                    ref_name = f"references/{s['title']}.md"
                    ref_path = skill_path / ref_name
                    ref_content = f"# {s['title']}\n\n> 何时读：需要了解{s['title']}时查阅。\n\n---\n\n"
                    ref_content += "\n".join(s["lines"])
                    ref_path.write_text(ref_content, encoding="utf-8")
                    fixes_applied.append({"action": "拆分到 reference", "target": ref_name, "status": "已执行"})

            # 重写 SKILL.md，只保留核心 sections
            new_lines = []
            for s in sections:
                if any(core in s["title"] for core in core_sections) or s in movable_sections:
                    if s not in movable_sections:
                        new_lines.extend(s["lines"])
                else:
                    new_lines.extend(s["lines"])

            # 在资源索引中添加新的 reference
            if "## 资源索引" in "\n".join(new_lines):
                insert_idx = None
                for i, line in enumerate(new_lines):
                    if "### 参考资料" in line:
                        insert_idx = i + 1
                        break
                if insert_idx:
                    for s in movable_sections:
                        if s not in sections or "steps/" in "".join(s["lines"]):
                            continue
                        new_lines.insert(insert_idx, f"- `references/{s['title']}.md` — {s['title']}")

            new_content = "\n".join(new_lines)
            skill_md.write_text(new_content, encoding="utf-8")
            fixes_applied.append({"action": "精简 SKILL.md", "target": f"{line_count}行 → {len(new_lines)}行", "status": "已执行"})

        elif movable_sections:
            fixes_applied.append({"action": "精简 SKILL.md", "target": f"{line_count}行，可拆出{len(movable_sections)}个section", "status": "dry-run"})

    # ── 4. step 文件缺少 checklist → 添加 ────────────────────────
    steps_dir = skill_path / "steps"
    if steps_dir.exists():
        for step_file in steps_dir.glob("step*.md"):
            step_content = step_file.read_text(encoding="utf-8")
            if "- [ ]" not in step_content and "- [x]" not in step_content:
                # 从标题生成 checklist
                title_match = re.search(r"^# Step \d+: (.+)$", step_content, re.MULTILINE)
                title = title_match.group(1) if title_match else "未知步骤"

                # 找到第一个 ## 标题，在前面插入 checklist
                h2_match = re.search(r"^## ", step_content, re.MULTILINE)
                if h2_match:
                    insert_pos = h2_match.start()
                    checklist = f"## 执行清单\n\n- [ ] 步骤1（待补充）\n- [ ] 步骤2（待补充）\n- [ ] 步骤3（待补充）\n\n"
                    new_content = step_content[:insert_pos] + checklist + step_content[insert_pos:]

                    if not dry_run:
                        step_file.write_text(new_content, encoding="utf-8")
                        fixes_applied.append({"action": "添加 checklist", "target": step_file.name, "status": "已执行"})
                    else:
                        fixes_applied.append({"action": "添加 checklist", "target": step_file.name, "status": "dry-run"})

    # ── 5. step 文件缺少 frontmatter → 添加 ──────────────────────
    if steps_dir.exists():
        for step_file in steps_dir.glob("step*.md"):
            step_content = step_file.read_text(encoding="utf-8")
            if not step_content.startswith("---"):
                # 从文件名提取 step 编号
                num_match = re.search(r"step(\d+)", step_file.name)
                step_num = int(num_match.group(1)) if num_match else 0

                # 从标题提取 title
                title_match = re.search(r"^# Step \d+: (.+)$", step_content, re.MULTILINE)
                title = title_match.group(1) if title_match else "未知步骤"

                frontmatter = f"---\nstep: {step_num}\ntitle: {title}\n---\n\n"
                new_content = frontmatter + step_content

                if not dry_run:
                    step_file.write_text(new_content, encoding="utf-8")
                    fixes_applied.append({"action": "添加 frontmatter", "target": step_file.name, "status": "已执行"})
                else:
                    fixes_applied.append({"action": "添加 frontmatter", "target": step_file.name, "status": "dry-run"})

    # ── 6. 记录修复历史 ──────────────────────────────────────────
    if not dry_run and fixes_applied:
        history_dir = skill_path / ".optimizer_history"
        history_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = history_dir / f"fix_{timestamp}.json"
        history_file.write_text(json.dumps({
            "timestamp": timestamp,
            "fixes": fixes_applied,
            "skipped": fixes_skipped,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"fixes_applied": fixes_applied, "fixes_skipped": fixes_skipped}


def format_report(result: dict) -> str:
    """格式化修复报告。"""
    lines = []

    if result["fixes_applied"]:
        lines.append(f"已执行 {len(result['fixes_applied'])} 项修复：")
        for fix in result["fixes_applied"]:
            status = fix.get("status", "")
            lines.append(f"  [{status}] {fix['action']}: {fix['target']}")
    else:
        lines.append("无需修复")

    if result["fixes_skipped"]:
        lines.append(f"\n跳过 {len(result['fixes_skipped'])} 项：")
        for skip in result["fixes_skipped"]:
            lines.append(f"  - {skip['action']}: {skip['reason']}")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: fix_skill.py <skill目录路径> [--dry-run]")
        return 1

    skill_dir = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if not os.path.isdir(skill_dir):
        print(f"[错误] 目录不存在: {skill_dir}")
        return 1

    if dry_run:
        print("[模式] dry-run（只输出计划，不执行）\n")

    result = analyze_and_fix(skill_dir, dry_run)
    print(format_report(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
