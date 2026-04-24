# Cahier de Charge — EduAI

**Assistant Pédagogique Intelligent basé sur l'IA**

---

|                         |                                                                                         |
| ----------------------- | --------------------------------------------------------------------------------------- |
| **Réalisé par**         | EL MEHDI HACHAMI                                                                        |
| **Encadrant**           | Pr. ERRAJI MEHDI                                                                        |
| **Établissement**       | École Supérieure de Technologie d'Essaouira                                             |
| **Filière**             | Bachelor — Ingénierie Informatique en Intelligence Artificielle et Sciences des Données |
| **Type de projet**      | Projet de Fin d'Études (PFE)                                                            |
| **Année universitaire** | 2025–2026                                                                               |
| **Date de début**       | 27 avril 2026                                                                           |
| **Version**             | V1                                                                                      |

---

## 1. Contexte et problématique

Les étudiants universitaires font face à un volume croissant de supports de cours au format PDF, souvent denses et longs (parfois supérieurs à 100 pages). La révision efficace de ces documents nécessite un temps considérable pour extraire les informations essentielles, comprendre les concepts clés et s'auto-évaluer. Les outils existants ne proposent pas de solution intégrée combinant résumé automatique, question-réponse contextualisé et auto-évaluation, tout en restant fidèle au contenu original du cours.

**Problématique** : Comment concevoir un assistant pédagogique intelligent capable d'analyser automatiquement un cours PDF, d'en produire des résumés structurés par chapitre, de répondre aux questions des étudiants de manière conversationnelle et contextualisée, et de générer des quiz d'auto-évaluation — en exploitant un pipeline combinant NLP classique, Deep Learning et grands modèles de langage (LLM) ?

---

## 2. Objectifs du projet

### 2.1 Objectif général

Concevoir et développer **EduAI**, une application web full-stack intégrant un pipeline complet de Traitement Automatique du Langage Naturel (NLP), de Deep Learning et de LLM pour assister les étudiants dans la compréhension et la révision de leurs cours au format PDF.

### 2.2 Objectifs spécifiques

1. **Extraction et indexation intelligente** — Extraire le texte structuré d'un PDF (chapitres, pages), le découper en passages sémantiquement cohérents, et l'indexer dans un espace vectoriel pour une recherche de similarité rapide.
2. **Résumé automatique par chapitre** — Produire des fiches de révision fidèles au contenu original via un pipeline hybride : extractif (TextRank + spaCy) puis génératif (reformulation LLM).
3. **Q&A conversationnel (RAG)** — Permettre à l'étudiant de poser des questions en langage naturel et obtenir des réponses contextualisées avec citations des passages sources, en temps réel via streaming.
4. **Génération de quiz d'auto-évaluation** — Créer des QCM multi-chapitres avec correction automatique et explications détaillées.
5. **Interface utilisateur moderne** — Fournir une expérience fluide et responsive pour l'ensemble des fonctionnalités (upload, résumés, chat, quiz).

---

## 3. Périmètre fonctionnel

### 3.1 Upload et traitement de PDF

| Fonctionnalité             | Description                                                                                   |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| Upload drag & drop         | Glisser-déposer un PDF (max 50 MB) ou sélection manuelle.                                     |
| Extraction structurée      | Texte extrait page par page avec détection automatique des titres de chapitres (taille/gras). |
| Chunking intelligent       | Découpage en passages de ≈ 400 tokens avec overlap de 50, respect des limites de phrases.     |
| Embeddings sémantiques     | Encodage de chaque passage en vecteur 384-d via un Transformer BERT multilingue.              |
| Indexation vectorielle     | Index FAISS (Inner Product) pour recherche de similarité en temps quasi-réel.                 |
| Pré-génération automatique | Résumés et quiz par défaut générés en arrière-plan dès la fin de l'upload.                    |

### 3.2 Résumés automatiques par chapitre

| Fonctionnalité                | Description                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------- |
| Résumé extractif              | Sélection des phrases les plus représentatives via TextRank (graph-based ranking). |
| Analyse linguistique          | Tokenisation, POS-tagging, lemmatisation et NER via spaCy pour les concepts clés.  |
| Reformulation pédagogique LLM | Reformulation en fiche de révision structurée et claire, fidèle aux extraits.      |
| Concepts clés                 | Extraction et affichage des termes techniques importants de chaque chapitre.       |
| Mise en cache                 | Résumés sauvegardés en base de données pour éviter de recalculer.                  |

