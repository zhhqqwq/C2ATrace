#!/usr/bin/env python3
import base64
import hashlib
from urllib.parse import unquote

import rfc8785


REQUEST_PLANNED_TESTS = {
    "request-attempt-invocation-cardinality-001",
    "request-snapshot-capture-level-001",
    "request-attempt-snapshot-isolation-001",
    "request-invocation-snapshot-reuse-001",
    "request-effective-snapshot-cardinality-001",
    "request-no-synthetic-snapshot-001",
    "request-capture-level-overclaim-001",
    "request-capture-level-unknown-001",
    "request-transition-no-inference-001",
    "request-transition-order-001",
    "request-binding-level-local-001",
    "request-binding-source-cardinality-001",
    "request-binding-target-cardinality-001",
    "request-binding-occurrence-cardinality-001",
    "request-binding-partial-source-001",
    "request-path-scheme-001",
    "request-json-pointer-001",
    "request-path-no-guess-001",
    "request-body-byte-location-001",
    "request-text-coordinate-001",
    "request-text-range-bounds-001",
    "request-text-invalid-scalar-001",
    "request-byte-coordinate-001",
    "request-byte-range-bounds-001",
    "request-region-basis-001",
    "request-binary-byte-binding-001",
    "request-media-encoded-lineage-001",
    "request-semantic-digest-profile-001",
    "request-byte-digest-basis-001",
    "request-digest-compatibility-001",
    "request-semantic-not-byte-001",
    "request-binding-verification-level-001",
    "request-hash-only-sublocation-001",
    "request-commitment-match-wording-001",
    "request-whole-commitment-equality-001",
    "request-redacted-binding-001",
    "request-hmac-verification-001",
    "request-binding-propagation-exact-001",
    "request-binding-propagation-partial-001",
    "request-binding-propagation-unknown-001",
    "request-prepared-body-no-provider-receipt-001",
    "request-prepared-body-no-wire-overclaim-001",
    "request-binding-no-provider-internal-001",
    "request-location-form-001",
    "request-structural-not-resolved-001",
    "request-location-resolution-001",
    "request-whole-snapshot-location-001",
}

CAPTURE_ORDER = {
    "sdk_arguments": 0,
    "provider_payload": 1,
    "prepared_http_body": 2,
}


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def records(receipt):
    return receipt.get("arp", {}).get("records", [])


def receipt_id(receipt):
    return receipt.get("arp", {}).get("receipt_id")


def record_index(receipt):
    return {r.get("id"): r for r in records(receipt) if isinstance(r, dict) and r.get("id")}


def by_kind(receipt, kind):
    return [r for r in records(receipt) if r.get("kind") == kind]


def ref_id(value):
    return value.get("id") if isinstance(value, dict) else None


def finding(requirement_id, check_id, receipt, object_id, domain, status,
            reason_code=None, prohibited=None, evidence_bases=None):
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
    if evidence_bases:
        out["evidence_bases"] = list(evidence_bases)
    return out


def primary_receipt(case, materialized):
    ids = (case.get("harness") or {}).get("primary_documents", [])
    receipts = [
        materialized[x] for x in ids
        if x in materialized and materialized[x].get("kind") == "ReceiptPresentation"
    ]
    if len(receipts) != 1:
        raise ValueError(f"request batch requires one primary receipt, found {len(receipts)}")
    return receipts[0]


def snapshot_index(receipt):
    return {x["id"]: x for x in by_kind(receipt, "RequestSnapshot")}


def binding_index(receipt):
    return {x["id"]: x for x in by_kind(receipt, "RequestBinding")}


def attempt_index(receipt):
    return {x["id"]: x for x in by_kind(receipt, "ProviderAttempt")}


def invocation_index(receipt):
    return {x["id"]: x for x in by_kind(receipt, "ModelInvocation")}


