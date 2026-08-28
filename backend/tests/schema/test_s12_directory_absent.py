"""Cột dấu `market.security.directory_absent_since` (market-data-store §4.4).

Dấu thời gian mã vắng khỏi danh bạ doanh nghiệp. `apply()` đóng/gỡ dấu, `plan_delist()`
đọc dấu của các lượt TRƯỚC để chọn ứng viên lật `delisted` sau ngưỡng ân hạn.
"""
import sqlalchemy as sa


def _stock(db, ticker, stype="stock"):
    return db.execute(sa.text(
        "INSERT INTO market.security (ticker, exchange, security_type, status) "
        "VALUES (:t,'HOSE',:ty,'listed') RETURNING security_id"),
        {"t": ticker, "ty": stype}).scalar_one()


def test_directory_absent_since_defaults_to_null(db):        # seam 1
    sid = _stock(db, "ZZZ1")
    assert db.execute(sa.text(
        "SELECT directory_absent_since FROM market.security WHERE security_id=:i"),
        {"i": sid}).scalar_one() is None


def test_etl_role_can_write_directory_absent_since(db):      # seam 2: đường ghi production
    sid = _stock(db, "ZZZ2")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text(
        "UPDATE market.security SET directory_absent_since = now() WHERE security_id=:i"),
        {"i": sid})
    assert db.execute(sa.text(
        "SELECT directory_absent_since IS NOT NULL FROM market.security WHERE security_id=:i"),
        {"i": sid}).scalar_one() is True
