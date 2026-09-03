# Fixture screener — hai response thật `GetScreenerItems` trang 1, `pageSize=30`

Nguyên văn, không cắt. Bản gốc và số đo: `docs/90-records/plans/2026-09-03-screener-daily-etl/`.

| File | Chụp lúc | Literal cho test |
|---|---|---|
| `page1-20260828-postclose.json` | 2026-08-28 20:51, sau phiên | 30 mã, `closePrice > 0` **30/30**; `DDB` UpcomIndex `tradingDate 2026-08-28T15:00:01.533`, `closePrice 9100.0`, `rtd7 12750.50715092`, `rtd11 107400000000.0`, `rtd14 113.41451175`; `V68` có `technical = null`; `CCC`/`AAN`/`SBG` đóng dấu **14:45**; `FUEIP100` là ETF trên VNINDEX; `totalCount 1545` |
| `page1-20260903-preopen.json` | 2026-09-03 08:38, trước mở cửa sau nghỉ lễ | cùng 30 mã, `closePrice > 0` **0/30**, mọi `tradingDate` = `2026-09-03T08:2x`, `referenceDate 2026-08-28` |
