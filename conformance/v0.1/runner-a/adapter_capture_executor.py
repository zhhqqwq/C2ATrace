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


def adapter_declarations(receipt):
    return (receipt.get("arp") or {}).get("adapter_declarations", [])


def receipt_id(receipt):
    return (receipt.get("arp") or {}).get("receipt_id")


def ref_id(value):
    return value.get("id") if isinstance(value, dict) else None


def record_index(receipt):
    index = {}
    for record in [*records(receipt), *adapter_declarations(receipt)]:
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

    capabilities = [
        declaration
        for declaration in adapter_declarations(receipt)
        if isinstance(declaration, dict)
        and declaration.get("kind") == "ToolAdapterCapability"
    ]
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

# Runner A Wave 03 Batch 21: provider-adapter request/attempt capture core.
_BATCH21_PROVIDER_REQUIREMENTS = {
    "provider-adapter-visibility-boundary-001": "PAD-001",
    "provider-capture-observed-bounded-001": "PAD-011",
    "provider-capture-diagnostic-asserted-001": "PAD-013",
    "provider-attempt-boundary-001": "PAD-018",
    "provider-attempt-disposition-boundary-001": "PAD-021",
    "provider-no-synthetic-level-001": "PAD-025",
    "provider-effective-snapshot-positive-001": "PAD-031",
    "provider-missing-level-valid-001": "PAD-032",
    "provider-request-reuse-not-equality-001": "PAD-035",
}
ADAPTER_CAPTURE_PLANNED_TESTS.update(_BATCH21_PROVIDER_REQUIREMENTS)


def provider_finding(
    requirement_id,
    check_id,
    receipt,
    object_id,
    *,
    domain="conformance",
    status="valid",
    reason_code=None,
    prohibited=None,
):
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


def provider_adapter_capability(materialized):
    capabilities = []
    for value in materialized.values():
        if not isinstance(value, dict):
            continue
        if value.get("kind") == "ProviderAdapterCapability":
            capabilities.append(value)
        elif value.get("kind") == "ReceiptPresentation":
            capabilities.extend(
                declaration
                for declaration in adapter_declarations(value)
                if isinstance(declaration, dict)
                and declaration.get("kind") == "ProviderAdapterCapability"
            )
    if len(capabilities) != 1:
        raise ValueError(
            f"provider-adapter case requires one ProviderAdapterCapability, found {len(capabilities)}"
        )
    capability = capabilities[0]
    levels = capability.get("request_capture_levels")
    if not isinstance(levels, list) or not levels:
        raise ValueError("ProviderAdapterCapability has no request capture levels")
    core_levels = {"sdk_arguments", "provider_payload", "prepared_http_body"}
    if any(level not in core_levels for level in levels):
        raise ValueError("ProviderAdapterCapability declares non-core request capture level")
    return capability


def require_application_visible_provider_boundaries(capability):
    if capability.get("invocation_boundary") != "observed logical application model call":
        raise ValueError("provider invocation boundary is not the declared application-visible baseline")
    if capability.get("attempt_boundary") != "application-visible provider attempt start":
        raise ValueError("provider attempt boundary is not the declared application-visible baseline")
    return capability


