"""Policy catalogue, decision questions and the recommendation (priority) engine.

The catalogue is a list of candidate documents, not a list every organization must create (spec §7.1).
Priority weights are configurable product heuristics, not requirements of any standard (spec §7.2).
"""
from __future__ import annotations

from .engine import Profile
from .questions import o

CATALOGUE_VERSION = "2026.10-1"

WEIGHTS = {"applicability": 0.25, "risk": 0.25, "maturity_gap": 0.15, "dependency": 0.15,
           "criticality": 0.15, "scope": 0.05}

LEVELS = {0: {"en": "Governance framework", "fr": "Cadre de gouvernance"},
          1: {"en": "Enterprise policy", "fr": "Politique d’entreprise"},
          2: {"en": "Topic-specific policy", "fr": "Politique thématique"},
          3: {"en": "Standard", "fr": "Norme"},
          4: {"en": "Procedure", "fr": "Procédure"}}

DOMAINS = {
    "governance": {"en": "Enterprise governance", "fr": "Gouvernance d’entreprise"},
    "people": {"en": "People", "fr": "Personnes"},
    "information": {"en": "Information", "fr": "Information"},
    "identity": {"en": "Identity and access", "fr": "Identités et accès"},
    "operations": {"en": "Infrastructure and operations", "fr": "Infrastructure et exploitation"},
    "development": {"en": "Architecture and development", "fr": "Architecture et développement"},
    "suppliers": {"en": "Suppliers", "fr": "Fournisseurs"},
    "resilience": {"en": "Detection and recovery", "fr": "Détection et rétablissement"},
    "specialized": {"en": "Physical and specialized", "fr": "Physique et spécialisé"},
}


def _t(en, fr):
    return {"en": en, "fr": fr}


