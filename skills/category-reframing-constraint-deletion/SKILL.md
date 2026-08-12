---
name: category-reframing-constraint-deletion
description: Use when a product or strategy is trapped in incremental competition on an accepted industry interface, artifact, workflow, metric, or constraint and may need a category-level rethink.
---

# Category Reframing Through Constraint Deletion

## Overview

Use this skill to detect when a team is improving the **wrong competition axis**.

The core question is not:

> How do we make the current thing better?

It is:

> Which thing does the industry assume must exist — but may only be an inherited artifact?

Then ask:

> If that artifact disappeared, what new product architecture would become possible?

This is not “be radical for the sake of novelty.” It is a disciplined method for separating the user’s real job from historical interfaces, inherited technical assumptions, and incumbent competition rules.

Chinese shorthand:

> **不要只做更好的键盘。先问：键盘为什么必须存在？**

---

## Historical Anchor: What the iPhone Example Actually Teaches

The important discontinuity happened with the **original iPhone in 2007**, not the iPhone 3GS in 2009.

Apple’s 2007 launch described a new interface based on a **large Multi-Touch display** and software controlled directly by fingers. The strategic shift was not merely “a nicer phone.” It moved the primary interaction surface away from the fixed physical-keyboard-centric model toward a dynamic software-defined surface.

The iPhone 3GS, introduced in 2009, was already an improvement **inside that new paradigm**: faster performance, better camera, video recording, voice control, and software improvements.

So the reusable lesson is:

```text
old category:
optimize the fixed interface

category reframing:
remove the fixed interface
→ move its function into a more general substrate
→ let software redefine the surface dynamically
```

Do not over-literalize the story. The original iPhone still had some physical buttons. The important move was the removal of the **traditional hardware keyboard as the dominant front-face interaction model**, not the magical removal of every piece of hardware.

---

## The Core Pattern

Most industries develop a **dominant competition axis**.

Examples:

```text
phones      → better keyboard / hinge / keypad / form factor
cloud       → faster VM startup
security    → more configuration knobs
AI agents   → more approvals / more tools / more prompts
sandboxes   → better runtime / faster provisioning / more provider features
```

Once an axis becomes normal, teams stop asking whether the axis itself is necessary.

They ask:

```text
How do we make X 10% better?
```

instead of:

```text
Why does X exist?
What user job was X originally solving?
Could that job move somewhere else?
What becomes possible if X disappears?
```

This skill calls that move **constraint deletion**.

---

# 1. Map the Competition Axis

Before ideating features, write down what the industry appears to compete on.

Use this table:

| Question | Answer |
|---|---|
| What do most competitors advertise? | |
| What do buyers compare in tables? | |
| What do reviewers benchmark? | |
| What do engineers spend time tuning? | |
| What features keep getting more knobs? | |
| What does everyone assume is mandatory? | |

The repeated answers reveal the current **competition axis**.

A competition axis may be useful — or it may be a historical trap.

---

# 2. Identify the Inherited Artifact

An **inherited artifact** is a product element that exists because of history, not because the user directly values the artifact itself.

Examples:

```text
physical keyboard
manual configuration screen
provider-specific policy syntax
approval popup
deployment manifest
security dashboard
runtime selector
multi-step setup wizard
```

Ask:

1. Does the user want this artifact, or only the outcome it enables?
2. If the artifact vanished, would the user still want the underlying outcome?
3. Is the artifact carrying real safety/capability, or merely exposing implementation detail?
4. Is it mandatory because of physics/security/law — or because the category grew around it?

Do not delete a true invariant just because it is inconvenient.

---

# 3. Separate the Job From the Artifact

Write two sentences.

Bad framing:

> Developers need an easier sandbox policy editor.

Better framing:

> Developers need an agent to accomplish an authorized task without gaining unintended authority.

Bad framing:

> Users need a better keyboard.

Better framing:

> Users need to enter text, navigate, communicate, and control applications efficiently.

The first sentence describes the inherited artifact.
The second describes the **job**.

Only redesign after the job is clear.

---

# 4. Run the Constraint-Deletion Question

Temporarily make the artifact illegal.

Ask:

> If we were forbidden from shipping X, how would we still deliver the user’s job?

Examples:

```text
No physical keyboard allowed.
No sandbox-provider selector allowed.
No security-policy editor allowed.
No repeated approval popup allowed.
No manual evidence review allowed.
No user knowledge of backend-specific syntax allowed.
```

