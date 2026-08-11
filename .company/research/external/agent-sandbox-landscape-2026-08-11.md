# Agent Sandbox Landscape — 2026-08-11

Status: active strategic research
Owner direction: Agent Sandbox / intelligent sandbox is now the primary product-research line.

## Executive conclusion

Agent sandbox infrastructure is converging around a layered model rather than a single `sandbox=true` primitive:

1. an isolation substrate (microVM, application kernel, OS sandbox, container, WASM, etc.);
2. filesystem and process boundaries;
3. network egress controls;
4. credential brokering or secret separation;
5. lifecycle/state management;
6. observability and evidence;
7. an authorization/policy layer above enforcement.

The strongest opportunity for AgentCI is **not** to immediately become another sandbox runtime provider. The initial product wedge is:

> AgentCI verifies whether an agent sandbox actually contains the agent, preserves the intended authority boundary, and produces reproducible certification evidence.

Longer term, an intelligence layer may inspect an environment, propose a minimum-capability policy, detect drift, recommend tighter policy, and learn from incidents. The intelligence layer must never itself be the final security boundary.

Core invariant:

> Observation may change understanding, but observation does not change authority. AI may propose policy; deterministic mechanisms enforce it. Privilege may contract automatically; privilege expansion requires external authority.

## Landscape map

### Kubernetes SIG Apps Agent Sandbox

Source: https://github.com/kubernetes-sigs/agent-sandbox

Why it matters:
- defines a first-class Kubernetes `Sandbox` abstraction for isolated, stateful singleton workloads including AI agent runtimes;
- introduces stable lifecycle/state concepts instead of treating sandboxes as disposable command containers only;
- recent v0.5.x work graduates APIs to v1beta1 and develops a standardized sandbox runtime interface;
- supports extension/runtime patterns that can sit above gVisor/Kata-style isolation.

AgentCI lesson:
- separate the **Sandbox Contract** from the backend implementation;
- certify lifecycle, claim/template semantics, runtime identity and actual containment separately.

Classification: `benchmark + design-source`

### Anthropic Sandbox Runtime

Sources:
- https://github.com/anthropic-experimental/sandbox-runtime
- https://www.anthropic.com/engineering/claude-code-sandboxing

Why it matters:
- lightweight OS-native sandbox for arbitrary processes, agents and MCP servers;
- Linux uses bubblewrap/network namespaces; macOS uses Seatbelt/sandbox-exec;
- combines filesystem and network isolation;
- network filtering is proxy-mediated and can request explicit expansion;
- explicitly designed to reduce permission-prompt fatigue while maintaining boundaries.

AgentCI lesson:
- filesystem and network restrictions must be certified together;
- subprocess/process-tree inheritance must be tested;
- permission requests are a separate authority channel, not proof of containment;
- proxy/TLS/redirect behavior is a first-class attack surface.

Classification: `benchmark + experiment`

### Docker Sandboxes

Sources:
- https://docs.docker.com/ai/sandboxes/
- https://docs.docker.com/ai/sandboxes/security/isolation/
- https://docs.docker.com/ai/sandboxes/architecture/

Why it matters:
- agent-oriented microVM architecture;
- separate Docker daemon inside the sandbox rather than exposing host `docker.sock`;
- layered filesystem/network/workspace/credential controls;
- credential proxy and network policy are separate from the VM boundary.

AgentCI lesson:
- microVM alone does not prove a complete sandbox;
- workspace mode (direct mount vs private clone) changes the real security contract;
- host Docker socket and shared skill/config locations are trust-boundary tests;
- certification must state which layers were verified.

Classification: `benchmark + experiment`

### Vercel Sandbox

Sources:
- https://vercel.com/docs/vercel-sandbox
- https://vercel.com/kb/guide/running-opencode-securely-with-the-vercel-sandbox

Why it matters:
- Firecracker-based ephemeral execution;
- configurable network policies and domain allowlists;
- snapshots and SDK-driven lifecycle;
- patterns for credential brokering/separation and agent-code execution.

AgentCI lesson:
- distinguish harness identity/credentials from generated-code identity;
- verify configured egress policy with runtime probes;
- backend readiness is not containment evidence.

Classification: `benchmark`

### Azure Container Apps Sandboxes

Sources:
- https://learn.microsoft.com/azure/container-apps/sandboxes-overview
- https://learn.microsoft.com/azure/container-apps/sandboxes-snapshots-state-management