def json_pointer_tokens(pointer):
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("invalid JSON Pointer")
    return [
        unquote(token).replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def resolve_json_pointer(value, pointer):
    current = value
    for token in json_pointer_tokens(pointer):
        if isinstance(current, list):
            if token == "-":
                raise KeyError("-")
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(token)
    return current


def snapshot_representation(snapshot):
    return snapshot.get("representation") or {}


def snapshot_json_value(snapshot):
    rep = snapshot_representation(snapshot)
    if rep.get("representation_kind") != "json":
        raise ValueError("snapshot is not JSON representation")
    return rep["value"]


def snapshot_bytes(snapshot):
    rep = snapshot_representation(snapshot)
    if rep.get("representation_kind") != "bytes":
        raise ValueError("snapshot is not byte representation")
    return base64.b64decode(rep["base64"], validate=True)


def resolve_binding_location(receipt, binding):
    snapshots = snapshot_index(receipt)
    snapshot = snapshots.get(ref_id(binding.get("snapshot")))
    if snapshot is None:
        return {"status": "unresolved", "snapshot": None, "selected": None, "reason": "snapshot_missing"}

    location = binding.get("location")
    if not isinstance(location, dict):
        return {"status": "unresolved", "snapshot": snapshot, "selected": None, "reason": "location_missing"}

    kind = location.get("location_kind")
    if kind == "whole_snapshot":
        rep = snapshot.get("representation")
        if rep is None:
            return {"status": "unverified", "snapshot": snapshot, "selected": None, "reason": "representation_unavailable"}
        return {"status": "resolved", "snapshot": snapshot, "selected": rep, "reason": None}

    if kind in {"structured_value", "structured_text_region"}:
        if snapshot.get("representation") is None:
            return {"status": "unverified", "snapshot": snapshot, "selected": None, "reason": "representation_unavailable"}
        path = location.get("path") or {}
        if path.get("scheme") != "json_pointer":
            return {"status": "unsupported", "snapshot": snapshot, "selected": None, "reason": "path_scheme_unsupported"}
        try:
            selected = resolve_json_pointer(snapshot_json_value(snapshot), path.get("value"))
        except (KeyError, IndexError, ValueError, TypeError):
            return {"status": "unresolved", "snapshot": snapshot, "selected": None, "reason": "request_location_not_found"}
        if kind == "structured_text_region":
            region = location.get("text") or {}
            if not isinstance(selected, str):
                return {"status": "unresolved", "snapshot": snapshot, "selected": selected, "reason": "selected_value_not_text"}
            if any(0xD800 <= ord(ch) <= 0xDFFF for ch in selected):
                return {"status": "unverified", "snapshot": snapshot, "selected": selected, "reason": "selected_text_not_valid_unicode_scalar_sequence"}
            start, end = region.get("start"), region.get("end")
            if region.get("unit") != "unicode_scalar":
                return {"status": "unsupported", "snapshot": snapshot, "selected": selected, "reason": "text_unit_unsupported"}
            if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start <= end <= len(selected)):
                return {"status": "invalid", "snapshot": snapshot, "selected": selected, "reason": "text_region_out_of_bounds"}
            selected = selected[start:end]
        return {"status": "resolved", "snapshot": snapshot, "selected": selected, "reason": None}

    if kind == "byte_region":
        region = location.get("bytes") or {}
        if region.get("unit") != "byte":
            return {"status": "unsupported", "snapshot": snapshot, "selected": None, "reason": "byte_unit_unsupported"}
        try:
            raw = snapshot_bytes(snapshot)
        except (KeyError, ValueError, TypeError):
            return {"status": "unverified", "snapshot": snapshot, "selected": None, "reason": "byte_representation_unavailable"}
        start, end = region.get("start"), region.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start <= end <= len(raw)):
            return {"status": "invalid", "snapshot": snapshot, "selected": raw, "reason": "byte_region_out_of_bounds"}
        return {"status": "resolved", "snapshot": snapshot, "selected": raw[start:end], "reason": None}

    return {"status": "unsupported", "snapshot": snapshot, "selected": None, "reason": "location_form_unsupported"}


def privacy_commitments(receipt, component_id):
    out = []
    for descriptor in receipt.get("arp", {}).get("privacy", []):
        subject_id = ref_id((descriptor.get("subject") or {}).get("ref"))
        if subject_id == component_id:
            out.extend(descriptor.get("commitments", []))
    return out


def commitments_compatible(a, b):
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    fields = ["method", "representation_basis"]
    if any(a.get(k) != b.get(k) for k in fields):
        return False
    if a.get("method") == "hmac-sha256":
        for key in ["key_ref", "comparison_domain", "profile_id"]:
            if a.get(key) != b.get(key):
                return False
    return True


def commitment_values_equal(a, b):
    return commitments_compatible(a, b) and (a.get("value") or {}).get("value") == (b.get("value") or {}).get("value")


