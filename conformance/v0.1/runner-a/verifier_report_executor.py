#!/usr/bin/env python3

VERIFIER_REPORT_REQUIREMENTS = {
    "verifier-finding-premises-001": "VFY-073",
    "verifier-composition-weakest-premise-001": "VFY-074",
    "verifier-established-scope-001": "VFY-075",
    "verifier-matched-scope-001": "VFY-076",
    "verifier-unverified-semantics-001": "VFY-079",
    "verifier-unsupported-semantics-001": "VFY-080",
    "verifier-invalid-bounded-001": "VFY-081",
    "verifier-mismatch-semantics-001": "VFY-082",
    "verifier-typed-status-domains-001": "VFY-084",
    "verifier-valid-not-true-001": "VFY-085",
}

VERIFIER_REPORT_PLANNED_TESTS = set(VERIFIER_REPORT_REQUIREMENTS)


def primary_report(case, materialized):
    document_ids = (case.get("harness") or {}).get("primary_documents", [])
    reports = [
        materialized[document_id]
        for document_id in document_ids
        if (
            document_id in materialized
            and isinstance(materialized[document_id], dict)
            and materialized[document_id].get("kind") == "VerificationReport"
        )
    ]
    if len(reports) != 1:
        raise ValueError(
            f"verifier-report batch requires one primary VerificationReport, found {len(reports)}"
        )
    report = reports[0]
    if not isinstance(report.get("report_id"), str) or not report["report_id"]:
        raise ValueError("VerificationReport report_id is missing")
    if not isinstance(report.get("process_outcome"), str) or not report["process_outcome"]:
        raise ValueError("VerificationReport process_outcome is missing")
    if not isinstance(report.get("findings"), list):
        raise ValueError("VerificationReport findings is not an array")
    return report


def finding_index(report):
    index = {}
    for finding in report.get("findings", []):
        if not isinstance(finding, dict):
            raise ValueError("VerificationReport contains a non-object finding")
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id:
            raise ValueError("VerificationReport contains finding without string finding_id")
        if finding_id in index:
            raise ValueError(f"VerificationReport contains duplicate finding_id {finding_id}")
        index[finding_id] = finding
    return index


def report_scope(report):
    return {"report_id": report["report_id"]}


def normalized_finding(
    requirement_id,
    check_id,
    report,
    domain,
    status,
    reason_code=None,
    prohibited=None,
):
    out = {
        "requirement_id": requirement_id,
        "check_id": check_id,
        "subject_scope": report_scope(report),
        "domain": domain,
        "status": status,
    }
    if reason_code is not None:
        out["reason_code"] = reason_code
    if prohibited:
        out["prohibited_inferences"] = list(prohibited)
    return out


def findings_matching(report, *, domain=None, status=None, reason_code=None):
    matches = []
    for finding in report.get("findings", []):
        if domain is not None and finding.get("domain") != domain:
            continue
        if status is not None and finding.get("status") != status:
            continue
        if reason_code is not None and finding.get("reason_code") != reason_code:
            continue
        matches.append(finding)
    return matches


def one_finding(report, *, domain=None, status=None, reason_code=None):
    matches = findings_matching(
        report,
        domain=domain,
        status=status,
        reason_code=reason_code,
    )
    if len(matches) != 1:
        raise ValueError(
            "expected one VerificationFinding for "
            f"domain={domain!r} status={status!r} reason_code={reason_code!r}; "
            f"found {len(matches)}"
        )
    return matches[0]


def require_receipt_subject_in_invocation(report, finding):
    subject = finding.get("subject") or {}
    if subject.get("subject_kind") != "receipt":
        raise ValueError("finding is not scoped to a receipt subject")
    receipt_id = subject.get("receipt_id")
    receipt_ids = (report.get("invocation") or {}).get("receipt_ids", [])
    if not isinstance(receipt_id, str) or receipt_id not in receipt_ids:
        raise ValueError("finding receipt subject is outside the verification invocation scope")


