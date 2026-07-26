from __future__ import annotations

import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import hypothesis_state


STAMP = "2026-07-26T10:00:00Z"


def hypothesis_record(
    *,
    revision: int = 0,
    state: str = "framing",
    verdict: str = "pending",
) -> dict:
    ready = state in {"ready_to_run", "running", "ready_for_review", "closed"}
    record = {
        "hypothesis_id": "hypothesis-one",
        "decision_scope_id": "scope-initial",
        "revision": revision,
        "created_at": STAMP,
        "updated_at": STAMP,
        "state": state,
        "verdict": verdict,
        "execution_ref": (
            "execution:demo"
            if state in {"running", "ready_for_review", "closed"}
            else None
        ),
        "origin": {
            "reason": "Resolve the earliest decision-critical uncertainty.",
            "nexus_revision": 0,
            "originating_entry_ids": [],
            "decision_to_unlock": "Decide whether to continue validation.",
        },
        "hypothesis_class": "customer_need",
        "lifecycle_context": ["discovery"],
        "statement": "The selected segment repeatedly encounters the problem.",
        "segment": "Defined test segment",
        "situation": "During the target workflow",
        "rationale": "The need must be established before solution investment.",
        "upstream_dependencies": [],
        "validation": {
            "method": "Review bounded behavioral evidence.",
            "conditions": [],
            "metrics": [
                {
                    "metric_id": "metric-primary",
                    "role": "primary",
                    "definition": "Owner-defined decision evidence.",
                    "numerator": None,
                    "denominator": None,
                    "segment": "Defined test segment",
                    "baseline": None,
                    "criterion": "Owner-approved criterion" if ready else None,
                    "criterion_provenance": "owner_supplied" if ready else "unset",
                    "approval_status": "approved" if ready else "pending",
                    "rationale": "The rule must change the product decision.",
                }
            ],
            "sample": {
                "population": "Defined test segment",
                "target_size": 10 if ready else None,
                "inclusion": [],
                "exclusion": [],
                "rationale": "Owner-selected decision sample" if ready else None,
                "provenance": "owner_supplied" if ready else "unset",
                "approval_status": "approved" if ready else "pending",
            },
            "time_window": {
                "definition": "Owner-selected period" if ready else None,
                "rationale": "Matches the decision horizon" if ready else None,
                "provenance": "owner_supplied" if ready else "unset",
                "approval_status": "approved" if ready else "pending",
            },
            "validity_threats": [],
            "decision_rules": {
                "if_confirmed": "Proceed to the next supported PAF question.",
                "if_disconfirmed": "Revise or stop the hypothesis.",
                "if_unresolved": "Collect one decision-relevant evidence item.",
            },
        },
        "owner_approvals": [],
        "pending_owner_approvals": [],
        "pending_owner_resolutions": [],
        "evidence_ids": ["evidence-one"] if state == "closed" else [],
        "result": {
            "observations": ["Owner reviewed the bounded result"]
            if state == "closed"
            else [],
            "interpretation": "The criterion was met" if state == "closed" else None,
            "validity_status": "adequate" if state == "closed" else "not_reviewed",
            "metric_results": (
                [
                    {
                        "metric_id": "metric-primary",
                        "evidence_ids": ["evidence-one"],
                        "observation_period": {
                            "start": None,
                            "end": None,
                        },
                        "observed_summary": (
                            "The primary criterion was evaluated against the bounded evidence."
                        ),
                        "actual_numerator": None,
                        "actual_denominator": None,
                        "actual_sample_size": 10,
                        "criterion_evaluation": (
                            "met"
                            if verdict == "confirmed"
                            else (
                                "not_met"
                                if verdict == "disconfirmed"
                                else "indeterminate"
                            )
                        ),
                        "validity_status": (
                            "adequate"
                            if verdict in {"confirmed", "disconfirmed"}
                            else "limited"
                        ),
                    }
                ]
                if state == "closed"
                else []
            ),
            "new_nexus_entry_ids": (
                ["nexus-learning-one"] if state == "closed" else []
            ),
            "external_outcome_status": "not_verified",
            "outcome_evidence_ids": [],
            "external_outcome_receipt_ref": None,
            "decision_taken": "Close the validation cycle"
            if state == "closed"
            else None,
            "decision_owner_acceptance_ref": "approval:terminal-verdict"
            if state == "closed"
            else None,
        },
        "next_step": {
            "action": "Review or execute the next bounded validation step.",
            "owner_ref": "owner:demo",
            "expected_evidence": "Evidence that can change the decision.",
            "pass_rule": "Proceed only when the owner-approved criterion is met.",
            "fail_rule": "Otherwise revise, stop, or collect missing evidence.",
        },
        "relations": {
            "based_on_hypothesis_ids": [],
            "replaces_hypothesis_id": None,
        },
    }
    if ready:
        add_approval(record, "decision_rule", "approval-decision-rule")
    if state in {"running", "ready_for_review"}:
        add_approval(
            record,
            "state_transition",
            "approval-state-transition",
        )
    if state == "closed":
        add_approval(
            record,
            "terminal_verdict",
            "approval-terminal-verdict",
        )
    return record


def add_approval(
    record: dict,
    scope: str,
    approval_id: str,
    *,
    owner_ref: str = "owner:demo",
    owner_tenure_id: str = "tenure-initial",
    decision: str = "approved",
    subject_revision: int | None = None,
) -> dict:
    bound_revision = (
        record["revision"] if subject_revision is None else subject_revision
    )
    approval = {
        "approval_id": approval_id,
        "scope": scope,
        "owner_ref": owner_ref,
        "owner_tenure_id": owner_tenure_id,
        "subject_revision": bound_revision,
        "subject_sha256": hypothesis_state.approval_subject_sha256(
            record,
            scope,
            "workspace-demo",
            owner_tenure_id,
            bound_revision,
        ),
        "decision": decision,
        "decided_at": STAMP,
        "safe_receipt_ref": f"approval:{scope.replace('_', '-')}",
    }
    record["owner_approvals"].append(approval)
    return approval


def workspace_state(record: dict | None = None, *, revision: int = 0) -> dict:
    record = record or hypothesis_record()
    initial_evidence = (
        [evidence_entry()] if record["evidence_ids"] else []
    )
    initial_nexus = [
        nexus_entry(
            entry_id=entry_id,
            sequence=index,
            evidence_ids=list(record["evidence_ids"]),
        )
        for index, entry_id in enumerate(
            record["result"]["new_nexus_entry_ids"],
            start=1,
        )
    ]
    return {
        "schema_version": "product-decision-paf/hypothesis-workspace-state/v1",
        "data_policy": "safe_refs_and_summaries_only",
        "workspace_id": "workspace-demo",
        "product_ref": "product:demo",
        "revision": revision,
        "revision_chain_head_sha256": None,
        "as_of": STAMP,
        "decision_owner_ref": "owner:demo",
        "owner_tenure_log": [
            {
                "tenure_id": "tenure-initial",
                "sequence": 1,
                "effective_at": STAMP,
                "effective_workspace_revision": 0,
                "owner_ref": "owner:demo",
                "predecessor_tenure_id": None,
                "transition_receipt_ref": "approval:initial-owner",
                "reason": "Initial decision ownership.",
            }
        ],
        "active_owner_tenure_id": "tenure-initial",
        "goal": {
            "actor": "Product decision owner",
            "outcome": "Reduce the named uncertainty.",
            "baseline": None,
            "target": None,
            "period": None,
            "decision_to_unlock": "Decide whether validation should continue.",
        },
        "decision_scope_log": [
            {
                "scope_id": "scope-initial",
                "sequence": 1,
                "opened_at": STAMP,
                "opened_workspace_revision": 0,
                "goal": {
                    "actor": "Product decision owner",
                    "outcome": "Reduce the named uncertainty.",
                    "baseline": None,
                    "target": None,
                    "period": None,
                    "decision_to_unlock": (
                        "Decide whether validation should continue."
                    ),
                },
                "predecessor_scope_id": None,
                "transition_receipt_ref": "approval:initial-scope",
                "reason": "Initial bounded product decision.",
            }
        ],
        "active_decision_scope_id": "scope-initial",
        "base": "data_base" if initial_evidence else "null_base",
        "nexus_entries": initial_nexus,
        "evidence_log": initial_evidence,
        "claim_log": [],
        "outcome_log": [],
        "focus_hypothesis_id": (
            None
            if record["state"] in {"closed", "cancelled", "superseded"}
            else record["hypothesis_id"]
        ),
        "hypotheses": [record],
        "last_persistence_receipt_ref": None,
    }


def evidence_entry() -> dict:
    return {
        "evidence_id": "evidence-one",
        "sequence": 1,
        "recorded_at": STAMP,
        "claim_refs": [],
        "source_ref": "source:bounded-observation",
        "observation_period": {"start": None, "end": None},
        "method": "Bounded source review",
        "segment": None,
        "numerator": None,
        "denominator": None,
        "filters": [],
        "exclusions": [],
        "summary": "A safe evidence summary.",
        "status": "supported",
        "supersedes_evidence_ids": [],
        "content_policy": "safe_summary_only",
    }


def nexus_entry(
    entry_id: str = "nexus-one",
    *,
    sequence: int = 1,
    kind: str = "fact",
    status: str = "supported",
    evidence_ids: list[str] | None = None,
) -> dict:
    return {
        "entry_id": entry_id,
        "sequence": sequence,
        "kind": kind,
        "decision_authority": None,
        "statement": "A bounded product-learning statement.",
        "evidence_ids": evidence_ids or [],
        "supersedes_entry_ids": [],
        "status": status,
        "valid_as_of": STAMP,
    }


def claim_event(
    event_id: str = "claim-event-one",
    *,
    claim_id: str = "claim-one",
    sequence: int = 1,
    status: str = "blocked",
    resolution: str | None = None,
    supersedes_event_ids: list[str] | None = None,
    resolution_evidence_ids: list[str] | None = None,
) -> dict:
    return {
        "event_id": event_id,
        "claim_id": claim_id,
        "sequence": sequence,
        "recorded_at": STAMP,
        "status": status,
        "resolution": resolution,
        "claim": "The strong claim is proven.",
        "reason": "The current evidence does not support that statement.",
        "required_evidence": ["A bounded source that can decide the claim."],
        "resolution_evidence_ids": resolution_evidence_ids or [],
        "supersedes_event_ids": supersedes_event_ids or [],
    }


def outcome_event(
    event_id: str = "outcome-event-one",
    *,
    sequence: int = 1,
    hypothesis_id: str = "hypothesis-one",
    status: str = "observed",
    evidence_ids: list[str] | None = None,
    supersedes_event_ids: list[str] | None = None,
    host_receipt_ref: str | None = None,
) -> dict:
    return {
        "event_id": event_id,
        "sequence": sequence,
        "recorded_at": STAMP,
        "hypothesis_id": hypothesis_id,
        "decision_scope_id": "scope-initial",
        "status": status,
        "evidence_ids": evidence_ids or ["evidence-outcome"],
        "summary": "A bounded post-release outcome observation.",
        "attribution_note": (
            "The observed change cannot yet be attributed exclusively."
            if status == "attribution_limited"
            else None
        ),
        "host_receipt_ref": host_receipt_ref,
        "supersedes_event_ids": supersedes_event_ids or [],
    }


def set_proposed_validation(record: dict, *, approved: bool) -> None:
    status = "approved" if approved else "pending"
    metric = record["validation"]["metrics"][0]
    metric["criterion"] = "At least 4 of 10 observations meet the rule."
    metric["criterion_provenance"] = "proposed_assumption"
    metric["approval_status"] = status
    sample = record["validation"]["sample"]
    sample["target_size"] = 10
    sample["rationale"] = "A bounded owner-reviewed initial sample."
    sample["provenance"] = "proposed_assumption"
    sample["approval_status"] = status
    time_window = record["validation"]["time_window"]
    time_window["definition"] = "One bounded observation period."
    time_window["rationale"] = "Matches the immediate decision horizon."
    time_window["provenance"] = "proposed_assumption"
    time_window["approval_status"] = status


