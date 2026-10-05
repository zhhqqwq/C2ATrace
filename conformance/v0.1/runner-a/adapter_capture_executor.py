#!/usr/bin/env python3

ADAPTER_CAPTURE_PLANNED_TESTS = {
    "tool-adapter-visibility-boundary-001",
    "tool-adapter-effective-invocation-capability-001",
    "tool-adapter-execution-capability-001",
    "tool-adapter-result-capability-001",
    "tool-capture-diagnostic-reuse-001",
    "tool-proposal-capability-optional-001",
    "tool-execution-no-implicit-allow-001",
    "tool-execution-start-boundary-001",
    "tool-result-boundary-001",
    "tool-success-no-effect-proof-001",
    "tool-argument-model-supplied-positive-001",
    "tool-argument-app-supplied-positive-001",
    "tool-argument-mixed-positive-001",
    "tool-argument-control-not-content-001",
    "tool-argument-dropped-not-effective-001",
    "tool-argument-enrichment-origin-001",
    "tool-transport-metadata-no-proposal-ancestry-001",
}


def records(receipt):
    return (receipt.get("arp") or {}).get("records", [])


def receipt_id(receipt):
    return (receipt.get("arp") or {}).get("receipt_id")


def ref_id(value):
    return value.get("id") if isinstance(value, dict) else None


def record_index(receipt):
    index = {}
    for record in records(receipt):
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise ValueError("receipt contains record without string id")
        if record["id"] in index:
            raise ValueError("receipt contains duplicate record id")
        index[record["id"]] = record
    return index


def resolve_local(index, reference, expected_kind=None):
    if not isinstance(reference, dict) or reference.get("ref_type") != "local":
        raise ValueError("reference is not local")
    target = index.get(ref_id(reference))
    if not isinstance(target, dict):
        raise ValueError("local reference did not resolve")
    declared = reference.get("expected_kind")
    if expected_kind is not None:
        if target.get("kind") != expected_kind:
            raise ValueError(f"reference did not resolve to {expected_kind}")
        if declared not in {None, expected_kind}:
            raise ValueError(f"reference declares wrong expected_kind for {expected_kind}")
    elif declared is not None and target.get("kind") != declared:
        raise ValueError("reference expected_kind does not match resolved object")
    return target


def resolve_json_pointer(value, pointer):
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("JSON Pointer is invalid")
    current = value
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise KeyError(token)
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit():
                raise ValueError("JSON Pointer array index is invalid")
            index = int(token)
            if index < 0 or index >= len(current):
                raise KeyError(token)
            current = current[index]
        else:
            raise KeyError(token)
    return current


def structured_path(region, pointer):
    if not isinstance(region, dict) or region.get("region_kind") != "structured":
        return False
    path = region.get("path")
    return (
        isinstance(path, dict)
        and path.get("scheme") == "json_pointer"
        and path.get("value") == pointer
    )


def argument_representation_basis(kind, basis):
    allowed = {
        "ToolInvocation": {"json-data-model", "tool_arguments_json"},
        "ToolProposal": {"json-data-model", "tool_proposal_arguments_json"},
        "ContextFragment": {"json-data-model"},
    }
    return basis in allowed.get(kind, {"json-data-model"})


def structured_json_pointer(region):
    if not isinstance(region, dict) or region.get("region_kind") != "structured":
        return None
    path = region.get("path")
    if not (
        isinstance(path, dict)
        and path.get("scheme") == "json_pointer"
        and isinstance(path.get("value"), str)
    ):
        return None
    return path["value"]


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
            f"adapter argument-provenance batch requires one primary receipt, found {len(receipts)}"
        )
    return receipts[0]


def finding(
    requirement_id,
    check_id,
    receipt,
    object_id,
    selector=None,
    domain="conformance",
    status="valid",
    prohibited=None,
):
    subject_scope = {
        "receipt_id": receipt_id(receipt),
        "object_id": object_id,
    }
    if selector:
        subject_scope.update(selector)
    out = {
        "requirement_id": requirement_id,
        "check_id": check_id,
        "subject_scope": subject_scope,
        "domain": domain,
        "status": status,
    }
    if prohibited:
        out["prohibited_inferences"] = list(prohibited)
    return out


