# V2 视觉设计标准 — 公众号文章排版规范

> 本文件定义了公众号文章 V2（亮色杂志风）的**完整视觉规范**。
> AI 生成 HTML 时必须严格对齐以下数值，不允许"大概差不多"。
> 所有样式必须内联（WeChat 硬约束），不允许 `<style>` / `<script>` / `::before` / `::after` / `clip-path` / `clamp()` / CSS 动画。

---

## 1. 全局基础

```
body:
  margin: 0
  padding: 0
  font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif
  background: #faf8f5
  color: #1a1a1a
  -webkit-font-smoothing: antialiased

content-wrapper（正文区域）:
  max-width: 680px
  margin: 0 auto
  padding: 0 20px
```

---

## 2. 排版基础

| 元素 | 字号 | 行高 | 颜色 | 字重 | margin-bottom |
|---|---|---|---|---|---|
| 正文段落 | 17px | 2.1 | #333 | 400 | 22px |
| 正文加粗 | 同上 | 同上 | #1a1a1a | 700 | — |
| section 标题 | 26px | 1.3 | #1a1a1a | 900 | — |
| callout 文字 | 19px | 1.8 | 按颜色 | 600 | — |
| action-card 标题 | 18px | — | #1a1a1a | 700 | 8px |
| action-card 描述 | 15px | 1.9 | #555 | 400 | — |
| 签名名字 | 22px | — | #1a1a1a | 900 | 8px |
| 签名描述 | 14px | 2 | #888 | 400 | — |

---

## 3. 组件库（12 个核心组件）

### 3.1 Hero 头图区

位于文章最顶部，全宽紫色渐变，居中排版。

```html
<section style="position:relative;padding:60px 24px 50px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);text-align:center;overflow:hidden;">
  <div style="font-size:60px;margin-bottom:16px;position:relative;z-index:1;">🚀</div>
  <div style="font-size:13px;letter-spacing:4px;color:rgba(255,255,255,0.7);margin-bottom:16px;position:relative;z-index:1;">{{author_name}} · 副标签</div>
  <h1 style="font-size:42px;font-weight:900;color:#fff;line-height:1.2;position:relative;z-index:1;text-shadow:0 4px 20px rgba(0,0,0,0.15);margin:0;">主标题</h1>
  <p style="font-size:15px;color:rgba(255,255,255,0.8);margin-top:16px;line-height:1.8;font-weight:300;position:relative;z-index:1;">副标题</p>
</section>
```

**关键数值**：
- padding: `60px 24px 50px`
- 标题: `42px`, `font-weight:900`, 带 `text-shadow`
- 大 emoji: `60px`
- 标签: `13px`, `letter-spacing:4px`, `rgba(255,255,255,0.7)`
- 副标题: `15px`, `rgba(255,255,255,0.8)`, `font-weight:300`

---

### 3.2 Section 标题（带图标徽章）

每个大章节的标题，用 flex 布局，左侧 48px 图标 + 右侧标题。底部 2px 分隔线。

```html
<div style="display:flex;align-items:center;gap:14px;margin:50px 0 24px;padding-bottom:12px;border-bottom:2px solid #eee;">
  <div style="width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;background:linear-gradient(135deg,#f0ebff,#e8e0ff);">💬</div>
  <div style="font-size:26px;font-weight:900;color:#1a1a1a;line-height:1.3;">标题文字</div>
</div>
```

**关键数值**：
- 上间距: `50px`（营造呼吸感！不能小于 40px）
- 下间距: `24px`
- 图标: `48×48px`, `border-radius:14px`, 各 section 用不同渐变色
- 标题: `26px`, `font-weight:900`
- 底线: `2px solid #eee`

**图标渐变色参考**：
- 紫色: `linear-gradient(135deg,#f0ebff,#e8e0ff)` — 通用/观点
- 蓝色: `linear-gradient(135deg,#eaf2ff,#d6e8ff)` — 分析/思考
- 红色: `linear-gradient(135deg,#fff0ed,#ffe8e3)` — 警告/情感
- 绿色: `linear-gradient(135deg,#eafaf1,#d5f5e3)` — 行动/方法
- 橙色: `linear-gradient(135deg,#fff8ed,#fff0d6)` — 踩坑/经验

---

### 3.3 Callout 卡片（5 色）

强调句/金句/核心观点。圆角 16px，左侧 4px 色条，渐变背景。

```html
<div style="padding:24px 24px 24px 28px;margin:28px 0;border-radius:16px;font-size:19px;font-weight:600;line-height:1.8;background:linear-gradient(135deg,{bg1},{bg2});color:{textColor};border-left:4px solid {accentColor};">
  <strong>卡片内容</strong>
</div>
```

