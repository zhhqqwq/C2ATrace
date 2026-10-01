# C2ATrace v0.1 — Verifier Contract

Status: DRAFT FOR ADVERSARIAL REVIEW.

Scope: verifier authority and trust boundary; Verification Invocation input model; parsing/profile prechecks; reference resolution; graph invariants; representation and commitment verification; privacy capability handling; Receipt canonicalization/digest/signature checks; per-envelope results; adapter assertion handling; per-claim evidence composition; typed result semantics; invalidity versus uncertainty; completeness/conflict/unsupported reporting; multi-Receipt verification; machine/human output; process exit boundary.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Purpose

The Verifier Contract defines how an independent C2ATrace verifier evaluates supplied protocol material without upgrading recorded provenance into external truth.

The verifier determines, within one explicit Verification Invocation:

- what material was supplied;
- what can be parsed under supported profiles;
- what references resolve;
- what identity and graph invariants hold;
- what representations and commitments match;
- what privacy-dependent checks can actually be performed;
- what Receipt digest/signature checks succeed;
- which runtime/external statements remain assertions;
- which claims are established, matched, asserted, unknown, unverified, invalid, conflicting, unsupported, or merely not present;
- what completeness dimensions remain unestablished.

Core boundary:

~~~text
successful evidence verification
does not make the verifier
an authority for facts outside that evidence
~~~

## 2. Verifier authority boundary

A Verifier evaluates supplied C2ATrace records, representations, commitments, keys/capabilities, and recognized evidence profiles.

It is not automatically the Producer, Provider, Tool runtime, source authority, signer-identity authority, timestamp authority, outcome oracle, or completeness oracle.

Verification is invocation-relative. A later invocation with stronger capabilities can establish more without changing the historical Receipt.

The verifier does not repair history by inventing missing records, edges, content, timestamps, executions, or effects.

## 3. Verification Invocation input model

One Verification Invocation conceptually contains:

~~~text
one primary Receipt Presentation
or a Resolution Set

plus optional capabilities:
  verification keys / configured key resolvers
  HMAC or keyed-commitment secret capabilities
  candidate representations
  recognized proof/evidence-profile implementations
  external evidence Artifacts
  trusted-time evidence/profile
  caller-selected verification goals/policy
~~~

Exact API and wire structure remain unfrozen.

Receipt material is untrusted input until applicable checks succeed.

A supplied verification key is cryptographic material, not proof of ownership or authorization.

Keyed-commitment secrets are verifier capabilities, not Receipt evidence.

A candidate representation can be tested against commitments without becoming historically disclosed Receipt content.

Caller policy can determine which checks are operationally required; it does not change historical evidence strength.

## 4. Baseline evaluation pipeline

Applicable checks are evaluated in dependency order:

~~~text
1. container/framing parse
2. protocol/profile/version dispatch
3. Receipt identity and ARP extraction
4. local structural checks
5. Resolution Set indexing
6. internal/external reference resolution
7. cross-Receipt identity/graph checks
8. representation/Region/commitment checks
9. privacy-capability-dependent checks
10. ARP canonicalization and digest recomputation
11. IntegrityEnvelope key/signature checks
12. ReceiptLink and pinned-reference checks
13. adapter assertion and CaptureDiagnostic checks
14. per-claim evidence composition
15. completeness/conflict/unsupported reporting
16. VerificationReport aggregation
~~~

Failure of one prerequisite blocks dependent checks where necessary; unrelated checks continue.

## 5. Parsing and profile dispatch

The verifier parses the supplied representation without silently inserting, dropping, or coercing protocol data.

Protocol/profile/version identifiers are interpreted before profile-specific canonicalization, digest, signature, privacy, or proof checks.

A syntactically recognizable but unimplemented profile can be unsupported rather than invalid.

The verifier does not silently reinterpret an unsupported profile as the baseline profile.

If one Receipt in a Resolution Set is malformed, independent Receipts can still be evaluated.

## 6. Resolution Set and identity

Receipts are indexed by Receipt identity, not payload digest.

Different Presentations of the same unchanged Receipt ARP do not create a new Receipt occurrence.

If the same Receipt identity denotes incompatible ARPs, the conflict is preserved.

Repeated C2ATrace object identities across Receipts are checked under their global identity/immutability semantics.

Input ordering does not define provenance ordering.

## 7. Reference resolution

InternalReference is local to the Receipt ARP.

A missing local target is not silently searched across other Receipts.

ExternalReference uses its explicit target Receipt identity and target object identity.

Unpinned resolution establishes identifier-based target resolution only.

Pinned resolution additionally requires the target ARP commitment to match the declared pin.

Unavailable targets remain unresolved; incompatible candidates remain ambiguous/conflicting.

Baseline verification is closed over supplied material. Network, filesystem, SourceRef, key-URI, or ExternalReference retrieval happens only through explicitly configured resolver/evidence capabilities.

Resolver-produced material becomes explicit attributable Verification Invocation evidence.

## 8. Graph and identity verification

After available reference resolution, the verifier evaluates applicable local and cross-Receipt invariants, including:

- reference existence/type compatibility;
- Artifact identity and immutability;
- Derivation acyclicity;
- RequestBinding target/cardinality/scope rules;
- ModelOutput/ProviderAttempt ownership;
- ToolInvocation/ToolExecution/ToolResult ownership;
- ReceiptLink acyclicity;
- repeated-object consistency across Receipts.

An unresolved prerequisite does not become a successful graph check.

## 9. Representation and commitment verification

When required representations are supplied, the verifier can evaluate representation equality, Regions, request locations, derivation mappings, and commitment recomputation under declared profiles.

The verifier uses the declared representation basis and does not add undeclared decoding, normalization, or canonicalization.

Representation equality is bounded to the checked representation/scope.

A mismatch is a check-local result; it does not by itself prove deception or unrelated factual falsehood.

## 10. RequestBinding verification

The verifier preserves the Part C ladder:

~~~text
recorded
structurally valid
location resolved
commitment matched
representation verified
~~~

A stronger level is emitted only when its prerequisites are available.

Whole-request commitments do not prove hidden sublocation membership.

Redacted derivatives do not representation-verify hidden originals.

## 11. Privacy capability handling

Privacy-dependent verification follows the verifier's actual capabilities.

For hash-only evidence, candidate/representation availability controls recomputation.

For HMAC/keyed commitments, candidate verification requires the corresponding secret capability or a separately recognized verification result.

Raw keyed secrets are not emitted in ordinary reports.

Verification of a redacted derivative remains bounded to that derivative unless original/rule/proof evidence supports more.

Privacy withholding can lower verification strength but never raise it.

## 12. Receipt canonicalization and digest

Baseline v0.1 ARP verification is:

~~~text
ARP
→ RFC 8785 JCS
→ canonical UTF-8 bytes
→ SHA-256
→ recomputed payload digest
~~~

The verifier separately reports canonicalization status, digest recomputation status, and digest match/mismatch.

Digest match is computational commitment evidence, not truth, identity equality, or completeness.

## 13. IntegrityEnvelope verification

Each IntegrityEnvelope is evaluated separately.

Per-envelope evaluation conceptually includes:

~~~text
structure/profile
target Receipt identity
target payload digest
verification-key reference
key resolution
Signing Statement canonicalization
Ed25519 signature check
binding to supplied ARP
external key-trust status if supplied
~~~

Cryptographic signature validity and binding to the supplied ARP are separate dimensions.

A signature can verify over its Signing Statement while the supplied ARP has a different recomputed digest.

Key trust/ownership is a separate evidence or policy dimension.

Multiple valid/invalid/unresolved/unsupported envelopes can coexist.

## 14. ReceiptLink verification

ReceiptLink resolution and digest matching are distinct from ExternalReference object resolution.

A valid link establishes the supplied recorded linkage only.

It does not establish adjacency, genesis, trusted chronology, or complete history.

Missing linked targets remain unresolved.

## 15. Adapter assertion handling

