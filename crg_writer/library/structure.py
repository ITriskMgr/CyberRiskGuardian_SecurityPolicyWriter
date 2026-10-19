"""Structure-only templates: mandatory sections and the decisions to complete, without pre-written requirements.
They are labelled as structure templates in the application and in the exported file."""
from .common import C, S, topic_frame


def _req(sid, en, fr, items):
    return S(sid, en, fr, [C(f"{sid[-3:]}{i + 1:02d}", f"[TECHNICAL_DETAIL: {a}]", f"[DÉTAIL_TECHNIQUE : {b}]", mod="must")
                         for i, (a, b) in enumerate(items)])


def _purpose(en, fr):
    return [C("P01", en, fr, mod="info")]


def _roles(*pairs):
    return [C(f"R{i + 1:02d}", a, b) for i, (a, b) in enumerate(pairs)]


CRYPTO = topic_frame(
    _purpose("This policy sets when and how {org} uses cryptography to protect information, and how cryptographic keys are managed.",
             "La présente politique établit quand et comment {org} utilise la cryptographie pour protéger l’information et comment les clés cryptographiques sont gérées."),
    [], _roles(("{sec} approves cryptographic standards and key-management practices.", "{sec} approuve les normes cryptographiques et les pratiques de gestion des clés."),
               ("Key custodians manage keys according to the key-management standard.", "Les gardiens de clés gèrent les clés selon la norme de gestion des clés.")),
    [_req("SEC-REQ-ENC", "Encryption by classification", "Chiffrement selon la classification", [
        ("When encryption is required at rest and in transit for each classification level", "Quand le chiffrement est requis au repos et en transit pour chaque niveau de classification"),
        ("Approved algorithms, protocols and minimum key lengths (kept in a standard)", "Algorithmes, protocoles et longueurs de clé minimales approuvés (tenus dans une norme)")]),
     _req("SEC-REQ-KEYS", "Key management", "Gestion des clés", [
        ("Key generation, storage (KMS/HSM), rotation, escrow/recovery and destruction", "Génération, stockage (KMS/HSM), renouvellement, dépôt/récupération et destruction des clés"),
        ("Segregation of duties over keys and ownership of keys used in cloud services", "Séparation des tâches pour les clés et propriété des clés utilisées dans les services infonuagiques"),
        ("Plan for migration to post-quantum cryptography", "Plan de migration vers la cryptographie post-quantique")])])

BCP = topic_frame(
    _purpose("This policy establishes how {org} prepares to maintain or resume its critical activities during and after a disruption.",
             "La présente politique établit comment {org} se prépare à maintenir ou à reprendre ses activités essentielles pendant et après une perturbation."),
    [], _roles(("[ROLE: Business continuity coordinator] coordinates the continuity programme.", "[RÔLE : coordonnateur de la continuité] coordonne le programme de continuité."),
               ("Business owners maintain the continuity plans of their activities.", "Les responsables d’affaires tiennent à jour les plans de continuité de leurs activités.")),
    [_req("SEC-REQ-BIA", "Impact analysis and objectives", "Analyse d’impact et objectifs", [
        ("Business impact analysis method and frequency; RTO/RPO per critical activity", "Méthode et fréquence de l’analyse d’impact; DMI/PDMA par activité essentielle")]),
     _req("SEC-REQ-PLANS", "Plans and exercises", "Plans et exercices", [
        ("Required plans (continuity, disaster recovery, crisis communication) and their owners", "Plans requis (continuité, reprise après sinistre, communication de crise) et leurs responsables"),
        ("Exercise types and frequency; criteria for invoking the plans", "Types et fréquence des exercices; critères de déclenchement des plans")])])

PHYS = topic_frame(
    _purpose("This policy protects {org}’s premises, equipment and media against unauthorized physical access, damage and environmental threats.",
             "La présente politique protège les locaux, équipements et supports de {org} contre l’accès physique non autorisé, les dommages et les menaces environnementales."),
    [], _roles(("[ROLE: Facilities or physical security lead] manages physical access controls.", "[RÔLE : responsable des installations ou de la sécurité physique] gère les contrôles d’accès physique."),),
    [_req("SEC-REQ-ZONES", "Secure areas", "Zones sécurisées", [
        ("Security zones, who may access them and how access is granted and reviewed", "Zones de sécurité, qui peut y accéder et comment l’accès est accordé et revu"),
        ("Visitor identification, escort and logging", "Identification, accompagnement et registre des visiteurs")]),
     _req("SEC-REQ-EQUIP", "Equipment and media", "Équipements et supports", [
        ("Protection of server and network rooms against fire, water, power loss and intrusion", "Protection des salles de serveurs et de réseau contre l’incendie, l’eau, les pannes et l’intrusion"),
        ("Clean desk and clear screen expectations; secure disposal of equipment", "Attentes de bureau propre et d’écran verrouillé; élimination sécuritaire des équipements")])])

CLOUD = topic_frame(
    _purpose("This policy governs the acquisition, configuration, use and exit of cloud services so that {org}’s responsibilities under the shared-responsibility model are met.",
             "La présente politique encadre l’acquisition, la configuration, l’utilisation et la sortie des services infonuagiques afin que {org} assume ses responsabilités selon le modèle de responsabilité partagée."),
    [], _roles(("{sec} approves cloud security baselines and new cloud services.", "{sec} approuve les configurations de référence infonuagiques et les nouveaux services."),),
    [_req("SEC-REQ-LIFE", "Cloud service lifecycle", "Cycle de vie des services infonuagiques", [
        ("Approval process before adopting a cloud service, including data location requirements", "Processus d’approbation avant l’adoption d’un service infonuagique, y compris les exigences d’emplacement des données"),
        ("Security baselines per provider and continuous configuration monitoring", "Configurations de référence par fournisseur et surveillance continue de la configuration"),
        ("Responsibility matrix (provider vs {org}) and exit plan", "Matrice des responsabilités (fournisseur et {org}) et plan de sortie")])])

TRAIN = topic_frame(
    _purpose("This policy ensures that everyone at {org} has the security knowledge their role requires.",
             "La présente politique assure que chaque personne chez {org} possède les connaissances en sécurité requises par son rôle."),
    [], _roles(("{sec} defines the training content and measures its effectiveness.", "{sec} définit le contenu de la formation et en mesure l’efficacité."),
               ("Human resources tracks completion.", "Les ressources humaines suivent la complétion.")),
    [_req("SEC-REQ-PROG", "Training programme", "Programme de formation", [
        ("Mandatory training by role, frequency and minimum content", "Formation obligatoire par rôle, fréquence et contenu minimal"),
        ("Phishing simulations and effectiveness measures; consequences of non-completion", "Simulations d’hameçonnage et mesures d’efficacité; conséquences de la non-complétion")])])
