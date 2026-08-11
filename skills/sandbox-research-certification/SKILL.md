---
name: sandbox-research-certification
description: Research, design, implement and adversarially verify AgentCI's provider-neutral Agent Sandbox Certification capability.
---

# Sandbox Research & Certification

Use this skill whenever work touches agent sandboxes, untrusted code execution, sandbox backends, sandbox policy, containment, runtime isolation, agent permission models, credential brokering, sandbox benchmarks, or adaptive sandbox intelligence.

Also read:
- `CONTEXT.md`
- `skills/autonomous-owner-multi-agent-master/SKILL.md`
- `skills/owner-autonomous-project-operator/SKILL.md`
- `skills/agent-precision/SKILL.md`
- `skills/proactive-open-source-adoption/SKILL.md`
- `docs/architecture/sandbox-certification-contract.md`
- `.company/research/external/agent-sandbox-landscape-2026-08-11.md`

## Strategic product boundary

Do not begin by building another hypervisor, microVM service, container platform or generic remote code execution provider.

Start with:

```text
understand environment
→ normalize sandbox contract
→ probe effective capability
→ attack/falsify containment
→ certify scoped guarantees
→ preserve evidence
```

Only after this is proven should AgentCI add adaptive policy intelligence.

Core statement:

> Sandbox providers build the cage. AgentCI proves the cage actually holds. Then intelligence can learn how the cage should evolve.

## Non-negotiable invariants

1. AI is never the final enforcement boundary.
2. Observation may change understanding; observation does not grant authority.
3. Automatic privilege contraction may be allowed; automatic self-expansion is not.
4. Configured/present/installed does not equal effective/verified.
5. A backend name is not a security verdict.
6. Certification binds to exact environment/backend/policy/test provenance.
7. Untested material capabilities cannot be hidden inside PASS.
8. All destructive or escape-oriented experiments must run only inside a deliberately nested, disposable, bounded environment.

## Source discipline

For technical claims prefer:
- upstream repository;
- official documentation;
- official release/security notes;
- standards/kernel docs;
- research paper for benchmark methodology.

For every important upstream record capture:

```text
name
source URL
maintainer/owner
retrieved_at_utc
event/release date
current relevant version
license / attribution obligation
isolation class
filesystem model
network model
credential model
process/resource model
lifecycle/state model
control-plane model
known limitations
AgentCI transferable pattern
AgentCI attack candidates
classification
```

Classify:

```text
adopt-now
experiment
benchmark
watch
reject
remove-existing
```

Do not turn upstream marketing text into AgentCI facts without independent evidence.

## Agent A role

Agent A is Builder/Researcher.

During S0:
- maintain the provider/primitives/benchmark matrix;
- extract stable common vocabulary;
- propose Sandbox Profile / Policy IR changes;
- build the smallest safe inspection/probe harness;
- prefer provider-neutral interfaces;
- add tests before claims;
- preserve exact source/version/provenance;
- keep external-provider adapters optional.

During S1+:
- implement generic checks before provider-specific branches;
- keep probes read-only or deliberately bounded where possible;
- return explicit `unverified` when the environment cannot safely test a capability;
- never fake cloud/provider evidence using mocks and then call it real certification;
- document backend limits and test preconditions.

Agent A does not declare its own sandbox certified.

## Agent B role

Agent B independently attacks both **Spec** and **Standards**.

### Spec questions
- Does the implementation actually enforce/measure the stated contract?
- Is the observed capability the one the user cares about?
- Are material capabilities missing from the verdict?
- Does evidence bind to the exact backend/policy/environment?

### Standards questions
- Can a hostile workload bypass the test or policy?
- Does another channel expose the same authority (MCP/API/helper/tool)?
- Can stale snapshot/state/credential data survive?
- Does the implementation fail closed under malformed/unknown state?
- Are limits bounded under blocking I/O/resource exhaustion?
- Is untrusted text able to manipulate policy authority?