This is a reasoning device, not an immediate product decision.

The purpose is to force architecture out of a local optimum.

---

# 5. Reassign the Artifact’s Functions

Every artifact performs functions. Before deleting it, enumerate them.

Example: a physical keyboard may provide:

```text
text entry
shortcuts
navigation
feedback
muscle memory
application commands
```

Removing the keyboard only works if those functions move elsewhere.

The original iPhone pattern was powerful because a more general substrate — a large software-defined touch surface — could change its interface by context.

General rule:

> **Delete the artifact only when a more general substrate can absorb its useful functions.**

Candidate substrates include:

```text
software
automation
policy compilation
intent declaration
dynamic UI
agent orchestration
evidence
protocols
inference
hardware abstraction
platform primitives
```

---

# 6. Use the ERRC Lens

For a candidate category reframe, complete all four:

## Eliminate

Which factor that the industry has long competed on should disappear from the user’s normal workflow?

## Reduce

Which complexity, configuration, cognitive load, latency, or dependency should become dramatically smaller?

## Raise

Which property should become substantially stronger than the industry standard?

## Create

What new capability or category becomes possible only after the old artifact is removed?

A useful reframe usually changes several axes at once.

---

# 7. The “Full-Screen” Test

A strong category-level idea has this shape:

```text
old world:
user manipulates implementation detail

new world:
user expresses intent / desired outcome
system dynamically provides the interface or mechanism
```

Ask:

1. What can become invisible?
2. What can become software-defined?
3. What can become provider-neutral?
4. What can become automatic but still deterministic?
5. What can move from configuration to verification?
6. What can become a proof instead of a promise?

This is the **full-screen test**: does removing the old fixed surface create a more general dynamic surface?

---

# 8. The Proof Test: Novelty Is Not Enough

Constraint deletion is useful only if it improves the actual job.

A proposal must survive these tests:

```text
Utility:       Does the user still accomplish the intended job?
Safety:        Did we remove an interface, or accidentally remove a safety invariant?
Generality:    Can the new substrate serve more situations than the old artifact?
Simplicity:    Is complexity truly removed, or merely hidden downstream?
Verifiability: Can we prove the new system does what it claims?
Adoption:      Can a new user understand and use the new model?
Migration:     Can users move from the old category without unacceptable cost?
```

If the proposal fails utility or safety, it is not a breakthrough. It is subtraction theater.

---

# 9. Competence-Destroying vs Competence-Enhancing Questions

Some innovations improve the incumbent system.
Others invalidate the knowledge and structure built around the old system.

Ask:

```text
If this idea wins,
which existing expertise becomes less central?
which comparison tables become irrelevant?
which incumbent advantage stops mattering?
```

This is useful because a true category reframe often looks wrong from the old scorecard.

Do not use old-category metrics as the only evaluation system for a new-category hypothesis.

---

# 10. The AgentCI Application

## Current Sandbox Industry Competition Axis

Much of the sandbox ecosystem competes on things such as:

```text
runtime isolation
microVM/container choice
startup latency
snapshots
CLI/SDK ergonomics
filesystem controls
network policy
credential handling
persistence
observability
provider integrations
```

These are real and valuable capabilities.

But AgentCI should ask a different question:

> **Why must the developer personally understand, choose, configure, and trust all of these implementation details?**

That may be our industry’s “physical keyboard.”

---

## Candidate Inherited Artifacts for AgentCI to Challenge

Potential inherited artifacts:

```text
1. explicit sandbox-provider choice
2. provider-specific policy syntax
3. manual capability allowlists as the primary UX
4. static sandbox profiles authored by hand
5. configuration treated as proof
6. backend labels treated as security meaning
7. repeated approval prompts for routine bounded actions
8. security reports that describe settings instead of effective behavior
9. developers manually reconciling identity, credentials, network, process, and lifecycle controls
```

Do not delete them blindly.
Treat each as a hypothesis.

---

# 11. The Strong AgentCI Reframe: Verified Execution

A possible category-level direction is:

> **The user should request an authorized outcome, not configure a sandbox.**

Strategic hypothesis:

