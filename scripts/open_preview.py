#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台浏览器预览打开器。

用法:
    python3 open_preview.py <html_file_path>

在 macOS / Windows / Linux 都能正确打开默认浏览器。
避免 shell 脚本里写死 `open` / `start` / `xdg-open` 导致的平台问题。
"""

import sys
import os
import platform
import subprocess


def open_in_browser(file_path: str) -> None:
    """在默认浏览器中打开本地 HTML 文件。"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    abs_path = os.path.abspath(file_path)
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", abs_path], check=True)
        elif system == "Windows":
            os.startfile(abs_path)  # noqa: type: ignore
        else:  # Linux / BSD
            subprocess.run(["xdg-open", abs_path], check=True)
        print(f"✅ 已在浏览器打开: {abs_path}")
    except Exception as e:
        print(f"❌ 打开失败: {e}", file=sys.stderr)
        print(f"   你可以手动把这个路径复制到浏览器地址栏：\n   file://{abs_path}")
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python3 open_preview.py <html_file_path>", file=sys.stderr)
        sys.exit(1)
    open_in_browser(sys.argv[1])


if __name__ == "__main__":
    main()
