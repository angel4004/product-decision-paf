from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import quick_validate
from scripts.quick_validate import run_validation


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class QuickValidateRegressionTests(unittest.TestCase):
    def copy_candidate(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        candidate = Path(temporary.name) / "product-decision-paf"
        shutil.copytree(
            PACKAGE_ROOT,
            candidate,
            ignore=shutil.ignore_patterns(".git", "__pycache__"),
        )
        return temporary, candidate

    def test_current_package_passes(self) -> None:
        result = run_validation(PACKAGE_ROOT)
        self.assertEqual([], result.errors)

    def test_missing_required_case_fails_closed(self) -> None:
        temporary, candidate = self.copy_candidate()
        self.addCleanup(temporary.cleanup)
        (
            candidate
            / "evals"
            / "cases"
            / "negative"
            / "paf-no-invented-threshold.json"
        ).unlink()

        result = run_validation(candidate)

        self.assertTrue(
            any("missing required case IDs" in error for error in result.errors),
            result.errors,
        )

    def test_unresolved_source_ref_fails_closed(self) -> None:
        temporary, candidate = self.copy_candidate()
        self.addCleanup(temporary.cleanup)
        case_path = (
            candidate
            / "evals"
            / "cases"
            / "positive"
            / "activation-paf-review.json"
        )
        case = json.loads(case_path.read_text(encoding="utf-8"))
        case["source_refs"] = ["missing/provenance.md"]
        case_path.write_text(
            json.dumps(case, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        result = run_validation(candidate)

        self.assertTrue(
            any("unresolved package-relative source_ref" in error for error in result.errors),
            result.errors,
        )

    def test_missing_invariant_mapping_fails_closed(self) -> None:
        invariant = "12-quality-claims-need-proof"
        removed = quick_validate.QUALITY_CRITICAL_INVARIANT_CASES.pop(invariant)
        try:
            result = run_validation(PACKAGE_ROOT)
        finally:
            quick_validate.QUALITY_CRITICAL_INVARIANT_CASES[invariant] = removed

        self.assertTrue(
            any(
                "missing quality-critical invariant mappings" in error
                for error in result.errors
            ),
            result.errors,
        )


if __name__ == "__main__":
    unittest.main()
