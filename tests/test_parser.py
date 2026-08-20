#!/usr/bin/env python3
# test_parser.py - Tests for man page parser

import pytest
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.manparser import ManParser, parse_man_text


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
       locate(1), xargs(1), chmod(1), findutils(1).
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

SAMPLE_LS_MAN = """
LS(1)                    General Commands Manual                   LS(1)

NAME
       ls - list directory contents

SYNOPSIS
       ls [OPTION]... [FILE]...

DESCRIPTION
       List information about the FILEs (the current directory by default).
       Sort entries alphabetically if none of -cftuvSUX nor --sort is specified.

OPTIONS
       -a, --all
              do not ignore entries starting with .

       -l
              use a long listing format

       -h, --human-readable
              with -l, print sizes in human readable format (e.g., 1K 234M 2G)

       -r, --reverse
              reverse order while sorting

       -t
              sort by modification time, newest first

EXAMPLES
       ls -la
              List all files in long format

       ls -lh /home
              List /home with human-readable sizes
"""

SAMPLE_GREP_MAN = """
GREP(1)                    General Commands Manual                   GREP(1)

NAME
       grep - print lines matching a pattern

SYNOPSIS
       grep [OPTION]... PATTERNS [FILE]...

DESCRIPTION
       grep searches for PATTERNS in each FILE.  PATTERNS is one or more
       patterns separated by newline characters, and grep prints each line
       that matches a pattern.

OPTIONS
       -i, --ignore-case
              Ignore case distinctions in patterns and input data.

       -r, -R, --recursive
              Read all files under each directory, recursively.

       -v, --invert-match
              Invert the sense of matching, to select non-matching lines.

       -n, --line-number
              Prefix each line of output with the 1-based line number within its input file.

EXAMPLES
       grep -r 'error' /var/log
              Search recursively for 'error' in /var/log

       grep -i 'warning' *.log
              Case-insensitive search for 'warning'
"""

SAMPLE_SED_MAN = """
SED(1)                    General Commands Manual                   SED(1)

NAME
       sed - stream editor for filtering and transforming text

SYNOPSIS
       sed [OPTION]... {script-only-if-no-other-script} [input-file]...

DESCRIPTION
       sed is a stream editor.  It reads input files line by line, applies
       the script, and outputs the result.

OPTIONS
       -n, --quiet, --silent
              Suppress automatic printing of pattern space.

       -e script, --expression=script
              Add the script to the commands to be executed.

       -f script-file, --file=script-file
              Add the contents of script-file to the commands to be executed.

EXAMPLES
       sed 's/foo/bar/g' file.txt
              Replace all 'foo' with 'bar' in file.txt

       sed -n '1,10p' file.txt
              Print lines 1-10
"""

SAMPLE_AWK_MAN = """
AWK(1)                    General Commands Manual                   AWK(1)

NAME
       awk - pattern scanning and processing language

SYNOPSIS
       awk [OPTION]... 'program' [input-file]...

DESCRIPTION
       awk is a programming language for text processing.  It reads input,
       splits into records, and applies the program to each record.

OPTIONS
       -F fs, --field-separator=fs
              Use fs for the input field separator.

       -v var=value
              Assign value to variable var.

EXAMPLES
       awk '{print $1}' file.txt
              Print first column

       awk -F: '{print $1}' /etc/passwd
              Print usernames from /etc/passwd
"""

SAMPLE_TAR_MAN = """
TAR(1)                    General Commands Manual                   TAR(1)

NAME
       tar - an archiving utility

SYNOPSIS
       tar [OPTION]... [FILE]...

DESCRIPTION
       GNU tar saves many files together into a single tape or disk archive,
       and can restore individual files from the archive.

OPTIONS
       -c, --create
              Create a new archive.

       -x, --extract, --get
              Extract files from an archive.

       -f, --file=ARCHIVE
              Use archive file ARCHIVE.

       -z, --gzip
              Filter the archive through gzip.

       -v, --verbose
              Verbosely list files processed.

EXAMPLES
       tar -czf archive.tar.gz /home/user
              Create gzipped archive

       tar -xzf archive.tar.gz
              Extract gzipped archive
"""

SAMPLE_CURL_MAN = """
CURL(1)                    General Commands Manual                   CURL(1)

NAME
       curl - transfer a URL

SYNOPSIS
       curl [OPTION]... [URL]...

DESCRIPTION
       curl is a tool to transfer data from or to a server, using one of the
       supported protocols (HTTP, HTTPS, FTP, FTPS, SCP, SFTP, TFTP,
       DICT, TELNET, LDAP or FILE).

OPTIONS
       -X, --request=COMMAND
              Specify a custom request command to use when communicating with the HTTP server.

       -H, --header=HEADER
              Pass custom header to server.

       -d, --data=DATA
              Send the specified data in a POST request to the HTTP server.

       -o, --output=FILE
              Write output to FILE instead of stdout.

EXAMPLES
       curl -X POST -H 'Content-Type: application/json' -d '{"key":"value"}' https://api.example.com
              POST JSON data

       curl -o file.zip https://example.com/file.zip
              Download file
"""

