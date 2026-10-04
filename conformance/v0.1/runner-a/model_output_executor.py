#!/usr/bin/env python3


MODEL_OUTPUT_PLANNED_TESTS = {
    "model-output-boundary-001",
    "model-capture-complete-scope-001",
    "model-text-no-hidden-reasoning-001",
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
            f"model-output batch requires one primary receipt, found {len(receipts)}"
        )
    return receipts[0]


def resolve_local(index, reference, expected_kind):
    if not isinstance(reference, dict) or reference.get("ref_type") != "local":
        raise ValueError(f"{expected_kind} reference is not local")
    target = index.get(ref_id(reference))
    if not isinstance(target, dict) or target.get("kind") != expected_kind:
        raise ValueError(f"{expected_kind} reference did not resolve to expected kind")
    if reference.get("expected_kind") not in {None, expected_kind}:
        raise ValueError(f"{expected_kind} reference declares wrong expected_kind")
    return target


def accepted_model_output(receipt):
    index = record_index(receipt)
    candidates = []
    for invocation in by_kind(receipt, "ModelInvocation"):
        accepted_ref = invocation.get("accepted_output")
        if not accepted_ref:
            continue
        output = resolve_local(index, accepted_ref, "ModelOutput")
        attempt = resolve_local(index, output.get("attempt"), "ProviderAttempt")
        owner = resolve_local(index, attempt.get("invocation"), "ModelInvocation")
        if owner.get("id") != invocation.get("id"):
            raise ValueError("accepted ModelOutput attempt belongs to a different invocation")
        if output.get("run_id") != invocation.get("run_id"):
            raise ValueError("accepted ModelOutput changed run occurrence")
        candidates.append((invocation, attempt, output))

    if len(candidates) != 1:
        raise ValueError(
            f"model-output bounded-claims batch requires one accepted ModelOutput, found {len(candidates)}"
        )
    return candidates[0]


def complete_capture_output(receipt):
    _invocation, _attempt, output = accepted_model_output(receipt)
    if output.get("capture_extent") != "complete":
        raise ValueError("accepted ModelOutput does not establish complete application-visible capture")
    return output


def captured_text_output(receipt):
    _invocation, _attempt, output = accepted_model_output(receipt)
    index = record_index(receipt)
    texts = []
    for item_ref in output.get("item_refs", []):
        target_id = ref_id(item_ref)
        target = index.get(target_id)
        if not isinstance(target, dict):
            raise ValueError("ModelOutput item reference is unresolved")
        if item_ref.get("ref_type") != "local":
            raise ValueError("ModelOutput item reference is not local")
        if target.get("kind") != item_ref.get("expected_kind"):
            raise ValueError("ModelOutput item reference kind mismatch")
        if target.get("kind") != "TextOutput":
            continue
        owner = resolve_local(index, target.get("output"), "ModelOutput")
        if owner.get("id") != output.get("id"):
            raise ValueError("TextOutput points to a different ModelOutput")
        if not isinstance(target.get("text"), str):
            raise ValueError("TextOutput does not contain captured text")
        texts.append(target)

    if len(texts) != 1:
        raise ValueError(
            f"model-text bounded-claim scenario requires one TextOutput, found {len(texts)}"
        )
    return texts[0]


def execute_model_output_case(row, case, materialized):
    requirement_id = row["requirement_id"]
    check_id = row["planned_test_id"]
    if check_id not in MODEL_OUTPUT_PLANNED_TESTS:
        raise NotImplementedError(check_id)

    receipt = primary_receipt(case, materialized)

    if check_id == "model-output-boundary-001":
        _invocation, _attempt, output = accepted_model_output(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                output["id"],
                domain="claim",
                status="asserted",
                prohibited=[
                    "P1:model_output_identity_implies_raw_provider_wire_or_internal_representation"
                ],
            )
        ]

    elif check_id == "model-capture-complete-scope-001":
        output = complete_capture_output(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                output["id"],
                domain="completeness",
                status="established",
                prohibited=[
                    "P1:complete_capture_proves_no_hidden_provider_output"
                ],
            )
        ]

    elif check_id == "model-text-no-hidden-reasoning-001":
        text = captured_text_output(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                text["id"],
                domain="claim",
                status="asserted",
                prohibited=[
                    "P1:text_output_is_hidden_reasoning_or_token_history"
                ],
            )
        ]

    else:
        raise NotImplementedError(check_id)

    return {
        "findings": findings,
        "process_outcome": "completed",
        "completeness": {},
    }
