"""Module LLM dùng chung của dự án — chỉ MiniMax M3 (chủ dự án chốt 2026-09-06), SDK anthropic trỏ giao diện
Anthropic của MiniMax. Consumer (etl.news_classify, api chatbot lát 10) chỉ import từ đây, không import SDK."""
from core.llm.errors import LLMConfigError, LLMError
from core.llm.settings import LLMSettings
from core.llm.usage import Usage

__all__ = ["LLMConfigError", "LLMError", "LLMSettings", "Usage"]
