#!/usr/bin/env python3


PROVIDER_ATTEMPT_PLANNED_TESTS = {
    "provider-attempt-distinct-identity-001",
    "provider-retry-new-attempt-001",
    "provider-retry-relation-positive-001",
    "provider-retry-no-prior-negation-001",
    "provider-retry-001",
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
        raise ValueError(
            f"provider-attempt batch requires one primary receipt, found {len(receipts)}"
        )
    return receipts[0]


def retry_attempt_pair(receipt):
    index = record_index(receipt)
    for attempt in by_kind(receipt, "ProviderAttempt"):
        predecessor_id = ref_id(attempt.get("retry_of"))
        if not predecessor_id:
            continue
        predecessor = index.get(predecessor_id)
        if not isinstance(predecessor, dict) or predecessor.get("kind") != "ProviderAttempt":
            continue
        if attempt.get("id") == predecessor.get("id"):
            raise ValueError("retry attempt reuses predecessor identity")
        if ref_id(attempt.get("invocation")) != ref_id(predecessor.get("invocation")):
            raise ValueError("retry attempt changed logical invocation")
        return predecessor, attempt
    raise ValueError("retry attempt pair not found")


def retry_orchestration_basis(attempt):
    for item in attempt.get("metadata", []):
        if item.get("name") != "orchestration_relation":
            continue
        if item.get("value") != "retry":
            continue
        origin = item.get("origin")
        if not isinstance(origin, str) or not origin:
            continue
        if origin == "provider_reported":
            continue
        return item
    return None


def require_visible_retry(receipt):
    predecessor, retry = retry_attempt_pair(receipt)
    basis = retry_orchestration_basis(retry)
    if basis is None:
        raise ValueError("retry_of lacks positive application/adapter orchestration evidence")
    return predecessor, retry, basis


def execute_provider_attempt_case(row, case, materialized):
    requirement_id = row["requirement_id"]
    check_id = row["planned_test_id"]
    if check_id not in PROVIDER_ATTEMPT_PLANNED_TESTS:
        raise NotImplementedError(check_id)

    receipt = primary_receipt(case, materialized)

    if check_id in {
        "provider-attempt-distinct-identity-001",
        "provider-retry-new-attempt-001",
        "provider-retry-001",
    }:
        _predecessor, retry, _basis = require_visible_retry(receipt)
        findings = [
            finding(requirement_id, check_id, receipt, retry["id"])
        ]

    elif check_id == "provider-retry-relation-positive-001":
        _predecessor, retry, _basis = require_visible_retry(receipt)
        findings = [
            finding(requirement_id, check_id, receipt, retry["id"])
        ]

    elif check_id == "provider-retry-no-prior-negation-001":
        predecessor, _retry, _basis = require_visible_retry(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                predecessor["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:retry_negates_prior_provider_work"],
            )
        ]

    else:
        raise NotImplementedError(check_id)

    return {
        "findings": findings,
        "process_outcome": "completed",
        "completeness": {},
    }
