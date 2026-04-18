#!/usr/bin/env python3
"""
⚠️ 已废弃 — 请使用 convert_to_wechat_markup.py 代替

本脚本基于错误假设：认为微信不支持 flex/gap/text-shadow 等 CSS 属性。
实际经过验证，微信完全支持这些 CSS，不兼容的是 HTML 标签结构。

正确方案：convert_to_wechat_markup.py
- div → section（微信要求用 section）
- 文本包裹 <span leaf="">（微信要求的标记格式）
- 添加 mp-style-type 元数据
- 保留所有 CSS 不修改

错误方案（本脚本之前做的）：
- section → div（方向反了！微信需要 section）
- 删除 gap/text-shadow/flex-shrink（不需要删！微信支持这些）
- flex:1 → 百分比宽度（不需要！微信支持 flex:1）
"""

import sys
print("⚠️  此脚本已废弃！请改用: python3 scripts/convert_to_wechat_markup.py --input X --output Y")
print("   详见 SKILL.md Phase 3")
sys.exit(1)
