# Architecture

## Overview

This document describes the architecture of the Shell Commands AI Skill — a system that provides structured reference for Unix/Linux shell commands with natural language search, explanations, examples, and optional sandboxed execution.

## High-Level Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FETCH     │───▶│   PARSE     │───▶│   INDEX     │───▶│    API      │───▶│  SANDBOX    │
│  (scripts)  │    │  (parser)   │    │ (scripts)   │    │  (FastAPI)  │    │  (Docker)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                │                 │                 │                 │
      ▼                ▼                 ▼                 ▼                 ▼
  man pages        JSON per         BM25 +         REST API          Docker
  (local/remote)   command          embeddings     endpoints         container
```

## Component Responsibilities

### 1. FETCH Layer (`/scripts/fetch_man.sh`)
- Downloads man pages from local system and remote sources
- Supports: `man -P cat`, `mandoc`, `groff -Tutf8`
- Sources: local man pages, man7.org, GNU docs, TLDP
- Outputs: raw text files to `data/raw/`

### 2. PARSE Layer (`/parser/`)
- `mandoc_wrapper.py`: Wrapper around mandoc for structured output
- `manparser.py`: Extracts synopsis, options, examples, description from raw man text
- Normalizes flags (`-h` vs `--help`), categorizes commands
- Outputs: JSON per command to `data/parsed/`

### 3. INDEX Layer (`/scripts/build_index.py`)
- Builds BM25 index (SQLite FTS5 or Tantivy) for keyword search
- Generates embeddings (sentence-transformers) for semantic search
- Creates FAISS/Milvus vector index
- Outputs: search index files to `data/index/`

### 4. API Layer (`/api/`)
- `schemas.py`: Pydantic models for request/response validation
- `routes.py`: FastAPI route handlers
- `app.py`: Application factory, middleware, lifespan
- Endpoints: command lookup, search, explain, list, categories

### 5. SANDBOX Layer (`/sandbox/`) — Optional
- `Dockerfile`: Minimal sandbox image with seccomp/AppArmor
- `sandbox_manager.py`: Orchestrates container execution
- `run_sandbox.sh`: CLI entrypoint for sandbox runs
- Policies: no network, read-only FS, CPU/memory limits, timeout

### 6. UI Layer (`/ui/web/`) — Optional
- Static web interface for browsing commands
- Chat-style interaction with the skill

## Data Flow

1. **Ingestion**: `fetch_man.sh` → raw man pages → `data/raw/`
2. **Parsing**: `parse_man.py` + `manparser.py` → structured JSON → `data/parsed/`
3. **Indexing**: `build_index.py` → BM25 + vector index → `data/index/`
4. **Serving**: `uvicorn api.app:app` → REST API on port 8000
5. **Execution** (optional): `docker run shell-skill-sandbox <command>` → isolated output

## Technology Choices

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Parser | mandoc / groff | Standard, handles all man page formats |
| Search | SQLite FTS5 + FAISS | Lightweight, no external deps, fast |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Small, fast, good quality |
| API | FastAPI | Async, auto-docs, type-safe |
| Sandbox | Docker + seccomp | Strong isolation, standard tooling |
| Tests | pytest | Standard Python testing |

## Scalability Considerations

- Parsing is embarrassingly parallel (one process per command)
- Index building is batch; can be incremental
- API is stateless; horizontally scalable
- Sandbox runs are isolated; can use container pool