#!/usr/bin/env python3


def records(receipt):
    return receipt.get("arp", {}).get("records", [])


def record_index(receipt):
    return {
        record["id"]: record
        for record in records(receipt)
        if isinstance(record, dict) and record.get("id")
    }


def ref_id(value):
    return value.get("id") if isinstance(value, dict) else None


def resolve_local(index, reference, expected_kind):
    if not isinstance(reference, dict) or reference.get("ref_type") != "local":
        raise ValueError(f"{expected_kind} reference is not local")
    target = index.get(ref_id(reference))
    if not isinstance(target, dict) or target.get("kind") != expected_kind:
        raise ValueError(f"{expected_kind} reference did not resolve to expected kind")
    if reference.get("expected_kind") not in {None, expected_kind}:
        raise ValueError(f"{expected_kind} reference declares wrong expected_kind")
    return target


def deny_decision_on_proposal(receipt):
    index = record_index(receipt)
    candidates = []
    for decision in records(receipt):
        if not isinstance(decision, dict):
            continue
        if decision.get("kind") != "ToolDecision" or decision.get("decision") != "deny":
            continue
        proposal = resolve_local(index, decision.get("subject"), "ToolProposal")
        if decision.get("run_id") != proposal.get("run_id"):
            raise ValueError("deny ToolDecision and ToolProposal changed run occurrence")
        candidates.append((decision, proposal))

    if len(candidates) != 1:
        raise ValueError(
            f"deny scenario requires one ToolDecision on ToolProposal, found {len(candidates)}"
        )
    return candidates[0]


def require_no_tool_invocation(receipt):
    invocations = [
        record
        for record in records(receipt)
        if isinstance(record, dict) and record.get("kind") == "ToolInvocation"
    ]
    if invocations:
        raise ValueError("ToolInvocation present in deny-without-invocation scenario")


def require_no_tool_execution(receipt):
    executions = [
        record
        for record in records(receipt)
        if isinstance(record, dict) and record.get("kind") == "ToolExecution"
    ]
    if executions:
        raise ValueError("ToolExecution present in deny-without-execution scenario")


def proposal_output_boundary(receipt):
    index = record_index(receipt)
    proposals = [
        record
        for record in records(receipt)
        if isinstance(record, dict) and record.get("kind") == "ToolProposal"
    ]
    if len(proposals) != 1:
        raise ValueError(
            f"proposal-only scenario requires one ToolProposal, found {len(proposals)}"
        )

    proposal = proposals[0]
    output = resolve_local(index, proposal.get("output"), "ModelOutput")

    if proposal.get("run_id") != output.get("run_id"):
        raise ValueError("ToolProposal and ModelOutput changed run occurrence")

    backrefs = []
    for reference in output.get("item_refs", []):
        if not isinstance(reference, dict) or reference.get("ref_type") != "local":
            continue
        if reference.get("id") != proposal.get("id"):
            continue
        if reference.get("expected_kind") not in {None, "ToolProposal"}:
            raise ValueError("ModelOutput proposal back-reference declares wrong expected_kind")
        backrefs.append(reference)

    if len(backrefs) != 1:
        raise ValueError(
            f"ModelOutput must contain one back-reference to ToolProposal, found {len(backrefs)}"
        )

    return proposal, output


def structured_json_pointer(region, expected_pointer):
    if not isinstance(region, dict) or region.get("region_kind") != "structured":
        return False
    path = region.get("path")
    return (
        isinstance(path, dict)
        and path.get("scheme") == "json_pointer"
        and path.get("value") == expected_pointer
    )


def resolve_json_pointer(value, pointer):
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("invalid JSON Pointer")
    current = value
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise ValueError(f"JSON Pointer token {token!r} missing")
            current = current[token]
        elif isinstance(current, list):
            if token == "-" or not token.isdigit():
                raise ValueError("JSON Pointer array index is invalid")
            index = int(token)
            if index < 0 or index >= len(current):
                raise ValueError("JSON Pointer array index out of bounds")
            current = current[index]
        else:
            raise ValueError("JSON Pointer descends through non-container value")
    return current


