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
  - Windows: PowerShell 写 System.Windows.Forms.DataObject 的 HTML Format（CF_HTML）
  - Linux:   xclip -selection clipboard -t text/html -i <file>

用法:
  python3 copy_html_to_clipboard.py <html_file_path>

  例:
  python3 copy_html_to_clipboard.py "$TMPDIR/preview/wechat_article.html"
"""

import argparse
import base64
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def copy_macos(html_path: Path) -> None:
    """macOS: 用 osascript 把 HTML 以 «class HTML» 类型塞进剪贴板。"""
    script = f'set the clipboard to (read (POSIX file "{html_path}") as «class HTML»)'
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def build_windows_cf_html(html: str) -> str:
    """构造 Windows CF_HTML 剪贴板格式。

    Windows 的 HTML 剪贴板不是裸 HTML 字符串，而是带 StartHTML /
    StartFragment 字节偏移的 CF_HTML 包。显式构造后，微信公众号后台
    粘贴时能稳定识别为富文本 HTML，而不是纯文本。
    """
    start_marker = "<html><body><!--StartFragment-->"
    end_marker = "<!--EndFragment--></body></html>"
    body = start_marker + html + end_marker

    header_template = (
        "Version:0.9\r\n"
        "StartHTML:{start_html:010d}\r\n"
        "EndHTML:{end_html:010d}\r\n"
        "StartFragment:{start_fragment:010d}\r\n"
        "EndFragment:{end_fragment:010d}\r\n"
    )
    dummy_header = header_template.format(
        start_html=0,
        end_html=0,
        start_fragment=0,
        end_fragment=0,
    )

    start_html = len(dummy_header.encode("utf-8"))
    start_fragment = start_html + len(start_marker.encode("utf-8"))
    end_fragment = start_fragment + len(html.encode("utf-8"))
    end_html = start_html + len(body.encode("utf-8"))

    header = header_template.format(
        start_html=start_html,
        end_html=end_html,
        start_fragment=start_fragment,
        end_fragment=end_fragment,
    )
    return header + body


def html_to_plain_text(html: str) -> str:
    """给剪贴板补一个 UnicodeText 兜底。"""
    text = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.I)
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def copy_windows(html_path: Path) -> None:
    """Windows: PowerShell 用 System.Windows.Forms.Clipboard 设置 Html 类型。

    关键修复点：
      1. 用 [System.IO.File]::ReadAllText + UTF-8 显式编码读取文件
         避免 PowerShell 5.1 默认 ANSI(cp936) 读 utf-8 文件乱码
      2. 路径用 base64 传递，规避反斜杠/引号/中文/$/单引号 等转义噩梦
      3. -ExecutionPolicy Bypass 兜底执行策略限制（公司电脑常见）
      4. 失败时把 stderr 解码后返回，方便上层定位问题
      5. v1.8 显式生成 Windows CF_HTML 头，避免裸 HTML 被目标程序当纯文本
    """
    html = html_path.read_text(encoding="utf-8")
    cf_html = build_windows_cf_html(html)
    plain_text = html_to_plain_text(html)

    def _write_temp(content: str, suffix: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=suffix, delete=False)
        try:
            f.write(content)
            return Path(f.name)
        finally:
            f.close()

    cf_path = _write_temp(cf_html, ".cfhtml")
    text_path = _write_temp(plain_text, ".txt")

    try:
        # base64 传路径 → 完全规避 PowerShell 字符串转义问题
        cf_b64 = base64.b64encode(str(cf_path).encode("utf-8")).decode("ascii")
        text_b64 = base64.b64encode(str(text_path).encode("utf-8")).decode("ascii")

        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            f"$cfBytes = [System.Convert]::FromBase64String('{cf_b64}'); "
            f"$textBytes = [System.Convert]::FromBase64String('{text_b64}'); "
            "$cfPath = [System.Text.Encoding]::UTF8.GetString($cfBytes); "
            "$textPath = [System.Text.Encoding]::UTF8.GetString($textBytes); "
            "$cfHtml = [System.IO.File]::ReadAllText($cfPath, [System.Text.Encoding]::UTF8); "
            "$plain = [System.IO.File]::ReadAllText($textPath, [System.Text.Encoding]::UTF8); "
            "$data = New-Object System.Windows.Forms.DataObject; "
            "$data.SetData([System.Windows.Forms.DataFormats]::Html, $cfHtml); "
            "$data.SetData([System.Windows.Forms.DataFormats]::UnicodeText, $plain); "
            "[System.Windows.Forms.Clipboard]::SetDataObject($data, $true)"
        )
        # -STA 必需：System.Windows.Forms.Clipboard 要求 STA 线程模型
        # -ExecutionPolicy Bypass：兜底受限策略（公司电脑可能 Restricted）
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-STA", "-Command", ps_script],
            check=True,
            capture_output=True,
        )
    finally:
        for p in (cf_path, text_path):
            try:
                p.unlink()
            except OSError:
                pass


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
