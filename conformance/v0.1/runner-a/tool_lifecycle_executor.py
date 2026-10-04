#!/usr/bin/env python3

from tool_predicates import (
    deny_decision_on_proposal,
    proposal_output_boundary,
    require_no_tool_execution,
    require_no_tool_invocation,
    tool_argument_json_pointer_paths,
    tool_argument_model_provenance,
    tool_decision_on_proposal,
)


TOOL_LIFECYCLE_PLANNED_TESTS = {
    "tool-result-capture-bounded-001",
    "tool-effect-result-basis-bounded-001",
    "tool-effect-not-outcome-001",
    "tool-deny-proposal-no-invocation-001",
    "tool-deny-no-execution-001",
    "tool-proposal-no-invocation-001",
    "tool-proposal-no-authorization-001",
    "tool-argument-provenance-positive-001",
    "tool-argument-model-supplied-bounded-001",
    "tool-argument-json-pointer-001",
    "tool-allow-no-execution-001",
}


def records(receipt):
    return receipt.get("arp", {}).get("records", [])


def receipt_id(receipt):
    return receipt.get("arp", {}).get("receipt_id")


def by_kind(receipt, kind):
    return [
        record
        for record in records(receipt)
        if isinstance(record, dict) and record.get("kind") == kind
    ]


def record_index(receipt):
    return {
        record["id"]: record
        for record in records(receipt)
        if isinstance(record, dict) and record.get("id")
    }


def ref_id(value):
    return value.get("id") if isinstance(value, dict) else None


def resolve_local(index, reference, expected_kind):
    if not isinstance(reference, dict) or reference.get("ref_type") != "local":
        raise ValueError(f"{expected_kind} reference is not local")
    target = index.get(ref_id(reference))
    if not isinstance(target, dict) or target.get("kind") != expected_kind:
        raise ValueError(f"{expected_kind} reference did not resolve to expected kind")
    if reference.get("expected_kind") not in {None, expected_kind}:
        raise ValueError(f"{expected_kind} reference declares wrong expected_kind")
    return target


def finding(requirement_id, check_id, receipt, object_id, domain, status, prohibited=None):
    out = {
        "requirement_id": requirement_id,
        "check_id": check_id,
        "subject_scope": {
            "receipt_id": receipt_id(receipt),
            "object_id": object_id,
        },
        "domain": domain,
        "status": status,
    }
    if prohibited:
        out["prohibited_inferences"] = list(prohibited)
    return out


def primary_receipt(case, materialized):
    ids = (case.get("harness") or {}).get("primary_documents", [])
    receipts = [
        materialized[document_id]
        for document_id in ids
        if (
            document_id in materialized
            and materialized[document_id].get("kind") == "ReceiptPresentation"
        )
    ]
    if len(receipts) != 1:
        raise ValueError(
            f"tool result/effect batch requires one primary receipt, found {len(receipts)}"
        )
    return receipts[0]


def tool_result_effect_chain(receipt):
    index = record_index(receipt)
    chains = []

    for effect in by_kind(receipt, "EffectObservation"):
        execution = resolve_local(index, effect.get("execution"), "ToolExecution")
        invocation = resolve_local(index, execution.get("invocation"), "ToolInvocation")
        result = resolve_local(index, effect.get("result"), "ToolResult")
        result_execution = resolve_local(
            index, result.get("execution"), "ToolExecution"
        )

        if result_execution.get("id") != execution.get("id"):
            raise ValueError("EffectObservation result belongs to a different ToolExecution")

        run_ids = {
            invocation.get("run_id"),
            execution.get("run_id"),
            result.get("run_id"),
            effect.get("run_id"),
        }
        if None in run_ids or len(run_ids) != 1:
            raise ValueError("tool invocation/execution/result/effect changed run occurrence")

        chains.append((invocation, execution, result, effect))

    if len(chains) != 1:
        raise ValueError(
            f"tool result/effect bounded-claims batch requires one effect chain, found {len(chains)}"
        )

    return chains[0]


