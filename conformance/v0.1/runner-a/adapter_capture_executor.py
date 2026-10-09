#!/usr/bin/env python3
import json

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

# Runner A Wave 03 Batch 23: tool streaming result core.
_BATCH23_STREAMING_REQUIREMENTS = {
    "tool-stream-result-consumption-001": "TAD-062",
    "tool-stream-result-semantics-001": "TAD-063",
    "tool-stream-result-unsupported-001": "TAD-064",
    "tool-stream-result-partial-preserve-001": "TAD-065",
    "tool-stream-result-loss-001": "TAD-066",
    "tool-stream-consumer-stop-bounded-001": "TAD-067",
    "tool-stream-chunks-optional-001": "TAD-068",
}
ADAPTER_CAPTURE_PLANNED_TESTS.update(_BATCH23_STREAMING_REQUIREMENTS)


def stream_metadata_items(record, name, origin=None, value_marker=None):
    items = [
        item
        for item in record.get("metadata", [])
        if isinstance(item, dict)
        and item.get("name") == name
        and (origin is None or item.get("origin") == origin)
    ]
    if value_marker is not None:
        items = [item for item in items if item.get("value") == value_marker]
    return items


def tool_streaming_context(receipt):
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
            f"tool streaming scenario requires one ToolAdapterCapability, found {len(capabilities)}"
        )
    capability = capabilities[0]
    if capability.get("result_boundary") != "application-visible stream consumption":
        raise ValueError("ToolAdapterCapability result boundary is not application-visible stream consumption")
    if capability.get("streaming_result") is not True:
        raise ValueError("ToolAdapterCapability does not positively declare streaming result support")

    if len(invocations) < 3 or len(executions) < 3 or len(results) < 3 or len(diagnostics) < 3:
        raise ValueError("tool streaming scenario is missing invocation/execution/result/diagnostic evidence")

    run_ids = {
        record.get("run_id")
        for record in [capability, *invocations, *executions, *results, *diagnostics]
        if isinstance(record, dict)
    }
    if len(run_ids) != 1 or None in run_ids:
        raise ValueError("tool streaming evidence crosses run ownership")

    for execution in executions:
        invocation = resolve_local(index, execution.get("invocation"), "ToolInvocation")
        if invocation.get("run_id") != execution.get("run_id"):
            raise ValueError("ToolExecution invocation crosses run ownership")

    for result in results:
        execution = resolve_local(index, result.get("execution"), "ToolExecution")
        if execution.get("run_id") != result.get("run_id"):
            raise ValueError("ToolResult execution crosses run ownership")

    for diagnostic in diagnostics:
        subject = resolve_local(index, (diagnostic.get("subject") or {}).get("ref"), "ToolResult")
        declaration = resolve_local(
            index, diagnostic.get("adapter_declaration"), "ToolAdapterCapability"
        )
        if subject.get("run_id") != diagnostic.get("run_id"):
            raise ValueError("CaptureDiagnostic subject crosses run ownership")
        if declaration.get("id") != capability.get("id"):
            raise ValueError("CaptureDiagnostic references a different ToolAdapterCapability")

    return {
        "receipt": receipt,
        "index": index,
        "capability": capability,
        "invocations": invocations,
        "executions": executions,
        "results": results,
        "diagnostics": diagnostics,
    }


def stream_result_for_execution(context, execution):
    matches = [
        result
        for result in context["results"]
        if ref_id(result.get("execution")) == execution.get("id")
    ]
    if len(matches) != 1:
        raise ValueError(
            f"streaming ToolExecution {execution.get('id')} requires one ToolResult, found {len(matches)}"
        )
    return matches[0]


def stream_diagnostic_for_result(context, result, slot=None):
    matches = [
        diagnostic
        for diagnostic in context["diagnostics"]
        if ref_id((diagnostic.get("subject") or {}).get("ref")) == result.get("id")
        and (slot is None or diagnostic.get("slot") == slot)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"streaming ToolResult {result.get('id')} requires one matching CaptureDiagnostic, found {len(matches)}"
        )
    return matches[0]


def require_stream_consumption_observation(context):
    candidates = []
    for execution in context["executions"]:
        observed = stream_metadata_items(
            execution, "stream_consumption_observed", "adapter_observed", True
        )
        result = stream_result_for_execution(context, execution)
        if len(observed) == 1 and result.get("capture_extent") == "partial":
            candidates.append(execution)
    if len(candidates) != 1:
        raise ValueError(
            f"expected one partially captured execution with positive stream consumption observation, found {len(candidates)}"
        )
    return candidates[0]


def require_supported_stream_semantics(context):
    candidates = []
    for result in context["results"]:
        if result.get("capture_extent") != "complete":
            continue
        execution = resolve_local(context["index"], result.get("execution"), "ToolExecution")
        tool_semantics = stream_metadata_items(execution, "event_semantics", "tool_reported")
        assembly_semantics = stream_metadata_items(
            result, "assembly_semantics", "adapter_observed"
        )
        if (
            len(tool_semantics) == 1
            and len(assembly_semantics) == 1
            and tool_semantics[0].get("value") == assembly_semantics[0].get("value")
        ):
            candidates.append((result, tool_semantics[0].get("value")))
    if len(candidates) != 1:
        raise ValueError(
            f"expected one complete ToolResult with supported matching event semantics, found {len(candidates)}"
        )
    result, event_semantics = candidates[0]
    if event_semantics != "replacement_events":
        raise ValueError("streaming semantics scenario does not preserve replacement-event semantics")
    return result, event_semantics


def require_unsupported_stream_semantics(context):
    candidates = [
        diagnostic
        for diagnostic in context["diagnostics"]
        if diagnostic.get("slot") == "tool_result.stream_assembly"
        and diagnostic.get("status") == "unsupported"
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"expected one unsupported stream-assembly diagnostic, found {len(candidates)}"
        )
    diagnostic = candidates[0]
    result = resolve_local(
        context["index"], (diagnostic.get("subject") or {}).get("ref"), "ToolResult"
    )
    if result.get("capture_extent") not in {"partial", "unknown"}:
        raise ValueError("unsupported stream semantics fabricated complete ToolResult capture")
    return diagnostic, result


