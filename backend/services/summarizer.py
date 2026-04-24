"""Résumé automatique par chapitre — approche extractive structurée.

Nettoie le texte source (déduplication, filtrage bruit PDF),
score les phrases par pertinence et qualité, produit un résumé
structuré en points clés, et extrait les concepts via spaCy.
"""

import logging
import re
import threading
from collections import Counter

logger = logging.getLogger(__name__)

_nlp = None
_nlp_lock = threading.Lock()


def _get_spacy():
    """Charge le modèle spaCy français (singleton thread-safe)."""
    global _nlp
    if _nlp is None:
        with _nlp_lock:
            if _nlp is None:
                import spacy
                try:
                    _nlp = spacy.load("fr_core_news_lg")
                except OSError:
                    logger.warning("fr_core_news_lg non trouvé, fallback sm…")
                    try:
                        _nlp = spacy.load("fr_core_news_sm")
                    except OSError:
                        logger.error("Aucun modèle spaCy français installé.")
                        _nlp = None
    return _nlp


# ═══════════════════════════════════════════════════════════════════════
# Mots génériques à exclure des concepts clés — liste exhaustive
# ═══════════════════════════════════════════════════════════════════════
# Principe : tout mot qui peut apparaître dans n'importe quel PDF
# académique, quelle que soit la matière, est un stop-concept.
# Les termes spécifiques à un domaine (VPN, Blockchain, DDoS, …)
# ne sont JAMAIS dans cette liste.

_STOP_CONCEPTS: set[str] = {
    # ── Noms ultra-génériques ──
    "chose", "choses", "truc", "machin",
    "exemple", "exemples",
    "type", "types", "sorte", "sortes", "genre", "genres", "espèce",
    "nombre", "nombres", "quantité", "quantités",
    "taille", "tailles", "mesure", "mesures", "degré", "degrés",
    "message", "messages", "ressource", "ressources",
    "résultat", "résultats",
    "manière", "manières", "façon", "façons", "mode", "modes",
    "partie", "parties", "point", "points",
    "moment", "moments", "instant", "instants",
    "période", "périodes", "durée", "durées",
    "lieu", "lieux", "endroit", "endroits", "espace", "espaces",
    "temps", "forme", "formes",
    "niveau", "niveaux", "ensemble", "ensembles",
    "figure", "figures",
    "qualité", "qualités",
    "efficacité", "performance", "performances", "fiabilité",
    # ── Structure de document académique ──
    "page", "pages", "chapitre", "chapitres",
    "cours", "leçon", "leçons",
    "introduction", "conclusion",
    "slide", "slides", "diapositive", "diapositives",
    "section", "sections", "paragraphe", "paragraphes",
    "image", "images", "tableau", "tableaux",
    "texte", "textes",
    "question", "questions", "réponse", "réponses",
    "titre", "titres", "ligne", "lignes",
    "mot", "mots", "lettre", "lettres",
    "document", "documents",
    "annexe", "annexes",
    "référence", "références", "bibliographie",
    "source", "sources", "note", "notes",
    "plan", "plans", "sommaire", "index",
    "résumé", "résumés",
    "schéma", "schémas", "diagramme", "diagrammes",
    "illustration", "illustrations",
    "extrait", "extraits",
    # ── Pronoms / déterminants / adjectifs génériques ──
    "cas", "fait", "faits", "fois",
    "jour", "jours", "année", "années", "mois",
    "début", "fin", "suite", "reste",
    "côté", "droit", "gauche", "haut", "bas",
    "tout", "tous", "toute", "toutes", "rien", "pas", "seul", "seule",
    "admis", "admise", "refusé", "refusée", "réel", "réelle",
    "autre", "autres", "même", "mêmes",
    "tel", "tels", "telle", "telles",
    "certain", "certains", "certaine", "certaines",
    "chaque", "plusieurs", "quelque", "quelques",
    "aucun", "aucune",
    "premier", "première", "premiers", "premières",
    "deuxième", "troisième",
    "dernier", "dernière", "derniers", "dernières",
    "nouveau", "nouvelle", "nouveaux", "nouvelles",
    "ancien", "ancienne", "anciens", "anciennes",
    "petit", "petite", "petits", "petites",
    "grand", "grande", "grands", "grandes",
    "bon", "bonne", "bons", "bonnes",
    "mauvais", "mauvaise",
    "beau", "belle",
    "long", "longue", "court", "courte",
    "important", "importante", "importants", "importantes",
    "principal", "principale", "principaux", "principales",
    "général", "générale", "généraux", "générales",
    "différent", "différente", "différents", "différentes",
    "possible", "possibles",
    "nécessaire", "nécessaires",
    "simple", "simples", "complexe", "complexes",
    "spécifique", "spécifiques",
    "particulier", "particulière", "particuliers",
    "essentiel", "essentielle", "essentiels",
    "fondamental", "fondamentale", "fondamentaux",
    "commun", "commune", "communs",
    "divers", "diverse", "diverses",
    "actuel", "actuelle", "actuels",
    "récent", "récente", "récents",
    "suivant", "suivante", "suivants",
    "précédent", "précédente", "précédents",
    # ── Méthodologie / académique générique ──
    "utilisation", "utilisations",
    "objectif", "objectifs",
    "définition", "définitions",
    "notion", "notions",
    "concept", "concepts",
    "méthode", "méthodes",
    "problème", "problèmes",
    "solution", "solutions",
    "donnée", "données",
    "système", "systèmes",
    "processus",
    "structure", "structures",
    "modèle", "modèles",
    "technique", "techniques",
    "information", "informations",
    "contenu", "contenus",
    "élément", "éléments",
    "valeur", "valeurs",
    "fonction", "fonctions",
    "opération", "opérations",
    "action", "actions",
    "effet", "effets",
    "condition", "conditions",
    "état", "états",
    "réseau", "réseaux",
    "approche", "approches",
    "étape", "étapes", "phase", "phases",
    "principe", "principes",
    "base", "bases",
    "catégorie", "catégories",
    "groupe", "groupes",
    "classe", "classes",
    "famille", "familles",
    "liste", "listes",
    "analyse", "analyses",
    "mise", "gestion",
    "contrôle", "contrôles",
    "test", "tests",
    "traitement", "traitements",
    "développement", "développements",
    "environnement", "environnements",
    "mécanisme", "mécanismes",
    "stratégie", "stratégies",
    "caractéristique", "caractéristiques",
    "propriété", "propriétés",
    "composant", "composants",
    "paramètre", "paramètres",
    "critère", "critères",
    "outil", "outils",
    "tâche", "tâches",
    "travail", "travaux",
    "rôle", "rôles",
    "but", "buts",
    "règle", "règles",
    "norme", "normes",
    "organisation", "organisations",
    "relation", "relations",
    "lien", "liens",
    "rapport", "rapports",
    "aspect", "aspects",
    "contexte", "contextes",
    "domaine", "domaines",
    "secteur", "secteurs",
    "facteur", "facteurs",
    "impact", "impacts",
    "conséquence", "conséquences",
    "cause", "causes",
    "raison", "raisons",
    "avantage", "avantages",
    "inconvénient", "inconvénients",
    "besoin", "besoins",
    "moyen", "moyens",
    "capacité", "capacités",
    "compétence", "compétences",
    "connaissance", "connaissances",
    "expérience", "expériences",
    "pratique", "pratiques",
    "théorie", "théories",
    "cadre", "cadres",
    "perspective", "perspectives",
    "dimension", "dimensions",
    "champ", "champs",
    "portée", "étendue",
    "limite", "limites",
    "contrainte", "contraintes",
    "exigence", "exigences",
    "standard", "standards",
    "procédure", "procédures",
    "protocole", "protocoles",
    "politique", "politiques",
    "directive", "directives",
    "référentiel", "référentiels",
    "indicateur", "indicateurs",
    # ── Personnes génériques ──
    "personne", "personnes",
    "utilisateur", "utilisateurs",
    "individu", "individus",
    "auteur", "auteurs",
    "expert", "experts",
    "responsable", "responsables",
    "membre", "membres",
    "équipe", "équipes",
    "client", "clients",
    "pirate", "pirates",
    "acteur", "acteurs",
    "opérateur", "opérateurs",
    "administrateur", "administrateurs",
    "spécialiste", "spécialistes",
    "professionnel", "professionnels",
    # ── Objets / artefacts génériques ──
    "objet", "objets",
    "dispositif", "dispositifs",
    "machine", "machines",
    "appareil", "appareils",
    "matériel", "matériels",
    "logiciel", "logiciels",
    "programme", "programmes",
    "application", "applications",
    "technologie", "technologies",
    "plateforme", "plateformes",
    "interface", "interfaces",
    "support", "supports",
    "équipement", "équipements",
    "infrastructure", "infrastructures",
    "architecture", "architectures",
    # ── Actions / processus génériques ──
    "accès", "navigation",
    "porte", "portes",
    "distance",
    "ordinateur", "ordinateurs",
    "activité", "activités",
    "service", "services",
    "serveur", "serveurs",
    "processeur", "processeurs",
    "protection", "protections",
    "stockage",
    "entité", "entités",
    "manipulation", "manipulations",
    "transmission", "transmissions",
    "communication", "communications",
    "connexion", "connexions",
    "configuration", "configurations",
    "installation", "installations",
    "implémentation", "implémentations",
    "déploiement", "exécution",
    "fonctionnement",
    "détection", "surveillance",
    "vérification", "vérifications",
    "validation", "validations",
    "évaluation", "évaluations",
    "planification", "supervision",
    "maintenance",
    "migration", "migrations",
    "transformation", "transformations",
    "évolution", "évolutions",
    "amélioration", "améliorations",
    "optimisation", "optimisations",
    "automatisation",
    "intégration", "intégrations",
    "adaptation", "adaptations",
    "modification", "modifications",
    "sauvegarde", "sauvegardes",
    "restauration", "restaurations",
    # ── Sécurité / tech trop générique (ubiquitaires) ──
    "attaque", "attaques", "attack", "attacks",
    "mémoire", "bande",
    "trafic", "inondation",
    "informatique", "informatiques",
    "surchargeant",
    # ── Académique / institutionnel ──
    "licence", "master", "doctorat",
    "module", "modules",
    "département", "départements",
    "génie", "mathématiques",
    "science", "sciences",
    "ingénierie",
    "professeur", "professeurs",
    "université", "universités",
    "faculté", "facultés",
    "institut", "instituts",
    "étudiant", "étudiants", "étudiante", "étudiantes",
    "étude", "études",
    "formation", "formations",
    "enseignement", "enseignements",
    "recherche", "recherches",
    "projet", "projets",
    "thèse", "thèses",
    "diplôme", "diplômes",
    "semestre", "semestres",
    "examen", "examens",
    "exercice", "exercices",
    "correction", "corrections",
    "épreuve", "épreuves",
    "devoir", "devoirs",
    "td", "tp", "cm",
    # ── Verbes qui fuient comme concepts ──
    "détourner", "créer", "utiliser", "permettre",
    "assurer", "garantir", "maintenir",
    "développer", "analyser", "évaluer",
    "identifier", "détecter", "surveiller",
    "protéger", "sécuriser", "vérifier",
    "gérer", "organiser", "planifier",
    "mettre", "faire", "avoir", "être",
    "prendre", "donner", "voir", "dire",
    "pouvoir", "vouloir", "devoir", "savoir",
    "falloir", "aller", "venir", "partir",
    "comprendre", "connaître", "apprendre",
    "montrer", "présenter", "expliquer",
    "proposer", "suggérer", "recommander",
    "fournir", "offrir", "apporter",
    "inclure", "contenir",
    "constituer", "représenter", "correspondre",
    "concerner", "impliquer", "nécessiter",
    "dépendre", "varier", "évoluer",
    "augmenter", "diminuer", "réduire",
    "améliorer", "optimiser", "renforcer",
    "empêcher", "éviter", "prévenir",
    "respecter", "appliquer", "suivre",
    "explorer", "découvrir", "résoudre", "obtenir", "réaliser",
    "exécuter", "construire", "configurer", "installer", "tester",
    "implémenter", "concevoir",
    # ── English generic ──
    "example", "examples", "type", "types",
    "number", "numbers", "result", "results",
    "part", "parts", "point", "points",
    "time", "level", "levels",
    "figure", "figures", "image", "images",
    "table", "tables", "text",
    "system", "systems", "method", "methods",
    "approach", "tool", "tools", "process",
    "data", "information",
    "network", "networks",
    "service", "services",
    "user", "users",
    "application", "applications",
    "device", "devices", "software",
    "computer", "computers",
    "security", "attack", "attacks",
    "resource", "resources",
    "management", "analysis",
    "control", "access", "protection",
    "function", "functions",
    "structure", "model", "models",
    "value", "values", "element", "elements",
    # ── Mois / dates / unités temporelles (souvent du watermark) ──
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    "january", "february", "march", "april", "june",
    "july", "august", "september", "october", "november", "december",
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    # ── Fragments PDF tronqués (bouts de mots restants après ligature ratée) ──
    "cun", "spéci", "entraîn", "ltres", "ltre", "chier",
    "nition", "nitions", "nale", "nales",
    # ── Variables/codes math seuls (1-3 lettres en majuscules ne sont pas des concepts utiles) ──
    "var", "vars", "norm", "norms",
    # ── Verbes courants supplémentaires ──
    "adapter", "restaurer", "préserver", "lisser", "ajuster",
    "réduire", "augmenter", "minimiser", "maximiser",
    "calculer", "estimer", "mesurer", "extraire",
    "transformer", "générer", "convertir", "modifier",
    # ── Adjectifs / mots vagues souvent extraits par spaCy ──
    "global", "globaux", "globale", "globales",
    "local", "locaux", "locale", "locales",
    "force", "forces", "puissance", "puissances",
    "type", "types", "modèle", "modèles",
    "actif", "actifs", "active", "actives",
    "passif", "passifs", "passive", "passives",
    "complet", "complets", "complète", "complètes",
}

