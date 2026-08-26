-- DDL kho realtime — spec §2–§4, đã kiểm trên CH 26.3.22.7 (spec §12).
-- Không sửa file này sau khi đã chạy. Sửa = migration kế tiếp.

CREATE TABLE IF NOT EXISTS rt.trade (
  symbol        LowCardinality(String),
  ts            DateTime('Asia/Ho_Chi_Minh'),
  seq           UInt64,
  price         Decimal64(2),
  volume        UInt64,
  side          LowCardinality(String),
  change        Decimal64(2),
  cum_volume    UInt64,
  cum_value     Decimal64(2),
  received_at   DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, seq)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.quote (
  symbol      LowCardinality(String),
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),
  top         UInt8,
  action      LowCardinality(String),
  bid_price   Decimal64(2),
  bid_qty     UInt64,
  ask_price   Decimal64(2),
  ask_qty     UInt64,
  cum_bid     UInt64,
  cum_ask     UInt64,
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, top)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.snapshot_delta (
  symbol      LowCardinality(String),
  exchange    LowCardinality(String),
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),
  b1 Nullable(Decimal64(2)), b2 Nullable(Decimal64(2)), b3 Nullable(Decimal64(2)),
  v1 Nullable(UInt64),       v2 Nullable(UInt64),       v3 Nullable(UInt64),
  s1 Nullable(Decimal64(2)), s2 Nullable(Decimal64(2)), s3 Nullable(Decimal64(2)),
  u1 Nullable(UInt64),       u2 Nullable(UInt64),       u3 Nullable(UInt64),
  total_bid   Nullable(UInt64),
  total_offer Nullable(UInt64),
  close_price Nullable(Decimal64(2)),
  change      Nullable(Decimal64(2)),
  change_pct  Nullable(Decimal64(2)),
  avg_price   Nullable(Decimal64(2)),
  high        Nullable(Decimal64(2)),
  last_vol    Nullable(UInt64),
  last_vol2   Nullable(UInt64),
  last_price  Nullable(Decimal64(2)),
  total_vol   Nullable(UInt64),
  total_value Nullable(Decimal64(2)),
  foreign_buy    Nullable(UInt64),
  foreign_sell   Nullable(UInt64),
  foreign_remain Nullable(UInt64),
  pt_price     Nullable(Decimal64(2)),
  pt_qty       Nullable(UInt64),
  pt_total_qty Nullable(UInt64),
  pt_total_val Nullable(Decimal64(2)),
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.index_delta (
  symbol      LowCardinality(String),
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),
  index_value Nullable(Decimal64(2)),
  change      Nullable(Decimal64(2)),
  change_pct  Nullable(Decimal64(2)),
  total_vol   Nullable(UInt64),
  total_value Nullable(Decimal64(2)),
  advances    Nullable(UInt16),
  declines    Nullable(UInt16),
  unchanged   Nullable(UInt16),
  ceiling_cnt Nullable(UInt16),
  adv_vol     Nullable(UInt64),
  dec_vol     Nullable(UInt64),
  unch_vol    Nullable(UInt64),
  pt_total    Nullable(UInt64),
  pt_value    Nullable(Decimal64(2)),
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.pt_match (
  symbol      LowCardinality(String),
  market      LowCardinality(String),
  ts          DateTime('Asia/Ho_Chi_Minh'),
  price       Decimal64(2),
  volume      UInt64,
  ref_price   Nullable(Decimal64(2)),
  ceil_price  Nullable(Decimal64(2)),
  floor_price Nullable(Decimal64(2)),
  order_id    String,
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, order_id)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),
  o    AggregateFunction(argMin, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  h    AggregateFunction(max, Decimal64(2)),
  l    AggregateFunction(min, Decimal64(2)),
  c    AggregateFunction(argMax, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  v    AggregateFunction(sum, UInt64),
  val  AggregateFunction(sum, Decimal128(2)),
  v_bu AggregateFunction(sum, UInt64),
  v_sd AggregateFunction(sum, UInt64)
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts)
SETTINGS non_replicated_deduplication_window = 100;

CREATE MATERIALIZED VIEW IF NOT EXISTS rt.mv_trade_to_bar_1m TO rt.bar_1m AS
SELECT
  symbol,
  toStartOfMinute(event_ts)                            AS ts,
  argMinState(price, (event_ts, seq, received_at))     AS o,
  maxState(price)                                      AS h,
  minState(price)                                      AS l,
  argMaxState(price, (event_ts, seq, received_at))     AS c,
  sumState(volume)                                     AS v,
  sumState(toDecimal128(price, 2) * volume)            AS val,
  sumState(if(side = 'B', volume, toUInt64(0)))        AS v_bu,
  sumState(if(side = 'S', volume, toUInt64(0)))        AS v_sd
FROM (SELECT symbol, ts AS event_ts, seq, price, volume, side, received_at FROM rt.trade)
GROUP BY symbol, ts;

CREATE VIEW IF NOT EXISTS rt.bar_1m_v AS
SELECT symbol, ts,
       argMinMerge(o) AS o, maxMerge(h) AS h, minMerge(l) AS l, argMaxMerge(c) AS c,
       sumMerge(v) AS v, sumMerge(val) AS val,
       sumMerge(v_bu) AS v_bu, sumMerge(v_sd) AS v_sd
FROM rt.bar_1m
GROUP BY symbol, ts;

CREATE TABLE IF NOT EXISTS rt.index_bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),
  o AggregateFunction(argMin, Decimal64(2), Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  h AggregateFunction(max, Decimal64(2)),
  l AggregateFunction(min, Decimal64(2)),
  c AggregateFunction(argMax, Decimal64(2), Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  cum_vol   AggregateFunction(max, Nullable(UInt64)),
  cum_value AggregateFunction(max, Nullable(Decimal64(2)))
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts);

CREATE MATERIALIZED VIEW IF NOT EXISTS rt.mv_index_to_bar_1m TO rt.index_bar_1m AS
SELECT
  symbol,
  toStartOfMinute(toDateTime(event_ts))                             AS ts,
  argMinState(assumeNotNull(index_value), (event_ts, received_at))  AS o,
  maxState(assumeNotNull(index_value))                              AS h,
  minState(assumeNotNull(index_value))                              AS l,
  argMaxState(assumeNotNull(index_value), (event_ts, received_at))  AS c,
  maxState(total_vol)                                               AS cum_vol,
  maxState(total_value)                                             AS cum_value
FROM (SELECT symbol, ts AS event_ts, index_value, total_vol, total_value, received_at
      FROM rt.index_delta WHERE index_value IS NOT NULL AND index_value > 0)
GROUP BY symbol, ts;

CREATE VIEW IF NOT EXISTS rt.index_bar_1m_v AS
SELECT symbol, ts,
       argMinMerge(o) AS o, maxMerge(h) AS h, minMerge(l) AS l, argMaxMerge(c) AS c,
       maxMerge(cum_vol) AS cum_vol, maxMerge(cum_value) AS cum_value
FROM rt.index_bar_1m
GROUP BY symbol, ts;
