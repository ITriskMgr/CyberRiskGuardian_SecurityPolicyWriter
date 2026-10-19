"""Topic-policy clause libraries: Personal information, AI use, Secure development, Logging, OT security."""
from .common import C, S, V, topic_frame

has = lambda code, *v: (lambda p: p.has(code, *v))  # noqa: E731
QC = "QC-P39.1"

# ------------------------------------------------------------------ Personal information protection
PRIV = topic_frame(
    purpose=[C("P01", "This policy sets how {org} protects the personal information it collects, uses, communicates, keeps and destroys, and how it governs privacy. It complements the information security policies, which protect the same information against security threats.",
               "La présente politique établit comment {org} protège les renseignements personnels qu’elle recueille, utilise, communique, conserve et détruit, et comment elle encadre la protection de la vie privée. Elle complète les politiques de sécurité de l’information, qui protègent ces mêmes renseignements contre les menaces.", mod="info")],
    scope_extra=[C("SC03", "Personal information means any information about an identifiable individual, in any form. The categories held by {org} include: {pi_categories}.",
                   "Un renseignement personnel est tout renseignement qui concerne une personne physique et permet de l’identifier, quelle que soit sa forme. Les catégories détenues par {org} comprennent : {pi_categories}.",
                   mod="info", src="answer", inputs=["DATA-01"])],
    roles=[
        C("R01", "{Privacy} is responsible for the protection of personal information within {org}: approves privacy practices, oversees privacy impact assessments, handles requests and complaints, and manages confidentiality incidents.",
          "{Privacy} est responsable de la protection des renseignements personnels au sein de {org} : approuve les pratiques, supervise les évaluations des facteurs relatifs à la vie privée, traite les demandes et les plaintes et gère les incidents de confidentialité.",
          src="answer", inputs=["DATA-08"]),
        C("R02", "Business owners are accountable for the personal information in their processes and systems.", "Les responsables d’affaires sont imputables des renseignements personnels de leurs processus et systèmes."),
        C("R03", "{sec} provides the security safeguards and supports incident handling.", "{sec} fournit les mesures de sécurité et soutient la gestion des incidents."),
        C("R04", "Legal counsel interprets legal obligations and confirms which laws apply.", "Le conseiller juridique interprète les obligations légales et confirme les lois applicables.", legal=True),
    ],
    requirements=[
        S("SEC-REQ-PRINCIPLES", "Principles", "Principes", [
            C("PP01", "{org} collects only the personal information necessary for identified purposes, informs individuals of those purposes, and obtains consent where it is required.",
              "{org} ne recueille que les renseignements personnels nécessaires aux fins déterminées, informe les personnes de ces fins et obtient leur consentement lorsqu’il est requis.", legal=True, refs=["ISO 27002:2022 5.34"]),
            C("PP02", "Personal information is used and communicated only for the purposes for which it was collected, unless the individual consents or the law permits otherwise.",
              "Les renseignements personnels ne sont utilisés et communiqués qu’aux fins pour lesquelles ils ont été recueillis, sauf consentement de la personne ou autorisation de la loi.", legal=True),
            C("PP03", "Access to personal information is limited to persons who need it for their duties, according to the identity and access management policy.",
              "L’accès aux renseignements personnels est limité aux personnes qui en ont besoin dans l’exercice de leurs fonctions, conformément à la politique de gestion des identités et des accès.", refs=["ISO 27002:2022 5.15"]),
            C("PP04", "Personal information is kept accurate, kept only as long as necessary, and then destroyed or anonymized according to the retention schedule.",
              "Les renseignements personnels sont tenus exacts, conservés seulement le temps nécessaire, puis détruits ou anonymisés selon le calendrier de conservation.", legal=True),
            C("PP05", "Individuals can request access to and correction of their personal information through the contact published by {org}.",
              "Les personnes peuvent demander l’accès à leurs renseignements personnels et leur rectification par l’intermédiaire des coordonnées publiées par {org}.", legal=True),
        ]),
        S("SEC-REQ-GOV", "Privacy governance", "Gouvernance de la vie privée", [
            C("GG01", "The title and contact information of the person in charge of the protection of personal information are published on {org}’s website, together with governance rules on personal information written in clear terms.",
              "Le titre et les coordonnées de la personne responsable de la protection des renseignements personnels sont publiés sur le site Web de {org}, avec des règles de gouvernance sur les renseignements personnels rédigées en termes clairs.",
              src="obligation", obligation=QC, legal=True),
            C("GG02", by="DEC-PRIV-PIA", src="decision", legal=True, variants={
                "projects": V("A privacy impact assessment must be carried out for any project to acquire, develop or overhaul an information system or electronic service delivery system involving personal information, and before personal information is communicated outside the jurisdiction where required.",
                              "Une évaluation des facteurs relatifs à la vie privée doit être réalisée pour tout projet d’acquisition, de développement ou de refonte d’un système d’information ou de prestation électronique de services impliquant des renseignements personnels, et avant toute communication de renseignements personnels hors du territoire lorsque c’est exigé."),
                "high_risk": V("A privacy impact assessment must be carried out for processing of personal information that presents a high risk to individuals.",
                               "Une évaluation des facteurs relatifs à la vie privée doit être réalisée pour tout traitement de renseignements personnels présentant un risque élevé pour les personnes."),
                "_none": V("A privacy impact assessment must be carried out [DECISION: when a privacy impact assessment is required — legal review].",
                           "Une évaluation des facteurs relatifs à la vie privée doit être réalisée [DÉCISION : quand une évaluation est exigée — révision juridique].")}),
            C("GG03", "Technology products and services offered to the public that collect personal information must have the highest privacy settings enabled by default, without any intervention by the individual.",
              "Les produits et services technologiques offerts au public qui recueillent des renseignements personnels doivent offrir par défaut le plus haut niveau de confidentialité, sans aucune intervention de la personne.",
              src="obligation", obligation=QC, legal=True),
            C("GG04", "Individuals must be informed when a decision about them is based exclusively on automated processing of their personal information.",
              "Les personnes doivent être informées lorsqu’une décision les concernant est fondée exclusivement sur un traitement automatisé de leurs renseignements personnels.",
              src="obligation", obligation=QC, legal=True, when=has("DATA-06", "profiling", "ai_products")),
        ]),
        S("SEC-REQ-INCIDENTS", "Confidentiality incidents", "Incidents de confidentialité", [
            C("CI01", "Any loss of, unauthorized access to, or unauthorized use or communication of personal information must be reported immediately according to the incident management policy and assessed by {privacy}.",
              "Toute perte de renseignements personnels, ou tout accès, utilisation ou communication non autorisés de ceux-ci, doit être signalé immédiatement conformément à la politique de gestion des incidents et évalué par {privacy}.",
              refs=["ISO 27002:2022 5.34"]),
            C("CI02", "{org} keeps a register of confidentiality incidents and, when an incident presents a risk of serious injury, notifies the regulator and the persons concerned as required by law.",
              "{org} tient un registre des incidents de confidentialité et, lorsqu’un incident présente un risque de préjudice sérieux, avise le régulateur et les personnes concernées comme l’exige la loi.",
              src="obligation", obligation=QC, legal=True),
            C("CI03", "[SOURCE: Breach notification requirements of each law confirmed as applicable, with thresholds and deadlines, as confirmed by legal review.]",
              "[SOURCE : Exigences de notification des atteintes de chaque loi dont l’applicabilité est confirmée, avec seuils et délais, telles que confirmées par la révision juridique.]",
              legal=True),
        ]),
    ],
)

