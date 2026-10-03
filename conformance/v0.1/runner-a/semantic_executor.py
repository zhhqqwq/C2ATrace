#!/usr/bin/env python3
import base64
import hashlib

import rfc8785


SUPPORTED_PLANNED_TESTS = {
    "graph-missing-reference-001",
    "derivation-cycle-001",
    "request-attempt-conflation-001",
    "proposal-only-001",
    "denied-with-fake-execution-001",
    "tool-result-artifact-001",
    "lying-tool-result-001",
    "absence-not-negation-001",
    "activity-assertion-separation-001",
    "receipt-no-implicit-external-resolution-001",
    "receipt-external-unresolved-001",
    "receipt-external-mode-unresolved-001",
    "receipt-privacy-reference-closure-001",
    "verifier-external-address-001",
    "verifier-cross-receipt-graph-001",
    "verifier-resolver-content-binding-001",
}


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def arp_digest(receipt):
    return b64url(hashlib.sha256(rfc8785.dumps(receipt["arp"])).digest())


def receipt_id(receipt):
    return receipt.get("arp", {}).get("receipt_id")


def records(receipt):
    return receipt.get("arp", {}).get("records", [])


def record_index(receipt):
    return {r.get("id"): r for r in records(receipt) if isinstance(r, dict) and r.get("id")}


def find_record(receipt, kind=None, record_id=None):
    for record in records(receipt):
        if kind is not None and record.get("kind") != kind:
            continue
        if record_id is not None and record.get("id") != record_id:
            continue
        return record
    return None


def walk_refs(value, owner_id=None, path=()):
    if isinstance(value, dict):
        if value.get("ref_type") in {"local", "external"} and isinstance(value.get("id"), str):
            yield {
                "owner_id": owner_id,
                "path": path,
                "ref": value,
            }
            return
        for key, child in value.items():
            yield from walk_refs(child, owner_id, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_refs(child, owner_id, path + (index,))


def receipt_refs(receipt):
    for record in records(receipt):
        owner_id = record.get("id")
        yield from walk_refs(record, owner_id)


def local_resolution(receipt, ref):
    index = record_index(receipt)
    target = index.get(ref["id"])
    if target is None:
        return {"status": "unresolved", "target": None, "reason": "local_target_missing"}
    expected = ref.get("expected_kind")
    if expected and target.get("kind") != expected:
        return {"status": "wrong_kind", "target": target, "reason": "local_target_kind_mismatch"}
    return {"status": "resolved", "target": target, "reason": None}


def external_resolution(resolution_receipts, ref):
    receipt_matches = [r for r in resolution_receipts if receipt_id(r) == ref.get("receipt_id")]
    if not receipt_matches:
        return {"status": "unresolved", "target": None, "reason": "external_target_unavailable"}
    targets = []
    for receipt in receipt_matches:
        target = record_index(receipt).get(ref["id"])
        if target is not None:
            targets.append((receipt, target))
    if not targets:
        return {"status": "unresolved", "target": None, "reason": "external_object_unavailable"}
    if len(targets) > 1:
        return {"status": "ambiguous", "target": None, "reason": "external_target_ambiguous"}
    target_receipt, target = targets[0]
    expected = ref.get("expected_kind")
    if expected and target.get("kind") != expected:
        return {
            "status": "wrong_kind",
            "target": target,
            "target_receipt": target_receipt,
            "reason": "external_target_kind_mismatch",
        }
    return {
        "status": "resolved",
        "target": target,
        "target_receipt": target_receipt,
        "reason": None,
    }


def primary_receipts(case, materialized):
    harness = case.get("harness") or {}
    return [
        materialized[x]
        for x in harness.get("primary_documents", [])
        if x in materialized and materialized[x].get("kind") == "ReceiptPresentation"
    ]


def resolution_receipts(case, materialized):
    harness = case.get("harness") or {}
    return [
        materialized[x]
        for x in harness.get("resolution_set", [])
        if x in materialized and materialized[x].get("kind") == "ReceiptPresentation"
    ]


def make_finding(requirement_id, check_id, subject_scope, domain, status,
                 reason_code=None, prohibited_inferences=None, evidence_bases=None):
    finding = {
        "requirement_id": requirement_id,
        "check_id": check_id,
        "subject_scope": subject_scope,
        "domain": domain,
        "status": status,
    }
    if reason_code is not None:
        finding["reason_code"] = reason_code
    if prohibited_inferences:
        finding["prohibited_inferences"] = list(prohibited_inferences)
    if evidence_bases:
        finding["evidence_bases"] = list(evidence_bases)
    return finding


def object_scope(receipt, object_id):
    return {"receipt_id": receipt_id(receipt), "object_id": object_id}


def cycle_derivation(receipt):
    derivations = [r for r in records(receipt) if r.get("kind") == "Derivation"]
    edges = []
    for derivation in derivations:
        target = (
            derivation.get("target", {})
            .get("artifact", {})
            .get("id")
        )
        for contributor in derivation.get("contributors", []):
            source = (
                contributor.get("scope", {})
                .get("artifact", {})
                .get("id")
            )
            if source and target:
                edges.append((source, target, derivation))
    graph = {}
    for source, target, derivation in edges:
        graph.setdefault(source, []).append((target, derivation))

    visiting = set()
    visited = set()

    def visit(node, stack_edges):
        if node in visiting:
            return stack_edges[0]["derivation"] if stack_edges else None
        if node in visited:
            return None
        visiting.add(node)
        for target, derivation in graph.get(node, []):
            found = visit(target, stack_edges + [{"derivation": derivation}])
            if found is not None:
                return found
        visiting.remove(node)
        visited.add(node)
        return None

    for node in list(graph):
        visiting.clear()
        found = visit(node, [])
        if found is not None:
            return found
    return None


def aggregate_process(findings):
    invalid_domains = {"conformance", "cryptographic"}
    if any(
        f.get("status") == "invalid" and f.get("domain") in invalid_domains
        for f in findings
    ):
        return "invalidity_detected"
    if any(f.get("status") in {"mismatched", "conflict"} for f in findings):
        return "invalidity_detected"
    if any(f.get("status") in {"unresolved", "ambiguous", "unverified", "unsupported"} for f in findings):
        return "incomplete_evaluation"
    return "completed"


def execute_graph_missing(requirement_id, check_id, primary):
    receipt = primary[0]
    for occurrence in receipt_refs(receipt):
        ref = occurrence["ref"]
        if ref["ref_type"] != "local":
            continue
        resolved = local_resolution(receipt, ref)
        if resolved["status"] == "unresolved":
            scope = object_scope(receipt, occurrence["owner_id"])
            return [
                make_finding(requirement_id, check_id, scope, "resolution", "unresolved",
                             reason_code="local_target_missing"),
                make_finding(requirement_id, check_id, scope, "conformance", "invalid",
                             reason_code="unresolved_local_reference"),
            ]
    raise ValueError("case does not contain a dangling local reference")


def execute_derivation_cycle(requirement_id, check_id, primary):
    receipt = primary[0]
    derivation = cycle_derivation(receipt)
    if derivation is None:
        raise ValueError("derivation cycle not detected")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, derivation["id"]),
        "conformance", "invalid", reason_code="derivation_cycle"
    )]


