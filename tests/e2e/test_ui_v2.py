"""Browser walkthrough of standards/procedures, OCR consent and Word re-import comparison."""
import copy
import io
import json
import os
import sys
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conftest import SOFTWARE_QC  # noqa: E402
from e2e.test_ui import server  # noqa: E402,F401
from test_levels_ocr_reimport import _para_with_bookmark, _set_text_keep_number, _text_image  # noqa: E402

SHOTS = os.environ.get("PB_SHOTS")


def shot(pg, name):
    if SHOTS:
        pg.screenshot(path=f"{SHOTS}/{name}.png", full_page=True)


def test_levels_ocr_reimport_walkthrough(server):
    import docx
    from docx.oxml.ns import qn  # noqa: F401
    base, tmp = server
    errors = []
    with pw.sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base + "/#/register")
        pg.click("button[data-lang=en]")
        pg.fill("input[name=display_name]", "Tester"); pg.fill("input[name=workspace_name]", "WS")
        pg.fill("input[name=email]", "t2@example.org"); pg.fill("input[name=password]", "correct-horse-battery")
        pg.click("button[type=submit]")
        pg.fill("input[name=name]", "Northstar v2"); pg.select_option("select[name=doc_language]", "en")
        pg.click("text=Create project"); pg.wait_for_selector(".q")
        pid = pg.url.split("/p/")[1].split("/")[0]
        hdr = {"x-requested-with": "policybuilder", "content-type": "application/json"}
        for k, v in dict(SOFTWARE_QC, **{"DOC-02": "complete"}).items():
            assert pg.request.put(f"{base}/api/projects/{pid}/answers/{k}", data=json.dumps({"value": v, "status": "answered"}), headers=hdr).ok
        # OCR: upload a scanned image, consent, recognize
        (tmp / "scan.png").write_bytes(_text_image(["Critical vulnerabilities must be remediated within 7 days."]))
        pg.goto(f"{base}/#/p/{pid}/documents"); pg.wait_for_selector("#file", state="attached")
        pg.set_input_files("#file", str(tmp / "scan.png"))
        ocr_btn = pg.wait_for_selector("button.ocr")
        shot(pg, "1_needs_ocr")
        pg.once("dialog", lambda d: d.accept())
        ocr_btn.click()
        pg.wait_for_selector("text=OCR", timeout=60000); pg.wait_for_selector(".fact")
        shot(pg, "2_after_ocr")
        # library shows standards and procedures; select recommended set
        pg.goto(f"{base}/#/p/{pid}/library"); pg.wait_for_selector("text=Authentication and Password Standard")
        shot(pg, "3_library")
        pg.click("#savesel"); pg.wait_for_selector(".q")
        pg.goto(f"{base}/#/p/{pid}/drafts"); pg.click("#genall"); pg.wait_for_selector("a:has-text('Open')", timeout=90000)
        pols = pg.request.get(f"{base}/api/projects/{pid}/policies").json()
        hdl = [x for x in pols if x["code"] == "STD-HANDLING"][0]
        pg.goto(f"{base}/#/p/{pid}/policy/{hdl['id']}"); pg.wait_for_selector("table.doc-table")
        shot(pg, "4_standard_table")
        iam = [x for x in pols if x["code"] == "IAM"][0]
        job = pg.request.post(f"{base}/api/projects/{pid}/exports", data=json.dumps({"kind": "docx", "document_id": iam["id"], "lang": "en"}), headers=hdr).json()
        d = docx.Document(io.BytesIO(pg.request.get(base + job["download"]).body()))
        _set_text_keep_number(_para_with_bookmark(d, "IAM-G02"), "Access must be assigned through roles defined by owners.")
        t = _para_with_bookmark(d, "IAM-T01"); t._p.getparent().remove(t._p)
        anchor = _para_with_bookmark(d, "IAM-PA04")
        new_p = copy.deepcopy(anchor._p)
        for b in list(new_p.iter(qn("w:bookmarkStart"))) + list(new_p.iter(qn("w:bookmarkEnd"))):
            b.getparent().remove(b)
        anchor._p.addnext(new_p)
        from docx.text.paragraph import Paragraph
        added = Paragraph(new_p, anchor._parent); added.runs[0].text = ""
        _set_text_keep_number(added, "Privileged users must complete annual privileged-access training.")
        d.save(tmp / "IAM_edited.docx")
        pg.goto(f"{base}/#/p/{pid}/drafts"); pg.wait_for_selector("#reimp", state="attached")
        pg.set_input_files("#reimp", str(tmp / "IAM_edited.docx"))
        pg.wait_for_selector(".change"); pg.wait_for_selector("del.d-del")
        shot(pg, "5_reimport_compare")
        pg.click(".change[data-key='del:IAM-T01'] button[data-d=reject]"); pg.wait_for_timeout(300)
        pg.click(".change[data-key='mod:IAM-G02'] button[data-d=accept]"); pg.wait_for_timeout(300)
        pg.click(".change[data-key='add:1'] button[data-d=accept]"); pg.wait_for_timeout(300)
        pg.click("#apply"); pg.wait_for_selector(".clause")
        assert "Privileged users must complete annual privileged-access training." in pg.content()
        shot(pg, "6_after_apply")
        pg.click("button[data-lang=fr]"); pg.goto(f"{base}/#/p/{pid}/drafts"); pg.wait_for_selector("text=Réimporter une ébauche modifiée dans Word")
        shot(pg, "7_drafts_fr")
        br.close()
    assert errors == []
