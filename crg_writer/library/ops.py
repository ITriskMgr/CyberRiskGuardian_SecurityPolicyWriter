"""Topic-policy clause libraries: Risk & exceptions, Backup, Third parties, Vulnerability/change, Remote work."""
from .common import C, S, V, topic_frame

has = lambda code, *v: (lambda p: p.has(code, *v))  # noqa: E731

# ------------------------------------------------------------------ Risk management and exceptions
RISK = topic_frame(
    purpose=[C("P01", "This policy defines how {org} identifies, assesses, accepts and treats cybersecurity risks and how it governs exceptions to security requirements, so that every risk decision is explicit, owned and justified.",
               "La présente politique définit comment {org} identifie, évalue, accepte et traite les risques de cybersécurité et comment elle encadre les dérogations aux exigences de sécurité, afin que chaque décision de risque soit explicite, assumée et justifiée.", mod="info")],
    scope_extra=[],
    roles=[
        C("R01", "{Approver} approves the cybersecurity risk appetite.", "{Approver} approuve l’appétit pour le risque de cybersécurité.", src="answer", inputs=["ORG-07B"]),
        C("R02", "Business owners own the risks to their services, processes and information and decide on their treatment within the risk appetite.", "Les responsables d’affaires sont propriétaires des risques touchant leurs services, processus et information et décident de leur traitement dans les limites de l’appétit pour le risque."),
        C("R03", "{sec} owns the risk-management process and methodology, facilitates assessments, challenges assumptions and maintains the risk and exception registers.", "{sec} est responsable du processus et de la méthode de gestion des risques, anime les évaluations, remet en question les hypothèses et tient les registres des risques et des dérogations."),
        C("R04", "{Committee} reviews significant risks, risks above appetite and the exception portfolio.", "{Committee} examine les risques importants, les risques au-delà de l’appétit et le portefeuille de dérogations."),
    ],
    requirements=[
        S("SEC-REQ-APPETITE", "Risk appetite", "Appétit pour le risque", [
            C("AP01", by="DEC-RISK-APPETITE-OWNER", src="decision", variants={
                "board": V("The board of directors approves the cybersecurity risk appetite on the recommendation of senior management and reviews it at least annually.",
                           "Le conseil d’administration approuve l’appétit pour le risque de cybersécurité sur recommandation de la haute direction et le revoit au moins une fois par année."),
                "exec": V("The executive committee approves the cybersecurity risk appetite and reviews it at least annually.",
                          "Le comité de direction approuve l’appétit pour le risque de cybersécurité et le revoit au moins une fois par année."),
                "ceo": V("The chief executive approves the cybersecurity risk appetite and reviews it at least annually.",
                         "Le premier dirigeant approuve l’appétit pour le risque de cybersécurité et le revoit au moins une fois par année."),
                "_none": V("[DECISION: Who approves the cybersecurity risk appetite.] It is reviewed at least annually.",
                           "[DÉCISION : Qui approuve l’appétit pour le risque de cybersécurité.] Il est revu au moins une fois par année.")},
              refs=["NIST CSF 2.0 GV.RM"]),
            C("AP02", by="GOV-01", src="answer", variants={
                "very_low": V("The current approved appetite is very low (0.1–0.2 on the CyberRiskGuardian scale).", "L’appétit approuvé actuel est très faible (0,1–0,2 sur l’échelle CyberRiskGuardian)."),
                "low": V("The current approved appetite is low (0.3 on the CyberRiskGuardian scale).", "L’appétit approuvé actuel est faible (0,3 sur l’échelle CyberRiskGuardian)."),
                "moderate": V("The current approved appetite is moderate (0.5 on the CyberRiskGuardian scale).", "L’appétit approuvé actuel est modéré (0,5 sur l’échelle CyberRiskGuardian)."),
                "high": V("The current approved appetite is relatively high (0.7 on the CyberRiskGuardian scale).", "L’appétit approuvé actuel est relativement élevé (0,7 sur l’échelle CyberRiskGuardian)."),
                "not_defined": V("[DECISION: No risk appetite is approved yet; approval is to be scheduled.]", "[DÉCISION : Aucun appétit pour le risque n’est encore approuvé; son approbation est à planifier.]"),
                "_none": V("[DECISION: State the approved risk appetite.]", "[DÉCISION : Indiquer l’appétit pour le risque approuvé.]")}),
            C("AP03", "Tolerance thresholds are set per impact category (operational, financial, legal, privacy, reputational, safety); risks exceeding a threshold require action or escalation.",
              "Des seuils de tolérance sont fixés par catégorie d’impact (opérationnel, financier, juridique, vie privée, réputation, sécurité des personnes); les risques qui dépassent un seuil exigent une action ou une escalade.", mod="should"),
        ]),
        S("SEC-REQ-ASSESS", "Risk assessment", "Évaluation des risques", [
            C("AS01", by="DEC-RISK-ASSESS-FREQ", src="decision", variants={
                "annual": V("A cybersecurity risk assessment of critical services and information must be performed at least annually and when a significant change occurs (new system, supplier, jurisdiction, incident or threat).",
                            "Une évaluation des risques de cybersécurité des services et de l’information essentiels doit être effectuée au moins une fois par année et lors de tout changement important (nouveau système, fournisseur, territoire, incident ou menace)."),
                "semiannual": V("A cybersecurity risk assessment of critical services and information must be performed every six months and when a significant change occurs.",
                                "Une évaluation des risques de cybersécurité des services et de l’information essentiels doit être effectuée tous les six mois et lors de tout changement important."),
                "_none": V("A cybersecurity risk assessment must be performed [DECISION: assessment frequency] and when a significant change occurs.",
                           "Une évaluation des risques de cybersécurité doit être effectuée [DÉCISION : fréquence de l’évaluation] et lors de tout changement important.")},
              refs=["ISO 27001:2022 8.2", "NIST CSF 2.0 ID.RA"]),
            C("AS02", "Assessments use scenarios that describe the threat source, the weakness exploited, the affected asset or process and the consequences, and distinguish documented facts, assumptions and estimates.",
              "Les évaluations s’appuient sur des scénarios décrivant la source de menace, la faiblesse exploitée, l’actif ou le processus touché et les conséquences, et distinguent les faits documentés, les hypothèses et les estimations.",
              refs=["NIST CSF 2.0 ID.RA"]),
            C("AS03", "Results are recorded in the risk register with an owner, a treatment decision and a review date.",
              "Les résultats sont consignés au registre des risques avec un responsable, une décision de traitement et une date de révision.", refs=["NIST CSF 2.0 GV.RM"]),
        ]),
        S("SEC-REQ-TREAT", "Risk treatment and acceptance", "Traitement et acceptation des risques", [
            C("TR01", "Each risk is mitigated, transferred, avoided or accepted. The decision is made by the risk owner within the appetite; risks above appetite are decided by {committee}.",
              "Chaque risque est atténué, transféré, évité ou accepté. La décision est prise par le responsable du risque dans les limites de l’appétit; les risques au-delà de l’appétit sont tranchés par {committee}."),
            C("TR02", "Accepted risks are documented with their rationale, approver and expiry date, and are reviewed at least annually.",
              "Les risques acceptés sont documentés avec leur justification, leur approbateur et leur date d’échéance, et sont revus au moins une fois par année."),
            C("TR03", "IT or security staff must not accept business risk on behalf of a business owner.",
              "Le personnel des TI ou de la sécurité ne doit pas accepter un risque d’affaires au nom d’un responsable d’affaires.", mod="must not"),
        ]),
        S("SEC-REQ-EXC", "Exceptions", "Dérogations", [
            C("XC01", "An exception request must state the requirement that cannot be met, the reason, the scope, the proposed duration, the compensating controls and the residual risk.",
              "Une demande de dérogation doit préciser l’exigence qui ne peut être respectée, la raison, la portée, la durée proposée, les mesures compensatoires et le risque résiduel.", refs=["ISO 27002:2022 5.36"]),
            C("XC02", by="DEC-EXC-APPROVER", src="decision", variants={
                "risk_owner": V("Exceptions are approved by the accountable risk owner after review by {sec}.",
                                "Les dérogations sont approuvées par le responsable du risque après examen par {sec}."),
                "exec": V("Exceptions are approved by the executive committee after review by {sec}.",
                          "Les dérogations sont approuvées par le comité de direction après examen par {sec}."),
                "tiered": V("Exceptions with moderate residual risk are approved by the accountable risk owner after review by {sec}; exceptions with high residual risk are approved by {committee}.",
                            "Les dérogations comportant un risque résiduel modéré sont approuvées par le responsable du risque après examen par {sec}; celles qui comportent un risque résiduel élevé sont approuvées par {committee}."),
                "_none": V("Exceptions are approved by [DECISION: exception approval authority] after review by {sec}.",
                           "Les dérogations sont approuvées par [DÉCISION : autorité d’approbation des dérogations] après examen par {sec}.")}),
            C("XC03", by="DEC-EXC-MAX", src="decision", variants={
                "3": V("An exception is granted for at most three months and may be renewed only after a new review.", "Une dérogation est accordée pour au plus trois mois et ne peut être renouvelée qu’après un nouvel examen."),
                "6": V("An exception is granted for at most six months and may be renewed only after a new review.", "Une dérogation est accordée pour au plus six mois et ne peut être renouvelée qu’après un nouvel examen."),
                "12": V("An exception is granted for at most twelve months and may be renewed only after a new review.", "Une dérogation est accordée pour au plus douze mois et ne peut être renouvelée qu’après un nouvel examen."),
                "_none": V("An exception is granted for at most [DECISION: maximum exception duration] and may be renewed only after a new review.",
                           "Une dérogation est accordée pour au plus [DÉCISION : durée maximale d’une dérogation] et ne peut être renouvelée qu’après un nouvel examen.")}),
            C("XC04", "Exceptions are recorded in the exception register; expired exceptions no longer provide cover, and the register is reported to {committee} at least quarterly.",
              "Les dérogations sont consignées au registre des dérogations; une dérogation échue ne couvre plus rien, et le registre est présenté à {committee} au moins une fois par trimestre."),
            C("XC05", "An exception must not be approved if it would leave unacceptable residual risk or set aside a legal, regulatory or contractual obligation.",
              "Une dérogation ne doit pas être approuvée si elle laisse un risque résiduel inacceptable ou écarte une obligation légale, réglementaire ou contractuelle.", mod="must not"),
        ]),
    ],
)