SAMPLE_CHMOD_MAN = """
CHMOD(1)                    General Commands Manual                   CHMOD(1)

NAME
       chmod - change file mode bits

SYNOPSIS
       chmod [OPTION]... MODE[,MODE]... FILE...

DESCRIPTION
       This manual page documents the GNU version of chmod.  chmod changes
       the file mode bits of each given file according to MODE, which can be
       either a symbolic representation of changes to make, or an octal number
       representing the bit pattern for the new mode bits.

OPTIONS
       -R, --recursive
              Change files and directories recursively.

       -v, --verbose
              Output a diagnostic for every file processed.

       -c, --changes
              Like verbose but report only when a change is made.

EXAMPLES
       chmod 755 script.sh
              Make script executable

       chmod -R 644 /var/www
              Set permissions recursively
"""

SAMPLE_SSH_MAN = """
SSH(1)                    General Commands Manual                   SSH(1)

NAME
       ssh - OpenSSH SSH client (remote login program)

SYNOPSIS
       ssh [OPTION]... [user@]hostname [command]

DESCRIPTION
       ssh (SSH client) is a program for logging into a remote machine and
       for executing commands on a remote machine.

OPTIONS
       -p port
              Port to connect to on the remote host.

       -i identity_file
              Selects a file from which the identity (private key) for public key authentication is read.

       -L local_socket:host:remote_socket
              Specify local port forwarding.

       -R remote_socket:host:local_socket
              Specify remote port forwarding.

EXAMPLES
       ssh user@host
              Connect to remote host

       ssh -i ~/.ssh/id_rsa user@host
              Connect using SSH key
"""

SAMPLE_CAT_MAN = """
CAT(1)                    General Commands Manual                   CAT(1)

NAME
       cat - concatenate files and print on the standard output

SYNOPSIS
       cat [OPTION]... [FILE]...

DESCRIPTION
       Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,
       read standard input.

OPTIONS
       -n, --number
              Number all output lines.

       -b, --number-nonblank
              Number non-empty output lines.

       -s, --squeeze-blank
              Suppress repeated empty output lines.

EXAMPLES
       cat file.txt
              Print file contents

       cat -n file.txt
              Print with line numbers
"""