# template: "full" = complete clause library; "structure" = mandatory sections with typed placeholders.
CATALOGUE: list[dict] = [
    {"code": "EISP", "abbr": "EISP", "level": 1, "domain": "governance", "parent": None, "template": "full",
     "title": _t("Enterprise Information Security Policy", "Politique de sécurité de l’information de l’entreprise"),
     "summary": _t("Organization-wide principles, scope, accountability and the policy framework.",
                   "Principes, portée, responsabilités et cadre de politiques pour toute l’organisation.")},
    {"code": "RISK", "abbr": "RSK", "level": 2, "domain": "governance", "parent": "EISP", "template": "full",
     "title": _t("Cybersecurity Risk Management and Exceptions Policy", "Politique de gestion des risques de cybersécurité et des dérogations"),
     "summary": _t("Risk ownership, appetite, assessment and time-bound exceptions.",
                   "Propriété des risques, appétit, évaluation et dérogations limitées dans le temps.")},
    {"code": "AUP", "abbr": "AUP", "level": 2, "domain": "people", "parent": "EISP", "template": "full",
     "title": _t("Acceptable Use Policy", "Politique d’utilisation acceptable"),
     "summary": _t("What users may and may not do with organizational information and technology.",
                   "Ce que les utilisateurs peuvent faire ou non avec l’information et les technologies de l’organisation.")},
    {"code": "IAM", "abbr": "IAM", "level": 2, "domain": "identity", "parent": "EISP", "template": "full",
     "title": _t("Identity and Access Management Policy", "Politique de gestion des identités et des accès"),
     "summary": _t("Authorization, authentication, privileged access, reviews and revocation.",
                   "Autorisation, authentification, accès privilégiés, revues et révocation.")},
    {"code": "CLASS", "abbr": "ICH", "level": 2, "domain": "information", "parent": "EISP", "template": "full",
     "title": _t("Information Classification and Handling Policy", "Politique de classification et de manipulation de l’information"),
     "summary": _t("One classification scheme and minimum handling rules per level.",
                   "Un seul schéma de classification et des règles minimales de manipulation par niveau.")},
    {"code": "IR", "abbr": "IRP", "level": 2, "domain": "resilience", "parent": "EISP", "template": "full",
     "title": _t("Security Incident Management Policy", "Politique de gestion des incidents de sécurité"),
     "summary": _t("Reporting, triage, response authority, notification decisions and lessons learned.",
                   "Signalement, triage, autorité d’intervention, décisions de notification et leçons apprises.")},
    {"code": "BACKUP", "abbr": "BKP", "level": 2, "domain": "resilience", "parent": "EISP", "template": "full",
     "title": _t("Backup and Recovery Policy", "Politique de sauvegarde et de restauration"),
     "summary": _t("Backup scope, protection, restoration testing and recovery objectives.",
                   "Portée des sauvegardes, protection, tests de restauration et objectifs de rétablissement.")},
    {"code": "TPRM", "abbr": "TPS", "level": 2, "domain": "suppliers", "parent": "EISP", "template": "full",
     "title": _t("Third-Party and Supplier Security Policy", "Politique de sécurité des tiers et des fournisseurs"),
     "summary": _t("Supplier tiering, due diligence, contract clauses, monitoring and exit.",
                   "Classement des fournisseurs, vérification, clauses contractuelles, suivi et sortie.")},
    {"code": "VULN", "abbr": "VPM", "level": 2, "domain": "operations", "parent": "EISP", "template": "full",
     "title": _t("Vulnerability, Patch and Change Management Policy", "Politique de gestion des vulnérabilités, des correctifs et des changements"),
     "summary": _t("Asset inventory, scanning, remediation timeframes, secure configuration and change control.",
                   "Inventaire des actifs, balayage, délais de correction, configuration sécurisée et contrôle des changements.")},
    {"code": "REMOTE", "abbr": "RMT", "level": 2, "domain": "people", "parent": "EISP", "template": "full",
     "title": _t("Remote Work and Mobile Device Policy", "Politique de télétravail et d’appareils mobiles"),
     "summary": _t("Secure remote access, device protection and personal-device rules.",
                   "Accès à distance sécurisé, protection des appareils et règles pour les appareils personnels.")},
    {"code": "PRIV", "abbr": "PRV", "level": 2, "domain": "information", "parent": "EISP", "template": "full",
     "title": _t("Personal Information Protection Policy", "Politique de protection des renseignements personnels"),
     "summary": _t("Privacy governance, lifecycle of personal information, impact assessments and incidents.",
                   "Gouvernance de la vie privée, cycle de vie des renseignements personnels, évaluations et incidents.")},
    {"code": "AI", "abbr": "AIU", "level": 2, "domain": "development", "parent": "EISP", "template": "full",
     "title": _t("Artificial Intelligence Acceptable and Secure Use Policy", "Politique d’utilisation acceptable et sécurisée de l’intelligence artificielle"),
     "summary": _t("Approved AI tools, data rules, human accountability and AI system inventory.",
                   "Outils d’IA approuvés, règles sur les données, responsabilité humaine et inventaire des systèmes d’IA.")},
    {"code": "SDLC", "abbr": "SDL", "level": 2, "domain": "development", "parent": "EISP", "template": "full",
     "title": _t("Secure Software Development Policy", "Politique de développement logiciel sécurisé"),
     "summary": _t("Security requirements, code review, secrets, dependencies and release.",
                   "Exigences de sécurité, revue de code, secrets, dépendances et mise en production.")},
    {"code": "LOG", "abbr": "LOG", "level": 2, "domain": "operations", "parent": "EISP", "template": "full",
     "title": _t("Logging and Monitoring Policy", "Politique de journalisation et de surveillance"),
     "summary": _t("Events to log, protection and retention of logs, review and alerting.",
                   "Événements à journaliser, protection et conservation des journaux, revue et alertes.")},
    {"code": "OT", "abbr": "OTS", "level": 2, "domain": "specialized", "parent": "EISP", "template": "full",
     "title": _t("Operational Technology Security Policy", "Politique de sécurité des technologies opérationnelles"),
     "summary": _t("Safety-first security for industrial and cyber-physical systems.",
                   "Sécurité des systèmes industriels et cyberphysiques, la sécurité des personnes d’abord.")},
    {"code": "CRYPTO", "abbr": "CRY", "level": 2, "domain": "information", "parent": "EISP", "template": "structure",
     "title": _t("Cryptography and Key Management Policy", "Politique de cryptographie et de gestion des clés"),
     "summary": _t("Encryption by classification and key ownership.", "Chiffrement selon la classification et propriété des clés.")},
    {"code": "BCP", "abbr": "BCM", "level": 2, "domain": "resilience", "parent": "EISP", "template": "structure",
     "title": _t("Business Continuity and Disaster Recovery Policy", "Politique de continuité des activités et de reprise après sinistre"),
     "summary": _t("Continuity governance, impact analysis, plans and exercises.", "Gouvernance de la continuité, analyse d’impact, plans et exercices.")},
    {"code": "PHYS", "abbr": "PHY", "level": 2, "domain": "specialized", "parent": "EISP", "template": "structure",
     "title": _t("Physical and Environmental Security Policy", "Politique de sécurité physique et environnementale"),
     "summary": _t("Secure areas, equipment and visitors.", "Zones sécurisées, équipements et visiteurs.")},
    {"code": "CLOUD", "abbr": "CLD", "level": 2, "domain": "development", "parent": "EISP", "template": "structure",
     "title": _t("Cloud Security Policy", "Politique de sécurité infonuagique"),
     "summary": _t("Cloud service lifecycle and shared responsibility.", "Cycle de vie des services infonuagiques et responsabilité partagée.")},
    {"code": "TRAIN", "abbr": "SAT", "level": 2, "domain": "people", "parent": "EISP", "template": "structure",
     "title": _t("Security Awareness and Training Policy", "Politique de sensibilisation et de formation à la sécurité"),
     "summary": _t("Role-based training, frequency and effectiveness measures.", "Formation selon le rôle, fréquence et mesure de l’efficacité.")},
    # ---------------------------------------------------------------- level 3: standards
    {"code": "STD-AUTH", "abbr": "AUTH", "level": 3, "domain": "identity", "parent": "IAM", "template": "full",
     "title": _t("Authentication and Password Standard", "Norme d’authentification et de mots de passe"),
     "summary": _t("Password length, compromised-password blocking, lockout, screen lock, MFA factors, service-account secrets.",
                   "Longueur des mots de passe, blocage des mots de passe compromis, verrouillage, écran de veille, facteurs d’AMF, secrets des comptes de service.")},
    {"code": "STD-HANDLING", "abbr": "HDL", "level": 3, "domain": "information", "parent": "CLASS", "template": "full",
     "title": _t("Information Handling Standard", "Norme de manipulation de l’information"),
     "summary": _t("Handling matrix per classification level: labelling, storage, transmission, sharing, disposal.",
                   "Matrice de manipulation par niveau de classification : mention, stockage, transmission, partage, élimination.")},
    {"code": "STD-CRYPTO", "abbr": "CRY", "level": 3, "domain": "information", "parent": "CLASS", "template": "full",
     "title": _t("Cryptography Standard", "Norme de cryptographie"),
     "summary": _t("Approved protocols and algorithms, encryption at rest and in transit, keys and certificates.",
                   "Protocoles et algorithmes approuvés, chiffrement au repos et en transit, clés et certificats.")},
    {"code": "STD-LOG", "abbr": "LOG", "level": 3, "domain": "operations", "parent": "LOG", "template": "full",
     "title": _t("Logging Standard", "Norme de journalisation"),
     "summary": _t("Log sources, events, retention, time synchronization, review frequency and access to logs.",
                   "Sources et événements journalisés, conservation, synchronisation de l’heure, fréquence de revue et accès aux journaux.")},
    # ---------------------------------------------------------------- level 4: procedures
    {"code": "PRC-IR", "abbr": "IR", "level": 4, "domain": "resilience", "parent": "IR", "template": "full",
     "title": _t("Security Incident Response Procedure", "Procédure d’intervention en cas d’incident de sécurité"),
     "summary": _t("Step by step: report, triage, severity, containment, evidence, notification assessment, recovery, review.",
                   "Étape par étape : signalement, triage, gravité, confinement, preuve, évaluation des notifications, rétablissement, revue.")},
    {"code": "PRC-JML", "abbr": "JML", "level": 4, "domain": "identity", "parent": "IAM", "template": "full",
     "title": _t("Access Provisioning and Revocation Procedure", "Procédure d’attribution et de révocation des accès"),
     "summary": _t("Joiners, movers, leavers and periodic access reviews.", "Arrivées, mouvements, départs et revues périodiques des accès.")},
    {"code": "PRC-EXC", "abbr": "EXC", "level": 4, "domain": "governance", "parent": "RISK", "template": "full",
     "title": _t("Exception Request and Approval Procedure", "Procédure de demande et d’approbation des dérogations"),
     "summary": _t("How to request, assess, approve, record, renew and close a security exception.",
                   "Comment demander, évaluer, approuver, consigner, renouveler et clore une dérogation de sécurité.")},
    {"code": "PRC-RESTORE", "abbr": "RST", "level": 4, "domain": "resilience", "parent": "BACKUP", "template": "full",
     "title": _t("Backup Restoration Test Procedure", "Procédure de test de restauration des sauvegardes"),
     "summary": _t("Planning, performing, verifying and recording restoration tests.",
                   "Planifier, effectuer, vérifier et consigner les tests de restauration.")},
]

