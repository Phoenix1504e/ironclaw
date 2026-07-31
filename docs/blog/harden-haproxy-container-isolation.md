---
title: "How to harden a HAProxy container: haproxy:latest scores 59/100 by default"
description: "haproxy:latest defaults score 59/100 (grade C): default capabilities retained, writable rootfs. The exact ironctl scan flags that take a load balancer to its honest 89/100 grade B."
---

# How to harden a HAProxy container (and is haproxy:latest safe at your edge?)

HAProxy sits in the request path: it terminates TLS, load-balances every inbound connection, and is the first thing an attacker reaches. A stock `docker run haproxy:latest` is better than most edge images out of the box because it runs non-root, but it is not yet the boundary that role deserves. Graded on IronClaw's seven-dimension containment scale, the default configuration scores **59 of 100, grade C (weak)**. Higher is safer. A few runtime flags take the same image to **89 of 100, grade B**, and the one dimension it cannot reach (`network=none`) is the one a load balancer needs by definition: it exists to accept and forward traffic. Here are the exact gaps and fixes from the scan data.

> Every number here comes from a read-only `docker inspect` of `docker.io/library/haproxy:latest`, the same data behind its [isolation scorecard](../scores/haproxy.md). No workload is executed. [How scoring works &rarr;](../scan.md)

## Where the default configuration leaks

`ironctl scan` grades seven independent containment boundaries. On a default `docker run haproxy:latest`, two fail and one is unconstrained. It already runs as a non-root user, which is why it starts a full grade above most edge images:

| Dimension | Verdict | Score | What the scan found |
|-----------|:-------:|------:|---------------------|
| Non-root user (uid != 0) | ✅ PASS | 15/15 | runs as haproxy (uid != 0) |
| Dropped capabilities | ❌ FAIL | 4/20 | default capability set retained (CAP_NET_RAW, CAP_MKNOD, and more) |
| Seccomp profile | ✅ PASS | 15/15 | seccomp profile active |
| Network isolation / egress | ❌ UNKNOWN | 0/15 | network mode not reported; assuming egress-capable (fail-closed) |
| Read-only root filesystem | ❌ FAIL | 0/10 | root filesystem is writable |
| No docker.sock exposure | ✅ PASS | 15/15 | no control socket mounted |
| No shared host namespaces | ✅ PASS | 10/10 | no host PID/IPC/network sharing |

HAProxy already gets the hardest dimension right by running as a non-root user (`haproxy`). The two main gaps that remain are the **retained capability set** and the **writable rootfs**. HAProxy parses attacker-controlled bytes on every request; a routing or TLS vulnerability that lands code execution leaves `CAP_NET_RAW` available to craft raw packets and a writable rootfs to persist. Neither is needed to forward traffic.

## Harden it: the exact remediation steps

For `haproxy:latest`:

- **`--cap-drop=ALL --cap-add=NET_BIND_SERVICE`** (Dropped capabilities): drop every Linux capability; retain only `CAP_NET_BIND_SERVICE` if you must bind to privileged ports (< 1024, e.g., 80/443 directly).
- **`--read-only --tmpfs /tmp --tmpfs /var/run`** (Read-only rootfs): make the root filesystem read-only. Mount in-memory filesystems (`tmpfs`) for `/tmp` and `/var/run` so runtime sockets and PID files can be created safely.
- **`--security-opt=no-new-privileges`** (Privilege Escalation): prevent child processes from gaining elevated privileges via `setuid` or `setgid` binaries.

## Before and after

```bash
# Before: 59/100, grade C
docker run -d --name haproxy haproxy:latest

# After: 89/100, grade B
docker run -d --name haproxy-hardened \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --security-opt=no-new-privileges \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  -p 80:80 -p 443:443 \
  haproxy:latest
```

Rescan with `go run ./cmd/ironctl scan haproxy-hardened` to report 89/100 grade B. That is a 30-point swing with no custom image build, just the right runtime flags. The only dimension short of full marks is network egress, because a load balancer exists to accept and proxy connections; `network=none` would score the last 15 points but leave the proxy unable to function.

## Verify it on your own HAProxy

```bash
# install (Homebrew)
brew install ironsecco/ironclaw/ironclaw

# grade your running container, then print the fixes
go run ./cmd/ironctl scan docker.io/library/haproxy:latest
go run ./cmd/ironctl scan docker.io/library/haproxy:latest --fix
```

`ironctl scan` also reads a `docker-compose.yml` service or a Kubernetes manifest, so you can grade
the HAProxy in your stack, not just a bare `docker run`.

## Keep going

- [All hardening guides &rarr;](hardening-guides.md): every harden-a-container walkthrough, with grade deltas.
- [haproxy isolation scorecard &rarr;](../scores/haproxy.md): the full dimension breakdown.
- [How to harden a Traefik container &rarr;](harden-traefik-container-isolation.md): the other popular edge proxy, with the same honest ceiling.
- [Scan any container in 10 seconds &rarr;](../scan.md): the full `ironctl scan` reference.
- [Run untrusted code in a real sandbox &rarr;](../index.md): IronClaw wraps every AI-agent session in a gVisor/Kata boundary with `network=none` by default.
