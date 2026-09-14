# Agent C Cycle 1 — Isolation / Runtime Semantics Packet

Status: bounded Agent C research packet for S0 integration; **not** a second canonical Sandbox IR, provider verdict, or certification result.

Role: Agent C — Isolation / Runtime Systems Researcher  
AgentCI base HEAD studied: `645b8a1ee157c24ad7f8488285f2ba3581b49a6d`  
Research date: 2026-08-11  
Primary consumers: A/#25, B/#26, D/#28, E/#29, Supervisor/#24

## Falsifiable claim

A provider-neutral containment claim can be portable across OS-native, application-kernel, and microVM backends **only when the evidence identifies the actual enforcement locus, shared host surface, inheritance/lifecycle behavior, and observability/receipt limits**. An `isolation_class` or backend name by itself is never sufficient evidence for a capability verdict.

A future AgentCI harness should be able to falsify this claim by finding a supposedly portable assertion below that cannot be evaluated without smuggling provider-specific semantics into the assertion itself. Until such an assertion has a working observer on a target, it remains `UNVERIFIED`.

## Source ledger and pins

Only primary upstream sources were used for the technical facts below.

| Source | Pin / date used | Why it matters | License / reuse note |
|---|---|---|---|
| Bubblewrap | `v0.11.2`, released 2026-04-23 | Linux mount/user/PID/network/IPC namespace constructor; explicit warning that policy depends on arguments | GNU Library GPL v2 in upstream `COPYING`; no upstream code copied here |
| Linux Landlock docs | upstream `Documentation/userspace-api/landlock.rst`, dated June 2026 | stackable unprivileged LSM, filesystem/network rules, inheritance and monotonic restriction semantics | kernel documentation carries GPL-2.0 SPDX; no code copied |
| Linux seccomp docs | upstream `Documentation/userspace-api/seccomp_filter.rst` | syscall-surface reduction, inheritance, notification/tracer authority channel | kernel source/docs; no code copied |
| gVisor | `release-20260803.0`, commit `48de7274186ae2cbab2c8656c43a73d115227a61` | application-kernel boundary; Sentry/Gofer; external cgroup/network-policy dependencies | Apache-2.0 primary license, with per-file exceptions noted upstream |
| Firecracker | `v1.16.1`, released 2026-07-02 | KVM microVM boundary plus VMM jailer/cgroup/namespace composition and snapshot lifecycle | Apache-2.0; no code copied |
| Kata Containers | `4.0.0`, released 2026-07-20 | VM-backed container composition with host runtime + guest agent; useful later comparison | Apache-2.0; no code copied |

Primary URLs:

- https://github.com/containers/bubblewrap/releases/tag/v0.11.2
- https://github.com/containers/bubblewrap/blob/v0.11.2/README.md
- https://github.com/torvalds/linux/blob/master/Documentation/userspace-api/landlock.rst
- https://github.com/torvalds/linux/blob/master/Documentation/userspace-api/seccomp_filter.rst
- https://github.com/google/gvisor/tree/release-20260803.0
- https://github.com/google/gvisor/blob/release-20260803.0/g3doc/architecture_guide/security.md
- https://github.com/firecracker-microvm/firecracker/releases/tag/v1.16.1
- https://github.com/firecracker-microvm/firecracker/blob/v1.16.1/docs/jailer.md
- https://github.com/kata-containers/kata-containers/releases/tag/4.0.0

## 1. Isolation semantics matrix

### 1.1 Linux OS-native / process sandbox composition

Representative mechanisms: Bubblewrap + Linux namespaces, optionally stacked with Landlock and seccomp. These are mechanisms that may be composed into a sandbox; they are not one complete policy by themselves.

