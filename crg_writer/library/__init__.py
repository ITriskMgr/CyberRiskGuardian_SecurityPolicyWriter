"""Registry of clause libraries by catalogue code. LIBRARY_VERSION changes whenever wording changes."""
import re

from . import core, eisp, levels, more, ops, structure

LIBRARY_VERSION = "2026.10-2"

LIBRARY = {
    "EISP": eisp.SECTIONS,
    "AUP": core.AUP, "IAM": core.IAM, "CLASS": core.CLASS, "IR": core.IR,
    "RISK": ops.RISK, "BACKUP": ops.BACKUP, "TPRM": ops.TPRM, "VULN": ops.VULN, "REMOTE": ops.REMOTE,
    "PRIV": more.PRIV, "AI": more.AI, "SDLC": more.SDLC, "LOG": more.LOG, "OT": more.OT,
    "CRYPTO": structure.CRYPTO, "BCP": structure.BCP, "PHYS": structure.PHYS, "CLOUD": structure.CLOUD,
    "TRAIN": structure.TRAIN,
    "STD-AUTH": levels.STD_AUTH, "STD-HANDLING": levels.STD_HANDLING, "STD-CRYPTO": levels.STD_CRYPTO, "STD-LOG": levels.STD_LOG,
    "PRC-IR": levels.PRC_IR, "PRC-JML": levels.PRC_JML, "PRC-EXC": levels.PRC_EXC, "PRC-RESTORE": levels.PRC_RESTORE,
}

_DEC_RE = re.compile(r"\{p:(DEC-[A-Z0-9\-]+)\}|\[(?:DECISION)")


def referenced_decisions(code: str) -> list[str]:
    """Decision codes a document depends on (variants, inputs and {p:…} tokens, including table cells)."""
    found: list[str] = []

    def add(x):
        if x and x.startswith("DEC-") and x not in found:
            found.append(x)

    def scan(text):
        for m in re.finditer(r"\{p:(DEC-[A-Z0-9\-]+)\}", text or ""):
            add(m.group(1))

    for sec in LIBRARY.get(code, []):
        for cl in sec["clauses"]:
            add(cl.get("by"))
            for i in cl.get("inputs", []):
                add(i)
            if cl.get("text"):
                scan(cl["text"]["en"])
            for v in (cl.get("variants") or {}).values():
                scan(v["en"])
            tbl = cl.get("table")
            if tbl:
                for row in tbl["rows"]["en"]:
                    for cell in row:
                        scan(cell)
    return found
