# LangGraph #8764 — accepted-but-not-durable boundary

Canonical upstream provenance: https://github.com/langchain-ai/langgraph/issues/8764

This provider-neutral fixture preserves the evidence boundary reported upstream when a process is killed before LangGraph's first durable checkpoint is persisted.

The upstream reproduction reports:

```text
recovery raised: EmptyInputError: Received no input for __start__
effect count: 0
durable checkpoints: 0
```

## Invariant

Runtime checkpoint absence alone cannot establish whether an external system never admitted a run or admitted it before runtime evidence became durable.

The fixture therefore keeps two classifications separate:

- `NOT_ADMITTED_OR_UNKNOWN` when no authoritative external admission record is available;
- `ADMITTED_BUT_RUNTIME_EVIDENCE_MISSING` only when an authoritative external admission record independently establishes that boundary.

The upstream issue does not provide such an authoritative external admission record, so this fixture does not assert that admission occurred. AgentCI has not independently reproduced the LangGraph runtime result and keeps the case `UNVERIFIED`.

Likewise, `user_effect_count=0` does not prove that a blind retry is safe. It only records the upstream observation at the injected crash boundary.

## Negative control

A run with no authoritative external admission evidence and no durable runtime checkpoint must remain `NOT_ADMITTED_OR_UNKNOWN`; it must not be promoted to an admitted/failed state merely because a recovery lookup was attempted.

## Validate

```bash
python -m pytest -q tests/test_langgraph_8764_accepted_not_durable_fixture.py
```

This fixture adds no LangGraph runtime dependency to AgentCI core and does not certify LangGraph or any backend.
