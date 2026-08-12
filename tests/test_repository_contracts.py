import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_workflows_are_read_only_and_run_required_checks():
    for path in ['.github/workflows/ci.yml', '.github/workflows/agentci.yml']:
        data = yaml.safe_load(read(path))
        assert data['permissions'] == {'contents': 'read'}
    ci = read('.github/workflows/ci.yml')
    assert 'python -m pytest' in ci
    assert 'python -m compileall src scripts' in ci
    assert 'agentci test examples/evals.yaml' in ci
    agentci = read('.github/workflows/agentci.yml')
    assert 'actions/upload-artifact' in agentci
    assert 'artifacts/agentci-results.json' in agentci
    assert 'artifacts/agentci-report.md' in agentci


def test_pr_template_contains_evidence_contract():
    text = read('.github/pull_request_template.md')
    for heading in ['WHY', 'WHAT', 'ACCEPTANCE', 'EVIDENCE', 'RISK', 'GROWTH ARTIFACT', 'RELATED ISSUE']:
        assert f'## {heading}' in text


def test_issue_templates_and_label_docs_cover_state_machine():
    for name in ['feature.yml', 'bug.yml', 'benchmark.yml', 'research.yml']:
        assert (ROOT / '.github/ISSUE_TEMPLATE' / name).exists()
    labels = read('docs/operations/labels.md')
    for label in ['state:ready', 'state:building', 'state:review', 'state:validation', 'state:changes-requested', 'growth:approved']:
        assert label in labels


def test_github_setup_preserves_independent_review_and_human_publish_boundary():
    text = read('docs/operations/github-agent-setup.md').lower()
    assert 'agent a' in text and 'agent b' in text
    assert 'branch protection' in text
    assert 'independent' in text
    assert 'human' in text and 'publish' in text


def test_agent_prompts_encode_critical_restrictions():
    builder = read('.agents/builder.system.md').lower()
    critic = read('.agents/critic-growth.system.md').lower()
    assert 'must not merge' in builder
    assert 'must not publish' in builder
    assert '3 * user_pain' in builder
    assert 'independently verify' in critic
    assert 'must not directly push' in critic
    assert 'never fabricate' in critic


def test_metrics_are_zero_initialized():
    metrics = json.loads(read('.company/metrics.json'))
    assert metrics['product']['weekly_active_projects'] == 0
    assert metrics['growth']['github_stars'] == 0
    assert metrics['business']['mrr_usd'] == 0
    assert metrics['business']['paid_teams'] == 0


def test_growth_rules_match_approved_thresholds():
    rules = yaml.safe_load(read('.company/growth/rules.yaml'))
    assert rules['benchmark']['min_runs'] == 300
    assert rules['performance']['min_improvement_percent'] == 20
    assert rules['performance']['min_samples'] == 100
    assert rules['security']['allowed_severity'] == ['high', 'critical']
    assert rules['security']['requires_disclosure_ready'] is True
    assert rules['dataset']['min_examples'] == 100


def test_gitignore_only_ignores_root_generated_growth_directory():
    lines = [line.strip() for line in read('.gitignore').splitlines() if line.strip()]
    assert '/growth/' in lines
    assert 'growth/' not in lines


def test_ci_proves_growth_validation_and_generation():
    ci = read('.github/workflows/ci.yml')
    assert 'validate_growth_artifact.py' in ci
    assert 'generate_growth_pack.py' in ci
    assert '.company/research/findings/demo-benchmark' in ci


def test_public_agent_surfaces_route_current_sandbox_roles_and_external_verifier():
    readme = read('README.md').lower()
    agents = read('AGENTS.md').lower()
    llms = read('llms.txt').lower()

    assert 'the two-agent operating loop' not in readme
    for role in ['agent c', 'agent d', 'agent e']:
        assert role in readme
        assert role in agents

    verifier_path = 'docs/testing/external-agent-verification.md'
    assert (ROOT / verifier_path).exists()
    assert verifier_path.lower() in agents
    assert verifier_path.lower() in llms
    assert 'external verifier' in agents
    assert 'external verifier' in llms


def test_agentci_skill_routes_current_sandbox_program_without_overclaiming_release():
    skill = read('skills/agentci/SKILL.md').lower()
    assert 'skills/sandbox-research-certification/skill.md' in skill
    assert 'agent sandbox certification' in skill
    for issue in ['#24', '#25', '#26', '#27', '#28', '#29']:
        assert issue in skill
    assert 'no backend' in skill and 'certified' in skill
    assert 'design-stage' in skill or 'experimental' in skill
    assert 'observation' in skill and 'authority' in skill


def test_agents_route_closed_loop_delivery_and_rotating_separation_of_duties():
    agents = read('AGENTS.md').lower()
    workflow_path = 'docs/operations/closed-loop-agent-delivery.md'
    assert (ROOT / workflow_path).exists()
    assert workflow_path in agents
    workflow = read(workflow_path).lower()
    for term in [
        'external user',
        'finder',
        'planner',
        'fixer',
        'challenger',
        'merge decider',
        'fixer != merge decider',
        'post-merge',
        'external contribution',
        'no-wait',
    ]:
        assert term in workflow
    assert 'main' in workflow
    assert 'expected head' in workflow