# ------------------------------------------------------------------ AI acceptable and secure use
AI = topic_frame(
    purpose=[C("P01", "This policy allows {org} to benefit from artificial intelligence while protecting its information, the people it serves and its reputation. Accountability for decisions and outputs always remains with people.",
               "La présente politique permet à {org} de tirer parti de l’intelligence artificielle tout en protégeant son information, les personnes qu’elle sert et sa réputation. La responsabilité des décisions et des résultats demeure toujours humaine.", mod="info")],
    scope_extra=[C("SC03", "It covers generative AI tools used by staff, AI features embedded in software and services, and AI systems developed or deployed by {org}.",
                   "Elle vise les outils d’IA générative utilisés par le personnel, les fonctions d’IA intégrées aux logiciels et services ainsi que les systèmes d’IA développés ou déployés par {org}.", mod="info")],
    roles=[
        C("R01", "Each AI system or approved use case has a business owner (intended use and risk acceptance) and a technical owner.", "Chaque système d’IA ou cas d’utilisation approuvé a un responsable d’affaires (usage prévu et acceptation du risque) et un responsable technique."),
        C("R02", "{sec}, with {privacy} where personal information is involved, assesses AI tools and use cases before approval.", "{sec}, avec {privacy} lorsque des renseignements personnels sont en cause, évalue les outils et cas d’utilisation d’IA avant leur approbation."),
        C("R03", "Users remain responsible for the work they produce with AI assistance.", "Les utilisateurs demeurent responsables du travail qu’ils produisent avec l’aide de l’IA."),
    ],
    requirements=[
        S("SEC-REQ-TOOLS", "Approved tools", "Outils approuvés", [
            C("TL01", by="DEC-AI-TOOLS", src="decision", variants={
                "approved_list": V("Staff may use only AI tools on the list approved by {sec}. Using other AI tools for {org} work is prohibited.",
                                   "Le personnel ne peut utiliser que les outils d’IA figurant sur la liste approuvée par {sec}. L’utilisation d’autres outils d’IA pour le travail de {org} est interdite."),
                "enterprise": V("Staff may use only AI tools licensed by {org} under an enterprise agreement; personal or consumer accounts must not be used for {org} work.",
                                "Le personnel ne peut utiliser que des outils d’IA dont {org} détient une licence d’entreprise; les comptes personnels ou grand public ne doivent pas être utilisés pour le travail de {org}."),
                "none": V("Until a decision is made by {committee}, AI tools must not be used for {org} work.",
                          "Tant qu’une décision n’est pas prise par {committee}, les outils d’IA ne doivent pas être utilisés pour le travail de {org}."),
                "_none": V("Staff may use [DECISION: which AI tools are permitted].", "Le personnel peut utiliser [DÉCISION : outils d’IA permis].")},
              refs=["ISO 27002:2022 5.10"]),
            C("TL02", "Before approval, AI tools are assessed for data retention, use of inputs for training, data location, access controls, contractual terms and security of integrations.",
              "Avant leur approbation, les outils d’IA sont évalués quant à la conservation des données, à l’utilisation des entrées pour l’entraînement, à l’emplacement des données, aux contrôles d’accès, aux conditions contractuelles et à la sécurité des intégrations.",
              refs=["ISO 27002:2022 5.19", "ISO 27002:2022 5.23"]),
        ]),
        S("SEC-REQ-DATA", "Information entered into AI tools", "Information saisie dans les outils d’IA", [
            C("DT01", by="DEC-AI-DATA", src="decision", variants={
                "public": V("Only information classified Public may be entered into AI tools.", "Seule l’information classifiée Public peut être saisie dans les outils d’IA."),
                "internal": V("Information classified above Internal, including personal information and client confidential information, must not be entered into AI tools.",
                              "L’information classifiée au-delà d’Interne, y compris les renseignements personnels et l’information confidentielle des clients, ne doit pas être saisie dans les outils d’IA."),
                "confidential": V("Information up to Confidential may be entered only into approved enterprise AI tools whose contract prevents training on {org} data; information classified {class_top} must not be entered.",
                                  "L’information jusqu’à Confidentiel ne peut être saisie que dans des outils d’IA d’entreprise approuvés dont le contrat interdit l’entraînement sur les données de {org}; l’information classifiée {class_top} ne doit pas y être saisie."),
                "_none": V("Information above [DECISION: highest classification allowed in AI tools] must not be entered into AI tools.",
                           "L’information au-delà de [DÉCISION : classification la plus élevée permise dans les outils d’IA] ne doit pas être saisie dans les outils d’IA.")},
              refs=["ISO 27002:2022 5.12"]),
            C("DT02", "Content from untrusted sources processed by AI tools (documents, web pages, emails) must be treated as data, never as instructions to perform actions with {org} privileges.",
              "Le contenu de sources non fiables traité par des outils d’IA (documents, pages Web, courriels) doit être traité comme des données, jamais comme des instructions d’exécuter des actions avec les privilèges de {org}."),
        ]),
        S("SEC-REQ-OUTPUT", "Human oversight and outputs", "Supervision humaine et résultats", [
            C("OU01", "AI outputs must be reviewed by a competent person before being relied on, published, sent to clients or used in decisions; users must check facts, sources and code.",
              "Les résultats de l’IA doivent être revus par une personne compétente avant qu’on s’y fie, qu’on les publie, qu’on les transmette aux clients ou qu’on les utilise dans des décisions; les utilisateurs doivent vérifier les faits, les sources et le code."),
            C("OU02", "AI must not be the sole basis of a decision that significantly affects an individual unless approved through a privacy impact assessment and disclosed as required by law.",
              "L’IA ne doit pas être le seul fondement d’une décision ayant une incidence importante sur une personne, sauf approbation au terme d’une évaluation des facteurs relatifs à la vie privée et divulgation comme l’exige la loi.",
              mod="must not", legal=True),
            C("OU03", "Content substantially generated by AI should be identified as such when shared outside {org} or when the audience could be misled.",
              "Le contenu substantiellement généré par l’IA devrait être signalé comme tel lorsqu’il est communiqué hors de {org} ou lorsque le public pourrait être induit en erreur.", mod="should"),
        ]),
        S("SEC-REQ-INVENTORY", "Inventory of AI systems", "Inventaire des systèmes d’IA", [
            C("IV01", "{org} keeps an inventory of approved AI tools and use cases, with their owners, purpose, data used, users and risk level. Use cases involving personal information, decisions about individuals, financial workflows or autonomous actions are rated high risk and require approval by {committee}.",
              "{org} tient un inventaire des outils et cas d’utilisation d’IA approuvés, avec leurs responsables, leur finalité, les données utilisées, les utilisateurs et le niveau de risque. Les cas impliquant des renseignements personnels, des décisions concernant des personnes, des processus financiers ou des actions autonomes sont jugés à risque élevé et exigent l’approbation de {committee}."),
        ]),
    ],
)

