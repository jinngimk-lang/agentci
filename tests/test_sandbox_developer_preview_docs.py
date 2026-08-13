from pathlib import Path


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