def require_partial_stream_result_preserved(context):
    candidates = [
        result
        for result in context["results"]
        if result.get("capture_extent") == "partial"
        and isinstance(result.get("representation"), dict)
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"expected one preserved partial ToolResult representation, found {len(candidates)}"
        )
    result = candidates[0]
    execution = resolve_local(context["index"], result.get("execution"), "ToolExecution")
    if len(
        stream_metadata_items(
            execution, "stream_consumption_observed", "adapter_observed", True
        )
    ) != 1:
        raise ValueError("partial ToolResult lacks positive application-visible consumption evidence")
    diagnostic = stream_diagnostic_for_result(
        context, result, "tool_result.stream_events"
    )
    if diagnostic.get("status") != "partial":
        raise ValueError("preserved partial ToolResult is not bounded by partial capture diagnostic")
    return result


def require_lost_events_bound_capture(context):
    candidates = [
        execution
        for execution in context["executions"]
        if len(
            stream_metadata_items(
                execution, "event_loss_detected", "adapter_observed", True
            )
        ) == 1
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected one positive lost-event observation, found {len(candidates)}")
    execution = candidates[0]
    result = stream_result_for_execution(context, execution)
    if result.get("capture_extent") != "partial":
        raise ValueError("known lost result events were reported as complete capture")
    diagnostic = stream_diagnostic_for_result(
        context, result, "tool_result.stream_events"
    )
    if diagnostic.get("status") != "partial":
        raise ValueError("known lost result events are not bounded by partial capture diagnostic")
    return result


def require_consumer_stop_bounded(context):
    candidates = [
        execution
        for execution in context["executions"]
        if len(
            stream_metadata_items(
                execution, "consumer_stopped", "adapter_observed", True
            )
        ) == 1
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected one consumer-stop observation, found {len(candidates)}")
    execution = candidates[0]
    if execution.get("lifecycle_state") == "terminal":
        raise ValueError("consumer stop was upgraded to terminal ToolExecution lifecycle")
    if execution.get("terminal_disposition") is not None:
        raise ValueError("consumer stop synthesized remote terminal disposition")
    return execution


def require_chunk_retention_optional(context):
    candidates = [
        result
        for result in context["results"]
        if result.get("capture_extent") == "complete"
        and isinstance(result.get("representation"), dict)
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"expected one complete terminal ToolResult representation, found {len(candidates)}"
        )
    result = candidates[0]
    execution = resolve_local(context["index"], result.get("execution"), "ToolExecution")
    if execution.get("lifecycle_state") != "terminal":
        raise ValueError("complete stream result is not attached to terminal ToolExecution")
    if execution.get("terminal_disposition") != "completed":
        raise ValueError("complete stream result lacks completed terminal disposition")
    if len(
        stream_metadata_items(
            execution, "stream_consumption_observed", "adapter_observed", True
        )
    ) != 1:
        raise ValueError("complete stream result lacks positive consumption observation")
    diagnostic = stream_diagnostic_for_result(
        context, result, "tool_result.stream_events"
    )
    if diagnostic.get("status") != "observed":
        raise ValueError("complete stream result lacks observed capture diagnostic")
    if any(
        isinstance(record.get("kind"), str)
        and "chunk" in record.get("kind", "").lower()
        for record in records(context["receipt"])
        if isinstance(record, dict)
    ):
        raise ValueError("chunk-optional scenario unexpectedly persists result-chunk records")
    return result


_execute_adapter_capture_case_before_batch23 = execute_adapter_capture_case


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    expected_requirement = _BATCH23_STREAMING_REQUIREMENTS.get(check_id)
    if expected_requirement is None:
        return _execute_adapter_capture_case_before_batch23(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)
    context = tool_streaming_context(receipt)

    if check_id == "tool-stream-result-consumption-001":
        execution = require_stream_consumption_observation(context)
        actual_finding = finding(requirement_id, check_id, receipt, execution["id"])
    elif check_id == "tool-stream-result-semantics-001":
        result, event_semantics = require_supported_stream_semantics(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            result["id"],
            selector={"event_semantics": event_semantics},
        )
    elif check_id == "tool-stream-result-unsupported-001":
        diagnostic, _result = require_unsupported_stream_semantics(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            diagnostic["id"],
            domain="support",
            status="unsupported",
        )
    elif check_id == "tool-stream-result-partial-preserve-001":
        result = require_partial_stream_result_preserved(context)
        actual_finding = finding(requirement_id, check_id, receipt, result["id"])
    elif check_id == "tool-stream-result-loss-001":
        result = require_lost_events_bound_capture(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            result["id"],
            selector={"capture_extent": result["capture_extent"]},
        )
    elif check_id == "tool-stream-consumer-stop-bounded-001":
        execution = require_consumer_stop_bounded(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            execution["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:consumer_stop_proves_remote_completion_or_effect_cardinality"],
        )
    elif check_id == "tool-stream-chunks-optional-001":
        result = require_chunk_retention_optional(context)
        actual_finding = finding(requirement_id, check_id, receipt, result["id"])
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": "completed",
        "completeness": {},
    }

# Runner A Wave 03 Batch 24: provider streaming boundary core.
_BATCH24_PROVIDER_STREAMING_REQUIREMENTS = {
    "provider-stream-consumption-boundary-001": "PAD-046",
    "provider-stream-event-semantics-001": "PAD-047",
    "provider-stream-unsupported-degrade-001": "PAD-048",
    "provider-stream-partial-preserve-001": "PAD-049",
    "provider-stream-app-stop-bounded-001": "PAD-050",
    "provider-stream-drop-no-complete-001": "PAD-051",
    "provider-stream-tool-fragment-001": "PAD-052",
}
ADAPTER_CAPTURE_PLANNED_TESTS.update(_BATCH24_PROVIDER_STREAMING_REQUIREMENTS)


def provider_streaming_capability(materialized):
    capabilities = [
        value
        for value in materialized.values()
        if isinstance(value, dict)
        and value.get("kind") == "ProviderAdapterCapability"
    ]
    if len(capabilities) != 1:
        raise ValueError(
            f"provider streaming scenario requires one inline ProviderAdapterCapability, found {len(capabilities)}"
        )
    capability = capabilities[0]
    if capability.get("output_capture") is not True:
        raise ValueError("ProviderAdapterCapability does not declare output capture")
    if capability.get("streaming_output") is not True:
        raise ValueError("ProviderAdapterCapability does not declare streaming output support")
    if capability.get("invocation_boundary") != "logical application model call":
        raise ValueError("ProviderAdapterCapability invocation boundary is not the application logical call")
    if capability.get("attempt_boundary") != "provider attempt start":
        raise ValueError("ProviderAdapterCapability attempt boundary is not provider attempt start")
    return capability


def provider_streaming_context(receipt):
    index = record_index(receipt)
    invocations = by_kind(receipt, "ModelInvocation")
    attempts = by_kind(receipt, "ProviderAttempt")
    outputs = by_kind(receipt, "ModelOutput")
    diagnostics = by_kind(receipt, "CaptureDiagnostic")
    proposals = by_kind(receipt, "ToolProposal")

    if len(invocations) != 1:
        raise ValueError(
            f"provider streaming scenario requires one ModelInvocation, found {len(invocations)}"
        )
    if len(attempts) != 1:
        raise ValueError(
            f"provider streaming scenario requires one ProviderAttempt, found {len(attempts)}"
        )
    if len(outputs) != 1:
        raise ValueError(
            f"provider streaming scenario requires one ModelOutput, found {len(outputs)}"
        )

    invocation = invocations[0]
    attempt = attempts[0]
    output = outputs[0]

    resolved_invocation = resolve_local(index, attempt.get("invocation"), "ModelInvocation")
    if resolved_invocation.get("id") != invocation.get("id"):
        raise ValueError("ProviderAttempt does not belong to the materialized ModelInvocation")

    resolved_attempt = resolve_local(index, output.get("attempt"), "ProviderAttempt")
    if resolved_attempt.get("id") != attempt.get("id"):
        raise ValueError("ModelOutput does not belong to the materialized ProviderAttempt")

    accepted_output = resolve_local(index, invocation.get("accepted_output"), "ModelOutput")
    if accepted_output.get("id") != output.get("id"):
        raise ValueError("ModelInvocation accepted_output is not the materialized ModelOutput")

    run_ids = {invocation.get("run_id"), attempt.get("run_id"), output.get("run_id")}
    if None in run_ids or len(run_ids) != 1:
        raise ValueError("provider streaming occurrence crosses run ownership")

    output_items = []
    for reference in output.get("item_refs", []):
        item = resolve_local(index, reference)
        if item.get("run_id") != output.get("run_id"):
            raise ValueError("ModelOutput item crosses run ownership")
        if item.get("kind") == "TextOutput" and item.get("output") is not None:
            backref = resolve_local(index, item.get("output"), "ModelOutput")
            if backref.get("id") != output.get("id"):
                raise ValueError("TextOutput back-reference points to a different ModelOutput")
        output_items.append(item)

    for diagnostic in diagnostics:
        subject_ref = (diagnostic.get("subject") or {}).get("ref")
        subject = resolve_local(index, subject_ref)
        if subject.get("run_id") != diagnostic.get("run_id"):
            raise ValueError("provider stream CaptureDiagnostic crosses run ownership")

    return {
        "receipt": receipt,
        "index": index,
        "invocation": invocation,
        "attempt": attempt,
        "output": output,
        "output_items": output_items,
        "diagnostics": diagnostics,
        "proposals": proposals,
    }


def provider_stream_diagnostic(context, slot, status, subject_kind):
    matches = [
        diagnostic
        for diagnostic in context["diagnostics"]
        if diagnostic.get("slot") == slot
        and diagnostic.get("status") == status
    ]
    if len(matches) != 1:
        raise ValueError(
            f"provider streaming scenario requires one {slot}/{status} diagnostic, found {len(matches)}"
        )
    diagnostic = matches[0]
    subject = resolve_local(
        context["index"],
        (diagnostic.get("subject") or {}).get("ref"),
        subject_kind,
    )
    return diagnostic, subject


def require_provider_stream_consumption(materialized, context):
    provider_streaming_capability(materialized)
    diagnostic, attempt = provider_stream_diagnostic(
        context, "provider_stream.events", "observed", "ProviderAttempt"
    )
    if attempt.get("id") != context["attempt"].get("id"):
        raise ValueError("stream-consumption diagnostic is not scoped to the materialized attempt")
    if ref_id(context["output"].get("attempt")) != attempt.get("id"):
        raise ValueError("stream-consumption diagnostic attempt is not the ModelOutput attempt")
    return diagnostic


def require_provider_stream_semantics(context):
    semantics = [
        item
        for item in context["invocation"].get("metadata", [])
        if isinstance(item, dict)
        and item.get("name") == "stream_assembly_semantics"
        and item.get("origin") == "adapter_observed"
    ]
    if len(semantics) != 1:
        raise ValueError(
            f"provider stream scenario requires one adapter-observed assembly semantic, found {len(semantics)}"
        )
    if semantics[0].get("value") != "indexed-delta":
        raise ValueError("provider stream assembly semantic is unsupported or blind-delta")
    return context["output"]


def require_provider_stream_unsupported_degrade(materialized, context):
    provider_streaming_capability(materialized)
    _diagnostic, attempt = provider_stream_diagnostic(
        context, "provider_stream.assembly", "unsupported", "ProviderAttempt"
    )
    if attempt.get("id") != context["attempt"].get("id"):
        raise ValueError("unsupported stream diagnostic is not scoped to the materialized attempt")
    output = context["output"]
    if output.get("capture_extent") not in {"partial", "unknown"}:
        raise ValueError("unsupported stream semantics fabricated complete ModelOutput capture")
    if output.get("response_termination") != "incomplete":
        raise ValueError("unsupported stream semantics fabricated terminal ModelOutput completion")
    return output


def require_provider_partial_output_preserved(context):
    attempt = context["attempt"]
    output = context["output"]
    if attempt.get("terminal_disposition") != "timeout":
        raise ValueError("partial stream preservation scenario lacks timeout termination")
    if output.get("capture_extent") != "partial":
        raise ValueError("observed partial ModelOutput was not preserved as partial")
    if output.get("response_termination") != "incomplete":
        raise ValueError("partial ModelOutput was upgraded to complete response termination")
    preserved_text = [
        item
        for item in context["output_items"]
        if item.get("kind") == "TextOutput"
        and isinstance(item.get("text"), str)
        and item.get("text") != ""
    ]
    if not preserved_text:
        raise ValueError("partial ModelOutput has no preserved observed text evidence")
    return output


def require_provider_app_stop_bounded(context):
    attempt = context["attempt"]
    output = context["output"]
    if attempt.get("terminal_disposition") not in {"timeout", "cancelled", "interrupted"}:
        raise ValueError("application stop scenario was upgraded to provider-normal completion")
    if output.get("response_termination") != "incomplete":
        raise ValueError("application stop scenario reports normal output completion")
    if output.get("capture_extent") != "partial":
        raise ValueError("application stop scenario reports complete output capture")
    return attempt


def require_provider_dropped_event_invalidity(context):
    diagnostic, output = provider_stream_diagnostic(
        context, "provider_stream.events", "partial", "ModelOutput"
    )
    if output.get("id") != context["output"].get("id"):
        raise ValueError("dropped-event diagnostic is not scoped to the materialized ModelOutput")
    if diagnostic.get("reason") != "known dropped events":
        raise ValueError("partial stream diagnostic does not establish known dropped events")
    if output.get("capture_extent") != "complete":
        raise ValueError("known dropped events do not conflict with complete capture in this case")
    return output


def require_incomplete_tool_fragment_bounded(context):
    fragments = [
        item
        for item in context["invocation"].get("metadata", [])
        if isinstance(item, dict)
        and item.get("name") == "tool_call_fragment"
        and item.get("origin") == "provider_reported"
        and isinstance(item.get("value"), str)
    ]
    if len(fragments) != 1:
        raise ValueError(
            f"provider stream scenario requires one provider-reported tool fragment, found {len(fragments)}"
        )
    try:
        json.loads(fragments[0]["value"])
    except json.JSONDecodeError:
        pass
    else:
        raise ValueError("tool_call_fragment is a complete JSON value rather than an incomplete fragment")
    if context["proposals"]:
        raise ValueError("incomplete provider tool fragment synthesized a ToolProposal occurrence")
    if context["output"].get("response_termination") != "incomplete":
        raise ValueError("tool-fragment scenario is not an incomplete ModelOutput")
    return context["output"]


_execute_adapter_capture_case_before_batch24 = execute_adapter_capture_case


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    expected_requirement = _BATCH24_PROVIDER_STREAMING_REQUIREMENTS.get(check_id)
    if expected_requirement is None:
        return _execute_adapter_capture_case_before_batch24(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)
    context = provider_streaming_context(receipt)
    process_outcome = "completed"

    if check_id == "provider-stream-consumption-boundary-001":
        diagnostic = require_provider_stream_consumption(materialized, context)
        actual_finding = provider_finding(
            requirement_id, check_id, receipt, diagnostic["id"]
        )
    elif check_id == "provider-stream-event-semantics-001":
        output = require_provider_stream_semantics(context)
        actual_finding = provider_finding(
            requirement_id, check_id, receipt, output["id"]
        )
    elif check_id == "provider-stream-unsupported-degrade-001":
        output = require_provider_stream_unsupported_degrade(materialized, context)
        actual_finding = provider_finding(
            requirement_id, check_id, receipt, output["id"]
        )
    elif check_id == "provider-stream-partial-preserve-001":
        output = require_provider_partial_output_preserved(context)
        actual_finding = provider_finding(
            requirement_id, check_id, receipt, output["id"]
        )
    elif check_id == "provider-stream-app-stop-bounded-001":
        attempt = require_provider_app_stop_bounded(context)
        actual_finding = provider_finding(
            requirement_id,
            check_id,
            receipt,
            attempt["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:application_stream_stop_is_provider_completion"],
        )
    elif check_id == "provider-stream-drop-no-complete-001":
        output = require_provider_dropped_event_invalidity(context)
        actual_finding = provider_finding(
            requirement_id,
            check_id,
            receipt,
            output["id"],
            status="invalid",
            reason_code="complete_capture_with_known_dropped_events",
        )
        process_outcome = "invalidity_detected"
    elif check_id == "provider-stream-tool-fragment-001":
        output = require_incomplete_tool_fragment_bounded(context)
        actual_finding = provider_finding(
            requirement_id,
            check_id,
            receipt,
            output["id"],
            prohibited=["P1:incomplete_tool_fragment_synthesizes_tool_proposal"],
        )
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": process_outcome,
        "completeness": {},
    }


