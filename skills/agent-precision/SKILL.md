---
name: agent-precision
description: Use when an AgentCI task involves interpreting project terminology, reviewing a change against its spec, diagnosing a hard bug, researching external technical claims, or writing instructions that other agents must execute reliably.
---

# Agent Precision

Use `CONTEXT.md` as the canonical vocabulary before reasoning about AgentCI. If a request uses an overloaded term, map it to the glossary before acting.

## 1. Review on two independent axes

For a PR or bounded change, keep these separate:

- **Spec axis** — does the change actually satisfy the originating issue, acceptance criteria, and stated evidence requirements? Flag missing requirements, partial behavior, incorrect behavior, and scope creep.
- **Standards axis** — does the change respect repository contracts, safety boundaries, tests, compatibility, maintainability, and established engineering rules?

Do not let a pass on one axis hide a failure on the other. Report both verdicts explicitly.

## 2. Hard bugs require a tight red-capable loop

Before forming a strong root-cause theory, build one command/test/harness that can reproduce the user's exact symptom and distinguish red from green.

Prefer, in order: failing test → CLI fixture/repro → integration/E2E harness → differential comparison → bounded fuzz/stress loop.

Tighten the loop until it is as deterministic, fast, and specific as practical. Then minimise the repro, form falsifiable hypotheses, change one variable at a time, fix the smallest root cause, and preserve the repro as regression evidence.

A successful command is not enough; the loop must be capable of catching the specific bug.

## 3. External research uses primary evidence

For standards, APIs, model/tool releases, security changes, protocol behavior, or competitor architecture:

1. Prefer official docs, specifications, source repositories, release notes, papers, or first-party APIs.
2. Record event/release date as well as publication date when relevant.
3. Separate verified fact from inference.
4. Classify the signal: `ignore | watch | experiment | build | benchmark | security-response | growth-opportunity`.
5. Before changing roadmap, define the smallest reversible experiment and evidence that would justify adoption.

## 4. Write instructions for reliable invocation

Agent-facing documents should be concise context pointers plus task-specific rules, not duplicated encyclopedias.

- Put shared terminology in `CONTEXT.md`.
- Keep one source of truth for each policy.
- Prefer positive target behavior over long prohibition lists, while preserving essential hard guardrails.
- Use checkable completion criteria.
- Put branch-specific detail behind a clear pointer instead of loading it every cycle.
- Do not restate facts the repository/config/`--help` can cheaply reveal unless the reason or gotcha is otherwise invisible.

## 5. Completion check

Before declaring work accepted, be able to answer:

1. Which canonical term/spec governs this work?
2. What exact evidence can turn the claim red or green?
3. What did the Spec axis conclude?
4. What did the Standards axis conclude?
5. Which external claims came from primary sources?
6. What remains unproven?

If any answer is vague, the work is not precise enough yet.

## Attribution

This skill adapts engineering patterns from Matt Pocock's `mattpocock/skills` project, especially `writing-for-agents`, `code-review`, `diagnosing-bugs`, `research`, and `domain-modeling`, under the MIT License. See `skills/agent-precision/NOTICE.md`.
