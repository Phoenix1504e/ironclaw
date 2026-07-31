---
title: "haproxy:latest container isolation score: 59/100 (grade C)"
description: "How isolated is haproxy:latest by default? IronClaw scores its sandbox posture 59/100 (C): retains default capabilities and writable rootfs. Scan any container in 10s."
---

# haproxy:latest container isolation score: 59/100 (grade C)

Run with plain `docker run haproxy:latest` defaults, no hardening flags, the **HAProxy** image scores **59/100, grade C (weak, fix the FAILs)** on IronClaw's seven-dimension container containment scale. Higher is safer. This is what you get straight out of a copy-pasted `docker run`; the fixes below close the gap.

> Graded from a read-only `docker inspect` of `docker.io/library/haproxy:latest`. No workload is executed. [How scoring works &rarr;](../scan.md)

## How it scores, dimension by dimension

| Dimension | Verdict | Score | What the scan found |
|-----------|:-------:|------:|---------------------|
| Non-root user (uid != 0) | ✅ PASS | 15/15 | runs as haproxy (uid != 0) |
| Dropped capabilities | ❌ FAIL | 4/20 | default capability set retained (includes CAP_NET_RAW, CAP_MKNOD, …) |
| Seccomp profile | ✅ PASS | 15/15 | seccomp profile active (syscall surface filtered) |
| Network isolation / egress | ❌ UNKNOWN | 0/15 | network mode not reported; assuming egress-capable (fail-closed) |
| Read-only root filesystem | ❌ FAIL | 0/10 | root filesystem is writable: tamper/persistence surface |
| No docker.sock exposure | ✅ PASS | 15/15 | no docker.sock / OCI control socket mounted |
| No shared host namespaces | ✅ PASS | 10/10 | no host PID/IPC/network namespace sharing |

## Harden it: the highest-value fixes

Applying these to your `docker run haproxy` closes the biggest gaps first (most points recovered first):

- **Dropped capabilities**, `--cap-drop=ALL --cap-add=NET_BIND_SERVICE`  
  Drop every Linux capability; add back only `NET_BIND_SERVICE` if binding ports < 1024 (e.g., 80/443).
- **Read-only root filesystem**, `--read-only --tmpfs /tmp --tmpfs /var/run`  
  Make the root filesystem read-only to remove the tamper/persistence surface.

A fully hardened run scores **89/100 (grade B)** (network proxy functionality requires active network access):

```bash
docker run -d --name haproxy-hardened \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --security-opt=no-new-privileges \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  haproxy:latest
```

## Scan your own container

These grades come from `ironctl scan`, a single, credential-free command that audits any running container, docker-compose service, or Kubernetes manifest, not just this image:

```bash
# install (Homebrew)
brew install ironsecco/ironclaw/ironclaw

# grade your own haproxy the same way this page was generated
go run ./cmd/ironctl scan docker.io/library/haproxy:latest
```

- [Scan any container &rarr;](../scan.md), the full command reference.
- [Add an isolation-score badge to your repo &rarr;](../blog/add-a-sandbox-isolation-score-badge-to-your-repo.md)
- [The State of Container Isolation, 2026 &rarr;](../blog/state-of-container-isolation-2026.md), the full survey this directory is built from.
- [Run untrusted code in a real sandbox &rarr;](../index.md), IronClaw wraps every AI-agent session in a gVisor/Kata isolation boundary with `network=none` by default.

## Badge this image

Maintain **haproxy** (or run it)? Show its default-config isolation score with a badge that links back to this scorecard:

[![Container Isolation Score: 59/100 C](https://img.shields.io/badge/container%20isolation-59%2F100%20C-yellow)](https://ironsecco.github.io/ironclaw/scores/haproxy/)

```markdown
[![Container Isolation Score: 59/100 C](https://img.shields.io/badge/container%20isolation-59%2F100%20C-yellow)](https://ironsecco.github.io/ironclaw/scores/haproxy/)
```

The badge is a plain [shields.io](https://shields.io) URL: no server, no build step, nothing to host. It reflects this page's default-configuration grade. Hardened your own deployment? Generate a live badge of *your* config with [`ironctl scan --badge-json`](../blog/add-a-sandbox-isolation-score-badge-to-your-repo.md), or compare every image on the [leaderboard](leaderboard.md).

---

*Part of the [Container Isolation Scores](index.md) directory, default-configuration containment grades for the most-pulled public images.*
