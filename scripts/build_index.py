#!/usr/bin/env python3
# build_index.py - Build search index from parsed commands
# Usage: python3 build_index.py <parsed_dir> <index_dir>

import os
import json
import argparse
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
    FAISS_IMPORT_ERROR = None
except ImportError as e:
    HAS_EMBEDDINGS = False
    FAISS_IMPORT_ERROR = str(e)
    print(f"Warning: sentence-transformers/faiss not installed. Only BM25 index will be built. Error: {e}")


def build_bm25_index(parsed_dir: Path, index_dir: Path):
    """Build SQLite FTS5 index for keyword search."""
    index_dir.mkdir(parents=True, exist_ok=True)
    db_path = index_dir / "commands.db"
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS commands_fts USING fts5(
            name, category, one_line, usage, options, examples, related,
            content='commands', content_rowid='rowid'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            rowid INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            category TEXT,
            one_line TEXT,
            usage TEXT,
            options TEXT,
            examples TEXT,
            related TEXT,
            risk_level TEXT,
            safety TEXT,
            source TEXT,
            json_data TEXT
        )
    """)
    
    # Clear existing
    conn.execute("DELETE FROM commands_fts")
    conn.execute("DELETE FROM commands")
    
    parsed_files = list(parsed_dir.glob('*.json'))
    parsed_files = [f for f in parsed_files if f.name != '_index.json']
    
    for i, pf in enumerate(parsed_files):
        with open(pf) as f:
            cmd = json.load(f)
        
        options_text = ' '.join([o['flag'] + ' ' + o['desc'] for o in cmd.get('options', [])])
        examples_text = ' '.join([e['code'] + ' ' + e.get('explain', '') for e in cmd.get('examples', [])])
        related_text = ' '.join(cmd.get('related_commands', []))
        
        cursor = conn.execute("""
            INSERT INTO commands (name, category, one_line, usage, options, examples, related, risk_level, safety, source, json_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cmd['name'], cmd['category'], cmd['one_line'], cmd['usage'],
            options_text, examples_text, related_text,
            cmd['risk_level'], cmd['safety'], cmd['source'],
            json.dumps(cmd)
        ))
        
        rowid = cursor.lastrowid
        conn.execute("""
            INSERT INTO commands_fts (rowid, name, category, one_line, usage, options, examples, related)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (rowid, cmd['name'], cmd['category'], cmd['one_line'], cmd['usage'],
              options_text, examples_text, related_text))
        
        if (i + 1) % 50 == 0:
            print(f"  Indexed {i + 1}/{len(parsed_files)} commands...")
    
    conn.commit()
    conn.close()
    print(f"BM25 index built: {db_path}")


def build_vector_index(parsed_dir: Path, index_dir: Path):
    """Build FAISS vector index for semantic search."""
    if not HAS_EMBEDDINGS:
        print("Skipping vector index (dependencies not available)")
        return
    
    index_dir.mkdir(parents=True, exist_ok=True)
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    parsed_files = list(parsed_dir.glob('*.json'))
    parsed_files = [f for f in parsed_files if f.name != '_index.json']
    
    texts = []
    metadatas = []
    
    for pf in parsed_files:
        with open(pf) as f:
            cmd = json.load(f)
        
        # Create searchable text combining name, description, usage
        text = f"{cmd['name']}: {cmd['one_line']}. Usage: {cmd['usage']}"
        for opt in cmd.get('options', []):
            text += f" {opt['flag']} {opt['desc']}"
        for ex in cmd.get('examples', []):
            text += f" Example: {ex['code']}"
        
        texts.append(text)
        metadatas.append({'name': cmd['name'], 'category': cmd['category']})
    
    print(f"Encoding {len(texts)} commands...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Build index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product = cosine for normalized vectors
    index.add(embeddings.astype('float32'))
    
    # Save index and metadata
    faiss.write_index(index, str(index_dir / "commands.faiss"))
    
    with open(index_dir / "vector_meta.json", 'w') as f:
        json.dump(metadatas, f, ensure_ascii=False, indent=2)
    
    print(f"Vector index built: {index_dir / 'commands.faiss'} ({len(texts)} vectors, dim={dimension})")


def main():
    parser = argparse.ArgumentParser(description='Build search indexes')
    parser.add_argument('parsed_dir', help='Directory with parsed command JSON')
    parser.add_argument('index_dir', help='Output directory for indexes')
    args = parser.parse_args()

    parsed_dir = Path(args.parsed_dir)
    index_dir = Path(args.index_dir)
    
    print("Building BM25 (keyword) index...")
    build_bm25_index(parsed_dir, index_dir)
    
    if HAS_EMBEDDINGS:
        print("Building FAISS (vector) index...")
        build_vector_index(parsed_dir, index_dir)
    else:
        print("Install sentence-transformers and faiss-cpu for vector search:")
        print("  pip install sentence-transformers faiss-cpu")
    
    print("All indexes built successfully!")


if __name__ == '__main__':
    main()