def provider_request_context(receipt):
    index = record_index(receipt)
    attempts = by_kind(receipt, "ProviderAttempt")
    snapshots = by_kind(receipt, "RequestSnapshot")
    bindings = by_kind(receipt, "RequestBinding")
    invocations = by_kind(receipt, "ModelInvocation")
    if not attempts:
        raise ValueError("provider request scenario has no ProviderAttempt")
    if not snapshots:
        raise ValueError("provider request scenario has no RequestSnapshot")
    if not invocations:
        raise ValueError("provider request scenario has no ModelInvocation")

    for attempt in attempts:
        invocation = resolve_local(index, attempt.get("invocation"), "ModelInvocation")
        if attempt.get("run_id") != invocation.get("run_id"):
            raise ValueError("ProviderAttempt and ModelInvocation changed run occurrence")
        seen_levels = set()
        for effective in attempt.get("effective_requests", []):
            if not isinstance(effective, dict):
                raise ValueError("ProviderAttempt effective request is not an object")
            level = effective.get("capture_level")
            if level in seen_levels:
                raise ValueError("ProviderAttempt has duplicate effective request capture level")
            seen_levels.add(level)
            snapshot = resolve_local(index, effective.get("snapshot"), "RequestSnapshot")
            if snapshot.get("capture_level") != level:
                raise ValueError("effective request capture level disagrees with RequestSnapshot")
            if snapshot.get("attempt_owner") is not None:
                owner = resolve_local(index, snapshot.get("attempt_owner"), "ProviderAttempt")
                if owner.get("id") != attempt.get("id"):
                    raise ValueError("attempt-scoped RequestSnapshot is used by a different ProviderAttempt")
            elif snapshot.get("invocation_owner") is not None:
                owner = resolve_local(index, snapshot.get("invocation_owner"), "ModelInvocation")
                if owner.get("id") != invocation.get("id"):
                    raise ValueError("invocation-scoped RequestSnapshot is used by another invocation")
            else:
                raise ValueError("RequestSnapshot has no occurrence owner")

    for binding in bindings:
        resolve_local(index, binding.get("snapshot"), "RequestSnapshot")
        resolve_local(index, binding.get("component"))

    return {
        "receipt": receipt,
        "index": index,
        "attempts": attempts,
        "snapshots": snapshots,
        "bindings": bindings,
        "invocations": invocations,
    }


def single_provider_attempt(context):
    if len(context["attempts"]) != 1:
        raise ValueError(
            f"provider adapter scenario requires one ProviderAttempt, found {len(context['attempts'])}"
        )
    return context["attempts"][0]


def provider_capture_diagnostic(receipt):
    index = record_index(receipt)
    diagnostics = [
        diagnostic
        for diagnostic in by_kind(receipt, "CaptureDiagnostic")
        if diagnostic.get("slot") == "provider_attempt.request"
    ]
    if len(diagnostics) != 1:
        raise ValueError(
            f"provider capture scenario requires one provider_attempt.request diagnostic, found {len(diagnostics)}"
        )
    diagnostic = diagnostics[0]
    if diagnostic.get("status") != "observed":
        raise ValueError("provider request CaptureDiagnostic is not observed")
    subject = diagnostic.get("subject") or {}
    attempt = resolve_local(index, subject.get("ref"), "ProviderAttempt")
    if diagnostic.get("run_id") != attempt.get("run_id"):
        raise ValueError("CaptureDiagnostic subject changed run occurrence")
    return diagnostic, attempt


def require_attempt_boundary(capability, context):
    require_application_visible_provider_boundaries(capability)
    attempt = single_provider_attempt(context)
    if attempt.get("lifecycle_state") not in {"in_progress", "terminal"}:
        raise ValueError("ProviderAttempt does not represent an observed attempt occurrence")
    resolve_local(context["index"], attempt.get("invocation"), "ModelInvocation")
    return attempt


def require_lifecycle_not_provider_status(context):
    attempt = single_provider_attempt(context)
    provider_status = [
        item
        for item in attempt.get("metadata", [])
        if isinstance(item, dict)
        and item.get("name") == "provider_status"
        and item.get("origin") == "provider_reported"
    ]
    if len(provider_status) != 1 or provider_status[0].get("value") != "success":
        raise ValueError("provider-reported success metadata premise is missing")
    if attempt.get("lifecycle_state") != "in_progress":
        raise ValueError("provider-reported metadata changed observed lifecycle state")
    if attempt.get("terminal_disposition") is not None:
        raise ValueError("provider-reported metadata synthesized terminal disposition")
    return attempt


