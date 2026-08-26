"""Dựng trạng thái đích của lượt refdata (spec §3 luật 1-5).

Thuần — không I/O. Nhận `NormResult` (đã chuẩn hoá), hợp nhất ba nguồn
(`/quotes` ∪ 18 chỉ số hằng số ∪ ticker chỉ có ở `GetListOrganization`) thành
danh sách `SecurityTarget` duy nhất theo ticker, cộng danh sách `IssuerTarget`
(mọi `OrgRec`, kể cả org-only).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from etl.refdata_indices import INDICES
from etl.refdata_normalize import IcbRec, NormResult, OrgRec, QuoteRec

log = logging.getLogger(__name__)

COM_GROUP_TO_EXCHANGE = {"VNINDEX": "HOSE", "HNXIndex": "HNX", "UpcomIndex": "UPCOM"}


@dataclass(frozen=True)
class SecurityTarget:
    ticker: str
    exchange: str
    security_type: str    # 'stock' | 'etf' | 'index' | 'fund_cert'
    status: str           # 'listed' | 'delisted'
    tradelot: int | None
    full_name: str | None
    organ_code: str | None                          # None = không nối issuer
    external_ids: tuple[tuple[str, str, str], ...]   # (source, code, sub)


@dataclass(frozen=True)
class IssuerTarget:
    organ_code: str
    name: str
    short_name: str | None
    com_type_code: str | None
    icb_code: str | None


@dataclass(frozen=True)
class TargetState:
    securities: list[SecurityTarget]
    issuers: list[IssuerTarget]
    icb: list[IcbRec]
    counters: dict[str, int]   # stocks_no_issuer · fiin_only_delisted (+ counters của normalize)


def _quote_target(q: QuoteRec, org_by_ticker: dict[str, OrgRec]) -> tuple[SecurityTarget, bool]:
    """Trả về (target, thiếu_issuer) — thiếu_issuer chỉ có ý nghĩa khi q là 'stock'."""
    org = org_by_ticker.get(q.symbol)
    organ_code = org.organ_code if org is not None else None
    target = SecurityTarget(
        ticker=q.symbol,
        exchange=q.exchange,
        security_type=q.security_type,
        status="listed",
        tradelot=q.tradelot,
        full_name=q.full_name,
        organ_code=organ_code,
        external_ids=(("bvsc", q.symbol, ""),),
    )
    missing_issuer = q.security_type == "stock" and org is None
    return target, missing_issuer


def _index_targets() -> list[SecurityTarget]:
    targets = []
    for d in INDICES:
        external_ids: list[tuple[str, str, str]] = [("bvsc", d.snap_code, "snapshot")]
        if d.tvc_code is not None:
            external_ids.append(("bvsc", d.tvc_code, "tvc"))
        targets.append(SecurityTarget(
            ticker=d.ticker,
            exchange=d.exchange,
            security_type="index",
            status="listed",
            tradelot=None,
            full_name=d.name,
            organ_code=None,
            external_ids=tuple(external_ids),
        ))
    return targets


def _fiin_only_target(org: OrgRec) -> SecurityTarget | None:
    """None khi `comGroupCode` lạ — giá trị lạ không được giết cả job (luật nhà:
    cùng cách xử StockType lạ và mã ICB lạ), caller đếm + log."""
    exchange = COM_GROUP_TO_EXCHANGE.get(org.com_group_code)
    if exchange is None:
        return None
    security_type = "fund_cert" if org.com_type_code == "QU" else "stock"
    return SecurityTarget(
        ticker=org.ticker,
        exchange=exchange,
        security_type=security_type,
        status="delisted",
        tradelot=None,
        full_name=org.organ_name,
        organ_code=org.organ_code,
        external_ids=(),
    )


def _dedupe_orgs(orgs) -> tuple[list, int]:
    """Luật 6 (phòng thủ — chưa từng quan sát trùng, đo 2026-08-26): trùng ticker
    thì bản `organTypeCode='DN'` thắng, bản còn lại đếm + log, không chặn job."""
    by_ticker: dict[str, object] = {}
    dups = 0
    for o in orgs:
        cur = by_ticker.get(o.ticker)
        if cur is None:
            by_ticker[o.ticker] = o
            continue
        dups += 1
        keep, drop = (o, cur) if (o.organ_type_code == "DN" and cur.organ_type_code != "DN") else (cur, o)
        by_ticker[o.ticker] = keep
        log.warning("trùng ticker %s trong GetListOrganization — giữ %s (organTypeCode=%s), bỏ %s",
                    o.ticker, keep.organ_code, keep.organ_type_code, drop.organ_code)
    return list(by_ticker.values()), dups


def merge(n: NormResult) -> TargetState:
    orgs, dup_org_ticker = _dedupe_orgs(n.orgs)
    org_by_ticker = {o.ticker: o for o in orgs}
    index_tickers = {d.ticker for d in INDICES}
    quote_tickers = {q.symbol for q in n.quotes}

    counters = dict(n.counters)
    stocks_no_issuer = 0

    securities: list[SecurityTarget] = []
    for q in n.quotes:
        target, missing_issuer = _quote_target(q, org_by_ticker)
        securities.append(target)
        if missing_issuer:
            stocks_no_issuer += 1

    securities.extend(_index_targets())

    fiin_only_delisted = 0
    unknown_com_group = 0
    for o in orgs:
        if o.ticker in quote_tickers or o.ticker in index_tickers:
            continue
        target = _fiin_only_target(o)
        if target is None:
            unknown_com_group += 1
            log.warning("comGroupCode lạ %r ở ticker %s — bỏ, không chặn job",
                        o.com_group_code, o.ticker)
            continue
        securities.append(target)
        fiin_only_delisted += 1

    counters["stocks_no_issuer"] = stocks_no_issuer
    counters["fiin_only_delisted"] = fiin_only_delisted
    counters["unknown_com_group"] = unknown_com_group
    counters["dup_org_ticker"] = dup_org_ticker

    issuers = [
        IssuerTarget(
            organ_code=o.organ_code,
            name=o.organ_name,
            short_name=o.organ_short_name,
            com_type_code=o.com_type_code,
            icb_code=o.icb_code,
        )
        for o in orgs
    ]

    return TargetState(
        securities=securities,
        issuers=issuers,
        icb=n.icb,
        counters=counters,
    )
