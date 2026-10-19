"""CyberRiskGuardian Security Policy Writer — the policy-writing engine of CyberRiskGuardian.

The Writer interviews the organization, reads its documents, takes legal applicability from the
CyberRiskGuardian Ontology (CRGO), and drafts the enterprise policy, topic policies, standards and
procedures in English and French. ISP management then manages them: review, approval frozen with a
SHA-256 hash, publication, acknowledgements, exceptions. The Writer writes; CyberRiskGuardian manages.

Standard library only: the CyberRiskGuardian helper (serve.py) imports this package and serves it on
127.0.0.1 through /api/writer/<operation>.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
NAME = "CyberRiskGuardian Security Policy Writer"
VERSION = "0.1.0"
CHANNEL = "beta"
LABEL = f"{VERSION} {CHANNEL}"
