# C2ATrace v0.1 — Phase 1 Part H: Integrity / Receipt Semantics

Status: DRAFT FOR ADVERSARIAL REVIEW.

Scope: Receipt identity/scope/subset semantics; package inventory; explicit external references; multi-Receipt resolution; ReceiptLink semantics; canonical representation; payload digest/signature scope; embedded/detached IntegrityEnvelope; signer/key-reference limits; tampering versus omission; privacy/integrity composition; independent verifier result model.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Design objective

Part H defines what a C2ATrace Receipt packages, what integrity mechanisms authenticate, how multiple Receipts can be resolved/linked, and what an independent verifier can actually conclude.

The central separations are:

~~~text
signature valid
≠
record true

receipt integrity valid
≠
receipt complete

package inventory complete
≠
runtime history complete

reference closure
≠
capture completeness

linked receipts valid
≠
no omitted receipt exists

hash/link chain intact
≠
global history complete

key verifies signature
≠
key owner identity verified

signing time recorded
≠
trusted timestamp

signed hash-only/redacted evidence
≠
signed unavailable plaintext
~~~

Integrity authenticates defined representations and linkages. It does not repair missing provenance or create external truth.

## 2. External standards basis

The baseline v0.1 integrity profile is grounded in:

- RFC 8785 JSON Canonicalization Scheme (JCS) for deterministic JSON canonicalization;
- SHA-256 for the payload digest;
- RFC 8032 Ed25519 for the baseline digital-signature algorithm.

JCS canonicalization yields deterministic UTF-8 bytes for compatible I-JSON data.

The exact JSON field names and binary/text encodings remain unfrozen until Schema work.

## 3. Receipt identity

### 3.1 Receipt role

A Receipt is a Package identity centered on one immutable Authenticated Receipt Payload plus zero or more non-identity-defining IntegrityEnvelope attachments.

Receipt is not a Run, Activity, Artifact, or Assertion.

A concrete transport serialization of one Receipt ARP together with some selected embedded/detached envelope material is a Receipt Presentation. Multiple Presentations can represent the same Receipt identity.

### 3.2 Receipt identity

Receipt identity is occurrence/package identity.

It is not derived solely from payload hash, signer key, Run identity, timestamp, or contained record IDs.

Two Receipts can contain representation-equivalent payloads while retaining distinct Receipt identities.

### 3.3 Receipt immutability

Once one Receipt identity denotes one Authenticated Receipt Payload, that same Receipt identity does not later denote a different Authenticated Receipt Payload.

Additional IntegrityEnvelopes can be associated with the same immutable Receipt payload without changing Receipt identity.

### 3.4 Receipt digest is not Receipt identity

A Receipt payload digest commits to one canonical payload representation.

Equal payload digests do not merge distinct Receipt identities.

## 4. Authenticated Receipt Payload

### 4.1 Definition

The Authenticated Receipt Payload (ARP) is the complete semantics-bearing Receipt payload used by the baseline digest/signature profile.

Conceptually it contains:

- Receipt identity;
- Receipt protocol/profile metadata;
- package inventory;
- included C2ATrace records;
- explicit ExternalReferences;
- ReceiptLinks;
- privacy descriptors/commitments that are part of the disclosed provenance;
- scope descriptors;
- any other field whose value changes a core protocol claim.

IntegrityEnvelope signature values are not part of the ARP.

### 4.2 Transport metadata

Transport-only metadata that is outside the ARP is not authenticated by the Receipt payload digest/signature.

Such metadata does not alter core provenance semantics.

### 4.3 Zero or more envelopes

A Receipt payload can exist with zero, one, or multiple IntegrityEnvelopes.

An unsigned Receipt can therefore be structurally evaluated while cryptographic authenticity remains not established.

## 5. Receipt inventory

### 5.1 Package inventory

A Receipt carries or deterministically defines an inventory of the records that are members of its ARP.

The inventory supports package-local statements such as:

> these records are included in this Receipt payload.

It does not establish that no other C2ATrace records exist.

### 5.2 Inventory completeness

Package inventory completeness means that the verifier can account for the record membership of the supplied ARP under the Receipt profile.

It is not capture completeness or Run completeness.

### 5.3 Inventory digesting

Because the inventory is part of the ARP, changing the included record set changes the canonical payload and therefore the baseline payload digest.

## 6. Receipt scope and subset semantics

### 6.1 Receipt can be a subset

A Receipt can intentionally contain only a subset of records from a Run, agent execution, provenance graph, time interval, or larger collection.

Subset Receipts are first-class.

### 6.2 Scope descriptor

A Receipt can describe its intended selection/scope, for example:

- one Run identifier;
- one or more root objects;
- a time window;
- an application-defined selection;
- unknown scope.

The scope descriptor is Producer-authored package metadata.

### 6.3 Scope does not imply completeness

A Receipt naming a Run, time interval, root object, or selection criterion does not prove that all records matching that scope are present.

Core v0.1 has no generic Receipt complete=true bit that establishes complete runtime history.

### 6.4 Three completeness concepts

Part H distinguishes:

~~~text
package inventory completeness
reference closure completeness
runtime/capture/history completeness
~~~

Package inventory completeness and reference closure can be evaluated against supplied data.

Runtime/capture/history completeness generally remains not established unless a future recognized completeness evidence profile supports it.

## 7. Internal and external references

### 7.1 InternalReference

An InternalReference identifies a target object inside the same Receipt payload.

### 7.2 ExternalReference

An ExternalReference is an explicit Reference form for a target object located in another Receipt.

Conceptually it identifies:

~~~text
target Receipt identity
+
target object identity
+
optional target object type
+
optional target Receipt payload-digest pin
~~~

The exact wire structure remains unfrozen.

### 7.3 Cross-Receipt address versus object identity

Conceptually:

~~~text
(receipt_id, object_id)
~~~

is a package-location address telling the resolver which Receipt occurrence should supply the referenced object.

The Receipt component does not redefine the underlying C2ATrace object identity.

The same immutable C2ATrace object identity can be packaged in multiple Receipts. When the same object identity appears more than once in one Resolution Set, the normal object-identity/immutability rules apply across all resolved occurrences.

### 7.4 Explicit externality

A reference to an object not included in the local Receipt must be explicitly represented as an ExternalReference under the external-reference-capable profile.

An ordinary unresolved local object ID is not silently reinterpreted as an external reference.

## 8. Receipt reference modes

Part H conceptually distinguishes two conformance modes:

~~~text
self-contained
external-references-allowed
~~~

A self-contained Receipt resolves all normative object references within its own ARP.

An external-reference-capable Receipt can contain explicit ExternalReferences.

An unresolved ExternalReference does not become an invented local object and does not silently disappear.

## 9. Multi-Receipt Resolution Set

### 9.1 Resolution Set

A Resolution Set is the set of Receipts and external resolution material actually available to one verifier invocation.

Resolution is relative to that supplied set/capability.

### 9.2 Unique resolution

An ExternalReference is uniquely resolved only when the verifier can identify one target Receipt/object pair matching the reference under the applicable resolution rules.

### 9.3 Ambiguity

If multiple supplied Receipt payloads claim the same Receipt identity while denoting different ARPs/payload digests, resolution by Receipt identity is ambiguous/conflicting.

The verifier does not select one by timestamp, input order, or signature count.

### 9.4 Unresolved reference

If the target Receipt/object is unavailable, the ExternalReference remains unresolved.

Dependent graph/type/content claims are correspondingly not established.

This does not prove the target never existed.

### 9.5 Cycle-safe resolution

Cross-Receipt ExternalReferences can create cycles at the package-reference level even when the Derivation DAG remains acyclic.

