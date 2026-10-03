#!/usr/bin/env python3
import argparse, copy, json, os, re, sys
from pathlib import Path
from urllib.parse import unquote

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
CONF = ROOT / "conformance" / "v0.1"
FAMILIES = ["tm","claim","graph","src","drv","req","out","tool","trust","taint","priv","rcpt","intg","pad","tad","vfy"]
PHASE_ORDER = {k:i for i,k in enumerate(["schema_validate","resolve_references","graph_checks","representation_checks","privacy_checks","integrity_checks","claim_checks","aggregate_report"])}
RUNNER_SCOPE_KEYS = {"subject_kind","receipt_id","object_id","expected_kind","envelope_id","profile_id","report_id","vector_id","linked_receipt_id","path","dropped_path","slot","compared_object_id","metadata_name","event_semantics","capture_extent","origin"}
EXPECTED_TOP = {"case_id","comparison_mode","schema_results","required_findings","forbidden_findings","envelope_results","process_outcome","completeness","notes","vector_results"}
MATCHER_KEYS = {"requirement_id","check_id","subject_selector","domain","status","evidence_bases","prohibited_inferences","reason_code"}
SCHEMA_RESULT_KEYS = {"document_id","schema_target","status","error_classes"}
VECTOR_KEYS = {"vector_id","check","status"}
ENVELOPE_KEYS = {"envelope_id","key_resolution","signature_status","arp_binding","key_ref"}
PROCESS = {"completed","invalidity_detected","incomplete_evaluation","operational_error"}
COMPLETE = {"established","unknown","unverified","unsupported"}

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",",":"), ensure_ascii=False)

def fail(rec, code, **detail):
    rec["failures"].append({"code": code, **detail})

def warn(rec, code, **detail):
    rec["warnings"].append({"code": code, **detail})

def ptr_tokens(ptr):
    if ptr == "": return []
    if not isinstance(ptr, str) or not ptr.startswith("/"):
        raise ValueError("JSON Pointer must be empty or start with /")
    return [unquote(x).replace("~1","/").replace("~0","~") for x in ptr[1:].split("/")]

def resolve_ptr(doc, ptr):
    cur = doc
    for tok in ptr_tokens(ptr):
        if isinstance(cur, list):
            if tok == "-": raise KeyError("- is not readable")
            cur = cur[int(tok)]
        elif isinstance(cur, dict):
            cur = cur[tok]
        else:
            raise KeyError(tok)
    return cur

def patch(doc, ops):
    out = copy.deepcopy(doc)
    for op in ops or []:
        typ, path = op["op"], op["path"]
        toks = ptr_tokens(path)
        if not toks: raise ValueError("root patch not allowed by v0.1 case schema")
        parent = out
        for tok in toks[:-1]:
            parent = parent[int(tok)] if isinstance(parent, list) else parent[tok]
        leaf = toks[-1]
        if isinstance(parent, list):
            if typ == "add":
                if leaf == "-": parent.append(copy.deepcopy(op["value"]))
                else: parent.insert(int(leaf), copy.deepcopy(op["value"]))
            elif typ == "remove": parent.pop(int(leaf))
            elif typ == "replace": parent[int(leaf)] = copy.deepcopy(op["value"])
            else: raise ValueError(typ)
        elif isinstance(parent, dict):
            if typ == "add": parent[leaf] = copy.deepcopy(op["value"])
            elif typ == "remove": del parent[leaf]
            elif typ == "replace":
                if leaf not in parent: raise KeyError(leaf)
                parent[leaf] = copy.deepcopy(op["value"])
            else: raise ValueError(typ)
        else: raise TypeError("patch parent is scalar")
    return out

def collect_ids(v, receipt_ids, object_ids, envelope_ids, profile_ids, secrets):
    if isinstance(v, dict):
        for k,x in v.items():
            if isinstance(x, str):
                if k == "receipt_id": receipt_ids.add(x)
                if k == "envelope_id": envelope_ids.add(x)
                if k == "profile_id": profile_ids.add(x)
                if k == "id" or k.endswith("_id"): object_ids.add(x)
                if "secret" in k.lower() or "private_key" in k.lower(): secrets.add(x)
            collect_ids(x, receipt_ids, object_ids, envelope_ids, profile_ids, secrets)
    elif isinstance(v, list):
        for x in v: collect_ids(x, receipt_ids, object_ids, envelope_ids, profile_ids, secrets)

