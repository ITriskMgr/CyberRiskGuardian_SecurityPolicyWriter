"""Evidence from the organization's documents: segments with locators, injection flags, candidate facts.

Input is text that CyberRiskGuardian already extracted on this computer (Organization → Context documents,
or the OCR of a scanned file). Nothing here sends anything anywhere. Facts are PROPOSALS: each carries the
quote it came from, the document and the locator, and the person confirms or rejects it. Documents that
disagree form a conflict group, and neither value is used until the person decides.

© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import hashlib
import json
import re

from .facts import extract_rule_facts
from .questions import BY_CODE as QBY

SEG_CHARS = 1500
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|prompts?|rules)",
    r"disregard\s+(all\s+|the\s+)?(previous|prior|above|system)\s+(instructions|prompt)",
    r"you\s+are\s+now\s+(a|an|the)\b", r"\bsystem\s+prompt\b", r"reveal\s+(your|the)\s+(instructions|prompt|secrets?|api\s*key)",
    r"\bact\s+as\s+(a|an)\s+(different|new)\b", r"do\s+not\s+follow\s+the\s+user",
    r"ignorez?\s+(toutes\s+)?(les\s+)?instructions\s+(précédentes|antérieures)", r"invite\s+système",
    r"exfiltrat", r"send\s+(all|the)\s+(data|documents|files)\s+to\b",
    # 0.1.1 (NV-008): the notice planted in the campaign's live pass, and the "everything is FACT" instruction
    r"\b(system|important)\s+(notice|message|instruction)s?\s+to\s+the\s+(ai|assistant|model)\b", r"state\s+every\s+value\s+as\s+fact",
]
INJ_RE = re.compile("|".join(INJECTION_PATTERNS), re.I)
# 0.1.1 (NV-009): the same list is ported to js/ai.js (INJ_RE); keep the two in step. Matching runs on a whitespace-
# normalised line: runs of spaces, tabs and non-breaking spaces count as one space.
WS_RE = re.compile(r"[\s\u00a0]+")


def flat(text: str) -> str:
    return WS_RE.sub(" ", text or "").strip()


def looks_injected(text: str) -> bool:
    return bool(INJ_RE.search(flat(text)))


def escape_untrusted(text: str) -> str:
    """A wrapper tag written inside a document must not close (or open) the <untrusted_document> wrapper."""
    return re.sub(r"<(/?)untrusted_document(\b[^>]*)>", r"&lt;\1untrusted_document\2&gt;", text or "", flags=re.I)


def injected_lines(text: str) -> set[int]:
    """1-based numbers of the lines that look like an instruction to an AI — read line by line AND by paragraph (a block
    of consecutive non-empty lines) joined with a space, so an instruction split across two lines ("IMPORTANT SYSTEM
    NOTICE" / "TO THE AI: …") is caught with the whole block it sits in (0.1.1, review L3)."""
    lines = re.split(r"\r?\n", text or "")
    bad: set[int] = set()
    block: list[int] = []

    def close():
        if not block:
            return
        hit = [i for i in block if i in bad]
        if not hit:
            # no line matches on its own: adjacent pairs, then the whole block (an instruction split over several lines)
            for a, b in zip(block, block[1:]):
                if looks_injected(flat(lines[a - 1]) + " " + flat(lines[b - 1])):
                    bad.update((a, b))
            if not any(i in bad for i in block) and looks_injected(" ".join(flat(lines[i - 1]) for i in block)):
                bad.update(block)
        block.clear()

    for i, line in enumerate(lines, 1):
        t = flat(line)
        if not t:
            close()
            continue
        if looks_injected(t):
            bad.add(i)
        block.append(i)
    close()
    return bad


def ai_text(docs: list[dict], max_chars: int = 20000) -> dict:
    """The text of the documents that may be sent to a model: every paragraph that looks like an instruction to an
    AI is left out, decided here and now on the text given (not on the flags of an earlier run), and wrapper tags
    are escaped. Returns {text, flagged, docs} — flagged in the same shape as extract()."""
    parts, flagged, used = [], [], []
    for d in docs or []:
        name = d.get("name") or d.get("id") or "document"
        kept = []
        text = d.get("text") or ""
        bad = injected_lines(text)
        for i, line in enumerate(re.split(r"\r?\n", text), 1):
            t = flat(line)
            if not t:
                continue
            if i in bad:
                flagged.append({"doc": d.get("id"), "name": name, "locator": f"{name}, ¶ {i}", "excerpt": t[:240]})
                continue
            kept.append(t)
        body = escape_untrusted("\n".join(kept))
        if body.strip():
            parts.append(f"### {name}\n{body[:max_chars]}")
            used.append({"id": d.get("id"), "name": name, "chars": min(len(body), max_chars), "truncated": len(body) > max_chars})
    return {"text": "\n\n".join(parts), "flagged": flagged, "docs": used}
PAGE_RE = re.compile(r"^\s*(?:-{2,}|={2,}|\[)?\s*(?:page|p\.)\s*(\d{1,4})\b.*$", re.I)


def segments(text: str, name: str) -> list[dict]:
    """Split a document's text into segments of at most ~1,500 characters with a locator (page when the
    text marks pages, else paragraph range). Paragraphs that look like instructions to an AI are set
    aside: they are listed in "flagged", never read for facts and never sent to a model."""
    paras: list[tuple[str, str, bool]] = []
    page = None
    bad = injected_lines(text or "")   # review L3: by line and by paragraph block
    for n, line in enumerate(re.split(r"\r?\n", text or ""), 1):
        t = flat(line)
        if not t:
            continue
        m = PAGE_RE.match(t) if len(t) < 40 else None
        if m:
            page = m.group(1)
            continue
        paras.append((page or "", t, n in bad))
    out, buf, start, size = [], [], 1, 0

    def flush(end):
        if not buf:
            return
        pg = sorted({p for p, _, _ in buf if p}, key=int)
        where = (f"p. {pg[0]}" + (f"–{pg[-1]}" if len(pg) > 1 else "") + ", ") if pg else ""
        loc = f"{name}, {where}¶ {start}" + (f"–{end}" if end > start else "")
        out.append({"locator": loc, "text": "\n".join(t for _, t, bad in buf if not bad), "name": name,
                    "paras": [(pg_, start + k, t) for k, (pg_, t, bad) in enumerate(buf) if not bad],
                    "injection": any(bad for _, _, bad in buf), "flagged": [t for _, t, bad in buf if bad]})

    for i, (pg, t, bad) in enumerate(paras, 1):
        if size + len(t) > SEG_CHARS and buf:
            flush(i - 1)
            buf, size, start = [], 0, i
        buf.append((pg, t, bad))
        size += len(t)
    flush(len(paras))
    return out


def _locate(seg: dict, quote: str) -> str:
    probe = (quote or "")[:60]
    for pg, n, t in seg.get("paras", []):
        if probe and probe in t:
            return f"{seg['name']}, " + (f"p. {pg}, " if pg else "") + f"¶ {n}"
    return seg["locator"]


def _label(code: str, value, lang: str) -> str:
    q = QBY.get(code)
    if not q:
        from .catalogue import DECISIONS
        q = next((d for d in DECISIONS if d["code"] == code), None)
    if not q:
        return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    opts = {o["value"]: o[lang] for o in q.get("options", [])}
    if isinstance(value, list):
        return ", ".join(opts.get(v, str(v)) for v in value)
    return opts.get(value, str(value))


def _question(code: str, lang: str) -> str:
    q = QBY.get(code)
    if not q:
        from .catalogue import DECISIONS
        q = next((d for d in DECISIONS if d["code"] == code), None)
    return q["label"][lang] if q else code


# ---------------------------------------------------------------- the CRG organization profile as evidence
_SECTOR = [(r"health|santé|clinic|clinique|hospital|hôpital", "healthcare"), (r"bank|financ|insur|assur|credit|crédit", "financial"),
           (r"software|saas|logiciel", "software_saas"), (r"it services|managed service|services ti|infogérance", "it_services"),
           (r"universit|college|cégep|school|école|education|enseignement|research", "education_research"),
           (r"manufactur|fabrication|usine|plant|industrial|industriel", "manufacturing_ot"), (r"retail|commerce|e-?commerce|détail", "retail_ecommerce"),
           (r"government|gouvernement|municipal|ministry|ministère|public body|organisme public", "public_sector"),
           (r"law firm|cabinet|accounting|comptab|consult|professional services|services professionnels", "professional_services"),
           (r"energy|énergie|utility|utilities|électricité|water|eau", "energy_utilities"), (r"non-?profit|à but non lucratif|obnl|charity|organisme de bienfaisance", "nonprofit")]
_JUR = [(r"qu[ée]bec|montr[ée]al|gatineau|saguenay|sherbrooke|laval", "QC"), (r"ontario|toronto|ottawa", "ON"), (r"british columbia|colombie-britannique|vancouver", "BC"),
        (r"alberta|calgary|edmonton", "AB"), (r"canada", "CA_OTHER"), (r"united states|états-unis|\busa\b|\bu\.s\.", "US"),
        (r"europe|\beu\b|france|germany|allemagne|belgi|ireland|irlande|spain|espagne|italy|italie", "EU"), (r"united kingdom|royaume-uni|\buk\b|london|londres", "UK")]
_TECH = [(r"microsoft 365|office 365|\bm365\b|\bo365\b|exchange online|sharepoint|teams", "m365"), (r"google workspace|g suite|gmail", "google_ws"),
         (r"\baws\b|amazon web services", "aws"), (r"azure", "azure"), (r"\bgcp\b|google cloud", "gcp"),
         (r"on-?prem|sur site|serveurs? locaux|data ?cent(er|re)|salle des serveurs|server room", "onprem"), (r"hosted|hébergé|colocation|hosting", "hosted"),
         (r"saas|cloud|infonuag|nuage", "saas_other")]
_DATA = [(r"health|santé|patient|medical|médical|clinical|clinique", "health"), (r"payment card|carte de paiement|credit card|carte de crédit|pci", "payment_card"),
         (r"financial|financi|bank|bancaire", "financial"), (r"employee|employé|staff|personnel|hr\b|rh\b", "employee"),
         (r"client|customer|patient|personal information|renseignements personnels|données personnelles", "customer_pi"),
         (r"student|étudiant|élève", "students"), (r"research|recherche", "research"), (r"intellectual property|propriété intellectuelle|trade secret|secret commercial", "ip")]
_SIZE = [(r"\b(\d[\d ,.]*)\s*(employees|employés|staff|people|personnes|workers|travailleurs)", None)]
_BANDS = [(10, "1-10"), (50, "11-50"), (250, "51-250"), (1000, "251-1000"), (5000, "1001-5000"), (10**9, "5000+")]


def profile_facts(org: dict, crown: list | None = None) -> list[dict]:
    """Candidate answers implied by the CyberRiskGuardian organization profile. Each keeps the profile field
    it came from as its quote; matching is by keyword, so each one is a proposal, never an answer."""
    org = org or {}
    out: list[dict] = []

    def add(code, label, value, field, conf="medium"):
        quote = str(org.get(field) if not isinstance(org.get(field), list) else "; ".join(org.get(field)))[:300]
        out.append({"fact_type": code, "label": label, "value": value, "quote": quote, "confidence": conf,
                    "source": "crg-profile", "locator": f"Organization profile → {field}"})

    if str(org.get("name", "")).strip():
        add("ORG-01", "Organization name", str(org["name"]).strip(), "name", "high")
    sec = " ".join(str(org.get(k, "")) for k in ("sector",)).lower()
    for rx, v in _SECTOR:
        if sec and re.search(rx, sec):
            add("ORG-02", "Industry / sector", v, "sector")
            break
    for f in ("region",):
        txt = str(org.get(f, "")).lower()
        found = [v for rx, v in _JUR if re.search(rx, txt)]
        if "CA_OTHER" in found and any(x in found for x in ("QC", "ON", "BC", "AB")):
            found.remove("CA_OTHER")
        if found:
            add("ORG-05", "Where the organization operates", found, f)
    szf = "employees" if str(org.get("employees", "")).strip() else "size"
    sz = str(org.get(szf, "")).lower()
    m = re.search(r"(\d[\d ,.]*)", sz)
    if m:
        try:
            n = int(re.sub(r"[ ,.]", "", m.group(1)))
            add("ORG-04", "Number of employees and contractors", next(b for lim, b in _BANDS if n <= lim), szf)
        except ValueError:
            pass
    tech = " ".join(str(org.get(k, "")) for k in ("systems", "cloud", "infrastructure")).lower()
    found = [v for rx, v in _TECH if re.search(rx, tech)]
    if found:
        add("TECH-01", "Technology environments", sorted(set(found), key=found.index), "systems" if org.get("systems") else "cloud")
    data = " ".join(str(org.get(k, "")) for k in ("sensitive",)).lower()
    found = [v for rx, v in _DATA if re.search(rx, data)]
    if found:
        add("DATA-01", "Kinds of information held", sorted(set(found), key=found.index), "sensitive")
    if str(org.get("mission", "")).strip():
        add("ORG-03", "Main activities / services", str(org.get("services") or org.get("mission")).strip()[:600], "services" if org.get("services") else "mission", "high")
    cj = [(c.get("name") or c.get("asset") or "") if isinstance(c, dict) else (str(c[1]) if isinstance(c, (list, tuple)) and len(c) > 1 else "")
          for c in (crown or [])]
    cj = [c for c in cj if c]
    if cj:
        out.append({"fact_type": "ORG-14", "label": "Critical services and assets", "value": "; ".join(cj[:12]),
                    "quote": "; ".join(cj[:12])[:300], "confidence": "high", "source": "crg-crown", "locator": "Organization → Crown jewels"})
    return out


def extract(docs: list[dict], org: dict | None = None, crown: list | None = None, lang: str = "en") -> dict:
    """docs: [{id, name, text, date?, ocr?}] → facts with quotes, conflict groups and flagged segments."""
    facts, flagged = [], []
    for d in docs or []:
        segs = segments(d.get("text") or "", d.get("name") or d.get("id") or "document")
        for s in segs:
            for bad in s["flagged"]:                      # never read for facts, never sent to an AI
                flagged.append({"doc": d.get("id"), "name": d.get("name"), "locator": s["locator"], "excerpt": bad[:240]})
            for f in extract_rule_facts(s["text"]):
                if d.get("ocr"):
                    f["confidence"] = "low" if f["confidence"] != "high" else "medium"
                facts.append({**f, "doc": d.get("id"), "source": "document", "doc_name": d.get("name"), "doc_date": d.get("date", ""),
                              "locator": _locate(s, f["quote"]), "ocr": bool(d.get("ocr")), "extractor": "rules"})
    facts += [{**f, "doc": None, "doc_name": f["locator"], "doc_date": "", "ocr": False, "extractor": "profile"} for f in profile_facts(org or {}, crown)]
    # ids, labels and conflicts
    seen, out = set(), []
    for f in facts:
        k = (f["fact_type"], json.dumps(f["value"], ensure_ascii=False, sort_keys=True), f["quote"], f.get("doc"))
        if k in seen:
            continue
        seen.add(k)
        f["id"] = "F-" + hashlib.sha1(json.dumps(k, ensure_ascii=False).encode()).hexdigest()[:10]
        f["question"] = _question(f["fact_type"], lang)
        f["value_label"] = _label(f["fact_type"], f["value"], lang)
        out.append(f)
    by_type: dict[str, set] = {}
    for f in out:
        if isinstance(f["value"], list):
            continue                                       # multi-select facts accumulate rather than conflict
        by_type.setdefault(f["fact_type"], set()).add(json.dumps(f["value"], ensure_ascii=False))
    for f in out:
        if not isinstance(f["value"], list) and len(by_type.get(f["fact_type"], ())) > 1:
            f["conflict_group"] = "CONFLICT-" + f["fact_type"]
    return {"facts": out, "flagged": flagged}
