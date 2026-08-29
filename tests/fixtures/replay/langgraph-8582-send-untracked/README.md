# LangGraph #8582: `Send` + `UntrackedValue` replay fidelity

Status: **UNVERIFIED**. AgentCI has not independently executed this case, and
LangGraph maintainers have not confirmed whether the reported behavior is a
bug or an intentional limitation.

## Provenance and credit

This provider-neutral fixture preserves
[`langchain-ai/langgraph#8582`](https://github.com/langchain-ai/langgraph/issues/8582)
as the canonical source. The report and reduced reproduction were contributed
by [`@Hello-world-Prakash`](https://github.com/Hello-world-Prakash) against
LangGraph commit `d56666f7f` with `InMemorySaver`.

AgentCI intake: [`jinngimk-lang/agentci#123`](https://github.com/jinngimk-lang/agentci/issues/123).

## What the fixture records

The initial dynamic `Send` dispatch to `worker` has two material dependencies:

- tracked `messages`, present at dispatch, checkpoint, and resume;
- untracked `resource` (`RuntimeResource`), present at dispatch but absent from
  the checkpoint and resumed input.

The resource is correctly absent from the checkpoint because it was declared
with `UntrackedValue`. The fidelity problem is separate: the failed worker
remains pending and is resumed with a materially different input shape. The
fixture therefore records the observed replay as `NON_FAITHFUL` and the
AgentCI result as `UNVERIFIED`.

No runtime resource value, secret, object digest, or credential is serialized.
The SHA-256 values bind only the canonical, bounded input-shape descriptors.

## Validate

```bash
python -m pytest -q tests/test_langgraph_8582_replay_fixture.py
```

The test verifies provenance, descriptor digests, tracked/untracked presence,
event order, task-reference continuity, and the explicit `UNVERIFIED` result.
It also proves that this first fixture introduces no LangGraph core dependency.

## Limitations

- `runtime_task_id` is `null` because the upstream issue did not publish a
  stable LangGraph-issued task ID. The `logical_task_ref` is case-local and is
  not presented as an upstream identity.
- `checkpoint_id` is also `null`; the report published the thread ID and state
  snapshot, but not a stable LangGraph-issued checkpoint identifier.
- This is a provider-neutral evidence fixture, not a live LangGraph reproducer.
- The recorded target is commit `d56666f7f`; no claim is made about later
  LangGraph revisions.
- Acceptable framework behavior remains one of faithful reconstruction, an
  explicit non-resumable/error outcome, or an explicit `UNVERIFIED` outcome.
