"""Questionnaire branching, recommendations, applicability candidates, composer guarantees, conflicts (AT-02, AT-03, AT-05, AT-14)."""
import json

import httpx
import pytest

from conftest import FOOD_OT, HEALTH, ORGS, SOFTWARE_QC, UNIVERSITY, apply_answers, make_docx, new_project, register
from app.catalogue.catalogue import CATALOGUE, recommend
from app.catalogue.rulesets import candidates
from app.drafting.composer import Context, compose, PH_RE
from app.drafting.library import LIBRARY
from app.questionnaire.engine import Profile, visible_questions


def prof(ans, lang="en"):
    return Profile({k: {"value": v, "status": "answered"} for k, v in ans.items()}, lang)


def test_express_interview_is_short_and_standard_branches():
    p = prof(SOFTWARE_QC)
    assert 15 <= len(visible_questions(p, "express")) <= 25
    std = {q["code"] for q in visible_questions(p, "standard")}
    assert "IND-SAAS-01" in std and "IND-HC-01" not in std and "IND-OT-01" not in std
    assert "IND-HC-01" in {q["code"] for q in visible_questions(prof(HEALTH), "standard")}
    assert "IND-OT-01" in {q["code"] for q in visible_questions(prof(FOOD_OT), "standard")}


@pytest.mark.parametrize("name", list(ORGS))
def test_recommendations_vary_by_context(name):
    rec = {r["code"] for r in recommend(prof(ORGS[name])) if r["recommended"]}
    assert "EISP" in rec and "IAM" in rec and "IR" in rec
    assert ("OT" in rec) == (name == "food_ot")
    assert ("SDLC" in rec) == (name == "software_qc")
    assert "REMOTE" in rec if ORGS[name]["TECH-02B"] != "no" or ORGS[name]["TECH-02"] != "onsite" else True


def test_candidates_never_applicable_without_decision():  # AT-02, AT-03, AT-14
    qc = candidates(prof(SOFTWARE_QC), "en", {})
    codes = {c["code"]: c for c in qc}
    assert "QC-P39.1" in codes and codes["QC-P39.1"]["status"] == "candidate"
    assert codes["QC-P39.1"]["verification"].startswith("Not verified")
    assert "EU-GDPR" not in codes
    hc = {c["code"] for c in candidates(prof(HEALTH), "en", {})}
    assert {"ON-PHIPA", "US-HIPAA", "QC-A2.1"} <= hc
    uni = {c["code"] for c in candidates(prof(UNIVERSITY), "en", {})}
    assert {"QC-A2.1", "QC-P39.1"} <= uni  # public-body status is exactly what the reviewer must confirm
    assert all(c["status"] != "applies" for c in candidates(prof(HEALTH), "en", {}))


def test_applicability_decision_requires_named_reviewer(client):
    register(client)
    pid = new_project(client)
    apply_answers(client, pid, SOFTWARE_QC)
    r = client.post(f"/api/projects/{pid}/applicability/QC-P39.1", json={"status": "applies"})
    assert r.status_code == 422
    r = client.post(f"/api/projects/{pid}/applicability/QC-P39.1",
                    json={"status": "applies", "reviewer_name": "J. Tremblay, counsel", "rationale": "Enterprise in Quebec holding PI"})
    assert r.status_code == 200
    item = [i for i in client.get(f"/api/projects/{pid}/applicability").json()["items"] if i["code"] == "QC-P39.1"][0]
    assert item["status"] == "applies" and item["decision"]["reviewer_name"].startswith("J. Tremblay")


@pytest.mark.parametrize("lang", ["en", "fr"])
@pytest.mark.parametrize("name", list(ORGS))
def test_every_policy_composes_cleanly(name, lang):
    p = prof(ORGS[name], lang)
    for code in LIBRARY:
        body = compose(code, Context(p, lang, list(LIBRARY), {}, {"QC-P39.1"}))
        ids = [c["clause_id"] for s in body["sections"] for c in s["clauses"]]
        assert len(ids) == len(set(ids)), code
        for s in body["sections"]:
            for c in s["clauses"]:
                assert "{" not in c["text"] and "}" not in c["text"], (code, c["clause_id"], c["text"])
                if c["source_type"] == "open_decision":
                    assert PH_RE.search(c["text"]), (code, c["clause_id"])
        # obligation-gated clauses are withheld while only a candidate
        assert not any(c["source_type"] == "confirmed_obligation" for s in body["sections"] for c in s["clauses"]
                       if c["clause_id"] != "EISP-LG02")
        if lang == "fr":
            txt = " ".join(c["text"] for s in body["sections"] for c in s["clauses"])
            assert " à le " not in txt and " de le " not in txt


def test_obligation_clause_appears_only_when_confirmed():
    p = prof(SOFTWARE_QC)
    before = compose("PRIV", Context(p, "en", ["PRIV"], {}, {"QC-P39.1"}))
    after = compose("PRIV", Context(p, "en", ["PRIV"], {"QC-P39.1": {"status": "applies"}}, {"QC-P39.1"}))
    t = lambda b: " ".join(c["text"] for s in b["sections"] for c in s["clauses"])  # noqa: E731
    assert "register of confidentiality incidents" not in t(before)
    assert any("withheld" in d["text"] for d in before["open_decisions"])
    assert "register of confidentiality incidents" in t(after)