# ------------------------------------------------------------------ Secure development
SDLC = topic_frame(
    purpose=[C("P01", "This policy ensures that software developed, configured or commissioned by {org} is designed, built, tested and released securely.",
               "La présente politique assure que les logiciels développés, configurés ou commandés par {org} sont conçus, construits, testés et mis en production de façon sécuritaire.", mod="info")],
    scope_extra=[C("SC03", "It applies to internal developers, outsourced developers, scripts, integrations, infrastructure-as-code and low-code solutions.",
                   "Elle s’applique aux développeurs internes et impartis, aux scripts, aux intégrations, à l’infrastructure en tant que code et aux solutions à code réduit.", mod="info")],
    roles=[
        C("R01", "Product or system owners define security requirements with {sec} and accept residual risks before release.", "Les responsables de produits ou de systèmes définissent les exigences de sécurité avec {sec} et acceptent les risques résiduels avant la mise en production."),
        C("R02", "Developers apply secure coding practices and fix security defects.", "Les développeurs appliquent des pratiques de codage sécuritaire et corrigent les défauts de sécurité."),
        C("R03", "{sec} defines the secure development standard and reviews high-risk designs.", "{sec} définit la norme de développement sécuritaire et examine les conceptions à risque élevé."),
    ],
    requirements=[
        S("SEC-REQ-DESIGN", "Requirements and design", "Exigences et conception", [
            C("DS01", "Security and privacy requirements must be identified at the start of each project, and threat modelling must be performed for new systems and significant changes that handle Confidential information or are exposed to the internet.",
              "Les exigences de sécurité et de vie privée doivent être déterminées dès le début de chaque projet, et une modélisation des menaces doit être réalisée pour les nouveaux systèmes et les changements importants qui traitent de l’information Confidentielle ou sont exposés à Internet.",
              refs=["ISO 27002:2022 8.25", "ISO 27002:2022 8.26", "ISO 27002:2022 8.27"]),
            C("DS02", "Multi-tenant platforms must enforce and test isolation between customers’ data.",
              "Les plateformes multilocataires doivent imposer et tester l’isolement entre les données des clients.", src="answer", inputs=["IND-SAAS-01"], when=lambda p: p.value("IND-SAAS-01") == "yes"),
        ]),
        S("SEC-REQ-BUILD", "Build and review", "Construction et revue", [
            C("BD01", by="DEC-SDLC-REVIEW", src="decision", variants={
                "all": V("Every change to source code must be reviewed by a person other than its author before it is merged.",
                         "Tout changement au code source doit être revu par une personne autre que son auteur avant d’être intégré."),
                "risk": V("Changes to security-relevant or customer-facing code must be reviewed by a person other than its author before they are merged.",
                          "Les changements au code sensible pour la sécurité ou exposé aux clients doivent être revus par une personne autre que leur auteur avant d’être intégrés."),
                "_none": V("Code changes must be reviewed according to [DECISION: code review requirement].", "Les changements de code doivent être revus selon [DÉCISION : exigence de revue de code].")},
              refs=["ISO 27002:2022 8.28"]),
            C("BD02", "Secrets (passwords, keys, tokens) must not be stored in source code or configuration repositories; they must be kept in an approved secrets manager.",
              "Les secrets (mots de passe, clés, jetons) ne doivent pas être stockés dans le code source ou les dépôts de configuration; ils doivent être conservés dans un gestionnaire de secrets approuvé.", mod="must not", refs=["ISO 27002:2022 8.24", "ISO 27002:2022 8.28"]),
            C("BD03", "Third-party and open-source components must come from trusted sources, be inventoried, and be monitored for known vulnerabilities.",
              "Les composants tiers et à code source ouvert doivent provenir de sources fiables, être inventoriés et faire l’objet d’un suivi des vulnérabilités connues.", refs=["ISO 27002:2022 8.28", "NIST CSF 2.0 GV.SC"]),
            C("BD04", "Development, test and production environments must be separated; production personal or confidential data must not be used for testing unless masked or approved by the owner.",
              "Les environnements de développement, d’essai et de production doivent être séparés; les données personnelles ou confidentielles de production ne doivent pas servir aux essais sauf si elles sont masquées ou si le responsable l’approuve.", refs=["ISO 27002:2022 8.31", "ISO 27002:2022 8.33"]),
        ]),
        S("SEC-REQ-TEST", "Testing and release", "Essais et mise en production", [
            C("TS01", "Security testing proportionate to risk (automated code analysis, dependency scanning and, for high-risk systems, penetration testing) must be performed before release; high and critical findings must be fixed or formally accepted.",
              "Des essais de sécurité proportionnés au risque (analyse automatisée du code, analyse des dépendances et, pour les systèmes à risque élevé, tests d’intrusion) doivent être effectués avant la mise en production; les constats élevés et critiques doivent être corrigés ou formellement acceptés.",
              refs=["ISO 27002:2022 8.29"]),
            C("TS02", "Outsourced development contracts must impose the requirements of this policy and give {org} the right to verify them.",
              "Les contrats de développement imparti doivent imposer les exigences de la présente politique et donner à {org} le droit de les vérifier.", refs=["ISO 27002:2022 8.30"],
              when=lambda p: p.value("TECH-06") == "outsourced"),
        ]),
    ],
)

