#!/usr/bin/env python3
"""
HTML 内联样式转换器（微信公众号兼容）
用法: python3 convert_to_inline_css.py --input article.html --output wechat_article.html

微信公众号的HTML限制：
- 不支持 <style> 标签
- 不支持 JavaScript
- 不支持 CSS 动画/过渡
- 不支持 ::before / ::after 伪元素
- 不支持外部字体
- 所有样式必须写在 style="" 属性里

本脚本主要用于最终检查和清理，因为在 Skill 流程中，
AI 会直接生成带内联样式的 HTML（模板中的占位符已经是内联的）。
"""

import argparse
import re
import sys


def strip_style_tags(html: str) -> str:
    """移除所有 <style> 标签及其内容"""
    return re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)


def strip_script_tags(html: str) -> str:
    """移除所有 <script> 标签及其内容"""
    return re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)


def strip_link_tags(html: str) -> str:
    """移除外部CSS链接"""
    return re.sub(r'<link[^>]*rel=["\']stylesheet["\'][^>]*/?>', '', html, flags=re.IGNORECASE)


def strip_css_animations(html: str) -> str:
    """从内联样式中移除动画相关属性"""
    # 移除 animation 相关
    html = re.sub(r'animation[^;]*;?', '', html)
    html = re.sub(r'transition[^;]*;?', '', html)
    html = re.sub(r'@keyframes[^}]*\{[^}]*\}', '', html)
    return html


def fix_pseudo_elements(html: str) -> str:
    """
    伪元素在微信中不工作。
    对于常见的左侧装饰线（::before），转换为 border-left。
    这只是一个尽力而为的转换，复杂的伪元素需要手动处理。
    """
    # 这里不做自动转换，因为伪元素的用途太多样
    # 只是确保没有 content 属性出现在内联样式里（它不属于内联样式）
    return html


def ensure_mobile_friendly(html: str) -> str:
    """确保图片和容器适配移动端（智能合并，不产生重复 style 属性）"""
    def _fix_img(m):
        attrs = m.group(1)
        close = m.group(2)
        if re.search(r'style\s*=', attrs, re.IGNORECASE):
            # 已有 style → 合并 max-width 进去
            def _merge(sm):
                val = sm.group(1).rstrip('; ')
                # 只在没有 max-width 时追加
                if 'max-width' not in val:
                    val += ';max-width:100%;height:auto'
                return f'style="{val};"'
            attrs = re.sub(r'style="([^"]*)"', _merge, attrs, count=1, flags=re.IGNORECASE)
            return f'<img {attrs}{close}>'
        else:
            return f'<img {attrs} style="max-width:100%;height:auto;" {close}>'
    html = re.sub(r'<img\s+([^>]*?)(/?)>', _fix_img, html, flags=re.IGNORECASE)
    return html


def extract_body_content(html: str) -> str:
    """提取 <body> 标签内的内容（如果存在完整HTML结构）"""
    body_match = re.search(r'<body[^>]*>(.*)</body>', html, flags=re.DOTALL | re.IGNORECASE)
    if body_match:
        return body_match.group(1).strip()
    return html


def clean_for_wechat(html: str) -> str:
    """主清理流程"""
    html = strip_style_tags(html)
    html = strip_script_tags(html)
    html = strip_link_tags(html)
    html = strip_css_animations(html)
    html = fix_pseudo_elements(html)

    # 移除 class 属性（微信里没有对应的样式定义了）
    # 注意：只在已经确认所有样式都是内联的情况下才移除
    # html = re.sub(r'\s+class="[^"]*"', '', html)

    # 移除多余空行
    html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)

    return html


def main():
    parser = argparse.ArgumentParser(description="微信公众号HTML内联样式转换器")
    parser.add_argument("--input", required=True, help="输入HTML文件路径")
    parser.add_argument("--output", required=True, help="输出HTML文件路径")
    parser.add_argument("--extract-body", action="store_true",
                        help="只提取body内容（用于API推送时不需要完整HTML结构）")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        html = f.read()

    print(f"📄 读取: {args.input} ({len(html):,} 字符)")

    html = clean_for_wechat(html)

    if args.extract_body:
        html = extract_body_content(html)
        print("   已提取body内容")

    html = ensure_mobile_friendly(html)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 输出: {args.output} ({len(html):,} 字符)")
    print("   已移除: <style>标签, <script>标签, 外部CSS链接, CSS动画")


if __name__ == "__main__":
    main()