A verifier resolves them using cycle-safe graph traversal rather than recursive assumptions about package order.

## 10. ExternalReference pinning

### 10.1 Unpinned reference

A reference containing target Receipt identity/object identity but no target payload digest can be identifier-resolved.

It does not cryptographically bind the referring Receipt to one exact target Receipt payload.

### 10.2 Pinned reference

A reference carrying a target Receipt payload-digest pin binds the referring record to the exact target ARP commitment when the digest is independently matched.

### 10.3 Pin mismatch

If the supplied target Receipt identity matches but its payload digest does not match the recorded pin, the pinned ExternalReference is not successfully resolved to that payload.

### 10.4 Pin is not signature

Matching a target payload-digest pin does not establish that the target Receipt is signed, that its signer is trusted, or that its records are true.

## 11. Cross-Receipt graph semantics

After an ExternalReference is uniquely resolved, existing object-type, graph, Derivation, RequestBinding, Tool, Trust/Taint, and Privacy rules apply across the resolution boundary.

Resolution does not create stronger provenance than the referenced records themselves.

A cross-Receipt path remains a recorded provenance path rather than proof of model causality, external truth, or runtime completeness.

## 12. ReceiptLink

### 12.1 Purpose

ReceiptLink is package-level integrity/linkage metadata distinct from ExternalReference.

An ExternalReference points to a provenance object in another Receipt.

A ReceiptLink commits the current Receipt payload to a relationship with another Receipt payload.

### 12.2 Baseline prior link

The baseline ReceiptLink identifies:

~~~text
linked prior Receipt identity
+
linked prior Receipt payload digest
~~~

The link is included in the current ARP.

### 12.3 Multiple prior links

One Receipt can link to zero, one, or multiple prior Receipt payloads.

Multiple links support branching/merging execution and avoid imposing a false single total chain.

### 12.4 Link graph

Resolved prior-link edges define a package-level partial ordering.

The resolved prior-link subgraph is not a runtime total order.

### 12.5 No immediate-adjacency claim

A ReceiptLink says that the Producer linked the current Receipt to the referenced prior payload.

It does not establish that no other Receipt existed between them or on another branch.

## 13. Linkage and completeness

A valid supplied ReceiptLink establishes only the recorded committed relationship between the current ARP and the linked target digest.

It does not establish:

- complete Run history;
- complete Producer history;
- no omitted predecessor;
- no omitted successor;
- no omitted sibling/branch;
- true genesis;
- trusted chronology.

A verifier does not call the first Receipt in the supplied set the global genesis unless separate evidence establishes that claim.

## 14. Baseline canonical representation

### 14.1 JCS profile

The baseline v0.1 JSON integrity profile canonicalizes the ARP using RFC 8785 JCS.

JCS-compatible input is therefore constrained by the JCS/I-JSON requirements.

### 14.2 UTF-8 canonical bytes

The baseline digest input is the exact UTF-8 byte sequence output by RFC 8785 canonicalization of the ARP.

### 14.3 No independent reordering

A verifier follows the canonicalization profile.

It does not sort array elements, normalize Unicode string values, coerce numbers, remove nulls, or otherwise alter semantics beyond the declared canonicalization profile.

### 14.4 Duplicate property names

A Receipt payload that cannot be parsed/canonicalized according to the baseline JCS/I-JSON profile cannot obtain baseline canonical-integrity success.

## 15. Baseline payload digest

The baseline v0.1 Receipt payload digest is SHA-256 over the canonical ARP bytes.

Conceptually:

~~~text
canonical_payload = JCS_UTF8(ARP)
payload_digest = SHA256(canonical_payload)
~~~

The payload digest is a computational representation commitment under the selected digest profile/security assumptions.

It is not factual truth, signer identity, capture completeness, mathematical proof of collision impossibility, or Receipt occurrence identity.

## 16. IntegrityEnvelope

### 16.1 Role

IntegrityEnvelope is integrity metadata that authenticates a defined Receipt payload commitment under a signature profile.

It is not a runtime provenance node.

### 16.2 Envelope identity

Each IntegrityEnvelope has its own occurrence identity.

Multiple envelopes can authenticate the same Receipt payload.

### 16.3 Envelope placement

An IntegrityEnvelope can be transported:

~~~text
embedded alongside the Receipt payload
or
detached from the Receipt payload
~~~

Embedded and detached forms have the same authentication semantics when they reference the same ARP commitment.

## 17. Baseline signature profile

The baseline v0.1 signature algorithm is Ed25519 as defined by RFC 8032.

The signature does not recursively sign its own signature value.

Instead, the envelope signs a deterministic C2ATrace Signing Statement.

Conceptually, the Signing Statement binds:

~~~text
C2ATrace signature domain separator
Receipt identity
Receipt payload digest
canonicalization profile identifier
digest algorithm identifier
signature algorithm/profile identifier
verification-key reference/fingerprint
semantically interpreted signed envelope metadata
~~~

The exact serialized field names remain unfrozen.

## 18. Domain separation and algorithm binding

The Signing Statement includes a C2ATrace-specific signature domain/context and the relevant algorithm/profile identifiers.

This prevents the same raw signature input from being silently reinterpreted as a different C2ATrace object/profile.

Algorithm identifiers used to interpret verification are authenticated by the signature input rather than left as unauthenticated switching metadata.

## 19. Embedded versus detached envelopes

### 19.1 Embedded envelope

An embedded envelope travels with the Receipt package but remains outside the ARP whose digest it authenticates.

### 19.2 Detached envelope

A detached envelope identifies the Receipt identity and payload digest it authenticates.

The verifier must bind the detached envelope to the exact supplied ARP before reporting signature success for that Receipt.

### 19.3 Envelope addition/removal

Adding another valid IntegrityEnvelope does not change the ARP or its payload digest.

Removing an envelope likewise does not mutate the ARP; it removes available authentication evidence.

Unless a higher-level container authenticates the envelope set, absence of an envelope is not automatically detectable as payload tampering.

## 20. Signer and key-reference limits

### 20.1 Verification key

Cryptographic signature verification establishes that a signature validates under specific verification-key material for the defined Signing Statement.

### 20.2 Key reference

A key identifier, URI, fingerprint label, account label, or signer name is recorded identity metadata.

It does not by itself establish real-world ownership of the corresponding verification key.

### 20.3 Key resolution

If the verifier cannot obtain/resolve the verification key required by the envelope, cryptographic signature validity remains unresolved rather than guessed.

### 20.4 Key trust

Key authenticity, organizational ownership, certificate/PKI trust, revocation, compromise, authorization, and governance are separate evidence/policy questions.

Core v0.1 does not infer them merely from successful Ed25519 verification.

### 20.5 Signing time

A signed signing-time value, when present, establishes that the signer authenticated that timestamp representation.

It is not a trusted wall-clock timestamp without a separate trusted-time profile.

## 21. Integrity versus truth

A cryptographically valid signed Receipt can still contain:

- false source metadata;
- fabricated observations;
- incorrect Derivation;
- incorrect Trust/Taint assertions;
- incomplete history;
- tool-server lies;
- false EffectObservation claims.

Integrity makes the signed representation tamper-evident relative to the signing key.

It does not make the representation factually true.

## 22. Tampering versus omission

### 22.1 Post-signing payload mutation

The verifier recomputes the baseline digest from the supplied ARP.

If the recomputed digest differs from the authenticated payload digest, the corresponding envelope does not bind to the modified ARP.

Digest-based tamper evidence remains computational and relies on the selected digest algorithm's security assumptions.

### 22.2 Removing a record from a signed ARP

Removing or changing an included record changes the canonical ARP input that must be re-digested.

