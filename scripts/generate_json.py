#!/usr/bin/env python3
# generate_json.py - Generate final JSON dataset from parsed commands
# Usage: python3 generate_json.py <parsed_dir> <output_dir>

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any


def main():
    parser = argparse.ArgumentParser(description='Generate final JSON dataset')
    parser.add_argument('parsed_dir', help='Directory with parsed command JSON')
    parser.add_argument('output_dir', help='Output directory for dataset')
    parser.add_argument('--single', action='store_true', help='Output single commands.json file')
    args = parser.parse_args()

    parsed_dir = Path(args.parsed_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed_files = list(parsed_dir.glob('*.json'))
    parsed_files = [f for f in parsed_files if f.name != '_index.json']

    all_commands = []
    categories = {}

    for pf in parsed_files:
        with open(pf) as f:
            cmd = json.load(f)
        all_commands.append(cmd)
        
        cat = cmd.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + 1

    # Sort by name
    all_commands.sort(key=lambda x: x['name'])

    if args.single:
        # Single file with all commands
        output_file = output_dir / "commands.json"
        output_file.write_text(json.dumps(all_commands, indent=2, ensure_ascii=False))
        print(f"Generated {output_file} with {len(all_commands)} commands")
    else:
        # Per-command files (already exist from parse_man.py)
        # Just create category index
        for cat, count in sorted(categories.items()):
            cat_commands = [c for c in all_commands if c.get('category') == cat]
            cat_file = output_dir / f"category_{cat}.json"
            cat_file.write_text(json.dumps(cat_commands, indent=2, ensure_ascii=False))
            print(f"Generated {cat_file} ({count} commands)")

    # Categories summary
    summary = {
        'total_commands': len(all_commands),
        'categories': categories,
        'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z'
    }
    summary_file = output_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Generated {summary_file}")

    print(f"\nDone. Total commands: {len(all_commands)}")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()