def schema_registry():
    reg = {}
    for base in [ROOT/"schema"/"v0.1", CONF/"schema"]:
        for p in base.glob("*.json"):
            try:
                j = load(p)
                if isinstance(j, dict) and isinstance(j.get("$id"), str): reg[j["$id"]] = (p,j)
            except Exception:
                pass
    return reg

def conformance_validators():
    schemas = {}
    resources = []
    for p in (CONF/"schema").glob("*.json"):
        j = load(p)
        if isinstance(j, dict) and isinstance(j.get("$id"), str):
            schemas[p.name] = j
            resources.append((j["$id"], Resource.from_contents(j)))
    registry = Registry().with_resources(resources)
    return (
        Draft202012Validator(schemas["case.schema.json"], registry=registry),
        Draft202012Validator(schemas["expected-result.schema.json"], registry=registry),
    )

def resolve_schema_target(target, reg):
    base, sep, frag = target.partition("#")
    if base not in reg: raise KeyError(base)
    if not sep or frag == "": return reg[base][1]
    if frag.startswith("/"): return resolve_ptr(reg[base][1], unquote(frag))
    raise ValueError("unsupported non-pointer fragment")

def verifier_rules():
    v = load(ROOT/"schema"/"v0.1"/"verifier.schema.json")
    vf = v["$defs"]["VerificationFinding"]
    ds = {}
    for branch in vf.get("allOf", []):
        dom = branch.get("if",{}).get("properties",{}).get("domain",{}).get("const")
        statuses = branch.get("then",{}).get("properties",{}).get("status",{}).get("enum")
        if dom and statuses: ds[dom] = set(statuses)
    variants = []
    for s in v["$defs"]["FindingSubject"]["oneOf"]:
        variants.append(set(s.get("properties",{})))
    return ds, variants, re.compile(v["$defs"]["EvidenceBasis"]["pattern"]), re.compile(v["$defs"]["ProhibitedInference"]["pattern"])

def selector_representable(sel, variants):
    if not isinstance(sel, dict) or not sel: return False
    if not set(sel) <= RUNNER_SCOPE_KEYS: return False
    return all(v is None or isinstance(v, (str, int, float, bool)) for v in sel.values())

def selector_addressable(sel, receipt_ids, object_ids, envelope_ids, profile_ids, harness):
    if not sel: return True
    if "receipt_id" in sel and sel["receipt_id"] not in receipt_ids: return False
    if "object_id" in sel and sel["object_id"] not in object_ids: return False
    if "envelope_id" in sel and sel["envelope_id"] not in envelope_ids: return False
    profiles = set(profile_ids) | set((harness or {}).get("supported_profiles",[]))
    if "profile_id" in sel and sel["profile_id"] not in profiles: return False
    return True

