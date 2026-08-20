# Development Guide

This guide covers setting up a development environment and common development tasks for Shell Commands AI Skill.

## Prerequisites

- **Python** 3.11+
- **Docker** 24+
- **Git** 2.40+
- **System packages**: `mandoc`, `groff`, `sqlite3`

## Quick Start

```bash
# Clone
git clone https://github.com/username9999-sys/shell-commands-ai-skill.git
cd shell-commands-ai-skill

# System packages (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y mandoc groff

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r api/requirements.txt
pip install pytest pytest-asyncio httpx ruff

# Verify setup
python -m pytest tests/ -v
```

## Project Structure

```
shell-commands-ai-skill/
├── api/                 # FastAPI application
│   ├── app.py          # App factory
│   ├── routes.py       # API endpoints
│   ├── schemas.py      # Pydantic models
│   └── requirements.txt
├── parser/             # Man page parsing
│   ├── manparser.py    # Core parsing logic
│   └── mandoc_wrapper.py
├── scripts/            # Data pipeline
│   ├── fetch_man.sh    # Fetch man pages
│   ├── parse_man.py    # Parse raw → JSON
│   ├── build_index.py  # Build search indexes
│   └── generate_json.py
├── sandbox/            # Secure execution
│   ├── Dockerfile
│   ├── run_sandbox.sh
│   └── sandbox_manager.py
├── tests/              # Unit/integration tests
├── docs/               # Documentation
├── examples/           # Seed data
├── data/
│   ├── raw/           # Raw man pages
│   ├── parsed/        # Parsed JSON
│   └── index/         # Search indexes
└── ci/                 # CI/CD
```

## Development Workflows

### 1. Adding a New Command

```bash
# 1. Add to seed list
echo '"newcmd"' >> examples/seed_commands.json  # (edit properly)

# 2. Fetch man page
./scripts/fetch_man.sh newcmd

# 3. Parse
python3 scripts/parse_man.py data/raw data/parsed

# 4. Verify parsed output
cat data/parsed/newcmd.json | jq .

# 4. Rebuild index
python3 scripts/build_index.py data/parsed data/index

# 5. Test API
uvicorn api.app:app --reload &
curl http://localhost:8000/api/v1/commands/newcmd
```

### 2. Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_parser.py -v

# With coverage
pip install pytest-cov
python -m pytest tests/ --cov=parser --cov=scripts --cov=api

# Watch mode
pip install pytest-watch
ptw tests/
```

### 3. Building Search Index

```bash
# Full rebuild
python3 scripts/build_index.py data/parsed data/index

# Verify index
sqlite3 data/index/commands.db "SELECT name FROM commands_fts WHERE commands_fts MATCH 'find';"
```

### 4. Running API Server

```bash
# Development
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Sandbox Development

```bash
# Build image
docker build -t shell-skill-sandbox ./sandbox

# Test manually
docker run --rm shell-skill-sandbox "find /workspace -name '*.txt'"

# Using manager
python3 -c "
from sandbox.sandbox_manager import SandboxManager
m = SandboxManager()
r = m.execute('find', ['/workspace', '-name', '*.py'])
print(r.stdout)
"
```

### 6. Linting & Formatting

```bash
# Install ruff
pip install ruff

# Check
ruff check .

# Fix
ruff check . --fix

# Format
ruff format .
```

## Common Issues

### mandoc/groff not found
```bash
sudo apt-get install mandoc groff
```

### FAISS import error
```bash
pip install faiss-cpu sentence-transformers
```

### Docker permission denied
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### SQLite FTS5 not available
```bash
# SQLite with FTS5 is standard in Python 3.11+
# If missing, compile SQLite with FTS5 or install package
sudo apt-get install sqlite3 libsqlite3-dev
```

## Debugging Tips

### Parser Debugging
```bash
# Test single command parsing
python3 -c "
from parser.manparser import parse_man_text
with open('data/raw/find.txt') as f:
    text = f.read()
result = parse_man_text('find', text)
import json
print(json.dumps(result, indent=2))
"
```

### API Debugging
```bash
# Run with debug logging
uvicorn api.app:app --reload --log-level debug
```

### Index Debugging
```bash
# Check index stats
sqlite3 data/index/commands.db "
  SELECT COUNT(*) FROM commands;
  SELECT COUNT(*) FROM commands_fts;
"
```

## Useful Commands

```bash
# Count parsed commands
ls data/parsed/*.json | wc -l

# List categories
python3 -c "
import json, glob
cats = {}
for f in glob.glob('data/parsed/*.json'):
    if '_index' not in f:
        with open(f) as fp:
            c = json.load(fp)
        cats[c['category']] = cats.get(c['category'], 0) + 1
for k, v in sorted(cats.items()):
    print(f'{k}: {v}')
"

# Check index size
du -sh data/index/
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PARSED_DIR` | `data/parsed` | Parsed commands directory |
| `INDEX_DIR` | `data/index` | Search index directory |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `SANDBOX_IMAGE` | `shell-skill-sandbox` | Docker image name |

## IDE Setup (VS Code)

Recommended extensions:
- Python
- Pylance
- Docker
- SQLite
- REST Client

Settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## Profiling

```bash
# Profile parser
python -m cProfile -o parse.prof scripts/parse_man.py data/raw data/parsed
python -c "import pstats; p = pstats.Stats('parse.prof'); p.sort_stats('cumulative').print_stats(20)"

# Profile API
pip install py-spy
sudo py-spy record -o api.svg -- uvicorn api.app:app
```