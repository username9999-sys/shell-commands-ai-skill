# Contributing to Shell Commands AI Skill

Thank you for your interest in contributing! This document outlines the process for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md) (please create one if not present).

## How to Contribute

### 1. Reporting Bugs

Before submitting a bug report:
- Check existing [issues](https://github.com/username9999-sys/shell-commands-ai-skill/issues)
- Provide a clear, descriptive title
- Include steps to reproduce
- Include expected vs actual behavior
- Include environment details (OS, Python version, Docker version)

### 2. Suggesting Features

- Open a [discussion](https://github.com/username9999-sys/shell-commands-ai-skill/discussions) first
- Describe the use case and motivation
- Consider implementation complexity

### 3. Code Contributions

#### Prerequisites
- Python 3.11+
- Docker
- mandoc, groff (system packages)

#### Setup
```bash
# Fork and clone
git clone https://github.com/your-username/shell-commands-ai-skill.git
cd shell-commands-ai-skill

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r api/requirements.txt
pip install pytest pytest-asyncio httpx

# Install system packages
sudo apt-get install mandoc groff
```

#### Making Changes
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `python -m pytest tests/ -v`
4. Run linter: `python -m ruff check .` (if configured)
5. Commit with conventional commits: `git commit -m "feat: add new parser for info pages"`
6. Push and open PR

### 4. Adding New Commands

To add a new command to the dataset:

1. Add command name to `examples/seed_commands.json`
2. Run fetch: `./scripts/fetch_man.sh <command>`
3. Run parse: `python3 scripts/parse_man.py data/raw data/parsed`
4. Verify output in `data/parsed/<command>.json`
5. Rebuild index: `python3 scripts/build_index.py data/parsed data/index`

### 5. Improving Parsers

The parser is in `/parser/manparser.py`. Key areas for improvement:
- Handle more man page formats (BSD, Solaris)
- Better option parsing for complex flags
- Extract examples from more sections
- Support `info` pages and builtin `help`

### 6. Testing

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_parser.py -v
```

### 7. Code Style

- Follow PEP 8
- Type hints required for new functions
- Docstrings for public functions/classes
- Max line length: 100 chars

### 8. Documentation

Update relevant docs when making changes:
- `docs/architecture.md` for architecture changes
- `docs/security.md` for security-related changes
- `docs/data-sources.md` for new data sources
- `README.md` for user-facing changes

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Request review from maintainers
5. Address feedback
6. Squash commits if requested

## Release Process

Releases are automated via GitHub Actions on push to main:
1. Tests run
2. Index built
3. Docker image built
4. Release created with artifacts

## Questions?

Open a [discussion](https://github.com/username9999-sys/shell-commands-ai-skill/discussions) or email the maintainers.