def test_no_invented_roles_or_approver():  # AT-08
    ans = dict(SOFTWARE_QC)
    ans["ORG-13"] = ["hr"]
    body = compose("EISP", Context(prof(ans), "en", ["EISP"], {}, set()))
    txt = " ".join(c["text"] for s in body["sections"] for c in s["clauses"])
    assert "[ROLE: person accountable for information security — CONFIRM]" in txt
    assert "[APPROVER: authority that approves the enterprise policy]" in txt
    assert "Chief Information Security Officer" not in txt


def test_contradictory_documents_surface_conflict(client):  # AT-05
    c = client
    register(c)
    pid = new_project(c)
    apply_answers(c, pid, SOFTWARE_QC)
    c.post(f"/api/projects/{pid}/sources", files={"file": ("old.docx", make_docx(
        ["Multi-factor authentication is required for privileged accounts only.", "Passwords must be changed every 90 days."]))})
    c.post(f"/api/projects/{pid}/sources", files={"file": ("new.docx", make_docx(
        ["Multi-factor authentication is required for all users.", "There is no periodic forced password change."]))})
    facts = c.get(f"/api/projects/{pid}/facts").json()
    mfa = [f for f in facts if f["fact_type"] == "DEC-IAM-MFA-SCOPE"]
    pwd = [f for f in facts if f["fact_type"] == "PARAM-PWD-ROTATION"]
    assert len(mfa) == 2 and all(f["conflict_group"] for f in mfa)
    assert len(pwd) == 2 and all(f["conflict_group"] for f in pwd)
    interview = c.get(f"/api/projects/{pid}/interview").json()
    assert not any(q["code"] == "DEC-IAM-MFA-SCOPE" and q["answer"] for q in interview["questions"])  # nothing chosen silently
    c.put(f"/api/projects/{pid}/selection", json={"codes": ["IAM"]})
    c.post(f"/api/projects/{pid}/generate", json={})
    assert any(i["kind"] == "evidence_conflict" for i in c.get(f"/api/projects/{pid}/issues").json())
    chosen = [f for f in mfa if f["value"] == "all"][0]
    c.post(f"/api/facts/{chosen['id']}/decision", json={"action": "confirm"})
    after = {f["id"]: f for f in c.get(f"/api/projects/{pid}/facts").json()}
    other = [f for f in mfa if f["value"] != "all"][0]
    assert after[chosen["id"]]["state"] == "confirmed" and after[other["id"]]["state"] == "rejected"


def test_pdf_and_xlsx_extraction():
    from app.ingestion.extract import extract
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Asset", "Owner", "Classification"])
    ws.append(["ERP", "CFO", "Confidential"])
    buf = io.BytesIO()
    wb.save(buf)
    ex = extract(buf.getvalue(), "inventory.xlsx")
    assert ex.kind == "xlsx" and "ERP | CFO | Confidential" in ex.segments[0].text and ex.segments[0].locator.startswith("Sheet")


def test_pdf_extraction_with_page_locator(tmp_path):
    import shutil
    import subprocess
    if not shutil.which("soffice"):
        pytest.skip("LibreOffice not installed")
    from app.ingestion.extract import extract
    src = tmp_path / "policy.docx"
    src.write_bytes(make_docx(["Critical vulnerabilities must be remediated within 7 days."]))
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(src)], check=True,
                   capture_output=True, timeout=120)
    ex = extract((tmp_path / "policy.pdf").read_bytes(), "policy.pdf")
    assert ex.kind == "pdf" and ex.segments[0].locator.startswith("p. 1")
    from app.ingestion.facts import extract_rule_facts
    assert any(f["fact_type"] == "DEC-VULN-CRIT" and f["value"] == "7" for f in extract_rule_facts(ex.segments[0].text))


def test_anthropic_provider_wire_format(monkeypatch):
    from app.drafting.ai import AnthropicProvider
    seen = {}

    def handler(request):
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"content": [{"type": "text", "text": '{"clauses": []}'}]})

    p = AnthropicProvider("k-123", "claude-sonnet-5-5", transport=httpx.MockTransport(handler))
    assert p.complete_json("tailor_section", "sys", "user") == {"clauses": []}
    assert seen["headers"]["x-api-key"] == "k-123" and seen["body"]["model"] == "claude-sonnet-5-5"
    assert seen["body"]["system"] == "sys"


def test_validate_tailored_rules():
    from app.drafting.ai import validate_tailored
    o = "Access must be reviewed [DECISION: access review frequency]."
    assert validate_tailored(o, "Access must be reviewed [DECISION: access review frequency] by owners.", "", "en") is None
    assert validate_tailored(o, "Access must be reviewed quarterly.", "", "en") == "placeholders changed"
    assert "numbers" in validate_tailored("Backups must be tested.", "Backups must be tested every 30 days.", "", "en")
    assert validate_tailored("Users must lock screens.", "Users should lock screens.", "", "en") == "normative strength changed"