# Pattern: words glued together from bad PDF extraction (e.g. "sécuritéRéseau")
_GLUED_WORD_RE = re.compile(r"[a-zéèêëàâäùûüôöîïç]{3}[A-ZÉÈÊËÀÂ][a-z]")

# Broader glued-word patterns for concept filtering
_GLUED_ENDINGS = re.compile(
    r"(és?|ès?|ée?s?|tion|sion|ment|eur|ble|que|ure|age|oir|ite|ité)"
    r"(réseau|pour|par|sur|dans|avec|entre|comme|leur|mais|sont|être|avoir|faire|cette|tout|plus|sans|sous|chez|vers|après|avant|depuis|pendant|chaque)",
    re.IGNORECASE,
)
_CONCEPT_ENDS_WITH_PREPOSITION = re.compile(
    r"(à|de|du|des|le|la|les|au|aux|un|une|en|et|ou|ni|si|que|qui|dont|où|par|pour|sur|dans|avec|sans|sous|vers|chez|entre|contre|depuis|pendant|durant|lors|hors)$",
    re.IGNORECASE,
)

# ── Concept cleaning patterns ─────────────────────────────────────────

# Leading French articles/determiners to strip from concepts
_LEADING_ARTICLES_RE = re.compile(
    r"^(?:les?\s+|la\s+|l['\u2019]|une?\s+|des?\s+|du\s+|d['\u2019]|"
    r"ses?\s+|sa\s+|son\s+|leurs?\s+|ces?\s+|cet(?:te)?\s+|aux?\s+|"
    r"tout(?:e)?s?\s+|chaque\s+|quelques?\s+|quelconque\s+|seule?\s+|"
    r"r\u00e9elle?\s+|notre\s+|votre\s+|"
    r"deux\s+|trois\s+|quatre\s+|cinq\s+|six\s+|sept\s+|huit\s+|neuf\s+|dix\s+)",
    re.IGNORECASE,
)

# Author/watermark/page-number patterns in concepts
_AUTHOR_WATERMARK_RE = re.compile(
    r"^[A-Z]\.\s*[A-Z]|"           # "A. Guezzaz", "Y.TAOUIL" (Initial.Surname)
    r"\d+\s*/\s*\d+|"              # "29 / 106" (page refs)
    r"\s\d{1,3}\s*$",              # Trailing page numbers "... 106", "... 8"
    re.IGNORECASE,
)

