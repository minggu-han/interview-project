"""Agent 公共基础：LLM 实例与 JSON 调用封装。"""
import json
import logging
from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
    )


def _extract_json(text: str):
    """从模型输出中尽可能稳健地提取 JSON。"""
    text = text.strip()
    if text.startswith("```"):
        # 去掉 ```json ... ``` 包裹
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    # 尝试直接解析；失败则截取首个 { 或 [ 到末尾
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for open_ch, close_ch in (("{", "}"), ("[", "]")):
            start = text.find(open_ch)
            end = text.rfind(close_ch)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    continue
        raise


async def _ainvoke_with_retry(llm, messages, retries: int = 3):
    """带重试的 LLM 调用，缓解网关偶发错误 / 限流。"""
    import asyncio

    last_exc = None
    for attempt in range(retries):
        try:
            resp = await llm.ainvoke(messages)
            logger.info("LLM 调用成功（第 %s 次尝试）", attempt + 1)
            return resp
        except Exception as e:  # noqa: BLE001 网关错误类型多样，统一重试
            last_exc = e
            logger.warning("LLM 调用失败（第 %s/%s 次）：%s", attempt + 1, retries, e)
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # 退避：1s, 2s
    logger.error("LLM 调用最终失败：%s", last_exc)
    raise last_exc


async def chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.3):
    """调用 LLM，要求其输出 JSON，并解析为 Python 对象。"""
    llm = get_llm(temperature)
    messages = [
        SystemMessage(content=system_prompt + "\n\n严格只输出合法 JSON，不要任何额外解释或 markdown。"),
        HumanMessage(content=user_prompt),
    ]
    resp = await _ainvoke_with_retry(llm, messages)
    return _extract_json(resp.content)


async def chat_text(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    llm = get_llm(temperature)
    resp = await _ainvoke_with_retry(
        llm, [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return resp.content.strip()
