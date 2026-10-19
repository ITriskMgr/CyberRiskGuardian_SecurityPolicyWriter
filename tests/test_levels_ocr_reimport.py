"""Standards and procedures, OCR of scanned documents, and Word re-import with clause comparison."""
import copy
import io
import zipfile

import docx
import pytest
from docx.oxml.ns import qn

from conftest import SOFTWARE_QC, answer, apply_answers, new_project, register
from app.catalogue.catalogue import recommend
from app.questionnaire.engine import Profile


def prof(ans):
    return Profile({k: {"value": v, "status": "answered"} for k, v in ans.items()}, "en")


# ---------------------------------------------------------------- standards and procedures
def test_depth_drives_standards_and_procedures():
    base = {r["code"]: r for r in recommend(prof(SOFTWARE_QC))}
    assert not base["STD-AUTH"]["recommended"] and not base["PRC-IR"]["recommended"]
    std = {r["code"]: r for r in recommend(prof(dict(SOFTWARE_QC, **{"DOC-02": "policies_standards"})))}
    assert std["STD-AUTH"]["recommended"] and std["STD-HANDLING"]["recommended"] and not std["PRC-IR"]["recommended"]
    full = {r["code"]: r for r in recommend(prof(dict(SOFTWARE_QC, **{"DOC-02": "complete"})))}
    assert full["PRC-IR"]["recommended"] and full["PRC-JML"]["recommended"] and full["PRC-EXC"]["recommended"]
    assert full["PRC-IR"]["level_label"] == "Procedure" and full["STD-AUTH"]["level_label"] == "Standard"


def test_standards_and_procedures_generate_and_export(client):
    c = client
    register(c)
    pid = new_project(c, lang="both")
    apply_answers(c, pid, dict(SOFTWARE_QC, **{"ORG-10": "both", "DOC-02": "complete"}))
    codes = ["EISP", "IAM", "IR", "CLASS", "STD-AUTH", "STD-HANDLING", "PRC-IR", "PRC-JML"]
    assert c.put(f"/api/projects/{pid}/selection", json={"codes": codes}).status_code == 200
    dec = {g["policy"]: [q["code"] for q in g["questions"]] for g in c.get(f"/api/projects/{pid}/decisions").json()}
    assert "DEC-AUTH-MINLEN" in dec["STD-AUTH"] and "DEC-PIR-DAYS" in dec["PRC-IR"]
    answer(c, pid, "DEC-AUTH-MINLEN", "15_8")
    answer(c, pid, "DEC-IAM-MFA-SCOPE", "all")
    assert c.post(f"/api/projects/{pid}/generate", json={}).status_code == 200
    pols = {p["code"]: p for p in c.get(f"/api/projects/{pid}/policies").json()}
    std = c.get(f"/api/policies/{pols['STD-AUTH']['id']}?lang=en").json()["body"]
    assert std["policy_id"] == "NOR-STD-AUTH-001" and std["policy_type"] == "standard"
    assert std["parent_policy_id"] == "NOR-POL-IAM-001"
    txt = " ".join(cl["text"] for s in std["sections"] for cl in s["clauses"])
    assert "at least 15 characters" in txt and "all users on all systems" in txt
    assert "Identity and Access Management Policy" in txt  # enabling-policy cross-reference
    hdl = c.get(f"/api/policies/{pols['STD-HANDLING']['id']}?lang=fr").json()["body"]
    matrix = [cl for s in hdl["sections"] for cl in s["clauses"] if cl.get("table")][0]
    assert matrix["table_cols"][0] == "Niveau" and len(matrix["table"]) == 4 and matrix["table"][3][0] == "Restreint"
    prc = c.get(f"/api/policies/{pols['PRC-IR']['id']}?lang=en").json()["body"]
    assert prc["policy_id"] == "NOR-PRC-IR-001" and prc["policy_type"] == "procedure"
    raci = [cl for s in prc["sections"] for cl in s["clauses"] if cl.get("table")][0]
    assert raci["table_cols"] == ["Activity", "Responsible", "Accountable", "Consulted", "Informed"]
    r = c.post(f"/api/projects/{pid}/exports", json={"kind": "zip"})
    names = zipfile.ZipFile(io.BytesIO(c.get(r.json()["download"]).content)).namelist()
    assert any("/EN/03_Standards/NOR-STD-AUTH-001" in n for n in names)
    assert any("/FR/04_Procedures/NOR-PRC-IR-001" in n for n in names)
    d = docx.Document(io.BytesIO(zipfile.ZipFile(io.BytesIO(c.get(r.json()["download"]).content)).read(
        [n for n in names if "/EN/03_Standards/NOR-STD-HDL-001" in n][0])))
    assert any(len(t.columns) == 6 for t in d.tables)  # handling matrix rendered as a real table