### 3.3 Q&A conversationnel (RAG)

| Fonctionnalité                 | Description                                                                         |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| Chat en langage naturel        | L'étudiant pose des questions librement (y compris salutations).                    |
| Retrieval-Augmented Generation | Recherche FAISS des passages pertinents → injection dans le prompt LLM → réponse.   |
| Citations des sources          | Chaque réponse référence les passages sources avec numéro de page.                  |
| Streaming temps réel (SSE)     | Réponses affichées token par token via Server-Sent Events.                          |
| Historique conversationnel     | Les derniers échanges sont inclus dans le contexte pour une conversation cohérente. |
| Limitation au contenu          | Le LLM refuse poliment les questions hors-sujet et redirige vers le cours.          |
| Fallback extractif             | En cas d'échec du LLM, un modèle CamemBERT extractif prend le relais.               |

### 3.4 Quiz d'auto-évaluation

| Fonctionnalité             | Description                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------- |
| Génération LLM de QCM      | QCM fidèles au contenu avec distracteurs plausibles, couvrant plusieurs chapitres. |
| Nombre configurable        | Entre 1 et 30 questions (défaut : 10).                                             |
| Mix de difficultés         | ~40 % mémorisation, ~40 % compréhension, ~20 % application.                        |
| Correction et explications | Score final avec explication détaillée pour chaque question.                       |
| Fallback extractif         | Si le LLM échoue, un modèle T5 génère les questions en mode extractif.             |
| Mise en cache              | Quiz pré-généré et mis en cache ; régénération possible à la demande.              |

### 3.5 Gestion des cours

| Fonctionnalité  | Description                                                                      |
| --------------- | -------------------------------------------------------------------------------- |
| Liste des cours | Page d'accueil affichant tous les cours uploadés (nom, date, nombre de pages).   |
| Page de détail  | Vue tabulée avec 3 onglets : Résumé, Q&A, Quiz.                                  |
| Suppression     | Suppression d'un cours avec cascade (chunks, index FAISS, sessions Q&A, caches). |

---

## 4. Architecture technique

### 4.1 Vue d'ensemble

```
┌─────────────────────────┐         ┌──────────────────────────────────┐
│   Frontend (Next.js)    │  HTTP   │      Backend (FastAPI)           │
│   React 18 + Tailwind   │◄──────►│      Python 3.13 + Motor        │
│   Port 3000             │  SSE    │      Port 8000                  │
└─────────────────────────┘         └──────────┬───────────────────────┘
                                               │
                      ┌────────────────────────┼──────────────────────┐
                      │                        │                      │
              ┌───────▼───────┐    ┌───────────▼────────┐    ┌───────▼────────┐
              │   MongoDB 7   │    │  FAISS Index       │    │  Groq Cloud    │
              │  (motor async)│    │  384-d, IndexFlatIP│    │  Llama 3.3 70B │
              └───────────────┘    └────────────────────┘    └────────────────┘
```

**Flux principal** : L'utilisateur upload un PDF via le frontend → le backend extrait le texte, le découpe en chunks, génère les embeddings, crée l'index FAISS, puis pré-génère les résumés et le quiz en arrière-plan. L'étudiant peut ensuite consulter les résumés, poser des questions (RAG) ou passer un quiz — le tout servi via une API REST avec streaming SSE pour le chat.

### 4.2 Stack technologique

| Couche                        | Technologie                                                             |
| ----------------------------- | ----------------------------------------------------------------------- |
| **Frontend**                  | Next.js 14, React 18, TypeScript, Tailwind CSS, Framer Motion           |
| **Backend**                   | FastAPI, Python 3.13, Uvicorn (ASGI), Pydantic v2                       |
| **Base de données**           | MongoDB 7 (Motor — driver asynchrone)                                   |
| **LLM**                       | Groq Cloud — Llama 3.3 70B Versatile                                    |
| **Embeddings**                | sentence-transformers / paraphrase-multilingual-MiniLM-L12-v2 (384-d)   |
| **Recherche vectorielle**     | FAISS (Facebook AI Similarity Search) — IndexFlatIP                     |
| **NLP**                       | spaCy fr_core_news_lg (tokenisation, POS, lemmatisation, NER)           |
| **Résumé extractif**          | TextRank (graph-based) + scoring multi-critères                         |
| **QA extractif (fallback)**   | CamemBERT fine-tuné FQuAD (etalab-ia/camembert-base-squadFR-fquad-piaf) |
| **Quiz extractif (fallback)** | T5-base-qa-qg-hl (valhalla)                                             |
| **Extraction PDF**            | PyMuPDF (fitz)                                                          |
| **Conteneurisation**          | Docker + Docker Compose                                                 |