def argument_context(receipt):
    index = record_index(receipt)
    invocations = [
        record
        for record in records(receipt)
        if isinstance(record, dict)
        and record.get("kind") == "ToolInvocation"
        and isinstance(record.get("argument_provenance"), list)
        and record.get("argument_provenance")
    ]
    if len(invocations) != 1:
        raise ValueError(
            f"argument-provenance scenario requires one ToolInvocation, found {len(invocations)}"
        )
    invocation = invocations[0]
    arguments = invocation.get("arguments") or {}
    if arguments.get("representation_kind") != "json":
        raise ValueError("ToolInvocation arguments are not JSON")
    argument_value = arguments.get("value")
    if not isinstance(argument_value, (dict, list)):
        raise ValueError("ToolInvocation JSON arguments are not structured")

    transform = resolve_local(index, invocation.get("preparation_transform"), "Transform")
    if transform.get("operation") != "tool_preparation":
        raise ValueError("ToolInvocation preparation_transform is not tool_preparation")
    generated = [
        item
        for item in transform.get("generated", [])
        if ref_id(item) == invocation.get("id")
    ]
    if len(generated) != 1:
        raise ValueError("preparation Transform must generate the selected ToolInvocation")
    resolve_local(index, generated[0], "ToolInvocation")

    proposals = [
        record
        for record in records(receipt)
        if isinstance(record, dict)
        and record.get("kind") == "ToolProposal"
        and record.get("run_id") == invocation.get("run_id")
    ]
    if len(proposals) != 1:
        raise ValueError(
            f"argument-provenance scenario requires one same-run ToolProposal, found {len(proposals)}"
        )
    proposal = proposals[0]
    proposal_args = proposal.get("arguments") or {}
    if proposal_args.get("representation_kind") != "json":
        raise ValueError("ToolProposal arguments are not JSON")

    run_ids = {invocation.get("run_id"), transform.get("run_id"), proposal.get("run_id")}
    if None in run_ids or len(run_ids) != 1:
        raise ValueError("proposal/preparation/invocation changed run occurrence")

    provenance = {}
    for item in invocation.get("argument_provenance", []):
        if not isinstance(item, dict):
            raise ValueError("argument_provenance entry is not an object")
        path = item.get("path")
        if not (
            isinstance(path, dict)
            and path.get("scheme") == "json_pointer"
            and isinstance(path.get("value"), str)
        ):
            raise ValueError("argument_provenance path is not a JSON Pointer")
        pointer = path["value"]
        if pointer in provenance:
            raise ValueError("duplicate argument_provenance path")
        resolve_json_pointer(argument_value, pointer)
        provenance[pointer] = item

    input_records = {}
    input_roles = {}
    for item in transform.get("inputs", []):
        if not isinstance(item, dict):
            continue
        artifact = item.get("artifact")
        target = resolve_local(index, artifact)
        input_records[target["id"]] = target
        input_roles[target["id"]] = item.get("usage_role")

    return {
        "receipt": receipt,
        "index": index,
        "invocation": invocation,
        "invocation_value": argument_value,
        "proposal": proposal,
        "proposal_value": proposal_args.get("value"),
        "transform": transform,
        "provenance": provenance,
        "input_records": input_records,
        "input_roles": input_roles,
    }


