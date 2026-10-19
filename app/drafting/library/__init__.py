"""Registry of clause libraries by catalogue code. LIBRARY_VERSION changes whenever wording changes."""
from app.drafting.library import core, eisp, more, ops, structure

LIBRARY_VERSION = "2026.10-1"

LIBRARY = {
    "EISP": eisp.SECTIONS,
    "AUP": core.AUP, "IAM": core.IAM, "CLASS": core.CLASS, "IR": core.IR,
    "RISK": ops.RISK, "BACKUP": ops.BACKUP, "TPRM": ops.TPRM, "VULN": ops.VULN, "REMOTE": ops.REMOTE,
    "PRIV": more.PRIV, "AI": more.AI, "SDLC": more.SDLC, "LOG": more.LOG, "OT": more.OT,
    "CRYPTO": structure.CRYPTO, "BCP": structure.BCP, "PHYS": structure.PHYS, "CLOUD": structure.CLOUD,
    "TRAIN": structure.TRAIN,
}
