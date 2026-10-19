# Threat model — Security Policy Writer 0.1.0 (in CyberRiskGuardian Desktop 1.7.0)

Scope: the Writer module of CyberRiskGuardian Desktop on one computer. The browser holds the workspace; the local
helper (127.0.0.1, requests must carry `X-CRG: 1` and a loopback Host) runs the stateless engine.

| Threat | Control | Residual risk / next step |
|---|---|---|
| Prompt injection in documents | Paragraphs matching instruction patterns are set aside, listed, never read for facts and never sent to a model; AI facts are kept only when their quote is found verbatim in the text sent and their type is allowed; the AI preview shows the payload before anything leaves. | Pattern detection is heuristic. |
| AI changing meaning while rewording | Rewording refused when placeholders change, a number appears, the modal verb changes or the length moves outside 0.5–1.8×; the person ticks what to apply; history records it. | Subtle meaning changes remain possible — every statement is reviewed before approval in ISP management. |
| Hallucinated legal requirements | Laws are candidates; CRGO's state is evidence; a named reviewer and a rationale are required; law-gated clauses wait for "applies". | Ruleset dated 2026-10-19; links must be re-verified. |
| Changing an approved policy | The Writer and Word re-import change drafts only; ISP management freezes approved versions with SHA-256 and checks the hash at publication. | — |
| Losing edits on regeneration | Statements, clauses and fields edited after the last generation are kept and counted as "kept as edited"; statements and sections a person removed stay removed. | A wording fix in the library does not reach a statement someone edited — by design. |
| Malicious Word files on re-import | ZIP checks (size, entries, macros refused), XML parsed with the standard library, only the policy's own identifier accepted, changes are proposals. | ElementTree is not hardened against every XML attack; files come from the person's own export. |
| Hostile images and PDFs (OCR) | 60 MB limit, 100 pages, type sniffed, recognition by local tools in a temporary folder deleted afterwards; OCR facts get lower confidence. | Tesseract and Poppler run with the user's rights. |
| Exposure of documents | Text never leaves the computer except through an AI request the person previews and sends under the installation's routing policy (features `writer_facts`, `writer_tailor`). | — |
| Misleading compliance | Word and ISP drafts say DRAFT; mappings are labelled as topics, never compliance; acknowledgement is never compliance. | — |