SAMPLES = {
    "find": SAMPLE_FIND_MAN,
    "rm": SAMPLE_RM_MAN,
    "ls": SAMPLE_LS_MAN,
    "grep": SAMPLE_GREP_MAN,
    "sed": SAMPLE_SED_MAN,
    "awk": SAMPLE_AWK_MAN,
    "tar": SAMPLE_TAR_MAN,
    "curl": SAMPLE_CURL_MAN,
    "chmod": SAMPLE_CHMOD_MAN,
    "ssh": SAMPLE_SSH_MAN,
    "cat": SAMPLE_CAT_MAN,
}


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
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-name" in f for f in option_flags)
        assert any("-type" in f for f in option_flags)
        assert any("-mtime" in f for f in option_flags)
        
        assert len(result["examples"]) > 0
        assert any("core" in ex["code"] for ex in result["examples"])
        
        assert result["risk_level"] == "low"
        assert "LOW RISK" in result["safety"]

    def test_parse_rm(self):
        result = parse_man_text("rm", SAMPLE_RM_MAN)
        
        assert result["name"] == "rm"
        assert result["category"] == "file"
        assert "remove" in result["one_line"].lower()
        assert "rm" in result["usage"]
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-f" in f or "--force" in f for f in option_flags)
        assert any("-i" in f or "--interactive" in f for f in option_flags)
        assert any("-r" in f or "-R" in f or "--recursive" in f for f in option_flags)
        
        assert len(result["examples"]) > 0
        
        assert result["risk_level"] == "high"
        assert "HIGH RISK" in result["safety"]

    def test_parse_ls(self):
        result = parse_man_text("ls", SAMPLE_LS_MAN)
        
        assert result["name"] == "ls"
        assert result["category"] == "file"
        assert "list" in result["one_line"].lower()
        assert "ls" in result["usage"]
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-a" in f or "--all" in f for f in option_flags)
        assert any("-l" in f for f in option_flags)
        assert any("-h" in f or "--human-readable" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_parse_grep(self):
        result = parse_man_text("grep", SAMPLE_GREP_MAN)
        
        assert result["name"] == "grep"
        assert result["category"] == "text"
        assert "grep" in result["usage"]
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-i" in f or "--ignore-case" in f for f in option_flags)
        assert any("-r" in f or "-R" in f or "--recursive" in f for f in option_flags)
        assert any("-v" in f or "--invert-match" in f for f in option_flags)
        assert any("-n" in f or "--line-number" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_parse_sed(self):
        result = parse_man_text("sed", SAMPLE_SED_MAN)
        
        assert result["name"] == "sed"
        assert result["category"] == "text"
        assert "stream editor" in result["one_line"].lower() or "sed" in result["one_line"].lower()
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-n" in f or "--quiet" in f or "--silent" in f for f in option_flags)
        assert any("-e" in f or "--expression" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_parse_awk(self):
        result = parse_man_text("awk", SAMPLE_AWK_MAN)
        
        assert result["name"] == "awk"
        assert result["category"] == "text"
        assert "awk" in result["usage"]
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-F" in f or "--field-separator" in f for f in option_flags)
        assert any("-v" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_parse_tar(self):
        result = parse_man_text("tar", SAMPLE_TAR_MAN)
        
        assert result["name"] == "tar"
        assert result["category"] == "archive"
        assert "archive" in result["one_line"].lower() or "tar" in result["one_line"].lower()
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-c" in f or "--create" in f for f in option_flags)
        assert any("-x" in f or "--extract" in f for f in option_flags)
        assert any("-f" in f or "--file" in f for f in option_flags)
        assert any("-z" in f or "--gzip" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_parse_curl(self):
        result = parse_man_text("curl", SAMPLE_CURL_MAN)
        
        assert result["name"] == "curl"
        assert result["category"] == "network"
        assert "transfer" in result["one_line"].lower() or "curl" in result["one_line"].lower()
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-X" in f or "--request" in f for f in option_flags)
        assert any("-H" in f or "--header" in f for f in option_flags)
        assert any("-d" in f or "--data" in f for f in option_flags)
        assert any("-o" in f or "--output" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_parse_chmod(self):
        result = parse_man_text("chmod", SAMPLE_CHMOD_MAN)
        
        assert result["name"] == "chmod"
        assert result["category"] == "permission"
        assert "mode" in result["one_line"].lower() or "chmod" in result["one_line"].lower()
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-R" in f or "--recursive" in f for f in option_flags)
        assert any("-v" in f or "--verbose" in f for f in option_flags)
        
        # chmod is medium risk
        assert result["risk_level"] == "medium"
        assert "MEDIUM RISK" in result["safety"]

    def test_parse_ssh(self):
        result = parse_man_text("ssh", SAMPLE_SSH_MAN)
        
        assert result["name"] == "ssh"
        assert result["category"] == "network"
        assert "ssh" in result["usage"]
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-p" in f for f in option_flags)
        assert any("-i" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_parse_cat(self):
        result = parse_man_text("cat", SAMPLE_CAT_MAN)
        
        assert result["name"] == "cat"
        assert result["category"] == "file"
        assert "cat" in result["usage"]
        
        option_flags = [o["flag"] for o in result["options"]]
        assert any("-n" in f or "--number" in f for f in option_flags)
        assert any("-b" in f or "--number-nonblank" in f for f in option_flags)
        
        assert result["risk_level"] == "low"

    def test_all_commands(self):
        """Test parsing all sample commands."""
        for name, man_text in SAMPLES.items():
            result = parse_man_text(name, man_text)
            assert result["name"] == name
            assert result["category"] != ""
            assert result["one_line"] != ""
            assert result["usage"] != ""
            assert len(result["options"]) > 0
            assert result["risk_level"] in ["low", "medium", "high"]
            assert result["safety"] != ""

    def test_destructive_example_detection(self):
        result = parse_man_text("find", SAMPLE_FIND_MAN)
        
        destructive_examples = [ex for ex in result["examples"] if ex["destructive"]]
        assert len(destructive_examples) > 0
        assert any("rm" in ex["code"] for ex in destructive_examples)

    def test_category_detection(self):
        assert self.parser.detect_category("ls", "list directory contents") == "file"
        assert self.parser.detect_category("grep", "search text") == "text"
        assert self.parser.detect_category("ps", "process status") == "process"
        assert self.parser.detect_category("ssh", "secure shell") == "network"
        assert self.parser.detect_category("apt", "package manager") == "package"
        assert self.parser.detect_category("alias", "shell builtin") == "shell-builtin"

    def test_safety_generation(self):
        safety = self.parser._generate_safety("rm", "high", [])
        assert "HIGH RISK" in safety
        assert "data loss" in safety.lower()
        
        safety = self.parser._generate_safety("chmod", "medium", [])
        assert "MEDIUM RISK" in safety
        
        safety = self.parser._generate_safety("ls", "low", [])
        assert "LOW RISK" in safety

    def test_related_commands(self):
        result = parse_man_text("find", SAMPLE_FIND_MAN)
        assert "locate" in result["related_commands"] or "xargs" in result["related_commands"]


if __name__ == '__main__':
    pytest.main([__file__, "-v"])