# Runner A Wave 03 Batch 26: tool metadata-origin core.
_BATCH26_METADATA_REQUIREMENTS = {
    "tool-metadata-origin-001": "TAD-069",
    "tool-metadata-reported-bounded-001": "TAD-070",
    "tool-transaction-id-no-commit-proof-001": "TAD-072",
    "tool-metadata-normalized-origin-001": "TAD-074",
    "tool-external-metadata-not-effect-observation-001": "TAD-116",
    "tool-async-acceptance-bounded-001": "TAD-117",
}
ADAPTER_CAPTURE_PLANNED_TESTS.update(_BATCH26_METADATA_REQUIREMENTS)

_TOOL_METADATA_ORIGINS = {
    "application_supplied",
    "adapter_observed",
    "tool_reported",
    "adapter_derived",
    "external_observed",
    "unknown",
}


def tool_metadata_origin_context(receipt):
    index = record_index(receipt)
    invocations = by_kind(receipt, "ToolInvocation")
    executions = by_kind(receipt, "ToolExecution")
    results = by_kind(receipt, "ToolResult")

    if len(invocations) != 1:
        raise ValueError(
            f"tool metadata-origin scenario requires one ToolInvocation, found {len(invocations)}"
        )
    if len(executions) != 1:
        raise ValueError(
            f"tool metadata-origin scenario requires one ToolExecution, found {len(executions)}"
        )
    if len(results) != 1:
        raise ValueError(
            f"tool metadata-origin scenario requires one ToolResult, found {len(results)}"
        )

    invocation = invocations[0]
    execution = executions[0]
    result = results[0]

    resolved_invocation = resolve_local(index, execution.get("invocation"), "ToolInvocation")
    if resolved_invocation.get("id") != invocation.get("id"):
        raise ValueError("ToolExecution does not belong to the materialized ToolInvocation")

    resolved_execution = resolve_local(index, result.get("execution"), "ToolExecution")
    if resolved_execution.get("id") != execution.get("id"):
        raise ValueError("ToolResult does not belong to the materialized ToolExecution")

    run_ids = {
        invocation.get("run_id"),
        execution.get("run_id"),
        result.get("run_id"),
    }
    if None in run_ids or len(run_ids) != 1:
        raise ValueError("tool metadata-origin occurrence crosses run ownership")

    metadata = result.get("metadata")
    if not isinstance(metadata, list) or not metadata:
        raise ValueError("ToolResult metadata is missing")

    metadata_by_name = {}
    for item in metadata:
        if not isinstance(item, dict):
            raise ValueError("ToolResult metadata contains a non-object item")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("ToolResult metadata item has no name")
        if name in metadata_by_name:
            raise ValueError(f"ToolResult metadata contains duplicate name {name}")
        origin = item.get("origin")
        if origin not in _TOOL_METADATA_ORIGINS:
            raise ValueError(f"ToolResult metadata {name} has unsupported origin {origin!r}")
        metadata_by_name[name] = item

    return {
        "receipt": receipt,
        "index": index,
        "invocation": invocation,
        "execution": execution,
        "result": result,
        "metadata_by_name": metadata_by_name,
    }


