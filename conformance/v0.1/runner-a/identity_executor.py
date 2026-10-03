#!/usr/bin/env python3


IDENTITY_PLANNED_TESTS = {
    "transform-selection-identity-001",
    "transform-aggregate-identity-001",
    "artifact-id-reuse-001",
    "request-attempt-identity-001",
    "request-level-identity-separation-001",
    "request-mutation-new-snapshot-001",
    "provider-request-mutation-new-snapshot-001",
    "request-digest-no-identity-001",
    "provider-id-not-c2a-identity-001",
    "provider-multihook-correlation-001",
    "provider-capture-diagnostic-no-merge-001",
    "model-requested-not-internal-001",
    "model-output-no-content-merge-001",
}

CAPTURE_ORDER = {
    "sdk_arguments": 0,
    "provider_payload": 1,
    "prepared_http_body": 2,
    "unknown": 3,
}


def records(receipt):
    return receipt.get("arp", {}).get("records", [])


def receipt_id(receipt):
    return receipt.get("arp", {}).get("receipt_id")


def by_kind(receipt, kind):
    return [r for r in records(receipt) if r.get("kind") == kind]


def record_index(receipt):
    return {
        r.get("id"): r
        for r in records(receipt)
        if isinstance(r, dict) and r.get("id")
    }


def ref_id(value):
    return value.get("id") if isinstance(value, dict) else None


def finding(requirement_id, check_id, receipt, object_id, domain="conformance",
            status="valid", reason_code=None, prohibited=None):
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
    if reason_code is not None:
        out["reason_code"] = reason_code
    if prohibited:
        out["prohibited_inferences"] = list(prohibited)
    return out


def primary_receipt(case, materialized):
    ids = (case.get("harness") or {}).get("primary_documents", [])
    receipts = [
        materialized[x] for x in ids
        if x in materialized and materialized[x].get("kind") == "ReceiptPresentation"
    ]
    if len(receipts) != 1:
        raise ValueError(f"identity batch requires one primary receipt, found {len(receipts)}")
    return receipts[0]


def selected_and_generated(receipt):
    index = record_index(receipt)
    for transform in by_kind(receipt, "Transform"):
        selected = [ref_id(x) for x in transform.get("selected", []) if ref_id(x)]
        generated = [ref_id(x) for x in transform.get("generated", []) if ref_id(x)]
        if selected and generated:
            if any(x not in index for x in selected + generated):
                raise ValueError("identity transform references missing artifact")
            return transform, selected, generated
    raise ValueError("selection/generated identity scenario not found")


def duplicate_representation_conflict(receipt):
    grouped = {}
    for record in records(receipt):
        record_id = record.get("id")
        if record_id:
            grouped.setdefault(record_id, []).append(record)
    for record_id, occurrences in grouped.items():
        if len(occurrences) < 2:
            continue
        representations = [
            occurrence.get("representation")
            for occurrence in occurrences
            if "representation" in occurrence
        ]
        if len(representations) >= 2 and any(
            representation != representations[0]
            for representation in representations[1:]
        ):
            return record_id
    return None


def retry_attempt_pair(receipt):
    index = record_index(receipt)
    for attempt in by_kind(receipt, "ProviderAttempt"):
        parent_id = ref_id(attempt.get("retry_of"))
        if not parent_id:
            continue
        parent = index.get(parent_id)
        if not isinstance(parent, dict) or parent.get("kind") != "ProviderAttempt":
            continue
        if attempt.get("id") == parent.get("id"):
            raise ValueError("retry attempt reuses parent identity")
        if ref_id(attempt.get("invocation")) != ref_id(parent.get("invocation")):
            raise ValueError("retry identity scenario changed invocation")
        return parent, attempt
    raise ValueError("retry occurrence pair not found")


def different_level_snapshot_pair(receipt):
    snapshots = by_kind(receipt, "RequestSnapshot")
    pairs = []
    for i, left in enumerate(snapshots):
        for right in snapshots[i + 1:]:
            if left.get("capture_level") == right.get("capture_level"):
                continue
            if left.get("id") == right.get("id"):
                raise ValueError("different capture levels reuse snapshot identity")
            pairs.append((left, right))
    if not pairs:
        raise ValueError("different-level snapshot pair not found")
    left, right = max(
        pairs,
        key=lambda pair: max(
            CAPTURE_ORDER.get(pair[0].get("capture_level"), -1),
            CAPTURE_ORDER.get(pair[1].get("capture_level"), -1),
        ),
    )
    return (
        right if CAPTURE_ORDER.get(right.get("capture_level"), -1)
        >= CAPTURE_ORDER.get(left.get("capture_level"), -1)
        else left
    )


