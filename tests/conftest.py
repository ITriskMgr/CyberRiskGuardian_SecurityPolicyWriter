import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------- synthetic organizations (fictional)
SOFTWARE_QC = {  # (A) 35-person Montreal software firm using AWS / Microsoft 365
    "ORG-01": "Northstar Digital Services Inc.", "ORG-01B": "Northstar", "ORG-02": "software_saas",
    "ORG-03": "Northstar builds and operates a B2B scheduling SaaS platform for clinics and retailers.",
    "ORG-04": "11-50", "ORG-05": ["QC", "ON"], "ORG-06": "private", "ORG-08": "scratch",
    "ORG-09": ["governance", "client_assurance"], "ORG-12": "developing", "ORG-13": ["it_manager"],
    "ORG-14": "The scheduling platform and its customer database", "DATA-01": ["employee", "customer_pi", "client_confidential"],
    "TECH-01": ["m365", "aws"], "TECH-02": "hybrid", "TECH-02B": "no", "ORG-15": "recommended",
}
FOOD_OT = {  # (B) 600-person Quebec food manufacturer with plants and outsourced IT
    "ORG-01": "Laiterie Boréale ltée", "ORG-02": "manufacturing_ot", "ORG-03": "Dairy processing plants supplying grocery chains.",
    "ORG-04": "251-1000", "ORG-05": ["QC"], "ORG-06": "private", "ORG-08": "some", "ORG-09": ["governance", "incidents"],
    "ORG-12": "informal", "ORG-13": ["msp", "hr"], "ORG-14": "Production lines, cold-chain monitoring and ERP",
    "DATA-01": ["employee", "ot_data", "financial"], "TECH-01": ["m365", "onprem"], "TECH-02": "onsite", "TECH-02B": "limited",
    "ORG-15": "recommended", "TECH-03": ["ot", "iot"],
}
HEALTH = {  # (C) 2,000-person multi-jurisdiction healthcare services network
    "ORG-01": "Meridian Care Network", "ORG-02": "healthcare", "ORG-03": "Outpatient clinics and home-care services.",
    "ORG-04": "1001-5000", "ORG-05": ["QC", "ON", "US"], "ORG-06": "healthcare", "ORG-08": "update",
    "ORG-09": ["governance", "privacy", "audit"], "ORG-12": "documented",
    "ORG-13": ["ciso", "security_team", "privacy_officer", "risk_committee", "internal_audit", "legal", "hr"],
    "ORG-13B": "Chief Information Security Officer", "ORG-14": "Electronic health records and scheduling",
    "DATA-01": ["employee", "customer_pi", "health", "financial"], "TECH-01": ["azure", "m365", "onprem"],
    "TECH-02": "hybrid", "TECH-02B": "limited", "ORG-15": "recommended",
}
UNIVERSITY = {  # (D) university with research and student records
    "ORG-01": "Université du Littoral (fictive)", "ORG-02": "education_research", "ORG-03": "Teaching and research university.",
    "ORG-04": "1001-5000", "ORG-05": ["QC"], "ORG-06": "education", "ORG-08": "some", "ORG-09": ["governance", "privacy"],
    "ORG-12": "developing", "ORG-13": ["ciso", "privacy_officer", "legal"], "ORG-14": "Student information system and research data",
    "DATA-01": ["employee", "students", "research", "ip"], "TECH-01": ["m365", "onprem", "azure"], "TECH-02": "hybrid",
    "TECH-02B": "yes", "ORG-15": "recommended",
}
ORGS = {"software_qc": SOFTWARE_QC, "food_ot": FOOD_OT, "health": HEALTH, "university": UNIVERSITY}



def answers(org: dict, **more) -> dict:
    """Interview answers in the shape the CyberRiskGuardian workspace stores them."""
    return {k: {"value": v, "status": "answered"} for k, v in {**org, **more}.items()}


def call(op, body=None):
    from crg_writer import api
    status, out = api.handle(op, body or {})
    assert status == 200, (op, status, out)
    return out


def isp_policy(isp: dict, pid="POL-001"):
    """What CyberRiskGuardian's ISP management stores for a Writer draft (mirror of js/writer.js applyDraft)."""
    cmap, clauses = {}, []
    for i, c in enumerate(isp["clauses"], 1):
        cmap[c["wsec"]] = f"C{i}"
        clauses.append({"id": f"C{i}", "heading": c["heading"], "text": c["text"]})
    st = [{"id": f"{pid}.{i}", "text": s["text"], "modality": s["modality"], "clause": cmap[s["wsec"]], "refs": s["refs"], "guideline": False}
          for i, s in enumerate(isp["statements"], 1)]
    return {"id": pid, "reference": isp["reference"], "title": isp["title"], "type": isp["type"], "version": "0.1", "status": "draft",
            "owner": isp["owner"], "approver": isp["approver"], "purpose": isp["purpose"], "scope": isp["scope"], "clauses": clauses,
            "statements": st, "reviewMonths": isp.get("reviewMonths", 12), "history": []}
