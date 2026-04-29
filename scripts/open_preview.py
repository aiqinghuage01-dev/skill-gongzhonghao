#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台浏览器预览打开器（增强版）。

用法:
    python3 open_preview.py <wechat_article_raw.html>

行为:
    - 必传 raw 版（浏览器友好，给眼睛看排版）
    - 自动检测同目录是否有 wechat_article.html（微信专用版）：
        * 有 → 生成一个带「📋 一键复制到公众号」浮动按钮的增强预览页，
              按钮点击会把 wechat 版以 text/html 写进系统剪贴板
        * 没 → 退化为纯预览，无按钮（同老版本行为）
    - 跨平台调用系统默认浏览器打开
"""

import sys
import os
import platform
import subprocess
import base64


COPY_BUTTON_SNIPPET = """
<div id="__copy_btn_wrap" style="position:fixed;top:16px;right:16px;z-index:99999;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;">
  <button id="__copy_btn" style="background:linear-gradient(135deg,#d4380d,#fa8c16);color:#fff;border:none;padding:12px 22px;border-radius:24px;font-size:14px;font-weight:700;cursor:pointer;box-shadow:0 4px 16px rgba(212,56,13,0.35);transition:transform 0.1s;">
    📋 一键复制到公众号
  </button>
  <div id="__copy_toast" style="display:none;margin-top:10px;background:rgba(0,0,0,0.85);color:#fff;padding:10px 16px;border-radius:8px;font-size:13px;text-align:center;line-height:1.5;">
    ✅ 已复制！去公众号后台 Cmd+V 粘贴
  </div>
</div>
<script>
(function() {
  const __WECHAT_HTML_B64 = "__WECHAT_B64_PAYLOAD__";

  function b64ToUtf8(b64) {
    const binary = atob(b64);
    const bytes = Uint8Array.from(binary, function(c) { return c.charCodeAt(0); });
    return new TextDecoder('utf-8').decode(bytes);
  }

  function showToast(text, ok) {
    const toast = document.getElementById('__copy_toast');
    toast.textContent = text;
    toast.style.background = ok ? 'rgba(0,0,0,0.85)' : 'rgba(180,30,30,0.92)';
    toast.style.display = 'block';
    setTimeout(function() { toast.style.display = 'none'; }, 3500);
  }

  document.getElementById('__copy_btn').addEventListener('click', async function() {
    const html = b64ToUtf8(__WECHAT_HTML_B64);
    try {
      const blob = new Blob([html], { type: 'text/html' });
      const item = new ClipboardItem({ 'text/html': blob });
      await navigator.clipboard.write([item]);
      showToast('✅ 已复制！去公众号后台 Cmd+V 粘贴', true);
    } catch (e) {
      // 兜底：写纯文本（部分老浏览器或 file:// 受限场景）
      try {
        await navigator.clipboard.writeText(html);
        showToast('⚠️ 仅复制了 HTML 源码（浏览器限制）。建议用脚本兜底：copy_html_to_clipboard.py', false);
      } catch (e2) {
        showToast('❌ 复制失败：' + e2.message + '。请重跑 copy_html_to_clipboard.py 兜底', false);
      }
    }
  });
})();
</script>
"""


def build_enhanced_preview(raw_html: str, wechat_html: str) -> str:
    """把复制按钮注入 raw 版的 </body> 之前。"""
    wechat_b64 = base64.b64encode(wechat_html.encode("utf-8")).decode("ascii")
    snippet = COPY_BUTTON_SNIPPET.replace("__WECHAT_B64_PAYLOAD__", wechat_b64)
    if "</body>" in raw_html:
        return raw_html.replace("</body>", snippet + "\n</body>")
    return raw_html + snippet


def open_in_browser(file_path: str) -> None:
    """在默认浏览器中打开本地 HTML 文件。"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    abs_raw = os.path.abspath(file_path)
    raw_dir = os.path.dirname(abs_raw)
    wechat_path = os.path.join(raw_dir, "wechat_article.html")

    target_path = abs_raw
    enhanced = False

    if os.path.exists(wechat_path):
        with open(abs_raw, "r", encoding="utf-8") as f:
            raw_html = f.read()
        with open(wechat_path, "r", encoding="utf-8") as f:
            wechat_html = f.read()
        merged = build_enhanced_preview(raw_html, wechat_html)
        enhanced_path = os.path.join(raw_dir, "wechat_article_preview.html")
        with open(enhanced_path, "w", encoding="utf-8") as f:
            f.write(merged)
        target_path = enhanced_path
        enhanced = True

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", target_path], check=True)
        elif system == "Windows":
            os.startfile(target_path)  # noqa: type: ignore
        else:
            subprocess.run(["xdg-open", target_path], check=True)
        if enhanced:
            print(f"✅ 已在浏览器打开（含一键复制按钮）: {target_path}")
        else:
            print(f"✅ 已在浏览器打开（纯预览，无按钮）: {target_path}")
            print(f"   提示：同目录放一份 wechat_article.html 即可启用一键复制按钮。")
    except Exception as e:
        print(f"❌ 打开失败: {e}", file=sys.stderr)
        print(f"   你可以手动把这个路径复制到浏览器地址栏：\n   file://{target_path}")
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python3 open_preview.py <wechat_article_raw.html>", file=sys.stderr)
        sys.exit(1)
    open_in_browser(sys.argv[1])


if __name__ == "__main__":
    main()
