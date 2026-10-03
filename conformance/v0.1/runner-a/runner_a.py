#!/usr/bin/env python3
import argparse
import copy
import json
import sys
from pathlib import Path
from urllib.parse import unquote

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from semantic_executor import SUPPORTED_PLANNED_TESTS, execute_semantic_case
from vector_executor import execute_case_vector

ROOT = Path(__file__).resolve().parents[3]
CONF = ROOT / "conformance" / "v0.1"

PHASE_ORDER = [
    "schema_validate",
    "resolve_references",
    "graph_checks",
    "representation_checks",
    "privacy_checks",
    "integrity_checks",
    "claim_checks",
    "aggregate_report",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pointer_tokens(pointer):
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("invalid JSON Pointer")
    return [unquote(x).replace("~1", "/").replace("~0", "~") for x in pointer[1:].split("/")]


def resolve_pointer(document, pointer):
    value = document
    for token in pointer_tokens(pointer):
        if isinstance(value, list):
            if token == "-":
                raise KeyError("- is not readable")
            value = value[int(token)]
        elif isinstance(value, dict):
            value = value[token]
        else:
            raise KeyError(token)
    return value


def apply_patches(document, patches):
    value = copy.deepcopy(document)
    for patch in patches or []:
        op = patch["op"]
        tokens = pointer_tokens(patch["path"])
        if not tokens:
            raise ValueError("root patch is not supported")
        parent = value
        for token in tokens[:-1]:
            parent = parent[int(token)] if isinstance(parent, list) else parent[token]
        leaf = tokens[-1]
        if isinstance(parent, list):
            if op == "add":
                if leaf == "-":
                    parent.append(copy.deepcopy(patch["value"]))
                else:
                    index = int(leaf)
                    if index < 0 or index > len(parent):
                        raise IndexError(index)
                    parent.insert(index, copy.deepcopy(patch["value"]))
            elif op == "remove":
                parent.pop(int(leaf))
            elif op == "replace":
                parent[int(leaf)] = copy.deepcopy(patch["value"])
            else:
                raise ValueError(op)
        elif isinstance(parent, dict):
            if op == "add":
                parent[leaf] = copy.deepcopy(patch["value"])
            elif op == "remove":
                del parent[leaf]
            elif op == "replace":
                if leaf not in parent:
                    raise KeyError(leaf)
                parent[leaf] = copy.deepcopy(patch["value"])
            else:
                raise ValueError(op)
        else:
            raise TypeError("patch parent is scalar")
    return value


class SchemaRegistry:
    def __init__(self):
        resources = []
        for base in (ROOT / "schema" / "v0.1", CONF / "schema"):
            for path in sorted(base.glob("*.json")):
                schema = load_json(path)
                schema_id = schema.get("$id")
                if schema_id:
                    resources.append((schema_id, Resource.from_contents(schema)))
        self.registry = Registry().with_resources(resources)

    def validate(self, target, instance):
        wrapper = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": target,
        }
        validator = Draft202012Validator(wrapper, registry=self.registry)
        errors = sorted(
            validator.iter_errors(instance),
            key=lambda e: (list(e.absolute_path), list(e.absolute_schema_path), e.message),
        )
        return {
            "status": "valid" if not errors else "invalid",
            "error_classes": sorted({str(e.validator) for e in errors}),
            "errors": [
                {
                    "path": list(e.absolute_path),
                    "schema_path": list(e.absolute_schema_path),
                    "validator": str(e.validator),
                    "message": e.message,
                }
                for e in errors
            ],
        }


def load_suite_rows():
    manifest = load_json(CONF / "manifest.json")
    rows = []
    for rel in manifest["case_indexes"]:
        index = load_json(ROOT / rel)
        rows.extend(index["cases"])
    return rows


def materialize_case(case):
    materialized = {}
    for document in case["documents"]:
        source = document["source"]
        if "path" in source:
            base = load_json(ROOT / source["path"])
            value = copy.deepcopy(resolve_pointer(base, source.get("extract_pointer", "")))
        elif "inline" in source:
            value = copy.deepcopy(source["inline"])
        else:
            raise ValueError(f"unsupported source for {document['document_id']}")
        value = apply_patches(value, document.get("patches", []))
        materialized[document["document_id"]] = value
    return materialized


def recursive_subset(expected, actual):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and recursive_subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return all(any(recursive_subset(e, a) for a in actual) for e in expected)
    return expected == actual


def finding_matches(matcher, finding):
    for key, expected in matcher.items():
        if key == "subject_selector":
            if not recursive_subset(expected, finding.get("subject_scope", {})):
                return False
        elif key in {"evidence_bases", "prohibited_inferences"}:
            actual = finding.get(key, [])
            if not isinstance(actual, list) or not all(v in actual for v in expected):
                return False
        elif finding.get(key) != expected:
            return False
    return True


