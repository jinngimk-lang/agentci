# AI Agent False-PASS and Evidence-Divergence Taxonomy

Use this guide when an agent workflow looks successful, recoverable, or equivalent **only because one evidence source is being trusted too early**.

AgentCI uses `PASS`, `FAIL`, and `UNVERIFIED` as evidence conclusions, not as synonyms for process exit, backend status, configuration presence, or an agent saying “done.” A missing proof boundary should stay explicit instead of being promoted to success.

This page is a routing guide, not a compatibility or certification matrix.

## Quick triage

| What you observe | Failure class | Evidence that must agree before a positive claim | Safe default when it does not |
| --- | --- | --- | --- |
| “The run was accepted, but recovery sees nothing.” | admission != durable runtime evidence | external admission authority + runtime/checkpoint identity + recovery observation | `UNVERIFIED` / admission unknown |
| “Resume treated my business payload as control metadata.” | payload shape != identity authority | pending control/interrupt identities + payload identity + classification decision | ordinary data unless authority is proven |
| “Reading state locally works, but platform state is empty.” | checkpoint identity != persistence authority | checkpoint identity + persistence source used for hydration/replay | `UNVERIFIED`; do not persist a mutation derived from the bad read |
| “Checkpoint contents look equal, but behavior changes after restore.” | value equality != semantic fidelity | semantic type/constructor state + serialized representation + post-restore behavior probe | non-faithful / `UNVERIFIED` |
| “Replay picked a null/empty value as the starting point.” | storage representation != replay seed authority | ancestor materiality + ordered delta/write evidence + selected seed | keep walking or return explicit no-seed |
| “The same documented query returns different answers on two backends.” | successful execution != semantic conformance | canonical input/filter + backend identity + canonical result identity | non-conformant / `UNVERIFIED` |
| “The runtime/status API says completed, but cleanup or effects disagree.” | management state != terminal evidence | run/attempt identity + effect/cleanup/resource terminality evidence | `UNVERIFIED` until terminal evidence exists |
| “A capability is installed/configured.” | configured != effective | bounded real probe + exact route/environment/policy identity | not-ready / `UNVERIFIED` |
| “A reviewer/model recommends an action.” | observation != authority | authenticated policy/authority decision bound to subject/action/context | recommendation only |

## 1. Admission is not durable execution evidence

**Search phrases:** accepted run disappeared, background agent lost before checkpoint, resume has no state, fire-and-forget run missing.

A caller can have its own record that work was accepted while the runtime has not yet produced durable state. Conversely, an empty runtime checkpoint store does **not** prove that an external system accepted anything.

Minimum evidence tuple:

```text
external admission record identity + authority
runtime thread/run identity
first durable checkpoint observation
user/external effect observation
crash/termination boundary
fresh-process recovery result
```

Do not collapse these cases:

```text
no authoritative admission + no runtime evidence -> NOT_ADMITTED_OR_UNKNOWN
proven admission + no runtime evidence          -> ADMITTED_BUT_RUNTIME_EVIDENCE_MISSING
```