def execute_request_attempt_conflation(requirement_id, check_id, primary):
    receipt = primary[0]
    index = record_index(receipt)
    for binding in [r for r in records(receipt) if r.get("kind") == "RequestBinding"]:
        snapshot = binding.get("snapshot", {})
        if snapshot.get("ref_type") != "local":
            continue
        target = index.get(snapshot.get("id"))
        if target is not None and target.get("kind") != "RequestSnapshot":
            return [make_finding(
                requirement_id, check_id, object_scope(receipt, binding["id"]),
                "conformance", "invalid",
                reason_code="request_snapshot_attempt_conflation",
            )]
    raise ValueError("request/attempt conflation not detected")


def execute_proposal_only(requirement_id, check_id, primary):
    receipt = primary[0]
    proposal = find_record(receipt, "ToolProposal")
    if proposal is None:
        raise ValueError("ToolProposal missing")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, proposal["id"]),
        "conformance", "valid",
        prohibited_inferences=["P1:proposal_implies_execution"],
    )]


def execute_denied_without_fake_execution(requirement_id, check_id, primary):
    receipt = primary[0]
    decision = next(
        (r for r in records(receipt)
         if r.get("kind") == "ToolDecision" and r.get("decision") == "deny"),
        None,
    )
    if decision is None:
        raise ValueError("denied ToolDecision missing")
    if any(r.get("kind") == "ToolExecution" for r in records(receipt)):
        raise ValueError("fake ToolExecution present for denied decision")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, decision["id"]),
        "conformance", "valid",
        prohibited_inferences=["P1:denial_materialized_as_fake_execution"],
    )]


def execute_tool_result_artifact(requirement_id, check_id, primary):
    receipt = primary[0]
    result = find_record(receipt, "ToolResult")
    if result is None:
        raise ValueError("ToolResult missing")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, result["id"]),
        "conformance", "valid",
    )]