def path_derivation(context, pointer, classification):
    item = context["provenance"].get(pointer)
    if not isinstance(item, dict):
        raise ValueError(f"missing argument_provenance for {pointer}")
    if item.get("classification") != classification:
        raise ValueError(
            f"{pointer} classification is {item.get('classification')!r}, expected {classification!r}"
        )
    refs = item.get("derivations", [])
    if not isinstance(refs, list) or len(refs) != 1:
        raise ValueError(f"{pointer} requires exactly one Derivation")
    derivation = resolve_local(context["index"], refs[0], "Derivation")

    target = derivation.get("target") or {}
    target_invocation = resolve_local(
        context["index"], target.get("artifact"), "ToolInvocation"
    )
    if target_invocation.get("id") != context["invocation"].get("id"):
        raise ValueError("Derivation target is not the selected ToolInvocation")
    if not argument_representation_basis(
        "ToolInvocation", target.get("representation_basis")
    ):
        raise ValueError("Derivation target basis is not a ToolInvocation argument basis")
    if not structured_path(target.get("region"), pointer):
        raise ValueError("Derivation target region does not match argument path")

    derivation_transform = resolve_local(
        context["index"], derivation.get("transform"), "Transform"
    )
    if derivation_transform.get("id") != context["transform"].get("id"):
        raise ValueError("Derivation does not use ToolInvocation preparation_transform")

    contributors = []
    for contributor in derivation.get("contributors", []):
        if not isinstance(contributor, dict):
            raise ValueError("Derivation contributor is not an object")
        scope = contributor.get("scope") or {}
        artifact = resolve_local(context["index"], scope.get("artifact"))
        if not argument_representation_basis(
            artifact.get("kind"), scope.get("representation_basis")
        ):
            raise ValueError("contributor basis is not valid for argument provenance")
        if structured_json_pointer(scope.get("region")) is None:
            raise ValueError("contributor region is not a structured JSON Pointer")
        if not structured_path(contributor.get("output_region"), pointer):
            raise ValueError("contributor output_region does not match argument path")
        if artifact.get("id") not in context["input_records"]:
            raise ValueError("Derivation contributor is not a preparation input")
        if context["input_roles"].get(artifact["id"]) not in {"data", "mixed"}:
            raise ValueError("Derivation contributor preparation input is not content-contributing")
        contributors.append(artifact)

    if not contributors:
        raise ValueError(f"{pointer} Derivation has no positive contributors")

    run_ids = {
        context["invocation"].get("run_id"),
        context["transform"].get("run_id"),
        derivation.get("run_id"),
        *[artifact.get("run_id") for artifact in contributors],
    }
    if None in run_ids or len(run_ids) != 1:
        raise ValueError("argument Derivation changed run occurrence")

    return item, derivation, contributors


def require_model_supplied(context, pointer):
    _item, derivation, contributors = path_derivation(
        context, pointer, "model_supplied"
    )
    if len(contributors) != 1 or contributors[0].get("kind") != "ToolProposal":
        raise ValueError("model_supplied path lacks exclusive ToolProposal ancestry")
    if contributors[0].get("id") != context["proposal"].get("id"):
        raise ValueError("model_supplied contributor is not the selected ToolProposal")
    if derivation.get("precision") != "exact":
        raise ValueError("model_supplied Derivation is not exact")
    proposal_value = resolve_json_pointer(context["proposal_value"], pointer)
    invocation_value = resolve_json_pointer(context["invocation_value"], pointer)
    if proposal_value != invocation_value:
        raise ValueError("model_supplied effective value differs from proposal value")
    return derivation


def require_application_supplied(context, pointer):
    _item, derivation, contributors = path_derivation(
        context, pointer, "application_supplied"
    )
    if len(contributors) != 1:
        raise ValueError("application_supplied path requires one positive contributor")
    contributor = contributors[0]
    if contributor.get("kind") == "ToolProposal":
        raise ValueError("application_supplied path uses ToolProposal ancestry")
    if contributor.get("kind") != "ContextFragment":
        raise ValueError("application_supplied contributor is not application ContextFragment")
    if derivation.get("precision") != "exact":
        raise ValueError("application_supplied Derivation is not exact")
    representation = contributor.get("representation") or {}
    if representation.get("representation_kind") != "json":
        raise ValueError("application contributor representation is not JSON")
    source_value = resolve_json_pointer(representation.get("value"), pointer)
    invocation_value = resolve_json_pointer(context["invocation_value"], pointer)
    if source_value != invocation_value:
        raise ValueError("application-supplied effective value differs from contributor value")
    return derivation, contributor


