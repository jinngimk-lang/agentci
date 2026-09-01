from __future__ import annotations

import json
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'replay' / 'langgraph-8764-accepted-not-durable'


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def _load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_reject_duplicate_keys)


def _load_trajectory():
    return [
        json.loads(line, object_pairs_hook=_reject_duplicate_keys)
        for line in (FIXTURE / 'trajectory.jsonl').read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]


def test_langgraph_8764_fixture_files_and_provenance_exist():
    assert FIXTURE.is_dir()
    assert {path.name for path in FIXTURE.iterdir()} == {
        'README.md',
        'case.json',
        'provenance.json',
        'trajectory.jsonl',
    }

    provenance = _load_json(FIXTURE / 'provenance.json')
    assert provenance['source'] == {
        'url': 'https://github.com/langchain-ai/langgraph/issues/8764',
        'repository': 'langchain-ai/langgraph',
        'issue_number': 8764,
        'reporter': 'mstevens843',
        'reported_at': '2026-08-30',
    }
    assert provenance['observed_commit_status'] == 'unavailable'
    assert provenance['agentci_reproduction_status'] == 'UNVERIFIED'


def test_upstream_observation_does_not_invent_admission_evidence():
    case = _load_json(FIXTURE / 'case.json')

    assert case['semantic_class'] == 'admission-vs-runtime-evidence'
    assert case['agentci_result'] == 'UNVERIFIED'
    assert case['upstream_observation'] == {
        'durable_checkpoint_count': 0,
        'user_effect_count': 0,
        'recovery_status': 'NO_RESUMABLE_RUNTIME_STATE',
        'recovery_error_type': 'EmptyInputError',
    }
    assert case['external_admission']['evidence_status'] == 'NOT_PROVIDED_UPSTREAM'
    assert case['external_admission']['authority'] == 'UNAVAILABLE'
    assert case['classification']['without_authoritative_external_admission'] == 'NOT_ADMITTED_OR_UNKNOWN'
    assert (
        case['classification']['with_authoritative_external_admission']
        == 'ADMITTED_BUT_RUNTIME_EVIDENCE_MISSING'
    )
    assert case['safety']['blind_retry_safe'] == 'UNVERIFIED'
    assert case['safety']['backend_certified'] is False


def test_trajectory_preserves_missing_runtime_evidence_boundary():
    case = _load_json(FIXTURE / 'case.json')
    events = _load_trajectory()

    assert [event['sequence'] for event in events] == [1, 2, 3, 4, 5]
    assert [event['event_type'] for event in events] == [
        'crash-boundary-observed',
        'checkpoint-count-observed',
        'user-effect-count-observed',
        'fresh-process-recovery-observed',
        'external-admission-evidence-checked',
    ]
    assert all(event['logical_run_ref'] == case['runtime_identity']['logical_run_ref'] for event in events)
    assert case['runtime_identity']['thread_id'] == 'accepted-run'
    assert case['runtime_identity']['runtime_run_id_status'] == 'unavailable'
    assert all(event['runtime_run_id'] is None for event in events)
    assert events[1]['durable_checkpoint_count'] == 0
    assert events[2]['user_effect_count'] == 0
    assert events[3]['recovery_status'] == 'NO_RESUMABLE_RUNTIME_STATE'
    assert events[4]['external_admission_evidence_status'] == 'NOT_PROVIDED_UPSTREAM'


def test_fixture_adds_no_langgraph_runtime_dependency():
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    dependencies = project['project']['dependencies']
    assert not any(dependency.lower().startswith('langgraph') for dependency in dependencies)
    for path in (ROOT / 'src' / 'agentci').rglob('*.py'):
        source = path.read_text(encoding='utf-8')
        assert 'import langgraph' not in source
        assert 'from langgraph' not in source
