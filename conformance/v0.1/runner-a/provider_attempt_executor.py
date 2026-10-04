#!/usr/bin/env python3

from datetime import datetime


PROVIDER_ATTEMPT_PLANNED_TESTS = {
    "provider-attempt-distinct-identity-001",
    "provider-retry-new-attempt-001",
    "provider-retry-relation-positive-001",
    "provider-retry-no-prior-negation-001",
    "provider-retry-001",
    "provider-hedge-distinct-attempts-001",
    "provider-hedge-cancel-bounded-001",
    "model-attempt-relation-no-self-loop-001",
    "model-attempt-predecessor-cycle-001",
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



def parse_timestamp(value):
    if not isinstance(value, str) or not value:
        raise ValueError("attempt timestamp missing")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def attempts_overlap(left, right):
    left_start = parse_timestamp(left.get("started_at"))
    left_end = parse_timestamp(left.get("ended_at"))
    right_start = parse_timestamp(right.get("started_at"))
    right_end = parse_timestamp(right.get("ended_at"))
    return max(left_start, right_start) < min(left_end, right_end)


def hedged_attempt_pair(receipt):
    index = record_index(receipt)
    for left in by_kind(receipt, "ProviderAttempt"):
        for ref in left.get("hedged_with", []):
            right = index.get(ref_id(ref))
            if not isinstance(right, dict) or right.get("kind") != "ProviderAttempt":
                continue
            if left.get("id") == right.get("id"):
                raise ValueError("hedged attempt relation reuses one occurrence identity")
            if ref_id(left.get("invocation")) != ref_id(right.get("invocation")):
                raise ValueError("hedged attempts do not share the logical invocation")
            reciprocal = {
                ref_id(item)
                for item in right.get("hedged_with", [])
                if ref_id(item)
            }
            if left.get("id") not in reciprocal:
                raise ValueError("hedged_with relation is not reciprocal")
            if not attempts_overlap(left, right):
                raise ValueError("hedged attempts do not overlap in observed lifecycle")
            return left, right
    raise ValueError("hedged attempt pair not found")


def application_cancelled_hedge(receipt):
    left, right = hedged_attempt_pair(receipt)
    cancelled = [
        attempt
        for attempt in (left, right)
        if attempt.get("terminal_disposition") == "cancelled"
    ]
    if len(cancelled) != 1:
        raise ValueError("expected exactly one locally cancelled hedge")
    loser = cancelled[0]
    for item in loser.get("metadata", []):
        if item.get("name") != "cancellation_source":
            continue
        if item.get("value") != "application":
            continue
        if item.get("origin") not in {"adapter_observed", "application_supplied"}:
            continue
        return left, right, loser
    raise ValueError("cancelled hedge lacks application-side cancellation evidence")


def provider_attempt_index(receipt):
    return {
        attempt["id"]: attempt
        for attempt in by_kind(receipt, "ProviderAttempt")
        if isinstance(attempt, dict) and attempt.get("id")
    }


def attempt_predecessor_graph(receipt):
    attempts = provider_attempt_index(receipt)
    graph = {}
    for attempt_id, attempt in attempts.items():
        predecessors = []
        for field in ("retry_of", "failover_from"):
            predecessor_id = ref_id(attempt.get(field))
            predecessor = attempts.get(predecessor_id)
            if (
                predecessor_id
                and isinstance(predecessor, dict)
                and predecessor.get("kind") == "ProviderAttempt"
            ):
                predecessors.append(predecessor_id)
        graph[attempt_id] = tuple(dict.fromkeys(predecessors))
    return attempts, graph


def graph_can_reach(graph, current, target, seen):
    if current == target:
        return True
    if current in seen:
        return False
    next_seen = set(seen)
    next_seen.add(current)
    return any(
        graph_can_reach(graph, predecessor, target, next_seen)
        for predecessor in graph.get(current, ())
    )


def predecessor_self_loops(receipt):
    attempts, graph = attempt_predecessor_graph(receipt)
    return [
        attempts[attempt_id]
        for attempt_id, predecessors in graph.items()
        if attempt_id in predecessors
    ]


def predecessor_cycle_members(receipt):
    attempts, graph = attempt_predecessor_graph(receipt)
    members = []
    for attempt_id, attempt in attempts.items():
        for predecessor_id in graph.get(attempt_id, ()):
            if predecessor_id == attempt_id:
                continue
            if graph_can_reach(graph, predecessor_id, attempt_id, set()):
                members.append(attempt)
                break
    return members


def execute_provider_attempt_case(row, case, materialized):
    requirement_id = row["requirement_id"]
    check_id = row["planned_test_id"]
    if check_id not in PROVIDER_ATTEMPT_PLANNED_TESTS:
        raise NotImplementedError(check_id)

    receipt = primary_receipt(case, materialized)
    process_outcome = "completed"

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

    elif check_id == "provider-hedge-distinct-attempts-001":
        left, right = hedged_attempt_pair(receipt)
        subject = right
        if right.get("terminal_disposition") != "cancelled" and left.get("terminal_disposition") == "cancelled":
            subject = left
        findings = [
            finding(requirement_id, check_id, receipt, subject["id"])
        ]

    elif check_id == "provider-hedge-cancel-bounded-001":
        _left, _right, loser = application_cancelled_hedge(receipt)
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                loser["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:application_cancellation_proves_remote_provider_stop"],
            )
        ]


    elif check_id == "model-attempt-relation-no-self-loop-001":
        invalid = predecessor_self_loops(receipt)
        if not invalid:
            raise ValueError("provider-attempt predecessor self-loop not found")
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                attempt["id"],
                status="invalid",
                reason_code="attempt_predecessor_self_loop",
            )
            for attempt in invalid
        ]
        process_outcome = "invalidity_detected"

    elif check_id == "model-attempt-predecessor-cycle-001":
        invalid = predecessor_cycle_members(receipt)
        if not invalid:
            raise ValueError("provider-attempt predecessor cycle not found")
        findings = [
            finding(
                requirement_id,
                check_id,
                receipt,
                attempt["id"],
                status="invalid",
                reason_code="attempt_predecessor_cycle",
            )
            for attempt in invalid
        ]
        process_outcome = "invalidity_detected"

    else:
        raise NotImplementedError(check_id)

    return {
        "findings": findings,
        "process_outcome": process_outcome,
        "completeness": {},
    }