def execute_finding_premises(requirement_id, planned, report, index):
    composed = one_finding(
        report,
        domain="claim",
        status="unknown",
        reason_code="weakest_premise_unresolved",
    )
    premises = composed.get("premises")
    if not isinstance(premises, list) or not premises:
        raise ValueError("composed finding does not preserve premise references")
    missing = [premise_id for premise_id in premises if premise_id not in index]
    if missing:
        raise ValueError(f"composed finding contains unresolved premise ids: {missing}")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "conformance",
        "valid",
        reason_code="premise_references_traceable",
    )]


def execute_weakest_premise(requirement_id, planned, report, index):
    composed = one_finding(
        report,
        domain="claim",
        status="unknown",
        reason_code="weakest_premise_unresolved",
    )
    premise_ids = composed.get("premises")
    if not isinstance(premise_ids, list) or not premise_ids:
        raise ValueError("composed conclusion has no explicit premises")
    premises = []
    for premise_id in premise_ids:
        premise = index.get(premise_id)
        if premise is None:
            raise ValueError(f"composed conclusion premise {premise_id} did not resolve")
        premises.append(premise)
    if not any(
        premise.get("status") in {"unresolved", "asserted"}
        for premise in premises
    ):
        raise ValueError("scenario has no unresolved or asserted limiting premise")
    if not any(
        premise.get("domain") == "resolution"
        and premise.get("status") == "unresolved"
        and premise.get("reason_code") == "prerequisite_unresolved"
        for premise in premises
    ):
        raise ValueError("expected unresolved prerequisite premise is missing")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "claim",
        "unknown",
        reason_code="weakest_premise_unresolved",
        prohibited=["P1:unresolved_premise_is_silently_upgraded_in_composed_claim"],
    )]


def execute_established_scope(requirement_id, planned, report):
    source = one_finding(report, domain="claim", status="established")
    require_receipt_subject_in_invocation(report, source)
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "claim",
        "established",
        prohibited=["P1:established_scoped_claim_becomes_unbounded_global_truth"],
    )]


def execute_matched_scope(requirement_id, planned, report):
    source = one_finding(report, domain="comparison", status="matched")
    require_receipt_subject_in_invocation(report, source)
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "comparison",
        "matched",
        prohibited=["P1:matched_comparison_is_factual_truth"],
    )]


def execute_unverified(requirement_id, planned, report):
    source = one_finding(
        report,
        domain="comparison",
        status="unverified",
        reason_code="required_capability_unavailable",
    )
    capability = source.get("capability")
    if not isinstance(capability, str) or not capability:
        raise ValueError("unverified finding does not identify the unavailable capability")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "comparison",
        "unverified",
        reason_code="required_capability_unavailable",
    )]


def execute_unsupported(requirement_id, planned, report):
    source = one_finding(
        report,
        domain="support",
        status="unsupported",
        reason_code="profile_not_implemented",
    )
    subject = source.get("subject") or {}
    if subject.get("subject_kind") != "profile" or not isinstance(subject.get("profile_id"), str):
        raise ValueError("unsupported finding is not scoped to a profile")
    profile_id = subject["profile_id"]
    implemented = set((report.get("verifier") or {}).get("profiles", []))
    implemented.update(
        ((report.get("invocation") or {}).get("capability_summary") or {}).get(
            "supported_profiles", []
        )
    )
    if profile_id in implemented:
        raise ValueError("unsupported profile is declared implemented by the verifier invocation")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "support",
        "unsupported",
        reason_code="profile_not_implemented",
    )]


def execute_invalid_bounded(requirement_id, planned, report):
    source = one_finding(
        report,
        domain="conformance",
        status="invalid",
        reason_code="local_check_failed",
    )
    if not isinstance(source.get("check_id"), str) or not source["check_id"]:
        raise ValueError("invalid finding does not identify the failed check")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "conformance",
        "invalid",
        reason_code="local_check_failed",
        prohibited=["P1:check_local_invalidity_becomes_universal_falsehood"],
    )]