def require_tool_metadata_item(context, name, origin):
    item = context["metadata_by_name"].get(name)
    if not isinstance(item, dict):
        raise ValueError(f"ToolResult metadata {name} is missing")
    if item.get("origin") != origin:
        raise ValueError(
            f"ToolResult metadata {name} origin is {item.get('origin')!r}, expected {origin!r}"
        )
    return item


def require_explicit_tool_metadata_origins(context):
    origins = {
        item.get("origin")
        for item in context["metadata_by_name"].values()
    }
    required = {"tool_reported", "adapter_derived", "adapter_observed"}
    if not required.issubset(origins):
        raise ValueError(
            "tool metadata-origin scenario does not distinguish reported, derived, and observed metadata"
        )
    return context["result"]


def require_tool_reported_metadata_bounded(context):
    status = require_tool_metadata_item(context, "server_status", "tool_reported")
    if not isinstance(status.get("value"), str) or not status["value"]:
        raise ValueError("tool-reported server_status has no bounded value")
    return context["result"], status


def require_transaction_id_not_commit_proof(context):
    transaction = require_tool_metadata_item(
        context, "transaction_id", "tool_reported"
    )
    if not isinstance(transaction.get("value"), str) or not transaction["value"]:
        raise ValueError("tool-reported transaction_id has no value")
    reported_status = context["result"].get("reported_status")
    if not isinstance(reported_status, str) or not reported_status:
        raise ValueError("ToolResult reported_status is missing")
    if by_kind(context["receipt"], "EffectObservation"):
        raise ValueError(
            "transaction-id boundedness scenario unexpectedly contains EffectObservation evidence"
        )
    return context["result"], transaction


