---
name: 公众号文章-学员版
description: >
  帮老板从一个选题出发，写出一篇 1800-2000 字的公众号文章，并生成可直接复制到
  公众号后台的 HTML 排版。不读死人设档案，完全从老板本地内容库
  （~/Desktop/我的内容库（勿动）/01-黄金五环、02-人设文案、03-人设故事）
  读取身份、口吻和素材，写出来的文章是老板自己的声音，不是 AI 味。
  触发口令（包含以下任意关键词即触发）：
  "公众号"、"写公众号"、"公众号文章"、"帮我写一篇"、"今天写什么"、
  "推送文章"、"出一篇推文"、"搞个公众号内容"、"发一篇公众号"、
  "微信文章"、"公众号发点啥"。
  当用户给了一个话题并提到"公众号"时也触发。
---

# 公众号文章（学员版）

## 执行回执（硬规则）

只要本轮因为 `skill` / `技能` 指名，或因为关键词命中而进入本技能，第一行先写：
`已走技能：公众号文章-学员版`

From topic to published draft — one skill, full pipeline. 从一个话题到可发布的文章，一次走完。

---

## 核心设计：两阶段渐进式

学员装完 skill 第一次用，**一个配置都不要问**。分两阶段：

| 阶段 | 触发时机 | 学员需要做什么 |
|------|---------|--------------|
| 🟢 **阶段 1 首次使用** | 学员第一次说"写公众号文章" | **零配置**。直接读本地内容库 → 写文章 → 生成 HTML 预览 → 学员复制粘贴到公众号后台 |
| 🟡 **阶段 2 升级签名卡** | 学员主动说"想让文章底部有我的头像 / 可跳转到我公众号" | 一次性问 3 件事（头像URL/biz_id/CTA），存到 `~/.wechat-article-config/author-card.json` |

**为什么不做"自动推送到草稿箱"**：需要企业主体公众号 + appid/appsecret + IP 白名单，且白名单一旦换网络（家→公司→咖啡馆→出差）就要重新加，运维负担太重。手动 Ctrl+V 粘贴只要 10 秒，比折腾这套 API 划算。本 skill 不提供自动推送路径。

**硬规则**：
- 首次使用**严禁**索要 biz_id/头像URL 等任何配置项。就是写一篇给他看。
- 只有学员**主动提出**想要某个高级功能时，才进入对应阶段的配置流程。

---

## Phase 0: 读学员本地内容库（声明式，不填表）

**学员的身份不从清华哥的人设档案来，也不从填表来——从学员自己的内容库来。**

固定路径：`~/Desktop/我的内容库（勿动）/`（由"内容库搭建-学员版" skill 维护）

### 读取顺序

```bash
BASE=~/Desktop/我的内容库（勿动）

# 1. 老板画像 — 身份/经历/客户/差异化/金句
ls "$BASE/01-黄金五环/"
# 如果有文件，读取最新一篇（通常是终版）

# 2. 学习老板的写作口吻
ls "$BASE/02-人设文案/" | head -3
# 读 2-3 篇最新的，感受语气/常用词/节奏

# 3. 真实故事素材（开头/细节/案例来源）
ls "$BASE/03-人设故事/" | head -3

# 4. 可选：感受整体表达风格
ls "$BASE/04-热点文案/" "$BASE/05-爆款改写/" "$BASE/06-直播稿/" 2>/dev/null | head -3
```

### 兜底规则

- **01-黄金五环 是空的** → 停住。告诉老板："先跑一次【黄金五环采集-学员版】，把你的老板画像填好。公众号文章要有灵魂，必须先认识你。"**不要硬写**。
- **02-人设文案 / 03-人设故事 是空的** → 可以写，但提示老板："建议先跑一次【人设文案-学员版】和【人设故事（员工视角）-学员版】，这样公众号文章的口吻会更贴近你本人，AI 味会更少。"
- **路径不存在（内容库没搭）** → 告诉老板："先跑一次【内容库搭建-学员版】建好本地内容库。"

### 读取后的行动

读完上面这些文件，在心里形成一份"老板是谁"的认知画像：
- 老板的真实身份（姓名/行业/年头/主要经历）
- 目标客户是谁
- 老板的差异化 / 核心价值
- 老板怎么说话（常用词、句式节奏、爱讲的故事类型）
- 老板的立场和价值观

