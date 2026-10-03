#!/usr/bin/env python3
import base64
import hashlib

import rfc8785

from identity_executor import IDENTITY_PLANNED_TESTS, execute_identity_case
from provider_attempt_executor import (
    PROVIDER_ATTEMPT_PLANNED_TESTS,
    execute_provider_attempt_case,
)
from request_executor import REQUEST_PLANNED_TESTS, execute_request_case


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

DERIVATION_PLANNED_TESTS = {
    "derivation-use-generation-no-inference-001",
    "derivation-transform-cardinality-001",
    "derivation-output-cardinality-001",
    "derivation-input-cardinality-001",
    "derivation-contributor-use-001",
    "derivation-target-generation-001",
    "derivation-binary-shorthand-001",
    "derivation-exact-coverage-001",
    "derivation-partial-positive-001",
    "derivation-unknown-no-edge-001",
    "derivation-use-role-no-edge-001",
    "derivation-control-no-content-001",
    "transform-selection-no-derivation-001",
    "derivation-region-basis-001",
    "derivation-coordinate-conversion-001",
    "derivation-one-to-many-isolation-001",
    "derivation-many-to-one-contributors-001",
    "derivation-generated-region-no-source-001",
    "derivation-unknown-region-blocks-exact-001",
    "derivation-absence-not-negation-001",
    "derivation-transitive-not-direct-001",
    "derivation-partial-composition-001",
    "derivation-unknown-composition-001",
    "derivation-concat-separator-001",
    "derivation-template-static-content-001",
    "derivation-truncate-discarded-001",
    "derivation-rerank-control-001",
    "derivation-redaction-no-equality-001",
    "derivation-no-fabricated-range-001",
}

SUPPORTED_PLANNED_TESTS.update(DERIVATION_PLANNED_TESTS)
SUPPORTED_PLANNED_TESTS.update(REQUEST_PLANNED_TESTS)
SUPPORTED_PLANNED_TESTS.update(IDENTITY_PLANNED_TESTS)
SUPPORTED_PLANNED_TESTS.update(PROVIDER_ATTEMPT_PLANNED_TESTS)


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
    if any(f.get("status") in {"unresolved", "ambiguous", "unverified"} for f in findings):
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
    index = record_index(receipt)
    dangling = []
    for occurrence in receipt_refs(receipt):
        if occurrence["ref"].get("ref_type") != "local":
            continue
        if local_resolution(receipt, occurrence["ref"])["status"] == "unresolved":
            dangling.append(occurrence)
    if not dangling:
        raise ValueError("privacy-created dangling local reference not detected")

    binding = next(
        (occurrence for occurrence in dangling
         if index.get(occurrence["owner_id"], {}).get("kind") == "RequestBinding"),
        None,
    )
    occurrence = binding or dangling[0]
    return [make_finding(
        requirement_id, check_id, object_scope(receipt, occurrence["owner_id"]),
        "conformance", "invalid",
        reason_code="privacy_export_created_dangling_local_reference",
    )]


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



def derivations(receipt):
    return [r for r in records(receipt) if r.get("kind") == "Derivation"]


def transforms(receipt):
    return [r for r in records(receipt) if r.get("kind") == "Transform"]


def ref_id(value):
    return value.get("id") if isinstance(value, dict) else None


def derivation_transform_id(derivation):
    return ref_id(derivation.get("transform"))


def derivation_target_id(derivation):
    return ref_id((derivation.get("target") or {}).get("artifact"))


def contributor_ids(derivation):
    return [
        ref_id((item.get("scope") or {}).get("artifact"))
        for item in derivation.get("contributors", [])
        if ref_id((item.get("scope") or {}).get("artifact"))
    ]


def transform_input_ids(transform, contributing_only=False):
    values = []
    for item in transform.get("inputs", []):
        if contributing_only and item.get("usage_role") not in {"data", "mixed"}:
            continue
        value = ref_id(item.get("artifact"))
        if value:
            values.append(value)
    return values