Provider Adapter and Tool Adapter runtime occurrence/lifecycle/capture statements remain E4 Producer/instrumentation assertions unless stronger external evidence exists.

The verifier can structurally establish that a record contains an assertion while preserving the asserted nature of the external proposition.

Example:

~~~text
established:
the Receipt contains ToolExecution disposition=completed

asserted:
the tool execution completed at the instrumented runtime boundary

not automatically established:
the remote tool committed the external effect
~~~

## 16. Claim composition

A composed VerificationFinding can depend on premise findings.

Premise relationships are retained sufficiently to explain evidence strength without disclosing unnecessary private content.

The weakest unresolved or Producer-asserted premise bounds the composed conclusion.

The verifier distinguishes "record asserts X" from "external proposition X is true."

P1 prohibited inferences are never generated as stronger conclusions from weaker premises.

## 17. Typed result model

The Verifier Contract does not define one universal ordered verification status.

Findings are typed by result domain.

Conceptual result domains include:

~~~text
conformance
resolution
comparison
cryptographic
claim
presence
support
conflict
completeness
~~~

## 18. Result vocabulary

established means the precisely worded claim is supported by the applicable supplied evidence and rules.

matched means a defined representation/commitment/digest comparison succeeded.

mismatched means the applicable comparison was performed and failed.

asserted means an E4 runtime/external/policy proposition is recorded but not independently established as external truth.

unknown means available evidence does not justify a stronger factual/provenance conclusion.

unverified means the check is recognized but required invocation-specific evidence/capability is unavailable.

unsupported means the verifier implementation does not implement the declared otherwise-recognizable profile/check.

valid means a defined structural/profile/cryptographic check succeeded.

invalid means supplied material fails the applicable check.

resolved/unresolved/ambiguous describe reference, dependency, or key resolution.

conflict means semantically incompatible evidence remains unresolved.

not_present means no requested record/property was found in the supplied verification scope; it is not proof that the event never occurred.

## 19. Unknown, unverified, and unsupported

These are distinct:

~~~text
unknown
= evidence does not justify the fact

unverified
= verifier recognizes the check but lacks invocation-specific prerequisite evidence/capability

unsupported
= verifier implementation lacks the required profile/check implementation
~~~

Example:

~~~text
HMAC tag present

no candidate
→ candidate check unverified

candidate present, no secret
→ candidate check unverified

MAC profile not implemented
→ unsupported

candidate + secret + supported profile, comparison succeeds
→ matched
~~~

Even after matched, external truth can remain asserted or unknown.

## 20. Invalidity versus factual uncertainty

Malformed references, impossible cardinality, identity conflicts, digest mismatches, invalid signatures, or violated graph invariants can produce invalid findings.

A structurally valid Producer assertion is not invalid merely because external truth cannot be independently checked.

Contradictory external evidence is preserved as conflict/contradiction under its profile unless a protocol invariant itself is violated.

## 21. Completeness reporting

The verifier keeps separate:

~~~text
package inventory completeness
explicit reference closure
adapter capture-scope completeness assertions
runtime / Run / history completeness
~~~

Package inventory and explicit reference closure can be established for supplied material.

Runtime/history completeness defaults to unknown/not established unless a recognized completeness evidence profile establishes a defined scope.

No missing-reference warning, no bypass diagnostic, and no extra supplied Receipt do not establish complete history.

## 22. Conflict preservation

The verifier preserves unresolved conflicts including:

- Receipt ID collisions;
- repeated Artifact identities with incompatible representations;
- incompatible TrustAssertions without applicable precedence;
- incompatible TaintAssertions without an applicable policy join;
- conflicting privacy declarations;
- conflicting CaptureDiagnostics;
- contradictory external evidence;
- ambiguous ExternalReference targets.

Timestamp, insertion order, signature count, and "last value wins" are not generic conflict resolution rules.

Unrelated checks continue.

## 23. Unsupported profiles

A syntactically valid declared profile that the verifier does not implement receives unsupported for dependent checks.

The verifier does not silently downgrade profiles, treat unsupported crypto as invalid, or execute arbitrary code named by untrusted profile metadata.

Malformed use of a supported profile remains invalid rather than unsupported.

## 24. Multi-Receipt verification

Semantic findings are independent of Resolution Set input ordering unless authenticated protocol data itself carries order semantics.

Repeated Presentations of one Receipt identity/ARP remain one Receipt occurrence.

Distinct consistent IntegrityEnvelope occurrences can be evaluated across Presentations.

Partial external-reference resolution still permits independent local checks.

Resolved objects participate in global identity, Derivation, and ReceiptLink checks.

A fully resolved supplied set is not the global history.

## 25. VerificationReport

VerificationReport is verifier-output metadata, not historical runtime provenance.

It conceptually contains:

- verifier implementation/profile metadata;
- Verification Invocation capability summary;
- evaluated Receipt/Resolution Set subjects;
- typed VerificationFindings;
- per-envelope integrity results;
- conflicts;
- unsupported/unverified checks;
- completeness dimensions;
- process aggregation outcome.

Exact Schema is deferred to Schema freeze.

## 26. VerificationFinding

A VerificationFinding conceptually identifies:

- finding/check identity;
- applicable normative requirement/profile check;
- subject/scope;
- result domain;
- status;
- evidence-basis tags;
- premise-finding references;
- bounded reason/details;
- capability/dependency state where relevant.

Raw private evidence does not need to be copied into the report when identifiers/commitments suffice.

## 27. Sensitive verifier inputs

Raw HMAC/keyed-commitment secrets are never ordinary report content.

Private signing keys are not required for verification.

Candidate plaintext that was not already disclosed in the Receipt is not automatically echoed into report output merely because it was compared.

A report can state that a candidate matched without serializing the secret or candidate bytes.

## 28. Machine-readable and human-readable output

The machine-readable VerificationReport is the normative semantic result surface.

Human-readable output is a rendering of those findings.

Human wording cannot strengthen machine semantics.

asserted cannot be rendered as proved external truth.

unknown cannot be rendered as false.

If a human summary omits detailed findings, its scope/limitations remain explicit or the full machine report remains available.

## 29. Process and exit outcome

A verifier/CLI can expose a coarse operational process outcome:

~~~text
completed
invalidity_detected
incomplete_evaluation
operational_error
~~~

completed means the requested mandatory verification goals ran without detected invalidity and without required checks being blocked.

invalidity_detected means at least one requested mandatory check produced applicable invalid/mismatch evidence.

incomplete_evaluation means one or more requested mandatory checks could not complete due to unresolved prerequisites or unsupported capability/profile.

operational_error means the verifier invocation itself could not run/finish as requested.

This process outcome is not a truth, provenance, signer-trust, or completeness verdict.

Exact numeric shell exit codes remain a later CLI implementation detail.

## 30. Determinism and safety boundary

Given semantically identical protocol inputs, verification goals, supported profiles, keys/secrets/candidates, and external evidence, the verifier produces semantically equivalent findings independent of non-semantic input order.

Resource-limit termination leaves affected checks incomplete/operationally blocked rather than invalid/false.

Untrusted profile identifiers, paths, URLs, locators, references, and metadata do not authorize arbitrary code execution, filesystem reads, or network access.

## 31. Normative verifier requirements

### VFY-001 — Verifier authority is evidence-bounded

A Verifier MUST NOT report a fact beyond the strongest precisely scoped claim established by supplied evidence/capabilities and applicable C2ATrace rules.

Planned test: verifier-authority-bounded-001.

### VFY-002 — Verification is invocation-relative

A Verifier MUST interpret results relative to the current Verification Invocation and MUST NOT assume evidence/capabilities from earlier invocations.

Planned test: verifier-invocation-relative-001.

### VFY-003 — No hidden evidence assumption

A Verifier MUST NOT use keys, secrets, candidates, Receipts, external evidence, or facts absent from the declared/current invocation except material returned by an explicitly configured resolver.

Planned test: verifier-no-hidden-evidence-001.

### VFY-004 — No history repair by invention