def component_commitment_matches(receipt, binding):
    component_id = ref_id(binding.get("component"))
    target = binding.get("target_commitment")
    return any(commitment_values_equal(source, target) for source in privacy_commitments(receipt, component_id))


def component_plaintext_commitment_matches(receipt, binding):
    component = record_index(receipt).get(ref_id(binding.get("component")))
    rep = (component or {}).get("representation") or {}
    text = rep.get("text")
    target = binding.get("target_commitment") or {}
    if not isinstance(text, str) or target.get("method") != "sha256":
        return False
    if target.get("representation_basis") != "decoded_text_utf8":
        return False
    return b64url(hashlib.sha256(text.encode("utf-8")).digest()) == (target.get("value") or {}).get("value")


def request_transition_pairs(receipt):
    index = record_index(receipt)
    pairs = []
    for transform in by_kind(receipt, "Transform"):
        if transform.get("operation") != "request_preparation":
            continue
        inputs = [
            index.get(ref_id(x.get("artifact")))
            for x in transform.get("inputs", [])
        ]
        outputs = [
            index.get(ref_id(x))
            for x in transform.get("generated", [])
        ]
        inputs = [x for x in inputs if isinstance(x, dict) and x.get("kind") == "RequestSnapshot"]
        outputs = [x for x in outputs if isinstance(x, dict) and x.get("kind") == "RequestSnapshot"]
        for source in inputs:
            for target in outputs:
                pairs.append((transform, source, target))
    return pairs


def transition_derivation(receipt, transform_id, source_id, target_id):
    for derivation in by_kind(receipt, "Derivation"):
        if ref_id(derivation.get("transform")) != transform_id:
            continue
        if ref_id((derivation.get("target") or {}).get("artifact")) != target_id:
            continue
        contributors = [
            ref_id((x.get("scope") or {}).get("artifact"))
            for x in derivation.get("contributors", [])
        ]
        if source_id in contributors:
            return derivation
    return None


def semantic_digest_valid(snapshot):
    digest = snapshot.get("semantic_digest")
    if not isinstance(digest, dict):
        return False
    if digest.get("algorithm") != "sha256":
        return False
    if not digest.get("canonicalization_profile"):
        return False
    if digest.get("representation_basis") != snapshot.get("representation_basis"):
        return False
    value = snapshot_json_value(snapshot)
    actual = b64url(hashlib.sha256(rfc8785.dumps(value)).digest())
    return actual == (digest.get("value") or {}).get("value")


def byte_digest_valid(snapshot):
    digest = snapshot.get("byte_digest")
    if not isinstance(digest, dict) or digest.get("algorithm") != "sha256":
        return False
    if digest.get("representation_basis") != snapshot.get("representation_basis"):
        return False
    actual = b64url(hashlib.sha256(snapshot_bytes(snapshot)).digest())
    return actual == (digest.get("value") or {}).get("value")


def invalidity_outcome(findings):
    if any(f.get("domain") == "conformance" and f.get("status") == "invalid" for f in findings):
        return "invalidity_detected"
    return "completed"