# ------------------------------------------------------------------ Backup and recovery
BACKUP = topic_frame(
    purpose=[C("P01", "This policy ensures that {org} can restore its information and critical services after a failure, error, disaster or cyberattack within the time the business can tolerate.",
               "La présente politique assure que {org} peut restaurer son information et ses services essentiels après une panne, une erreur, un sinistre ou une cyberattaque dans les délais que les activités peuvent tolérer.", mod="info")],
    scope_extra=[C("SC03", "It includes data held in software-as-a-service applications, for which {org} remains responsible for ensuring recoverability under the shared-responsibility model.",
                   "Elle inclut les données conservées dans des applications SaaS, pour lesquelles {org} demeure responsable d’assurer la récupération selon le modèle de responsabilité partagée.",
                   mod="info", when=has("TECH-01", "m365", "google_ws", "saas_other"))],
    roles=[
        C("R01", "Business owners set the recovery objectives of their services.", "Les responsables d’affaires fixent les objectifs de rétablissement de leurs services."),
        C("R02", "IT operations (internal or outsourced) performs, protects and tests backups and keeps the records.", "L’exploitation des TI (interne ou impartie) effectue, protège et teste les sauvegardes et en conserve les traces."),
        C("R03", "{sec} verifies that backups are protected against tampering and that tests are performed.", "{sec} vérifie que les sauvegardes sont protégées contre l’altération et que les tests sont effectués."),
    ],
    requirements=[
        S("SEC-REQ-OBJ", "Recovery objectives", "Objectifs de rétablissement", [
            C("OB01", "Each critical service must have a documented recovery time objective (RTO) and recovery point objective (RPO) approved by its business owner.",
              "Chaque service essentiel doit avoir un délai maximal d’interruption (DMI) et une perte de données maximale admissible (PDMA) documentés et approuvés par son responsable d’affaires.", refs=["ISO 27002:2022 5.30", "NIST CSF 2.0 RC.RP"]),
            C("OB02", by="DEC-BKP-RTO", src="decision", variants={
                "4h": V("The target RTO for the most critical services is 4 hours.", "Le DMI visé pour les services les plus critiques est de 4 heures."),
                "24h": V("The target RTO for the most critical services is 24 hours.", "Le DMI visé pour les services les plus critiques est de 24 heures."),
                "72h": V("The target RTO for the most critical services is 72 hours.", "Le DMI visé pour les services les plus critiques est de 72 heures."),
                "_none": V("The target RTO for the most critical services is [DECISION: recovery time objective of the most critical services].",
                           "Le DMI visé pour les services les plus critiques est de [DÉCISION : délai maximal d’interruption des services les plus critiques].")}),
        ]),
        S("SEC-REQ-BACKUP", "Backups", "Sauvegardes", [
            C("BK01", by="DEC-BKP-FREQ", src="decision", variants={
                "daily": V("Critical systems and data must be backed up at least daily, and more often where their RPO requires it.",
                           "Les systèmes et données critiques doivent être sauvegardés au moins une fois par jour, et plus souvent si leur PDMA l’exige."),
                "hourly": V("Critical systems and data must be backed up several times a day, according to their RPO.",
                            "Les systèmes et données critiques doivent être sauvegardés plusieurs fois par jour, selon leur PDMA."),
                "weekly": V("Critical systems and data must be backed up at least weekly, and more often where their RPO requires it.",
                            "Les systèmes et données critiques doivent être sauvegardés au moins une fois par semaine, et plus souvent si leur PDMA l’exige."),
                "_none": V("Critical systems and data must be backed up [DECISION: minimum backup frequency].",
                           "Les systèmes et données critiques doivent être sauvegardés [DÉCISION : fréquence minimale de sauvegarde].")},
              refs=["ISO 27002:2022 8.13", "NIST CSF 2.0 PR.DS"]),
            C("BK02", "Backups must be encrypted, stored in a location separate from the primary systems, and protected so that an attacker with administrative access to production cannot delete or alter them.",
              "Les sauvegardes doivent être chiffrées, conservées dans un emplacement distinct des systèmes principaux et protégées de sorte qu’un attaquant disposant d’un accès administratif à la production ne puisse ni les supprimer ni les modifier.",
              refs=["ISO 27002:2022 8.13"]),
            C("BK03", by="DEC-BKP-IMMUTABLE", src="decision", variants={
                "yes": V("At least one copy of critical backups must be offline or immutable for a defined retention period.",
                         "Au moins une copie des sauvegardes critiques doit être hors ligne ou immuable pendant une période de conservation définie."),
                "no": V("Offline or immutable backup copies are not required; the residual ransomware risk is accepted by the business owners concerned.",
                        "Des copies de sauvegarde hors ligne ou immuables ne sont pas exigées; le risque résiduel de rançongiciel est accepté par les responsables d’affaires concernés."),
                "_none": V("[DECISION: Whether at least one copy of critical backups must be offline or immutable.]",
                           "[DÉCISION : Si au moins une copie des sauvegardes critiques doit être hors ligne ou immuable.]")}),
            C("BK04", "Backup retention must meet the records retention schedule and legal holds, and backups must be destroyed securely at the end of retention.",
              "La conservation des sauvegardes doit respecter le calendrier de conservation et les mises en suspens juridiques, et les sauvegardes doivent être détruites de façon sécuritaire à la fin de la conservation.", legal=True),
        ]),
        S("SEC-REQ-TEST", "Restoration testing", "Tests de restauration", [
            C("TS01", by="DEC-BKP-TEST", src="decision", variants={
                "quarterly": V("Restoration must be tested at least quarterly for a sample of critical systems, and each critical system at least once a year; results are recorded and failures corrected.",
                               "La restauration doit être testée au moins une fois par trimestre pour un échantillon de systèmes critiques, et chaque système critique au moins une fois par année; les résultats sont consignés et les échecs corrigés."),
                "semiannual": V("Restoration must be tested every six months for critical systems; results are recorded and failures corrected.",
                                "La restauration doit être testée tous les six mois pour les systèmes critiques; les résultats sont consignés et les échecs corrigés."),
                "annual": V("Restoration must be tested at least annually for each critical system; results are recorded and failures corrected.",
                            "La restauration doit être testée au moins une fois par année pour chaque système critique; les résultats sont consignés et les échecs corrigés."),
                "_none": V("Restoration must be tested [DECISION: restoration test frequency]; results are recorded and failures corrected.",
                           "La restauration doit être testée [DÉCISION : fréquence des tests de restauration]; les résultats sont consignés et les échecs corrigés.")},
              refs=["ISO 27002:2022 8.13", "NIST CSF 2.0 RC.RP"],
              gap=("TECH-07", ["no", "partial"], V("Restoration testing is not yet performed.", "Les tests de restauration ne sont pas encore effectués."))),
            C("TS02", "Recovery procedures for critical services must be documented and kept current so that someone other than the usual administrator can perform them.",
              "Les procédures de rétablissement des services essentiels doivent être documentées et tenues à jour afin qu’une personne autre que l’administrateur habituel puisse les exécuter.", refs=["ISO 27002:2022 5.37"]),
        ]),
    ],
)