def expected_shape(e, rec, ds, variants, ev_re, pi_re):
    if not isinstance(e, dict): fail(rec,"expected_not_object"); return
    extra = sorted(set(e)-EXPECTED_TOP)
    if extra: fail(rec,"expected_extra_keys", keys=extra)
    for k in ["case_id","comparison_mode","schema_results","required_findings","forbidden_findings"]:
        if k not in e: fail(rec,"expected_missing_required", field=k)
    if e.get("comparison_mode") not in {"contains_normative","exact_normative"}: fail(rec,"comparison_mode_invalid")
    for k in ["schema_results","required_findings","forbidden_findings"]:
        if not isinstance(e.get(k), list): fail(rec,"expected_array_invalid", field=k)
    for s in e.get("schema_results",[]) if isinstance(e.get("schema_results"),list) else []:
        if not isinstance(s,dict): fail(rec,"schema_result_not_object"); continue
        extra = sorted(set(s)-SCHEMA_RESULT_KEYS)
        if extra: fail(rec,"schema_result_extra_keys", keys=extra)
        if not isinstance(s.get("document_id"),str) or not s.get("document_id"): fail(rec,"schema_result_document_id_invalid")
        if s.get("status") not in {"valid","invalid"}: fail(rec,"schema_result_status_invalid")
        if "error_classes" in s and (not isinstance(s["error_classes"],list) or len(s["error_classes"]) != len(set(s["error_classes"]))): fail(rec,"schema_result_error_classes_invalid")
    for which in ["required_findings","forbidden_findings"]:
        arr = e.get(which,[]) if isinstance(e.get(which),list) else []
        if len({canon(x) for x in arr}) != len(arr): fail(rec,"duplicate_matcher", collection=which)
        for m in arr:
            if not isinstance(m,dict): fail(rec,"matcher_not_object", collection=which); continue
            extra = sorted(set(m)-MATCHER_KEYS)
            if extra: fail(rec,"matcher_noncomparable_fields", collection=which, keys=extra)
            for k in ["requirement_id","domain","status"]:
                if k not in m: fail(rec,"matcher_missing_required", collection=which, field=k)
            if m.get("domain") not in ds or m.get("status") not in ds.get(m.get("domain"),set()): fail(rec,"matcher_domain_status_invalid", domain=m.get("domain"), status=m.get("status"))
            if "subject_selector" in m and not selector_representable(m["subject_selector"], variants): fail(rec,"subject_selector_unrepresentable", selector=m["subject_selector"])
            if "evidence_bases" in m:
                vals=m["evidence_bases"]
                if not isinstance(vals,list) or len(vals)!=len(set(vals)) or any(not isinstance(x,str) or not ev_re.fullmatch(x) for x in vals): fail(rec,"evidence_bases_unbounded")
            if "prohibited_inferences" in m:
                vals=m["prohibited_inferences"]
                if not isinstance(vals,list) or len(vals)!=len(set(vals)) or any(not isinstance(x,str) or not pi_re.fullmatch(x) for x in vals): fail(rec,"prohibited_inferences_unbounded")
    req=e.get("required_findings",[]) if isinstance(e.get("required_findings"),list) else []
    forb=e.get("forbidden_findings",[]) if isinstance(e.get("forbidden_findings"),list) else []
    for a in req:
        if not isinstance(a,dict): continue
        for b in forb:
            if not isinstance(b,dict): continue
            if all(k in a and a[k]==v for k,v in b.items()): fail(rec,"required_forbidden_contradiction", required=a, forbidden=b)
    for v in e.get("vector_results",[]) or []:
        if not isinstance(v,dict) or set(v)-VECTOR_KEYS: fail(rec,"vector_result_shape_invalid")
        elif not all(isinstance(v.get(k),str) and v.get(k) for k in ["vector_id","check"]) or v.get("status") not in {"matched","mismatched","valid","invalid"}: fail(rec,"vector_result_shape_invalid")
    for v in e.get("envelope_results",[]) or []:
        if not isinstance(v,dict) or set(v)-ENVELOPE_KEYS or not isinstance(v.get("envelope_id"),str) or not v.get("envelope_id"): fail(rec,"envelope_result_shape_invalid")
    if "process_outcome" in e and e["process_outcome"] not in PROCESS: fail(rec,"process_outcome_invalid")
    if "completeness" in e:
        c=e["completeness"]
        if not isinstance(c,dict) or set(c)-{"package_inventory","reference_closure","runtime_history"} or any(x not in COMPLETE for x in c.values()): fail(rec,"completeness_shape_invalid")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output", required=True); args=ap.parse_args()
    reg=schema_registry(); ds,variants,ev_re,pi_re=verifier_rules()
    case_validator, expected_validator = conformance_validators()
    rows=[]; meta=[]
    for fam in FAMILIES:
        idx=load(CONF/"index"/f"{fam}.json"); tx=load(ROOT/"traceability"/"v0.1"/f"{fam}.json")
        if idx.get("count") != len(idx.get("cases",[])): meta.append({"code":"index_count","family":fam})
        if tx.get("count") != len(tx.get("requirements",[])): meta.append({"code":"trace_count","family":fam})
        tm={r["id"]:r for r in tx.get("requirements",[])}
        for r in idx.get("cases",[]):
            t=tm.get(r["requirement_id"])
            if not t: meta.append({"code":"trace_requirement_missing","case_id":r["case_id"]})
            else:
                if t.get("planned_test") != r.get("planned_test_id"): meta.append({"code":"planned_test_index_trace","case_id":r["case_id"]})
                if t.get("primary_enforcement") != r.get("primary_enforcement"): meta.append({"code":"enforcement_index_trace","case_id":r["case_id"]})
            rows.append(r)
    if len(rows) != 907: meta.append({"code":"case_count","actual":len(rows),"expected":907})
    if len({r["case_id"] for r in rows}) != len(rows): meta.append({"code":"duplicate_case_id"})
    if len({r["requirement_id"] for r in rows}) != len(rows): meta.append({"code":"duplicate_requirement_mapping"})

    results=[]
    for r in rows:
        rec={"case_id":r["case_id"],"requirement_id":r["requirement_id"],"planned_test_id":r["planned_test_id"],"primary_enforcement":r["primary_enforcement"],"case_path":r["case_path"],"expected_result_path":r["expected_result_path"],"failures":[],"warnings":[]}
        cp=ROOT/r["case_path"]; ep=ROOT/r["expected_result_path"]
        if not cp.is_file(): fail(rec,"case_file_missing",path=r["case_path"]); results.append(rec); continue
        if not ep.is_file(): fail(rec,"expected_file_missing",path=r["expected_result_path"]); results.append(rec); continue
        try: c=load(cp)
        except Exception as ex: fail(rec,"case_json_parse",detail=str(ex)); results.append(rec); continue
        try: e=load(ep)
        except Exception as ex: fail(rec,"expected_json_parse",detail=str(ex)); results.append(rec); continue
        for err in sorted(case_validator.iter_errors(c), key=lambda x: str(list(x.absolute_path)))[:10]:
            fail(rec,"case_schema_invalid",path=list(err.absolute_path),validator=err.validator)
        for err in sorted(expected_validator.iter_errors(e), key=lambda x: str(list(x.absolute_path)))[:10]:
            fail(rec,"expected_result_schema_invalid",path=list(err.absolute_path),validator=err.validator)
        if c.get("case_id") != r["case_id"]: fail(rec,"case_id_join")
        if c.get("requirement_ids") != [r["requirement_id"]]: fail(rec,"requirement_join",actual=c.get("requirement_ids"))
        if c.get("planned_test_ids") != [r["planned_test_id"]]: fail(rec,"planned_test_join",actual=c.get("planned_test_ids"))
        if c.get("primary_enforcement") != r["primary_enforcement"]: fail(rec,"enforcement_join")
        if c.get("status") != r["status"]: warn(rec,"status_layer_differs",case_status=c.get("status"),index_status=r["status"])
        if c.get("expected_result") != r["expected_result_path"]: fail(rec,"expected_path_join")
        if e.get("case_id") != r["case_id"]: fail(rec,"expected_case_id_join")
        expected_shape(e,rec,ds,variants,ev_re,pi_re)

        docs=c.get("documents",[]) if isinstance(c.get("documents"),list) else []
        rec["input_documents"] = [
            {
                "document_id": d.get("document_id"),
                "role": d.get("role"),
                "source_kind": "path" if isinstance(d.get("source"),dict) and "path" in d["source"] else "inline",
                "source_path": d.get("source",{}).get("path") if isinstance(d.get("source"),dict) else None,
                "extract_pointer": d.get("source",{}).get("extract_pointer") if isinstance(d.get("source"),dict) else None,
                "patch_count": len(d.get("patches",[]) or []),
                "schema_target": d.get("schema_target"),
            }
            for d in docs if isinstance(d,dict)
        ]
        ids=[d.get("document_id") for d in docs if isinstance(d,dict)]
        if len(ids)!=len(set(ids)): fail(rec,"duplicate_document_id")
        material={}; receipt_ids=set(); object_ids=set(); envelope_ids=set(); profile_ids=set(); secrets=set()
        for d in docs:
            if not isinstance(d,dict): fail(rec,"document_not_object"); continue
            did=d.get("document_id"); src=d.get("source") or {}
            if "path" in src:
                sp=ROOT/src["path"]
                if not sp.is_file(): fail(rec,"source_missing",document_id=did,path=src["path"]); continue
                try: base=load(sp)
                except Exception as ex: fail(rec,"source_json_parse",document_id=did,detail=str(ex)); continue
                try:
                    val=copy.deepcopy(resolve_ptr(base,src.get("extract_pointer","")))
                    val=patch(val,d.get("patches",[])); material[did]=val
                    collect_ids(val,receipt_ids,object_ids,envelope_ids,profile_ids,secrets)
                except Exception as ex: fail(rec,"materialization_failed",document_id=did,detail=str(ex))
            elif "inline" in src:
                try:
                    val=copy.deepcopy(src["inline"])
                    val=patch(val,d.get("patches",[])); material[did]=val
                    collect_ids(val,receipt_ids,object_ids,envelope_ids,profile_ids,secrets)
                except Exception as ex: fail(rec,"materialization_failed",document_id=did,detail=str(ex))
            else: fail(rec,"source_invalid",document_id=did)
            target=d.get("schema_target")
            try: resolve_schema_target(target,reg)
            except Exception as ex: fail(rec,"schema_target_unresolved",document_id=did,target=target,detail=str(ex))

        phases=(c.get("execution") or {}).get("phases",[])
        if len(phases)!=len(set(phases)): fail(rec,"duplicate_phase")
        if any(x not in PHASE_ORDER and x != "vector_checks" for x in phases): fail(rec,"phase_unknown")
        ordered=[x for x in phases if x in PHASE_ORDER]
        if any(PHASE_ORDER[ordered[i]]>PHASE_ORDER[ordered[i+1]] for i in range(len(ordered)-1)): fail(rec,"phase_order")
        rec["phases"] = phases
        h=c.get("harness")
        rec["harness"] = {
            "present": isinstance(h,dict),
            "primary_documents": list((h or {}).get("primary_documents",[]) or []) if isinstance(h,dict) else [],
            "resolution_set": list((h or {}).get("resolution_set",[]) or []) if isinstance(h,dict) else [],
            "external_evidence": list((h or {}).get("external_evidence",[]) or []) if isinstance(h,dict) else [],
        }
        if r["primary_enforcement"] in {"semantic_verifier","mixed_schema_semantic"} and not isinstance(h,dict): fail(rec,"harness_missing")
        if isinstance(h,dict):
            for key in ["primary_documents","resolution_set","external_evidence"]:
                for x in h.get(key,[]) or []:
                    if x not in ids: fail(rec,"harness_document_ref_dangling",field=key,value=x)
            profile_ids.update(h.get("supported_profiles",[]) or [])
            for cap in h.get("hmac_capabilities",[]) or []:
                if isinstance(cap,dict) and isinstance(cap.get("secret_hex"),str): secrets.add(cap["secret_hex"])

        for s in e.get("schema_results",[]) if isinstance(e.get("schema_results"),list) else []:
            if not isinstance(s,dict): continue
            did=s.get("document_id")
            if did not in ids: fail(rec,"schema_result_document_dangling",document_id=did)
            else:
                d=next((x for x in docs if x.get("document_id")==did),None)
                if s.get("schema_target") and d and s["schema_target"] != d.get("schema_target"): fail(rec,"schema_result_target_mismatch",document_id=did)
        allm=[]
        for key in ["required_findings","forbidden_findings"]:
            if isinstance(e.get(key),list): allm += [m for m in e[key] if isinstance(m,dict)]
        target=[m for m in allm if m.get("requirement_id")==r["requirement_id"]]
        for m in allm:
            sel=m.get("subject_selector")
            if isinstance(sel,dict) and not selector_representable(sel,variants): fail(rec,"subject_selector_scope_unbounded",selector=sel)
        enf=r["primary_enforcement"]
        if enf=="semantic_verifier" and not target: fail(rec,"target_matcher_missing")
        if enf=="mixed_schema_semantic" and (not e.get("schema_results") or not target): fail(rec,"mixed_layer_coverage_incomplete")
        if enf=="direct_schema" and not e.get("schema_results"): fail(rec,"direct_schema_coverage_incomplete")
        if enf=="deterministic_vector" and not e.get("vector_results"): fail(rec,"vector_coverage_incomplete")
        if enf in {"semantic_verifier","mixed_schema_semantic"} and e.get("comparison_mode")=="exact_normative": warn(rec,"exact_normative_semantic_scope")
        et=canon(e)
        for s in secrets:
            if s and s in et: fail(rec,"secret_leaked_to_expected")
        rec["matcher_count"] = len(allm)
        rec["required_matcher_count"] = len(e.get("required_findings",[]) or [])
        rec["forbidden_matcher_count"] = len(e.get("forbidden_findings",[]) or [])
        rec["target_matcher_count"] = len(target)
        rec["comparison_mode"] = e.get("comparison_mode")
        rec["status"] = "pass" if not rec["failures"] else "fail"
        results.append(rec)

    for rec in results:
        rec.setdefault("status","pass" if not rec["failures"] else "fail")
    fails=[r for r in results if r["status"]=="fail"]
    warns=[r for r in results if r["warnings"]]
    counts={}
    for r in results:
        x=counts.setdefault(r["primary_enforcement"],{"total":0,"pass":0,"fail":0})
        x["total"]+=1; x[r["status"]]+=1
    comparison_modes={}
    for r in results:
        m=r.get("comparison_mode")
        comparison_modes[m]=comparison_modes.get(m,0)+1
    matcher_counts={
        "total":sum(r.get("matcher_count",0) or 0 for r in results),
        "required":sum(r.get("required_matcher_count",0) or 0 for r in results),
        "forbidden":sum(r.get("forbidden_matcher_count",0) or 0 for r in results),
        "target_requirement":sum(r.get("target_matcher_count",0) or 0 for r in results),
    }
    materialization_counts={
        "documents":sum(len(r.get("input_documents",[])) for r in results),
        "path_sources":sum(1 for r in results for d in r.get("input_documents",[]) if d.get("source_kind")=="path"),
        "inline_sources":sum(1 for r in results for d in r.get("input_documents",[]) if d.get("source_kind")=="inline"),
        "extract_pointers":sum(1 for r in results for d in r.get("input_documents",[]) if d.get("extract_pointer") is not None),
        "patched_documents":sum(1 for r in results for d in r.get("input_documents",[]) if d.get("patch_count",0)>0),
        "patch_operations":sum(d.get("patch_count",0) for r in results for d in r.get("input_documents",[])),
    }
    report={
      "audit":"C2ATrace v0.1 P5 expected VerificationFinding matcher coverage audit",
      "baseline_commit":"f0ecc83f9adce66f77860173b34dc0ddaca5af82",
      "audited_commit":os.environ.get("GITHUB_SHA"),
      "scope":{"requirements":907,"cases":907},
      "checks":["case_schema_validation","expected_result_schema_validation","index_trace_case_expected_join","deterministic_source_materialization","json_pointer_resolution","ordered_patch_application","schema_target_resolution","phase_legality_and_order","harness_document_reference_closure","expected_result_machine_shape","domain_status_legality","normalized_subject_scope_key_boundedness","evidence_basis_and_prohibited_inference_bounds","enforcement_layer_coverage","required_forbidden_noncontradiction","secret_nonleakage"],
      "aggregate":{"meta_failures":len(meta),"case_pass":len(results)-len(fails),"case_fail":len(fails),"case_warn":len(warns),"by_enforcement":counts,"comparison_modes":comparison_modes,"matchers":matcher_counts,"materialization":materialization_counts},
      "meta_failures":meta,
      "failed_cases":[{"case_id":r["case_id"],"failures":r["failures"]} for r in fails],
      "warning_cases":[{"case_id":r["case_id"],"warnings":r["warnings"]} for r in warns],
      "case_results":[{"case_id":r["case_id"],"requirement_id":r["requirement_id"],"planned_test_id":r["planned_test_id"],"primary_enforcement":r["primary_enforcement"],"case_path":r.get("case_path"),"expected_result_path":r.get("expected_result_path"),"status":r["status"],"comparison_mode":r.get("comparison_mode"),"matcher_count":r.get("matcher_count"),"required_matcher_count":r.get("required_matcher_count"),"forbidden_matcher_count":r.get("forbidden_matcher_count"),"target_matcher_count":r.get("target_matcher_count"),"input_documents":r.get("input_documents",[]),"phases":r.get("phases",[]),"harness":r.get("harness")} for r in results]
    }
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report["aggregate"],sort_keys=True))
    return 2 if meta or fails else 0

if __name__=="__main__": sys.exit(main())