A Verifier MUST NOT fabricate missing objects, references, edges, representations, timestamps, executions, or Effect observations to make supplied material verify.

Planned test: verifier-no-history-repair-001.

### VFY-005 — Supplied key is not identity proof

A Verifier MUST NOT infer real-world verification-key ownership/authorization solely because key material is supplied.

Planned test: verifier-key-not-identity-001.

### VFY-006 — HMAC secret is verifier capability only

A Verifier MUST NOT treat possession of a keyed-commitment secret as Receipt evidence that the Producer/signer possessed or used that secret.

Planned test: verifier-hmac-capability-bounded-001.

### VFY-007 — Candidate match does not rewrite historical disclosure

A Verifier MUST NOT report later-supplied candidate plaintext as having been directly disclosed in the original Receipt solely because it matches a commitment.

Planned test: verifier-candidate-no-history-rewrite-001.

### VFY-008 — Caller policy does not change historical evidence

A Verifier MUST NOT change historical provenance/evidence strength solely because the caller marks a check required or optional.

Planned test: verifier-policy-no-history-rewrite-001.

### VFY-009 — Dependent checks respect prerequisites

A Verifier MUST NOT report a dependent check successful when a required prerequisite is unresolved, unsupported, invalid, or otherwise unavailable.

Planned test: verifier-dependency-prerequisite-001.

### VFY-010 — Independent checks continue

A Verifier MUST continue unrelated independently evaluable checks when another check fails or is blocked.

Planned test: verifier-independent-checks-001.

### VFY-011 — Parse without silent repair

A Verifier MUST NOT silently insert, delete, or coerce malformed protocol data and then report the repaired form as the supplied Receipt.

Planned test: verifier-parse-no-repair-001.

### VFY-012 — Profile dispatch precedes profile checks

A Verifier MUST identify applicable version/profile semantics before applying profile-specific canonicalization, digest, signature, privacy, or proof logic.

Planned test: verifier-profile-dispatch-001.

### VFY-013 — No unsupported-profile fallback

A Verifier MUST NOT reinterpret an unsupported/unknown declared profile as the baseline profile solely to complete verification.

Planned test: verifier-profile-no-fallback-001.

### VFY-014 — Baseline JCS constraints are enforced

A Verifier MUST NOT report successful baseline JCS canonicalization for input violating selected JCS/I-JSON constraints such as duplicate property names.

Planned test: verifier-jcs-input-constraints-001.

### VFY-015 — Malformed Receipt does not erase independent results

In a multi-Receipt invocation, a Verifier MUST preserve the malformed Receipt result and continue independent checks on other parseable Receipts where dependencies permit.

Planned test: verifier-multireceipt-partial-evaluation-001.

### VFY-016 — Receipt identity is not payload digest

A Verifier MUST NOT merge distinct Receipt identities solely because payload digests or non-identity content match.

Planned test: verifier-receipt-id-not-digest-001.

### VFY-017 — Conflicting Receipt identity is preserved

If one Receipt identity denotes incompatible ARPs in the Resolution Set, a Verifier MUST report conflict and MUST NOT choose by timestamp, input order, or signature count.

Planned test: verifier-receipt-id-conflict-001.

### VFY-018 — Repeated Presentation is not new Receipt

A Verifier MUST NOT create a new Receipt occurrence solely because one Receipt ARP appears with another wrapper, envelope placement, or presentation serialization.

Planned test: verifier-presentation-no-new-receipt-001.

### VFY-019 — Repeated object identity obeys immutability

A Verifier MUST enforce identity/immutability constraints across repeated C2ATrace object identities in different Receipts and MUST report incompatible representations as conflict/invalidity as applicable.

Planned test: verifier-cross-receipt-object-identity-001.

### VFY-020 — InternalReference stays local

A Verifier MUST NOT resolve an InternalReference by silently searching another Receipt for a matching object ID.

Planned test: verifier-internal-reference-local-001.

### VFY-021 — ExternalReference follows explicit address

A Verifier MUST resolve ExternalReference using explicit target Receipt/object identity rather than content similarity.

Planned test: verifier-external-address-001.

### VFY-022 — Unpinned resolution is not exact payload binding

A Verifier MUST NOT report unpinned ExternalReference resolution as cryptographic binding to the exact target ARP.

Planned test: verifier-external-unpinned-001.

### VFY-023 — Pinned resolution requires target digest match

A Verifier MUST require a compatible target ARP digest match before reporting the recorded pin as matched.

Planned test: verifier-external-pin-match-001.

### VFY-024 — Pin match does not prove target signature/truth

A Verifier MUST NOT infer target signature validity, key trust, truth, or completeness solely from a matched target payload pin.

Planned test: verifier-external-pin-bounded-001.

### VFY-025 — Unavailable target remains unresolved

A Verifier MUST NOT invent/substitute an unavailable ExternalReference target and MUST preserve dependent unresolved/unverified states.

Planned test: verifier-external-unresolved-001.

### VFY-026 — Ambiguous target remains ambiguous

A Verifier MUST NOT choose among incompatible reference targets solely by timestamp, input order, signer count, or similarity.

Planned test: verifier-external-ambiguous-001.

### VFY-027 — No implicit external I/O

A baseline Verifier MUST NOT automatically perform network/filesystem retrieval from ExternalReferences, SourceRef locators, key URIs, or other untrusted metadata without explicit configured capability.

Planned test: verifier-no-implicit-io-001.

### VFY-028 — Resolver evidence is explicit

Material obtained by an explicitly configured resolver MUST be represented in the invocation/evidence context sufficiently for attribution and reproducibility.

Planned test: verifier-resolver-evidence-001.

### VFY-029 — Cross-Receipt graph checks use resolved material

A Verifier MUST apply applicable identity/type/graph invariants across all successfully resolved objects in the Resolution Set.

Planned test: verifier-cross-receipt-graph-001.

### VFY-030 — Unresolved dependency is not valid

A Verifier MUST NOT report a dependent graph/property check successful when its required target remains unresolved and the check cannot actually be completed.

Planned test: verifier-unresolved-not-valid-001.

### VFY-031 — Derivation acyclicity is global over resolved graph

A Verifier MUST detect Derivation cycles that appear only after cross-Receipt resolution.

Planned test: verifier-cross-receipt-derivation-cycle-001.

### VFY-032 — ReceiptLink acyclicity is global over resolved links

A Verifier MUST detect cycles in the resolved prior ReceiptLink graph.

Planned test: verifier-receiptlink-cycle-001.

### VFY-033 — Explicit dependencies outrank timestamps

A Verifier MUST NOT use wall-clock timestamps to reverse or override valid explicit provenance/ReceiptLink dependencies.

Planned test: verifier-dependency-vs-time-001.

### VFY-034 — Representation verification uses declared basis

A Verifier MUST use the declared representation basis/profile and MUST NOT silently normalize/convert values beyond that profile.

Planned test: verifier-representation-basis-001.

### VFY-035 — Equality remains scope-bounded

A Verifier MUST NOT upgrade representation/commitment equality into occurrence identity, source identity, runtime observation truth, Provider receipt, Tool execution, Effect truth, or causality.

Planned test: verifier-equality-bounded-001.

### VFY-036 — Mismatch remains check-local

A Verifier MUST NOT infer intentional deception or unrelated external falsehood solely from a representation/commitment mismatch.

Planned test: verifier-mismatch-bounded-001.

### VFY-037 — RequestBinding evidence levels remain distinct

A Verifier MUST preserve recorded, structural, location-resolved, commitment-matched, and representation-verified RequestBinding levels rather than collapse them into one boolean.

Planned test: verifier-binding-levels-001.

### VFY-038 — Whole commitment does not prove hidden sublocation

A Verifier MUST NOT report hidden RequestBinding location/membership from a whole-request commitment match alone.

Planned test: verifier-binding-whole-commitment-001.

### VFY-039 — Redacted derivative does not verify hidden original binding

A Verifier MUST NOT use a redacted derivative alone to representation-verify unavailable original RequestSnapshot content/location.

Planned test: verifier-binding-redacted-original-001.

