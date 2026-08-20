#!/usr/bin/env python3
# parse_man.py - Parse raw man pages into structured JSON
# Usage: python3 parse_man.py <raw_dir> <parsed_dir>

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

@dataclass
class CommandOption:
    flag: str
    desc: str
    examples: List[str] = field(default_factory=list)

@dataclass
class CommandExample:
    code: str
    explain: str
    destructive: bool = False

@dataclass
class ParsedCommand:
    name: str
    category: str
    one_line: str
    usage: str
    options: List[CommandOption]
    examples: List[CommandExample]
    risk_level: str  # low, medium, high
    safety: str
    related_commands: List[str]
    source: str
    source_version: str = ""
    fetched_at: str = ""

class ManParser:
    def __init__(self):
        self.category_keywords = {
            'file': ['file', 'directory', 'copy', 'move', 'remove', 'link', 'find', 'locate', 'stat', 'ls', 'cp', 'mv', 'rm', 'mkdir', 'rmdir', 'touch', 'chmod', 'chown', 'ln'],
            'text': ['text', 'stream', 'editor', 'grep', 'sed', 'awk', 'sort', 'cut', 'tr', 'wc', 'head', 'tail', 'cat', 'less', 'more', 'uniq', 'fmt', 'fold', 'join', 'paste'],
            'process': ['process', 'job', 'signal', 'kill', 'ps', 'top', 'htop', 'jobs', 'bg', 'fg', 'nohup', 'disown', 'wait', 'sleep'],
            'network': ['network', 'ssh', 'scp', 'rsync', 'curl', 'wget', 'ping', 'netstat', 'ss', 'ip', 'dig', 'nslookup', 'traceroute'],
            'package': ['package', 'apt', 'yum', 'dnf', 'pacman', 'dpkg', 'rpm', 'snap', 'flatpak', 'brew'],
            'shell-builtin': ['builtin', 'alias', 'unalias', 'export', 'set', 'unset', 'declare', 'local', 'readonly', 'typeset', 'shift', 'history', 'fc', 'type', 'which', 'command'],
            'archive': ['archive', 'compress', 'tar', 'gzip', 'gunzip', 'bzip2', 'xz', 'zip', 'unzip', '7z'],
            'system': ['system', 'reboot', 'shutdown', 'halt', 'systemctl', 'service', 'journalctl', 'dmesg', 'uptime', 'who', 'w', 'last'],
            'disk': ['disk', 'df', 'du', 'fdisk', 'parted', 'lsblk', 'mount', 'umount', 'fsck', 'mkfs', 'dd'],
            'permission': ['permission', 'chmod', 'chown', 'chgrp', 'umask', 'stat', 'getfacl', 'setfacl'],
            'search': ['search', 'find', 'locate', 'grep', 'rg', 'ag', 'ack', 'which', 'whereis', 'type'],
        }

    def detect_category(self, name: str, description: str) -> str:
        text = f"{name} {description}".lower()
        scores = {}
        for cat, keywords in self.category_keywords.items():
            scores[cat] = sum(1 for kw in keywords if kw in text)
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'other'

    def parse(self, name: str, raw_text: str) -> ParsedCommand:
        # Clean text
        text = raw_text.strip()
        
        # Extract sections
        sections = self._extract_sections(text)
        
        # One-line summary (from DESCRIPTION first paragraph)
        one_line = self._extract_one_line(sections.get('DESCRIPTION', ''))
        
        # Usage (from SYNOPSIS)
        usage = self._extract_usage(sections.get('SYNOPSIS', ''))
        
        # Options (from OPTIONS)
        options = self._extract_options(sections.get('OPTIONS', ''))
        
        # Examples (from EXAMPLES or scattered)
        examples = self._extract_examples(text)
        
        # Risk level
        risk_level = self._assess_risk(name, options, examples)
        
        # Safety notes
        safety = self._generate_safety(name, risk_level, options)
        
        # Related commands
        related = self._find_related(name, text)
        
        category = self.detect_category(name, one_line)
        
        return ParsedCommand(
            name=name,
            category=category,
            one_line=one_line,
            usage=usage,
            options=options,
            examples=examples,
            risk_level=risk_level,
            safety=safety,
            related_commands=related,
            source=f"man {name}",
        )

    def _extract_sections(self, text: str) -> Dict[str, str]:
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            # Detect section headers (all caps, possibly with numbers)
            match = re.match(r'^([A-Z][A-Z\s]+)\s*$', line.strip())
            if match and len(line.strip()) < 50:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections

    def _extract_one_line(self, desc: str) -> str:
        if not desc:
            return ""
        # First sentence of description
        sentences = re.split(r'(?<=[.!?])\s+', desc.strip())
        return sentences[0] if sentences else desc[:200]

    def _extract_usage(self, synopsis: str) -> str:
        if not synopsis:
            return ""
        # Clean up synopsis
        usage = re.sub(r'\s+', ' ', synopsis).strip()
        # Remove leading command name if duplicated
        return usage

    def _extract_options(self, options_text: str) -> List[CommandOption]:
        options = []
        if not options_text:
            return options
        
        # Pattern: -x, --long description
        option_pattern = re.compile(
            r'^(\s*-\w(?:,\s*--[\w-]+)?|--[\w-]+)\s+(.+)$',
            re.MULTILINE
        )
        
        for match in option_pattern.finditer(options_text):
            flag = match.group(1).strip()
            desc = match.group(2).strip()
            # Clean up description
            desc = re.sub(r'\s+', ' ', desc)
            options.append(CommandOption(flag=flag, desc=desc))
        
        return options[:20]  # Limit

    def _extract_examples(self, text: str) -> List[CommandExample]:
        examples = []
        
        # Look for EXAMPLES section
        examples_section = re.search(r'EXAMPLES?\n(.*?)(?:\n[A-Z]{2,}|\Z)', text, re.IGNORECASE | re.DOTALL)
        if examples_section:
            example_text = examples_section.group(1)
            # Find code blocks (indented lines)
            code_blocks = re.findall(r'^\s{4,}(.+)$', example_text, re.MULTILINE)
            for code in code_blocks[:4]:
                code = code.strip()
                if code and not code.startswith('#'):
                    examples.append(CommandExample(
                        code=code,
                        explain=f"Example usage of {code.split()[0] if code.split() else 'command'}",
                        destructive=self._is_destructive(code)
                    ))
        
        return examples

    def _is_destructive(self, code: str) -> bool:
        destructive_patterns = [
            r'\brm\s+.*-[rf]', r'\bdd\s+', r'\bmkfs\b', r'\bfdisk\b',
            r'\bparted\b', r'>\s*/dev/', r'curl\s+.*\|\s*(sh|bash)',
            r'wget\s+.*\|\s*(sh|bash)', r'chmod\s+777', r'chown\s+-R'
        ]
        return any(re.search(p, code) for p in destructive_patterns)

    def _assess_risk(self, name: str, options: List[CommandOption], examples: List[CommandExample]) -> str:
        high_risk = {'rm', 'dd', 'mkfs', 'fdisk', 'parted', 'mkfs.*', 'shred', 'wipefs'}
        medium_risk = {'chmod', 'chown', 'chgrp', 'mount', 'umount', 'kill', 'systemctl', 'service'}
        
        if name in high_risk:
            return 'high'
        if name in medium_risk:
            return 'medium'
        if any(ex.destructive for ex in examples):
            return 'high'
        if any('recursive' in o.desc.lower() or 'force' in o.desc.lower() for o in options):
            return 'medium'
        return 'low'

    def _generate_safety(self, name: str, risk_level: str, options: List[CommandOption]) -> str:
        if risk_level == 'high':
            return f"HIGH RISK: {name} can cause data loss or system damage. Always use --dry-run or preview first. Never run without explicit confirmation and sandboxing."
        elif risk_level == 'medium':
            return f"MEDIUM RISK: {name} modifies system state. Review options carefully. Use -i/--interactive for confirmation prompts."
        return "LOW RISK: Read-only or safe operations. Still verify paths and arguments before running."

    def _find_related(self, name: str, text: str) -> List[str]:
        # Simple heuristic: find other command names mentioned
        common_commands = ['ls', 'cp', 'mv', 'rm', 'find', 'grep', 'sed', 'awk', 'sort', 'cat', 'less', 'head', 'tail', 'mkdir', 'rmdir', 'touch', 'chmod', 'chown', 'tar', 'gzip', 'ssh', 'scp', 'rsync']
        mentioned = [cmd for cmd in common_commands if re.search(rf'\b{cmd}\b', text) and cmd != name]
        return mentioned[:5]


def main():
    parser = argparse.ArgumentParser(description='Parse man pages to JSON')
    parser.add_argument('raw_dir', help='Directory with raw man pages')
    parser.add_argument('parsed_dir', help='Output directory for parsed JSON')
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    parsed_dir = Path(args.parsed_dir)
    parsed_dir.mkdir(parents=True, exist_ok=True)

    parser = ManParser()
    results = []

    for raw_file in raw_dir.glob('*.txt'):
        if raw_file.name.startswith('.'):
            continue
        name = raw_file.stem
        try:
            content = raw_file.read_text(encoding='utf-8', errors='ignore')
            parsed = parser.parse(name, content)
            parsed.fetched_at = raw_file.stat().st_mtime
            results.append(parsed)
            
            # Write individual JSON
            output_file = parsed_dir / f"{name}.json"
            output_file.write_text(json.dumps(asdict(parsed), indent=2, ensure_ascii=False))
            print(f"✓ Parsed: {name}")
        except Exception as e:
            print(f"✗ Failed {name}: {e}")

    # Write index
    index_file = parsed_dir / "_index.json"
    index_file.write_text(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
    print(f"\nDone. Parsed {len(results)} commands.")

if __name__ == '__main__':
    main()