# ------------------------------------------------------------------ Logging and monitoring
LOG = topic_frame(
    purpose=[C("P01", "This policy ensures that {org} records the events needed to detect, investigate and learn from security incidents, and protects those records.",
               "La présente politique assure que {org} enregistre les événements nécessaires pour détecter les incidents de sécurité, enquêter et en tirer des leçons, et protège ces enregistrements.", mod="info")],
    scope_extra=[],
    roles=[
        C("R01", "System owners ensure their systems generate the required logs.", "Les responsables des systèmes s’assurent que leurs systèmes produisent les journaux requis."),
        C("R02", "{sec} defines log sources, reviews alerts and controls access to logs.", "{sec} définit les sources de journaux, examine les alertes et contrôle l’accès aux journaux."),
        C("R03", "{Privacy} is consulted on logs containing personal information and on monitoring of individuals.", "{Privacy} est consulté sur les journaux contenant des renseignements personnels et sur la surveillance de personnes.", when=lambda p: p.handles_pi),
    ],
    requirements=[
        S("SEC-REQ-EVENTS", "Events to log", "Événements à journaliser", [
            C("EV01", "Systems must log, at a minimum: authentication successes and failures; use of privileged accounts; changes to accounts, permissions and security settings; access to information classified {class_top}; and security alerts.",
              "Les systèmes doivent journaliser au minimum : les réussites et échecs d’authentification; l’utilisation des comptes privilégiés; les modifications aux comptes, permissions et paramètres de sécurité; l’accès à l’information classifiée {class_top}; les alertes de sécurité.",
              refs=["ISO 27002:2022 8.15", "NIST CSF 2.0 DE.CM", "CIS v8.1 8"]),
            C("EV02", "Each log entry must identify the user or system, the action, the time and the source; clocks must be synchronized to a common reference.",
              "Chaque entrée de journal doit identifier l’utilisateur ou le système, l’action, l’heure et la source; les horloges doivent être synchronisées sur une référence commune.", refs=["ISO 27002:2022 8.17"]),
        ]),
        S("SEC-REQ-PROTECT", "Protection and retention", "Protection et conservation", [
            C("PR01", "Logs must be protected against alteration and deletion, and access to them limited to authorized personnel.",
              "Les journaux doivent être protégés contre la modification et la suppression, et leur accès limité au personnel autorisé.", refs=["ISO 27002:2022 8.15"]),
            C("PR02", by="DEC-LOG-RETENTION", src="decision", legal=True, variants={
                "90": V("Security logs must be retained for at least 90 days, unless a longer period is required by law or contract.", "Les journaux de sécurité doivent être conservés au moins 90 jours, sauf si la loi ou un contrat exige une période plus longue."),
                "365": V("Security logs must be retained for at least one year, unless a longer period is required by law or contract.", "Les journaux de sécurité doivent être conservés au moins un an, sauf si la loi ou un contrat exige une période plus longue."),
                "730": V("Security logs must be retained for at least two years, unless a longer period is required by law or contract.", "Les journaux de sécurité doivent être conservés au moins deux ans, sauf si la loi ou un contrat exige une période plus longue."),
                "_none": V("Security logs must be retained for [DECISION: minimum log retention].", "Les journaux de sécurité doivent être conservés pendant [DÉCISION : durée minimale de conservation des journaux].")}),
        ]),
        S("SEC-REQ-REVIEW", "Monitoring and review", "Surveillance et revue", [
            C("MR01", "Logs from critical systems must be collected centrally and analysed for suspicious activity; alerts must be triaged according to the incident management policy.",
              "Les journaux des systèmes critiques doivent être centralisés et analysés pour détecter les activités suspectes; les alertes doivent être triées conformément à la politique de gestion des incidents.",
              refs=["ISO 27002:2022 8.16", "NIST CSF 2.0 DE.AE"],
              gap=("TECH-08", lambda p: p.answered("TECH-08") and not p.has("TECH-08", "siem", "soc"), V("Centralized log collection and analysis are not yet in place.", "La centralisation et l’analyse des journaux ne sont pas encore en place."))),
            C("MR02", "Monitoring is proportionate to its security purpose and complies with privacy law; it is not used to evaluate employee performance.",
              "La surveillance est proportionnée à sa finalité de sécurité et respecte les lois sur la vie privée; elle ne sert pas à évaluer le rendement des employés.", legal=True),
        ]),
    ],
)

