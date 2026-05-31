#!/usr/bin/env python3
"""
Skill 架构分析脚本。

用法：
  analyze_skill.py <skill目录路径>

检查维度：
  1. SKILL.md 行数（建议 ≤200）
  2. step 文件是否有执行清单
  3. 参考资料格式（是否是速查表）
  4. 文件组织合理性
  5. frontmatter 完整性
  6. 跨文件重复检测
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any


def analyze_skill(skill_dir: str) -> dict:
    """分析 skill 目录，返回问题清单和评分。"""
    skill_path = Path(skill_dir)
    issues = []
    score = 100

    # ── 检查目录结构 ──────────────────────────────────────────────
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        issues.append({"severity": "critical", "category": "架构", "issue": "缺少 SKILL.md"})
        return {"score": 0, "issues": issues}

    # ── 检查 SKILL.md ─────────────────────────────────────────────
    content = skill_md.read_text(encoding="utf-8")
    lines = content.split("\n")
    line_count = len(lines)

    # 行数检查
    if line_count > 300:
        issues.append({"severity": "high", "category": "架构", "issue": f"SKILL.md 有 {line_count} 行（建议 ≤200），应拆到 steps/"})
        score -= 15
    elif line_count > 200:
        issues.append({"severity": "medium", "category": "架构", "issue": f"SKILL.md 有 {line_count} 行（建议 ≤200），考虑精简"})
        score -= 5

    # frontmatter 检查
    if not content.startswith("---"):
        issues.append({"severity": "high", "category": "架构", "issue": "SKILL.md 缺少 frontmatter"})
        score -= 10
    else:
        if "name:" not in content[:500]:
            issues.append({"severity": "high", "category": "架构", "issue": "frontmatter 缺少 name 字段"})
            score -= 5
        if "description:" not in content[:1000]:
            issues.append({"severity": "high", "category": "架构", "issue": "frontmatter 缺少 description 字段"})
            score -= 5

    # ── 检查 step 文件 ────────────────────────────────────────────
    steps_dir = skill_path / "steps"
    if steps_dir.exists():
        step_files = list(steps_dir.glob("step*.md"))
        if not step_files:
            issues.append({"severity": "medium", "category": "架构", "issue": "steps/ 目录为空"})
            score -= 5

        for step_file in step_files:
            step_content = step_file.read_text(encoding="utf-8")

            # 检查是否有执行清单
            if "- [ ]" not in step_content and "- [x]" not in step_content:
                issues.append({"severity": "medium", "category": "架构", "issue": f"{step_file.name} 缺少执行清单"})
                score -= 3

            # 检查是否有 frontmatter
            if not step_content.startswith("---"):
                issues.append({"severity": "low", "category": "架构", "issue": f"{step_file.name} 缺少 frontmatter"})
                score -= 1
    else:
        # 没有 steps 目录，检查 SKILL.md 是否太长
        if line_count > 100:
            issues.append({"severity": "medium", "category": "架构", "issue": "没有 steps/ 目录，且 SKILL.md 超过 100 行，建议拆分"})
            score -= 5

    # ── 检查 references ───────────────────────────────────────────
    refs_dir = skill_path / "references"
    if refs_dir.exists():
        ref_files = list(refs_dir.glob("*.md"))
        for ref_file in ref_files:
            ref_content = ref_file.read_text(encoding="utf-8")
            ref_lines = len(ref_content.split("\n"))

            # 检查是否是速查表格式（应有表格或列表）
            has_table = "|" in ref_content and "---" in ref_content
            has_list = "- " in ref_content
            has_toc = "何时读" in ref_content[:200] or "用途" in ref_content[:200]

            if not has_table and not has_list:
                issues.append({"severity": "low", "category": "Token效率", "issue": f"{ref_file.name} 可能不是速查表格式（缺少表格或列表）"})
                score -= 2

            if ref_lines > 300:
                issues.append({"severity": "medium", "category": "Token效率", "issue": f"{ref_file.name} 有 {ref_lines} 行（建议 ≤300），考虑精简"})
                score -= 3

    # ── 检查模板 ──────────────────────────────────────────────────
    templates_dir = skill_path / "assets" / "templates"
    if templates_dir.exists():
        template_files = list(templates_dir.glob("*"))
        if not template_files:
            issues.append({"severity": "low", "category": "架构", "issue": "assets/templates/ 目录为空"})
            score -= 2

    # ── 检查脚本 ──────────────────────────────────────────────────
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        script_files = list(scripts_dir.glob("*"))
        if not script_files:
            issues.append({"severity": "low", "category": "架构", "issue": "scripts/ 目录为空"})
            score -= 2

    # ── 检查范例 ──────────────────────────────────────────────────
    examples_dir = skill_path / "examples"
    if not examples_dir.exists():
        issues.append({"severity": "low", "category": "质量", "issue": "没有 examples/ 目录，建议提供示例"})
        score -= 3

    # ── 检查跨文件重复 ────────────────────────────────────────────
    all_files = list(skill_path.rglob("*.md"))
    file_contents = {}
    for f in all_files:
        try:
            file_contents[f.name] = f.read_text(encoding="utf-8")
        except Exception:
            pass

    # 简单的重复检测：检查是否有大段相同内容
    file_names = list(file_contents.keys())
    for i in range(len(file_names)):
        for j in range(i + 1, len(file_names)):
            content_i = file_contents[file_names[i]]
            content_j = file_contents[file_names[j]]

            # 检查是否有超过 200 字的相同段落
            lines_i = set(line.strip() for line in content_i.split("\n") if len(line.strip()) > 50)
            lines_j = set(line.strip() for line in content_j.split("\n") if len(line.strip()) > 50)
            common = lines_i & lines_j

            if len(common) > 3:
                issues.append({"severity": "medium", "category": "Token效率", "issue": f"{file_names[i]} 和 {file_names[j]} 有 {len(common)} 行重复内容"})
                score -= 5

    # ── 检查工作流导航 ────────────────────────────────────────────
    if "步骤" not in content and "step" not in content.lower() and "流程" not in content:
        issues.append({"severity": "medium", "category": "架构", "issue": "SKILL.md 缺少工作流导航"})
        score -= 5

    # ── 检查触发条件 ──────────────────────────────────────────────
    if "触发" not in content and "trigger" not in content.lower() and "何时" not in content:
        issues.append({"severity": "medium", "category": "质量", "issue": "SKILL.md 缺少触发条件说明"})
        score -= 5

    return {"score": max(score, 0), "issues": issues}


def format_report(result: dict) -> str:
    """格式化分析报告。"""
    lines = []
    score = result["score"]

    if score >= 90:
        grade = "A — 优秀"
    elif score >= 80:
        grade = "B — 良好"
    elif score >= 70:
        grade = "C — 可用，建议改进"
    elif score >= 60:
        grade = "D — 较弱，需要较多改进"
    else:
        grade = "F — 需要重构"

    lines.append(f"总分: {score}/100 — {grade}")
    lines.append("")

    # 按严重程度排序
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_issues = sorted(result["issues"], key=lambda x: severity_order.get(x["severity"], 99))

    severity_labels = {
        "critical": "[严重]",
        "high": "[高]",
        "medium": "[中]",
        "low": "[低]",
    }

    for issue in sorted_issues:
        severity = severity_labels.get(issue["severity"], "⚪")
        lines.append(f"  {severity} [{issue['category']}] {issue['issue']}")

    if not result["issues"]:
        lines.append("  未发现问题")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: analyze_skill.py <skill目录路径>")
        return 1

    skill_dir = sys.argv[1]
    if not os.path.isdir(skill_dir):
        print(f"[错误] 目录不存在: {skill_dir}")
        return 1

    result = analyze_skill(skill_dir)
    print(format_report(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
