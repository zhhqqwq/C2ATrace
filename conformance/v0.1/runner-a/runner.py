#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import hmac
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
CONF = ROOT / "conformance" / "v0.1"
FAMILIES = ["tm","claim","graph","src","drv","req","out","tool","trust","taint","priv","rcpt","intg","pad","tad","vfy"]
SUPPORTED_ENFORCEMENTS = {"direct_schema", "deterministic_vector"}


class RunnerError(Exception):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))


def _assert_jcs_value(value: Any) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        raise RunnerError("Runner A baseline JCS supports current integer-only vector numbers; float support is not yet implemented")
    if isinstance(value, list):
        for item in value:
            _assert_jcs_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RunnerError("JCS object keys must be strings")
            if any(ord(ch) > 0x7F for ch in key):
                raise RunnerError("Runner A baseline JCS key ordering is limited to ASCII keys")
            _assert_jcs_value(item)
        return
    raise RunnerError(f"unsupported JCS value type: {type(value).__name__}")


def jcs_bytes(value: Any) -> bytes:
    _assert_jcs_value(value)
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return text.encode("utf-8")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hmac_sha256(secret: bytes, data: bytes) -> bytes:
    return hmac.new(secret, data, hashlib.sha256).digest()


def pointer_tokens(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise RunnerError("JSON Pointer must be empty or begin with /")
    return [unquote(x).replace("~1", "/").replace("~0", "~") for x in pointer[1:].split("/")]


def resolve_pointer(value: Any, pointer: str) -> Any:
    cur = value
    for tok in pointer_tokens(pointer):
        if isinstance(cur, list):
            if tok == "-":
                raise RunnerError("- cannot be dereferenced")
            cur = cur[int(tok)]
        elif isinstance(cur, dict):
            cur = cur[tok]
        else:
            raise RunnerError(f"pointer descends through scalar at {tok!r}")
    return cur


def apply_patches(value: Any, patches: list[dict[str, Any]]) -> Any:
    out = copy.deepcopy(value)
    for patch in patches:
        op = patch["op"]
        toks = pointer_tokens(patch["path"])
        if not toks:
            raise RunnerError("root patch is outside the v0.1 case patch subset")
        parent = out
        for tok in toks[:-1]:
            parent = parent[int(tok)] if isinstance(parent, list) else parent[tok]
        leaf = toks[-1]
        if isinstance(parent, list):
            if op == "add":
                if leaf == "-":
                    parent.append(copy.deepcopy(patch["value"]))
                else:
                    parent.insert(int(leaf), copy.deepcopy(patch["value"]))
            elif op == "remove":
                parent.pop(int(leaf))
            elif op == "replace":
                parent[int(leaf)] = copy.deepcopy(patch["value"])
            else:
                raise RunnerError(f"unsupported patch op {op!r}")
        elif isinstance(parent, dict):
            if op == "add":
                parent[leaf] = copy.deepcopy(patch["value"])
            elif op == "remove":
                del parent[leaf]
            elif op == "replace":
                if leaf not in parent:
                    raise RunnerError(f"replace target missing: {patch['path']}")
                parent[leaf] = copy.deepcopy(patch["value"])
            else:
                raise RunnerError(f"unsupported patch op {op!r}")
        else:
            raise RunnerError(f"patch parent is scalar: {patch['path']}")
    return out


def materialize_document(spec: dict[str, Any]) -> Any:
    source = spec["source"]
    if "path" in source:
        base = load_json(ROOT / source["path"])
        value = copy.deepcopy(resolve_pointer(base, source.get("extract_pointer", "")))
    elif "inline" in source:
        value = copy.deepcopy(source["inline"])
    else:
        raise RunnerError("document source has neither path nor inline")
    return apply_patches(value, spec.get("patches", []))


@dataclass
class SchemaRegistry:
    registry: Registry

    @classmethod
    def build(cls) -> "SchemaRegistry":
        resources: list[tuple[str, Resource]] = []
        for folder in (ROOT / "schema" / "v0.1", CONF / "schema"):
            for path in sorted(folder.glob("*.json")):
                doc = load_json(path)
                schema_id = doc.get("$id") if isinstance(doc, dict) else None
                if isinstance(schema_id, str):
                    resources.append((schema_id, Resource.from_contents(doc)))
        return cls(Registry().with_resources(resources))

    def validate(self, instance: Any, target: str) -> dict[str, Any]:
        wrapper = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": target}
        validator = Draft202012Validator(wrapper, registry=self.registry)
        errors = list(validator.iter_errors(instance))
        result: dict[str, Any] = {"status": "valid" if not errors else "invalid"}
        if errors:
            result["error_classes"] = sorted({str(e.validator) for e in errors})
        return result


def signing_statement(envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": "C2ATrace/v0.1/ReceiptSignature",
        "receipt_id": envelope["receipt_id"],
        "payload_digest": envelope["payload_digest"],
        "canonicalization_profile": envelope["canonicalization_profile"],
        "digest_algorithm": envelope["digest_algorithm"],
        "signature_profile": envelope["signature_profile"],
        "key_ref": envelope["key_ref"],
        "envelope_id": envelope["id"],
        "signed_metadata": envelope.get("signed_metadata", {}),
    }


def verify_ed25519(public_key_b64u: str, message: bytes, signature_b64u: str) -> bool:
    key = Ed25519PublicKey.from_public_bytes(b64u_decode(public_key_b64u))
    try:
        key.verify(b64u_decode(signature_b64u), message)
        return True
    except InvalidSignature:
        return False


def verify_envelope(envelope: dict[str, Any], public_key_b64u: str) -> bool:
    return verify_ed25519(public_key_b64u, jcs_bytes(signing_statement(envelope)), envelope["signature"]["value"])


def arp_digest_b64u(arp: Any) -> str:
    return b64u(sha256(jcs_bytes(arp)))


def vr(vector_id: str, check: str, status: str) -> dict[str, str]:
    return {"vector_id": vector_id, "check": check, "status": status}


def match_status(ok: bool) -> str:
    return "matched" if ok else "mismatched"


def validity_status(ok: bool) -> str:
    return "valid" if ok else "invalid"


def sha_commitment_match(commitment: dict[str, Any], candidate: str, required_basis: str | None = None) -> str:
    if commitment.get("method") != "sha256":
        return "invalid"
    if required_basis is not None and commitment.get("representation_basis") != required_basis:
        return "invalid"
    actual = b64u(sha256(candidate.encode("utf-8")))
    return match_status(actual == commitment.get("value", {}).get("value"))


def hmac_commitment_match(commitment: dict[str, Any], candidate: str | None, secret_hex: str | None, domain: str | None) -> str:
    if commitment.get("method") != "hmac-sha256":
        return "invalid"
    if candidate is None or secret_hex is None:
        return "invalid"
    if domain != commitment.get("comparison_domain"):
        return "invalid"
    actual = b64u(hmac_sha256(bytes.fromhex(secret_hex), candidate.encode("utf-8")))
    return match_status(actual == commitment.get("value", {}).get("value"))


def _mutation(base: Any, pointer: str, new_value: Any) -> Any:
    return apply_patches(base, [{"op": "replace", "path": pointer, "value": new_value}])


def eval_privacy_hash(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid = vector["vector_id"]
    if planned != "privacy-hash-only-profile-001":
        raise RunnerError(f"unsupported privacy hash planned test {planned}")
    expected = vector["expected_digest_base64url"]
    pos = b64u(sha256(vector["candidate_utf8"].encode("utf-8"))) == expected
    neg = b64u(sha256(vector["negative_candidate_utf8"].encode("utf-8"))) == expected
    return [vr(vid, "positive-candidate", match_status(pos)), vr(vid, "negative-candidate", match_status(neg))]


def eval_privacy_hmac(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid = vector["vector_id"]
    if planned != "privacy-hmac-profile-001":
        raise RunnerError(f"unsupported privacy HMAC planned test {planned}")
    candidate = vector["candidate_utf8"].encode("utf-8")
    negative = vector["negative_candidate_utf8"].encode("utf-8")
    secret = bytes.fromhex(vector["secret_key_hex"])
    wrong = bytes.fromhex(vector["wrong_secret_key_hex"])
    target = vector["expected_tag_base64url"]
    return [
        vr(vid, "correct-key-positive-candidate", match_status(b64u(hmac_sha256(secret, candidate)) == target)),
        vr(vid, "wrong-key-positive-candidate", match_status(b64u(hmac_sha256(wrong, candidate)) == target)),
        vr(vid, "correct-key-negative-candidate", match_status(b64u(hmac_sha256(secret, negative)) == target)),
    ]


def eval_privacy_commitment(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid = vector["vector_id"]
    u = vector["unkeyed"]
    hm = vector["hmac"]
    red = vector["redaction"]
    ctx = vector["contexts"]
    if planned == "privacy-commitment-compatibility-001":
        return [
            vr(vid, "compatible-hash.commitment-equality", sha_commitment_match(u["compatible_commitment"], u["candidate_utf8"], "utf8-text")),
            vr(vid, "incompatible-basis.representation-equality", sha_commitment_match(u["incompatible_basis_commitment"], u["candidate_utf8"], "utf8-text")),
            vr(vid, "incompatible-method.representation-equality", sha_commitment_match(u["incompatible_method_commitment"], u["candidate_utf8"], "utf8-text")),
        ]
    if planned == "privacy-hmac-secret-required-001":
        good = ctx["hmac_with_secret_and_candidate"]
        missing = ctx["hmac_without_secret"]
        return [
            vr(vid, "hmac-with-secret.candidate-match", hmac_commitment_match(hm["commitment"], hm["candidate_utf8"] if good["candidate_available"] else None, hm["secret_key_hex"] if good["secret_available"] else None, good["comparison_domain"])),
            vr(vid, "hmac-without-secret.independent-candidate-match", hmac_commitment_match(hm["commitment"], hm["candidate_utf8"] if missing["candidate_available"] else None, hm["secret_key_hex"] if missing["secret_available"] else None, missing["comparison_domain"])),
        ]
    if planned == "privacy-hmac-domain-compatibility-001":
        good = ctx["hmac_with_secret_and_candidate"]
        wrong = ctx["hmac_wrong_domain"]
        return [
            vr(vid, "hmac-compatible-domain.candidate-match", hmac_commitment_match(hm["commitment"], hm["candidate_utf8"], hm["secret_key_hex"], good["comparison_domain"])),
            vr(vid, "hmac-incompatible-domain.hidden-equality", hmac_commitment_match(hm["commitment"], hm["candidate_utf8"], hm["secret_key_hex"], wrong["comparison_domain"])),
        ]
    if planned == "privacy-redaction-commitment-separation-001":
        same = red["original_commitment"]["value"]["value"] == red["redacted_commitment"]["value"]["value"]
        substitution_valid = red["original_commitment"].get("representation_basis") == red["redacted_commitment"].get("representation_basis")
        return [
            vr(vid, "redaction.pre-post-commitment-equality", match_status(same)),
            vr(vid, "redaction.commitment-substitution", validity_status(substitution_valid)),
        ]
    if planned == "privacy-redacted-not-original-001":
        return [
            vr(vid, "redacted-commitment.redacted-candidate", sha_commitment_match(red["redacted_commitment"], red["redacted_candidate_utf8"], "redacted_utf8-text")),
            vr(vid, "redacted-commitment.original-candidate", sha_commitment_match(red["redacted_commitment"], red["original_candidate_utf8"], "redacted_utf8-text")),
        ]
    if planned == "privacy-original-commitment-no-redaction-proof-001":
        return [
            vr(vid, "original-commitment.original-candidate", sha_commitment_match(red["original_commitment"], red["original_candidate_utf8"], "original_utf8-text")),
            vr(vid, "original-commitment.redaction-correctness", "invalid"),
        ]
    if planned == "privacy-whole-hash-equality-001":
        return [
            vr(vid, "whole-hash.commitment-equality", sha_commitment_match(u["compatible_commitment"], u["candidate_utf8"], "utf8-text")),
            vr(vid, "whole-hash.identity-inference", "invalid"),
            vr(vid, "whole-hash.external-truth-inference", "invalid"),
        ]
    if planned == "privacy-whole-hmac-match-001":
        good = ctx["hmac_with_secret_and_candidate"]
        return [vr(vid, "whole-hmac.with-capability-candidate-match", hmac_commitment_match(hm["commitment"], hm["candidate_utf8"], hm["secret_key_hex"], good["comparison_domain"]))]
    if planned == "privacy-hmac-tag-not-recomputed-001":
        recorded_equal = hm["commitment"]["value"]["value"] == b64u(hmac_sha256(bytes.fromhex(hm["secret_key_hex"]), hm["candidate_utf8"].encode("utf-8")))
        no_secret = ctx["equal_recorded_tags_only"]["secret_available"] is False
        return [
            vr(vid, "hmac-tag.recorded-value-equality", match_status(recorded_equal)),
            vr(vid, "hmac-tag.recomputed-without-secret", "invalid" if no_secret else "valid"),
        ]
    if planned == "privacy-candidate-required-001":
        c = ctx["hmac_without_candidate"]
        result = hmac_commitment_match(hm["commitment"], hm["candidate_utf8"] if c["candidate_available"] else None, hm["secret_key_hex"] if c["secret_available"] else None, c["comparison_domain"])
        return [vr(vid, "hmac-without-candidate.candidate-match", result)]
    if planned == "privacy-hmac-tag-equality-bounded-001":
        c = ctx["equal_recorded_tags_only"]
        recomputed_tag = b64u(hmac_sha256(bytes.fromhex(hm["secret_key_hex"]), hm["candidate_utf8"].encode("utf-8")))
        recorded_equal = hm["commitment"]["value"]["value"] == recomputed_tag
        hidden_equality_verifiable = bool(c["secret_available"] and c["candidate_available"])
        return [
            vr(vid, "equal-recorded-hmac-tags.value-equality", match_status(recorded_equal)),
            vr(vid, "equal-recorded-hmac-tags.hidden-representation-equality", "valid" if hidden_equality_verifiable else "invalid"),
        ]
    raise RunnerError(f"unsupported privacy commitment planned test {planned}")


def parse_json_reject_duplicates(raw: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in items:
            if k in out:
                raise RunnerError(f"duplicate JSON member name: {k}")
            out[k] = v
        return out
    return json.loads(raw, object_pairs_hook=pairs)


def eval_jcs_edge(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid = vector["vector_id"]
    if planned == "integrity-jcs-input-validity-001":
        try:
            parse_json_reject_duplicates(vector["invalid_json"]["raw_json_utf8"])
            status = "valid"
        except Exception:
            status = "invalid"
        return [vr(vid, "invalid-json.baseline-canonicalization", status)]
    if planned == "integrity-jcs-duplicate-name-001":
        try:
            parse_json_reject_duplicates(vector["duplicate_names"]["raw_json_utf8"])
            status = "valid"
        except Exception:
            status = "invalid"
        return [vr(vid, "duplicate-names.baseline-canonicalization", status)]
    if planned == "integrity-jcs-utf8-bytes-001":
        c = vector["utf8_case"]
        ok = b64u(sha256(jcs_bytes(c["value"]))) == c["expected_sha256_base64url"] and jcs_bytes(c["value"]).hex() == c["expected_jcs_utf8_hex"]
        return [vr(vid, "utf8-case.sha256-from-jcs-utf8", match_status(ok))]
    if planned == "integrity-jcs-no-unicode-normalize-001":
        c = vector["unicode_no_normalization"]
        eq = sha256(jcs_bytes(c["nfc_value"])) == sha256(jcs_bytes(c["nfd_value"]))
        return [vr(vid, "unicode-no-normalization.digest-equality", match_status(eq))]
    if planned == "integrity-jcs-array-order-001":
        c = vector["array_order"]
        eq = sha256(jcs_bytes(c["first_value"])) == sha256(jcs_bytes(c["second_value"]))
        return [vr(vid, "array-order.digest-equality", match_status(eq))]
    if planned == "integrity-sha256-profile-001":
        c = vector["utf8_case"]
        ok = hashlib.sha256(jcs_bytes(c["value"])).hexdigest() == c["expected_sha256_hex"]
        return [vr(vid, "utf8-case.sha256", match_status(ok))]
    if planned == "integrity-digest-complete-arp-001":
        c = vector["complete_arp_scope"]
        eq = sha256(jcs_bytes(c["base_arp"])) == sha256(jcs_bytes(c["modified_arp"]))
        return [vr(vid, "complete-arp-scope.digest-equality", match_status(eq))]
    raise RunnerError(f"unsupported JCS edge planned test {planned}")


def eval_jcs_baseline(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    if planned != "integrity-jcs-profile-001":
        raise RunnerError(f"unsupported baseline JCS planned test {planned}")
    ok = jcs_bytes(vector["arp"]).decode("utf-8") == vector["expected_arp_jcs_utf8"]
    return [vr(vector["vector_id"], "expected_arp_jcs_utf8", match_status(ok))]


def eval_signing_binding(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid = vector["vector_id"]
    base = vector["base_signing_statement"]
    sig = vector["expected_signature_base64url"]
    pub = vector["public_key_base64url"]
    if planned == "integrity-ed25519-profile-001":
        return [
            vr(vid, "signature-algorithm", match_status(vector.get("signature_algorithm") == "ed25519")),
            vr(vid, "baseline-ed25519.signature", validity_status(verify_ed25519(pub, jcs_bytes(base), sig))),
        ]
    mutation_tests = {
        "integrity-signature-domain-001": [("domain", "mutation-domain.signature")],
        "integrity-signature-receipt-id-001": [("receipt_id", "mutation-receipt-id.signature")],
        "integrity-signature-payload-digest-001": [("payload_digest", "mutation-payload-digest.signature")],
        "integrity-signature-algorithm-binding-001": [("canonicalization_profile", "mutation-canonicalization-profile.signature"), ("digest_algorithm", "mutation-digest-algorithm.signature")],
        "integrity-signature-profile-binding-001": [("signature_profile", "mutation-signature-profile.signature")],
        "integrity-signature-keyref-binding-001": [("key_ref", "mutation-key-ref.signature")],
        "integrity-envelope-metadata-authenticated-001": [("signed_metadata", "mutation-signed-metadata.signature")],
        "integrity-envelope-id-binding-001": [("envelope_id", "mutation-envelope-id.signature")],
    }
    if planned in mutation_tests:
        out=[]
        for mutation_name, check in mutation_tests[planned]:
            m=vector["mutations"][mutation_name]
            changed=_mutation(base,m["path"],m["value"])
            out.append(vr(vid,check,validity_status(verify_ed25519(pub,jcs_bytes(changed),sig))))
        return out
    if planned == "integrity-signature-no-recursion-001":
        keys=set(base)
        ok=not ({"signature","signature_value"}&keys) and vector.get("signature_value_in_signing_statement") is False
        return [vr(vid,"signing-statement.excludes-signature-value",match_status(ok))]
    if planned == "integrity-signing-statement-jcs-001":
        ok=jcs_bytes(base).decode("utf-8")==vector["expected_signing_statement_jcs_utf8"]
        return [vr(vid,"signing-statement.jcs-utf8",match_status(ok))]
    raise RunnerError(f"unsupported signing-binding planned test {planned}")


def eval_envelope_placement(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid=vector["vector_id"]
    pub=vector["test_key"]["public_key_base64url"]
    if planned == "integrity-embedded-envelope-stable-digest-001":
        p=vector["embedded"]["presentation"]
        env=p["integrity_envelopes"][0]
        digest=arp_digest_b64u(p["arp"])
        stable=digest==env["payload_digest"]["value"]["value"]==vector["base"]["expected_payload_digest_base64url"]
        return [vr(vid,"embedded.arp-digest-stable",match_status(stable)),vr(vid,"embedded.signature",validity_status(verify_envelope(env,pub)))]
    if planned == "integrity-detached-envelope-target-001":
        d=vector["detached"]; env=d["envelope"]; arp=d["supplied_arp"]
        rid=env["receipt_id"]==arp["receipt_id"]
        pd=env["payload_digest"]["value"]["value"]==arp_digest_b64u(arp)
        return [vr(vid,"detached.target-receipt-id",match_status(rid)),vr(vid,"detached.target-payload-digest",match_status(pd)),vr(vid,"detached.signature",validity_status(verify_envelope(env,pub)))]
    if planned == "integrity-detached-mismatch-001":
        d=vector["detached_mismatch"]; env=d["envelope"]; arp=d["supplied_arp"]
        sig=verify_envelope(env,pub)
        binding=env["receipt_id"]==arp["receipt_id"] and env["payload_digest"]["value"]["value"]==arp_digest_b64u(arp)
        return [vr(vid,"detached-mismatch.signature",validity_status(sig)),vr(vid,"detached-mismatch.target-binding",match_status(binding)),vr(vid,"detached-mismatch.overall-binding",validity_status(sig and binding))]
    if planned == "integrity-signed-record-deletion-001":
        d=vector["record_deletion"]; env=d["original_envelope"]
        match=env["payload_digest"]["value"]["value"]==arp_digest_b64u(d["modified_arp"])
        return [vr(vid,"record-deletion.prior-digest-match",match_status(match)),vr(vid,"record-deletion.arp-binding",match_status(match))]
    raise RunnerError(f"unsupported envelope-placement planned test {planned}")


def eval_integrity_separation(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid=vector["vector_id"]
    fixture=load_json(ROOT/vector["base_fixture"])
    env=fixture["integrity_envelopes"][0]
    if planned == "integrity-signature-invalid-001":
        c=next(x for x in vector["cases"] if x["case_id"]=="wrong-public-key")
        pub=c["verification_key_override"]["public_key_base64url"]
        return [vr(vid,"wrong-public-key.signature",validity_status(verify_envelope(env,pub)))]
    if planned == "integrity-post-sign-tamper-001":
        c=next(x for x in vector["cases"] if x["case_id"]=="tampered-arp-preserve-envelope")
        tampered=apply_patches(fixture,c["patches"])
        pub=vector["verification_key"]["public_key_base64url"]
        sig=verify_envelope(tampered["integrity_envelopes"][0],pub)
        binding=tampered["integrity_envelopes"][0]["payload_digest"]["value"]["value"]==arp_digest_b64u(tampered["arp"])
        return [vr(vid,"tampered-arp-preserve-envelope.signature",validity_status(sig)),vr(vid,"tampered-arp-preserve-envelope.arp_binding",match_status(binding))]
    raise RunnerError(f"unsupported integrity-separation planned test {planned}")


def _privacy_section_signature(section: dict[str, Any], pub: str) -> bool:
    return verify_envelope(section["envelope"],pub)


def _find_commitment(arp: dict[str, Any], method: str) -> dict[str, Any] | None:
    for desc in arp.get("privacy",[]):
        for c in desc.get("commitments",[]):
            if c.get("method")==method:
                return c
    return None


def eval_integrity_privacy(vector: dict[str, Any], planned: str) -> list[dict[str, str]]:
    vid=vector["vector_id"]; pub=vector["test_key"]["public_key_base64url"]
    if planned in {"integrity-hashonly-signing-scope-001","integrity-signed-commitment-candidate-001"}:
        s=vector["signed_hash_only"]; sig=_privacy_section_signature(s,pub); c=_find_commitment(s["arp"],"sha256")
        candidate=s.get("external_candidate_utf8")
        match=c is not None and candidate is not None and sha_commitment_match(c,candidate,c.get("representation_basis"))=="matched"
        serialized=json.dumps(s["arp"],ensure_ascii=False,sort_keys=True,separators=(",",":"))
        direct=candidate is not None and candidate in serialized
        if planned=="integrity-hashonly-signing-scope-001":
            return [vr(vid,"signed-hash-only.signature",validity_status(sig)),vr(vid,"signed-hash-only.commitment-authenticated",match_status(sig and c is not None)),vr(vid,"signed-hash-only.direct-plaintext-authentication",validity_status(sig and direct))]
        return [vr(vid,"signed-hash-candidate.signature",validity_status(sig)),vr(vid,"signed-hash-candidate.commitment-match",match_status(match)),vr(vid,"signed-hash-candidate.candidate-directly-present-in-signed-arp",validity_status(direct))]
    if planned=="integrity-hmac-signature-no-secret-001":
        s=vector["signed_hmac"]; sig=_privacy_section_signature(s,pub); c=s["signature_only_context"]
        return [vr(vid,"signed-hmac.signature",validity_status(sig)),vr(vid,"signed-hmac.secret-capability-from-signature",validity_status(bool(c.get("hmac_secret_available")))),vr(vid,"signed-hmac.candidate-verification-without-secret",validity_status(bool(c.get("hmac_secret_available") and c.get("candidate_available"))))]
    if planned=="integrity-redacted-signing-scope-001":
        s=vector["signed_redacted"]; sig=_privacy_section_signature(s,pub)
        red_text=s["disclosed_redacted_candidate_utf8"]
        orig=s["unavailable_original_candidate_utf8"]
        serialized=json.dumps(s["arp"],ensure_ascii=False,sort_keys=True,separators=(",",":"))
        return [vr(vid,"signed-redacted.signature",validity_status(sig)),vr(vid,"signed-redacted.redacted-representation-authenticated",match_status(sig and red_text in serialized)),vr(vid,"signed-redacted.original-plaintext-direct-authentication",validity_status(sig and orig in serialized))]
    if planned=="integrity-signed-pin-bounded-001":
        s=vector["signed_pin"]; sig=_privacy_section_signature(s,pub)
        links=s["arp"].get("receipt_links",[])
        pin=any(x.get("linked_receipt_id")==s["recorded_target_receipt_id"] and x.get("linked_payload_digest",{}).get("value",{}).get("value")==s["recorded_target_payload_digest_base64url"] for x in links)
        return [vr(vid,"signed-pin.current-signature",validity_status(sig)),vr(vid,"signed-pin.recorded-pin-authenticated",match_status(sig and pin)),vr(vid,"signed-pin.target-signature-authenticated-by-current-signature","invalid"),vr(vid,"signed-pin.target-truth-authenticated-by-current-signature","invalid")]
    raise RunnerError(f"unsupported integrity-privacy planned test {planned}")


VECTOR_EVALUATORS: dict[str, Callable[[dict[str, Any], str], list[dict[str, str]]]] = {
    "privacy-hash-sha256-001": eval_privacy_hash,
    "privacy-hmac-sha256-001": eval_privacy_hmac,
    "privacy-commitment-semantics-001": eval_privacy_commitment,
    "integrity-jcs-sha256-ed25519-001": eval_jcs_baseline,
    "integrity-jcs-edge-cases-001": eval_jcs_edge,
    "integrity-signing-statement-binding-001": eval_signing_binding,
    "integrity-envelope-placement-001": eval_envelope_placement,
    "integrity-separation-001": eval_integrity_separation,
    "integrity-privacy-composition-001": eval_integrity_privacy,
}


def execute_vector(document: Any, planned_test_id: str) -> list[dict[str, str]]:
    if not isinstance(document, dict) or not isinstance(document.get("vector_id"), str):
        raise RunnerError("deterministic vector document missing vector_id")
    fn=VECTOR_EVALUATORS.get(document["vector_id"])
    if fn is None:
        raise RunnerError(f"unsupported vector_id {document['vector_id']}")
    return fn(document,planned_test_id)


def schema_result(document_id: str, target: str, result: dict[str, Any]) -> dict[str, Any]:
    out={"document_id":document_id,"schema_target":target,"status":result["status"]}
    if result.get("error_classes"):
        out["error_classes"]=result["error_classes"]
    return out


def _subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and _subset(v,actual[k]) for k,v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and all(any(_subset(e,a) for a in actual) for e in expected)
    return expected==actual


def compare_schema_results(expected: list[dict[str, Any]], actual: list[dict[str, Any]], exact: bool) -> list[str]:
    errors=[]; amap={x["document_id"]:x for x in actual}
    if exact and set(amap)!={x["document_id"] for x in expected}:
        errors.append("schema document-id set differs")
    for e in expected:
        a=amap.get(e["document_id"])
        if a is None:
            errors.append(f"missing schema result {e['document_id']}"); continue
        for k in ["schema_target","status"]:
            if k in e and a.get(k)!=e[k]: errors.append(f"schema {e['document_id']} {k}: expected {e[k]!r}, got {a.get(k)!r}")
        if "error_classes" in e:
            eset=set(e["error_classes"]); aset=set(a.get("error_classes",[]))
            if exact:
                if aset!=eset: errors.append(f"schema {e['document_id']} error_classes: expected {sorted(eset)}, got {sorted(aset)}")
            elif not eset<=aset:
                errors.append(f"schema {e['document_id']} missing error classes {sorted(eset-aset)}")
    return errors


def compare_vector_results(expected: list[dict[str, Any]], actual: list[dict[str, Any]], exact: bool) -> list[str]:
    errors=[]
    ecanon={json.dumps(x,sort_keys=True,separators=(",",":")) for x in expected}
    acanon={json.dumps(x,sort_keys=True,separators=(",",":")) for x in actual}
    if exact:
        if ecanon!=acanon:
            missing=sorted(ecanon-acanon); extra=sorted(acanon-ecanon)
            if missing: errors.append("missing vector results: "+"; ".join(missing))
            if extra: errors.append("extra vector results: "+"; ".join(extra))
    else:
        missing=ecanon-acanon
        if missing: errors.append("missing vector results: "+"; ".join(sorted(missing)))
    return errors


def matcher_matches(matcher: dict[str, Any], finding: dict[str, Any], exact: bool) -> bool:
    for k,v in matcher.items():
        if k=="subject_selector":
            if not _subset(v,finding.get("subject_scope",{})): return False
        elif k in {"evidence_bases","prohibited_inferences"}:
            actual=finding.get(k,[])
            if exact:
                if set(actual)!=set(v): return False
            elif not set(v)<=set(actual): return False
        elif finding.get(k)!=v:
            return False
    return True


def compare_expected(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    exact=expected.get("comparison_mode")=="exact_normative"
    errors=compare_schema_results(expected.get("schema_results",[]),actual.get("schema_results",[]),exact)
    errors+=compare_vector_results(expected.get("vector_results",[]),actual.get("vector_results",[]),exact)
    findings=actual.get("findings",[])
    for m in expected.get("required_findings",[]):
        if not any(matcher_matches(m,f,exact) for f in findings): errors.append("required finding not matched: "+json.dumps(m,sort_keys=True))
    for m in expected.get("forbidden_findings",[]):
        if any(matcher_matches(m,f,exact) for f in findings): errors.append("forbidden finding matched: "+json.dumps(m,sort_keys=True))
    if exact and expected.get("required_findings") is not None and len(findings)!=len(expected.get("required_findings",[])):
        errors.append(f"exact normative finding count differs: expected {len(expected.get('required_findings',[]))}, got {len(findings)}")
    for k in ["process_outcome","completeness"]:
        if k in expected and actual.get(k)!=expected[k]: errors.append(f"{k}: expected {expected[k]!r}, got {actual.get(k)!r}")
    return errors


def git_head() -> str | None:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    except Exception:
        return None


def load_case_rows() -> list[dict[str, Any]]:
    rows=[]
    manifest=load_json(CONF/"manifest.json")
    for index_path in manifest["case_indexes"]:
        index=load_json(ROOT/index_path)
        rows.extend(index["cases"])
    if len(rows)!=907 or len({x["case_id"] for x in rows})!=907:
        raise RunnerError(f"suite index invariant failed: {len(rows)} rows")
    return rows


def execute_case(row: dict[str, Any], schemas: SchemaRegistry) -> dict[str, Any]:
    case=load_json(ROOT/row["case_path"])
    materialized: dict[str,Any]={}
    actual={"schema_results":[],"findings":[],"vector_results":[]}
    errors=[]
    try:
        for doc in case["documents"]:
            value=materialize_document(doc)
            materialized[doc["document_id"]]=value
            sr=schemas.validate(value,doc["schema_target"])
            actual["schema_results"].append(schema_result(doc["document_id"],doc["schema_target"],sr))
    except Exception as exc:
        return {"case_id":row["case_id"],"primary_enforcement":row["primary_enforcement"],"status":"error","errors":[f"materialization/schema error: {exc}"]}

    enforcement=row["primary_enforcement"]
    if enforcement=="deterministic_vector":
        try:
            if len(materialized)!=1:
                raise RunnerError("deterministic_vector case must have exactly one materialized vector document in Runner A wave 01")
            vector_doc=next(iter(materialized.values()))
            actual["vector_results"]=execute_vector(vector_doc,case["planned_test_ids"][0])
        except Exception as exc:
            return {"case_id":row["case_id"],"primary_enforcement":enforcement,"status":"error","errors":[f"vector execution error: {exc}"],"actual":actual}
    expected=load_json(ROOT/row["expected_result_path"])
    if enforcement not in SUPPORTED_ENFORCEMENTS:
        schema_errors=compare_schema_results(expected.get("schema_results",[]),actual["schema_results"],False)
        return {"case_id":row["case_id"],"primary_enforcement":enforcement,"status":"blocked_semantic_checker","schema_surface_match":not schema_errors,"errors":schema_errors,"actual":{"schema_results":actual["schema_results"]}}

    errors=compare_expected(expected,actual)
    return {"case_id":row["case_id"],"primary_enforcement":enforcement,"status":"passed" if not errors else "failed","errors":errors,"actual":actual}


def run_all() -> dict[str, Any]:
    schemas=SchemaRegistry.build(); rows=load_case_rows(); results=[]
    for row in rows:
        results.append(execute_case(row,schemas))
    counts={}
    by_enforcement={}
    for r in results:
        counts[r["status"]]=counts.get(r["status"],0)+1
        e=by_enforcement.setdefault(r["primary_enforcement"],{})
        e[r["status"]]=e.get(r["status"],0)+1
    schema_surface_matches=sum(1 for r in results if r.get("schema_surface_match") is True)
    return {
        "runner":{"name":"C2ATrace Runner A","implementation":"python-independent","stage":"P6-wave-01"},
        "source_commit":git_head(),
        "summary":{"total":len(results),"status_counts":counts,"by_enforcement":by_enforcement,"schema_surface_matches_on_blocked":schema_surface_matches},
        "cases":results,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    report=run_all()
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report["summary"],sort_keys=True))
    failed=report["summary"]["status_counts"].get("failed",0)+report["summary"]["status_counts"].get("error",0)
    expected_pass=49
    actual_pass=report["summary"]["status_counts"].get("passed",0)
    if failed or actual_pass!=expected_pass:
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