BY_CODE = {c["code"]: c for c in CATALOGUE}


def d(code, policy, label_en, label_fr, options, suggested=None, why_en="", why_fr="", legal=False, kind="select"):
    return {"code": code, "policy": policy, "section": "decisions", "type": kind, "options": options,
            "label": _t(label_en, label_fr), "help": _t(why_en, why_fr), "why": _t(why_en, why_fr),
            "suggested": suggested, "legal_review": legal, "mode": "decision", "required": False}


DAYS = lambda *n: [o(str(x), f"{x} days", f"{x} jours") for x in n]  # noqa: E731

DECISIONS: list[dict] = [
    d("DEC-EISP-COMMITTEE", "EISP", "Is there (or will there be) a security governance committee?",
      "Existe-t-il (ou existera-t-il) un comité de gouvernance de la sécurité?",
      [o("yes", "Yes", "Oui"), o("no", "No — the executive team fulfils this role", "Non — l’équipe de direction joue ce rôle")],
      "yes", "Names the body that oversees the security programme.", "Désigne l’instance qui supervise le programme de sécurité."),
    d("DEC-EISP-COMMITTEE-NAME", "EISP", "Name of that committee", "Nom de ce comité", [], None,
      "e.g., “Information Security Steering Committee”.", "p. ex. « Comité directeur de la sécurité de l’information ».", kind="text"),
    d("DEC-RISK-APPETITE-OWNER", "RISK", "Who approves the cybersecurity risk appetite?", "Qui approuve l’appétit pour le risque de cybersécurité?",
      [o("board", "Board of directors", "Conseil d’administration"), o("exec", "Executive committee", "Comité de direction"),
       o("ceo", "Chief executive", "Dirigeant principal")], "board",
      "Appetite is a governance decision endorsed at the top.", "L’appétit est une décision de gouvernance entérinée au sommet."),
    d("DEC-RISK-ASSESS-FREQ", "RISK", "How often is the cybersecurity risk assessment refreshed?", "À quelle fréquence l’évaluation des risques de cybersécurité est-elle mise à jour?",
      [o("annual", "At least annually and on major change", "Au moins annuellement et lors de changements majeurs"),
       o("semiannual", "Every six months and on major change", "Tous les six mois et lors de changements majeurs")], "annual",
      "A common practice; choose what you can sustain.", "Pratique courante; choisissez ce que vous pouvez maintenir."),
    d("DEC-EXC-APPROVER", "RISK", "Who approves exceptions to security requirements?", "Qui approuve les dérogations aux exigences de sécurité?",
      [o("risk_owner", "The accountable risk owner, after security review", "Le responsable du risque, après avis de la sécurité"),
       o("exec", "The executive committee", "Le comité de direction"),
       o("tiered", "Tiered: risk owner for moderate risk, executive committee for high risk",
         "Par palier : responsable du risque pour un risque modéré, comité de direction pour un risque élevé")], "tiered",
      "Exceptions must be approved by the risk owner, not only by IT.", "Les dérogations doivent être approuvées par le responsable du risque, pas seulement par les TI."),
    d("DEC-EXC-MAX", "RISK", "Maximum duration of an exception before renewal", "Durée maximale d’une dérogation avant renouvellement",
      [o("3", "3 months", "3 mois"), o("6", "6 months", "6 mois"), o("12", "12 months", "12 mois")], "6",
      "Exceptions must be time-bound.", "Les dérogations doivent être limitées dans le temps."),
    d("DEC-AUP-PERSONAL", "AUP", "Is limited personal use of work technology allowed?", "L’utilisation personnelle limitée des technologies de travail est-elle permise?",
      [o("limited", "Yes, limited and reasonable", "Oui, limitée et raisonnable"), o("no", "No", "Non")], "limited",
      "A normative choice for management.", "Un choix normatif de la direction."),
    d("DEC-AUP-MONITOR", "AUP", "Does the organization monitor the use of its systems?", "L’organisation surveille-t-elle l’utilisation de ses systèmes?",
      [o("yes_notice", "Yes, for security purposes, with notice to users", "Oui, à des fins de sécurité, avec avis aux utilisateurs"),
       o("no", "No systematic monitoring", "Aucune surveillance systématique")], None,
      "Employee monitoring has legal and ethical limits; legal review required.", "La surveillance des employés a des limites juridiques et éthiques; révision juridique requise.", legal=True),
    d("DEC-IAM-MFA-SCOPE", "IAM", "Where must multi-factor authentication be required?", "Où l’authentification multifacteur doit-elle être exigée?",
      [o("all", "All users on all systems that support it", "Tous les utilisateurs sur tous les systèmes qui la permettent"),
       o("remote_priv_cloud", "Remote access, privileged accounts, email and cloud services", "Accès à distance, comptes privilégiés, courriel et services infonuagiques"),
       o("priv", "Privileged accounts only", "Comptes privilégiés seulement")], "remote_priv_cloud",
      "A material security decision; the draft states it only once you choose.", "Une décision de sécurité importante; l’ébauche ne l’énonce qu’une fois choisie."),
    d("DEC-IAM-REVIEW", "IAM", "How often are user access rights reviewed?", "À quelle fréquence les droits d’accès sont-ils revus?",
      [o("quarterly_priv", "Privileged quarterly, others annually", "Privilégiés trimestriellement, autres annuellement"),
       o("semiannual", "Every six months for all", "Tous les six mois pour tous"), o("annual", "Annually for all", "Annuellement pour tous")], "quarterly_priv",
      "Recertification by business owners.", "Recertification par les responsables d’affaires."),
    d("DEC-IAM-LEAVER", "IAM", "Deadline to disable access when someone leaves", "Délai pour désactiver l’accès d’une personne qui quitte",
      [o("same_day", "By the end of the last working day", "Au plus tard à la fin du dernier jour de travail"),
       o("24h", "Within 24 hours", "Dans les 24 heures"), o("72h", "Within 72 hours", "Dans les 72 heures")], "same_day",
      "Timely revocation limits insider and orphan-account risk.", "Une révocation rapide limite le risque d’initié et de comptes orphelins."),
    d("DEC-IAM-APPROVER", "IAM", "Who approves access to a system?", "Qui approuve l’accès à un système?",
      [o("owner", "The system or information owner", "Le responsable du système ou de l’information"),
       o("manager_owner", "The person’s manager and the system owner", "Le gestionnaire de la personne et le responsable du système")], "manager_owner",
      "Access is a business decision implemented by IT.", "L’accès est une décision d’affaires mise en œuvre par les TI."),
    d("DEC-CLASS-DEFAULT", "CLASS", "Default classification of unlabelled information", "Classification par défaut de l’information non étiquetée",
      [o("internal", "Internal", "Interne"), o("confidential", "Confidential", "Confidentiel")], "internal",
      "Applies until the owner classifies the information.", "S’applique jusqu’à ce que le responsable classifie l’information."),
    d("DEC-IR-REPORT", "IR", "How quickly must staff report a suspected incident?", "Dans quel délai le personnel doit-il signaler un incident soupçonné?",
      [o("immediately", "Immediately", "Immédiatement"), o("1h", "Within one hour of noticing", "Dans l’heure suivant la constatation"),
       o("same_day", "The same working day", "Le jour ouvrable même")], "immediately",
      "Early reporting shortens response.", "Un signalement rapide raccourcit l’intervention."),
    d("DEC-IR-AUTHORITY", "IR", "Who may isolate systems or suspend services during an incident?", "Qui peut isoler des systèmes ou suspendre des services pendant un incident?",
      [o("security_lead", "The information security lead", "Le responsable de la sécurité de l’information"),
       o("security_lead_exec", "The security lead, with an executive informed without delay", "Le responsable de la sécurité, un dirigeant étant informé sans délai"),
       o("exec", "An executive only", "Un dirigeant seulement")], "security_lead_exec",
      "Unclear incident authority is a known failure pattern.", "Une autorité floue en cas d’incident est un schéma d’échec connu."),
    d("DEC-IR-EXERCISE", "IR", "How often is incident response exercised?", "À quelle fréquence la réponse aux incidents est-elle exercée?",
      [o("annual", "At least annually", "Au moins annuellement"), o("semiannual", "Twice a year", "Deux fois par an")], "annual",
      "Tabletop or technical exercises.", "Exercices sur table ou techniques."),
    d("DEC-BKP-FREQ", "BACKUP", "Minimum backup frequency for critical systems", "Fréquence minimale de sauvegarde des systèmes critiques",
      [o("daily", "Daily", "Quotidienne"), o("hourly", "Several times a day", "Plusieurs fois par jour"), o("weekly", "Weekly", "Hebdomadaire")], "daily",
      "Should match the tolerable data loss (RPO).", "Devrait correspondre à la perte de données tolérable (PMDA)."),
    d("DEC-BKP-TEST", "BACKUP", "How often is restoration tested?", "À quelle fréquence la restauration est-elle testée?",
      [o("quarterly", "Quarterly", "Trimestriellement"), o("semiannual", "Every six months", "Tous les six mois"), o("annual", "Annually", "Annuellement")], "quarterly",
      "Untested backups are an assumption, not a control.", "Une sauvegarde non testée est une hypothèse, pas une mesure."),
    d("DEC-BKP-IMMUTABLE", "BACKUP", "Must at least one copy be offline or immutable?", "Au moins une copie doit-elle être hors ligne ou immuable?",
      [o("yes", "Yes", "Oui"), o("no", "No", "Non")], "yes",
      "Protects backups from ransomware.", "Protège les sauvegardes contre les rançongiciels."),
    d("DEC-BKP-RTO", "BACKUP", "Recovery time objective (RTO) for the most critical services", "Délai maximal d’interruption (DMI) des services les plus critiques",
      [o("4h", "4 hours", "4 heures"), o("24h", "24 hours", "24 heures"), o("72h", "72 hours", "72 heures")], None,
      "A business decision, usually from an impact analysis.", "Une décision d’affaires, issue d’ordinaire d’une analyse d’impact."),
    d("DEC-TP-REASSESS", "TPRM", "How often are critical suppliers reassessed?", "À quelle fréquence les fournisseurs critiques sont-ils réévalués?",
      [o("annual", "Annually", "Annuellement"), o("biennial", "Every two years", "Tous les deux ans")], "annual",
      "Ongoing assurance, not only at onboarding.", "Assurance continue, pas seulement à l’intégration."),
    d("DEC-TP-NOTIFY", "TPRM", "Deadline for suppliers to notify you of a security incident", "Délai de notification d’un incident de sécurité par les fournisseurs",
      [o("24", "24 hours", "24 heures"), o("48", "48 hours", "48 heures"), o("72", "72 hours", "72 heures")], "24",
      "Written into contracts; check what your contracts already say.", "Inscrit aux contrats; vérifiez ce que prévoient déjà vos contrats."),
    d("DEC-VULN-CRIT", "VULN", "Remediation time for critical vulnerabilities", "Délai de correction des vulnérabilités critiques",
      DAYS(7, 14, 30), "14", "Measured from availability of a fix; exploited vulnerabilities faster.",
      "Mesuré à partir de la disponibilité d’un correctif; plus vite si la vulnérabilité est exploitée."),
    d("DEC-VULN-HIGH", "VULN", "Remediation time for high vulnerabilities", "Délai de correction des vulnérabilités élevées",
      DAYS(30, 60, 90), "30", "Choose what operations can sustain.", "Choisissez ce que l’exploitation peut soutenir."),
    d("DEC-VULN-SCAN", "VULN", "Vulnerability scanning frequency", "Fréquence du balayage des vulnérabilités",
      [o("weekly", "Weekly", "Hebdomadaire"), o("monthly", "Monthly", "Mensuelle"), o("quarterly", "Quarterly", "Trimestrielle")], "monthly",
      "Internet-facing systems may need more frequent scans.", "Les systèmes exposés à Internet peuvent exiger des balayages plus fréquents."),
    d("DEC-REM-NETWORK", "REMOTE", "Rule for remote connections", "Règle pour les connexions à distance",
      [o("vpn", "Organization VPN or approved secure access service required", "RPV de l’organisation ou service d’accès sécurisé approuvé obligatoire"),
       o("mfa_cloud", "Direct access to cloud services allowed with MFA", "Accès direct aux services infonuagiques permis avec AMF")], "mfa_cloud",
      "Depends on where systems are hosted.", "Dépend de l’endroit où les systèmes sont hébergés."),
    d("DEC-REM-BYOD-MDM", "REMOTE", "Condition for personal devices to access work data", "Condition d’accès des appareils personnels aux données de travail",
      [o("mdm", "Enrolment in device management (MDM/MAM)", "Inscription à la gestion des appareils (MDM/MAM)"),
       o("app_only", "Approved apps only, with screen lock and current OS", "Applications approuvées seulement, avec verrouillage et SE à jour")], "app_only",
      "Asked only when personal devices are permitted.", "Posée seulement si les appareils personnels sont permis.", legal=True),
    d("DEC-PRIV-PIA", "PRIV", "When is a privacy impact assessment required?", "Quand une évaluation des facteurs relatifs à la vie privée est-elle exigée?",
      [o("projects", "For any project to acquire, develop or overhaul a system involving personal information",
         "Pour tout projet d’acquisition, de développement ou de refonte d’un système impliquant des renseignements personnels"),
       o("high_risk", "Only for high-risk processing", "Seulement pour les traitements à risque élevé")], None,
      "Legal review required — obligations depend on jurisdiction.", "Révision juridique requise — les obligations dépendent du territoire.", legal=True),
    d("DEC-AI-TOOLS", "AI", "Which AI tools may staff use?", "Quels outils d’IA le personnel peut-il utiliser?",
      [o("approved_list", "Only tools on an approved list", "Seulement les outils d’une liste approuvée"),
       o("enterprise", "Enterprise-licensed tools only, no consumer accounts", "Outils sous licence d’entreprise seulement, aucun compte grand public"),
       o("none", "None until a policy decision is made", "Aucun tant qu’une décision n’est pas prise")], "approved_list",
      "Shadow AI is a growing data-leak channel.", "L’IA de l’ombre est un canal de fuite de données en croissance."),
    d("DEC-AI-DATA", "AI", "Highest classification that may be entered into approved AI tools",
      "Classification la plus élevée pouvant être saisie dans les outils d’IA approuvés",
      [o("public", "Public only", "Public seulement"), o("internal", "Up to Internal", "Jusqu’à Interne"),
       o("confidential", "Up to Confidential, in enterprise tools with contractual safeguards", "Jusqu’à Confidentiel, dans des outils d’entreprise avec garanties contractuelles")], "internal",
      "Links AI use to the classification scheme.", "Relie l’utilisation de l’IA au schéma de classification."),
    d("DEC-SDLC-REVIEW", "SDLC", "Code review requirement before release", "Exigence de revue de code avant la mise en production",
      [o("all", "Peer review for every change", "Revue par un pair pour chaque changement"),
       o("risk", "Peer review for changes to security-relevant or customer-facing code", "Revue par un pair pour le code sensible pour la sécurité ou exposé aux clients")], "all",
      "Segregation between author and approver.", "Séparation entre l’auteur et l’approbateur."),
    d("DEC-LOG-RETENTION", "LOG", "Minimum retention of security logs", "Conservation minimale des journaux de sécurité",
      [o("90", "90 days", "90 jours"), o("365", "1 year", "1 an"), o("730", "2 years", "2 ans")], "365",
      "Long enough for investigations; check legal and contractual requirements.", "Assez longue pour les enquêtes; vérifiez les exigences légales et contractuelles."),
    d("DEC-OT-REMOTE", "OT", "Rule for vendor remote access to OT systems", "Règle d’accès à distance des fournisseurs aux systèmes TO",
      [o("brokered", "Only through a monitored, brokered connection enabled on request", "Seulement par une connexion intermédiée et surveillée, activée sur demande"),
       o("none", "Not permitted", "Interdit")], "brokered",
      "Vendor access is a frequent OT entry point.", "L’accès des fournisseurs est un point d’entrée fréquent en TO."),
]