**严禁**：读完不用。每一个判断、每一句口吻都必须回到这些画像。

---

## Phase 1: 选题与标题

### Mode A: 用户给了一个话题 → 直接做标题

### Mode B: 用户说"今天写什么" / "搜热点" →
1. WebSearch 今天的热点（科技/AI/商业/民生）
2. 过滤：这个热点能不能**连接到老板的行业**？（连接不上的直接筛掉）
3. 给 3 个角度，每个含：热点钩子 + 老板视角的切入点 + 开头第一句草稿
4. 让老板选

### 标题工程

公众号 80% 打开率靠标题。按以下规则出 **3 个备选**：

- 15-25 字（太短没信息量，太长手机折行）
- 必含：一个**情绪触发词** + 一个**身份锚点**（老板/实体人/开店的）
- 可加：一个**悬念缺口**（为什么/怎么做到的/竟然）
- 详见 `references/style-bible.md` Section 2

**输出格式**（必须用数字选项）：

```
请选标题（输入 1 / 2 / 3）：

1. {标题A}
2. {标题B}
3. {标题C}
```

老板选完再进 Phase 2。

---

## Phase 2: 写文章

### 写前必读

- `references/writing-methodology.md` — 7 步骨架 + 公众号适配规则
- `references/style-bible.md` — 通用写作原则 + 六原则 + 六维评分

### 文章结构（1800-2000 字）

按 `writing-methodology.md` 的 7 步骨架：

1. **高冲突开场判断**（2-3 句）
2. **场景重建**（1-2 段，含 1 个真实细节 — 从老板 03-人设故事 里取素材）
3. **角色冲突 / 错位解释**（1 段）
4. **理论锚点**（3-5 句话带过，只给结论）
5. **反转升华**（"你以为…其实…"，1-2 句）
6. **三条行动建议**（每条 2-3 句，第 3 条自然桥接到老板的业务）
7. **结尾金句 + 分享钩子**（1 段）

**字数硬规则**：
- 目标 1800-2000 字
- 超过 2000 字 → 砍场景描写冗余 / 合并重复判断
- 少于 1800 字 → 补一个真实细节 / 加一个行动建议的展开

### 写前先出大纲（避免写完才发现方向不对）

给老板看 5-7 行大纲：

```
📋 大纲预览
- 开场判断：{用什么场景/判断开头}
- 中段论点：{核心论点 1-2 个}
- 业务植入位置：{第几段/怎么植入}
- 结尾落点：{金句方向}

OK 就回复 "继续"，要调就告诉我调哪里。
```

### 业务植入规则

- 前 30% **禁止**出现产品名/课程名/价格
- 第三条行动建议或结尾金句之前 → 自然桥接到老板自己的业务
- 桥接不是硬推销，是"我一直在做这件事 → 我的工具/方法/产品能帮你一起走"

### 写后三层自检（必输出）

**Layer 1: 六原则逐段扫描**（`style-bible.md` Section 6）

逐段检查 6 条：

1. ✅ 每个重要判断先给了结论？（原则①先定性再解释）
2. ✅ 没有不必要的否定/撇清？（原则②不此地无银）
3. ✅ 关键动作后面有"因为"？（原则③给理由建信任）
4. ✅ 朗读一遍没有书面感重的词？（原则④口语化但精准）
5. ✅ 场景描写有 ≥1 个真实细节？（原则⑤用细节建画面）
6. ✅ 叙事基调是"我选择"不是"我被迫"？（原则⑥主动性）

**任何一条不通过 = 修改该段重写自检。**

**Layer 2: 六维评分**（`style-bible.md` Section 4）

开场抓取力 / 结构推进力 / 人设可信度 / 业务植入丝滑度 / 听感可读性 / 风险控制，
每项 20 分共 120 分。**必须 ≥105 且单项 ≥16**。

**Layer 3: 一票否决**

触发任一 = 整篇重写：
- 恐吓式焦虑推转化
- 虚构人物/数据/案例/结果
- 明显夸张或做不实承诺
- 硬推销导致真诚感丧失

### 自检报告格式（必须输出）

```
📋 质量自检:
字数: {实际字数} (目标 1800-2000)
六原则: ✅✅✅✅✅✅ (6/6 通过)
六维评分: 108/120 (最低项 17)
一票否决: 无触发
```

