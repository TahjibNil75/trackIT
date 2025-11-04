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
uvicorn src.main:app --reload
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