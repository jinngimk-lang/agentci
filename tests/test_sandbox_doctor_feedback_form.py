from pathlib import Path


FORM = Path(__file__).resolve().parents[1] / ".github" / "ISSUE_TEMPLATE" / "sandbox-doctor-feedback.yml"


def test_retention_choice_cannot_imply_issue_publication_control():
    text = FORM.read_text(encoding="utf-8")

    assert "This GitHub issue submission is public regardless of this choice." in text
    assert "May AgentCI reuse this report as downstream public project evidence?" in text
