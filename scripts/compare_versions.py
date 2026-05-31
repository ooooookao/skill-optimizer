#!/usr/bin/env python3
"""
版本对比脚本。

用法：
  compare_versions.py <skill目录路径>

读取 .optimizer_history/ 中的历史记录，对比最近两次分析的结果。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def load_history(skill_dir: str) -> list[dict]:
    """加载历史记录。"""
    history_dir = Path(skill_dir) / ".optimizer_history"
    if not history_dir.exists():
        return []

    records = []
    for f in sorted(history_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_file"] = f.name
            records.append(data)
        except Exception:
            pass

    return records


def compare(skill_dir: str) -> dict:
    """对比最近两次分析结果。"""
    records = load_history(skill_dir)

    if len(records) < 2:
        return {"error": "历史记录不足，需要至少两次分析才能对比"}

    prev = records[-2]
    curr = records[-1]

    prev_fixes = len(prev.get("fixes", []))
    curr_fixes = len(curr.get("fixes", []))

    return {
        "previous": {
            "timestamp": prev.get("timestamp", "未知"),
            "fixes_count": prev_fixes,
            "file": prev.get("_file", ""),
        },
        "current": {
            "timestamp": curr.get("timestamp", "未知"),
            "fixes_count": curr_fixes,
            "file": curr.get("_file", ""),
        },
        "delta": {
            "fixes_change": curr_fixes - prev_fixes,
        },
    }


def format_report(result: dict) -> str:
    """格式化对比报告。"""
    if "error" in result:
        return result["error"]

    lines = []
    lines.append("版本对比：")
    lines.append(f"  上次: {result['previous']['timestamp']} ({result['previous']['fixes_count']} 项修复)")
    lines.append(f"  本次: {result['current']['timestamp']} ({result['current']['fixes_count']} 项修复)")
    lines.append(f"  变化: {result['delta']['fixes_change']:+d} 项修复")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: compare_versions.py <skill目录路径>")
        return 1

    skill_dir = sys.argv[1]
    if not os.path.isdir(skill_dir):
        print(f"[错误] 目录不存在: {skill_dir}")
        return 1

    result = compare(skill_dir)
    print(format_report(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