---

## Phase 3: HTML 转换（V3 Clean 模板）

### Step 1：读视觉标准

```
assets/template-v3-clean.html — V3 Clean 黄金模板
```

这是本 skill 的**唯一模板入口**。不要切其他模板。

### Step 2：生成 HTML

骨架：

```html
<div class="wrapper">
  <div class="hero">
    <div class="hero-badge">{2-4字标签 如"老板必看"}</div>
    <div class="hero-title">{6-10字核心判断，关键词用 .hero-highlight 黄色高亮}</div>
    <div class="hero-subtitle">{关键词A · 关键词B · 关键词C}</div>
  </div>
  <div class="article-body">
    <div class="content">
      正文
    </div>
  </div>

  底部签名区 - 阶段 1 用纯文字版 / 阶段 2 读 author-card.json
  <div class="footer-fixed">
    见 Phase 3.5 签名区生成规则
  </div>
</div>
```

### 视觉节奏必检项（不通过 = 重做）

- [ ] **Hero 横幅开场**（不要 emoji 开场，用 `.hero-badge` 替代）
- [ ] **Callout 卡片 ≥ 2 个**（灰红 `.callout` / 蓝 `.callout-blue` / 绿 `.callout-green`）
- [ ] **金句高亮框 ≥ 1 个**（`.golden`）
- [ ] **连续正文段落 ≤ 4 段**（超过插 callout / 金句 / 分隔线）
- [ ] **分隔线 `· · ·`** — 每个大章节之间一个
- [ ] **Section 标题带 emoji + 暖色底**
- [ ] **≥ 1 个数据可视化**（stat-card / timeline / compare-row / step-list）
- [ ] **荧光笔高亮 1-2 处**（`.highlight-line`）

**⚠️ 不要在 HTML 中写标题/作者/日期栏** — 微信推送时自动添加。正文直接从 Hero 开始。

**⚠️ 不要写 HTML 注释**（尖括号加叹号加两个减号那种） — 微信会变成可见文字。

### V3 Clean 色板（硬规则，不要私自改）

- 主强调色: `#d4380d`（红棕）
- 金句底: `linear-gradient(135deg, #fff7e6, #ffe7ba)`
- Callout 灰: `#f6f8fa` + 左线 `#d4380d`
- Callout 蓝: `#f0f5ff` + 左线 `#1890ff`
- 正文: `16px` / `line-height:2` / `color:#333`
- 圆角统一: `10px`-`12px`

### 微信兼容性

**可以用**：`<style>` 块 + CSS class（脚本自动内联）、`display:flex` / `gap` / `flex:1` / `linear-gradient` / `box-shadow` / `border-radius` / `text-shadow`

**禁用**：`::before` / `::after` / `clip-path` / `clamp()` / CSS animation / CSS Grid / 外部字体 / 非 `mmbiz.qpic.cn` 域名的图片 / `position:relative`（会被微信自动移除）

---

## Phase 3.5: 签名区生成（两阶段核心分流点）

### 🟢 阶段 1：纯文字签名区（首次使用 / author-card.json 不存在）

**检测**：
```bash
test -f ~/.wechat-article-config/author-card.json || echo "走阶段1"
```

**从 01-黄金五环 提取**：
- 老板姓名 → `author_name`
- 一句话介绍（经历+差异化）→ `author_tagline`
- 价值观金句 → `ending_motto`

**模板**：

```html
<div class="footer-fixed">
  <div class="footer-divider">— — —</div>
  <div class="sign-motto-box">
    <div class="sign-motto">"{从黄金五环提取的金句}"</div>
  </div>
  <div class="author-card-text">
    <div class="author-name">{姓名}</div>
    <div class="author-tagline">{一句话介绍}</div>
  </div>
</div>
```

**不放**：头像、公众号跳转链接、CTA 按钮。

**生成后告诉老板**：
```
💡 提示：现在你的签名卡是纯文字版。
如果想让底部显示你的头像并且可以点击跳转到你的公众号主页，
任何时候跟我说"配置签名卡"就行（需要 3 个信息，一次配好）。
```

### 🟡 阶段 2：完整签名卡（author-card.json 存在）

**读取**：
```bash
cat ~/.wechat-article-config/author-card.json
```

