# Security Policy

AgentCI is a security-verification project. Please treat vulnerability reports, sandbox-escape findings, credential exposure, authority-confusion cases, and evidence-verification bypasses as potentially sensitive until triaged.

## Reporting a vulnerability

Do **not** publish actionable exploit details, real credentials, secrets, or a working third-party sandbox escape in a public issue, pull request, discussion, fixture, or log.

Preferred reporting path:

1. Use GitHub's private vulnerability reporting / Security Advisory flow for this repository when that option is available in the repository UI.
2. If a private GitHub reporting action is not available to you, contact the repository maintainer through the maintainer's GitHub profile and request a private reporting channel **without including exploit details in the public message**.
3. Include the affected AgentCI version/commit, environment, minimal reproduction conditions, expected boundary, observed boundary, and whether any third-party product or credential may be affected.

We will keep unknown claims `UNVERIFIED` until they can be reproduced safely. We will not ask reporters to run destructive escape testing on ordinary CI or a developer host.

## Safe reproduction boundary

For security research submitted to AgentCI:

- use disposable, explicitly authorized environments;
- replace credentials and sensitive values with synthetic canaries;
- prefer a minimized failing test or evidence fixture over a weaponized exploit;
- separate provider configuration from independently observed behavior;
- record versions, policy state, execution route, cleanup state, and relevant evidence provenance;
- do not publish actionable third-party vulnerability details before responsible-disclosure readiness.

A readiness probe, valid evidence envelope, or `ELIGIBLE` route-binding result is **not** a security certification.

## Supported project states

Security reports are welcome for the latest tagged Developer Preview and for the current `main` development line. Older historical branches and superseded experimental PRs may not receive fixes unless the behavior is still present on a supported line.

## Scope priorities

High-priority report classes include:

- false-PASS / false-ELIGIBLE conditions;
- evidence or receipt tampering accepted as valid;
- caller-controlled data becoming verifier authority;
- execution-route, attempt, environment, policy, or identity confusion;
- secret or credential exposure caused by AgentCI;
- unsafe default probes or destructive behavior;
- packaging/install behavior that silently weakens a verification boundary.

Provider vulnerabilities are not automatically AgentCI vulnerabilities. When a report concerns a third-party runtime or sandbox, AgentCI will preserve provenance and coordinate the finding without claiming authority over the upstream project.
