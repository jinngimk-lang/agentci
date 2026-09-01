# Package discovery collision — 2026-09-01

## Question

What happens when a user discovers this project by name and follows the natural package-index path instead of cloning the canonical repository?

## Observed public surfaces

### PyPI `agentci`

Source: https://pypi.org/project/agentci/

Observed on 2026-09-01:

- project title/description: `AgentCI CLI` / `Agent CI command-line interface`;
- maintainer: `tcdent`;
- published versions: `0.1.0` and `0.1.1` from October 2025;
- project links point to the separate `Agent-CI/cli` project / `agent-ci.com`;
- installation guidance uses the `agentci` package name.

This public package is **not** evidence of a release from `jinngimk-lang/agentci`.

### piwheels `agentci`

Source: https://www.piwheels.org/project/agentci/

Observed on 2026-09-01:

- mirrors the same `agentci` distribution line;
- lists the old 0.1.0 / 0.1.1 artifacts and `agentci-client-config` dependency.

This creates a second search/index surface that can reinforce the wrong package identity for users who search only by project/CLI name.

## Canonical repository evidence

`jinngimk-lang/agentci` currently declares:

```toml
[project]
name = "agentci-v0"
version = "0.3.0.dev0"

[project.scripts]
agentci = "agentci.cli:main"
```

Therefore the repository already distinguishes its Python distribution identity (`agentci-v0`) from its executable command (`agentci`).

## Acquisition implication

A plausible discovery path is:

```text
AgentCI name / CLI mention
→ package-index search
→ PyPI `agentci`
→ unrelated project
```

This is a real path conflict, not evidence that anyone actually followed it. Traffic/referrer data for this repository remains unavailable, so no visit, install, confusion, or conversion count may be inferred.

## Decision

1. Never tell users to `pip install agentci` for this repository.
2. Keep source-based Developer Preview installation explicit until a real distribution/release path is verified.
3. Publish a canonical `INSTALL.md` that states repository / distribution / CLI identities separately.
4. Add an automated repository contract so future docs cannot accidentally reintroduce the conflicting package command.
5. If/when publishing to an index, verify the exact distribution name and release artifact first; do not infer availability from `pyproject.toml` alone.

## Status

Classification: `DISCOVERY_PATH_CONFLICT_CONFIRMED`

User impact / conversion impact: `UNVERIFIED`
