# Contributing to AgentCI

AgentCI is an open-source reliability, evaluation, and evidence layer for AI agents and agent-native tool harnesses. Contributions are welcome from users, agent/tool builders, security researchers, benchmark authors, and maintainers.

## Good ways to contribute

You do not need to start with a large feature. High-value contributions include:

- reproduce and minimize a bug;
- add a regression test for a real failure;
- improve first-run installation or documentation;
- contribute a realistic eval case or benchmark scenario;
- improve target/harness compatibility tests;
- test a public agent CLI, MCP/tool server, or coding-agent integration;
- improve error messages or machine-readable evidence;
- review a pull request and independently reproduce its claims;
- propose a bounded research experiment with clear success/failure criteria.

For security findings, do not publish exploit-enabling details in a public issue before responsible-disclosure readiness. Open a minimal non-sensitive report or contact the maintainer privately when appropriate.

## Before starting

1. Read `README.md`.
2. For executable target work, read `docs/architecture/agent-harness-contract.md`.
3. Search existing Issues and PRs to avoid duplicates.
4. Prefer an existing issue before starting a substantial change. If no issue exists, open one describing the user problem, proposed evidence, and smallest useful scope.
5. Keep one PR focused on one problem.

The repository uses an evidence-first development model. A plausible implementation is not enough: important claims should be reproducible by another contributor.

## Local setup

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m compileall src scripts
agentci test examples/evals.yaml
```

If you change an installed CLI/target path, include an end-to-end test that installs/runs the public entrypoint from an unrelated working directory when practical. Do not rely only on `PYTHONPATH=src` for integration claims.

## Development rules

For behavior changes:

1. Restate the desired behavior as a testable claim.
2. Add or reproduce a failing test first when practical.
3. Make the smallest implementation change that satisfies the claim.
4. Run targeted tests.
5. Run the full repository validation.
6. Record exact evidence in the PR body.

Do not weaken an existing test or threshold simply to make a change pass.

For target/adapter changes:

- commands must use argv arrays rather than implicit shell interpolation;
- machine-readable JSON is the canonical agent boundary;
- malformed/unknown protocol data should fail closed;
- timeout/output/process behavior must be bounded and described truthfully;
- do not call a process boundary a sandbox unless isolation is actually implemented and verified;
- integration claims should exercise the real installed target/backend where applicable.

## Pull requests

Use the repository PR template and include:

- **WHY** — user/problem value;
- **WHAT** — bounded implementation scope;
- **ACCEPTANCE** — observable success criteria;
- **EVIDENCE** — tests, reproductions, artifacts, benchmark commands;
- **RISK** — failure modes, compatibility, security/resource considerations;
- **GROWTH ARTIFACT** — yes/no and why;
- **RELATED ISSUE** — issue/command links.

A reviewer may try to falsify the claim with adversarial inputs. That is expected and is part of the AgentCI development model.

## Benchmarks and research

A benchmark contribution should document:

- what hypothesis it tests;
- task/sample selection;
- environment and versions;
- success metric;
- failure/invalid-task handling;
- raw or canonical evidence paths;
- important limitations.

Do not present a benchmark score as product truth if the benchmark itself has not been sanity-checked.

## Public claims and project promotion

Contributors are welcome to share AgentCI and their work, but please keep public claims evidence-backed. Do not fabricate adoption, user quotes, benchmark wins, security impact, performance gains, or partnerships.

When a contribution produces a real reusable benchmark, dataset, integration, research finding, or major capability, link the canonical evidence so maintainers can decide whether it qualifies for a Growth Artifact and broader project distribution.

## New contributor path

If you want to help but do not know where to start:

1. Look for small reproducible bugs, docs friction, test gaps, or issues marked for community contribution.
2. Comment with the scope you want to take.
3. Start with a narrow PR that can be independently verified.
4. Ask questions on the relevant issue rather than silently expanding scope.

Maintainers should keep a healthy queue of newcomer-sized work and clearly separate `good first issue` tasks from deep architecture/security tasks.

## Community conduct

Be technical, specific, and respectful. Critique claims and evidence rather than people. Preserve failing evidence even when it is inconvenient to the current implementation or marketing story.