def require_normalized_metadata_origin(context):
    normalized = require_tool_metadata_item(
        context, "normalized_status", "adapter_derived"
    )
    basis = normalized.get("mapping_basis")
    if not isinstance(basis, str) or not basis:
        raise ValueError("adapter-derived normalized_status has no mapping basis")
    source = require_tool_metadata_item(context, "server_status", "tool_reported")
    source_value = source.get("value")
    if not isinstance(source_value, str) or not source_value:
        raise ValueError("tool-reported server_status has no source value")
    if "server_status" not in basis or source_value not in basis:
        raise ValueError(
            "normalized_status mapping basis does not preserve the tool-reported source basis"
        )
    return context["result"], normalized


def require_external_metadata_not_separate_observation(context):
    external = require_tool_metadata_item(
        context, "external_state_echo", "external_observed"
    )
    if "value" not in external:
        raise ValueError("external_observed metadata has no observed value")
    if any(
        observation.get("basis") == "separate_observation"
        for observation in by_kind(context["receipt"], "EffectObservation")
    ):
        raise ValueError(
            "external_observed metadata scenario unexpectedly contains separate_observation evidence"
        )
    return context["result"]


def require_async_acceptance_bounded(context):
    async_states = {
        "accepted",
        "queued",
        "scheduled",
        "pending",
        "job_created",
        "job-created",
    }
    result = context["result"]
    if result.get("reported_status") not in async_states:
        raise ValueError("ToolResult is not in an asynchronous acceptance state")

    server_status = require_tool_metadata_item(
        context, "server_status", "tool_reported"
    )
    if server_status.get("value") not in async_states:
        raise ValueError("tool-reported server_status is not asynchronous")

    normalized = require_tool_metadata_item(
        context, "normalized_status", "adapter_derived"
    )
    if normalized.get("value") not in async_states:
        raise ValueError("adapter-derived normalized_status is not asynchronous")
    if not isinstance(normalized.get("mapping_basis"), str) or not normalized["mapping_basis"]:
        raise ValueError("async normalized_status has no mapping basis")

    representation = result.get("representation") or {}
    if representation.get("representation_kind") != "json":
        raise ValueError("async ToolResult representation is not JSON")
    value = representation.get("value")
    if not isinstance(value, dict):
        raise ValueError("async ToolResult representation is not a JSON object")
    if value.get("status") not in async_states:
        raise ValueError("async ToolResult representation status is not asynchronous")
    if not isinstance(value.get("job_id"), str) or not value["job_id"]:
        raise ValueError("async ToolResult representation has no job_id")

    if by_kind(context["receipt"], "EffectObservation"):
        raise ValueError(
            "async-acceptance boundedness scenario unexpectedly contains EffectObservation evidence"
        )
    return result


_execute_adapter_capture_case_before_batch26 = execute_adapter_capture_case


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    expected_requirement = _BATCH26_METADATA_REQUIREMENTS.get(check_id)
    if expected_requirement is None:
        return _execute_adapter_capture_case_before_batch26(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)
    context = tool_metadata_origin_context(receipt)

    if check_id == "tool-metadata-origin-001":
        result = require_explicit_tool_metadata_origins(context)
        actual_finding = finding(
            requirement_id, check_id, receipt, result["id"]
        )
    elif check_id == "tool-metadata-reported-bounded-001":
        result, _status = require_tool_reported_metadata_bounded(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            result["id"],
            selector={"metadata_name": "server_status"},
            domain="claim",
            status="asserted",
            prohibited=["P1:tool_reported_metadata_is_independently_verified"],
        )
    elif check_id == "tool-transaction-id-no-commit-proof-001":
        result, _transaction = require_transaction_id_not_commit_proof(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            result["id"],
            selector={"metadata_name": "transaction_id"},
            domain="claim",
            status="asserted",
            prohibited=["P1:tool_reported_transaction_id_proves_commit"],
        )
    elif check_id == "tool-metadata-normalized-origin-001":
        result, _normalized = require_normalized_metadata_origin(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            result["id"],
            selector={
                "metadata_name": "normalized_status",
                "origin": "adapter_derived",
            },
        )
    elif check_id == "tool-external-metadata-not-effect-observation-001":
        result = require_external_metadata_not_separate_observation(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            result["id"],
            domain="claim",
            status="asserted",
            prohibited=[
                "P1:external_observed_metadata_is_separate_effect_observation"
            ],
        )
    elif check_id == "tool-async-acceptance-bounded-001":
        result = require_async_acceptance_bounded(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            result["id"],
            domain="claim",
            status="asserted",
            prohibited=[
                "P1:async_acceptance_proves_remote_completion_effect_or_outcome"
            ],
        )
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": "completed",
        "completeness": {},
    }


