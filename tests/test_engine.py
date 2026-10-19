"""The Writer engine as CyberRiskGuardian's helper serves it: interview, catalogue, legal candidates with CRGO,
decisions, composition into ISP drafts, quality checks. Standard library only."""
import re
import subprocess
import sys

import pytest

from conftest import ORGS, SOFTWARE_QC, HEALTH, answers, call

TOKEN = re.compile(r"\{[A-Za-z_]+(?::[A-Z0-9\-]+)?\}")
CRGO_QC = {"date": "2026-10-19", "source": "local", "release": "v0.10.0",
           "results": {"P-39.1": {"state": "Applicable", "met": ["P39-1-ENT"], "undetermined": []}, "PIPEDA": {"state": "PotentiallyApplicable"}}}


def test_engine_imports_with_the_standard_library_only():
    code = "import sys; sys.path.insert(0, '.'); import crg_writer.api as a; print(a.handle('meta', {})[0])"
    out = subprocess.run([sys.executable, "-S", "-c", code], capture_output=True, text=True, cwd=str(__import__('conftest').ROOT))
    assert out.stdout.strip() == "200", out.stderr


def test_meta_counts():
    m = call("meta")
    assert m["version"] == "0.1.0" and m["documents"] == 28 and m["clauses"] == 606 and m["crgo"] == "v0.10.0"


def test_express_is_short_standard_branches():
    a = answers(SOFTWARE_QC)
    ex = call("interview", {"answers": a, "mode": "express"})
    st = call("interview", {"answers": a, "mode": "standard"})
    assert 15 <= ex["progress"]["total"] <= 25 < st["progress"]["total"]
    fr = call("interview", {"answers": a, "lang": "fr"})
    assert any("organisation" in q["label"].lower() for q in fr["questions"])


def test_answer_validation_is_bilingual():
    assert call("answer", {"code": "ORG-04", "value": "11-50"})["value"] == "11-50"
    from crg_writer import api
    st, out = api.handle("answer", {"code": "ORG-04", "value": "lots"})
    assert st == 400 and out["error_fr"] != out["error"]
    st, _ = api.handle("answer", {"code": "NOPE", "value": "x"})
    assert st == 404
    assert call("answer", {"code": "ORG-04", "status": "unknown"})["status"] == "unknown"


@pytest.mark.parametrize("name", list(ORGS))
def test_catalogue_carries_crgo_control_refs(name):
    items = call("catalogue", {"answers": answers(ORGS[name])})["items"]
    iam = next(x for x in items if x["code"] == "IAM")
    assert "ISO22:5.15" in iam["refs"] and all(not r.startswith("ISO 27002") for x in items for r in x["refs"])


def test_crgo_state_is_evidence_never_a_decision():
    a = answers(SOFTWARE_QC)
    legal = call("legal", {"answers": a, "crgo": CRGO_QC})
    p39 = next(c for c in legal["candidates"] if c["code"] == "QC-P39.1")
    assert p39["crgo"]["instrument"] == "P-39.1" and p39["suggested"] == "applies" and p39["status"] == "candidate"
    pip = next(c for c in legal["candidates"] if c["code"] == "CA-PIPEDA")
    assert pip["suggested"] == "needs_legal_review"
    # the profile proposal: additions only, from the answers
    prop = legal["proposal"]
    assert {"value": "JurQuebec", "because": "ORG-05"} in prop["establishedIn"] and prop["orgTypes"][0]["value"] == "OrgEnterprise"


def test_law_clause_drafted_only_after_a_named_reviewer_confirms():
    a = answers(SOFTWARE_QC, **{"DOC-02": "policies"})
    base = {"answers": a, "selection": ["EISP", "PRIV", "IR"], "codes": ["IR"], "crgo": CRGO_QC}
    before = call("compose", base)["documents"][0]["isp"]
    after = call("compose", {**base, "applicability": {"QC-P39.1": {"status": "applies", "reviewer": "Counsel"}}})["documents"][0]["isp"]
    wids = lambda d: {s["wid"] for s in d["statements"]}  # noqa: E731
    gated = {"IR-NT02"}                                       # Law 25 confidentiality-incident register (obligation="QC-P39.1")
    assert not (gated & wids(before)) and gated <= wids(after)
    sources = {s["wid"]: s["src"] for s in after["statements"]}
    assert all(sources[w] == "confirmed_obligation" for w in gated)