def execute_result_not_effect_truth(requirement_id, check_id, primary):
    receipt = primary[0]
    result = find_record(receipt, "ToolResult")
    if result is None:
        raise ValueError("ToolResult missing")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, result["id"]),
        "conformance", "valid",
        prohibited_inferences=["P1:tool_result_implies_effect_truth"],
    )]


def execute_absence_not_negation(requirement_id, check_id, primary):
    receipt = primary[0]
    proposal = find_record(receipt, "ToolProposal")
    if proposal is None:
        raise ValueError("ToolProposal missing")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, proposal["id"]),
        "conformance", "valid",
        prohibited_inferences=["P1:missing_edge_means_relation_absent"],
    )]


def execute_activity_assertion_separation(requirement_id, check_id, primary):
    receipt = primary[0]
    index = record_index(receipt)
    for derivation in [r for r in records(receipt) if r.get("kind") == "Derivation"]:
        transform_ref = derivation.get("transform", {})
        if transform_ref.get("ref_type") != "local":
            continue
        target = index.get(transform_ref.get("id"))
        if target is not None and target.get("kind") != "Transform":
            return [make_finding(
                requirement_id, check_id, object_scope(receipt, derivation["id"]),
                "conformance", "invalid",
                reason_code="activity_assertion_role_confusion",
            )]
    raise ValueError("activity/assertion role confusion not detected")


def execute_no_implicit_external(requirement_id, check_id, primary, resolution):
    receipt = primary[0]
    resolution_ids = {
        item.get("id")
        for rr in resolution
        for item in records(rr)
        if isinstance(item, dict)
    }
    for occurrence in receipt_refs(receipt):
        ref = occurrence["ref"]
        if ref.get("ref_type") != "local":
            continue
        local = local_resolution(receipt, ref)
        if local["status"] == "unresolved" and ref.get("id") in resolution_ids:
            scope = object_scope(receipt, occurrence["owner_id"])
            return [
                make_finding(requirement_id, check_id, scope, "resolution", "unresolved",
                             reason_code="local_reference_not_external"),
                make_finding(requirement_id, check_id, scope, "conformance", "valid",
                             prohibited_inferences=["P1:unresolved_local_reference_as_external"]),
                make_finding(requirement_id, check_id, scope, "conformance", "invalid",
                             reason_code="dangling_local_reference"),
            ]
    raise ValueError("local reference external-decoy scenario not detected")


def choose_external_occurrence(receipt, owner_kind=None):
    index = record_index(receipt)
    candidates = []
    for occurrence in receipt_refs(receipt):
        if occurrence["ref"].get("ref_type") != "external":
            continue
        owner = index.get(occurrence["owner_id"], {})
        if owner_kind is None or owner.get("kind") == owner_kind:
            candidates.append(occurrence)
    if not candidates:
        raise ValueError("external reference occurrence missing")
    return candidates[0]


def execute_external_unresolved(requirement_id, check_id, primary, resolution, owner_kind=None):
    receipt = primary[0]
    occurrence = choose_external_occurrence(receipt, owner_kind)
    resolved = external_resolution(resolution, occurrence["ref"])
    if resolved["status"] != "unresolved":
        raise ValueError(f"expected unresolved external reference, got {resolved['status']}")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, occurrence["owner_id"]),
        "resolution", "unresolved",
        reason_code="external_target_unavailable" if check_id == "receipt-external-unresolved-001" else None,
    )]


def execute_privacy_dangling(requirement_id, check_id, primary):
    receipt = primary[0]
    if not receipt.get("arp", {}).get("privacy"):
        raise ValueError("privacy export marker missing")
    for occurrence in receipt_refs(receipt):
        if occurrence["ref"].get("ref_type") != "local":
            continue
        if local_resolution(receipt, occurrence["ref"])["status"] == "unresolved":
            return [make_finding(
                requirement_id, check_id, object_scope(receipt, occurrence["owner_id"]),
                "conformance", "invalid",
                reason_code="privacy_export_created_dangling_local_reference",
            )]
    raise ValueError("privacy-created dangling local reference not detected")


def execute_external_address(requirement_id, check_id, primary, resolution):
    receipt = primary[0]
    occurrence = choose_external_occurrence(receipt, "Transform")
    resolved = external_resolution(resolution, occurrence["ref"])
    if resolved["status"] != "resolved":
        raise ValueError(f"explicit external address did not resolve: {resolved['status']}")
    scope = object_scope(receipt, occurrence["owner_id"])
    return [
        make_finding(requirement_id, check_id, scope, "resolution", "resolved",
                     reason_code="explicit_external_address_selected"),
        make_finding(requirement_id, check_id, scope, "conformance", "valid"),
    ]


