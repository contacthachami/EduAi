# EduAI — Assistant Pédagogique Intelligent

EduAI est une application web full-stack qui transforme un PDF de cours en espace de révision intelligent.

L'application permet à l'étudiant d'importer un cours au format PDF, puis de générer automatiquement des questions-réponses, des synthèses par chapitre, des quiz de révision et des sources vérifiables.

---

## Fonctionnalités principales

- Upload et indexation de fichiers PDF
- Extraction du contenu avec PyMuPDF
- Recherche sémantique avec FAISS
- Questions-réponses basées sur le contenu du cours
- Réponses contextualisées avec sources vérifiables
- Génération de synthèses par chapitre
- Génération de quiz de révision
- API REST avec FastAPI
- Interface web moderne avec Next.js

---

## Stack technique

### Frontend

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

### Backend

- FastAPI
- Python
- MongoDB
- FAISS

### IA et NLP

- PyMuPDF
- sentence-transformers
- spaCy
- Transformers
- Groq
- Ollama

---

## Architecture générale

Utilisateur -> Frontend Next.js -> Backend FastAPI -> Pipeline IA/NLP

Le backend gère :

- l'extraction du contenu PDF ;
- le traitement NLP ;
- l'indexation vectorielle avec FAISS ;
- la sauvegarde des données dans MongoDB ;
- la génération des réponses, synthèses et quiz.

---

## Prérequis

Avant de lancer le projet, vous devez installer :

- Python 3.10 ou plus
- Node.js 18 ou plus
- npm
- Docker et Docker Compose, optionnel mais recommandé
- MongoDB, localement ou avec Docker

---

## Installation

### 1. Cloner le projet

Commande :

git clone https://github.com/contacthachami/EduAi.git

Puis entrer dans le dossier :

cd eduai

Remplacez USERNAME par votre nom d'utilisateur GitHub.

---

### 2. Configurer les variables d'environnement

Copiez le fichier .env.example vers .env.

Sur Windows PowerShell :

Copy-Item .env.example .env

Variables principales :

BACKEND_URL=http://127.0.0.1:8000

MONGODB_URL=mongodb://localhost:27017

GROQ_API_KEY=

Important : la clé GROQ_API_KEY doit être renseignée uniquement dans le fichier .env. Elle ne doit jamais être ajoutée dans Git.

---

## Lancement recommandé en développement

Depuis la racine du projet, lancez :

.\scripts\dev.ps1

Ce script :

- démarre MongoDB avec Docker Compose si Docker est disponible ;
- lance le backend FastAPI sur http://127.0.0.1:8000 ;
- attend que l'endpoint /health réponde ;
- lance ensuite le frontend Next.js sur http://localhost:3000.

---

## Lancement manuel

### Terminal 1 — MongoDB

docker compose up -d mongodb

### Terminal 2 — Backend

Depuis la racine du projet :

python -m uvicorn backend.main:app --reload --port 8000

Le backend sera disponible sur :

http://127.0.0.1:8000

### Terminal 3 — Frontend

cd frontend

npm run dev

Le frontend sera disponible sur :

http://localhost:3000

Important : le frontend proxy /api/* vers le backend. Si FastAPI n'est pas lancé sur le port 8000, Next.js affichera une erreur de proxy ECONNREFUSED.

---

## Lancement avec Docker Compose

Pour lancer tous les services avec Docker Compose :

docker compose up --build

Services disponibles :

- Frontend : http://localhost:3000
- Backend : http://localhost:8000
- MongoDB : localhost:27017

---

## API

Documentation interactive FastAPI :

http://localhost:8000/docs

Endpoints principaux :

- POST /api/courses/upload : upload et indexation d'un PDF
- GET /api/courses : liste des cours
- GET /api/courses/{id} : détail d'un cours
- DELETE /api/courses/{id} : suppression d'un cours
- POST /api/qa/ask : question-réponse
- POST /api/qa/ask/stream : Q&A en streaming SSE
- GET /api/summary/{course_id} : synthèses du cours
- GET /api/quiz/{course_id} : quiz du cours
- POST /api/quiz/submit : correction du quiz

---

## Structure du projet

eduai/

- backend/
  - main.py
  - routers/
  - services/
  - models/
  - database/

- frontend/
  - src/
  - app/
  - components/
  - lib/

- scripts/
  - dev.ps1

- data/
- docker-compose.yml
- .env.example
- README.md

---

## Vérification rapide

Depuis le dossier frontend :

cd frontend

npm run lint

.\node_modules\.bin\tsc --noEmit --incremental false

Pour lancer un build de production :

npm run build

Avant d'exécuter npm run build, arrêtez d'abord le serveur npm run dev afin d'éviter les conflits avec le dossier .next.

---

## Workflow utilisateur

1. L'utilisateur importe un PDF de cours.
2. Le backend extrait le texte du document.
3. Le contenu est découpé et indexé avec FAISS.
4. L'utilisateur pose une question.
5. Le système recherche les passages les plus pertinents.
6. Une réponse contextualisée est générée.
7. Les sources utilisées sont affichées.
8. L'utilisateur peut aussi générer des synthèses et des quiz.

---

## Objectif du projet

L'objectif d'EduAI est d'aider les étudiants à réviser plus efficacement leurs cours en utilisant l'intelligence artificielle.

Le projet combine le traitement automatique du langage naturel, la recherche sémantique et une interface web moderne pour proposer une expérience simple, rapide et interactive.

---

## Auteur

Projet développé par El Mehdi Hachami.

---

## Licence

Ce projet est réalisé dans un cadre académique.