def require_no_synthetic_intermediate_levels(context):
    attempt = single_provider_attempt(context)
    snapshot_levels = [snapshot.get("capture_level") for snapshot in context["snapshots"]]
    effective_levels = [
        effective.get("capture_level")
        for effective in attempt.get("effective_requests", [])
    ]
    if snapshot_levels != ["provider_payload"]:
        raise ValueError("request-level baseline contains synthesized or unexpected RequestSnapshot levels")
    if effective_levels != ["provider_payload"]:
        raise ValueError("request-level baseline contains synthesized or unexpected effective levels")
    snapshot = resolve_local(
        context["index"], attempt["effective_requests"][0].get("snapshot"), "RequestSnapshot"
    )
    return attempt, snapshot


def require_effective_snapshot_basis_missing(context):
    attempt = single_provider_attempt(context)
    effective = attempt.get("effective_requests", [])
    if len(effective) != 1 or effective[0].get("capture_level") != "provider_payload":
        raise ValueError("effective-snapshot scenario lacks one provider_payload designation")
    selected = resolve_local(context["index"], effective[0].get("snapshot"), "RequestSnapshot")
    candidates = [
        snapshot
        for snapshot in context["snapshots"]
        if snapshot.get("capture_level") == "provider_payload"
        and ref_id(snapshot.get("attempt_owner")) == attempt.get("id")
    ]
    if len(candidates) < 2:
        raise ValueError("effective-snapshot scenario has fewer than two same-level candidates")
    if selected.get("id") not in {snapshot.get("id") for snapshot in candidates}:
        raise ValueError("effective RequestSnapshot is not one of the same-level candidates")
    timestamps = [snapshot.get("recorded_at") for snapshot in candidates]
    if any(not isinstance(value, str) or not value for value in timestamps):
        raise ValueError("effective-snapshot timestamp premise is missing")
    if len(set(timestamps)) != len(timestamps):
        raise ValueError("effective-snapshot candidates do not have distinct timestamps")
    for diagnostic in by_kind(context["receipt"], "CaptureDiagnostic"):
        subject = diagnostic.get("subject") or {}
        if (
            ref_id(subject.get("ref")) == selected.get("id")
            and diagnostic.get("status") == "observed"
            and diagnostic.get("basis")
        ):
            raise ValueError("effective-snapshot scenario unexpectedly contains positive selection basis")
    return attempt


def require_actual_invocation_snapshot_reuse(context):
    usage = {}
    for attempt in context["attempts"]:
        invocation_id = ref_id(attempt.get("invocation"))
        for effective in attempt.get("effective_requests", []):
            snapshot = resolve_local(context["index"], effective.get("snapshot"), "RequestSnapshot")
            usage.setdefault(snapshot.get("id"), []).append((attempt, invocation_id, snapshot))

    candidates = []
    for uses in usage.values():
        if len(uses) < 2:
            continue
        snapshot = uses[0][2]
        owner_id = ref_id(snapshot.get("invocation_owner"))
        if not owner_id:
            continue
        owner = resolve_local(context["index"], snapshot.get("invocation_owner"), "ModelInvocation")
        if any(invocation_id != owner.get("id") for _attempt, invocation_id, _snapshot in uses):
            raise ValueError("reused RequestSnapshot crosses invocation ownership")
        if snapshot.get("attempt_owner") is not None:
            raise ValueError("reused invocation-scoped RequestSnapshot also has attempt_owner")
        candidates.append(snapshot)
    if len(candidates) != 1:
        raise ValueError(
            f"request-reuse scenario requires one actually reused invocation snapshot, found {len(candidates)}"
        )
    return candidates[0]