# ------------------------------------------------------------------ Third parties
TPRM = topic_frame(
    purpose=[C("P01", "This policy ensures that suppliers, service providers and partners who access, process or support {org}’s information or critical services protect them to the level {org} requires, throughout the relationship and at its end.",
               "La présente politique assure que les fournisseurs, prestataires et partenaires qui accèdent à l’information de {org}, la traitent ou soutiennent ses services essentiels les protègent au niveau exigé par {org}, tout au long de la relation et à sa fin.", mod="info")],
    scope_extra=[C("SC03", "It covers cloud and software-as-a-service providers, managed service providers, outsourced developers, consultants and any subcontractors they use.",
                   "Elle vise les fournisseurs infonuagiques et SaaS, les fournisseurs de services gérés, les développeurs impartis, les consultants et les sous-traitants auxquels ils ont recours.", mod="info")],
    roles=[
        C("R01", "The business owner of each supplier relationship accepts its risks and ensures the supplier meets this policy.", "Le responsable d’affaires de chaque relation avec un fournisseur en accepte les risques et s’assure que le fournisseur respecte la présente politique."),
        C("R02", "Procurement ensures that the process is followed before any commitment.", "L’approvisionnement s’assure que le processus est suivi avant tout engagement."),
        C("R03", "{sec} sets the security requirements by tier and assesses suppliers.", "{sec} fixe les exigences de sécurité par catégorie et évalue les fournisseurs."),
        C("R04", "Legal counsel ensures that contracts make the requirements enforceable.", "Le conseiller juridique s’assure que les contrats rendent les exigences exécutoires.",
          when=lambda p: p.has("ORG-13", "legal") or p.value("REG-10") == "yes"),
        C("R05", "{Privacy} reviews arrangements involving personal information.", "{Privacy} examine les ententes qui touchent des renseignements personnels.", when=lambda p: p.handles_pi),
    ],
    requirements=[
        S("SEC-REQ-TIER", "Inventory and tiering", "Inventaire et catégorisation", [
            C("TI01", "{org} must keep an inventory of suppliers that access its information or support its services, with the business owner, the services provided, the data involved and the tier.",
              "{org} doit tenir un inventaire des fournisseurs qui accèdent à son information ou soutiennent ses services, indiquant le responsable d’affaires, les services fournis, les données en cause et la catégorie.",
              refs=["ISO 27002:2022 5.19", "NIST CSF 2.0 GV.SC"]),
            C("TI02", "Suppliers are tiered according to the sensitivity of the data they handle, the criticality of the service, their level of access and how easily they can be replaced. The tier determines the depth of assessment and the contractual requirements.",
              "Les fournisseurs sont catégorisés selon la sensibilité des données qu’ils traitent, la criticité du service, leur niveau d’accès et la facilité de les remplacer. La catégorie détermine la profondeur de l’évaluation et les exigences contractuelles.",
              refs=["ISO 27002:2022 5.19"]),
        ]),
        S("SEC-REQ-DUE", "Due diligence and contracts", "Vérification et contrats", [
            C("DU01", "Before contracting, suppliers in the higher tiers must be assessed by {sec} using questionnaires, independent assurance reports (such as ISO/IEC 27001 certification or SOC 2 reports) or other evidence proportionate to the risk.",
              "Avant la conclusion du contrat, les fournisseurs des catégories supérieures doivent être évalués par {sec} au moyen de questionnaires, de rapports d’assurance indépendants (comme une certification ISO/IEC 27001 ou un rapport SOC 2) ou d’autres preuves proportionnées au risque.",
              refs=["ISO 27002:2022 5.19", "ISO 27002:2022 5.21"]),
            C("DU02", "Contracts must include, as applicable: security and confidentiality obligations; incident notification; right to audit or obtain assurance; restrictions on subcontracting; data location; return and destruction of data at the end of the contract; and remedies for non-compliance.",
              "Les contrats doivent prévoir, selon le cas : des obligations de sécurité et de confidentialité; la notification des incidents; un droit d’audit ou d’obtention d’assurance; des restrictions à la sous-traitance; l’emplacement des données; la restitution et la destruction des données à la fin du contrat; des recours en cas de manquement.",
              refs=["ISO 27002:2022 5.20"], legal=True),
            C("DU03", by="DEC-TP-NOTIFY", src="decision", variants={
                "24": V("Contracts must require suppliers to notify {org} of any security incident affecting its information or services within 24 hours of discovery.",
                        "Les contrats doivent obliger les fournisseurs à aviser {org} de tout incident de sécurité touchant son information ou ses services dans les 24 heures suivant sa découverte."),
                "48": V("Contracts must require suppliers to notify {org} of any security incident affecting its information or services within 48 hours of discovery.",
                        "Les contrats doivent obliger les fournisseurs à aviser {org} de tout incident de sécurité touchant son information ou ses services dans les 48 heures suivant sa découverte."),
                "72": V("Contracts must require suppliers to notify {org} of any security incident affecting its information or services within 72 hours of discovery.",
                        "Les contrats doivent obliger les fournisseurs à aviser {org} de tout incident de sécurité touchant son information ou ses services dans les 72 heures suivant sa découverte."),
                "_none": V("Contracts must require suppliers to notify {org} of security incidents within [DECISION: supplier incident notification deadline].",
                           "Les contrats doivent obliger les fournisseurs à aviser {org} des incidents de sécurité dans un délai de [DÉCISION : délai de notification des incidents par les fournisseurs].")}),
            C("DU04", "Before personal information is communicated outside Quebec, a privacy impact assessment must be performed and a written agreement must provide the required protections.",
              "Avant que des renseignements personnels ne soient communiqués à l’extérieur du Québec, une évaluation des facteurs relatifs à la vie privée doit être effectuée et une entente écrite doit prévoir les protections requises.",
              src="obligation", obligation="QC-P39.1", legal=True),
        ]),
        S("SEC-REQ-MONITOR", "Monitoring and exit", "Suivi et sortie", [
            C("MN01", by="DEC-TP-REASSESS", src="decision", variants={
                "annual": V("Critical suppliers must be reassessed at least annually and whenever their service, ownership or security posture changes significantly.",
                            "Les fournisseurs critiques doivent être réévalués au moins une fois par année et chaque fois que leur service, leur propriété ou leur posture de sécurité change de façon importante."),
                "biennial": V("Critical suppliers must be reassessed at least every two years and whenever their service, ownership or security posture changes significantly.",
                              "Les fournisseurs critiques doivent être réévalués au moins tous les deux ans et chaque fois que leur service, leur propriété ou leur posture de sécurité change de façon importante."),
                "_none": V("Critical suppliers must be reassessed [DECISION: reassessment frequency].", "Les fournisseurs critiques doivent être réévalués [DÉCISION : fréquence de réévaluation].")},
              refs=["ISO 27002:2022 5.22", "NIST CSF 2.0 GV.SC"]),
            C("MN02", "Supplier access to {org} systems must follow the identity and access management policy and be logged.",
              "L’accès des fournisseurs aux systèmes de {org} doit respecter la politique de gestion des identités et des accès et être journalisé."),
            C("MN03", "For critical suppliers, an exit plan must describe how {org} would recover its data and continue the service if the relationship ended.",
              "Pour les fournisseurs critiques, un plan de sortie doit décrire comment {org} récupérerait ses données et poursuivrait le service si la relation prenait fin.", mod="should"),
            C("MN04", "The managed service provider that operates {org}’s IT is a critical supplier: its privileged access must be individually attributable, protected by multi-factor authentication and reviewed.",
              "Le fournisseur de services gérés qui exploite les TI de {org} est un fournisseur critique : ses accès privilégiés doivent être attribuables individuellement, protégés par authentification multifacteur et revus.",
              src="answer", inputs=["ORG-13"], when=has("ORG-13", "msp")),
        ]),
    ],
)

