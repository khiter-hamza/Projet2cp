# Projet 2CP - Backend

FastAPI Backend with PostgreSQL and Docker.

## 🚀 Getting Started

### 1. Prerequisites
- Docker and Docker Compose installed.

### 2. Environment Setup
Create your local environment file by copying the example:
```bash
cp .env.example .env
```

### 3. Run the Project
Start all services (Backend + Database) in the background:
```bash
docker compose -f docker/docker-compose.yml up -d
```

The API will be available at: [http://localhost:8000](http://localhost:8000)

### 4. Verify Installation
Check the health status:
```bash
curl http://localhost:8000/api/v1/health
```

---

## 🛠 Useful Commands

| Action | Command |
| :--- | :--- |
| **Start Services** | `docker compose -f docker/docker-compose.yml up -d` |
| **Stop Services** | `docker compose -f docker/docker-compose.yml down` |
| **View Logs** | `docker compose -f docker/docker-compose.yml logs -f backend` |
| **Rebuild Image** | `docker compose -f docker/docker-compose.yml up -d --build` |

## 📁 Project Structure
- `app/api/v1/`: API endpoints and routing.
- `app/core/`: Configuration and database setup.
- `app/models/`: SQLAlchemy database models.
- `docker/`: Dockerfile and Docker Compose configurations.
- `requirements/`: Python dependency files.




for db  migration  :


From project root:
docker exec projet2cp_backend sh -lc "cd /app ; alembic revision --autogenerate -m your_message"
Apply:
docker exec projet2cp_backend sh -lc "cd /app ; alembic upgrade head"
Check current:
docker exec projet2cp_backend sh -lc "cd /app ; alembic current"




idK  3lah .env daymen mansibouch , anyway :
PROJECT_NAME=Projet2CP Backend
VERSION=1.0.0
API_V1_STR=/api/v1

SECRET_KEY=change-this-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=11520

POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=projet2cp
POSTGRES_PORT=5432

CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