**模板**：照原 V3 Clean 的 `.footer-fixed` 结构，用 `author-card.json` 里的字段填充。所有 `{{变量}}` 做字符串替换，空字段就跳过对应行。

### Visual self-check（必输出）

```
📋 视觉自检:
✅ Callout 卡片: {N} 个 (≥2 ✓)
✅ 金句高亮框: {N} 个 (≥1 ✓)
✅ 连续正文: 最长 {N} 段 (≤4 ✓)
✅ 分隔线: {N} 个 ✓
✅ Section 标题带暖色底: {N} 个 ✓
✅ 数据可视化: {组件类型} ✓
✅ 荧光笔高亮: {N} 处 ✓
✅ 签名区: {阶段 1 纯文字 / 阶段 2 完整卡} ✓
```

---

## Phase 4: 预览 + 发布引导（默认路径）

> **学员是实体老板，不会 python**。本 Phase 所有命令都是 LLM（你）替学员跑的。**学员永远只看浏览器预览页**——不看终端、不看路径、不看 traceback。

### Step 1: 一段 Python 跑完所有发布步骤（LLM 唯一调用点）

**⚠️ 硬规则**：

1. **不要用 `python3` / `python` 命令名**调脚本（Windows 默认只有 `python`，没 `python3`；Linux 反过来）。**统一用 Python `subprocess` + `sys.executable`**——它自动找到当前 Python 解释器，跨平台 100% OK。
2. **不要用 shell 变量 `${TMPDIR:-/tmp}`** 算路径（Windows PowerShell/cmd 不认）。**统一用 `tempfile.gettempdir()`**。

把下面这一段 Python **整段执行**（你应该有跑 Python 代码的能力——和 Phase 0 / Phase 3 写文件一样）：

```python
import sys, os, subprocess, tempfile

# 1. 环境前置检查（缺 bs4 自动装）
try:
    import bs4  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "beautifulsoup4"], check=True)

# 2. 算跨平台临时目录 + 写 raw HTML
preview_dir = os.path.join(tempfile.gettempdir(), "preview")
os.makedirs(preview_dir, exist_ok=True)
raw_path = os.path.join(preview_dir, "wechat_article_raw.html")
with open(raw_path, "w", encoding="utf-8") as f:
    f.write(RAW_HTML)  # 你刚生成的 V3 Clean HTML 字符串

# 3. 调 run_pipeline.py（用 sys.executable 自动用对的 Python，无需纠结 python/python3）
script = os.path.join(os.getcwd(), "scripts", "run_pipeline.py")
if not os.path.exists(script):
    raise RuntimeError(f"找不到 run_pipeline.py（当前目录: {os.getcwd()}）。检查 skill 安装路径。")

result = subprocess.run(
    [sys.executable, script, raw_path],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
print(result.stdout)
if result.returncode != 0:
    # 你（LLM）看到 stderr → 自己 debug，不要丢给学员
    print("⚠️ run_pipeline 报错（LLM 处理，不要让学员看）:", result.stderr, file=sys.stderr)
    raise RuntimeError("run_pipeline 失败，需要 LLM 介入 debug")
```

`run_pipeline.py` 内部按顺序跑三步，**Windows / macOS / Linux 全兼容**：

1. **转微信标记**：raw HTML → `wechat_article.html`（含 `<section>` / `<span leaf="">` / `<mp-style-type>`）
2. **塞剪贴板**（兜底）：把微信版以 `text/html` MIME 写进系统剪贴板（macOS osascript / Windows PowerShell .NET / Linux xclip）。**Windows 端用 `[System.IO.File]::ReadAllText` + UTF-8 显式编码读取**，规避中文乱码
3. **弹增强预览页**：浏览器自动打开 `wechat_article_preview.html`，**右上角浮动「📋 一键复制到公众号」红橙按钮**

### Step 2: 学员看到的最终结果

学员的浏览器自动弹一个文章预览页，**右上角一定有红橙色按钮**。两条粘贴姿势：

- **路 A（推荐）**：直接切公众号后台 → Ctrl+V（Mac: Cmd+V）→ 一粘到位
- **路 B（剪贴板被覆盖时兜底）**：在预览页点右上角按钮 → 看到 toast「✅ 已复制」或「✅ 已复制（兼容模式）」→ 切公众号后台 Ctrl+V