def require_mixed(context, pointer):
    _item, derivation, contributors = path_derivation(context, pointer, "mixed")
    kinds = {artifact.get("kind") for artifact in contributors}
    if "ToolProposal" not in kinds:
        raise ValueError("mixed path lacks ToolProposal contributor")
    if not any(kind != "ToolProposal" for kind in kinds):
        raise ValueError("mixed path lacks non-ToolProposal contributor")
    if not any(artifact.get("kind") == "ContextFragment" for artifact in contributors):
        raise ValueError("mixed path lacks application ContextFragment contributor")
    if derivation.get("precision") not in {"exact", "partial"}:
        raise ValueError("mixed Derivation has unsupported precision")
    return derivation


def require_control_not_content(context):
    controls = [
        artifact
        for artifact_id, artifact in context["input_records"].items()
        if context["input_roles"].get(artifact_id) == "control"
    ]
    if len(controls) != 1:
        raise ValueError(
            f"control-only scenario requires one control input, found {len(controls)}"
        )
    control = controls[0]
    for record in records(context["receipt"]):
        if not isinstance(record, dict) or record.get("kind") != "Derivation":
            continue
        target = record.get("target") or {}
        if ref_id(target.get("artifact")) != context["invocation"].get("id"):
            continue
        for contributor in record.get("contributors", []):
            scope = contributor.get("scope") if isinstance(contributor, dict) else None
            if ref_id((scope or {}).get("artifact")) == control.get("id"):
                raise ValueError("control-only preparation input has positive content Derivation")
    representation = control.get("representation") or {}
    if representation.get("representation_kind") == "json":
        for key in (representation.get("value") or {}):
            if isinstance(context["invocation_value"], dict) and key in context["invocation_value"]:
                raise ValueError("control-only key appears in effective ToolInvocation arguments")
    return control


def require_dropped_proposal_argument(context, pointer):
    proposal_value = resolve_json_pointer(context["proposal_value"], pointer)
    if proposal_value is None:
        raise ValueError("dropped proposal argument has no proposal-side value")
    try:
        resolve_json_pointer(context["invocation_value"], pointer)
    except KeyError:
        pass
    else:
        raise ValueError("dropped proposal argument remains in effective ToolInvocation")
    if pointer in context["provenance"]:
        raise ValueError("dropped proposal argument has effective argument_provenance")
    for record in records(context["receipt"]):
        if not isinstance(record, dict) or record.get("kind") != "Derivation":
            continue
        target = record.get("target") or {}
        if ref_id(target.get("artifact")) != context["invocation"].get("id"):
            continue
        if structured_path(target.get("region"), pointer):
            raise ValueError("dropped proposal argument has positive effective Derivation")
    return proposal_value


def require_transport_metadata_separation(context):
    metadata = context["invocation"].get("metadata", [])
    runtime = [
        item
        for item in metadata
        if isinstance(item, dict) and item.get("origin") == "runtime_transport"
    ]
    if not runtime:
        raise ValueError("ToolInvocation has no runtime_transport metadata")
    proposal_keys = set(context["proposal_value"]) if isinstance(context["proposal_value"], dict) else set()
    for item in runtime:
        name = item.get("name")
        if isinstance(name, str) and name in proposal_keys:
            raise ValueError("runtime transport metadata collides with ToolProposal argument key")
    for provenance in context["provenance"].values():
        if provenance.get("classification") == "model_supplied":
            for ref in provenance.get("derivations", []):
                derivation = resolve_local(context["index"], ref, "Derivation")
                target = derivation.get("target") or {}
                if target.get("representation_basis") != "json-data-model":
                    raise ValueError("model ancestry Derivation targets non-argument representation")
    return runtime


def by_kind(receipt, kind):
    return [
        record
        for record in records(receipt)
        if isinstance(record, dict) and record.get("kind") == kind
    ]


