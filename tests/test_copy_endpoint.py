#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_for_server(port):
    deadline = time.time() + 3
    while time.time() < deadline:
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=0.1)
            sock.close()
            return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("server did not start")


class CopyEndpointTest(unittest.TestCase):
    def test_windows_cf_html_offsets_wrap_original_fragment(self):
        clip = _load_module("copy_html_to_clipboard", SCRIPTS / "copy_html_to_clipboard.py")
        html = '<section><span leaf="">中文 hello</span></section><mp-style-type data-value="10000"></mp-style-type>'
        cf_html = clip.build_windows_cf_html(html)
        fields = {}
        for line in cf_html.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                if key in {"StartHTML", "EndHTML", "StartFragment", "EndFragment"}:
                    fields[key] = int(value)

        data = cf_html.encode("utf-8")
        fragment = data[fields["StartFragment"]:fields["EndFragment"]].decode("utf-8")
        full_html = data[fields["StartHTML"]:fields["EndHTML"]].decode("utf-8")

        self.assertEqual(fragment, html)
        self.assertIn("<!--StartFragment-->", full_html)
        self.assertIn("<!--EndFragment-->", full_html)
        self.assertIn("<mp-style-type", fragment)

    def test_preview_button_uses_local_endpoint_not_browser_clipboard(self):
        open_preview = _load_module("open_preview", SCRIPTS / "open_preview.py")
        preview = open_preview.build_enhanced_preview(
            "<html><body><p>preview</p></body></html>",
            '<section><span leaf="">hello</span></section><p><mp-style-type data-value="10000"></mp-style-type></p>',
        )

        self.assertIn("/__copy_wechat", preview)
        self.assertNotIn("new ClipboardItem", preview)
        self.assertNotIn("document.execCommand", preview)
        self.assertNotIn("writeText(", preview)

    def test_copy_endpoint_reads_wechat_html_with_wechat_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            wechat = Path(tmp) / "wechat_article.html"
            wechat.write_text(
                '<section style="color:red"><span leaf="">hello</span></section>'
                '<p style="display:none"><mp-style-type data-value="10000"></mp-style-type></p>',
                encoding="utf-8",
            )

            port = _free_port()
            env = os.environ.copy()
            env["NRG_COPY_DRY_RUN"] = "1"
            proc = subprocess.Popen(
                [sys.executable, str(SCRIPTS / "_temp_http_server.py"), str(port), tmp, "30"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
            try:
                _wait_for_server(port)
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/__copy_wechat",
                    data=b"",
                    method="POST",
                    headers={"Accept": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))

                self.assertTrue(payload["ok"])
                self.assertTrue(payload["dry_run"])
                self.assertEqual(payload["markers"]["section"], 1)
                self.assertEqual(payload["markers"]["span_leaf"], 1)
                self.assertEqual(payload["markers"]["mp_style_type"], 1)
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    unittest.main()