# Verb infinitives that shouldn't start a concept
_INFINITIVE_START_RE = re.compile(
    r"^(créer|détourner|utiliser|permettre|assurer|garantir|maintenir|"
    r"développer|analyser|évaluer|identifier|détecter|surveiller|"
    r"protéger|sécuriser|vérifier|gérer|organiser|planifier|"
    r"comprendre|connaître|apprendre|montrer|présenter|expliquer|"
    r"proposer|fournir|mettre|faire|avoir|être|prendre|donner|"
    r"explorer|découvrir|résoudre|obtenir|réaliser|appliquer|exécuter|"
    r"construire|configurer|installer|tester|implémenter|concevoir)(\s|$)",
    re.IGNORECASE,
)

# Math notation symbols
_MATH_SYMBOLS_RE = re.compile(r"[ˆ∂∇σαβγδεζηθλμπρτφψω∈∉∀∃∑∏∫≈≤≥±×÷√∞]")


def _clean_concept(term: str) -> str:
    """Clean a concept: strip articles, digits, punctuation, normalize."""
    # Normalize whitespace and strip newlines
    term = re.sub(r"\s+", " ", term).strip()
    # Strip quotes «»""'' and leading punctuation/bullets
    term = re.sub(r"^[«»\u201c\u201d\u2018\u2019,;:.\-\u2013\u2014•●■▪\s]+", "", term).strip()
    term = re.sub(r"[«»\u201c\u201d\u2018\u2019]+$", "", term).strip()
    # Strip leading digits/numbering (e.g., "1 L'algorithme" → "L'algorithme")
    term = re.sub(r"^\d+[.):\s]+\s*", "", term).strip()
    # Strip leading French articles/determiners
    cleaned = _LEADING_ARTICLES_RE.sub("", term).strip()
    # If stripping removed everything or left < 3 chars, keep original
    if len(cleaned) >= 3:
        term = cleaned
    # Re-capitalize first letter if needed
    if term and term[0].islower():
        term = term[0].upper() + term[1:]
    return term


# ── Unicode artefact characters from PDF ──────────────────────────────

_PDF_JUNK_CHARS = re.compile(r"[\u25a1\u25a0\u25aa\u25ab\u25cf\u25cb\u25b6\u25b7\u25c0\u25c1\uf0b7\uf0a7\uf0d8\uf0fc\u2003\u2002\u200b\u00ad]")


# ── Réparation universelle des ligatures fi/fl/ff/ffi perdues ────────
# Beaucoup de PDFs perdent les ligatures lors de l'extraction texte,
# laissant un espace ou un trou : "Classi cation" → "Classification",
# "in nie" → "infinie", "di érent" → "différent", "e cace" → "efficace".
# Patterns construits empiriquement à partir de cas réels observés.

# Approche conservatrice : on ne répare une ligature que si :
#  (1) le préfixe + suffixe collés forment un mot français existant connu
#  (2) le préfixe seul N'EST PAS un mot français commun (sinon on risque de massacrer le texte)
# C'est pour cela qu'on utilise une LISTE EXPLICITE de paires (préfixe, suffixe, ligature, mot_résultant)
# plutôt que des patterns génériques qui ont causé "perceptron et" → "perceptronffet".

# Format : (préfixe_avant_ligature, suffixe_après_ligature, ligature)
# Tous insensibles à la casse. Le préfixe DOIT être un fragment qui n'est PAS un mot autonome.
_LIGATURE_REPAIRS: list[tuple[str, str, str]] = [
    # ── fi : Classification, Définition, Spécification ──
    ("classi", "cation", "fi"),
    ("classi", "cations", "fi"),
    ("classi", "catif", "fi"),
    ("classi", "cative", "fi"),
    ("identi", "cation", "fi"),
    ("identi", "er", "fi"),
    ("identi", "é", "fi"),
    ("identi", "ée", "fi"),
    ("identi", "és", "fi"),
    ("identi", "ées", "fi"),
    ("speci", "cation", "fi"),
    ("spéci", "cation", "fi"),
    ("spéci", "cations", "fi"),
    ("spéci", "que", "fi"),
    ("spéci", "ques", "fi"),
    ("spéci", "er", "fi"),
    ("modi", "cation", "fi"),
    ("modi", "cations", "fi"),
    ("modi", "er", "fi"),
    ("modi", "é", "fi"),
    ("modi", "ée", "fi"),
    ("véri", "cation", "fi"),
    ("véri", "er", "fi"),
    ("justi", "cation", "fi"),
    ("quali", "cation", "fi"),
    ("quali", "er", "fi"),
    ("quanti", "cation", "fi"),
    ("noti", "cation", "fi"),
    ("signi", "cation", "fi"),
    ("signi", "e", "fi"),
    ("signi", "er", "fi"),
    ("signi", "catif", "fi"),
    ("béné", "cier", "fi"),
    ("béné", "ce", "fi"),
    ("béné", "ces", "fi"),
    ("sacri", "er", "fi"),
    ("sacri", "ce", "fi"),
    ("dé", "nition", "fi"),
    ("dé", "nitions", "fi"),
    ("dé", "nitif", "fi"),
    ("dé", "nitive", "fi"),
    ("dé", "nir", "fi"),
    ("dé", "ni", "fi"),
    ("dé", "nie", "fi"),
    ("dé", "nies", "fi"),
    ("prédé", "ni", "fi"),
    ("prédé", "nie", "fi"),
    ("prédé", "nies", "fi"),
    ("prédé", "nis", "fi"),
    ("prédé", "nir", "fi"),
    ("prédé", "nition", "fi"),
    ("dé", "s", "fi"),  # défis
    ("in", "nie", "fi"),
    ("in", "nies", "fi"),
    ("in", "ni", "fi"),
    ("in", "nis", "fi"),
    ("in", "niment", "fi"),
    ("in", "nité", "fi"),
    ("con", "rme", "fi"),
    ("con", "rmer", "fi"),
    ("con", "rmation", "fi"),
    ("con", "ance", "fi"),
    ("con", "guration", "fi"),
    ("con", "gurer", "fi"),
    ("sur", "sant", "ffi"),  # rare mais cohérent
    ("insu", "sant", "ffi"),
    ("insu", "sante", "ffi"),
    ("insu", "sants", "ffi"),
    ("insu", "samment", "ffi"),
    ("e", "cace", "ffi"),  # efficace
    ("e", "caces", "ffi"),
    ("e", "cacement", "ffi"),
    ("e", "cacité", "ffi"),
    # ── ff : différent, difficile ──
    ("di", "érent", "ff"),
    ("di", "érents", "ff"),
    ("di", "érente", "ff"),
    ("di", "érentes", "ff"),
    ("di", "érence", "ff"),
    ("di", "érences", "ff"),
    ("di", "érer", "ff"),
    ("di", "cile", "ff"),
    ("di", "ciles", "ff"),
    ("di", "culté", "ff"),
    ("di", "cultés", "ff"),
    ("o", "rir", "ff"),
    ("o", "re", "ff"),
    ("o", "res", "ff"),
    ("sou", "rir", "ff"),
    ("sou", "rance", "ff"),
    # ── fl : flux, flèche ──
    ("in", "uence", "fl"),
    ("in", "uencer", "fl"),
    ("in", "uences", "fl"),
    # ── Anglais courant (Over-fitting / fitting / file) ──
    ("over-", "tting", "fi"),
    ("over", "tting", "fi"),
    ("under-", "tting", "fi"),
    ("under", "tting", "fi"),
    ("over", "ow", "fl"),
    ("under", "ow", "fl"),
    ("work", "ow", "fl"),
    ("data", "ow", "fl"),
    ("o", "set", "ff"),  # offset
    ("sti", "", "ff"),   # stiff (rare)
    ("e", "ect", "ff"),  # effect
    ("e", "ects", "ff"),
    ("e", "ective", "ff"),
    ("di", "er", "ff"),  # differ
    ("di", "ers", "ff"),
]

