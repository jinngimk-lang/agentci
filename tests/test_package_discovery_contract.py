from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_python_distribution_and_cli_names_are_not_conflated():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["name"] == "agentci-v0"
    assert project["scripts"]["agentci"] == "agentci.cli:main"
    assert project["name"] != "agentci"


def test_public_docs_do_not_direct_users_to_the_unrelated_pypi_name():
    for path in (ROOT / "README.md", ROOT / "llms.txt"):
        text = path.read_text(encoding="utf-8").lower()
        assert "pip install agentci\n" not in text
        assert "pip install agentci " not in text
        assert "pip3 install agentci\n" not in text
        assert "uv pip add agentci" not in text


def test_canonical_install_notice_explains_repository_distribution_and_cli_identity():
    notice = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

    assert "Do not use `pip install agentci`" in notice
    assert "jinngimk-lang/agentci" in notice
    assert "agentci-v0" in notice
    assert "CLI command" in notice
    assert "python -m pip install -e '.[dev]'" in notice
