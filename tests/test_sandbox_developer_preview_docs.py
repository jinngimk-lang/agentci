import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_developer_preview_commands_are_publicly_discoverable():
    surfaces = [
        ROOT / 'README.md',
        ROOT / 'llms.txt',
        ROOT / 'skills' / 'agentci' / 'SKILL.md',
        ROOT / 'docs' / 'releases' / '0.2.0-developer-preview.md',
    ]
    for surface in surfaces:
        text = surface.read_text(encoding='utf-8').lower()
        assert 'agentci sandbox doctor' in text, surface
        assert 'agentci sandbox verify' in text, surface
        assert 'not a security certification' in text, surface


def test_release_note_states_evidence_validity_is_not_pass():
    text = (ROOT / 'docs' / 'releases' / '0.2.0-developer-preview.md').read_text(encoding='utf-8').lower()
    assert 'valid evidence' in text
    assert 'recorded verdict' in text
    assert 'unverified' in text
    assert '0.2.0' in text


def test_released_receipt_flow_is_discoverable_from_every_agent_entry_point():
    """Breaks when the installed strict receipt flow is hidden from a clean agent."""
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT / 'src'), str(ROOT)])
    help_result = subprocess.run(
        [sys.executable, '-m', 'agentci.cli', 'sandbox', 'verify', '--help'],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert '--receipt' in help_result.stdout
    assert '--receipt-bundle' in help_result.stdout

    for surface in [
        ROOT / 'README.md',
        ROOT / 'llms.txt',
        ROOT / 'skills' / 'agentci' / 'SKILL.md',
    ]:
        text = surface.read_text(encoding='utf-8').lower()
        assert '--receipt' in text, surface
        assert '--receipt-bundle' in text, surface
        assert 'certification_claim' in text, surface
        assert 'fixture binding manifest' in text, surface
        assert 'verifier-pinned' in text, surface
        assert 'provider execution proof' in text, surface
        assert '```bash\nagentci sandbox replay' not in text, surface


def test_fixture_revalidation_cannot_be_misread_as_backend_reexecution():
    for surface in [
        ROOT / 'README.md',
        ROOT / 'llms.txt',
        ROOT / 'skills' / 'agentci' / 'SKILL.md',
        ROOT / 'docs' / 'releases' / '0.2.0-developer-preview.md',
    ]:
        text = surface.read_text(encoding='utf-8').lower()
        assert 'does not rerun a sandbox, provider, workload, or external observer' in text, surface
        assert 'no `agentci sandbox replay` command is released' in text, surface
        assert 'receipt/replay' not in text, surface


def test_public_license_scope_preserves_third_party_terms():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8').lower()
    assert 'agentci original work' in readme
    assert 'third_party_notices.md' in readme
    assert 'notice.md' in readme
