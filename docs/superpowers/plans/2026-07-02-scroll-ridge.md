# Phase 2b-5:header 捲動稜線進度條 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** header 的靜態 hairline 升級為捲動進度條(accent 填充隨捲動百分比)。

**Architecture:** `Base.astro` 內:hairline 改軌道+填充結構;新增一段 `is:inline` vanilla script(rAF 節流的 scroll/resize 監聽)驅動 `#scrollRidge` 寬度。單檔、無 React。

**Tech Stack:** Astro(inline script)+ Tailwind token classes。

## Global Constraints

- 只改 `web/src/layouts/Base.astro`。軌道 `bg-border`、填充 `bg-accent`(token,自動翻色);填充 `aria-hidden="true"`、初始 `width:0`;無 transition。
- script:`scroll`/`resize` 皆 `{ passive: true }` + rAF 節流;`max = scrollHeight - clientHeight`,`max ≤ 0 → 0`;掛載即先跑一次(換頁初始位置正確);`getElementById` 無元素直接 return。
- 既有 no-flash/theme/nav script、header 其他內容不動。build 成功。

## 執行順序
單一 task → controller 收尾。

---

## Task 1: 軌道+填充 + 驅動 script

**Files:** Modify `web/src/layouts/Base.astro`

- [ ] **Step 1: hairline 改軌道+填充**

把:
```astro
      <div class="mt-2 h-px w-full bg-border"></div>
```
換成:
```astro
      <div class="relative mt-2 h-px w-full bg-border">
        <div id="scrollRidge" class="absolute inset-y-0 left-0 bg-accent" style="width:0" aria-hidden="true"></div>
      </div>
```

- [ ] **Step 2: 加驅動 script**

在既有 `is:inline` script 區(nav/theme 那個 `<script is:inline>` 內,或緊接其後同型式新段)追加:
```js
      (() => {
        const bar = document.getElementById("scrollRidge");
        if (!bar) return;
        let raf = 0;
        const update = () => {
          raf = 0;
          const doc = document.documentElement;
          const max = doc.scrollHeight - doc.clientHeight;
          const p = max > 0 ? Math.min(1, Math.max(0, doc.scrollTop / max)) : 0;
          bar.style.width = (p * 100).toFixed(2) + "%";
        };
        const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };
        addEventListener("scroll", onScroll, { passive: true });
        addEventListener("resize", onScroll, { passive: true });
        update();
      })();
```

- [ ] **Step 3: build + 瀏覽器抽查**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。
瀏覽器(深/淺各一輪):長頁(如 /athletes 某選手頁)捲動 → 綠線左→右填、捲回縮回;短頁保持 0;首屏載入時位置正確;header wordmark/nav/主題切換不受影響。

- [ ] **Step 4: Commit**

```bash
git add web/src/layouts/Base.astro
git commit -m "feat(ridge): header hairline fills with scroll progress"
```

---

## Controller 收尾(合併前)

- [ ] `npm --prefix web run build`(成功);瀏覽器深/淺抽查如上。

## Self-Review

**1. Spec coverage:** 軌道+填充結構 ✅;rAF+passive+短頁歸零+掛載即跑 ✅;無 transition/aria-hidden/token 翻色 ✅;只動 Base.astro ✅。
**2. Placeholder scan:** 無;全碼。
**3. Type consistency:** 純 DOM,無跨檔介面。