def tool_adapter_baseline_context(receipt):
    index = record_index(receipt)

    capabilities = by_kind(receipt, "ToolAdapterCapability")
    invocations = by_kind(receipt, "ToolInvocation")
    executions = by_kind(receipt, "ToolExecution")
    results = by_kind(receipt, "ToolResult")
    diagnostics = by_kind(receipt, "CaptureDiagnostic")

    if len(capabilities) != 1:
        raise ValueError(
            f"tool-adapter baseline requires one ToolAdapterCapability, found {len(capabilities)}"
        )
    if len(invocations) != 1:
        raise ValueError(
            f"tool-adapter baseline requires one ToolInvocation, found {len(invocations)}"
        )
    if len(executions) != 1:
        raise ValueError(
            f"tool-adapter baseline requires one ToolExecution, found {len(executions)}"
        )
    if len(results) != 1:
        raise ValueError(
            f"tool-adapter baseline requires one ToolResult, found {len(results)}"
        )
    if len(diagnostics) != 3:
        raise ValueError(
            f"tool-adapter baseline requires three CaptureDiagnostics, found {len(diagnostics)}"
        )

    capability = capabilities[0]
    invocation = invocations[0]
    execution = executions[0]
    result = results[0]

    resolved_invocation = resolve_local(index, execution.get("invocation"), "ToolInvocation")
    if resolved_invocation.get("id") != invocation.get("id"):
        raise ValueError("ToolExecution does not reference the baseline ToolInvocation")

    resolved_execution = resolve_local(index, result.get("execution"), "ToolExecution")
    if resolved_execution.get("id") != execution.get("id"):
        raise ValueError("ToolResult does not reference the baseline ToolExecution")

    run_ids = {
        capability.get("run_id"),
        invocation.get("run_id"),
        execution.get("run_id"),
        result.get("run_id"),
        *[diagnostic.get("run_id") for diagnostic in diagnostics],
    }
    if None in run_ids or len(run_ids) != 1:
        raise ValueError("tool-adapter baseline records changed run occurrence")

    expected_slots = {
        "tool_invocation.effective": ("ToolInvocation", invocation.get("id")),
        "tool_execution.lifecycle": ("ToolExecution", execution.get("id")),
        "tool_result.application_visible": ("ToolResult", result.get("id")),
    }
    resolved_diagnostics = {}

    for diagnostic in diagnostics:
        slot = diagnostic.get("slot")
        if slot not in expected_slots:
            raise ValueError(f"unexpected CaptureDiagnostic slot: {slot!r}")
        if slot in resolved_diagnostics:
            raise ValueError(f"duplicate CaptureDiagnostic slot: {slot}")
        if diagnostic.get("status") != "observed":
            raise ValueError(f"CaptureDiagnostic {slot} is not observed")

        declaration = resolve_local(
            index, diagnostic.get("adapter_declaration"), "ToolAdapterCapability"
        )
        if declaration.get("id") != capability.get("id"):
            raise ValueError("CaptureDiagnostic references a different adapter declaration")

        subject = diagnostic.get("subject") or {}
        expected_kind, expected_id = expected_slots[slot]
        subject_record = resolve_local(index, subject.get("ref"), expected_kind)
        if subject_record.get("id") != expected_id:
            raise ValueError(f"CaptureDiagnostic {slot} references wrong subject")

        expected_basis = {
            "ToolInvocation": "tool_invocation",
            "ToolExecution": "tool_execution",
            "ToolResult": "tool_result",
        }[expected_kind]
        if subject.get("representation_basis") != expected_basis:
            raise ValueError(f"CaptureDiagnostic {slot} has wrong representation_basis")

        resolved_diagnostics[slot] = diagnostic

    if set(resolved_diagnostics) != set(expected_slots):
        raise ValueError("tool-adapter baseline diagnostic slots are incomplete")

    return {
        "receipt": receipt,
        "index": index,
        "capability": capability,
        "invocation": invocation,
        "execution": execution,
        "result": result,
        "diagnostics": resolved_diagnostics,
    }