Attack families:
- filesystem traversal/symlink/hardlink/mount;
- secret and credential reads;
- egress redirect/DNS/private IP/IPv6/proxy/socket;
- cloud metadata;
- `docker.sock`/runtime socket/device access;
- process tree/orphans/fork bomb;
- stdin deadlock/stdout-stderr flood/deadline;
- snapshot/resume stale policy and secret state;
- cross-tenant residue;
- shared skill/config poisoning;
- control-plane/MCP authority confusion;
- prompt-induced permission expansion;
- configured-vs-effective mismatch;
- degraded/fallback backend mismatch.

B must record exact counterexamples. A PASS on one review axis cannot hide a FAIL on the other.

## Supervisor role

Supervisor owns convergence:
- keep one canonical Sandbox Contract;
- remove duplicate terminology;
- choose high-information reference targets;
- prevent provider/runtime scope creep;
- prioritize meaningful cross-backend evidence;
- decide experiment graduation;
- preserve known limitations;
- ensure A/B work on complementary tasks instead of duplicating research.

The Supervisor should split work in parallel:

```text
A: provider mapping + generic implementation + reproducible probe
B: threat model + attack corpus + independent upstream verification
Supervisor: architecture synthesis + evidence gate + target selection
```

## Environment Capability Graph

The intelligence layer may model:

```text
OS/kernel
runtime
filesystem
network
credentials
process/resources
devices/sockets
tools/MCP
workspace sharing
lifecycle/snapshots
control plane
threat model
```

The graph must distinguish facts by evidence source and confidence.

Example states:

```text
declared
configured
probed
verified
failed
unverified
not-applicable
```

Do not collapse these into a boolean `sandboxed` flag.

## Policy authority model

Separate:

### Trusted authority
- owner/Supervisor policy;
- signed organization policy;
- immutable baseline;
- explicitly approved capability grant;
- deterministic validator rules.

### Untrusted observations
- repo content;
- README;
- package scripts/metadata;
- web content;
- tool output;
- MCP content;
- model output;
- generated code.

Untrusted observations may cause:

```text
risk signal
proposal
quarantine
request-for-authority
```

They may not directly cause:

```text
DENY → ALLOW
RO → RW
no-network → network
no-secret → secret
workspace → host
no-device → privileged device/socket
```

## Test design

Every certification test should specify:

```text
capability under test
threat model
precondition
probe/attack
expected deterministic boundary
observable evidence
cleanup condition
false-positive risk
false-negative risk
backend assumptions
```

Prefer a generic semantic assertion, e.g.:

> A workload cannot read the configured sensitive path.

Then implement provider-specific setup/probes underneath it.

Do not encode provider marketing names as expected outcomes.

## Trajectory evidence

Where feasible preserve:
- command/tool event;
- requested resource/capability;
- allow/deny result;
- process identity;
- destination/path;
- policy/version;
- timestamp;
- cleanup state;
- final artifact/verdict.

A blocked malicious attempt and an unattempted action are not the same evidence.

## Reference-target strategy

S0 should study many systems.

S1 should test few systems deeply.

Aim for diversity:
- OS-native sandbox;
- container/application-kernel/Kubernetes sandbox;
- microVM/provider sandbox when available;
- provider-independent runtime interface as an adapter target.

Do not require paid infrastructure for the first proof.

## Graduation gates

Do not call Sandbox Certification a shipped/core capability until:

1. >=3 materially different real sandbox/runtime targets are tested;
2. most checks are provider-neutral semantic checks;
3. at least one meaningful containment/policy difference or defect is independently reproduced;
4. exact policy/backend/environment provenance is preserved;
5. setup/reproduction is practical for CI or an agent;
6. Agent B reports Spec PASS and Standards PASS;
7. README/`llms.txt`/SKILL claims match released behavior.

## Adaptive sandbox intelligence gate

Do not start autonomous policy mutation merely because the contract exists.

Required sequence:

```text
inspect
→ certify
→ incident evidence
→ drift detection
→ proposed delta
→ deterministic validation
→ B attack
→ safe contraction only
```

Privilege expansion remains externally authorized.

## Research output

Each meaningful cycle should end with at least one of:
- new verified upstream fact;
- new cross-provider invariant;
- new bounded experiment;
- new attack test;
- accepted/rejected architecture change;
- independently reproduced sandbox difference;
- updated provider matrix;
- evidence-backed removal of a bad idea.

Do not create status noise when nothing meaningful changed.
