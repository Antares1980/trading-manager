# Developer Guide

Complete guide for developers working on the Trading Manager application.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- PostgreSQL/TimescaleDB (via Docker)
- Redis (via Docker)

### Initial Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Antares1980/trading-manager.git
cd trading-manager
```

2. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Copy environment file:**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Start services with Docker:**
```bash
docker-compose up timescaledb redis -d
```

6. **Run database migrations:**
```bash
alembic upgrade head
```

7. **Seed the database (optional):**
```bash
python -m flask db-seed
```

8. **Start the Flask application:**
```bash
python app.py
# Or using Flask CLI:
# flask run
```

9. **Start Celery worker (optional):**
```bash
celery -A backend.tasks.celery_app worker --loglevel=info
```

Application will be available at http://localhost:5000

## Project Structure

```
trading-manager/
├── backend/
│   ├── api/                 # API route handlers
│   │   ├── analysis_routes.py
│   │   ├── asset_routes.py
│   │   ├── auth_routes.py
│   │   ├── candle_routes.py
│   │   ├── indicator_routes.py
│   │   ├── market_routes.py
│   │   ├── signal_routes.py
│   │   └── watchlist_routes.py
│   ├── models/              # SQLAlchemy models
│   │   ├── asset.py
│   │   ├── candle.py
│   │   ├── indicator.py
│   │   ├── signal.py
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   └── watchlist_item.py
│   ├── migrations/          # Alembic migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── seed/                # Database seeding
│   │   └── seed.py
│   ├── tasks/               # Celery tasks
│   │   ├── __init__.py
│   │   ├── indicators.py
│   │   └── signals.py
│   ├── utils/               # Utility modules
│   │   ├── market_data.py
│   │   ├── mock_data.py
│   │   └── technical_analysis.py
│   ├── app.py               # Flask application factory
│   ├── config.py            # Configuration classes
│   └── db.py                # Database initialization
├── frontend/                # Frontend files
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       └── index.html
├── docs/                    # Documentation
│   ├── api.md
│   ├── db.md
│   ├── dev.md
│   ├── security.md
│   └── worker.md
├── tests/                   # Test files
│   ├── test_api.py
│   └── test_models.py
├── data/                    # Data directory
│   └── example_stocks.csv
├── app.py                   # Main entry point
├── alembic.ini              # Alembic configuration
├── docker-compose.yml       # Docker services
├── Dockerfile.backend       # Backend Dockerfile
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
└── README.md
```

## Development Workflow

### Creating a New Feature

1. **Create a new branch:**
```bash
git checkout -b feature/my-feature
```

2. **Make your changes**

3. **Run tests:**
```bash
pytest tests/
```

4. **Run linting (if configured):**
```bash
flake8 backend/
black backend/ --check
```

5. **Commit changes:**
```bash
git add .
git commit -m "Add: description of changes"
```

6. **Push and create PR:**
```bash
git push origin feature/my-feature
```

### Working with Alembic Migrations

#### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to users"

# Create empty migration
alembic revision -m "Custom migration"
```

#### Edit Migration File

Migrations are in `backend/migrations/versions/`. Edit the upgrade() and downgrade() functions:

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('new_field', sa.String(100)))

def downgrade() -> None:
    op.drop_column('users', 'new_field')
```

#### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade by one revision
alembic upgrade +1

# Downgrade by one revision
alembic downgrade -1

# Show SQL without executing
alembic upgrade head --sql
```

### Working with Models

#### Create a New Model

```python
# backend/models/my_model.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from backend.db import Base
from datetime import datetime, timezone
import uuid

class MyModel(Base):
    """My model description."""
    
    __tablename__ = 'my_table'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

#### Register Model

Add to `backend/models/__init__.py`:
```python
from backend.models.my_model import MyModel

__all__ = [..., 'MyModel']
```

### Creating New API Endpoints

#### Create Route File

```python
# backend/api/my_routes.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from backend.db import session_scope
from backend.models import MyModel

my_bp = Blueprint('my_resource', __name__)

@my_bp.route('/', methods=['GET'])
def list_items():
    """List all items."""
    with session_scope() as session:
        items = session.query(MyModel).all()
        return jsonify({
            'items': [item.to_dict() for item in items]
        }), 200

@my_bp.route('/', methods=['POST'])
@jwt_required()
def create_item():
    """Create a new item."""
    data = request.get_json()
    
    with session_scope() as session:
        item = MyModel(name=data['name'])
        session.add(item)
        session.commit()
        
        return jsonify({
            'message': 'Item created',
            'item': item.to_dict()
        }), 201