# Mots entiers commençant par une ligature manquante (ex: "ltres" → "filtres")
_LIGATURE_WORD_START_REPAIRS: list[tuple[str, str]] = [
    ("ltres", "filtres"),
    ("ltre", "filtre"),
    ("ltrer", "filtrer"),
    ("ltrage", "filtrage"),
    ("ltré", "filtré"),
    ("ltrée", "filtrée"),
    ("chier", "fichier"),
    ("chiers", "fichiers"),
]


def _repair_ligatures(text: str) -> str:
    """Répare les ligatures fi/fl/ff perdues à l'extraction PDF (approche conservatrice par dictionnaire)."""
    if not text:
        return text
    # Réparation dictionnaire : préfixe + espace + suffixe → préfixe + ligature + suffixe
    for prefix, suffix, ligature in _LIGATURE_REPAIRS:
        if not suffix:
            continue
        # \b assure qu'on est sur des frontières de mots
        pattern = r"\b(" + re.escape(prefix) + r")\s+(" + re.escape(suffix) + r")\b"
        replacement = r"\1" + ligature + r"\2"
        try:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        except re.error:
            continue
    # Mots entiers tronqués
    for broken, fixed in _LIGATURE_WORD_START_REPAIRS:
        text = re.sub(r"\b" + re.escape(broken) + r"\b", fixed, text, flags=re.IGNORECASE)
    return text


# ── Détection universelle de watermarks (texte répété sur de nombreuses pages) ──

def _detect_watermarks(chunks: list[dict], min_freq_ratio: float = 0.02) -> list[str]:
    """Identifie les fragments répétés (watermarks, en-têtes, pieds de page).

    Approche universelle, deux passes :
      1. Lignes courtes répétées (en-têtes / pieds classiques)
      2. N-grammes (3 à 7 mots) répétés au sein du texte continu — détecte les
         watermarks insérés à l'intérieur d'un bloc texte (ex: "Y.TAOUIL Deep
         Learning mars 2026 /").
    """
    if not chunks or len(chunks) < 4:
        return []

    candidate_freq: Counter[str] = Counter()
    n_chunks = len(chunks)

    def _normalize(s: str) -> str:
        s = re.sub(r"\s+", " ", s.lower())
        s = re.sub(r"\b\d+\b", "", s).strip()
        return re.sub(r"\s+", " ", s)

    for chunk in chunks:
        text = chunk.get("text", "")
        if not text:
            continue
        seen_in_chunk: set[str] = set()

        # Passe 1 : lignes courtes
        for line in text.split("\n"):
            line = line.strip()
            if 8 < len(line) < 120:
                norm = _normalize(line)
                if len(norm) >= 8 and norm not in seen_in_chunk:
                    seen_in_chunk.add(norm)
                    candidate_freq[norm] += 1

        # Passe 2 : n-grammes 3-7 mots (alphanumériques + ponctuation simple)
        # On tokenise grossièrement en gardant les majuscules pour repérer auteurs/dates
        words = re.findall(r"[\wÀ-ÿ.\-]+", text)
        for n in (5, 4, 6, 3, 7):
            if len(words) < n:
                continue
            for i in range(len(words) - n + 1):
                gram = " ".join(words[i:i+n])
                # On ne s'intéresse qu'aux n-grammes "métadonnée-like" :
                # contiennent une initiale point (auteur), ou un mois, ou un slash, ou /
                if not re.search(r"(\b[A-ZÀ-Ý]\.|\b\d{4}\b|/|\bjanvier|\bfévrier|\bmars|\bavril|\bmai|\bjuin|\bjuillet|\baoût|\bseptembre|\boctobre|\bnovembre|\bdécembre)", gram):
                    continue
                norm = _normalize(gram)
                if 10 <= len(norm) <= 100 and norm not in seen_in_chunk:
                    seen_in_chunk.add(norm)
                    candidate_freq[norm] += 1

    threshold = max(4, int(n_chunks * min_freq_ratio))
    watermarks = [c for c, freq in candidate_freq.items() if freq >= threshold]
    # Conserver les plus longs en priorité (suppression plus précise)
    watermarks.sort(key=lambda s: -len(s))
    if watermarks:
        logger.info(
            "Watermarks détectés (%d chunks, seuil=%d) : %s",
            n_chunks, threshold, watermarks[:5],
        )
    return watermarks


def _strip_watermarks(text: str, watermarks: list[str]) -> str:
    """Supprime les watermarks détectés du texte (insensible à la casse, tolérant aux chiffres/séparateurs)."""
    # Aussi nettoyer les caractères de contrôle / escape résiduels
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    for wm in watermarks or []:
        if not wm or len(wm) < 5:
            continue
        # Tokens du watermark (mots, possiblement avec . - intégrés)
        tokens = re.findall(r"[\wÀ-ÿ.\-]+", wm)
        if not tokens:
            continue
        # Pattern : tokens séparés par espaces/chiffres/séparateurs typographiques
        escaped = [re.escape(t) for t in tokens]
        sep = r"[\s\d/\\\-_]*"
        pattern = sep.join(escaped)
        # Permettre chiffres/slashes optionnels en queue (numéros de page)
        full_pattern = pattern + r"\s*\d{0,4}\s*[/\\]?\s*\d{0,4}"
        try:
            text = re.sub(full_pattern, " ", text, flags=re.IGNORECASE)
        except re.error:
            continue

    # ── Filet de sécurité universel : signatures auteur + date ──
    # Capture les patterns du genre "Y.TAOUIL 2 mars 2026" / "J. Dupont janvier 2024"
    # qui peuvent rester si non détectés via fréquence.
    _MOIS = r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre|january|february|march|april|may|june|july|august|september|october|november|december)"
    # Initiale.NOM (ou Initiale. Nom) suivi optionnellement d'un mot, puis date (jour? mois année)
    author_date = re.compile(
        rf"\b[A-ZÀ-Ý]\.\s?[A-ZÀ-Ý][A-Za-zÀ-ÿ\-]+(?:\s+[A-Za-zÀ-ÿ\-]+){{0,3}}\s+\d{{0,2}}\s*{_MOIS}\s+\d{{4}}(?:\s*\d{{0,4}}\s*[/\\]?\s*\d{{0,4}})?",
        re.IGNORECASE,
    )
    text = author_date.sub(" ", text)
    # Date isolée style "2 mars 2026 1 / 69" en fin de ligne
    date_pagination = re.compile(
        rf"\b\d{{1,2}}\s*{_MOIS}\s+\d{{4}}\s*\d{{0,4}}\s*[/\\]\s*\d{{1,4}}",
        re.IGNORECASE,
    )
    text = date_pagination.sub(" ", text)

    # Compresser les espaces multiples
    text = re.sub(r"[ \t]+", " ", text)
    return text


# ── Réparation des mots collés (artefacts PDF) ───────────────────────

