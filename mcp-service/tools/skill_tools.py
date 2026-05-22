"""
tools/skill_tools.py — Category D: Skill 呼叫（2 個 Tools）
sg_list_skills | sg_get_skill
"""

import os
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"


async def tool_list_skills() -> dict:
    """列出所有可用的 System Governor Skill。"""
    skills = []
    if SKILLS_DIR.exists():
        for f in sorted(SKILLS_DIR.glob("*.md")):
            # 讀取第一行作為描述
            try:
                lines = f.read_text(encoding="utf-8").splitlines()
                title = next((l.lstrip("# ").strip() for l in lines if l.strip()), f.stem)
                desc = next((l.strip() for l in lines[1:] if l.strip() and not l.startswith("#")), "")
            except Exception:
                title = f.stem
                desc = ""
            skills.append({
                "name": f.stem,
                "title": title,
                "description": desc[:100],
                "file": f.name,
            })

    return {
        "total": len(skills),
        "skills": skills,
        "_reminders": [],
        "_note": "使用 sg_get_skill(name) 取得完整 Skill 定義。",
    }


async def tool_get_skill(name: str) -> dict:
    """
    取得指定 Skill 的完整 Markdown 定義原文。
    name: skill 的檔名（不含 .md）
    """
    skill_path = SKILLS_DIR / f"{name}.md"
    if not skill_path.exists():
        available = [f.stem for f in SKILLS_DIR.glob("*.md")] if SKILLS_DIR.exists() else []
        return {
            "error": f"找不到 skill: {name}",
            "available_skills": available,
            "_reminders": [],
        }

    content = skill_path.read_text(encoding="utf-8")
    return {
        "name": name,
        "content": content,
        "path": str(skill_path),
        "_reminders": [],
    }