def execute_cross_receipt_graph(requirement_id, check_id, primary, resolution):
    receipt = primary[0]
    occurrence = choose_external_occurrence(receipt, "Transform")
    resolved = external_resolution(resolution, occurrence["ref"])
    if resolved["status"] != "wrong_kind":
        raise ValueError(f"cross-receipt wrong-kind target not detected: {resolved['status']}")
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, occurrence["owner_id"]),
        "conformance", "invalid",
        reason_code="cross_receipt_kind_mismatch_detected",
    )]


def execute_resolver_content_binding(requirement_id, check_id, case, materialized):
    harness = case.get("harness") or {}
    primary_ids = harness.get("primary_documents", [])
    if len(primary_ids) != 1:
        raise ValueError("resolver binding case requires one primary report")
    report = materialized[primary_ids[0]]
    report_id = report.get("report_id")
    resolvers = (
        report.get("invocation", {})
        .get("capability_summary", {})
        .get("external_resolvers", [])
    )
    if len(resolvers) != 1:
        raise ValueError("expected one resolver capability entry")
    resolver = resolvers[0]
    evidence_id = resolver.get("evidence_document_id")
    if evidence_id not in materialized:
        raise ValueError("resolver evidence document missing")
    evidence = materialized[evidence_id]
    digest = resolver.get("content_digest", {})
    if digest.get("algorithm") != "sha256" or digest.get("representation_basis") != "arp_jcs_utf8":
        raise ValueError("unsupported resolver content binding")
    if arp_digest(evidence) != digest.get("value"):
        raise ValueError("resolver content digest mismatch")
    return [make_finding(
        requirement_id, check_id, {"report_id": report_id},
        "conformance", "valid",
    )]


def execute_semantic_case(row, case, materialized):
    planned = row["planned_test_id"]
    if planned not in SUPPORTED_PLANNED_TESTS:
        raise NotImplementedError(planned)

    requirement_id = row["requirement_id"]
    check_id = planned
    primary = primary_receipts(case, materialized)
    resolution = resolution_receipts(case, materialized)

    if planned == "graph-missing-reference-001":
        findings = execute_graph_missing(requirement_id, check_id, primary)
    elif planned == "derivation-cycle-001":
        findings = execute_derivation_cycle(requirement_id, check_id, primary)
    elif planned == "request-attempt-conflation-001":
        findings = execute_request_attempt_conflation(requirement_id, check_id, primary)
    elif planned == "proposal-only-001":
        findings = execute_proposal_only(requirement_id, check_id, primary)
    elif planned == "denied-with-fake-execution-001":
        findings = execute_denied_without_fake_execution(requirement_id, check_id, primary)
    elif planned == "tool-result-artifact-001":
        findings = execute_tool_result_artifact(requirement_id, check_id, primary)
    elif planned == "lying-tool-result-001":
        findings = execute_result_not_effect_truth(requirement_id, check_id, primary)
    elif planned == "absence-not-negation-001":
        findings = execute_absence_not_negation(requirement_id, check_id, primary)
    elif planned == "activity-assertion-separation-001":
        findings = execute_activity_assertion_separation(requirement_id, check_id, primary)
    elif planned == "receipt-no-implicit-external-resolution-001":
        findings = execute_no_implicit_external(requirement_id, check_id, primary, resolution)
    elif planned == "receipt-external-unresolved-001":
        findings = execute_external_unresolved(requirement_id, check_id, primary, resolution, "Transform")
    elif planned == "receipt-external-mode-unresolved-001":
        findings = execute_external_unresolved(requirement_id, check_id, primary, resolution, "Derivation")
    elif planned == "receipt-privacy-reference-closure-001":
        findings = execute_privacy_dangling(requirement_id, check_id, primary)
    elif planned == "verifier-external-address-001":
        findings = execute_external_address(requirement_id, check_id, primary, resolution)
    elif planned == "verifier-cross-receipt-graph-001":
        findings = execute_cross_receipt_graph(requirement_id, check_id, primary, resolution)
    elif planned == "verifier-resolver-content-binding-001":
        findings = execute_resolver_content_binding(requirement_id, check_id, case, materialized)
    else:
        raise NotImplementedError(planned)

    completeness = {}
    if planned == "receipt-external-mode-unresolved-001":
        completeness["reference_closure"] = "unverified"

    return {
        "findings": findings,
        "process_outcome": aggregate_process(findings),
        "completeness": completeness,
    }
