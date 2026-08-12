# AgentCI Agent Entry Point

Use this file as a lightweight context router.

- **Always read `CONTEXT.md`** before interpreting AgentCI terminology or introducing new domain language.
- **Always read `skills/autonomous-owner-multi-agent-master/SKILL.md`** when operating, supervising, researching, improving, publishing, or growing this project. It is the consolidated owner operating policy.
- **Always read `skills/owner-autonomous-project-operator/SKILL.md`** when operating, supervising, researching, improving, publishing, or growing this project.
- **Read `skills/proactive-open-source-adoption/SKILL.md`** when scanning GitHub/open-source ecosystems for useful skills/projects, evaluating whether to adopt an external pattern, deploying a reversible external-inspired improvement, or deciding whether a new dependency/integration should be experiment/benchmark/watch/reject.
- **Read `skills/agent-precision/SKILL.md`** when reviewing changes, diagnosing hard bugs, researching external technical claims, or writing/editing agent-facing instructions.
- **Read `skills/web-research-acquisition/SKILL.md`** when gathering current public web evidence, crawling multi-page official documentation, extracting structured public web data, or preserving external research provenance. Crawl4AI is an optional research sidecar, not a core runtime dependency.
- **Read `skills/capability-routing-reach/SKILL.md`** when work touches target discovery, external executable readiness, multiple adapter backends, `doctor`/health semantics, capability fallback, installed-but-broken tools, or certification of whether a discovered backend is actually usable. Pair it with `docs/architecture/capability-routing-doctor.md` for H2 design work.
- **Read `skills/sandbox-research-certification/SKILL.md`** for the current primary strategic line: agent sandbox research, sandbox providers/primitives, containment, policy/authority modeling, Sandbox Profile/Policy IR, adversarial sandbox testing, certification, runtime drift, crisis handling, or adaptive sandbox intelligence. Pair it with `docs/architecture/sandbox-certification-contract.md` and `.company/research/external/agent-sandbox-landscape-2026-08-11.md`.
- **Read `docs/testing/external-agent-verification.md`** when testing AgentCI as an External Verifier: simulate an unknown developer/agent using public surfaces only, do not fill documentation gaps from private memory, classify environment failures separately from product failures, and turn reproducible drift/bugs into RED→GREEN evidence. The External Verifier is a clean-perspective lane, not an independent identity or a replacement for Agent B.
- **Read `skills/agent-native-distribution/SKILL.md`** when promoting, releasing, documenting, packaging, or distributing AgentCI. Every qualifying Growth Artifact should consider both human-facing campaign assets and agent-facing discovery/invocation surfaces such as `llms.txt`, `skills/agentci/SKILL.md`, README, CLI help, canonical evidence links, and legitimate agent/tool registries when verified.

## Current Sandbox Program role routing

- **Agent A** owns canonical product/schema/probe integration and must also read `AGENT_A.md` plus CMD:A #25.
- **Agent B** owns independent falsification / red-team / Spec + Standards verdicts and must also read `AGENT_B.md` plus CMD:B #26.
- **Agent C** owns isolation/runtime enforcement semantics and coordinates through issue #27.
- **Agent D** owns authority/identity/credentials/network-policy semantics and coordinates through issue #28.
- **Agent E** owns evidence/telemetry/replay/cleanup semantics and coordinates through issue #29.
- **Supervisor** owns stage gates, WIP/conflict resolution, and program decisions; read `.company/supervisor.md`, program #24, and current role issues before issuing or changing commands.
- **External Verifier** is a perspective lane documented in `docs/testing/external-agent-verification.md`; route its findings to A/B/C/D/E/Supervisor by domain and never treat it as an extra approval authority.

Do not duplicate these policies into new agent docs unless a task-specific reason requires it. Point to the authoritative source instead.