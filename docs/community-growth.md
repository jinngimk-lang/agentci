# Open-Source Community & Distribution Loop

AgentCI is open source. Growth is not only traffic acquisition: the project should convert attention into users, contributors, reproducible evidence, and stronger product feedback.

## Core loop

```text
verified engineering/research result
→ Growth Artifact
→ GitHub-native distribution + platform-native distribution
→ repository visit
→ install / first successful run
→ issue / question / integration request
→ contributor onboarding
→ PR / benchmark / reproduction
→ Agent A implementation + Agent B verification
→ stronger product
→ next verified result
```

Do not publish merely because a schedule says content is due. Distribution still requires a valid Growth Artifact under `.company/growth/rules.yaml` and the current authorization phase.

## GitHub-native growth

GitHub is both the product surface and the first distribution channel. Maintain:

- a README that explains the problem, quickstart, current maturity, and contribution path;
- `CONTRIBUTING.md` with reproducible setup and evidence rules;
- useful issue templates for bugs/features/research/benchmarks;
- a visible queue of newcomer-sized tasks using `good first issue` / `help wanted` when repository permissions support labels;
- release notes for meaningful milestones;
- Discussions when the repository enables them, for questions, ideas, integrations, benchmarks, and show-and-tell;
- public benchmark/research artifacts that users can reproduce;
- links from Growth Artifacts back to the exact issue/PR/commit/evidence.

Do not manufacture issues just to appear active. A `good first issue` should be bounded, useful, and verifiable by a new contributor without hidden repository context.

## Contributor funnel

Track the community funnel qualitatively first, and quantitatively only when data is real:

```text
repository visitor
→ README/quickstart understood
→ successful first run
→ issue/discussion interaction
→ first contribution claim
→ first PR
→ PR independently verified
→ merged contributor
→ repeat contributor / adapter maintainer
```

Useful signals include:

- repeated installation friction;
- unanswered questions;
- time from contributor interest to first useful PR;
- number of externally reported reproducible defects;
- externally contributed eval cases/adapters/benchmarks;
- repeat contributors;
- integrations requested by multiple independent users.

Stars/forks are discovery signals, not proof of product adoption.

## Platform distribution matrix

Only use platforms that fit the artifact and current authorization policy.

### GitHub

- README / Releases / Discussions / Issues
- reproducible demo repository paths
- benchmark/dataset artifacts
- contribution invitations tied to concrete open work

### Developer communities

- Hacker News for novel technical tools/research
- Reddit communities when self-promotion rules permit and the post teaches methodology/results first
- Dev.to for reproducible tutorials/engineering lessons
- relevant technical forums and open-source communities

### Professional / founder

- X for concise verified results, charts, demos, and contributor calls
- LinkedIn for engineering/business implications and open-source collaboration
- Product Hunt only for a launch-quality milestone

### Long-form / owned

- project technical blog
- Medium when long-form distribution adds reach rather than duplicating the canonical post
- newsletter/email only for opted-in audiences

### Video / visual

- YouTube walkthroughs for benchmarks, architecture, demos, contributor guides
- Shorts/TikTok/Reels only when a real visual result can be shown accurately
- GIFs/social cards generated from real evidence

## Platform-native contributor calls

A contributor CTA should state what kind of help is actually needed. Examples:

- "Help us add adversarial cases for local-command targets."
- "We need 3 maintainers of public agent CLIs/MCP servers to try the harness conformance experiment."
- "Contribute a reproducible eval case that caught a real regression."
- "Test the installed AgentCI entrypoint on Windows/macOS/Linux and report exact evidence."

Avoid generic "contributors wanted" posts with no bounded entry point.

## Agent A responsibilities

Agent A should:

- keep quickstart and contributor setup working;
- fix activation friction discovered by external users;
- create bounded community-sized issues from verified gaps;
- respond to external PR evidence technically;
- avoid rewriting contributor work unless necessary—prefer reviewable guidance;
- convert recurring community pain into product priorities.

## Agent B responsibilities

Agent B should:

- independently verify externally contributed technical claims using the same standards as Agent A claims;
- identify Growth Artifacts that are useful to a specific developer community;
- prepare platform-native drafts plus a concrete contributor CTA when appropriate;
- check community/self-promotion rules before recommending a platform;
- measure qualified downstream behavior rather than raw impressions;
- surface useful external criticism, bug reports, and benchmark challenges back to the Supervisor.

## Supervisor responsibilities

During inspection, the Supervisor should consider both product and community health:

1. Is there a real result worth sharing?
2. Is the first-run path ready for incoming users?
3. Is there at least one bounded contribution path for interested developers?
4. Are external issues/PRs/questions being answered with evidence?
5. Which platform/audience specifically benefits from the current artifact?
6. Did prior distribution produce installs, successful runs, bugs, integration requests, or contributors?
7. Should Agent A improve onboarding before the next campaign?

When a real Growth Artifact exists, the default campaign should include a GitHub-native update and, when useful, an explicit invitation for reproducible testing/contribution.

## Safety and integrity

Never:

- fabricate contributors, users, stars, testimonials, benchmarks, or community demand;
- spam unrelated repositories/issues/communities;
- impersonate independent users;
- use automated replies to flood discussions;
- hide valid criticism because it hurts promotion;
- expose actionable security details before responsible disclosure;
- promise maintainership, roadmap commitments, or commercial terms without authorization.

The objective is a credible open-source flywheel: useful engineering creates useful public evidence; public evidence attracts real users and contributors; their evidence improves the product.
