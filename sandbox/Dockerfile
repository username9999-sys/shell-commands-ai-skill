# Sandbox Dockerfile
# Minimal, secure container for executing shell commands

FROM alpine:3.19

# Install basic utilities for command execution
RUN apk add --no-cache \
    bash \
    coreutils \
    findutils \
    grep \
    sed \
    awk \
    grep \
    sort \
    uniq \
    cut \
    tr \
    wc \
    head \
    tail \
    cat \
    less \
    more \
    xargs \
    which \
    whereis \
    file \
    stat \
    tar \
    gzip \
    gunzip \
    bzip2 \
    xz \
    zip \
    unzip \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN adduser -D -u 1000 -s /bin/bash sandbox

# Workspace directory (writable)
RUN mkdir -p /workspace && chown sandbox:sandbox /workspace

# Switch to non-root user
USER sandbox
WORKDIR /workspace

# Default command
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["echo 'Sandbox ready. Use docker run --rm -v $(pwd):/workspace shell-skill-sandbox \"<command>\"'"]

# Labels
LABEL maintainer="Shell Commands AI Skill"
LABEL description="Secure sandbox for shell command execution"