def compare_schema_results(expected, actual):
    failures = []
    exp = {x["document_id"]: x for x in expected}
    act = {x["document_id"]: x for x in actual}
    if set(exp) != set(act):
        failures.append({
            "code": "schema_result_document_set_mismatch",
            "expected": sorted(exp),
            "actual": sorted(act),
        })
        return failures
    for document_id, e in exp.items():
        a = act[document_id]
        if a.get("schema_target") != e.get("schema_target"):
            failures.append({"code": "schema_target_mismatch", "document_id": document_id})
        if a.get("status") != e.get("status"):
            failures.append({
                "code": "schema_status_mismatch",
                "document_id": document_id,
                "expected": e.get("status"),
                "actual": a.get("status"),
            })
        required_errors = e.get("error_classes", [])
        actual_errors = a.get("error_classes", [])
        if not all(x in actual_errors for x in required_errors):
            failures.append({
                "code": "schema_error_class_mismatch",
                "document_id": document_id,
                "expected_subset": required_errors,
                "actual": actual_errors,
            })
    return failures


def compare_findings(expected, actual):
    failures = []
    required = expected.get("required_findings", [])
    forbidden = expected.get("forbidden_findings", [])
    for matcher in required:
        if not any(finding_matches(matcher, finding) for finding in actual):
            failures.append({"code": "required_finding_missing", "matcher": matcher})
    for matcher in forbidden:
        if any(finding_matches(matcher, finding) for finding in actual):
            failures.append({"code": "forbidden_finding_present", "matcher": matcher})
    if expected.get("comparison_mode") == "exact_normative":
        unmatched = [
            finding for finding in actual
            if not any(finding_matches(matcher, finding) for matcher in required)
        ]
        if unmatched:
            failures.append({"code": "unexpected_normative_findings", "findings": unmatched})
    return failures


def compare_process_and_completeness(expected, actual):
    failures = []
    if "process_outcome" in expected and actual.get("process_outcome") != expected["process_outcome"]:
        failures.append({
            "code": "process_outcome_mismatch",
            "expected": expected["process_outcome"],
            "actual": actual.get("process_outcome"),
        })
    for key, value in (expected.get("completeness") or {}).items():
        if (actual.get("completeness") or {}).get(key) != value:
            failures.append({
                "code": "completeness_mismatch",
                "dimension": key,
                "expected": value,
                "actual": (actual.get("completeness") or {}).get(key),
            })
    return failures


def compare_vector_results(expected, actual):
    failures = []
    expected_results = expected.get("vector_results", [])
    exp = {(x["vector_id"], x["check"]): x["status"] for x in expected_results}
    act = {(x["vector_id"], x["check"]): x["status"] for x in actual}

    if len(act) != len(actual):
        failures.append({"code": "duplicate_actual_vector_result"})
        return failures

    for key, expected_status in exp.items():
        if key not in act:
            failures.append({
                "code": "required_vector_result_missing",
                "vector_id": key[0],
                "check": key[1],
            })
        elif act[key] != expected_status:
            failures.append({
                "code": "vector_status_mismatch",
                "vector_id": key[0],
                "check": key[1],
                "expected": expected_status,
                "actual": act[key],
            })

    if expected.get("comparison_mode") == "exact_normative":
        extra = sorted(set(act) - set(exp))
        if extra:
            failures.append({
                "code": "unexpected_vector_results",
                "results": [{"vector_id": v, "check": c} for v, c in extra],
            })
    return failures