# Runner A Wave 03 Batch 28: tool capture-failure separation core.
_BATCH28_CAPTURE_FAILURE_REQUIREMENTS = {
    "tool-capture-execution-failure-separation-001": "TAD-094",
    "tool-capture-result-failure-no-fabrication-001": "TAD-095",
    "tool-adapter-error-origin-001": "TAD-097",
    "tool-missing-result-not-negation-001": "TAD-115",
}
ADAPTER_CAPTURE_PLANNED_TESTS.update(_BATCH28_CAPTURE_FAILURE_REQUIREMENTS)

_BATCH28_CAPTURE_FAILURE_SLOTS = {
    "tool_execution.terminal_lifecycle",
    "tool_result.application_visible",
    "effect_observation.follow_up",
    "adapter.instrumentation",
}


def tool_capture_failure_context(receipt):
    index = record_index(receipt)
    invocations = by_kind(receipt, "ToolInvocation")
    executions = by_kind(receipt, "ToolExecution")
    results = by_kind(receipt, "ToolResult")
    diagnostics = by_kind(receipt, "CaptureDiagnostic")

    if len(invocations) != 1:
        raise ValueError(
            f"tool capture-failure scenario requires one ToolInvocation, found {len(invocations)}"
        )
    if len(executions) != 1:
        raise ValueError(
            f"tool capture-failure scenario requires one ToolExecution, found {len(executions)}"
        )
    if len(results) > 1:
        raise ValueError(
            f"tool capture-failure scenario permits at most one ToolResult, found {len(results)}"
        )
    if len(diagnostics) != 4:
        raise ValueError(
            f"tool capture-failure scenario requires four CaptureDiagnostics, found {len(diagnostics)}"
        )

    invocation = invocations[0]
    execution = executions[0]
    resolved_invocation = resolve_local(index, execution.get("invocation"), "ToolInvocation")
    if resolved_invocation.get("id") != invocation.get("id"):
        raise ValueError("ToolExecution does not belong to the materialized ToolInvocation")

    run_id = execution.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("ToolExecution run ownership is missing")
    if invocation.get("run_id") != run_id:
        raise ValueError("ToolInvocation and ToolExecution cross run ownership")

    results_by_execution = []
    for result in results:
        resolved_execution = resolve_local(index, result.get("execution"), "ToolExecution")
        if resolved_execution.get("id") != execution.get("id"):
            raise ValueError("ToolResult belongs to a different ToolExecution")
        if result.get("run_id") != run_id:
            raise ValueError("ToolResult crosses run ownership")
        results_by_execution.append(result)

    diagnostics_by_slot = {}
    declaration_ids = set()
    for diagnostic in diagnostics:
        slot = diagnostic.get("slot")
        if slot not in _BATCH28_CAPTURE_FAILURE_SLOTS:
            raise ValueError(f"unexpected tool capture-failure diagnostic slot: {slot!r}")
        if slot in diagnostics_by_slot:
            raise ValueError(f"duplicate tool capture-failure diagnostic slot: {slot}")
        if diagnostic.get("status") != "unavailable":
            raise ValueError(f"CaptureDiagnostic {slot} is not unavailable")
        reason = diagnostic.get("reason")
        if not isinstance(reason, str) or not reason:
            raise ValueError(f"CaptureDiagnostic {slot} has no bounded reason")

        declaration = resolve_local(
            index, diagnostic.get("adapter_declaration"), "ToolAdapterCapability"
        )
        declaration_id = declaration.get("id")
        if not isinstance(declaration_id, str) or not declaration_id:
            raise ValueError(f"CaptureDiagnostic {slot} adapter declaration has no id")
        declaration_ids.add(declaration_id)
        if declaration.get("run_id") != run_id:
            raise ValueError(f"CaptureDiagnostic {slot} adapter declaration crosses run ownership")

        subject = diagnostic.get("subject") or {}
        if subject.get("representation_basis") != "tool_execution":
            raise ValueError(f"CaptureDiagnostic {slot} has wrong representation basis")
        subject_record = resolve_local(index, subject.get("ref"), "ToolExecution")
        if subject_record.get("id") != execution.get("id"):
            raise ValueError(f"CaptureDiagnostic {slot} references wrong ToolExecution")
        if subject_record.get("run_id") != run_id:
            raise ValueError(f"CaptureDiagnostic {slot} subject crosses run ownership")
        if diagnostic.get("run_id") != run_id:
            raise ValueError(f"CaptureDiagnostic {slot} crosses run ownership")

        diagnostics_by_slot[slot] = diagnostic

    if set(diagnostics_by_slot) != _BATCH28_CAPTURE_FAILURE_SLOTS:
        raise ValueError("tool capture-failure diagnostic slots are incomplete")
    if len(declaration_ids) != 1:
        raise ValueError("tool capture-failure diagnostics reference multiple adapter declarations")

    return {
        "receipt": receipt,
        "index": index,
        "invocation": invocation,
        "execution": execution,
        "results": results_by_execution,
        "diagnostics": diagnostics_by_slot,
        "adapter_declaration_id": next(iter(declaration_ids)),
    }


def require_execution_capture_failure_separated(context):
    diagnostic = context["diagnostics"]["tool_execution.terminal_lifecycle"]
    execution = context["execution"]
    if execution.get("lifecycle_state") != "in_progress":
        raise ValueError("execution capture failure was upgraded to terminal ToolExecution lifecycle")
    if execution.get("terminal_disposition") is not None:
        raise ValueError("execution capture failure fabricated terminal disposition")
    reason = diagnostic.get("reason", "").lower()
    if "instrumentation failed" not in reason or "no terminal disposition observed" not in reason:
        raise ValueError("execution capture-failure diagnostic reason is not bounded to missing lifecycle observation")
    return diagnostic