Why it matters:
- first-class sandbox resource for agent workflows;
- isolated lightweight VM boundary;
- full memory/disk snapshot, suspend/resume, lifecycle and stateful agent workloads;
- networking and storage are part of the programmable sandbox contract.

AgentCI lesson:
- lifecycle/snapshot semantics belong in certification;
- snapshots create replay/forensics opportunities and stale-secret/stale-policy risks;
- a sandbox can be secure at launch but unsafe after resume/restore.

Classification: `benchmark + future incident-replay target`

### Agent-Sandbox (self-hosted Kubernetes runtime)

Source: https://github.com/agent-sandbox/agent-sandbox

Why it matters:
- REST/MCP-facing self-hosted sandbox runtime on Kubernetes;
- E2B protocol/SDK compatibility;
- code/browser/computer/shell workloads;
- pools, pause/resume, snapshots, scale-to-zero, metrics.

AgentCI lesson:
- E2B-compatible APIs are a useful interoperability target;
- MCP/REST control-plane authority must be certified separately from workload containment;
- multi-tenant and pooled reuse require cross-tenant residue tests.

Classification: `experiment + interoperability target`

### E2B

Source: https://e2b.dev/

Why it matters:
- widely used agent code-execution sandbox API pattern;
- stateful session and code-interpreter usage makes it a useful ecosystem compatibility target.

AgentCI lesson:
- treat as a provider target, not as a security oracle;
- verify actual backend behavior and configuration rather than assuming guarantees from API compatibility.

Classification: `benchmark + ecosystem target`

### Daytona

Source: https://www.daytona.io/

Why it matters:
- agent-oriented sandbox/runtime APIs across multiple execution classes;
- state/snapshot and remote development patterns;
- integrations with agent frameworks.

AgentCI lesson:
- certification schema must support heterogeneous runtime classes and persistent sessions.

Classification: `benchmark`

### Cloudflare Sandbox SDK

Source: https://github.com/cloudflare/sandbox-sdk

Why it matters:
- isolated container execution behind Workers/Durable Objects;
- command/files/background services/public tunnels;
- AI-agent examples including OpenAI Agents and Claude Code.

AgentCI lesson:
- exposing sandbox services/tunnels expands the containment surface;
- ingress capability is as important as egress capability;
- provider-specific control-plane and runtime isolation should be separate evidence categories.

Classification: `benchmark + attack-surface source`

### SWE-ReX

Source: https://github.com/SWE-agent/SWE-ReX

Why it matters:
- provider-independent runtime interface over local, Docker, AWS, Modal and other environments;
- deliberately separates agent logic from execution infrastructure;
- interactive and parallel shell sessions.

AgentCI lesson:
- execution abstraction is becoming standardized, but security certification remains fragmented;
- AgentCI can sit above runtime interfaces and certify what the environment actually allows.

Classification: `design-source + integration candidate`

## Isolation/enforcement primitives to study

### Firecracker
Source: https://github.com/firecracker-microvm/firecracker

Lesson: hardware microVM isolation is a substrate, not a complete sandbox. Network filtering, credentials, workspace sharing, lifecycle and policy still require external controls.

### gVisor
Source: https://gvisor.dev/

Lesson: application-kernel isolation provides a different security/performance profile than containers or VMs. Certification must test observable guarantees, not infer safety from backend names.

### Kata Containers
Source: https://katacontainers.io/

Lesson: VM-backed container architecture adds a second isolation layer; resource enforcement may exist at multiple layers and should be explicitly located in the contract.

### Landlock
Source: https://docs.kernel.org/userspace-api/landlock.html

Lesson: unprivileged processes can add restrictions that are inherited; restrictions cannot be used to restore ambient rights. Strong fit for the invariant that autonomous adaptation may tighten but not self-escalate.

### seccomp / namespaces / cgroups

Lesson: syscall, namespace and resource controls remain foundational Linux layers. Their presence must be probed and their policy must be bound to the tested process tree.

### Tetragon / eBPF runtime enforcement
Source: https://tetragon.io/docs/getting-started/enforcement/

Lesson: kernel-level observation and runtime enforcement can provide crisis-mode evidence and emergency actions. Signal-only termination and operation-overriding semantics must be distinguished.

### OPA / Cedar
Sources:
- https://www.openpolicyagent.org/docs
- https://www.cedarpolicy.com/

Lesson: useful models for separating policy decisions from enforcement. They are candidates for policy decision/validation, not sandbox boundaries themselves.

### Windows sandbox primitives
Source: https://learn.microsoft.com/windows/win32/secauthz/createprocessinsandbox