DECISIONS += [
    d("DEC-AUTH-MINLEN", "STD-AUTH", "Minimum password length", "Longueur minimale des mots de passe",
      [o("15_8", "15 characters, or 8 when multi-factor authentication protects the account",
         "15 caractères, ou 8 lorsque l’authentification multifacteur protège le compte"),
       o("12", "12 characters for all accounts", "12 caractères pour tous les comptes"),
       o("14", "14 characters for all accounts", "14 caractères pour tous les comptes")], "15_8",
      "Length matters more than complexity rules.", "La longueur compte davantage que les règles de complexité."),
    d("DEC-AUTH-LOCKOUT", "STD-AUTH", "Failed sign-in attempts before an account is locked or throttled",
      "Tentatives de connexion échouées avant le verrouillage ou le ralentissement d’un compte",
      [o("5", "5 attempts", "5 tentatives"), o("10", "10 attempts", "10 tentatives")], "10",
      "Balances guessing attacks against help-desk load.", "Équilibre entre attaques par devinette et charge du centre d’assistance."),
    d("DEC-AUTH-SCREENLOCK", "STD-AUTH", "Automatic screen lock after inactivity", "Verrouillage automatique de l’écran après inactivité",
      [o("5", "5 minutes", "5 minutes"), o("10", "10 minutes", "10 minutes"), o("15", "15 minutes", "15 minutes")], "10",
      "Shorter in public-facing or clinical areas.", "Plus court dans les aires publiques ou cliniques."),
    d("DEC-AUTH-FACTORS", "STD-AUTH", "Accepted second factors", "Seconds facteurs acceptés",
      [o("phishing_resistant_admin", "Authenticator app or security key; phishing-resistant keys or passkeys for administrators",
         "Application d’authentification ou clé de sécurité; clés résistantes à l’hameçonnage ou clés d’accès pour les administrateurs"),
       o("app_token", "Authenticator app or hardware token; SMS not accepted", "Application d’authentification ou jeton matériel; SMS non accepté"),
       o("any", "Any, including SMS as a fallback", "Tout facteur, y compris le SMS en solution de repli")], "phishing_resistant_admin",
      "SMS codes can be intercepted or redirected.", "Les codes par SMS peuvent être interceptés ou détournés."),
    d("DEC-HDL-CLOUD", "STD-HANDLING", "Where may Confidential information be stored?", "Où l’information Confidentielle peut-elle être stockée?",
      [o("approved_list", "Only in storage services on the list approved by the security lead", "Seulement dans les services de stockage figurant sur la liste approuvée par le responsable de la sécurité"),
       o("tenant", "Only in the organization’s own collaboration tenant (e.g., its Microsoft 365 or Google Workspace)", "Seulement dans l’environnement de collaboration de l’organisation (p. ex. son Microsoft 365 ou Google Workspace)")],
      "approved_list", "Prevents copies in personal or unmanaged cloud accounts.", "Évite les copies dans des comptes infonuagiques personnels ou non gérés."),
    d("DEC-HDL-USB", "STD-HANDLING", "Removable media (USB keys, external drives)", "Supports amovibles (clés USB, disques externes)",
      [o("encrypted_only", "Allowed only if encrypted and issued by the organization", "Permis seulement s’ils sont chiffrés et fournis par l’organisation"),
       o("blocked", "Blocked, except by approved exception", "Bloqués, sauf dérogation approuvée")], "encrypted_only",
      "A frequent source of loss and malware.", "Une source fréquente de pertes et de logiciels malveillants."),
    d("DEC-CRY-TLS", "STD-CRYPTO", "Minimum TLS version for data in transit", "Version minimale de TLS pour les données en transit",
      [o("1.2", "TLS 1.2, with TLS 1.3 preferred", "TLS 1.2, TLS 1.3 privilégié"), o("1.3", "TLS 1.3 only", "TLS 1.3 seulement")], "1.2",
      "TLS 1.3 only may break older clients or partners.", "TLS 1.3 seulement peut exclure des clients ou partenaires plus anciens."),
    d("DEC-CRY-KEYROT", "STD-CRYPTO", "Rotation of encryption keys you manage", "Renouvellement des clés de chiffrement gérées par l’organisation",
      [o("annual", "At least annually and on suspected compromise", "Au moins annuellement et en cas de compromission soupçonnée"),
       o("biennial", "At least every two years and on suspected compromise", "Au moins tous les deux ans et en cas de compromission soupçonnée")], "annual",
      "Managed cloud key services can rotate automatically.", "Les services de clés infonuagiques gérés peuvent les renouveler automatiquement."),
    d("DEC-LOG-REVIEW", "STD-LOG", "How are security logs reviewed?", "Comment les journaux de sécurité sont-ils revus?",
      [o("alerts_daily", "Automated alerts triaged daily; full review weekly", "Alertes automatisées triées chaque jour; revue complète chaque semaine"),
       o("weekly", "Manual review weekly", "Revue manuelle chaque semaine"),
       o("mdr", "By the managed detection and response provider, continuously", "Par le fournisseur de détection et réponse gérées, en continu")], "alerts_daily",
      "Logs no one reviews do not detect anything.", "Des journaux que personne ne consulte ne détectent rien."),
    d("DEC-PIR-DAYS", "PRC-IR", "Post-incident review held within", "Revue post-incident tenue dans un délai de",
      [o("5", "5 working days after closure", "5 jours ouvrables après la clôture"), o("10", "10 working days after closure", "10 jours ouvrables après la clôture")], "10",
      "While memories are fresh.", "Pendant que les souvenirs sont frais."),
    d("DEC-EXC-NOTICE", "PRC-EXC", "Reminder to the exception owner before expiry", "Rappel au responsable de la dérogation avant l’échéance",
      [o("30", "30 days before expiry", "30 jours avant l’échéance"), o("14", "14 days before expiry", "14 jours avant l’échéance")], "30",
      "Time to renew or remediate.", "Le temps de renouveler ou de corriger."),
]

