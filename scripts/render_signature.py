#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签名区渲染器（阶段 1 / 阶段 2 自动分流）。

工作流程：
  1. 检测 ~/.wechat-article-config/author-card.json
  2. 存在 → 输出阶段 2（完整签名卡：头像 + 公众号跳转 + CTA）
  3. 不存在 → 用命令行参数输出阶段 1（纯文字签名区）

用法:
  # 阶段 1（首次使用，配置不存在时）:
  python3 render_signature.py \\
      --author-name "张明" \\
      --author-tagline "20年钢琴老师，3000名学生考级通过" \\
      --ending-motto "慢就是快"

  # 阶段 2（配置存在时自动使用 author-card.json，命令行参数忽略）

输出：HTML 片段写到 stdout，直接插入 .article-body 下方。
"""

import argparse
import json
import os
import sys
from pathlib import Path


CONFIG_PATH = Path.home() / ".wechat-article-config" / "author-card.json"


def escape_html(text: str) -> str:
    """简单 HTML 转义，防止特殊字符破坏模板。"""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_stage1(author_name: str, author_tagline: str, ending_motto: str) -> str:
    """阶段 1：纯文字签名区（无头像、无跳转、无 CTA）。"""
    name = escape_html(author_name) or "（未填写姓名）"
    tagline = escape_html(author_tagline) or ""
    motto = escape_html(ending_motto) or ""

    parts = [
        '<div class="footer-fixed">',
        '  <div class="footer-divider">— — —</div>',
    ]

    if motto:
        parts.extend([
            '  <div class="sign-motto-box">',
            f'    <div class="sign-motto">"{motto}"</div>',
            '  </div>',
        ])

    parts.extend([
        '  <div class="author-card-text" style="text-align:center; padding:20px 0;">',
        f'    <div class="author-name" style="font-size:20px; font-weight:700; color:#222; margin-bottom:8px;">{name}</div>',
    ])
    if tagline:
        parts.append(
            f'    <div class="author-tagline" style="font-size:14px; color:#666;">{tagline}</div>'
        )
    parts.extend([
        '  </div>',
        '</div>',
    ])

    return "\n".join(parts)


def render_stage2(config: dict) -> str:
    """阶段 2：完整签名卡（从 author-card.json 读取）。"""
    def g(key: str, default: str = "") -> str:
        return escape_html(config.get(key, default))

    author_name = g("author_name")
    author_avatar_url = g("author_avatar_url")
    author_tagline = g("author_tagline")
    mp_biz_id = g("mp_biz_id")

    parts = [
        '<div class="footer-fixed">',
        '  <div class="footer-divider">— — —</div>',
    ]

    # 金句
    ending_motto = g("ending_motto")
    ending_motto_sub = g("ending_motto_sub")
    if ending_motto:
        parts.append('  <div class="sign-motto-box">')
        parts.append(f'    <div class="sign-motto">"{ending_motto}"</div>')
        if ending_motto_sub:
            parts.append(f'    <div class="sign-motto-sub">{ending_motto_sub}</div>')
        parts.append('  </div>')

    # 作者卡（有头像 + biz_id 才走完整版）
    parts.append('  <div class="author-card">')
    if author_avatar_url and mp_biz_id:
        parts.append(
            f'    <a href="https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={mp_biz_id}#wechat_redirect">'
            f'<img class="author-avatar" src="{author_avatar_url}" alt="{author_name}"></a>'
        )
    elif author_avatar_url:
        parts.append(
            f'    <img class="author-avatar" src="{author_avatar_url}" alt="{author_name}">'
        )
    if author_name:
        parts.append(f'    <div class="author-name">{author_name}</div>')
    if author_tagline:
        parts.append(f'    <div class="author-tagline">{author_tagline}</div>')
    for slogan_key in ("author_slogan_1", "author_slogan_2"):
        slogan = g(slogan_key)
        if slogan:
            parts.append(f'    <div class="author-slogan">{slogan}</div>')
    parts.append('  </div>')

    # CTA 区
    cta_title = g("cta_title")
    cta_subtitle = g("cta_subtitle")
    if cta_title or cta_subtitle:
        parts.append('  <div class="cta-box">')
        if cta_title:
            parts.append(f'    <div class="cta-title">{cta_title}</div>')
        if cta_subtitle:
            parts.append(f'    <div class="cta-subtitle">{cta_subtitle}</div>')
        parts.append('  </div>')

    parts.append('</div>')

    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="签名区渲染器")
    parser.add_argument("--author-name", default="", help="老板姓名（阶段 1 必填）")
    parser.add_argument("--author-tagline", default="", help="老板一句话介绍（阶段 1 可选）")
    parser.add_argument("--ending-motto", default="", help="结尾金句（阶段 1 可选）")
    parser.add_argument(
        "--force-stage1",
        action="store_true",
        help="强制阶段 1（即使有配置文件也不读）",
    )
    parser.add_argument(
        "--config-path",
        default=str(CONFIG_PATH),
        help=f"配置文件路径（默认 {CONFIG_PATH}）",
    )

    args = parser.parse_args()

    config_path = Path(args.config_path).expanduser()

    if not args.force_stage1 and config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            html = render_stage2(config)
            print(html)
            print(f"\n<!-- 签名区已使用阶段 2（{config_path}） -->", file=sys.stderr)
            return
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ 配置文件读取失败（{e}），降级到阶段 1", file=sys.stderr)

    # 阶段 1
    html = render_stage1(
        author_name=args.author_name,
        author_tagline=args.author_tagline,
        ending_motto=args.ending_motto,
    )
    print(html)
    print("\n<!-- 签名区使用阶段 1（纯文字版） -->", file=sys.stderr)


if __name__ == "__main__":
    main()