# ------------------------------------------------------------------ OT security
OT = topic_frame(
    purpose=[C("P01", "This policy protects the industrial control and other cyber-physical systems of {org}. In these environments, the safety of people and the environment and the continuity of operations take precedence; security measures are designed so as not to compromise them.",
               "La présente politique protège les systèmes de contrôle industriels et autres systèmes cyberphysiques de {org}. Dans ces environnements, la sécurité des personnes et de l’environnement ainsi que la continuité des opérations ont préséance; les mesures de sécurité sont conçues pour ne pas les compromettre.", mod="info")],
    scope_extra=[],
    roles=[
        C("R01", "Operations and plant management own OT risks and approve changes affecting production or safety.", "La direction des opérations et des usines est propriétaire des risques TO et approuve les changements touchant la production ou la sécurité des personnes."),
        C("R02", "OT engineering maintains the OT asset inventory and implements controls.", "L’ingénierie TO tient l’inventaire des actifs TO et met en œuvre les mesures."),
        C("R03", "{sec} sets OT security requirements jointly with engineering and monitors their application.", "{sec} fixe les exigences de sécurité TO conjointement avec l’ingénierie et en suit l’application."),
        C("R04", "Procurement includes OT security requirements in purchases of equipment and services.", "L’approvisionnement intègre les exigences de sécurité TO aux achats d’équipements et de services."),
    ],
    requirements=[
        S("SEC-REQ-SEGMENT", "Inventory and segmentation", "Inventaire et segmentation", [
            C("SG01", "{org} must maintain an inventory of OT assets, including controllers, workstations, network devices and their firmware versions, with a criticality rating.",
              "{org} doit tenir un inventaire des actifs TO, y compris les automates, postes, équipements réseau et leurs versions de micrologiciel, avec une cote de criticité.", refs=["ISO 27002:2022 5.9", "NIST CSF 2.0 ID.AM"]),
            C("SG02", "OT networks must be separated from the corporate IT network, with only documented and approved flows through a controlled boundary.",
              "Les réseaux TO doivent être séparés du réseau TI de l’entreprise, seuls des flux documentés et approuvés transitant par une frontière contrôlée.",
              refs=["ISO 27002:2022 8.22"],
              gap=("IND-OT-01", ["no", "partial"], V("OT and IT networks are not yet fully separated.", "Les réseaux TO et TI ne sont pas encore entièrement séparés."))),
        ]),
        S("SEC-REQ-ACCESS", "Remote and vendor access", "Accès à distance et des fournisseurs", [
            C("VA01", by="DEC-OT-REMOTE", src="decision", variants={
                "brokered": V("Vendor remote access to OT systems is permitted only through a monitored, brokered connection with multi-factor authentication, enabled for the duration of an approved intervention and disabled afterwards.",
                              "L’accès à distance des fournisseurs aux systèmes TO n’est permis que par une connexion intermédiée et surveillée avec authentification multifacteur, activée pour la durée d’une intervention approuvée puis désactivée."),
                "none": V("Vendor remote access to OT systems is not permitted; interventions are performed on site or by {org} staff.",
                          "L’accès à distance des fournisseurs aux systèmes TO n’est pas permis; les interventions sont faites sur place ou par le personnel de {org}."),
                "_none": V("Vendor remote access to OT systems is permitted only under [DECISION: OT vendor remote access rule].",
                           "L’accès à distance des fournisseurs aux systèmes TO n’est permis qu’aux conditions suivantes : [DÉCISION : règle d’accès à distance des fournisseurs TO].")}),
        ]),
        S("SEC-REQ-CHANGE", "Changes, patches and devices", "Changements, correctifs et appareils", [
            C("CG01", "Changes and patches to OT systems must be tested and scheduled in maintenance windows approved by operations, with a rollback plan; where patching is not possible, compensating controls must be documented.",
              "Les changements et correctifs aux systèmes TO doivent être testés et planifiés dans des fenêtres d’entretien approuvées par les opérations, avec un plan de retour arrière; lorsque l’application d’un correctif est impossible, des mesures compensatoires doivent être documentées.",
              refs=["ISO 27002:2022 8.32", "ISO 27002:2022 8.8"]),
            C("CG02", "Devices that cannot be managed or secured require an explicit, time-bound exception with a business justification, a risk owner, compensating controls and a review date.",
              "Les appareils qui ne peuvent être gérés ni sécurisés exigent une dérogation explicite et limitée dans le temps, comportant une justification d’affaires, un responsable du risque, des mesures compensatoires et une date de révision."),
            C("CG03", "Removable media must be scanned before use on OT systems.", "Les supports amovibles doivent être analysés avant toute utilisation sur des systèmes TO.", refs=["ISO 27002:2022 7.10"]),
            C("CG04", "Security testing such as active scanning must not be performed on live OT systems without approval from operations and a safety assessment.",
              "Des essais de sécurité comme le balayage actif ne doivent pas être effectués sur des systèmes TO en exploitation sans l’approbation des opérations et une évaluation de la sécurité des personnes.", mod="must not"),
        ]),
    ],
)
