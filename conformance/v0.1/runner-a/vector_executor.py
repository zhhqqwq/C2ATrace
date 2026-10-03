#!/usr/bin/env python3
import base64
import copy
import hashlib
import hmac
import json
from pathlib import Path
from urllib.parse import unquote

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


CASE_CHECKS = {
    "privacy-hash-only-profile-001": [
        "positive-candidate",
        "negative-candidate",
    ],
    "privacy-hmac-profile-001": [
        "correct-key-positive-candidate",
        "wrong-key-positive-candidate",
        "correct-key-negative-candidate",
    ],
    "privacy-commitment-compatibility-001": [
        "compatible-hash.commitment-equality",
        "incompatible-basis.representation-equality",
        "incompatible-method.representation-equality",
    ],
    "privacy-hmac-secret-required-001": [
        "hmac-with-secret.candidate-match",
        "hmac-without-secret.independent-candidate-match",
    ],
    "privacy-hmac-domain-compatibility-001": [
        "hmac-compatible-domain.candidate-match",
        "hmac-incompatible-domain.hidden-equality",
    ],
    "privacy-redaction-commitment-separation-001": [
        "redaction.pre-post-commitment-equality",
        "redaction.commitment-substitution",
    ],
    "privacy-redacted-not-original-001": [
        "redacted-commitment.redacted-candidate",
        "redacted-commitment.original-candidate",
    ],
    "privacy-original-commitment-no-redaction-proof-001": [
        "original-commitment.original-candidate",
        "original-commitment.redaction-correctness",
    ],
    "privacy-whole-hash-equality-001": [
        "whole-hash.commitment-equality",
        "whole-hash.identity-inference",
        "whole-hash.external-truth-inference",
    ],
    "privacy-whole-hmac-match-001": [
        "whole-hmac.with-capability-candidate-match",
    ],
    "privacy-hmac-tag-not-recomputed-001": [
        "hmac-tag.recorded-value-equality",
        "hmac-tag.recomputed-without-secret",
    ],
    "privacy-candidate-required-001": [
        "hmac-without-candidate.candidate-match",
    ],
    "privacy-hmac-tag-equality-bounded-001": [
        "equal-recorded-hmac-tags.value-equality",
        "equal-recorded-hmac-tags.hidden-representation-equality",
    ],
    "integrity-jcs-profile-001": [
        "expected_arp_jcs_utf8",
    ],
    "integrity-jcs-input-validity-001": [
        "invalid-json.baseline-canonicalization",
    ],
    "integrity-jcs-utf8-bytes-001": [
        "utf8-case.sha256-from-jcs-utf8",
    ],
    "integrity-jcs-duplicate-name-001": [
        "duplicate-names.baseline-canonicalization",
    ],
    "integrity-jcs-no-unicode-normalize-001": [
        "unicode-no-normalization.digest-equality",
    ],
    "integrity-jcs-array-order-001": [
        "array-order.digest-equality",
    ],
    "integrity-sha256-profile-001": [
        "utf8-case.sha256",
    ],
    "integrity-digest-complete-arp-001": [
        "complete-arp-scope.digest-equality",
    ],
    "integrity-ed25519-profile-001": [
        "signature-algorithm",
        "baseline-ed25519.signature",
    ],
    "integrity-signature-domain-001": [
        "mutation-domain.signature",
    ],
    "integrity-signature-receipt-id-001": [
        "mutation-receipt-id.signature",
    ],
    "integrity-signature-payload-digest-001": [
        "mutation-payload-digest.signature",
    ],
    "integrity-signature-algorithm-binding-001": [
        "mutation-canonicalization-profile.signature",
        "mutation-digest-algorithm.signature",
    ],
    "integrity-signature-profile-binding-001": [
        "mutation-signature-profile.signature",
    ],
    "integrity-signature-keyref-binding-001": [
        "mutation-key-ref.signature",
    ],
    "integrity-envelope-metadata-authenticated-001": [
        "mutation-signed-metadata.signature",
    ],
    "integrity-signature-no-recursion-001": [
        "signing-statement.excludes-signature-value",
    ],
    "integrity-embedded-envelope-stable-digest-001": [
        "embedded.arp-digest-stable",
        "embedded.signature",
    ],
    "integrity-detached-envelope-target-001": [
        "detached.target-receipt-id",
        "detached.target-payload-digest",
        "detached.signature",
    ],
    "integrity-detached-mismatch-001": [
        "detached-mismatch.signature",
        "detached-mismatch.target-binding",
        "detached-mismatch.overall-binding",
    ],
    "integrity-signature-invalid-001": [
        "wrong-public-key.signature",
    ],
    "integrity-post-sign-tamper-001": [
        "tampered-arp-preserve-envelope.signature",
        "tampered-arp-preserve-envelope.arp_binding",
    ],
    "integrity-signed-record-deletion-001": [
        "record-deletion.prior-digest-match",
        "record-deletion.arp-binding",
    ],
    "integrity-hashonly-signing-scope-001": [
        "signed-hash-only.signature",
        "signed-hash-only.commitment-authenticated",
        "signed-hash-only.direct-plaintext-authentication",
    ],
    "integrity-hmac-signature-no-secret-001": [
        "signed-hmac.signature",
        "signed-hmac.secret-capability-from-signature",
        "signed-hmac.candidate-verification-without-secret",
    ],
    "integrity-redacted-signing-scope-001": [
        "signed-redacted.signature",
        "signed-redacted.redacted-representation-authenticated",
        "signed-redacted.original-plaintext-direct-authentication",
    ],
    "integrity-signed-commitment-candidate-001": [
        "signed-hash-candidate.signature",
        "signed-hash-candidate.commitment-match",
        "signed-hash-candidate.candidate-directly-present-in-signed-arp",
    ],
    "integrity-signed-pin-bounded-001": [
        "signed-pin.current-signature",
        "signed-pin.recorded-pin-authenticated",
        "signed-pin.target-signature-authenticated-by-current-signature",
        "signed-pin.target-truth-authenticated-by-current-signature",
    ],
    "integrity-signing-statement-jcs-001": [
        "signing-statement.jcs-utf8",
    ],
    "integrity-envelope-id-binding-001": [
        "mutation-envelope-id.signature",
    ],
}


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(value):
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def canonicalize(value):
    return rfc8785.dumps(value)


