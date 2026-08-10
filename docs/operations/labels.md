# Repository Labels

Canonical labels for the operating loop:

- Types: `type:bug`, `type:feature`, `type:benchmark`, `type:security`, `type:research`, `type:growth`
- Priority: `priority:p0`, `priority:p1`, `priority:p2`, `priority:p3`
- State: `state:research`, `state:ready`, `state:building`, `state:review`, `state:validation`, `state:changes-requested`, `state:merged`, `state:released`, `state:measure`
- Growth: `growth:candidate`, `growth:approved`, `growth:published`
- Source: `source:user`, `source:benchmark`, `source:agent`, `source:community`

Normal path: `state:research` → `state:ready` → `state:building` → `state:review` → `state:validation` → `state:merged` → `state:released` → `state:measure`.

Failure path: `state:review` or `state:validation` → `state:changes-requested` → `state:building`.