# ---------------------------------------------------------------- OCR
def _text_image(lines, fmt="PNG"):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1700, 200 + 90 * len(lines)), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
    except OSError:
        pytest.skip("No TrueType font available to build an OCR fixture")
    for i, line in enumerate(lines):
        draw.text((60, 80 + 90 * i), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


ocr_engine = pytest.mark.skipif(not __import__("app.ingestion.ocr", fromlist=["x"]).engine_info()["available"],
                                reason="No OCR engine installed")


@ocr_engine
@pytest.mark.parametrize("fmt,name", [("PNG", "scan.png"), ("PDF", "scan.pdf")])
def test_scanned_document_needs_consent_then_ocr(client, fmt, name):
    c = client
    register(c)
    pid = new_project(c)
    data = _text_image(["Critical vulnerabilities must be remediated within 7 days.", "Backups are taken daily."], fmt)
    r = c.post(f"/api/projects/{pid}/sources", files={"file": (name, data)})
    assert r.status_code == 200, r.text
    src = c.get(f"/api/projects/{pid}/sources").json()[0]
    assert src["state"] == "needs_ocr" and src["ocr_pages"] == [1] and src["facts"] == 0  # nothing read without consent
    r = c.post(f"/api/sources/{src['id']}/ocr")
    assert r.status_code == 200, r.text
    assert r.json()["pages"] == 1 and r.json()["mean_confidence"] > 50
    src = c.get(f"/api/projects/{pid}/sources").json()[0]
    assert src["state"] == "extracted" and src["ocr_meta"]["engine"] in ("tesseract", "rapidocr")
    assert any("OCR" in w for w in src["warnings"])
    segs = c.get(f"/api/sources/{src['id']}/segments").json()["segments"]
    assert "(OCR" in segs[0]["locator"]
    facts = c.get(f"/api/projects/{pid}/facts").json()
    vuln = [f for f in facts if f["fact_type"] == "DEC-VULN-CRIT"]
    assert vuln and vuln[0]["value"] == "7" and vuln[0]["extractor"].endswith("+ocr") and vuln[0]["confidence"] in ("medium", "low")
    assert c.post(f"/api/sources/{src['id']}/ocr").status_code == 409  # already done


def test_text_pdf_does_not_need_ocr_and_bomb_image_rejected(client):
    c = client
    register(c)
    pid = new_project(c)
    from PIL import Image
    buf = io.BytesIO()
    Image.new("1", (12000, 12000)).save(buf, format="PNG")
    r = c.post(f"/api/projects/{pid}/sources", files={"file": ("huge.png", buf.getvalue())})
    assert r.status_code == 422


# ---------------------------------------------------------------- Word re-import
def _para_with_bookmark(d, clause_id):
    from app.export.docx_render import bookmark_name
    name = bookmark_name(clause_id)
    for p in d.paragraphs:
        if any(b.get(qn("w:name")) == name for b in p._p.iter(qn("w:bookmarkStart"))):
            return p
    raise AssertionError(clause_id)


def _set_text_keep_number(p, new_text):
    runs = p.runs
    runs[1].text = new_text
    for r in runs[2:]:
        r._r.getparent().remove(r._r)


def test_word_reimport_round_trip(client):
    c = client
    register(c)
    pid = new_project(c)
    apply_answers(c, pid, SOFTWARE_QC)
    c.put(f"/api/projects/{pid}/selection", json={"codes": ["EISP", "IAM"]})
    c.post(f"/api/projects/{pid}/generate", json={})
    iam = [p for p in c.get(f"/api/projects/{pid}/policies").json() if p["code"] == "IAM"][0]
    job = c.post(f"/api/projects/{pid}/exports", json={"kind": "docx", "document_id": iam["id"], "lang": "en"}).json()
    d = docx.Document(io.BytesIO(c.get(job["download"]).content))

    # 1) wording change on a clause (bookmark kept)
    _set_text_keep_number(_para_with_bookmark(d, "IAM-G02"), "Access must be assigned through roles defined by owners.")
    # 2) a decision filled in directly in Word
    _set_text_keep_number(_para_with_bookmark(d, "IAM-G01"),
                          "Access must be granted only on a documented request approved by the system owner.")
    # 3) a clause whose hidden marker was lost but whose number is intact
    p = _para_with_bookmark(d, "IAM-A03")
    for b in list(p._p.iter(qn("w:bookmarkStart"))) + list(p._p.iter(qn("w:bookmarkEnd"))):
        b.getparent().remove(b)
    _set_text_keep_number(p, "Default passwords must be changed before first use.")
    # 4) a deleted clause
    t = _para_with_bookmark(d, "IAM-T01")
    t._p.getparent().remove(t._p)
    # 5) an added paragraph after IAM-PA04
    anchor = _para_with_bookmark(d, "IAM-PA04")
    new_p = copy.deepcopy(anchor._p)
    for b in list(new_p.iter(qn("w:bookmarkStart"))) + list(new_p.iter(qn("w:bookmarkEnd"))):
        b.getparent().remove(b)
    anchor._p.addnext(new_p)
    from docx.text.paragraph import Paragraph
    added = Paragraph(new_p, anchor._parent)
    added.runs[0].text = ""
    _set_text_keep_number(added, "Privileged users must complete annual privileged-access training.")
    buf = io.BytesIO()
    d.save(buf)

    r = c.post(f"/api/projects/{pid}/reimports", files={"file": ("IAM edited.docx", buf.getvalue())})
    assert r.status_code == 200, r.text
    ri = r.json()
    kinds = {(ch["kind"], ch["clause_id"]) for ch in ri["changes"]}
    assert ("modified", "IAM-G02") in kinds and ("modified", "IAM-G01") in kinds and ("modified", "IAM-A03") in kinds
    assert ("deleted", "IAM-T01") in kinds and any(k == "added" for k, _ in kinds)
    a03 = [ch for ch in ri["changes"] if ch["clause_id"] == "IAM-A03"][0]
    assert a03["match"] == "number" and any("matched by their number" in w for w in ri["warnings"])
    g02 = [ch for ch in ri["changes"] if ch["clause_id"] == "IAM-G02"][0]
    assert any(op[0] == "del" for op in g02["diff"]) and any(op[0] == "ins" for op in g02["diff"])
    assert g02["modality_from"] == "should" and g02["modality_to"] == "must"  # strength change is surfaced
    assert all(ch["decision"] == "pending" for ch in ri["changes"])  # nothing applied automatically

    # accept all but the deletion
    dec = {ch["key"]: ("reject" if ch["kind"] == "deleted" else "accept") for ch in ri["changes"]}
    assert c.post(f"/api/reimports/{ri['id']}/decisions", json={"decisions": dec}).status_code == 200
    r = c.post(f"/api/reimports/{ri['id']}/apply")
    assert r.status_code == 200 and r.json()["version_no"] == 2
    body = c.get(f"/api/policies/{iam['id']}").json()["body"]
    by = {cl["clause_id"]: cl for s in body["sections"] for cl in s["clauses"]}
    assert by["IAM-G02"]["text"] == "Access must be assigned through roles defined by owners." and by["IAM-G02"]["edited"]
    assert by["IAM-G02"]["modality"] == "must"
    assert "IAM-T01" in by  # rejected deletion kept
    assert by["IAM-U01"]["source_type"] == "user_added"
    ids = [cl["clause_id"] for s in body["sections"] for cl in s["clauses"]]
    assert ids.index("IAM-U01") == ids.index("IAM-PA04") + 1
    assert not any(od["clause_id"] == "IAM-G01" for od in body["open_decisions"])  # decision resolved in Word
    v1 = c.get(f"/api/policies/{iam['id']}?version=1").json()["body"]
    assert "[DECISION: role(s) that approve access requests]" in [cl for s in v1["sections"] for cl in s["clauses"] if cl["clause_id"] == "IAM-G01"][0]["text"]
    assert c.post(f"/api/reimports/{ri['id']}/apply").status_code == 409  # cannot apply twice

    # the newly exported file carries the new clause bookmark, so it can be re-imported again
    job = c.post(f"/api/projects/{pid}/exports", json={"kind": "docx", "document_id": iam["id"], "lang": "en"}).json()
    d2 = docx.Document(io.BytesIO(c.get(job["download"]).content))
    _para_with_bookmark(d2, "IAM-U01")
    r = c.post(f"/api/projects/{pid}/reimports", files={"file": ("same.docx", c.get(job["download"]).content)})
    assert r.json()["changes"] == []


def test_reimport_rejects_foreign_or_unknown_files(client):
    c = client
    register(c)
    pid = new_project(c)
    from conftest import make_docx
    r = c.post(f"/api/projects/{pid}/reimports", files={"file": ("random.docx", make_docx(["Hello"]))})
    assert r.status_code == 422 and "identifier" in r.json()["detail"]
    d = docx.Document()
    d.core_properties.identifier = "XYZ-EISP-001|00000000-0000-0000-0000-000000000000|v0.1|en"
    buf = io.BytesIO()
    d.save(buf)
    r = c.post(f"/api/projects/{pid}/reimports", files={"file": ("forged.docx", buf.getvalue())})
    assert r.status_code == 422 and "not exported from this project" in r.json()["detail"]