| Dimension | Actual enforcement locus | What can be asserted from configuration | What still requires effective probing |
|---|---|---|---|
| Filesystem | mount namespace and mount flags; optionally Landlock LSM layers | which host paths were bind/ro-bind mounted; Landlock ruleset intent | canary read/write denial, path aliases, bind/overlay behavior, unexpected sockets/files exposed through mounted trees |
| Network | network namespace can remove normal external interfaces; Landlock can restrict supported TCP/UDP port actions; external proxies/sockets may add mediated channels | namespace creation and declared port rules | each channel independently: HTTP(S), direct TCP, proxied TCP, UDP, ICMP, DNS, Unix socket, ingress/tunnel |
| Process tree | PID namespace if requested; Bubblewrap supplies a PID 1 when PID namespace is used; Landlock/seccomp restrictions inherit to descendants under documented conditions | namespace/filter/ruleset attachment | orphan/daemon survival, sibling-thread coverage, helpers launched outside the workload boundary |
| Syscalls | seccomp BPF filter at host kernel | loaded filter and supported actions | whether the filter covers the expected architecture/ABI and whether user-notification/tracer/helper channels change effective authority |
| Resources | host cgroups/rlimits if separately configured | configured limits | wall-clock/CPU/memory/PID/output behavior under bounded stress; cleanup after limit breach |
| Devices / IPC | mount/device exposure + IPC namespace + host Unix sockets explicitly mounted or inherited | namespace and mount declarations | access to meaningful device/runtime/control sockets and whether a socket is a forbidden host surface or intended enforcement transport |
| Workspace coupling | explicit bind mounts / readonly binds | path mapping and rw/ro flags | aliases, symlinks, mounts, writable metadata, host-coupled sockets/config inside the workspace tree |
| Lifecycle | namespace lifetime/process lifetime; temporary mount root disappears when final process exits | launcher exit and declared teardown | descendants outside the namespace, external helpers, leftover files/sockets/processes/cgroups |

Important upstream constraints:

- Bubblewrap always creates a new mount namespace, but upstream explicitly states that it is a sandbox-construction tool and that protection is determined by the arguments supplied.
- Bubblewrap `--unshare-net` produces a network namespace with loopback only; that is a stronger statement about direct namespace networking than a generic hostname allowlist, but it does **not** prove there is no alternate proxy/Unix-socket/helper channel.
- Bubblewrap warns that a mounted D-Bus socket can be an authority channel capable of invoking host services; therefore `filesystem isolated` cannot imply `host control plane isolated`.
- Bubblewrap `v0.11.2` is a security update for setuid mode and upstream now defaults to building without setuid support. S1 should use unprivileged user namespaces, not setuid Bubblewrap.
- Landlock is stackable and can only add restrictions to an already Landlocked thread/domain. Current upstream docs also make ABI support explicit; unsupported rights are intentionally dropped in best-effort compatibility examples. Therefore the harness must record the **effective Landlock ABI/features**, not merely `landlock=true`.
- Landlock inheritance is thread/descendant scoped. Current docs call out multithread coverage nuances and a synchronization flag in newer ABIs. A process-level statement is unsafe unless all relevant threads were proven attached.
- Seccomp upstream explicitly says syscall filtering is **not a sandbox**. It reduces host kernel syscall surface. If `fork`/`clone`/`execve` are permitted, descendants inherit the same filters, but seccomp user-notification and ptrace paths introduce privileged external decision surfaces that must be modelled separately.

### 1.2 Application-kernel / container-hardening class — gVisor

Pin: `release-20260803.0` (`48de7274186ae2cbab2c8656c43a73d115227a61`).

The core enforcement boundary is the gVisor **Sentry**, a userspace application kernel that implements the Linux-like System API rather than passing application syscalls directly through to the host kernel. Filesystem access can involve a **Gofer** process; the Sentry may receive file descriptors and operate on them, or filesystem modes may change the host surface. Network traffic may flow through a virtual interface/netstack, while host networking is a materially different mode.

Crucially, upstream's own security model places some guarantees outside the Sentry:

- host cgroups remain responsible for resource-exhaustion / DoS controls;
- network policy should be applied at the container level;
- data mapped into the container remains an operator responsibility;
- directfs/host-networking modes change the host surface and must be recorded as effective backend modes, not hidden behind `gvisor`.

Therefore a generic field such as `isolation_class: application-kernel` should tell AgentCI **where syscall mediation occurs**, but must not imply filesystem scope, network deny, resource limits, or credential isolation.

Suggested C-level observability split:

