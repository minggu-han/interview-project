"""多 Agent 系统。

基于 LangChain + OpenAI，包含 5 个职责单一的 agent：
  1. QuestionGeneratorAgent  生成题库
  2. QualityCheckerAgent     检验题目质量
  3. ScorerAgent             对回答评分
  4. AnalystAgent            梳理优缺点与知识掌握情况
  5. SummaryAgent            总结并给出建议

面试者回答原封不动落库，不再做整理润色（故无 RecorderAgent）。
每个 agent 都通过 chat_json 调用 LLM 并强制返回 JSON，便于结构化落库。
"""
from .base import get_llm
from .question_generator import QuestionGeneratorAgent
from .quality_checker import QualityCheckerAgent
from .scorer import ScorerAgent
from .analyst import AnalystAgent
from .summary import SummaryAgent

__all__ = [
    "get_llm",
    "QuestionGeneratorAgent",
    "QualityCheckerAgent",
    "ScorerAgent",
    "AnalystAgent",
    "SummaryAgent",
]