按钮 JS 三段式回退（应付任何浏览器/协议组合）：
1. `ClipboardItem` API（现代 Chrome / Edge / Safari，安全上下文 + user gesture）
2. `execCommand('copy')` + 隐藏 `contenteditable`（Windows file:// 协议下被拒绝 ClipboardItem 时兜底，墨滴 / Markdown Nice 长期姿势）
3. `writeText` 纯源码（最后兜底，几乎不会到）

学员**全程只看浏览器**，不需要看终端、不需要敲任何命令。

### Step 3: 告诉学员怎么发（LLM 输出给学员看的话术）

```
✅ 文章写好了！浏览器应该已经弹出来一个预览页。

📋 下一步（一粘即发）：
1. 看一眼浏览器预览页排版，没问题就走下一步
2. 打开 mp.weixin.qq.com → 新建图文消息
3. 在编辑区直接 Ctrl+V（Mac: Cmd+V）← 排版会完整粘进去
4. 标题填《{刚才选的标题}》
5. 摘要填：{自动生成的摘要}
6. (可选) 上传封面图 → 点"保存为草稿"或"发布"

⚠️ 注意：
- 不要点"粘贴为纯文本"，选默认粘贴就行
- 万一粘贴上去是空的或者排版乱了，回到浏览器预览页右上角点【📋 一键复制到公众号】按钮，再去公众号后台 Ctrl+V 一次
```

**⚠️ 学员可见话术绝对禁止内容（铁律）**：
- 任何文件路径（`C:\Users\...` / `/var/folders/...` / `~/.cache/...`）
- 任何命令（`python ...` / `pip install ...`）
- 任何 traceback 或错误堆栈
- 任何"在终端里跑这个"的指引

### 故障兜底（如果 run_pipeline.py 跑挂了）

**你（LLM）自己 debug，不要丢锅给学员**。所有调用都用 Python `subprocess` + `sys.executable` 模式，绝不直接 shell 调 `python` / `python3`：

```python
import sys, subprocess, os

# 单独跑某一步定位问题
SCRIPTS = os.path.join(os.getcwd(), "scripts")

# 单独转换
subprocess.run([sys.executable, os.path.join(SCRIPTS, "convert_to_wechat_markup.py"),
                "--input", raw_path, "--output", wechat_path, "--meta", meta_path], check=True)

# 单独塞剪贴板
subprocess.run([sys.executable, os.path.join(SCRIPTS, "copy_html_to_clipboard.py"),
                wechat_path], check=True)

# 单独弹预览
subprocess.run([sys.executable, os.path.join(SCRIPTS, "open_preview.py"),
                raw_path], check=True)
```

**最后兜底**：如果以上全挂了，把生成的 `wechat_article_preview.html` **绝对路径用 `file://` 协议**告诉学员"双击这个文件打开"——但**不要让学员敲任何命令**。

---

## Phase 5: 封面图（可选，不强推）

**只在老板主动说"要封面"或"生成一下封面"时做。** 默认不生成——因为公众号后台自带封面编辑器，很多老板习惯在后台弄。

如果老板要：

1. 从标题提取 2-6 字核心短语
2. 挑一个 2-4 字标签（"老板必看" / "AI实战" / "实体获客" / 行业词）
3. 生成（用 Python subprocess + sys.executable 模式，跨平台）：

```python
import sys, os, subprocess, tempfile

preview_dir = os.path.join(tempfile.gettempdir(), "preview")
cover_path = os.path.join(preview_dir, "cover.jpg")
script = os.path.join(os.getcwd(), "scripts", "generate_cover.py")

subprocess.run([sys.executable, script,
                "--title", "{主标题}",
                "--label", "{标签}",
                "--output", cover_path], check=True)
```

4. 规格 900×383（微信 2.35:1）

---

## Phase 6: 签名卡配置（仅在阶段 2 触发时走）

**触发条件**：老板说"配置签名卡" / "想让文章底部有我头像" / "让读者能跳转我公众号"。

### 引导对话