- **enforceable and partially observable**: Sentry-mediated syscall semantics and sandbox process behavior;
- **external enforcement dependency**: cgroups and container-level network policy;
- **shared host surfaces**: Sentry/Gofer processes, host kernel APIs reached by those components, host-backed files made available through the filesystem path, virtual networking plumbing;
- **mode-sensitive**: directfs and host-network configurations;
- **unknown until S1 probe**: checkpoint/restore semantics relevant to AgentCI's matched lifecycle assertions; do not infer from class name.

### 1.3 microVM class — Firecracker

Pin: `v1.16.1`, released 2026-07-02. The x86_64 release archive published by upstream has SHA-256 `382a02a869e4d6d5cb14c40577f9545e8458021ea8b0b2d3fc10ec14d9c242e6`.

The workload/host-kernel boundary is the guest kernel + KVM hardware virtualization boundary, mediated by the Firecracker VMM. This still composes with host controls:

- upstream states that safe multi-tenant use depends on a correctly configured Linux host;
- the Firecracker jailer adds a mount namespace/chroot, cgroup placement/resource configuration, uid/gid drop, optional network namespace, and optional PID namespace around the **VMM process**;
- the jailer deliberately exposes `/dev/kvm` and `/dev/net/tun` inside its jail because the VMM needs them;
- guest disks are host file-backed block devices; network interfaces are configured through the VMM and effective egress depends on host TAP/netns/routing/firewall policy;
- the VMM API socket is a host control-plane surface and is not equivalent to guest network access;
- Firecracker uses additional seccomp filters for the VMM.

Process semantics are two-level: guest processes are governed by the guest kernel; the VMM is a host process governed by the jailer/cgroups. Killing the guest process, stopping the VM, and killing the VMM are **three different cleanup statements**.

Lifecycle is also non-trivial. Firecracker `v1.16.1` fixed a vsock guest-to-host timeout after snapshot restore involving an in-flight TX descriptor. This is direct evidence that snapshot/restore can preserve or reconstruct device/queue state and must not be treated as a clean boot by AgentCI. Restore-related credential/socket/policy freshness therefore remains a D/E concern and is not implied by `microvm`.

### 1.4 VM-backed container composition — Kata Containers

Pin: `4.0.0`, released 2026-07-20.

Kata's own architecture is a useful S2 comparison because the container-facing runtime runs on the host while an agent runs inside a VM/POD and a hypervisor supplies the VM boundary. `kata-runtime check` exists specifically because host virtualization readiness is not implied by installation.

This class adds more control-plane components than raw Firecracker and is useful for future adapter/attachment tests, but it is not the highest-information S1 Cycle 1 target while the Supervisor host has no usable Docker/WSL runtime.

## 2. Five-plus cross-backend semantic traps

These are handoff items for B/#26. The same phrase can represent materially different guarantees.

1. **`network denied`** — may mean no external interface in a Linux net namespace, no route/firewall permission around a VM, an external container policy around gVisor, port-only LSM restrictions, or proxy-mediated access. HTTP(S), generic TCP, UDP, ICMP, DNS, Unix sockets and ingress/tunnels must be evaluated separately.
2. **`Unix socket denied`** — a host/runtime socket can be a breakout/authority surface, but another backend may intentionally use a Unix socket as its enforcement transport. The portable claim is about workload capability and peer/resource scope, not about the existence of the socket primitive.
3. **`process terminated`** — parent exit, PID-namespace init exit, process-group cleanup, sandbox-runtime teardown, VM stop and VMM termination are different events. A helper or descendant outside the selected boundary may survive.
4. **`workspace isolated`** — mount omission/readonly bind, Landlock path restriction, gVisor Gofer/directfs host-backed access, and microVM block-device/shared-filesystem designs expose different aliasing and host-coupling risks.
5. **`credential brokered`** — none of the isolation substrates proves broker correctness. A credential may cross a proxy, Unix socket, control-plane API, environment, file, FD, or helper process. Broker semantics belong to D and must be tested as an alternate authority channel by B.
6. **`filesystem denied`** — absence from a mount namespace, LSM denial, application-kernel virtual filesystem denial, and guest/host filesystem separation are not interchangeable and have different alias/mount/device surfaces.
7. **`resource limited`** — gVisor delegates DoS defense to host cgroups; Firecracker may combine guest/VMM configuration with host cgroups/rate limiters; OS-native tools need separate cgroups/rlimits. Configuration location must be explicit.
8. **`restored safely`** — snapshot/restore may preserve process, device, socket/FD or other runtime state. Same policy text before/after restore does not prove fresh authority.