**5 种颜色的精确色值**：

| 颜色 | background-gradient | text color | border-left |
|---|---|---|---|
| 紫 | `#f0ebff, #e8e0ff` | `#4a2fbd` | `#7c5ce7` |
| 红 | `#fff0ed, #ffe8e3` | `#c0392b` | `#e74c3c` |
| 绿 | `#eafaf1, #d5f5e3` | `#1e8449` | `#27ae60` |
| 蓝 | `#eaf2ff, #d6e8ff` | `#2471a3` | `#3498db` |
| 橙 | `#fff8ed, #fff0d6` | `#b7791f` | `#f39c12` |

**使用原则**：
- 紫色: 核心观点、金句、结论
- 红色: 警告、反面案例、痛点
- 绿色: 好消息、正面结论、鼓励
- 蓝色: 客观分析、比喻、类比
- 橙色: 踩坑提醒、补充说明、CTA
- **一篇文章至少用 3 种颜色**，避免视觉单调

---

### 3.4 分隔线（Emoji Divider）

用于章节之间的过渡，提供呼吸感。

```html
<div style="display:flex;align-items:center;justify-content:center;gap:12px;margin:36px 0;color:#ccc;">
  <div style="flex:1;height:1px;background:#e8e8e8;"></div>
  <span style="font-size:18px;">💡</span>
  <div style="flex:1;height:1px;background:#e8e8e8;"></div>
</div>
```

**关键数值**：
- margin: `36px 0`（不能小于 30px）
- 线: `1px`, `#e8e8e8`
- emoji: `18px`
- **每 3-5 个内容块之间必须有一个分隔线**

---

### 3.5 双列对比卡片（Phone Visual）

用于并列对比（before/after、A/B、两个数据）。非常有视觉冲击力。

```html
<div style="display:flex;margin:28px 0;">
  <div style="flex:1;padding:28px 20px;border-radius:20px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.06);background:linear-gradient(135deg,#f093fb,#f5576c);color:#fff;margin-right:16px;">
    <div style="font-size:32px;margin-bottom:10px;">💸</div>
    <div style="font-size:42px;font-weight:900;line-height:1;margin-bottom:8px;">数据</div>
    <div style="font-size:13px;opacity:0.85;line-height:1.6;">说明文字</div>
  </div>
  <div style="flex:1;padding:28px 20px;border-radius:20px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.06);background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;">
    <div style="font-size:32px;margin-bottom:10px;">⚡</div>
    <div style="font-size:42px;font-weight:900;line-height:1;margin-bottom:8px;">数据</div>
    <div style="font-size:13px;opacity:0.85;line-height:1.6;">说明文字</div>
  </div>
</div>
```

**关键数值**：
- 两卡用 `flex:1` 等宽，间距用 `margin-right:16px`
- 大数字: `42px`, `font-weight:900`
- 圆角: `20px`
- shadow: `0 4px 20px rgba(0,0,0,0.06)`

**可用渐变组合**：
- 粉红: `linear-gradient(135deg,#f093fb,#f5576c)` — 痛点/旧方式
- 紫色: `linear-gradient(135deg,#667eea,#764ba2)` — 亮点/新方式
- 绿色: `linear-gradient(135deg,#43e97b,#38f9d7)` — 正面/增长

---

### 3.6 Tag 标签云

用于罗列多个关键词/数据点/标签。药丸形状。

```html
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:22px 0;">
  <span style="padding:10px 18px;border-radius:50px;font-size:14px;font-weight:600;display:inline-flex;align-items:center;gap:6px;background:#f0ebff;color:#7c5ce7;">🔥 标签内容</span>
  <span style="padding:10px 18px;border-radius:50px;font-size:14px;font-weight:600;display:inline-flex;align-items:center;gap:6px;background:#fff0ed;color:#e74c3c;">💳 标签内容</span>
  <span style="padding:10px 18px;border-radius:50px;font-size:14px;font-weight:600;display:inline-flex;align-items:center;gap:6px;background:#eafaf1;color:#27ae60;">✅ 标签内容</span>
</div>
```

**5 种 Tag 色值**：
| 编号 | background | color |
|---|---|---|
| t1 | `#fff0ed` | `#e74c3c` |
| t2 | `#fff8ed` | `#f39c12` |
| t3 | `#eafaf1` | `#27ae60` |
| t4 | `#f0ebff` | `#7c5ce7` |
| t5 | `#eaf2ff` | `#3498db` |

---