def sha256_bytes(data):
    return hashlib.sha256(data).digest()


def sha256_text(text):
    return sha256_bytes(text.encode("utf-8"))


def sha256_jcs(value):
    return sha256_bytes(canonicalize(value))


def hmac_sha256(secret_hex, text):
    return hmac.new(bytes.fromhex(secret_hex), text.encode("utf-8"), hashlib.sha256).digest()


def matched(value):
    return "matched" if value else "mismatched"


def valid(value):
    return "valid" if value else "invalid"


def strict_json_loads(raw):
    class DuplicateName(ValueError):
        pass

    def pairs_hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise DuplicateName(key)
            out[key] = value
        return out

    return json.loads(raw, object_pairs_hook=pairs_hook)


def pointer_tokens(pointer):
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ValueError("invalid JSON Pointer")
    return [unquote(x).replace("~1", "/").replace("~0", "~") for x in pointer[1:].split("/")]


def set_pointer(document, pointer, value):
    out = copy.deepcopy(document)
    tokens = pointer_tokens(pointer)
    if not tokens:
        return copy.deepcopy(value)
    parent = out
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    leaf = tokens[-1]
    if isinstance(parent, list):
        parent[int(leaf)] = copy.deepcopy(value)
    else:
        parent[leaf] = copy.deepcopy(value)
    return out


def apply_patches(document, patches):
    out = copy.deepcopy(document)
    for patch in patches or []:
        tokens = pointer_tokens(patch["path"])
        if not tokens:
            raise ValueError("root patch is not supported")
        parent = out
        for token in tokens[:-1]:
            parent = parent[int(token)] if isinstance(parent, list) else parent[token]
        leaf = tokens[-1]
        if isinstance(parent, list):
            index = int(leaf) if leaf != "-" else len(parent)
            if patch["op"] == "add":
                parent.insert(index, copy.deepcopy(patch["value"]))
            elif patch["op"] == "remove":
                parent.pop(index)
            elif patch["op"] == "replace":
                parent[index] = copy.deepcopy(patch["value"])
            else:
                raise ValueError(patch["op"])
        else:
            if patch["op"] == "add":
                parent[leaf] = copy.deepcopy(patch["value"])
            elif patch["op"] == "remove":
                del parent[leaf]
            elif patch["op"] == "replace":
                if leaf not in parent:
                    raise KeyError(leaf)
                parent[leaf] = copy.deepcopy(patch["value"])
            else:
                raise ValueError(patch["op"])
    return out