## 3. Portable semantic assertions for A/#25

These are **claim shapes**, not schema fields. A owns the canonical object names and schema.

1. **Authorized workspace utility**: a canary created in the authorized workspace is readable/writable as intended by the workload, and the observer confirms the expected host/lifecycle coupling.
2. **Sensitive-path denial**: an external oracle first proves that a synthetic sensitive canary exists, then the workload cannot read it through the tested path/alias class. A missing canary is harness failure/UNVERIFIED, not PASS.
3. **Channel-specific network denial**: for one named network channel, the workload cannot reach a synthetic forbidden endpoint, while an authorized control endpoint on the same relevant stack remains reachable. Record the actual endpoint and enforcement transport separately.
4. **Host socket/device denial**: a named host/control socket or device is not usable by the workload unless it is explicitly part of the declared enforcement transport; if it is transport, test its peer/scope rather than calling socket presence a failure.
5. **Process cleanup**: after the declared deadline/termination action, no descendant, daemon, socket or file residue survives within the claim's defined lifecycle boundary. The observer must be outside that boundary.
6. **Effective resource boundary**: bounded workload pressure reaches the declared limit/failure mode without escaping the sandbox boundary; merely finding a cgroup/config file does not satisfy the claim.
7. **Backend dependency visibility**: a PASS-worthy claim states which enforcement layers were actually tested and which remain external/unverified. A backend class cannot silently stand in for those layers.

For all of the above, `configured`, `attached`, `enforced`, and `observed` are distinct facts. C recommends that A/E preserve those distinctions even if the final canonical vocabulary uses different names.

## 4. Enforcement receipt / evidence implications for E/#29

None of the selected substrates natively supplies a complete AgentCI authority receipt containing `decision_id + policy_digest + authority_epoch` for every workload action.

- Bubblewrap: launcher arguments and namespace state are configuration/topology evidence, not per-action authority receipts.
- Landlock: kernel enforcement can be behaviorally tested and newer ABIs expose additional logging/synchronization capabilities, but a Landlock rule hit is not automatically an AgentCI grant/decision receipt.
- seccomp: notification/log/trap paths can provide syscall-event evidence, but the external supervisor/tracer itself becomes an authority-sensitive component; AgentCI IDs/epochs must be bound by the harness/control plane.
- gVisor: Sentry/runsc tracing/logging can provide runtime evidence, but external cgroup/network-policy decisions are outside the Sentry and must be joined from their own collectors.
- Firecracker: API configuration, jailer state, metrics and guest observations do not by themselves prove an authorization decision at the actual workload resource boundary.

Required semantic distinction for E/A (field names are intentionally left to A):

```text
native enforcement receipt
vs adapter-derived receipt
vs external-observer behavioral evidence
vs unavailable
```

If direct decision→enforcement binding is unavailable, the evidence may still prove a bounded behavioral assertion, but it must not claim that a specific authority decision was the enforcement cause. That dimension remains `UNVERIFIED`.

## 5. Observable vs enforceable handoff

| Mechanism/class | Enforceable but not automatically proven by config | Observable but not itself enforcement | Typical blind spot |
|---|---|---|---|
| Bubblewrap/namespaces | mount/net/PID/IPC topology once correctly created | argv, namespace/mount inspection | alternate mounted sockets/helpers; host processes outside namespace |
| Landlock | LSM path/port restrictions and inherited layers | ABI support, selected logging/probe outcomes | incomplete thread/ABI coverage; no generic proof of all alternate channels |
| seccomp | syscall actions | trap/log/user-notif events | information-flow/filesystem/network policy beyond syscall decision; privileged supervisor/tracer behavior |
| gVisor | Sentry System API mediation | runsc/Sentry/Gofer logs and behavioral probes | external cgroups/network policy; host-backed data exposure; mode changes |
| Firecracker | guest/KVM isolation + VMM/jailer controls | VMM API/config/metrics, host process state, guest probe | guest semantic policy, host network plumbing, stale restored device/session state |
| Kata | VM boundary + runtime/guest-agent composition | runtime/agent/hypervisor telemetry | attachment/config drift across host runtime, guest agent and hypervisor |