@pytest.mark.parametrize("name", list(ORGS))
@pytest.mark.parametrize("lang", ["en", "fr"])
def test_every_document_composes_into_isp_shape(name, lang):
    a = answers(ORGS[name], **{"DOC-02": "complete"})
    from crg_writer.catalogue import CATALOGUE
    sel = [c["code"] for c in CATALOGUE]
    out = call("compose", {"answers": a, "selection": sel, "languages": [lang]})
    assert len(out["documents"]) == 28
    for d in out["documents"]:
        x = d["isp"]
        assert x["title"] and x["type"] in ("policy", "standard", "procedure")
        assert x["statements"] or x["template"] == "structure", d["code"]
        for s in x["statements"]:
            assert s["modality"] in ("must", "mustnot", "should", "may") and s["wid"].startswith(d["code"] + "-")
            assert not TOKEN.search(s["text"]), (d["code"], s["text"])
            assert all(":" in r or r == "SP800-63B" for r in s["refs"])
        for c in x["clauses"]:
            assert not TOKEN.search(c["text"])
        assert not TOKEN.search(x["purpose"] + x["scope"])
    assert {i["kind"] for i in out["issues"]} <= {"unresolved_placeholders", "legal_review", "missing_parent", "implementation_gap", "structure_template",
                                                  "role_inconsistency", "evidence_conflict", "ambiguous_wording", "broken_cross_reference"}


def test_both_languages_share_statement_ids():
    out = call("compose", {"answers": answers(HEALTH), "selection": ["EISP", "IAM"], "codes": ["IAM"], "languages": ["en", "fr"]})
    en, fr = (next(d["isp"] for d in out["documents"] if d["lang"] == lg) for lg in ("en", "fr"))
    assert [s["wid"] for s in en["statements"]] == [s["wid"] for s in fr["statements"]]
    assert en["title"] != fr["title"] and "doit" in " ".join(s["text"] for s in fr["statements"])


def test_no_invented_owner_or_approver():
    a = answers({k: v for k, v in SOFTWARE_QC.items() if k not in ("ORG-07", "ORG-07B")})
    d = call("compose", {"answers": a, "selection": ["EISP"], "codes": ["EISP"]})["documents"][0]["isp"]
    assert d["approver"] == "" and d["approver_text"].startswith("[")


def test_decisions_carry_suggestions_and_legal_flags():
    g = call("decisions", {"answers": answers(SOFTWARE_QC, **{"TECH-02B": "limited"}), "selection": ["EISP", "AUP", "REMOTE", "PRIV"]})["groups"]
    qs = {q["code"]: q for grp in g for q in grp["questions"]}
    assert qs["DEC-EISP-COMMITTEE"]["suggested"] == "yes" and not qs["DEC-EISP-COMMITTEE"]["legal"]
    assert qs["DEC-AUP-MONITOR"]["legal"] and qs["DEC-AUP-MONITOR"]["suggested"] is None
    assert qs["DEC-REM-BYOD-MDM"]["legal"]


def test_rewording_validation():
    out = call("validate_rewording", {"items": [{"id": "a", "text": "Users must lock their screen within [VALUE: minutes]."},
                                                {"id": "b", "text": "Backups should be tested."}, {"id": "c", "text": "Access must be reviewed."}],
                                      "proposed": {"a": "Users should lock their screen within [VALUE: minutes].", "b": "Backups should be tested every 30 days.",
                                                   "c": "Access rights must be reviewed.", "x": "?"}, "lang": "en"})
    acc = {a["id"] for a in out["accepted"]}
    rej = {r["id"]: r["reason"] for r in out["rejected"]}
    assert acc == {"c"} and "normative" in rej["a"] and "numbers" in rej["b"] and rej["x"] == "unexpected id"
