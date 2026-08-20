# Data Sources

## Primary Sources

| Source | URL | Type | Update Frequency |
|--------|-----|------|------------------|
| Local man pages | `man <command>` | System | OS package updates |
| Linux man-pages | https://man7.org/linux/man-pages/ | Web | Monthly |
| GNU Coreutils | https://www.gnu.org/software/coreutils/manual/ | Web | Per release |
| GNU Bash | https://www.gnu.org/software/bash/manual/ | Web | Per release |
| OpenBSD man | https://man.openbsd.org/ | Web | Per release |
| TLDP | https://tldp.org/ | Web | Occasional |

## Verification Rules

1. **Prefer local man pages** — Use `man -P cat <command>` or `mandoc -T utf8` for authoritative version matching installed binaries
2. **Cross-reference** — Compare local vs man7.org vs GNU docs for discrepancies
3. **Version tagging** — Store source version/date in each command JSON (`source_version`, `fetched_at`)
4. **Checksum validation** — SHA256 of raw man page content for change detection

## Fetch Priority

```
Priority 1: Local man pages (man, mandoc)
Priority 2: man7.org (Linux man-pages project)
Priority 3: GNU official documentation
Priority 4: TLDP / distro-specific docs
Priority 5: OpenBSD (for POSIX reference)
```

## Fetch Script Behavior (`fetch_man.sh`)

```bash
# For each command:
1. Try local: man -P cat <cmd> > data/raw/<cmd>.txt
2. If fails: curl man7.org/<cmd>.1.html → extract text
3. If fails: curl gnu.org/software/<pkg>/manual/<cmd>.html
4. Store metadata: source, fetched_at, version, checksum
```

## Update Policy

- **Automated**: Weekly cron job to re-fetch and compare checksums
- **Manual**: `./scripts/fetch_man.sh --force <command>` for specific updates
- **Version pinning**: Lock to specific man-pages release for reproducibility