### VFY-040 — Privacy verification follows actual capabilities

A Verifier MUST base privacy-dependent checks on candidates, secrets, representations, and recognized proofs actually available in the current invocation.

Planned test: verifier-privacy-capability-001.

### VFY-041 — Hash match is not confidentiality proof

A Verifier MUST NOT report unkeyed commitment match as confidentiality, anonymity, unlinkability, or low-entropy resistance proof.

Planned test: verifier-hash-no-confidentiality-001.

### VFY-042 — HMAC recomputation requires secret capability

A Verifier MUST NOT report keyed candidate recomputation/match without the required secret capability or separately recognized verification result.

Planned test: verifier-hmac-secret-required-001.

### VFY-043 — HMAC secrets are not report content

A Verifier MUST NOT emit raw HMAC/keyed-commitment secret material into ordinary machine-readable or human-readable VerificationReport output.

Planned test: verifier-hmac-secret-nondisclosure-001.

### VFY-044 — HMAC tag presence is not candidate verification

A Verifier lacking required candidate/secret material MUST NOT report hidden candidate matching solely from a recorded keyed tag.

Planned test: verifier-hmac-tag-bounded-001.

### VFY-045 — Redacted verification stays derivative-bounded

A Verifier MUST NOT report verified redacted derivative content as verification of unavailable original plaintext or redaction correctness without required original/rule/proof evidence.

Planned test: verifier-redacted-bounded-001.

### VFY-046 — Privacy omission cannot strengthen findings

A Verifier MUST NOT strengthen provenance or claim status because evidence was withheld for privacy.

Planned test: verifier-privacy-no-upgrade-001.

### VFY-047 — Baseline ARP canonicalization uses JCS

A baseline Verifier MUST canonicalize ARP with RFC 8785 JCS UTF-8 rules before SHA-256 payload-digest recomputation.

Planned test: verifier-arp-jcs-001.

### VFY-048 — Digest is independently recomputed

A Verifier MUST recompute the baseline ARP digest from supplied ARP content and MUST NOT treat a recorded digest value alone as successful verification.

Planned test: verifier-digest-recompute-001.

### VFY-049 — Digest match is bounded commitment evidence

A Verifier MUST NOT report digest match as factual truth, completeness, Receipt identity equality, or mathematical collision impossibility.

Planned test: verifier-digest-bounded-001.

### VFY-050 — Digest mismatch blocks supplied-ARP binding

When recomputed digest differs from the compared authenticated/recorded digest, a Verifier MUST report mismatch and MUST NOT report binding to that supplied ARP as successful.

Planned test: verifier-digest-mismatch-001.

### VFY-051 — IntegrityEnvelopes are evaluated individually

A Verifier MUST report cryptographic status per IntegrityEnvelope and MUST NOT reduce multiple envelopes to one signed boolean.

Planned test: verifier-envelope-individual-001.

### VFY-052 — Signing Statement uses authenticated metadata

A Verifier MUST construct/verify the Signing Statement from the authenticated Receipt/profile/key/envelope metadata defined by Part H and MUST NOT substitute unauthenticated switching metadata.

Planned test: verifier-signing-statement-binding-001.

### VFY-053 — Baseline Signing Statement uses JCS UTF-8 bytes

A baseline Verifier MUST verify Ed25519 over RFC 8785 JCS UTF-8 canonical Signing Statement bytes.

Planned test: verifier-signing-statement-jcs-001.

### VFY-054 — Unresolved key differs from invalid signature

A Verifier MUST distinguish unresolved verification key from cryptographic failure under a resolved applicable key.

Planned test: verifier-key-unresolved-vs-invalid-001.

### VFY-055 — Unsupported signature profile differs from invalid

A Verifier MUST distinguish unsupported crypto/profile from failure of a supported profile.

Planned test: verifier-signature-unsupported-vs-invalid-001.

### VFY-056 — Signature validity is key-relative

A Verifier reporting signature validity MUST identify/bind the verification key/material actually used.

Planned test: verifier-signature-key-relative-001.

### VFY-057 — Signature validity is not key trust

A Verifier MUST NOT restate signature validity as real-world signer identity, authorization, uncompromised key, revocation status, or trust without separate evidence/policy.

Planned test: verifier-signature-no-key-trust-001.

### VFY-058 — Signature verification differs from supplied-ARP binding

A Verifier MUST preserve the distinction between cryptographic verification of the Signing Statement and matching the authenticated Receipt identity/payload digest to the supplied ARP.

Planned test: verifier-signature-vs-arp-binding-001.

### VFY-059 — Valid signature is not record truth

A Verifier MUST NOT report valid Receipt signature as proof that contained provenance/runtime/external assertions are factually true.

Planned test: verifier-signature-no-truth-001.

### VFY-060 — Valid signature is not completeness

A Verifier MUST NOT report valid Receipt signature as capture/Run/history completeness proof.

Planned test: verifier-signature-no-completeness-001.

### VFY-061 — Invalid signature is not universal factual falsehood

A Verifier MUST NOT infer all Receipt statements factually false solely because an IntegrityEnvelope signature is invalid.

Planned test: verifier-invalid-signature-bounded-001.

### VFY-062 — Signature count is not truth voting

A Verifier MUST NOT infer factual correctness/completeness from number or majority of valid signatures.

Planned test: verifier-multisig-no-truth-vote-001.

### VFY-063 — ReceiptLink result remains linkage-only

A Verifier MUST NOT upgrade matched/resolved ReceiptLinks into adjacency, genesis, trusted chronology, or complete-history proof.

Planned test: verifier-receiptlink-bounded-001.

### VFY-064 — Missing linked target remains unresolved

A Verifier MUST preserve a missing ReceiptLink target as unresolved and MUST NOT delete the authenticated link from semantics.

Planned test: verifier-receiptlink-missing-001.

### VFY-065 — Adapter assertions remain assertions

A Verifier MUST preserve Provider/Tool Adapter occurrence/lifecycle/decision/capture/effect-observation claims as Producer/instrumentation assertions unless stronger evidence establishes the external proposition.

Planned test: verifier-adapter-assertion-bounded-001.

### VFY-066 — Record existence differs from external fact

A Verifier MUST distinguish establishing that a record asserts X from establishing external proposition X.

Planned test: verifier-record-vs-fact-001.

### VFY-067 — CaptureDiagnostic is not global coverage

A Verifier MUST NOT report CaptureDiagnostic observed state, absence of bypass_detected, or signed adapter capability declarations as global instrumentation completeness proof.

Planned test: verifier-capture-diagnostic-bounded-001.

### VFY-068 — Tool success is not Effect truth

A Verifier MUST NOT infer external Effect truth solely from ToolExecution completion or ToolResult/tool-reported success.

Planned test: verifier-tool-success-no-effect-001.

### VFY-069 — Non-completed execution is not no-effect proof

A Verifier MUST NOT infer absence of external Effect solely from failed, timeout, cancelled, interrupted, or unknown ToolExecution disposition.

Planned test: verifier-tool-failure-not-no-effect-001.

### VFY-070 — EffectObservation is not OutcomeVerification

A Verifier MUST NOT report EffectObservation as proof that desired application/business Outcome was achieved.

Planned test: verifier-effect-not-outcome-001.

### VFY-071 — Evidence count does not create truth

A Verifier MUST NOT upgrade external claims to objective truth solely because multiple supporting Artifacts/assertions exist.

Planned test: verifier-evidence-count-bounded-001.

### VFY-072 — Temporal proximity and reachability are not causality

A Verifier MUST NOT infer model/tool/external causal responsibility solely from timestamps, graph reachability, inclusion, identifier equality, or temporal proximity.

Planned test: verifier-no-causal-upgrade-001.

### VFY-073 — Finding premises remain traceable

A composed VerificationFinding MUST preserve premise/evidence references sufficient to explain evidence strength, subject to privacy constraints.

Planned test: verifier-finding-premises-001.

### VFY-074 — Weakest unresolved premise bounds conclusion