```text
OLD:
choose sandbox
→ configure provider policy
→ inject credentials
→ run agent
→ inspect logs
→ hope the boundary held

NEW:
declare task intent + authorized utility + non-negotiable constraints
→ AgentCI derives/proposes the minimum execution contract
→ deterministic authority validates what is allowed
→ backend adapter compiles/maps the contract
→ execution runs on an available substrate
→ AgentCI adversarially verifies the effective boundary
→ every run emits a proof-bearing execution receipt
```

Working category names:

```text
Verified Agent Execution
Proof-Bearing Agent Execution
Execution Boundary Compiler
Agent Execution Contract
Verified Execution Layer
```

These are strategic names, not released-product claims.

---

# 12. What AgentCI Could “Delete”

The most important deletion may not be the sandbox itself.

It may be the user-facing requirement to reason about the sandbox.

Potential “delete” move:

```text
DELETE from normal user workflow:
- provider-specific security vocabulary
- manual backend comparison
- static policy authoring for common tasks
- trust in configuration screenshots
- interpreting raw security telemetry

KEEP underneath:
- real deterministic enforcement
- explicit authority
- policy epochs
- credential boundaries
- network enforcement
- runtime isolation
- telemetry
- adversarial verification
```

This distinction is critical:

> **Delete cognitive interface, not enforcement.**

---

# 13. AgentCI’s Possible “Dynamic Screen”

The equivalent of the dynamic software surface could be a provider-neutral **Task / Execution Contract**.

Conceptual input:

```yaml
intent:
  outcome: "fix tests and open a PR"

authorized_utility:
  workspace:
    read: true
    write: true
  git:
    commit: true
    push_branch: true
    merge_main: false
  network:
    package_registry: true
    arbitrary_internet: false

forbidden:
  - read_host_secrets
  - access_cloud_metadata
  - use_raw_host_credentials
  - modify_repository_admin_settings

limits:
  wall_clock_seconds: 900
  max_processes: 64
```

The user thinks in terms of **task and authority**.

The system translates that into provider/runtime mechanisms.

This is only a strategic example. The actual contract must emerge from evidence and experiments.

---

# 14. AI Must Not Become the New Physical Keyboard

A dangerous failure mode is replacing manual sandbox configuration with:

> “The model decides what permissions it needs.”

That is not category innovation. It is authority collapse.

Preserve:

> **Observation != Authority**

AI may:

```text
infer task requirements
propose minimum capabilities
identify drift
suggest tighter policy
explain evidence
```

AI may not unilaterally:

```text
grant itself network
unlock credentials
expand filesystem scope
add privileged devices
bypass external authority
convert missing evidence into PASS
```

For AgentCI, the discontinuity must remove configuration burden **without removing independent authority**.

---

# 15. Authorized Utility Is the Replacement for Feature Checklists

A sandbox that denies everything is secure but useless.

A new-category execution system must optimize for:

```text
containment
+
authorized utility
```

Therefore every category-reframing proposal for AgentCI should ask:

1. What useful work must still succeed?
2. What authority is genuinely required?
3. What should be impossible?
4. What evidence proves both sides?

Do not reward a product for becoming safer by making the agent unable to do the job.

---

# 16. Strategic Falsification Tests for “Verified Execution”

Before treating the reframe as real, require evidence such as:

```text
1. The same task/authority intent can map to >=2 materially different backends.
2. The user does not need provider-specific security syntax for the common path.
3. A backend can be changed without changing the semantic security intent.
4. Missing effective-policy evidence yields UNVERIFIED, not PASS.
5. Provider claims/configuration alone cannot create certification.
6. A deliberately permissive control fails the same semantic checks.
7. Authorized utility still succeeds under the derived contract.
8. The system refuses execution when no safe backend mapping exists.
9. Privilege expansion still requires an external authenticated authority path.
10. A proof-bearing receipt binds task, authority, backend, effective policy, evidence, and verdict.
```

Until these exist, “Verified Execution” remains a strategic hypothesis.

---

# 17. The Competition-Axis Inversion Exercise

For any roadmap discussion, fill this out:

```text
Industry optimizes:

Users actually need:

Inherited artifact:

If artifact were forbidden:

Functions artifact currently provides:

New substrate that could absorb those functions:

ELIMINATE:
REDUCE:
RAISE:
CREATE:

New category statement:

Old metrics that become misleading:

New evidence needed:

Most dangerous failure mode:

Smallest falsifiable experiment:
```

