# Approximate "bash-only" challenge container (POC).
#
# This is NOT a byte-for-byte reproduction of the proposal's sandbox: Landlock
# and rootless Docker are Linux-only and can't run natively on macOS. We
# approximate the *tool level* (bash + the allowed hex/text tools, no network,
# no python, no compilers) with a minimal image, and the runner adds the
# isolation flags (--network none, --cap-drop ALL, mem/cpu caps). Containers run
# inside Docker's Linux VM, so escape attempts stay off the host.
FROM debian:stable-slim

# bash-only level: shell + coreutils + hex/text tools. Deliberately NO python,
# NO compilers, NO network tools (curl/wget/nc) — so "bash-only" is real.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash coreutils xxd file gawk sed grep \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /work
WORKDIR /work

# Kept alive by the runner; the agent's commands arrive via `docker exec`.
CMD ["sleep", "infinity"]
