import copy

from scripts.validate_sandbox_authority import validate
from tests.test_sandbox_authority_semantics import _bundle


def test_attested_workload_cannot_self_issue_capability_without_delegation():
    bundle = _bundle()

    # PrincipalAttestation proves identity/scope, not grant-issuer authority.
    # Replacing the root issuer with the attested workload must not let the
    # workload manufacture its own grant when no parent/delegation exists.
    bundle["grants"][0]["issuer_principal_id"] = "workload-1"

    assert validate(copy.deepcopy(bundle)) != []
