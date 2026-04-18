#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 HTML 文件内容塞进系统剪贴板（text/html MIME 格式）。

为什么需要这个脚本：
  convert_to_wechat_markup.py 产出的 wechat_article.html 是**微信公众号富文本
  编辑器专用格式**（含 <section>、<span leaf="">、<mp-style-type> 等标签）。

  这个 HTML **不能用浏览器打开后 Ctrl+C 复制** —— 浏览器会把
  <section> 转成 <div>、丢弃 <mp-style-type>，导致排版在粘贴到公众号后台
  时大面积塌陷。

  正确姿势：跳过浏览器，直接用系统 API 把 HTML 以 text/html MIME 类型
  塞进系统剪贴板。学员在公众号后台 Ctrl+V 时，编辑器识别为富文本 HTML
  粘贴，完整保留 section / span leaf 等微信专用结构。

  这也是墨滴、Markdown Nice 等公众号排版工具背后的核心机制。

跨平台实现：
  - macOS:   osascript 把 HTML 文件读入 clipboard 的 «class HTML» 类型
  - Windows: PowerShell 通过 System.Windows.Forms.Clipboard.SetText(.., 'Html')
  - Linux:   xclip -selection clipboard -t text/html -i <file>

用法:
  python3 copy_html_to_clipboard.py <html_file_path>

  例:
  python3 copy_html_to_clipboard.py "$TMPDIR/preview/wechat_article.html"
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path


def copy_macos(html_path: Path) -> None:
    """macOS: 用 osascript 把 HTML 以 «class HTML» 类型塞进剪贴板。"""
    script = f'set the clipboard to (read (POSIX file "{html_path}") as «class HTML»)'
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def copy_windows(html_path: Path) -> None:
    """Windows: PowerShell 用 System.Windows.Forms.Clipboard 设置 Html 类型。"""
    # 注意路径里的反斜杠和引号要转义
    win_path = str(html_path).replace("\\", "\\\\").replace('"', '\\"')
    ps_script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        f"$html = Get-Content -Raw -Path \"{win_path}\"; "
        "[System.Windows.Forms.Clipboard]::SetText($html, 'Html')"
    )
    # -STA 必需：System.Windows.Forms.Clipboard 要求 STA 线程模型
    subprocess.run(
        ["powershell", "-NoProfile", "-STA", "-Command", ps_script],
        check=True,
        capture_output=True,
    )


def copy_linux(html_path: Path) -> None:
    """Linux: 用 xclip 设置 text/html 类型。"""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    subprocess.run(
        ["xclip", "-selection", "clipboard", "-t", "text/html", "-i"],
        input=html,
        text=True,
        check=True,
        capture_output=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="把 HTML 文件以 text/html 格式塞进系统剪贴板"
    )
    parser.add_argument(
        "html_path",
        help="HTML 文件路径（应该是 convert_to_wechat_markup.py 输出的 wechat_article.html）",
    )
    args = parser.parse_args()

    html_path = Path(args.html_path).expanduser().resolve()
    if not html_path.exists():
        print(f"❌ 文件不存在: {html_path}", file=sys.stderr)
        sys.exit(1)

    system = platform.system()
    try:
        if system == "Darwin":
            copy_macos(html_path)
        elif system == "Windows":
            copy_windows(html_path)
        else:
            copy_linux(html_path)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace").strip()
        print(f"❌ 复制失败: {err or e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ 找不到系统工具: {e}", file=sys.stderr)
        if system == "Linux":
            print("   Linux 学员需要装 xclip: sudo apt install xclip", file=sys.stderr)
        sys.exit(1)

    size_kb = html_path.stat().st_size / 1024
    print(f"✅ HTML 已塞进系统剪贴板（{size_kb:.1f} KB，text/html 格式）")
    print(f"📋 下一步：")
    print(f"   1. 打开 https://mp.weixin.qq.com → 新建图文消息")
    print(f"   2. 在编辑器里直接 Ctrl+V（Mac: Cmd+V）")
    print(f"   3. 起标题 → 点'保存为草稿'或'发布'")
    print(f"")
    print(f"⚠️ 粘贴时不要点'粘贴为纯文本'！否则排版会丢。")


if __name__ == "__main__":
    main()