The modified payload retains digest-match status only if the recomputed digest actually matches the authenticated digest under the selected profile.

### 22.3 Producer omission before signing

If a Producer omits a real event/record before creating the ARP and then correctly signs the incomplete ARP, signature verification cannot detect the omitted real-world event.

### 22.4 Whole-Receipt omission

Removing an entire Receipt from a larger collection does not necessarily invalidate the remaining Receipts.

It is detectable only when remaining supplied evidence contains a dependency/link that requires the omitted Receipt.

### 22.5 Chain truncation

A valid linked prefix, suffix, branch, or subset can remain cryptographically valid even when other Receipts are omitted.

Therefore intact supplied linkage does not prove complete history.

## 23. Replay and freshness

A valid Receipt can be replayed/copied and still have a valid signature.

Signature validity does not establish freshness, first-seen time, uniqueness of presentation, or non-replay.

Receipt identity distinguishes the logical package, not each transport presentation of it.

Trusted freshness requires a separate timestamping/transparency/nonce protocol.

## 24. Privacy and integrity composition

### 24.1 Full Receipt

If plaintext is included in the ARP, the signature authenticates that disclosed plaintext representation as part of the signed payload.

### 24.2 Hash-only Receipt

If original content is withheld and only an unkeyed commitment is in the ARP, the signature authenticates the recorded commitment metadata/value, not unavailable plaintext bytes directly.

A later candidate can be commitment-matched under Part G, producing a composed claim rather than retroactively changing the signed bytes.

### 24.3 HMAC Receipt

If the ARP contains an HMAC/keyed commitment, the Receipt signature authenticates the recorded tag/profile metadata.

It does not grant the HMAC secret or establish candidate matching for a verifier lacking that capability.

### 24.4 Redacted Receipt

If the ARP discloses a redacted derivative, the signature authenticates the redacted derivative and its recorded lineage/commitment metadata as included in the ARP.

It does not authenticate unavailable original plaintext as if that plaintext were directly included.

### 24.5 Signed commitment plus later candidate

When a candidate later matches a commitment value that was authenticated by a valid Receipt signature, the verifier can report:

> candidate matches a commitment value authenticated by the signature under the applicable profile.

It does not need to misstate that the signature directly contained/signed the unavailable candidate representation.

## 25. Reference/integrity composition

Resolving an ExternalReference and validating the target Receipt signature are separate operations.

A target can be:

- unresolved;
- resolved but unpinned;
- resolved and digest-pinned;
- resolved with valid target Receipt integrity evidence;
- resolved with unresolved/invalid/unsupported target integrity evidence.

The verifier preserves these dimensions rather than collapsing them into one "resolved and trusted" state.

## 26. Independent verifier result model

Part H rejects one overloaded boolean such as:

~~~text
verified = true
~~~

A verifier conceptually reports orthogonal result dimensions including:

1. parsing/profile compatibility;
2. Receipt/package structural validity;
3. package inventory status;
4. reference-resolution/closure status;
5. canonicalization status;
6. payload-digest status;
7. per-IntegrityEnvelope signature status;
8. key-resolution status;
9. cross-Receipt link status;
10. privacy-dependent evidence capability;
11. per-claim semantic verification/evidence status;
12. runtime/history completeness status.

The exact output schema remains for the Verifier Contract.

## 27. Receipt validity vocabulary

Part H distinguishes:

~~~text
structurally valid / invalid
references resolved / unresolved / ambiguous
digest matched / mismatched / unavailable
signature valid / invalid / unresolved-key / unsupported-profile / absent
claim established / asserted / matched / unknown / unverified
runtime-history completeness not established
~~~

Exact machine enum spelling remains unfrozen.

The verifier does not use "fully verified" as shorthand for all dimensions.

## 28. Normative Receipt requirements

### RCPT-001 — Receipt identity is occurrence/package identity

A verifier MUST NOT merge distinct Receipt identities solely because their non-identity payload content, Run IDs, timestamps, or IntegrityEnvelopes match.

Planned test: receipt-identity-no-merge-001.

### RCPT-002 — Receipt payload identity is immutable

The same Receipt identity MUST NOT denote two different Authenticated Receipt Payloads within one resolution context.

Planned test: receipt-id-payload-conflict-001.

### RCPT-003 — Payload digest is not Receipt identity

A verifier MUST NOT infer Receipt identity equality solely from equal payload digests.

Planned test: receipt-digest-not-identity-001.

### RCPT-004 — IntegrityEnvelope count does not define Receipt identity

A verifier MUST NOT create a new Receipt identity solely because IntegrityEnvelopes are added, removed, embedded, or detached while the ARP remains unchanged.

Planned test: receipt-envelope-no-new-identity-001.

### RCPT-005 — Unsigned Receipt is structurally representable

A conforming representation MUST permit a Receipt ARP with zero IntegrityEnvelopes.

Planned test: receipt-unsigned-valid-structure-001.

### RCPT-006 — Package inventory is explicit/deterministic

A conforming Receipt MUST provide or deterministically define the membership inventory of records included in its ARP.

Planned test: receipt-inventory-001.

### RCPT-007 — Inventory completeness is package-local

A verifier MUST NOT report package inventory completeness as Run/runtime/capture/history completeness.

Planned test: receipt-inventory-not-history-001.

### RCPT-008 — Scope descriptor does not establish completeness

A verifier MUST NOT infer complete coverage solely because a Receipt declares a Run ID, root object, time window, or selection scope.

Planned test: receipt-scope-no-completeness-001.

### RCPT-009 — Subset Receipt is valid

A conforming representation MUST permit a Receipt to contain a proper subset of a larger Run/provenance graph.

Planned test: receipt-subset-valid-001.

### RCPT-010 — Missing record is not negative proof

Absence of a record from a Receipt MUST NOT be reported as proof that the runtime event/object never existed.

Planned test: receipt-missing-record-not-negation-001.

### RCPT-011 — Runtime completeness is separate

A verifier MUST NOT report runtime/capture/history completeness unless a recognized completeness evidence profile establishes the claimed scope.

Planned test: receipt-runtime-completeness-not-established-001.

### RCPT-012 — InternalReference stays local

An InternalReference MUST resolve to an object in the same Receipt ARP.

Planned test: receipt-internal-reference-local-001.

### RCPT-013 — Externality is explicit

A reference whose target is not included in the local ARP MUST be explicitly represented as an ExternalReference under an external-reference-capable profile.

Planned test: receipt-external-reference-explicit-001.

### RCPT-014 — Dangling local reference is not implicit external reference

A verifier MUST NOT reinterpret an unresolved local object ID as an ExternalReference merely because another Receipt contains a matching object ID.

Planned test: receipt-no-implicit-external-resolution-001.

### RCPT-015 — ExternalReference identifies target Receipt and object

A conforming ExternalReference MUST identify a target Receipt identity and target object identity.

Planned test: receipt-external-reference-address-001.

### RCPT-016 — Cross-Receipt address does not redefine object identity

A verifier MUST NOT treat the Receipt component of an ExternalReference address as creating a new underlying C2ATrace object identity when the referenced object ID denotes an existing identity in the Resolution Set.

Planned test: receipt-address-vs-object-identity-001.

### RCPT-017 — Optional target type is not self-verifying

A recorded target-object type in an ExternalReference MUST NOT be reported as verified until the target is resolved and type compatibility is checked.

Planned test: receipt-external-type-resolution-001.

### RCPT-018 — Unresolved ExternalReference remains unresolved

A verifier MUST NOT invent, substitute, or silently drop an unavailable ExternalReference target.

Planned test: receipt-external-unresolved-001.

### RCPT-019 — Unresolved does not mean nonexistent

A verifier MUST NOT report an unresolved ExternalReference as proof that the referenced target never existed.