def require_result_capture_failure_no_fabrication(context):
    diagnostic = context["diagnostics"]["tool_result.application_visible"]
    if context["results"]:
        raise ValueError("result capture-failure no-fabrication case contains a ToolResult")
    reason = diagnostic.get("reason", "").lower()
    if "result capture instrumentation failed" not in reason:
        raise ValueError("result capture-failure diagnostic does not identify instrumentation failure")
    if "no complete toolresult representation observed" not in reason:
        raise ValueError("result capture-failure diagnostic does not preserve bounded observation scope")
    return diagnostic


def require_adapter_error_origin_bounded(context):
    diagnostic = context["diagnostics"]["adapter.instrumentation"]
    execution = context["execution"]
    if diagnostic.get("reason") != "adapter instrumentation exception":
        raise ValueError("adapter instrumentation diagnostic does not preserve adapter-origin exception")
    if execution.get("lifecycle_state") != "in_progress":
        raise ValueError("adapter instrumentation exception was upgraded to terminal tool lifecycle")
    if execution.get("terminal_disposition") is not None:
        raise ValueError("adapter instrumentation exception fabricated tool/runtime/server disposition")
    for result in context["results"]:
        if result.get("reported_status") not in {None, "unknown"}:
            raise ValueError("adapter instrumentation exception was upgraded to tool/server result status")
    return diagnostic


def require_missing_result_not_negation(context):
    diagnostic = context["diagnostics"]["tool_result.application_visible"]
    if context["results"]:
        raise ValueError("missing-result boundedness case contains a ToolResult")
    if diagnostic.get("status") != "unavailable":
        raise ValueError("missing ToolResult is not bounded by unavailable result capture")
    reason = diagnostic.get("reason", "").lower()
    if "result capture instrumentation failed" not in reason:
        raise ValueError("missing ToolResult is not tied to known result-capture degradation")
    return diagnostic


_execute_adapter_capture_case_before_batch28 = execute_adapter_capture_case


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    expected_requirement = _BATCH28_CAPTURE_FAILURE_REQUIREMENTS.get(check_id)
    if expected_requirement is None:
        return _execute_adapter_capture_case_before_batch28(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)
    context = tool_capture_failure_context(receipt)

    if check_id == "tool-capture-execution-failure-separation-001":
        diagnostic = require_execution_capture_failure_separated(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            diagnostic["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:execution_capture_failure_means_tool_execution_failed"],
        )
    elif check_id == "tool-capture-result-failure-no-fabrication-001":
        diagnostic = require_result_capture_failure_no_fabrication(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            diagnostic["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:result_capture_failure_fabricates_tool_result"],
        )
    elif check_id == "tool-adapter-error-origin-001":
        diagnostic = require_adapter_error_origin_bounded(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            diagnostic["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:adapter_exception_is_tool_or_server_exception"],
        )
    elif check_id == "tool-missing-result-not-negation-001":
        diagnostic = require_missing_result_not_negation(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            diagnostic["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:missing_tool_result_proves_no_runtime_result"],
        )
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": "completed",
        "completeness": {},
    }


# Runner A Wave 03 Batch 29: tool lifecycle/effect bounds core.
_BATCH29_LIFECYCLE_EFFECT_REQUIREMENTS = {
    "tool-execution-disposition-boundary-001": "TAD-043",
    "tool-completed-not-effect-001": "TAD-044",
    "tool-timeout-not-no-effect-001": "TAD-045",
    "tool-noncompleted-not-no-effect-001": "TAD-113",
}
ADAPTER_CAPTURE_PLANNED_TESTS.update(_BATCH29_LIFECYCLE_EFFECT_REQUIREMENTS)


