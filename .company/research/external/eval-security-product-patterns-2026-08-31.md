# External Eval / Security Product Patterns — 2026-08-31

Status: evidence-backed product scan
Purpose: identify transferable product, activation, corpus, and verification patterns without cloning project identity or importing unnecessary dependencies.

## Decision summary

The strongest cross-project signal is not “AgentCI needs more features.” It is that mature adjacent tools make their existing capability **easy to discover, select, run, and inspect**.

AgentCI's strongest differentiation remains fail-closed evidence semantics, identity/authority binding, and refusal to turn configuration into proof. The immediate gap is the activation/corpus layer around that verifier core.

Recommended classifications:

| Project | License observed | Transferable pattern | AgentCI classification |
| --- | --- | --- | --- |
| `promptfoo/promptfoo` | MIT | extremely short init/eval/view loop; local result inspection; declarative selection | `adopt-now` as activation pattern; no dependency |
| `UKGovernmentBEIS/inspect_ai` | MIT | large prebuilt eval corpus; extension model; strong agent-facing doc indexes | `adopt-now` for corpus/discovery pattern; `watch` integration |
| `ethz-spylab/agentdojo` | MIT | task suite × attack × defense benchmark matrix; public result browsing | `benchmark` + `adopt-now` corpus taxonomy ideas |
| `modelcontextprotocol/inspector` | MIT in root package metadata | one shared core exposed through Web/CLI/TUI; real composable test servers; showcase configs | `adopt-now` for showcase/real-fixture pattern; `watch` UI |
| `NVIDIA/garak` | Apache-2.0 | enumerated probe catalog; category selection; machine-readable run logs | `adopt-now` for catalog/selective-run pattern; `benchmark` for security coverage |

No source code from these projects is required for the current recommendation. Prefer independent AgentCI implementations of the transferable patterns. If code or data is later copied or adapted, inspect the exact source path/license/NOTICE obligations first and update `THIRD_PARTY_NOTICES.md` as required.

## 1. Promptfoo

Source: https://github.com/promptfoo/promptfoo
Observed license: MIT.

### Relevant pattern

The README makes first success legible in a few commands:

```text
install
→ init an example
→ eval
→ view
```

It also keeps evaluation, red teaming, comparison, CI/CD, and result viewing close to the primary entry point.

### AgentCI gap exposed

AgentCI currently has real commands and canonical examples, but a newcomer must understand several evidence concepts before they know which example answers their problem. The first-run path is technically valid but cognitively expensive.

### Decision: `adopt-now`

Adopt the activation principle, not the implementation:

- one cheap discovery path that lists runnable AgentCI showcase cases;
- one exact command per case/category;
- expected artifact/verdict/claim boundary visible before execution;
- a short “first useful result” path that does not require architecture-document reading.

Do not add a JS dependency or copy Promptfoo's provider matrix merely to look feature-complete.

## 2. Inspect AI

Source: https://github.com/UKGovernmentBEIS/inspect_ai
Observed license: MIT.

### Relevant pattern

Inspect exposes a large ready-to-run evaluation collection and publishes dedicated agent-discovery documentation surfaces (`llms.txt`, guide/full variants, Markdown-friendly pages). Its extension model allows capability growth without making every extension part of core.

### AgentCI gap exposed

AgentCI already has `llms.txt` and an agent skill, so the discovery principle is partly implemented. The bigger missing layer is a **dense, queryable corpus index**: what fixtures/cases exist, which semantic class they cover, whether they are fixture-only or independently reproduced, and how to run/validate them.

### Decision: `adopt-now` + `watch`

- Strengthen the machine-readable corpus index and cross-link it from `llms.txt`/README when the catalog exists.
- Keep optional adapters/extensions outside core when possible.
- Do not chase “hundreds of evals” as a vanity count; every AgentCI corpus item must preserve provenance and evidence state.

## 3. AgentDojo

Source: https://github.com/ethz-spylab/agentdojo
Observed license: MIT.

### Relevant pattern

AgentDojo presents benchmark work as combinations of suites/tasks, attacks, defenses, models, and results. The user can ask a concrete question and select a bounded slice rather than running an opaque monolith.

### AgentCI gap exposed

AgentCI's fixtures are increasingly valuable, but semantic categories are not yet a first-class browsing/selection experience. Replay fidelity, cleanup/terminality, authority confusion, route binding, residual-resource state, and false-PASS controls should be discoverable as explicit classes.

### Decision: `benchmark` + `adopt-now`

Adopt a taxonomy suited to AgentCI rather than copying AgentDojo's attack model:

```text
semantic class
→ provenance
→ evidence maturity
→ runnable validation command
→ expected/acceptable outcomes
→ claim boundary
```