Planned test: receipt-external-unresolved-not-negation-001.

### RCPT-020 — Unique resolution is required

A verifier MUST NOT report an ExternalReference as uniquely resolved when multiple incompatible target Receipt/object candidates satisfy the unpinned identifier fields.

Planned test: receipt-external-ambiguous-001.

### RCPT-021 — Receipt ID collision is preserved as conflict

If two supplied ARPs use the same Receipt identity but have different payload commitments/contents, a verifier MUST report an identity conflict and MUST NOT choose one by timestamp, signature count, or input order.

Planned test: receipt-id-collision-001.

### RCPT-022 — Unpinned resolution is not payload binding

A verifier MUST NOT report an unpinned ExternalReference as cryptographically bound to the exact resolved target Receipt payload solely from Receipt/object identifier equality.

Planned test: receipt-external-unpinned-bounded-001.

### RCPT-023 — Pinned reference binds target payload commitment

When an ExternalReference includes a target Receipt payload-digest pin, successful pinned resolution MUST require the resolved target ARP to match that digest under the declared compatible digest profile.

Planned test: receipt-external-pin-match-001.

### RCPT-024 — Pin mismatch blocks pinned resolution

A verifier MUST NOT report a pinned ExternalReference as successfully resolved to a target ARP whose payload digest mismatches the recorded pin.

Planned test: receipt-external-pin-mismatch-001.

### RCPT-025 — Pin match is not target signature validity

A verifier MUST NOT infer target Receipt signature validity, signer trust, factual truth, or completeness solely from a matching ExternalReference payload pin.

Planned test: receipt-external-pin-not-signature-001.

### RCPT-026 — Resolution does not prove runtime timing

A verifier MUST NOT infer that a resolved external target existed at a particular runtime wall-clock time solely from the reference and resolution relationship.

Planned test: receipt-external-no-time-proof-001.

### RCPT-027 — Resolution does not create causality

A verifier MUST NOT upgrade a cross-Receipt provenance path to model/tool/external causal responsibility merely because all ExternalReferences resolve.

Planned test: receipt-external-no-causal-upgrade-001.

### RCPT-028 — Cross-Receipt resolver is cycle-safe

A conforming verifier MUST handle cyclic ExternalReference package dependencies without infinite recursion or implicit ordering assumptions.

Planned test: receipt-external-cycle-safe-001.

### RCPT-029 — Self-contained mode has no unresolved normative targets

A Receipt claiming the self-contained reference mode MUST resolve all normative object references within its own ARP.

Planned test: receipt-self-contained-001.

### RCPT-030 — External-reference mode preserves unresolved dependencies

An external-reference-capable Receipt MAY remain structurally parseable when some explicit ExternalReferences are unavailable, but a verifier MUST report the dependent resolution/graph checks as unresolved rather than successful.

Planned test: receipt-external-mode-unresolved-001.

### RCPT-031 — ReceiptLink is distinct from ExternalReference

A verifier MUST NOT interpret ReceiptLink as an object-level ExternalReference or infer a specific provenance-object relationship solely from ReceiptLink.

Planned test: receipt-link-not-object-reference-001.

### RCPT-032 — Baseline ReceiptLink is digest-pinned

A baseline prior ReceiptLink MUST identify the linked prior Receipt identity and its payload digest.

Planned test: receipt-link-pinned-001.

### RCPT-033 — ReceiptLink is part of current ARP

A baseline ReceiptLink MUST be included in the current Receipt's ARP so that the current payload digest/signature commits to the recorded linkage.

Planned test: receipt-link-in-payload-001.

### RCPT-034 — No self prior-link

A Receipt MUST NOT identify its own Receipt identity/payload digest as its own prior ReceiptLink target.

Planned test: receipt-link-no-self-001.

### RCPT-035 — Resolved prior-link graph is acyclic

The resolved directed graph of baseline prior ReceiptLinks MUST be acyclic.

Planned test: receipt-link-cycle-001.

### RCPT-036 — Multiple prior links are permitted

A conforming representation MUST permit one Receipt to carry multiple prior ReceiptLinks.

Planned test: receipt-link-multiple-priors-001.

### RCPT-037 — ReceiptLink does not impose total order

A verifier MUST NOT impose a total Receipt order solely from a partial ReceiptLink graph.

Planned test: receipt-link-no-total-order-001.

### RCPT-038 — ReceiptLink is not immediate adjacency proof

A verifier MUST NOT report a prior ReceiptLink as proof that no omitted Receipt occurred between or alongside the linked Receipts.

Planned test: receipt-link-no-adjacency-proof-001.

### RCPT-039 — Linked set is not complete history

A verifier MUST NOT infer from valid supplied ReceiptLinks that no earlier, later, sibling, branch, or otherwise omitted Receipt exists.

Planned test: receipt-link-no-global-completeness-001.

### RCPT-040 — First supplied Receipt is not genesis proof

A verifier MUST NOT describe the earliest/first supplied Receipt as the global genesis of a Run/Producer history without separate evidence.

Planned test: receipt-no-genesis-inference-001.

### RCPT-041 — Missing linked target is unresolved dependency

If a supplied ReceiptLink target is unavailable, a verifier MUST report the link target as unresolved and MUST NOT silently delete the link from the current Receipt semantics.

Planned test: receipt-link-target-missing-001.

### RCPT-042 — Timestamps do not override links

A verifier MUST NOT use wall-clock timestamp ordering to reverse or override an explicit valid ReceiptLink dependency.

Planned test: receipt-link-timestamp-conflict-001.

### RCPT-043 — ReceiptLink does not establish trusted chronology

A verifier MUST NOT report ReceiptLink as trusted wall-clock chronology or timestamp evidence.

Planned test: receipt-link-no-trusted-time-001.

### RCPT-044 — Reference closure is not capture completeness

A verifier MUST NOT report a fully reference-resolved Receipt/Resolution Set as complete runtime/capture/history evidence solely because all explicit references resolve.

Planned test: receipt-reference-closure-not-history-001.

### RCPT-045 — Reference absence is not no-dependency proof

Absence of an ExternalReference or ReceiptLink MUST NOT be reported as proof that no omitted cross-Receipt relation/dependency existed.

Planned test: receipt-reference-absence-not-negation-001.

### RCPT-046 — Privacy cannot create dangling normative references silently

A privacy transformation/export MUST NOT remove a required referenced record while leaving an ordinary unresolved local reference and still claim self-contained Receipt conformance.

Planned test: receipt-privacy-reference-closure-001.

### RCPT-047 — Resolution status is capability-relative

A verifier MUST evaluate cross-Receipt resolution against the actual Resolution Set/capabilities it possesses and MUST NOT report unavailable external targets as resolved by assumption.

Planned test: receipt-resolution-capability-001.

### RCPT-048 — Receipt subset semantics survive valid linkage

A Receipt that links to other Receipts MUST NOT be treated as a complete superseding aggregate unless an explicit recognized aggregation/completeness profile establishes that stronger claim.

Planned test: receipt-linked-subset-not-aggregate-001.

### RCPT-049 — Repeated object identity across Receipts must remain representation-consistent

When the same immutable Artifact/object identity is supplied by multiple Receipts in one Resolution Set, a verifier MUST enforce the applicable identity/immutability constraints across those occurrences and MUST report incompatible representations as an identity conflict.

Planned test: receipt-cross-receipt-object-consistency-001.

### RCPT-050 — Resolved cross-Receipt Derivation graph remains acyclic

After resolving ExternalReferences, the combined explicit Artifact Derivation graph across the Resolution Set MUST satisfy GRAPH-003 and remain acyclic.