def derive_public_key(seed_hex):
    private = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))
    return b64url(private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    ))


def sign_ed25519(seed_hex, message):
    private = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))
    return b64url(private.sign(message))


def verify_ed25519(public_key_base64url, signature_base64url, message):
    try:
        key = Ed25519PublicKey.from_public_bytes(b64url_decode(public_key_base64url))
        key.verify(b64url_decode(signature_base64url), message)
        return True
    except (InvalidSignature, ValueError):
        return False


def signing_statement_from_envelope(envelope, domain="C2ATrace/v0.1/ReceiptSignature"):
    return {
        "domain": domain,
        "receipt_id": envelope["receipt_id"],
        "payload_digest": envelope["payload_digest"],
        "canonicalization_profile": envelope["canonicalization_profile"],
        "digest_algorithm": envelope["digest_algorithm"],
        "signature_profile": envelope["signature_profile"],
        "key_ref": envelope["key_ref"],
        "envelope_id": envelope["id"],
        "signed_metadata": envelope.get("signed_metadata", {}),
    }


def verify_envelope(envelope, public_key_base64url, domain="C2ATrace/v0.1/ReceiptSignature"):
    statement = signing_statement_from_envelope(envelope, domain)
    return verify_ed25519(
        public_key_base64url,
        envelope["signature"]["value"],
        canonicalize(statement),
    )


def arp_binding(envelope, arp):
    return b64url(sha256_jcs(arp)) == envelope["payload_digest"]["value"]["value"]


def contains_exact_string(value, target):
    if isinstance(value, str):
        return value == target
    if isinstance(value, list):
        return any(contains_exact_string(x, target) for x in value)
    if isinstance(value, dict):
        return any(contains_exact_string(x, target) for x in value.values())
    return False


def privacy_hash(vector):
    target = vector["expected_digest_base64url"]
    positive = b64url(sha256_text(vector["candidate_utf8"]))
    negative = b64url(sha256_text(vector["negative_candidate_utf8"]))
    return {
        "positive-candidate": matched(positive == target),
        "negative-candidate": matched(negative == target),
    }


def privacy_hmac(vector):
    target = vector["expected_tag_base64url"]
    positive = b64url(hmac_sha256(vector["secret_key_hex"], vector["candidate_utf8"]))
    wrong_key = b64url(hmac_sha256(vector["wrong_secret_key_hex"], vector["candidate_utf8"]))
    negative = b64url(hmac_sha256(vector["secret_key_hex"], vector["negative_candidate_utf8"]))
    return {
        "correct-key-positive-candidate": matched(positive == target),
        "wrong-key-positive-candidate": matched(wrong_key == target),
        "correct-key-negative-candidate": matched(negative == target),
    }


def commitment_sha_match(candidate, commitment, basis):
    if commitment.get("method") != "sha256" or commitment.get("representation_basis") != basis:
        return None
    return b64url(sha256_text(candidate)) == commitment["value"]["value"]


def commitment_hmac_match(candidate, secret_hex, commitment, context_domain):
    if commitment.get("method") != "hmac-sha256":
        return None
    if commitment.get("representation_basis") != "utf8-text":
        return None
    if commitment.get("comparison_domain") != context_domain:
        return None
    return b64url(hmac_sha256(secret_hex, candidate)) == commitment["value"]["value"]


