# Fixture refdata — chụp 2026-08-26 (đêm)

Cắt từ payload thật; bản FULL không vào repo (scratchpad phiên chụp). `indexsnaps.json` + `icb.json` giữ **nguyên văn** (chứa cả 2 dòng rác thật của indexsnaps). Số đo toàn cục lúc chụp: xem ledger của plan.

| File | Nội dung | Literal cho test |
|---|---|---|
| `quotes.json` | 14 dòng: 7 StockType=2 (6 CP thật + `L40_WFT_01` rác) · 3 ETF · 2 CW · 2 bond | sau normalize: 6 stock, 3 etf; đếm bỏ: cw 2 · bond 2 · junk_stocktype2 1 |
| `organization.json` | 8 dòng: ACV(ACVN) · VHM(NHN) · SHB(SHB,NH) · CLI(0106839469) · NCG(ANOVA) · FUEMAVND(2172623,QU) · EGL · FUCTVGF4 (2 org-only) | HTB + 1 CP khác không có org ⇒ issuer NULL |
| `indexsnaps.json` | nguyên văn, 20 bản ghi | sau lọc: 18 mã đúng hằng số |
| `icb.json` | nguyên văn, 176 bản ghi | level: 11/19/40/106 |
