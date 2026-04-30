#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号文章发布流水线（跨平台一站式入口）。

用法:
    python3 run_pipeline.py <wechat_article_raw.html>

行为:
    1. 把 raw HTML 转成微信专用标记（section / span leaf / mp-style-type）
    2. 把微信版 HTML 以 text/html MIME 塞进系统剪贴板
    3. 生成带「📋 一键复制到公众号」按钮的增强预览页并弹出浏览器

为什么需要这个脚本:
    SKILL.md 里原本的 bash 命令（${TMPDIR:-/tmp}/preview）在 Windows
    PowerShell/cmd 下无法解析，导致路径错位、wechat_article.html 不在
    raw 同目录、open_preview.py 退化为纯预览（没按钮）。

    本脚本全 Python 实现，所有路径通过 tempfile.gettempdir() 计算，
    macOS / Windows / Linux 一套代码全兼容。
"""

import sys
import os
import subprocess
import tempfile


def main():
    if len(sys.argv) < 2:
        print("用法: python3 run_pipeline.py <wechat_article_raw.html>", file=sys.stderr)
        sys.exit(1)

    raw_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(raw_path):
        print(f"❌ raw 文件不存在: {raw_path}", file=sys.stderr)
        sys.exit(1)

    # 跨平台临时目录：所有产物都跟 raw 同目录（避免路径错位）
    preview_dir = os.path.dirname(raw_path)
    wechat_path = os.path.join(preview_dir, "wechat_article.html")
    meta_path = os.path.join(preview_dir, "article_meta.json")

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    python = sys.executable  # 用当前 python 解释器，避免 python3/python 名字差异

    print("=" * 60)
    print(f"📂 工作目录: {preview_dir}")
    print(f"🐍 Python:   {python}")
    print("=" * 60)

    # Step 1: 转换为微信兼容标记
    print("\n[1/3] 转换为微信兼容标记...")
    r = subprocess.run([
        python,
        os.path.join(scripts_dir, "convert_to_wechat_markup.py"),
        "--input", raw_path,
        "--output", wechat_path,
        "--meta", meta_path,
    ])
    if r.returncode != 0:
        print("❌ convert_to_wechat_markup.py 失败", file=sys.stderr)
        sys.exit(1)

    # Step 2: 塞剪贴板
    print("\n[2/3] 塞剪贴板（text/html 富文本）...")
    r = subprocess.run([
        python,
        os.path.join(scripts_dir, "copy_html_to_clipboard.py"),
        wechat_path,
    ])
    if r.returncode != 0:
        print("⚠️ copy_html_to_clipboard.py 失败（不致命，预览页里的按钮可以兜底）", file=sys.stderr)
        # 不 exit，继续走预览

    # Step 3: 弹增强预览页（含一键复制按钮）
    print("\n[3/3] 弹浏览器预览（含「📋 一键复制到公众号」按钮）...")
    r = subprocess.run([
        python,
        os.path.join(scripts_dir, "open_preview.py"),
        raw_path,
    ])
    if r.returncode != 0:
        print("❌ open_preview.py 失败", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ 全部完成！")
    print("\n📋 下一步（一粘即发）：")
    print("   1. 浏览器预览页右上角点「📋 一键复制到公众号」（或剪贴板已自动塞好）")
    print("   2. 打开 mp.weixin.qq.com → 新建图文消息")
    print("   3. 编辑器里直接 Ctrl+V（Mac: Cmd+V）")
    print("   4. 起标题 → 点「保存为草稿」或「发布」")
    print("=" * 60)


if __name__ == "__main__":
    main()