def privacy_commitment(vector):
    unkeyed = vector["unkeyed"]
    hmac_vector = vector["hmac"]
    redaction = vector["redaction"]
    contexts = vector["contexts"]

    compatible = commitment_sha_match(
        unkeyed["candidate_utf8"],
        unkeyed["compatible_commitment"],
        "utf8-text",
    )
    incompatible_basis = commitment_sha_match(
        unkeyed["candidate_utf8"],
        unkeyed["incompatible_basis_commitment"],
        "utf8-text",
    )
    incompatible_method = commitment_sha_match(
        unkeyed["candidate_utf8"],
        unkeyed["incompatible_method_commitment"],
        "utf8-text",
    )

    with_secret = contexts["hmac_with_secret_and_candidate"]
    hmac_match = None
    if with_secret["secret_available"] and with_secret["candidate_available"]:
        hmac_match = commitment_hmac_match(
            hmac_vector["candidate_utf8"],
            hmac_vector["secret_key_hex"],
            hmac_vector["commitment"],
            with_secret["comparison_domain"],
        )

    compatible_domain = commitment_hmac_match(
        hmac_vector["candidate_utf8"],
        hmac_vector["secret_key_hex"],
        hmac_vector["commitment"],
        contexts["hmac_with_secret_and_candidate"]["comparison_domain"],
    )
    incompatible_domain = commitment_hmac_match(
        hmac_vector["candidate_utf8"],
        hmac_vector["secret_key_hex"],
        hmac_vector["commitment"],
        contexts["hmac_wrong_domain"]["comparison_domain"],
    )

    original_match = commitment_sha_match(
        redaction["original_candidate_utf8"],
        redaction["original_commitment"],
        "original_utf8-text",
    )
    redacted_match = commitment_sha_match(
        redaction["redacted_candidate_utf8"],
        redaction["redacted_commitment"],
        "redacted_utf8-text",
    )
    redacted_against_original = commitment_sha_match(
        redaction["original_candidate_utf8"],
        redaction["redacted_commitment"],
        "redacted_utf8-text",
    )
    pre_post_equal = (
        redaction["original_commitment"]["value"]["value"]
        == redaction["redacted_commitment"]["value"]["value"]
    )

    recorded_tag = hmac_vector["commitment"]["value"]["value"]
    recomputed_tag = b64url(hmac_sha256(
        hmac_vector["secret_key_hex"],
        hmac_vector["candidate_utf8"],
    ))

    return {
        "compatible-hash.commitment-equality": (
            "invalid" if compatible is None else matched(compatible)
        ),
        "incompatible-basis.representation-equality": (
            "invalid" if incompatible_basis is None else matched(incompatible_basis)
        ),
        "incompatible-method.representation-equality": (
            "invalid" if incompatible_method is None else matched(incompatible_method)
        ),
        "hmac-with-secret.candidate-match": (
            "invalid" if hmac_match is None else matched(hmac_match)
        ),
        "hmac-without-secret.independent-candidate-match": (
            "invalid" if not contexts["hmac_without_secret"]["secret_available"]
            else matched(False)
        ),
        "hmac-compatible-domain.candidate-match": (
            "invalid" if compatible_domain is None else matched(compatible_domain)
        ),
        "hmac-incompatible-domain.hidden-equality": (
            "invalid" if incompatible_domain is None else matched(incompatible_domain)
        ),
        "redaction.pre-post-commitment-equality": matched(pre_post_equal),
        "redaction.commitment-substitution": (
            "invalid"
            if redaction["original_commitment"]["representation_basis"]
            != redaction["redacted_commitment"]["representation_basis"]
            else matched(pre_post_equal)
        ),
        "redacted-commitment.redacted-candidate": (
            "invalid" if redacted_match is None else matched(redacted_match)
        ),
        "redacted-commitment.original-candidate": (
            "invalid" if redacted_against_original is None else matched(redacted_against_original)
        ),
        "original-commitment.original-candidate": (
            "invalid" if original_match is None else matched(original_match)
        ),
        "original-commitment.redaction-correctness": "invalid",
        "whole-hash.commitment-equality": (
            "invalid" if compatible is None else matched(compatible)
        ),
        "whole-hash.identity-inference": "invalid",
        "whole-hash.external-truth-inference": "invalid",
        "whole-hmac.with-capability-candidate-match": (
            "invalid" if hmac_match is None else matched(hmac_match)
        ),
        "hmac-tag.recorded-value-equality": matched(recorded_tag == recomputed_tag),
        "hmac-tag.recomputed-without-secret": (
            "invalid" if not contexts["hmac_without_secret"]["secret_available"]
            else matched(False)
        ),
        "hmac-without-candidate.candidate-match": (
            "invalid" if not contexts["hmac_without_candidate"]["candidate_available"]
            else matched(False)
        ),
        "equal-recorded-hmac-tags.value-equality": matched(recorded_tag == recomputed_tag),
        "equal-recorded-hmac-tags.hidden-representation-equality": (
            "invalid"
            if (
                not contexts["equal_recorded_tags_only"]["secret_available"]
                and not contexts["equal_recorded_tags_only"]["candidate_available"]
            )
            else matched(False)
        ),
    }


