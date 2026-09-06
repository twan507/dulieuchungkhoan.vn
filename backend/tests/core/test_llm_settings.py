"""LLMSettings: khoá bắt buộc, mặc định MiniMax, repr/redact không lộ khoá (CLAUDE.md §5)."""
import pytest

from core.llm import LLMConfigError, LLMSettings

KEY = "zz-secret-key-0123456789"          # 24 ký tự


def test_missing_key_raises_named_error():
    with pytest.raises(LLMConfigError) as e:
        LLMSettings.from_env({})
    assert "LLM_API" in str(e.value)
    with pytest.raises(LLMConfigError):
        LLMSettings.from_env({"LLM_API": "   "})


def test_defaults_point_to_minimax_anthropic():
    s = LLMSettings.from_env({"LLM_API": KEY})
    assert s.base_url == "https://api.minimax.io/anthropic"
    assert s.model == "MiniMax-M3"
    assert s.timeout_s == 120.0
    s2 = LLMSettings.from_env({"LLM_API": KEY, "LLM_BASE_URL": "https://x.test/anthropic/", "LLM_MODEL": "M", "LLM_TIMEOUT_S": "30"})
    assert (s2.base_url, s2.model, s2.timeout_s) == ("https://x.test/anthropic", "M", 30.0)


def test_repr_and_redact_never_expose_key():
    s = LLMSettings.from_env({"LLM_API": KEY})
    assert KEY not in repr(s) and KEY not in str(s)
    assert "24 ký tự" in repr(s)
    assert s.redact(f"Bearer {KEY} hết") == "Bearer <REDACTED> hết"