def execute_mismatched(requirement_id, planned, report):
    source = one_finding(
        report,
        domain="comparison",
        status="mismatched",
        reason_code="comparison_performed_and_failed",
    )
    if not isinstance(source.get("check_id"), str) or not source["check_id"]:
        raise ValueError("mismatched finding does not identify the performed comparison")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "comparison",
        "mismatched",
        reason_code="comparison_performed_and_failed",
        prohibited=["P1:mismatched_emitted_without_actual_comparison"],
    )]


def execute_typed_domains(requirement_id, report):
    typed = [
        ("typed-claim", "claim", "asserted"),
        ("typed-comparison", "comparison", "matched"),
        ("typed-resolution", "resolution", "resolved"),
        ("typed-support", "support", "unsupported"),
        ("typed-presence", "presence", "not_present"),
    ]
    findings = []
    for check_id, domain, status in typed:
        one_finding(report, domain=domain, status=status)
        findings.append(normalized_finding(
            requirement_id,
            check_id,
            report,
            domain,
            status,
        ))
    return findings


def execute_valid_not_true(requirement_id, planned, report):
    one_finding(report, domain="conformance", status="valid")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "conformance",
        "valid",
        prohibited=["P1:valid_check_result_means_factual_truth"],
    )]


def execute_verifier_report_case(row, case, materialized):
    planned = row["planned_test_id"]
    requirement_id = row["requirement_id"]
    expected_requirement = VERIFIER_REPORT_REQUIREMENTS.get(planned)
    if expected_requirement is None:
        raise NotImplementedError(planned)
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{planned}")

    report = primary_report(case, materialized)
    index = finding_index(report)

    if planned == "verifier-finding-premises-001":
        findings = execute_finding_premises(requirement_id, planned, report, index)
    elif planned == "verifier-composition-weakest-premise-001":
        findings = execute_weakest_premise(requirement_id, planned, report, index)
    elif planned == "verifier-established-scope-001":
        findings = execute_established_scope(requirement_id, planned, report)
    elif planned == "verifier-matched-scope-001":
        findings = execute_matched_scope(requirement_id, planned, report)
    elif planned == "verifier-unverified-semantics-001":
        findings = execute_unverified(requirement_id, planned, report)
    elif planned == "verifier-unsupported-semantics-001":
        findings = execute_unsupported(requirement_id, planned, report)
    elif planned == "verifier-invalid-bounded-001":
        findings = execute_invalid_bounded(requirement_id, planned, report)
    elif planned == "verifier-mismatch-semantics-001":
        findings = execute_mismatched(requirement_id, planned, report)
    elif planned == "verifier-typed-status-domains-001":
        findings = execute_typed_domains(requirement_id, report)
    elif planned == "verifier-valid-not-true-001":
        findings = execute_valid_not_true(requirement_id, planned, report)
    else:
        raise NotImplementedError(planned)

    return {
        "findings": findings,
        "process_outcome": report["process_outcome"],
        "completeness": dict(report.get("completeness") or {}),
    }

# Runner A Wave 03 Batch 25: verifier conflict/completeness core.
_BATCH25_VERIFIER_REQUIREMENTS = {
    "verifier-history-completeness-default-001": "VFY-090",
    "verifier-conflict-independent-checks-001": "VFY-096",
    "verifier-unsupported-no-downgrade-001": "VFY-097",
    "verifier-profile-no-code-execution-001": "VFY-099",
    "verifier-consistent-bounded-001": "VFY-151",
    "verifier-conflict-and-invalid-001": "VFY-153",
    "verifier-conflict-not-universal-invalidity-001": "VFY-154",
}
VERIFIER_REPORT_REQUIREMENTS.update(_BATCH25_VERIFIER_REQUIREMENTS)
VERIFIER_REPORT_PLANNED_TESTS.update(_BATCH25_VERIFIER_REQUIREMENTS)


