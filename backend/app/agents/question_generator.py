"""Agent 1：题库生成。根据岗位与所需技术生成面试题。"""
from .base import chat_json

SYSTEM = """你是一位资深技术面试官，负责为特定岗位设计高质量的面试题。
你需要结合岗位、候选人级别和所需技术点，设计有区分度、循序渐进的题目。
每道题需覆盖一个明确的技术点，并给出参考答案要点。"""


class QuestionGeneratorAgent:
    async def generate(
        self,
        position: str,
        skills: list[str],
        seniority: str | None,
        num_questions: int = 5,
    ) -> list[dict]:
        user = f"""岗位：{position}
候选人级别：{seniority or '不限'}
所需技术：{', '.join(skills) if skills else '通用'}
请生成 {num_questions} 道面试题。

输出 JSON 数组，每个元素格式：
{{
  "skill": "考察的技术点",
  "difficulty": "easy|medium|hard",
  "content": "题目内容",
  "reference_answer": "参考答案要点"
}}"""
        data = await chat_json(SYSTEM, user, temperature=0.6)
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]
        return data if isinstance(data, list) else []
