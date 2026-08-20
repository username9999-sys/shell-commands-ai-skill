#!/usr/bin/env python3
# manparser.py - Core man page parser

import re
from typing import Dict, List, Any
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
    CATEGORY_KEYWORDS = {
        'permission': ['chmod', 'chown', 'chgrp', 'umask', 'mode', 'permission'],
        'network': ['ssh', 'scp', 'rsync', 'curl', 'wget', 'ping', 'netstat', 'ss', 'dig', 'nslookup', 'traceroute', 'transfer', 'url', 'http', 'ftp'],
        'archive': ['tar', 'gzip', 'gunzip', 'bzip2', 'xz', 'zip', 'unzip', 'compress', 'extract', 'archive'],
        'process': ['ps', 'top', 'kill', 'jobs', 'bg', 'fg', 'nohup', 'disown', 'wait', 'sleep', 'process'],
        'disk': ['df', 'du', 'fdisk', 'parted', 'mount', 'umount', 'mkfs', 'disk', 'partition'],
        'system': ['reboot', 'shutdown', 'systemctl', 'service', 'uptime', 'who', 'w'],
        'package': ['apt', 'yum', 'dnf', 'pacman', 'dpkg', 'rpm', 'brew', 'package'],
        'shell-builtin': ['alias', 'unalias', 'export', 'set', 'unset', 'declare', 'history', 'type', 'builtin', 'which', 'command'],
        'text': ['grep', 'sed', 'awk', 'sort', 'cut', 'tr', 'wc', 'head', 'tail', 'cat', 'less', 'more', 'uniq', 'fmt', 'fold', 'join', 'paste', 'print', 'matching', 'pattern', 'stream'],
        'file': ['ls', 'cp', 'mv', 'rm', 'find', 'mkdir', 'rmdir', 'touch', 'ln', 'chmod', 'chown', 'file', 'directory', 'copy', 'move', 'remove', 'link', 'locate', 'stat', 'list'],
        'search': ['find', 'locate', 'grep', 'which', 'whereis', 'search'],
    }

    def detect_category(self, name: str, description: str) -> str:
        name_map = {
            'chmod': 'permission', 'chown': 'permission', 'chgrp': 'permission', 'umask': 'permission',
            'ssh': 'network', 'scp': 'network', 'rsync': 'network', 'curl': 'network', 'wget': 'network',
            'tar': 'archive', 'gzip': 'archive', 'gunzip': 'archive', 'zip': 'archive', 'unzip': 'archive',
            'ps': 'process', 'top': 'process', 'kill': 'process', 'killall': 'process', 'nohup': 'process',
            'df': 'disk', 'du': 'disk', 'mount': 'disk', 'umount': 'disk',
            'find': 'search', 'grep': 'text', 'sed': 'text', 'awk': 'text', 'sort': 'text',
            'ls': 'file', 'cp': 'file', 'mv': 'file', 'rm': 'file', 'cat': 'file',
            'mkdir': 'file', 'rmdir': 'file', 'touch': 'file', 'ln': 'file',
            'head': 'text', 'tail': 'text', 'less': 'text', 'more': 'text', 'cut': 'text',
            'tr': 'text', 'wc': 'text', 'uniq': 'text',
            'alias': 'shell-builtin', 'export': 'shell-builtin', 'history': 'shell-builtin',
            'apt': 'package', 'yum': 'package', 'dnf': 'package', 'pacman': 'package',
        }
        if name in name_map:
            return name_map[name]

        text = f"{name} {description}".lower()
        scores = {}
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            scores[cat] = sum(1 for kw in keywords if kw in text)
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'other'

    def parse(self, name: str, raw_text: str) -> ParsedCommand:
        text = raw_text.strip()
        sections = self._extract_sections(text)

        name_section = sections.get('NAME', '')
        one_line = self._extract_one_line(name_section)
        usage = self._extract_usage(sections.get('SYNOPSIS', ''))
        options = self._extract_options(sections.get('OPTIONS', ''))
        examples = self._extract_examples(text)

        risk_level = self._assess_risk(name, options, examples)
        safety = self._generate_safety(name, risk_level)
        related = self._find_related(name, raw_text)
        category = self.detect_category(name, one_line)

        return ParsedCommand(
            name=name, category=category, one_line=one_line, usage=usage,
            options=options, examples=examples, risk_level=risk_level,
            safety=safety, related_commands=related, source=f"man {name}",
        )

    def _extract_sections(self, text: str) -> Dict[str, str]:
        sections = {}
        current = None
        lines_buf = []

        for line in text.split('\n'):
            stripped = line.strip()
            if stripped and stripped[0].isupper() and stripped.isupper() and len(stripped) < 50:
                if current:
                    sections[current] = '\n'.join(lines_buf).strip()
                current = stripped
                lines_buf = []
            elif current:
                lines_buf.append(line)

        if current:
            sections[current] = '\n'.join(lines_buf).strip()

        return sections

    def _extract_one_line(self, name_text: str) -> str:
        if not name_text:
            return ""
        name_text = re.sub(r'\s+', ' ', name_text).strip()
        if ' - ' in name_text:
            parts = name_text.split(' - ', 1)
            if len(parts) > 1:
                desc = parts[1].strip()
                # Include command name if not in description
                return parts[0].strip() + " - " + desc if parts[0].strip().lower() not in desc.lower() else desc
        sentences = re.split(r'(?<=[.!?])\s+', name_text)
        for s in sentences:
            s = s.strip()
            if len(s) > 10:
                return s
        return name_text[:200]

    def _extract_usage(self, synopsis: str) -> str:
        if not synopsis:
            return ""
        return re.sub(r'\s+', ' ', synopsis).strip()

    def _extract_options(self, options_text: str) -> List[CommandOption]:
        """Parse OPTIONS section - extract flag+description pairs."""
        options = []
        if not options_text:
            return options

        lines = options_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check if this line starts with a flag
            flag_match = re.match(r'^(-\S+(?:,\s*--\S+)?)', line)
            if not flag_match:
                i += 1
                continue

            flag = flag_match.group(1).strip()
            
            # Description is rest of this line + any continuation lines that don't start with flag
            desc_parts = [line[flag_match.end():].strip()]
            i += 1
            
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                # Check if next line starts a new flag
                if re.match(r'^-\S', next_line):
                    break
                # Continuation line - add to description
                if next_line:
                    desc_parts.append(next_line)
                i += 1

            desc = ' '.join(desc_parts)
            desc = re.sub(r'\s+', ' ', desc).strip()
            if desc:
                options.append(CommandOption(flag=flag, desc=desc))
            else:
                i += 1

        return options[:20]

    def _extract_examples(self, text: str) -> List[CommandExample]:
        examples = []
        examples_section = re.search(r'EXAMPLES?\n(.*?)(?:\n[A-Z]{2,}|\Z)', text, re.IGNORECASE | re.DOTALL)
        if examples_section:
            example_text = examples_section.group(1)
            # Split by double newline (empty line) to separate examples
            example_blocks = re.split(r'\n\s*\n', example_text.strip())
            for block in example_blocks[:4]:
                lines = block.strip().split('\n')
                if lines:
                    code = lines[0].strip()  # First line is the command
                    if code:
                        examples.append(CommandExample(
                            code=code,
                            explain=f"Example of {code.split()[0] if code.split() else 'command'}",
                            destructive=self._is_destructive(code)
                        ))
        return examples

    def _is_destructive(self, code: str) -> bool:
        patterns = [
            r'\brm\s+.*-[rf]', r'\bdd\s+', r'\bmkfs\b', r'\bfdisk\b',
            r'curl\s+.*\|\s*(sh|bash)', r'chmod\s+777', r'chown\s+-R',
            r'\b-exec\s+rm\b', r'\brm\s+[{}]',  # find -exec rm {} patterns
        ]
        return any(re.search(p, code) for p in patterns)

    def _assess_risk(self, name, options, examples) -> str:
        if name in ('rm', 'dd', 'mkfs', 'fdisk', 'parted', 'shred', 'wipefs'):
            return 'high'
        if name in ('chmod', 'chown', 'chgrp', 'mount', 'umount', 'kill', 'systemctl'):
            return 'medium'
        # Only consider recursive/force as medium risk for commands that modify filesystem
        modifying_commands = {'cp', 'mv', 'rm', 'chmod', 'chown', 'chgrp', 'mkdir', 'rmdir', 'tar', 'cpio'}
        if name in modifying_commands and any('recursive' in o.desc.lower() or 'force' in o.desc.lower() for o in options):
            return 'medium'
        return 'low'

    def _generate_safety(self, name: str, risk_level: str, options: List[CommandOption] = None) -> str:
        if risk_level == 'high':
            return f"HIGH RISK: {name} can cause data loss or system damage. Always use --dry-run or preview first. Never run without explicit confirmation and sandboxing."
        if risk_level == 'medium':
            return f"MEDIUM RISK: {name} modifies system state. Review options carefully. Use -i/--interactive for confirmation prompts."
        return "LOW RISK: Read-only or safe operations. Still verify paths and arguments before running."

    def _find_related(self, name, text) -> List[str]:
        related = ['ls', 'cp', 'mv', 'rm', 'find', 'grep', 'sed', 'awk', 'sort', 'cat', 'less', 'head', 'tail', 'mkdir', 'touch', 'tar', 'ssh', 'curl', 'locate', 'xargs', 'cut', 'tr', 'wc']
        mentioned = [cmd for cmd in related if re.search(rf'\b{cmd}\b', text, re.IGNORECASE) and cmd != name]
        return mentioned[:5]

    def detect_category(self, name: str, description: str) -> str:
        name_map = {
            'chmod': 'permission', 'chown': 'permission', 'chgrp': 'permission', 'umask': 'permission',
            'ssh': 'network', 'scp': 'network', 'rsync': 'network', 'curl': 'network', 'wget': 'network',
            'tar': 'archive', 'gzip': 'archive', 'gunzip': 'archive', 'zip': 'archive', 'unzip': 'archive',
            'ps': 'process', 'top': 'process', 'kill': 'process', 'killall': 'process', 'nohup': 'process',
            'df': 'disk', 'du': 'disk', 'mount': 'disk', 'umount': 'disk',
            'find': 'search', 'grep': 'text', 'sed': 'text', 'awk': 'text', 'sort': 'text',
            'ls': 'file', 'cp': 'file', 'mv': 'file', 'rm': 'file', 'cat': 'file',
            'mkdir': 'file', 'rmdir': 'file', 'touch': 'file', 'ln': 'file',
            'head': 'text', 'tail': 'text', 'less': 'text', 'more': 'text', 'cut': 'text',
            'tr': 'text', 'wc': 'text', 'uniq': 'text',
            'alias': 'shell-builtin', 'export': 'shell-builtin', 'history': 'shell-builtin',
            'apt': 'package', 'yum': 'package', 'dnf': 'package', 'pacman': 'package',
        }
        if name in name_map:
            return name_map[name]

        text = f"{name} {description}".lower()
        scores = {}
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            scores[cat] = sum(1 for kw in keywords if kw in text)
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'other'

    def _extract_sections(self, text: str) -> Dict[str, str]:
        sections = {}
        current = None
        lines_buf = []

        for line in text.split('\n'):
            stripped = line.strip()
            if stripped and stripped[0].isupper() and stripped.isupper() and len(stripped) < 50:
                if current:
                    sections[current] = '\n'.join(lines_buf).strip()
                current = stripped
                lines_buf = []
            elif current:
                lines_buf.append(line)

        if current:
            sections[current] = '\n'.join(lines_buf).strip()

        return sections

    def _extract_one_line(self, name_text: str) -> str:
        if not name_text:
            return ""
        name_text = re.sub(r'\s+', ' ', name_text).strip()
        if ' - ' in name_text:
            parts = name_text.split(' - ', 1)
            if len(parts) > 1:
                desc = parts[1].strip()
                # Include command name if not in description
                return parts[0].strip() + " - " + desc if parts[0].strip().lower() not in desc.lower() else desc
        sentences = re.split(r'(?<=[.!?])\s+', name_text)
        for s in sentences:
            s = s.strip()
            if len(s) > 10:
                return s
        return name_text[:200]

    def _extract_usage(self, synopsis: str) -> str:
        if not synopsis:
            return ""
        return re.sub(r'\s+', ' ', synopsis).strip()

    def _extract_examples(self, text: str) -> List[CommandExample]:
        examples = []
        examples_section = re.search(r'EXAMPLES?\n(.*?)(?:\n[A-Z]{2,}|\Z)', text, re.IGNORECASE | re.DOTALL)
        if examples_section:
            example_text = examples_section.group(1)
            # Split by double newline (empty line) to separate examples
            example_blocks = re.split(r'\n\s*\n', example_text.strip())
            for block in example_blocks[:4]:
                lines = block.strip().split('\n')
                if lines:
                    code = lines[0].strip()  # First line is the command
                    if code:
                        examples.append(CommandExample(
                            code=code,
                            explain=f"Example of {code.split()[0] if code.split() else 'command'}",
                            destructive=self._is_destructive(code)
                        ))
        return examples

    def _is_destructive(self, code: str) -> bool:
        patterns = [
            r'\brm\s+.*-[rf]', r'\bdd\s+', r'\bmkfs\b', r'\bfdisk\b',
            r'curl\s+.*\|\s*(sh|bash)', r'chmod\s+777', r'chown\s+-R',
            r'\b-exec\s+rm\b', r'\brm\s+[{}]',  # find -exec rm {} patterns
        ]
        return any(re.search(p, code) for p in patterns)

    def _assess_risk(self, name, options, examples) -> str:
        if name in ('rm', 'dd', 'mkfs', 'fdisk', 'parted', 'shred', 'wipefs'):
            return 'high'
        if name in ('chmod', 'chown', 'chgrp', 'mount', 'umount', 'kill', 'systemctl'):
            return 'medium'
        # Only consider recursive/force as medium risk for commands that modify filesystem
        modifying_commands = {'cp', 'mv', 'rm', 'chmod', 'chown', 'chgrp', 'mkdir', 'rmdir', 'tar', 'cpio'}
        if name in modifying_commands and any('recursive' in o.desc.lower() or 'force' in o.desc.lower() for o in options):
            return 'medium'
        return 'low'

    def _generate_safety(self, name: str, risk_level: str, options: List[CommandOption] = None) -> str:
        if risk_level == 'high':
            return f"HIGH RISK: {name} can cause data loss or system damage. Always use --dry-run or preview first. Never run without explicit confirmation and sandboxing."
        if risk_level == 'medium':
            return f"MEDIUM RISK: {name} modifies system state. Review options carefully. Use -i/--interactive for confirmation prompts."
        return "LOW RISK: Read-only or safe operations. Still verify paths and arguments before running."

    def _find_related(self, name, text) -> List[str]:
        related = ['ls', 'cp', 'mv', 'rm', 'find', 'grep', 'sed', 'awk', 'sort', 'cat', 'less', 'head', 'tail', 'mkdir', 'touch', 'tar', 'ssh', 'curl', 'locate', 'xargs', 'cut', 'tr', 'wc']
        mentioned = [cmd for cmd in related if re.search(rf'\b{cmd}\b', text, re.IGNORECASE) and cmd != name]
        return mentioned[:5]


def parse_man_text(name: str, text: str) -> Dict[str, Any]:
    parser = ManParser()
    result = parser.parse(name, text)
    return asdict(result)


if __name__ == '__main__':
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python3 manparser.py <command> [raw_text_file]")
        sys.exit(1)
    command = sys.argv[1]
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            text = f.read()
    else:
        import subprocess
        result = subprocess.run(['man', '-P', 'cat', command], capture_output=True, text=True)
        text = result.stdout
    result = parse_man_text(command, text)
    print(json.dumps(result, indent=2, ensure_ascii=False))