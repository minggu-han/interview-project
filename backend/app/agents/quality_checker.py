"""Agent 2：题目质量检验。对生成的题目逐条打分与把关。"""
from .base import chat_json

SYSTEM = """你是面试题质量审核专家。你需要评估一道面试题是否：
1) 与岗位/技术点相关；2) 表述清晰无歧义；3) 难度标注准确；4) 有考察区分度；5) 参考答案合理。
对每道题给出 0-10 的质量分，是否通过（>=6 为通过），以及改进意见。"""


class QualityCheckerAgent:
    async def check(self, question: dict, position: str) -> dict:
        user = f"""岗位：{position}
题目技术点：{question.get('skill')}
难度：{question.get('difficulty')}
题目：{question.get('content')}
参考答案：{question.get('reference_answer')}

输出 JSON：
{{"quality_score": 0-10, "passed": true/false, "feedback": "改进意见"}}"""
        data = await chat_json(SYSTEM, user, temperature=0.2)
        score = float(data.get("quality_score", 0))
        return {
            "quality_score": score,
            "passed": bool(data.get("passed", score >= 6)),
            "feedback": data.get("feedback", ""),
        }
