"""Phần thuần của lưới phân loại: schema công cụ (enum là thứ cho 0 lỗi schema — minimax.md §5), prompt, trần cắt, đường lui title_only."""
import pytest
from pydantic import ValidationError

from etl import news_classify as nc

CODES = ["NGANHANG", "CHUNGKHOAN", "BAOHIEM", "DANDUNG", "KHUCONGNGHIEP", "XAYDUNG", "VATLIEU", "KIMLOAI", "KHOANGSAN", "HOACHAT", "NHUA", "THIETBI",
         "NONGNGHIEP", "THUYSAN", "DETMAY", "CAOSU", "BANLE", "THUCPHAM", "DULICH", "YTE", "TIENICH", "DAUKHI", "VANTAI", "CONGNGHE"]
INDUSTRIES = [(c, f"Tên {c}") for c in CODES]
GOOD = {"group": "3", "sub": "3d", "confidence": 0.9, "summary_ai": "Tóm tắt.", "tickers": ["HPG"], "industries": ["KIMLOAI"]}


def _row(content, hint=3, title="Tiêu đề HPG", sapo="Sapo", src="cafef", feed="chung-khoan"):
    return nc.Row(1, src, feed, hint, hint == 3, "https://cafef.vn/a.chn", title, sapo, content)


def test_schema_enums_and_shape():
    S = nc.build_schema(CODES)
    js = S.model_json_schema()
    assert S.__name__ == "Classification" and js["additionalProperties"] is False
    # AC3: tickers/industries CÓ default [] — model bỏ hẳn trường khi rỗng (đo thật, 1/12 lời gọi, minimax.md §5) ⇒ không được required
    assert set(js["required"]) == {"group", "sub", "confidence", "summary_ai"}
    assert js["properties"]["group"]["enum"] == ["1", "2", "3", "x"]
    assert len(js["properties"]["sub"]["enum"]) == 21 and "3i" in js["properties"]["sub"]["enum"] and "x" in js["properties"]["sub"]["enum"]
    assert js["properties"]["industries"]["items"]["enum"] == CODES                 # đúng thứ tự đưa vào
    v = S.model_validate(GOOD)
    assert v.group == "3" and v.industries == ["KIMLOAI"]
    assert S.model_validate(dict(GOOD, group="x", sub="x", tickers=[], industries=[])).sub == "x"
    v2 = S.model_validate({"group": "x", "sub": "x", "confidence": 0.5, "summary_ai": "s"})
    assert v2.tickers == [] and v2.industries == []


@pytest.mark.parametrize("bad", [dict(GOOD, sub="1a"), dict(GOOD, confidence=1.2), dict(GOOD, industries=["THEP"]), dict(GOOD, extra=1),
                                 dict(GOOD, group="x")])
def test_schema_rejects_sub_outside_group_bad_confidence_unknown_industry_extra(bad):
    with pytest.raises(ValidationError):
        nc.build_schema(CODES).model_validate(bad)


def test_build_schema_rejects_duplicate_or_empty_codes():
    with pytest.raises(ValueError):
        nc.build_schema(["A", "A"])
    with pytest.raises(ValueError):
        nc.build_schema([])


def test_system_prompt_lists_industries_from_input_not_hardcoded():
    s = nc.system_prompt(INDUSTRIES)
    assert s.count(" — Tên ") == 24 and "KIMLOAI — Tên KIMLOAI" in s
    assert "3i Xếp hạng tín nhiệm và ESG" in s and "tối đa 3" in s
    assert nc.system_prompt([("ZZNGANH", "Ngành thử")]).count(" — ") == 1


def test_user_prompt_cuts_at_cap_and_reports_chars():
    text, n, cf = nc.user_prompt(_row("a" * 5000), cap=3000)
    assert (n, cf) == (3000, "content")
    assert "nhóm gợi ý: 3" in text and "Tiêu đề: Tiêu đề HPG" in text and "Sapo: Sapo" in text and "(đã cắt 3000 ký tự)" in text
    assert text.endswith("a" * 3000) and "a" * 3001 not in text


def test_user_prompt_title_only_below_200_and_missing_hint():
    text, n, cf = nc.user_prompt(_row("b" * 150, hint=None), cap=3000)
    assert (n, cf) == (150, "title_only") and "nhóm gợi ý: không có" in text
    text2, n2, cf2 = nc.user_prompt(_row("", hint=1, sapo=None))
    assert (n2, cf2) == (0, "title_only") and "Sapo: \n" in text2
    assert nc.user_prompt(_row("c" * 200))[1:] == (200, "content")                 # biên: đúng 200 là content