# ------------------------------------------------------------------ Vulnerability, patch and change management
VULN = topic_frame(
    purpose=[C("P01", "This policy ensures that {org} knows its technology assets, keeps them securely configured and up to date, remediates vulnerabilities within defined timeframes and controls changes to production.",
               "La présente politique assure que {org} connaît ses actifs technologiques, les maintient configurés de façon sécuritaire et à jour, corrige les vulnérabilités dans des délais définis et contrôle les changements en production.", mod="info")],
    scope_extra=[],
    roles=[
        C("R01", "System owners ensure their systems are inventoried, maintained and remediated, and accept the risk of any delay.", "Les responsables des systèmes s’assurent que leurs systèmes sont inventoriés, maintenus et corrigés, et acceptent le risque de tout retard."),
        C("R02", "IT operations applies patches and configurations and performs approved changes.", "L’exploitation des TI applique les correctifs et configurations et effectue les changements approuvés."),
        C("R03", "{sec} runs vulnerability scanning, rates vulnerabilities and tracks remediation.", "{sec} effectue le balayage des vulnérabilités, les évalue et suit leur correction."),
    ],
    requirements=[
        S("SEC-REQ-ASSETS", "Asset inventory and configuration", "Inventaire des actifs et configuration", [
            C("AS01", "{org} must maintain an inventory of hardware, software, cloud services and data stores, each with an owner and a criticality rating.",
              "{org} doit tenir un inventaire du matériel, des logiciels, des services infonuagiques et des dépôts de données, chacun avec un responsable et une cote de criticité.", refs=["ISO 27002:2022 5.9", "NIST CSF 2.0 ID.AM", "CIS v8.1 1", "CIS v8.1 2"]),
            C("AS02", "Systems must be deployed from secure configuration baselines approved by {sec}; deviations require an exception.",
              "Les systèmes doivent être déployés à partir de configurations de référence sécuritaires approuvées par {sec}; tout écart exige une dérogation.", refs=["ISO 27002:2022 8.9", "CIS v8.1 4"]),
            C("AS03", "Software and systems no longer supported by their vendor must be replaced, isolated or covered by an approved exception with compensating controls.",
              "Les logiciels et systèmes qui ne sont plus pris en charge par leur fournisseur doivent être remplacés, isolés ou couverts par une dérogation approuvée assortie de mesures compensatoires.", refs=["ISO 27002:2022 8.8"]),
            C("AS04", "Anti-malware protection must be active and kept up to date on all endpoints and servers that support it.",
              "Une protection contre les logiciels malveillants doit être active et tenue à jour sur tous les terminaux et serveurs qui la permettent.", refs=["ISO 27002:2022 8.7"]),
        ]),
        S("SEC-REQ-VULN", "Vulnerability management", "Gestion des vulnérabilités", [
            C("VU01", by="DEC-VULN-SCAN", src="decision", variants={
                "weekly": V("Systems must be scanned for vulnerabilities at least weekly, and internet-facing systems also after significant changes.",
                            "Les systèmes doivent faire l’objet d’un balayage des vulnérabilités au moins une fois par semaine, et les systèmes exposés à Internet aussi après un changement important."),
                "monthly": V("Systems must be scanned for vulnerabilities at least monthly, and internet-facing systems also after significant changes.",
                             "Les systèmes doivent faire l’objet d’un balayage des vulnérabilités au moins une fois par mois, et les systèmes exposés à Internet aussi après un changement important."),
                "quarterly": V("Systems must be scanned for vulnerabilities at least quarterly, and internet-facing systems also after significant changes.",
                               "Les systèmes doivent faire l’objet d’un balayage des vulnérabilités au moins une fois par trimestre, et les systèmes exposés à Internet aussi après un changement important."),
                "_none": V("Systems must be scanned for vulnerabilities [DECISION: scanning frequency].", "Les systèmes doivent faire l’objet d’un balayage des vulnérabilités [DÉCISION : fréquence du balayage].")},
              refs=["ISO 27002:2022 8.8", "NIST CSF 2.0 ID.RA", "CIS v8.1 7"],
              gap=("TECH-08", lambda p: p.answered("TECH-08") and not p.has("TECH-08", "vuln_scan"), V("Vulnerability scanning is not yet in place.", "Le balayage des vulnérabilités n’est pas encore en place."))),
            C("VU02", "Vulnerabilities are rated using CVSS v4.0 and adjusted for exposure, asset criticality and evidence of active exploitation.",
              "Les vulnérabilités sont cotées selon CVSS v4.0 et ajustées selon l’exposition, la criticité de l’actif et les preuves d’exploitation active.", refs=["ISO 27002:2022 8.8"]),
            C("VU03", "Remediation timeframes, measured from the availability of a fix: critical — {p:DEC-VULN-CRIT}; high — {p:DEC-VULN-HIGH}; medium and low — at the next scheduled maintenance. Vulnerabilities known to be actively exploited must be remediated or mitigated as a priority, ahead of these timeframes.",
              "Délais de correction, mesurés à partir de la disponibilité d’un correctif : critique — {p:DEC-VULN-CRIT}; élevée — {p:DEC-VULN-HIGH}; moyenne et faible — au prochain entretien planifié. Les vulnérabilités dont l’exploitation active est connue doivent être corrigées ou atténuées en priorité, avant ces délais.",
              src="decision", inputs=["DEC-VULN-CRIT", "DEC-VULN-HIGH"], refs=["ISO 27002:2022 8.8", "CIS v8.1 7"]),
            C("VU04", "A remediation that cannot meet its timeframe requires a documented risk acceptance or exception by the system owner.",
              "Une correction qui ne peut respecter son délai exige une acceptation du risque ou une dérogation documentée par le responsable du système."),
        ]),
        S("SEC-REQ-CHANGE", "Change management", "Gestion des changements", [
            C("CH01", "Changes to production systems must be recorded, assessed for security and business impact, approved by the system owner or the change authority, tested and reversible.",
              "Les changements aux systèmes de production doivent être consignés, évalués quant à leur incidence sur la sécurité et les activités, approuvés par le responsable du système ou l’autorité de changement, testés et réversibles.",
              refs=["ISO 27002:2022 8.32", "NIST CSF 2.0 PR.PS"]),
            C("CH02", "Emergency changes may be made to restore service or address a security threat, provided they are documented and approved retrospectively within [VALUE: number of working days].",
              "Des changements d’urgence peuvent être effectués pour rétablir un service ou contrer une menace, pourvu qu’ils soient documentés et approuvés a posteriori dans un délai de [VALEUR : nombre de jours ouvrables].", mod="may"),
            C("CH03", "The person who develops or requests a change should not be the only person who approves and deploys it to production.",
              "La personne qui développe ou demande un changement ne devrait pas être la seule à l’approuver et à le déployer en production.", mod="should", refs=["ISO 27002:2022 5.3"]),
        ]),
    ],
)