def run_case(row, schemas):
    case = load_json(ROOT / row["case_path"])
    expected = load_json(ROOT / row["expected_result_path"])
    result = {
        "case_id": row["case_id"],
        "requirement_id": row["requirement_id"],
        "planned_test_id": row["planned_test_id"],
        "primary_enforcement": row["primary_enforcement"],
        "status": "fail",
        "failures": [],
        "actual": {
            "schema_results": [],
            "findings": [],
            "vector_results": [],
            "process_outcome": None,
            "completeness": {},
        },
    }
    try:
        materialized = materialize_case(case)
    except Exception as exc:
        result["failures"].append({"code": "materialization_error", "detail": str(exc)})
        return result

    phases = case.get("execution", {}).get("phases", [])
    ordered = [p for p in phases if p in PHASE_ORDER]
    if any(PHASE_ORDER.index(ordered[i]) > PHASE_ORDER.index(ordered[i + 1]) for i in range(len(ordered) - 1)):
        result["failures"].append({"code": "phase_order_error"})
        return result

    if "schema_validate" in phases:
        for document in case["documents"]:
            document_id = document["document_id"]
            validation = schemas.validate(document["schema_target"], materialized[document_id])
            result["actual"]["schema_results"].append({
                "document_id": document_id,
                "schema_target": document["schema_target"],
                "status": validation["status"],
                "error_classes": validation["error_classes"],
            })

    result["failures"].extend(compare_schema_results(
        expected.get("schema_results", []),
        result["actual"]["schema_results"],
    ))

    enforcement = row["primary_enforcement"]
    if enforcement == "direct_schema":
        result["failures"].extend(compare_findings(expected, []))
    elif enforcement == "deterministic_vector":
        vector_documents = [
            materialized[d["document_id"]]
            for d in case["documents"]
            if d["schema_target"] == "urn:c2atrace:conformance:v0.1:deterministic-vector"
        ]
        if len(vector_documents) != 1:
            result["failures"].append({
                "code": "vector_document_cardinality",
                "actual": len(vector_documents),
            })
        elif case.get("planned_test_ids") != [row["planned_test_id"]]:
            result["failures"].append({"code": "planned_test_join_mismatch"})
        else:
            try:
                result["actual"]["vector_results"] = execute_case_vector(
                    vector_documents[0],
                    row["planned_test_id"],
                    ROOT,
                )
            except Exception as exc:
                result["failures"].append({
                    "code": "vector_execution_error",
                    "detail": f"{type(exc).__name__}: {exc}",
                })
            result["failures"].extend(compare_vector_results(
                expected,
                result["actual"]["vector_results"],
            ))
            result["failures"].extend(compare_findings(expected, []))
    elif enforcement in {"semantic_verifier", "mixed_schema_semantic"}:
        if row["planned_test_id"] not in SUPPORTED_PLANNED_TESTS:
            result["failures"].append({"code": "semantic_executor_not_implemented"})
        else:
            try:
                semantic = execute_semantic_case(row, case, materialized)
                result["actual"]["findings"] = semantic["findings"]
                result["actual"]["process_outcome"] = semantic["process_outcome"]
                result["actual"]["completeness"] = semantic["completeness"]
            except Exception as exc:
                result["failures"].append({
                    "code": "semantic_execution_error",
                    "detail": f"{type(exc).__name__}: {exc}",
                })
            result["failures"].extend(compare_findings(
                expected,
                result["actual"]["findings"],
            ))
            result["failures"].extend(compare_process_and_completeness(
                expected,
                result["actual"],
            ))
    else:
        result["failures"].append({"code": "unknown_enforcement", "value": enforcement})

    if not result["failures"]:
        result["status"] = "pass"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--enforcement", action="append", choices=[
        "direct_schema", "mixed_schema_semantic", "semantic_verifier", "deterministic_vector"
    ])
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--primary-primitive", action="append")
    parser.add_argument("--batch-manifest")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    selected = load_suite_rows()
    if args.enforcement:
        selected = [x for x in selected if x["primary_enforcement"] in set(args.enforcement)]
    if args.case_id:
        selected = [x for x in selected if x["case_id"] in set(args.case_id)]
    batch_id = None
    selection_failures = []
    if args.primary_primitive:
        coverage = load_json(CONF / "primitives" / "coverage-matrix.json")
        wanted_requirements = {
            entry["requirement_id"]
            for entry in coverage["entries"]
            if entry["primary_primitive"] in set(args.primary_primitive)
        }
        selected = [x for x in selected if x["requirement_id"] in wanted_requirements]
    if args.batch_manifest:
        batch = load_json(ROOT / args.batch_manifest)
        batch_id = batch.get("batch_id")
        coverage = load_json(CONF / "primitives" / "coverage-matrix.json")
        primitive_requirements = {
            entry["requirement_id"]
            for entry in coverage["entries"]
            if entry["primary_primitive"] in set(batch.get("primary_primitives", []))
        }
        wanted_requirements = primitive_requirements | set(batch.get("additional_requirement_ids", []))
        selected = [x for x in selected if x["requirement_id"] in wanted_requirements]
        expected_count = batch.get("expected_case_count")
        if expected_count is not None and len(selected) != expected_count:
            selection_failures.append({
                "code": "batch_case_count_mismatch",
                "batch_id": batch_id,
                "expected": expected_count,
                "actual": len(selected),
            })

    schemas = SchemaRegistry()
    results = [run_case(row, schemas) for row in selected]
    passed = [r for r in results if r["status"] == "pass"]
    failed = [r for r in results if r["status"] == "fail"]
    by_enforcement = {}
    for result in results:
        bucket = by_enforcement.setdefault(
            result["primary_enforcement"],
            {"total": 0, "pass": 0, "fail": 0},
        )
        bucket["total"] += 1
        bucket[result["status"]] += 1

    report = {
        "runner": "C2ATrace v0.1 runner A",
        "implementation": "python-independent",
        "scope": {
            "selected_cases": len(results),
            "enforcements": sorted({r["primary_enforcement"] for r in results}),
            "batch_id": batch_id,
        },
        "aggregate": {
            "pass": len(passed),
            "fail": len(failed),
            "selection_failures": len(selection_failures),
            "by_enforcement": by_enforcement,
        },
        "selection_failures": selection_failures,
        "failed_cases": [
            {"case_id": r["case_id"], "failures": r["failures"]}
            for r in failed
        ],
        "case_results": results,
    }
    Path(args.output).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["aggregate"], sort_keys=True))

    if args.require_complete and (failed or selection_failures):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
