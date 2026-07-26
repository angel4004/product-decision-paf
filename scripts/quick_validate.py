#!/usr/bin/env python3
"""Validate the portable product-decision-paf package with Python stdlib only."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


SKILL_NAME = "product-decision-paf"
SKILL_DESCRIPTION = (
    "Use when evaluating product decisions, product artifacts, user evidence, "
    "PAF fit, PMF/PCF claims, or founder/CPO product arguments. Helps decide "
    "what to inspect, which claims are unsupported, what artifact is missing, "
    "and what the next product step should be."
)

REQUIRED_DOCS = (
    "README.md",
    "NOTICE.md",
    "docs/migration-map.md",
    "docs/equivalence-coverage.md",
    "docs/release-checklist.md",
    "references/bayram-skill-architecture.md",
    "references/paf-hypothesis-method.md",
)

REQUIRED_EVAL_FIELDS = {
    "id",
    "case_id",
    "mode",
    "prompt",
    "expected",
    "forbidden",
    "tags",
    "source_refs",
}

REQUIRED_EVAL_TAGS = {
    "activation-positive",
    "activation-negative",
    "paf-review",
    "forbidden-claim",
    "insufficient-evidence",
    "robin-embedded",
    "privacy-publication",
    "product-passport",
    "disputed-pmf-pcf",
    "external-write",
    "out-of-scope",
    "paf-hypothesis-method",
    "null-base",
    "data-base",
    "hypothesis-card",
    "upstream-gate",
    "und-id-ex",
}

REQUIRED_CASE_IDS = {
    "activation-artifact-claims",
    "activation-cpo-argument",
    "activation-next-product-step",
    "activation-paf-review",
    "activation-pmf-pcf-evidence",
    "activation-product-hypothesis",
    "activation-product-passport",
    "client-feedback-intake",
    "coding-task-no-activation",
    "customer-success-metric-uplift",
    "disputed-pcf-demo-reaction",
    "disputed-pmf-contradictory",
    "existing-passport-review",
    "external-write-without-approval",
    "forbidden-business-impact",
    "forbidden-pmf-marketing-bypass",
    "insufficient-evidence-next-step",
    "paf-confidence-point-no-fake-score",
    "paf-data-base-nexus-bottleneck",
    "paf-hypothesis-card-complete",
    "paf-hypothesis-type-classification",
    "paf-no-invented-threshold",
    "paf-null-base-customer-value-solution",
    "paf-und-id-ex-harvest",
    "paf-upstream-gate-no-downstream-claim",
    "paf-value-solution-cotest",
    "privacy-publication-boundary",
    "private-memory-refusal",
    "realistic-project-passport",
    "regulated-advice-out-of-scope",
    "robin-embedded-review",
    "robin-permission-expansion",
    "root-agent-refusal",
    "scoped-pmf-evidence",
    "standalone-enforcement-boundary",
    "ui-evidence-gate",
    "visual-landing-no-activation",
}

QUALITY_CRITICAL_INVARIANT_CASES = {
    "1-evidence-first": {
        "insufficient-evidence-next-step",
        "disputed-pmf-contradictory",
    },
    "2-paf-not-scoring": {
        "activation-paf-review",
        "paf-confidence-point-no-fake-score",
    },
    "3-strong-claims-need-sources": {
        "forbidden-pmf-marketing-bypass",
        "forbidden-business-impact",
        "customer-success-metric-uplift",
    },
    "4-goal-before-artifact": {
        "activation-product-hypothesis",
        "activation-artifact-claims",
    },
    "5-artifact-purpose-gate": {
        "activation-product-passport",
        "realistic-project-passport",
    },
    "6-insufficient-data-is-valid": {
        "insufficient-evidence-next-step",
        "disputed-pcf-demo-reaction",
    },
    "7-compact-disputed-claim-review": {
        "disputed-pmf-contradictory",
        "disputed-pcf-demo-reaction",
    },
    "8-one-default-next-step": {
        "activation-next-product-step",
        "insufficient-evidence-next-step",
    },
    "9-route-sources-first": {
        "client-feedback-intake",
        "ui-evidence-gate",
    },
    "10-robin-owns-host-state": {
        "robin-embedded-review",
        "robin-permission-expansion",
    },
    "11-private-state-not-published": {
        "privacy-publication-boundary",
        "private-memory-refusal",
    },
    "12-quality-claims-need-proof": {
        "standalone-enforcement-boundary",
        "paf-upstream-gate-no-downstream-claim",
    },
}

REQUIRED_INVARIANT_IDS = {
    "1-evidence-first",
    "2-paf-not-scoring",
    "3-strong-claims-need-sources",
    "4-goal-before-artifact",
    "5-artifact-purpose-gate",
    "6-insufficient-data-is-valid",
    "7-compact-disputed-claim-review",
    "8-one-default-next-step",
    "9-route-sources-first",
    "10-robin-owns-host-state",
    "11-private-state-not-published",
    "12-quality-claims-need-proof",
}

FORBIDDEN_CLAIM_PATTERNS = {
    "pmf": re.compile(r"\bpmf\b", re.IGNORECASE),
    "pcf": re.compile(r"\bpcf\b", re.IGNORECASE),
    "business-impact": re.compile(
        r"\bbusiness[\s_-]+impact\b|бизнес[\s_-]*эффект", re.IGNORECASE
    ),
    "customer-success": re.compile(
        r"\bcustomer[\s_-]+success\b|успех\w*\s+клиент", re.IGNORECASE
    ),
    "user-need": re.compile(
        r"\busers?[\s_-]+need\b|\bproduct[\s_-]+need\b|"
        r"нуж\w*\s+пользовател",
        re.IGNORECASE,
    ),
    "metric-uplift": re.compile(
        r"\bmetric[\s_-]+uplift\b|improv\w*\s+(?:the\s+)?metric|"
        r"улучш\w*\s+метрик",
        re.IGNORECASE,
    ),
    "readiness": re.compile(
        r"\breadiness\b|\bquality-ready\b|\bproduction-ready\b|готовност",
        re.IGNORECASE,
    ),
    "paf-consistency": re.compile(
        r"\bpaf[\s_-]+consisten|\bpaf[\s_-]+fit\b|паф[\s_-]*"
        r"(?:согласован|соответств)",
        re.IGNORECASE,
    ),
}

DISALLOWED_TOP_LEVEL_DIRECTORIES = {
    "memory",
    "traces",
    "observability",
    "automation",
    "migration",
}

IGNORED_DIRECTORY_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
TOC_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:contents|table\s+of\s+contents|toc|содержание|оглавление)"
    r"(?:\s|$)",
    re.IGNORECASE | re.MULTILINE,
)
RAW_TRANSCRIPT_FILENAME_RE = re.compile(
    r"raw[-_. ]*transcript|transcript[-_. ]*raw", re.IGNORECASE
)

SENSITIVE_CONTENT_PATTERNS = (
    (
        "private-key block",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            re.IGNORECASE,
        ),
    ),
    (
        "OpenAI-style token",
        re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    ),
    (
        "GitHub-style token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "Slack-style token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    ),
    (
        "JWT-like token",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{8,}\."
            r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
        ),
    ),
    (
        "Bearer token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.IGNORECASE),
    ),
)

PRIVATE_UNIX_USER_ROOTS = (
    "/" + "Users" + "/",
    "/" + "home" + "/",
)

PRIVATE_PATH_PATTERNS = (
    (
        "private Windows user path",
        re.compile(r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+)[^\\/\s`\"'<>]+"),
    ),
    (
        "private Unix user path",
        re.compile(
            r"(?i)(?:"
            + "|".join(re.escape(root) for root in PRIVATE_UNIX_USER_ROOTS)
            + r")[^/\s`\"'<>]+"
        ),
    ),
)

CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    \b
    (?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|
       password|passwd|secret|private[_-]?key)
    \b
    \s*[:=]\s*
    ["']?
    ([A-Za-z0-9_./+=-]{12,})
    """
)

