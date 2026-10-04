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