# ------------------------------------------------------------------ Remote work and mobile devices
REMOTE = topic_frame(
    purpose=[C("P01", "This policy protects {org}’s information when people work outside its premises or use mobile devices, including, where permitted, personal devices.",
               "La présente politique protège l’information de {org} lorsque des personnes travaillent hors de ses locaux ou utilisent des appareils mobiles, y compris, lorsque c’est permis, des appareils personnels.", mod="info")],
    scope_extra=[],
    roles=[
        C("R01", "Managers authorize remote work arrangements for their staff.", "Les gestionnaires autorisent les modalités de télétravail de leur personnel."),
        C("R02", "IT provides and manages secure remote access and device management.", "Les TI fournissent et gèrent un accès à distance et une gestion des appareils sécuritaires."),
        C("R03", "Users protect devices and information wherever they work.", "Les utilisateurs protègent les appareils et l’information où qu’ils travaillent."),
    ],
    requirements=[
        S("SEC-REQ-REMOTE", "Remote work", "Télétravail", [
            C("RW01", by="DEC-REM-NETWORK", src="decision", variants={
                "vpn": V("Remote access to {org} systems must use the organization’s VPN or another secure access service approved by {sec}, with multi-factor authentication.",
                         "L’accès à distance aux systèmes de {org} doit passer par le RPV de l’organisation ou un autre service d’accès sécurisé approuvé par {sec}, avec authentification multifacteur."),
                "mfa_cloud": V("Remote users may access approved cloud services directly over the internet with multi-factor authentication; access to internal systems must use a secure access service approved by {sec}.",
                               "Les utilisateurs à distance peuvent accéder directement aux services infonuagiques approuvés par Internet avec authentification multifacteur; l’accès aux systèmes internes doit passer par un service d’accès sécurisé approuvé par {sec}."),
                "_none": V("Remote access must use [DECISION: approved remote-access method] with multi-factor authentication.",
                           "L’accès à distance doit utiliser [DÉCISION : méthode d’accès à distance approuvée] avec authentification multifacteur.")},
              refs=["ISO 27002:2022 6.7", "NIST CSF 2.0 PR.AA"]),
            C("RW02", "Users must work in a setting where confidential information cannot be seen or overheard by others, and must not leave devices unattended in public places or vehicles.",
              "Les utilisateurs doivent travailler dans un lieu où l’information confidentielle ne peut être vue ou entendue par d’autres et ne doivent pas laisser d’appareil sans surveillance dans un lieu public ou un véhicule.", refs=["ISO 27002:2022 6.7"]),
            C("RW03", "Paper documents classified Confidential or above must not be printed at home unless authorized, and must be returned or shredded securely.",
              "Les documents papier classifiés Confidentiel ou plus ne doivent pas être imprimés à domicile sans autorisation et doivent être rapportés ou déchiquetés de façon sécuritaire.", mod="must not"),
            C("RW04", "Travelling abroad with devices that contain {org} information requires prior approval by {sec} when the destination presents elevated risk.",
              "Voyager à l’étranger avec des appareils contenant de l’information de {org} exige l’autorisation préalable de {sec} lorsque la destination présente un risque élevé.", mod="should"),
        ]),
        S("SEC-REQ-DEVICES", "Organization devices", "Appareils de l’organisation", [
            C("MD01", "Laptops and mobile devices provided by {org} must have full-disk encryption, a screen lock, current security updates and endpoint protection, and must be manageable and remotely wipeable by IT.",
              "Les ordinateurs portables et appareils mobiles fournis par {org} doivent être dotés d’un chiffrement complet du disque, d’un verrouillage d’écran, des mises à jour de sécurité courantes et d’une protection des terminaux, et doivent pouvoir être gérés et effacés à distance par les TI.",
              refs=["ISO 27002:2022 8.1", "CIS v8.1 4"]),
        ]),
        S("SEC-REQ-BYOD", "Personal devices", "Appareils personnels", [
            C("BY01", "Personal devices must not be used to access {org} email, systems or data.",
              "Les appareils personnels ne doivent pas être utilisés pour accéder au courriel, aux systèmes ou aux données de {org}.",
              mod="must not", src="answer", inputs=["TECH-02B"], when=lambda p: p.value("TECH-02B") == "no"),
            C("BY02", by="DEC-REM-BYOD-MDM", src="decision", legal=True, when=lambda p: p.value("TECH-02B") in ("limited", "yes"), variants={
                "mdm": V("Personal devices may access {org} information only after enrolment in {org}’s device management, which enforces encryption, screen lock and current operating systems and allows {org} data to be removed. Users are informed of what the management tool can and cannot see.",
                         "Les appareils personnels ne peuvent accéder à l’information de {org} qu’après inscription à la gestion des appareils de {org}, qui impose le chiffrement, le verrouillage et un système d’exploitation à jour et permet de retirer les données de {org}. Les utilisateurs sont informés de ce que l’outil de gestion peut voir ou non."),
                "app_only": V("Personal devices may access {org} information only through approved applications that keep {org} data separate and removable, on a device with a screen lock and a supported, up-to-date operating system.",
                              "Les appareils personnels ne peuvent accéder à l’information de {org} qu’au moyen d’applications approuvées qui gardent les données de {org} séparées et effaçables, sur un appareil doté d’un verrouillage d’écran et d’un système d’exploitation pris en charge et à jour."),
                "_none": V("Personal devices may access {org} information only under [DECISION: conditions for personal-device access].",
                           "Les appareils personnels ne peuvent accéder à l’information de {org} qu’aux conditions suivantes : [DÉCISION : conditions d’accès des appareils personnels].")}),
            C("BY03", "Information classified {class_top} must not be stored on personal devices.",
              "L’information classifiée {class_top} ne doit pas être stockée sur des appareils personnels.",
              mod="must not", when=lambda p: p.value("TECH-02B") in ("limited", "yes")),
        ]),
    ],
)