```
好，配置签名卡我要问你 3 件事，一次配好以后所有文章自动用：

1️⃣ 你公众号的头像（微信永久图片 URL）
   怎么拿：公众号后台 → 素材管理 → 图片 → 上传一张头像 → 右键图片 → 复制图片地址
   （URL 一定是 mmbiz.qpic.cn 开头的，外部图床微信会屏蔽）

2️⃣ 你公众号主页的 __biz 参数
   怎么拿：发你公众号任意一篇历史文章的链接给我，我自己从里面提取
   （链接里 __biz= 后面那一串等号结尾的）

3️⃣ CTA 话术（底部引导关注的一句话）
   比如："关注我，每周讲一个实体老板的真实问题"
   "想链接更多实体老板，在公众号留言"

我等你发 3 个信息过来，一次配好。
```

### 配置落盘

**Step 1: 跑配置迁移脚本**（必须，否则可能 mkdir 失败）

```python
# 检测 ~/.wechat-article-config 是文件还是目录
# - 是目录或不存在 → 啥都不做
# - 是文件（旧版 skill 留下的） → 备份到 ~/.wechat-article-config-legacy.json
#   并升级为目录形式，自动迁移合法的 wechat API JSON
import sys, os, subprocess
script = os.path.join(os.getcwd(), "scripts", "migrate_legacy_config.py")
subprocess.run([sys.executable, script], check=True)
```

**Step 2: 写入 author-card.json**

```bash
# 组装 author-card.json：
# - author_name / author_tagline / ending_motto → 从 01-黄金五环 自动提取
# - author_avatar_url / mp_biz_id / cta_title → 老板提供
# - author_slogan_1/2 / cta_subtitle / ending_motto_sub → 可选，有就填没有就空
cat > ~/.wechat-article-config/author-card.json <<'EOF'
{...}
EOF
```

### 确认

```
✅ 签名卡已配置。以后写公众号自动用这套。
想改的话随时跟我说"改签名卡"。

📍 配置文件位置：~/.wechat-article-config/author-card.json
（你可以直接编辑这个文件，也可以跟我说改哪项）
```

---

## 严禁事项（学员版铁律）

1. **严禁** 在首次使用时索要 biz_id / 头像URL / CTA 等任何配置项（这些只在学员主动要"配置签名卡"时才问）
2. **严禁** 跳过 `01-黄金五环` 硬写文章。没画像 = 让老板先跑黄金五环采集
3. **严禁** 用清华哥的语言 DNA、金句、经历去写老板的文章
4. **严禁** 在文章里编造老板没有的数据、案例、人物、经历
5. **严禁** 写完不做六原则 + 六维评分 + 一票否决的三层自检
6. **严禁** 字数超过 2000（超过就砍，不给特殊情况加字数）
7. **严禁** 把 `/tmp/` 写死在脚本或指令里，或用 bash 语法 `${TMPDIR:-/tmp}` 算路径（Windows PowerShell/cmd 不认 → 路径错位 → 一键复制按钮不显示）。**统一用 Python 的 `tempfile.gettempdir()`**
8. **严禁** 在 HTML 中写注释、`::before/after`、外部图床、CSS 动画
9. **严禁** 调用任何公众号推送 API（本 skill 已下线自动推送，统一走 HTML 预览 + 一键复制 + 学员手动 Ctrl+V）
10. **严禁** 选项用 ABC（用数字 1 / 2 / 3）
11. **严禁** 把任何 `python3 / pip / shell` 命令、文件绝对路径、终端操作丢给学员手敲——学员是实体老板，看到命令文字会直接劝退。所有命令都是 LLM（你）替学员跑的，学员全程**只看浏览器预览页**。命令跑挂了你（LLM）自己 debug，**绝对不要让学员碰终端**
12. **严禁** 直接用 shell 调用 `python3 scripts/xxx.py` 或 `python scripts/xxx.py`——Windows 学员系统默认只有 `python` 命令、没有 `python3`；Linux/macOS 反过来。**统一用 Python `subprocess.run([sys.executable, script, ...])` 模式**，sys.executable 自动找对的 Python 解释器
13. **严禁** 把 traceback / 错误堆栈 / 文件路径泄漏到学员可见的话术里。出错时 LLM 自己消化，告诉学员的话术只能是"重新跑一次"或"系统繁忙稍后再试"这种业务语言
14. **严禁** 假设学员装了 bs4 / requests 等任何第三方包——首次跑前必须 `try: import bs4 except ImportError: subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "beautifulsoup4"])` 自动装齐