A Verifier MUST NOT report a composed conclusion stronger than the weakest unresolved or Producer-asserted prerequisite permits.

Planned test: verifier-composition-weakest-premise-001.

### VFY-075 — established is precisely scoped

A Verifier MUST use established only for the precisely worded supported claim and MUST NOT broaden it to stronger external truth, causality, trust, or completeness.

Planned test: verifier-established-scope-001.

### VFY-076 — matched is comparison-only

A Verifier MUST use matched only for the declared comparison and MUST NOT treat matched as occurrence identity or external truth.

Planned test: verifier-matched-scope-001.

### VFY-077 — asserted preserves E4 nature

A Verifier MUST use asserted/bounded assertion wording for E4 runtime/external/policy facts lacking stronger independent evidence.

Planned test: verifier-asserted-wording-001.

### VFY-078 — unknown is not false

A Verifier MUST NOT render unknown as false, absent, failed, safe, untrusted, or invalid.

Planned test: verifier-unknown-not-false-001.

### VFY-079 — unverified means prerequisite/capability missing

A Verifier MUST use unverified when a recognized check cannot complete because invocation-specific evidence/capability is unavailable and MUST NOT silently treat it as valid.

Planned test: verifier-unverified-semantics-001.

### VFY-080 — unsupported is implementation limitation

A Verifier MUST use unsupported for an otherwise recognizable declared profile/check it does not implement and MUST NOT restate that as protocol/crypto invalidity.

Planned test: verifier-unsupported-semantics-001.

### VFY-081 — invalid is check-specific

A Verifier MUST scope invalid to the failed protocol/profile/check and MUST NOT automatically restate it as factual falsity of unrelated external claims.

Planned test: verifier-invalid-bounded-001.

### VFY-082 — mismatched requires an actual comparison

A Verifier MUST use mismatched only when the applicable comparison was performed and failed; missing prerequisites are unverified/unsupported instead.

Planned test: verifier-mismatch-semantics-001.

### VFY-083 — not_present is supplied-scope absence only

A Verifier MUST NOT render not_present as proof that the runtime event/fact did not occur outside supplied scope.

Planned test: verifier-not-present-bounded-001.

### VFY-084 — Result domains remain typed

A Verifier MUST NOT collapse conformance, resolution, comparison, cryptographic, claim, completeness, presence, support, and conflict results into one universal ordered status.

Planned test: verifier-typed-status-domains-001.

### VFY-085 — valid is not true

A Verifier MUST NOT render structural/profile/cryptographic valid as factual true, safe, authorized, trusted, or complete.

Planned test: verifier-valid-not-true-001.

### VFY-086 — Invalidity differs from factual uncertainty

A Verifier MUST distinguish protocol/profile invalidity from a structurally valid but externally unverified/unknown assertion.

Planned test: verifier-invalid-vs-uncertain-001.

### VFY-087 — Contradictory external evidence is preserved as conflict

A Verifier MUST preserve contradiction/conflict between external evidence and Producer assertions rather than automatically treating unrelated Receipt structure as invalid.

Planned test: verifier-external-conflict-001.

### VFY-088 — Package inventory completeness is package-local

A Verifier MUST NOT report package-inventory completeness as runtime/Run/history completeness.

Planned test: verifier-inventory-not-history-001.

### VFY-089 — Reference closure is not history completeness

A Verifier MUST NOT report complete explicit reference closure as complete runtime/capture/history evidence.

Planned test: verifier-reference-closure-not-history-001.

### VFY-090 — Runtime/history completeness defaults not established

Without a recognized completeness evidence profile, a Verifier MUST report runtime/capture/history completeness as unknown/not established rather than complete.

Planned test: verifier-history-completeness-default-001.

### VFY-091 — Adapter capture completeness stays bounded

A Verifier MUST NOT upgrade adapter capture_extent/diagnostics to global capture completeness without stronger recognized evidence.

Planned test: verifier-adapter-completeness-bounded-001.

### VFY-092 — Absence cannot complete history

A Verifier MUST NOT infer complete history from absence of missing-reference diagnostics, bypass diagnostics, or additional supplied Receipts.

Planned test: verifier-absence-no-completeness-001.

### VFY-093 — Conflicts are preserved

A Verifier MUST preserve unresolved incompatible records/evidence as conflict rather than silently select a winner.

Planned test: verifier-conflict-preservation-001.

### VFY-094 — Timestamp is not generic conflict precedence

A Verifier MUST NOT resolve conflict by latest/earliest timestamp unless an explicit applicable policy/profile defines that precedence.

Planned test: verifier-conflict-no-timestamp-winner-001.

### VFY-095 — Signature count is not conflict precedence

A Verifier MUST NOT resolve conflicting claims/Receipts solely by selecting the one with more signatures.

Planned test: verifier-conflict-no-signature-vote-001.

### VFY-096 — Unrelated checks continue through conflict

A conflict in one subject/scope MUST NOT cause unrelated independent findings to be silently discarded.

Planned test: verifier-conflict-independent-checks-001.

### VFY-097 — Unsupported profile is not silently downgraded

A Verifier MUST NOT substitute a supported weaker/different profile for an unsupported declared profile.

Planned test: verifier-unsupported-no-downgrade-001.

### VFY-098 — Malformed supported profile is invalid, not unsupported

When the verifier implements a selected profile but supplied data violates it, the Verifier MUST report applicable invalid/mismatch rather than unsupported.

Planned test: verifier-malformed-supported-invalid-001.

### VFY-099 — Profile identifiers do not execute code

A Verifier MUST NOT execute/load arbitrary untrusted code solely because Receipt/profile metadata names a plugin, module, path, or URI.

Planned test: verifier-profile-no-code-execution-001.

### VFY-100 — Multi-Receipt semantics are input-order independent

A Verifier MUST produce semantically equivalent findings for permutations of the same Resolution Set except where authenticated protocol data itself carries order semantics.

Planned test: verifier-resolution-set-order-001.

### VFY-101 — Presentation deduplication preserves envelope occurrences

When multiple Presentations represent one Receipt identity/ARP, a Verifier MUST NOT duplicate Receipt occurrence identity and MUST preserve distinct consistent IntegrityEnvelope occurrences without merging conflicting envelope identities/content.

Planned test: verifier-presentation-envelope-union-001.

### VFY-102 — Partial resolution permits local verification

A Verifier MUST continue local/independent checks when some ExternalReferences remain unresolved and MUST mark only dependent checks unresolved/unverified as applicable.

Planned test: verifier-partial-resolution-local-001.

### VFY-103 — Fully resolved supplied set is not global history

A Verifier MUST NOT report a fully resolved Resolution Set as all Receipts/all runtime history without completeness evidence.

Planned test: verifier-resolved-set-not-history-001.

### VFY-104 — VerificationReport is not historical provenance

A Verifier MUST NOT insert VerificationReport/VerificationFindings into the historical Receipt as though they were original runtime provenance.

Planned test: verifier-report-not-runtime-provenance-001.

### VFY-105 — Finding identifies check, subject, domain, status

A machine-readable VerificationFinding MUST identify evaluated subject/scope, applicable check/requirement, result domain, and status sufficiently for independent interpretation.

Planned test: verifier-finding-minimum-001.

### VFY-106 — Finding preserves evidence basis

A VerificationFinding MUST preserve applicable E1/E2/E3/E4/P1 or recognized profile-basis information rather than hide assertion premises behind generic success.

Planned test: verifier-finding-evidence-basis-001.

### VFY-107 — Private evidence need not be echoed

A VerificationFinding MUST NOT require copying raw private evidence into the report when identifiers, commitments, or premise references suffice.

Planned test: verifier-finding-private-evidence-001.

### VFY-108 — Keyed secrets never appear in ordinary report

A Verifier MUST NOT serialize raw keyed-commitment secrets into ordinary machine/human VerificationReport output.

Planned test: verifier-report-no-keyed-secret-001.

### VFY-109 — Candidate plaintext is not automatically echoed