SAFE_CREDENTIAL_VALUE_MARKERS = {
    "example",
    "placeholder",
    "redacted",
    "not-run",
    "not_available",
    "not-available",
    "host-required",
    "dummy",
    "sample",
    "your-",
}


class Validation:
    """Collect validation errors without exposing matched sensitive values."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.errors: list[str] = []
        self.checks_run = 0
        self.eval_case_count = 0
        self.eval_tags: set[str] = set()

    def error(self, message: str) -> None:
        self.errors.append(message)

    def check(self, function) -> None:
        self.checks_run += 1
        try:
            function()
        except Exception as exc:  # Defensive: report a safe failure, not a traceback.
            self.error(f"{function.__name__}: unexpected validation error: {exc}")

    def relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except (OSError, ValueError):
            return path.as_posix()

    def read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8-sig")
        except FileNotFoundError:
            self.error(f"missing required file: {self.relative(path)}")
        except UnicodeDecodeError:
            self.error(f"file is not UTF-8 text: {self.relative(path)}")
        except OSError as exc:
            self.error(f"cannot read {self.relative(path)}: {exc}")
        return None

    def files_under(self, directory: Path) -> list[Path]:
        if not directory.is_dir():
            self.error(f"missing required directory: {self.relative(directory)}")
            return []
        return sorted(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and not any(part in IGNORED_DIRECTORY_NAMES for part in path.parts)
        )


def unquote_scalar(raw_value: str) -> str:
    value = raw_value.strip()
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        parsed = ast.literal_eval(value)
        if not isinstance(parsed, str):
            raise ValueError("quoted YAML scalar is not a string")
        return parsed
    return value


def validate_skill_frontmatter(result: Validation) -> None:
    skill_path = result.root / "SKILL.md"
    text = result.read_text(skill_path)
    if text is None:
        return

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        result.error("SKILL.md must start with a YAML frontmatter delimiter")
        return

    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        result.error("SKILL.md frontmatter has no closing delimiter")
        return

    fields: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        if not line.strip():
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)", line)
        if not match:
            result.error(
                f"SKILL.md:{line_number}: unsupported frontmatter syntax"
            )
            continue
        key, raw_value = match.groups()
        if key in fields:
            result.error(f"SKILL.md:{line_number}: duplicate frontmatter key {key}")
            continue
        try:
            fields[key] = unquote_scalar(raw_value)
        except (SyntaxError, ValueError) as exc:
            result.error(f"SKILL.md:{line_number}: invalid scalar for {key}: {exc}")

    required_keys = {"name", "description"}
    actual_keys = set(fields)
    if actual_keys != required_keys:
        missing = sorted(required_keys - actual_keys)
        extra = sorted(actual_keys - required_keys)
        if missing:
            result.error(f"SKILL.md frontmatter missing keys: {', '.join(missing)}")
        if extra:
            result.error(
                "SKILL.md frontmatter must contain only name and description; "
                f"extra keys: {', '.join(extra)}"
            )

    if fields.get("name") != SKILL_NAME:
        result.error(f"SKILL.md name must be exactly {SKILL_NAME!r}")
    if fields.get("description") != SKILL_DESCRIPTION:
        result.error("SKILL.md description does not match the required exact text")


def parse_openai_yaml(result: Validation, path: Path) -> dict[str, dict[str, str]]:
    text = result.read_text(path)
    if text is None:
        return {}

    sections: dict[str, dict[str, str]] = {}
    current_section: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        section_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*", line)
        if section_match:
            current_section = section_match.group(1)
            if current_section in sections:
                result.error(
                    f"agents/openai.yaml:{line_number}: duplicate section "
                    f"{current_section}"
                )
            sections.setdefault(current_section, {})
            continue

        field_match = re.fullmatch(
            r" {2}([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*", line
        )
        if not field_match or current_section is None:
            result.error(
                f"agents/openai.yaml:{line_number}: unsupported YAML structure"
            )
            continue
        key, raw_value = field_match.groups()
        if key in sections[current_section]:
            result.error(
                f"agents/openai.yaml:{line_number}: duplicate key "
                f"{current_section}.{key}"
            )
        sections[current_section][key] = raw_value

    return sections


def validate_openai_yaml(result: Validation) -> None:
    path = result.root / "agents" / "openai.yaml"
    sections = parse_openai_yaml(result, path)
    if not sections:
        return

    required_strings = (
        ("interface", "display_name"),
        ("interface", "short_description"),
        ("interface", "default_prompt"),
    )
    parsed_strings: dict[tuple[str, str], str] = {}

    for section, key in required_strings:
        raw_value = sections.get(section, {}).get(key)
        if raw_value is None:
            result.error(f"agents/openai.yaml missing {section}.{key}")
            continue
        if (
            len(raw_value) < 2
            or raw_value[0] not in {"'", '"'}
            or raw_value[-1] != raw_value[0]
        ):
            result.error(
                f"agents/openai.yaml {section}.{key} must be explicitly quoted"
            )
            continue
        try:
            value = ast.literal_eval(raw_value)
        except (SyntaxError, ValueError):
            result.error(
                f"agents/openai.yaml {section}.{key} is not a valid quoted string"
            )
            continue
        if not isinstance(value, str) or not value.strip():
            result.error(
                f"agents/openai.yaml {section}.{key} must be a non-empty string"
            )
            continue
        parsed_strings[(section, key)] = value

    short_description = parsed_strings.get(("interface", "short_description"))
    if short_description is not None and not 25 <= len(short_description) <= 64:
        result.error(
            "agents/openai.yaml interface.short_description must be 25-64 "
            f"characters; got {len(short_description)}"
        )

    default_prompt = parsed_strings.get(("interface", "default_prompt"))
    if default_prompt is not None and "$product-decision-paf" not in default_prompt:
        result.error(
            "agents/openai.yaml interface.default_prompt must contain "
            "$product-decision-paf"
        )

    implicit = sections.get("policy", {}).get("allow_implicit_invocation")
    if implicit is None:
        result.error(
            "agents/openai.yaml missing policy.allow_implicit_invocation"
        )
    elif implicit != "false":
        result.error(
            "agents/openai.yaml policy.allow_implicit_invocation must be "
            "explicitly false"
        )


def markdown_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<"):
        closing = target.find(">")
        return target[1:closing] if closing != -1 else target[1:]
    return target.split(maxsplit=1)[0]


def is_external_markdown_target(target: str) -> bool:
    return bool(
        re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target)
        or target.startswith("//")
    )


def resolve_local_markdown_target(
    result: Validation, markdown_file: Path, raw_target: str
) -> Path | None:
    target = unquote(markdown_target(raw_target))
    if not target or target.startswith("#") or is_external_markdown_target(target):
        return None

    path_part = target.split("#", 1)[0].split("?", 1)[0]
    if not path_part:
        return None
    if re.match(r"^[A-Za-z]:[\\/]", path_part) or path_part.startswith(("/", "\\")):
        result.error(
            f"{result.relative(markdown_file)}: absolute local Markdown link "
            "is not allowed"
        )
        return None

    candidate = (markdown_file.parent / path_part).resolve()
    try:
        candidate.relative_to(result.root)
    except ValueError:
        result.error(
            f"{result.relative(markdown_file)}: Markdown link escapes package: "
            f"{path_part}"
        )
        return None
    return candidate


def validate_direct_skill_references(result: Validation) -> None:
    skill_path = result.root / "SKILL.md"
    skill_text = result.read_text(skill_path)
    if skill_text is None:
        return

    linked_paths: set[Path] = set()
    for match in MARKDOWN_LINK_RE.finditer(skill_text):
        candidate = resolve_local_markdown_target(result, skill_path, match.group(1))
        if candidate is not None:
            linked_paths.add(candidate)

    required_files: list[Path] = []
    for directory_name in ("references", "assets"):
        required_files.extend(result.files_under(result.root / directory_name))

    for required_file in required_files:
        if required_file.resolve() not in linked_paths:
            result.error(
                "SKILL.md must directly link to "
                f"{result.relative(required_file)}"
            )

    if "scripts/quick_validate.py" not in skill_text:
        result.error("SKILL.md must directly reference scripts/quick_validate.py")


def validate_markdown_links(result: Validation) -> None:
    markdown_files = sorted(
        path
        for path in result.root.rglob("*.md")
        if path.is_file()
        and not any(part in IGNORED_DIRECTORY_NAMES for part in path.parts)
    )
    for markdown_file in markdown_files:
        text = result.read_text(markdown_file)
        if text is None:
            continue
        for match in MARKDOWN_LINK_RE.finditer(text):
            candidate = resolve_local_markdown_target(
                result, markdown_file, match.group(1)
            )
            if candidate is not None and not candidate.exists():
                result.error(
                    f"{result.relative(markdown_file)}: broken local Markdown "
                    f"link: {markdown_target(match.group(1))}"
                )


def validate_required_docs(result: Validation) -> None:
    for relative_path in REQUIRED_DOCS:
        path = result.root / relative_path
        if not path.is_file():
            result.error(f"missing required document: {relative_path}")


def validate_string_list(
    result: Validation,
    case_path: Path,
    field: str,
    value,
    *,
    require_nonempty: bool,
) -> list[str]:
    if not isinstance(value, list):
        result.error(
            f"{result.relative(case_path)}: {field} must be a list of strings"
        )
        return []
    if require_nonempty and not value:
        result.error(f"{result.relative(case_path)}: {field} must not be empty")
    clean: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            result.error(
                f"{result.relative(case_path)}: {field}[{index}] must be a "
                "non-empty string"
            )
        else:
            clean.append(item.strip())
    return clean


def validate_eval_cases(result: Validation) -> None:
    cases_root = result.root / "evals" / "cases"
    if not cases_root.is_dir():
        result.error("missing required eval directory: evals/cases")
        return

    case_files = sorted(cases_root.rglob("*.json"))
    if not case_files:
        result.error("no JSON eval cases found under evals/cases")
        return

    seen_ids: dict[str, str] = {}
    corpus_parts: list[str] = []

    for case_path in case_files:
        relative_path = result.relative(case_path)
        try:
            data = json.loads(case_path.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError:
            result.error(f"{relative_path}: eval case is not UTF-8")
            continue
        except json.JSONDecodeError as exc:
            result.error(
                f"{relative_path}: invalid JSON at line {exc.lineno}, "
                f"column {exc.colno}"
            )
            continue
        except OSError as exc:
            result.error(f"{relative_path}: cannot read eval case: {exc}")
            continue

        if not isinstance(data, dict):
            result.error(f"{relative_path}: eval case must be a JSON object")
            continue

        actual_fields = set(data)
        missing_fields = sorted(REQUIRED_EVAL_FIELDS - actual_fields)
        extra_fields = sorted(actual_fields - REQUIRED_EVAL_FIELDS)
        if missing_fields:
            result.error(
                f"{relative_path}: missing eval fields: "
                f"{', '.join(missing_fields)}"
            )
        if extra_fields:
            result.error(
                f"{relative_path}: unknown eval fields: {', '.join(extra_fields)}"
            )

        case_id = data.get("case_id")
        public_id = data.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            result.error(f"{relative_path}: case_id must be a non-empty string")
            case_id = ""
        if not isinstance(public_id, str) or not public_id.strip():
            result.error(f"{relative_path}: id must be a non-empty string")
            public_id = ""
        if case_id and public_id and case_id != public_id:
            result.error(f"{relative_path}: id and case_id must be identical")
        if case_id and case_path.stem != case_id:
            result.error(
                f"{relative_path}: filename stem must equal case_id {case_id!r}"
            )
        if case_id:
            if case_id in seen_ids:
                result.error(
                    f"{relative_path}: duplicate case_id {case_id!r}; first in "
                    f"{seen_ids[case_id]}"
                )
            else:
                seen_ids[case_id] = relative_path

        mode = data.get("mode")
        if mode not in {"standalone", "embedded-robin"}:
            result.error(
                f"{relative_path}: mode must be standalone or embedded-robin"
            )

        prompt = data.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            result.error(f"{relative_path}: prompt must be a non-empty string")

        expected = validate_string_list(
            result,
            case_path,
            "expected",
            data.get("expected"),
            require_nonempty=True,
        )
        forbidden = validate_string_list(
            result,
            case_path,
            "forbidden",
            data.get("forbidden"),
            require_nonempty=False,
        )
        tags = validate_string_list(
            result,
            case_path,
            "tags",
            data.get("tags"),
            require_nonempty=True,
        )
        source_refs = validate_string_list(
            result,
            case_path,
            "source_refs",
            data.get("source_refs"),
            require_nonempty=True,
        )

        for tag in tags:
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", tag):
                result.error(
                    f"{relative_path}: tag must use lowercase kebab-case: {tag!r}"
                )
        result.eval_tags.update(tags)

        for source_ref in source_refs:
            if (
                re.match(r"^[A-Za-z]:[\\/]", source_ref)
                or source_ref.startswith(PRIVATE_UNIX_USER_ROOTS)
                or "\n" in source_ref
            ):
                result.error(
                    f"{relative_path}: source_refs must use HTTPS or safe "
                    "package-relative refs"
                )
                continue
            if source_ref.startswith("https://"):
                continue
            if source_ref.startswith(("http://", "//")):
                result.error(
                    f"{relative_path}: external source_ref must use HTTPS"
                )
                continue

            path_part = unquote(source_ref.split("#", 1)[0]).strip()
            local_ref = Path(path_part)
            if not path_part or local_ref.is_absolute() or ".." in local_ref.parts:
                result.error(
                    f"{relative_path}: unsafe package-relative source_ref "
                    f"{source_ref!r}"
                )
                continue
            resolved_ref = (result.root / local_ref).resolve()
            if not resolved_ref.is_relative_to(result.root) or not resolved_ref.is_file():
                result.error(
                    f"{relative_path}: unresolved package-relative source_ref "
                    f"{source_ref!r}"
                )

        corpus_parts.extend(
            [
                prompt if isinstance(prompt, str) else "",
                "\n".join(expected),
                "\n".join(forbidden),
                "\n".join(tags),
            ]
        )
        result.eval_case_count += 1

    missing_tags = sorted(REQUIRED_EVAL_TAGS - result.eval_tags)
    if missing_tags:
        result.error(
            "eval coverage missing required tags: " + ", ".join(missing_tags)
        )

    observed_case_ids = set(seen_ids)
    missing_case_ids = sorted(REQUIRED_CASE_IDS - observed_case_ids)
    if missing_case_ids:
        result.error(
            "eval inventory missing required case IDs: " + ", ".join(missing_case_ids)
        )

    mapped_invariant_ids = set(QUALITY_CRITICAL_INVARIANT_CASES)
    missing_invariant_ids = sorted(REQUIRED_INVARIANT_IDS - mapped_invariant_ids)
    unexpected_invariant_ids = sorted(mapped_invariant_ids - REQUIRED_INVARIANT_IDS)
    if missing_invariant_ids:
        result.error(
            "missing quality-critical invariant mappings: "
            + ", ".join(missing_invariant_ids)
        )
    if unexpected_invariant_ids:
        result.error(
            "unexpected quality-critical invariant mappings: "
            + ", ".join(unexpected_invariant_ids)
        )

    for invariant, required_ids in QUALITY_CRITICAL_INVARIANT_CASES.items():
        missing_invariant_cases = sorted(required_ids - observed_case_ids)
        if missing_invariant_cases:
            result.error(
                f"quality-critical invariant {invariant} missing mapped cases: "
                + ", ".join(missing_invariant_cases)
            )

    corpus = "\n".join(corpus_parts)
    missing_claim_terms = sorted(
        name
        for name, pattern in FORBIDDEN_CLAIM_PATTERNS.items()
        if not pattern.search(corpus)
    )
    if missing_claim_terms:
        result.error(
            "eval corpus does not represent forbidden claim terms: "
            + ", ".join(missing_claim_terms)
        )


def validate_disallowed_directories(result: Validation) -> None:
    for directory_name in sorted(DISALLOWED_TOP_LEVEL_DIRECTORIES):
        path = result.root / directory_name
        if path.exists():
            result.error(
                f"disallowed top-level runtime/private directory: {directory_name}/"
            )


def iter_scannable_files(result: Validation):
    for path in sorted(result.root.rglob("*")):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(result.root).parts
        except ValueError:
            continue
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative_parts):
            continue
        yield path


def validate_publication_safety(result: Validation) -> None:
    for path in iter_scannable_files(result):
        relative_path = result.relative(path)
        lower_name = path.name.lower()

        if lower_name == ".env" or lower_name.startswith(".env."):
            result.error(f"disallowed environment file: {relative_path}")
        if RAW_TRANSCRIPT_FILENAME_RE.search(path.name):
            result.error(f"disallowed raw transcript filename: {relative_path}")
        if lower_name in {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}:
            result.error(f"disallowed private-key filename: {relative_path}")
        if path.suffix.lower() in {".key", ".p12", ".pfx"}:
            result.error(f"disallowed credential container: {relative_path}")

        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            result.error(f"cannot scan {relative_path}: {exc}")
            continue
        if b"\x00" in raw_bytes:
            continue
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue

        for pattern_name, pattern in SENSITIVE_CONTENT_PATTERNS:
            if pattern.search(text):
                result.error(
                    f"{relative_path}: detected {pattern_name}; value not printed"
                )
        for pattern_name, pattern in PRIVATE_PATH_PATTERNS:
            if pattern.search(text):
                result.error(f"{relative_path}: detected {pattern_name}")

        for match in CREDENTIAL_ASSIGNMENT_RE.finditer(text):
            value = match.group(1).lower()
            if not any(marker in value for marker in SAFE_CREDENTIAL_VALUE_MARKERS):
                result.error(
                    f"{relative_path}: detected token-like credential assignment; "
                    "value not printed"
                )
                break


def validate_reference_tocs(result: Validation) -> None:
    references_root = result.root / "references"
    for path in result.files_under(references_root):
        if path.suffix.lower() != ".md":
            continue
        text = result.read_text(path)
        if text is None:
            continue
        line_count = len(text.splitlines())
        if line_count > 100 and not TOC_HEADING_RE.search(text):
            result.error(
                f"{result.relative(path)} has {line_count} lines and needs a "
                "Contents/TOC heading"
            )


def run_validation(root: Path) -> Validation:
    result = Validation(root)
    if not result.root.is_dir():
        result.error(f"package root does not exist or is not a directory: {root}")
        return result

    for check in (
        validate_skill_frontmatter,
        validate_openai_yaml,
        validate_direct_skill_references,
        validate_markdown_links,
        validate_required_docs,
        validate_eval_cases,
        validate_disallowed_directories,
        validate_publication_safety,
        validate_reference_tocs,
    ):
        result.check(lambda check=check: check(result))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate product-decision-paf package structure, metadata, links, "
            "eval coverage, and obvious publication hazards. This does not run "
            "a model or prove external outcomes."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Package root (default: parent of this script's directory).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_validation(args.root)

    if result.errors:
        print(
            f"FAIL {SKILL_NAME} validation: {len(result.errors)} error(s)",
            file=sys.stderr,
        )
        for error in result.errors:
            print(f"- {error}", file=sys.stderr)
        print(
            f"checks_run={result.checks_run} "
            f"eval_cases={result.eval_case_count}",
            file=sys.stderr,
        )
        return 1

    print(f"PASS {SKILL_NAME} package validation")
    print(f"root={result.root}")
    print(f"checks_run={result.checks_run}")
    print(f"eval_cases={result.eval_case_count}")
    print("eval_tags=" + ",".join(sorted(result.eval_tags)))
    print(
        "scope=static package integrity only; model behavior and external "
        "outcomes are not proven"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