def integrity_baseline(vector):
    actual_jcs = canonicalize(vector["arp"]).decode("utf-8")
    return {
        "expected_arp_jcs_utf8": matched(actual_jcs == vector["expected_arp_jcs_utf8"]),
    }


def integrity_jcs_edges(vector):
    results = {}

    try:
        strict_json_loads(vector["invalid_json"]["raw_json_utf8"])
        invalid_json = False
    except (ValueError, json.JSONDecodeError):
        invalid_json = True
    results["invalid-json.baseline-canonicalization"] = valid(not invalid_json)

    try:
        strict_json_loads(vector["duplicate_names"]["raw_json_utf8"])
        duplicate_invalid = False
    except (ValueError, json.JSONDecodeError):
        duplicate_invalid = True
    results["duplicate-names.baseline-canonicalization"] = valid(not duplicate_invalid)

    utf8 = vector["utf8_case"]
    utf8_bytes = canonicalize(utf8["value"])
    utf8_hash = sha256_bytes(utf8_bytes)
    results["utf8-case.sha256-from-jcs-utf8"] = matched(
        utf8_bytes.hex() == utf8["expected_jcs_utf8_hex"]
        and utf8_hash.hex() == utf8["expected_sha256_hex"]
        and b64url(utf8_hash) == utf8["expected_sha256_base64url"]
    )
    results["utf8-case.sha256"] = matched(
        utf8_hash.hex() == utf8["expected_sha256_hex"]
        and b64url(utf8_hash) == utf8["expected_sha256_base64url"]
    )

    unicode_case = vector["unicode_no_normalization"]
    nfc = sha256_jcs(unicode_case["nfc_value"])
    nfd = sha256_jcs(unicode_case["nfd_value"])
    results["unicode-no-normalization.digest-equality"] = matched(nfc == nfd)

    array_case = vector["array_order"]
    first = sha256_jcs(array_case["first_value"])
    second = sha256_jcs(array_case["second_value"])
    results["array-order.digest-equality"] = matched(first == second)

    scope = vector["complete_arp_scope"]
    base = sha256_jcs(scope["base_arp"])
    modified = sha256_jcs(scope["modified_arp"])
    results["complete-arp-scope.digest-equality"] = matched(base == modified)
    return results


def integrity_signing_binding(vector):
    statement = vector["base_signing_statement"]
    statement_bytes = canonicalize(statement)
    expected_signature = vector["expected_signature_base64url"]

    public_from_seed = derive_public_key(vector["private_seed_hex"])
    recomputed_signature = sign_ed25519(vector["private_seed_hex"], statement_bytes)
    baseline_valid = (
        public_from_seed == vector["public_key_base64url"]
        and recomputed_signature == expected_signature
        and verify_ed25519(vector["public_key_base64url"], expected_signature, statement_bytes)
    )
    results = {
        "signature-algorithm": matched(vector["signature_algorithm"] == "ed25519"),
        "baseline-ed25519.signature": valid(baseline_valid),
        "signing-statement.excludes-signature-value": matched(
            "signature" not in statement
        ),
        "signing-statement.jcs-utf8": matched(
            statement_bytes.decode("utf-8")
            == vector["expected_signing_statement_jcs_utf8"]
        ),
    }

    check_names = {
        "domain": "mutation-domain.signature",
        "receipt_id": "mutation-receipt-id.signature",
        "payload_digest": "mutation-payload-digest.signature",
        "canonicalization_profile": "mutation-canonicalization-profile.signature",
        "digest_algorithm": "mutation-digest-algorithm.signature",
        "signature_profile": "mutation-signature-profile.signature",
        "key_ref": "mutation-key-ref.signature",
        "signed_metadata": "mutation-signed-metadata.signature",
        "envelope_id": "mutation-envelope-id.signature",
    }
    for mutation_name, mutation in vector["mutations"].items():
        mutated = set_pointer(statement, mutation["path"], mutation["value"])
        still_valid = verify_ed25519(
            vector["public_key_base64url"],
            expected_signature,
            canonicalize(mutated),
        )
        results[check_names[mutation_name]] = valid(still_valid)
    return results