### 3.7 全宽渐变色块（Colored Section）

**视觉高潮组件**——全宽渐变背景，居中大文字。用于强化核心信息。

```html
</div><!-- 先关闭 content-wrapper -->
<section style="margin:40px 0 0;padding:40px 24px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;text-align:center;">
  <div style="max-width:680px;margin:0 auto;">
    <div style="font-size:48px;margin-bottom:16px;">🚀</div>
    <div style="font-size:28px;font-weight:900;line-height:1.4;margin-bottom:12px;">大标题</div>
    <div style="font-size:16px;line-height:1.9;opacity:0.9;">说明文字</div>
  </div>
</section>
<div style="max-width:680px;margin:0 auto;padding:0 20px;"><!-- 重新打开 content-wrapper -->
```

**3 种渐变组合**：
| 名称 | gradient | text color |
|---|---|---|
| 紫色 | `#667eea → #764ba2` | `#fff` |
| 粉红 | `#f093fb → #f5576c` | `#fff` |
| 绿色 | `#43e97b → #38f9d7` | `#1a1a1a` |

**使用原则**：
- **一篇文章至少 2-3 个**（这是与普通排版拉开差距的关键！）
- 放在章节转折点，打断阅读节奏，制造视觉高潮
- 需要先关闭 `content-wrapper`，让色块全宽，再重新打开
- emoji: `48px`，标题: `28px font-weight:900`

---

### 3.8 Action 编号卡片

用于"三个建议/三件事/三步走"的列表呈现。白底卡片 + 渐变数字徽章。

```html
<div style="display:flex;flex-direction:column;gap:20px;margin:28px 0;">
  <div style="display:flex;gap:20px;align-items:flex-start;padding:24px;border-radius:20px;background:#fff;box-shadow:0 4px 20px rgba(0,0,0,0.06);border:1px solid rgba(0,0,0,0.04);">
    <div style="width:52px;height:52px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900;flex-shrink:0;color:#fff;background:linear-gradient(135deg,#667eea,#764ba2);">1</div>
    <div style="flex:1;">
      <div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:8px;">建议标题 💬</div>
      <div style="font-size:15px;line-height:1.9;color:#555;">详细描述。<strong style="color:#1a1a1a;">加粗重点。</strong></div>
    </div>
  </div>
  <!-- 第 2 张用 #f093fb,#f5576c 粉红渐变 -->
  <!-- 第 3 张用 #43e97b,#38f9d7 绿色渐变，文字色 #1a1a1a -->
</div>
```

**关键数值**：
- 徽章: `52×52px`, `border-radius:16px`
- 卡片: `padding:24px`, `border-radius:20px`
- shadow: `0 4px 20px rgba(0,0,0,0.06)`
- border: `1px solid rgba(0,0,0,0.04)`

---

### 3.9 Phase 卡片（Day 时间线变体）

与 Action 卡片结构相同，但徽章内容为文字（如 D1-4, D5-7）而非数字。适合展示阶段/时间线。

```html
<!-- 结构同 3.8，徽章内容改为: -->
<div style="...font-size:16px;...">D1-4</div>  <!-- 紫色渐变 -->
<div style="...font-size:16px;...">D5-7</div>  <!-- 粉红渐变 -->
<div style="...font-size:14px;...">D8+</div>   <!-- 绿色渐变 -->
```

**注意**：文字较长时 font-size 需适当缩小（16px → 14px），保持不换行。

---

### 3.10 签名卡片

文章末尾的作者签名。白底居中，头像圆形渐变。

```html
<div style="margin:48px 0 20px;padding:32px;border-radius:24px;background:#fff;box-shadow:0 4px 20px rgba(0,0,0,0.06);text-align:center;border:1px solid rgba(0,0,0,0.04);">
  <div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;font-size:28px;color:#fff;font-weight:900;margin:0 auto 16px;box-shadow:0 4px 15px rgba(102,126,234,0.3);">{{姓氏首字}}</div>
  <div style="font-size:22px;font-weight:900;color:#1a1a1a;margin-bottom:8px;">{{author_name}}</div>
  <div style="font-size:14px;color:#888;line-height:2;">
    {{author_tagline}}<br>
    {{author_slogan_1}}
  </div>
</div>
```

---

### 3.11 底部 CTA 卡片

签名下方的关注引导。渐变紫色背景。

```html
<div style="margin:20px 0 40px;padding:24px;border-radius:20px;background:linear-gradient(135deg,#667eea,#764ba2);text-align:center;color:#fff;">
  <p style="font-size:15px;line-height:1.8;opacity:0.9;margin:0;">👆 引导文案</p>
</div>
```

