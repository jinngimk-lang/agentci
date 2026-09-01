# Installing this AgentCI repository

Canonical repository: https://github.com/jinngimk-lang/agentci

## Important package-name boundary

**Do not use `pip install agentci` to install this repository.**

As of 2026-09-01, the `agentci` project name on PyPI belongs to a different project whose published metadata points to `Agent-CI/cli`. It is not the package built from `jinngimk-lang/agentci`.

This repository deliberately uses the Python **distribution name** `agentci-v0` while exposing the local **CLI command** `agentci`.

Those are different identities:

```text
repository:     jinngimk-lang/agentci
Python dist:    agentci-v0
CLI command:    agentci
```

AgentCI does not claim a public PyPI release for this repository merely because `pyproject.toml` has a distribution name. Use the installation path documented by the exact repository revision/release you are working from.

## Developer Preview install from source

Requirements: Python 3.11+.

From a clone of the canonical repository:

```bash
python -m pip install -e '.[dev]'
agentci --help
agentci test examples/evals.yaml
agentci sandbox doctor --json
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

The editable install is intentionally repository-bound: it installs the code you cloned instead of relying on a same-named external package index entry.

## Before trusting an install command from search results

Verify all three of these:

1. the source repository is `https://github.com/jinngimk-lang/agentci`;
2. the distribution metadata names `agentci-v0` for this project;
3. the installed `agentci` CLI exposes the commands documented by the checked-out revision.

A matching CLI name is not proof of package or repository identity.

## Current claim boundary

The repository is a Developer Preview. Installation success does not imply a sandbox backend is executed, secure, compatible, or certified. Follow `README.md` and `llms.txt` for the currently released command surface and truth boundaries.