Planned test: receipt-cross-receipt-derivation-cycle-001.

### RCPT-051 — Receipt Presentation does not define new Receipt identity

A verifier MUST NOT create a new Receipt identity solely because the same Receipt ARP is transported with different serialization wrappers, embedded/detached envelope placement, or a different subset/order of non-identity-defining IntegrityEnvelope attachments.

Planned test: receipt-presentation-no-new-identity-001.

## 29. Normative Integrity requirements

### INTG-001 — Baseline canonicalization profile

A baseline v0.1 signed Receipt ARP MUST use RFC 8785 JCS canonicalization unless an explicitly different future integrity profile is selected.

Planned test: integrity-jcs-profile-001.

### INTG-002 — Baseline canonicalization requires compatible JSON

A Receipt that cannot be parsed/canonicalized under the selected JCS/I-JSON profile MUST NOT report baseline canonicalization success.

Planned test: integrity-jcs-input-validity-001.

### INTG-003 — Canonical digest bytes are UTF-8 JCS output

The baseline payload digest MUST be computed over the exact UTF-8 bytes produced by RFC 8785 canonicalization of the ARP.

Planned test: integrity-jcs-utf8-bytes-001.

### INTG-004 — Duplicate JSON names are not accepted by baseline canonicalization

A verifier MUST NOT accept duplicate JSON object property names as a valid baseline JCS Receipt payload.

Planned test: integrity-jcs-duplicate-name-001.

### INTG-005 — Verifier does not add Unicode normalization

A verifier MUST NOT Unicode-normalize string values beyond the selected canonicalization profile before computing the baseline payload digest.

Planned test: integrity-jcs-no-unicode-normalize-001.

### INTG-006 — Verifier does not reorder arrays

A verifier MUST NOT reorder Receipt array elements before canonicalization unless the future Schema/profile itself defines a prior deterministic semantic transformation that produces the ARP.

Planned test: integrity-jcs-array-order-001.

### INTG-007 — Baseline payload digest is SHA-256

The baseline v0.1 Receipt payload-digest profile MUST use SHA-256 over the canonical ARP bytes.

Planned test: integrity-sha256-profile-001.

### INTG-008 — Digest scope is the complete ARP

The baseline payload digest MUST commit to the complete Authenticated Receipt Payload, not merely the included runtime records.

Planned test: integrity-digest-complete-arp-001.

### INTG-009 — Semantics-bearing fields are inside ARP

A field whose value changes a core Receipt/provenance/privacy/reference/link claim MUST NOT be excluded from the ARP under the baseline profile.

Planned test: integrity-semantic-field-authenticated-001.

### INTG-010 — IntegrityEnvelope signature value is outside ARP

The baseline ARP MUST NOT include the IntegrityEnvelope signature value being used to authenticate that same ARP.

Planned test: integrity-no-self-signature-recursion-001.

### INTG-011 — Transport metadata outside ARP is unauthenticated

A verifier MUST NOT treat transport-only metadata outside the ARP as authenticated by the Receipt payload digest/signature.

Planned test: integrity-transport-metadata-bounded-001.

### INTG-012 — Transport metadata cannot alter core semantics

A conforming verifier MUST NOT use unauthenticated transport-only metadata to override authenticated ARP semantics.

Planned test: integrity-transport-no-override-001.

### INTG-013 — Digest match is representation integrity only

A verifier MUST NOT report payload-digest success as factual truth, Producer honesty, external origin truth, or capture completeness.

Planned test: integrity-digest-no-truth-001.

### INTG-014 — Digest match is not Receipt identity equality

A verifier MUST NOT merge Receipt identities solely because their baseline payload digests match.

Planned test: integrity-digest-no-receipt-identity-001.

### INTG-015 — Baseline signature algorithm is Ed25519

A baseline v0.1 digital-signature IntegrityEnvelope MUST use Ed25519 under the selected baseline profile.

Planned test: integrity-ed25519-profile-001.

### INTG-016 — Signature input is domain-separated

The baseline Signing Statement MUST include a C2ATrace-specific domain/context value.

Planned test: integrity-signature-domain-001.

### INTG-017 — Signature binds Receipt identity

The baseline Signing Statement MUST authenticate the Receipt identity associated with the payload digest.

Planned test: integrity-signature-receipt-id-001.

### INTG-018 — Signature binds payload digest

The baseline Signing Statement MUST authenticate the exact Receipt payload digest it claims to sign.

Planned test: integrity-signature-payload-digest-001.

### INTG-019 — Signature binds canonicalization/digest algorithms

The baseline Signing Statement MUST authenticate the canonicalization and digest profile identifiers used to interpret the payload commitment.

Planned test: integrity-signature-algorithm-binding-001.

### INTG-020 — Signature binds signature profile

The baseline Signing Statement MUST authenticate the signature algorithm/profile identifier used to interpret the signature.

Planned test: integrity-signature-profile-binding-001.

### INTG-021 — Signature binds verification-key reference

The baseline Signing Statement MUST authenticate the verification-key reference/fingerprint used as signer/key metadata for that envelope.

Planned test: integrity-signature-keyref-binding-001.

### INTG-022 — Interpreted envelope metadata is authenticated

Semantically interpreted IntegrityEnvelope metadata other than the signature value and explicitly transport-only metadata MUST be included in the authenticated Signing Statement or otherwise cryptographically bound by the selected profile.

Planned test: integrity-envelope-metadata-authenticated-001.

### INTG-023 — Signature value is not recursively signed

The signature value itself MUST NOT be included as an input field that requires its own value to compute the same signature.

Planned test: integrity-signature-no-recursion-001.

### INTG-024 — Embedded envelope does not change ARP

Embedding an IntegrityEnvelope alongside an unchanged ARP MUST NOT change the baseline ARP payload digest.

Planned test: integrity-embedded-envelope-stable-digest-001.

### INTG-025 — Detached envelope targets exact Receipt commitment

A detached IntegrityEnvelope MUST identify the Receipt identity and payload digest it authenticates.

Planned test: integrity-detached-envelope-target-001.

### INTG-026 — Detached digest mismatch is not valid binding

A verifier MUST NOT report detached-envelope signature success for a supplied Receipt whose Receipt identity/payload digest does not match the envelope's authenticated target.

Planned test: integrity-detached-mismatch-001.

### INTG-027 — Multiple envelopes are allowed

A conforming representation MUST permit multiple IntegrityEnvelopes to authenticate one Receipt ARP.

Planned test: integrity-multiple-envelopes-001.

### INTG-028 — Envelope identity is occurrence-based

A verifier MUST NOT merge distinct IntegrityEnvelope identities solely because signer key, signature value, payload digest, or profile matches.

Planned test: integrity-envelope-no-merge-001.

### INTG-029 — Adding envelope does not imply stronger truth

A verifier MUST NOT upgrade factual/provenance/completeness claims solely because additional signatures are attached to the same ARP.

Planned test: integrity-multisig-no-truth-upgrade-001.

### INTG-030 — Removing envelope reduces evidence, not payload identity

Removal of an IntegrityEnvelope from a package MUST NOT be reported as mutation of the unchanged ARP, while the verifier MUST reflect that the removed authentication evidence is no longer available.

Planned test: integrity-envelope-removal-001.

### INTG-031 — Signature validity is key-relative cryptographic validity

A verifier reporting signature=valid MUST identify or bind that result to the verification-key material/reference actually used.

Planned test: integrity-signature-key-relative-001.

### INTG-032 — Key reference is not real-world identity proof

A verifier MUST NOT report a key ID, URI, label, signer name, or fingerprint alone as verified real-world signer identity.

Planned test: integrity-keyref-no-real-identity-001.

### INTG-033 — Valid signature does not prove key ownership

