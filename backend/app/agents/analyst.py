"""Agent 5：优缺点与知识掌握分析。综合全部问答与评分进行分析。"""
from .base import chat_json

SYSTEM = """你是技术面试分析专家。基于候选人所有题目的问答与评分，
梳理其优点、缺点，以及每个技术点的掌握程度（0-100）。"""


class AnalystAgent:
    async def analyze(self, position: str, skills: list[str], qa_items: list[dict]) -> dict:
        lines = []
        for i, it in enumerate(qa_items, 1):
            lines.append(
                f"{i}. [{it.get('skill','')}] 题:{it.get('question','')}\n"
                f"   答:{it.get('answer','')}\n   得分:{it.get('score','')} 评:{it.get('comment','')}"
            )
        body = "\n".join(lines)
        user = f"""岗位：{position}
考察技术点：{', '.join(skills)}
问答与评分：
{body}

输出 JSON：
{{
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["缺点1", "缺点2"],
  "skill_mastery": {{"技术点": 0-100}}
}}"""
        data = await chat_json(SYSTEM, user, temperature=0.3)
        return {
            "strengths": data.get("strengths", []),
            "weaknesses": data.get("weaknesses", []),
            "skill_mastery": data.get("skill_mastery", {}),
        }
