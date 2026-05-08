# EduAI — Architecture Backend : Rôle de chaque fichier & Pipeline Upload PDF

> Document technique de référence pour comprendre l'organisation du backend FastAPI,
> le rôle exact de chaque fichier, et le déroulement complet du pipeline d'upload PDF.

---

## Table des matières

1. [Vue d'ensemble de l'arborescence](#1-vue-densemble-de-larborescence)
2. [Couche racine — Point d'entrée & Configuration](#2-couche-racine)
3. [Couche `database/` — Accès aux données](#3-couche-database)
4. [Couche `models/` — Schémas de validation](#4-couche-models)
5. [Couche `routers/` — Contrôleurs HTTP](#5-couche-routers)
6. [Couche `services/` — Logique métier & IA](#6-couche-services)
7. [Pipeline d'upload PDF — Étape par étape](#7-pipeline-dupload-pdf)
8. [Mécanisme détaillé du pipeline NLP/ML](#8-mécanisme-détaillé-du-pipeline-nlpml)
9. [Diagramme de flux complet](#9-diagramme-de-flux-complet)
10. [Glossaire débutant — Chaque technologie expliquée simplement](#10-glossaire-débutant)

---

## 1. Vue d'ensemble de l'arborescence

```
backend/
├── main.py                   ← Point d'entrée FastAPI (lifespan, CORS, routers)
├── config.py                 ← Configuration centralisée (pydantic-settings)
├── requirements.txt          ← Dépendances Python
├── Dockerfile                ← Image Docker production
│
├── database/
│   └── mongodb.py            ← Connexion Motor async + CRUD helpers
│
├── models/
│   └── schemas.py            ← Tous les schémas Pydantic (request/response)
│
├── routers/                  ← 9 routers HTTP (un domaine = un fichier)
│   ├── auth.py
│   ├── courses.py            ← ⭐ Upload PDF + pipeline indexation
│   ├── qa.py
│   ├── summary.py
│   ├── quiz.py
│   ├── flashcards.py
│   ├── mindmap.py
│   ├── exam.py
│   └── export.py
│
└── services/                 ← Moteurs IA/NLP (la vraie intelligence)
    ├── auth.py               ← JWT + bcrypt
    ├── pdf_extractor.py      ← Extraction texte PyMuPDF
    ├── chunker.py            ← Découpage en chunks
    ├── embedder.py           ← MiniLM → vecteurs 384-d
    ├── retriever.py          ← Index FAISS (création, recherche, suppression)
    ├── qa_engine.py          ← CamemBERT extractif (fallback Q&A)
    ├── summarizer.py         ← spaCy + TextRank (extractif)
    ├── llm_client.py         ← Client HTTP Groq/Ollama (générique)
    ├── llm_qa.py             ← Prompts RAG conversationnel
    ├── llm_summarizer.py     ← Prompts résumé pédagogique
    ├── llm_quiz.py           ← Prompts génération QCM
    ├── llm_flashcards.py     ← Prompts génération flashcards
    ├── llm_mindmap.py        ← Prompts génération mind map
    ├── llm_exam.py           ← Prompts génération examen simulé
    ├── quiz_generator.py     ← Ancien générateur T5 (legacy, non utilisé en prod)
    └── retriever.py          ← Index FAISS
```

---

## 2. Couche Racine

### `main.py` — Point d'entrée de l'application

**Rôle :** C'est le fichier qui lance toute l'application. FastAPI s'instancie ici.

**Ce qu'il fait exactement :**

- Définit le `lifespan` (événements démarrage/arrêt) qui s'exécute une seule fois au boot :
  1. Configure les variables d'environnement pour le cache HuggingFace
  2. Ouvre la connexion MongoDB via `connect_db()`
  3. **Pré-charge le modèle MiniLM** en mémoire (warmup) pour que le premier upload ne soit pas lent
  4. Vérifie la disponibilité du LLM Groq (non bloquant — si indisponible, mode fallback extractif)
- Configure le middleware **CORS** (autorise le frontend Next.js à communiquer)
- Enregistre les **9 routers** dans cet ordre : auth, courses, qa, summary, quiz, flashcards, mindmap, exam, export
- Gère les erreurs globales (handler 500 avec traceback)

```
POST http://backend/api/auth/...      → router auth.py
POST http://backend/api/courses/...   → router courses.py
...
```

---

### `config.py` — Configuration centralisée

**Rôle :** Source unique de vérité pour tous les paramètres de l'application.

**Ce qu'il fait exactement :**

- Définit la classe `Settings` (hérite de `pydantic-settings BaseSettings`)
- Lit les valeurs depuis les **variables d'environnement** (ou `.env`)
- Accessible partout via `get_settings()` (cache `@lru_cache` → instance unique)

**Paramètres clés gérés :**

| Catégorie | Paramètre              | Valeur défaut                           |
| --------- | ---------------------- | --------------------------------------- |
| DB        | `mongodb_url`          | `mongodb://localhost:27017`             |
| DB        | `mongodb_db_name`      | `eduai_db`                              |
| ML        | `embedding_model`      | `paraphrase-multilingual-MiniLM-L12-v2` |
| ML        | `qa_model`             | `camembert-base-squadFR-fquad-piaf`     |
| NLP       | `chunk_size`           | `400` mots                              |
| NLP       | `chunk_overlap`        | `50` mots                               |
| LLM       | `llm_backend`          | `groq`                                  |
| LLM       | `groq_model`           | `llama-3.3-70b-versatile`               |
| Upload    | `max_pdf_size_mb`      | `50` MB                                 |
| Upload    | `max_courses_per_user` | `20`                                    |
| FAISS     | `faiss_index_dir`      | `data/faiss_indexes/`                   |

---

## 3. Couche `database/`

### `database/mongodb.py` — Connexion & CRUD

**Rôle :** Couche d'accès aux données. Tout ce qui touche MongoDB passe par ce fichier.

**Ce qu'il fait exactement :**

- Maintient une **connexion Motor async globale** (client + db en singleton module-level)
- Expose `connect_db()` et `close_db()` pour le lifespan
- Expose `get_db()` pour récupérer l'instance de la base n'importe où
- Fournit tous les **helpers CRUD** utilisés par les routers :

| Fonction                    | Collection                                                        | Opération                        |
| --------------------------- | ----------------------------------------------------------------- | -------------------------------- |
| `insert_course()`           | `courses`                                                         | insertOne                        |
| `get_all_courses()`         | `courses`                                                         | find (filtré par user_id)        |
| `get_course_by_id()`        | `courses`                                                         | findOne                          |
| `delete_course_by_id()`     | `courses` + `chunks` + `qa_sessions` + `summaries` + `quiz_cache` | deleteOne + deleteMany (cascade) |
| `insert_chunks()`           | `chunks`                                                          | insertMany                       |
| `get_chunks_by_course()`    | `chunks`                                                          | find                             |
| `update_course_status()`    | `courses`                                                         | updateOne                        |
| `save_qa_exchange()`        | `qa_exchanges`                                                    | insertOne                        |
| `get_qa_history()`          | `qa_exchanges`                                                    | find (par session)               |
| `get_cached_summary()`      | `summaries`                                                       | findOne                          |
| `save_cached_summary()`     | `summaries`                                                       | replaceOne (upsert)              |
| `get_cached_course_quiz()`  | `quiz_cache`                                                      | findOne                          |
| `save_cached_course_quiz()` | `quiz_cache`                                                      | replaceOne (upsert)              |

> **Note sécurité :** Toutes les requêtes qui touchent des données d'un cours filtrent
> sur `user_id` pour éviter qu'un utilisateur accède aux données d'un autre.

---

## 4. Couche `models/`

### `models/schemas.py` — Validation des données

**Rôle :** Définit la forme exacte de toutes les données qui entrent et sortent de l'API.

**Ce qu'il fait exactement :**

- Déclare tous les modèles **Pydantic v2** pour la validation automatique
- FastAPI utilise ces schémas pour : valider les requêtes, sérialiser les réponses, générer la doc OpenAPI

**Schémas principaux :**

| Schéma                 | Utilisé par          | Description                               |
| ---------------------- | -------------------- | ----------------------------------------- |
| `CourseUploadResponse` | POST /courses/upload | Réponse après upload                      |
| `CourseInfo`           | GET /courses         | Info résumée d'un cours                   |
| `CourseDetail`         | GET /courses/{id}    | Détail complet (chapitres, statut)        |
| `QuestionRequest`      | POST /qa/ask         | Corps de la question posée                |
| `AnswerResponse`       | GET /qa/stream       | Réponse complète avec sources             |
| `SummaryResponse`      | GET /summary/{id}    | Fiche pédagogique complète                |
| `ChapterSummary`       | (imbriqué)           | Résumé d'un chapitre                      |
| `QuizQuestion`         | GET /quiz/{id}       | Une question QCM                          |
| `QuizSubmission`       | POST /quiz/submit    | Réponses soumises par l'étudiant          |
| `QuizResult`           | POST /quiz/submit    | Score + corrections                       |
| `PipelineMeta`         | GET /summary/{id}    | Métadonnées du pipeline NLP/ML            |
| `PipelineStep`         | (imbriqué)           | Détail d'une étape (nom, modèle, famille) |

---

## 5. Couche `routers/`

Chaque router correspond à un domaine fonctionnel. Il est enregistré dans `main.py` avec un préfixe `/api/`.

---

### `routers/auth.py` — Authentification

**Endpoints :**

- `POST /api/auth/register` → crée un compte (hash bcrypt + JWT)
- `POST /api/auth/login` → connecte un utilisateur (vérifie hash + JWT)
- `GET /api/auth/me` → restaure la session depuis le token JWT

---

### `routers/courses.py` — Gestion des cours ⭐

**Le router le plus important.** C'est lui qui déclenche le pipeline upload PDF.

**Endpoints :**

- `POST /api/courses/upload` → **déclenche tout le pipeline** (voir section 7)
- `GET /api/courses` → liste les cours de l'utilisateur connecté
- `GET /api/courses/{id}` → détail d'un cours (avec recovery si stuck "processing")
- `DELETE /api/courses/{id}` → supprime cours + chunks MongoDB + index FAISS

**Mécanisme de recovery intégré :**
Si le serveur redémarre pendant une indexation, le statut reste "processing".
Quand l'étudiant recharge, le `GET /{id}` détecte cet état bloqué :

- Si le `.faiss` existe sur disque → marque "ready" directement
- Sinon → relance l'indexation depuis les chunks déjà sauvegardés en MongoDB

---

### `routers/qa.py` — Questions-Réponses (RAG)

**Endpoints :**

- `GET /api/qa/stream` → stream SSE token par token (réponse LLM ou CamemBERT)
- `GET /api/qa/history/{session_id}` → historique d'une session (existe mais non appelé par le frontend)

**Flux interne :**

1. Embed la question (MiniLM)
2. Cherche dans FAISS (top-3 chunks, seuil ≥ 0.30)
3. Charge les 3 derniers tours de l'historique MongoDB
4. Appelle `stream_answer_with_llm()` → SSE token par token
5. Si LLM indisponible → fallback `answer_question()` CamemBERT

---

**Méthode technique — Questions & Réponses (RAG)**
_Vectorisation de la question, recherche sémantique dans les passages du cours, génération streaming par LLM._

**`01`** **Pré-indexation du cours** — `Base`
Lors de l'upload, tous les passages du cours ont déjà été convertis en vecteurs et stockés dans un index FAISS sur disque. Cette étape est faite une seule fois — pas à chaque question.

> `Stack : MiniLM · paraphrase-multilingual-MiniLM-L12-v2 + FAISS · IndexFlatIP`

**`02`** **Vectorisation de la question** — `Apprentissage`
La question tapée par l'étudiant est convertie en vecteur de 384 nombres avec le même modèle MiniLM, pour qu'elle soit comparable aux vecteurs des passages du cours.

> `Stack : MiniLM · embed_query → vecteur (384,) normalisé`

**`03`** **Recherche sémantique** — `Recherche`
FAISS compare le vecteur de la question aux vecteurs de tous les passages et retourne les 3 passages les plus proches sémantiquement. Un seuil de 0.30 filtre les passages non pertinents (score trop bas = hors-sujet).

> `Stack : FAISS · IndexFlatIP.search (top-3, seuil score ≥ 0.30)`

**`04`** **Injection du contexte & historique** — `Mémoire`
Les 3 passages pertinents sont ajoutés au prompt envoyé au LLM, ainsi que les 3 derniers échanges de la conversation. Cela donne au LLM la mémoire de court terme et le contenu du cours en même temps.

> `Stack : MongoDB · get_chunks_by_course + get_qa_history (3 tours)`

**`05`** **Génération RAG streaming** — `LLM`
Le LLM génère une réponse pédagogique structurée (Définition, Explication, Exemple, À retenir, Sources [1][2]) et l'envoie **token par token** au navigateur en temps réel. C'est pour ça que le texte s'affiche progressivement — exactement comme ChatGPT.

> `Stack : Groq · llama-3.3-70b-versatile (SSE — Server-Sent Events)`

**`06`** **Fallback extractif** — `Sécurité`
Si Groq est indisponible (panne réseau, quota dépassé), CamemBERT prend le relais. Il extrait directement la réponse en surlignant le passage concerné, sans reformuler. Moins riche, mais toujours fonctionnel.

> `Stack : CamemBERT · camembert-base-squadFR-fquad-piaf`

---

### `routers/summary.py` — Résumés pédagogiques

**Endpoints :**

- `GET /api/summary/{course_id}` → génère ou retourne la fiche depuis le cache

**Flux interne :**

1. Vérifie le cache MongoDB (`summaries` collection)
2. Si cache HIT → retourne instantanément
3. Si cache MISS → pipeline `summarize_course()` (spaCy + TextRank) puis `refine_chapter()` (LLM)
4. Sauvegarde en cache et retourne

Expose aussi `pregenerate_summary_in_background()` utilisé lors de l'upload.

---

**Méthode technique — Synthèse pédagogique**
_Extraction linguistique, résumé extractif par graphe de similarité, reformulation narrative par LLM._

**`01`** **Extraction & segmentation** — `NLP`
Le PDF est lu page par page. Le texte est découpé en passages de ≈400 mots avec un overlap de 50 mots pour préserver le sens aux jonctions entre passages. Cette étape est faite une seule fois lors de l'upload.

> `Stack : PyMuPDF (fitz) + chunker maison`

**`02`** **Analyse linguistique** — `NLP`
Chaque passage est analysé grammaticalement : les mots sont tokenisés, leur nature grammaticale identifiée (nom, verbe, adjectif...), et les entités importantes reconnues (noms de concepts, acronymes, termes techniques).

> `Stack : spaCy · fr_core_news_lg (tokenisation, POS-tagging, NER)`

**`03`** **Résumé extractif** — `NLP`
Les phrases de chaque chapitre sont classées par importance via un graphe de similarité : une phrase est "importante" si de nombreuses autres phrases lui ressemblent. L'algorithme sélectionne les phrases les plus centrales.

> `Stack : TextRank · scoring multi-critères (graph-based ranking)`

**`04`** **Reformulation pédagogique** — `LLM`
Le LLM reçoit les phrases extraites (pas le PDF brut) et les reformule en fiche de révision narrative fluide : prose continue, pas de liste à puces, pas d'émojis, structurée par chapitre avec titre, corps et concepts clés.

> `Stack : Groq · llama-3.3-70b-versatile`

**`05`** **Cache MongoDB** — `Cache`
La fiche générée est mise en cache. Les prochaines consultations retournent le résultat instantanément sans relancer le pipeline coûteux. La pré-génération se déclenche automatiquement juste après l'indexation FAISS.

> `Stack : MongoDB · collection summaries (upsert)`

---

### `routers/quiz.py` — Quiz interactif

**Endpoints :**

- `GET /api/quiz/{course_id}` → génère ou retourne le quiz (param `?regenerate=true` ignore le cache)
- `POST /api/quiz/submit` → calcule le score, retourne corrections

Expose aussi `pregenerate_quiz_in_background()` utilisé lors de l'upload.

---

**Méthode technique — Quiz interactif**
_Sélection diversifiée des passages du cours, génération QCM par LLM, anti-biais et mise en cache._

**`01`** **Sélection diversifiée des passages** — `Données`
Des passages représentatifs sont sélectionnés en couvrant tous les chapitres du cours. L'algorithme veille à l'équilibre : pas trop de questions sur un seul chapitre, contenu varié.

> `Stack : algorithme de sélection par chapitre (Python maison)`

**`02`** **Génération QCM par LLM** — `LLM`
Un seul appel LLM génère toutes les questions en même temps en mode JSON strict. Chaque question contient : l'énoncé, 4 options de réponse, l'index de la bonne réponse (0-3), une explication pédagogique.

> `Stack : Groq · llama-3.3-70b-versatile (JSON mode strict)`

**`03`** **Validation du JSON** — `Contrôle`
Chaque question générée est validée automatiquement : 4 options non vides et uniques, index correct entre 0 et 3, explication présente. Les questions invalides sont écartées silencieusement.

> `Stack : validation Python maison`

**`04`** **Anti-biais aléatoire** — `Qualité`
Les 4 options de chaque question sont mélangées aléatoirement après génération. Sans cette étape, le LLM a tendance à toujours mettre la bonne réponse en première position (biais statistique).

> `Stack : random.shuffle() sur les options + recalcul de correct_index`

**`05`** **Cache & correction serveur** — `Cache`
Le quiz est mis en cache pour les prochaines consultations. Les corrections (score + explications) sont calculées côté serveur uniquement lors de la soumission — jamais exposées avant pour éviter la triche.

> `Stack : MongoDB · collection quiz_cache (upsert)`

---

### `routers/flashcards.py` — Flashcards SM-2

**Endpoints :**

- `POST /api/flashcards/generate` → génère N flashcards via LLM
- `GET /api/flashcards/deck/{course_id}` → charge le jeu de cartes
- `POST /api/flashcards/review` → applique l'algorithme SM-2, met à jour les params

---

**Méthode technique — Flashcards & Répétition espacée**
_Génération de cartes question/réponse par LLM, mémorisation adaptative par l'algorithme SM-2._

**`01`** **Sélection du contenu représentatif** — `Données`
Les passages les plus denses en information sont sélectionnés (maximum 5000 caractères) pour couvrir les concepts importants du cours sans surcharger le contexte du LLM.

> `Stack : algorithme de sélection par densité (Python maison)`

**`02`** **Génération des cartes** — `LLM`
Le LLM génère N flashcards structurées. Chaque carte a un recto (question courte), un verso (réponse concise), et un niveau de difficulté. Le format JSON est strict pour faciliter la validation.

> `Stack : Groq · llama-3.3-70b-versatile → {front, back, difficulty}`

**`03`** **Validation & structuration** — `Contrôle`
Chaque carte est validée : recto et verso non vides, difficulté dans la liste autorisée (easy/medium/hard). Les cartes incomplètes sont écartées. Le JSON est normalisé.

> `Stack : validation Python maison`

**`04`** **Initialisation SM-2** — `Apprentissage`
Chaque nouvelle carte reçoit les paramètres initiaux de l'algorithme de répétition espacée : intervalle de 1 jour, facteur de facilité de 2.5 (valeur neutre), 0 répétitions réussies.

> `Stack : algorithme SM-2 (SuperMemo 2) · interval=1, ease_factor=2.5, repetitions=0`

**`05`** **Révision adaptative** — `Apprentissage`
À chaque révision, l'étudiant donne un score (1–5). L'algorithme SM-2 recalcule l'intervalle et le facteur de facilité : les cartes difficiles reviennent dans 1 jour, les faciles dans plusieurs semaines. `next_review` est stocké en base.

> `Stack : SM-2 · recalcul interval + ease_factor + next_review · MongoDB flashcards`

---

### `routers/mindmap.py` — Carte mentale

**Endpoints :**

- `GET /api/mindmap/{course_id}` → génère ou retourne le graphe (nodes + edges) depuis le cache

---

**Méthode technique — Carte mentale**
_Extraction des chapitres et concepts, génération d'un graphe structuré par LLM, fallback automatique si LLM indisponible._

**`01`** **Extraction des chapitres** — `Données`
Les titres de chapitres détectés lors de l'upload (texte avec police 1.3× plus grande que le texte normal, ou gras ≥ 14pt) servent de nœuds racines de la carte mentale.

> `Stack : données existantes · pdf_extractor (titres détectés à l'upload)`

**`02`** **Sélection des extraits par chapitre** — `Données`
Les premiers passages de chaque chapitre sont sélectionnés pour donner au LLM le contenu à cartographier. Maximum 4000 caractères au total pour ne pas dépasser la fenêtre de contexte.

> `Stack : algorithme maison · premiers chunks par chapitre`

**`03`** **Génération du graphe** — `LLM`
Le LLM génère la structure complète de la carte en JSON : liste de nœuds (maximum 25) avec leur type (chapitre / concept / détail) et liste d'arêtes avec des étiquettes décrivant la relation entre nœuds.

> `Stack : Groq · llama-3.3-70b-versatile → {nodes[], edges[]} (JSON mode)`

**`04`** **Validation de la structure** — `Contrôle`
Chaque nœud est validé : `{id, label, type, chapter}`. Chaque arête : `{source, target, label}`. Les arêtes pointant vers des nœuds inexistants sont corrigées ou supprimées pour éviter un graphe cassé.

> `Stack : validation Python maison`

**`05`** **Fallback structurel** — `Sécurité`
Si Groq est indisponible, une carte mentale basique est générée automatiquement à partir des seuls chapitres détectés, sans LLM. Moins riche visuellement mais toujours utilisable.

> `Stack : Python maison · _fallback_mindmap(chapters, chunks)`

**`06`** **Cache** — `Cache`
Le graphe généré est mis en cache pour les consultations suivantes. Le recalcul n'est déclenché que si le cache est absent ou si l'utilisateur force une régénération.

> `Stack : MongoDB · collection mindmap_cache`

---

### `routers/exam.py` — Examen simulé

**Endpoints :**

- `POST /api/exam/start` → génère des questions QCM (sans `correct_index` dans la réponse = anti-triche)
- `POST /api/exam/submit` → calcule score, note A–F, `passed = score ≥ 60%`

---

**Méthode technique — Mode Examen**
_Génération de QCM à difficulté équilibrée, protection anti-triche côté serveur, notation par lettre._

**`01`** **Sélection équilibrée des passages** — `Données`
Les passages sont sélectionnés en couvrant tous les chapitres et en respectant le mix de difficultés voulu : 30% facile, 50% moyen, 20% difficile. Cela garantit un examen représentatif de l'ensemble du cours.

> `Stack : algorithme de sélection pondéré par chapitre et difficulté`

**`02`** **Génération des questions d'examen** — `LLM`
Le LLM génère des questions avec contexte d'examen explicite (consigne de rigueur, pas de devinettes). Chaque question indique : énoncé, 4 options, index correct, explication et niveau de difficulté.

> `Stack : Groq · llama-3.3-70b-versatile (JSON mode · mix 30/50/20 easy/medium/hard)`

**`03`** **Anti-triche serveur** — `Sécurité`
Le `correct_index` (la bonne réponse) est stocké uniquement en MongoDB côté serveur. La réponse envoyée au frontend au démarrage de l'examen ne contient **jamais** cet index. Il n'est accessible qu'au moment de la correction.

> `Stack : MongoDB · exam_sessions (correct_index stocké serveur uniquement)`

**`04`** **Session d'examen** — `Session`
Les questions sont liées à un identifiant de session unique stocké en base. Le timer s'exécute uniquement côté client (le serveur ne coupe pas la session à la fin du temps — décision UX).

> `Stack : MongoDB · collection exam_sessions`

**`05`** **Correction & notation par lettre** — `Correction`
À la soumission, les réponses sont comparées aux bonnes réponses en base. Le score calcule automatiquement la note : A (≥ 90%), B (≥ 80%), C (≥ 70%), D (≥ 60%), F (< 60%). Un champ `passed` indique si l'examen est réussi.

> `Stack : logique Python maison · seuil passed = score ≥ 60%`

---

### `routers/export.py` — Export PDF

**Endpoints :**

- `GET /api/export/summary/{course_id}` → génère et télécharge le résumé en PDF
- `GET /api/export/flashcards/{course_id}` → génère et télécharge les flashcards en PDF

---

**Méthode technique — Export PDF**
_Récupération des données MongoDB, mise en page professionnelle avec la palette EduAI, génération en mémoire et réponse binaire._

**`01`** **Authentification & récupération des données** — `Sécurité`
Avant toute génération, le serveur vérifie que le cours appartient bien à l'utilisateur connecté (filtre `user_id`). Les données (résumé ou flashcards) sont ensuite récupérées depuis MongoDB.

> `Stack : JWT Bearer + MongoDB · courses + summaries / flashcards`

**`02`** **Mise en page du document** — `Design`
Le contenu est structuré en éléments visuels : page de couverture avec bandeau coloré, en-tête EduAI sur chaque page avec le nom du cours, numérotation de bas de page, séparation visuelle par chapitre ou par carte.

> `Stack : ReportLab · SimpleDocTemplate, onFirstPage (cover), onLaterPages (header/footer)`

**`03`** **Styles visuels & palette EduAI** — `Design`
Chaque type d'élément (titre, corps de texte, concept-clé, label de section) utilise un style typographique défini avec la palette officielle EduAI : fond crème `#F6F3EF`, accent brun-orange `#B85B2A`, texte sombre `#171412`.

> `Stack : ReportLab · ParagraphStyle, HexColor, TableStyle`

**`04`** **Génération en mémoire** — `Rendu`
Le PDF est construit entièrement en mémoire dans un buffer Python (`io.BytesIO`). Aucun fichier temporaire n'est créé sur le disque du serveur. Une fois généré, le buffer est rembobiné au début pour être lu.

> `Stack : ReportLab · doc.build() → io.BytesIO`

**`05`** **Réponse binaire streaming** — `Transport`
Le buffer PDF est retourné directement comme réponse HTTP binaire. Le nom du fichier est nettoyé (accents supprimés, espaces remplacés) pour être compatible avec tous les navigateurs.

> `Stack : FastAPI · StreamingResponse, Content-Type: application/pdf, Content-Disposition: attachment`

---

## 6. Couche `services/`

Ce sont les moteurs. Ils ne savent rien de HTTP. Ils reçoivent des données, font le travail, retournent des résultats.

---

### `services/auth.py` — Authentification JWT + bcrypt

**Ce qu'il fait exactement :**

- `hash_password(password)` → `bcrypt.hash(password[:72])` (limite 72 bytes, sécurité bcrypt)
- `verify_password(plain, hashed)` → `bcrypt.verify(plain[:72], hashed)`
- `create_access_token(user_id, email)` → JWT HS256 avec expiration 7 jours
- `decode_token(token)` → vérifie signature + expiration, retourne payload
- `get_current_user(credentials)` → **dépendance FastAPI** injectée dans tous les endpoints protégés

---

### `services/pdf_extractor.py` — Extraction texte PDF

**Ce qu'il fait exactement :**

- Utilise **PyMuPDF (fitz)** pour lire le PDF page par page
- Pour chaque page, récupère les blocs de texte avec leurs **métadonnées de mise en forme** (taille police, flags gras)
- Détecte les **titres de chapitres** via deux critères :
  - `taille_police > médiane_page × 1.3` (titre nettement plus grand que le texte normal)
  - OU `gras ET taille ≥ 14pt`
- Suit le chapitre courant et l'attache à chaque bloc de texte
- Retourne une liste de `PageBlock` : `{page_num, text, is_title, chapter_name}`
- Rejette les PDFs protégés par mot de passe (exception `ValueError`)
- Nettoie le texte (numéros de page isolés, en-têtes répétés)

**Ce qu'il ne fait PAS :** il ne découpe pas en chunks. Il extrait uniquement le texte structuré.

---

### `services/chunker.py` — Découpage en chunks

**Ce qu'il fait exactement :**

- Reçoit les `PageBlock[]` de `pdf_extractor`
- Regroupe les blocs par **chapitre** (les blocs "is_title" servent de séparateurs)
- Pour chaque chapitre, découpe le texte en **chunks de ≈400 mots avec 50 mots d'overlap** :
  - Split par phrases (regex `[.!?]\s+`) pour respecter les limites naturelles
  - Construit un chunk en accumulant des phrases jusqu'à atteindre `chunk_size` mots
  - Le chunk suivant commence en reprenant les `chunk_overlap` derniers mots du chunk précédent
- Retourne une liste de `Chunk` : `{text, page, chapter, chunk_index}`

**Pourquoi l'overlap ?** Pour que les questions qui chevauchent deux chunks puissent trouver le contexte dans l'un ou l'autre.

---

### `services/embedder.py` — Vecteurs sémantiques MiniLM

**Ce qu'il fait exactement :**

- Charge le modèle **`paraphrase-multilingual-MiniLM-L12-v2`** en **singleton** (une seule fois au warmup)
- Détecte automatiquement CUDA/CPU
- `embed_texts(texts[])` → encode une liste de textes en **matrice numpy (N × 384)**  
  (vecteurs normalisés L2, batch size 128)
- `embed_query(query)` → encode une seule question en **vecteur (384,)** normalisé
- Les vecteurs sont normalisés → le produit scalaire (Inner Product) équivaut à la cosine similarity

**Pourquoi ce modèle ?** Il est multilingue (français + anglais + 50 langues), léger (384 dims vs 768 pour BERT full), et très bon pour la recherche sémantique.

---

### `services/retriever.py` — Index FAISS

**Ce qu'il fait exactement :**

- **`create_index(course_id, embeddings)`** :
  - Crée un `faiss.IndexFlatIP` (produit intérieur = cosine similarity sur vecteurs normalisés)
  - Ajoute tous les embeddings des chunks
  - Sauvegarde sur disque : `data/faiss_indexes/{course_id}.faiss`
  - Met en cache en mémoire dans `_index_cache` dict
- **`search(course_id, query_vector, k=3)`** :
  - Charge l'index depuis le cache mémoire ou depuis le disque
  - Appelle `index.search(query_vector, k)` → retourne les k indices de chunks les plus proches + leurs scores
- **`delete_index(course_id)`** :
  - Supprime le fichier `.faiss` sur disque
  - Purge du cache mémoire

**Un index par cours.** La recherche sur 1000 chunks = quelques millisecondes (FAISS est ultra-optimisé).

---

### `services/qa_engine.py` — CamemBERT extractif (fallback Q&A)

**Ce qu'il fait exactement :**

- Charge le modèle **`camembert-base-squadFR-fquad-piaf`** (Question Answering extractif français)
- Reçoit une question + les chunks récupérés par FAISS
- Concatène les chunks en contexte (max 2000 chars pour tenir dans 512 tokens BERT)
- Tokenise `[question, contexte]` et passe au modèle
- Extrait le span de réponse (start_logits / end_logits) directement depuis le texte source
- Retourne `{answer, confidence, sources}`

**Quand est-il utilisé ?** Uniquement si le LLM Groq est indisponible (`LLMUnavailable`).
La réponse est moins riche (pas de reformulation pédagogique) mais toujours correcte factuelment.

---

### `services/summarizer.py` — Analyse NLP (spaCy + TextRank)

**Ce qu'il fait exactement :**

- Charge **spaCy `fr_core_news_lg`** (tokenisation, POS-tagging, lemmatisation, NER)
- Reçoit les chunks d'un cours
- Pour chaque chapitre :
  - Analyse linguistique complète avec spaCy
  - Filtre les phrases parasites (longueur, ponctuation, répétitions)
  - Applique un scoring **TextRank** (graphe de similarité entre phrases) pour extraire les plus représentatives
  - Extrait les **concepts clés** via NER (entités nommées) + POS-tagging (noms propres/communs importants)
  - Filtre les stop-concepts (liste exhaustive de ~200 termes génériques comme "chose", "page", "cours"...)
- Retourne une structure par chapitre : `{title, bullets[], key_concepts[], pages[]}`

**Ce n'est pas le résumé final.** C'est la matière première fournie au LLM pour la reformulation.

---

### `services/llm_client.py` — Client LLM générique

**Ce qu'il fait exactement :**

- Abstrait l'accès au LLM (Groq Cloud ou Ollama local selon `LLM_BACKEND`)
- Pattern singleton via `get_client()` → retourne `GroqClient` ou `OllamaClient`
- **Health check** avec cache 30 secondes (évite de spammer le service)
- **`chat(system, user, ...)`** → génère du texte (streaming désactivé)
- **`generate_json(prompt)`** → génère du JSON strict (utilise `response_format=json_object` chez Groq)
- **`stream_chat(system, user, history)`** → retourne un `AsyncIterator[str]` token par token (SSE)
- Gère les **retries** automatiques et lève `LLMUnavailable` si tout échoue

> **Clarification importante — Groq vs Ollama vs Llama :**
> Ces trois noms désignent des choses très différentes.
> Voir la [Section 10 — Glossaire débutant](#10-glossaire-débutant) pour une explication complète.
>
> En production sur EduAI : **seul Groq est utilisé** (`LLM_BACKEND=groq`).
> Ollama est du code de secours présent dans le fichier mais jamais activé tant que Groq fonctionne.
> Llama est le **nom du modèle d'IA** — ni Groq ni Ollama ne sont le modèle, ce sont les _moyens d'y accéder_.

---

### `services/llm_summarizer.py` — Prompts résumé

**Ce qu'il fait exactement :**

- Reçoit le résultat extractif de `summarizer.py` (bullets + concepts par chapitre)
- Détecte la langue du cours (`fr` ou `en`) via heuristique sur les 400 premiers mots
- Choisit le prompt système (FR ou EN) — instructions strictes : prose continue, pas d'émojis, pas de listes à puces
- Appelle `llm_client.chat()` pour **reformuler chaque chapitre en fiche de révision narrative**
- Le LLM voit uniquement le matériel extrait (pas le PDF brut) → anti-hallucination + tient dans le contexte

---

### `services/llm_qa.py` — Prompts Q&A conversationnel

**Ce qu'il fait exactement :**

- `answer_with_llm()` → réponse complète (non-streaming)
- `stream_answer_with_llm()` → réponse en streaming SSE token par token
- Gère 3 types de messages : salutations (réponse courte naturelle), questions sur le cours (markdown structuré avec sources), hors-sujet (refus poli)
- Injecte le contexte : chunks pertinents (numérotés [1], [2]...) + historique des 3 derniers tours
- Interdit les émojis dans les réponses

---

### `services/llm_quiz.py` — Génération QCM

**Ce qu'il fait exactement :**

- Sélectionne des passages diversifiés à travers les chapitres
- Envoie **un seul appel LLM** avec demande JSON stricte
- Valide chaque question : 4 options uniques, index 0–3, explication
- Mélange (`shuffle`) les options après génération pour éviter le biais LLM (mettre la bonne réponse en A)

---

### `services/llm_flashcards.py` — Génération flashcards

**Ce qu'il fait exactement :**

- Sélectionne ~5000 chars de contenu représentatif
- Génère N flashcards via LLM au format `{front, back, difficulty}`
- Valide le JSON et normalise la structure

---

### `services/llm_mindmap.py` — Génération mind map

**Ce qu'il fait exactement :**

- Envoie les premiers chunks de chaque chapitre (max 4000 chars) + la liste des chapitres
- Génère un graphe JSON `{nodes[], edges[]}` avec `type ∈ {chapter, concept, detail}`
- Fallback si LLM indisponible : génère une mind map basique depuis les chapitres détectés

---

### `services/llm_exam.py` — Génération examen

**Ce qu'il fait exactement :**

- Génère des questions QCM d'examen avec mix de difficultés (30% facile, 50% moyen, 20% difficile)
- Le `correct_index` est bien généré et stocké en MongoDB
- **Mais il n'est PAS retourné au frontend** (anti-triche) → uniquement au moment de `POST /exam/submit`

---

### `services/quiz_generator.py` — Générateur T5 (legacy)

**Rôle :** Ancien générateur de quiz basé sur T5-QG + spaCy pour les distracteurs.
**Statut :** Non utilisé en production. Le quiz passe maintenant exclusivement par `llm_quiz.py` (LLM Groq) pour une meilleure qualité. Ce fichier reste dans la codebase mais n'est plus appelé.

---

## 7. Pipeline d'upload PDF — Étape par étape

Voici ce qui se passe **exactement**, ligne par ligne, quand un étudiant uploade un PDF.

### Phase 1 — Validation (synchrone, avant tout)

```
Frontend → POST /api/courses/upload
           multipart/form-data { file: PDF, course_name: "..." }
           Authorization: Bearer <JWT>
```

**Étape 1.1 — Authentification**

```python
current_user = Depends(get_current_user)
```

Le JWT dans le header est extrait et décodé. Si invalide ou expiré → `401 Unauthorized` immédiat.

**Étape 1.2 — Vérification du quota**

```python
user_courses_count = await db.courses.count_documents({"user_id": user_id})
if user_courses_count >= 20:
    raise HTTPException(403, "Limite atteinte")
```

Un utilisateur ne peut pas dépasser 20 cours.

**Étape 1.3 — Validation du fichier**

```python
if not file.filename.endswith(".pdf"):
    raise HTTPException(422, "Seuls les PDF sont acceptés")

file_bytes = await file.read()

size_mb = len(file_bytes) / (1024 * 1024)
if size_mb > 50:
    raise HTTPException(413, "Fichier trop volumineux")
```

Extension `.pdf` obligatoire. Taille max 50 MB.

---

### Phase 2 — Extraction du texte PDF (synchrone)

**Étape 2.1 — Lecture PyMuPDF**

```python
page_blocks = extract_pdf(file_bytes)
```

`pdf_extractor.py` ouvre le PDF **en mémoire** (pas de fichier temporaire sur disque), parcourt chaque page, extrait les blocs de texte avec leur style.

**Ce qui se passe page par page :**

```
Page 1 :
  Bloc "Introduction aux Réseaux"  → taille=18pt, gras → is_title=True, chapter_name="Introduction aux Réseaux"
  Bloc "Un réseau informatique est..." → taille=12pt → is_title=False, chapter_name="Introduction aux Réseaux"
  Bloc "Les protocoles permettent..." → taille=12pt → is_title=False, chapter_name="Introduction aux Réseaux"

Page 2 :
  Bloc "TCP/IP et les Couches"  → taille=16pt → is_title=True, chapter_name="TCP/IP et les Couches"
  ...
```

**Étape 2.2 — Comptage des pages**

```python
total_pages = get_total_pages(file_bytes)
```

---

### Phase 3 — Chunking (synchrone)

**Étape 3.1 — Découpage intelligent**

```python
chunks = create_chunks(page_blocks, chunk_size=400, chunk_overlap=50)
```

`chunker.py` regroupe d'abord les blocs par chapitre, puis pour chaque chapitre :

```
Chapitre "Introduction aux Réseaux" (800 mots) :

  Chunk 0 : mots 0–399   + métadonnées {page:1, chapter:"Introduction...", chunk_index:0}
  Chunk 1 : mots 350–749  (50 mots d'overlap avec chunk 0)
  Chunk 2 : mots 700–799  (dernier, plus court)

Chapitre "TCP/IP et les Couches" (600 mots) :

  Chunk 3 : mots 0–399
  Chunk 4 : mots 350–599
```

**Si aucun chunk** → le PDF ne contient pas de texte extractible (scan image) → `422 Unprocessable`.

**Étape 3.2 — Détection des chapitres**

```python
chapters = list({c["chapter"] for c in chunks})
# Ex: ["Introduction aux Réseaux", "TCP/IP et les Couches", "Sécurité Réseau"]
```

---

### Phase 4 — Sauvegarde initiale MongoDB (statut "processing")

**Étape 4.1 — Insertion du cours**

```python
course_data = {
    "user_id": user_id,
    "name": course_name,
    "filename": file.filename,
    "created_at": datetime.now(timezone.utc),
    "chunks_count": len(chunks),
    "pages": total_pages,
    "chapters": chapters,
    "status": "processing",   # ← important : pas encore "ready"
}
course_id = await insert_course(course_data)
```

Le cours est immédiatement visible dans la liste avec statut "processing".
Le `course_id` est un ObjectId MongoDB converti en string hexadécimale (ex: `69e633746ba4f898782d25a2`).

**Étape 4.2 — Insertion des chunks**

```python
for chunk in chunks:
    chunk["course_id"] = course_id
await insert_chunks(chunks)
```

Tous les chunks sont sauvegardés en MongoDB avec leur `course_id`.
**C'est une sécurité importante** : si le serveur redémarre pendant l'indexation,
les chunks sont déjà en base → la recovery peut relancer l'indexation.

---

### Phase 5 — Réponse immédiate au frontend

```python
return CourseUploadResponse(
    course_id=course_id,
    course_name=course_name,
    chunks_count=len(chunks),
    pages_count=total_pages,
    status="processing",
)
```

**Le frontend reçoit la réponse `200 OK` immédiatement** — sans attendre l'indexation FAISS.
Le statut `"processing"` déclenche un polling côté frontend.

---

### Phase 6 — Indexation FAISS (asynchrone en arrière-plan)

**Étape 6.1 — Lancement en arrière-plan**

```python
asyncio.create_task(_index_in_background(course_id, texts))
```

FastAPI continue de servir d'autres requêtes. L'indexation tourne en arrière-plan.

**Étape 6.2 — Génération des embeddings**

```python
embeddings = await asyncio.to_thread(embed_texts, texts)
```

`asyncio.to_thread` exécute `embed_texts()` dans un thread séparé (bloquant CPU)
pour ne pas bloquer la boucle d'événements asyncio.

Le modèle MiniLM encode tous les chunks :

```
["Un réseau informatique est...", "Les protocoles permettent...", ...]
→ numpy.ndarray shape (N_chunks, 384)   dtype=float32, vecteurs normalisés L2
```

**Étape 6.3 — Création de l'index FAISS**

```python
await asyncio.to_thread(create_index, course_id, embeddings)
```

```python
index = faiss.IndexFlatIP(384)   # Inner Product = cosine sim sur vecteurs normalisés
index.add(embeddings)             # Ajoute tous les vecteurs
faiss.write_index(index, f"data/faiss_indexes/{course_id}.faiss")
_index_cache[course_id] = index  # Cache mémoire pour les prochaines requêtes
```

Le fichier `.faiss` est persistant sur disque. Si le serveur redémarre, l'index est rechargé depuis le disque lors de la première recherche.

**Étape 6.4 — Mise à jour du statut**

```python
await update_course_status(course_id, "ready")
```

MongoDB : `{ "status": "ready" }` → le frontend détecte le changement via polling et arrête.

---

### Phase 7 — Pré-génération LLM (post-indexation, arrière-plan)

Immédiatement après que le statut passe à "ready" :

```python
asyncio.create_task(pregenerate_summary_in_background(course_id))
asyncio.create_task(pregenerate_quiz_in_background(course_id))
```

Ces deux tâches tournent **en parallèle** et de manière **non bloquante** :

- Génèrent la fiche pédagogique (spaCy + TextRank + Groq LLM)
- Génèrent le quiz par défaut (Groq LLM)
- Sauvegardent les résultats dans `summaries` et `quiz_cache`

**L'étudiant n'attend pas.** Quand il clique sur "Résumé" ou "Quiz", le cache est déjà prêt.

---

## 8. Mécanisme détaillé du pipeline NLP/ML

### Relation entre les services durant l'upload

```
pdf_extractor.py
    │  list[PageBlock]
    ▼
chunker.py
    │  list[Chunk] = [{text, page, chapter, chunk_index}]
    ▼
embedder.py (via asyncio.to_thread → CPU thread pool)
    │  numpy.ndarray (N_chunks × 384)
    ▼
retriever.py → faiss.IndexFlatIP.add(embeddings) → .faiss fichier sur disque
    │
    ▼
mongodb.py  → insert_chunks(chunks)   → collection "chunks"
            → update_course_status → "ready"
    │
    ▼ (en parallèle)
summarizer.py (spaCy + TextRank) + llm_summarizer.py (Groq LLM)
    └→ mongodb.py → save_cached_summary → collection "summaries"

llm_quiz.py (Groq LLM)
    └→ mongodb.py → save_cached_course_quiz → collection "quiz_cache"
```

### Ce qui reste après l'upload

Après un upload complet, ces données existent en base/disque :

| Stockage                        | Contenu                                                       |
| ------------------------------- | ------------------------------------------------------------- |
| `MongoDB.courses`               | Métadonnées du cours (nom, pages, chapitres, statut, user_id) |
| `MongoDB.chunks`                | Tous les chunks texte avec page + chapitre (N documents)      |
| `MongoDB.summaries`             | Fiche pédagogique générée (cache résumé)                      |
| `MongoDB.quiz_cache`            | Quiz QCM pré-généré (cache quiz)                              |
| `data/faiss_indexes/{id}.faiss` | Index vectoriel binaire pour la recherche sémantique          |

### Cycle de vie lors d'une question (Q&A)

Une fois le cours indexé, une question de l'étudiant déclenche ce flux :

```
Question : "Qu'est-ce que le protocole TCP ?"
    │
    ▼ embed_query() — MiniLM
    vector (384,) normalisé
    │
    ▼ retriever.search() — FAISS IndexFlatIP
    [
      {index: 12, score: 0.87},  ← chunk le plus proche sémantiquement
      {index: 13, score: 0.81},
      {index: 7,  score: 0.74},
    ]
    │
    ▼ get_chunks_by_course() — MongoDB
    (traduit les index FAISS → textes réels)
    [
      {text: "TCP (Transmission Control Protocol) est...", page: 5, chapter: "TCP/IP"},
      {text: "La connexion TCP s'établit via...", page: 5, chapter: "TCP/IP"},
      {text: "Les ports TCP permettent...", page: 6, chapter: "TCP/IP"},
    ]
    │
    ▼ Seuil de pertinence (score ≥ 0.30)
    Tous les 3 sont pertinents → passer au LLM
    │
    ▼ get_qa_history() — MongoDB (3 derniers tours)
    historique = [{role:"user", content:"..."}, {role:"assistant", content:"..."}]
    │
    ▼ stream_answer_with_llm() — Groq LLM (streaming)
    "TCP (Transmission Control Protocol) est un **protocole de transport**
    orienté connexion défini dans la couche Transport du modèle OSI..."
    │ (tokens streamés un par un via SSE)
    ▼
Frontend — affichage progressif dans le ChatInterface
```

---

## 9. Diagramme de flux complet

```
FRONTEND                        BACKEND (FastAPI)                    SERVICES & DATA

  Upload PDF
  ─────────────────────────────→ POST /api/courses/upload
                                  │
                                  ├─ [1] Authentification JWT          services/auth.py
                                  ├─ [2] Vérif quota (MongoDB)         database/mongodb.py
                                  ├─ [3] Validation (type, taille)
                                  │
                                  ├─ [4] extract_pdf()         ──→     services/pdf_extractor.py
                                  │       ↳ PyMuPDF page par page      (détection titres/chapitres)
                                  │
                                  ├─ [5] create_chunks()       ──→     services/chunker.py
                                  │       ↳ 400 mots + 50 overlap      (split par phrases)
                                  │
                                  ├─ [6] insert_course()       ──→     MongoDB.courses  status="processing"
                                  ├─ [7] insert_chunks()       ──→     MongoDB.chunks
                                  │
  ← 200 { course_id, status:"processing" }
  │ (réponse immédiate)
  │
  │ polling GET /api/courses/{id}
  │                               │
  │                               ▼ asyncio.create_task (arrière-plan)
  │
  │                         _index_in_background()
  │                               │
  │                               ├─ [8] embed_texts()         ──→     services/embedder.py
  │                               │       ↳ MiniLM → (N × 384)         (asyncio.to_thread)
  │                               │
  │                               ├─ [9] create_index()        ──→     services/retriever.py
  │                               │       ↳ FAISS IndexFlatIP           data/faiss_indexes/{id}.faiss
  │                               │
  │                               ├─[10] update_course_status  ──→     MongoDB.courses  status="ready"
  │                               │
  │                               ├─[11] pregenerate_summary() ──→     summarizer + llm_summarizer
  │                               │       ↳ spaCy + TextRank + LLM      MongoDB.summaries
  │                               │
  │                               └─[12] pregenerate_quiz()    ──→     llm_quiz
  │                                       ↳ Groq LLM → QCM              MongoDB.quiz_cache
  │
  ← status:"ready"
  Cours prêt — fonctionnalités débloquées
```

---

## Résumé des technologies par service

| Service               | Technologie                          | Rôle dans le pipeline                                 |
| --------------------- | ------------------------------------ | ----------------------------------------------------- |
| `pdf_extractor.py`    | PyMuPDF (fitz)                       | Lecture PDF + structuration page/chapitre             |
| `chunker.py`          | Python natif (regex)                 | Découpage phrases-aware avec overlap                  |
| `embedder.py`         | sentence-transformers + MiniLM       | Représentation vectorielle sémantique 384-d           |
| `retriever.py`        | FAISS IndexFlatIP                    | Recherche cosine similarity ultra-rapide              |
| `summarizer.py`       | spaCy fr_core_news_lg + TextRank     | Analyse NLP + extraction phrases clés                 |
| `qa_engine.py`        | CamemBERT-SquadFR                    | QA extractif (fallback sans LLM)                      |
| `llm_client.py`       | httpx async                          | Client HTTP Groq Cloud / Ollama                       |
| `llm_*.py`            | Groq llama-3.3-70b                   | Génération naturelle (résumés, QCM, flashcards, exam) |
| `database/mongodb.py` | Motor async                          | Persistance (cours, chunks, cache, historique)        |
| `services/auth.py`    | python-jose (JWT) + passlib (bcrypt) | Authentification sécurisée                            |

---

## 10. Glossaire débutant

> Cette section est écrite pour quelqu'un qui découvre l'IA et le développement backend.
> Chaque technologie est expliquée avec une analogie du monde réel, son rôle exact dans EduAI,
> et pourquoi elle a été choisie.

---

### PyMuPDF (aussi appelé `fitz`)

**C'est quoi ?**
Une bibliothèque Python qui sait lire les fichiers PDF. C'est comme avoir un "lecteur PDF" programmable qui ne se contente pas d'afficher le texte, mais qui te donne aussi des informations sur la mise en forme : taille des polices, si le texte est en gras, la position de chaque mot sur la page.

**Analogie :** Imagine que tu ouvres un livre PDF avec une loupe magique. La loupe te dit non seulement ce qui est écrit, mais aussi "ce mot est en gros caractères gras, donc c'est probablement un titre".

**Son rôle dans EduAI :**

- Ouvrir le PDF uploadé par l'étudiant
- Extraire tout le texte page par page
- Détecter les titres de chapitres (texte plus grand que la normale)
- Retourner une liste structurée de blocs de texte avec leur numéro de page et chapitre

**Pourquoi on l'a utilisé ?**
C'est l'une des bibliothèques PDF les plus rapides et les plus précises pour Python. Elle gère les PDF complexes (colonnes multiples, tableaux) mieux que les alternatives comme `pdfplumber` ou `pdfminer`. De plus, elle fonctionne entièrement en mémoire sans créer de fichiers temporaires sur le disque.

---

### MiniLM (modèle `paraphrase-multilingual-MiniLM-L12-v2`)

**C'est quoi ?**
Un modèle d'intelligence artificielle entraîné à comprendre le **sens** des phrases. Il transforme n'importe quel texte en une liste de 384 nombres (appelée "vecteur" ou "embedding"). Ces nombres représentent le sens du texte de manière mathématique.

**Analogie :** Imagine que chaque phrase est convertie en coordonnées GPS. Deux phrases qui veulent dire la même chose auront des coordonnées proches. "Le chien court vite" et "Le canidé se déplace rapidement" auront des coordonnées quasi-identiques, même si les mots sont différents.

**Ce que les 384 nombres représentent :**
Chaque nombre capture une dimension sémantique abstraite : le premier pourrait capturer "appartient au domaine médical", le deuxième "parle d'une action", etc. Personne ne sait exactement ce que chaque dimension signifie — c'est le réseau de neurones qui l'a appris tout seul.

**Son rôle dans EduAI :**

- Convertir chaque chunk de cours en vecteur (lors de l'upload)
- Convertir chaque question d'étudiant en vecteur (lors d'une Q&A)
- Permettre la comparaison mathématique entre la question et tous les chunks

**Pourquoi on l'a utilisé ?**

- **Multilingue** : fonctionne en français, anglais, arabe, et 50 autres langues
- **Léger** : 384 dimensions seulement (vs 768 pour BERT complet), donc rapide
- **Qualité élevée** : spécialement entraîné pour la recherche sémantique ("paraphrase" dans le nom)
- **Gratuit et local** : tourne sur la machine, pas besoin d'API externe

---

### Index FAISS (`faiss.IndexFlatIP`)

**C'est quoi ?**
FAISS (Facebook AI Similarity Search) est une bibliothèque créée par Meta (Facebook) pour faire des recherches ultra-rapides dans des millions de vecteurs. Un "index" FAISS est comme un annuaire téléphonique spécial, mais au lieu de chercher un nom, on cherche le vecteur le plus proche d'un autre vecteur.

**Analogie :** Tu as 1000 livres dans une bibliothèque. Chaque livre est représenté par ses coordonnées GPS. Quand tu veux trouver les 3 livres les plus proches de ta position, FAISS les trouve en quelques millisecondes au lieu de comparer ta position avec chacun des 1000 livres un par un.

**`IndexFlatIP` — qu'est-ce que ça veut dire ?**

- `Flat` = index simple (compare chaque vecteur un par un, mais très optimisé en C++)
- `IP` = Inner Product (produit intérieur). Sur des vecteurs normalisés, le produit intérieur est équivalent à la similarité cosinus — une mesure de l'angle entre deux vecteurs. Score de 1.0 = identiques, score de 0.0 = sans rapport

**Son rôle dans EduAI :**

- Stocker les vecteurs de tous les chunks d'un cours dans un fichier `.faiss`
- Quand l'étudiant pose une question, trouver les 3 chunks les plus pertinents en millisecondes
- Filtrer les chunks non pertinents (score < 0.30) pour éviter de donner du contexte hors-sujet au LLM

**Pourquoi on l'a utilisé ?**
Pour la rapidité. Une recherche dans 1000 chunks prend < 1ms avec FAISS. De plus, l'index est sauvegardé sur disque — pas besoin de recalculer à chaque redémarrage du serveur. C'est la solution standard pour les applications RAG (Retrieval-Augmented Generation).

---

### CamemBERT (`camembert-base-squadFR-fquad-piaf`)

**C'est quoi ?**
CamemBERT est un modèle d'IA spécialisé pour la **langue française**, développé par des chercheurs français (INRIA, Facebook). Son nom est un jeu de mot avec BERT (le modèle original de Google) et le camembert (fromage français). Il est entraîné à répondre à des questions en extrayant la réponse directement depuis un texte donné.

**Analogie :** Donne-lui un paragraphe de 3 lignes et une question. Il va surligner dans ce paragraphe exactement les mots qui répondent à ta question. C'est comme un étudiant qui souligne la réponse dans son livre.

**`squadFR-fquad-piaf` — qu'est-ce que ça veut dire ?**
Ce sont les noms des datasets (jeux de données d'entraînement) utilisés :

- `SQuAD-FR` : version française de SQuAD (Stanford Question Answering Dataset)
- `FQuAD` : French Question Answering Dataset
- `PIAF` : Pour une IA Francophone (dataset français de QA)

**Son rôle dans EduAI :**
Il est le **plan B** (fallback). Si Groq est en panne, CamemBERT prend le relais. Il lit les 3 chunks les plus pertinents et extrait directement la réponse depuis le texte — sans reformuler, sans inventer, sans enrichissement pédagogique.

**Différence avec le LLM (Groq/Llama) :**

|                 | CamemBERT                         | LLM (Llama via Groq)           |
| --------------- | --------------------------------- | ------------------------------ |
| Type            | Extractif (copie depuis le texte) | Génératif (rédige une réponse) |
| Hallucination   | Impossible (copie textuelle)      | Possible si mal guidé          |
| Richesse        | Réponse brute                     | Explication pédagogique        |
| Langue          | Français uniquement               | Multilingue                    |
| Besoin internet | Non (local)                       | Oui (API Groq)                 |

**Pourquoi on l'a utilisé ?**
Pour la robustesse. Si l'API Groq est indisponible (panne réseau, quota dépassé), l'application continue de fonctionner avec CamemBERT. Les étudiants ne voient jamais un message d'erreur d'IA.

---

### spaCy (`fr_core_news_lg`)

**C'est quoi ?**
spaCy est une bibliothèque de traitement du langage naturel (NLP = Natural Language Processing). Elle analyse le texte grammaticalement et linguistiquement : elle sait identifier les noms, verbes, sujets, objets, les entités (noms de personnes, de lieux, d'organisations), et peut lemmatiser les mots ("courons" → "courir").

**Analogie :** Un professeur de grammaire très avancé qui lit une phrase et peut te dire : "ce mot est un nom commun, ce mot est un verbe au présent, ce groupe nominal est le sujet, cette entité est une organisation".

**`fr_core_news_lg` — qu'est-ce que ça veut dire ?**

- `fr` = français
- `core` = modèle principal (vocabulaire + syntaxe + entités)
- `news` = entraîné sur des textes journalistiques
- `lg` = large (le plus précis, 560 MB, vs `sm` small 45 MB)

**Son rôle dans EduAI :**

- Tokeniser le texte des cours (diviser en mots/phrases)
- Identifier les entités nommées (NER) : noms de concepts importants, acronymes, termes techniques
- Filtrer les mots parasites (stop-words, ponctuation)
- Servir de base pour l'algorithme TextRank

**Pourquoi on l'a utilisé ?**
spaCy est la référence industrielle pour le NLP en Python. Il est beaucoup plus rapide et précis que NLTK (l'ancienne bibliothèque standard). Le modèle `lg` est nécessaire pour une bonne reconnaissance d'entités dans des textes scientifiques/techniques.

---

### TextRank

**C'est quoi ?**
TextRank est un **algorithme mathématique** (pas un modèle d'IA) qui classe les phrases d'un texte par importance. Il fonctionne exactement comme l'algorithme PageRank de Google (qui classe les pages web par importance), mais appliqué aux phrases.

**Comment ça fonctionne ?**

1. Prend toutes les phrases d'un chapitre
2. Compare chaque phrase avec toutes les autres (similarité de vocabulaire)
3. Construit un graphe : les phrases similaires sont reliées par des arêtes pondérées
4. Applique PageRank sur ce graphe : une phrase est "importante" si beaucoup d'autres phrases lui ressemblent
5. Sélectionne les N phrases avec le score le plus élevé

**Analogie :** Imagine 10 personnes dans une pièce. La personne la plus influente est celle avec qui le plus d'autres personnes sont d'accord. TextRank fait pareil avec les phrases : la phrase "centrale" qui capture l'essentiel de ce que disent les autres phrases reçoit le score le plus élevé.

**Son rôle dans EduAI :**
Avant d'envoyer le texte d'un chapitre entier au LLM (ce qui coûterait beaucoup de tokens), on utilise TextRank pour sélectionner les 5-10 phrases les plus représentatives de chaque chapitre. Le LLM reçoit ensuite ces phrases condensées pour rédiger la fiche de révision.

**Pourquoi on l'a utilisé ?**

- Gratuit et local (pas d'API)
- Aucune hallucination possible (ne génère rien, sélectionne juste)
- Très rapide (quelques millisecondes même pour 50 pages)
- Réduit la taille du contexte envoyé au LLM → moins de coût API + moins de risque de hallucination

---

### Llama (le modèle d'IA)

**C'est quoi ?**
Llama (Large Language Model Meta AI) est le **modèle d'intelligence artificielle** créé par **Meta (Facebook)**. C'est le "cerveau" — le système qui comprend les questions et génère des réponses en langage naturel, rédige des résumés, crée des QCM, etc.

**Analogie :** Llama est comme un expert humain très intelligent. La question est : comment accéder à cet expert ? Tu peux l'appeler au téléphone via un service (Groq), ou l'avoir directement chez toi (Ollama).

**Version utilisée dans EduAI :** `llama-3.3-70b-versatile`

- `3.3` = version 3.3 (la plus récente au moment du développement)
- `70b` = 70 milliards de paramètres (très grand, très intelligent)
- `versatile` = adapté à toutes les tâches (résumé, QCM, Q&A, etc.)

---

### Groq (le service cloud)

**C'est quoi ?**
Groq est une **entreprise** qui a développé des puces matérielles (LPU = Language Processing Unit) ultra-rapides pour faire tourner des modèles LLM. Ils proposent une **API cloud** : tu leur envoies une question, ils l'exécutent sur leurs serveurs avec Llama (ou d'autres modèles) et te retournent la réponse.

**Analogie :** Groq est comme Netflix pour les modèles d'IA. Netflix héberge les films sur ses serveurs, tu y accèdes via une connexion internet. Groq héberge Llama sur ses serveurs, tu y accèdes via une clé API.

**Comment ça fonctionne dans EduAI :**

```
EduAI Backend  ──→  API Groq  ──→  Llama 70B tourne sur les serveurs Groq
               ←── Réponse  ←──
```

**Ce que Groq fournit :**

- Une URL d'API compatible avec le format OpenAI
- Une clé API (variable d'environnement `GROQ_API_KEY`)
- Des serveurs très rapides (génération de texte 10x plus rapide que les GPU classiques)

**Pourquoi Groq et pas OpenAI/Claude ?**

- Vitesse : Groq est significativement plus rapide pour la génération de tokens
- Prix : niveau gratuit généreux pour le développement et les petits projets
- Llama est open-source : pas de dépendance à une entreprise propriétaire

---

### Ollama (l'alternative locale)

**C'est quoi ?**
Ollama est un **outil open-source** qui permet de télécharger et de faire tourner des modèles LLM (comme Llama) directement sur ton propre ordinateur ou serveur, sans connexion internet, sans clé API, sans envoyer tes données à une entreprise tierce.

**Analogie :** Si Groq est Netflix (streaming), Ollama est un DVD player (lecture locale). Le film (Llama) est le même — seul le moyen d'y accéder change.

**Différence fondamentale Groq vs Ollama :**

|                 | Groq                             | Ollama                                      |
| --------------- | -------------------------------- | ------------------------------------------- |
| Hébergement     | Cloud (serveurs Groq)            | Local (ton propre serveur)                  |
| Connexion       | Internet requise                 | Aucune connexion nécessaire                 |
| Configuration   | Clé API dans `.env`              | Installation sur le serveur                 |
| Vitesse         | Très rapide (LPU)                | Dépend du hardware local                    |
| Coût            | Gratuit (limité) / Payant        | Gratuit (mais tu paies le serveur)          |
| Confidentialité | Données envoyées à Groq          | Données restent en local                    |
| Modèle          | `llama-3.3-70b` hébergé par Groq | N'importe quel modèle téléchargé localement |

---

### Pourquoi Ollama est mentionné dans le code alors qu'on utilise Groq ?

Tu as posé une excellente question. Voici la réponse claire :

**La réponse courte :** Ollama est du **code de fallback** (plan de secours) qui ne s'exécute jamais en production tant que Groq fonctionne.

**La réponse longue :**
Le fichier `llm_client.py` a été conçu pour être **flexible** :

```python
# Dans config.py :
LLM_BACKEND = "groq"   # ← cette valeur décide tout

# Dans llm_client.py :
if settings.llm_backend == "groq":
    return GroqClient()    # ← en production : TOUJOURS ce chemin
else:
    return OllamaClient()  # ← jamais activé en prod (LLM_BACKEND != "groq")
```

**Dans quels cas Ollama serait utile ?**

- Un développeur qui veut travailler **hors ligne** (pas d'internet, pas de clé API)
- Un déploiement où la **confidentialité des données** est critique (hôpital, défense, etc.)
- Un test local avant de déployer avec Groq
- Si Groq devient payant ou disparaît → changer `LLM_BACKEND=ollama` suffit, aucun autre code à modifier

**Ce qui se passe réellement dans EduAI en production :**

```
.env : LLM_BACKEND=groq, GROQ_API_KEY=gsk_xxxx

EduAI → llm_client.py → GroqClient → API Groq → Llama 70B
                         OllamaClient  (jamais instancié)
```

Ollama n'est pas "actif" — il est juste disponible comme alternative si tu changes une ligne dans `.env`.

---

### Modèle T5 et `quiz_generator.py` (legacy)

**C'est quoi T5 ?**
T5 (Text-To-Text Transfer Transformer) est un modèle d'IA créé par **Google** en 2019. Son idée originale : traiter TOUTES les tâches NLP (traduction, résumé, QA, génération de questions) comme un problème de "texte vers texte". Tu lui donnes du texte, il te retourne du texte.

**Le modèle spécifique utilisé :** `valhalla/t5-base-qa-qg-hl`

- Spécialisé dans la génération de questions (QG = Question Generation)
- Prend un texte surligné (hl = highlight) et génère une question sur ce passage

**Pourquoi il a été remplacé ?**
T5 génère des questions mécaniques, souvent répétitives et grammaticalement bancales en français. Exemple :

- T5 : "What is the definition of TCP ?"
- Llama via Groq : "Dans le contexte du modèle OSI, quelle est la différence fondamentale entre TCP et UDP en termes de garantie de livraison ?"

La qualité du LLM est incomparablement supérieure. T5 a donc été gardé dans le code comme archive/documentation historique, mais n'est jamais appelé en production.

**Son statut :** `quiz_generator.py` existe dans le dossier `services/` mais aucun router ni aucun autre service ne l'importe ou l'appelle. Il est inactif.

---

### RAG — Retrieval-Augmented Generation

**C'est quoi ?**
RAG est le **nom de l'architecture globale** utilisée pour la fonctionnalité Q&A d'EduAI. Ce n'est pas une bibliothèque ou un modèle — c'est un pattern (une façon de concevoir un système).

**Sans RAG :** Tu poses une question à Llama → Llama répond avec ce qu'il a appris lors de son entraînement → ne connaît pas le contenu spécifique de ton cours.

**Avec RAG :**

1. **R**etrieval (Récupération) : On cherche dans le cours les passages pertinents (FAISS)
2. **A**ugmented (Enrichissement) : On injecte ces passages dans le contexte du LLM
3. **G**eneration (Génération) : Le LLM génère sa réponse en se basant sur ces passages

**Analogie :** C'est comme permettre à un expert de répondre à tes questions en ayant ton livre ouvert devant lui, au lieu de répondre de mémoire.

**Pourquoi c'est important ?**
Sans RAG, Llama ne saurait pas ce qu'il y a dans le cours d'un étudiant. Grâce à RAG, il peut répondre précisément en citant des passages du cours uploadé.

---

### JWT (JSON Web Token)

**C'est quoi ?**
Un JWT est un **ticket numérique signé** que le serveur donne à l'utilisateur après la connexion. L'utilisateur présente ce ticket à chaque requête pour prouver son identité.

**Analogie :** Comme un bracelet de festival. Quand tu entres et paies, on te donne un bracelet. Pour accéder aux scènes, tu montres le bracelet — pas besoin de repayer ou de te réidentifier.

**Structure d'un JWT :**

```
eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiNjllNjMzLi4uIn0.abc123signature
└─ header (algo) ─┘ └─────── payload (données) ────────┘ └── signature ──┘
```

**Dans EduAI :** Le JWT contient `user_id` et `email`. Il est valide 7 jours. La signature HS256 empêche toute falsification.

---

### bcrypt (hashage de mots de passe)

**C'est quoi ?**
bcrypt est un algorithme de **hachage** de mots de passe. Il transforme un mot de passe en une chaîne illisible impossible à inverser.

**Analogie :** Imagine un broyeur à papier. Tu mets le mot de passe dedans, tu obtiens une bouillie. On ne peut pas reconstruire le mot de passe depuis la bouillie. La seule façon de vérifier : broyer le nouveau mot de passe et comparer les bouillis.

**Pourquoi pas MD5 ou SHA256 ?**
bcrypt est intentionnellement **lent** (paramètre de "cost"). Même avec un ordinateur puissant, essayer tous les mots de passe possibles par force brute prend des années.

---

### SSE (Server-Sent Events)

**C'est quoi ?**
SSE est une technologie web qui permet au serveur d'envoyer des données au navigateur **en continu**, au fur et à mesure qu'elles sont disponibles, sans que le navigateur ait besoin de refaire une requête.

**Analogie :** C'est comme regarder un match de sport en direct au lieu d'attendre le résumé du lendemain. Le serveur t'envoie les informations dès qu'elles existent.

**Dans EduAI :** Quand le LLM génère une réponse mot par mot, chaque mot est envoyé immédiatement au navigateur via SSE. C'est pour ça que tu vois le texte s'afficher progressivement — exactement comme ChatGPT.

---

### SM-2 (algorithme des flashcards)

**C'est quoi ?**
SM-2 (SuperMemo 2) est un **algorithme de répétition espacée** inventé en 1987 par Piotr Wozniak. Il calcule la date optimale à laquelle revoir une flashcard en fonction de la facilité avec laquelle tu l'as retenue.

**Principe :** Si tu réponds facilement → la prochaine révision est dans longtemps. Si tu hésites → la prochaine révision est bientôt.

**Paramètres dans EduAI :**

- `interval` : nombre de jours avant la prochaine révision
- `ease_factor` : facteur de facilité (2.5 = normal, augmente si facile, diminue si difficile)
- `repetitions` : nombre de fois révisée avec succès
- `next_review` : date exacte de la prochaine révision (calculée par SM-2)

**Pourquoi on l'a utilisé ?** C'est le même algorithme que Anki (l'application de flashcards la plus utilisée au monde). Il est prouvé scientifiquement pour optimiser la mémorisation à long terme.