def pending_requirement(
    record: dict,
    scope: str,
    change_id: str,
    *,
    subject_sha256: str | None = None,
) -> dict:
    return {
        "approval_scope": scope,
        "hypothesis_id": record["hypothesis_id"],
        "owner_ref": "owner:demo",
        "owner_tenure_id": "tenure-initial",
        "subject_revision": record["revision"],
        "subject_sha256": (
            subject_sha256
            if subject_sha256 is not None
            else hypothesis_state.approval_subject_sha256(
                record,
                scope,
                "workspace-demo",
                "tenure-initial",
                record["revision"],
            )
        ),
        "reason": f"The owner must approve {scope}.",
        "source_change_set_id": change_id,
    }


def change_set(
    state: dict,
    *,
    change_id: str,
    operation: str,
    expected_revision: int | None,
    previous: dict | None,
) -> dict:
    previous_records = (
        {item["hypothesis_id"]: item for item in previous["hypotheses"]}
        if previous
        else {}
    )
    creates = []
    updates = []
    for record in state["hypotheses"]:
        old = previous_records.get(record["hypothesis_id"])
        if old is None:
            creates.append(
                {
                    "hypothesis_id": record["hypothesis_id"],
                    "candidate_revision": record["revision"],
                }
            )
        elif record != old:
            updates.append(
                {
                    "hypothesis_id": record["hypothesis_id"],
                    "expected_revision": old["revision"],
                    "candidate_revision": record["revision"],
                    "from_state": old["state"],
                    "to_state": record["state"],
                }
            )

    previous_focus = previous["focus_hypothesis_id"] if previous else None
    previous_approval_ids = {
        approval["approval_id"]
        for record in previous["hypotheses"]
        for approval in record["owner_approvals"]
    } if previous else set()
    new_approval_ids = sorted(
        approval["approval_id"]
        for record in state["hypotheses"]
        for approval in record["owner_approvals"]
        if approval["approval_id"] not in previous_approval_ids
    )
    focus_change = (
        None
        if previous_focus == state["focus_hypothesis_id"]
        else {"from": previous_focus, "to": state["focus_hypothesis_id"]}
    )
    return {
        "schema_version": "product-decision-paf/hypothesis-change-set/v1",
        "data_policy": "safe_refs_and_summaries_only",
        "persistence_intent": "proposal",
        "change_set_id": change_id,
        "request_id": f"request-{change_id}",
        "workspace_id": state["workspace_id"],
        "created_at": STAMP,
        "workspace_operation": operation,
        "expected_workspace_revision": expected_revision,
        "candidate_workspace_revision": state["revision"],
        "candidate_state": state,
        "change_manifest": {
            "hypothesis_creates": creates,
            "hypothesis_updates": updates,
            "appended_nexus_entry_ids": (
                [
                    item["entry_id"]
                    for item in state["nexus_entries"]
                ]
                if previous is None
                else [
                    item["entry_id"]
                    for item in state["nexus_entries"][
                        len(previous["nexus_entries"]):
                    ]
                ]
            ),
            "appended_decision_scope_ids": [
                item["scope_id"]
                for item in state["decision_scope_log"][
                    len(previous["decision_scope_log"]) if previous else 0:
                ]
            ],
            "appended_owner_tenure_ids": [
                item["tenure_id"]
                for item in state["owner_tenure_log"][
                    len(previous["owner_tenure_log"]) if previous else 0:
                ]
            ],
            "appended_evidence_ids": [
                item["evidence_id"]
                for item in state["evidence_log"][
                    len(previous["evidence_log"]) if previous else 0:
                ]
            ],
            "appended_claim_event_ids": [
                item["event_id"]
                for item in state["claim_log"][
                    len(previous["claim_log"]) if previous else 0:
                ]
            ],
            "appended_outcome_event_ids": [
                item["event_id"]
                for item in state["outcome_log"][
                    len(previous["outcome_log"]) if previous else 0:
                ]
            ],
            "new_owner_approval_ids": new_approval_ids,
            "focus_change": focus_change,
            "base_change": (
                None
                if previous is not None and previous["base"] == state["base"]
                else {
                    "from": previous["base"] if previous is not None else None,
                    "to": state["base"],
                }
            ),
        },
        "required_owner_approvals": [
            requirement
            for record in state["hypotheses"]
            for requirement in record["pending_owner_approvals"]
        ],
        "enforcement_boundary": {
            "reasoning": "instruction_supported",
            "persistence": "host_required",
            "external_effect": "not_supported_standalone",
        },
    }


class HypothesisStateAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "hypothesis-state"
        self.change_path = Path(self.temporary.name).resolve() / "change.json"

    def write_change(self, value: dict) -> None:
        self.change_path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def run_main(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = hypothesis_state.main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def commit(self, proposal: dict) -> tuple[int, dict | None, str]:
        self.write_change(proposal)
        code, output, error = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )
        return code, json.loads(output) if output else None, error

    def read_bundle(self) -> dict:
        return json.loads(
            self.bundle_path().read_text(encoding="utf-8")
        )

    def bundle_path(self) -> Path:
        return self.root / hypothesis_state.BUNDLE_FILENAME

    def test_proposal_intent_is_valid_but_never_commit_eligible(self) -> None:
        intent_path = (
            hypothesis_state.PACKAGE_ROOT
            / "evals"
            / "conformance"
            / "standalone-no-store-proposal-intent.json"
        )
        code, output, error = self.run_main(
            ["validate-intent", "--intent", str(intent_path)]
        )
        self.assertEqual(0, code, error)
        validation = json.loads(output)
        self.assertEqual("valid_proposal_intent", validation["status"])
        self.assertFalse(validation["commit_eligible"])
        self.assertEqual("not_persisted", validation["persistence_status"])

        intent = json.loads(intent_path.read_text(encoding="utf-8"))
        self.write_change(intent)
        commit_code, _, commit_error = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )
        self.assertEqual(4, commit_code)
        self.assertIn("change set is invalid", commit_error)
        self.assertFalse(self.bundle_path().exists())

        intent["commit_eligible"] = True
        self.write_change(intent)
        invalid_code, _, invalid_error = self.run_main(
            ["validate-intent", "--intent", str(self.change_path)]
        )
        self.assertEqual(4, invalid_code)
        self.assertIn("proposal intent is invalid", invalid_error)

    def test_proposal_intent_semantics_fail_closed(self) -> None:
        fixture_path = (
            hypothesis_state.PACKAGE_ROOT
            / "evals"
            / "conformance"
            / "standalone-no-store-proposal-intent.json"
        )
        original = json.loads(fixture_path.read_text(encoding="utf-8"))
        cases: list[tuple[str, dict, str]] = []

        invalid_revisions = copy.deepcopy(original)
        invalid_revisions["known_bindings"]["expected_workspace_revision"] = 9
        invalid_revisions["known_bindings"]["candidate_workspace_revision"] = 2
        cases.append(
            (
                "invalid-create-revisions",
                invalid_revisions,
                "create proposal intent requires expected revision null",
            )
        )

        resolved_listed_as_missing = copy.deepcopy(original)
        resolved_listed_as_missing["known_bindings"]["workspace_id"] = (
            "workspace-demo"
        )
        cases.append(
            (
                "resolved-listed-as-missing",
                resolved_listed_as_missing,
                "lists resolved binding workspace_id as unresolved",
            )
        )

        missing_not_listed = copy.deepcopy(original)
        missing_not_listed["unresolved_bindings"].remove("workspace_id")
        cases.append(
            (
                "missing-not-listed",
                missing_not_listed,
                "omits unresolved binding workspace_id",
            )
        )

        missing_lifecycle_not_listed = copy.deepcopy(original)
        missing_lifecycle_not_listed["unresolved_bindings"].remove(
            "lifecycle_context"
        )
        cases.append(
            (
                "missing-lifecycle-not-listed",
                missing_lifecycle_not_listed,
                "omits unresolved binding lifecycle_context",
            )
        )

        missing_target_state = copy.deepcopy(original)
        missing_target_state["requested_change"]["target_state"] = None
        cases.append(
            (
                "missing-target-state",
                missing_target_state,
                "target_state",
            )
        )

        effect_gaps_only = copy.deepcopy(original)
        effect_gaps_only["known_bindings"].update(
            {
                "workspace_id": "workspace-demo",
                "product_ref": "product:demo",
                "hypothesis_id": "hypothesis-demo",
                "decision_scope_id": "scope-initial",
                "owner_tenure_id": "tenure-initial",
            }
        )
        effect_gaps_only["requested_change"].update(
            {
                "hypothesis_statement": "The segment repeatedly has the need.",
                "hypothesis_class": "customer_need",
                "lifecycle_context": ["discovery"],
                "segment": "Defined segment",
                "validation_design_ref": "validation:demo",
            }
        )
        effect_gaps_only["unresolved_bindings"] = [
            "write_authority",
            "state_root_or_host_adapter",
        ]
        cases.append(
            (
                "effect-gaps-only",
                effect_gaps_only,
                "requires at least one unresolved candidate-state binding",
            )
        )

        incomplete_materialization = copy.deepcopy(original)
        incomplete_materialization["materialization_contract"][
            "required_to_commit"
        ] = [
            "authorized_host_adapter",
            "write_authority",
            "explicit_state_root",
        ]
        cases.append(
            (
                "incomplete-materialization",
                incomplete_materialization,
                "materialization contract omits resolved_bindings",
            )
        )

        for label, candidate, expected_error in cases:
            with self.subTest(label=label):
                self.write_change(candidate)
                code, _, error = self.run_main(
                    ["validate-intent", "--intent", str(self.change_path)]
                )
                self.assertEqual(4, code)
                self.assertIn(expected_error, error)

    def test_create_and_verify_round_trip(self) -> None:
        state = workspace_state()
        proposal = change_set(
            state,
            change_id="change-create",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        self.write_change(proposal)

        code, output, error = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )

        self.assertEqual(0, code, error)
        receipt = json.loads(output)
        self.assertEqual("accepted", receipt["status"])
        bundle_path = self.root / hypothesis_state.BUNDLE_FILENAME
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        persisted = bundle["current_state"]
        self.assertEqual(
            f"receipt:{receipt['receipt_id']}",
            persisted["last_persistence_receipt_ref"],
        )

        code, output, error = self.run_main(
            ["verify", "--root", str(self.root)]
        )
        self.assertEqual(0, code, error)
        self.assertEqual("verified", json.loads(output)["status"])

    def test_stale_revision_returns_conflict_without_overwrite(self) -> None:
        initial = workspace_state()
        create = change_set(
            initial,
            change_id="change-create",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        self.write_change(create)
        code, _, error = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )
        self.assertEqual(0, code, error)
        before_bundle = json.loads(
            (self.root / hypothesis_state.BUNDLE_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        before_state = before_bundle["current_state"]

        stale = copy.deepcopy(initial)
        stale["revision"] = 1
        stale_record = stale["hypotheses"][0]
        stale_record["revision"] = 1
        stale_record["updated_at"] = "2026-07-26T11:00:00Z"
        stale_record["state"] = "awaiting_owner_rule"
        stale_proposal = change_set(
            stale,
            change_id="change-stale",
            operation="replace",
            expected_revision=9,
            previous=initial,
        )
        self.write_change(stale_proposal)

        code, output, _ = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )

        self.assertEqual(3, code)
        self.assertEqual("conflict", json.loads(output)["status"])
        after_bundle = json.loads(
            (self.root / hypothesis_state.BUNDLE_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(before_state, after_bundle["current_state"])
        self.assertEqual(2, len(after_bundle["receipts"]))
        replay_code, replay_output, replay_error = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )
        self.assertEqual(3, replay_code, replay_error)
        self.assertEqual(json.loads(output), json.loads(replay_output))
        self.assertEqual(2, len(self.read_bundle()["receipts"]))

    def test_terminal_hypothesis_is_immutable(self) -> None:
        previous = workspace_state(
            hypothesis_record(state="closed", verdict="confirmed")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["hypotheses"][0]["revision"] = 1
        candidate["hypotheses"][0]["statement"] = "Rewritten historical claim"
        proposal = change_set(
            candidate,
            change_id="change-terminal",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(proposal, previous)

        self.assertTrue(
            any("terminal hypothesis" in error for error in errors),
            errors,
        )

    def test_evidence_log_is_append_only(self) -> None:
        previous = workspace_state()
        previous["evidence_log"] = [evidence_entry()]
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["evidence_log"][0]["summary"] = "Rewritten prior observation."
        proposal = change_set(
            candidate,
            change_id="change-rewrite-evidence",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(proposal, previous)

        self.assertTrue(
            any("append-only prefix" in error for error in errors),
            errors,
        )

    def test_claim_log_is_append_only_and_manifested(self) -> None:
        previous = workspace_state()
        previous["claim_log"] = [claim_event()]
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["claim_log"] = []
        proposal = change_set(
            candidate,
            change_id="change-drop-blocked-claim",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("claim_log must preserve" in error for error in errors),
            errors,
        )

    def test_claim_event_ids_are_unique(self) -> None:
        state = workspace_state()
        state["claim_log"] = [claim_event(), claim_event()]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("duplicate event_id" in error for error in errors),
            errors,
        )

    def test_claim_resolution_is_append_only_and_evidence_bound(self) -> None:
        state = workspace_state()
        state["evidence_log"] = [evidence_entry()]
        state["claim_log"] = [
            claim_event(),
            claim_event(
                "claim-event-two",
                sequence=2,
                status="resolved",
                resolution="supported",
                supersedes_event_ids=["claim-event-one"],
                resolution_evidence_ids=["evidence-one"],
            ),
        ]
        state["evidence_log"][0]["status"] = "supported"
        state["base"] = "data_base"

        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(state),
        )
        self.assertEqual(
            [],
            hypothesis_state.active_blocked_claim_ids(state["claim_log"]),
        )

    def test_claim_resolution_requires_evidence_and_latest_event_link(self) -> None:
        state = workspace_state()
        state["claim_log"] = [
            claim_event(),
            claim_event(
                "claim-event-two",
                sequence=2,
                status="resolved",
                resolution="supported",
            ),
        ]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("must supersede the latest event" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("lacks resolution evidence" in error for error in errors),
            errors,
        )

    def test_claim_cannot_resolve_as_supported_from_partial_evidence(self) -> None:
        state = workspace_state()
        weak = evidence_entry()
        weak["status"] = "partial"
        state["evidence_log"] = [weak]
        state["base"] = "data_base"
        state["claim_log"] = [
            claim_event(),
            claim_event(
                "claim-event-two",
                sequence=2,
                status="resolved",
                resolution="supported",
                supersedes_event_ids=["claim-event-one"],
                resolution_evidence_ids=["evidence-one"],
            ),
        ]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("is not supported by its resolution evidence" in error for error in errors),
            errors,
        )

    def test_claim_can_be_withdrawn_from_contradictory_evidence(self) -> None:
        state = workspace_state()
        contradiction = evidence_entry()
        contradiction["status"] = "contradictory"
        state["evidence_log"] = [contradiction]
        state["base"] = "data_base"
        state["claim_log"] = [
            claim_event(),
            claim_event(
                "claim-event-two",
                sequence=2,
                status="resolved",
                resolution="withdrawn",
                supersedes_event_ids=["claim-event-one"],
                resolution_evidence_ids=["evidence-one"],
            ),
        ]

        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(state),
        )

    def test_first_claim_event_must_be_blocked(self) -> None:
        state = workspace_state()
        state["evidence_log"] = [evidence_entry()]
        state["claim_log"] = [
            claim_event(
                status="resolved",
                resolution="supported",
                resolution_evidence_ids=["evidence-one"],
            )
        ]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("first event" in error and "must be blocked" in error for error in errors),
            errors,
        )

    def test_evidence_base_tracks_current_usable_evidence(self) -> None:
        empty_data_base = workspace_state()
        empty_data_base["base"] = "data_base"
        errors = hypothesis_state.validate_state_semantics(empty_data_base)
        self.assertTrue(
            any("data_base requires" in error for error in errors),
            errors,
        )

        previous = workspace_state()
        previous["base"] = "data_base"
        previous["evidence_log"] = [evidence_entry()]
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        stale = evidence_entry()
        stale["evidence_id"] = "evidence-two"
        stale["sequence"] = 2
        stale["status"] = "stale"
        stale["supersedes_evidence_ids"] = ["evidence-one"]
        candidate["evidence_log"].append(stale)
        candidate["base"] = "null_base"
        proposal = change_set(
            candidate,
            change_id="change-base-regression",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )
        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )
        self.assertEqual([], errors)

    def test_base_change_is_explicit_in_revision_manifest(self) -> None:
        previous = workspace_state()
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["base"] = "data_base"
        candidate["evidence_log"].append(evidence_entry())
        proposal = change_set(
            candidate,
            change_id="change-base-explicit",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )
        proposal["change_manifest"]["base_change"] = None

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("evidence base change" in error for error in errors),
            errors,
        )

    def test_owner_approval_order_is_append_only(self) -> None:
        previous = workspace_state(
            hypothesis_record(state="running")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["owner_approvals"].reverse()
        proposal = change_set(
            candidate,
            change_id="change-reorder-approvals",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("approvals are append-only" in error for error in errors),
            errors,
        )

    def test_correction_can_only_supersede_earlier_evidence(self) -> None:
        state = workspace_state()
        invalid = evidence_entry()
        invalid["supersedes_evidence_ids"] = ["evidence-one"]
        state["evidence_log"] = [invalid]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("may supersede only earlier entries" in error for error in errors),
            errors,
        )

    def test_supported_nexus_entry_requires_supported_evidence(self) -> None:
        state = workspace_state()
        state["nexus_entries"] = [nexus_entry()]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("supported status lacks evidence" in error for error in errors),
            errors,
        )

    def test_nexus_decision_requires_bound_owner_authority(self) -> None:
        state = workspace_state()
        state["evidence_log"] = [evidence_entry()]
        state["base"] = "data_base"
        state["nexus_entries"] = [
            nexus_entry(
                kind="decision",
                evidence_ids=["evidence-one"],
            )
        ]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("lacks owner authority" in error for error in errors),
            errors,
        )

    def test_nexus_decision_subject_is_bound_to_owner_receipt(self) -> None:
        state = workspace_state()
        state["evidence_log"] = [evidence_entry()]
        state["base"] = "data_base"
        decision = nexus_entry(
            kind="decision",
            evidence_ids=["evidence-one"],
        )
        decision["decision_authority"] = {
            "owner_ref": "owner:demo",
            "owner_tenure_id": "tenure-initial",
            "decision_scope_id": "scope-initial",
            "decided_at": STAMP,
            "reversibility": "reversible",
            "safe_receipt_ref": "approval:nexus-decision",
            "subject_sha256": "0" * 64,
        }
        decision["decision_authority"]["subject_sha256"] = (
            hypothesis_state.nexus_decision_subject_sha256(
                decision,
                state["workspace_id"],
            )
        )
        state["nexus_entries"] = [decision]

        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )
        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(state),
        )
        self.assertEqual(
            [],
            registry.validate(
                state,
                hypothesis_state.WORKSPACE_SCHEMA,
            ),
        )

    def test_ready_state_rejects_unapproved_model_rule(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        record["validation"]["metrics"][0]["criterion_provenance"] = (
            "proposed_assumption"
        )
        state = workspace_state(record)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("proposed-assumption approval" in error for error in errors),
            errors,
        )

    def test_exact_replay_returns_same_receipt_without_rewrite(self) -> None:
        state = workspace_state()
        proposal = change_set(
            state,
            change_id="change-idempotent",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, first_receipt, error = self.commit(proposal)
        self.assertEqual(0, code, error)
        before = (
            self.root / hypothesis_state.BUNDLE_FILENAME
        ).read_bytes()

        code, second_receipt, error = self.commit(proposal)

        self.assertEqual(0, code, error)
        self.assertEqual(first_receipt, second_receipt)
        self.assertEqual(
            before,
            (self.root / hypothesis_state.BUNDLE_FILENAME).read_bytes(),
        )

    def test_bundle_verification_detects_receipt_state_hash_tampering(self) -> None:
        proposal = change_set(
            workspace_state(),
            change_id="change-tamper-check",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, _, error = self.commit(proposal)
        self.assertEqual(0, code, error)
        bundle = self.read_bundle()
        bundle["receipts"][0]["state_sha256"] = "0" * 64
        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )

        errors = hypothesis_state.validate_bundle_semantics(
            bundle, registry
        )

        self.assertTrue(
            any("state hash does not match" in error for error in errors),
            errors,
        )

    def test_proposal_chain_detects_paired_accepted_hash_rewrite(self) -> None:
        proposal = change_set(
            workspace_state(),
            change_id="change-proposal-chain-accepted",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, _, error = self.commit(proposal)
        self.assertEqual(0, code, error)
        bundle = self.read_bundle()
        bundle["receipts"][0]["change_set_sha256"] = "0" * 64
        bundle["handled_proposals"][0]["change_set_sha256"] = "0" * 64
        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )

        errors = hypothesis_state.validate_bundle_semantics(
            bundle,
            registry,
        )

        self.assertTrue(
            any(
                "proposal-attempt commitment hash" in item
                or "accepted receipt change-set hash" in item
                for item in errors
            ),
            errors,
        )

    def test_proposal_chain_detects_deleted_rejected_attempt(self) -> None:
        invalid = hypothesis_record(state="awaiting_owner_rule")
        proposal = change_set(
            workspace_state(invalid),
            change_id="change-proposal-chain-rejected",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, receipt, error = self.commit(proposal)
        self.assertEqual(4, code, error)
        self.assertEqual("rejected", receipt["status"])
        bundle = self.read_bundle()
        bundle["receipts"] = []
        bundle["handled_proposals"] = []
        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )

        errors = hypothesis_state.validate_bundle_semantics(
            bundle,
            registry,
        )

        self.assertTrue(
            any(
                "proposal-attempt history head" in item
                for item in errors
            ),
            errors,
        )

    def test_revision_chain_detects_archived_hypothesis_tampering(self) -> None:
        code, _, error = self.commit(
            change_set(
                workspace_state(),
                change_id="change-history-create",
                operation="create",
                expected_revision=None,
                previous=None,
            )
        )
        self.assertEqual(0, code, error)
        previous = self.read_bundle()["current_state"]
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["statement"] = "A refined, still unvalidated problem statement."
        code, _, error = self.commit(
            change_set(
                candidate,
                change_id="change-history-update",
                operation="replace",
                expected_revision=0,
                previous=previous,
            )
        )
        self.assertEqual(0, code, error)
        bundle = self.read_bundle()
        bundle["hypothesis_history"][0]["statement"] = (
            "A silently rewritten archived statement."
        )
        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )

        errors = hypothesis_state.validate_bundle_semantics(
            bundle,
            registry,
        )

        self.assertTrue(
            any("revision delta hash" in item for item in errors),
            errors,
        )

    def test_current_state_must_match_revision_chain_head(self) -> None:
        code, _, error = self.commit(
            change_set(
                workspace_state(),
                change_id="change-chain-head",
                operation="create",
                expected_revision=None,
                previous=None,
            )
        )
        self.assertEqual(0, code, error)
        bundle = self.read_bundle()
        bundle["current_state"]["revision_chain_head_sha256"] = "0" * 64
        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )

        errors = hypothesis_state.validate_bundle_semantics(bundle, registry)

        self.assertTrue(
            any("revision-chain head" in item for item in errors),
            errors,
        )

    def test_replace_rejects_pure_revision_churn(self) -> None:
        previous = workspace_state()
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        proposal = change_set(
            candidate,
            change_id="change-noop",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal,
            previous,
        )

        self.assertTrue(
            any("no substantive state change" in item for item in errors),
            errors,
        )

    def test_hypothesis_can_origin_from_nexus_added_in_same_revision(self) -> None:
        state = workspace_state()
        state["evidence_log"] = [evidence_entry()]
        state["base"] = "data_base"
        state["nexus_entries"] = [
            nexus_entry(evidence_ids=["evidence-one"])
        ]
        record = state["hypotheses"][0]
        record["origin"]["originating_entry_ids"] = ["nexus-one"]
        record["origin"]["nexus_revision"] = 0
        proposal = change_set(
            state,
            change_id="change-atomic-origin",
            operation="create",
            expected_revision=None,
            previous=None,
        )

        self.assertEqual(
            [],
            hypothesis_state.validate_change_semantics(proposal, None),
        )

    def test_reused_change_id_with_different_content_fails_closed(self) -> None:
        state = workspace_state()
        proposal = change_set(
            state,
            change_id="change-collision",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, _, error = self.commit(proposal)
        self.assertEqual(0, code, error)
        before = (
            self.root / hypothesis_state.BUNDLE_FILENAME
        ).read_bytes()

        changed = copy.deepcopy(proposal)
        changed["candidate_state"]["goal"]["outcome"] = (
            "A materially different proposal."
        )
        code, receipt, error = self.commit(changed)

        self.assertEqual(5, code)
        self.assertIsNone(receipt)
        self.assertIn("different content", error)
        self.assertEqual(
            before,
            (self.root / hypothesis_state.BUNDLE_FILENAME).read_bytes(),
        )

    def test_goal_change_requires_a_new_decision_scope_event(self) -> None:
        previous = workspace_state()
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["goal"]["outcome"] = "A different product goal."
        proposal = change_set(
            candidate,
            change_id="change-goal-rewrite",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("current goal does not match active decision scope" in error for error in errors),
            errors,
        )

    def test_new_decision_scope_preserves_product_nexus_history(self) -> None:
        previous = workspace_state()
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        next_goal = {
            "actor": "Product decision owner",
            "outcome": "Resolve the next product uncertainty.",
            "baseline": None,
            "target": None,
            "period": "Next decision horizon",
            "decision_to_unlock": "Choose the next bounded investment.",
        }
        candidate["decision_scope_log"].append(
            {
                "scope_id": "scope-next",
                "sequence": 2,
                "opened_at": "2026-07-26T11:00:00Z",
                "opened_workspace_revision": 1,
                "goal": next_goal,
                "predecessor_scope_id": "scope-initial",
                "transition_receipt_ref": "approval:scope-next",
                "reason": "The prior bounded decision scope ended.",
            }
        )
        candidate["active_decision_scope_id"] = "scope-next"
        candidate["goal"] = next_goal
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["state"] = "cancelled"
        record["verdict"] = "not_run"
        add_approval(
            record,
            "state_transition",
            "approval-close-old-scope",
        )
        candidate["focus_hypothesis_id"] = None
        proposal = change_set(
            candidate,
            change_id="change-open-next-scope",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )
        self.assertEqual(
            [],
            registry.validate(
                candidate,
                hypothesis_state.WORKSPACE_SCHEMA,
            ),
        )
        self.assertEqual(
            [],
            hypothesis_state.validate_change_semantics(
                proposal,
                previous,
            ),
        )

    def test_owner_transition_requires_new_tenure_bound_approval(self) -> None:
        previous = workspace_state(
            hypothesis_record(state="ready_to_run")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["owner_tenure_log"].append(
            {
                "tenure_id": "tenure-next",
                "sequence": 2,
                "effective_at": "2026-07-26T11:00:00Z",
                "effective_workspace_revision": 1,
                "owner_ref": "owner:next",
                "predecessor_tenure_id": "tenure-initial",
                "transition_receipt_ref": "approval:owner-transition",
                "reason": "Decision ownership changed.",
            }
        )
        candidate["active_owner_tenure_id"] = "tenure-next"
        candidate["decision_owner_ref"] = "owner:next"
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        add_approval(
            record,
            "decision_rule",
            "approval-next-owner-decision",
            owner_ref="owner:next",
            owner_tenure_id="tenure-next",
        )
        proposal = change_set(
            candidate,
            change_id="change-owner-tenure",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        self.assertEqual(
            [],
            hypothesis_state.validate_change_semantics(
                proposal,
                previous,
            ),
        )

    def test_owner_transition_can_invalidate_old_pending_request(
        self,
    ) -> None:
        record = hypothesis_record(state="awaiting_owner_rule")
        requirement = pending_requirement(
            record,
            "decision_rule",
            "change-open-old-owner-request",
        )
        record["pending_owner_approvals"] = [requirement]
        previous = workspace_state(record)
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["owner_tenure_log"].append(
            {
                "tenure_id": "tenure-next",
                "sequence": 2,
                "effective_at": "2026-07-26T11:00:00Z",
                "effective_workspace_revision": 1,
                "owner_ref": "owner:next",
                "predecessor_tenure_id": "tenure-initial",
                "transition_receipt_ref": "approval:owner-transition",
                "reason": "Decision ownership changed.",
            }
        )
        candidate["active_owner_tenure_id"] = "tenure-next"
        candidate["decision_owner_ref"] = "owner:next"
        candidate_record = candidate["hypotheses"][0]
        candidate_record["revision"] = 1
        candidate_record["updated_at"] = "2026-07-26T11:00:00Z"
        candidate_record["state"] = "framing"
        candidate_record["pending_owner_approvals"] = []
        candidate_record["pending_owner_resolutions"].append(
            {
                "resolution_id": "resolution-owner-transition",
                "resolved_at": "2026-07-26T11:00:00Z",
                "hypothesis_id": candidate_record["hypothesis_id"],
                "approval_scope": requirement["approval_scope"],
                "request_owner_tenure_id": requirement[
                    "owner_tenure_id"
                ],
                "subject_revision": requirement["subject_revision"],
                "subject_sha256": requirement["subject_sha256"],
                "resolution": "invalidated_by_tenure_transition",
                "authority_owner_ref": "owner:next",
                "authority_tenure_id": "tenure-next",
                "safe_receipt_ref": "approval:owner-transition",
                "reason": "The former owner request has no authority in the new tenure.",
            }
        )
        proposal = change_set(
            candidate,
            change_id="change-transition-with-old-pending",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )
        self.assertEqual(
            [],
            registry.validate(
                candidate,
                hypothesis_state.WORKSPACE_SCHEMA,
            ),
        )
        self.assertEqual(
            [],
            hypothesis_state.validate_change_semantics(
                proposal,
                previous,
            ),
        )

    def test_closing_after_owner_transition_requires_active_tenure_decision(
        self,
    ) -> None:
        previous = workspace_state(
            hypothesis_record(state="ready_for_review")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate["owner_tenure_log"].append(
            {
                "tenure_id": "tenure-next",
                "sequence": 2,
                "effective_at": "2026-07-26T11:00:00Z",
                "effective_workspace_revision": 1,
                "owner_ref": "owner:next",
                "predecessor_tenure_id": "tenure-initial",
                "transition_receipt_ref": "approval:owner-transition",
                "reason": "Decision ownership changed before closure.",
            }
        )
        candidate["active_owner_tenure_id"] = "tenure-next"
        candidate["decision_owner_ref"] = "owner:next"
        record = candidate["hypotheses"][0]
        closed = hypothesis_record(
            revision=1,
            state="closed",
            verdict="confirmed",
        )
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["state"] = "closed"
        record["verdict"] = "confirmed"
        record["evidence_ids"] = closed["evidence_ids"]
        record["result"] = closed["result"]
        add_approval(
            record,
            "terminal_verdict",
            "approval-old-owner-terminal",
        )
        candidate["evidence_log"] = [evidence_entry()]
        candidate["base"] = "data_base"
        candidate["focus_hypothesis_id"] = None
        proposal = change_set(
            candidate,
            change_id="change-owner-and-close",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal,
            previous,
        )

        self.assertTrue(
            any(
                "closing decision lacks decision_rule approval from the active owner tenure"
                in error
                for error in errors
            ),
            errors,
        )
        self.assertTrue(
            any(
                "closing decision lacks terminal_verdict approval from the active owner tenure"
                in error
                for error in errors
            ),
            errors,
        )

    def test_atomic_write_failure_preserves_previous_bundle(self) -> None:
        initial = workspace_state()
        create = change_set(
            initial,
            change_id="change-create-atomic",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, _, error = self.commit(create)
        self.assertEqual(0, code, error)
        before = (
            self.root / hypothesis_state.BUNDLE_FILENAME
        ).read_bytes()

        candidate = copy.deepcopy(initial)
        candidate["revision"] = 1
        candidate["hypotheses"][0]["revision"] = 1
        candidate["hypotheses"][0]["updated_at"] = "2026-07-26T11:00:00Z"
        candidate["hypotheses"][0]["statement"] = (
            "A revised but still unvalidated need statement."
        )
        replace = change_set(
            candidate,
            change_id="change-atomic-failure",
            operation="replace",
            expected_revision=0,
            previous=initial,
        )
        self.write_change(replace)
        with patch.object(
            hypothesis_state,
            "atomic_write",
            side_effect=OSError("injected"),
        ):
            code, _, error = self.run_main(
                [
                    "commit",
                    "--root",
                    str(self.root),
                    "--change-set",
                    str(self.change_path),
                ]
            )

        self.assertEqual(5, code, error)
        self.assertEqual(
            before,
            (self.root / hypothesis_state.BUNDLE_FILENAME).read_bytes(),
        )

    def test_non_standard_nan_is_rejected(self) -> None:
        state = workspace_state()
        state["goal"]["baseline"] = float("nan")
        proposal = change_set(
            state,
            change_id="change-nan",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        self.write_change(proposal)

        code, output, error = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )

        self.assertEqual(5, code)
        self.assertEqual("", output)
        self.assertIn("strict JSON", error)
        self.assertFalse(
            (self.root / hypothesis_state.BUNDLE_FILENAME).exists()
        )

    def test_change_set_size_is_bounded_before_json_parse(self) -> None:
        self.change_path.write_text(
            '{"padding":"' + ("x" * 512) + '"}\n',
            encoding="utf-8",
        )
        with patch.object(
            hypothesis_state,
            "MAX_CHANGE_SET_BYTES",
            128,
        ):
            code, output, error = self.run_main(
                [
                    "commit",
                    "--root",
                    str(self.root),
                    "--change-set",
                    str(self.change_path),
                ]
            )

        self.assertEqual(5, code)
        self.assertEqual("", output)
        self.assertIn("bounded size limit", error)

    def test_change_set_nesting_depth_is_bounded(self) -> None:
        depth = hypothesis_state.MAX_JSON_DEPTH + 10
        self.change_path.write_text(
            ("[" * depth) + "0" + ("]" * depth),
            encoding="utf-8",
        )

        code, output, error = self.run_main(
            [
                "commit",
                "--root",
                str(self.root),
                "--change-set",
                str(self.change_path),
            ]
        )

        self.assertEqual(5, code)
        self.assertEqual("", output)
        self.assertIn("nesting depth", error)

    def test_duplicate_json_object_keys_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            hypothesis_state.strict_json_loads(
                '{"workspace_id":"one","workspace_id":"two"}'
            )

    def test_sensitive_data_patterns_are_rejected_without_state(self) -> None:
        samples = (
            "Contact demo" + "@" + "example.com for evidence.",
            "Call " + "+1 202 555 0123" + " for evidence.",
            "Private " + "message follows with source content.",
        )
        for index, sample in enumerate(samples):
            with self.subTest(sample=sample):
                state = workspace_state()
                state["goal"]["outcome"] = sample
                proposal = change_set(
                    state,
                    change_id=f"change-sensitive-{index}",
                    operation="create",
                    expected_revision=None,
                    previous=None,
                )
                code, receipt, error = self.commit(proposal)
                self.assertEqual(4, code, error)
                self.assertEqual("rejected", receipt["status"])
                self.assertFalse(
                    receipt["validation"]["sensitive_data_scan_passed"]
                )
                self.assertIsNone(self.read_bundle()["current_state"])

    def test_bundle_symlink_is_rejected(self) -> None:
        self.root.mkdir(parents=True)
        outside = Path(self.temporary.name).resolve() / "outside.json"
        outside.write_text("unchanged\n", encoding="utf-8")
        bundle_path = self.root / hypothesis_state.BUNDLE_FILENAME
        try:
            bundle_path.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink creation is unavailable: {exc}")

        proposal = change_set(
            workspace_state(),
            change_id="change-symlink",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, receipt, error = self.commit(proposal)

        self.assertEqual(5, code)
        self.assertIsNone(receipt)
        self.assertIn("symlink", error)
        self.assertEqual("unchanged\n", outside.read_text(encoding="utf-8"))

    def test_running_requires_execution_evidence(self) -> None:
        record = hypothesis_record(state="running")
        record["execution_ref"] = None
        state = workspace_state(record)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("lacks host execution evidence" in error for error in errors),
            errors,
        )

    def test_approval_from_wrong_owner_is_rejected(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        record["owner_approvals"][0]["owner_ref"] = "owner:other"

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("does not match tenure" in error for error in errors),
            errors,
        )

    def test_approval_binding_fields_are_required_by_schema(self) -> None:
        state = workspace_state(
            hypothesis_record(state="ready_to_run")
        )
        state["hypotheses"][0]["owner_approvals"][0].pop("subject_sha256")
        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )

        errors = registry.validate(
            state,
            hypothesis_state.WORKSPACE_SCHEMA,
        )

        self.assertTrue(
            any("subject_sha256" in error for error in errors),
            errors,
        )

    def test_ready_validation_design_is_frozen(self) -> None:
        previous = workspace_state(
            hypothesis_record(state="ready_to_run")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["validation"]["metrics"][0]["criterion"] = "Changed after approval"
        proposal = change_set(
            candidate,
            change_id="change-frozen-rule",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("test contract is frozen" in error for error in errors),
            errors,
        )

    def test_ready_hypothesis_statement_is_part_of_frozen_contract(self) -> None:
        previous = workspace_state(
            hypothesis_record(state="ready_to_run")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["statement"] = "A different claim under the old approval."
        proposal = change_set(
            candidate,
            change_id="change-frozen-statement",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("test contract is frozen" in error for error in errors),
            errors,
        )

    def test_hypothesis_origin_cannot_be_rewritten(self) -> None:
        previous = workspace_state()
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["origin"]["reason"] = "A rewritten origin."
        proposal = change_set(
            candidate,
            change_id="change-origin-rewrite",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("origin is immutable" in error for error in errors),
            errors,
        )

    def test_ready_state_rejects_premature_result_claims(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        record["result"]["observations"] = ["The experiment succeeded."]
        record["result"]["interpretation"] = "Treat as confirmed."
        record["result"]["validity_status"] = "adequate"

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("premature result claims" in error for error in errors),
            errors,
        )

    def test_ready_for_review_rejects_a_premature_decision(self) -> None:
        record = hypothesis_record(state="ready_for_review")
        record["evidence_ids"] = ["evidence-one"]
        record["result"]["observations"] = ["The bounded run produced a result."]
        record["result"]["interpretation"] = "Validity review is still pending."
        record["result"]["decision_taken"] = "Ship globally now."

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("premature decision" in error for error in errors),
            errors,
        )

    def test_focus_cannot_point_to_a_terminal_hypothesis(self) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        state = workspace_state(record)
        state["focus_hypothesis_id"] = record["hypothesis_id"]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("points to a terminal hypothesis" in error for error in errors),
            errors,
        )

    def test_ready_state_requires_a_primary_metric(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        record["validation"]["metrics"] = []
        record["owner_approvals"] = []
        add_approval(
            record,
            "decision_rule",
            "approval-empty-metrics",
        )

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("no primary decision metric" in error for error in errors),
            errors,
        )

    def test_ready_state_requires_concrete_sample_and_time_window(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        sample = record["validation"]["sample"]
        sample["target_size"] = None
        sample["rationale"] = None
        sample["provenance"] = "unset"
        time_window = record["validation"]["time_window"]
        time_window["definition"] = None
        time_window["rationale"] = None
        time_window["provenance"] = "unset"
        record["owner_approvals"] = []
        add_approval(
            record,
            "decision_rule",
            "approval-incomplete-design",
        )

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("sample contract is incomplete" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("time-window contract is incomplete" in error for error in errors),
            errors,
        )

    def test_metric_ids_are_unique(self) -> None:
        record = hypothesis_record()
        duplicate = copy.deepcopy(record["validation"]["metrics"][0])
        duplicate["role"] = "diagnostic"
        record["validation"]["metrics"].append(duplicate)

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("duplicate metric_id" in error for error in errors),
            errors,
        )

    def test_closed_state_requires_interpretation_and_decision(self) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        record["result"]["interpretation"] = None
        record["result"]["decision_taken"] = None

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any(
                "closed without interpretation or decision" in error
                for error in errors
            ),
            errors,
        )

    def test_closed_state_must_return_evidence_bound_learning_to_nexus(
        self,
    ) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        record["result"]["new_nexus_entry_ids"] = []

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any(
                "closed without returning learning to Nexus" in error
                for error in errors
            ),
            errors,
        )

    def test_terminal_verdict_requires_supported_metric_evidence(self) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        state = workspace_state(record)
        state["evidence_log"][0]["status"] = "partial"

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("terminal verdict lacks supported evidence" in error for error in errors),
            errors,
        )

    def test_confirmed_verdict_must_match_primary_criterion_result(self) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        record["result"]["metric_results"][0][
            "criterion_evaluation"
        ] = "indeterminate"
        record["owner_approvals"] = [
            approval
            for approval in record["owner_approvals"]
            if approval["scope"] != "terminal_verdict"
        ]
        add_approval(
            record,
            "terminal_verdict",
            "approval-terminal-rebound",
        )

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("confirmed verdict conflicts" in error for error in errors),
            errors,
        )

    def test_review_requires_a_result_for_every_primary_metric(self) -> None:
        record = hypothesis_record(state="ready_for_review")
        record["evidence_ids"] = ["evidence-one"]
        record["result"]["observations"] = ["The bounded run produced a result."]
        record["result"]["interpretation"] = "Review is pending."
        record["result"]["validity_status"] = "limited"
        state = workspace_state(record)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("every primary metric" in error for error in errors),
            errors,
        )

    def test_verified_external_outcome_requires_evidence_and_host_receipt(
        self,
    ) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        record["result"]["external_outcome_status"] = "verified"

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("external outcome lacks evidence" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("verified outcome lacks host receipt" in error for error in errors),
            errors,
        )

    def test_verified_external_outcome_rejects_weak_evidence(self) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        record["result"]["external_outcome_status"] = "verified"
        record["result"]["outcome_evidence_ids"] = ["evidence-two"]
        record["result"]["external_outcome_receipt_ref"] = "receipt:outcome"
        record["owner_approvals"] = [
            approval
            for approval in record["owner_approvals"]
            if approval["scope"] != "terminal_verdict"
        ]
        add_approval(
            record,
            "terminal_verdict",
            "approval-terminal-outcome",
        )
        state = workspace_state(record)
        weak = evidence_entry()
        weak["evidence_id"] = "evidence-two"
        weak["sequence"] = 2
        weak["status"] = "partial"
        state["evidence_log"].append(weak)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("verified outcome lacks supported evidence" in error for error in errors),
            errors,
        )

    def test_observed_external_outcome_rejects_missing_evidence(self) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        record["result"]["external_outcome_status"] = "observed"
        record["result"]["outcome_evidence_ids"] = ["evidence-two"]
        record["owner_approvals"] = [
            approval
            for approval in record["owner_approvals"]
            if approval["scope"] != "terminal_verdict"
        ]
        add_approval(
            record,
            "terminal_verdict",
            "approval-terminal-observed-outcome",
        )
        state = workspace_state(record)
        missing = evidence_entry()
        missing["evidence_id"] = "evidence-two"
        missing["sequence"] = 2
        missing["status"] = "missing"
        state["evidence_log"].append(missing)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("observed outcome cites unusable evidence" in error for error in errors),
            errors,
        )

    def test_post_release_outcome_appends_after_terminal_hypothesis(
        self,
    ) -> None:
        initial = workspace_state(
            hypothesis_record(state="closed", verdict="confirmed")
        )
        code, _, error = self.commit(
            change_set(
                initial,
                change_id="change-close-before-outcome",
                operation="create",
                expected_revision=None,
                previous=None,
            )
        )
        self.assertEqual(0, code, error)
        previous = self.read_bundle()["current_state"]
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        outcome_evidence = evidence_entry()
        outcome_evidence["evidence_id"] = "evidence-outcome"
        outcome_evidence["sequence"] = 2
        candidate["evidence_log"].append(outcome_evidence)
        candidate["outcome_log"].append(outcome_event())
        proposal = change_set(
            candidate,
            change_id="change-observe-post-release-outcome",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        code, receipt, error = self.commit(proposal)

        self.assertEqual(0, code, error)
        self.assertEqual("accepted", receipt["status"])
        bundle = self.read_bundle()
        self.assertEqual(
            ["outcome-event-one"],
            [
                item["event_id"]
                for item in bundle["current_state"]["outcome_log"]
            ],
        )
        self.assertEqual(1, len(bundle["hypothesis_history"]))

    def test_outcome_log_rejects_weak_observed_evidence(self) -> None:
        state = workspace_state(
            hypothesis_record(state="closed", verdict="confirmed")
        )
        weak = evidence_entry()
        weak["evidence_id"] = "evidence-outcome"
        weak["sequence"] = 2
        weak["status"] = "missing"
        state["evidence_log"].append(weak)
        state["outcome_log"].append(outcome_event())

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any(
                "lacks supported outcome evidence" in error
                for error in errors
            ),
            errors,
        )

    def test_blocked_state_requires_an_unresolved_dependency(self) -> None:
        record = hypothesis_record(state="blocked_upstream")

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("blocked without an unresolved dependency" in error for error in errors),
            errors,
        )

    def test_upstream_dependency_cannot_reference_itself(self) -> None:
        record = hypothesis_record()
        record["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-self",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": record["hypothesis_id"],
                "required_class": "customer_need",
                "evidence_status": "supported",
                "evidence_ids": [],
            }
        ]

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("cannot depend on itself" in error for error in errors),
            errors,
        )

    def test_upstream_dependency_ids_are_unique(self) -> None:
        record = hypothesis_record()
        dependency = {
            "dependency_id": "dependency-duplicate",
            "mode": "prerequisite",
            "co_test_plan_ref": None,
            "hypothesis_id": None,
            "required_class": "customer_need",
            "evidence_status": "missing",
            "evidence_ids": [],
        }
        record["upstream_dependencies"] = [
            dependency,
            copy.deepcopy(dependency),
        ]

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("duplicate dependency_id" in error for error in errors),
            errors,
        )

    def test_upstream_dependency_graph_must_be_acyclic(self) -> None:
        first = hypothesis_record()
        second = hypothesis_record()
        second["hypothesis_id"] = "hypothesis-two"
        second["hypothesis_class"] = "value_proposition"
        first["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-one-to-two",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": second["hypothesis_id"],
                "required_class": "value_proposition",
                "evidence_status": "missing",
                "evidence_ids": [],
            }
        ]
        second["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-two-to-one",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": first["hypothesis_id"],
                "required_class": "customer_need",
                "evidence_status": "missing",
                "evidence_ids": [],
            }
        ]
        state = workspace_state(first)
        state["hypotheses"].append(second)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("contains a cycle" in error for error in errors),
            errors,
        )

    def test_linked_upstream_class_must_match_required_class(self) -> None:
        upstream = hypothesis_record()
        downstream = hypothesis_record()
        downstream["hypothesis_id"] = "hypothesis-two"
        downstream["hypothesis_class"] = "solution"
        downstream["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-upstream",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": upstream["hypothesis_id"],
                "required_class": "business_model",
                "evidence_status": "missing",
                "evidence_ids": [],
            }
        ]
        state = workspace_state(upstream)
        state["hypotheses"].append(downstream)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("upstream class does not match" in error for error in errors),
            errors,
        )

    def test_supported_upstream_requires_a_real_support_anchor(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        record["hypothesis_class"] = "solution"
        record["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-unanchored",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": None,
                "required_class": "customer_need",
                "evidence_status": "supported",
                "evidence_ids": [],
            }
        ]
        record["owner_approvals"] = []
        add_approval(
            record,
            "decision_rule",
            "approval-unanchored-decision",
        )

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("lacks supported direct evidence" in error for error in errors),
            errors,
        )

    def test_supported_upstream_accepts_supported_direct_evidence(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        record["hypothesis_class"] = "solution"
        record["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-direct-evidence",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": None,
                "required_class": "customer_need",
                "evidence_status": "supported",
                "evidence_ids": ["evidence-one"],
            }
        ]
        record["owner_approvals"] = []
        add_approval(
            record,
            "decision_rule",
            "approval-direct-evidence-decision",
        )
        state = workspace_state(record)
        supported = evidence_entry()
        supported["status"] = "supported"
        state["evidence_log"] = [supported]
        state["base"] = "data_base"

        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(state),
        )

    def test_supported_upstream_accepts_confirmed_linked_hypothesis(self) -> None:
        upstream = hypothesis_record(state="closed", verdict="confirmed")
        downstream = hypothesis_record(state="ready_to_run")
        downstream["hypothesis_id"] = "hypothesis-two"
        downstream["hypothesis_class"] = "solution"
        downstream["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-confirmed-need",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": upstream["hypothesis_id"],
                "required_class": "customer_need",
                "evidence_status": "supported",
                "evidence_ids": ["evidence-one"],
            }
        ]
        downstream["owner_approvals"] = []
        add_approval(
            downstream,
            "decision_rule",
            "approval-downstream-decision",
        )
        state = workspace_state(upstream)
        state["hypotheses"].append(downstream)
        state["focus_hypothesis_id"] = downstream["hypothesis_id"]

        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(state),
        )

    def test_superseded_upstream_learning_removes_current_dependency_authority(
        self,
    ) -> None:
        upstream = hypothesis_record(state="closed", verdict="confirmed")
        downstream = hypothesis_record(state="ready_to_run")
        downstream["hypothesis_id"] = "hypothesis-two"
        downstream["hypothesis_class"] = "value_proposition"
        downstream["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-stale-need",
                "mode": "prerequisite",
                "co_test_plan_ref": None,
                "hypothesis_id": upstream["hypothesis_id"],
                "required_class": "customer_need",
                "evidence_status": "supported",
                "evidence_ids": ["evidence-one"],
            }
        ]
        downstream["owner_approvals"] = []
        add_approval(
            downstream,
            "decision_rule",
            "approval-downstream-stale-decision",
        )
        state = workspace_state(upstream)
        state["hypotheses"].append(downstream)
        state["focus_hypothesis_id"] = downstream["hypothesis_id"]
        correction = evidence_entry()
        correction["evidence_id"] = "evidence-two"
        correction["sequence"] = 2
        correction["status"] = "contradictory"
        correction["supersedes_evidence_ids"] = ["evidence-one"]
        state["evidence_log"].append(correction)
        corrected_nexus = nexus_entry(
            "nexus-learning-two",
            sequence=2,
            status="contradictory",
            evidence_ids=["evidence-two"],
        )
        corrected_nexus["supersedes_entry_ids"] = [
            "nexus-learning-one"
        ]
        state["nexus_entries"].append(corrected_nexus)

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any(
                "upstream support lacks current supported evidence" in error
                for error in errors
            ),
            errors,
        )
        self.assertTrue(
            any(
                "upstream support lacks current Nexus authority" in error
                for error in errors
            ),
            errors,
        )

    def test_paf_value_and_solution_can_be_ready_as_a_bound_co_test(self) -> None:
        value = hypothesis_record(state="ready_to_run")
        value["hypothesis_class"] = "value_proposition"
        value["owner_approvals"] = []
        add_approval(
            value,
            "decision_rule",
            "approval-value-decision",
        )
        solution = hypothesis_record(state="ready_to_run")
        solution["hypothesis_id"] = "hypothesis-two"
        solution["hypothesis_class"] = "solution"
        solution["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-value-cotest",
                "mode": "co_test",
                "co_test_plan_ref": "plan:value-solution-soft-launch",
                "hypothesis_id": value["hypothesis_id"],
                "required_class": "value_proposition",
                "evidence_status": "partial",
                "evidence_ids": [],
            }
        ]
        solution["owner_approvals"] = []
        add_approval(
            solution,
            "decision_rule",
            "approval-solution-decision",
        )
        state = workspace_state(value)
        state["hypotheses"].append(solution)
        state["focus_hypothesis_id"] = solution["hypothesis_id"]

        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(state),
        )

    def test_paf_co_test_requires_a_plan_and_separate_peer_rules(self) -> None:
        value = hypothesis_record(state="ready_to_run")
        value["hypothesis_class"] = "value_proposition"
        value["owner_approvals"] = []
        solution = hypothesis_record(state="ready_to_run")
        solution["hypothesis_id"] = "hypothesis-two"
        solution["hypothesis_class"] = "solution"
        solution["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-unbound-cotest",
                "mode": "co_test",
                "co_test_plan_ref": None,
                "hypothesis_id": value["hypothesis_id"],
                "required_class": "value_proposition",
                "evidence_status": "partial",
                "evidence_ids": [],
            }
        ]
        solution["owner_approvals"] = []
        add_approval(
            solution,
            "decision_rule",
            "approval-solution-only",
        )
        state = workspace_state(value)
        state["hypotheses"].append(solution)
        state["focus_hypothesis_id"] = solution["hypothesis_id"]

        errors = hypothesis_state.validate_state_semantics(state)

        self.assertTrue(
            any("co-test lacks a plan ref" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("co-test peer lacks separate approved rules" in error for error in errors),
            errors,
        )

    def test_paf_co_test_can_leave_one_peer_open_after_other_closes(
        self,
    ) -> None:
        value = hypothesis_record(state="closed", verdict="confirmed")
        value["hypothesis_class"] = "value_proposition"
        value["owner_approvals"] = []
        add_approval(
            value,
            "decision_rule",
            "approval-value-closed-decision",
        )
        add_approval(
            value,
            "terminal_verdict",
            "approval-value-closed-terminal",
        )
        solution = hypothesis_record(state="ready_for_review")
        solution["hypothesis_id"] = "hypothesis-two"
        solution["hypothesis_class"] = "solution"
        solution["evidence_ids"] = ["evidence-one"]
        solution["result"]["observations"] = [
            "The shared run resolved the value proposition first."
        ]
        solution["result"]["interpretation"] = (
            "The solution result still requires owner review."
        )
        solution["result"]["validity_status"] = "adequate"
        solution["result"]["metric_results"] = copy.deepcopy(
            value["result"]["metric_results"]
        )
        solution["upstream_dependencies"] = [
            {
                "dependency_id": "dependency-value-cotest-open",
                "mode": "co_test",
                "co_test_plan_ref": "plan:value-solution-shared-run",
                "hypothesis_id": value["hypothesis_id"],
                "required_class": "value_proposition",
                "evidence_status": "partial",
                "evidence_ids": [],
            }
        ]
        solution["owner_approvals"] = []
        add_approval(
            solution,
            "decision_rule",
            "approval-solution-open-decision",
        )
        add_approval(
            solution,
            "state_transition",
            "approval-solution-open-transition",
        )
        state = workspace_state(value)
        state["hypotheses"].append(solution)
        state["focus_hypothesis_id"] = solution["hypothesis_id"]

        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(state),
        )

    def test_cancelled_state_requires_owner_transition_approval(self) -> None:
        record = hypothesis_record(state="cancelled", verdict="not_run")

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("lacks terminal transition approval" in error for error in errors),
            errors,
        )
        add_approval(
            record,
            "state_transition",
            "approval-cancel-transition",
        )
        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(workspace_state(record)),
        )

    def test_decision_rule_approval_carries_forward_when_subject_is_unchanged(
        self,
    ) -> None:
        previous = workspace_state(
            hypothesis_record(state="ready_to_run")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["state"] = "running"
        record["execution_ref"] = "execution:demo"
        add_approval(
            record,
            "state_transition",
            "approval-run-transition",
        )
        proposal = change_set(
            candidate,
            change_id="change-start-run",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertEqual([], errors)

    def test_rejected_approval_revokes_same_subject(self) -> None:
        record = hypothesis_record(state="ready_to_run")
        add_approval(
            record,
            "decision_rule",
            "approval-decision-revoked",
            decision="rejected",
            subject_revision=0,
        )

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("requires approved decision rules" in error for error in errors),
            errors,
        )

    def test_terminal_acceptance_ref_must_match_bound_approval(self) -> None:
        record = hypothesis_record(state="closed", verdict="confirmed")
        record["result"]["decision_owner_acceptance_ref"] = "approval:other"

        errors = hypothesis_state.validate_state_semantics(
            workspace_state(record)
        )

        self.assertTrue(
            any("terminal acceptance ref does not match" in error for error in errors),
            errors,
        )

    def test_awaiting_owner_rule_requires_exact_pending_requirement(self) -> None:
        record = hypothesis_record(state="awaiting_owner_rule")
        record["pending_owner_approvals"] = [
            pending_requirement(
                record,
                "decision_rule",
                "change-awaiting-owner",
            )
        ]
        state = workspace_state(record)
        proposal = change_set(
            state,
            change_id="change-awaiting-owner",
            operation="create",
            expected_revision=None,
            previous=None,
        )

        code, receipt, error = self.commit(proposal)

        self.assertEqual(0, code, error)
        self.assertEqual("accepted", receipt["status"])
        persisted = self.read_bundle()["current_state"]["hypotheses"][0]
        self.assertEqual(
            record["pending_owner_approvals"],
            persisted["pending_owner_approvals"],
        )

    def test_approved_awaiting_checkpoint_can_become_ready(self) -> None:
        record = hypothesis_record(state="awaiting_owner_rule")
        set_proposed_validation(record, approved=False)
        record["pending_owner_approvals"] = [
            pending_requirement(
                record,
                scope,
                "change-owner-checkpoint",
            )
            for scope in ("decision_rule", "proposed_assumption")
        ]
        initial = workspace_state(record)
        create = change_set(
            initial,
            change_id="change-owner-checkpoint",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, _, error = self.commit(create)
        self.assertEqual(0, code, error)
        persisted = self.read_bundle()["current_state"]

        candidate = copy.deepcopy(persisted)
        candidate["revision"] = 1
        candidate_record = candidate["hypotheses"][0]
        candidate_record["revision"] = 1
        candidate_record["updated_at"] = "2026-07-26T11:00:00Z"
        candidate_record["state"] = "ready_to_run"
        set_proposed_validation(candidate_record, approved=True)
        candidate_record["pending_owner_approvals"] = []
        add_approval(
            candidate_record,
            "decision_rule",
            "approval-owner-decision",
            subject_revision=0,
        )
        add_approval(
            candidate_record,
            "proposed_assumption",
            "approval-owner-assumption",
            subject_revision=0,
        )
        replace = change_set(
            candidate,
            change_id="change-owner-ready",
            operation="replace",
            expected_revision=0,
            previous=persisted,
        )

        code, receipt, error = self.commit(replace)

        self.assertEqual(0, code, error)
        self.assertEqual("accepted", receipt["status"])
        self.assertEqual(
            "ready_to_run",
            self.read_bundle()["current_state"]["hypotheses"][0]["state"],
        )

    def test_archived_pending_approval_binding_is_revalidated(self) -> None:
        record = hypothesis_record(state="awaiting_owner_rule")
        record["pending_owner_approvals"] = [
            pending_requirement(
                record,
                "decision_rule",
                "change-archive-pending",
            )
        ]
        initial = workspace_state(record)
        code, _, error = self.commit(
            change_set(
                initial,
                change_id="change-archive-pending",
                operation="create",
                expected_revision=None,
                previous=None,
            )
        )
        self.assertEqual(0, code, error)
        previous = self.read_bundle()["current_state"]
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate_record = candidate["hypotheses"][0]
        candidate_record["revision"] = 1
        candidate_record["updated_at"] = "2026-07-26T11:00:00Z"
        candidate_record["state"] = "ready_to_run"
        candidate_record["pending_owner_approvals"] = []
        template = hypothesis_record(revision=1, state="ready_to_run")
        candidate_record["validation"] = template["validation"]
        old_subject = copy.deepcopy(previous["hypotheses"][0])
        old_subject["owner_approvals"] = []
        resolved_old = add_approval(
            old_subject,
            "decision_rule",
            "approval-archive-old-rejected",
            decision="rejected",
        )
        candidate_record["owner_approvals"] = [resolved_old]
        add_approval(
            candidate_record,
            "decision_rule",
            "approval-archive-ready",
        )
        code, _, error = self.commit(
            change_set(
                candidate,
                change_id="change-archive-ready",
                operation="replace",
                expected_revision=0,
                previous=previous,
            )
        )
        self.assertEqual(0, code, error)
        bundle = self.read_bundle()
        bundle["hypothesis_history"][0]["pending_owner_approvals"][0][
            "owner_ref"
        ] = "owner:other"
        registry = hypothesis_state.SchemaRegistry(hypothesis_state.ASSET_ROOT)

        errors = hypothesis_state.validate_bundle_semantics(bundle, registry)

        self.assertTrue(
            any("pending owner does not match tenure" in item for item in errors),
            errors,
        )

    def test_awaiting_owner_rule_without_requirement_is_rejected(self) -> None:
        record = hypothesis_record(state="awaiting_owner_rule")
        state = workspace_state(record)
        proposal = change_set(
            state,
            change_id="change-awaiting-missing",
            operation="create",
            expected_revision=None,
            previous=None,
        )

        code, receipt, error = self.commit(proposal)

        self.assertEqual(4, code, error)
        self.assertEqual("rejected", receipt["status"])
        self.assertFalse(receipt["validation"]["semantic_valid"])
        replay_code, replay_receipt, replay_error = self.commit(proposal)
        self.assertEqual(4, replay_code, replay_error)
        self.assertEqual(receipt, replay_receipt)
        self.assertEqual(1, len(self.read_bundle()["receipts"]))
        verify_code, _, verify_error = self.run_main(
            ["verify", "--root", str(self.root)]
        )
        self.assertEqual(2, verify_code, verify_error)
        self.assertIn("no accepted workspace state", verify_error)

    def test_pending_owner_request_cannot_disappear_without_a_decision(
        self,
    ) -> None:
        record = hypothesis_record(state="awaiting_owner_rule")
        record["pending_owner_approvals"] = [
            pending_requirement(
                record,
                "decision_rule",
                "change-pending-open",
            )
        ]
        previous = workspace_state(record)
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate_record = candidate["hypotheses"][0]
        candidate_record["revision"] = 1
        candidate_record["updated_at"] = "2026-07-26T11:00:00Z"
        candidate_record["state"] = "framing"
        candidate_record["pending_owner_approvals"] = []
        proposal = change_set(
            candidate,
            change_id="change-drop-pending",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal,
            previous,
        )

        self.assertTrue(
            any("disappeared without a matching decision" in error for error in errors),
            errors,
        )

    def test_new_pending_owner_request_is_bound_to_current_change_set(
        self,
    ) -> None:
        previous = workspace_state()
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        candidate_record = candidate["hypotheses"][0]
        candidate_record["revision"] = 1
        candidate_record["updated_at"] = "2026-07-26T11:00:00Z"
        candidate_record["state"] = "awaiting_owner_rule"
        candidate_record["pending_owner_approvals"] = [
            pending_requirement(
                candidate_record,
                "decision_rule",
                "change-from-another-hypothesis",
            )
        ]
        proposal = change_set(
            candidate,
            change_id="change-current-owner-request",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal,
            previous,
        )

        self.assertTrue(
            any(
                "source does not match the current change set" in error
                for error in errors
            ),
            errors,
        )

    def test_required_approval_with_wrong_subject_hash_is_rejected(self) -> None:
        record = hypothesis_record(state="awaiting_owner_rule")
        record["pending_owner_approvals"] = [
            pending_requirement(
                record,
                "decision_rule",
                "change-awaiting-wrong-hash",
                subject_sha256="0" * 64,
            )
        ]
        state = workspace_state(record)
        proposal = change_set(
            state,
            change_id="change-awaiting-wrong-hash",
            operation="create",
            expected_revision=None,
            previous=None,
        )

        code, receipt, error = self.commit(proposal)

        self.assertEqual(4, code, error)
        self.assertEqual("rejected", receipt["status"])

    def test_execution_ref_is_immutable_after_start(self) -> None:
        previous = workspace_state(
            hypothesis_record(state="running")
        )
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["state"] = "ready_for_review"
        record["execution_ref"] = "execution:other"
        add_approval(
            record,
            "state_transition",
            "approval-review-transition",
        )
        proposal = change_set(
            candidate,
            change_id="change-execution-rewrite",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )

        errors = hypothesis_state.validate_change_semantics(
            proposal, previous
        )

        self.assertTrue(
            any("execution ref is immutable" in error for error in errors),
            errors,
        )

    def test_schema_registry_rejects_unknown_keyword(self) -> None:
        registry = object.__new__(hypothesis_state.SchemaRegistry)

        with self.assertRaises(hypothesis_state.AdapterError):
            registry._assert_supported_schema(
                {"type": "string", "maxItems": 1},
                "schema:test",
            )

    def test_custom_and_official_schema_validators_agree_on_fixture(self) -> None:
        try:
            from jsonschema import Draft202012Validator
            from referencing import Registry, Resource
        except ImportError:
            self.skipTest("optional jsonschema differential check unavailable")

        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )
        resource_registry = Registry().with_resources(
            [
                (
                    document["$id"],
                    Resource.from_contents(document),
                )
                for document in registry.documents.values()
            ]
        )
        official = Draft202012Validator(
            registry.documents[hypothesis_state.WORKSPACE_SCHEMA],
            registry=resource_registry,
        )
        valid = workspace_state()
        invalid = copy.deepcopy(valid)
        invalid.pop("workspace_id")

        self.assertEqual([], registry.validate(
            valid, hypothesis_state.WORKSPACE_SCHEMA
        ))
        self.assertEqual([], list(official.iter_errors(valid)))
        self.assertTrue(registry.validate(
            invalid, hypothesis_state.WORKSPACE_SCHEMA
        ))
        self.assertTrue(list(official.iter_errors(invalid)))

    def test_official_validator_accepts_all_schema_documents(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("optional jsonschema meta-validation unavailable")

        registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )
        for schema_name, document in registry.documents.items():
            with self.subTest(schema=schema_name):
                Draft202012Validator.check_schema(document)

    def test_official_validator_accepts_committed_bundle_fixture(self) -> None:
        try:
            from jsonschema import Draft202012Validator
            from referencing import Registry, Resource
        except ImportError:
            self.skipTest("optional jsonschema bundle validation unavailable")

        code, _, error = self.commit(
            change_set(
                workspace_state(),
                change_id="change-official-bundle-fixture",
                operation="create",
                expected_revision=None,
                previous=None,
            )
        )
        self.assertEqual(0, code, error)
        schema_registry = hypothesis_state.SchemaRegistry(
            hypothesis_state.ASSET_ROOT
        )
        resource_registry = Registry().with_resources(
            [
                (
                    document["$id"],
                    Resource.from_contents(document),
                )
                for document in schema_registry.documents.values()
            ]
        )
        official = Draft202012Validator(
            schema_registry.documents[hypothesis_state.BUNDLE_SCHEMA],
            registry=resource_registry,
        )

        self.assertEqual(
            [],
            list(official.iter_errors(self.read_bundle())),
        )

    def test_lock_recovery_requires_exact_dead_pid(self) -> None:
        self.root.mkdir(parents=True)
        lock_path = self.root / hypothesis_state.LOCK_FILENAME
        lock_token = "a" * 32
        lock_payload = {
            "pid": os.getpid(),
            "host": hypothesis_state.socket.gethostname(),
            "token": lock_token,
            "created_at": STAMP,
            "purpose": "product-decision-paf-state-commit",
            "bundle_temp_filename": hypothesis_state.bundle_temp_filename(
                lock_token
            ),
            "owner_filename": hypothesis_state.lock_owner_filename(
                lock_token
            ),
        }
        lock_path.write_text(
            json.dumps(lock_payload)
            + "\n",
            encoding="utf-8",
        )
        code, output, error = self.run_main(
            ["inspect-lock", "--root", str(self.root)]
        )
        self.assertEqual(0, code, error)
        self.assertEqual("alive", json.loads(output)["owner_process_status"])

        code, _, error = self.run_main(
            [
                "recover-lock",
                "--root",
                str(self.root),
                "--expected-pid",
                str(os.getpid()),
                "--expected-token",
                lock_token,
            ]
        )
        self.assertEqual(5, code)
        self.assertIn("not proven dead", error)
        self.assertTrue(lock_path.exists())

        dead_pid = 2147483647
        lock_payload["pid"] = dead_pid
        lock_temp = (
            self.root / lock_payload["bundle_temp_filename"]
        )
        lock_temp.write_text("staged\n", encoding="utf-8")
        lock_path.write_text(
            json.dumps(lock_payload)
            + "\n",
            encoding="utf-8",
        )
        with hypothesis_state.lock_operation_gate(self.root):
            code, _, error = self.run_main(
                [
                    "recover-lock",
                    "--root",
                    str(self.root),
                    "--expected-pid",
                    str(dead_pid),
                    "--expected-token",
                    lock_token,
                ]
            )
            self.assertEqual(5, code)
            self.assertIn(
                "another lock operation is already in progress",
                error,
            )
            with self.assertRaisesRegex(
                hypothesis_state.AdapterError,
                "another lock operation is already in progress",
            ):
                with hypothesis_state.exclusive_lock(self.root):
                    self.fail("lock publication must share the recovery gate")
            self.assertTrue(lock_path.exists())
            self.assertTrue(lock_temp.exists())
        code, output, error = self.run_main(
            [
                "recover-lock",
                "--root",
                str(self.root),
                "--expected-pid",
                str(dead_pid),
                "--expected-token",
                lock_token,
            ]
        )
        self.assertEqual(0, code, error)
        self.assertEqual("recovered", json.loads(output)["status"])
        self.assertFalse(lock_path.exists())
        self.assertFalse(lock_temp.exists())
        gate_path = self.root / hypothesis_state.LOCK_GATE_FILENAME
        self.assertEqual(b"\0", gate_path.read_bytes())

    def test_accepted_commit_survives_lock_cleanup_failure(self) -> None:
        proposal = change_set(
            workspace_state(),
            change_id="change-accepted-lock-cleanup-warning",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        original_unlink = Path.unlink

        def fail_main_lock_unlink(path: Path, *args, **kwargs) -> None:
            if path.name == hypothesis_state.LOCK_FILENAME:
                raise PermissionError("simulated lock cleanup failure")
            original_unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", new=fail_main_lock_unlink):
            code, receipt, error = self.commit(proposal)

        self.assertEqual(0, code, error)
        self.assertEqual("accepted", receipt["status"])
        warning = json.loads(error)
        self.assertEqual("lock_cleanup_required", warning["warning"])
        self.assertTrue(warning["authoritative_result_unchanged"])
        self.assertEqual("lock_record_remove", warning["stage"])
        bundle = self.read_bundle()
        self.assertEqual(0, bundle["current_state"]["revision"])
        self.assertEqual("accepted", bundle["receipts"][-1]["status"])

        lock_path = self.root / hypothesis_state.LOCK_FILENAME
        lock_payload = json.loads(lock_path.read_text(encoding="utf-8"))
        self.assertEqual(warning["lock_id"], lock_payload["token"])
        with patch.object(
            hypothesis_state,
            "process_liveness",
            return_value="dead",
        ):
            recover_code, output, recover_error = self.run_main(
                [
                    "recover-lock",
                    "--root",
                    str(self.root),
                    "--expected-pid",
                    str(lock_payload["pid"]),
                    "--expected-token",
                    lock_payload["token"],
                ]
            )
        self.assertEqual(0, recover_code, recover_error)
        self.assertEqual("recovered", json.loads(output)["status"])
        self.assertFalse(lock_path.exists())

    def test_post_replace_readback_failure_is_outcome_unknown(self) -> None:
        proposal = change_set(
            workspace_state(),
            change_id="change-outcome-unknown",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        original_load_json = hypothesis_state.load_json

        def fail_written_readback(path, label, **kwargs):
            if label == "written hypothesis state bundle":
                raise hypothesis_state.AdapterError("injected readback failure")
            return original_load_json(path, label, **kwargs)

        with patch.object(
            hypothesis_state,
            "load_json",
            side_effect=fail_written_readback,
        ):
            code, receipt, error = self.commit(proposal)

        self.assertEqual(6, code)
        self.assertIsNone(receipt)
        self.assertIn("OUTCOME UNKNOWN", error)
        verify_code, _, verify_error = self.run_main(
            ["verify", "--root", str(self.root)]
        )
        self.assertEqual(0, verify_code, verify_error)

    def test_owner_approval_subject_hash_golden_vector(self) -> None:
        record = hypothesis_record()

        digest = hypothesis_state.approval_subject_sha256(
            record,
            "decision_rule",
            "workspace-demo",
            "tenure-initial",
            0,
        )

        self.assertEqual(
            "8f0010168b5abbf7bcc363a092515fe5f43a2c6e9c161830ab4746bbe286ef63",
            digest,
        )

    def test_accepted_receipt_schema_requires_every_gate_to_pass(self) -> None:
        proposal = change_set(
            workspace_state(),
            change_id="change-receipt-validation",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, receipt, error = self.commit(proposal)
        self.assertEqual(0, code, error)
        receipt["validation"]["semantic_valid"] = False
        registry = hypothesis_state.SchemaRegistry(hypothesis_state.ASSET_ROOT)

        errors = registry.validate(
            receipt,
            hypothesis_state.RECEIPT_SCHEMA,
        )

        self.assertTrue(
            any("semantic_valid" in item and "constant" in item for item in errors),
            errors,
        )

    def test_bundle_rejects_receipt_from_another_adapter(self) -> None:
        proposal = change_set(
            workspace_state(),
            change_id="change-adapter-binding",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, _, error = self.commit(proposal)
        self.assertEqual(0, code, error)
        bundle = self.read_bundle()
        bundle["receipts"][0]["adapter"] = "robin"
        self.bundle_path().write_text(
            json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        verify_code, _, verify_error = self.run_main(
            ["verify", "--root", str(self.root)]
        )

        self.assertEqual(5, verify_code)
        self.assertTrue(
            "another adapter" in verify_error
            or "receipt commitment" in verify_error,
            verify_error,
        )

    def test_reference_adapter_enforces_bundle_size_on_load(self) -> None:
        proposal = change_set(
            workspace_state(),
            change_id="change-size-bound",
            operation="create",
            expected_revision=None,
            previous=None,
        )
        code, _, error = self.commit(proposal)
        self.assertEqual(0, code, error)

        with patch.object(
            hypothesis_state,
            "MAX_BUNDLE_BYTES",
            self.bundle_path().stat().st_size - 1,
        ):
            verify_code, _, verify_error = self.run_main(
                ["verify", "--root", str(self.root)]
            )

        self.assertEqual(5, verify_code)
        self.assertIn("size limit", verify_error)

    def test_incremental_bundle_avoids_repeated_full_workspace_snapshots(
        self,
    ) -> None:
        initial = workspace_state()
        code, _, error = self.commit(
            change_set(
                initial,
                change_id="change-growth-000",
                operation="create",
                expected_revision=None,
                previous=None,
            )
        )
        self.assertEqual(0, code, error)
        sizes: dict[int, int] = {}

        for revision in range(1, 21):
            previous = self.read_bundle()["current_state"]
            candidate = copy.deepcopy(previous)
            candidate["revision"] = revision
            record = candidate["hypotheses"][0]
            record["revision"] = revision
            record["updated_at"] = f"2026-07-26T10:{revision:02d}:00Z"
            item = evidence_entry()
            item["evidence_id"] = f"evidence-{revision:03d}"
            item["sequence"] = revision
            item["summary"] = "x" * 200
            candidate["evidence_log"].append(item)
            candidate["base"] = "data_base"
            record["evidence_ids"].append(item["evidence_id"])
            code, _, error = self.commit(
                change_set(
                    candidate,
                    change_id=f"change-growth-{revision:03d}",
                    operation="replace",
                    expected_revision=revision - 1,
                    previous=previous,
                )
            )
            self.assertEqual(0, code, error)
            if revision in {10, 20}:
                sizes[revision] = self.bundle_path().stat().st_size

        bundle = self.read_bundle()
        self.assertEqual(21, len(bundle["revision_history"]))
        self.assertEqual(21, len(bundle["hypothesis_history"]))
        self.assertLess(sizes[20], sizes[10] * 2.2)

    def test_schema_numeric_values_are_bounded_safe_integers(self) -> None:
        registry = hypothesis_state.SchemaRegistry(hypothesis_state.ASSET_ROOT)

        def numeric_contracts(value: object, path: str = "$"):
            if isinstance(value, dict):
                if value.get("type") in {"integer", "number"}:
                    yield path, value
                for key, child in value.items():
                    yield from numeric_contracts(child, f"{path}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from numeric_contracts(child, f"{path}[{index}]")

        for schema_name, schema in registry.documents.items():
            for path, contract in numeric_contracts(schema):
                with self.subTest(schema=schema_name, path=path):
                    self.assertEqual("integer", contract.get("type"))
                    self.assertIn("minimum", contract)
                    self.assertEqual(
                        hypothesis_state.MAX_SAFE_INTEGER,
                        contract.get("maximum"),
                    )

    def test_canonical_json_rejects_non_nfc_text_and_unsafe_integers(self) -> None:
        for value in (
            {"label": "Cafe\u0301"},
            {"Cafe\u0301": "value"},
            {"count": hypothesis_state.MAX_SAFE_INTEGER + 1},
            {"count": -(hypothesis_state.MAX_SAFE_INTEGER + 1)},
            {"amount": 12.5},
            {"text": "\ud800"},
            {"\udfff": "text"},
        ):
            with self.subTest(value=value):
                with self.assertRaises(hypothesis_state.AdapterError):
                    hypothesis_state.canonical_bytes(value)

    def test_canonical_decimal_schema_and_hash_have_portable_vectors(self) -> None:
        registry = hypothesis_state.SchemaRegistry(hypothesis_state.ASSET_ROOT)
        canonical_state = workspace_state()
        canonical_evidence = evidence_entry()
        canonical_evidence["numerator"] = "12.5"
        canonical_evidence["denominator"] = "100"
        canonical_state["evidence_log"] = [canonical_evidence]
        canonical_state["base"] = "data_base"
        self.assertEqual(
            [],
            registry.validate(
                canonical_state,
                hypothesis_state.WORKSPACE_SCHEMA,
            ),
        )

        for non_canonical in (12.5, "12.50", "01", "-0", "0.0", "1e3"):
            invalid_state = copy.deepcopy(canonical_state)
            invalid_state["evidence_log"][0]["numerator"] = non_canonical
            with self.subTest(non_canonical=non_canonical):
                self.assertTrue(
                    registry.validate(
                        invalid_state,
                        hypothesis_state.WORKSPACE_SCHEMA,
                    )
                )

        vector = {
            "amount": "12.5",
            "count": hypothesis_state.MAX_SAFE_INTEGER,
            "\u00e9": "caf\u00e9",
        }
        self.assertEqual(
            b'{"amount":"12.5","count":9007199254740991,'
            b'"\xc3\xa9":"caf\xc3\xa9"}',
            hypothesis_state.canonical_bytes(vector),
        )
        self.assertEqual(
            "504d1444d22795d3ba6c700794440ac77b6d03721fcc9206289caa3a92551c1e",
            hypothesis_state.sha256_bytes(
                hypothesis_state.canonical_bytes(vector)
            ),
        )
        utf16_order_vector = {
            "\ue000": "bmp",
            "\U00010000": "astral",
        }
        self.assertEqual(
            b'{"\xf0\x90\x80\x80":"astral","\xee\x80\x80":"bmp"}',
            hypothesis_state.canonical_bytes(utf16_order_vector),
        )
        self.assertEqual(
            "5e72745dd500f8b8d997ef851679707b89099da29d2aca4b93dfd85810ebaa20",
            hypothesis_state.sha256_bytes(
                hypothesis_state.canonical_bytes(utf16_order_vector)
            ),
        )

    def test_relation_graph_is_acyclic_and_replacement_target_is_superseded(
        self,
    ) -> None:
        first = hypothesis_record()
        second = hypothesis_record()
        second["hypothesis_id"] = "hypothesis-two"
        first["relations"]["based_on_hypothesis_ids"] = ["hypothesis-two"]
        second["relations"]["based_on_hypothesis_ids"] = ["hypothesis-one"]
        cyclic = workspace_state(first)
        cyclic["hypotheses"].append(second)

        errors = hypothesis_state.validate_state_semantics(cyclic)

        self.assertTrue(
            any("hypothesis relation graph contains a cycle" in error for error in errors),
            errors,
        )

        current = hypothesis_record()
        replacement = hypothesis_record()
        replacement["hypothesis_id"] = "hypothesis-two"
        replacement["relations"]["replaces_hypothesis_id"] = "hypothesis-one"
        invalid_replacement = workspace_state(current)
        invalid_replacement["hypotheses"].append(replacement)
        errors = hypothesis_state.validate_state_semantics(invalid_replacement)
        self.assertTrue(
            any(
                "replacement target is not a closed or superseded record"
                in error
                for error in errors
            ),
            errors,
        )

        superseded = hypothesis_record(state="superseded", verdict="not_run")
        add_approval(
            superseded,
            "state_transition",
            "approval-superseded-for-replacement",
        )
        valid_replacement = workspace_state(superseded)
        valid_replacement["hypotheses"].append(replacement)
        valid_replacement["focus_hypothesis_id"] = "hypothesis-two"
        self.assertEqual(
            [],
            hypothesis_state.validate_state_semantics(valid_replacement),
        )

    def test_new_nexus_learning_is_bound_to_same_revision_run_evidence(
        self,
    ) -> None:
        previous = workspace_state(hypothesis_record(state="running"))
        candidate = copy.deepcopy(previous)
        candidate["revision"] = 1
        record = candidate["hypotheses"][0]
        record["revision"] = 1
        record["updated_at"] = "2026-07-26T11:00:00Z"
        record["state"] = "ready_for_review"
        first_evidence = evidence_entry()
        second_evidence = evidence_entry()
        second_evidence["evidence_id"] = "evidence-two"
        second_evidence["sequence"] = 2
        candidate["evidence_log"] = [first_evidence, second_evidence]
        candidate["base"] = "data_base"
        record["evidence_ids"] = ["evidence-one"]
        record["result"]["observations"] = ["A bounded run observation."]
        record["result"]["interpretation"] = "Ready for owner review."
        record["result"]["validity_status"] = "adequate"
        record["result"]["metric_results"] = [
            {
                "metric_id": "metric-primary",
                "evidence_ids": ["evidence-one"],
                "observation_period": {"start": None, "end": None},
                "observed_summary": "The primary criterion was evaluated.",
                "actual_numerator": "4",
                "actual_denominator": "10",
                "actual_sample_size": 10,
                "criterion_evaluation": "met",
                "validity_status": "adequate",
            }
        ]
        record["result"]["new_nexus_entry_ids"] = ["nexus-learning"]
        candidate["nexus_entries"] = [
            nexus_entry(
                "nexus-learning",
                evidence_ids=["evidence-one"],
            )
        ]
        add_approval(
            record,
            "state_transition",
            "approval-ready-for-review",
        )
        valid_change = change_set(
            candidate,
            change_id="change-bound-nexus-learning",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )
        self.assertEqual(
            [],
            hypothesis_state.validate_change_semantics(
                valid_change,
                previous,
            ),
        )

        invalid_candidate = copy.deepcopy(candidate)
        invalid_candidate["nexus_entries"][0]["evidence_ids"] = [
            "evidence-two"
        ]
        invalid_change = change_set(
            invalid_candidate,
            change_id="change-unbound-nexus-learning",
            operation="replace",
            expected_revision=0,
            previous=previous,
        )
        errors = hypothesis_state.validate_change_semantics(
            invalid_change,
            previous,
        )
        self.assertTrue(
            any("not bound to its run evidence" in error for error in errors),
            errors,
        )

    def test_adapter_rejects_state_root_inside_package(self) -> None:
        with self.assertRaises(hypothesis_state.AdapterError):
            hypothesis_state.ensure_state_root(
                hypothesis_state.PACKAGE_ROOT / "private-state",
                create=False,
            )


if __name__ == "__main__":
    unittest.main()