_execute_adapter_capture_case_before_batch21 = execute_adapter_capture_case


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    expected_requirement = _BATCH21_PROVIDER_REQUIREMENTS.get(check_id)
    if expected_requirement is None:
        return _execute_adapter_capture_case_before_batch21(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)
    process_outcome = "completed"

    if check_id == "provider-adapter-visibility-boundary-001":
        capability = provider_adapter_capability(materialized)
        require_application_visible_provider_boundaries(capability)
        actual_finding = provider_finding(
            requirement_id,
            check_id,
            receipt,
            capability["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:provider_adapter_has_provider_internal_visibility"],
        )
    elif check_id in {
        "provider-capture-observed-bounded-001",
        "provider-capture-diagnostic-asserted-001",
    }:
        diagnostic, _attempt = provider_capture_diagnostic(receipt)
        if check_id == "provider-capture-observed-bounded-001":
            actual_finding = provider_finding(
                requirement_id,
                check_id,
                receipt,
                diagnostic["id"],
                domain="completeness",
                status="unverified",
                prohibited=["P1:observed_slot_means_global_capture_complete"],
            )
        else:
            actual_finding = provider_finding(
                requirement_id,
                check_id,
                receipt,
                diagnostic["id"],
                domain="claim",
                status="asserted",
                prohibited=["P1:capture_diagnostic_is_independent_completeness_verification"],
            )
    elif check_id == "provider-attempt-boundary-001":
        capability = provider_adapter_capability(materialized)
        context = provider_request_context(receipt)
        attempt = require_attempt_boundary(capability, context)
        actual_finding = provider_finding(requirement_id, check_id, receipt, attempt["id"])
    elif check_id == "provider-attempt-disposition-boundary-001":
        context = provider_request_context(receipt)
        attempt = require_lifecycle_not_provider_status(context)
        actual_finding = provider_finding(
            requirement_id,
            check_id,
            receipt,
            attempt["id"],
            prohibited=["P1:provider_reported_status_determines_attempt_disposition"],
        )
    elif check_id == "provider-no-synthetic-level-001":
        context = provider_request_context(receipt)
        attempt, _snapshot = require_no_synthetic_intermediate_levels(context)
        actual_finding = provider_finding(
            requirement_id,
            check_id,
            receipt,
            attempt["id"],
            prohibited=["P1:missing_request_levels_are_synthesized"],
        )
    elif check_id == "provider-effective-snapshot-positive-001":
        context = provider_request_context(receipt)
        attempt = require_effective_snapshot_basis_missing(context)
        actual_finding = provider_finding(
            requirement_id,
            check_id,
            receipt,
            attempt["id"],
            domain="claim",
            status="unverified",
            reason_code="effective_snapshot_selection_basis_missing",
        )
        process_outcome = "incomplete_evaluation"
    elif check_id == "provider-missing-level-valid-001":
        context = provider_request_context(receipt)
        attempt, _snapshot = require_no_synthetic_intermediate_levels(context)
        actual_finding = provider_finding(requirement_id, check_id, receipt, attempt["id"])
    elif check_id == "provider-request-reuse-not-equality-001":
        context = provider_request_context(receipt)
        snapshot = require_actual_invocation_snapshot_reuse(context)
        actual_finding = provider_finding(requirement_id, check_id, receipt, snapshot["id"])
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": process_outcome,
        "completeness": {},
    }

# Runner A Wave 03 Batch 22: tool orchestration relation core.
_BATCH22_ORCHESTRATION_REQUIREMENTS = {
    "tool-retry-new-execution-001": "TAD-047",
    "tool-retry-changed-invocation-001": "TAD-048",
    "tool-retry-relation-positive-001": "TAD-049",
    "tool-replay-relation-positive-001": "TAD-051",
    "tool-duplicate-relation-bounded-001": "TAD-052",
    "tool-idempotency-no-exactly-once-001": "TAD-055",
    "tool-idempotency-reported-dedup-001": "TAD-056",
}
ADAPTER_CAPTURE_PLANNED_TESTS.update(_BATCH22_ORCHESTRATION_REQUIREMENTS)