```

#### Register Blueprint

In `backend/app.py`:
```python
from backend.api.my_routes import my_bp

app.register_blueprint(my_bp, url_prefix='/api/my-resource')
```

### Creating Background Tasks

```python
# backend/tasks/my_tasks.py
from backend.tasks import celery_app, DatabaseTask

@celery_app.task(base=DatabaseTask, bind=True)
def my_background_task(self, param1):
    """My background task."""
    # Task logic here
    return {'status': 'completed'}
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=backend tests/

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_api.py::test_login_endpoint
```

### Seeding Development Data

```bash
# Seed database with demo data
python -m flask db-seed

# Force re-seed even if data exists
python -m flask db-seed --force

# Or run seed script directly
python backend/seed/seed.py
```

After seeding, you can login with:
- Username: `demo`, Password: `demo123`
- Username: `admin`, Password: `admin123`

### CLI Commands

The Flask app provides CLI commands:

```bash
# Initialize database
python -m flask db-init

# Seed database
python -m flask db-seed

# Run Flask shell
python -m flask shell

# List all routes
python -m flask routes
```

## Database Management

### Connect to Database

```bash
# Via Docker
docker-compose exec timescaledb psql -U trading_user -d trading_manager

# Locally
psql postgresql://trading_user:trading_password@localhost:5432/trading_manager
```

### Useful SQL Commands

```sql
-- List all tables
\dt

-- Describe table
\d users

-- Check hypertables
SELECT * FROM timescaledb_information.hypertables;

-- Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM candles;

-- Recent signals
SELECT a.symbol, s.signal_type, s.ts 
FROM signals s 
JOIN assets a ON a.id = s.asset_id 
ORDER BY s.ts DESC LIMIT 10;
```

## Debugging

### Flask Debug Mode

Set in `.env`:
```
FLASK_DEBUG=True
```

Or run with debugger:
```bash
python -m pdb app.py
```

### Logging

Adjust log level in code:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in `.env`:
```
LOG_LEVEL=DEBUG
```

### Database Query Logging

Enable in `.env`:
```
SQL_ECHO=true
```

Or in code:
```python
app.config['SQLALCHEMY_ECHO'] = True
```

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

### Flask Shell

```bash
python -m flask shell
```

```python
# In shell
from backend.db import get_session
from backend.models import User, Asset

session = get_session()

# Query users
users = session.query(User).all()
for user in users:
    print(user.username)

# Create user
user = User(username='test', email='test@example.com')
user.set_password('password')
session.add(user)
session.commit()
```

## Code Style

### Python Style Guide

Follow PEP 8 guidelines:

- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings to functions and classes
- Type hints where appropriate

### Recommended Tools

```bash
# Install development tools
pip install black flake8 mypy isort

# Format code
black backend/

# Check style
flake8 backend/

# Sort imports
isort backend/

# Type checking
mypy backend/
```

## Performance Tips

### Database Query Optimization

```python
# Bad - N+1 query problem
watchlists = session.query(Watchlist).all()
for wl in watchlists:
    print(wl.items)  # Triggers separate query

# Good - eager loading
from sqlalchemy.orm import joinedload

watchlists = session.query(Watchlist).options(
    joinedload(Watchlist.items)
).all()
```

### Pagination

```python
# Add pagination to list endpoints
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 20, type=int)

query = session.query(Asset)
total = query.count()
items = query.limit(per_page).offset((page - 1) * per_page).all()
```

### Caching

Consider using Flask-Caching for frequently accessed data:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.cached(timeout=300)
def get_asset_list():
    # Expensive query
    pass
```

## Common Issues

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000
# Kill process
kill -9 <PID>
```

### Database Connection Issues

1. Check if PostgreSQL is running
2. Verify DATABASE_URL in .env
3. Check firewall settings
4. Verify pg_hba.conf permissions

### Celery Tasks Not Running

1. Verify Redis is running
2. Check REDIS_URL in .env
3. Ensure worker is started
4. Check worker logs for errors

### Migration Conflicts

```bash
# Stamp database at current revision
alembic stamp head

# Or reset to base
alembic downgrade base
alembic upgrade head
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)

## Getting Help

- Check existing issues on GitHub
- Review documentation in `docs/` directory
- Check application logs
- Use Flask shell for debugging
- Ask questions in GitHub Discussions
