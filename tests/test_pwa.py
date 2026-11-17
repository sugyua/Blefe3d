"""Regressões para PWA, ícones reais e cache conservador."""
import asyncio
import json
from pathlib import Path
import struct
import unittest
import zlib

import pwa_icons
import server


PUBLIC=Path(__file__).resolve().parent.parent/"public"


class PwaTests(unittest.TestCase):
    def test_manifest_is_valid_and_installable(self):
        data=json.loads((PUBLIC/"manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(data["display"],"standalone")
        self.assertEqual(data["scope"],"/")
        self.assertEqual(data["lang"],"pt-BR")
        self.assertEqual({x["sizes"] for x in data["icons"] if x["type"]=="image/png"},{"192x192","512x512"})

    def test_png_icons_have_real_pixels(self):
        for size in (180,192,512):
            with self.subTest(size=size):
                png=pwa_icons.icon_png(size)
                self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(struct.unpack(">II",png[16:24]),(size,size))
                self.assertGreater(len(png),1000)
                self.assertEqual(pwa_icons.icon_png(size),png)

    def test_service_worker_excludes_dynamic_requests(self):
        sw=(PUBLIC/"sw.js").read_text(encoding="utf-8")
        self.assertIn("r.mode==='navigate'",sw)
        self.assertIn("u.pathname.startsWith('/static/')",sw)
        self.assertIn("u.pathname.startsWith('/icons/')",sw)
        self.assertNotIn("cache.addAll(['/'])",sw)
        self.assertIn("fetch(r)",sw)

    def test_install_controls_have_targets(self):
        page=(PUBLIC/"index.html").read_text(encoding="utf-8")
        script=(PUBLIC/"pwa.js").read_text(encoding="utf-8")
        for field in ("installApp","welcomeGuide","welcomeClose","installModal","publicBrowse"):
            self.assertIn(f'id="{field}"',page)
        self.assertIn("beforeinstallprompt",script)
        self.assertIn("serviceWorker.register('/sw.js'",script)
        self.assertIn('href="/manifest.webmanifest"',page)


class PwaHandlersTests(unittest.IsolatedAsyncioTestCase):
    async def test_dynamic_png_http_response(self):
        class Request:
            match_info={"size":"192"}
        result=await server.pwa_icon(Request())
        self.assertEqual(result.content_type,"image/png")
        self.assertTrue(result.body.startswith(b"\x89PNG"))


if __name__=="__main__":
    unittest.main()
