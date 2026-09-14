# Agent C Cycle 3 — Event Feasibility / Observability Matrix

Status: bounded Agent C S0/S1-feasibility input. **Not** a second canonical IR, provider verdict, S1 certification result, or permission to run nested/destructive probes on ordinary CI.

AgentCI base for this packet: `main@645b8a1ee157c24ad7f8488285f2ba3581b49a6d`  
A exact head reviewed in parallel: `a07129559923f7258ca16db95df2d0c97afa852f` (PR #34)  
Date: 2026-08-11

## Falsifiable claim

For the first S1 reference candidates, event evidence is only portable when each claim names the **enforcement locus**, **external dependencies**, **observer locus**, **receipt provenance strength**, **safe probe class**, and **unavailable/unverified dimensions**. A backend or isolation class cannot substitute for any of those facts.

Receipt provenance classes used here are descriptive C vocabulary for handoff only; A owns canonical schema naming:

- `native-enforcement`: the enforcement component itself can emit evidence tied to the enforced action;
- `adapter-derived`: AgentCI can bind configuration/runtime facts plus collector evidence, but the backend does not natively emit an AgentCI authority receipt;
- `external-behavioral`: an observer can prove bounded behavior, not decision causation;
- `unavailable/unverified`: no sufficient source is identified for the claim.

No selected target natively emits the complete AgentCI tuple `decision_id + grant/principal refs + policy_digest + policy_epoch + authority_epoch + credential_epoch` for arbitrary workload actions. D/A must therefore not upgrade behavioral evidence into trusted authority-causation evidence.

## Primary source pins

### Bubblewrap
- `containers/bubblewrap` `v0.11.2`, released 2026-04-23.
- README: Bubblewrap constructs a sandbox from Linux namespaces/mounts and explicitly says the security boundary depends on arguments; it is not a complete ready-made policy.
- `v0.11.2` is a setuid-mode security update; upstream recommends normal non-setuid builds.

Primary:
- https://github.com/containers/bubblewrap/releases/tag/v0.11.2
- https://github.com/containers/bubblewrap/blob/v0.11.2/README.md

### gVisor
- `google/gvisor` `release-20260803.0`, commit `48de7274186ae2cbab2c8656c43a73d115227a61`.
- Security model: application syscalls are mediated by the Sentry; filesystem can involve Gofer; host cgroups remain responsible for resource-exhaustion controls and container-level policy remains relevant for network policy.
- Observability docs: Prometheus metrics are mostly gVisor internals and explicitly do **not** provide workload introspection.
- Runtime Monitoring: trace points can stream workload actions, including syscall and container-start events, to an external monitoring process isolated from the sandbox.

Primary:
- https://github.com/google/gvisor/blob/release-20260803.0/g3doc/architecture_guide/security.md
- https://gvisor.dev/docs/user_guide/observability/
- https://gvisor.dev/docs/user_guide/runtimemonitor/

### Firecracker
- `firecracker-microvm/firecracker` `v1.16.1`, released 2026-07-02.
- Firecracker uses KVM microVMs; the jailer composes host mount namespace/chroot, cgroups, uid/gid drop and optional network/PID namespaces around the VMM.
- Snapshot versioning docs state snapshots persist guest memory and VMM state while referencing external TAP, block and vsock resources; successful restore requires those external resources to be available/compatible.
- `v1.16.1` fixed a guest-to-host vsock timeout after snapshot restore with an in-flight TX descriptor, direct evidence that communication/device state across restore is non-trivial.

Primary:
- https://github.com/firecracker-microvm/firecracker/releases/tag/v1.16.1
- https://github.com/firecracker-microvm/firecracker/blob/v1.16.1/docs/jailer.md
- https://github.com/firecracker-microvm/firecracker/blob/v1.16.1/docs/snapshotting/versioning.md

## Classification

`EO` = enforceable + observable from an identified safe source for the bounded claim.  
`EN` = enforceable but not sufficiently observable for the proposed claim.  
`ON` = observable but the observer is not the enforcement point.  
`U` = unavailable/unverified for this candidate/configuration.

These marks are **claim-scoped**, not provider scores.

## Matrix — Bubblewrap v0.11.2 / OS-native composition

| Event / claim class | Class | Enforcement locus | Observer locus / evidence | Receipt provenance | Safe probe class | Material unavailable / unverified |
|---|---|---|---|---|---|---|
| `process.lifecycle` | ON | host kernel PID/process semantics; PID namespace only if configured | launcher + external host process observer limited to owned test tree | external-behavioral | disposable ordinary Linux runner; owned child tree only | helpers/processes launched outside selected tree; sibling namespaces without privileges |
| `filesystem.access` | EN/ON | mount namespace + mount flags; optional external LSM such as Landlock | mount/namespace inspection proves topology; canary access proves bounded behavior | adapter-derived + external-behavioral | synthetic temp dirs/canaries | complete per-access audit is not native Bubblewrap evidence; aliases/host services require explicit cases |
| `network.resolve` | EN/ON | network namespace if `--unshare-net`; otherwise whatever network stack/policy is composed around it | synthetic DNS/resolve probe plus namespace inspection | external-behavioral | synthetic local resolver / no Internet dependency | alternate host proxy/Unix-socket/helper channels are separate |
| `network.connect` | EN/ON | network namespace and any composed proxy/filter/LSM | synthetic allowed/forbidden local endpoints; inspect namespace and declared transports | external-behavioral | local loopback/namespaced synthetic sink only | no generic proof for every protocol/channel; mounted Unix sockets must be enumerated separately |
| `policy.attachment` | ON | launcher/kernel objects created from exact Bubblewrap argv plus any separately configured LSM | exact argv + namespace/mount state + LSM-specific attachment evidence where used | adapter-derived | inspect owned process namespaces/mountinfo | Bubblewrap alone has no first-class policy object/attachment receipt |
| `authority.decision` / `enforcement.receipt` | U | not a Bubblewrap concept | none native | unavailable/unverified | none | D/A decision/grant/epoch causation must come from external control plane if present |
| `lifecycle.snapshot|restore` | U | not a Bubblewrap lifecycle primitive | none native | unavailable/unverified | N/A | do not manufacture parity with VM snapshot semantics |
| `cleanup.postcondition` | ON | host process/filesystem lifecycle + launcher cleanup | external observer outside sandbox boundary checks owned descendants/files/sockets | external-behavioral | disposable runner, test-owned resources | system-wide proof requires privileges and is out of ordinary-CI scope |
| `collector.health` | EO | AgentCI collector itself | collector self-test + expected canary events | adapter-derived | ordinary CI | health proves collector readiness, not containment |

Bubblewrap-specific attachment rule: exact launcher arguments and created namespace/mount topology can prove **configured/instantiated topology**, but not a complete per-action security receipt. If Landlock/seccomp are added, their ABI/filter/attachment state must be separately pinned and collected; do not collapse them into `bubblewrap=true`.

## Matrix — gVisor release-20260803.0 / application kernel

| Event / claim class | Class | Enforcement locus | Observer locus / evidence | Receipt provenance | Safe probe class | Material unavailable / unverified |
|---|---|---|---|---|---|---|
| `process.lifecycle` | EO/ON | Sentry process model for sandboxed workload; host runtime owns outer sandbox lifecycle | Runtime Monitoring trace points / runtime state plus external runsc/container observer | adapter-derived | disposable Linux runner with runsc; synthetic workload | host helpers outside sandbox and container-manager lifecycle remain external |
| `filesystem.access` | EO/ON | Sentry VFS + Gofer/directfs mode-dependent host interaction | Runtime Monitoring syscall/file trace points when explicitly enabled; bounded canaries | adapter-derived | synthetic files only | Prometheus metrics alone are insufficient; directfs/Gofer mode changes surface and must be recorded |
| `network.resolve` | EO/ON | Sentry/network stack or host-network mode plus external container network policy | Runtime Monitoring network/syscall events + synthetic resolver/endpoint observer | adapter-derived | local synthetic DNS/service | effective container-level network-policy attachment is external to Sentry unless separately collected |
| `network.connect` | EO/ON | Sentry/netstack or host-network mode; external network policy may enforce authorization | Runtime Monitoring + actual endpoint observer; record host-network/netstack mode | adapter-derived | local allowed/forbidden service | channel-specific external enforcement still requires its own collector; do not infer from gVisor class |
| `policy.attachment` | ON/U | runtime configuration for gVisor mode; external container/cgroup/network policies outside Sentry | runsc/runtime config can prove effective runtime selection; external policy attachment requires its own source | adapter-derived / unverified | config/runtime identity inspection | no generic proof that an external policy selected the workload without that control-plane collector |
| `authority.decision` / `enforcement.receipt` | U/ON | depends on external policy/broker; Sentry is not AgentCI authorization authority | Runtime Monitoring can show action behavior but not generic D grant/decision causation | external-behavioral unless external PEP emits receipt | none beyond synthetic behavior | complete AgentCI authority tuple unavailable from gVisor alone |
| `lifecycle.snapshot|restore` | U for S1 claim | mode/version-specific and not established in this packet | none accepted for portable claim | unavailable/unverified | do not include as mandatory S1 parity | must not infer snapshot semantics from `application-kernel` |
| `cleanup.postcondition` | ON | Sentry process model + outer runtime teardown | Runtime Monitoring plus external runsc/container observer; test-owned file/socket checks | adapter-derived + external-behavioral | disposable runner | outer host helpers/resources require external observation |
| `collector.health` | EO | Runtime Monitoring/metric server configuration and AgentCI collector | monitor handshake + canary trace point + collector heartbeat | adapter-derived | ordinary disposable runner | Prometheus availability does not prove workload-event coverage |

Critical gVisor rule: **Prometheus metrics must not satisfy mandatory workload-event telemetry.** Upstream explicitly says those metrics mostly describe gVisor internals. A PASS-worthy workload claim requiring event evidence needs Runtime Monitoring/trace-point coverage (or another explicitly bound workload observer), with configuration/version/health recorded.

## Matrix — Firecracker v1.16.1 / conditional microVM feasibility

Precondition: this target remains `U` for real S1 execution until `/dev/kvm` and nested-or-bare-metal virtualization readiness are actually probed. Binary/tag presence is not readiness.

| Event / claim class | Class | Enforcement locus | Observer locus / evidence | Receipt provenance | Safe probe class | Material unavailable / unverified |
|---|---|---|---|---|---|---|
| `process.lifecycle` | ON/U | guest kernel for guest processes; VMM/jailer for host-side VM lifecycle | guest agent/serial for guest process; host VMM observer for VM process | external-behavioral | only after KVM readiness on disposable host | no single observer proves guest process + VMM + external helper cleanup |
| `filesystem.access` | ON/U | guest kernel/filesystem; host file-backed block devices and VMM configuration outside guest | synthetic guest canaries + host-owned backing-file setup | external-behavioral | disposable KVM host, synthetic disks | no native per-file AgentCI receipt; host backing/resource scope must be separately proven |
| `network.resolve` | ON/U | guest stack + virtual NIC; host TAP/netns/routing/firewall external | guest probe + host synthetic endpoint/TAP observer | external-behavioral | isolated synthetic network only | host network policy/attachment and every external hop are not implied by microVM |
| `network.connect` | ON/U | guest kernel/NIC + VMM device + host TAP/routing/filter | guest event plus host endpoint/TAP evidence | external-behavioral | isolated synthetic network | actual endpoint and policy causation need external collectors |
| `policy.attachment` | ON/U | Firecracker API/jailer config and host network/resource controls | API/config identity can prove VM config; host policy attachment needs its own collector | adapter-derived | read-only config inspection after readiness | no generic workload-policy attachment receipt across host layers |
| `authority.decision` / `enforcement.receipt` | U | external authorization/broker if any | Firecracker API/metrics do not provide generic AgentCI authority causation | unavailable/unverified | none | complete D tuple unavailable from Firecracker alone |
| `lifecycle.snapshot|restore` | EO/ON after readiness | Firecracker snapshot/load + guest/VMM state; external TAP/block/vsock resources remain dependencies | API/log/guest canary + external resource identity comparison | adapter-derived + external-behavioral | disposable KVM host only | preserved/reconstructed session/transport authorization freshness needs separate D/E evidence |
| `cleanup.postcondition` | ON/U | guest shutdown/VM stop/VMM termination are distinct | guest observer + external VMM/jailer/resource observer | external-behavioral | disposable KVM host | one terminal state cannot prove all three lifecycle levels clean |
| `collector.health` | EO after readiness | AgentCI collectors + Firecracker log/metrics/guest observer stack | collector self-test, guest canary, expected host observation | adapter-derived | disposable KVM host | health of one layer cannot stand in for guest + VMM + host visibility |

Firecracker restore rule: snapshot versioning explicitly references external TAP, block and vsock resources; `v1.16.1` also fixed an in-flight vsock restore bug. Therefore `snapshot restored` cannot imply `network/session authority freshly revalidated`. C hands that causation requirement to D/E.

## Safe probe classes

### Ordinary/disposable Linux runner — allowed C feasibility work
- version / binary provenance;
- Bubblewrap namespace/mount topology with synthetic temporary trees;
- synthetic filesystem canaries;
- synthetic local network allow/deny endpoints, without scanning external networks;
- owned process-tree timeout/cleanup checks;
- gVisor runtime selection/config identity on a disposable Linux runner;
- gVisor Runtime Monitoring canary/collector-health checks when runsc is already installed/configured safely.

### Requires dedicated nested/privileged disposable infrastructure
- Firecracker execution requiring `/dev/kvm`;
- host TAP/netns/firewall manipulation beyond a prebuilt isolated fixture;
- privileged eBPF/system-wide process or network collectors;
- kernel/runtime adversarial tests that could affect unrelated host workloads;
- snapshot/restore continuity experiments that preserve live sockets/devices.

### Prohibited on ordinary CI under AgentCI safety policy
- escape payloads or host breakout attempts;
- host-wide destructive network/filesystem mutation;
- reading real credentials/secrets as canaries;
- probing unrelated host processes/sockets/devices;
- treating lack of test permission/visibility as PASS.

The safety grouping above is an AgentCI policy inference, not an upstream provider guarantee.

## Handoff to A

The next canonical A head should be able to represent, without provider-specific free text:
1. enforcement topology/locus distinct from `isolation_class`;
2. shared host/control surfaces and external enforcement dependencies;
3. lifecycle boundary plus observer locus outside the asserted cleanup boundary;
4. evidence/receipt provenance strength (`native`, `adapter-derived`, `external-behavioral`, `unavailable` or equivalent);
5. safe probe class and unavailable/unverified dimensions.

C does not prescribe exact field names. A owns the single canonical schema.

## Handoff to B

High-yield falsification cases:
- accept gVisor Prometheus metrics as mandatory workload-event evidence;
- accept Bubblewrap argv/namespace configuration as a per-access enforcement receipt;
- accept Firecracker API config as proof of host network-policy attachment;
- accept a cleanup observer that runs inside the boundary it is supposed to prove terminated;
- accept `microvm` or `application-kernel` as sufficient cause for filesystem/network/credential PASS;
- upgrade `external-behavioral` evidence into a D `Decision`/`EnforcementReceipt` causation claim;
- infer snapshot/session freshness from policy equality or successful VM restore.

## Handoff to D/E

- D: treat runtime evidence as authority-causation only when a resolvable decision/receipt source actually exists; otherwise preserve `unverified` for causation.
- E: make mandatory telemetry claim-specific. gVisor Prometheus metrics are insufficient for workload introspection; Bubblewrap has no native complete per-access event stream; Firecracker needs a multi-observer guest/VMM/host model for lifecycle/network claims.
- Both: attachment evidence is a separate object/fact from policy/config presence.

## A exact-head C fidelity check — `a07129559923f7258ca16db95df2d0c97afa852f`

Compared with prior reviewed head `1267fa2878798e42680bcc12806342d85d927184`, A changed only the red-control fixture, semantic validator and evidence-contract tests for `SBX-EVID-001`; the canonical schema/integration document did not change.

C verdict on the five isolation deltas: **PARTIAL / RETURN unchanged**.

1. enforcement topology/locus — still not structurally represented beyond `backend.isolation_class` and free-form enforcement layer strings;
2. shared host/control surface + external enforcement dependencies — still not first-class structured evidence;
3. lifecycle boundary + observer locus — cleanup post-conditions exist, but observer location/trust is not bound to the asserted boundary;
4. receipt/evidence provenance strength — `EnforcementReceipt` shape exists, but EvidenceEnvelope does not distinguish native enforcement causation from adapter/external behavioral evidence;
5. safe probe class + unavailable dimensions — still not structurally represented for TestCase/reference target planning.

This is not a B verdict on `SBX-EVID-001`. A's RED→GREEN work may correctly fix that separate false-PASS path while the C isolation integration remains incomplete.

## Next smallest loop

A integrates only the five C deltas into the same canonical v0alpha1 contract (without widening provider-specific schema) and publishes a new immutable head. C then rechecks those five items only. B remains owner of independent Spec + Standards acceptance.