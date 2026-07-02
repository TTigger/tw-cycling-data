# Phase 2b-5:header 捲動稜線進度條 — 設計 spec

**日期**:2026-07-02
**狀態**:已核可,待寫實作計畫
**範圍**:把 header nav 下方的靜態 hairline(Phase 1 放的 `<div class="mt-2 h-px w-full bg-border">`)升級為「軌道 + accent 填充」的捲動進度條。Ridgeline 改版 Phase 2b 的最後一個子項(收尾點綴)。

## 已核可決策

1. **直線填充**(非稜線形 SVG——1px 高看不出形狀,徒增複雜,不採)。
2. 結構:hairline 改為相對定位軌道(`bg-border`)+ 絕對定位填充(`bg-accent`,`width:0` 起始,`aria-hidden`):
   ```astro
   <div class="relative mt-2 h-px w-full bg-border">
     <div id="scrollRidge" class="absolute inset-y-0 left-0 bg-accent" style="width:0" aria-hidden="true"></div>
   </div>
   ```
3. 驅動:`is:inline` vanilla script(與既有 nav/theme script 同區)——`scroll`/`resize`(passive)+ rAF 節流;`width = scrollTop / (scrollHeight - clientHeight) * 100%`;`max ≤ 0`(短頁)→ 0。
4. **無 transition**(寬度直接跟捲動,非動畫;不涉 reduced-motion);純裝飾 `aria-hidden`;深/淺由 token 自動翻。
5. 只改 `web/src/layouts/Base.astro`;不動 React/資料。

## 測試

- build 成功。
- 瀏覽器抽查(深/淺):長頁捲動時綠線從左往右填、捲回縮回;換頁重置為對應位置;短頁(無捲動)保持 0;header 其他(wordmark/nav/toggle)不受影響。

## 風險

- rAF 節流防 scroll 抖動;`getElementById` 防呆(無元素直接 return);`document.documentElement` 的 scrollTop/scrollHeight 為標準路徑。

## YAGNI(不做)

- 不做稜線形 SVG 填充、不加百分比數字、不做 sticky header。
