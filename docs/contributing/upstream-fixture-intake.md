# From an upstream bug to an AgentCI fixture

This path is for an upstream issue author, maintainer, or reproducer who already has a concrete agent-runtime failure and wants to preserve it as a small, provider-neutral verification fixture.

The upstream issue stays canonical. AgentCI does not need to copy the upstream implementation, decide the upstream product contract, or claim the behavior is a confirmed bug before maintainers do.

## Good fit

A strong intake usually has most of these properties:

- a minimal or tightly bounded reproduction;
- a semantic failure that can be stated without depending on one provider SDK;
- a mismatch between two facts that should not be collapsed, such as replay vs changed input, runtime success vs durable evidence, delivery ACK vs content completeness, terminal refusal vs retry authority, or process liveness vs observer-path liveness;
- a clear negative control;
- an upstream issue URL and exact version/commit when known.

If important evidence is missing, `UNVERIFIED` is an acceptable outcome. Do not fill gaps with assumptions.

## Smallest useful first contribution

Start with one directory:

```text
tests/fixtures/<class>/<upstream-project>-<issue-number>-<short-name>/
  provenance.json
  case.json
  trajectory.jsonl
  README.md
```

The first PR should normally contain those four files plus one focused validation test. Do not add the upstream project as an AgentCI core dependency just to preserve the fixture.

### `provenance.json`

Record only source facts:

- upstream repository and issue URL;
- reporter/contributor credit;
- exact upstream commit/version when known;
- capture date;
- upstream issue state at capture;
- AgentCI reproduction status, initially `UNVERIFIED` unless independently reproduced.

### `case.json`

Describe the provider-neutral semantic case:

- actors/objects that matter;
- initial conditions;
- the consequential transition;
- observations before and after it;
- acceptable outcomes;
- the exact failure condition.

Do not serialize secrets, credentials, opaque runtime resources, or provider-private state. When a material dependency cannot be serialized safely, describe only the bounded properties needed for the claim, such as name, tracking state, presence, or type.

### `trajectory.jsonl`

Preserve the smallest ordered evidence trace needed to falsify the claim. Use upstream-issued identities when they exist. If they do not, a case-local reference may correlate rows but must not be presented as an upstream-issued identity.

### `README.md`

State:

- exact upstream provenance and contributor credit;
- the falsifiable invariant;
- validation command(s);
- what the fixture can and cannot prove;
- why any material claim remains `UNVERIFIED`.

## Contribution boundary

Prefer this sequence:

```text
upstream issue
→ AgentCI intake issue
→ provider-neutral fixture
→ focused validator/test
→ independent reproduction or challenge
→ stronger claim only if evidence supports it
```

The intake issue is a handoff surface after a qualified upstream failure exists; it is not the acquisition channel itself. Keep discussion of the original product behavior in the upstream issue whenever possible.

## Example that converted into a contribution

LangGraph issue #8582 became AgentCI intake #123 and then external PR #124. The successful handoff kept LangGraph #8582 as canonical provenance, asked for a four-file provider-neutral fixture, avoided a LangGraph core dependency, and kept AgentCI status `UNVERIFIED` until independent reproduction.

- Upstream: https://github.com/langchain-ai/langgraph/issues/8582
- AgentCI intake: https://github.com/jinngimk-lang/agentci/issues/123
- Contributed fixture PR: https://github.com/jinngimk-lang/agentci/pull/124

Use that shape as a starting point, not as a requirement that every failure be a replay bug.

## What not to claim

A merged fixture does **not** by itself establish:

- upstream product correctness or incorrectness;
- provider compatibility;
- production prevalence;
- security certification;
- independent reproduction;
- permission to replay, retry, restore, or reapply a side effect.

The fixture should make unsupported conclusions harder, not easier.
