```sh
uvicorn src.main:_app --reload
```

## Alembic setup
```sh
## For async template
alembic init -t async migrations
```

## env.py setup
1. Import models
2. from sqlmodel import SQLModel
3. from src.config import Config

```py
database_url = Config.DATABASE_URL
```

```py
config.set_main_option("sqlalchemy.url", database_url)  
```

```py
## Change None from SQLModel.metadata
target_metadata = SQLModel.metadata
```

## Sqript.py.mako
1. add
import sqlmodel