## 6. S1 reference targets and disposable runner plan

### Target 1 — Bubblewrap `v0.11.2` (+ optional Landlock/seccomp probe composition)

**Why first**: low software/setup cost, explicit OS-native semantics, easy to create both strict and deliberately permissive controls.

Prerequisites:
- dedicated/disposable Linux runner;
- unprivileged user namespaces enabled and actually probed;
- build/install Bubblewrap `v0.11.2` without setuid mode;
- record exact kernel version and effective Landlock ABI if Landlock is included;
- do not assume current Supervisor host readiness.

Pin:
- tag `v0.11.2`;
- upstream release archive SHA-256 `69abc30005d2186baf7737feacd8da35633b93cf5af38838ecff17c5f8e924f6`.

Safe setup/teardown:
- create a fresh temporary workspace/canary tree and synthetic local services/sockets;
- launch one sandbox per attempt;
- after exit, externally verify child process/socket/file residue is absent;
- delete the disposable work tree;
- never mount real user credential stores or real runtime control sockets.

Cost: upstream software $0; only disposable Linux runner capacity.

### Target 2 — gVisor `release-20260803.0`

**Why second**: materially different application-kernel enforcement; exposes the important split between Sentry mediation and external cgroup/network policy.

Prerequisites:
- dedicated Linux runner;
- pin commit `48de7274186ae2cbab2c8656c43a73d115227a61` / release tag;
- install `runsc` and record `runsc --version` plus exact host kernel;
- use a reproducible containerd/Docker or direct runsc setup on the dedicated runner; Supervisor host currently lacks Docker and should not be treated as ready.

Safe setup/teardown:
- fresh sandbox/container for each attempt;
- record filesystem mode and network mode explicitly;
- after deletion, verify no runsc/Gofer workload process or synthetic socket/file residue remains;
- use only synthetic canaries/endpoints.

Cost: upstream software $0; moderate runner configuration cost.

### Target 3 — Firecracker `v1.16.1` feasibility, then real target only with KVM

**Why third**: gives a real hardware-virtualized microVM class, but requiring it before a verified KVM runner exists would create fake evidence pressure.

Prerequisites:
- dedicated disposable/self-hosted Linux environment with `/dev/kvm` and nested/bare-metal virtualization proven by a bounded readiness probe;
- pinned Firecracker/jailer `v1.16.1` pair;
- pinned guest kernel/rootfs digest;
- explicit TAP/netns/firewall setup and cleanup;
- no production credentials or networks.

Safe teardown must verify:
- guest stopped;
- Firecracker VMM and jailer descendants gone;
- TAP/netns/cgroup/jail/temp disk/socket artifacts removed;
- no stale resumed snapshot/session is reused unless the test is explicitly a lifecycle case.

Cost: upstream software $0; requires suitable KVM hardware/runner. Until that runner is actually available, this target is `feasibility/UNVERIFIED`, not tested.

### Why not Kata in the first matched pair

Kata `4.0.0` is valuable later because it adds a host runtime + guest agent + hypervisor composition and exposes attachment/control-plane semantics, but it has higher installation/runtime complexity and less incremental S0 information than first contrasting Bubblewrap and gVisor. Keep it as an S2/third-or-fourth target candidate unless dedicated infrastructure is already available.

## 7. Safe probes vs tests forbidden on ordinary CI

### Safe on a disposable Linux runner when prerequisites are present

- workspace utility canary read/write;
- synthetic sensitive-canary denial with an external existence oracle;
- synthetic local allow/deny network endpoints with channel separated explicitly;
- synthetic Unix socket reachability/denial;
- harmless syscall denial for a pinned seccomp test profile;
- bounded process-tree timeout/cleanup checks;
- bounded file/output/process-count controls well below host exhaustion thresholds;
- configuration-versus-effective mismatch checks that do not require escaping the nested sandbox.

