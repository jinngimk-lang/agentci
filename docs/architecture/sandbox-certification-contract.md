# AgentCI Sandbox Certification Contract

Status: design contract / strategic main line. This document does not claim that all described commands or backends are already implemented.

## Product boundary

AgentCI does not initially replace Firecracker, gVisor, Kata, Docker Sandboxes, Vercel Sandbox, Azure Container Apps Sandboxes, Kubernetes Agent Sandbox, E2B, Daytona, Anthropic Sandbox Runtime, Cloudflare Sandbox, or OS-native sandbox primitives.

AgentCI initially provides a provider-neutral **inspection, policy, adversarial verification, certification, and evidence layer**.

Core statement:

> Sandbox providers build the cage. AgentCI proves the cage actually holds. Then an intelligence layer can learn how the cage should evolve.

## Security invariants

1. **AI is not the enforcement boundary.** AI may interpret evidence and propose policy. Deterministic enforcement mechanisms decide and enforce effective access.
2. **Observation is not authority.** Repository text, web content, package metadata, tool output, MCP content and model output are untrusted observations. They may change a threat model; they may not directly grant authority.
3. **Privilege change is asymmetric.** Safe automatic contraction may be allowed. Expansion requires an external authorized decision path.
4. **Configured is not effective.** A policy file, runtime class, binary name or provider claim is not certification evidence. Effective behavior must be probed where safe.
5. **A backend name is not a verdict.** microVM, container, gVisor, Kata, Landlock, seccomp or AppContainer each describe mechanisms. Certification concerns the whole composed boundary.
6. **Trajectory matters.** Final output alone is insufficient. Attempted forbidden actions, cleanup, propagation, recovery and side effects belong in evidence.
7. **Certification is scoped.** Every verdict binds to an environment fingerprint, backend/version, policy digest, test suite version and explicit limitations.

## Planned CLI surface

These names are the intended contract, not current released behavior:

```text
agentci sandbox inspect <target>
agentci sandbox plan <target>
agentci sandbox test <profile>
agentci sandbox certify <profile>
agentci sandbox replay <incident>
```

Maturity sequence:

```text
inspect → test → certify → replay → adaptive policy
```

Do not implement adaptive permission mutation before inspect/test/certify evidence is credible.

## Sandbox Profile / Policy IR

A provider-neutral Sandbox Profile should represent desired and observed capabilities without requiring one enforcement backend.

Conceptual shape:

```yaml
apiVersion: agentci.dev/sandbox/v0alpha1
kind: SandboxProfile
metadata:
  name: coding-agent-default

backend:
  class: microvm
  provider: example
  version: unknown

workspace:
  mode: clone
  paths:
    - path: /workspace
      read: true
      write: true
    - path: /home
      read: true
      write: false
    - path: /secrets
      read: false
      write: false

network:
  default: deny
  allow:
    - host: pypi.org
      protocols: [https]
  denyPrivateRanges: true
  denyMetadataEndpoints: true
  followRedirectPolicy: revalidate-destination

credentials:
  github:
    mode: brokered
    scopes: [repo:read]

process:
  maxProcesses: 64
  timeoutSeconds: 300
  descendantsMustBeContained: true

resources:
  memoryMiB: 4096
  cpu: 4
  diskMiB: 10240
  stdoutBytes: 10485760
  stderrBytes: 10485760

devices:
  dockerSocket: deny
  kvm: deny

lifecycle:
  persistence: ephemeral
  snapshot: supported
  resumeRequiresPolicyRevalidation: true

authority:
  automaticTightening: true
  automaticExpansion: false
```

The real schema will evolve from experiments. Do not treat this example as a released stable API.

## Capability states

For each capability distinguish:

```text
declared
configured
probed
verified
failed
unverified
not-applicable
```

This extends AgentCI's existing readiness discipline. `configured` never implies `verified`.

## Authority classes

### Trusted policy inputs

Examples:
- owner/Supervisor policy;
- signed organization policy;
- immutable environment baseline;
- explicitly approved capability grants;
- backend/version facts from trusted discovery;
- test/certification rules.

### Untrusted observations

Examples:
- README/repository instructions;
- source comments;
- package metadata/install scripts;
- web pages;
- issue/PR text;
- MCP descriptions and tool results;
- model output;
- generated code;
- sandbox workload output.

Untrusted observations may create a **proposal** or **risk signal**. They may not cross the authority boundary by themselves.

## Privilege delta rule

Candidate automatic changes that may be permitted after deterministic validation:

```text
RW → RO
ALLOW → DENY
broad network → allowlist
raw secret → brokered credential
durable → ephemeral
larger limit → smaller limit
```

Changes that require external authorized approval:

```text
RO → RW
DENY → ALLOW
no network → network
allowlist → arbitrary internet
no credential → credential
brokered credential → raw secret
workspace-only → host access
no device → docker.sock / privileged device
container → host namespace sharing
```

An LLM cannot be the only approver of a privilege-expanding delta that benefits its own task completion.

## Certification dimensions

### Filesystem
- workspace write scope;
- read scope;
- sensitive path denial;
- traversal/symlink/hardlink/mount behavior;
- host coupling;
- temporary directories;
- cross-session residue.

