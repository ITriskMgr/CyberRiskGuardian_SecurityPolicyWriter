"""Browser walkthrough (Playwright + Chromium). Starts the real server on a free port with a temporary data folder.
Run: python -m pytest tests/e2e -q   (skipped when Playwright is not installed)."""
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from conftest import SOFTWARE_QC, make_docx  # noqa: E402


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("e2e")
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    env = dict(os.environ, PB_DATA_DIR=str(tmp / "data"), PB_NO_BROWSER="1", PB_AI_PROVIDER="mock")
    env.pop("ANTHROPIC_API_KEY", None)
    proc = subprocess.Popen([sys.executable, "serve.py", str(port)], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(60):
        try:
            import urllib.request
            urllib.request.urlopen(base + "/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    yield base, tmp
    proc.terminate()
    proc.wait(10)


def test_walkthrough(server):
    base, tmp = server
    (tmp / "old.docx").write_bytes(make_docx(["Multi-factor authentication is required for privileged accounts only."], "Access Policy 2019"))
    errors = []
    with pw.sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base + "/")  # first visit, not signed in: must land on the sign-in form, not an error
        pg.wait_for_selector("input[name=email]")
        assert "#/login" in pg.url
        pg.click("a[href='#/register']")
        pg.wait_for_selector("input[name=workspace_name]")
        pg.click("button[data-lang=en]")
        pg.fill("input[name=display_name]", "Tester"); pg.fill("input[name=workspace_name]", "WS")
        pg.fill("input[name=email]", "t@example.org"); pg.fill("input[name=password]", "correct-horse-battery")
        pg.click("button[type=submit]")
        pg.fill("input[name=name]", "Northstar"); pg.select_option("select[name=doc_language]", "both")
        pg.click("text=Create project"); pg.wait_for_selector(".q")
        pg.fill(".q[data-code='ORG-01'] input", "Northstar Digital Services Inc."); pg.keyboard.press("Tab")
        pg.check(".q[data-code='ORG-02'] input[value=software_saas]")
        pg.wait_for_function("document.querySelectorAll('.saved').length && [...document.querySelectorAll('.saved')].some(s => s.textContent)")
        pid = pg.url.split("/p/")[1].split("/")[0]
        hdr = {"x-requested-with": "policybuilder", "content-type": "application/json"}
        for k, v in SOFTWARE_QC.items():
            assert pg.request.put(f"{base}/api/projects/{pid}/answers/{k}", data=json.dumps({"value": v, "status": "answered"}), headers=hdr).ok
        pg.goto(f"{base}/#/p/{pid}/documents"); pg.wait_for_selector("#file", state="attached")
        pg.set_input_files("#file", str(tmp / "old.docx")); pg.wait_for_selector(".fact")
        pg.click(".fact[data-a=confirm] >> nth=0"); pg.wait_for_selector("text=Confirmed")
        pg.goto(f"{base}/#/p/{pid}/library"); pg.wait_for_selector(".pick"); pg.click("#savesel")
        pg.wait_for_selector(".use-sugg"); pg.click(".use-sugg >> nth=0")
        pg.goto(f"{base}/#/p/{pid}/drafts"); pg.click("#genall"); pg.wait_for_selector("a:has-text('Open')", timeout=60000)
        pg.click("a:has-text('Open') >> nth=0"); pg.wait_for_selector("mark.ph")
        pg.click("button[data-lang=fr]"); pg.wait_for_selector("text=Télécharger Word")
        pg.click("[data-dl=fr]"); pg.wait_for_selector("text=ÉBAUCHE — NON APPROUVÉE")
        pg.goto(f"{base}/#/p/{pid}/export"); pg.wait_for_selector("#zip")
        with pg.expect_download() as d:
            pg.click("#zip")
        assert d.value.suggested_filename.endswith(".zip")
        pg.set_viewport_size({"width": 390, "height": 844}); pg.goto(f"{base}/#/p/{pid}/interview"); pg.wait_for_selector(".q")
        assert pg.evaluate("document.documentElement.scrollWidth") <= 400
        br.close()
    assert errors == []