### Require deliberately nested, disposable, privileged infrastructure

- kernel/runtime escape payloads or exploit chains;
- tests against real host `docker.sock`, production runtime sockets or privileged host services;
- `/dev/kvm`/device abuse beyond normal Firecracker setup;
- aggressive fork bombs, disk-fill, memory exhaustion or host-wide DoS;
- raw packet/proxy-bypass tests against real private/link-local/cloud metadata services;
- privileged mount namespace manipulation intended to cross the outer runner boundary;
- kernel fault injection, eBPF enforcement experiments requiring elevated host authority;
- snapshot/restore adversarial state tests that could preserve real credentials or network sessions.

Use synthetic/nested equivalents first. A destructive success condition must never be the ordinary CI host being compromised.

## 8. Handoff deltas

### To A/#25

Integrate only these durable semantics, not this document as a parallel schema:

- `isolation_class` needs a separate effective enforcement-locus/shared-host-surface representation;
- network capability must remain separate from enforcement transport;
- filesystem/workspace claims must identify host coupling mode;
- process cleanup must define the lifecycle boundary and use an observer outside it;
- resources may be enforced by a different layer than syscall/filesystem isolation;
- effective backend modes such as gVisor directfs/host networking or Firecracker host netns are material provenance;
- a provider-neutral PASS must list unverified external layers rather than inheriting guarantees from the backend class.

### To B/#26

Prioritize these counterexamples against A's exact head:

- `network denied` represented as one boolean/channel;
- host Unix socket categorized as always forbidden even when it is declared enforcement transport, or accepted without peer/scope evidence when it is a host authority surface;
- `process terminated` checked only inside the sandbox boundary so an external helper/orphan survives unseen;
- `workspace isolated` inferred from a mount/profile without alias/host-coupling evidence;
- `credential brokered` inferred from isolation class;
- resource limit inferred from gVisor/VM class despite external cgroup dependency;
- snapshot restore treated as a new authority epoch without continuity evidence.

### To D/#28

Isolation mechanisms do not grant authority. In particular:

- seccomp user-notification/tracer, mounted Unix sockets, gVisor host networking/filesystem modes, Firecracker API/netns/TAP configuration and Kata host runtime are **external authority/control channels** that must bind to D's principal/grant/decision model rather than being hidden as implementation details;
- restore safety cannot be derived from the isolation class; continue D's requirement to bind fresh authority/credential epochs and prove or mark continuity state.

### To E/#29

For each semantic case, capture enforcement-locus and observer-locus separately. Behavioral PASS is possible without a native authority receipt only for a narrowly scoped assertion; lack of decision→enforcement binding must remain an explicit limitation/UNVERIFIED dimension.

The matched quartet should use Bubblewrap + gVisor first, then Firecracker when KVM becomes real. This maximizes cross-class information without inventing cloud or runtime evidence.

## 9. Known limitations / unknowns preserved

- No real S1 target was executed in this C cycle; this is upstream semantics + feasibility, not certification evidence.
- Supervisor host readiness remains unchanged: no Docker runtime was established and no usable WSL distribution was established by the Supervisor inspection.
- Firecracker/Kata readiness is not inferred from documentation or binary availability.
- gVisor checkpoint/restore semantics relevant to AgentCI lifecycle claims were not independently probed in this cycle.
- Landlock effective ABI/features vary with the running kernel and must be probed per runner.
- No selected substrate natively proves D's complete authority model; receipt binding is an integration/evidence responsibility.

## 10. Next smallest C loop

After A publishes an exact S0 integration head:

1. verify that the seven A handoff semantics above are represented without provider names becoming guarantees;
2. give B one concrete counterexample for any omitted enforcement/shared-surface distinction;
3. if A is structurally correct, help E finalize the Bubblewrap/gVisor observability adapters for the matched semantic quartet;
4. do **not** expand to new providers unless a specific unresolved field requires another isolation mechanism to disambiguate it.
