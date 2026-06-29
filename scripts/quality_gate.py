#!/usr/bin/env python3
"""
质量门禁脚本（四态判定）。

用法：
  quality_gate.py <skill目录路径> [--config gate.json] [--content-score N] [--waive]

四态判定：
  PASS     — 全部检查通过
  CONCERNS — 仅 low 级问题，无 critical/high
  BLOCK    — 有 critical 或 high 问题
  WAIVED   -- 用户主动豁免 BLOCK

返回 exit code 0=PASS/CONCERNS/WAIVED, 1=BLOCK。

默认门禁条件（可通过 --config 自定义）：
  - SKILL.md ≤ 200 行
  - 每个 step 文件有 checklist
  - 总分 ≥ 75（结构60 + 内容40）
  - 无严重问题
  - 高危问题 ≤ 2
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 复用 analyze_skill 的分析逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_skill import analyze_skill


DEFAULT_GATE = {
    "max_skill_md_lines": 200,
    "min_score": 75,
    "max_critical_issues": 0,
    "max_high_issues": 2,
    "require_step_checklists": True,
    "require_frontmatter": True,
}


def load_gate_config(config_path: str | None) -> dict:
    """加载门禁配置。"""
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_GATE


def check_gate(skill_dir: str, gate: dict, content_score: int | None = None, waive: bool = False) -> dict:
    """检查是否满足门禁条件（四态判定）。

    Args:
        content_score: LLM 内容评估分数（满分 40）。如果提供，门禁检查合并分数。
        waive: 用户主动豁免 BLOCK 状态。
    """
    result = analyze_skill(skill_dir)
    checks = []
    passed = True

    # 检查 SKILL.md 行数
    skill_md = Path(skill_dir) / "SKILL.md"
    if skill_md.exists():
        line_count = len(skill_md.read_text(encoding="utf-8").split("\n"))
        max_lines = gate.get("max_skill_md_lines", 200)
        check_passed = line_count <= max_lines
        checks.append({
            "name": "SKILL.md 行数",
            "condition": f"≤ {max_lines}",
            "actual": line_count,
            "passed": check_passed,
        })
        if not check_passed:
            passed = False

    # 计算总分：结构分（脚本满分100→映射到60）+ 内容分（满分40）
    raw_score = result["score"]
    structure_score = round(raw_score * 0.6)  # 映射到 60 分制
    if content_score is not None:
        total_score = structure_score + content_score
        score_label = f"{total_score}/100（结构{structure_score}/60+内容{content_score}/40，原始{raw_score}）"
    else:
        total_score = structure_score
        score_label = f"{total_score}/60（仅结构分，原始{raw_score}）"

    # 检查总分
    min_score = gate.get("min_score", 75)
    if content_score is not None:
        # 有内容分：总分满分 100，门禁要求 75
        score_passed = total_score >= min_score
        condition_label = f"≥ {min_score}"
    else:
        # 无内容分：结构分满分 60，门禁按比例缩放（75 * 0.6 = 45）
        min_structure_score = round(min_score * 0.6)
        score_passed = total_score >= min_structure_score
        condition_label = f"≥ {min_structure_score}（仅结构分）"
    checks.append({
        "name": "总分",
        "condition": condition_label,
        "actual": score_label,
        "passed": score_passed,
    })
    if not score_passed:
        passed = False

    # 检查严重问题数
    max_critical = gate.get("max_critical_issues", 0)
    critical_count = sum(1 for i in result["issues"] if i["severity"] == "critical")
    critical_passed = critical_count <= max_critical
    checks.append({
        "name": "严重问题数",
        "condition": f"≤ {max_critical}",
        "actual": critical_count,
        "passed": critical_passed,
    })
    if not critical_passed:
        passed = False

    # 检查高危问题数
    max_high = gate.get("max_high_issues", 2)
    high_count = sum(1 for i in result["issues"] if i["severity"] == "high")
    high_passed = high_count <= max_high
    checks.append({
        "name": "高危问题数",
        "condition": f"≤ {max_high}",
        "actual": high_count,
        "passed": high_passed,
    })
    if not high_passed:
        passed = False

    # 检查 step 文件 checklist
    if gate.get("require_step_checklists", True):
        steps_dir = Path(skill_dir) / "steps"
        if steps_dir.exists():
            step_files = list(steps_dir.glob("step*.md"))
            missing = []
            for sf in step_files:
                content = sf.read_text(encoding="utf-8")
                if "- [ ]" not in content and "- [x]" not in content:
                    missing.append(sf.name)
            checklist_passed = len(missing) == 0
            checks.append({
                "name": "step 文件 checklist",
                "condition": "全部有",
                "actual": f"{len(missing)} 个缺失" if missing else "全部有",
                "passed": checklist_passed,
            })
            if not checklist_passed:
                passed = False

    # 检查 step 文件 frontmatter
    if gate.get("require_frontmatter", True):
        steps_dir = Path(skill_dir) / "steps"
        if steps_dir.exists():
            step_files = list(steps_dir.glob("step*.md"))
            missing_fm = []
            for sf in step_files:
                content = sf.read_text(encoding="utf-8")
                if not content.startswith("---"):
                    missing_fm.append(sf.name)
            fm_passed = len(missing_fm) == 0
            checks.append({
                "name": "step 文件 frontmatter",
                "condition": "全部有",
                "actual": f"{len(missing_fm)} 个缺失" if missing_fm else "全部有",
                "passed": fm_passed,
            })
            if not fm_passed:
                passed = False

    max_score = 100 if content_score is not None else 60

    # 四态判定
    has_critical = any(i["severity"] == "critical" for i in result["issues"])
    has_high = any(i["severity"] == "high" for i in result["issues"])

    if passed:
        status = "PASS"
    elif has_critical or has_high:
        if waive:
            status = "WAIVED"
        else:
            status = "BLOCK"
    else:
        # 只有 low/medium 级问题
        status = "CONCERNS"

    return {
        "passed": passed,
        "status": status,
        "score": total_score,
        "max_score": max_score,
        "structure_score": structure_score,
        "checks": checks,
        "issues": result["issues"],
    }


def format_report(gate_result: dict) -> str:
    """格式化门禁报告（四态）。"""
    lines = []

    status = gate_result.get("status", "PASS" if gate_result["passed"] else "BLOCK")
    status_labels = {
        "PASS": "通过 [PASS]",
        "CONCERNS": "有警告 [CONCERNS]",
        "BLOCK": "阻塞 [BLOCK]",
        "WAIVED": "已豁免 [WAIVED]",
    }
    lines.append(f"门禁结果: {status_labels.get(status, status)}")

    max_score = gate_result.get("max_score", 100)
    lines.append(f"总分: {gate_result['score']}/{max_score}")
    lines.append("")

    for check in gate_result["checks"]:
        check_status = "[PASS]" if check["passed"] else "[FAIL]"
        lines.append(f"  {check_status} {check['name']}: {check['actual']}（要求 {check['condition']}）")

    # CONCERNS 时列出警告
    if status == "CONCERNS":
        lines.append("")
        lines.append("警告项（不阻塞，建议修复）：")
        for issue in gate_result.get("issues", []):
            if issue["severity"] in ("low", "medium"):
                lines.append(f"  - [{issue['category']}] {issue['issue']}")

    # BLOCK 时列出阻塞项
    if status == "BLOCK":
        lines.append("")
        lines.append("阻塞项（必须修复）：")
        for issue in gate_result.get("issues", []):
            if issue["severity"] in ("critical", "high"):
                lines.append(f"  - [{issue['category']}] {issue['issue']}")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: quality_gate.py <skill目录路径> [--config gate.json] [--content-score N] [--waive]")
        return 1

    skill_dir = sys.argv[1]
    config_path = None
    content_score = None
    waive = "--waive" in sys.argv

    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = sys.argv[idx + 1]

    if "--content-score" in sys.argv:
        idx = sys.argv.index("--content-score")
        if idx + 1 < len(sys.argv):
            content_score = int(sys.argv[idx + 1])

    if not os.path.isdir(skill_dir):
        print(f"[错误] 目录不存在: {skill_dir}")
        return 1

    gate = load_gate_config(config_path)
    result = check_gate(skill_dir, gate, content_score, waive=waive)
    print(format_report(result))

    # PASS/CONCERNS/WAIVED 返回 0，BLOCK 返回 1
    return 0 if result["status"] in ("PASS", "CONCERNS", "WAIVED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
