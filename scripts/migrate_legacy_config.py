#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置迁移工具：把旧版 ~/.wechat-article-config（单文件）升级为目录形式。

背景：
  原版"公众号文章" skill 把 wechat_appid / appsecret 写在
  ~/.wechat-article-config 这个**单文件**里。学员版需要在同名路径下
  放多个文件（author-card.json / wechat-api.json），所以必须是目录。

  直接 mkdir -p ~/.wechat-article-config 在已有同名文件时会失败。
  这个脚本负责安全迁移。

迁移规则：
  1. 路径不存在            → 直接 mkdir，结束
  2. 路径是目录            → 已是新格式，啥都不做
  3. 路径是文件            → 备份成 ~/.wechat-article-config-legacy.json
                            然后 mkdir 新目录
                            如果备份的是合法的 wechat API 凭证 JSON，
                            自动复制到 ~/.wechat-article-config/wechat-api.json

用法：
  python3 migrate_legacy_config.py
  python3 migrate_legacy_config.py --dry-run    # 只看会做什么，不实际改
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


CONFIG_PATH = Path.home() / ".wechat-article-config"
LEGACY_BACKUP = Path.home() / ".wechat-article-config-legacy.json"


def detect_state():
    """返回当前路径的状态：'missing' | 'directory' | 'file'"""
    if not CONFIG_PATH.exists():
        return "missing"
    if CONFIG_PATH.is_dir():
        return "directory"
    if CONFIG_PATH.is_file():
        return "file"
    return "unknown"


def is_wechat_api_json(file_path: Path) -> bool:
    """检查文件是不是合法的 wechat API JSON（含 wechat_appid 字段）。"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, dict) and "wechat_appid" in data
    except (json.JSONDecodeError, IOError):
        return False


def migrate(dry_run: bool = False) -> int:
    """执行迁移。返回 0 = 成功，1 = 失败。"""
    state = detect_state()
    print(f"📍 检测路径：{CONFIG_PATH}")
    print(f"📊 当前状态：{state}")
    print()

    if state == "directory":
        print("✅ 已经是目录格式，无需迁移。")
        return 0

    if state == "missing":
        print(f"📁 路径不存在，{'将' if dry_run else ''}创建空目录。")
        if not dry_run:
            CONFIG_PATH.mkdir(parents=True, exist_ok=True)
            print(f"✅ 已创建：{CONFIG_PATH}")
        return 0

    if state == "file":
        is_api = is_wechat_api_json(CONFIG_PATH)
        action_label = "将" if dry_run else ""

        print(f"⚠️  路径当前是【单文件】格式（旧版 skill 留下的）。")
        if is_api:
            print(f"   内容是合法的 wechat API JSON（含 wechat_appid）。")
        else:
            print(f"   内容不是标准 wechat API JSON 格式。")
        print()
        print(f"📋 迁移计划：")
        print(f"   1. {action_label}把当前文件备份到 {LEGACY_BACKUP}")
        print(f"   2. {action_label}创建新目录 {CONFIG_PATH}")
        if is_api:
            print(f"   3. {action_label}把备份内容复制到 {CONFIG_PATH}/wechat-api.json")
        print()

        if dry_run:
            print("🟡 dry-run 模式，未实际执行。再跑一次去掉 --dry-run 就执行。")
            return 0

        # 实际执行
        try:
            # Step 1: 备份
            shutil.copy2(CONFIG_PATH, LEGACY_BACKUP)
            print(f"✅ 已备份：{LEGACY_BACKUP}")

            # Step 2: 删除旧文件，建新目录
            CONFIG_PATH.unlink()
            CONFIG_PATH.mkdir(parents=True, exist_ok=True)
            print(f"✅ 已创建目录：{CONFIG_PATH}")

            # Step 3: 如果是 API JSON，复制到新位置
            if is_api:
                target = CONFIG_PATH / "wechat-api.json"
                shutil.copy2(LEGACY_BACKUP, target)
                print(f"✅ API 配置已迁移：{target}")
            else:
                print(f"ℹ️  原文件已备份到 {LEGACY_BACKUP}，没有自动迁移到新目录")
                print(f"   （内容不是标准 API JSON，你可以手动检查后决定怎么放）")

            print()
            print("🎉 迁移完成。现在可以正常使用学员版 skill。")
            return 0

        except Exception as e:
            print(f"❌ 迁移失败：{e}", file=sys.stderr)
            return 1

    print(f"❓ 未知路径状态，跳过。", file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(description="配置目录迁移工具")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示会做什么，不实际修改",
    )
    args = parser.parse_args()
    sys.exit(migrate(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
