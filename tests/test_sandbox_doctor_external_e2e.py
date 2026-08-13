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
    assert "certif" not in json.dumps(payload).lower().replace("certification", "")

    limitations = " ".join(payload["limitations"]).lower()
    assert "not backend execution" in limitations
    assert "not isolation proof" in limitations
    assert "not security certification" in limitations

    # Default discovery/version probes are deliberately not runtime-route proof.
    # On an ordinary CI host, Docker/Podman/bubblewrap/WSL-style default
    # candidates may be installed, missing or broken, but none may become an
    # active backend solely because its client/status command returned zero.
    default_ids = {"docker", "podman", "bubblewrap", "wsl", "windows-sandbox"}
    default_candidates = [c for c in payload["candidates"] if c["id"] in default_ids]
    assert all(c["readiness"] != "ready" for c in default_candidates)
    assert payload["active_backend"] not in default_ids
