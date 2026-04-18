#!/usr/bin/env python3
"""
微信公众号 HTML 标记格式转换器

微信公众号富文本编辑器使用特殊的标记格式（从成功发布的文章逆向分析得出）：
1. 容器用 <section> 不用 <div>
2. 标题用 <p> 不用 <h1>/<h2>
3. 文本节点用 <span leaf="">文字</span> 包裹
4. 换行用 <br  /> (两个空格+斜杠)
5. 末尾加 <p style="display:none;"><mp-style-type data-value="10000"></mp-style-type></p>
6. CSS 完全保留 — flex/gap/gradient/text-shadow/box-shadow 等全部支持

重要：微信不兼容的是 HTML 标签，不是 CSS！
  ✅ display:flex, gap, flex:1, text-shadow, linear-gradient, box-shadow
  ❌ <div>（必须用 <section>）, 裸文本节点（必须用 <span leaf="">）

用法:
  python3 convert_to_wechat_markup.py --input raw.html --output wechat.html
  python3 convert_to_wechat_markup.py --input raw.html --output wechat.html --extract-body
"""

import argparse
import re
import sys
import json
from bs4 import BeautifulSoup, Tag, NavigableString, Comment


def inline_css(html):
    """将 <style> 块中的 CSS 内联到元素的 style 属性上，然后移除 <style> 块。
    使用 premailer 库实现，确保微信删掉 <style> 后样式不丢失。"""
    # 只有当 HTML 包含 <style> 块时才需要内联
    if not re.search(r'<style[^>]*>', html, re.IGNORECASE):
        return html

    try:
        from premailer import transform
        html = transform(
            html,
            remove_classes=True,        # 内联后删掉 class 属性（微信不需要）
            strip_important=True,        # 移除 !important
            keep_style_tags=False,       # 内联完毕后删除 <style> 块
            cssutils_logging_level=50,   # 静默 cssutils 的警告
        )
        print("🎨 CSS 内联: 已将 <style> 规则内联到元素 style 属性")
    except ImportError:
        print("⚠️ premailer 未安装，跳过 CSS 内联（请运行: pip3 install premailer）")
        # fallback: 直接删掉 <style>（会丢样式，但至少不报错）
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    return html


def convert_to_wechat(html):
    """将标准 HTML 转换为微信公众号标记格式"""

    # === Step 0: 清理 HTML 注释 ===
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # === Step 0.5: CSS 内联 + 移除 <style>/<script>/<link> 标签 ===
    # 先内联 CSS（将 <style> 中的规则写入元素 style=""），再删除残留标签
    html = inline_css(html)
    # 确保 <script>/<link> 也被清理
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<link[^>]*rel=["\']stylesheet["\'][^>]*/?>', '', html, flags=re.IGNORECASE)

    soup = BeautifulSoup(html, 'html.parser')

    # === Step 1: 提取 body 内容（如果有完整 HTML 结构）===
    body = soup.find('body')
    if body:
        # 保留 body 的子节点，丢弃 head/html 外壳
        new_soup = BeautifulSoup('', 'html.parser')
        for child in list(body.children):
            new_soup.append(child.extract())
        soup = new_soup

    # === Step 2: div → section ===
    for tag in soup.find_all('div'):
        tag.name = 'section'

    # === Step 3: h1/h2/h3 → p（保留样式）===
    for heading in soup.find_all(['h1', 'h2', 'h3']):
        heading.name = 'p'

    # === Step 4: 包裹所有文本节点为 <span leaf=""> ===
    def wrap_text_nodes(element):
        for child in list(element.children):
            if isinstance(child, Comment):
                # 移除残留的 Comment 对象
                child.extract()
            elif isinstance(child, NavigableString):
                text = str(child)
                if text.strip():
                    span = soup.new_tag('span')
                    span.attrs['leaf'] = ''
                    span.string = text
                    child.replace_with(span)
            elif isinstance(child, Tag):
                if child.name not in ('br', 'img', 'mp-style-type'):
                    wrap_text_nodes(child)

    wrap_text_nodes(soup)

    # === Step 5: flex 容器内的小图标（固定宽高 ≤72px）→ span ===
    for el in soup.find_all('section', style=True):
        style = el.get('style', '')
        if 'display:flex' not in style.replace(' ', ''):
            continue
        for child in el.find_all('section', recursive=False):
            child_style = child.get('style', '').rstrip().rstrip(';') + ';'  # 确保末尾有分号
            w_match = re.search(r'width:(\d+)px', child_style)
            h_match = re.search(r'height:(\d+)px', child_style)
            if w_match and h_match:
                w, h = int(w_match.group(1)), int(h_match.group(1))
                if w <= 72 and h <= 72:
                    child.name = 'span'
                    if 'display:flex' in child_style:
                        child_style = child_style.replace('display:flex', 'display:inline-block')
                        if f'line-height:{h}px' not in child_style:
                            child_style += f' text-align:center;line-height:{h}px;'
                        child['style'] = child_style
                    elif 'display:' not in child_style:
                        child_style += f' display:inline-block;text-align:center;line-height:{h}px;'
                        child['style'] = child_style

    # === Step 6: flex 行内的简单子元素 → span ===
    for el in soup.find_all('section', style=True):
        style = el.get('style', '').replace(' ', '')
        if 'display:flex' not in style or 'flex-direction:column' in style:
            continue
        for child in [c for c in el.children if isinstance(c, Tag)]:
            if child.name != 'section':
                continue
            cs = child.get('style', '')
            has_block = any(p in cs for p in ['padding:', 'border-radius:', 'box-shadow:', 'border:'])
            if not has_block and 'flex:1' not in cs:
                child.name = 'span'

    # === Step 7: 图片添加 max-width:100%（头像等固定尺寸图片不加 height:auto）===
    for img in soup.find_all('img'):
        style = img.get('style', '')
        if 'max-width' not in style:
            # 如果图片已有明确的 width+height+border-radius:50%（圆形头像），
            # 只加 max-width，不加 height:auto，避免破坏正圆形
            has_fixed_size = ('border-radius:50%' in style.replace(' ', '') or
                             'border-radius: 50%' in style)
            if has_fixed_size:
                img['style'] = style.rstrip('; ') + ';max-width:100%;' if style else 'max-width:100%;'
            else:
                img['style'] = style.rstrip('; ') + ';max-width:100%;height:auto;' if style else 'max-width:100%;height:auto;'

    # === Step 8: 添加 mp-style-type 结尾标记 ===
    mp_p = soup.new_tag('p')
    mp_p['style'] = 'display:none;'
    mp_tag = soup.new_tag('mp-style-type')
    mp_tag.attrs['data-value'] = '10000'
    mp_p.append(mp_tag)
    soup.append(mp_p)

    # === Step 9: 转字符串 + 修复 <br> 格式 ===
    result = str(soup)
    result = re.sub(r'<br\s*/?>', '<br  />', result)

    # 清理多余空行
    result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)

    return result