---

### 3.12 正文段落

最基础的组件，但不能出错。

```html
<p style="font-size:17px;line-height:2.1;color:#333;margin-bottom:22px;">正文内容</p>
<p style="font-size:17px;line-height:2.1;color:#333;margin-bottom:22px;">段落中<strong style="color:#1a1a1a;">加粗部分</strong>保持同字号。</p>
```

---

## 4. 视觉节奏规则（最重要！）

一篇好的公众号文章，视觉上必须**有节奏感**，像音乐一样有高低起伏。

### 4.1 必须满足的节奏约束

| 规则 | 最低要求 |
|---|---|
| 全宽渐变色块数量 | ≥ 2 个（推荐 3 个） |
| Callout 颜色种类 | ≥ 3 种不同颜色 |
| 分隔线数量 | 每 3-5 个内容块之间放一个 |
| Section 标题数量 | ≥ 3 个 |
| 正文段落最大连续数量 | 不超过 3 段连续正文（必须插入视觉组件打断） |
| 双列/Tag/卡片等丰富组件 | 至少出现 2 种 |

### 4.2 推荐的文章编排节奏

```
HERO
├── Section 标题
├── 1-2 段正文
├── Callout（紫/红）
├── 1-2 段正文
├── Divider ✦
├── Section 标题
├── 1-2 段正文
├── 双列对比卡 / Tag 标签云
├── 1-2 段正文
├── Divider ✦
├── Section 标题
├── Callout（蓝/绿）
├── 1 段正文
├── ════ 全宽渐变色块 1 ════
├── Callout
├── Action/Phase 卡片（3 个）
├── Callout
├── Divider ✦
├── Section 标题
├── 1-2 段正文
├── Action 卡片（3 个）
├── ════ 全宽渐变色块 2（CTA） ════
├── Divider ✦
├── Section 标题
├── Callout（绿）
├── 2-3 段正文
├── ════ 全宽渐变色块 3（金句结尾） ════
├── Callout（橙，点在看引导）
├── 签名卡片
└── 底部 CTA 卡片
```

### 4.3 组件间距速查

| 组件 → 下一组件 | margin |
|---|---|
| Hero → content-wrapper | 0（content-wrapper 内第一个 section-header 自带 margin-top:50px） |
| section-header → 正文/callout | 24px（header 自带 padding-bottom:12px） |
| 正文段落 → 正文段落 | 22px |
| 正文 → callout | callout 自带 margin-top:28px |
| callout → 正文 | callout 自带 margin-bottom:28px |
| 正文/callout → divider | divider 自带 margin-top:36px |
| divider → section-header | section-header 自带 margin-top:50px |
| 正文 → 全宽色块 | 先关闭 content-wrapper，色块自带 margin-top:40px |
| 全宽色块 → 正文 | 重新打开 content-wrapper，第一个组件的 margin-top 即可 |

---

## 5. WeChat 硬约束清单

生成 HTML 时**绝对不能出现**的内容：

- [ ] `<style>` 标签
- [ ] `<script>` 标签
- [ ] `::before` / `::after` 伪元素
- [ ] `clip-path`
- [ ] `clamp()` 函数
- [ ] CSS 动画 / `@keyframes`
- [ ] 外部字体引用
- [ ] CSS Grid（用 flex 替代）
- [ ] `position: fixed` / `position: sticky`
- [ ] 外部图片链接（需用微信素材 URL 或省略）

**可以安全使用的**：
- [x] `display: flex` + `gap`
- [x] `border-radius`
- [x] `box-shadow`
- [x] `linear-gradient()` 在 background 中
- [x] `text-shadow`
- [x] `opacity`
- [x] `border-left` 代替 `::before` 做色条

---

## 6. 色彩体系总览

### 主色板
| 用途 | 色值 |
|---|---|
| 页面背景 | `#faf8f5` |
| 正文色 | `#333` |
| 标题色 | `#1a1a1a` |
| 辅助色 | `#555` |
| 弱色 | `#888` |
| 线条 | `#e8e8e8` / `#eee` |

### 渐变色板
| 名称 | 渐变 | 用途 |
|---|---|---|
| 紫色渐变 | `#667eea → #764ba2` | Hero、色块、徽章、CTA |
| 粉红渐变 | `#f093fb → #f5576c` | 色块、徽章、对比卡 |
| 绿色渐变 | `#43e97b → #38f9d7` | 色块、徽章（文字用 #1a1a1a） |

### Callout 色板
（见 3.3 节表格）

### Tag 色板
（见 3.6 节表格）
