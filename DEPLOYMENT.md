# Production Deployment Guide - RiskPulse

This guide outlines how to deploy the production-ready RiskPulse stack (FastAPI, React, PostgreSQL, Redis, Celery) to cloud environments.

---

## 1. Stack Architecture
In production, the application is deployed in microservices using Docker containers orchestrated by Nginx:

```
                          [ Client Browser ]
                                  │ (Port 80/443)
                                  ▼
                            [ Nginx Reverse Proxy ]
                            /                   \
                   (Static Assets)          (API Requests)
                          /                       \
                         ▼                         ▼
                  [ React Frontend ]        [ FastAPI Backend ]
                                             /       |       \
                                            /        |        \
                                           ▼         ▼         ▼
                                     [PostgreSQL] [Redis]  [MLflow Registry]
                                                     ▲
                                                     │
                                             [Celery Workers]
```

---

## 2. Docker Compose Deployment
We provide a unified `docker-compose.yml` to launch all services locally or in staging:

### Commands
1. **Build and start the container stack in detached mode:**
   ```bash
   docker-compose up --build -d
   ```
2. **Inspect container logs:**
   ```bash
   docker-compose logs -f backend
   ```
3. **Shutdown all services and retain database volumes:**
   ```bash
   docker-compose down
   ```

---

## 3. Environment Configurations
Rename/create `.env` files in the backend workspace for secure deployments:

```ini
# Database
DATABASE_URL=postgresql://postgres:secure_db_password@postgres:5432/riskpulse

# Security
SECRET_KEY=change_this_to_a_long_random_hash_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Queue & Cache
REDIS_HOST=redis
REDIS_PORT=6379

# MLflow Tracking Server
MLFLOW_TRACKING_URI=http://mlflow_server:5000
```

---

## 4. Scaling Celery Background Workers
To scale background training or OCR document extractions, spin up additional worker instances using Docker Compose:

```bash
docker-compose up -d --scale celery_worker=3
```
This launches 3 independent worker containers linked to the Redis task broker.

---

## 5. Security & SSL Setup
Configure an SSL certificate (e.g. Let's Encrypt) on the Nginx front door and restrict PostgreSQL access to local service bindings only. Enable role-based token validation inside `deps.py` for sensitive retraining tasks.