Potential categories: replay/restore, cleanup/terminality, route/identity binding, authority/policy, resource enforcement, serialization/state integrity, capability drift, and false-PASS controls.

## 4. MCP Inspector

Source: https://github.com/modelcontextprotocol/inspector
Observed license: MIT in root `package.json`.

### Relevant pattern

The current Inspector line uses a shared inspection core across Web, CLI, and TUI. More important for AgentCI, it maintains **real composable test servers and showcase configs** for concrete protocol behaviors, with smoke/integration paths that exercise real transports rather than relying only on mocks.

### AgentCI gap exposed

AgentCI has many rigorous fixtures and tests but does not yet turn them into an obvious showcase surface. A user should be able to see “here are the exact semantic failures AgentCI knows how to challenge” without reading the test tree.

### Decision: `adopt-now` for fixture/showcase architecture; `watch` UI

- Build a catalog over canonical examples/fixtures.
- Preserve real subprocess/transport testing where AgentCI has executable targets/backends.
- Treat a future UI as secondary; first make the catalog correct and useful from CLI/JSON/docs.
- Keep one semantic source of truth so any later CLI/TUI/Web surface cannot drift into separate verdict logic.

## 5. garak

Source: https://github.com/NVIDIA/garak
Observed license: Apache-2.0.

### Relevant pattern

Garak exposes an explicit probe catalog, lets users list/select probe families, and keeps detailed run evidence in logs/JSONL. Its model generator matrix is broad, but the more durable pattern is **enumerability + selective execution + machine-readable run history**.

### AgentCI gap exposed

AgentCI has strong individual evidence contracts but weaker user-facing enumeration. A user/agent should be able to discover available semantic probes/cases and choose a bounded category without memorizing file paths.

### Decision: `adopt-now` for catalog semantics; `benchmark` for security breadth

Candidate AgentCI behavior for a later bounded implementation:

```text
agentci showcase list [--json]
agentci showcase show <id> [--json]
```

A run command should only be added when it can delegate to already-released canonical validation/eval paths without introducing a second verdict engine. Exact command naming remains an implementation decision and must be tested before public documentation.

## Cross-project synthesis

The recurring pattern is:

```text
catalog / examples
→ select a bounded case
→ run one obvious command
→ inspect structured result
→ compare or reproduce
→ contribute another case
```

AgentCI already owns the harder trust problem underneath that loop. The next product advantage is to expose the verifier corpus without weakening it.

## Proposed AgentCI product shape

### P1: machine-readable showcase / fixture catalog

Each entry should be derived from repository truth and include at least:

- stable AgentCI case ID;
- title/semantic class;
- source/provenance URL when external;
- evidence maturity (`fixture`, `UNVERIFIED external report`, `independently reproduced`, etc.);
- canonical local paths;
- exact currently released command(s) that validate/run it;
- expected/acceptable outcome semantics;
- whether a result is a fixture validation, real execution observation, or other evidence type;
- explicit certification/compatibility claim boundary.

The catalog must be generated or contract-tested against actual files so it cannot become a marketing-only inventory.

### P1: human + agent discovery

Once the catalog exists:

- link a concise showcase section from README;
- add compact machine discovery to `llms.txt` / `skills/agentci/SKILL.md`;
- make the first useful command obvious;
- keep architecture docs as deeper progressive disclosure, not a prerequisite for first success.

### P2: contribution conversion

External outreach should be able to point to one canonical “contribute a breaker” format. The successful LangGraph #8582 → AgentCI #124 funnel is the reference: upstream provenance preserved, fixture scope bounded, no provider dependency, and explicit `UNVERIFIED` state until independent reproduction.

### Experiment: real backend execution

Do not confuse corpus discoverability with backend support. The real-backend experiment remains separate and must preserve independent route observations and cross-backend semantic comparability.

## Explicit non-goals from this scan

Do not:

- clone Promptfoo's provider breadth;
- chase Inspect's corpus size without evidence quality;
- convert AgentCI into an attack-benchmark-only product;
- build a web dashboard before the underlying catalog/activation path is useful;
- import MCP Inspector, garak, or another large framework as a core dependency merely to claim coverage;
- create a second verdict engine for showcase convenience;
- claim benchmark/security superiority without independent measurements.

## Follow-up validation

A future implementation of the showcase catalog should be falsified against:

1. stale/missing referenced files;
2. unknown category or maturity values;
3. a catalog entry that claims a command not exposed by the installed CLI;
4. an external provenance entry with no source URL;
5. a real-execution claim backed only by a fixture;
6. duplicate IDs;
7. deterministic JSON ordering/output where machine consumption depends on it;
8. installed-entrypoint use from an unrelated working directory.

If those checks cannot be made reliable, keep the catalog as a docs-only experiment rather than a product command.