A verifier MUST NOT infer organizational/user ownership or authorization of a verification key solely because a signature verifies under that key.

Planned test: integrity-key-no-ownership-proof-001.

### INTG-034 — Unresolved key means unresolved signature verification

If the required verification key cannot be resolved, a verifier MUST NOT report the cryptographic signature as valid or invalid by guess; it remains unresolved-key/not-established.

Planned test: integrity-key-unresolved-001.

### INTG-035 — Wrong-key verification failure is invalid for that envelope/key

If the resolved key/profile is applicable and Ed25519 verification fails, a verifier MUST NOT report the envelope signature as valid.

Planned test: integrity-signature-invalid-001.

### INTG-036 — Unsupported profile is not successful verification

A verifier that does not implement the declared canonicalization/digest/signature profile MUST NOT report the envelope as cryptographically verified.

Planned test: integrity-profile-unsupported-001.

### INTG-037 — Cryptographic validity does not establish key trust

A verifier MUST NOT restate successful signature verification as trusted signer, authorized signer, uncompromised key, non-revoked key, or approved organization without separate trust/policy evidence.

Planned test: integrity-signature-no-key-trust-001.

### INTG-038 — Signing time is not trusted time

A verifier MUST NOT report a signed signing-time field as trusted wall-clock time without a separate trusted timestamp/time-evidence profile.

Planned test: integrity-signing-time-bounded-001.

### INTG-039 — Valid signature is not record truth

A verifier MUST NOT report a cryptographically valid Receipt signature as proof that its provenance/assertion contents are factually true.

Planned test: integrity-signature-no-truth-001.

### INTG-040 — Valid signature is not capture completeness

A verifier MUST NOT report a cryptographically valid Receipt signature as proof of capture, Run, or history completeness.

Planned test: integrity-signature-no-completeness-001.

### INTG-041 — Signed fabricated data remains possible

A verifier MUST preserve that a valid signer can sign incorrect, fabricated, or maliciously incomplete C2ATrace records.

Planned test: integrity-signed-fabrication-001.

### INTG-042 — Omission before signing is not detected by signature

A verifier MUST NOT claim that signature validity detects records/events omitted by the Producer before ARP creation.

Planned test: integrity-pre-sign-omission-001.

### INTG-043 — Recomputed digest mismatch breaks envelope binding

A verifier MUST report payload-digest mismatch when SHA-256 recomputation over the supplied canonical ARP produces a value different from the authenticated payload digest.

Planned test: integrity-post-sign-tamper-001.

### INTG-044 — Deleting record requires digest recomputation

After an included ARP record is removed or changed, a verifier MUST recompute the canonical ARP digest and MUST NOT retain prior digest-match status without a fresh matching recomputation.

Planned test: integrity-signed-record-deletion-001.

### INTG-045 — Whole-Receipt omission can remain undetected

A verifier MUST NOT claim that valid signatures on supplied Receipts prove that no entire Receipt was omitted from the supplied Resolution Set.

Planned test: integrity-whole-receipt-omission-001.

### INTG-046 — Valid linkage is not no-omission proof

A verifier MUST NOT infer from a valid resolved ReceiptLink graph that no unlinked/omitted Receipt, branch, sibling, predecessor, or successor exists.

Planned test: integrity-linkage-no-omission-proof-001.

### INTG-047 — Replay is not detected by signature validity

A verifier MUST NOT report a valid signature as proof that a Receipt is fresh, newly observed, non-replayed, or presented only once.

Planned test: integrity-signature-no-freshness-001.

### INTG-048 — Signed hash-only Receipt authenticates disclosed commitment evidence

For hash_only content, a verifier MUST describe Receipt signature scope as authenticating the disclosed commitment/profile metadata and ARP representation, not unavailable plaintext directly.

Planned test: integrity-hashonly-signing-scope-001.

### INTG-049 — Signed HMAC Receipt does not grant HMAC capability

A verifier MUST NOT infer candidate HMAC verification capability or possession of the HMAC secret solely from a valid Receipt signature over the HMAC tag/profile metadata.

Planned test: integrity-hmac-signature-no-secret-001.

### INTG-050 — Signed redacted Receipt authenticates redacted evidence only

A verifier MUST NOT report a valid signature over a redacted ARP as direct signature authentication of unavailable pre-redaction plaintext.

Planned test: integrity-redacted-signing-scope-001.

### INTG-051 — Signed commitment plus candidate match uses composed wording

When a later candidate matches a commitment authenticated by a valid Receipt signature, a verifier MUST preserve the two-premise composition and MUST NOT falsely state that unavailable candidate bytes were directly present in the signed ARP.

Planned test: integrity-signed-commitment-candidate-001.

### INTG-052 — Signature does not prove redaction effectiveness

A verifier MUST NOT infer that redaction removed all sensitive content solely because the redacted Receipt/lineage is signed.

Planned test: integrity-signature-no-redaction-proof-001.

### INTG-053 — Integrity does not strengthen privacy claims

A verifier MUST NOT infer confidentiality, secure deletion, anonymity, unlinkability, or non-disclosure solely from Receipt digest/signature success.

Planned test: integrity-no-privacy-upgrade-001.

### INTG-054 — Structural validity and signature validity are separate

A verifier MUST NOT collapse Receipt structural/reference validation and cryptographic signature validation into one undifferentiated success state.

Planned test: integrity-structural-vs-signature-001.

### INTG-055 — Per-envelope signature status is separate

When a Receipt has multiple IntegrityEnvelopes, a verifier MUST evaluate/report cryptographic status per envelope rather than replacing all envelopes with one aggregate signature boolean.

Planned test: integrity-per-envelope-status-001.

### INTG-056 — Key-resolution status is separate

A verifier MUST distinguish an invalid signature from a signature that could not be evaluated because required key material was unresolved.

Planned test: integrity-invalid-vs-unresolved-key-001.

### INTG-057 — Unsupported profile is separate from invalid cryptography

A verifier MUST distinguish unsupported algorithm/profile from a supported-profile cryptographic verification failure.

Planned test: integrity-unsupported-vs-invalid-001.

### INTG-058 — Completeness status remains separate

A verifier MUST report runtime/history completeness separately from package/reference/digest/signature success and MUST NOT default it to complete.

Planned test: integrity-verifier-completeness-dimension-001.

### INTG-059 — Claim verification remains per-claim

A valid Receipt signature MUST NOT automatically upgrade every contained provenance/assertion claim to independently verified; each claim remains evaluated under its own evidence basis.

Planned test: integrity-per-claim-evidence-001.

### INTG-060 — No fully-verified shorthand

A conforming verifier MUST NOT use an unqualified "fully verified" or equivalent overall verdict when unresolved reference, claim-evidence, signer-identity, privacy-capability, or completeness dimensions remain not established.

Planned test: integrity-no-fully-verified-shorthand-001.

### INTG-061 — Weakest unresolved premise is preserved

When an integrity-supported conclusion composes digest, signature, reference-resolution, privacy capability, and provenance premises, verifier output MUST preserve the weakest unresolved/Producer-asserted premise rather than report only the strongest cryptographic component.

Planned test: integrity-composed-claim-bounded-001.

### INTG-062 — Signature failure does not prove record false

A verifier MUST NOT infer factual falsehood of the Receipt contents solely because an IntegrityEnvelope signature is invalid.

Planned test: integrity-invalid-signature-not-falsehood-001.

### INTG-063 — Unsigned does not mean structurally invalid

A verifier MUST NOT report a Receipt as structurally invalid solely because no IntegrityEnvelope is present.

Planned test: integrity-unsigned-structure-001.

### INTG-064 — Signed ARP does not authenticate external target payload unless pinned/linked