DECISIONS_BY_POLICY: dict[str, list[dict]] = {}
for _d in DECISIONS:
    DECISIONS_BY_POLICY.setdefault(_d["policy"], []).append(_d)


# ------------------------------------------------------------------ recommendation engine
def _reasons(code: str, p: Profile, lang: str) -> tuple[dict, list[str], bool]:
    """Return (dimension scores 0-5, reasons, recommended) for one catalogue entry."""
    T = (lambda en, fr: fr if lang == "fr" else en)
    s = {"applicability": 1, "risk": 2, "maturity_gap": 2, "dependency": 1, "criticality": 2, "scope": 2}
    r: list[str] = []
    rec = False
    immature = p.value("ORG-12") in ("informal", "developing", None)
    if immature:
        s["maturity_gap"] = 4
    if code == "EISP":
        s.update(applicability=4, dependency=5, criticality=5, scope=5)
        r.append(T("Parent document: every other policy derives its authority from it.",
                   "Document parent : toutes les autres politiques en tirent leur autorité."))
        rec = True
    elif code == "RISK":
        s.update(dependency=4, risk=3)
        r.append(T("Defines who accepts risk and how exceptions are approved — referenced by every policy.",
                   "Définit qui accepte le risque et comment les dérogations sont approuvées — citée par toutes les politiques."))
        if p.value("GOV-01B") in ("it", "unclear") or p.value("GOV-06") in ("no", "partial"):
            s["maturity_gap"] = 5
            r.append(T("Risk acceptance or exception handling is not yet clearly governed.",
                       "L’acceptation des risques ou la gestion des dérogations n’est pas encore clairement encadrée."))
        rec = True
    elif code == "AUP":
        s.update(risk=4, criticality=3)
        r.append(T("Sets the rules every user must follow; usually the first policy staff read.",
                   "Fixe les règles que chaque utilisateur doit suivre; souvent la première politique lue par le personnel."))
        rec = True
    elif code == "IAM":
        s.update(risk=5, criticality=4)
        r.append(T("Compromised or excessive access is a leading cause of incidents.",
                   "Les accès compromis ou excessifs sont une cause majeure d’incidents."))
        if p.value("TECH-04") in ("no", "partial"):
            r.append(T("MFA is not yet in place everywhere.", "L’AMF n’est pas encore en place partout."))
            s["maturity_gap"] = 5
        rec = True
    elif code == "CLASS":
        s.update(risk=4, dependency=4)
        r.append(T("Provides the single classification scheme other policies refer to.",
                   "Fournit le schéma de classification unique auquel les autres politiques renvoient."))
        if p.value("DATA-02") in ("none", "informal"):
            s["maturity_gap"] = 5
        rec = True
    elif code == "IR":
        s.update(risk=5, criticality=5)
        r.append(T("Every organization needs to know who decides and who reports during an incident.",
                   "Toute organisation doit savoir qui décide et qui signale pendant un incident."))
        if not p.has("TECH-08", "ir_plan"):
            r.append(T("No written incident response plan was reported.", "Aucun plan écrit de réponse aux incidents n’a été indiqué."))
        rec = True
    elif code == "BACKUP":
        s.update(risk=4, criticality=5)
        r.append(T("Recovery from ransomware and failures depends on tested backups.",
                   "Le rétablissement après rançongiciel ou panne dépend de sauvegardes testées."))
        if p.value("TECH-07") in ("no", "partial"):
            s["maturity_gap"] = 5
        rec = True
    elif code == "TPRM":
        s.update(risk=4)
        r.append(T("Suppliers and cloud services hold or reach your data.", "Des fournisseurs et services infonuagiques détiennent vos données ou y accèdent."))
        if p.value("REG-06") == "critical" or p.has("ORG-13", "msp"):
            s.update(risk=5, criticality=4)
            r.append(T("Some suppliers are critical to operations or manage your IT.", "Certains fournisseurs sont essentiels ou gèrent vos TI."))
        rec = True
    elif code == "VULN":
        s.update(risk=5, criticality=3)
        r.append(T("Unpatched and misconfigured systems are routinely exploited.", "Les systèmes non corrigés et mal configurés sont couramment exploités."))
        rec = True
    elif code == "REMOTE":
        if p.value("TECH-02") in ("hybrid", "remote") or p.value("TECH-02B") in ("limited", "yes"):
            s.update(applicability=3, risk=4)
            r.append(T("Staff work remotely or use personal devices.", "Le personnel travaille à distance ou utilise des appareils personnels."))
            rec = True
        else:
            r.append(T("Mostly on-site work and no personal devices reported — rules can live in the acceptable use policy.",
                       "Travail surtout sur place et aucun appareil personnel indiqué — les règles peuvent figurer dans la politique d’utilisation acceptable."))
    elif code == "PRIV":
        if p.handles_pi:
            s.update(applicability=4, risk=4, criticality=4)
            r.append(T("Personal information is held; privacy-law candidates need review.",
                       "Des renseignements personnels sont détenus; des lois candidates sur la vie privée sont à examiner."))
            rec = True
        else:
            r.append(T("No personal information categories were selected.", "Aucune catégorie de renseignements personnels n’a été sélectionnée."))
    elif code == "AI":
        if p.has("DATA-06", "ai_tools", "ai_products"):
            s.update(applicability=3, risk=4)
            r.append(T("Staff use generative AI or products include AI.", "Le personnel utilise l’IA générative ou les produits intègrent de l’IA."))
            rec = True
        else:
            r.append(T("Recommended once AI use is confirmed (Standard interview).", "Recommandée une fois l’utilisation de l’IA confirmée (entrevue standard)."))
    elif code == "SDLC":
        if p.value("TECH-06") in ("inhouse", "outsourced") or p.has("ORG-02", "software_saas"):
            s.update(applicability=3, risk=4, criticality=4)
            r.append(T("The organization builds or commissions software.", "L’organisation développe ou fait développer des logiciels."))
            rec = True
    elif code == "LOG":
        s.update(risk=3)
        r.append(T("Detection and investigations rely on protected logs.", "La détection et les enquêtes reposent sur des journaux protégés."))
        rec = not p.small
    elif code == "OT":
        if p.has("TECH-03", "ot") or p.has("ORG-02", "manufacturing_ot", "energy_utilities"):
            s.update(applicability=4, risk=5, criticality=5)
            r.append(T("Industrial or cyber-physical systems are in scope; safety comes first.",
                       "Des systèmes industriels ou cyberphysiques sont visés; la sécurité des personnes d’abord."))
            rec = True
    elif code == "BCP":
        s.update(criticality=4)
        r.append(T("Usually maintained with business continuity owners; structure template only.",
                   "Habituellement tenue avec les responsables de la continuité; gabarit de structure seulement."))
        rec = not p.small and p.size_rank >= 3
    elif code in ("CRYPTO", "PHYS", "CLOUD", "TRAIN"):
        r.append(T("Structure template: sections and decisions to complete; requirements are not pre-written.",
                   "Gabarit de structure : sections et décisions à compléter; les exigences ne sont pas prérédigées."))
        if code == "CLOUD" and p.has("TECH-01", "aws", "azure", "gcp") and p.size_rank >= 2:
            rec = True
    if p.small and code in ("LOG", "TRAIN", "CRYPTO", "PHYS", "CLOUD", "BCP"):
        r.append(T("For a small organization these rules can be consolidated into the EISP or related policies.",
                   "Pour une petite organisation, ces règles peuvent être regroupées dans la PSIE ou des politiques connexes."))
    return s, r, rec


