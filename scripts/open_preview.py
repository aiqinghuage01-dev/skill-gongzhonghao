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

  async function copyViaLocalServer() {
    if (!/^https?:\\/\\/(127\\.0\\.0\\.1|localhost):\\d+$/i.test(window.location.origin)) {
      throw new Error('当前不是本机预览服务');
    }
    const resp = await fetch('/__copy_wechat', {
      method: 'POST',
      headers: { 'Accept': 'application/json' },
      cache: 'no-store'
    });
    let data = null;
    try {
      data = await resp.json();
    } catch (e) {
      data = null;
    }
    if (!resp.ok || !data || !data.ok) {
      throw new Error((data && data.error) || ('复制失败 HTTP ' + resp.status));
    }
    return data;
  }

  document.getElementById('__copy_btn').addEventListener('click', async function() {
    const html = b64ToUtf8(__WECHAT_HTML_B64);

    // v1.8：按钮也走系统剪贴板，不再走浏览器 ClipboardItem / execCommand。
    // Windows 上浏览器复制会清洗微信专用标签，导致粘到公众号只剩文字。
    try {
      const result = await copyViaLocalServer();
      const hotkey = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || '') ? 'Cmd+V' : 'Ctrl+V';
      const markerOk = result.markers && result.markers.mp_style_type > 0 && result.markers.section > 0;
      showToast(markerOk ? ('✅ 已复制！去公众号后台 ' + hotkey + ' 粘贴') : ('✅ 已复制，请去公众号后台 ' + hotkey + ' 粘贴'), true);
      return;
    } catch (e) {
      // 不能再用浏览器兜底：它会把微信专用排版清洗掉，成功也是假成功。
      showToast('❌ 按钮复制没成功。生成时已自动复制过，请先去公众号后台直接粘贴；如果排版不对，重新生成一次。', false);
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
    """在默认浏览器中打开本地 HTML 文件。

    v1.8 关键升级：尝试启动一个 detach HTTP server 在 127.0.0.1:port 上
    serve 预览文件，浏览器打开 http://127.0.0.1/ URL 而不是 file://。
    按钮点击时 POST /__copy_wechat，让本机 Python 直接把 wechat_article.html
    以 text/html 写进系统剪贴板。

    原因：Windows 上浏览器 ClipboardItem / execCommand 都可能清洗 HTML，
    把 <mp-style-type> 等微信专用标签吃掉。只要经过浏览器复制，成功也可能
    是假成功；系统剪贴板路径才是事实源。

    HTTP server 起不来时（端口、防火墙）回退到 file://。
    """
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    abs_raw = os.path.abspath(file_path)
    raw_dir = os.path.dirname(abs_raw)
    wechat_path = os.path.join(raw_dir, "wechat_article.html")

    target_path = abs_raw
    target_filename = os.path.basename(abs_raw)
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
        target_filename = os.path.basename(enhanced_path)
        enhanced = True

    # 尝试启动 detach HTTP server，浏览器开 http://127.0.0.1/...
    server_url = _start_detached_http_server(raw_dir, target_filename)

    system = platform.system()
    try:
        if server_url:
            # 走 HTTP — 按钮调用本地系统剪贴板端点
            _open_url(server_url, system)
            print(f"✅ 已在浏览器打开 [HTTP localhost 模式]: {server_url}")
            print(f"   按钮一键复制走本机系统剪贴板，剪贴板里是完整微信格式")
        else:
            # 兜底走 file://（按钮不再做浏览器复制，避免覆盖成坏剪贴板）
            if system == "Darwin":
                subprocess.run(["open", target_path], check=True)
            elif system == "Windows":
                os.startfile(target_path)  # noqa: type: ignore
            else:
                subprocess.run(["xdg-open", target_path], check=True)
            print(f"⚠️  HTTP server 起不来，回退到 file:// 协议: {target_path}")
            print(f"   为避免浏览器清洗排版，按钮不会再走浏览器复制；请直接粘贴已自动写入的剪贴板")
    except Exception as e:
        print(f"❌ 打开失败: {e}", file=sys.stderr)
        print(f"   你可以手动把这个路径复制到浏览器地址栏：\n   file://{target_path}")
        sys.exit(1)


def _open_url(url: str, system: str) -> None:
    """跨平台打开 URL（不是文件路径）"""
    if system == "Darwin":
        subprocess.run(["open", url], check=True)
    elif system == "Windows":
        # os.startfile 也能开 URL，但 webbrowser 更稳
        import webbrowser
        webbrowser.open(url)
    else:
        subprocess.run(["xdg-open", url], check=True)


def _find_free_port() -> int:
    """找一个可用的本地端口（让 OS 分配）"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _start_detached_http_server(directory: str, filename: str, timeout_sec: int = 1800):
    """启动 detach 的 HTTP server 子进程，返回 http://127.0.0.1:port/filename URL。
    失败返回 None（调用方回退到 file://）。"""
    import socket
    import time

    try:
        port = _find_free_port()
    except OSError:
        return None

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(scripts_dir, "_temp_http_server.py")
    if not os.path.exists(server_script):
        return None

    # detach 子进程（关键：跨平台姿势不同）
    popen_kwargs = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if platform.system() == "Windows":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        popen_kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    try:
        subprocess.Popen(
            [sys.executable, server_script, str(port), directory, str(timeout_sec)],
            **popen_kwargs,
        )
    except Exception:
        return None

    # 等 server 起来（最多等 3 秒）
    for _ in range(30):
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=0.1)
            sock.close()
            return f"http://127.0.0.1:{port}/{filename}"
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)

    return None


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python3 open_preview.py <wechat_article_raw.html>", file=sys.stderr)
        sys.exit(1)
    open_in_browser(sys.argv[1])


if __name__ == "__main__":
    main()