def transform_generated_ids(transform):
    return [ref_id(x) for x in transform.get("generated", []) if ref_id(x)]


def transform_selected_ids(transform):
    return [ref_id(x) for x in transform.get("selected", []) if ref_id(x)]


def find_transform_for_derivation(receipt, derivation):
    return record_index(receipt).get(derivation_transform_id(derivation))


def text_interval(region):
    if not isinstance(region, dict) or region.get("region_kind") != "text":
        return None
    text = region.get("text")
    if not isinstance(text, dict):
        return None
    start, end = text.get("start"), text.get("end")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
        return None
    return (start, end)


def target_interval(receipt, derivation):
    target = derivation.get("target") or {}
    interval = text_interval(target.get("region"))
    if interval is not None:
        return interval
    target_record = record_index(receipt).get(ref_id(target.get("artifact")))
    representation = (target_record or {}).get("representation") or {}
    text = representation.get("text")
    if isinstance(text, str):
        return (0, len(text))
    return None


def exact_origin_accounted(receipt, derivation):
    if derivation.get("precision") != "exact":
        return False
    if derivation.get("unknown_origin_regions"):
        return False
    target = target_interval(receipt, derivation)
    if target is None:
        return False
    segments = []
    for contributor in derivation.get("contributors", []):
        interval = text_interval(contributor.get("output_region"))
        if interval is not None:
            segments.append(interval)
    for region in derivation.get("generated_output_regions", []):
        interval = text_interval(region)
        if interval is not None:
            segments.append(interval)
    if not segments:
        return False
    start, end = target
    clipped = sorted((max(start, a), min(end, b)) for a, b in segments if b > start and a < end)
    cursor = start
    for a, b in clipped:
        if a > cursor:
            return False
        cursor = max(cursor, b)
    return cursor >= end


def derivation_linkage(receipt, derivation):
    index = record_index(receipt)
    transform = find_transform_for_derivation(receipt, derivation)
    if not isinstance(transform, dict) or transform.get("kind") != "Transform":
        return {
            "transform_ok": False,
            "target_generated": False,
            "contributors_used": False,
            "contributor_set_complete": False,
        }
    generated = set(transform_generated_ids(transform))
    used = set(transform_input_ids(transform))
    contributing = set(transform_input_ids(transform, contributing_only=True))
    contributors = set(contributor_ids(derivation))
    target = derivation_target_id(derivation)
    return {
        "transform_ok": index.get(derivation_transform_id(derivation), {}).get("kind") == "Transform",
        "target_generated": target in generated,
        "contributors_used": contributors <= used and bool(contributors),
        "contributor_set_complete": contributing <= contributors and bool(contributors),
    }


def single_derivation(receipt):
    items = derivations(receipt)
    if len(items) != 1:
        raise ValueError(f"expected one Derivation, found {len(items)}")
    return items[0]


def validate_no_positive_derivation(receipt):
    if derivations(receipt):
        raise ValueError("unexpected positive Derivation assertion")


def derivation_finding(requirement_id, check_id, receipt, object_id, status="valid",
                       domain="conformance", reason_code=None, prohibited=None):
    return make_finding(
        requirement_id,
        check_id,
        object_scope(receipt, object_id),
        domain,
        status,
        reason_code=reason_code,
        prohibited_inferences=prohibited,
    )