def integrity_envelope_placement(vector):
    key = vector["test_key"]["public_key_base64url"]
    domain = vector["signing_statement_domain"]
    results = {}

    embedded = vector["embedded"]["presentation"]
    embedded_envelope = embedded["integrity_envelopes"][0]
    embedded_digest = b64url(sha256_jcs(embedded["arp"]))
    results["embedded.arp-digest-stable"] = matched(
        embedded_digest == embedded["payload_digest"]["value"]["value"]
        and embedded_digest == embedded_envelope["payload_digest"]["value"]["value"]
    )
    results["embedded.signature"] = valid(
        verify_envelope(embedded_envelope, key, domain)
    )

    detached = vector["detached"]
    detached_envelope = detached["envelope"]
    detached_digest = b64url(sha256_jcs(detached["supplied_arp"]))
    results["detached.target-receipt-id"] = matched(
        detached_envelope["receipt_id"] == detached["supplied_arp"]["receipt_id"]
    )
    results["detached.target-payload-digest"] = matched(
        detached_envelope["payload_digest"]["value"]["value"] == detached_digest
    )
    results["detached.signature"] = valid(
        verify_envelope(detached_envelope, key, domain)
    )

    mismatch = vector["detached_mismatch"]
    mismatch_envelope = mismatch["envelope"]
    mismatch_digest = b64url(sha256_jcs(mismatch["supplied_arp"]))
    mismatch_signature_valid = verify_envelope(mismatch_envelope, key, domain)
    mismatch_target = (
        mismatch_envelope["receipt_id"] == mismatch["supplied_arp"]["receipt_id"]
        and mismatch_envelope["payload_digest"]["value"]["value"] == mismatch_digest
    )
    results["detached-mismatch.signature"] = valid(mismatch_signature_valid)
    results["detached-mismatch.target-binding"] = matched(mismatch_target)
    results["detached-mismatch.overall-binding"] = valid(
        mismatch_signature_valid and mismatch_target
    )

    deletion = vector["record_deletion"]
    deletion_digest = b64url(sha256_jcs(deletion["modified_arp"]))
    prior_match = (
        deletion_digest
        == deletion["original_envelope"]["payload_digest"]["value"]["value"]
    )
    results["record-deletion.prior-digest-match"] = matched(prior_match)
    results["record-deletion.arp-binding"] = matched(prior_match)
    return results


def integrity_separation(vector, root):
    fixture = json.loads((root / vector["base_fixture"]).read_text(encoding="utf-8"))
    by_id = {case["case_id"]: case for case in vector["cases"]}
    results = {}

    wrong = by_id["wrong-public-key"]
    wrong_receipt = apply_patches(fixture, wrong["patches"])
    wrong_envelope = wrong_receipt["integrity_envelopes"][0]
    wrong_key = wrong["verification_key_override"]["public_key_base64url"]
    results["wrong-public-key.signature"] = valid(
        verify_envelope(wrong_envelope, wrong_key)
    )

    tampered = by_id["tampered-arp-preserve-envelope"]
    tampered_receipt = apply_patches(fixture, tampered["patches"])
    tampered_envelope = tampered_receipt["integrity_envelopes"][0]
    base_key = vector["verification_key"]["public_key_base64url"]
    results["tampered-arp-preserve-envelope.signature"] = valid(
        verify_envelope(tampered_envelope, base_key)
    )
    results["tampered-arp-preserve-envelope.arp_binding"] = matched(
        arp_binding(tampered_envelope, tampered_receipt["arp"])
    )
    return results


def section_signature_and_binding(section, public_key):
    signature_valid = verify_envelope(section["envelope"], public_key)
    binding_valid = arp_binding(section["envelope"], section["arp"])
    return signature_valid, binding_valid


