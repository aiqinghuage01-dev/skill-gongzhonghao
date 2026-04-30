#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号文章-学员版 一键安装 + 环境检查脚本（幂等）。

用法:
    python scripts/setup.py            # 安装依赖（缺啥装啥）
    python scripts/setup.py --check    # smoke test，只检查不装东西

幂等性：重复跑不重复装、不报错。
"""

import os
import subprocess
import sys
import tempfile
import platform

PY_MIN = (3, 8)
# (import 名, pip 包名)
DEPS = [
    ("bs4", "beautifulsoup4"),
]
KEY_SCRIPTS = [
    "run_pipeline.py",
    "convert_to_wechat_markup.py",
    "copy_html_to_clipboard.py",
    "open_preview.py",
    "convert_to_inline_css.py",
    "render_signature.py",
    "migrate_legacy_config.py",
]


def header(msg):
    print("=" * 56)
    print(msg)
    print("=" * 56)


def check_python():
    v = sys.version_info
    if (v.major, v.minor) < PY_MIN:
        print(f"❌ Python 版本太低: {v.major}.{v.minor}.{v.micro}，需要 >= {PY_MIN[0]}.{PY_MIN[1]}")
        return False
    print(f"✅ Python {v.major}.{v.minor}.{v.micro}（>= {PY_MIN[0]}.{PY_MIN[1]} ✓）")
    return True


def check_platform():
    p = platform.system()
    print(f"✅ 平台: {p} {platform.machine()}")
    if p == "Linux":
        # Linux 学员需要 xclip 来塞剪贴板
        r = subprocess.run(["which", "xclip"], capture_output=True)
        if r.returncode != 0:
            print("⚠️  Linux 检测到缺 xclip（剪贴板功能依赖）。")
            print("   安装方法：sudo apt-get install xclip")
            return False
    return True


def check_module(import_name):
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def install_pkg(pip_name):
    print(f"   pip install {pip_name}...")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", pip_name],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        print(f"❌ {pip_name} 安装失败")
        if r.stderr:
            print(f"   stderr: {r.stderr.strip()[:300]}")
        return False
    return True


def check_tempdir_writable():
    try:
        d = tempfile.gettempdir()
        test = os.path.join(d, ".wechat_article_setup_smoketest")
        with open(test, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test)
        print(f"✅ 临时目录可写: {d}")
        return True
    except Exception as e:
        print(f"❌ 临时目录不可写: {e}")
        return False


def check_key_scripts():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    missing = [s for s in KEY_SCRIPTS if not os.path.exists(os.path.join(scripts_dir, s))]
    if missing:
        print(f"❌ 缺少关键脚本: {', '.join(missing)}")
        return False
    print(f"✅ 关键脚本齐全（{len(KEY_SCRIPTS)} 个）")
    return True


def check_assets_and_refs():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    needed = [
        ("assets/template-v3-clean.html", "V3 Clean HTML 模板"),
        ("references/style-bible.md", "写作风格手册"),
    ]
    all_ok = True
    for rel, desc in needed:
        if not os.path.exists(os.path.join(root, rel)):
            print(f"❌ 缺少 {desc}: {rel}")
            all_ok = False
    if all_ok:
        print(f"✅ 模板和参考文档齐全")
    return all_ok


def main():
    check_only = "--check" in sys.argv

    header("公众号文章-学员版 环境检查" + ("（smoke test 模式）" if check_only else ""))

    # 1. Python 版本
    if not check_python():
        sys.exit(1)

    # 2. 平台
    check_platform()  # warn-only

    # 3. 临时目录
    if not check_tempdir_writable():
        sys.exit(1)

    # 4. 关键脚本
    if not check_key_scripts():
        sys.exit(1)

    # 5. 模板和参考
    if not check_assets_and_refs():
        sys.exit(1)

    # 6. Python 第三方依赖
    print()
    print("[检查 Python 依赖]")
    missing = [(imp, pkg) for imp, pkg in DEPS if not check_module(imp)]
    if not missing:
        for imp, _ in DEPS:
            print(f"✅ {imp}")
    else:
        for imp, _ in DEPS:
            print(f"{'✅' if check_module(imp) else '❌'} {imp}")
        if check_only:
            print()
            print(f"❌ smoke test 失败：缺少 {', '.join(p for _, p in missing)}")
            print(f"   修复：跑 python scripts/setup.py（不带 --check）自动安装")
            sys.exit(1)
        # 装依赖
        print()
        print("[自动安装缺失依赖]")
        for imp, pkg in missing:
            if not install_pkg(pkg):
                sys.exit(1)
        # 二次验证
        print()
        print("[安装后再次验证]")
        for imp, pkg in missing:
            if not check_module(imp):
                print(f"❌ {imp} 安装后仍无法 import，可能是 pip 装错环境")
                sys.exit(1)
            print(f"✅ {imp}")

    print()
    header("✅ 环境就绪，可以开始写公众号文章了")


if __name__ == "__main__":
    main()
