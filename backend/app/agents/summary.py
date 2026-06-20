"""Agent 6：总结。给出整体评价与录用建议。"""
from .base import chat_json

SYSTEM = """你是面试委员会负责人。基于候选人的综合得分、优缺点与技能掌握情况，
撰写一段总体评价，并给出明确的录用建议（强烈推荐/推荐/待定/不推荐）及理由与提升建议。"""


class SummaryAgent:
    async def summarize(
        self,
        position: str,
        overall_score: float,
        strengths: list[str],
        weaknesses: list[str],
        skill_mastery: dict,
    ) -> dict:
        user = f"""岗位：{position}
综合得分：{overall_score}
优点：{strengths}
缺点：{weaknesses}
技能掌握：{skill_mastery}

输出 JSON：
{{
  "summary": "总体评价",
  "recommendation": "录用建议（含级别、理由与提升建议）"
}}"""
        data = await chat_json(SYSTEM, user, temperature=0.4)
        return {
            "summary": data.get("summary", ""),
            "recommendation": data.get("recommendation", ""),
        }
