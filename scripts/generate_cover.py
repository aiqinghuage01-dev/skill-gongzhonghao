#!/usr/bin/env python3
"""
封面图生成器
用法: python3 generate_cover.py --title "别瞎学AI" --subtitle "副标题" --label "老板必看" --output "${TMPDIR}/preview/cover.jpg"

流程: 生成 cover.html → 启动临时 WEBrick 服务器 → Chrome headless 截图 → 清理
"""

import argparse
import subprocess
import os
import time
import signal
import sys

COVER_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=900, initial-scale=1.0">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Noto Sans SC', -apple-system, sans-serif;
    width: 900px; height: 383px;
    overflow: hidden;
    background: #0a0a0a;
    display: flex; align-items: center; justify-content: center;
    position: relative;
  }}
  body::before {{
    content: '';
    position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background:
      radial-gradient(ellipse at 20% 50%, rgba(120, 80, 255, 0.15) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 20%, rgba(255, 100, 50, 0.1) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 80%, rgba(50, 200, 255, 0.08) 0%, transparent 50%);
  }}
  .content {{ position: relative; z-index: 2; text-align: center; }}
  .label {{
    font-size: 16px; font-weight: 300; color: rgba(255,255,255,0.4);
    letter-spacing: 4px; margin-bottom: 18px;
  }}
  .title {{
    font-size: {title_font_size}px; font-weight: 900; line-height: 1.2;
    background: linear-gradient(135deg, #7850ff, #ff6432, #32c8ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .subtitle {{
    font-size: 15px; color: rgba(255,255,255,0.4); margin-top: 20px;
    font-weight: 300; line-height: 1.8;
  }}
  .dot1, .dot2, .dot3 {{ position: absolute; border-radius: 50%; }}
  .dot1 {{ width: 4px; height: 4px; background: rgba(120,80,255,0.5); top: 20%; left: 15%; }}
  .dot2 {{ width: 6px; height: 6px; background: rgba(255,100,50,0.4); top: 30%; right: 20%; }}
  .dot3 {{ width: 3px; height: 3px; background: rgba(50,200,255,0.5); bottom: 25%; left: 35%; }}
</style>
</head>
<body>
  <div class="dot1"></div>
  <div class="dot2"></div>
  <div class="dot3"></div>
  <div class="content">
    <div class="label">{label}</div>
    <div class="title">{title}</div>
    <div class="subtitle">{subtitle}</div>
  </div>
</body>
</html>"""

import tempfile
import platform as _platform

# Chrome 路径按平台自动识别
if _platform.system() == "Darwin":
    CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif _platform.system() == "Windows":
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
else:
    CHROME_PATH = "/usr/bin/google-chrome"

# 预览目录跨平台用 tempfile
PREVIEW_DIR = os.path.join(tempfile.gettempdir(), "preview")


def main():
    parser = argparse.ArgumentParser(description="生成微信公众号封面图")
    parser.add_argument("--title", required=True, help="封面大标题（2-6个字效果最好）")
    parser.add_argument("--subtitle", default="", help="副标题（可多行，用<br>分隔）")
    parser.add_argument("--label", default="老板必看", help="顶部小标签（建议 2-6 字）")
    parser.add_argument("--output", default=f"{PREVIEW_DIR}/cover.jpg", help="输出图片路径")
    parser.add_argument("--port", type=int, default=8090, help="临时服务器端口（默认8090）")
    args = parser.parse_args()

    # 根据标题长度调整字号
    title_len = len(args.title)
    if title_len <= 4:
        title_font_size = 72
    elif title_len <= 6:
        title_font_size = 64
    elif title_len <= 10:
        title_font_size = 48
    else:
        title_font_size = 36

    # 确保目录存在
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    # 生成 cover HTML
    cover_html = COVER_TEMPLATE.format(
        title=args.title,
        subtitle=args.subtitle,
        label=args.label,
        title_font_size=title_font_size,
    )

    cover_html_path = os.path.join(PREVIEW_DIR, "cover.html")
    with open(cover_html_path, "w", encoding="utf-8") as f:
        f.write(cover_html)

    print(f"📄 封面HTML已生成: {cover_html_path}")

    # 启动临时 WEBrick 服务器
    print(f"🌐 启动临时服务器 (端口 {args.port})...")
    server_proc = subprocess.Popen(
        [
            "/usr/bin/ruby", "-e",
            f"require 'webrick'; s=WEBrick::HTTPServer.new(:Port=>{args.port},:DocumentRoot=>'{PREVIEW_DIR}',:Logger=>WEBrick::Log.new('/dev/null'),:AccessLog=>[]); trap('INT'){{s.shutdown}}; s.start"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # 等待服务器启动
        time.sleep(1)

        # Chrome headless 截图
        print(f"📸 截图中...")
        screenshot_cmd = [
            CHROME_PATH,
            "--headless",
            f"--screenshot={args.output}",
            "--window-size=900,383",
            "--hide-scrollbars",
            "--disable-gpu",
            "--no-sandbox",
            f"http://localhost:{args.port}/cover.html",
        ]

        result = subprocess.run(screenshot_cmd, capture_output=True, text=True, timeout=15)

        if os.path.exists(args.output):
            file_size = os.path.getsize(args.output)
            print(f"✅ 封面图已生成: {args.output} ({file_size:,} bytes)")
        else:
            print(f"❌ 截图失败")
            if result.stderr:
                print(f"   错误: {result.stderr[:200]}")
            sys.exit(1)

    finally:
        # 关闭临时服务器
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("🧹 临时服务器已关闭")


if __name__ == "__main__":
    main()