### 4.3 Pipeline NLP / Deep Learning

Le traitement d'un cours PDF suit un pipeline multi-étapes combinant NLP classique, Deep Learning et LLM :

1. **Extraction & segmentation** _(NLP)_ — PyMuPDF extrait le texte page par page et détecte les titres de chapitres par analyse de la taille et du style de police. Le texte est découpé en chunks de ≈ 400 tokens avec overlap de 50 tokens, en respectant les limites de phrases.

2. **Analyse linguistique** _(NLP)_ — spaCy `fr_core_news_lg` effectue la tokenisation, le POS-tagging, la lemmatisation et la reconnaissance d'entités nommées (NER) pour identifier les concepts clés.

3. **Embeddings sémantiques** _(Deep Learning)_ — Chaque chunk est encodé en un vecteur dense de 384 dimensions via un modèle BERT distillé multilingue (`paraphrase-multilingual-MiniLM-L12-v2`), normalisé pour la similarité cosinus.

4. **Indexation vectorielle** _(Deep Learning)_ — Les vecteurs sont stockés dans un index FAISS (`IndexFlatIP`) permettant une recherche de similarité exacte par produit scalaire.

5. **Résumé extractif** _(NLP)_ — TextRank + scoring multi-critères sélectionne les phrases les plus représentatives de chaque chapitre.

6. **Reformulation pédagogique** _(LLM)_ — Le résumé extractif est envoyé au LLM (Groq · Llama 3.3 70B) qui le reformule en fiche de révision structurée, fidèle aux extraits sans hallucination.

7. **RAG pour le Q&A** _(Deep Learning + LLM)_ — La question est encodée, les top-k chunks similaires sont récupérés via FAISS, puis injectés comme contexte dans le prompt du LLM pour générer une réponse conversationnelle avec citations.

8. **Génération de quiz** _(LLM)_ — Des passages diversifiés sont échantillonnés à travers les chapitres et envoyés au LLM en un seul appel pour produire des QCM en JSON strict, avec validation des réponses.

---

## 5. Planning prévisionnel

| Semaine       | Dates            | Tâches                                                                                                                                                                                                                                                                |
| ------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Semaine 1** | 27 avril – 4 mai | Livraison du Cahier de Charge V1 au Pr. Erraji Mehdi. Développement de l'application web from scratch (frontend Next.js + backend FastAPI). Traçage et conception de l'architecture du pipeline pour l'intégration du volet IA et Data Science (Deep Learning + NLP). |
| **Semaine 2** | 4 mai – 11 mai   | Mise en place de l'architecture du pipeline NLP / Deep Learning : extraction PDF, chunking, embeddings sémantiques (MiniLM-L12-v2), indexation vectorielle FAISS, résumé extractif (TextRank + spaCy). Intégration des briques IA dans le backend.                    |
| **Semaine 3** | 11 mai – 18 mai  | Tests et validation du pipeline complet. Suivi et adaptation pour s'assurer que chaque étape (extraction → embeddings → indexation → résumé → reformulation LLM) fonctionne comme un pipeline cohérent d'Assistant Pédagogique Intelligent.                           |
| **Semaine 4** | 18 mai – 24 mai  | Tests du Q&A conversationnel RAG (streaming SSE, historique, citations). Tests du quiz génératif LLM (correction, explications). Tests de la reformulation pédagogique LLM des résumés. Déploiement de l'application si possible.                                     |
| **Semaine 5** | 25 mai – 1 juin  | Tests finaux et corrections de bugs. Rédaction du rapport de PFE. Préparation de la soutenance.                                                                                                                                                                       |

---

_Document rédigé par EL MEHDI HACHAMI — V1, avril 2026._
