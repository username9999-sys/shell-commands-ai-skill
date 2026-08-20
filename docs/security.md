# Security Policy

## Blacklisted Commands (Never Execute)

The following commands/patterns are **blacklisted** and must never be executed, even in sandbox:

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | System destruction |
| `rm -rf /*` | System destruction |
| `dd if=/dev/zero of=/dev/sd*` | Disk destruction |
| `dd if=/dev/random of=/dev/sd*` | Disk destruction |
| `mkfs.*` | Filesystem destruction |
| `fdisk /dev/sd*` | Partition table destruction |
| `parted /dev/sd*` | Partition destruction |
| `iptables -F` / `iptables -X` | Firewall rule deletion |
| `ufw disable` | Firewall disable |
| `systemctl stop` / `systemctl disable` (critical services) | Service disruption |
| `curl \| sh` / `wget \| sh` / `curl \| bash` | Remote code execution |
| `bash -c "$(curl ...)"` | Remote code execution |
| `chmod 777 /` | Permission escalation |
| `chown -R root:root /` | Ownership destruction |
| `mv / /dev/null` | Filesystem destruction |
| `:(){ :\|:& };:` | Fork bomb |
| `dd if=/dev/urandom of=/dev/mem` | Memory corruption |
| `echo 1 > /proc/sys/kernel/panic` | Kernel panic |

## Sandbox Policies

### Container Configuration
```dockerfile
# Base: alpine:latest or gcr.io/distroless/base
# User: non-root (uid=1000)
# Capabilities: DROP ALL
# Security: seccomp profile, AppArmor
# Network: NONE (--network=none)
# Filesystem: read-only root, tmpfs for /tmp
# Resources: --cpus=0.5 --memory=128m --pids-limit=50
# Timeout: --timeout=30s
```

### Execution Rules
1. **No network access** — All containers run with `--network=none`
2. **Read-only root filesystem** — Only `/tmp` and `/workspace` writable
3. **Resource limits** — CPU 0.5 cores, RAM 128MB, 50 pids max
4. **Timeout** — Hard 30 second timeout per execution
5. **No privilege escalation** -- `--security-opt=no-new-privileges:true`
6. **Seccomp profile** — Block dangerous syscalls (ptrace, process_vm_writev, etc.)

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `GET /command/{name}` | 60 req/min per IP |
| `POST /search` | 30 req/min per IP |
| `POST /explain` | 20 req/min per IP |
| `GET /commands` | 100 req/min per IP |
| Sandbox execution | 5 req/min per IP |

## Logging Requirements

All API requests must log:
- Timestamp (ISO8601)
- Client IP (hashed)
- Endpoint + method
- Response status + latency
- User agent (truncated)

Sandbox executions must additionally log:
- Command executed
- Exit code
- Stdout/stderr (truncated to 1KB)
- Resource usage (CPU, memory, time)
- Security violations (if any)

## Data Handling

- **No PII stored** — No user accounts, no personal data
- **Query logs** — Retained 30 days, then aggregated/anonymized
- **Sandbox output** — Not persisted beyond request lifecycle
- **Source attribution** — All command data includes source URL

## Incident Response

1. Detect: Anomalous sandbox behavior (resource spike, forbidden syscall)
2. Isolate: Kill container, block IP temporarily
3. Analyze: Review logs, determine if attack or bug
4. Remediate: Update seccomp profile, adjust limits, patch
5. Document: Record in security log with timestamp