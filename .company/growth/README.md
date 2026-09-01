# Growth Evidence Records

This directory stores AgentCI growth/distribution evidence. Growth records are evidence accounting, not a license to infer hidden traffic or adoption.

## `agentci.outreach.v2`

New placement-level outreach batches use `schema_version: agentci.outreach.v2` and are validated by `scripts/validate_outreach_batch.py`.

A counted `placement` means only that a public external write was successfully created and preserved at its exact GitHub comment URL. Counted placements must:

- have a stable unique placement id;
- have a unique confirmed public GitHub issue/PR comment URL;
- use `publication_result: posted`;
- preserve the target repository/item and semantic problem class;
- record the concrete CTA and claim boundary;
- use only observable downstream states accepted by the validator.

Permission failures, 403s, duplicates, skipped targets, and other non-writes belong in `attempts`. They never count as successful placements.

## Observable downstream evidence

Allowed downstream states are:

```text
posted
replied
repo_action
contribution
merged
repeat_contributor
```

`posted` is proven by the placement's public comment URL. Every later state requires at least one public GitHub evidence URL in `downstream_urls`.

Replies, reactions when recorded, forks, issues, pull requests, merges, repeat contributions, stars, and similar public events are **observable signals**. They do not by themselves prove that a particular AgentCI comment caused a repository visit, adoption, or another event. When a causal link is not publicly evidenced, record the event conservatively and keep attribution unknown.

Traffic, referrer, impression, click, and repository-visit data are **unknown** whenever the connected tooling cannot observe them. Never infer them from timing, stars, forks, or replies.

## External acquisition boundary

Promotion is external only when it occurs on an external user/community path. Comments in `jinngimk-lang/agentci` are landing, support, intake, or conversion work; they do not count as external promotion.

Before scaling a channel:

1. identify how qualified users encounter the problem;
2. verify the thread contains a real AgentCI-relevant invariant or evidence gap;
3. deduplicate against existing AgentCI comments;
4. lead with technical value before the project link;
5. preserve upstream provenance and disclose AgentCI affiliation;
6. prefer a bounded fixture/reproduction/validator contribution CTA;
7. scale only when downstream public evidence supports the channel.

A raw write quota is not a success metric. A verified external contribution is stronger acquisition evidence than many unresponsive comments.

See `docs/community-growth.md` and the newest attribution/growth checkpoint under `.company/checkpoints/` for current channel decisions.
