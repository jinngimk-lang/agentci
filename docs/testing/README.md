# AgentCI Testing and Evidence Guides

Start here when a workflow, checkpoint, backend, or agent result looks correct but the evidence does not yet justify the claim.

These guides route concrete failure symptoms to the smallest next verification action. They are not a backend compatibility list and do not certify any provider, framework, sandbox, or runtime.

## Find the right guide

| If you searched for… | Start here | Next action |
| --- | --- | --- |
| agent says success but tool failed | [False-PASS and evidence-divergence taxonomy](false-pass-taxonomy.md) | identify which evidence boundary was promoted too early, then reduce a negative control |
| checkpoint resume changed state | [False-PASS and evidence-divergence taxonomy](false-pass-taxonomy.md) | bind checkpoint identity, persistence authority, replay inputs, and post-resume state |
| accepted run disappeared before checkpoint | [False-PASS and evidence-divergence taxonomy](false-pass-taxonomy.md) | separate external admission evidence from runtime durability evidence |
| resume payload treated as control metadata | [False-PASS and evidence-divergence taxonomy](false-pass-taxonomy.md) | bind pending control identities instead of trusting payload shape |
| restored state has same values but behaves differently | [False-PASS and evidence-divergence taxonomy](false-pass-taxonomy.md) | test semantic type/constructor state and one post-restore behavior probe |
| two backends return different results for the same operation | [False-PASS and evidence-divergence taxonomy](false-pass-taxonomy.md) | compare canonical input and canonical result identity before claiming conformance |
| how can an unfamiliar agent verify AgentCI from public evidence? | [External agent verification](external-agent-verification.md) | start from public discovery surfaces only and record any missing/ambiguous contract |
| how do I define acceptance for a target adapter? | [Target adapter test-plan template](target-adapter-test-plan-template.md) | bind the exact target, environment, evidence producer, negative controls, and claim boundary |

## Fast path: a result looks green but may be false

1. Open the [False-PASS taxonomy](false-pass-taxonomy.md).
2. Match the symptom to the evidence boundary, not to a provider name.
3. Record the immutable identities that matter: run/attempt, checkpoint, input/work, environment/policy, and authority where applicable.
4. Add at least one negative control that would fail if the evidence source were being trusted incorrectly.
5. Keep missing material evidence as `UNVERIFIED`; do not infer PASS from absence, configuration, process exit, or a successful API call.
6. If the failure came from an external project, preserve its public issue/PR as canonical provenance and reduce only the provider-neutral invariant needed by AgentCI.

## Released commands and claim boundaries

For the released Developer Preview, use the repository README and installed CLI help as command authority. Useful existing entry points include:

```bash
agentci test examples/evals.yaml
agentci sandbox doctor --json
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

Important distinctions:

- a successful process exit is not automatically a backend PASS;
- sandbox readiness is not execution proof;
- a valid evidence envelope is not a security certification;
- fixture replay is deterministic evidence revalidation, not rerunning a provider workload;
- an observed/recommended action is not an authoritative permission decision;
- an unreleased command described only in architecture documents must not be guessed into existence.

See the root [README](../../README.md) for current released-versus-main-only boundaries.

## Contributing a real failure

The strongest contribution is a small failure case with a falsifiable invariant rather than a general framework complaint.

Prefer this shape:

```text
public upstream provenance URL
minimal reproduction or bounded observation
exact semantic invariant
positive control
negative control
machine-readable evidence/fixture where practical
what was independently reproduced vs only reported upstream
explicit non-certification / claim boundary
```

For backend/runtime evidence, use the repository's backend evidence intake template. For a target-specific integration, use the [target adapter test-plan template](target-adapter-test-plan-template.md).

## Core rule

> Evidence may justify a claim only when it is bound to the subject, identity, environment, authority, and observation boundary that the claim actually depends on.

When that binding is missing, the useful result is usually `UNVERIFIED`, not an optimistic PASS.
