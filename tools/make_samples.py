#!/usr/bin/env python3
"""Build the sample Word drafts in samples/ from the fictional Northstar organization of the tests.
python3 tools/make_samples.py   © 2026 Marc-André Léger. CC BY-NC 4.0"""
import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from conftest import SOFTWARE_QC, answers, call, isp_policy  # noqa: E402

OUT = ROOT / "samples"
OUT.mkdir(exist_ok=True)
sel = ["EISP", "AUP", "IAM", "CLASS", "IR", "STD-AUTH", "PRC-IR"]
res = call("compose", {"answers": answers(SOFTWARE_QC, **{"DOC-02": "complete"}), "selection": sel, "languages": ["en", "fr"],
                       "applicability": {"QC-P39.1": {"status": "applies", "reviewer": "Fictional reviewer"}}})
for i, d in enumerate(res["documents"], 1):
    x = d["isp"]
    pol = isp_policy(x, f"POL-{i:03d}")
    data = call("docx", {"doc": {"lang": d["lang"], "org": "Northstar Digital Services (fictional)", "ws": "sample", "policy": pol,
                                 "writer": {**x["meta"], "code": d["code"]}, "generator": "CyberRiskGuardian Security Policy Writer 0.1.0 (beta) — sample"}})
    (OUT / f"{x['reference']}_{d['lang']}.docx").write_bytes(base64.b64decode(data["data"]))
print(f"{len(res['documents'])} documents written to {OUT}")