A Verifier MUST NOT automatically echo undisclosed candidate plaintext merely because a commitment comparison was performed.

Planned test: verifier-report-no-candidate-echo-001.

### VFY-110 — Human output cannot strengthen machine findings

A human renderer MUST NOT translate a weaker machine finding into stronger truth, causality, trust, safety, completeness, authorization, or identity language.

Planned test: verifier-human-no-strengthening-001.

### VFY-111 — asserted cannot render as proved truth

A human renderer MUST NOT present asserted as independently proved/verified external truth.

Planned test: verifier-human-asserted-wording-001.

### VFY-112 — unknown cannot render as false

A human renderer MUST NOT present unknown as false, absent, failed, safe, or invalid.

Planned test: verifier-human-unknown-wording-001.

### VFY-113 — Summary omission is scope-explicit

If human output omits detailed findings, it MUST expose summary scope/limitations or provide access to full machine findings.

Planned test: verifier-human-summary-scope-001.

### VFY-114 — No overall fully-verified boolean

A conforming Verifier MUST NOT expose one unqualified overall verified/fully_verified boolean implying all provenance, external truth, signer identity, privacy, capture completeness, and history completeness dimensions succeeded.

Planned test: verifier-no-overall-boolean-001.

### VFY-115 — Process outcome is operational only

A Verifier MUST treat CLI/process outcome as operational aggregation and MUST NOT describe it as factual/provenance/completeness truth.

Planned test: verifier-exit-operational-only-001.

### VFY-116 — invalidity_detected requires failed mandatory check

A Verifier MUST NOT emit invalidity_detected solely because a claim is asserted, unknown, unverified, unsupported, conflict, or not_present; an applicable requested mandatory invalid/mismatch result is required.

Planned test: verifier-exit-invalidity-001.

### VFY-117 — incomplete_evaluation preserves blocked mandatory checks

A Verifier MUST use incomplete_evaluation when requested mandatory checks cannot complete because of unresolved prerequisite or unsupported capability/profile rather than reporting completed.

Planned test: verifier-exit-incomplete-001.

### VFY-118 — operational_error is verifier execution failure

A Verifier MUST reserve operational_error for failure of the verifier invocation itself and MUST NOT use it as a substitute for Receipt invalidity or factual uncertainty.

Planned test: verifier-exit-operational-error-001.

### VFY-119 — Exit zero cannot mean all facts true

Any CLI numeric mapping MUST NOT define exit code zero as "all recorded facts are true/complete"; its documented meaning remains bounded to selected verification goals/process outcome.

Planned test: verifier-exit-zero-bounded-001.

### VFY-120 — Semantic determinism

Given semantically identical inputs, goals, capabilities, and supported profiles, a Verifier MUST produce semantically equivalent findings independent of non-semantic ordering/environmental noise.

Planned test: verifier-determinism-001.

### VFY-121 — Resource limits do not rewrite claims

If evaluation stops due to resource limits, a Verifier MUST report affected checks incomplete/operationally blocked and MUST NOT mark unevaluated claims invalid or false.

Planned test: verifier-resource-limit-bounded-001.

### VFY-122 — Untrusted metadata does not authorize I/O

A Verifier MUST NOT perform filesystem/network access solely because untrusted Receipt/profile/reference metadata contains a path/URI.

Planned test: verifier-untrusted-metadata-no-io-001.

### VFY-123 — External resolver use is attributable

When external I/O resolution is explicitly enabled, a Verifier MUST record/identify the resolver/evidence capability supplying resulting material sufficiently for attribution.

Planned test: verifier-resolver-attribution-001.

### VFY-124 — Provider receipt remains unestablished by adapter evidence

A Verifier MUST NOT report Provider receipt/internal request use solely from Provider Adapter RequestSnapshot/ProviderAttempt evidence.

Planned test: verifier-provider-receipt-unestablished-001.

### VFY-125 — Remote tool receipt/commit remains unestablished by client evidence

A Verifier MUST NOT report remote tool-server receipt, transaction commit, remote retry count, or side-effect cardinality solely from client-side Tool Adapter evidence.

Planned test: verifier-tool-remote-unestablished-001.

### VFY-126 — TrustAssertion stays policy-scoped

A Verifier MUST preserve TrustAssertion issuer/policy/dimension/state and MUST NOT restate trusted/untrusted as objective trustworthiness.

Planned test: verifier-trust-wording-001.

### VFY-127 — TaintAssertion stays policy-scoped

A Verifier MUST preserve TaintAssertion policy/kind/channel/precision/state and MUST NOT restate tainted as malicious or absent as objectively clean.

Planned test: verifier-taint-wording-001.

### VFY-128 — Sanitization does not erase ancestry

A Verifier MUST NOT remove upstream provenance/taint history or create Trust solely because downstream sanitization reports taint absent.

Planned test: verifier-sanitization-history-001.

### VFY-129 — Signed private evidence remains disclosure-bounded

A Verifier MUST NOT describe valid signature over hash_only/HMAC/redacted ARP evidence as direct signature over unavailable original plaintext.

Planned test: verifier-signed-private-evidence-001.

### VFY-130 — Valid linkage does not complete history

A Verifier MUST NOT report valid signed/pinned Receipt linkage as proof that no omitted Receipt, branch, predecessor, successor, or history exists.

Planned test: verifier-linkage-no-history-001.

### VFY-131 — Schema validation does not replace semantic verification

After Schema freeze, a Verifier MUST NOT treat JSON Schema or equivalent structural-schema success as proof that cross-object semantic, representation, cryptographic, provenance, or completeness requirements are satisfied.

Planned test: verifier-schema-not-semantic-proof-001.

### VFY-132 — Schema failure is structural invalidity when applicable

When a selected supported protocol Schema applies and supplied data violates that Schema, a Verifier MUST report the applicable structural invalidity while still permitting independent checks that do not require the invalid structure where safely possible.

Planned test: verifier-schema-failure-001.

### VFY-133 — Unsupported extension does not erase independently verifiable integrity

If an extension/profile semantic is unsupported but the Receipt remains parseable/canonicalizable under a supported integrity profile, a Verifier MUST preserve unsupported semantic findings while still evaluating independent digest/signature checks that do not require understanding that extension.

Planned test: verifier-unsupported-extension-integrity-001.

### VFY-134 — Unknown extension is not silently interpreted

A Verifier MUST NOT invent semantics for an unknown extension field/profile merely because its JSON shape resembles a known object.

Planned test: verifier-unknown-extension-no-guess-001.

### VFY-135 — Unsigned Receipt is not invalid solely for signature absence

A Verifier MUST NOT report a structurally conforming unsigned Receipt invalid solely because no IntegrityEnvelope is present unless the selected verification goal/profile explicitly requires a signature.

Planned test: verifier-unsigned-not-invalid-001.

### VFY-136 — Signature absence is distinct from unverified/invalid

When signature evaluation is applicable but no IntegrityEnvelope exists, a Verifier MUST preserve signature absence as a presence/applicability result rather than fabricate invalid cryptography or unresolved key.

Planned test: verifier-signature-absence-001.

### VFY-137 — Ambiguous key resolution is preserved

If a key reference resolves to multiple incompatible candidate verification keys without a rule establishing one applicable key, a Verifier MUST report ambiguous key resolution and MUST NOT silently select a key solely because one candidate verifies the signature.

Planned test: verifier-key-resolution-ambiguous-001.

### VFY-138 — Key verification success does not resolve unrelated key ambiguity

A successful cryptographic check under one candidate key MUST NOT by itself establish that the ambiguous key reference was uniquely/authoritatively resolved.

Planned test: verifier-key-success-no-identity-resolution-001.

### VFY-139 — Withheld is not not_present

A Verifier MUST NOT report a privacy-withheld representation/value as not_present when the protocol record establishes that the subject/scope exists but its representation is withheld.

Planned test: verifier-withheld-not-not-present-001.

### VFY-140 — Conflict is distinct from unknown

A Verifier MUST NOT collapse positively detected incompatible evidence into unknown merely to avoid reporting conflict.