A valid signature over a Receipt containing an unpinned ExternalReference MUST NOT be reported as signature authentication of the externally resolved target Receipt payload.

Planned test: integrity-unpinned-external-target-001.

### INTG-065 — Pinned target digest plus current signature authenticates the recorded pin

When a signed Receipt contains a pinned ExternalReference/ReceiptLink, the current Receipt signature authenticates the recorded target digest value as part of the ARP; it does not by itself verify the target Receipt signature or truth.

Planned test: integrity-signed-pin-bounded-001.

### INTG-066 — Signed link graph is supplied linkage only

Even when every supplied ReceiptLink is included in valid signed ARPs and every digest pin resolves, a verifier MUST NOT report the resulting graph as complete global history.

Planned test: integrity-signed-linkage-not-history-001.

### INTG-067 — Signing Statement uses deterministic canonical bytes

The baseline Ed25519 signature input MUST be the UTF-8 bytes of the baseline RFC 8785 JCS-canonicalized C2ATrace Signing Statement.

Planned test: integrity-signing-statement-jcs-001.

### INTG-068 — IntegrityEnvelope identity is authenticated when semantically present

If an IntegrityEnvelope identity is part of the protocol representation, the baseline Signing Statement MUST cryptographically bind that envelope identity so it cannot be substituted without invalidating the signature.

Planned test: integrity-envelope-id-binding-001.

### INTG-069 — Cryptographic integrity wording is computationally bounded

A verifier MUST NOT describe SHA-256 digest matching or Ed25519 signature validity as mathematical proof that collisions, forgeries, or key compromise are impossible; results are reported under the selected cryptographic profile/security assumptions.

Planned test: integrity-crypto-assumption-wording-001.

### INTG-070 — Digest match is profile-relative commitment match

A verifier reporting payload-digest success MUST describe it as a match under the selected canonicalization/digest profile and MUST NOT upgrade it to stronger factual/completeness claims.

Planned test: integrity-digest-match-profile-relative-001.

## 30. Adversarial architecture review

### Review A — Same payload exported twice with different Receipt IDs

The Receipts remain distinct package occurrences even if their canonical ARP bytes or payload digest are equal.

Result: RESOLVED by RCPT-001 through RCPT-004.

### Review B — Add a second signature later

The ARP and payload digest remain unchanged.

The new IntegrityEnvelope adds authentication evidence without changing Receipt identity.

Result: RESOLVED by RCPT-004, INTG-024, and INTG-027.

### Review C — Remove one embedded signature

The ARP remains unchanged but that signature evidence is absent.

This is not ARP tampering unless a higher-level signed container commits to the envelope set.

Result: RESOLVED by INTG-030.

### Review D — Receipt contains only a subgraph of a Run

The Receipt can be structurally/integrity valid without implying that omitted Run records do not exist.

Result: RESOLVED by RCPT-007 through RCPT-011.

### Review E — Receipt says run_id=R

That scopes/group-labels the package but does not establish "all records for R."

Result: RESOLVED by RCPT-008 and RCPT-011.

### Review F — Object reference missing locally, same object ID exists elsewhere

The verifier does not guess an ExternalReference.

The reference is invalid/unresolved unless explicitly encoded for cross-Receipt resolution.

Result: RESOLVED by RCPT-013 and RCPT-014.

### Review G — Unpinned ExternalReference resolves to Receipt B

This establishes identifier-based resolution in the supplied Resolution Set.

It does not prove that the referring Receipt cryptographically committed to B's exact ARP.

Result: RESOLVED by RCPT-022.

### Review H — Pinned target Receipt ID matches but digest differs

The target cannot satisfy pinned resolution.

Result: RESOLVED by RCPT-023 and RCPT-024.

### Review I — Two Receipts reuse same Receipt ID with different payloads

The verifier reports identity conflict rather than choosing the newer or more-signed one.

Result: RESOLVED by RCPT-021.

### Review J — ExternalReferences form A→B→A cycle

The resolver is cycle-safe.

This package-level cycle does not automatically create a Derivation cycle.

Result: RESOLVED by RCPT-028 and existing GRAPH-003 semantics.

### Review K — Receipt B links to A and C

Multiple prior links create a DAG/partial order rather than forcing one previous-receipt pointer.

Result: RESOLVED by RCPT-036 and RCPT-037.

### Review L — A→B link is valid, but Receipt X occurred between them

The link does not prove immediate adjacency.

Result: RESOLVED by RCPT-038.

### Review M — Supplied chain starts at Receipt C

C is only the first supplied Receipt, not proven global genesis.

Result: RESOLVED by RCPT-039 and RCPT-040.

### Review N — Remove an unreferenced whole Receipt from a signed set

The remaining individual signatures can remain valid.

The omission is not necessarily detectable.

Result: RESOLVED by INTG-045 and INTG-046.

### Review O — Producer fabricates provenance then signs it correctly

Signature validity authenticates the fabricated representation under the key; it does not make the provenance factual.

Result: RESOLVED by INTG-039 through INTG-042.

### Review P — Modify a signed record field

The canonical ARP digest no longer matches the signed payload digest.

Result: RESOLVED by INTG-043.

### Review Q — Canonical JSON object keys reordered in transport

JCS canonicalization produces the same canonical payload when JSON semantics are unchanged.

Result: RESOLVED by INTG-001 through INTG-003.

### Review R — Array order changed

JCS does not semantically reorder arrays.

Changing ARP array order changes canonical bytes unless the future Schema defines a distinct pre-canonical semantic normalization.

Result: RESOLVED by INTG-006.

### Review S — Unicode-normalized string before verification

The verifier does not normalize beyond JCS; changing string code-point representation can change canonical bytes/digest.

Result: RESOLVED by INTG-005.

### Review T — Detached signature references correct ID but wrong digest

The envelope is not bound successfully to that Receipt payload.

Result: RESOLVED by INTG-025 and INTG-026.

### Review U — Signature verifies under a key labelled "OpenAI"

The cryptographic check establishes only verification under the key.

The human-readable label does not prove key ownership by that organization.

Result: RESOLVED by INTG-032 through INTG-037.

### Review V — Signed timestamp says 12:00

The signature authenticates the timestamp string but does not establish trusted wall-clock time.

Result: RESOLVED by INTG-038.

### Review W — Old valid Receipt replayed today

The signature can remain valid.

Freshness/non-replay is not established.

Result: RESOLVED by INTG-047.

### Review X — Signed hash-only source content

The signature authenticates the commitment value/profile in the ARP.

It does not directly sign unavailable plaintext.

Result: RESOLVED by INTG-048.

### Review Y — Signed HMAC commitment, verifier lacks HMAC key

Receipt signature verification can succeed while HMAC candidate verification remains unavailable.

Result: RESOLVED by INTG-049.

### Review Z — Signed redacted derivative

The signature authenticates the disclosed redacted representation/lineage metadata, not hidden original plaintext and not redaction effectiveness.

Result: RESOLVED by INTG-050 and INTG-052.

### Review AA — Candidate later matches signed original commitment

The verifier reports a composed result: candidate matches a commitment value authenticated by the signature.

It does not rewrite history to say the candidate bytes were directly included in the original signed ARP.

Result: RESOLVED by INTG-051.

### Review AB — Multiple signatures: one valid, one invalid, one key unresolved

All statuses are preserved per envelope.

The Receipt is not reduced to one opaque signed=true boolean.

Result: RESOLVED by INTG-055 through INTG-057.

### Review AC — All explicit cross-Receipt refs resolve

Reference closure can be complete while runtime history completeness remains not established.

Result: RESOLVED by RCPT-044 and INTG-058.

