#!/usr/bin/env python3
# test_index.py - Tests for search index

import pytest
import tempfile
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.build_index import build_bm25_index


class TestIndex:
    def test_bm25_index_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            parsed_dir = Path(tmpdir) / "parsed"
            index_dir = Path(tmpdir) / "index"
            parsed_dir.mkdir()
            index_dir.mkdir()
            
            # Create sample parsed commands
            sample_commands = [
                {
                    "name": "find",
                    "category": "file",
                    "one_line": "search for files in a directory hierarchy",
                    "usage": "find [path...] [expression]",
                    "options": [{"flag": "-name", "desc": "match filename pattern"}],
                    "examples": [{"code": "find /tmp -name '*.txt'", "explain": "find txt files"}],
                    "risk_level": "low",
                    "safety": "LOW RISK",
                    "related_commands": ["locate"],
                    "source": "man find"
                },
                {
                    "name": "grep",
                    "category": "text",
                    "one_line": "print lines matching a pattern",
                    "usage": "grep [options] pattern [file...]",
                    "options": [{"flag": "-i", "desc": "ignore case"}],
                    "examples": [{"code": "grep -r 'error' /var/log", "explain": "search recursively"}],
                    "risk_level": "low",
                    "safety": "LOW RISK",
                    "related_commands": ["sed", "awk"],
                    "source": "man grep"
                }
            ]
            
            for cmd in sample_commands:
                (parsed_dir / f"{cmd['name']}.json").write_text(json.dumps(cmd))
            
            # Build index
            build_bm25_index(parsed_dir, index_dir)
            
            # Verify index files created
            assert (index_dir / "commands.db").exists()
            
            # Verify can query
            import sqlite3
            conn = sqlite3.connect(index_dir / "commands.db")
            conn.row_factory = sqlite3.Row
            
            # Test FTS5 search
            rows = conn.execute("SELECT name FROM commands_fts WHERE commands_fts MATCH 'find'").fetchall()
            assert len(rows) == 1
            assert rows[0]["name"] == "find"
            
            rows = conn.execute("SELECT name FROM commands_fts WHERE commands_fts MATCH 'grep'").fetchall()
            assert len(rows) == 1
            assert rows[0]["name"] == "grep"
            
            rows = conn.execute("SELECT name FROM commands_fts WHERE commands_fts MATCH 'search'").fetchall()
            assert len(rows) >= 1
            
            conn.close()


if __name__ == '__main__':
    pytest.main([__file__, "-v"])