Upstream provenance example: [LangGraph #8764](https://github.com/langchain-ai/langgraph/issues/8764). The reported reproduction shows zero user effects and zero durable checkpoints; it does not provide an authoritative external admission record. That distinction is material.

## 2. Payload shape is not identity authority

**Search phrases:** resume dict ignored, interrupt resume map bug, business payload treated as control data, agent resume identity mismatch.

A payload must not gain control-plane meaning merely because its keys look like IDs. Control meaning needs a binding to identities that are actually pending for the durable state being resumed.

Minimum evidence tuple:

```text
thread/checkpoint identity
pending control/interrupt identity set
resume payload canonical shape/digest
classification decision
matched pending identities
post-resume state
```

Strong negative controls include empty maps, non-string keys, and ordinary business dictionaries whose keys happen to resemble control identifiers.

Upstream provenance example: [LangGraph #8693](https://github.com/langchain-ai/langgraph/issues/8693).

## 3. Checkpoint identity is not persistence authority

**Search phrases:** get_state empty in production, config checkpointer differs from compiled checkpointer, update_state erased messages, replay uses wrong saver.

The same logical checkpoint can be interpreted differently if hydration/replay consults a different persistence source than the one that supplied the checkpoint. A mutation derived from a false empty read can then make the bad observation durable.

Minimum evidence tuple:

```text
logical thread/checkpoint identity
persistence authority that loaded the checkpoint
persistence authority used for channel hydration/replay
pre-update state digest/count
whether ancestor replay was required
hydrated state digest/count
post-mutation head digest/count
```

A mutation must not be accepted as valid merely because the write API succeeded when its read basis came from the wrong or missing persistence authority.

Upstream provenance example: [LangGraph #8653](https://github.com/langchain-ai/langgraph/issues/8653).

## 4. Value equality is not checkpoint semantic fidelity

**Search phrases:** checkpoint restore changes type, defaultdict becomes dict, counter loses behavior after resume, replay state looks right but code breaks.

Two values can serialize to the same plain key/value projection while differing in behavior-bearing type or constructor state. A checkpoint that silently erases those semantics is not faithful merely because its JSON-like contents look equal.

Minimum evidence tuple:

```text
state field identity
pre-checkpoint semantic type identity
canonical content digest
material constructor/behavior state
serialized representation identity
restored semantic type/state
bounded behavior probe after restore
```

Upstream provenance example: [LangGraph #8184](https://github.com/langchain-ai/langgraph/issues/8184), where mapping subclasses can restore as plain dictionaries.

## 5. Storage representation is not replay-seed authority

**Search phrases:** DeltaChannel migration replay fails, checkpoint null seed, migrated thread broken, ancestor replay stops early.

A replay walker needs evidence that an ancestor actually materializes the semantic starting value. A storage-level `None`, sentinel, missing blob, or placeholder cannot become the replay seed simply because it occupies a field.

Minimum evidence tuple:

```text
migration-boundary checkpoint identity
channel semantic/version before and after migration
per-ancestor materiality observation
ordered durable writes/deltas
selected replay seed or explicit NO_SEED
reconstructed result digest
```

Upstream provenance example: [LangGraph #8686](https://github.com/langchain-ai/langgraph/issues/8686).

## 6. Successful query execution is not backend semantic conformance

**Search phrases:** SQLite store filter wrong results, memory and SQLite disagree, backend query passes but returns wrong rows, agent store false success.

“No exception” only proves the backend executed something. If two backends claim the same documented query contract, conformance is about the **canonical result identity** for the same canonical input.

Minimum evidence tuple:

```text
canonical dataset/items digest
canonical query/filter representation
backend + version identity
storage-bound parameter representation class where material
ordered result-key digest
positive and negative controls
```

Upstream provenance example: [LangGraph #8759](https://github.com/langchain-ai/langgraph/issues/8759), where operator-form complex filters can silently diverge between SQLite and in-memory stores.

## 7. Management completion is not terminal evidence

A scheduler, API, or management plane can report a task as cancelled/completed while processes, sockets, leases, child work, or external effects remain. Conversely, a caller-visible error does not prove all work rolled back.

Bind terminal claims to the same run/attempt and collect the relevant real-world evidence:

```text
run/attempt identity
last authoritative execution event
effect receipts or explicit effect absence boundary
process/resource terminality observations
cleanup receipt
bounded observation window
```

If the material terminal surface is not observable, keep the result `UNVERIFIED` rather than treating the management label as proof.

## 8. Configured capability is not effective capability

An installed executable, environment variable, policy file, backend label, or successful version probe proves configuration/discovery only. It does not prove that the requested capability works for the requested route, environment, policy, identity, or mode.

AgentCI's sandbox readiness and S1 work deliberately preserve this separation. See [the repository README](../../README.md) and [the S1 route-binding design](../architecture/s1-execution-route-binding.md).

## 9. Observation and recommendation are not authority

A model, reviewer, telemetry system, or diagnostic can observe facts and recommend actions. That output must not self-promote into permission to execute, merge, deploy, expand privilege, or certify a backend.

An authoritative decision needs an authenticated authority path bound to the exact subject/action/resource/context. AgentCI's core rule remains:

> **Observation != Authority**

## How to contribute a failure fixture

Prefer the smallest provider-neutral evidence shape that preserves the failure invariant and upstream provenance.

A useful contribution normally includes:

```text
upstream issue URL
minimal reproduction or observed evidence
exact semantic invariant
positive control
negative control
machine-readable fixture/evidence
what AgentCI independently reproduced vs did not reproduce
explicit claim boundary
```

Do not import a provider SDK into AgentCI core merely to preserve an evidence shape. Do not turn an upstream report into a compatibility/certification claim.

For a new backend/runtime evidence case, use the repository's backend evidence intake template. For a target adapter, start with [the target adapter test-plan template](target-adapter-test-plan-template.md).

## What this taxonomy does not prove

The existence of a row, fixture, upstream report, or successful AgentCI validation does **not** prove that a provider, framework, sandbox, model, or runtime is secure, correct, compatible, or certified.

Use this taxonomy to decide **what evidence is missing and which boundary must be tested next**.