def integrity_privacy_composition(vector):
    public_key = vector["test_key"]["public_key_base64url"]
    results = {}

    hash_only = vector["signed_hash_only"]
    hash_signature, hash_binding = section_signature_and_binding(hash_only, public_key)
    hash_commitment = hash_only["arp"]["privacy"][0]["commitments"][0]
    candidate_hash = b64url(sha256_text(hash_only["external_candidate_utf8"]))
    hash_commitment_match = candidate_hash == hash_commitment["value"]["value"]
    hash_candidate_present = contains_exact_string(
        hash_only["arp"], hash_only["external_candidate_utf8"]
    )
    results["signed-hash-only.signature"] = valid(hash_signature)
    results["signed-hash-only.commitment-authenticated"] = matched(
        hash_signature and hash_binding and hash_commitment_match
    )
    results["signed-hash-only.direct-plaintext-authentication"] = (
        matched(True) if hash_signature and hash_binding and hash_candidate_present else "invalid"
    )
    results["signed-hash-candidate.signature"] = valid(hash_signature)
    results["signed-hash-candidate.commitment-match"] = matched(hash_commitment_match)
    results["signed-hash-candidate.candidate-directly-present-in-signed-arp"] = (
        matched(True) if hash_candidate_present else "invalid"
    )

    signed_hmac = vector["signed_hmac"]
    hmac_signature, hmac_binding_ok = section_signature_and_binding(signed_hmac, public_key)
    context = signed_hmac["signature_only_context"]
    results["signed-hmac.signature"] = valid(hmac_signature)
    results["signed-hmac.secret-capability-from-signature"] = (
        matched(True)
        if hmac_signature and hmac_binding_ok and context["hmac_secret_available"]
        else "invalid"
    )
    results["signed-hmac.candidate-verification-without-secret"] = (
        matched(True)
        if (
            hmac_signature
            and hmac_binding_ok
            and context["hmac_secret_available"]
            and context["candidate_available"]
        )
        else "invalid"
    )

    redacted = vector["signed_redacted"]
    redacted_signature, redacted_binding = section_signature_and_binding(redacted, public_key)
    redacted_present = contains_exact_string(
        redacted["arp"], redacted["disclosed_redacted_candidate_utf8"]
    )
    original_present = contains_exact_string(
        redacted["arp"], redacted["unavailable_original_candidate_utf8"]
    )
    results["signed-redacted.signature"] = valid(redacted_signature)
    results["signed-redacted.redacted-representation-authenticated"] = matched(
        redacted_signature and redacted_binding and redacted_present
    )
    results["signed-redacted.original-plaintext-direct-authentication"] = (
        matched(True)
        if redacted_signature and redacted_binding and original_present
        else "invalid"
    )

    signed_pin = vector["signed_pin"]
    pin_signature, pin_binding = section_signature_and_binding(signed_pin, public_key)
    links = signed_pin["arp"].get("receipt_links", [])
    recorded_pin_present = any(
        link.get("linked_receipt_id") == signed_pin["recorded_target_receipt_id"]
        and link.get("linked_payload_digest", {}).get("value", {}).get("value")
        == signed_pin["recorded_target_payload_digest_base64url"]
        for link in links
    )
    results["signed-pin.current-signature"] = valid(pin_signature)
    results["signed-pin.recorded-pin-authenticated"] = matched(
        pin_signature and pin_binding and recorded_pin_present
    )
    results["signed-pin.target-signature-authenticated-by-current-signature"] = "invalid"
    results["signed-pin.target-truth-authenticated-by-current-signature"] = "invalid"
    return results


VECTOR_EXECUTORS = {
    "privacy-hash-sha256-001": privacy_hash,
    "privacy-hmac-sha256-001": privacy_hmac,
    "privacy-commitment-semantics-001": privacy_commitment,
    "integrity-jcs-sha256-ed25519-001": integrity_baseline,
    "integrity-jcs-edge-cases-001": integrity_jcs_edges,
    "integrity-signing-statement-binding-001": integrity_signing_binding,
    "integrity-envelope-placement-001": integrity_envelope_placement,
    "integrity-privacy-composition-001": integrity_privacy_composition,
}


def execute_case_vector(vector, planned_test_id, root):
    if planned_test_id not in CASE_CHECKS:
        raise KeyError(f"no vector check mapping for {planned_test_id}")
    vector_id = vector.get("vector_id")
    if vector_id == "integrity-separation-001":
        computed = integrity_separation(vector, Path(root))
    else:
        executor = VECTOR_EXECUTORS.get(vector_id)
        if executor is None:
            raise KeyError(f"unsupported vector_id {vector_id}")
        computed = executor(vector)

    results = []
    for check in CASE_CHECKS[planned_test_id]:
        if check not in computed:
            raise KeyError(f"executor did not produce {vector_id}:{check}")
        results.append({
            "vector_id": vector_id,
            "check": check,
            "status": computed[check],
        })
    return results
