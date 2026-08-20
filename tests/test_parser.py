#!/usr/bin/env python3
# test_parser.py - Tests for man page parser

import pytest
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))

from manparser import ManParser, parse_man_text


# Sample man page text for testing
SAMPLE_FIND_MAN = """
FIND(1)                    General Commands Manual                   FIND(1)

NAME
       find - search for files in a directory hierarchy

SYNOPSIS
       find [-H] [-L] [-P] [-D debugopts] [-Olevel] [path...] [expression]

DESCRIPTION
       This manual page documents the GNU version of find.  GNU find searches
       the directory tree rooted at each given file name by evaluating the
       given expression from left to right, according to the rules of precedence
       (see section OPERATORS), until the outcome is known (the left hand side
       is true for and operations, false for or operations), at which point
       find moves on to the next file name.

       If no path is given, the current directory is used.  If no expression
       is given, the expression -print is used.

OPTIONS
       -H, -L, -P
              Control the treatment of symbolic links.

       -D debugopts
              Print diagnostic information.

       -Olevel
              Enables query optimization.

       -name pattern
              Base of file name (the path with the leading directories removed)
              matches shell pattern pattern.

       -type c
              File is of type c:
              b      block (buffered) special
              c      character (unbuffered) special
              d      directory
              p      named pipe (FIFO)
              f      regular file
              l      symbolic link
              s      socket
              D      door (Solaris)

       -mtime n
              File's data was last modified n*24 hours ago.

EXAMPLES
       find /tmp -name core -type f -print
              Print out file names in /tmp whose name is core.

       find /var/log -type f -name '*.log' -mtime -7
              Find all .log files in /var/log modified in the last 7 days.

       find . -type f -exec rm {} \;
              Remove all files in current directory (DANGEROUS).

SEE ALSO
       locate(1), locate(1), xargs(1), chmod(1), findutils(1).
"""

SAMPLE_RM_MAN = """
RM(1)                    General Commands Manual                   RM(1)

NAME
       rm - remove files or directories

SYNOPSIS
       rm [OPTION]... [FILE]...

DESCRIPTION
       This manual page documents the GNU version of rm.  rm removes each
       specified file.  By default, it does not remove directories.

       If the -I or --interactive=once option is given, and there are more
       than three files or the -r, -R, or --recursive option is given, rm
       prompts the user for whether to proceed with the entire operation.

OPTIONS
       -f, --force
              Ignore nonexistent files and arguments, never prompt.

       -i, --interactive
              Prompt before every removal.

       -I
              Prompt once before removing more than three files, or when
              removing recursively.

       -r, -R, --recursive
              Remove directories and their contents recursively.

       -d, --dir
              Remove empty directories.

       -v, --verbose
              Explain what is being done.

EXAMPLES
       rm -i file.txt
              Remove file.txt with confirmation.

       rm -rf /tmp/testdir
              Recursively remove /tmp/testdir and all contents (DANGEROUS).

       rm --dry-run *.tmp
              Show what would be removed without actually removing.
"""


class TestManParser:
    def setup_method(self):
        self.parser = ManParser()

    def test_parse_find(self):
        result = parse_man_text("find", SAMPLE_FIND_MAN)
        
        assert result["name"] == "find"
        assert result["category"] in ["file", "search"]
        assert "search" in result["one_line"].lower() or "find" in result["one_line"].lower()
        assert "find" in result["usage"]
        assert len(result["options"]) > 0
        
        # Check for key options
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-name" in f for f in option_flags)
        assert any("-type" in f for f in option_flags)
        assert any("-mtime" in f for f in option_flags)
        
        # Check examples
        assert len(result["examples"]) > 0
        assert any("core" in ex["code"] for ex in result["examples"])
        
        # Risk level should be low for find
        assert result["risk_level"] == "low"
        
        # Safety note
        assert "LOW RISK" in result["safety"]

    def test_parse_rm(self):
        result = parse_man_text("rm", SAMPLE_RM_MAN)
        
        assert result["name"] == "rm"
        assert result["category"] == "file"
        assert "remove" in result["one_line"].lower()
        assert "rm" in result["usage"]
        
        # Check options
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-f" in f or "--force" in f for f in option_flags)
        assert any("-i" in f or "--interactive" in f for f in option_flags)
        assert any("-r" in f or "-R" in f or "--recursive" in f for f in option_flags)
        
        # Check examples
        assert len(result["examples"]) > 0
        
        # Risk level should be high for rm
        assert result["risk_level"] == "high"
        
        # Safety note should mention HIGH RISK
        assert "HIGH RISK" in result["safety"]

    def test_destructive_example_detection(self):
        result = parse_man_text("find", SAMPLE_FIND_MAN)
        
        # The example with -exec rm should be marked destructive
        destructive_examples = [ex for ex in result["examples"] if ex["destructive"]]
        assert len(destructive_examples) > 0
        assert any("rm" in ex["code"] for ex in destructive_examples)

    def test_category_detection(self):
        # Test various commands
        assert self.parser.detect_category("ls", "list directory contents") == "file"
        assert self.parser.detect_category("grep", "search text") == "text"
        assert self.parser.detect_category("ps", "process status") == "process"
        assert self.parser.detect_category("ssh", "secure shell") == "network"
        assert self.parser.detect_category("apt", "package manager") == "package"
        assert self.parser.detect_category("alias", "shell builtin") == "shell-builtin"

    def test_safety_generation(self):
        # High risk
        safety = self.parser._generate_safety("rm", "high", [])
        assert "HIGH RISK" in safety
        assert "data loss" in safety.lower()
        
        # Medium risk
        safety = self.parser._generate_safety("chmod", "medium", [])
        assert "MEDIUM RISK" in safety
        
        # Low risk
        safety = self.parser._generate_safety("ls", "low", [])
        assert "LOW RISK" in safety

    def test_related_commands(self):
        result = parse_man_text("find", SAMPLE_FIND_MAN)
        # Should find related commands mentioned in text
        assert "locate" in result["related_commands"] or "xargs" in result["related_commands"]


if __name__ == '__main__':
    pytest.main([__file__, "-v"])