def _fix_glued_words(text: str) -> str:
    """Répare les mots collés produits par l'extraction PDF.

    Cible les patterns les plus fréquents sans casser les mots normaux :
    - lowercase→Uppercase transition (ex: attaquesInformatiques)
    - comma not followed by space (ex: DDoS,phishing)
    - plural 's' followed by function words (ex: incidentset → incidents et)
    - noun endings followed by function words (ex: protectiondes → protection des)
    - accented endings followed by verbs (ex: cybersécuritéincluent)
    - verb forms glued with function words (ex: élaboredesstratégies)
    - word glued to l'/d' articles (ex: contrôlerl'accès)
    - words inside French quotes (ex: «attaqueactive»)
    """
    # 1. Fix comma-glued: "DDoS,phishing" → "DDoS, phishing"
    text = re.sub(r"([a-zA-Zéèêàâùûôîï]),([a-zA-Zéèêàâùûôîï])", r"\1, \2", text)
    # 2. Fix lowercase→Uppercase: "attaquesInformatiques" → "attaques Informatiques"
    text = re.sub(r"([a-zéèêàâùûôîï])([A-ZÉÈÊÀÂ][a-z])", r"\1 \2", text)
    # 3. Plural 's' glued with function words (5+ chars before 's' to avoid false positives)
    text = re.sub(
        r"(\w{5,}s)(et|de|du|des|le|la|les|en|ou|pour|par|sur|dans|avec|sans|qui|que)\b",
        r"\1 \2", text,
    )
    # 4. Noun/adjective endings glued with function words
    text = re.sub(
        r"(\w{4,}(?:tion|sion|ment|eur|ence|ance|isme|iste|ture|ible|able))"
        r"(des|de|du|le|la|les|en|et|ou|par|pour|sur|dans|avec|un|une)\b",
        r"\1 \2", text,
    )
    # 5. Accented endings glued with verbs/function words
    text = re.sub(
        r"(\w{4,}(?:é|ée|és|ées|ité|ité))"
        r"(incluent|englobent|impliquent|assurent|permettent|concernent|présentent|utilisent|est|sont|ont|et|de|des|du|le|la|les|en|ou|par|pour|sur|dans|avec|un|une)\b",
        r"\1 \2", text,
    )
    # 6. Verb forms (ending in -e, -er, -re, -ir) glued with function words
    text = re.sub(
        r"(\w{5,}(?:er|re|ir|ore|ure|ère|ère))(l['\u2019]|d['\u2019]|des|de|du|le|la|les|en|et|ou|par|pour|sur|dans|avec|un|une)\b",
        r"\1 \2", text,
    )
    text = re.sub(
        r"(\w{5,}e)(des|du)([a-zéèêàâùûôîï])",
        r"\1 \2 \3", text,
    )
    # 6b. Word ending in 's' glued with 'à': "accèsà" → "accès à"
    text = re.sub(r"(\w{4,}s)(à|au|aux)\b", r"\1 \2", text)
    # 7. Word glued to l'/d' articles: "contrôlerl'accès" → "contrôler l'accès"
    text = re.sub(r"(\w{4,})(l['\u2019]|d['\u2019])([a-zéèêàâùûôîï])", r"\1 \2\3", text)
    # 8. Function word glued to next word after l'/d': "àun" → "à un"
    text = re.sub(r"(à|de|du|le|la)(un|une|des|les|le|la)\b", r"\1 \2", text)
    # 9. Fix inside French quotes: "«attaqueactive»" → "«attaque active»"
    text = re.sub(r"«(\w+?)([a-zéèêàâùûôîï])([a-zéèêàâùûôîï])»",
                  lambda m: "«" + m.group(0)[1:-1] + "»", text)
    # More robust: split words inside « »
    def _fix_quoted(m: re.Match) -> str:
        inner = m.group(1)
        inner = re.sub(r"([a-zéèêàâùûôîï])(active|passive|interne|externe)\b", r"\1 \2", inner)
        return "«" + inner + "»"
    text = re.sub(r"«([^»]+)»", _fix_quoted, text)
    # 10. Common PDF split words: "aujour d'hui" → "aujourd'hui"
    text = re.sub(r"\baujour\s+d[''\u2019]hui\b", "aujourd'hui", text)
    # 11. Extra space before punctuation: "mot , mot" → "mot, mot"
    text = re.sub(r"\s+([,;:!?])", r"\1", text)
    return text


# ── Nettoyage du texte source ─────────────────────────────────────────

def _clean_source_text(text: str) -> str:
    """Filtre le bruit : code, en-têtes, pieds de page, artefacts PDF,
    et élimine les lignes dupliquées / quasi-dupliquées typiques des PDF slides."""
    # Strip PDF junk characters (□, ■, ▪, etc.)
    text = _PDF_JUNK_CHARS.sub(" ", text)

    lines = text.split("\n")
    kept: list[str] = []
    seen_normalised: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Lignes de code
        if re.match(r"^(import |from |def |class |print\s*\(|write\s*\(|#\s|>>>|\.\.\.)", stripped):
            continue
        # En-têtes/pieds de page de cours
        if re.match(r"^(CSC\s+\d+|Page\s+\d+)", stripped, re.IGNORECASE):
            continue
        # Author/footer watermark lines (e.g. "Y.TAOUIL Deep Learning / 106")
        if re.match(r"^[A-Z]\.\s*[A-Z][A-Za-zÉÈÊÀÂéèêàâ]+\s+", stripped) and len(stripped) < 80:
            continue
        # Institutional / cover page lines
        if re.search(
            r"\b(licence\s+ing[ée]nierie|d[ée]partement\s+g[ée]nie|"
            r"facult[ée]|universit[ée]|3iasd|\bgim\b|pr\.\s+[a-z]|"
            r"module\s+s[ée]curit[ée]|g[ée]nie\s+informatique\s+et\s+math[ée]matiques)\b",
            stripped,
            re.IGNORECASE,
        ):
            continue
        # Isolated page numbers (single number on a line, or number followed by space)
        if re.match(r"^\d{1,3}\s*$", stripped):
            continue
        # Lignes avec trop peu de texte alphabétique
        alpha = sum(1 for c in stripped if c.isalpha())
        if len(stripped) > 10 and alpha / len(stripped) < 0.35:
            continue
        # Lignes très courtes
        if len(stripped) < 10:
            continue

        # ── Déduplication des lignes proches ──
        norm = re.sub(r"\s+", " ", stripped.lower())
        is_dup = False
        replace_idx = -1
        for j, prev in enumerate(seen_normalised):
            if norm in prev:
                is_dup = True
                break
            if prev in norm:
                replace_idx = j
                break
            n_words = set(norm.split())
            p_words = set(prev.split())
            overlap = len(n_words & p_words)
            smaller = min(len(n_words), len(p_words))
            if smaller >= 4 and overlap / smaller > 0.7:
                if len(norm) > len(prev):
                    replace_idx = j
                else:
                    is_dup = True
                break
        if is_dup:
            continue
        if replace_idx >= 0:
            seen_normalised[replace_idx] = norm
            kept[replace_idx] = stripped
            continue

        seen_normalised.append(norm)
        kept.append(stripped)

    result = " ".join(kept)
    # Strip inline author watermarks (e.g., "Y.TAOUIL Deep Learning / 106")
    result = re.sub(
        r"[A-Z]\.\s*[A-Z][A-Za-z\u00e9\u00e8\u00ea\u00e0\u00e2\u00c9\u00c8\u00ca\u00c0\u00c2]+"
        r"(?:\s+[A-Za-z\u00e9\u00e8\u00ea\u00e0\u00e2\u00c9\u00c8\u00ca\u00c0\u00c2]+){1,3}\s*/\s*(?:\d{1,3}\s*)?",
        " ", result,
    )
    # Strip inline page numbers that leaked: " 19 " surrounded by spaces
    result = re.sub(r"\s+\d{1,3}\s+", " ", result)
    return result


# ── Découpage en phrases ──────────────────────────────────────────────

def _split_into_sentences(text: str) -> list[str]:
    """Découpe le texte nettoyé en phrases exploitables.

    Gère les patterns académiques français : bullets, listes à puces,
    abréviations courantes et points-virgules comme séparateurs.
    """
    text = re.sub(r"\s+", " ", text).strip()
    text = _fix_glued_words(text)

    # Replace bullet markers with sentence boundaries
    text = re.sub(r"\s*[•●■▪▶→–]\ +", ". ", text)
    # Handle numbered list items: "1. " or "1) " mid-text
    text = re.sub(r"\s+(\d{1,2})[.)]\s+", r". ", text)

    # Protect common French abbreviations
    _ABBREV_MAP = {
        "dr.": "dr§", "pr.": "pr§", "mr.": "mr§", "mme.": "mme§",
        "mm.": "mm§", "pp.": "pp§", "ex.": "ex§", "cf.": "cf§",
        "etc.": "etc§", "vol.": "vol§", "éd.": "éd§", "fig.": "fig§",
        "réf.": "réf§", "ch.": "ch§", "av.": "av§", "apr.": "apr§",
    }
    for abbr, placeholder in _ABBREV_MAP.items():
        text = re.sub(re.escape(abbr), placeholder, text, flags=re.IGNORECASE)

    # Split on sentence-ending punctuation (. ! ? ;)
    raw = re.split(r"(?<=[.!?;])\s+", text)

    # Restore abbreviations and filter
    sentences: list[str] = []
    for s in raw:
        for abbr, placeholder in _ABBREV_MAP.items():
            s = s.replace(placeholder, abbr)
        s = s.strip()
        # Clean leading punctuation/bullet remnants
        s = re.sub(r"^[.,:;\-\u2013\u2014]\s*", "", s).strip()
        if len(s) < 25:
            continue
        alpha = sum(1 for c in s if c.isalpha())
        if alpha < len(s) * 0.4:
            continue
        # Skip pure Roman numeral lines
        if re.match(r"^[IVXLCDM\s.]+$", s):
            continue
        sentences.append(s)
    return sentences


