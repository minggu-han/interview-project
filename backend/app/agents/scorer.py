"""Agent 4：评分。对候选人某题的完整回答打分。"""
from .base import chat_json

SYSTEM = """你是严谨的技术面试评分官。基于题目、参考答案和候选人回答，从
正确性、完整性、深度、表达 四个维度评分（各 0-10），并给出 0-100 的综合分与简评。"""


class ScorerAgent:
    async def score(self, question: str, reference: str | None, answer: str) -> dict:
        user = f"""题目：{question}
参考答案：{reference or '无'}
候选人回答：{answer or '（未作答）'}

输出 JSON：
{{
  "dimensions": {{"correctness": 0-10, "completeness": 0-10, "depth": 0-10, "expression": 0-10}},
  "overall": 0-100,
  "comment": "简评"
}}"""
        data = await chat_json(SYSTEM, user, temperature=0.2)
        return {
            "dimensions": data.get("dimensions", {}),
            "overall": float(data.get("overall", 0)),
            "comment": data.get("comment", ""),
        }
