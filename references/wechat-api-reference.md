# 微信公众号API推送参考

## 前置条件

1. 已认证的微信公众号（服务号或已认证订阅号）
2. AppID 和 AppSecret（mp.weixin.qq.com → 开发 → 基本配置）
3. 服务器IP白名单已添加（同一页面）

## API调用流程

### 第1步：获取 access_token

```bash
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET"
```

返回：
```json
{"access_token": "TOKEN_STRING", "expires_in": 7200}
```

注意：
- token有效期2小时
- 每天获取次数有限制（2000次），不要频繁调用
- 如果报错 `{"errcode":40164}`，是IP白名单问题，需要把报错信息中的IP加到白名单

### 第2步：上传封面为永久素材

```bash
curl -s -F "media=@/path/to/cover.jpg" \
  "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=TOKEN&type=thumb"
```

返回：
```json
{"media_id": "MEDIA_ID_STRING", "url": "..."}
```

注意：
- type 必须是 `thumb`（缩略图类型）
- 图片格式支持 jpg/png
- 封面推荐尺寸 900x383（2.35:1比例）
- 永久素材有数量上限（5000个图文素材）

### 第3步：创建草稿

```bash
curl -s -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=TOKEN" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

payload.json 格式：
```json
{
  "articles": [
    {
      "title": "文章标题",
      "author": "作者名",
      "digest": "摘要（不超过120字）",
      "content": "<p style=\"...\">文章HTML内容（全部内联样式）</p>",
      "thumb_media_id": "上一步获取的MEDIA_ID",
      "need_open_comment": 1,
      "only_fans_can_comment": 0
    }
  ]
}
```

返回：
```json
{"media_id": "DRAFT_MEDIA_ID"}
```

注意：
- content 中的HTML必须全部使用内联样式
- 不支持 `<style>` 标签、JavaScript、外部CSS
- 不支持 CSS 动画、伪元素
- 图片 src 必须使用微信素材URL（通过uploadimg接口上传）或不使用图片
- JSON中的HTML内容需要正确转义引号
- `position:relative` 会被 API 自动移除（不报错，但布局中不要依赖）

## ⚠️ 微信富文本标记格式（重要！）

微信公众号的富文本编辑器使用**特殊的 HTML 标记格式**，不是标准 HTML。
如果不遵循这个格式，文章在微信中会**完全排版异常**（即使 CSS 是正确的）。

### 必须遵循的标记规则

| 标准 HTML | 微信格式 | 说明 |
|-----------|---------|------|
| `<div>` | `<section>` | 微信使用 section 作为容器标签 |
| 裸文本 | `<span leaf="">文字</span>` | 所有文本节点必须包在带 leaf 属性的 span 中 |
| `<h1>`/`<h2>` | `<p>` | 标题用 p 标签 + 内联样式模拟 |
| `<br>` | `<br  />` | 两个空格 + 斜杠 |
| 无 | `<mp-style-type data-value="10000">` | 末尾必须有此元数据标签 |

### 末尾元数据标签

每篇文章的 HTML 末尾必须包含：
```html
<p style="display:none;"><mp-style-type data-value="10000"></mp-style-type></p>
```

### CSS 兼容性实测结果

以下 CSS 属性经过实际发布验证，**微信完全支持**：
- ✅ `display:flex` / `align-items` / `justify-content` / `flex-direction`
- ✅ `gap`（flex gap）
- ✅ `flex:1` / `flex-shrink`
- ✅ `text-shadow`
- ✅ `linear-gradient`（不需要 -webkit- 前缀）
- ✅ `box-shadow`
- ✅ `border-radius`
- ✅ `letter-spacing`
- ✅ `overflow:hidden`

以下 CSS 属性**不支持**：
- ❌ CSS animations / transitions / @keyframes
- ❌ `::before` / `::after` 伪元素
- ❌ `clip-path` / `clamp()`
- ❌ CSS Grid
- ❌ 外部字体 (`@font-face`)
- ❌ `position:fixed` / `position:sticky`

### 转换工具

使用 `scripts/convert_to_wechat_markup.py` 自动完成格式转换：
```bash
python3 scripts/convert_to_wechat_markup.py --input raw.html --output wechat.html
```

## 常见错误码

| 错误码 | 含义 | 解决方法 |
|--------|------|---------|
| 40001 | access_token无效 | 重新获取token |
| 40164 | IP不在白名单 | 在公众平台添加IP到白名单 |
| 42001 | access_token过期 | 重新获取token |
| 45009 | API调用次数超限 | 等待次日重置 |
| 45028 | 素材数量超限 | 清理旧素材 |
| 40005 | 文件类型不合法 | 检查上传文件格式 |

## 调试技巧

1. 获取当前出口IP：`curl -s https://api.ipify.org` 或 `curl -s ifconfig.me`
   - 注意：如果有代理，实际出口IP可能不同，以微信报错信息中的IP为准
2. 测试token是否有效：`curl -s "https://api.weixin.qq.com/cgi-bin/getcallbackip?access_token=TOKEN"`
3. 查看草稿列表：`curl -s -X POST "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=TOKEN" -d '{"offset":0,"count":5}'`

## payload.json 生成方式

因为文章HTML内容可能很长且包含特殊字符，推荐用Python生成payload：

```python
import json

payload = {
    "articles": [{
        "title": title,
        "author": author,
        "digest": digest,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }]
}

import tempfile, os
preview_dir = os.path.join(tempfile.gettempdir(), "preview")
os.makedirs(preview_dir, exist_ok=True)
with open(os.path.join(preview_dir, "draft_payload.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)
```
