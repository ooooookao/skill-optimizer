#!/usr/bin/env python3
"""
Skill 架构分析脚本。

用法：
  analyze_skill.py <skill目录路径>

检查维度：
  1. SKILL.md 行数（建议 ≤200）
  2. frontmatter 完整性（name + description）
  3. step 文件执行清单
  4. step 文件 frontmatter
  5. 参考资料格式（是否是速查表）
  6. 目录完整性（templates/scripts/examples）
  7. README.md 存在性
  8. 跨文件重复检测
  9. 工作流导航
  10. 触发条件（有无）
  11. 强制拦截（Gate）
  12. 工作区权限配置
  13. 经验积累/学习机制
  14. 熔断机制
  15. 用户选择机制
  16. 安全边界（敏感信息 + 高副作用操作 + 外部依赖）
  17. 触发语义质量（description 是否精准、是否有中英文双语）
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
        issues.append({"severity": "critical", "category": "结构规范", "issue": "缺少 SKILL.md"})
        return {"score": 0, "issues": issues}

    # ── 检查 SKILL.md ─────────────────────────────────────────────
    content = skill_md.read_text(encoding="utf-8")
    lines = content.split("\n")
    line_count = len(lines)

    # 行数检查
    if line_count > 300:
        issues.append({"severity": "high", "category": "结构规范", "issue": f"SKILL.md 有 {line_count} 行（建议 ≤200），应拆到 steps/"})
        score -= 10
    elif line_count > 200:
        issues.append({"severity": "medium", "category": "结构规范", "issue": f"SKILL.md 有 {line_count} 行（建议 ≤200），考虑精简"})
        score -= 5

    # frontmatter 检查
    if not content.startswith("---"):
        issues.append({"severity": "high", "category": "结构规范", "issue": "SKILL.md 缺少 frontmatter"})
        score -= 10
    else:
        if "name:" not in content[:500]:
            issues.append({"severity": "high", "category": "结构规范", "issue": "frontmatter 缺少 name 字段"})
            score -= 5
        if "description:" not in content[:1000]:
            issues.append({"severity": "high", "category": "结构规范", "issue": "frontmatter 缺少 description 字段"})
            score -= 5

    # ── 检查 step 文件 ────────────────────────────────────────────
    steps_dir = skill_path / "steps"
    if steps_dir.exists():
        step_files = list(steps_dir.glob("step*.md"))
        if not step_files:
            issues.append({"severity": "medium", "category": "结构规范", "issue": "steps/ 目录为空"})
            score -= 5

        for step_file in step_files:
            step_content = step_file.read_text(encoding="utf-8")

            # 检查是否有执行清单
            if "- [ ]" not in step_content and "- [x]" not in step_content:
                issues.append({"severity": "medium", "category": "结构规范", "issue": f"{step_file.name} 缺少执行清单"})
                score -= 3

            # 检查是否有 frontmatter
            if not step_content.startswith("---"):
                issues.append({"severity": "low", "category": "结构规范", "issue": f"{step_file.name} 缺少 frontmatter"})
                score -= 1
    else:
        # 没有 steps 目录，检查 SKILL.md 是否太长
        if line_count > 100:
            issues.append({"severity": "medium", "category": "结构规范", "issue": "没有 steps/ 目录，且 SKILL.md 超过 100 行，建议拆分"})
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
            issues.append({"severity": "low", "category": "结构规范", "issue": "assets/templates/ 目录为空"})
            score -= 2

    # ── 检查脚本 ──────────────────────────────────────────────────
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        script_files = list(scripts_dir.glob("*"))
        if not script_files:
            issues.append({"severity": "low", "category": "结构规范", "issue": "scripts/ 目录为空"})
            score -= 2

    # ── 检查范例 ──────────────────────────────────────────────────
    examples_dir = skill_path / "examples"
    if not examples_dir.exists():
        issues.append({"severity": "low", "category": "结构规范", "issue": "没有 examples/ 目录，建议提供示例"})
        score -= 5

    # ── 检查 README ──────────────────────────────────────────────
    readme_path = skill_path / "README.md"
    if not readme_path.exists():
        issues.append({"severity": "medium", "category": "README", "issue": "缺少 README.md，其他用户难以了解此 skill 的用途和用法"})
        score -= 5
    else:
        readme_content = readme_path.read_text(encoding="utf-8")
        readme_lines = len(readme_content.split("\n"))
        if readme_lines < 5:
            issues.append({"severity": "low", "category": "README", "issue": "README.md 内容过少（<5行），建议补充功能说明和使用方式"})
            score -= 2
        # 内容准确性需 LLM 评估，此处只检查结构。详见 references/LLM评估指南.md

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

    # ── 检查子 agent 使用（复杂 skill） ──────────────────────────
    # 复杂 skill（≥5 步 或 提到并行/批处理）应使用子 agent 做上下文隔离和并行
    if steps_dir.exists():
        step_count = len(list(steps_dir.glob("step*.md")))
    else:
        step_count = 0

    content_lower_for_sa = content.lower()
    is_complex = step_count >= 5
    if not is_complex:
        complexity_keywords = ["并行", "parallel", "批量", "batch", "同时执行", "多个子"]
        if any(kw in content_lower_for_sa for kw in complexity_keywords):
            is_complex = True

    if is_complex:
        has_subagent = False
        subagent_keywords = ["子agent", "子 agent", "sub-agent", "subagent", "spawn",
                             "background=true", "并行执行", "并行提取", "子agent并行"]
        # 检查 SKILL.md
        if any(kw in content_lower_for_sa for kw in subagent_keywords):
            has_subagent = True
        # 检查 step 文件
        if not has_subagent and steps_dir.exists():
            for step_file in steps_dir.glob("step*.md"):
                step_content = step_file.read_text(encoding="utf-8").lower()
                if any(kw in step_content for kw in subagent_keywords):
                    has_subagent = True
                    break
        # 检查 references
        if not has_subagent:
            refs_dir_for_sa = skill_path / "references"
            if refs_dir_for_sa.exists():
                for ref_file in refs_dir_for_sa.glob("*.md"):
                    ref_content = ref_file.read_text(encoding="utf-8").lower()
                    if any(kw in ref_content for kw in subagent_keywords):
                        has_subagent = True
                        break

        if not has_subagent:
            issues.append({"severity": "low", "category": "Token效率",
                           "issue": f"复杂 skill（{step_count} 步）未使用子 agent，主 agent 上下文易膨胀"})
            score -= 2

    # ── 检查工作流导航 ────────────────────────────────────────────
    if "步骤" not in content and "step" not in content.lower() and "流程" not in content:
        issues.append({"severity": "medium", "category": "结构规范", "issue": "SKILL.md 缺少工作流导航"})
        score -= 5

    # ── 检查触发条件 ──────────────────────────────────────────────
    if "触发" not in content and "trigger" not in content.lower() and "何时" not in content:
        issues.append({"severity": "medium", "category": "语义边界", "issue": "SKILL.md 缺少触发条件说明"})
        score -= 5

    # ── 检查强制拦截（Gate） ─────────────────────────────────────
    has_gate = False
    gate_keywords = ["通过条件", "不可跳过", "⚠️", "Gate", "自检", "不能进入"]

    if steps_dir.exists():
        for step_file in steps_dir.glob("step*.md"):
            step_content = step_file.read_text(encoding="utf-8")
            if any(kw in step_content for kw in gate_keywords):
                has_gate = True
                break

    if not has_gate:
        issues.append({"severity": "low", "category": "结构规范", "issue": "step 文件缺少强制拦截（Gate），agent 可能跳步"})
        score -= 3

    # ── 检查工作区权限配置 ────────────────────────────────────────
    has_permission_config = False
    permission_keywords = ["settings.json", "permissions", "工作区权限", "权限配置", "permission"]

    # 检查 SKILL.md
    content_lower = content.lower()
    if any(kw in content_lower for kw in permission_keywords):
        has_permission_config = True

    # 检查 step 文件
    if not has_permission_config and steps_dir.exists():
        for step_file in steps_dir.glob("step*.md"):
            step_content = step_file.read_text(encoding="utf-8").lower()
            if any(kw in step_content for kw in permission_keywords):
                has_permission_config = True
                break

    # 检查 references 目录
    refs_dir_for_perm = skill_path / "references"
    if not has_permission_config and refs_dir_for_perm.exists():
        for ref_file in refs_dir_for_perm.glob("*.md"):
            ref_content = ref_file.read_text(encoding="utf-8").lower()
            if any(kw in ref_content for kw in permission_keywords):
                has_permission_config = True
                break

    if not has_permission_config:
        issues.append({"severity": "medium", "category": "工作区权限", "issue": "缺少工作区权限配置流程，用户需逐一确认权限弹窗"})
        score -= 5

    # ── 检查经验积累/学习机制 ─────────────────────────────────────
    has_learning = False
    learning_keywords = [
        "experience", "经验积累", "经验库", "历史记录", "历史追踪",
        "library.json", "库", "复用", "跨项目经验", "反馈循环",
        "越用越聪明", "跨项目复用", "通用库", "world-library",
        "optimizer_history", ".history", "经验迁移",
    ]

    # 检查 SKILL.md
    if any(kw in content_lower for kw in learning_keywords):
        has_learning = True

    # 检查 step 文件
    if not has_learning and steps_dir.exists():
        for step_file in steps_dir.glob("step*.md"):
            step_content = step_file.read_text(encoding="utf-8").lower()
            if any(kw in step_content for kw in learning_keywords):
                has_learning = True
                break

    # 检查 references 目录
    refs_dir_for_learn = skill_path / "references"
    if not has_learning and refs_dir_for_learn.exists():
        for ref_file in refs_dir_for_learn.glob("*.md"):
            ref_content = ref_file.read_text(encoding="utf-8").lower()
            if any(kw in ref_content for kw in learning_keywords):
                has_learning = True
                break

    # 检查是否存在经验/知识库文件
    if not has_learning:
        learning_paths = [
            skill_path / "assets" / "world-library.json",
            skill_path / "experience",
            skill_path / "references" / "experience.md",
        ]
        for lp in learning_paths:
            if lp.exists():
                has_learning = True
                break
        # 检查 assets 下是否有 library 类 json
        assets_dir = skill_path / "assets"
        if not has_learning and assets_dir.exists():
            for f in assets_dir.glob("*library*"):
                has_learning = True
                break
            for f in assets_dir.glob("*库*"):
                has_learning = True
                break

    if not has_learning:
        issues.append({"severity": "low", "category": "经验积累", "issue": "缺少经验积累机制，skill 无法越用越聪明"})
        score -= 3

    # ── 检查熔断机制 ─────────────────────────────────────────────
    has_circuit_breaker = False
    cb_keywords = ["熔断", "circuit", "降级", "放弃条件", "终止条件", "最大重试"]

    if any(kw in content_lower for kw in cb_keywords):
        has_circuit_breaker = True

    if not has_circuit_breaker and steps_dir.exists():
        for step_file in steps_dir.glob("step*.md"):
            step_content = step_file.read_text(encoding="utf-8").lower()
            if any(kw in step_content for kw in cb_keywords):
                has_circuit_breaker = True
                break

    if not has_circuit_breaker and refs_dir_for_learn.exists():
        for ref_file in refs_dir_for_learn.glob("*.md"):
            ref_content = ref_file.read_text(encoding="utf-8").lower()
            if any(kw in ref_content for kw in cb_keywords):
                has_circuit_breaker = True
                break

    if not has_circuit_breaker:
        issues.append({"severity": "medium", "category": "熔断机制", "issue": "缺少熔断机制，失败时可能无限重试"})
        score -= 5

    # ── 检查用户选择机制 ─────────────────────────────────────────
    has_user_choice = False
    uc_keywords = ["选项", "选择", "利弊", "用户确认", "用户决定", "让用户", "询问用户"]

    if any(kw in content_lower for kw in uc_keywords):
        has_user_choice = True

    if not has_user_choice and steps_dir.exists():
        for step_file in steps_dir.glob("step*.md"):
            step_content = step_file.read_text(encoding="utf-8").lower()
            if any(kw in step_content for kw in uc_keywords):
                has_user_choice = True
                break

    if not has_user_choice:
        issues.append({"severity": "medium", "category": "用户交互", "issue": "缺少用户选择机制，策略性决策未交给用户"})
        score -= 5

    # ── 检查安全边界（第 16 项）──────────────────────────────────────
    # 16a. 敏感信息泄露
    secret_patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', '疑似 OpenAI API Key'),
        (r'ghp_[a-zA-Z0-9]{36,}', '疑似 GitHub Personal Access Token'),
        (r'Bearer [a-zA-Z0-9_\-\.]{20,}', '疑似 Bearer Token'),
        (r'password\s*[:=]\s*["\'][^"\']{6,}', '疑似硬编码密码'),
        (r'api[_-]?key\s*[:=]\s*["\'][^"\']{10,}', '疑似硬编码 API Key'),
        (r'secret[_-]?key\s*[:=]\s*["\'][^"\']{10,}', '疑似硬编码 Secret Key'),
        (r'token\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{20,}', '疑似硬编码 Token'),
    ]
    all_md_files = list(skill_path.rglob("*.md"))
    for md_file in all_md_files:
        try:
            md_content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for pattern, desc in secret_patterns:
            if re.search(pattern, md_content, re.IGNORECASE):
                issues.append({"severity": "critical", "category": "安全边界", "issue": f"{md_file.name} 中发现{desc}"})
                score -= 15
                break  # 每个文件只报一次

    # 16b. 高副作用操作无确认提示
    danger_commands = [
        (r'rm\s+-rf', 'rm -rf'),
        (r'git\s+push\s+--force', 'git push --force'),
        (r'DROP\s+TABLE', 'DROP TABLE'),
        (r'DELETE\s+FROM', 'DELETE FROM'),
        (r'git\s+reset\s+--hard', 'git reset --hard'),
    ]
    confirm_keywords = ["确认", "confirm", "二次确认", "用户确认", "询问用户", "让用户", "⚠️"]
    for md_file in all_md_files:
        try:
            md_content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        md_lower = md_content.lower()
        for pattern, cmd_name in danger_commands:
            if re.search(pattern, md_content, re.IGNORECASE):
                # 检查同一文件中是否有确认提示
                if not any(kw in md_lower for kw in confirm_keywords):
                    issues.append({"severity": "high", "category": "安全边界", "issue": f"{md_file.name} 包含 '{cmd_name}' 但无确认提示"})
                    score -= 8

    # 16c. 外部依赖无安装命令
    dep_patterns = [
        (r'npx\s+skills\s+', 'npx skills'),
        (r'pip\s+install', 'pip install'),
        (r'npm\s+install', 'npm install'),
        (r'apt\s+install', 'apt install'),
        (r'brew\s+install', 'brew install'),
        (r'cargo\s+install', 'cargo install'),
    ]
    install_keywords = ["install", "安装", "setup", "配置", "前置", "依赖", "pip install", "npm install", "npx"]
    for md_file in all_md_files:
        try:
            md_content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        md_lower = md_content.lower()
        for pattern, dep_name in dep_patterns:
            if re.search(pattern, md_content, re.IGNORECASE):
                # 检查是否有安装说明（在同文件或 README 中）
                has_install = any(kw in md_lower for kw in install_keywords)
                if not has_install:
                    issues.append({"severity": "low", "category": "安全边界", "issue": f"{md_file.name} 使用了 '{dep_name}' 但未说明安装方式"})
                    score -= 2

    # ── 检查触发语义质量（第 17 项）────────────────────────────────
    if content.startswith("---"):
        fm_end = content.find("---", 3)
        if fm_end > 0:
            frontmatter = content[3:fm_end]
            # 17a. 检查 description 是否有具体触发关键词
            if "description:" in frontmatter:
                desc_match = re.search(r'description:\s*>?\s*\n?(.*?)(?:\n\w|\Z)', frontmatter, re.DOTALL)
                if not desc_match:
                    desc_match = re.search(r'description:\s*(.+)', frontmatter)
                if desc_match:
                    desc_text = desc_match.group(1).strip()
                    # 检查是否有触发关键词（引号中的具体短语）
                    has_specific_triggers = bool(re.search(r'["\'].*?["\']', desc_text))
                    # 检查是否有泛泛描述（只有抽象概念）
                    vague_words = ["分析", "优化", "检查", "生成", "处理", "管理", "创建"]
                    specific_words = ["当用户", "触发", "trigger", "关键词", "说"]
                    has_vague = any(w in desc_text for w in vague_words)
                    has_specific = any(w in desc_text for w in specific_words) or has_specific_triggers
                    if has_vague and not has_specific:
                        issues.append({"severity": "medium", "category": "触发语义质量", "issue": "description 只有泛泛描述，缺少具体触发关键词"})
                        score -= 3
                    # 17b. 检查是否有中英文双语触发
                    has_chinese = bool(re.search(r'[一-鿿]', desc_text))
                    has_english = bool(re.search(r'[a-zA-Z]{3,}', desc_text))
                    if has_chinese and not has_english:
                        issues.append({"severity": "low", "category": "触发语义质量", "issue": "触发条件只有中文，建议补充英文触发词"})
                        score -= 1

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
