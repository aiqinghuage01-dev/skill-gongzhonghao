#!/bin/bash
# 微信公众号一键推送脚本
# 用法: ./push_to_wechat.sh <title> <author> <digest> <html_file> <cover_image>
#
# 自动流程: 读取凭据 → 获取token → 上传封面 → 创建草稿
# 凭据从 ~/.wechat-article-config 读取

set -e

# ========== 参数检查 ==========
if [ "$#" -lt 5 ]; then
    echo "用法: $0 <标题> <作者> <摘要> <HTML文件路径> <封面图片路径>"
    echo ""
    echo "示例: $0 '别瞎学AI' '{作者名}' '摘要文字...' \"\${TMPDIR:-/tmp}/preview/article.html\" \"\${TMPDIR:-/tmp}/preview/cover.jpg\""
    exit 1
fi

TITLE="$1"
AUTHOR="$2"
DIGEST="$3"
HTML_FILE="$4"
COVER_IMAGE="$5"

# ========== 读取配置 ==========
CONFIG_FILE="$HOME/.wechat-article-config"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    echo "请先运行配置流程，创建包含 wechat_appid 和 wechat_appsecret 的配置文件。"
    exit 1
fi

APPID=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['wechat_appid'])")
APPSECRET=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['wechat_appsecret'])")

if [ -z "$APPID" ] || [ -z "$APPSECRET" ]; then
    echo "❌ 配置文件中缺少 wechat_appid 或 wechat_appsecret"
    exit 1
fi

# ========== 检查文件存在 ==========
if [ ! -f "$HTML_FILE" ]; then
    echo "❌ HTML文件不存在: $HTML_FILE"
    exit 1
fi

if [ ! -f "$COVER_IMAGE" ]; then
    echo "❌ 封面图片不存在: $COVER_IMAGE"
    exit 1
fi

echo "🚀 开始推送到微信公众号..."
echo "   标题: $TITLE"
echo "   作者: $AUTHOR"
echo ""

# ========== 第1步：获取 access_token ==========
echo "📡 步骤1/3: 获取 access_token..."

TOKEN_RESPONSE=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$APPID&secret=$APPSECRET")

# 检查是否有错误
ERROR_CODE=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('errcode',''))" 2>/dev/null || echo "")

if [ "$ERROR_CODE" = "40164" ]; then
    echo "❌ IP白名单错误！"
    echo "请把以下IP添加到微信公众平台 → 开发 → 基本配置 → IP白名单："
    echo "$TOKEN_RESPONSE"
    echo ""
    echo "当前机器IP: $(curl -s https://api.ipify.org 2>/dev/null || echo '获取失败')"
    exit 1
elif [ -n "$ERROR_CODE" ] && [ "$ERROR_CODE" != "0" ] && [ "$ERROR_CODE" != "" ]; then
    echo "❌ 获取token失败: $TOKEN_RESPONSE"
    exit 1
fi

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "   ✅ token获取成功"

# ========== 第2步：上传封面 ==========
echo "🖼️  步骤2/3: 上传封面图片..."

UPLOAD_RESPONSE=$(curl -s -F "media=@$COVER_IMAGE" \
    "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=$ACCESS_TOKEN&type=thumb")

THUMB_MEDIA_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('media_id',''))" 2>/dev/null || echo "")

if [ -z "$THUMB_MEDIA_ID" ]; then
    echo "❌ 封面上传失败: $UPLOAD_RESPONSE"
    exit 1
fi
echo "   ✅ 封面上传成功 (media_id: ${THUMB_MEDIA_ID:0:20}...)"

# ========== 第3步：创建草稿 ==========
echo "📝 步骤3/3: 创建草稿..."

# 用 Python 生成 payload（处理 HTML 中的特殊字符、转义串和缺失摘要）
PAYLOAD_FILE="/tmp/wechat_draft_payload_$$.json"
NORMALIZED_META_FILE="/tmp/wechat_draft_meta_$$.json"

python3 - "$TITLE" "$AUTHOR" "$DIGEST" "$HTML_FILE" "$THUMB_MEDIA_ID" "$PAYLOAD_FILE" "$NORMALIZED_META_FILE" <<'PYEOF'
import codecs
import json
import re
import sys
from pathlib import Path


