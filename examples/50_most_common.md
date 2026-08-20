# 50 Most Common Unix/Linux Commands

Reference list for seed dataset prioritization.

## File Operations
1. **ls** - List directory contents
2. **cd** - Change directory
3. **pwd** - Print working directory
4. **cp** - Copy files/directories
5. **mv** - Move/rename files
6. **rm** - Remove files (HIGH RISK)
7. **mkdir** - Create directories
8. **rmdir** - Remove empty directories
9. **touch** - Create empty files / update timestamps
10. **cat** - Concatenate and display files
11. **head** - Display first lines
12. **tail** - Display last lines
13. **less** - Pager for viewing files
14. **more** - Pager (older)
15. **find** - Search for files
16. **locate** - Find files by name (database)
17. **which** - Locate command binary
18. **whereis** - Locate binary/source/man
18. **file** - Determine file type
19. **stat** - Display file status
20. **ln** - Create links

## Text Processing
21. **grep** - Pattern search
22. **egrep** - Extended grep
23. **fgrep** - Fixed string grep
24. **sed** - Stream editor
25. **awk** - Text processing language
26. **sort** - Sort lines
26. **uniq** - Remove duplicate lines
27. **cut** - Remove sections from lines
28. **tr** - Translate/delete characters
29. **wc** - Word/line/character count
30. **fmt** - Format text
31. **fold** - Wrap lines
32. **join** - Join lines on common field
33. **paste** - Merge lines

## System Information
34. **ps** - Process status
35. **top** - Process monitor
36. **htop** - Interactive process viewer
37. **kill** - Send signal to process
38. **jobs** - List background jobs
39. **bg** - Resume job in background
40. **fg** - Bring job to foreground
41. **nohup** - Run immune to hangups
42. **df** - Disk space usage
43. **du** - Directory space usage
44. **free** - Memory usage
45. **uptime** - System uptime
46. **whoami** - Current user
47. **id** - User/group IDs
48. **date** - Date/time
49. **cal** - Calendar
50. **uptime** - System uptime

## Archive & Compression
- **tar** - Tape archive
- **gzip/gunzip** - GNU zip
- **bzip2/bunzip2** - Bzip2 compress
- **xz/unxz** - XZ compress
- **zip/unzip** - ZIP archives

## Network
- **ssh** - Secure shell
- **scp** - Secure copy
- **rsync** - Remote sync
- **curl** - Transfer data
- **wget** - Web get
- **ping** - Network connectivity
- **traceroute** - Trace route
- **dig/nslookup** - DNS lookup

## Package Management (distro-specific)
- **apt/apt-get** - Debian/Ubuntu
- **yum/dnf** - RHEL/Fedora
- **pacman** - Arch
- **zypper** - openSUSE
- **brew** - macOS

## Shell Builtins
- **alias/unalias** - Command aliases
- **export** - Environment variables
- **set/unset** - Shell options
- **declare/local** - Variable attributes
- **history** - Command history
- **type** - Command type
- **command** - Run without alias
- **builtin** - Run shell builtin
- **eval** - Evaluate arguments
- **exec** - Replace shell

## Permissions & Ownership
- **chmod** - Change permissions
- **chown** - Change owner
- **chgrp** - Change group
- **umask** - Default permissions
- **getfacl/setfacl** - ACLs

## Process Control
- **&** - Background
- **Ctrl+Z** - Suspend
- **jobs** - List jobs
- **bg/fg** - Background/foreground
- **kill/killall** - Terminate
- **wait** - Wait for jobs
- **disown** - Remove from job table

## Redirection & Pipes
- **>** - Stdout redirect
- **>>** - Append redirect
- **<** - Stdin redirect
- **2>** - Stderr redirect
- **|** - Pipe
- **tee** - Split output
- **xargs** - Build commands from stdin

## Safety Notes
Commands marked **HIGH RISK** in this skill:
- `rm -rf` (recursive force delete)
- `dd` (disk destroyer)
- `mkfs.*` (format filesystem)
- `fdisk/parted` (partition manipulation)
- `chmod 777 /` (permission destruction)
- `curl | sh` (remote code execution)

Always use `--dry-run` or `-i` (interactive) when available.