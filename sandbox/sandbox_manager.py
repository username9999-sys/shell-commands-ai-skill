#!/usr/bin/env python3
# sandbox_manager.py - Programmatic sandbox execution manager

import subprocess
import json
import tempfile
import os
import shlex
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timeout: bool = False
    error: Optional[str] = None


class SandboxManager:
    """Manages secure sandbox execution of shell commands."""
    
    BLACKLIST_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'dd\s+if=/dev/(zero|random)\s+of=/dev/sd',
        r'mkfs\.',
        r'fdisk\s+/dev/sd',
        r'parted\s+/dev/sd',
        r'iptables\s+(-F|-X)',
        r'ufw\s+disable',
        r'curl\s+\|\s*(sh|bash)',
        r'wget\s+\|\s*(sh|bash)',
        r'bash\s+-c\s+\$\\(curl',
        r'chmod\s+777\s+/',
        r'chown\s+-R\s+root:root\s+/',
        r'mv\s+/\s+/dev/null',
        r':\(\)\{\s*:\|:&\s*\};:',
    ]
    
    def __init__(self, image_name: str = "shell-skill-sandbox"):
        self.image_name = image_name
        self._ensure_image()
    
    def _ensure_image(self):
        """Build sandbox image if it doesn't exist."""
        try:
            subprocess.run(
                ["docker", "image", "inspect", self.image_name],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            print(f"Building sandbox image: {self.image_name}")
            dockerfile_dir = Path(__file__).parent
            subprocess.run(
                ["docker", "build", "-t", self.image_name, str(dockerfile_dir)],
                check=True
            )
    
    def _validate_command(self, command: str) -> Optional[str]:
        """Check command against blacklist patterns."""
        import re
        for pattern in self.BLACKLIST_PATTERNS:
            if re.search(pattern, command):
                return f"Command matches blacklist pattern: {pattern}"
        return None
    
    def execute(
        self,
        command: str,
        args: List[str] = None,
        timeout: int = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        readonly_mounts: Optional[List[str]] = None,
        writable_mounts: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """
        Execute a command in the sandbox.
        
        Args:
            command: Command to execute (e.g., "find")
            args: List of arguments (e.g., ["/var/log", "-name", "*.log"])
            timeout: Execution timeout in seconds
            cwd: Working directory (mounted read-only)
            env: Environment variables
            readonly_mounts: Host paths to mount read-only
            writable_mounts: Dict of host_path -> container_path for writable mounts
        """
        # Build full command string for validation
        full_cmd = " ".join([command] + (args or []))
        
        # Validate against blacklist
        blacklist_error = self._validate_command(full_cmd)
        if blacklist_error:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr="",
                error=blacklist_error
            )
        
        # Build docker run command
        docker_cmd = [
            "docker", "run", "--rm",
            "--network=none",
            "--cpus=0.5",
            "--memory=128m",
            "--pids-limit=50",
            "--security-opt=no-new-privileges:true",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=50m",
            "--tmpfs", "/workspace:rw,noexec,nosuid,size=100m",
            "-u", "1000:1000",
            "--cap-drop=ALL",
        ]
        
        # Add read-only mounts
        if readonly_mounts:
            for mount in readonly_mounts:
                docker_cmd.extend(["-v", f"{mount}:/mnt/{os.path.basename(mount)}:ro"])
        
        # Add writable mounts
        if writable_mounts:
            for host_path, container_path in writable_mounts.items():
                docker_cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        # Add current directory as read-only mount if cwd specified
        if cwd:
            docker_cmd.extend(["-v", f"{os.path.abspath(cwd)}:/workspace:ro"])
        
        # Add environment variables
        if env:
            for k, v in env.items():
                docker_cmd.extend(["-e", f"{k}={v}"])
        
        # Image and command
        docker_cmd.append(self.image_name)
        docker_cmd.append("bash")
        docker_cmd.append("-c")
        docker_cmd.append(full_cmd)
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return SandboxResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr="",
                timeout=True,
                error=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr="",
                error=str(e)
            )
    
    def execute_safe(self, command: str, **kwargs) -> SandboxResult:
        """
        Execute with additional safety checks - only allows whitelisted commands.
        """
        # Whitelist of safe commands for unrestricted use
        SAFE_COMMANDS = {
            'ls', 'cat', 'head', 'tail', 'less', 'more',
            'grep', 'egrep', 'fgrep', 'rg', 'ag',
            'find', 'locate', 'which', 'whereis', 'type',
            'head', 'tail', 'wc', 'sort', 'uniq', 'cut',
            'tr', 'sed', 'awk', 'date', 'cal', 'bc',
            'factor', 'seq', 'yes', 'tee', 'script',
            'time', 'timeout', 'env', 'printenv',
            'who', 'whoami', 'id', 'groups', 'pwd',
            'df', 'du', 'free', 'uptime', 'stat',
            'file', 'tar', 'gzip', 'gunzip', 'bzip2',
            'xz', 'zip', 'unzip', 'ssh', 'scp', 'rsync',
        }
        
        if command not in SAFE_COMMANDS:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr="",
                error=f"Command '{command}' not in safe whitelist. Use execute() with explicit validation instead."
            )
        
        return self.execute(command, **kwargs)


def run_in_sandbox(
    command: str,
    args: List[str] = None,
    timeout: int = 30,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function for simple sandbox execution.
    Returns dict with result.
    """
    manager = SandboxManager()
    result = manager.execute(command, args, timeout, cwd)
    return {
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timeout": result.timeout,
        "error": result.error
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 sandbox_manager.py <command> [args...]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    manager = SandboxManager()
    result = manager.execute(cmd, args)
    
    print(json.dumps({
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timeout": result.timeout,
        "error": result.error
    }, indent=2))