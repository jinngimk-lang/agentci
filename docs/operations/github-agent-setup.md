# GitHub Agent Setup

## Trust boundary

GitHub branch protection is authoritative. Configure required checks for `CI` and `AgentCI Regression`, require at least one independent approval, dismiss stale approvals after new commits, and prevent force-pushes/deletion on the protected branch.

## Agent A — Builder

Use a separate GitHub App or fine-grained token. Grant repository contents write only where branch creation/commits require it, issues write, pull requests write, and actions read. Do not grant administration, secrets, branch-protection, or deployment permissions. Agent A must never approve or merge its own PR.

## Agent B — Critic / Growth

Use a different identity and credential. Grant repository contents read, issues write, pull-request review/write, and actions read. Agent B should review independently and must not be able to change branch protection or production secrets.

## Merge rule

A human repository owner configures branch protection so passing checks and an independent review are required. Neither agent can disable the gate to make progress. In V0, merge can be performed by the human owner or a narrowly scoped merge automation after GitHub itself confirms the rules.

## Publishing rule

External social credentials remain human-owned. Agents can create repository-local draft files, but a human must review and publish them in V0. Never place publishing tokens in prompts, repository files, or generic coding-agent environments.