Lesson: Policy IR must remain cross-platform. Do not design AgentCI Sandbox as Linux-only.

## Benchmark and research signals

### SANDBOXESCAPEBENCH
Source: https://arxiv.org/abs/2603.02277

Why it matters:
- directly evaluates LLM ability to exploit sandbox misconfiguration/runtime/orchestration weaknesses;
- nested sandbox architecture provides a safe benchmark pattern;
- validates that adversarial agents can find intentionally introduced escapes.

AgentCI action:
- map its attack classes into the Sandbox Certification test taxonomy;
- do not copy exploit payloads into ordinary CI without an explicit safe nested environment.

### Containment / trajectory-oriented evaluation

The emerging research direction is important even when terminal damage is zero: certification should preserve trajectory, attempted forbidden actions, propagation, recovery and authorized utility rather than report only a final PASS/FAIL.

### WeClawArena (2026-08)
Source: https://arxiv.org/abs/2608.03499

Why it matters:
- cross-user agent sandbox with auditable messages/tool/resource operations;
- separates utility from attack success;
- highlights multi-principal authority and privacy boundaries.

AgentCI action:
- add cross-tenant/cross-principal cases to the future certification matrix.

## Cross-project synthesis

The initial AgentCI Sandbox model should have these dimensions:

1. backend identity and isolation class;
2. authority source and immutable policy baseline;
3. filesystem read/write/deny scope;
4. network default, allowlist, protocol, redirect, DNS, private/link-local/metadata behavior;
5. credential mode and scopes (raw/mounted/env/brokered);
6. process tree and child/orphan behavior;
7. CPU/memory/PID/disk/output/time bounds;
8. devices/sockets such as `docker.sock` and `/dev/kvm`;
9. workspace sharing mode and host coupling;
10. ingress/service exposure;
11. lifecycle: create/pause/resume/snapshot/restore/delete;
12. persistence and cross-tenant residue;
13. audit/trajectory evidence;
14. runtime drift and crisis transitions;
15. policy mutation rules;
16. provenance: backend/version/policy hash/test suite/environment fingerprint.

## Highest-value attack classes

- path traversal, symlink/hardlink and mount escape;
- secret/SSH/credential-store reads;
- raw environment secret leakage;
- arbitrary egress, redirects, DNS rebinding, IPv6/private IP/metadata endpoints;
- proxy tunnelling and post-redirect destination confusion;
- Unix sockets and host `docker.sock`;
- process-tree/orphan/daemon persistence;
- fork/process bombs and CPU/memory/disk/output exhaustion;
- blocking stdin/stdout/stderr and timeout-boundary failures;
- snapshot/restore with stale policy or credentials;
- cross-tenant storage/process/network residue;
- shared config/skill poisoning;
- control-plane/MCP authority confusion;
- malicious README/package/tool output requesting sandbox disablement;
- attempts to mutate policy or persuade the Sandbox Intelligence Agent to expand privileges;
- differences between configured policy and effective runtime capability.

## Product decision

### Do now
- define provider-neutral Sandbox Profile / Policy IR;
- define certification evidence and attack taxonomy;
- independently map 6–10 real sandbox providers/primitives;
- select 2–3 reference targets for bounded real experiments;
- build read-only inspection and certification before adaptive mutation;
- preserve trajectory evidence and limitations.

### Do later
- policy compilation into multiple enforcement backends;
- runtime drift detection;
- automatic tightening;
- crisis/quarantine control;
- incident memory / Sandbox Genome;
- authorized policy mutation.

### Do not do now
- build a new hypervisor/microVM runtime;
- claim a provider is secure because it uses a particular backend;
- let an LLM directly grant itself filesystem/network/credential/host authority;
- treat a config file or `PATH`/runtime presence as proof of effective containment;
- run destructive escape research outside a deliberately nested disposable environment.

## Primary success hypothesis

If AgentCI can take multiple real agent sandbox environments and produce one repeatable, provider-neutral certification report that discovers meaningful containment differences or defects that ordinary unit/config checks miss, then Sandbox Certification is a viable core product line.

Evidence threshold for graduation:
- at least 3 materially different real sandbox/runtime targets;
- reusable provider-neutral checks form the majority of the suite;
- at least one independently reproduced meaningful containment/policy mismatch or weakness;
- exact environment/policy/backend provenance;
- low enough setup cost that an agent or CI job can repeat the certification;
- Agent B independently passes both Spec and Standards review.
