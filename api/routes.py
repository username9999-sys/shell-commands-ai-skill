from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import json
import sqlite3
from pathlib import Path

from .schemas import (
    Command, CommandCreate, CommandUpdate,
    SearchRequest, ExplainRequest, ListCommandsRequest,
    PaginatedResponse, SummaryResponse, CategorySummary,
    HealthResponse, RiskLevel,
    RunExampleRequest, RunExampleResponse
)

router = APIRouter()

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
PARSED_DIR = BASE_DIR / "data" / "parsed"
INDEX_DIR = BASE_DIR / "data" / "index"
DB_PATH = INDEX_DIR / "commands.db"

# In-memory cache for commands (for demo)
_commands_cache: dict = {}
_categories_cache: dict = {}


def load_commands_cache():
    """Load commands from parsed JSON files into memory."""
    global _commands_cache, _categories_cache
    if _commands_cache:
        return
    
    for f in PARSED_DIR.glob("*.json"):
        if f.name == "_index.json":
            continue
        with open(f) as fp:
            cmd = json.load(fp)
        _commands_cache[cmd["name"]] = cmd
        cat = cmd.get("category", "other")
        _categories_cache[cat] = _categories_cache.get(cat, 0) + 1


def get_db():
    """Get database connection."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Search index not built. Run build_index.py first.")
    return sqlite3.connect(DB_PATH)


# Initialize cache on module load
load_commands_cache()


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        commands_indexed=len(_commands_cache),
        index_updated_at="2026-01-01T00:00:00Z"  # TODO: actual timestamp
    )


@router.get("/commands", response_model=PaginatedResponse)
async def list_commands(
    category: Optional[str] = None,
    risk_level: Optional[RiskLevel] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("name", pattern="^(name|category|risk_level)$"),
    order: str = Query("asc", pattern="^(asc|desc)$")
):
    """List commands with pagination and filtering."""
    
    filtered = list(_commands_cache.values())
    
    if category:
        filtered = [c for c in filtered if c.get("category") == category]
    if risk_level:
        filtered = [c for c in filtered if c.get("risk_level") == risk_level.value]
    
    # Sort
    reverse = order == "desc"
    filtered.sort(key=lambda x: x.get(sort, ""), reverse=reverse)
    
    total = len(filtered)
    items = filtered[offset:offset + limit]
    
    return PaginatedResponse(
        items=[Command(**item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total
    )


@router.get("/commands/{name}", response_model=Command)
async def get_command(name: str):
    """Get a specific command by name."""
    if name not in _commands_cache:
        raise HTTPException(status_code=404, detail=f"Command '{name}' not found")
    
    return Command(**_commands_cache[name])


@router.post("/commands", response_model=Command, status_code=201)
async def create_command(command: CommandCreate):
    """Create a new command entry."""
    if command.name in _commands_cache:
        raise HTTPException(status_code=409, detail=f"Command '{command.name}' already exists")
    
    # Save to parsed directory
    output_file = PARSED_DIR / f"{command.name}.json"
    output_file.write_text(json.dumps(command.dict(), indent=2, ensure_ascii=False))
    
    _commands_cache[command.name] = command.dict()
    cat = command.category
    _categories_cache[cat] = _categories_cache.get(cat, 0) + 1
    
    return Command(**command.dict())


@router.patch("/commands/{name}", response_model=Command)
async def update_command(name: str, update: CommandUpdate):
    """Update a command entry."""
    if name not in _commands_cache:
        raise HTTPException(status_code=404, detail=f"Command '{name}' not found")
    
    cmd = _commands_cache[name].copy()
    update_data = update.dict(exclude_unset=True)
    cmd.update(update_data)
    
    # Save
    output_file = PARSED_DIR / f"{name}.json"
    output_file.write_text(json.dumps(cmd, indent=2, ensure_ascii=False))
    
    _commands_cache[name] = cmd
    
    return Command(**cmd)


@router.delete("/commands/{name}", status_code=204)
async def delete_command(name: str):
    """Delete a command entry."""
    if name not in _commands_cache:
        raise HTTPException(status_code=404, detail=f"Command '{name}' not found")
    
    # Remove file
    output_file = PARSED_DIR / f"{name}.json"
    if output_file.exists():
        output_file.unlink()
    
    del _commands_cache[name]
    
    # Update category count
    cat = _commands_cache.get(name, {}).get("category")
    if cat and cat in _categories_cache:
        _categories_cache[cat] = max(0, _categories_cache[cat] - 1)


@router.post("/search", response_model=PaginatedResponse)
async def search_commands(request: SearchRequest):
    """Search commands using keyword (BM25) and/or semantic search."""
    
    if not DB_PATH.exists():
        # Fallback to simple text search
        filtered = list(_commands_cache.values())
        query_lower = request.query.lower()
        
        if request.semantic:
            # Simple text matching for demo
            filtered = [
                c for c in filtered
                if query_lower in c.get("name", "").lower()
                or query_lower in c.get("one_line", "").lower()
                or query_lower in c.get("usage", "").lower()
            ]
        else:
            filtered = [
                c for c in filtered
                if query_lower in c.get("name", "").lower()
            ]
        
        if request.category:
            filtered = [c for c in filtered if c.get("category") == request.category]
        if request.risk_level:
            filtered = [c for c in filtered if c.get("risk_level") == request.risk_level.value]
        
        total = len(filtered)
        items = filtered[request.offset:request.offset + request.limit]
        
        return PaginatedResponse(
            items=[Command(**item) for item in items],
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=request.offset + request.limit < total
        )
    
    # Use SQLite FTS5 for BM25 search
    conn = get_db()
    conn.row_factory = sqlite3.Row
    
    where_clauses = ["commands_fts MATCH ?"]
    params = [request.query]
    
    if request.category:
        where_clauses.append("category = ?")
        params.append(request.category)
    if request.risk_level:
        where_clauses.append("risk_level = ?")
        params.append(request.risk_level.value)
    
    where_sql = " AND ".join(where_clauses)
    
    # Count total
    count_sql = f"SELECT COUNT(*) FROM commands_fts WHERE {where_sql}"
    total = conn.execute(count_sql, params).fetchone()[0]
    
    # Get results with rank
    search_sql = f"""
        SELECT c.*, bm25(commands_fts) as rank
        FROM commands_fts
        JOIN commands c ON commands_fts.rowid = c.rowid
        WHERE {where_sql}
        ORDER BY rank
        LIMIT ? OFFSET ?
    """
    params.extend([request.limit, request.offset])
    
    rows = conn.execute(search_sql, params).fetchall()
    conn.close()
    
    items = []
    for row in rows:
        cmd = json.loads(row["json_data"])
        items.append(Command(**cmd))
    
    return PaginatedResponse(
        items=items,
        total=total,
        limit=request.limit,
        offset=request.offset,
        has_more=request.offset + request.limit < total
    )


@router.post("/explain", response_model=Command)
async def explain_command(request: ExplainRequest):
    """Get contextual explanation for a command."""
    if request.command not in _commands_cache:
        raise HTTPException(status_code=404, detail=f"Command '{request.command}' not found")
    
    cmd = _commands_cache[request.command].copy()
    
    # Filter examples based on safety level
    if request.safety == "safe":
        cmd["examples"] = [e for e in cmd.get("examples", []) if not e.get("destructive", False)]
    
    return Command(**cmd)


@router.get("/categories", response_model=List[CategorySummary])
async def get_categories():
    """Get all categories with command counts."""
    return [
        CategorySummary(category=cat, count=count)
        for cat, count in sorted(_categories_cache.items())
    ]


@router.get("/summary", response_model=SummaryResponse)
async def get_summary():
    """Get overall summary statistics."""
    return SummaryResponse(
        total_commands=len(_commands_cache),
        categories=[
            CategorySummary(category=cat, count=count)
            for cat, count in sorted(_categories_cache.items())
        ],
        generated_at=__import__("datetime").datetime.utcnow().isoformat() + "Z"
    )


@router.post("/run-example", response_model=RunExampleResponse)
async def run_example(request: RunExampleRequest):
    """Execute a command example in the sandbox."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from sandbox.sandbox_manager import run_in_sandbox
    
    if request.command not in _commands_cache:
        raise HTTPException(status_code=404, detail=f"Command '{request.command}' not found")
    
    # Safety check
    if request.safety == "safe":
        cmd_data = _commands_cache[request.command]
        # Check if any example is destructive
        for ex in cmd_data.get("examples", []):
            if ex.get("destructive", False):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Command '{request.command}' has destructive examples. Use safety=allow-risky-examples to override."
                )
    
    # Execute in sandbox
    try:
        result = run_in_sandbox(
            command=request.command,
            args=request.args,
            timeout=request.timeout,
            cwd=request.cwd
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sandbox execution failed: {str(e)}")
    
    return RunExampleResponse(
        exit_code=result["exit_code"],
        stdout=result["stdout"],
        stderr=result["stderr"],
        timeout=result["timeout"],
        error=result["error"],
        command=request.command,
        args=request.args
    )