def maybe_decode_escaped_text(text: str) -> str:
    """把误传进来的 \\uXXXX / \\n 这类转义串还原成正常文本。"""
    if not isinstance(text, str):
        return text

    value = text
    stripped = value.strip()

    # 先尝试把 `"..."` 这种 JSON 字符串字面量还原
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        try:
            loaded = json.loads(stripped)
        except Exception:
            loaded = None
        if isinstance(loaded, str):
            value = loaded
            stripped = value.strip()

    if re.search(r'\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}|\\x[0-9a-fA-F]{2}', value):
        try:
            value = codecs.decode(value, "unicode_escape")
        except Exception:
            pass

    if "\\n" in value and "\n" not in value:
        value = value.replace("\\n", "\n")
    if "\\t" in value and "\t" not in value:
        value = value.replace("\\t", "\t")

    return value


def candidate_meta_paths(html_path: Path) -> list[Path]:
    candidates = [
        html_path.parent / "article_meta.json",
        html_path.with_suffix(".meta.json"),
        html_path.with_suffix(".json"),
    ]

    html_name = html_path.name
    if html_name.endswith("-wechat.html"):
        candidates.append(html_path.with_name(html_name.replace("-wechat.html", "-meta.json")))
    if html_name == "wechat_article.html":
        candidates.append(html_path.parent / "article_meta.json")

    deduped = []
    seen = set()
    for path in candidates:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def load_meta(html_path: Path) -> dict:
    for meta_path in candidate_meta_paths(html_path):
        if not meta_path.exists():
            continue
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            return data
    return {}


def normalize_title_and_digest(title: str, digest: str, html_content: str, meta: dict) -> tuple[str, str]:
    title = maybe_decode_escaped_text(title).strip()
    digest = maybe_decode_escaped_text(digest).strip()

    if not title:
        title = str(meta.get("title", "")).strip()

    if not digest:
        digest = str(meta.get("digest", "")).strip()

    # 摘要为空或明显是从 HTML 错抓出来时，优先用 meta 文件的摘要
    suspicious_digest = (
        not digest
        or digest.startswith("\\u")
        or digest.startswith("<")
        or digest.count("\n") >= 2
        or len(digest.strip()) < 8
    )
    if suspicious_digest:
        meta_digest = str(meta.get("digest", "")).strip()
        if meta_digest:
            digest = meta_digest

    if not digest:
        # 最后一层兜底：从正文里抽纯文本前 120 字
        plain = re.sub(r"<[^>]+>", " ", html_content)
        plain = re.sub(r"\s+", " ", plain).strip()
        digest = plain[:120]

    return title, digest


title, author, digest, html_file, thumb_media_id, payload_file, normalized_meta_file = sys.argv[1:]
html_path = Path(html_file)

html_content = html_path.read_text(encoding="utf-8")
html_content = maybe_decode_escaped_text(html_content)
meta = load_meta(html_path)
title, digest = normalize_title_and_digest(title, digest, html_content, meta)
author = maybe_decode_escaped_text(author).strip()

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

Path(payload_file).write_text(
    json.dumps(payload, ensure_ascii=False),
    encoding="utf-8",
)
Path(normalized_meta_file).write_text(
    json.dumps(
        {
            "title": title,
            "author": author,
            "digest": digest,
        },
        ensure_ascii=False,
    ),
    encoding="utf-8",
)

print(f"   规范化标题: {title}")
print(f"   规范化摘要: {digest[:40]}")
PYEOF

