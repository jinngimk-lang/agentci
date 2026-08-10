import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT / 'src'), str(ROOT)])
    return subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True)


def test_full_v0_loop(tmp_path: Path):
    eval_out = tmp_path / 'eval'
    eval_result = run(sys.executable, '-m', 'agentci.cli', 'test', 'examples/evals.yaml', '--output-dir', str(eval_out))
    assert eval_result.returncode == 0, eval_result.stderr
    assert (eval_out / 'agentci-results.json').exists()

    invalid = run(sys.executable, 'scripts/validate_growth_artifact.py', 'tests/fixtures/growth/invalid-benchmark')
    assert invalid.returncode == 1
    assert 'INELIGIBLE' in invalid.stdout

    valid = run(sys.executable, 'scripts/validate_growth_artifact.py', '.company/research/findings/demo-benchmark')
    assert valid.returncode == 0, valid.stdout + valid.stderr

    growth_root = tmp_path / 'growth'
    generated = run(
        sys.executable, 'scripts/generate_growth_pack.py',
        '.company/research/findings/demo-benchmark', '--output-root', str(growth_root),
    )
    assert generated.returncode == 0, generated.stdout + generated.stderr
    pack = growth_root / 'demo-benchmark'
    assert (pack / 'x.md').exists()
    assert (pack / 'publish-checklist.md').exists()
    assert 'NO AUTO-PUBLISH IN V0' in (pack / 'publish-checklist.md').read_text()


def test_readme_explains_quickstart_and_safety_boundary():
    text = (ROOT / 'README.md').read_text(encoding='utf-8')
    for phrase in ['agentci test examples/evals.yaml', 'Agent A', 'Agent B', 'Growth Pack', 'no auto-publish', 'branch protection']:
        assert phrase.lower() in text.lower()