# ── Scoring des phrases ───────────────────────────────────────────────

def _score_sentences(
    sentences: list[str],
    chapter_title: str,
) -> list[tuple[float, int, str]]:
    """Attribue un score de pertinence à chaque phrase."""
    title_words = {w.lower() for w in chapter_title.split() if len(w) > 2}
    total = len(sentences)
    scored: list[tuple[float, int, str]] = []

    for idx, sentence in enumerate(sentences):
        words = sentence.split()
        n_words = len(words)
        if n_words < 5:
            continue

        # Position bonus (beginning of chapter = more informative)
        pos_ratio = idx / max(total, 1)
        if pos_ratio < 0.25:
            position_score = 1.0
        elif pos_ratio > 0.85:
            position_score = 0.85
        else:
            position_score = 0.65

        # Length: prefer complete sentences (10-35 words)
        if n_words < 8:
            length_score = 0.5
        elif n_words <= 35:
            length_score = min(n_words / 18.0, 1.0)
        else:
            length_score = 0.7

        # Lexical diversity
        unique_ratio = len(set(w.lower() for w in words)) / n_words

        # Noise penalty
        special = sum(1 for c in sentence if c in "(){}[]=<>|&@#$%^*~`\\")
        noise = 1.0 if special < 3 else (0.5 if special < 6 else 0.2)

        # Title relevance bonus
        overlap = len({w.lower() for w in words} & title_words) if title_words else 0
        title_bonus = 1.0 + overlap * 0.15

        # Definition / explanation bonus
        definition = 1.0
        if re.search(
            r"\b(est un|est une|est le|est la|consiste à|permet de|désigne|"
            r"se définit|on appelle|on parle de|on distingue|il existe|"
            r"c['\u2019]est|signifie|fait référence)\b",
            sentence,
            re.IGNORECASE,
        ):
            definition = 1.35

        # Penalty for trivial aside sentences (no educational value)
        aside_penalty = 1.0
        if re.match(
            r"^\s*(c['\u2019]est[-\s]à[-\s]dire|par exemple|autrement dit|"
            r"en d['\u2019]autres termes|en effet|en fait|en résumé|"
            r"c['\u2019]est[-\s]à[-\s]dire que|soit)\b",
            sentence,
            re.IGNORECASE,
        ):
            aside_penalty = 0.4
        # Very short sentences are also less useful
        if n_words < 10:
            aside_penalty *= 0.6

        # Penalty for outline / plan lines (Roman numerals, numbering)
        if re.search(r"\b(I{1,3}|IV|VI{0,3}|IX|XI{0,3})\.\s", sentence):
            aside_penalty *= 0.5

        # Bullet penalty
        bullet = 0.85 if sentence[0] in "•●■▪→-*" else 1.0

        # Fragment penalty: lowercase start = continuation, not standalone
        fragment_penalty = 1.0
        if sentence[0].islower():
            fragment_penalty = 0.5
        if re.match(
            r"^\s*(et\s|mais\s|ou\s|car\s|donc\s|ni\s|or\s|puis\s|"
            r"cependant|toutefois|néanmoins|pourtant|alors\s)",
            sentence, re.IGNORECASE,
        ):
            fragment_penalty *= 0.6

        # Math-heavy penalty: math notation makes poor summary bullets
        math_chars = len(re.findall(r"[ˆ∂∇σαβγδεζηθλμπρτφψω∈∉∀∃∑∏∫≈≤≥±×÷√∞]", sentence))
        math_penalty = 1.0
        if math_chars > 3:
            math_penalty = 0.3
        elif math_chars > 1:
            math_penalty = 0.6

        # Incomplete sentence penalty: ends with ":" or ";" (header, not content)
        incomplete_penalty = 1.0
        stripped_end = sentence.rstrip()
        if stripped_end and stripped_end[-1] in ":;":
            incomplete_penalty = 0.3

        # Content-dump penalty: very long sentences are plan/outline dumps
        dump_penalty = 1.0
        if n_words > 80:
            dump_penalty = 0.3
        elif n_words > 50:
            dump_penalty = 0.5
        colon_count = sentence.count(":")
        if colon_count > 3:
            dump_penalty *= 0.4

        score = (
            position_score * length_score * unique_ratio
            * noise * title_bonus * definition * bullet * aside_penalty
            * fragment_penalty * math_penalty * incomplete_penalty * dump_penalty
        )
        scored.append((score, idx, sentence))

    return scored


# ── Détection de page de couverture / métadonnées ─────────────────────

_COVER_PATTERNS = re.compile(
    r"\b(licence|master|ingénierie|département|professeur|"
    r"pr\.\s|module|3iasd|gim|faculté|université)\b",
    re.IGNORECASE,
)


def _is_cover_or_metadata(text: str) -> bool:
    """Détecte si un texte est juste une page de couverture / métadonnées."""
    cleaned = _clean_source_text(text)
    words = cleaned.split()
    if len(words) < 30:
        # Very short text — check if it's mostly metadata
        matches = len(_COVER_PATTERNS.findall(cleaned))
        word_count = len(words)
        if word_count > 0 and matches / word_count > 0.15:
            return True
        # If very short and no real educational content
        if word_count < 15:
            return True
    return False


# ── Résumé extractif structuré ────────────────────────────────────────

