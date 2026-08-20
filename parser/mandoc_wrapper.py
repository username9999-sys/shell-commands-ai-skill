#!/usr/bin/env python3
# mandoc_wrapper.py - Wrapper around mandoc for structured man page parsing

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List


def check_mandoc() -> bool:
    """Check if mandoc is available."""
    return shutil.which('mandoc') is not None


def check_groff() -> bool:
    """Check if groff is available."""
    return shutil.which('groff') is not None


def mandoc_to_text(man_page_path: Path) -> str:
    """Convert man page to plain text using mandoc."""
    if not check_mandoc():
        raise RuntimeError("mandoc not found. Install with: apt-get install mandoc")
    
    result = subprocess.run(
        ['mandoc', '-T', 'utf8', str(man_page_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"mandoc failed: {result.stderr}")
    
    return result.stdout


def mandoc_to_html(man_page_path: Path) -> str:
    """Convert man page to HTML using mandoc."""
    if not check_mandoc():
        raise RuntimeError("mandoc not found")
    
    result = subprocess.run(
        ['mandoc', '-T', 'html', str(man_page_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"mandoc failed: {result.stderr}")
    
    return result.stdout


def mandoc_to_markdown(man_page_path: Path) -> str:
    """Convert man page to markdown using mandoc."""
    if not check_mandoc():
        raise RuntimeError("mandoc not found")
    
    result = subprocess.run(
        ['mandoc', '-T', 'markdown', str(man_page_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"mandoc failed: {result.stderr}")
    
    return result.stdout


def groff_to_text(man_page_path: Path) -> str:
    """Convert man page to plain text using groff (fallback)."""
    if not check_groff():
        raise RuntimeError("groff not found. Install with: apt-get install groff")
    
    result = subprocess.run(
        ['groff', '-T', 'utf8', '-man', str(man_page_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"groff failed: {result.stderr}")
    
    return result.stdout


def man_to_text(command: str) -> str:
    """Get man page text for a command using system man."""
    result = subprocess.run(
        ['man', '-P', 'cat', command],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"man failed: {result.stderr}")
    
    return result.stdout


def parse_man_sections(text: str) -> Dict[str, str]:
    """Parse man page text into sections."""
    sections = {}
    current_section = None
    current_content = []
    
    for line in text.split('\n'):
        # Detect section headers (all caps, short)
        stripped = line.strip()
        if stripped and stripped.isupper() and len(stripped) < 40:
            # Likely a section header
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = stripped
            current_content = []
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections


def extract_synopsis(sections: Dict[str, str]) -> str:
    """Extract synopsis from SYNOPSIS section."""
    return sections.get('SYNOPSIS', '').strip()


def extract_description(sections: Dict[str, str]) -> str:
    """Extract description from DESCRIPTION section."""
    return sections.get('DESCRIPTION', '').strip()


def extract_options(sections: Dict[str, str]) -> List[Dict[str, str]]:
    """Extract options from OPTIONS section."""
    options_text = sections.get('OPTIONS', '')
    options = []
    
    # Pattern: -x, --long description
    import re
    option_pattern = re.compile(
        r'^(\s*-\w(?:,\s*--[\w-]+)?|--[\w-]+)\s+(.+)$',
        re.MULTILINE
    )
    
    for match in option_pattern.finditer(options_text):
        flag = match.group(1).strip()
        desc = match.group(2).strip()
        desc = re.sub(r'\s+', ' ', desc)
        options.append({'flag': flag, 'desc': desc})
    
    return options


def extract_examples(sections: Dict[str, str]) -> List[str]:
    """Extract examples from EXAMPLES section."""
    examples_text = sections.get('EXAMPLES', '') or sections.get('EXAMPLE', '')
    examples = []
    
    # Find indented code blocks
    import re
    code_blocks = re.findall(r'^\s{4,}(.+)$', examples_text, re.MULTILINE)
    for code in code_blocks:
        code = code.strip()
        if code:
            examples.append(code)
    
    return examples


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 mandoc_wrapper.py <command> [--format text|html|markdown]")
        sys.exit(1)
    
    command = sys.argv[1]
    format_arg = sys.argv[2] if len(sys.argv) > 2 else 'text'
    
    try:
        if format_arg == 'html':
            output = mandoc_to_html(Path(f"/usr/share/man/man1/{command}.1.gz"))
        elif format_arg == 'markdown':
            output = mandoc_to_markdown(Path(f"/usr/share/man/man1/{command}.1.gz"))
        else:
            output = man_to_text(command)
        print(output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)