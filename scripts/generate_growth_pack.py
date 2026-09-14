from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import shutil
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.growth_policy import ArtifactError, validate_artifact


class GrowthGenerationError(ValueError):
    """Raised when an artifact is valid input but unsafe/ineligible for draft generation."""


DEFAULT_RULES = Path('.company/growth/rules.yaml')
NUMBER_RE = re.compile(r'(?<![\w.])[+-]?\d(?:\d|,(?=[\d,]))*(?:\.\d+)?(?:[eE][+-]?\d+)?%?')


def _structured_numbers(facts: dict) -> set[Decimal]:
    return {
        Decimal(str(value))
        for value in facts.values()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _numeric_claim_value(token: str) -> Decimal:
    number_text = token[:-1] if token.endswith('%') else token
    mantissa = re.split(r'[eE]', number_text, maxsplit=1)[0]
    unsigned_mantissa = mantissa[1:] if mantissa.startswith(('+', '-')) else mantissa
    integer_part = unsigned_mantissa.split('.', 1)[0]

    if ',' in integer_part:
        groups = integer_part.split(',')
        valid_grouping = (
            1 <= len(groups[0]) <= 3
            and groups[0].isdigit()
            and all(len(group) == 3 and group.isdigit() for group in groups[1:])
        )
        if not valid_grouping:
            raise GrowthGenerationError(
                f"public numeric claim {token} has invalid thousands separators"
            )

    normalized = number_text.replace(',', '')
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise GrowthGenerationError(f"public numeric claim {token} is malformed") from exc


def _assert_numeric_claims_are_structured(facts: dict) -> None:
    allowed = _structured_numbers(facts)
    public_strings = [facts['title'], *facts['public_claims']]
    for text in public_strings:
        for match in NUMBER_RE.finditer(text):
            token = match.group(0)
            if _numeric_claim_value(token) not in allowed:
                raise GrowthGenerationError(
                    f"public numeric claim {token} is not backed by a structured numeric fact"
                )


def _claims_block(claims: list[str]) -> str:
    if not claims:
        return "No public numeric/result claim is included in this draft."
    return "\n".join(f"- {claim}" for claim in claims)


def _render_x(title: str, claims: list[str]) -> str:
    lead = claims[0] if claims else title
    remainder = claims[1:]
    parts = [lead]
    if remainder:
        parts.append("\n".join(remainder))
    parts.append("Evidence, method, and reproduction notes are in the open repository artifact.")
    return "\n\n".join(parts) + "\n"


def _render_reddit(title: str, claims: list[str]) -> str:
    return (
        f"# {title}\n\n"
        "I built this as a reproducible engineering/research artifact rather than a launch announcement.\n\n"
        f"## Findings\n\n{_claims_block(claims)}\n\n"
        "## Method\n\nThe repository includes the canonical facts, evidence, sources, and reproduction material used for these claims.\n\n"
        "## Limitations\n\nTreat the result as scoped to the documented fixture/method. Re-run the artifact before generalizing it to a different agent, model, toolchain, or workload.\n\n"
        "## Reproduction\n\nUse the repository evidence directory and validation command before discussing or extending the result.\n"
    )


def _render_hn(title: str, category: str, claims: list[str]) -> str:
    headline = f"Show HN: AgentCI – {title}" if category in {"release", "integration"} else title
    return (
        f"{headline}\n\n"
        f"{_claims_block(claims)}\n\n"
        "The repository contains the structured facts, evidence, source list, and reproduction notes. Feedback on methodology, failure cases, and reproducibility is especially useful.\n"
    )


def _render_blog(title: str, claims: list[str]) -> str:
    return (
        f"# {title}\n\n"
        "## Result\n\n"
        f"{_claims_block(claims)}\n\n"
        "## Method\n\nThis draft is generated only after the repository policy validator accepts the canonical artifact. The detailed method lives in the paired evidence file and source list.\n\n"
        "## Evidence\n\nPublic claims in this draft come from `facts.json`; numeric claims must match structured numeric fields in that file.\n\n"
        "## Limitations\n\nThe artifact should not be generalized beyond its documented scope without another reproducible run.\n\n"
        "## Reproduction\n\nValidate the canonical artifact with the repository growth validator, then inspect its evidence and sources before publication.\n"
    )


def generate_growth_pack(artifact_dir: Path, output_root: Path, rules_path: Path = DEFAULT_RULES) -> Path:
    artifact_dir = Path(artifact_dir)
    output_root = Path(output_root)
    result = validate_artifact(artifact_dir, Path(rules_path))
    if not result.eligible:
        detail = '; '.join(result.reasons)
        raise GrowthGenerationError(f"artifact is not eligible for growth generation: {detail}")

    facts = result.facts
    _assert_numeric_claims_are_structured(facts)
    title = facts['title']
    category = facts['category']
    claims = facts['public_claims']

    out = output_root / facts['artifact_id']
    if out.exists():
        raise GrowthGenerationError(f"output already exists: {out}")
    out.mkdir(parents=True)

    shutil.copyfile(artifact_dir / 'facts.json', out / 'facts.json')
    shutil.copyfile(artifact_dir / 'evidence.md', out / 'evidence.md')
    (out / 'x.md').write_text(_render_x(title, claims), encoding='utf-8')
    (out / 'reddit.md').write_text(_render_reddit(title, claims), encoding='utf-8')
    (out / 'hackernews.md').write_text(_render_hn(title, category, claims), encoding='utf-8')
    (out / 'blog.md').write_text(_render_blog(title, claims), encoding='utf-8')
    (out / 'publish-checklist.md').write_text(
        "# Publish Checklist\n\n"
        f"- Artifact: `{facts['artifact_id']}`\n"
        f"- Category: `{category}`\n"
        "- [x] Repository growth policy validated\n"
        "- [x] Canonical facts/evidence copied into this pack\n"
        "- [x] Numeric public claims checked against structured facts\n"
        f"- [x] Disclosure check: {'ready' if category == 'security' else 'not applicable'}\n"
        "- [ ] Human approval\n\n"
        "**NO AUTO-PUBLISH IN V0.** External publication requires a human owner.\n",
        encoding='utf-8',
    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Generate a draft-only growth pack')
    parser.add_argument('artifact_dir', type=Path)
    parser.add_argument('--output-root', type=Path, default=Path('growth'))
    parser.add_argument('--rules', type=Path, default=DEFAULT_RULES)
    args = parser.parse_args(argv)
    try:
        out = generate_growth_pack(args.artifact_dir, args.output_root, args.rules)
    except ArtifactError as exc:
        print(f'INVALID: {exc}')
        return 2
    except GrowthGenerationError as exc:
        print(f'REJECTED: {exc}')
        return 1
    print(f'GENERATED: {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
