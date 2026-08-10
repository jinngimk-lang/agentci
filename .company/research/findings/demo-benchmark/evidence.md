# Demo Benchmark Evidence

This V0 artifact exists to prove the evidence-to-growth pipeline, not to claim superiority over any model or agent framework.

## Method

The fixture represents 300 deterministic evaluation runs under the repository's benchmark policy. V0 does not call external model providers; it tests the policy, reporting, and publication-gating mechanics.

## Reproduction

Run:

```bash
python scripts/validate_growth_artifact.py .company/research/findings/demo-benchmark
python scripts/generate_growth_pack.py .company/research/findings/demo-benchmark --output-root growth
```

## Limitation

This is an integration fixture. It is not a real-world model comparison and must not be presented as one.