### Network
- default posture;
- DNS resolution;
- domain/IP/protocol controls;
- redirect revalidation;
- private/link-local/cloud metadata ranges;
- IPv4/IPv6 parity;
- raw TCP/UDP/ICMP where applicable;
- proxy bypass/tunnelling;
- Unix sockets;
- ingress/public tunnels.

### Credentials
- raw env/file exposure;
- credential helpers;
- brokered transformation;
- scope/expiry;
- child-process inheritance;
- snapshot/restoration behavior;
- revocation.

### Process and resources
- process tree containment;
- orphan/daemon survival;
- PID/fork limits;
- CPU/memory/disk constraints;
- stdin blocking;
- stdout/stderr flooding;
- wall-clock deadlines;
- cleanup determinism.

### Devices and host interfaces
- `docker.sock`;
- container runtime sockets;
- `/dev/kvm`;
- host namespaces;
- privileged mounts;
- kernel/debug interfaces.

### Lifecycle and state
- create/delete;
- pause/resume;
- snapshot/restore;
- policy revalidation after restore;
- stale credential invalidation;
- tenant cleanup;
- pooled instance reuse.

### Control plane
- sandbox API authentication/authorization;
- MCP/REST capability boundaries;
- template/blueprint mutation;
- policy source/digest;
- audit trail;
- separation between sandbox workload and control-plane authority.

## Attack taxonomy

Agent B should maintain reusable attack families rather than provider-specific one-off scripts:

1. filesystem escape and sensitive-read attacks;
2. network bypass and indirect-egress attacks;
3. credential exfiltration and scope-confusion attacks;
4. process/resource exhaustion and cleanup attacks;
5. host-socket/device/namespace attacks;
6. snapshot/persistence/cross-tenant residue attacks;
7. policy mutation and authority-confusion attacks;
8. prompt-induced privilege-expansion attacks;
9. control-plane/MCP/API authentication attacks;
10. configuration-vs-effective-behavior mismatch;
11. provider fallback/degraded-mode mismatch;
12. trajectory/propagation/recovery failures.

## Crisis contract

Future adaptive runtime work may use:

```text
NORMAL
→ SUSPICIOUS
→ RESTRICTED
→ QUARANTINED
→ TERMINATED
```

A deterministic crisis path may:
- deny new egress;
- revoke brokered credentials;
- stop/freeze a process tree where the backend supports it;
- preserve logs/trajectory/artifacts;
- capture a snapshot when safe and supported;
- clone evidence into a forensic environment;
- terminate the original workload according to policy.

The intelligence layer may analyze the incident after containment. It does not delay an emergency deny action while it reasons.

## Certification evidence envelope

Every certification should eventually preserve at least:

```json
{
  "profile_version": "...",
  "environment_fingerprint": "...",
  "backend": {"provider": "...", "class": "...", "version": "..."},
  "policy_digest": "sha256:...",
  "test_suite_version": "...",
  "started_at": "...",
  "finished_at": "...",
  "checks": [],
  "trajectory_artifact": "...",
  "limitations": [],
  "verdict": "PASS|FAIL|PARTIAL|UNVERIFIED"
}
```

A `PASS` must never silently include untested material capabilities. Untested capabilities are `UNVERIFIED` or explicit limitations.

## Phase plan

### S0 — Landscape + Contract
- map real providers/primitives/benchmarks;
- finalize v0alpha1 capability vocabulary;
- define attack taxonomy;
- select reference targets.

Exit evidence:
- >= 6 relevant upstream systems studied from primary sources;
- >= 3 isolation classes represented;
- provider-neutral contract reviewed by B on Spec and Standards.

### S1 — Read-only inspection + reference certification
- implement environment/profile parsing;
- implement safe read-only probes;
- certify 2–3 real targets or deliberately isolated reference environments;
- produce deterministic JSON evidence.

Exit evidence:
- same generic checks run against multiple backends;
- at least one meaningful difference/mismatch is surfaced;
- no need for privileged/destructive escape payloads in normal CI.

### S2 — Provider adapters / Policy IR
- backend adapters translate provider facts/config into common IR;
- add conformance checks for filesystem/network/process/credential/lifecycle;
- optional compiler experiments only after semantics are stable.

### S3 — Runtime drift + automatic tightening
- detect capability/environment drift;
- generate proposed policy deltas;
- deterministic validator;
- only safe contraction may be auto-applied;
- B attacks authority confusion and prompt injection.

### S4 — Crisis + Incident Memory / Sandbox Genome
- replay incidents;
- preserve learned patterns with evidence/provenance;
- adapt recommended profiles by environment class;
- never learn privilege expansions as automatic authority.

## Initial reference-target selection criteria

Prefer targets that together cover different isolation classes and can be tested reproducibly without unsafe infrastructure:

- one OS-native sandbox (e.g. Anthropic Sandbox Runtime / bubblewrap or equivalent);
- one container/application-kernel or Kubernetes sandbox;
- one microVM/provider sandbox when accessible;
- optionally one provider-independent runtime interface such as SWE-ReX for adapter research.

Do not require paid cloud credentials to prove the first contract. Cloud targets can remain external benchmarks until access exists.

## Success condition

Sandbox Certification becomes a core AgentCI capability only when evidence shows AgentCI can discover or reproduce security/reliability differences across real sandbox environments that their configuration/unit tests alone do not make obvious.
