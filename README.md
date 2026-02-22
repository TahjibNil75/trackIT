# trackIT

trackIT is a ticket management system built with FastAPI
---

## Prerequisites

- Python 3.11+
- `pip` installed
- PostgreSQL database (local or remote)
<!-- - Redis server (required for logout API) -->
- Git

---

## Setup Instructions for LOCALHOST

### 1. Clone the repository

```bash
git clone https://github.com/TahjibNil75/trackIT.git
cd trackIT
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

### 5. Start The Application

```bash
uvicorn src.main:_app --reload
```

The API will be available at:
http://127.0.0.1:8000


### 6. Swagger Documentation

Interactive API documentation will be available at:
http://127.0.0.1:8000/docs




## Data Migration

After creating or updating models, use Alembic to generate and apply migrations:

```bash
# Generate a new migration after changing models
alembic revision --autogenerate -m "your message"

# Apply migrations
alembic upgrade head
```

---

## Docker Setup

### Prerequisites

- Docker and Docker Compose installed on your system
- Git

### 1. Clone the repository

```bash
git clone https://github.com/TahjibNil75/trackIT.git
cd trackIT
```

### 2. Configure environment variables

Create a `.env` file in the `src/` directory based on `src/.env.example`:

```bash
cp src/.env.example src/.env
```

Update the environment variables in `src/.env` as needed, especially:
- Database credentials
- JWT secret
- AWS S3 credentials

### 3. Start the application with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

This will start:
- **FastAPI application** on http://localhost:8000
- **PostgreSQL database** on localhost:5432
- **Redis** on localhost:6379
- **Celery worker** for background tasks

### 4. Access the application

- **API endpoints**: http://localhost:8000
- **Swagger documentation**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/v1/health

### 5. Database migrations (if needed)

```bash
# Run migrations inside the running container
docker-compose exec app alembic upgrade head

# Generate new migrations
docker-compose exec app alembic revision --autogenerate -m "your message"
```

### 6. Stop the application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (will delete database data)
docker-compose down -v
```

### Docker Compose Services

- **app**: Main FastAPI application
- **postgres**: PostgreSQL database
- **redis**: Redis for caching and Celery broker
- **celery**: Background task worker

### Development with Docker

For development with hot reload:

```bash
docker-compose up --build app
```

The `src/` directory is mounted as a volume, so changes to your code will be reflected immediately.

---

## CI/CD Pipeline

### Overview

The application includes a GitHub Actions workflow that automatically deploys to an EC2 instance via a bastion host when code is pushed to the `main` branch.

### Architecture

```
GitHub Actions → Bastion Host → App Server EC2
                      ↓
                 Docker Containers
```

### Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

- **`EC2_SSH_KEY`**: Private SSH key for EC2 access
- **`EC2_USER`**: SSH user (e.g., `ubuntu`)
- **`BASTION_HOST`**: Public IP or DNS of bastion host
- **`APP_PRIVATE_IP`**: Private IP of app server EC2

### Initial EC2 Setup

1. **Connect to app server via bastion:**
   ```bash
   ssh -J ubuntu@<BASTION_IP> ubuntu@<APP_PRIVATE_IP>
   ```

2. **Run the setup script:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/TahjibNil75/trackIT/main/scripts/setup-ec2.sh | bash
   ```

3. **Configure environment variables:**
   ```bash
   cd /home/ubuntu/trackIT
   nano src/.env  # Update with your actual values
   ```

4. **Start the application:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Deployment Process

The CI/CD pipeline automatically:

1. Pulls latest code from GitHub
2. Stops existing Docker containers
3. Builds and starts new containers
4. Performs health check
5. Cleans up old Docker images

### Manual Deployment

To deploy manually from the app server:

```bash
cd /home/ubuntu/trackIT
./scripts/deploy.sh
```

### Systemd Service (Optional)

For automatic startup on server reboot:

```bash
# Copy service file
sudo cp scripts/trackit.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable trackit
sudo systemctl start trackit

# Check status
sudo systemctl status trackit
```

### Monitoring

- **Application logs**: `docker-compose -f docker-compose.prod.yml logs -f`
- **Container status**: `docker-compose -f docker-compose.prod.yml ps`
- **Health check**: `curl http://localhost:8000/api/v1/health`

### Security Considerations

- SSH keys are stored as GitHub secrets
- App server is only accessible via bastion
- Docker containers run with non-root user
- Environment variables are not exposed in logs