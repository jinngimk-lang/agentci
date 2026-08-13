import json
import subprocess


def test_installed_sandbox_doctor_is_truth_bounded_on_real_ci_host():
    completed = subprocess.run(
        ["agentci", "sandbox", "doctor", "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)

    assert payload["report_version"] == payload["api_version"] == "v0alpha1"
    assert isinstance(payload["platform"], dict)
    assert isinstance(payload["candidates"], list)
    assert payload["state"] in {"ready", "not-ready"}

    limitations = " ".join(payload["limitations"]).lower()
    assert "not backend execution" in limitations
    assert "not isolation proof" in limitations
    assert "not security certification" in limitations

    # Default discovery/version probes are deliberately not runtime-route proof.
    # On an ordinary CI host, these candidates may be installed, missing, broken,
    # or unverified, but client/status success alone must never make them ready.
    default_ids = {"docker", "podman", "bubblewrap", "wsl", "windows-sandbox"}
    default_candidates = [c for c in payload["candidates"] if c["id"] in default_ids]
    assert all(c["readiness"] != "ready" for c in default_candidates)
    assert payload["active_backend"] not in default_ids