def _extractive_summary(
    text: str,
    chapter_title: str = "",
    max_sentences: int = 8,
    other_titles: list[str] | None = None,
) -> str:
    """Génère un résumé extractif structuré en points clés."""
    cleaned = _clean_source_text(text)
    sentences = _split_into_sentences(cleaned)

    # Deduplicate: fuzzy word-overlap > 60% → keep longer
    unique: list[str] = []
    for s in sentences:
        s_words = set(s.lower().split())
        is_dup = False
        for i, existing in enumerate(unique):
            e_words = set(existing.lower().split())
            overlap = len(s_words & e_words)
            smaller = min(len(s_words), len(e_words))
            if smaller > 0 and overlap / smaller > 0.6:
                if len(s) > len(existing):
                    unique[i] = s
                is_dup = True
                break
        if not is_dup:
            unique.append(s)

    if not unique:
        return ""

    # Remove sentences that are just the chapter title echoed back
    title_lower = chapter_title.lower().strip()
    title_words = set(title_lower.split())
    # Also collect other chapter titles to detect cross-chapter bleed
    other_title_lowers = []
    if other_titles:
        other_title_lowers = [t.lower().strip() for t in other_titles if t.lower().strip() != title_lower]

    if len(title_words) >= 2 or other_title_lowers:
        filtered: list[str] = []
        for s in unique:
            s_lower = s.lower().strip()
            # Skip if sentence starts with or equals this chapter's title
            if len(title_words) >= 2:
                if s_lower.startswith(title_lower):
                    continue
                # Skip if first few words overlap heavily with title
                s_first_words = set(s_lower.split()[:len(title_words) + 2])
                overlap = len(s_first_words & title_words)
                if len(title_words) > 0 and overlap / len(title_words) >= 0.8:
                    continue
            # Skip if sentence starts with another chapter's title (cross-chapter bleed)
            skip = False
            for ot in other_title_lowers:
                if s_lower.startswith(ot):
                    skip = True
                    break
                # Also check if first 4+ words match another title
                ot_words = set(ot.split())
                if len(ot_words) >= 3:
                    s_first = set(s_lower.split()[:len(ot_words) + 2])
                    if len(s_first & ot_words) / len(ot_words) >= 0.8:
                        skip = True
                        break
            if skip:
                continue
            filtered.append(s)
        unique = filtered if filtered else unique

    scored = _score_sentences(unique, chapter_title)
    if not scored:
        return ""

    # Adaptive max sentences based on content length
    content_length = len(cleaned)
    if content_length < 500:
        adaptive_max = 3
    elif content_length < 1500:
        adaptive_max = 4
    elif content_length < 3000:
        adaptive_max = 5
    elif content_length < 5000:
        adaptive_max = 6
    elif content_length < 8000:
        adaptive_max = 7
    elif content_length < 12000:
        adaptive_max = 8
    else:
        adaptive_max = min(10, 5 + content_length // 3000)
    effective_max = min(max_sentences, adaptive_max)

    # Normalize scores to [0, 1] for MMR
    max_score = max(s[0] for s in scored)
    if max_score > 0:
        scored = [(s / max_score, idx, sent) for s, idx, sent in scored]
    scored.sort(key=lambda x: x[0], reverse=True)

    # MMR-style diverse selection: balance relevance and topic coverage
    selected: list[tuple[float, int, str]] = [scored[0]]
    remaining = list(scored[1:])

    while len(selected) < effective_max and remaining:
        best_idx = -1
        best_mmr = -1.0

        for i, (score, idx, sent) in enumerate(remaining):
            s_words = set(sent.lower().split())
            max_sim = 0.0
            for _, _, sel_sent in selected:
                sel_words = set(sel_sent.lower().split())
                intersection = len(s_words & sel_words)
                union = len(s_words | sel_words)
                if union > 0:
                    sim = intersection / union
                    max_sim = max(max_sim, sim)
            # λ=0.6: slightly favor relevance over diversity
            mmr = 0.6 * score + 0.4 * (1.0 - max_sim)
            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = i

        if best_idx >= 0:
            selected.append(remaining.pop(best_idx))
        else:
            break

    # Re-order by original position for coherence
    selected.sort(key=lambda x: x[1])

    # Build structured bullet-point summary with cleanup
    points: list[str] = []
    for _, _, sentence in selected:
        s = re.sub(r"^[•●■▪→\-\*\d]+[.):\s]*\s*", "", sentence).strip()
        # Remove nested bullets within the sentence
        s = re.sub(r"\s*[•●■▪]\s*", " ", s).strip()
        # Strip inline author watermarks (e.g., "Y.TAOUIL Deep Learning / 106")
        s = re.sub(
            r"[A-Z]\.\s*[A-Z][A-Za-z\u00e9\u00e8\u00ea\u00e0\u00e2]+"
            r"(?:\s+[A-Za-z\u00e9\u00e8\u00ea\u00e0\u00e2]+){1,3}\s*/\s*(?:\d{1,3}\s*)?",
            " ", s,
        ).strip()
        # Clean trailing ellipsis artifacts (single …, …., ..., etc.)
        s = re.sub(r",?\s*…+\.?\s*$", ".", s)
        s = re.sub(r"\.{2,}\s*$", ".", s)
        # Remove Roman numeral artifacts at end
        s = re.sub(r"\s+[IVXLCDM]{1,4}\.\s*$", ".", s)
        # Remove trailing author/page watermarks (e.g. "Y.TAOUIL Deep Learning / 106")
        s = re.sub(r"\s+[A-Z]\.[A-Z][A-Za-zéèêàâ]+\s.*?/\s*\d+\.?\s*$", ".", s)
        s = re.sub(r"\s+\d{2,3}\.\s*$", ".", s)
        # Also clean standalone page numbers at end (e.g. "... 106.")
        s = re.sub(r"\s+\d{1,3}\s*\.\s*$", ".", s)
        # Clean colon/semicolon before period (e.g., "ressources:.")
        s = re.sub(r"[:;]\.", ".", s)
        # Clean trailing colon/semicolon/comma (incomplete sentence)
        s = re.sub(r"[;:,]\s*$", ".", s)
        # Max bullet length: truncate at ~300 chars at sentence boundary
        if len(s) > 300:
            cut = s[:300].rfind(". ")
            if cut > 100:
                s = s[:cut + 1]
            else:
                cut = s[:300].rfind(", ")
                if cut > 100:
                    s = s[:cut] + "."
                else:
                    s = s[:297] + "..."
        if not s or len(s) < 15:
            continue
        if s[-1] not in ".!?":
            s += "."
        s = s[0].upper() + s[1:]
        points.append(s)

    return "\n".join(f"• {p}" for p in points) if points else ""


# ── Extraction des concepts clés ──────────────────────────────────────

def _extract_key_concepts(text: str, max_concepts: int = 6) -> list[str]:
    """Extrait les concepts clés via spaCy NER + noun chunks + fréquence."""
    nlp = _get_spacy()
    if nlp is None:
        return []

    # Clean source text first to remove institutional/watermark noise
    text = _clean_source_text(text)
    text = _fix_glued_words(text)

    doc = nlp(text[:5000])
    concept_scores: dict[str, float] = {}

    # Named entities (skip PERSON — author names aren't educational concepts)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            continue
        if ent.label_ not in ("ORG", "MISC", "LOC", "EVENT", "PRODUCT"):
            continue
        term = _clean_concept(ent.text.strip())
        if not _is_valid_concept(term):
            continue
        concept_scores[term] = concept_scores.get(term, 0) + 2.0

    # Noun chunks for multi-word concepts (e.g. "déni de service")
    for chunk in doc.noun_chunks:
        term = _clean_concept(chunk.text.strip())
        words = term.split()
        if len(words) < 2 or len(words) > 4:
            continue
        # At least one meaningful word (not in stop concepts)
        meaningful = [w for w in words if w.lower() not in _STOP_CONCEPTS and len(w) > 2]
        if not meaningful:
            continue
        if not _is_valid_concept(term):
            continue
        # Boost capitalized / technical terms
        has_upper = any(w[0].isupper() for w in words if w)
        bonus = 1.5 if has_upper else 1.0
        concept_scores[term] = concept_scores.get(term, 0) + bonus

    # Frequent nouns (lemmatized, ≥ 2 occurrences)
    noun_freq: dict[str, tuple[str, int]] = {}
    for token in doc:
        if token.pos_ not in ("NOUN", "PROPN") or token.is_stop or len(token.text) < 4:
            continue
        lemma = token.lemma_.lower()
        if lemma in _STOP_CONCEPTS or not lemma.isalpha():
            continue
        display = token.text.strip().capitalize()
        if not _is_valid_concept(display):
            continue
        if lemma not in noun_freq:
            noun_freq[lemma] = (display, 0)
        _, cnt = noun_freq[lemma]
        noun_freq[lemma] = (noun_freq[lemma][0], cnt + 1)

    for lemma, (display, count) in noun_freq.items():
        if count >= 2 and display not in concept_scores:
            concept_scores[display] = count * 0.5

    # Boost acronyms (all-caps terms ≥ 3 chars, validated)
    for token in doc:
        t = token.text.strip()
        if t.isupper() and len(t) >= 3 and t.isalpha() and t.lower() not in _STOP_CONCEPTS:
            if _is_valid_concept(t):
                concept_scores[t] = concept_scores.get(t, 0) + 2.5

    sorted_concepts = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)
    concepts: list[str] = []
    seen_lower: set[str] = set()
    for term, _ in sorted_concepts:
        # Clean concept before final check
        term = _clean_concept(term)
        if not _is_valid_concept(term):
            continue
        lower = term.lower()
        if lower in seen_lower or lower in _STOP_CONCEPTS:
            continue
        # Don't add if a longer/shorter version already present
        is_subset = False
        for existing in concepts:
            if lower in existing.lower() or existing.lower() in lower:
                is_subset = True
                break
        if is_subset:
            continue
        seen_lower.add(lower)
        concepts.append(term)
        if len(concepts) >= max_concepts:
            break

    return concepts