Do not move directly from “new category statement” to implementation.
Run the smallest falsifiable experiment first.

---

# 18. When to Use This Skill in the Agent Loop

Use this skill before:

```text
major product roadmap changes
new product category definitions
large UI/configuration surfaces
provider abstraction decisions
platform strategy
new security workflow design
new agent permission UX
new “AI-native” product concepts
```

Pair it with:

```text
External User / Finder
→ category-reframing analysis
→ falsifiable strategic claim
→ Planner
→ bounded experiment
→ Challenger
→ evidence
→ keep / narrow / reject
```

This skill creates strategic hypotheses.
It does not bypass the normal closed-loop delivery or evidence gates.

---

# 19. Common Mistakes

## Mistake: “Remove things = innovation”

Wrong.

Deletion only matters when useful functions move to a better substrate.

## Mistake: Copying Apple aesthetics

The lesson is not “use touchscreens” or “remove buttons.”
The lesson is to challenge inherited category assumptions.

## Mistake: Hidden complexity

If the user loses a configuration screen but operators now maintain a much more fragile hidden system, complexity was displaced, not eliminated.

## Mistake: Deleting security controls

Never confuse eliminating a user-facing security burden with eliminating enforcement, authority, or evidence.

## Mistake: Calling every successful product disruptive

Use “category reframe” or “constraint deletion” unless the evidence actually supports a stronger innovation-theory claim.

## Mistake: Old metrics only

A new category may initially look worse on incumbent benchmarks while being dramatically better on the user’s real job.

## Mistake: Big-bang implementation

The idea may be radical; the experiment should still be small and falsifiable.

---

# 20. Decision Rule

A candidate category reframe is worth serious investment when all are true:

```text
A. The competition axis is widely accepted.
B. The artifact is not itself the user’s job.
C. Its useful functions can move to a more general substrate.
D. The new model removes meaningful cognitive/operational cost.
E. Safety and authority invariants survive.
F. The new model creates capabilities the old category could not express well.
G. A bounded experiment can falsify the thesis.
```

If C, E, or G is false, do not commit to the reframe yet.

---

# 21. Agent Prompt

When using this skill, reason in this order:

```text
1. What is the industry optimizing?
2. What is the user actually trying to accomplish?
3. Which competition axis is being mistaken for the user job?
4. Which artifact appears mandatory only because of history?
5. What breaks if we delete it?
6. What more general substrate could absorb its useful functions?
7. What should be eliminated/reduced/raised/created?
8. Which safety or authority invariants must remain deterministic?
9. What new category becomes possible?
10. What smallest experiment could prove the idea wrong?
```

Output at least:

```text
Current competition axis
Inherited artifact
Underlying job
Constraint-deletion hypothesis
New substrate
ERRC
New category statement
Critical invariants
Counterarguments
Smallest falsifiable experiment
Decision: EXPERIMENT | NARROW | REJECT | WATCH
```

---

# 22. Source Anchors

Historical and strategic anchors used to derive this skill:

- Apple, **“Apple Reinvents the Phone with iPhone”**, January 9, 2007 — original iPhone introduced a new user interface built around a large Multi-Touch display and direct finger control.
- Apple, **“Apple Announces the New iPhone 3GS — The Fastest, Most Powerful iPhone Yet”**, June 8, 2009 — shows 3GS as an improvement inside the already-established iPhone paradigm.
- W. Chan Kim and Renée Mauborgne, **Eliminate-Reduce-Raise-Create Grid / Blue Ocean Strategy** — asks which long-competed-on factors should be eliminated, reduced, raised, or created.
- Michael L. Tushman and Philip Anderson, **“Technological Discontinuities and Organizational Environments”** (1986) — distinguishes incremental periods from technological discontinuities that can destroy incumbent competence.
- Rebecca Henderson and Kim Clark, **“Architectural Innovation”** (1990) — explains how changes in product architecture can invalidate embedded incumbent knowledge even when individual components are familiar.

These sources are reasoning anchors, not proof that every proposed category reframe will succeed.

---

# Final Principle

> **Do not ask only how to win the existing game. Ask which rule, interface, artifact, or comparison axis can disappear so the user gets the job more directly.**

For AgentCI specifically:

> **The breakthrough may not be a better sandbox. It may be making “choosing and configuring a sandbox” disappear from the normal developer experience, while making effective authority and containment more provable than before.**