def complete_tool_result(receipt):
    _invocation, _execution, result, _effect = tool_result_effect_chain(receipt)
    if result.get("capture_extent") != "complete":
        raise ValueError("ToolResult does not establish complete captured-result extent")
    return result


def execution_result_effect(receipt):
    _invocation, _execution, result, effect = tool_result_effect_chain(receipt)
    if effect.get("basis") != "execution_result":
        raise ValueError("EffectObservation is not based on execution_result")
    if not isinstance(effect.get("proposition"), str) or not effect.get("proposition"):
        raise ValueError("EffectObservation proposition is missing")
    return result, effect


def execute_tool_lifecycle_case(row, case, materialized):
    requirement_id = row["requirement_id"]
    check_id = row["planned_test_id"]
    if check_id not in TOOL_LIFECYCLE_PLANNED_TESTS:
        raise NotImplementedError(check_id)

    receipt = primary_receipt(case, materialized)

    if check_id == "tool-result-capture-bounded-001":
        result = complete_tool_result(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                result["id"],
                domain="completeness",
                status="established",
                prohibited=[
                    "P1:complete_tool_result_capture_proves_remote_state_or_truth"
                ],
            )
        ]

    elif check_id == "tool-effect-result-basis-bounded-001":
        _result, effect = execution_result_effect(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                effect["id"],
                domain="claim",
                status="asserted",
                prohibited=[
                    "P1:execution_result_basis_is_independent_external_verification"
                ],
            )
        ]

    elif check_id == "tool-effect-not-outcome-001":
        _result, effect = execution_result_effect(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                effect["id"],
                domain="claim",
                status="asserted",
                prohibited=[
                    "P1:effect_observation_implies_desired_outcome_achieved"
                ],
            )
        ]

    elif check_id == "tool-deny-proposal-no-invocation-001":
        decision, _proposal = deny_decision_on_proposal(receipt)
        require_no_tool_invocation(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                decision["id"],
                domain="conformance",
                status="valid",
            )
        ]

    elif check_id == "tool-deny-no-execution-001":
        decision, _proposal = deny_decision_on_proposal(receipt)
        require_no_tool_execution(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                decision["id"],
                domain="conformance",
                status="valid",
                prohibited=["P1:deny_decision_creates_execution"],
            )
        ]

    elif check_id == "tool-proposal-no-invocation-001":
        proposal, _output = proposal_output_boundary(receipt)
        require_no_tool_invocation(receipt)
        require_no_tool_execution(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                proposal["id"],
                domain="conformance",
                status="valid",
                prohibited=["P1:tool_proposal_implies_invocation"],
            )
        ]

    elif check_id == "tool-proposal-no-authorization-001":
        proposal, _output = proposal_output_boundary(receipt)
        require_no_tool_invocation(receipt)
        require_no_tool_execution(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                proposal["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:tool_proposal_implies_authorization"],
            )
        ]

    elif check_id == "tool-argument-provenance-positive-001":
        _proposal, invocation, _derivation, _transform = tool_argument_model_provenance(
            receipt, pointer="/title"
        )
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                invocation["id"],
                domain="conformance",
                status="valid",
            )
        ]

    elif check_id == "tool-argument-model-supplied-bounded-001":
        _proposal, invocation, _derivation, _transform = tool_argument_model_provenance(
            receipt, pointer="/title"
        )
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                invocation["id"],
                domain="claim",
                status="asserted",
                prohibited=[
                    "P1:model_supplied_means_hidden_model_origin_or_causal_responsibility"
                ],
            )
        ]

    elif check_id == "tool-argument-json-pointer-001":
        invocation, _checked_paths = tool_argument_json_pointer_paths(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                invocation["id"],
                domain="conformance",
                status="valid",
            )
        ]

    elif check_id == "tool-allow-no-execution-001":
        decision, _proposal = tool_decision_on_proposal(receipt, "allow")
        require_no_tool_execution(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                decision["id"],
                domain="conformance",
                status="valid",
                prohibited=["P1:allow_decision_implies_execution"],
            )
        ]

    else:
        raise NotImplementedError(check_id)

    return {
        "findings": findings,
        "process_outcome": "completed",
        "completeness": {},
    }