def require_conflict_completeness_report(report):
    if report.get("process_outcome") != "completed":
        raise ValueError("conflict/completeness VerificationReport is not completed")

    invocation = report.get("invocation") or {}
    receipt_ids = invocation.get("receipt_ids")
    if (
        not isinstance(receipt_ids, list)
        or not receipt_ids
        or any(not isinstance(receipt_id, str) or not receipt_id for receipt_id in receipt_ids)
        or len(set(receipt_ids)) != len(receipt_ids)
    ):
        raise ValueError("VerificationReport invocation receipt scope is missing or ambiguous")
    receipt_scope = set(receipt_ids)

    completeness = report.get("completeness")
    if not isinstance(completeness, dict):
        raise ValueError("VerificationReport completeness block is missing")
    expected_completeness = {
        "package_inventory": "established",
        "reference_closure": "established",
        "runtime_history": "unknown",
    }
    if any(completeness.get(key) != value for key, value in expected_completeness.items()):
        raise ValueError("VerificationReport completeness block does not preserve bounded history scope")

    index = finding_index(report)
    for finding in index.values():
        subject = finding.get("subject") or {}
        receipt_id = subject.get("receipt_id")
        if receipt_id is not None and receipt_id not in receipt_scope:
            raise ValueError(
                f"finding {finding.get('finding_id')} is outside the verification invocation receipt scope"
            )
    return index, receipt_scope


def finding_receipt_scope(finding):
    subject = finding.get("subject") or {}
    if subject.get("subject_kind") not in {"receipt", "object"}:
        raise ValueError("finding is not scoped to a supplied receipt/object")
    receipt_id = subject.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id:
        raise ValueError("finding supplied scope has no receipt_id")
    return receipt_id


def require_unsupported_profile_source(report):
    source = one_finding(
        report,
        domain="support",
        status="unsupported",
        reason_code="profile_not_implemented",
    )
    subject = source.get("subject") or {}
    if subject.get("subject_kind") != "profile":
        raise ValueError("unsupported finding is not scoped to a profile identifier")
    profile_id = subject.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id:
        raise ValueError("unsupported profile identifier is missing")

    supported = set((report.get("verifier") or {}).get("profiles", []))
    supported.update(
        ((report.get("invocation") or {}).get("capability_summary") or {}).get(
            "supported_profiles", []
        )
    )
    if profile_id in supported:
        raise ValueError("unsupported profile is declared supported by the verifier invocation")
    return source


def execute_history_completeness_default(requirement_id, planned, report):
    source = one_finding(
        report,
        domain="completeness",
        status="unknown",
        reason_code="runtime_history_not_established",
    )
    require_receipt_subject_in_invocation(report, source)
    if (report.get("completeness") or {}).get("runtime_history") != "unknown":
        raise ValueError("runtime history completeness was silently upgraded")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "completeness",
        "unknown",
        reason_code="runtime_history_not_established",
    )]


def execute_conflict_independent_checks(requirement_id, report):
    conflict = one_finding(report, domain="conflict", status="conflict")
    valid = one_finding(report, domain="conformance", status="valid")
    conflict_receipt = finding_receipt_scope(conflict)
    valid_receipt = finding_receipt_scope(valid)
    if conflict_receipt == valid_receipt:
        raise ValueError("independent valid check is not separate from the conflicting scope")
    require_receipt_subject_in_invocation(report, valid)
    if conflict_receipt not in set((report.get("invocation") or {}).get("receipt_ids", [])):
        raise ValueError("conflict finding is outside the verification invocation")
    return [
        normalized_finding(
            requirement_id,
            "conflicting-scope",
            report,
            "conflict",
            "conflict",
        ),
        normalized_finding(
            requirement_id,
            "independent-scope",
            report,
            "conformance",
            "valid",
        ),
    ]


def execute_unsupported_no_downgrade(requirement_id, planned, report):
    require_unsupported_profile_source(report)
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "support",
        "unsupported",
        reason_code="profile_not_implemented",
        prohibited=["P1:unsupported_profile_silently_downgraded_to_baseline"],
    )]


def execute_profile_identifier_no_code(requirement_id, planned, report):
    source = require_unsupported_profile_source(report)
    subject = source.get("subject") or {}
    if set(subject) != {"subject_kind", "profile_id"}:
        raise ValueError("profile finding subject contains non-declarative execution material")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "support",
        "unsupported",
        prohibited=["P1:profile_identifier_authorizes_or_executes_code"],
    )]