def tool_lifecycle_effect_context(receipt):
    index = record_index(receipt)
    invocations = by_kind(receipt, "ToolInvocation")
    executions = by_kind(receipt, "ToolExecution")
    results = by_kind(receipt, "ToolResult")
    diagnostics = by_kind(receipt, "CaptureDiagnostic")
    effects = by_kind(receipt, "EffectObservation")

    if len(invocations) != 3:
        raise ValueError(
            f"tool lifecycle/effect scenario requires three ToolInvocations, found {len(invocations)}"
        )
    if len(executions) != 3:
        raise ValueError(
            f"tool lifecycle/effect scenario requires three ToolExecutions, found {len(executions)}"
        )
    if len(results) != 1:
        raise ValueError(
            f"tool lifecycle/effect scenario requires one ToolResult, found {len(results)}"
        )
    if len(diagnostics) != 1:
        raise ValueError(
            f"tool lifecycle/effect scenario requires one CaptureDiagnostic, found {len(diagnostics)}"
        )

    run_ids = {
        record.get("run_id")
        for record in [*invocations, *executions, *results, *diagnostics]
    }
    if None in run_ids or len(run_ids) != 1:
        raise ValueError("tool lifecycle/effect evidence crosses run ownership")
    run_id = next(iter(run_ids))

    invocation_by_id = {record.get("id"): record for record in invocations}
    if len(invocation_by_id) != 3 or None in invocation_by_id:
        raise ValueError("ToolInvocation identities are missing or duplicated")

    execution_by_disposition = {}
    for execution in executions:
        if execution.get("lifecycle_state") != "terminal":
            raise ValueError("tool lifecycle/effect scenario contains non-terminal ToolExecution")
        invocation = resolve_local(index, execution.get("invocation"), "ToolInvocation")
        if invocation.get("id") not in invocation_by_id:
            raise ValueError("ToolExecution resolves to an unexpected ToolInvocation")
        if invocation.get("run_id") != run_id:
            raise ValueError("ToolExecution invocation crosses run ownership")

        disposition = execution.get("terminal_disposition")
        if disposition not in {"completed", "timeout", "cancelled"}:
            raise ValueError(f"unexpected ToolExecution disposition {disposition!r}")
        if disposition in execution_by_disposition:
            raise ValueError(f"duplicate ToolExecution disposition {disposition}")
        execution_by_disposition[disposition] = execution

    if set(execution_by_disposition) != {"completed", "timeout", "cancelled"}:
        raise ValueError("completed/timeout/cancelled ToolExecution occurrences are incomplete")

    expected_basis = {
        "completed": "runtime_returned",
        "timeout": "client_timeout",
        "cancelled": "local_cancellation",
    }
    lifecycle_basis = {}
    for disposition, execution in execution_by_disposition.items():
        items = [
            item
            for item in execution.get("metadata", [])
            if isinstance(item, dict)
            and item.get("name") == "lifecycle_basis"
        ]
        if len(items) != 1:
            raise ValueError(
                f"ToolExecution {execution.get('id')} requires one lifecycle_basis metadata item"
            )
        item = items[0]
        if item.get("origin") != "adapter_observed":
            raise ValueError(
                f"ToolExecution {execution.get('id')} lifecycle_basis is not adapter_observed"
            )
        if item.get("value") != expected_basis[disposition]:
            raise ValueError(
                f"ToolExecution {execution.get('id')} lifecycle_basis does not match {disposition}"
            )
        lifecycle_basis[disposition] = item

    result = results[0]
    resolved_execution = resolve_local(index, result.get("execution"), "ToolExecution")
    completed = execution_by_disposition["completed"]
    if resolved_execution.get("id") != completed.get("id"):
        raise ValueError("ToolResult is not attached to the completed ToolExecution")
    if result.get("run_id") != run_id:
        raise ValueError("ToolResult crosses run ownership")

    diagnostic = diagnostics[0]
    if diagnostic.get("slot") != "tool_execution.lifecycle":
        raise ValueError("lifecycle CaptureDiagnostic has unexpected slot")
    if diagnostic.get("status") != "observed":
        raise ValueError("lifecycle CaptureDiagnostic is not observed")
    subject = resolve_local(
        index, (diagnostic.get("subject") or {}).get("ref"), "ToolExecution"
    )
    if subject.get("id") != completed.get("id"):
        raise ValueError("lifecycle CaptureDiagnostic is not scoped to completed execution")
    if subject.get("run_id") != run_id or diagnostic.get("run_id") != run_id:
        raise ValueError("lifecycle CaptureDiagnostic crosses run ownership")
    if (diagnostic.get("subject") or {}).get("representation_basis") != "tool_execution":
        raise ValueError("lifecycle CaptureDiagnostic has wrong representation basis")
    if diagnostic.get("reason") != "runtime completion observed":
        raise ValueError("lifecycle CaptureDiagnostic does not preserve runtime completion basis")

    return {
        "receipt": receipt,
        "index": index,
        "run_id": run_id,
        "invocations": invocations,
        "executions": execution_by_disposition,
        "result": result,
        "diagnostic": diagnostic,
        "lifecycle_basis": lifecycle_basis,
        "effects": effects,
    }


def require_runtime_observed_disposition(context):
    completed = context["executions"]["completed"]
    result = context["result"]
    basis = context["lifecycle_basis"]["completed"]
    if basis.get("origin") != "adapter_observed" or basis.get("value") != "runtime_returned":
        raise ValueError("completed disposition lacks runtime-observed lifecycle basis")
    if context["diagnostic"].get("status") != "observed":
        raise ValueError("completed disposition lacks observed lifecycle diagnostic")
    if result.get("reported_status") != "success":
        raise ValueError("disposition-boundary scenario lacks contrasting tool-reported status")
    if completed.get("terminal_disposition") != "completed":
        raise ValueError("runtime-returned lifecycle did not produce completed disposition")
    return completed


def require_completed_effect_bounded(context):
    completed = context["executions"]["completed"]
    if completed.get("terminal_disposition") != "completed":
        raise ValueError("completed-effect boundedness scenario lacks completed execution")
    if context["lifecycle_basis"]["completed"].get("value") != "runtime_returned":
        raise ValueError("completed execution lacks runtime lifecycle basis")
    if context["effects"]:
        raise ValueError("completed-effect boundedness scenario contains independent EffectObservation")
    return completed


def require_timeout_effect_bounded(context):
    timeout = context["executions"]["timeout"]
    if timeout.get("terminal_disposition") != "timeout":
        raise ValueError("timeout-effect boundedness scenario lacks timeout execution")
    if context["lifecycle_basis"]["timeout"].get("value") != "client_timeout":
        raise ValueError("timeout execution lacks observed client-timeout basis")
    if context["effects"]:
        raise ValueError("timeout-effect boundedness scenario contains independent EffectObservation")
    return timeout


def require_noncompleted_effect_bounded(context):
    timeout = require_timeout_effect_bounded(context)
    if timeout.get("terminal_disposition") not in {
        "failed",
        "timeout",
        "cancelled",
        "interrupted",
        "unknown",
    }:
        raise ValueError("non-completed boundedness scenario lacks non-completed disposition")
    return timeout


_execute_adapter_capture_case_before_batch29 = execute_adapter_capture_case


def execute_adapter_capture_case(row, case, materialized):
    check_id = row["planned_test_id"]
    expected_requirement = _BATCH29_LIFECYCLE_EFFECT_REQUIREMENTS.get(check_id)
    if expected_requirement is None:
        return _execute_adapter_capture_case_before_batch29(row, case, materialized)

    requirement_id = row["requirement_id"]
    if requirement_id != expected_requirement:
        raise NotImplementedError(f"{requirement_id}:{check_id}")

    receipt = primary_receipt(case, materialized)
    context = tool_lifecycle_effect_context(receipt)

    if check_id == "tool-execution-disposition-boundary-001":
        execution = require_runtime_observed_disposition(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            execution["id"],
        )
    elif check_id == "tool-completed-not-effect-001":
        execution = require_completed_effect_bounded(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            execution["id"],
            domain="claim",
            status="asserted",
            prohibited=[
                "P1:completed_tool_execution_proves_effect_or_outcome_success"
            ],
        )
    elif check_id == "tool-timeout-not-no-effect-001":
        execution = require_timeout_effect_bounded(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            execution["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:tool_timeout_proves_no_effect"],
        )
    elif check_id == "tool-noncompleted-not-no-effect-001":
        execution = require_noncompleted_effect_bounded(context)
        actual_finding = finding(
            requirement_id,
            check_id,
            receipt,
            execution["id"],
            domain="claim",
            status="asserted",
            prohibited=["P1:noncompleted_tool_execution_proves_no_effect"],
        )
    else:
        raise NotImplementedError(check_id)

    return {
        "findings": [actual_finding],
        "process_outcome": "completed",
        "completeness": {},
    }