def orchestration_context(receipt):
    index = record_index(receipt)
    invocations = by_kind(receipt, "ToolInvocation")
    executions = by_kind(receipt, "ToolExecution")
    results = by_kind(receipt, "ToolResult")
    if len(invocations) < 2:
        raise ValueError("tool orchestration scenario requires at least two ToolInvocations")
    if len(executions) < 4:
        raise ValueError("tool orchestration scenario requires retry/replay/duplicate ToolExecutions")
    run_ids = {
        record.get("run_id")
        for record in [*invocations, *executions, *results]
        if isinstance(record, dict)
    }
    if len(run_ids) != 1 or None in run_ids:
        raise ValueError("tool orchestration objects are not owned by one explicit run")
    for execution in executions:
        invocation = resolve_local(index, execution.get("invocation"), "ToolInvocation")
        if invocation.get("run_id") != execution.get("run_id"):
            raise ValueError("ToolExecution invocation crosses run ownership")
        for relation in ("retry_of", "replay_of", "duplicate_of"):
            if execution.get(relation) is None:
                continue
            prior = resolve_local(index, execution.get(relation), "ToolExecution")
            if prior.get("run_id") != execution.get("run_id"):
                raise ValueError(f"{relation} crosses run ownership")
            if prior.get("id") == execution.get("id"):
                raise ValueError(f"{relation} self-reference is invalid")
    for result in results:
        execution = resolve_local(index, result.get("execution"), "ToolExecution")
        if execution.get("run_id") != result.get("run_id"):
            raise ValueError("ToolResult execution crosses run ownership")
    return {
        "receipt": receipt,
        "index": index,
        "invocations": invocations,
        "executions": executions,
        "results": results,
    }


def relation_execution(context, relation):
    matches = [execution for execution in context["executions"] if execution.get(relation) is not None]
    if len(matches) != 1:
        raise ValueError(f"tool orchestration scenario requires one {relation} relation, found {len(matches)}")
    current = matches[0]
    prior = resolve_local(context["index"], current.get(relation), "ToolExecution")
    if prior.get("run_id") != current.get("run_id"):
        raise ValueError(f"{relation} relation changed run occurrence")
    return current, prior


def application_orchestration_metadata(execution, name, expected_value):
    matches = [
        item
        for item in execution.get("metadata", [])
        if isinstance(item, dict)
        and item.get("name") == name
        and item.get("value") == expected_value
        and item.get("origin") == "application_observed"
    ]
    if len(matches) != 1:
        raise ValueError(f"{name} lacks one application-observed orchestration basis")
    return matches[0]


def require_visible_retry_new_execution(context):
    current, prior = relation_execution(context, "retry_of")
    application_orchestration_metadata(current, "retry_orchestration", "application_retry")
    if current.get("id") == prior.get("id"):
        raise ValueError("visible retry reused prior ToolExecution identity")
    return current, prior


def require_changed_retry_invocation(context):
    current, prior = require_visible_retry_new_execution(context)
    current_invocation = resolve_local(context["index"], current.get("invocation"), "ToolInvocation")
    prior_invocation = resolve_local(context["index"], prior.get("invocation"), "ToolInvocation")
    if current_invocation.get("id") == prior_invocation.get("id"):
        raise ValueError("changed retry reused prior ToolInvocation identity")
    execution_relevant_fields = ("tool_name", "arguments", "idempotency_key", "metadata")
    if all(current_invocation.get(field) == prior_invocation.get(field) for field in execution_relevant_fields):
        raise ValueError("retry ToolInvocation representation did not change")
    return current_invocation, prior_invocation


def require_retry_orchestration(context):
    current, prior = relation_execution(context, "retry_of")
    application_orchestration_metadata(current, "retry_orchestration", "application_retry")
    return current, prior


def require_replay_orchestration(context):
    current, prior = relation_execution(context, "replay_of")
    application_orchestration_metadata(current, "replay_orchestration", "operator_replay")
    return current, prior


def require_duplicate_relation(context):
    current, prior = relation_execution(context, "duplicate_of")
    evidence = [
        item
        for item in current.get("metadata", [])
        if isinstance(item, dict)
        and item.get("name") == "duplicate_classification"
        and item.get("origin") == "application_observed"
    ]
    if len(evidence) != 1:
        raise ValueError("duplicate_of lacks bounded application-observed classification evidence")
    return current, prior