def tool_argument_model_provenance(receipt, pointer="/title"):
    index = record_index(receipt)
    proposal, _output = proposal_output_boundary(receipt)
    candidates = []

    for invocation in records(receipt):
        if not isinstance(invocation, dict) or invocation.get("kind") != "ToolInvocation":
            continue

        for provenance in invocation.get("argument_provenance", []):
            path = provenance.get("path") if isinstance(provenance, dict) else None
            if not (
                isinstance(path, dict)
                and path.get("scheme") == "json_pointer"
                and path.get("value") == pointer
            ):
                continue
            if provenance.get("classification") != "model_supplied":
                raise ValueError("selected tool argument provenance is not model_supplied")

            refs = provenance.get("derivations", [])
            if not isinstance(refs, list) or len(refs) != 1:
                raise ValueError("model_supplied argument requires exactly one Derivation reference")
            derivation = resolve_local(index, refs[0], "Derivation")

            target = derivation.get("target") or {}
            target_invocation = resolve_local(index, target.get("artifact"), "ToolInvocation")
            if target_invocation.get("id") != invocation.get("id"):
                raise ValueError("Derivation target is not the selected ToolInvocation")
            if target.get("representation_basis") != "tool_arguments_json":
                raise ValueError("Derivation target does not use tool_arguments_json")
            if not structured_json_pointer(target.get("region"), pointer):
                raise ValueError("Derivation target region does not match argument path")

            contributors = derivation.get("contributors", [])
            if not isinstance(contributors, list) or len(contributors) != 1:
                raise ValueError("model_supplied argument requires exactly one contributor")
            contributor = contributors[0]
            scope = contributor.get("scope") or {}
            contributor_proposal = resolve_local(index, scope.get("artifact"), "ToolProposal")
            if contributor_proposal.get("id") != proposal.get("id"):
                raise ValueError("Derivation contributor is not the selected ToolProposal")
            if scope.get("representation_basis") != "tool_proposal_arguments_json":
                raise ValueError("Derivation contributor does not use tool_proposal_arguments_json")
            if not structured_json_pointer(scope.get("region"), pointer):
                raise ValueError("Derivation contributor region does not match argument path")
            if not structured_json_pointer(contributor.get("output_region"), pointer):
                raise ValueError("Derivation contributor output_region does not match argument path")

            if derivation.get("precision") != "exact":
                raise ValueError("positive model-supplied argument Derivation is not exact")
            if derivation.get("unknown_origin_regions"):
                raise ValueError("positive model-supplied argument Derivation has unknown origin")

            transform = resolve_local(index, derivation.get("transform"), "Transform")
            prep_transform = resolve_local(
                index, invocation.get("preparation_transform"), "Transform"
            )
            if prep_transform.get("id") != transform.get("id"):
                raise ValueError("Derivation transform differs from ToolInvocation preparation_transform")

            input_matches = []
            for item in transform.get("inputs", []):
                if not isinstance(item, dict):
                    continue
                artifact = item.get("artifact")
                if ref_id(artifact) != proposal.get("id"):
                    continue
                resolved = resolve_local(index, artifact, "ToolProposal")
                if resolved.get("id") != proposal.get("id"):
                    continue
                if item.get("usage_role") not in {"data", "mixed"}:
                    raise ValueError("proposal Transform input is not content-contributing")
                input_matches.append(item)
            if len(input_matches) != 1:
                raise ValueError("Transform must contain one contributing ToolProposal input")

            generated_matches = []
            for generated in transform.get("generated", []):
                if ref_id(generated) != invocation.get("id"):
                    continue
                resolved = resolve_local(index, generated, "ToolInvocation")
                if resolved.get("id") == invocation.get("id"):
                    generated_matches.append(generated)
            if len(generated_matches) != 1:
                raise ValueError("Transform must generate the selected ToolInvocation")

            run_ids = {
                proposal.get("run_id"),
                invocation.get("run_id"),
                derivation.get("run_id"),
                transform.get("run_id"),
            }
            if None in run_ids or len(run_ids) != 1:
                raise ValueError("tool argument provenance chain changed run occurrence")

            proposal_args = proposal.get("arguments") or {}
            invocation_args = invocation.get("arguments") or {}
            if proposal_args.get("representation_kind") != "json":
                raise ValueError("ToolProposal arguments are not JSON")
            if invocation_args.get("representation_kind") != "json":
                raise ValueError("ToolInvocation arguments are not JSON")
            proposal_value = resolve_json_pointer(proposal_args.get("value"), pointer)
            invocation_value = resolve_json_pointer(invocation_args.get("value"), pointer)
            if proposal_value != invocation_value:
                raise ValueError("derived ToolInvocation argument does not match ToolProposal value")

            candidates.append((proposal, invocation, derivation, transform))

    if len(candidates) != 1:
        raise ValueError(
            f"expected one model_supplied provenance chain at {pointer}, found {len(candidates)}"
        )
    return candidates[0]


def tool_argument_json_pointer_paths(receipt):
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
            f"argument-path scenario requires one ToolInvocation with provenance, found {len(invocations)}"
        )

    invocation = invocations[0]
    arguments = invocation.get("arguments") or {}
    if arguments.get("representation_kind") != "json":
        raise ValueError("ToolInvocation arguments are not JSON")

    value = arguments.get("value")
    checked = []
    for provenance in invocation.get("argument_provenance", []):
        if not isinstance(provenance, dict):
            raise ValueError("argument_provenance entry is not an object")
        path = provenance.get("path")
        if not isinstance(path, dict):
            raise ValueError("argument_provenance path is missing")
        if path.get("scheme") != "json_pointer":
            raise ValueError("argument_provenance path scheme is not json_pointer")
        pointer = path.get("value")
        if not isinstance(pointer, str):
            raise ValueError("argument_provenance JSON Pointer is not a string")

        resolved_value = resolve_json_pointer(value, pointer)
        checked.append(
            {
                "path": pointer,
                "classification": provenance.get("classification"),
                "resolved_value": resolved_value,
            }
        )

    if not checked:
        raise ValueError("ToolInvocation has no argument_provenance entries")
    return invocation, checked
