from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs' / 'failure-patterns'


def test_public_failure_pattern_library_is_linked_and_grounded():
    expected_pages = {
        'README.md',
        'replay-restore-fidelity.md',
        'false-success-terminality.md',
        'evidence-authority-capability.md',
    }
    assert DOCS.is_dir()
    assert expected_pages <= {path.name for path in DOCS.iterdir()}

    index = (DOCS / 'README.md').read_text(encoding='utf-8')
    assert 'replay-restore-fidelity.md' in index
    assert 'false-success-terminality.md' in index
    assert 'evidence-authority-capability.md' in index
    assert 'tests/fixtures/replay/langgraph-8582-send-untracked' in index
    assert 'Valid evidence is not PASS' in index

    root_readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'docs/failure-patterns/README.md' in root_readme
