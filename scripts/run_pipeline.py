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
       按钮也调用本机系统剪贴板，不走浏览器复制

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


def _ensure_dependencies():
    """零依赖假设：学员可能没装 bs4。检测 + 自动 pip install。

    必须在 main() 执行前跑——run_pipeline 自己不直接 import bs4，
    但它通过 subprocess 调 convert_to_wechat_markup.py，那个脚本依赖 bs4。
    在这里检测保证：即使 LLM 没跑过 setup.py，单独跑 run_pipeline.py 也能自愈。
    """
    try:
        import bs4  # noqa: F401
        return
    except ImportError:
        pass

    print("[setup] 检测到缺少 beautifulsoup4，自动安装中...", file=sys.stderr)
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "beautifulsoup4"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        print("❌ beautifulsoup4 安装失败", file=sys.stderr)
        if r.stderr:
            print(f"   {r.stderr.strip()[:300]}", file=sys.stderr)
        print(f"   手动修复：{sys.executable} -m pip install beautifulsoup4", file=sys.stderr)
        sys.exit(1)

    # 二次验证
    try:
        import bs4  # noqa: F401
    except ImportError:
        print("❌ beautifulsoup4 安装后仍无法 import", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 run_pipeline.py <wechat_article_raw.html>", file=sys.stderr)
        sys.exit(1)

    # 零依赖兜底：缺 bs4 自动装（学员第一次跑时大概率会触发）
    _ensure_dependencies()

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
    print("   1. 打开 mp.weixin.qq.com → 新建图文消息")
    print("   2. 编辑器里直接 Ctrl+V（Mac: Cmd+V）")
    print("   3. 如果剪贴板被别的内容覆盖，再回预览页点右上角「📋 一键复制到公众号」")
    print("   4. 起标题 → 点「保存为草稿」或「发布」")
    print("=" * 60)


if __name__ == "__main__":
    main()
