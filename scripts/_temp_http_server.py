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
import os
import socketserver
import sys
import threading


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

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, fmt, *args):
            # 静默——不要污染 stderr/stdout（detach 进程的日志没人看）
            pass

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