def mutation_snapshot_pair(receipt):
    snapshots = by_kind(receipt, "RequestSnapshot")
    for i, before in enumerate(snapshots):
        for after in snapshots[i + 1:]:
            if before.get("capture_level") != after.get("capture_level"):
                continue
            before_owner = ref_id(before.get("attempt_owner")) or ref_id(before.get("invocation_owner"))
            after_owner = ref_id(after.get("attempt_owner")) or ref_id(after.get("invocation_owner"))
            if before_owner != after_owner:
                continue
            if before.get("representation") == after.get("representation"):
                continue
            if before.get("id") == after.get("id"):
                raise ValueError("mutated request representation reused snapshot identity")
            return before, after
    raise ValueError("same-level request mutation pair not found")


def equal_semantic_digest_pair(receipt):
    snapshots = [
        snapshot for snapshot in by_kind(receipt, "RequestSnapshot")
        if isinstance(snapshot.get("semantic_digest"), dict)
    ]
    for i, left in enumerate(snapshots):
        left_digest = left["semantic_digest"]
        for right in snapshots[i + 1:]:
            right_digest = right["semantic_digest"]
            compatible = (
                left_digest.get("algorithm") == right_digest.get("algorithm")
                and left_digest.get("representation_basis") == right_digest.get("representation_basis")
                and left_digest.get("canonicalization_profile") == right_digest.get("canonicalization_profile")
            )
            equal_value = (
                (left_digest.get("value") or {}).get("value")
                == (right_digest.get("value") or {}).get("value")
            )
            if compatible and equal_value:
                if left.get("id") == right.get("id"):
                    raise ValueError("equal semantic digests collapsed snapshot identity")
                return left, right
    raise ValueError("equal semantic digest snapshot pair not found")



def provider_remote_id_pair(receipt):
    attempts = by_kind(receipt, "ProviderAttempt")
    values = []
    for attempt in attempts:
        for item in attempt.get("metadata", []):
            if item.get("origin") != "provider_reported":
                continue
            name = item.get("name")
            if name not in {"provider_request_id", "provider_response_id", "provider_attempt_id"}:
                continue
            values.append((name, item.get("value"), attempt))
    for i, (name, value, left) in enumerate(values):
        for other_name, other_value, right in values[i + 1:]:
            if name != other_name or value != other_value:
                continue
            if left.get("id") == right.get("id"):
                raise ValueError("provider-reported identifier collapsed C2ATrace attempt identity")
            return left, right
    raise ValueError("shared provider-reported identifier across distinct attempts not found")


def diagnostic_semantic_key(diagnostic):
    subject = diagnostic.get("subject") or {}
    return (
        ref_id(subject.get("ref")),
        subject.get("representation_basis"),
        diagnostic.get("slot"),
        diagnostic.get("status"),
        ref_id(diagnostic.get("adapter_declaration")),
    )


def duplicate_diagnostic_occurrence_pair(receipt):
    diagnostics = by_kind(receipt, "CaptureDiagnostic")
    for i, left in enumerate(diagnostics):
        left_key = diagnostic_semantic_key(left)
        for right in diagnostics[i + 1:]:
            if diagnostic_semantic_key(right) != left_key:
                continue
            if left.get("id") == right.get("id"):
                raise ValueError("duplicate diagnostic occurrence reused C2ATrace identity")
            return left, right
    raise ValueError("semantically matching diagnostic occurrence pair not found")


def output_item_value(record):
    kind = record.get("kind")
    if kind == "TextOutput":
        return ("text", record.get("text"))
    if kind == "StructuredOutput":
        return ("structured", record.get("value"))
    if kind == "UnknownOutput":
        return ("unknown", record.get("representation"))
    return (kind, None)


def model_output_content_signature(receipt, output):
    index = record_index(receipt)
    values = []
    for ref in output.get("item_refs", []):
        item = index.get(ref_id(ref))
        if not isinstance(item, dict):
            raise ValueError("ModelOutput item reference is unresolved")
        if ref_id(item.get("output")) != output.get("id"):
            raise ValueError("OutputItem ownership does not match ModelOutput")
        values.append(output_item_value(item))
    return tuple(values)


