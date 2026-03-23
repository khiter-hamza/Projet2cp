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