def _is_valid_concept(term: str) -> bool:
    """Vérifie qu'un concept est valide (pas un artefact PDF, pas trop générique)."""
    if len(term) < 3 or len(term) > 40:
        return False
    if not term[-1].isalnum():
        return False
    # Reject concepts containing colons (e.g. "Pas d'apprentissage: Rien sur comment")
    if ":" in term:
        return False
    if re.search(r"[●■▪•→○\(\)\[\]]", term):
        return False
    if term.lower() in _STOP_CONCEPTS:
        return False
    # Reject glued words (e.g. "Accèsà", "Sécuritéréseau", "Modèlepourla")
    if _GLUED_WORD_RE.search(term):
        return False
    # Broader glued-word detection: common endings fused with common words
    if _GLUED_ENDINGS.search(term):
        return False
    # Concepts ending in a preposition/article (e.g. "Accèsà", "Modèlede")
    if _CONCEPT_ENDS_WITH_PREPOSITION.search(term):
        return False
    # Single-token concepts that are suspiciously long (likely glued)
    if " " not in term and len(term) > 16:
        return False
    # Reject terms with Roman numerals appended (e.g. "HTTPS VI")
    if re.search(r"\s+(VI|VII|VIII|IX|XI|XII|III|IV)\s*$", term):
        return False
    # Reject 1-2 char all-caps codes
    if len(term) <= 2 and term.isupper():
        return False
    # Reject standalone Roman numerals (I, II, III, IV, etc.)
    if re.match(r"^[IVXLCDM]+$", term):
        return False
    # Reject author/watermark/page-number patterns
    if _AUTHOR_WATERMARK_RE.search(term):
        return False
    # Reject concepts with math symbols
    if _MATH_SYMBOLS_RE.search(term):
        return False
    # Reject concepts containing newlines
    if "\n" in term:
        return False
    # Reject concepts starting with verb infinitives
    if _INFINITIVE_START_RE.match(term):
        return False
    # Reject concepts that are mostly digits (page references)
    digit_count = sum(1 for c in term if c.isdigit())
    if digit_count > 0 and digit_count / len(term) > 0.3:
        return False
    # Reject concepts with isolated single-letter tokens (math variables)
    words = term.split()
    if len(words) > 5:
        return False
    if len(words) > 1:
        single_letters = [w for w in words if len(w) == 1 and w.isalpha() and w.lower() != "à"]
        if single_letters:
            return False
    return True


# ── Résumé d'un chapitre ──────────────────────────────────────────────

def summarize_chapter(
    chapter_text: str,
    chapter_title: str,
    pages: list[int],
    other_titles: list[str] | None = None,
) -> dict:
    """Génère un résumé structuré pour un chapitre."""
    # Detect cover / metadata-only chapters
    if _is_cover_or_metadata(chapter_text):
        return {
            "title": chapter_title,
            "summary": "",
            "pages": pages,
            "key_concepts": [],
        }

    summary = _extractive_summary(chapter_text, chapter_title, other_titles=other_titles)
    key_concepts = _extract_key_concepts(chapter_text)

    # Remove concepts that are just the chapter title
    title_lower = chapter_title.lower().strip()
    key_concepts = [c for c in key_concepts if c.lower().strip() != title_lower]

    return {
        "title": chapter_title,
        "summary": summary,
        "pages": pages,
        "key_concepts": key_concepts,
    }


# ---------------------------------------------------------------------------
# Merge chapters — regroupe les petits chapitres en sections logiques
# ---------------------------------------------------------------------------

def _merge_chapters_for_summary(
    raw_chapters: list[dict],
    min_content_chars: int = 500,
    max_chapters: int = 12,
) -> list[dict]:
    """Fusionne les chapitres trop petits en sections logiques."""
    if not raw_chapters:
        return []

    # Phase 0: Detect and merge cover/metadata chapters into the next real chapter
    filtered: list[dict] = []
    pending_cover: dict | None = None
    for ch in raw_chapters:
        if _is_cover_or_metadata(ch["text"]):
            if pending_cover is None:
                pending_cover = {
                    "title": ch["title"],
                    "text": ch["text"],
                    "pages": set(ch["pages"]),
                }
            else:
                pending_cover["text"] += "\n" + ch["text"]
                pending_cover["pages"] |= set(ch["pages"])
        else:
            if pending_cover is not None:
                # Merge cover into this real chapter
                ch["text"] = pending_cover["text"] + "\n" + ch["text"]
                ch["pages"] = set(ch["pages"]) | pending_cover["pages"]
                pending_cover = None
            filtered.append(ch)
    # If all chapters were cover pages (unlikely), keep them
    if not filtered:
        filtered = raw_chapters
    elif pending_cover is not None:
        # Trailing cover merges into last chapter
        filtered[-1]["text"] += "\n" + pending_cover["text"]
        filtered[-1]["pages"] = set(filtered[-1]["pages"]) | pending_cover["pages"]

    # Phase 1: Forward-merge small chapters
    merged: list[dict] = []
    buffer: dict | None = None

    for ch in filtered:
        if buffer is None:
            buffer = {
                "title": ch["title"],
                "text": ch["title"] + "\n" + ch["text"],
                "pages": set(ch["pages"]),
            }
        else:
            buffer["text"] += "\n\n" + ch["title"] + "\n" + ch["text"]
            buffer["pages"] |= set(ch["pages"])

        content_len = len(buffer["text"].strip())
        if content_len >= min_content_chars:
            merged.append(buffer)
            buffer = None

    if buffer is not None:
        if merged:
            merged[-1]["text"] += "\n\n" + buffer["text"]
            merged[-1]["pages"] |= buffer["pages"]
        else:
            merged.append(buffer)

    # Phase 2: Iteratively merge smallest if too many chapters
    while len(merged) > max_chapters:
        min_idx = min(range(len(merged)), key=lambda j: len(merged[j]["text"]))
        if min_idx < len(merged) - 1:
            merge_with = min_idx + 1
        else:
            merge_with = min_idx - 1
        a, b = min(min_idx, merge_with), max(min_idx, merge_with)
        merged[a]["text"] += "\n\n" + merged[b]["text"]
        merged[a]["pages"] |= merged[b]["pages"]
        merged.pop(b)

    logger.info("Fusion chapitres : %d → %d sections", len(raw_chapters), len(merged))
    return merged


def summarize_course(chunks: list[dict]) -> list[dict]:
    """Génère les résumés de tous les chapitres d'un cours."""
    # Step 0: Détection universelle des watermarks (texte répété sur les pages)
    watermarks = _detect_watermarks(chunks)

    # Step 1: Group chunks by chapter (preserving order), strip watermarks à la volée
    chapter_order: list[str] = []
    chapter_data: dict[str, dict] = {}
    for chunk in chunks:
        ch_raw = chunk.get("chapter", "Sans titre")
        # Réparer les ligatures aussi dans le titre (qui vient du PDF)
        ch = _repair_ligatures(ch_raw)
        if ch not in chapter_data:
            chapter_order.append(ch)
            chapter_data[ch] = {"title": ch, "text": "", "pages": set()}
        # Supprimer les watermarks détectés dynamiquement
        clean_text = _strip_watermarks(chunk["text"], watermarks)
        # Réparer les ligatures fi/fl/ff perdues à l'extraction
        clean_text = _repair_ligatures(clean_text)
        chapter_data[ch]["text"] += "\n" + clean_text
        chapter_data[ch]["pages"].add(chunk["page"])

    raw_chapters = [chapter_data[ch] for ch in chapter_order]

    # Step 2: Merge small / cover chapters
    merged = _merge_chapters_for_summary(raw_chapters)

    # Step 3: Generate summaries
    all_titles = [data["title"] for data in merged]
    summaries = []
    total = len(merged)
    for i, data in enumerate(merged, 1):
        logger.info("Résumé chapitre %d/%d : %s", i, total, data["title"])
        result = summarize_chapter(
            chapter_text=data["text"].strip(),
            chapter_title=data["title"],
            pages=sorted(data["pages"]),
            other_titles=all_titles,
        )
        # Only include chapters with actual content
        if result["summary"]:
            summaries.append(result)
        else:
            logger.info("Chapitre '%s' ignoré (couverture/métadonnées)", data["title"])

    logger.info("Résumés générés : %d chapitres", len(summaries))

    # Step 4: Cross-chapter concept deduplication
    # Remove concepts that appear in >60% of chapters (too generic for this course)
    if len(summaries) >= 3:
        concept_chapter_count: Counter[str] = Counter()
        for s in summaries:
            for c in s["key_concepts"]:
                concept_chapter_count[c.lower()] += 1

        threshold = len(summaries) * 0.6
        overrepresented = {c for c, cnt in concept_chapter_count.items() if cnt > threshold}

        if overrepresented:
            for s in summaries:
                s["key_concepts"] = [
                    c for c in s["key_concepts"]
                    if c.lower() not in overrepresented
                ]

    return summaries