def execute_request_case(row, case, materialized):
    requirement_id = row["requirement_id"]
    check_id = row["planned_test_id"]
    if check_id not in REQUEST_PLANNED_TESTS:
        raise NotImplementedError(check_id)

    receipt = primary_receipt(case, materialized)
    index = record_index(receipt)
    snapshots = snapshot_index(receipt)
    bindings = binding_index(receipt)
    attempts = attempt_index(receipt)
    invocations = invocation_index(receipt)
    findings = []

    if check_id == "request-attempt-invocation-cardinality-001":
        attempt = next(iter(attempts.values()))
        target = index.get(ref_id(attempt.get("invocation")))
        if target is None or target.get("kind") != "ModelInvocation":
            findings.append(finding(requirement_id, check_id, receipt, attempt["id"], "conformance", "invalid"))
        else:
            raise ValueError("invalid invocation ownership not detected")

    elif check_id == "request-snapshot-capture-level-001":
        snapshot = next(iter(snapshots.values()))
        if snapshot.get("capture_level") not in {"sdk_arguments", "provider_payload", "prepared_http_body", "unknown"}:
            raise ValueError("semantic snapshot capture level is not core-valid")
        findings.append(finding(requirement_id, check_id, receipt, snapshot["id"], "conformance", "valid"))

    elif check_id == "request-attempt-snapshot-isolation-001":
        offender = None
        for attempt in attempts.values():
            for effective in attempt.get("effective_requests", []):
                snapshot = snapshots.get(ref_id(effective.get("snapshot")))
                if snapshot is None:
                    continue
                owner = ref_id(snapshot.get("attempt_owner"))
                if owner and owner != attempt["id"]:
                    offender = attempt
                    break
            if offender:
                break
        if offender is None:
            raise ValueError("attempt-scoped snapshot reuse violation not detected")
        findings.append(finding(requirement_id, check_id, receipt, offender["id"], "conformance", "invalid"))

    elif check_id == "request-invocation-snapshot-reuse-001":
        offender = None
        for attempt in attempts.values():
            attempt_invocation = ref_id(attempt.get("invocation"))
            for effective in attempt.get("effective_requests", []):
                snapshot = snapshots.get(ref_id(effective.get("snapshot")))
                if snapshot is None:
                    continue
                owner = ref_id(snapshot.get("invocation_owner"))
                if owner and owner != attempt_invocation:
                    offender = attempt
                    break
            if offender:
                break
        if offender is None:
            raise ValueError("cross-invocation snapshot reuse violation not detected")
        findings.append(finding(requirement_id, check_id, receipt, offender["id"], "conformance", "invalid"))

    elif check_id == "request-effective-snapshot-cardinality-001":
        offender = None
        for attempt in attempts.values():
            levels = [x.get("capture_level") for x in attempt.get("effective_requests", [])]
            if len(levels) != len(set(levels)):
                offender = attempt
                break
        if offender is None:
            raise ValueError("duplicate effective capture level not detected")
        findings.append(finding(requirement_id, check_id, receipt, offender["id"], "conformance", "invalid"))

    elif check_id == "request-no-synthetic-snapshot-001":
        attempt = next(iter(attempts.values()))
        if attempt.get("effective_requests") or snapshots:
            raise ValueError("missing capture was materialized")
        findings.append(finding(
            requirement_id, check_id, receipt, attempt["id"], "conformance", "valid",
            prohibited=["P1:missing_capture_synthesized_as_request_snapshot"],
        ))

    elif check_id == "request-capture-level-overclaim-001":
        snapshot = next(iter(snapshots.values()))
        if snapshot.get("capture_level") != "sdk_arguments":
            raise ValueError("sdk_arguments premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, snapshot["id"], "claim", "asserted",
            prohibited=["P1:sdk_arguments_overclaimed_as_provider_boundary"],
        ))

    elif check_id == "request-capture-level-unknown-001":
        snapshot = next(iter(snapshots.values()))
        if snapshot.get("capture_level") != "unknown":
            raise ValueError("unknown capture level premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, snapshot["id"], "conformance", "valid",
            prohibited=["P1:unknown_capture_level_guessed_from_shape_or_adapter"],
        ))

    elif check_id == "request-transition-no-inference-001":
        ordered = sorted(
            [x for x in snapshots.values() if x.get("capture_level") in CAPTURE_ORDER],
            key=lambda x: CAPTURE_ORDER[x["capture_level"]],
        )
        if len(ordered) < 2 or request_transition_pairs(receipt):
            raise ValueError("adjacent-without-transition premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, ordered[-1]["id"], "conformance", "valid",
            prohibited=["P1:adjacent_capture_levels_imply_request_transition"],
        ))

    elif check_id == "request-transition-order-001":
        bad = None
        for transform, source, target in request_transition_pairs(receipt):
            s, t = CAPTURE_ORDER.get(source.get("capture_level")), CAPTURE_ORDER.get(target.get("capture_level"))
            if s is not None and t is not None and t < s:
                bad = transform
                break
        if bad is None:
            raise ValueError("backward request transition not detected")
        findings.append(finding(requirement_id, check_id, receipt, bad["id"], "conformance", "invalid"))

    elif check_id == "request-binding-level-local-001":
        binding = next(iter(bindings.values()))
        if len(request_transition_pairs(receipt)) != 1:
            raise ValueError("transition premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "conformance", "valid",
            prohibited=["P1:binding_automatically_crosses_capture_level_transition"],
        ))

    elif check_id == "request-binding-source-cardinality-001":
        binding = next(iter(bindings.values()))
        component = index.get(ref_id(binding.get("component")))
        if component is not None and component.get("kind") in {"ContextFragment", "ModelInputComponent"}:
            raise ValueError("invalid binding source not detected")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "invalid"))

    elif check_id == "request-binding-target-cardinality-001":
        binding = next(iter(bindings.values()))
        if ref_id(binding.get("snapshot")) not in snapshots or not isinstance(binding.get("location"), dict):
            raise ValueError("semantic binding target is incomplete")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"))

    elif check_id == "request-binding-occurrence-cardinality-001":
        values = list(bindings.values())
        if len(values) < 2:
            raise ValueError("two binding occurrences not present")
        a, b = values[0], values[1]
        if ref_id(a.get("component")) != ref_id(b.get("component")) or a.get("location") == b.get("location"):
            raise ValueError("occurrence multiplicity premise missing")
        findings.append(finding(requirement_id, check_id, receipt, b["id"], "conformance", "valid"))

    elif check_id == "request-binding-partial-source-001":
        binding = next(iter(bindings.values()))
        resolution = resolve_binding_location(receipt, binding)
        component = index.get(ref_id(binding.get("component"))) or {}
        text = (component.get("representation") or {}).get("text")
        location = binding.get("location") or {}
        region = location.get("text") or {}
        partial_target = (
            isinstance(resolution.get("selected"), str)
            and isinstance(text, str)
            and region.get("start") == 0
            and isinstance(region.get("end"), int)
            and region.get("end") < len(text)
        )
        if not partial_target or binding.get("source_scope") is not None:
            raise ValueError("partial-source omission premise missing")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "invalid"))

    elif check_id == "request-path-scheme-001":
        binding = next(iter(bindings.values()))
        path = (binding.get("location") or {}).get("path") or {}
        if not path.get("scheme"):
            raise ValueError("semantic path scheme missing")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"))

    elif check_id == "request-json-pointer-001":
        binding = next(iter(bindings.values()))
        path = (binding.get("location") or {}).get("path") or {}
        snapshot = snapshots.get(ref_id(binding.get("snapshot")))
        if path.get("scheme") != "json_pointer" or (snapshot or {}).get("representation_basis") != "json-data-model":
            raise ValueError("JSON Pointer interoperability premise missing")
        resolve_json_pointer(snapshot_json_value(snapshot), path.get("value"))
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"))

    elif check_id == "request-path-no-guess-001":
        binding = next(iter(bindings.values()))
        path = (binding.get("location") or {}).get("path") or {}
        if path.get("scheme") in {None, "json_pointer"}:
            raise ValueError("unsupported path scheme premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "support", "unsupported",
            reason_code="request_path_scheme_unsupported",
            prohibited=["P1:unsupported_path_scheme_guessed"],
        ))

    elif check_id == "request-body-byte-location-001":
        binding = next(iter(bindings.values()))
        snapshot = snapshots.get(ref_id(binding.get("snapshot")))
        if (snapshot or {}).get("capture_level") != "prepared_http_body":
            raise ValueError("prepared body premise missing")
        if (binding.get("location") or {}).get("location_kind") == "byte_region":
            raise ValueError("explicit byte region unexpectedly present")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "claim", "asserted",
            prohibited=["P1:structured_path_alone_proves_prepared_body_byte_inclusion"],
        ))

    elif check_id == "request-text-coordinate-001":
        binding = next(iter(bindings.values()))
        region = (binding.get("location") or {}).get("text") or {}
        if region.get("unit") != "unicode_scalar":
            raise ValueError("Unicode scalar text coordinate missing")
        if resolve_binding_location(receipt, binding)["status"] != "resolved":
            raise ValueError("valid text region did not resolve")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"))

    elif check_id == "request-text-range-bounds-001":
        binding = next(iter(bindings.values()))
        resolution = resolve_binding_location(receipt, binding)
        if resolution["reason"] != "text_region_out_of_bounds":
            raise ValueError("text out-of-bounds premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "conformance", "invalid",
            reason_code="text_region_out_of_bounds",
        ))

    elif check_id == "request-text-invalid-scalar-001":
        binding = next(iter(bindings.values()))
        resolution = resolve_binding_location(receipt, binding)
        if resolution["reason"] != "selected_text_not_valid_unicode_scalar_sequence":
            raise ValueError("ill-formed scalar premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "support", "unverified",
            reason_code="selected_text_not_valid_unicode_scalar_sequence",
        ))

    elif check_id == "request-byte-coordinate-001":
        binding = next(iter(bindings.values()))
        region = (binding.get("location") or {}).get("bytes") or {}
        if region.get("unit") != "byte" or resolve_binding_location(receipt, binding)["status"] != "resolved":
            raise ValueError("valid byte coordinate premise missing")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"))

    elif check_id == "request-byte-range-bounds-001":
        binding = next(iter(bindings.values()))
        resolution = resolve_binding_location(receipt, binding)
        if resolution["reason"] != "byte_region_out_of_bounds":
            raise ValueError("byte out-of-bounds premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "conformance", "invalid",
            reason_code="byte_region_out_of_bounds",
        ))

    elif check_id == "request-region-basis-001":
        binding = next(iter(bindings.values()))
        source_scope = binding.get("source_scope") or {}
        snapshot = snapshots.get(ref_id(binding.get("snapshot"))) or {}
        if source_scope.get("representation_basis") == snapshot.get("representation_basis"):
            raise ValueError("region basis mismatch premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "support", "unsupported",
            reason_code="request_region_basis_mapping_not_defined",
            prohibited=["P1:request_region_basis_silently_converted"],
        ))

    elif check_id == "request-binary-byte-binding-001":
        binding = next(iter(bindings.values()))
        resolution = resolve_binding_location(receipt, binding)
        if resolution["status"] != "resolved" or (resolution["snapshot"] or {}).get("representation_basis") != "captured_bytes":
            raise ValueError("binary byte binding did not resolve")
        findings.extend([
            finding(requirement_id, check_id, receipt, binding["id"], "resolution", "resolved"),
            finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"),
        ])

    elif check_id == "request-media-encoded-lineage-001":
        binding = next(iter(bindings.values()))
        component_id = ref_id(binding.get("component"))
        component = index.get(component_id) or {}
        resolution = resolve_binding_location(receipt, binding)
        transform = next(
            (x for x in by_kind(receipt, "Transform")
             if x.get("operation") == "base64_encode"
             and component_id in [ref_id(y) for y in x.get("generated", [])]),
            None,
        )
        derivation = next(
            (x for x in by_kind(receipt, "Derivation")
             if ref_id((x.get("target") or {}).get("artifact")) == component_id
             and transform and ref_id(x.get("transform")) == transform["id"]),
            None,
        )
        if transform is None or derivation is None or resolution["status"] != "resolved":
            raise ValueError("encoded-media lineage premise missing")
        if (component.get("representation") or {}).get("text") != resolution["selected"]:
            raise ValueError("binding is not to visible encoded representation")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"))

    elif check_id == "request-semantic-digest-profile-001":
        snapshot = next(iter(snapshots.values()))
        if not semantic_digest_valid(snapshot):
            raise ValueError("semantic digest/profile verification failed")
        findings.append(finding(requirement_id, check_id, receipt, snapshot["id"], "conformance", "valid"))

    elif check_id == "request-byte-digest-basis-001":
        snapshot = next(iter(snapshots.values()))
        if not byte_digest_valid(snapshot):
            raise ValueError("byte digest verification failed")
        findings.append(finding(
            requirement_id, check_id, receipt, snapshot["id"], "claim", "asserted",
            prohibited=["P1:captured_byte_digest_proves_later_transport_or_provider_received_bytes"],
        ))

    elif check_id == "request-digest-compatibility-001":
        values = [x for x in snapshots.values() if isinstance(x.get("semantic_digest"), dict)]
        if len(values) < 2:
            raise ValueError("two semantic digests required")
        a, b = values[0]["semantic_digest"], values[1]["semantic_digest"]
        compatible = (
            a.get("algorithm") == b.get("algorithm")
            and a.get("representation_basis") == b.get("representation_basis")
            and a.get("canonicalization_profile") == b.get("canonicalization_profile")
        )
        if compatible:
            raise ValueError("incompatible digest bases not detected")
        subject = values[1]
        findings.append(finding(
            requirement_id, check_id, receipt, subject["id"], "comparison", "unverified",
            reason_code="request_digest_bases_incompatible",
        ))

    elif check_id == "request-semantic-not-byte-001":
        values = [x for x in snapshots.values() if isinstance(x.get("semantic_digest"), dict)]
        if len(values) < 2:
            raise ValueError("semantic peers missing")
        a, b = values[0], values[1]
        sem_a, sem_b = a["semantic_digest"], b["semantic_digest"]
        compatible = (
            sem_a.get("algorithm") == sem_b.get("algorithm")
            and sem_a.get("representation_basis") == sem_b.get("representation_basis")
            and sem_a.get("canonicalization_profile") == sem_b.get("canonicalization_profile")
        )
        if not compatible or (sem_a.get("value") or {}).get("value") != (sem_b.get("value") or {}).get("value"):
            raise ValueError("semantic equality premise missing")
        byte_a, byte_b = a.get("byte_digest"), b.get("byte_digest")
        if not byte_a or not byte_b or (byte_a.get("value") or {}).get("value") == (byte_b.get("value") or {}).get("value"):
            raise ValueError("byte inequality premise missing")
        findings.extend([
            finding(requirement_id, check_id, receipt, b["id"], "comparison", "matched"),
            finding(
                requirement_id, check_id, receipt, b["id"], "conformance", "valid",
                prohibited=["P1:semantic_digest_equality_implies_byte_equality"],
            ),
        ])

    elif check_id == "request-binding-verification-level-001":
        resolved = bindings["bind-001"]
        missing = bindings["bind-missing-001"]
        commit_only = bindings["bind-commit-only-001"]
        if resolve_binding_location(receipt, resolved)["status"] != "resolved":
            raise ValueError("resolved binding premise failed")
        if resolve_binding_location(receipt, missing)["status"] != "unresolved":
            raise ValueError("missing binding premise failed")
        if not component_commitment_matches(receipt, commit_only):
            raise ValueError("commitment-only comparison did not match")
        if resolve_binding_location(receipt, commit_only)["status"] != "unverified":
            raise ValueError("commitment-only location should be unverified")
        findings.extend([
            finding(requirement_id, check_id, receipt, resolved["id"], "resolution", "resolved"),
            finding(requirement_id, check_id, receipt, missing["id"], "resolution", "unresolved"),
            finding(requirement_id, check_id, receipt, commit_only["id"], "comparison", "matched"),
            finding(requirement_id, check_id, receipt, commit_only["id"], "resolution", "unverified"),
        ])

    elif check_id == "request-hash-only-sublocation-001":
        binding = next(iter(bindings.values()))
        if resolve_binding_location(receipt, binding)["status"] not in {"unverified", "unresolved"}:
            raise ValueError("hash-only sublocation unexpectedly resolved")
        if not component_plaintext_commitment_matches(receipt, binding):
            raise ValueError("recorded sublocation commitment does not match source plaintext")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "resolution", "unverified",
            prohibited=["P1:whole_snapshot_digest_proves_sublocation_membership"],
        ))

    elif check_id in {"request-commitment-match-wording-001", "request-whole-commitment-equality-001"}:
        binding = next(iter(bindings.values()))
        if not component_commitment_matches(receipt, binding):
            raise ValueError("compatible source/target commitments do not match")
        if check_id == "request-whole-commitment-equality-001" and (binding.get("location") or {}).get("location_kind") != "whole_snapshot":
            raise ValueError("whole-scope commitment premise missing")
        prohibited = (
            "P1:commitment_match_implies_target_location_membership"
            if check_id == "request-commitment-match-wording-001"
            else "P1:whole_commitment_equality_implies_identity_or_external_truth"
        )
        findings.extend([
            finding(requirement_id, check_id, receipt, binding["id"], "comparison", "matched"),
            finding(requirement_id, check_id, receipt, binding["id"], "claim", "asserted", prohibited=[prohibited]),
        ])

    elif check_id == "request-redacted-binding-001":
        binding = next(iter(bindings.values()))
        snapshot = snapshots.get(ref_id(binding.get("snapshot"))) or {}
        rep = snapshot_representation(snapshot)
        value = rep.get("value")
        if "[REDACTED]" not in repr(value):
            raise ValueError("redacted snapshot premise missing")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "conformance", "valid",
            prohibited=["P1:redacted_snapshot_verifies_unavailable_pre_redaction_content"],
        ))

    elif check_id == "request-hmac-verification-001":
        binding = next(iter(bindings.values()))
        source = privacy_commitments(receipt, ref_id(binding.get("component")))
        target = binding.get("target_commitment")
        if not any(commitment_values_equal(x, target) for x in source):
            raise ValueError("HMAC commitment metadata mismatch")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "comparison", "unverified",
            reason_code="hmac_secret_capability_unavailable",
        ))

    elif check_id in {
        "request-binding-propagation-exact-001",
        "request-binding-propagation-partial-001",
        "request-binding-propagation-unknown-001",
    }:
        binding = next(iter(bindings.values()))
        source_id = ref_id(binding.get("snapshot"))
        pairs = [
            (transform, source, target)
            for transform, source, target in request_transition_pairs(receipt)
            if source["id"] == source_id
        ]
        if len(pairs) != 1:
            raise ValueError("single request transition path required")
        transform, source, target = pairs[0]
        derivation = transition_derivation(receipt, transform["id"], source["id"], target["id"])
        if check_id == "request-binding-propagation-exact-001":
            if derivation is None or derivation.get("precision") != "exact":
                raise ValueError("exact request transition mapping missing")
            if (derivation.get("target") or {}).get("representation_basis") != source.get("representation_basis"):
                raise ValueError("request transition coordinate basis incompatible")
            findings.append(finding(
                requirement_id, check_id, receipt, target["id"], "claim", "established",
                evidence_bases=["E1"],
            ))
        elif check_id == "request-binding-propagation-partial-001":
            if derivation is None or derivation.get("precision") != "partial":
                raise ValueError("partial request transition premise missing")
            findings.append(finding(
                requirement_id, check_id, receipt, target["id"], "claim", "unverified",
                prohibited=["P1:partial_request_transition_yields_exact_binding_propagation"],
            ))
        else:
            if derivation is not None:
                raise ValueError("unknown request transition unexpectedly has positive derivation")
            findings.append(finding(
                requirement_id, check_id, receipt, target["id"], "claim", "unverified",
                prohibited=["P1:unknown_request_transition_yields_positive_binding"],
            ))

    elif check_id in {
        "request-prepared-body-no-provider-receipt-001",
        "request-prepared-body-no-wire-overclaim-001",
    }:
        snapshot = next(iter(snapshots.values()))
        if snapshot.get("capture_level") != "prepared_http_body":
            raise ValueError("prepared body capture premise missing")
        prohibited = (
            "P1:prepared_http_body_proves_provider_receipt"
            if check_id == "request-prepared-body-no-provider-receipt-001"
            else "P1:prepared_http_body_proves_complete_wire_request"
        )
        findings.append(finding(
            requirement_id, check_id, receipt, snapshot["id"], "claim", "asserted",
            prohibited=[prohibited],
        ))

    elif check_id == "request-binding-no-provider-internal-001":
        binding = next(iter(bindings.values()))
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "claim", "asserted",
            prohibited=["P1:request_binding_proves_provider_or_model_internal_representation"],
        ))

    elif check_id == "request-location-form-001":
        binding = next(iter(bindings.values()))
        kind = (binding.get("location") or {}).get("location_kind")
        if kind not in {"whole_snapshot", "structured_value", "structured_text_region", "byte_region"}:
            raise ValueError("recognized request location form missing")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "conformance", "valid"))

    elif check_id == "request-structural-not-resolved-001":
        binding = next(iter(bindings.values()))
        resolution = resolve_binding_location(receipt, binding)
        if resolution["status"] != "unresolved":
            raise ValueError("structurally valid missing path unexpectedly resolved")
        findings.append(finding(
            requirement_id, check_id, receipt, binding["id"], "resolution", "unresolved",
            reason_code="request_location_not_found",
        ))

    elif check_id == "request-location-resolution-001":
        binding = next(iter(bindings.values()))
        if resolve_binding_location(receipt, binding)["status"] != "resolved":
            raise ValueError("request location failed to resolve")
        findings.append(finding(requirement_id, check_id, receipt, binding["id"], "resolution", "resolved"))

    elif check_id == "request-whole-snapshot-location-001":
        binding = next(iter(bindings.values()))
        if (binding.get("location") or {}).get("location_kind") != "whole_snapshot":
            raise ValueError("whole snapshot location premise missing")
        if resolve_binding_location(receipt, binding)["status"] != "resolved":
            raise ValueError("whole snapshot representation unavailable")
        findings.extend([
            finding(requirement_id, check_id, receipt, binding["id"], "resolution", "resolved"),
            finding(
                requirement_id, check_id, receipt, binding["id"], "conformance", "valid",
                prohibited=["P1:whole_snapshot_interpreted_as_unspecified_sublocation"],
            ),
        ])

    else:
        raise NotImplementedError(check_id)

    outcome = invalidity_outcome(findings)
    if check_id == "request-text-invalid-scalar-001":
        outcome = "incomplete_evaluation"

    return {
        "findings": findings,
        "process_outcome": outcome,
        "completeness": {},
    }