Planned test: verifier-conflict-not-unknown-001.

### VFY-141 — VerificationReport declares invocation goals and capability summary

A machine-readable VerificationReport MUST identify the selected verification goals/profile and a privacy-safe summary of material capabilities used or unavailable sufficiently to interpret unverified/unsupported findings.

Planned test: verifier-report-goals-capabilities-001.

### VFY-142 — Mandatory checks cannot disappear from machine report

A VerificationReport MUST represent every requested mandatory check as evaluated, blocked/unverified, unsupported, invalid/mismatched, or otherwise explicitly accounted for and MUST NOT silently omit a mandatory check.

Planned test: verifier-report-mandatory-accounting-001.

### VFY-143 — Detected mandatory failures remain visible

A VerificationReport MUST NOT omit detected mandatory invalid/mismatch/conflict findings from the machine-readable result merely because a higher-level summary is shorter.

Planned test: verifier-report-failure-visibility-001.

### VFY-144 — Resolver material is content-bound for reproducibility

When external resolver material contributes to verification, a Verifier MUST retain or identify a stable content commitment/identity for the resolved material sufficient to distinguish later changed resolver output.

Planned test: verifier-resolver-content-binding-001.

### VFY-145 — Trusted-time claim requires recognized time evidence

A Verifier MUST NOT upgrade producer-, adapter-, tool-, provider-, or signer-recorded timestamps to trusted wall-clock time without a recognized trusted-time evidence profile.

Planned test: verifier-trusted-time-required-001.

### VFY-146 — Invalidity and incompleteness can coexist in findings

A Verifier MUST preserve both detected invalid/mismatch findings and blocked/unverified/unsupported mandatory findings when they coexist, even though the process outcome is coarse.

Planned test: verifier-invalid-and-incomplete-coexist-001.

### VFY-147 — Process outcome aggregation precedence is deterministic

When a trustworthy VerificationReport can be produced, process aggregation MUST use deterministic precedence: invalidity_detected over incomplete_evaluation over completed; operational_error is used when the invocation itself cannot reliably complete/report according to its execution contract.

Planned test: verifier-exit-precedence-001.

### VFY-148 — Process outcome never hides detailed findings

A coarse process outcome MUST NOT replace, erase, or semantically override detailed machine-readable findings.

Planned test: verifier-exit-does-not-hide-findings-001.

### VFY-149 — Unsupported optional extension does not force incomplete mandatory baseline

A Verifier MUST NOT classify baseline verification incomplete solely because an optional extension is unsupported when no selected mandatory verification goal depends on that extension.

Planned test: verifier-optional-extension-exit-001.

### VFY-150 — Profile/check applicability is explicit

A Verifier MUST determine whether a check is applicable under the selected Receipt/profile/goals before treating absence, unsupported capability, or unverified evidence as a mandatory verification failure.

Planned test: verifier-check-applicability-001.

## 32. Adversarial architecture review

### Review A — Everything is structurally valid and signed, but Producer fabricated the run

The verifier establishes structural/digest/signature findings while runtime/external propositions remain asserted.

Result: RESOLVED by VFY-001, VFY-059, VFY-065, and VFY-075 through VFY-085.

### Review B — Same Receipt verified once with HMAC key and later without it

The Receipt is unchanged. The later invocation's candidate check is unverified.

Result: RESOLVED by VFY-002 and VFY-040 through VFY-044.

### Review C — Candidate plaintext matches a signed commitment

The report can state candidate-to-commitment match and signature-authenticated commitment. It does not claim the plaintext was directly in the signed Receipt.

Result: RESOLVED by VFY-007 and VFY-129.

### Review D — Dangling InternalReference matches an object ID in another Receipt

It remains a bad/missing local reference, not an implicit ExternalReference.

Result: RESOLVED by VFY-020 and VFY-021.

### Review E — ExternalReference contains an HTTP URL

Baseline verifier does not fetch it. An explicit resolver can, and returned material becomes attributable invocation evidence.

Result: RESOLVED by VFY-027, VFY-028, VFY-122, and VFY-123.

### Review F — Two Receipts reuse one Receipt ID and one has more signatures

Identity conflict is preserved. Signature count is not conflict precedence.

Result: RESOLVED by VFY-017 and VFY-095.

### Review G — Cross-Receipt Derivation creates a cycle

The global resolved graph catches it.

Result: RESOLVED by VFY-029 through VFY-032.

### Review H — Whole request commitment matches but hidden path is claimed

The verifier reports the allowed commitment level and does not upgrade hidden location membership.

Result: RESOLVED by VFY-037 through VFY-039.

### Review I — HMAC tag exists but no secret exists in this invocation

Tag presence/integrity can be checked, but candidate match is unverified.

Result: RESOLVED by VFY-042 through VFY-044 and VFY-079.

### Review J — Digest matches but one envelope signature fails

Digest and per-envelope signature findings remain separate.

Result: RESOLVED by VFY-048 through VFY-058 and VFY-084.

### Review K — Signature verifies over declared digest but supplied ARP differs

Signature cryptographic status can be valid while envelope-to-supplied-ARP binding is mismatched.

Result: RESOLVED by VFY-050 and VFY-058.

### Review L — Key label says TrustedCorp

Signature verification under the key does not establish key ownership or trust.

Result: RESOLVED by VFY-005, VFY-056, and VFY-057.

### Review M — Tool execution completed and result reports success

Completion remains runtime asserted, success remains tool-reported, and external Effect remains unestablished absent stronger evidence.

Result: RESOLVED by VFY-065, VFY-068, and VFY-125.

### Review N — Tool execution failed after external state changed

Failure is not no-effect proof.

Result: RESOLVED by VFY-069.

### Review O — EffectObservation says separate_observation

The verifier can verify the distinct evidence structure as available without turning the external proposition into OutcomeVerification.

Result: RESOLVED by VFY-066, VFY-070, and VFY-071.

### Review P — Trust says trusted and Taint says present

Both policy-scoped assertions are preserved; no safe/unsafe synthesis is invented.

Result: RESOLVED by VFY-126 through VFY-128.

### Review Q — Every explicit reference resolves

Reference closure can be established while runtime/history completeness remains unknown.

Result: RESOLVED by VFY-088 through VFY-092.

### Review R — No bypass diagnostic exists

No instrumentation-completeness conclusion is made.

Result: RESOLVED by VFY-067 and VFY-092.

### Review S — Signature profile is syntactically known but not implemented

Status is unsupported, not invalid and not silently baseline.

Result: RESOLVED by VFY-013, VFY-055, VFY-097, and VFY-098.

### Review T — Supported Ed25519 envelope is malformed

The profile is implemented; malformed/failed check is invalid rather than unsupported.

Result: RESOLVED by VFY-054, VFY-055, and VFY-098.

### Review U — One external Receipt is absent

Independent local checks continue; dependent checks are unresolved/unverified.

Result: RESOLVED by VFY-010, VFY-025, and VFY-102.

### Review V — Human CLI prints only Verified

That would overstate multidimensional findings.

Result: RESOLVED by VFY-110 through VFY-115.

### Review W — CLI exits zero

Exit zero can only mean the selected operational goals completed according to the CLI mapping, not universal truth/completeness.

Result: RESOLVED by VFY-115 through VFY-119.

### Review X — Graph traversal hits a resource limit

Unevaluated checks become incomplete/operationally blocked, not false or invalid.

Result: RESOLVED by VFY-121.

### Review Y — Profile identifier names a module or URL

Untrusted metadata does not authorize arbitrary code or I/O.

Result: RESOLVED by VFY-099 and VFY-122.

### Review Z — Resolution Set order is reversed

Semantic findings remain equivalent unless authenticated protocol data carries order.

Result: RESOLVED by VFY-100 and VFY-120.

### Review AA — Same Receipt has embedded and detached Presentations with different valid envelopes

Receipt occurrence remains one and consistent envelope occurrences can both be evaluated.

Result: RESOLVED by VFY-018 and VFY-101.

