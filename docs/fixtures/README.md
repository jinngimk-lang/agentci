# Real upstream fixture gallery

AgentCI preserves small provider-neutral fixtures from real upstream failures so the evidence boundary can be tested without turning the upstream SDK into an AgentCI core dependency.

The upstream issue remains canonical provenance. A fixture is not a claim that AgentCI reproduced the bug, that the upstream project accepted AgentCI's framing, or that any provider/runtime is compatible, secure, or certified. Unless independent execution evidence exists, the AgentCI result stays **UNVERIFIED**.

Machine-readable index: [`tests/fixtures/index.json`](../../tests/fixtures/index.json).

## Current upstream-derived fixtures

| Upstream | Fixture | What it preserves | AgentCI state |
| --- | --- | --- | --- |
| [LangGraph #8582](https://github.com/langchain-ai/langgraph/issues/8582) | [`langgraph-8582-send-untracked`](../../tests/fixtures/replay/langgraph-8582-send-untracked/) | A failed dynamic task resumes after checkpoint recovery with a materially different input shape because a runtime dependency was intentionally untracked. The fixture distinguishes correct non-persistence from replay fidelity. | `UNVERIFIED` |
| [LangGraph #8764](https://github.com/langchain-ai/langgraph/issues/8764) | [`langgraph-8764-precheckpoint-admission-gap`](../../tests/fixtures/recovery/langgraph-8764-precheckpoint-admission-gap/) | Process death occurs before the first durable checkpoint and before the external effect. `0 checkpoints + 0 effects + EmptyInputError` does not prove admission state; admission authority is a separate evidence boundary. | `UNVERIFIED` |

## Why these cases matter

Both cases look simple if one observation is allowed to impersonate another:

- persisted state can be mistaken for faithful replay input;
- a thread ID can be mistaken for proof that a run was admitted;
- missing runtime state can be mistaken for proof that nothing was accepted;
- process/runtime success can be mistaken for complete user-visible or externally observable success.

AgentCI fixtures make those dimensions explicit so false-PASS and false-absence claims can be challenged deterministically.

## Bring an upstream bug

A strong intake usually has:

1. a canonical upstream issue;
2. a self-contained or tightly bounded reproduction;
3. one semantic invariant that can be stated without importing the whole framework;
4. exact observed evidence and exact missing evidence;
5. a claim boundary that says what remains unknown.

Start with [`docs/contributing/upstream-fixture-intake.md`](../contributing/upstream-fixture-intake.md) or [open the upstream fixture intake form](https://github.com/jinngimk-lang/agentci/issues/new?template=upstream-fixture-intake.yml).

The smallest first contribution is usually `provenance.json`, `case.json`, `trajectory.jsonl`, `README.md`, plus one focused validation test. Preserve upstream contributor credit and keep unsupported conclusions `UNVERIFIED`.
