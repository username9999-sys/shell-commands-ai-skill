# Shell Commands AI Skill

Tujuan: menyediakan referensi terstruktur untuk perintah shell Unix/Linux.

## Quick Start

```bash
# 1. Install dependencies
pip install -r api/requirements.txt

# 2. Fetch man pages
./scripts/fetch_man.sh coreutils find grep ls cp mv rm mkdir rmdir cat head tail less more sed awk sort uniq cut tr wc grep egrep fgrep xargs find locate which whereis type alias unalias history fc jobs bg fg kill nohup disown wait sleep date cal bc dc factor seq yes tee script time timeout env printenv export set unset declare local readonly typeset shift

# 3. Parse man pages
python3 scripts/parse_man.py data/raw data/parsed

# 4. Build search index
python3 scripts/build_index.py data/parsed data/index

# 5. Generate JSON dataset
python3 scripts/generate_json.py data/parsed data/parsed

# 6. Run API server
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /command/{name}` - Get command details
- `POST /search` - Natural language search
- `POST /explain` - Contextual explanation
- `GET /commands` - List all commands (paginated)
- `GET /categories` - List categories with counts

## Sandbox Execution (Optional)

```bash
# Build sandbox image
docker build -t shell-skill-sandbox ./sandbox

# Run example in sandbox
docker run --rm shell-skill-sandbox find /var/log -type f -name '*.log' -mtime -7
```

## Project Structure

```
├── README.md
├── LICENSE
├── .gitignore
├── /docs
│   ├── architecture.md
│   ├── data-sources.md
│   └── security.md
├── /scripts
│   ├── fetch_man.sh
│   ├── parse_man.py
│   ├── build_index.py
│   └── generate_json.py
├── /parser
│   ├── mandoc_wrapper.py
│   └── manparser.py
├── /data
│   ├── raw/
│   ├── parsed/
│   └── index/
├── /api
│   ├── app.py
│   ├── requirements.txt
│   ├── schemas.py
│   └── routes.py
├── /sandbox
│   ├── Dockerfile
│   ├── run_sandbox.sh
│   └── sandbox_manager.py
├── /ui/web
├── /tests
│   ├── test_parser.py
│   ├── test_index.py
│   └── test_api.py
├── /ci/pipeline.yml
└── /examples
    ├── seed_commands.json
    └── 50_most_common.md
```

## Data Sources

- Local `man` pages (mandoc/groff)
- man7.org (Linux man-pages project)
- GNU coreutils documentation
- TLDP (The Linux Documentation Project)
- OpenBSD man pages (for POSIX reference)

## Security

See [docs/security.md](docs/security.md) for:
- Blacklisted destructive commands
- Sandbox policies
- Rate limiting rules
- Logging requirements

## License

MIT License - see LICENSE file.