def execute_derivation_mapping(requirement_id, check_id, primary):
    if len(primary) != 1:
        raise ValueError("derivation checks require one primary receipt")
    receipt = primary[0]
    index = record_index(receipt)
    xforms = transforms(receipt)

    if check_id == "derivation-use-generation-no-inference-001":
        validate_no_positive_derivation(receipt)
        transform = next((x for x in xforms if transform_input_ids(x) and transform_generated_ids(x)), None)
        if transform is None:
            raise ValueError("use+generation premise missing")
        return [derivation_finding(
            requirement_id, check_id, receipt, transform["id"],
            prohibited=["P1:use_and_generation_imply_derivation"],
        )]

    if check_id in {
        "derivation-transform-cardinality-001",
        "derivation-output-cardinality-001",
        "derivation-input-cardinality-001",
        "derivation-contributor-use-001",
        "derivation-target-generation-001",
        "derivation-binary-shorthand-001",
        "derivation-exact-coverage-001",
        "derivation-partial-positive-001",
        "derivation-region-basis-001",
        "derivation-coordinate-conversion-001",
        "derivation-many-to-one-contributors-001",
        "derivation-generated-region-no-source-001",
        "derivation-unknown-region-blocks-exact-001",
        "derivation-concat-separator-001",
        "derivation-template-static-content-001",
        "derivation-truncate-discarded-001",
        "derivation-redaction-no-equality-001",
        "derivation-no-fabricated-range-001",
    }:
        derivation = single_derivation(receipt)
        transform = find_transform_for_derivation(receipt, derivation)
        linkage = derivation_linkage(receipt, derivation)

        if check_id == "derivation-transform-cardinality-001":
            if linkage["transform_ok"]:
                raise ValueError("invalid transform binding not detected")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"], status="invalid")]

        if check_id == "derivation-output-cardinality-001":
            if linkage["target_generated"]:
                raise ValueError("invalid target binding not detected")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"], status="invalid")]

        if check_id == "derivation-input-cardinality-001":
            if linkage["contributors_used"]:
                raise ValueError("invalid contributor binding not detected")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"], status="invalid")]

        if check_id == "derivation-contributor-use-001":
            if linkage["contributors_used"]:
                raise ValueError("unused contributor not detected")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"], status="invalid",
                reason_code="contributor_not_transform_input",
            )]

        if check_id == "derivation-target-generation-001":
            if linkage["target_generated"]:
                raise ValueError("non-generated target not detected")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"], status="invalid",
                reason_code="derivation_target_not_generated",
            )]

        if check_id == "derivation-binary-shorthand-001":
            if len(derivation.get("contributors", [])) != 1 or not all(linkage.values()):
                raise ValueError("qualified one-input derivation premise missing")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"],
                prohibited=["P1:binary_derived_from_stronger_than_qualified_derivation"],
            )]

        if check_id == "derivation-exact-coverage-001":
            if exact_origin_accounted(receipt, derivation):
                raise ValueError("exact origin gap not detected")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"], status="invalid",
                reason_code="exact_origin_accounting_incomplete",
            )]

        if check_id == "derivation-partial-positive-001":
            if derivation.get("precision") != "partial" or not contributor_ids(derivation):
                raise ValueError("partial positive ancestry premise missing")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"])]

        if check_id == "derivation-region-basis-001":
            scopes = [derivation.get("target") or {}] + [
                item.get("scope") or {} for item in derivation.get("contributors", [])
            ]
            for scope in scopes:
                if scope.get("region") is not None and not scope.get("representation_basis"):
                    raise ValueError("region lacks representation basis")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"])]

        if check_id == "derivation-coordinate-conversion-001":
            target_basis = (derivation.get("target") or {}).get("representation_basis")
            mismatched = any(
                (item.get("scope") or {}).get("region") is not None
                and item.get("output_region") is not None
                and (item.get("scope") or {}).get("representation_basis") != target_basis
                for item in derivation.get("contributors", [])
            )
            if not mismatched:
                raise ValueError("coordinate basis mismatch not detected")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"],
                domain="support", status="unsupported",
                reason_code="coordinate_basis_conversion_not_defined",
            )]

        if check_id == "derivation-many-to-one-contributors-001":
            if derivation.get("precision") != "exact" or linkage["contributor_set_complete"]:
                raise ValueError("incomplete exact contributor set not detected")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"], status="invalid")]

        if check_id == "derivation-generated-region-no-source-001":
            if not derivation.get("generated_output_regions"):
                raise ValueError("transform-generated region missing")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"],
                prohibited=["P1:generated_region_attributed_to_source"],
            )]

        if check_id == "derivation-unknown-region-blocks-exact-001":
            if derivation.get("precision") != "exact" or not derivation.get("unknown_origin_regions"):
                raise ValueError("unknown-origin exact-coverage premise missing")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"],
                domain="completeness", status="unverified",
                reason_code="unknown_origin_region_blocks_exact_coverage",
            )]

        if check_id == "derivation-concat-separator-001":
            if not transform or transform.get("operation") != "concat":
                raise ValueError("concat transform missing")
            if not derivation.get("generated_output_regions") or not exact_origin_accounted(receipt, derivation):
                raise ValueError("concat separator not fully accounted")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"])]

        if check_id == "derivation-template-static-content-001":
            if not transform or transform.get("operation") != "template":
                raise ValueError("template transform missing")
            if not derivation.get("generated_output_regions") or not exact_origin_accounted(receipt, derivation):
                raise ValueError("template static region not accounted")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"],
                prohibited=["P1:template_static_content_attributed_to_interpolated_input"],
            )]

        if check_id == "derivation-truncate-discarded-001":
            if not transform or transform.get("operation") != "truncate":
                raise ValueError("truncate transform missing")
            input_id = transform_input_ids(transform)[0]
            output_id = derivation_target_id(derivation)
            input_text = (index.get(input_id, {}).get("representation") or {}).get("text")
            output_text = (index.get(output_id, {}).get("representation") or {}).get("text")
            scope_region = (derivation.get("contributors", [{}])[0].get("scope") or {}).get("region")
            if not isinstance(input_text, str) or not isinstance(output_text, str) or len(input_text) <= len(output_text):
                raise ValueError("discarded suffix premise missing")
            if text_interval(scope_region) != (0, len(output_text)):
                raise ValueError("retained input region not isolated")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"],
                prohibited=["P1:discarded_truncated_region_contributes_output_content"],
            )]

        if check_id == "derivation-redaction-no-equality-001":
            if not transform or transform.get("operation") != "redact" or derivation.get("precision") != "partial":
                raise ValueError("redaction partial-derivation premise missing")
            input_id = transform_input_ids(transform)[0]
            output_id = derivation_target_id(derivation)
            input_text = (index.get(input_id, {}).get("representation") or {}).get("text")
            output_text = (index.get(output_id, {}).get("representation") or {}).get("text")
            if input_text == output_text:
                raise ValueError("redaction output unexpectedly byte-equal")
            return [derivation_finding(
                requirement_id, check_id, receipt, derivation["id"],
                prohibited=["P1:redaction_derivation_implies_byte_equality"],
            )]

        if check_id == "derivation-no-fabricated-range-001":
            contributor = derivation.get("contributors", [{}])[0]
            if derivation.get("precision") != "partial":
                raise ValueError("precision reduction premise missing")
            if (contributor.get("scope") or {}).get("region") is not None or contributor.get("output_region") is not None:
                raise ValueError("exact range was fabricated")
            return [derivation_finding(requirement_id, check_id, receipt, derivation["id"])]

    if check_id in {
        "derivation-unknown-no-edge-001",
        "derivation-use-role-no-edge-001",
        "derivation-control-no-content-001",
        "transform-selection-no-derivation-001",
        "derivation-absence-not-negation-001",
        "derivation-rerank-control-001",
    }:
        validate_no_positive_derivation(receipt)
        transform = xforms[0] if xforms else None
        if transform is None:
            raise ValueError("Transform premise missing")
        prohibited = {
            "derivation-unknown-no-edge-001": "P1:uncertainty_encoded_as_positive_derivation",
            "derivation-use-role-no-edge-001": "P1:usage_role_implies_derivation",
            "derivation-control-no-content-001": "P1:control_input_derives_output_content",
            "transform-selection-no-derivation-001": "P1:selection_or_rerank_implies_candidate_derivation",
            "derivation-absence-not-negation-001": "P1:missing_derivation_edge_means_no_real_derivation",
            "derivation-rerank-control-001": "P1:excluded_rerank_candidate_derives_selected_content",
        }[check_id]
        if check_id == "derivation-control-no-content-001":
            if not any(x.get("usage_role") == "control" for x in transform.get("inputs", [])):
                raise ValueError("control-only input premise missing")
        if check_id in {"transform-selection-no-derivation-001", "derivation-rerank-control-001"}:
            if transform.get("operation") != "rerank" or not transform_selected_ids(transform):
                raise ValueError("rerank selection premise missing")
        return [derivation_finding(
            requirement_id, check_id, receipt, transform["id"], prohibited=[prohibited]
        )]

    if check_id == "derivation-one-to-many-isolation-001":
        transform = next((x for x in xforms if len(transform_generated_ids(x)) > 1), None)
        if transform is None:
            raise ValueError("one-to-many transform premise missing")
        derived_targets = {derivation_target_id(d) for d in derivations(receipt)}
        missing = [x for x in transform_generated_ids(transform) if x not in derived_targets]
        if not missing:
            raise ValueError("all sibling outputs already have derivations")
        return [derivation_finding(
            requirement_id, check_id, receipt, missing[0],
            prohibited=["P1:one_output_derivation_copied_to_sibling_output"],
        )]

    if check_id in {"derivation-transitive-not-direct-001", "derivation-partial-composition-001"}:
        items = derivations(receipt)
        if len(items) != 2:
            raise ValueError("two-step derivation chain required")
        by_target = {derivation_target_id(d): d for d in items}
        downstream = next(
            (d for d in items if any(cid in by_target for cid in contributor_ids(d))),
            None,
        )
        if downstream is None:
            raise ValueError("transitive derivation chain not found")
        upstream_id = next(cid for cid in contributor_ids(downstream) if cid in by_target)
        upstream = by_target[upstream_id]
        source_ids = set(contributor_ids(upstream))
        if source_ids & set(contributor_ids(downstream)):
            raise ValueError("direct source-to-final derivation already present")
        if check_id == "derivation-transitive-not-direct-001":
            if upstream.get("precision") != "exact" or downstream.get("precision") != "exact":
                raise ValueError("exact transitive premise missing")
            prohibited = "P1:transitive_ancestry_reported_as_direct_derivation"
        else:
            if "partial" not in {upstream.get("precision"), downstream.get("precision")}:
                raise ValueError("partial intermediate premise missing")
            prohibited = "P1:partial_intermediate_yields_exact_composed_mapping"
        return [derivation_finding(
            requirement_id, check_id, receipt, downstream["id"], prohibited=[prohibited]
        )]

    if check_id == "derivation-unknown-composition-001":
        if len(derivations(receipt)) != 1:
            raise ValueError("unknown-middle scenario requires one recorded derivation")
        transform = next((x for x in xforms if x.get("id") == "xf-mid-001"), None)
        if transform is None or not transform_input_ids(transform) or not transform_generated_ids(transform):
            raise ValueError("unknown middle transform premise missing")
        if any(derivation_transform_id(d) == transform["id"] for d in derivations(receipt)):
            raise ValueError("unknown middle step has positive derivation")
        return [derivation_finding(
            requirement_id, check_id, receipt, transform["id"],
            prohibited=["P1:unknown_middle_step_yields_positive_composed_derivation"],
        )]

    raise NotImplementedError(check_id)

def execute_semantic_case(row, case, materialized):
    planned = row["planned_test_id"]
    if planned not in SUPPORTED_PLANNED_TESTS:
        raise NotImplementedError(planned)

    if planned in REQUEST_PLANNED_TESTS:
        return execute_request_case(row, case, materialized)
    if planned in IDENTITY_PLANNED_TESTS:
        return execute_identity_case(row, case, materialized)
    if planned in PROVIDER_ATTEMPT_PLANNED_TESTS:
        return execute_provider_attempt_case(row, case, materialized)

    requirement_id = row["requirement_id"]
    check_id = planned
    primary = primary_receipts(case, materialized)
    resolution = resolution_receipts(case, materialized)

    if planned in DERIVATION_PLANNED_TESTS:
        findings = execute_derivation_mapping(requirement_id, check_id, primary)
    elif planned == "graph-missing-reference-001":
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