def equal_content_model_output_pair(receipt):
    outputs = by_kind(receipt, "ModelOutput")
    for i, left in enumerate(outputs):
        left_sig = model_output_content_signature(receipt, left)
        for right in outputs[i + 1:]:
            right_sig = model_output_content_signature(receipt, right)
            if left_sig != right_sig:
                continue
            if left.get("id") == right.get("id"):
                raise ValueError("equal output content collapsed ModelOutput identity")
            return left, right
    raise ValueError("equal-content distinct ModelOutput occurrence pair not found")

def execute_identity_case(row, case, materialized):
    requirement_id = row["requirement_id"]
    check_id = row["planned_test_id"]
    if check_id not in IDENTITY_PLANNED_TESTS:
        raise NotImplementedError(check_id)

    receipt = primary_receipt(case, materialized)

    if check_id == "transform-selection-identity-001":
        _transform, selected, generated = selected_and_generated(receipt)
        selected_id = selected[0]
        if selected_id in generated:
            raise ValueError("selection was modeled as generation")
        findings = [
            finding(requirement_id, check_id, receipt, selected_id)
        ]
        outcome = "completed"

    elif check_id == "transform-aggregate-identity-001":
        transform, selected, generated = selected_and_generated(receipt)
        input_ids = [
            ref_id(item.get("artifact"))
            for item in transform.get("inputs", [])
            if ref_id(item.get("artifact"))
        ]
        fresh = [
            artifact_id for artifact_id in generated
            if artifact_id not in set(selected + input_ids)
        ]
        if not fresh:
            raise ValueError("generated aggregate did not receive fresh artifact identity")
        findings = [
            finding(requirement_id, check_id, receipt, fresh[0])
        ]
        outcome = "completed"

    elif check_id == "artifact-id-reuse-001":
        conflict_id = duplicate_representation_conflict(receipt)
        if conflict_id is None:
            raise ValueError("immutable artifact identity conflict not detected")
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                conflict_id,
                domain="conflict",
                status="conflict",
                reason_code="artifact_id_representation_conflict",
            )
        ]
        outcome = "invalidity_detected"

    elif check_id == "request-attempt-identity-001":
        _parent, retry = retry_attempt_pair(receipt)
        findings = [
            finding(requirement_id, check_id, receipt, retry["id"])
        ]
        outcome = "completed"

    elif check_id == "request-level-identity-separation-001":
        later = different_level_snapshot_pair(receipt)
        findings = [
            finding(requirement_id, check_id, receipt, later["id"])
        ]
        outcome = "completed"

    elif check_id in {
        "request-mutation-new-snapshot-001",
        "provider-request-mutation-new-snapshot-001",
    }:
        _before, after = mutation_snapshot_pair(receipt)
        findings = [
            finding(requirement_id, check_id, receipt, after["id"])
        ]
        outcome = "completed"

    elif check_id == "request-digest-no-identity-001":
        _left, right = equal_semantic_digest_pair(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                right["id"],
                prohibited=["P1:digest_equality_merges_snapshot_identity"],
            )
        ]
        outcome = "completed"

    elif check_id == "provider-id-not-c2a-identity-001":
        _left, right = provider_remote_id_pair(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                right["id"],
                prohibited=["P1:provider_id_is_c2atrace_identity"],
            )
        ]
        outcome = "completed"

    elif check_id in {
        "provider-multihook-correlation-001",
        "provider-capture-diagnostic-no-merge-001",
    }:
        _left, right = duplicate_diagnostic_occurrence_pair(receipt)
        findings = [
            finding(requirement_id, check_id, receipt, right["id"])
        ]
        outcome = "completed"

    elif check_id == "model-requested-not-internal-001":
        invocations = by_kind(receipt, "ModelInvocation")
        if len(invocations) != 1:
            raise ValueError("requested-model identity scenario requires one ModelInvocation")
        invocation = invocations[0]
        requested_model = invocation.get("requested_model")
        if not isinstance(requested_model, str) or not requested_model:
            raise ValueError("requested_model evidence missing")
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                invocation["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:requested_model_is_internal_model_identity"],
            )
        ]
        outcome = "completed"

    elif check_id == "model-output-no-content-merge-001":
        left, right = equal_content_model_output_pair(receipt)
        # Use the earlier occurrence as the subject so occurrence identity is
        # tested independently of accepted-output selection.
        subject = left
        if right.get("id") < left.get("id"):
            subject = right
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                subject["id"],
                prohibited=["P1:equal_output_content_merges_modeloutput_occurrences"],
            )
        ]
        outcome = "completed"

    else:
        raise NotImplementedError(check_id)

    return {
        "findings": findings,
        "process_outcome": outcome,
        "completeness": {},
    }