# ========== 第3.5步：重复草稿保护 ==========
DEDUP_RESULT=$(python3 - "$ACCESS_TOKEN" "$NORMALIZED_META_FILE" "$PAYLOAD_FILE" <<'PYEOF'
import hashlib
import json
import sys
import urllib.request


def normalize_text(value: str) -> str:
    return " ".join((value or "").split())


def content_fingerprint(article: dict) -> str:
    basis = "\n".join(
        [
            normalize_text(article.get("title", "")),
            normalize_text(article.get("digest", "")),
            article.get("content", ""),
        ]
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


access_token, normalized_meta_file, payload_file = sys.argv[1:]
meta = json.loads(open(normalized_meta_file, encoding="utf-8").read())
payload = json.loads(open(payload_file, encoding="utf-8").read())
target = payload["articles"][0]
target_fp = content_fingerprint(target)

if str(meta.get("title", "")).strip() == "":
    print(json.dumps({"duplicate": False}, ensure_ascii=False))
    raise SystemExit

if __import__("os").environ.get("WECHAT_FORCE_NEW_DRAFT") == "1":
    print(json.dumps({"duplicate": False, "forced": True}, ensure_ascii=False))
    raise SystemExit

url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
req = urllib.request.Request(
    url,
    data=json.dumps({"offset": 0, "count": 20, "no_content": 0}, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

try:
    resp = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
except Exception as exc:
    print(json.dumps({"duplicate": False, "check_error": str(exc)}, ensure_ascii=False))
    raise SystemExit

for item in resp.get("item", []):
    news_items = item.get("content", {}).get("news_item", [])
    if not news_items:
        continue
    article = news_items[0]
    if content_fingerprint(article) == target_fp:
        print(
            json.dumps(
                {
                    "duplicate": True,
                    "media_id": item.get("media_id", ""),
                    "title": article.get("title", ""),
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit

print(json.dumps({"duplicate": False}, ensure_ascii=False))
PYEOF
)

DUPLICATE_MEDIA_ID=$(python3 -c "import sys,json; print(json.loads(sys.argv[1]).get('media_id',''))" "$DEDUP_RESULT" 2>/dev/null || echo "")
IS_DUPLICATE=$(python3 -c "import sys,json; print('1' if json.loads(sys.argv[1]).get('duplicate') else '0')" "$DEDUP_RESULT" 2>/dev/null || echo "0")

if [ "$IS_DUPLICATE" = "1" ] && [ -n "$DUPLICATE_MEDIA_ID" ]; then
    NORMALIZED_TITLE=$(python3 -c "import json; print(json.load(open('$NORMALIZED_META_FILE'))['title'])" 2>/dev/null || echo "$TITLE")
    NORMALIZED_AUTHOR=$(python3 -c "import json; print(json.load(open('$NORMALIZED_META_FILE'))['author'])" 2>/dev/null || echo "$AUTHOR")
    rm -f "$PAYLOAD_FILE"
    rm -f "$NORMALIZED_META_FILE"
    echo ""
    echo "✅ ===== 检测到重复草稿，已直接复用 ====="
    echo "   标题: $NORMALIZED_TITLE"
    echo "   作者: $NORMALIZED_AUTHOR"
    echo "   草稿ID: $DUPLICATE_MEDIA_ID"
    echo ""
    echo "👉 已存在同标题同正文草稿，未再新建，避免草稿箱堆重复稿"
    exit 0
fi

DRAFT_RESPONSE=$(curl -s -X POST \
    "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=$ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d @"$PAYLOAD_FILE")

DRAFT_MEDIA_ID=$(echo "$DRAFT_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('media_id',''))" 2>/dev/null || echo "")

NORMALIZED_TITLE=$(python3 -c "import json; print(json.load(open('$NORMALIZED_META_FILE'))['title'])" 2>/dev/null || echo "$TITLE")
NORMALIZED_AUTHOR=$(python3 -c "import json; print(json.load(open('$NORMALIZED_META_FILE'))['author'])" 2>/dev/null || echo "$AUTHOR")

# 清理临时文件
rm -f "$PAYLOAD_FILE"
rm -f "$NORMALIZED_META_FILE"

if [ -z "$DRAFT_MEDIA_ID" ]; then
    echo "❌ 创建草稿失败: $DRAFT_RESPONSE"
    exit 1
fi

echo ""
echo "✅ ===== 推送成功！====="
echo "   标题: $NORMALIZED_TITLE"
echo "   作者: $NORMALIZED_AUTHOR"
echo "   草稿ID: $DRAFT_MEDIA_ID"
echo ""
echo "👉 去公众号后台 → 草稿箱 → 点\"发布\"即可"
echo "   https://mp.weixin.qq.com"
