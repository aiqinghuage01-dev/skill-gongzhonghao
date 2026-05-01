#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时 HTTP server（detach 子进程跑），给预览页用。

为什么需要：
    file:// 协议下浏览器拒绝 navigator.clipboard.write({'text/html': blob})，
    按钮兜底走 execCommand('copy') 时，浏览器会把非标准标签
    （比如 <mp-style-type>）从剪贴板序列化结果里 strip 掉，导致公众号
    后台粘贴时识别不出微信富文本格式，整段降级为纯文字。

    把预览页跑在 http://127.0.0.1:port/ 上 → localhost 是 W3C
    secure context → ClipboardItem API 永远能用 → 写的是原始字符串
    mp-style-type / span leaf / section 全保留。

用法（被 open_preview.py 当 detach 子进程启动）:
    python _temp_http_server.py <port> <directory> [timeout_seconds]

  port:               监听端口（127.0.0.1 only，loopback，Windows 防火墙
                      不会弹窗）
  directory:          serve 哪个目录
  timeout_seconds:    多少秒后自动退出（默认 1800 = 30 分钟）
                      避免学员系统积累僵尸进程
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading


def _wechat_markers(html):
    low = html.lower()
    return {
        "section": low.count("<section"),
        "span_leaf": low.count(" leaf="),
        "mp_style_type": low.count("<mp-style-type"),
    }


def _copy_wechat_html(directory):
    """把当前预览目录里的 wechat_article.html 写进系统剪贴板。"""
    html_path = os.path.join(directory, "wechat_article.html")
    if not os.path.exists(html_path):
        return 404, {
            "ok": False,
            "error": "找不到微信排版文件，请重新生成文章。",
        }

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    markers = _wechat_markers(html)
    size_kb = os.path.getsize(html_path) / 1024

    # 测试用：不真实改系统剪贴板，只验证 endpoint 能读到完整微信 HTML。
    if os.environ.get("NRG_COPY_DRY_RUN") == "1":
        return 200, {
            "ok": True,
            "dry_run": True,
            "size_kb": round(size_kb, 1),
            "markers": markers,
        }

    copy_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "copy_html_to_clipboard.py")
    if not os.path.exists(copy_script):
        return 500, {
            "ok": False,
            "error": "复制工具缺失，请重新安装这套工具。",
        }

    r = subprocess.run(
        [sys.executable, copy_script, html_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip()
        return 500, {
            "ok": False,
            "error": (detail[:240] if detail else "系统剪贴板写入失败，请重新生成一次。"),
            "markers": markers,
        }

    return 200, {
        "ok": True,
        "size_kb": round(size_kb, 1),
        "markers": markers,
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python _temp_http_server.py <port> <directory> [timeout]", file=sys.stderr)
        sys.exit(1)

    port = int(sys.argv[1])
    directory = sys.argv[2]
    timeout_sec = int(sys.argv[3]) if len(sys.argv) > 3 else 1800

    if not os.path.isdir(directory):
        print(f"❌ 目录不存在: {directory}", file=sys.stderr)
        sys.exit(1)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        """SimpleHTTPRequestHandler 子类：静默日志 + 锁定 directory。"""

        extensions_map = {
            **http.server.SimpleHTTPRequestHandler.extensions_map,
            ".html": "text/html; charset=utf-8",
            ".htm": "text/html; charset=utf-8",
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, fmt, *args):
            # 静默——不要污染 stderr/stdout（detach 进程的日志没人看）
            pass

        def _send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            # 读掉请求体，避免 keep-alive 管道里残留。
            try:
                length = int(self.headers.get("Content-Length") or "0")
            except ValueError:
                length = 0
            if length:
                self.rfile.read(length)

            path = self.path.split("?", 1)[0]
            if path != "/__copy_wechat":
                self._send_json(404, {"ok": False, "error": "not found"})
                return

            status, payload = _copy_wechat_html(directory)
            self._send_json(status, payload)

    # ThreadingTCPServer 让多浏览器请求并发不阻塞
    class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True  # 进程退出时强杀所有处理线程

    try:
        with ReusableThreadingTCPServer(("127.0.0.1", port), QuietHandler) as httpd:
            # timeout 计时器：到时直接 _exit（绕过 atexit、daemon thread join 等）
            timer = threading.Timer(timeout_sec, lambda: os._exit(0))
            timer.daemon = True
            timer.start()

            httpd.serve_forever()
    except OSError as e:
        # 端口被占用、权限不足等
        print(f"❌ HTTP server 启动失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
