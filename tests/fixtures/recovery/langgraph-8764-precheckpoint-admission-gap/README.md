# LangGraph #8764: pre-checkpoint admission / durability gap

Status: **UNVERIFIED**. AgentCI has not independently executed this case, and LangGraph maintainers have not confirmed the intended admission/durability contract.

## Canonical provenance

This provider-neutral fixture preserves [`langchain-ai/langgraph#8764`](https://github.com/langchain-ai/langgraph/issues/8764) as the canonical source. The reproduction and scope clarification were published by [`@mstevens843`](https://github.com/mstevens843) against `langgraph==1.2.11` and `langgraph-checkpoint-sqlite==3.1.1`.

AgentCI intake: [`jinngimk-lang/agentci#159`](https://github.com/jinngimk-lang/agentci/issues/159).

## What the upstream run actually observed

The injected `SIGKILL` fires inside the first `SqliteSaver.put` before a durable checkpoint commits. The reporter later clarified the important boundary:

```text
subject exit code: -9
recovery raised: EmptyInputError: Received no input for __start__
effect count: 0
durable checkpoints: 0
```

The user node did **not** cross its file effect in the posted run. This fixture therefore does not claim a hidden or duplicated side effect.

The deterministic runtime evidence is narrower:

- process termination occurred during the first checkpoint persistence boundary;
- no durable checkpoint was observed afterward;
- no external file effect was observed;
- fresh-process `invoke(None, ...)` could not recover state and raised `EmptyInputError`.

## The admission boundary

The thread ID `accepted-run` is a correlation identifier, not evidence that an external system durably admitted the run.

The upstream issue describes the operational risk for fire-and-forget systems: an external caller may already have accepted or enqueued work while LangGraph has no durable runtime record. But the posted reproduction does not include an authoritative external acceptance ledger.

Therefore this fixture keeps admission **UNVERIFIED**. It rejects both shortcuts:

```text
zero checkpoints => NOT_ADMITTED
zero checkpoints => ADMITTED_BUT_FAILED
```

Either conclusion requires independent admission authority. If an external ledger later proves admission, the same runtime observations can support `ADMITTED_BUT_RUNTIME_EVIDENCE_MISSING`. If an authoritative ledger proves no admission, `NOT_ADMITTED` is appropriate. Without that evidence, neither is justified.

This also follows the reporter's clarification that a recovery-time failure record must be bound to authoritative accepted-run evidence; otherwise recovery could manufacture an admitted failure for a run that was never admitted.

## Validate

```bash
python -m pytest -q tests/test_langgraph_8764_admission_fixture.py
```

The focused test verifies provenance, the corrected zero-effect boundary, event ordering, the correlation-vs-authority distinction, fail-closed admission classification, and the absence of any LangGraph core dependency.

## Limitations

- AgentCI did not independently execute LangGraph for this fixture.
- The upstream issue publishes package versions but no exact Git commit; `observed_commit` is therefore explicitly unavailable.
- No external acceptance/admission ledger is included in the upstream reproduction.
- The fixture does not choose whether LangGraph should persist an accepted marker, require callers to maintain an outbox, or adopt another product contract.
- A thread ID, missing checkpoint, `EmptyInputError`, or zero effect count is not admission authority.
- This fixture is evidence for an admission/durability distinction, not a LangGraph compatibility or reliability certification.