def execute_consistent_bounded(requirement_id, planned, report):
    source = one_finding(report, domain="conflict", status="consistent")
    require_receipt_subject_in_invocation(report, source)
    message = source.get("message")
    if not isinstance(message, str) or "supplied scope" not in message.lower():
        raise ValueError("consistent finding does not preserve supplied-scope boundedness")
    return [normalized_finding(
        requirement_id,
        planned,
        report,
        "conflict",
        "consistent",
        prohibited=["P1:consistent_supplied_scope_means_global_truth_or_completeness"],
    )]


def execute_conflict_and_invalid(requirement_id, report):
    conflict = one_finding(report, domain="conflict", status="conflict")
    invalid = one_finding(
        report,
        domain="conformance",
        status="invalid",
        reason_code="local_structural_invalidity",
    )
    conflict_receipt = finding_receipt_scope(conflict)
    invalid_receipt = finding_receipt_scope(invalid)
    if conflict_receipt != invalid_receipt:
        raise ValueError("conflict and structural invalidity do not coexist on the same supplied scope")
    if conflict_receipt not in set((report.get("invocation") or {}).get("receipt_ids", [])):
        raise ValueError("coexisting conflict/invalidity scope is outside the verification invocation")
    return [
        normalized_finding(
            requirement_id,
            "coexisting-conflict",
            report,
            "conflict",
            "conflict",
        ),
        normalized_finding(
            requirement_id,
            "coexisting-invalidity",
            report,
            "conformance",
            "invalid",
        ),
    ]


def execute_conflict_not_universal_invalidity(requirement_id, report):
    conflict = one_finding(report, domain="conflict", status="conflict")
    valid = one_finding(report, domain="conformance", status="valid")
    conflict_receipt = finding_receipt_scope(conflict)
    valid_receipt = finding_receipt_scope(valid)
    if conflict_receipt == valid_receipt:
        raise ValueError("conflict scenario lacks an independent valid supplied scope")
    require_receipt_subject_in_invocation(report, valid)
    if conflict_receipt not in set((report.get("invocation") or {}).get("receipt_ids", [])):
        raise ValueError("conflict scope is outside the verification invocation")
    return [
        normalized_finding(
            requirement_id,
            "conflicting-scope",
            report,
            "conflict",
            "conflict",
            prohibited=["P1:conflict_alone_makes_all_material_invalid"],
        ),
        normalized_finding(
            requirement_id,
            "independent-valid-scope",
            report,
            "conformance",
            "valid",
        ),
    ]


_execute_verifier_report_case_before_batch25 = execute_verifier_report_case


def execute_verifier_report_case(row, case, materialized):
    planned = row["planned_test_id"]
    expected_requirement = _BATCH25_VERIFIER_REQUIREMENTS.get(planned)
    if expected_requirement is None:
        return _execute_verifier_report_case_before_batch25(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{planned}")

    report = primary_report(case, materialized)
    require_conflict_completeness_report(report)

    if planned == "verifier-history-completeness-default-001":
        findings = execute_history_completeness_default(
            requirement_id, planned, report
        )
    elif planned == "verifier-conflict-independent-checks-001":
        findings = execute_conflict_independent_checks(requirement_id, report)
    elif planned == "verifier-unsupported-no-downgrade-001":
        findings = execute_unsupported_no_downgrade(
            requirement_id, planned, report
        )
    elif planned == "verifier-profile-no-code-execution-001":
        findings = execute_profile_identifier_no_code(
            requirement_id, planned, report
        )
    elif planned == "verifier-consistent-bounded-001":
        findings = execute_consistent_bounded(
            requirement_id, planned, report
        )
    elif planned == "verifier-conflict-and-invalid-001":
        findings = execute_conflict_and_invalid(requirement_id, report)
    elif planned == "verifier-conflict-not-universal-invalidity-001":
        findings = execute_conflict_not_universal_invalidity(
            requirement_id, report
        )
    else:
        raise NotImplementedError(planned)

    return {
        "findings": findings,
        "process_outcome": report["process_outcome"],
        "completeness": dict(report.get("completeness") or {}),
    }
