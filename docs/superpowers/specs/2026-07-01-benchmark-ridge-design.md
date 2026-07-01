# Phase 2b-2:/benchmark 你在分布上的綠點 — 設計 spec

**日期**:2026-07-01
**狀態**:已核可方向,待寫實作計畫
**範圍**:把 /benchmark 結果區那條陽春的扁平分布條,換成重用 `DistributionRidge`(2b-1)的**完賽時間分布稜線**,把使用者輸入的時間標成**松綠點**,一眼看出自己落在該 cohort 分布的哪個位置。順帶為 `RidgeMarker` 加選填 `labelColor`(呼應 2b-1 終審建議)。Ridgeline 改版 Phase 2b 的第二個子項。

## 背景與動機

/benchmark 現況(`BenchmarkTool.tsx`):選賽事 → 距離/組別 → cohort → 輸入時間 → 顯示「你贏過 X%」+ 最快/中位/最慢,並畫一條**扁平 `h-2` 分布條**(`bg-border` 背景 + 一個 0.5px 寬的 accent tick 標你的位置)。這條扁平條看不出分布形狀。

`cohort.bp` 是 101 個百分位斷點(`bp[0]`=最快、`bp[50]`=中位、`bp[100]`=最慢),本身就是該 cohort 完賽時間的分布(inverse CDF)。把 bp 餵給 2b-1 的 `DistributionRidge`(→ histogram → 密度)即可畫出真正的分布形狀;斷點在人多的時間帶密集,天然反映密度。

## 已核可決策

1. 結果區用 **`DistributionRidge`**(重用 2b-1)取代扁平分布條,資料 = `cohort.bp`。
2. markers:**中位**(`bp[50]`,琴珀,cohort 一選就顯示)+ **你**(輸入有效時間時 = 松綠,標籤也綠)。
3. `RidgeMarker` 加選填 `labelColor`(預設 `colors.ink`),讓「你」marker 的標籤與其綠線一致。
4. 保留「你贏過 X%」文字與 最快/中位/最慢 那行;移除扁平 `h-2` 分布條。
5. 只動 `BenchmarkTool.tsx` + `DistributionRidge.tsx`;不改資料、`densityRidge` 不動。

## 元件變更

### `DistributionRidge.tsx`(小加強)
- `RidgeMarker` 介面加 `labelColor?: string`。
- markLine 的 `label.color` 由固定 `colors.ink` 改為 `m.labelColor ?? colors.ink`;`lineStyle.color` 維持 `m.color ?? colors.secondary`。其餘不變(既有 /race 呼叫未帶 labelColor,行為不變)。

### `BenchmarkTool.tsx`(整合)
- import `DistributionRidge`(from `../charts/DistributionRidge`)、`useChartColors`(from `../../lib/chart-colors`)。
- 在 `Tool` 元件函式體(render body)加 `const colors = useChartColors();`。
- 組 markers:
  ```ts
  const ridgeMarkers = cohort ? [
    { value: cohort.bp[50], label: "中位", color: colors.secondary },
    ...(secs != null && beat != null
      ? [{ value: secs, label: "你", color: colors.accent, labelColor: colors.accent }]
      : []),
  ] : [];
  ```
- 在 cohort 選定後(`{cohort && (...)}`)新增一塊:
  ```tsx
  <DistributionRidge values={cohort.bp} height={200} markers={ridgeMarkers} />
  ```
  置於「你的完賽時間」輸入之後、結果框附近(cohort 一選就顯示分布+中位;輸入有效時間後多出綠色「你」marker)。
- **移除**結果框內的扁平分布條(`<div className="relative h-2 …">…</div>` 那段),其餘結果文字(「你贏過 X%」、最快/中位/最慢、小樣本警示)保留。

## 資料來源說明(誠實)

`DistributionRidge` 吃 `cohort.bp`(101 個時間斷點)當 values;histogram 對這些斷點分箱得到的密度,與實際完賽時間分布密度成正比(斷點密集處=人多)。這是分布的忠實近似,非原始逐筆(benchmarks 本就只存 bp,不存逐筆);UI 呈現為「該 cohort 的完賽時間分布」。

## 測試(照 dev-workflow)

- **vitest**:若為 `DistributionRidge` 的 `labelColor` 加可測純邏輯較勉強(它是 ECharts option 組裝);以既有 `densityRidge` 測試覆蓋資料路徑即可,labelColor 由 build + 瀏覽器驗證。(不強加無意義單元測試。)
- **build**:astro build 成功。
- **瀏覽器抽查**:/benchmark 選一場賽事→組別→cohort **深/淺各一輪**——分布稜線 + 中位(琴珀)顯示;輸入時間後出現**綠色「你」marker**(標籤也綠)且位置隨輸入時間左右移動、與「你贏過 X%」一致;切換翻色;扁平條已不在。

## 風險與緩解

- **bp 當 values 的近似**:101 點分箱在極端分布可能鋸齒;`DistributionRidge` 的 `smooth: 0.4` 已平滑;binWidth 用預設 300 秒。若太粗/太細,實作時可調 binWidth(不改介面)。
- **你 marker 超出分布範圍**(輸入極快/極慢):markLine 仍以 `xAxis: secs` 定位,ECharts 會落在軸範圍或邊界;可接受(代表你比最快還快/比最慢還慢)。
- **labelColor 破壞 /race**:/race 呼叫未帶 `labelColor` → `?? colors.ink` 維持原行為;不受影響。

## YAGNI(不做)

- 不改 benchmark 的選擇流程/資料/百分位計算。
- 不加逐筆分布(資料只有 bp)。
- 不動其他頁。