def recommend(p: Profile, lang: str = "en") -> list[dict]:
    out = []
    for c in CATALOGUE:
        scores, reasons, rec = _reasons(c["code"], p, lang)
        score = round(sum(WEIGHTS[k] * v for k, v in scores.items()) / 5 * 100)
        priority = "high" if score >= 70 else "medium" if score >= 50 else "low"
        out.append({"code": c["code"], "title": c["title"][lang], "summary": c["summary"][lang], "level": c["level"],
                    "level_label": LEVELS[c["level"]][lang], "domain": c["domain"], "domain_label": DOMAINS[c["domain"]][lang],
                    "parent": c["parent"], "template": c["template"], "recommended": rec, "score": score,
                    "priority": priority, "dimensions": scores, "reasons": reasons,
                    "decisions": [x["code"] for x in DECISIONS_BY_POLICY.get(c["code"], [])]})
    T = (lambda en, fr: fr if lang == "fr" else en)
    depth = p.value("DOC-02")
    rec_by = {x["code"]: x["recommended"] for x in out}
    for x in out:
        if x["level"] < 3:
            continue
        parent_ok = rec_by.get(x["parent"], False)
        wanted = depth == "complete" or (depth == "policies_standards" and x["level"] == 3)
        x["recommended"] = bool(wanted and parent_ok)
        ptitle = BY_CODE[x["parent"]]["title"][lang]
        x["reasons"] = [T(f"Supports the {ptitle}; keeps its measurable parameters or steps out of the policy.",
                          f"Appuie la {ptitle}; garde ses paramètres mesurables ou ses étapes hors de la politique.")]
        if not depth or depth == "policies":
            x["reasons"].append(T("Not recommended because the package depth is “policies only” or not chosen.",
                                  "Non recommandée parce que la profondeur choisie est « politiques seulement » ou n’est pas choisie."))
        elif x["level"] == 4 and depth == "policies_standards":
            x["reasons"].append(T("Procedures are recommended when the package depth includes procedures.",
                                  "Les procédures sont recommandées lorsque la profondeur choisie inclut les procédures."))
        elif not parent_ok:
            x["reasons"].append(T("Its parent policy is not recommended for this organization.",
                                  "Sa politique parente n’est pas recommandée pour cette organisation."))
    out.sort(key=lambda x: (x["level"], -int(x["recommended"]), -x["score"]))
    return out


def decision_applies(dec: dict, p: Profile) -> bool:
    if dec["code"] == "DEC-REM-BYOD-MDM":
        return p.value("TECH-02B") in ("limited", "yes")
    if dec["code"] == "DEC-EISP-COMMITTEE-NAME":
        return p.value("DEC-EISP-COMMITTEE") == "yes"
    return True
