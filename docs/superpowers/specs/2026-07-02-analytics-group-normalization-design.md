# 分析層分組化:難度係數 + DNA 兩軸 — 設計 spec

**日期**:2026-07-02
**狀態**:已核可,待寫實作計畫
**範圍**:把 #27 的 (race_key, result_label) 分組手術套到**分析層**——① `build_difficulty` 難度係數改組內計算(修正跨年校正與嚴苛度的混組污染);② `build_race_dna` 的「選擇性」軸改組內 CoV、「女子比例」軸加 known-gender 覆蓋門檻。騎乘分身**維持現狀**(不在本案)。

## 背景與動機(實測)

三項分析功能 2026-06-16 上線,**早於 #27 分組正規化兩週**。#27 證明 125 個 race_key 有 71 個混多距離組(63 個組間差 >2×),而:
- `build_difficulty.py:17` 明寫係數用「ALL timed finishers」的整場中位——年度組別結構改變(如 50K/130K 完賽者比例變動)會被誤讀成難度變化。實測:31 場可校正賽事中 **8 場係數年間擺動 >1.5×、4 場 >2×**(難度真變 2× 不合理),直接污染選手頁校正曲線與 /race 嚴苛度。
- `build_race_dna` 的 `sel`(選擇性)= 整場 CoV——混距離必然膨脹,「高選擇性」是假讀數。`fem`(女子比例)在 known-gender 覆蓋低的賽事讀到的是**來源效應**(有的來源整批無性別)而非真實占比。
- 爬坡度(逐列距離→速度,抗混組)、規模/回頭率/含金量(計數型)不動。

## 已核可決策

1. **難度資料形狀仿 #27**:`race_difficulty.json` 改
   `{rk: {name, groups: {group_label: {baseline, years: {y: {median, coeff, n}}}}}}`,
   `group_label` = result_label 或 `全部`;門檻**每組每年 ≥20 timed**(沿用 MIN_FINISHERS)、**每組 ≥2 年**才收;race 保留須 ≥1 組。
2. **校正查表嚴格**:`calibratedSeries` 用該筆成績的 `h.label`(或 `全部`)查其組的該年 coeff;該組該年未覆蓋 → **跳過該年**(寧缺勿錯,不做跨組 fallback)。
3. **嚴苛度改讀最大組**:`raceSeverity`/`raceSeverityAll` 改用該賽事**最大組**(跨年總完賽 n 最多者)的 years 序列(coeff 與 n 皆是)——組成穩定、逐年可比;UI 註明所依組別(如「以 130K挑戰 組為準」)。
4. **DNA `sel`**:= 各組(組 n ≥10)CoV 的 **n 加權平均**;無合格組 → null。
5. **DNA `fem`**:known-gender(M/F)占該賽事完賽者 **<30%** → 該軸 null(雷達已容忍 null 軸)。
6. 只動分析層;不動 dataset/master、不動 benchmarks/crossyear(#27 已處理)、不動騎乘分身、`RaceDna.tsx` 前端不動(軸值後端算)。

## 元件設計

### 後端
- **`scrapers/build_difficulty.py`**:聚合鍵改 (race_key, result_label或全部, year);每組自己 `baseline = median(該組年中位們)`、`coeff = 年中位/組 baseline`。輸出巢狀 groups 形狀。可測純邏輯抽到函式(輸入 rows → 巢狀 dict)。
- **`scrapers/build_race_dna.py`**:
  - `sel`:rows 先按 group 分桶;各組 n≥10 者算 `_cov(組 secs)`;`sel = Σ(cov_g × n_g) / Σ n_g`;無合格組 → None。
  - `fem`:計 `known = M數+F數`;`known / total < 0.30` → None;否則沿用現算式(F/known)。
  - 其他軸不動。
- 兩者的既有 pytest 更新 + 新增分組斷言(混組輸入 → 各組各自 coeff/CoV,不混)。

### 前端(`web/src/lib/difficulty.ts` + types + 2 元件)
- **types**:`RaceDifficulty` 改 `{name, groups: Record<string, {baseline, years: Record<string, YearDifficulty>}>}`(`YearDifficulty {median,coeff,n}` 不變)。
- **`calibratedSeries(history, rk, diff)`**:每筆 `h` 取 `g = h.label ?? "全部"`;`diff.groups[g]?.years[String(h.y)]` 有才產點(嚴格跳過)。同年多筆仍取最快。
- **新 helper `dominantGroup(diff): string | null`**:回傳跨年 Σn 最大的組鍵(嚴苛度用;純函式可 vitest)。
- **`raceSeverity`/`raceSeverityAll`**:改吃 `diff.groups[dominantGroup(diff)]` 的 years;回傳物件加 `group: string` 欄。
- **`calibratableRaces`**:邏輯不變(仍以 `calibratedSeries(...).length >= 2` 判定),自動反映新嚴格性。
- **`CalibratedProgress.tsx`**:資料流不變(吃 `calibratedSeries`);說明文字補「依你所屬距離/組別各自校正;未覆蓋的年份不顯示」。
- **`RaceSeverity.tsx`**:顯示 `severity.group`(「以 X 組為準」小字);其餘不動。
- **`docs/API.md`**:race_difficulty.json 端點 schema 更新為巢狀 groups(манifest description 若有提及一併)。

## 誠實呈現

- 校正曲線只畫「你那個組有覆蓋」的年 → 曲線可能變短,這是**正確性換覆蓋**的刻意取捨,UI 文字說明。
- 嚴苛度標明所依組;sel/fem 的 null 在雷達自然缺軸(climb 已有先例)。
- 重算後**量測並回報**:可校正賽事數(原 31)與大擺動場數(原 8/4)的變化——預期大擺動顯著下降;若某場分組後仍 >1.5×,那才可能是真難度事件。

## 測試(照 dev-workflow)

- **pytest**:difficulty——混組輸入(TT+公路)→ 各組各自 baseline/coeff、組年 <20 剔除、組 <2 年剔除、race 無組剔除;DNA——sel 加權(手算對照)、單組退化、全組 <10 → None;fem——known<30% → None、≥30% 照算。
- **vitest**:`calibratedSeries` 嚴格跳過(label 對組、缺覆蓋年跳過、同年取最快);`dominantGroup`;`raceSeverity` 讀最大組 + 回傳 group。
- **build + 抽查**:重建兩 json;/athletes 校正卡(多距離常客選手:曲線合理、說明字)、/race 嚴苛度(標組)、/race DNA 雷達(混距賽事 sel 下降、低性別覆蓋賽事 fem 缺軸)深/淺各一輪。

## 風險與緩解

- **覆蓋縮水**:組內 n 較小,部分場/年掉出門檻——刻意取捨;量測回報實數。若可校正場數暴跌(如 <15),回報後再議是否調門檻(不預先放寬)。
- **RaceSeverity 語意變化**:n 從全場變成最大組——同一序列內自比,verdict 邏輯不變;UI 標組避免誤讀。
- **`h.label` 與組鍵對不上**(髒值):`?? "全部"` 只處理 null;字串不匹配即跳過(嚴格),符合寧缺勿錯。
- **API 消費者**:race_difficulty.json 為公開端點,形狀是 breaking change——API.md 同步更新;此端點無 MCP tool,影響面小。

## YAGNI(不做)

- 不動騎乘分身;不做跨組 fallback;不動 DNA 其他四軸;不加新 UI 元件;不動 dataset/release。
