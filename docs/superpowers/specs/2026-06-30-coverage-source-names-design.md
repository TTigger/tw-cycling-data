# /coverage 來源站名 + 連結 — 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:`/coverage` 的「已收錄的來源」區塊改善——顯示**準確的 8 個來源**(目前讀過期的 coverage.json 只有 6 個)、每個來源加上**人類可讀站名 + 連結**(目前只列網域)。加碼項 #28。

## 背景與動機

`/coverage` 的「✅ 已收錄的來源」Card 目前讀 `coverage.json.summary.by_source`,只顯示網域(`bravelog.tw` 46553…)。兩個問題:
1. `coverage.json` 由 `discover.py` 另外產生、已過期——只有 6 個來源、舊筆數,缺最新的 `taiwanbike.org` / `twbike.org`(master 實際有 8 來源)。
2. 只列網域,使用者不易立即識別是哪個網站。

## 已核可的決策

1. **準確來源**:來源清單與筆數改由 master 在 build 時算出(8 來源),不依賴過期的 coverage.json。
2. **站名 + 連結**:curated 對照表,顯示站名 + 連結。
3. **站名對照(已確認)**:

| 網域 (source_platform) | 站名 | 連結 |
|---|---|---|
| `bravelog.tw` | Bravelog 運動趣 | https://www.bravelog.tw/ |
| `irunner.biji.co` | iRunner(biji 運動社群) | https://irunner.biji.co/ |
| `tsu.com.tw` | 運動筆記 | https://www.tsu.com.tw/ |
| `taiwanbike.org` | 中華民國自行車協會(TBA) | https://taiwanbike.org/ |
| `twbike.org` | 中華民國登山車協會 | https://twbike.org/ |
| `cyclist.org.tw` | 自行車騎士協會 | https://www.cyclist.org.tw/ |
| `criterium.tw` | criterium.tw(TCU 城市繞圈賽) | https://criterium.tw/ |
| `cycling.org.tw` | 中華民國自由車協會 | https://cycling.org.tw/ |

## 元件設計

### 後端:`build_viz.build_overview` 加 `by_source`
- 在 overview.json 加 `by_source: {source_platform: count}`(由 master 逐筆累計,8 來源、準確筆數;對齊既有 `kpi.sources` 計數)。降序排列或前端排序皆可。
- overview.json 仍小。

### 前端
- `web/src/lib/sources.ts`(可測純資料/函式):`SOURCE_INFO: Record<string, {name: string; url: string}>`(上表 8 筆);`sourceInfo(domain) -> {name, url}`(未知網域 fallback `{name: domain, url: ""}`)。
- `web/src/lib/overview.ts`:`OverviewData` 加 `by_source: Record<string, number>` 型別。
- `web/src/components/coverage/CoverageApp.tsx`:「已收錄的來源」Card 改讀 `overview.by_source`(若 coverage 頁目前只載 coverage.json,則一併載入 overview.json 或在頁面預載 by_source);每列顯示 **站名(連結,開新分頁)+ 筆數**;網域作為次要灰字或 fallback。

> 註:實作時確認 CoverageApp 目前如何取得資料(讀 coverage.json)。最小改動:讓 Card 改用 `overview.by_source`(準確 8 來源)+ `sourceInfo` 對照;coverage.json 其餘用途(gaps)不變。

## 測試(照 dev-workflow)
- 前端 `web/src/lib/sources.test.ts`(vitest):`sourceInfo` 對 8 個已知網域回正確站名;未知網域 fallback(name=網域、url 空)。
- 後端:`build_overview` 加 `by_source` 後,既有 overview 測試不破;可加斷言 `by_source` 為 dict 且鍵數 == sources 數。
- 流程:`pytest scrapers/` + `vitest` → 重建 overview(build_viz)→ astro build → 瀏覽器抽查 /coverage(8 來源、站名、連結可點、筆數)。

## YAGNI(不做)
- 不修 `discover.py`/coverage.json 的 gaps 部分(本案只動來源清單顯示)。
- 不做來源 logo / 圖示。
- 站名不做多語(中文為主)。

## 未來待辦
- 若日後此站名/連結對照在他處也需要(如 /api、dataset 文件),可把 `SOURCE_INFO` 提升為共用資料。