def extract_metadata(html):
    """从 HTML 中提取标题和摘要信息"""
    soup = BeautifulSoup(html, 'html.parser')
    meta = {}

    # 先从 hero 标题获取标题，再回退到 h1
    hero_title = soup.select_one('.hero-title')
    if hero_title:
        meta['title'] = hero_title.get_text(strip=True)

    # 尝试从 h1 获取标题
    h1 = soup.find('h1')
    if h1 and 'title' not in meta:
        # 提取纯文本，处理 <br> 为空格
        for br in h1.find_all('br'):
            br.replace_with(' ')
        meta['title'] = h1.get_text(strip=True)

    # 先从 hero 副标题获取摘要，再回退到旧版 hero p 提取逻辑
    hero = soup.select_one('.hero')
    hero_subtitle = soup.select_one('.hero-subtitle')
    if hero_subtitle:
        text = hero_subtitle.get_text(strip=True)
        if len(text) > 10:
            meta['digest'] = text.replace('\n', ' ')[:120]

    if not hero:
        for el in soup.find_all(style=True):
            style = el.get('style', '')
            if 'linear-gradient' in style and ('padding' in style or 'text-align:center' in style):
                hero = el
                break

    if hero:
        if 'digest' not in meta:
            paragraphs = hero.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 10:
                    meta['digest'] = text.replace('\n', ' ')[:120]
                    break

    return meta


def main():
    parser = argparse.ArgumentParser(description="微信公众号HTML标记格式转换器")
    parser.add_argument("--input", required=True, help="输入HTML文件路径")
    parser.add_argument("--output", required=True, help="输出HTML文件路径")
    parser.add_argument("--meta", help="输出元数据JSON文件（标题、摘要）")
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        html = f.read()

    print(f"📄 读取: {args.input} ({len(html):,} 字符)")

    # 提取元数据（在转换前，因为转换会改标签名）
    if args.meta:
        meta = extract_metadata(html)
        with open(args.meta, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"📋 元数据: {meta}")

    # 转换
    result = convert_to_wechat(html)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"✅ 输出: {args.output} ({len(result):,} 字符)")

    # 验证
    checks = {
        'section': result.count('<section'),
        'span_leaf': result.count('span leaf'),
        'mp-style-type': result.count('mp-style-type'),
        'div': result.count('<div'),
        'display_flex': result.count('display:flex'),
    }
    print(f"   检查: {checks}")

    issues = []
    if checks['div'] > 0:
        issues.append(f'{checks["div"]}个<div>未转换')
    if checks['span_leaf'] == 0:
        issues.append('无span leaf')
    if checks['mp-style-type'] == 0:
        issues.append('缺少mp-style-type')
    if '<style' in result.lower():
        issues.append('<style>标签残留')

    if issues:
        print(f"   ⚠️ 问题: {', '.join(issues)}")
    else:
        print(f"   ✅ 微信标记格式验证通过")


if __name__ == '__main__':
    main()
