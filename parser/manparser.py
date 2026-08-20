#!/usr/bin/env python3
# manparser.py - Core man page parser used by parse_man.py
# This is the main parsing logic, extracted for reusability

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


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
    risk_level: str
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
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'other'

    def parse(self, name: str, raw_text: str) -> ParsedCommand:
        text = raw_text.strip()
        sections = self._extract_sections(text)
        
        one_line = self._extract_one_line(sections.get('DESCRIPTION', ''))
        usage = self._extract_usage(sections.get('SYNOPSIS', ''))
        options = self._extract_options(sections.get('OPTIONS', ''))
        examples = self._extract_examples(text)
        
        risk_level = self._assess_risk(name, options, examples)
        safety = self._generate_safety(name, risk_level, options)
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
        sentences = re.split(r'(?<=[.!?])\s+', desc.strip())
        return sentences[0] if sentences else desc[:200]

    def _extract_usage(self, synopsis: str) -> str:
        if not synopsis:
            return ""
        return re.sub(r'\s+', ' ', synopsis).strip()

    def _extract_options(self, options_text: str) -> List[CommandOption]:
        options = []
        if not options_text:
            return options
        
        option_pattern = re.compile(
            r'^(\s*-\w(?:,\s*--[\w-]+)?|--[\w-]+)\s+(.+)$',
            re.MULTILINE
        )
        
        for match in option_pattern.finditer(options_text):
            flag = match.group(1).strip()
            desc = match.group(2).strip()
            desc = re.sub(r'\s+', ' ', desc)
            options.append(CommandOption(flag=flag, desc=desc))
        
        return options[:20]

    def _extract_examples(self, text: str) -> List[CommandExample]:
        examples = []
        
        examples_section = re.search(r'EXAMPLES?\n(.*?)(?:\n[A-Z]{2,}|\Z)', text, re.IGNORECASE | re.DOTALL)
        if examples_section:
            example_text = examples_section.group(1)
            code_blocks = re.findall(r'^\s{4,}(.+)$', example_text, re.MULTILINE)
            for code in code_blocks[:4]:
                code = code.strip()
                if code:
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
        common_commands = ['ls', 'cp', 'mv', 'rm', 'find', 'grep', 'sed', 'awk', 'sort', 'cat', 'less', 'head', 'tail', 'mkdir', 'rmdir', 'touch', 'chmod', 'chown', 'tar', 'gzip', 'ssh', 'scp', 'rsync']
        mentioned = [cmd for cmd in common_commands if re.search(rf'\b{cmd}\b', text) and cmd != name]
        return mentioned[:5]


def parse_man_text(name: str, text: str) -> Dict[str, Any]:
    """Convenience function to parse man text and return dict."""
    parser = ManParser()
    result = parser.parse(name, text)
    return asdict(result)


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python3 manparser.py <command> [raw_text_file]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            text = f.read()
    else:
        # Try to fetch from system man
        import subprocess
        result = subprocess.run(['man', '-P', 'cat', command], capture_output=True, text=True)
        text = result.stdout
    
    result = parse_man_text(command, text)
    print(json.dumps(result, indent=2, ensure_ascii=False))