def require_reused_idempotency_key(context):
    keyed = [
        invocation
        for invocation in context["invocations"]
        if isinstance(invocation.get("idempotency_key"), str) and invocation.get("idempotency_key")
    ]
    groups = {}
    for invocation in keyed:
        groups.setdefault(invocation["idempotency_key"], []).append(invocation)
    reused = [items for items in groups.values() if len(items) >= 2]
    if len(reused) != 1:
        raise ValueError("tool orchestration scenario requires one reused idempotency key")
    invocations = reused[0]
    if len({item.get("id") for item in invocations}) != len(invocations):
        raise ValueError("idempotency-key reuse does not span distinct ToolInvocation identities")
    retry, prior = require_visible_retry_new_execution(context)
    retry_invocation = resolve_local(context["index"], retry.get("invocation"), "ToolInvocation")
    prior_invocation = resolve_local(context["index"], prior.get("invocation"), "ToolInvocation")
    if retry_invocation.get("idempotency_key") != prior_invocation.get("idempotency_key"):
        raise ValueError("visible retry does not reuse the idempotency key")
    return retry_invocation


def require_tool_reported_dedup(context):
    candidates = []
    for result in context["results"]:
        reported = [
            item
            for item in result.get("metadata", [])
            if isinstance(item, dict)
            and item.get("name") == "deduplicated"
            and item.get("value") is True
            and item.get("origin") == "tool_reported"
        ]
        if result.get("reported_status") == "deduplicated" and len(reported) == 1:
            candidates.append(result)
    if len(candidates) != 1:
        raise ValueError("tool orchestration scenario requires one tool-reported deduplication result")
    result = candidates[0]
    resolve_local(context["index"], result.get("execution"), "ToolExecution")
    return result


_execute_adapter_capture_case_before_batch22 = execute_adapter_capture_case


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    expected_requirement = _BATCH22_ORCHESTRATION_REQUIREMENTS.get(check_id)
    if expected_requirement is None:
        return _execute_adapter_capture_case_before_batch22(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)
    context = orchestration_context(receipt)

    if check_id == "tool-retry-new-execution-001":
        current, _prior = require_visible_retry_new_execution(context)
        actual_finding = finding(requirement_id, check_id, receipt, current["id"])
    elif check_id == "tool-retry-changed-invocation-001":
        current_invocation, _prior_invocation = require_changed_retry_invocation(context)
        actual_finding = finding(requirement_id, check_id, receipt, current_invocation["id"])
    elif check_id == "tool-retry-relation-positive-001":
        current, _prior = require_retry_orchestration(context)
        actual_finding = finding(requirement_id, check_id, receipt, current["id"])
    elif check_id == "tool-replay-relation-positive-001":
        current, _prior = require_replay_orchestration(context)
        actual_finding = finding(requirement_id, check_id, receipt, current["id"])
    elif check_id == "tool-duplicate-relation-bounded-001":
        current, _prior = require_duplicate_relation(context)
        actual_finding = finding(
            requirement_id, check_id, receipt, current["id"],
            domain="claim", status="asserted",
            prohibited=["P1:duplicate_relation_proves_duplicate_effect_state"],
        )
    elif check_id == "tool-idempotency-no-exactly-once-001":
        invocation = require_reused_idempotency_key(context)
        actual_finding = finding(
            requirement_id, check_id, receipt, invocation["id"],
            domain="claim", status="asserted",
            prohibited=["P1:idempotency_key_proves_exactly_once"],
        )
    elif check_id == "tool-idempotency-reported-dedup-001":
        result = require_tool_reported_dedup(context)
        actual_finding = finding(
            requirement_id, check_id, receipt, result["id"],
            domain="claim", status="asserted",
            prohibited=["P1:tool_reported_deduplication_is_independently_verified"],
        )
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": "completed",
        "completeness": {},
    }