### Review AD — Signed unpinned ExternalReference resolves to later substituted Receipt

The referring signature authenticates the external Receipt/object identifiers, not the exact target payload.

Payload pinning is required for cryptographic target-content binding.

Result: RESOLVED by RCPT-022 and INTG-064.

### Review AE — Every link is signed and digest-pinned

The supplied package linkage is strongly tamper-evident.

It still does not prove no omitted branch or Receipt exists.

Result: RESOLVED by INTG-065 and INTG-066.

### Review AF — Same Artifact appears full in Receipt A and commitment-only in Receipt B

The Artifact keeps one object identity across the Resolution Set.

The tuple (receipt_id, object_id) locates the packaged occurrence; it does not create two Artifacts.

If the disclosed representations/commitments conflict, the verifier reports an object-identity conflict.

Result: RESOLVED by RCPT-016 and RCPT-049.

### Review AG — Cross-Receipt Derivation closes a cycle

Each individual Receipt can look locally acyclic while the resolved combined graph creates A→B→A across package boundaries.

The combined resolved Derivation graph must still satisfy GRAPH-003.

Result: RESOLVED by RCPT-050.

### Review AH — Envelope ID changed while signature value is copied

If envelope identity is protocol-semantic metadata, changing it changes the authenticated Signing Statement and invalidates the copied signature.

Result: RESOLVED by INTG-022 and INTG-068.

### Review AI — Signing Statement serialized with different JSON key order

The baseline Signing Statement is JCS-canonicalized before Ed25519 signing/verifying, so semantically equivalent object key ordering does not change signature input.

Result: RESOLVED by INTG-067.

### Review AJ — Same ARP shipped once with embedded signature and once with detached signature

These are different Receipt Presentations of the same Receipt identity, not new Receipt occurrences, provided the ARP/Receipt identity is unchanged.

Result: RESOLVED by RCPT-004 and RCPT-051.

### Review AK — Modified ARP happens to have a colliding SHA-256 digest

Core integrity language is computational rather than mathematical.

Verifier behavior is based on recomputed profile results and does not claim collision impossibility.

Result: RESOLVED by INTG-043, INTG-069, and INTG-070.

## 31. Architecture revisions caused by Part H

### 31.1 ExternalReference becomes a core Reference form

Part H resolves cross-Receipt object addressing as:

~~~text
target receipt identity
+
target object identity
+
optional target receipt payload pin
~~~

GRAPH-001 can therefore be revised from "all references local" to "all normative references are either internally resolved or explicitly external."

### 31.2 Receipt inventory/scope/completeness are separated

Part H separates:

- what records are in the ARP;
- what scope the Producer says the Receipt represents;
- whether explicit references resolve;
- whether runtime history is complete.

Only the first three can be evaluated directly from ordinary supplied Receipt evidence.

### 31.3 IntegrityEnvelope is outside the ARP

The ARP is immutable and can accumulate zero or more embedded/detached envelopes without recursive signing or changing payload digest.

### 31.4 ReceiptLink is package-level commitment, not provenance object relation

ReceiptLink supports tamper-evident supplied package linkage while preserving branching and avoiding false total-order/completeness claims.

### 31.5 Baseline crypto profile is fixed semantically

Baseline v0.1 uses:

~~~text
RFC 8785 JCS
→ SHA-256
→ Ed25519
~~~

The later Schema will freeze concrete field names/encodings and test vectors.

### 31.6 Verifier output is multidimensional

Part H explicitly rejects one overall verified boolean.

Structural, resolution, digest, signature, key, privacy capability, claim evidence, and completeness remain separate.

## 32. Resolution of Phase 0 Open Questions

### OQ-013 — External references and multi-Receipt resolution

RESOLVED.

External references are explicit and address target objects by Receipt identity + object identity, with optional target payload-digest pinning.

Resolution is capability/Resolution-Set relative, ambiguity is preserved, and unpinned resolution is not cryptographic target-content binding.

### OQ-014 — Receipt scope declaration without implying completeness

RESOLVED.

Receipt inventory, scope descriptor, reference closure, and runtime/history completeness are separate concepts.

Core v0.1 has no generic complete=true field that turns a Receipt scope declaration into proven complete history.

### OQ-015 — IntegrityEnvelope signing scope and detached/embedded representation

RESOLVED.

The baseline signs a deterministic Signing Statement over the immutable ARP payload digest plus Receipt/profile/key metadata.

IntegrityEnvelope signature values are outside the ARP.

Embedded and detached envelopes have equivalent authentication semantics when bound to the same Receipt identity/payload digest.

## 33. Part H resolved decisions

Part H locks the following decisions:

1. Receipt identity is package occurrence identity centered on one immutable ARP and is distinct from payload digest or transport Presentation.
2. Receipt identity denotes one immutable ARP; envelopes can be added/removed or embedded/detached without changing ARP identity.
3. ARP contains all semantics-bearing Receipt payload data and excludes the signature value/envelope set.
4. Receipt package inventory is exact for the supplied ARP but does not establish runtime history completeness.
5. Receipt scope metadata is Producer-authored and does not imply complete coverage.
6. Subset Receipts are first-class.
7. Cross-Receipt object references use explicit ExternalReference.
8. Receipt identity + object identity is a package-location address; underlying C2ATrace object identity remains stable across repeated packaging and must remain representation-consistent.
9. ExternalReference can be unpinned or payload-digest pinned; pinning binds target content commitment, not target truth/signature.
10. Cross-Receipt resolution is Resolution-Set/capability relative and ambiguity is preserved.
11. ReceiptLink is separate package-level prior-payload linkage.
12. Multiple prior links are allowed and define partial order, not a total chain.
13. Valid linkage does not prove adjacency, genesis, or complete history.
14. Baseline canonicalization is RFC 8785 JCS over the ARP with UTF-8 canonical bytes.
15. Baseline payload digest is SHA-256.
16. Baseline signature algorithm is Ed25519.
17. Baseline signatures authenticate RFC 8785 JCS UTF-8 canonical bytes of a domain-separated Signing Statement binding Receipt ID, payload digest, algorithm profiles, verification-key reference, envelope identity, and interpreted envelope metadata.
18. Embedded/detached envelopes are semantically equivalent when bound to the same ARP.
19. Multiple envelopes are first-class and evaluated individually.
20. Signature/digest validity is computationally profile-relative and establishes key-/commitment-relative cryptographic results, not mathematical collision/forgery impossibility, real-world signer identity, key trust, truth, completeness, or trusted time.
21. Tampering with an already signed ARP is detectable; Producer omission before signing generally is not.
22. Whole-Receipt omission/truncation can leave supplied signatures/linkage valid.
23. Signature validity does not establish freshness/non-replay.
24. Signed hash-only/HMAC/redacted Receipts authenticate exactly the disclosed ARP evidence, not unavailable plaintext.
25. Signed commitment + later candidate match is reported as a composed claim.
26. Independent verifier results are multidimensional; no generic "fully verified" shorthand is allowed when other dimensions remain unresolved.

## 34. Open items handed to later phases

Part H intentionally does not freeze:

- final JSON field names;
- Receipt/ARP wire schema;
- exact Base64/Base64url/hex encodings;
- exact key-reference wire format;
- public-key embedding format;
- certificate/PKI integration;
- revocation/compromise policy;
- trusted timestamping;
- transparency-log anchoring;
- Merkle inclusion/non-inclusion proofs;
- threshold/multisignature policy semantics;
- completeness attestations;
- transport/container format;
- CLI verifier output schema.

These remain constrained by Part H semantics.

## 35. Gate decision

Phase 1 Part H is ready for adversarial/mechanical review.

JSON Schema and implementation remain BLOCKED.
