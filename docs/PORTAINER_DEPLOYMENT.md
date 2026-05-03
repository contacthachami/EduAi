# EduAI Portainer Deployment

This setup deploys EduAI as three main containers:

- `eduai-frontend`: Next.js standalone server on port `3000`
- `eduai-backend`: FastAPI server on port `8000`
- `eduai-mongodb`: MongoDB, internal only

Persistent Docker volumes:

- `eduai_mongo_data`: MongoDB data
- `eduai_backend_data`: FAISS indexes and backend data
- `eduai_models_cache`: Hugging Face / Transformers model cache

## Requirements

- A VPS/server with Docker and Portainer CE.
- Recommended minimum for the ML backend: 4 CPU cores, 8 GB RAM, and 20 GB free disk.
- Internet access during the first backend start, so Hugging Face models can be downloaded into `eduai_models_cache`.
- A Groq API key if you want LLM summaries, quizzes, and chat via `LLM_BACKEND=groq`.

Keep `HF_HUB_OFFLINE=0` and `TRANSFORMERS_OFFLINE=0` for the first deployment. After the model cache is warm, you can set both to `1` if you want fully cached/offline Hugging Face loading.

## Option A: Portainer Builds From Git

Use this if your project is pushed to GitHub/GitLab and Portainer can access it.

1. Push this repository to Git.
2. In Portainer, open `Stacks` > `Add stack`.
3. Choose `Repository`.
4. Set the compose path to:

```text
docker-compose.portainer.yml
```

5. Add environment variables from `.env.portainer.example`.
6. Change at least these values:

```env
ALLOWED_ORIGINS=https://your-domain.example.com,http://localhost:3000,http://127.0.0.1:3000
MONGO_ROOT_PASSWORD=replace-with-a-long-password
SECRET_KEY=replace-with-a-long-random-secret
GROQ_API_KEY=gsk_your_key_here
```

7. Deploy the stack.

The first backend start can take several minutes because it loads/downloads ML models.

## Option B: Push Images, Then Portainer Pulls Them

Use this if you want to paste a stack in Portainer or deploy without giving Portainer your source repo.

From the project root:

```powershell
docker build -t your-dockerhub-user/eduai-backend:latest -f backend/Dockerfile .
docker build -t your-dockerhub-user/eduai-frontend:latest --build-arg BACKEND_URL=http://backend:8000 ./frontend
docker push your-dockerhub-user/eduai-backend:latest
docker push your-dockerhub-user/eduai-frontend:latest
```

Then in Portainer:

1. Open `Stacks` > `Add stack`.
2. Choose `Web editor`.
3. Paste `docker-compose.portainer.images.yml`.
4. Add environment variables from `.env.portainer.example`.
5. Set:

```env
EDUAI_BACKEND_IMAGE=your-dockerhub-user/eduai-backend:latest
EDUAI_FRONTEND_IMAGE=your-dockerhub-user/eduai-frontend:latest
```

6. Deploy the stack.

## Nginx Proxy Manager

Your screenshot shows Nginx Proxy Manager already running. The simplest setup is:

- Forward hostname/IP: your server IP
- Forward port: `3000`
- Scheme: `http`
- Enable Websockets support
- Request an SSL certificate with Let's Encrypt

Recommended advanced config for PDF uploads and long AI responses:

```nginx
client_max_body_size 60m;
proxy_connect_timeout 60s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
proxy_buffering off;
proxy_cache off;
send_timeout 600s;
```

If you do not have a domain yet, open:

```text
http://SERVER_IP:3000
```

and set:

```env
ALLOWED_ORIGINS=http://SERVER_IP:3000,http://localhost:3000,http://127.0.0.1:3000
```

## Important Notes

- MongoDB is not exposed publicly. Only the backend can reach it on the Docker network.
- The backend port is bound to `127.0.0.1:8000` by default for local server debugging.
- Use simple Mongo passwords or URL-encode special characters, because the password is used inside `MONGODB_URL`.
- If the backend logs show missing Hugging Face models, set `HF_HUB_OFFLINE=0` and redeploy once.
- If Groq is not configured, the app still runs with extractive fallbacks, but LLM quality features are reduced.

## Quick Health Checks

Frontend:

```text
http://SERVER_IP:3000
```

Backend from the server:

```powershell
curl http://127.0.0.1:8000/health
```

In Portainer, all three containers should be `running`, and the backend/frontend should become `healthy` after startup.