def require_baseline_capability_boundaries(context):
    capability = context["capability"]
    if capability.get("invocation_boundary") != "effective pre-execution ToolInvocation":
        raise ValueError("adapter invocation_boundary does not match baseline contract")
    if (
        capability.get("execution_boundary")
        != "application-visible execution start through terminal runtime lifecycle"
    ):
        raise ValueError("adapter execution_boundary does not match baseline contract")
    if capability.get("result_boundary") != "application-visible ToolResult":
        raise ValueError("adapter result_boundary does not match baseline contract")
    return capability


def require_no_proposal_ancestry(context):
    capability = context["capability"]
    if capability.get("proposal_association") is not False:
        raise ValueError("baseline adapter unexpectedly declares proposal association")
    if by_kind(context["receipt"], "ToolProposal"):
        raise ValueError("baseline receipt invents ToolProposal occurrence")
    invocation = context["invocation"]
    if invocation.get("proposal") is not None:
        raise ValueError("baseline ToolInvocation invents proposal linkage")
    return invocation


def require_no_implicit_allow(context):
    if any(
        decision.get("decision") == "allow"
        for decision in by_kind(context["receipt"], "ToolDecision")
    ):
        raise ValueError("baseline receipt contains explicit allow decision")
    return context["execution"]


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    if check_id not in ADAPTER_CAPTURE_PLANNED_TESTS:
        raise NotImplementedError(check_id)

    batch19_requirements = {
        "tool-adapter-visibility-boundary-001": "TAD-001",
        "tool-adapter-effective-invocation-capability-001": "TAD-004",
        "tool-adapter-execution-capability-001": "TAD-005",
        "tool-adapter-result-capability-001": "TAD-006",
        "tool-capture-diagnostic-reuse-001": "TAD-010",
        "tool-proposal-capability-optional-001": "TAD-014",
        "tool-execution-no-implicit-allow-001": "TAD-020",
        "tool-execution-start-boundary-001": "TAD-039",
        "tool-result-boundary-001": "TAD-057",
        "tool-success-no-effect-proof-001": "TAD-075",
    }
    requirement_id = row["requirement_id"]
    if (
        check_id in batch19_requirements
        and requirement_id != batch19_requirements[check_id]
    ):
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    allowed_requirements = {
        "TAD-030",
        "TAD-031",
        "TAD-032",
        "TAD-034",
        "TAD-036",
        "TAD-037",
        "TAD-038",
    }
    if check_id not in batch19_requirements and requirement_id not in allowed_requirements:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)

    if check_id in batch19_requirements:
        context = tool_adapter_baseline_context(receipt)
        capability = require_baseline_capability_boundaries(context)
        invocation = context["invocation"]
        execution = context["execution"]
        result = context["result"]

        if check_id == "tool-adapter-visibility-boundary-001":
            actual_finding = finding(
                requirement_id,
                check_id,
                receipt,
                capability["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:tool_adapter_visible_evidence_proves_hidden_remote_state"],
            )
        elif check_id == "tool-adapter-effective-invocation-capability-001":
            context["diagnostics"]["tool_invocation.effective"]
            actual_finding = finding(
                requirement_id, check_id, receipt, invocation["id"]
            )
        elif check_id == "tool-adapter-execution-capability-001":
            context["diagnostics"]["tool_execution.lifecycle"]
            actual_finding = finding(
                requirement_id, check_id, receipt, execution["id"]
            )
        elif check_id == "tool-adapter-result-capability-001":
            context["diagnostics"]["tool_result.application_visible"]
            actual_finding = finding(
                requirement_id, check_id, receipt, result["id"]
            )
        elif check_id == "tool-capture-diagnostic-reuse-001":
            diagnostic = context["diagnostics"]["tool_result.application_visible"]
            actual_finding = finding(
                requirement_id, check_id, receipt, diagnostic["id"]
            )
        elif check_id == "tool-proposal-capability-optional-001":
            require_no_proposal_ancestry(context)
            actual_finding = finding(
                requirement_id, check_id, receipt, invocation["id"]
            )
        elif check_id == "tool-execution-no-implicit-allow-001":
            require_no_implicit_allow(context)
            actual_finding = finding(
                requirement_id,
                check_id,
                receipt,
                execution["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:tool_execution_implies_allow_decision"],
            )
        elif check_id == "tool-execution-start-boundary-001":
            context["diagnostics"]["tool_execution.lifecycle"]
            if execution.get("lifecycle_state") != "terminal":
                raise ValueError("baseline ToolExecution does not preserve terminal lifecycle")
            actual_finding = finding(
                requirement_id, check_id, receipt, execution["id"]
            )
        elif check_id == "tool-result-boundary-001":
            context["diagnostics"]["tool_result.application_visible"]
            actual_finding = finding(
                requirement_id, check_id, receipt, result["id"]
            )
        elif check_id == "tool-success-no-effect-proof-001":
            if result.get("reported_status") != "success":
                raise ValueError("baseline ToolResult is not reported success")
            if by_kind(receipt, "EffectObservation"):
                raise ValueError("baseline receipt contains separate EffectObservation evidence")
            actual_finding = finding(
                requirement_id,
                check_id,
                receipt,
                result["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:tool_result_success_proves_external_effect_truth"],
            )
        else:
            raise NotImplementedError(check_id)

    elif check_id == "tool-argument-model-supplied-positive-001":
        context = argument_context(receipt)
        invocation = context["invocation"]
        require_model_supplied(context, "/title")
        actual_finding = finding(
            requirement_id, check_id, receipt, invocation["id"], {"path": "/title"}
        )
    elif check_id == "tool-argument-app-supplied-positive-001":
        context = argument_context(receipt)
        invocation = context["invocation"]
        require_application_supplied(context, "/repo")
        actual_finding = finding(
            requirement_id, check_id, receipt, invocation["id"], {"path": "/repo"}
        )
    elif check_id == "tool-argument-mixed-positive-001":
        context = argument_context(receipt)
        invocation = context["invocation"]
        require_mixed(context, "/mixed_note")
        actual_finding = finding(
            requirement_id, check_id, receipt, invocation["id"], {"path": "/mixed_note"}
        )
    elif check_id == "tool-argument-control-not-content-001":
        context = argument_context(receipt)
        invocation = context["invocation"]
        control = require_control_not_content(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            control["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:control_input_is_argument_content_contributor"],
        )
    elif check_id == "tool-argument-dropped-not-effective-001":
        context = argument_context(receipt)
        invocation = context["invocation"]
        require_dropped_proposal_argument(context, "/priority")
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            invocation["id"],
            {"dropped_path": "/priority"},
            domain="claim",
            status="asserted",
            prohibited=["P1:dropped_proposal_argument_remains_effective_argument"],
        )
    elif check_id == "tool-argument-enrichment-origin-001":
        context = argument_context(receipt)
        invocation = context["invocation"]
        require_application_supplied(context, "/secret_ref")
        try:
            resolve_json_pointer(context["proposal_value"], "/secret_ref")
        except KeyError:
            pass
        else:
            raise ValueError("runtime enrichment already exists in ToolProposal arguments")
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            invocation["id"],
            {"path": "/secret_ref"},
            domain="claim",
            status="asserted",
            prohibited=["P1:application_enrichment_is_model_supplied_by_proximity"],
        )
    elif check_id == "tool-transport-metadata-no-proposal-ancestry-001":
        context = argument_context(receipt)
        invocation = context["invocation"]
        runtime = require_transport_metadata_separation(context)
        if len(runtime) != 1 or runtime[0].get("name") != "Authorization":
            raise ValueError("transport metadata scenario requires one Authorization entry")
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            invocation["id"],
            {"metadata_name": "Authorization"},
            domain="claim",
            status="asserted",
            prohibited=["P1:transport_metadata_inherits_tool_proposal_ancestry"],
        )
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": "completed",
        "completeness": {},
    }
