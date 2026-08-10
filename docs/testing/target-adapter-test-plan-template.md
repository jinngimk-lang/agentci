# Target Adapter Test Plan Template

Use this template for every new executable/provider/tool adapter before writing production code. Keep the plan in the implementation branch and append results before asking for independent acceptance.

## 1. Adapter claim

- Target/backend:
- Public user capability enabled:
- Protocol/transport:
- Required external dependencies:
- Explicit non-goals:

## 2. Contract inventory

List planned tests before implementation:

- configuration/schema validation;
- executable/endpoint discovery;
- request serialization;
- result parsing;
- timeout/cancellation;
- process/resource bounds;
- malformed output;
- non-zero/backend error;
- backwards compatibility;
- installed-entrypoint E2E;
- real-backend E2E when applicable;
- artifact/trajectory validation when applicable.

For each category record expected test count and key edge cases.

## 3. Adversarial matrix

At minimum consider:

- empty/missing fields;
- wrong types;
- unsupported protocol/schema version;
- non-finite/extreme numeric values;
- malformed/non-UTF-8 structured output;
- oversized stdout/stderr/event lines;
- slow/hanging process;
- descendant processes after timeout;
- path traversal/symlink escapes for artifacts;
- working-directory assumptions;
- environment/secret leakage;
- duplicate/out-of-order trajectory events;
- partial writes/truncated evidence;
- target self-report contradicting an observable artifact.

Document which cases are in scope and why any case is excluded.

## 4. Real workflow E2E

Describe one realistic user workflow, not only a synthetic function call.

Workflow:

```text
install AgentCI
→ run from unrelated cwd
→ inspect/doctor target when supported
→ execute real target through public config
→ generate AgentCI evidence
→ verify canonical JSON/report/artifacts
```

Verification must check observable outputs, not only exit code.

For external integration adapters, use the actual dependency/service in a dedicated E2E job when credentials/safety permit. If that dependency is required for the integration claim, a missing dependency should make that dedicated job fail clearly rather than silently pass as covered.

## 5. TDD evidence

Record the pre-implementation RED command and failure summary:

```text
Command:
Expected failing tests:
Observed failure reason:
Commit/head:
```

Then record GREEN verification:

```text
Targeted command:
Full test command:
Syntax/type/lint command if applicable:
E2E command:
Observed results:
Commit/head:
```

## 6. Artifact verification

For each generated artifact/evidence object state:

- producer;
- expected location;
- allowed path boundary;
- format/schema verification;
- size bound;
- truthfulness check against the real execution;
- cleanup/retention semantics.

## 7. Platform assumptions

Record tested operating systems/runtime versions and behavior that is best-effort or platform-dependent. Do not generalize a Linux-only process-tree test into an unqualified cross-platform claim.

## 8. Independent falsification handoff

Provide Agent B:

- exact PR head SHA;
- exact reproduction commands;
- known limitations;
- trust/security boundary;
- highest-risk assumptions to attack;
- any result that would invalidate the feature claim.

## 9. Final results

Append after implementation:

- total tests / pass rate / runtime;
- targeted and full CI links;
- E2E evidence;
- defects found during self-review;
- remaining coverage gaps;
- Agent B findings and disposition;
- whether a Growth Artifact genuinely exists.

A passing implementation is not accepted until the evidence survives independent review or an explicit Supervisor decision.