### Review AB — One valid envelope and one invalid envelope coexist

Both remain visible. One does not erase the other.

Result: RESOLVED by VFY-051, VFY-061, and VFY-062.

### Review AC — External attestation contradicts Producer assertion

The verifier preserves evidence conflict rather than silently rewriting signed history or invalidating unrelated structure.

Result: RESOLVED by VFY-087 and VFY-093.

### Review AD — Candidate is secret and absent from Receipt

The verifier can report match without echoing candidate plaintext.

Result: RESOLVED by VFY-107 through VFY-109.

### Review AE — Caller requires all signatures to validate

This changes operational exit aggregation only; it does not make signatures prove truth/completeness.

Result: RESOLVED by VFY-008 and VFY-115 through VFY-119.

### Review AF — ProviderAttempt record exists

The verifier can establish record existence while runtime occurrence remains Producer/instrumentation asserted.

Result: RESOLVED by VFY-065 and VFY-066.

### Review AG — ReceiptLink graph is signed, pinned, and resolved

Supplied linkage integrity can be established while global history completeness remains unknown.

Result: RESOLVED by VFY-063, VFY-090, VFY-103, and VFY-130.

### Review AH — Source and target commitments match but target request plaintext is hidden

The verifier reports commitment match at its bounded level and does not upgrade to hidden representation/location verification.

Result: RESOLVED by VFY-037 through VFY-039.

### Review AI — Producer assertion is well-formed but externally unverifiable

The assertion can remain structurally valid and asserted, not invalid merely because truth is unknown.

Result: RESOLVED by VFY-077, VFY-086, and VFY-087.

### Review AJ — UI renders unknown with a green success check

Human rendering cannot strengthen unknown into success.

Result: RESOLVED by VFY-110 and VFY-112.

### Review AK — Receipt is Schema-valid but cross-Receipt Derivation is cyclic

Schema success does not replace semantic graph verification.

Result: RESOLVED by VFY-131.

### Review AL — Receipt contains an optional extension the verifier does not understand

The extension semantic checks are unsupported, but JCS/digest/signature checks can still run when their inputs remain supported and canonicalizable.

Result: RESOLVED by VFY-133, VFY-134, and VFY-149.

### Review AM — Receipt has no signatures

Unsigned does not mean structurally invalid. Signature absence is reported as absence unless the caller/profile requires signature verification.

Result: RESOLVED by VFY-135, VFY-136, and VFY-150.

### Review AN — Key reference resolves to two keys and one verifies

The verifier can report the cryptographic result under the tested key while preserving ambiguous key-reference resolution; successful verification does not silently establish key identity.

Result: RESOLVED by VFY-137 and VFY-138.

### Review AO — Secret ToolInvocation argument exists but is withheld

The argument is withheld, not not_present.

Result: RESOLVED by VFY-139.

### Review AP — Two contradictory CaptureDiagnostics exist

Positive contradiction is conflict, not generic unknown.

Result: RESOLVED by VFY-093 and VFY-140.

### Review AQ — Verification requested five mandatory checks but report only lists four

The machine report is incomplete/non-conforming because mandatory checks cannot silently disappear.

Result: RESOLVED by VFY-141 through VFY-143.

### Review AR — External resolver returns different content tomorrow

The verification invocation/result retains a stable content identity/commitment for the material actually used so later resolver changes do not rewrite the original verification context.

Result: RESOLVED by VFY-144.

### Review AS — Signed adapter timestamp looks plausible

Without recognized trusted-time evidence it remains recorded/signed time, not trusted wall-clock time.

Result: RESOLVED by VFY-145.

### Review AT — One mandatory signature is invalid and another mandatory external proof is unavailable

Both detailed states remain in the report. The coarse process outcome deterministically selects invalidity_detected while preserving the incomplete check.

Result: RESOLVED by VFY-146 through VFY-148.

## 33. Architecture revisions caused by Verifier Contract

### 33.1 VerificationReport and VerificationFinding are verifier-output meta objects

They are not historical runtime provenance nodes and are not inserted into the Receipt under verification.

### 33.2 Verification is capability-relative

A Verification Invocation explicitly defines the Receipts and capabilities used.

A stronger invocation can produce stronger findings without changing the historical Receipt.

### 33.3 Result statuses are typed

valid/invalid, resolved/unresolved/ambiguous, matched/mismatched, established/asserted/unknown/unverified, unsupported, conflict, and not_present live in result-specific domains.

There is no universal verification-strength score.

### 33.4 Signature status and ARP binding are separate

A signature can verify over its statement while the supplied ARP fails to match the authenticated digest.

### 33.5 Baseline verification has no ambient external I/O

Resolvers are explicit capabilities and returned material becomes attributable input evidence.

### 33.6 Machine findings are authoritative

Human summaries and process exit outcomes are bounded renderings/aggregations and cannot strengthen semantic claims.

## 34. Contract decisions

The Verifier Contract locks:

1. verifier authority is bounded by supplied evidence/capabilities;
2. verification is relative to an explicit Verification Invocation;
3. inputs can include Receipt/Resolution Set plus keys, keyed secrets, candidates, recognized proof/evidence profiles, external evidence, and verification goals;
4. evaluation is dependency-ordered while independent checks continue;
5. unsupported profile is distinct from malformed/invalid supported profile; unsupported optional extensions do not block independent baseline integrity checks;
6. baseline verification performs no implicit network/filesystem resolution;
7. ExternalReference resolution is explicit and pin-aware;
8. cross-Receipt identity and graph invariants are globally evaluated after resolution;
9. representation/commitment equality remains scope-bounded;
10. RequestBinding verification preserves its evidence ladder;
11. privacy-dependent verification follows actual capabilities;
12. secret verifier capabilities, withheld values, and undisclosed candidates remain distinct from absence and are not automatically emitted;
13. ARP canonicalization/digest and per-envelope signatures remain separate dimensions; unsigned Receipt remains structurally evaluable;
14. signature validity is separate from supplied-ARP binding and key trust;
15. adapter/runtime statements remain assertions absent stronger evidence;
16. per-claim composition preserves the weakest unresolved/asserted premise;
17. result semantics are typed rather than globally ordered;
18. structural invalidity is distinct from factual uncertainty/conflict;
19. package inventory/reference closure are distinct from runtime/history completeness;
20. conflicts are preserved without generic timestamp/signature-count precedence;
21. fully resolved supplied Resolution Set is not global history;
22. VerificationReport/VerificationFinding are verifier-output meta objects;
23. machine-readable findings are normative, account for all requested mandatory checks, and human output cannot strengthen them;
24. there is no unqualified overall fully_verified boolean;
25. process/CLI outcome is operational aggregation only, with deterministic invalidity_detected > incomplete_evaluation > completed precedence when a trustworthy report is produced;
26. semantic results are deterministic for semantically identical inputs/capabilities;
27. resource limits/operational failure do not rewrite unevaluated claims as invalid/false;
28. untrusted metadata cannot trigger arbitrary code/network/filesystem access;
29. Schema validation does not replace semantic verification, and future extensions remain explicitly supported/unsupported rather than guessed;
30. recorded timestamps do not become trusted time without a recognized time-evidence profile;
31. ordinary Provider/Tool adapter evidence does not establish hidden remote/internal state;
32. valid supplied linkage does not establish complete history.

## 35. Schema-unlock implications

If this contract passes review, all pre-Schema semantic/contract gates are complete.

Schema freeze can then define concrete wire structures for:

- core runtime records/assertions;
- CaptureDiagnostic;
- ExternalReference;
- Receipt/ARP/inventory/scope;
- ReceiptLink;
- IntegrityEnvelope and Signing Statement;
- Provider/Tool adapter capability declarations;
- serialized Verification Invocation references where needed;
- VerificationReport;
- VerificationFinding;
- typed result domains/statuses.

Schema work must encode accepted semantics rather than reopen them implicitly.

## 36. Gate decision

Verifier Contract is ready for adversarial/mechanical review.

JSON Schema remains BLOCKED until this contract passes.
