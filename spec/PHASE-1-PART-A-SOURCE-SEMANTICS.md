# C2ATrace v0.1 — Phase 1 Part A: SourceRef / SourceObservation Semantics

Status: ACCEPTED AFTER ADVERSARIAL REVIEW.

Scope: source identity, locators, observation identity/versioning, redirects and aliases, content commitments, unknown source handling, repeated observations, source-origin claim strength.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Design objective

Part A defines what C2ATrace means when it says that data came from a source.

The central rule is conservative identity:

~~~text
recorded SourceRef identity
≠
real-world resource identity

locator equality
≠
source identity

content equality
≠
source identity

redirect target
≠
source identity

external version token
≠
SourceObservation identity
~~~

A SourceRef gives C2ATrace a stable logical identity inside its resolution scope. A SourceObservation represents one recorded capture occurrence of a representation associated with that SourceRef.

## 2. SourceRef identity model

### 2.1 Recorded logical identity

A SourceRef ID is the protocol-level identity of a logical source within the active C2ATrace resolution scope.

This establishes statements such as:

> these two records refer to the same recorded SourceRef.

It does not independently establish:

> these locators identify the same real-world resource.

or:

> the Producer's source grouping is objectively correct.

### 2.2 Source kind

Source kind is descriptive classification metadata.

Examples may include:

~~~text
system
developer
user
memory
rag
web
database
file
tool
mcp
subagent
application
unknown
~~~

The exact vocabulary remains subject to later vocabulary review.

Source kind is not source identity and is not proof of origin.

### 2.3 Locator

A locator is an address, identifier string, or access reference associated with a SourceRef or with a particular SourceObservation acquisition.

Examples include:

~~~text
https://example.com/article
app://system-prompt
user://message/183
rag://kb/document-17
file:///workspace/policy.md
~~~

Locators are scheme-dependent and may be mutable, aliased, redirected, reused, or produce different representations under different request conditions.

Core v0.1 therefore does not use locator normalization as an implicit source-identity algorithm.

### 2.4 Locator equality

Two equal locator strings establish only string equality of the recorded locator values.

They do not by themselves establish:

- equal SourceRef identity;
- equal SourceObservation identity;
- equal representation;
- equal source state at different times;
- equal application semantics.

Two different locator strings likewise do not prove that two logical sources are different real-world resources.

### 2.5 Multiple locators

A Producer can associate multiple locators with one SourceRef when the Producer intentionally treats them as addresses or identifiers for one recorded logical source.

That grouping is part of the Producer's recorded source model.

It is not independent proof that those locators are objectively equivalent in the external system.

## 3. Redirect and alias semantics

### 3.1 Observation-specific resolution

Redirect and resolver behavior belongs to the observation/acquisition context, not to SourceRef identity itself.

Conceptually a SourceObservation may retain:

~~~text
requested locator
→ zero or more resolution / redirect hops
→ effective locator
→ observed representation
~~~

The exact wire representation is not frozen in Part A.

### 3.2 Redirect is not identity equivalence

A redirect from locator A to locator B records an access-path transition.

It does not automatically establish that:

~~~text
SourceRef(A) == SourceRef(B)
~~~

For HTTP, this intentionally treats redirect metadata as address-resolution evidence rather than a general-purpose identity theorem.

### 3.3 Alias assertion

If a Producer explicitly records that two SourceRefs or locators are aliases for application purposes, that relationship is a Producer assertion.

An alias assertion does not merge the identities or histories of the two SourceRefs in core v0.1.

Core v0.1 does not infer transitive alias closure unless a future profile explicitly defines such semantics.

## 4. SourceObservation identity model

### 4.1 Capture occurrence, not source version

A SourceObservation is an Artifact representing one recorded capture occurrence of a source representation.

It is not a universal version number for the source.

The same SourceRef can therefore have:

~~~text
SourceObservation O1
SourceObservation O2
SourceObservation O3
...
~~~

### 4.2 Repeated observations

Two distinct capture occurrences remain distinct SourceObservations even when:

- they refer to the same SourceRef;
- they use the same locator;
- they have matching content commitments;
- they report the same external validator;
- their timestamps are equal or unavailable.

If the same previously captured SourceObservation Artifact is reused without a new capture occurrence, that existing Artifact can be referenced again instead of manufacturing a new observation.

### 4.3 Observation timestamps

An observation timestamp is Producer-recorded timing metadata.

It does not define SourceObservation identity and does not independently establish source-version ordering.

Logical dependencies remain governed by the graph rules from Phase 0.

## 5. Source-provided version and validator metadata

A SourceObservation may record external version hints such as:

~~~text
revision ID
document version
ETag
Last-Modified
database row version
object generation
commit identifier
~~~

These values describe what the Producer observed or was told by the external system.

They are not C2ATrace Artifact identity.

Core v0.1 does not infer total ordering, source equivalence, or representation equality solely from external version hints.

A source-specific future profile may define stronger semantics for a particular version system.

## 6. Content commitment semantics

### 6.1 Purpose

A content commitment binds a SourceObservation to a particular recorded representation without making that representation the identity of the SourceRef.

Conceptually a commitment has:

~~~text
commitment method
commitment value
representation basis
~~~

Exact schema and cryptographic vocabulary are intentionally deferred.

### 6.2 Representation basis

The representation basis identifies what input was committed.

Examples might include:

~~~text
captured byte sequence
declared canonical encoding of captured text
another explicitly defined representation
~~~

A commitment cannot be meaningfully compared with another commitment unless their commitment method and representation basis are compatible.

### 6.3 Commitment match

A matching compatible commitment supports a representation-level match claim.

It does not establish:

- the same SourceRef;
- the same SourceObservation;
- the same locator;
- the same external resource;
- the same capture occurrence.

### 6.4 Privacy-preserving observations

A SourceObservation can remain useful when original content is not retained.

Conceptually the evidence may be:

~~~text
content retained
commitment only
content unavailable
content state unknown
~~~

The exact wire vocabulary belongs to the later privacy/representation profile.

When content required for representation verification is unavailable, claim strength is downgraded according to CLAIM-002.

## 7. Observation extent and completeness

### 7.1 Declared Capture Target

A Declared Capture Target is the Producer-described representation scope against which observation extent is stated.

Examples include an HTTP selected response representation, a file object, a database projection, an API page, or another explicitly bounded source representation.

Declaring a capture target is itself Producer-authored scope metadata; choosing a narrow target does not prove that a larger external resource was completely captured.

### 7.2 Observation extent

A SourceObservation represents what was captured at the C2ATrace source boundary.

It does not automatically mean the Producer captured the entire remote resource.

Conceptually an observation can describe its extent as:

~~~text
complete relative to the Producer-declared capture target
partial
unknown
~~~

"Complete" remains a Producer assertion about the declared capture target; it is not independent proof that the entire external source was captured.

Examples of partial observations include:

- HTTP range retrieval;
- database projection;
- selected document field;
- paginated API subset;
- file prefix;
- upstream truncation that occurred before the C2ATrace observation boundary.

Detailed partial-range lineage belongs to Phase 1 Part B.

## 8. Unknown source semantics

Unknown source is a first-class state.

A SourceObservation whose source identity cannot be established is associated with a SourceRef whose source classification is unknown rather than with a fabricated trusted locator or inferred source.

Separate unknown SourceRefs remain separate recorded logical identities.

"Unknown A" and "Unknown B" are not merged merely because both have kind unknown.

If later evidence establishes a relationship, it can be represented as an explicit Producer assertion without rewriting prior identity history.

## 9. Source-origin claim matrix

| Claim | Evidence basis | Core v0.1 interpretation |
|---|---|---|
| Two references use the same SourceRef ID in one resolution scope | STRUCTURAL | Same recorded logical source identity |
| Two SourceRefs have equal locator strings | STRUCTURAL string match | No automatic source-identity equivalence |
| Producer associates locator L with SourceRef S | PRODUCER_ASSERTED | Recorded locator association |
| Producer records SourceObservation O as observed from SourceRef S | STRUCTURAL + PRODUCER_ASSERTED premise | Provenance link is present; real origin is not independently proved |
| Supplied content matches O's compatible content commitment | REPRESENTATION | Commitment/representation match |
| O1 and O2 have matching compatible commitments | REPRESENTATION | Matching committed representations, not matching source identity |
| Producer records redirect A → B | PRODUCER_ASSERTED | Recorded resolution transition |
| Producer records alias between two SourceRefs | PRODUCER_ASSERTED | Alias assertion only; identities remain distinct |
| Producer records ETag / revision / Last-Modified | PRODUCER_ASSERTED | External version hint |
| Producer records observation extent as complete | PRODUCER_ASSERTED | Completeness assertion relative to declared capture target |
| External bytes objectively originated from claimed source | unsupported by core | Requires stronger external evidence |
| Two locators identify the same real-world resource | unsupported by core | Requires external/source-specific evidence |
| Full external source state was captured | unsupported by core | Not established from observation existence alone |

## 10. Normative requirements

### SRC-001 — SourceRef identity scope

Within a C2ATrace resolution scope, a verifier MUST use SourceRef identity, not locator, source kind, content commitment, timestamp, or external version metadata, as the protocol-level source identity key.

Planned test: `source-identity-key-001`.

### SRC-002 — SourceRef resolution uniqueness

Within one resolution scope, one SourceRef identity MUST resolve to exactly one SourceRef record.

Planned test: `source-ref-resolution-001`.

### SRC-003 — No locator-based merge

A verifier MUST NOT merge distinct SourceRefs solely because their locators are equal, URI-normalized-equivalent, redirected, or otherwise syntactically related.

Planned test: `source-locator-no-merge-001`.

### SRC-004 — No content-based source merge

A verifier MUST NOT merge distinct SourceRefs or SourceObservations solely because compatible content commitments match.

Planned test: `source-content-no-merge-001`.

### SRC-005 — Multiple locator claim strength

When multiple locators are associated with one SourceRef, a verifier MUST report their external equivalence, if mentioned, as Producer-asserted rather than independently verified.

Planned test: `source-multi-locator-wording-001`.

### SRC-006 — Redirect preservation

When a Producer records both a requested locator and a different effective locator for a SourceObservation, a conforming representation MUST preserve both values; a verifier MUST NOT replace the requested locator with the effective locator as though no redirect/resolution transition occurred.

Planned test: `source-redirect-preservation-001`.

### SRC-007 — Redirect is not alias

A verifier MUST NOT infer SourceRef identity equivalence or alias equivalence solely from a recorded redirect/resolution transition.

Planned test: `source-redirect-no-alias-001`.

### SRC-008 — Alias does not collapse identity

If an alias relationship is recorded between distinct SourceRefs, a verifier MUST preserve the distinct SourceRef identities and MUST NOT merge their prior observations or provenance histories.

Planned test: `source-alias-no-collapse-001`.

### SRC-009 — Observation source cardinality

Every SourceObservation MUST reference exactly one SourceRef in core v0.1.

A representation produced from multiple source observations belongs in the Transform/Derivation model rather than being encoded as a multi-source SourceObservation.

Planned test: `source-observation-cardinality-001`.

### SRC-010 — Unknown source preservation

When source identity is unknown, a conforming Producer MUST represent an unknown SourceRef rather than invent a locator or stronger source classification.

A verifier MUST NOT merge distinct unknown SourceRefs solely because both are unknown.

Planned test: `source-unknown-preservation-001`.

### SRC-011 — Distinct capture occurrences

If a Producer records two distinct source capture occurrences, they MUST have distinct SourceObservation identities even when their content commitments and external version hints match.

Planned test: `source-repeat-observation-001`.

### SRC-012 — Reuse without recapture

If no new source capture occurrence is recorded and the same previously captured SourceObservation Artifact is reused, a Producer MAY reference the existing SourceObservation identity rather than create a duplicate observation.

Planned test: `source-observation-reuse-001`.

### SRC-013 — External version hints are not Artifact identity

A verifier MUST NOT use ETag, Last-Modified, revision IDs, document-version strings, commit identifiers, or similar external version hints as substitutes for SourceObservation identity.

Planned test: `source-version-hint-identity-001`.

### SRC-014 — No implicit version ordering

A verifier MUST NOT infer SourceObservation version ordering solely from external version hints or observation timestamps unless a future source-specific profile defines that ordering rule.

Planned test: `source-version-order-001`.

### SRC-015 — Commitment basis is explicit

Any content commitment used for representation-level verification MUST record both a commitment-method identifier and a representation-basis identifier. Comparability is determined by the applicable commitment profile.

Planned test: `source-commitment-basis-001`.

### SRC-016 — No hidden commitment normalization

A verifier MUST NOT report a commitment as binding exact captured bytes when the recorded commitment basis describes a normalized, canonicalized, decoded, or otherwise different representation.

Planned test: `source-commitment-basis-wording-001`.

### SRC-017 — Comparable commitments only

A verifier MUST NOT report two content commitments as a representation match unless their commitment methods and representation bases are compatible under the applicable profile.

Planned test: `source-commitment-compatibility-001`.

### SRC-018 — Commitment equality is not source identity

A verifier MUST NOT infer equal SourceRef identity, equal SourceObservation identity, or equal external origin from matching content commitments.

Planned test: `source-commitment-no-identity-001`.

### SRC-019 — Observation completeness is bounded

A verifier MUST NOT infer that a SourceObservation contains the full external source solely because the SourceObservation exists or its retained content matches its commitment.

Planned test: `source-observation-completeness-001`.

### SRC-020 — Unknown observation extent

When the Producer cannot establish whether the observation is complete relative to its declared capture target, the observation extent MUST remain unknown rather than being upgraded to complete.

Planned test: `source-observation-extent-unknown-001`.

### SRC-021 — Source-origin claim strength

A verifier MUST NOT report the observed_from relationship, source kind, locator association, redirect trace, alias assertion, observation timestamp, external version hint, or observation-completeness assertion as independently verified external truth solely from core C2ATrace records.

Planned test: `source-origin-claim-strength-001`.

### SRC-022 — Cross-receipt identity is not implicit

Until the external-reference and identity-resolution profile is defined, a verifier MUST NOT infer global SourceRef identity across Receipts solely from equal SourceRef ID strings, equal locators, or matching content commitments.

Planned test: `source-cross-receipt-identity-001`.

## 11. Adversarial architecture review

### Review A — Same URL, different negotiated representations

Scenario:

~~~text
GET https://example.com/doc
Accept-Language: en
→ bytes A

GET https://example.com/doc
Accept-Language: ja
→ bytes B
~~~

One logical SourceRef can have two distinct SourceObservations with the same locator and different representation commitments.

The locator is not treated as a version identifier.

Result: RESOLVED.

### Review B — Two sources contain identical bytes

Scenario:

~~~text
SourceRef A → sha256:X
SourceRef B → sha256:X
~~~

Matching content does not merge the source identities.

Result: RESOLVED by SRC-004 and SRC-018.

### Review C — Permanent HTTP redirect

Scenario:

~~~text
https://old.example/doc
→ 301 / 308
→ https://new.example/doc
~~~

The observation can preserve requested and effective locators.

The redirect does not automatically prove real-world identity equivalence and does not collapse separate SourceRefs.

Result: RESOLVED by SRC-006 and SRC-007.

### Review D — URI normalization appears equivalent

Scenario:

~~~text
HTTP://EXAMPLE.COM/a
http://example.com/a
~~~

Core v0.1 does not use URI normalization to merge SourceRefs.

A source-specific profile could later define safe normalization rules for a constrained scheme/use case.

Result: RESOLVED by SRC-003.

### Review E — Two unrelated unknown sources

Scenario:

~~~text
unknown source A
unknown source B
~~~

They receive distinct SourceRef identities unless the Producer actually knows they are one recorded logical source.

Unknown does not act as a global singleton.

Result: RESOLVED by SRC-010.

### Review F — Same source fetched twice, same bytes

Scenario:

~~~text
capture occurrence 1 → digest X
capture occurrence 2 → digest X
~~~

The observations remain distinct because capture occurrence identity is distinct.

Result: RESOLVED by SRC-011.

### Review G — Same observation reused twice

Scenario:

~~~text
SourceObservation O1
→ used in ModelInvocation A
→ reused in ModelInvocation B
~~~

No new capture occurred, so O1 can be referenced twice.

Result: RESOLVED by SRC-012.

### Review H — ETag agrees but content commitment disagrees

A buggy, malicious, weak, or otherwise unsuitable external validator cannot override the C2ATrace representation commitment.

ETag remains an external version hint.

Result: RESOLVED by SRC-013 and SRC-017.

### Review I — Different ETags, matching content

Different external validators do not automatically establish different SourceObservation content.

If compatible content commitments match, the representation match can be reported while observation identities remain distinct.

Result: RESOLVED.

### Review J — Hidden newline normalization before hashing

If the commitment basis is normalized text, the verifier cannot describe it as a commitment to exact captured bytes.

Any later content-changing normalization used in lineage belongs in the Transform model.

Result: RESOLVED by SRC-015 and SRC-016.

### Review K — Partial source retrieval

A byte range, field projection, API page, or upstream-truncated representation can be recorded as partial.

The existence of a valid commitment proves only the committed observed representation, not source completeness.

Result: RESOLVED by SRC-019 and SRC-020.

### Review L — Content omitted for privacy

A commitment-only SourceObservation can still support later equality checks when the candidate representation is available and the commitment profile permits them.

Without the representation, the verifier reports structural/commitment evidence only and does not claim representation-verified inclusion.

Result: RESOLVED conceptually; exact privacy wire model remains deferred.

### Review M — HTTP 304 / cache reuse

If an application performs a new source-access/capture occurrence whose effective content comes from cache reuse, it records a new SourceObservation if it chooses to record that new capture occurrence.

If it merely reuses an already recorded SourceObservation without a new capture occurrence, it reuses the existing observation identity.

The content commitment can match in both cases.

Result: RESOLVED by the capture-occurrence rule.

### Review N — Source kind is wrong

A signed Receipt can say:

~~~text
source_kind = trusted_local_file
~~~

even when the Producer is wrong or malicious.

The verifier can validate the recorded classification, not its external truth.

Result: ACCEPTED LIMITATION under SRC-021 and Phase 0 claim rules.

### Review O — Alias assertion later proves mistaken

Because alias assertions do not collapse SourceRef identities or rewrite prior observations, a later correction does not require provenance-history mutation.

Result: RESOLVED by SRC-008.

### Review P — Same SourceRef ID string appears in another Receipt

Until cross-receipt resolution semantics exist, equal strings do not create global identity.

Result: RESOLVED by SRC-022.

## 12. Part A resolved decisions

Part A locks the following semantic decisions:

1. SourceRef identity is protocol identity inside a resolution scope, not URI/resource truth.
2. Locator is address/identifier metadata, not the source identity key.
3. Core v0.1 performs no implicit locator normalization for source merging.
4. Redirect is an observation-specific resolution transition, not identity equivalence.
5. Alias is Producer-asserted and does not collapse SourceRef histories.
6. SourceObservation represents a capture occurrence, not a universal source version.
7. External validators/version strings are hints, not Artifact identity.
8. Matching content commitments establish representation-level match only.
9. Unknown source is first-class and not a singleton.
10. Observation completeness is bounded to the declared capture target and is Producer-asserted.
11. Source-origin claims remain Producer-asserted unless a future stronger evidence profile is used.
12. Cross-receipt source identity remains unresolved pending the external-reference profile.

## 13. Open items handed to later phases

Part A intentionally does not freeze:

- exact SourceRef or SourceObservation JSON fields;
- exact locator record wire format;
- exact redirect-trace wire format;
- exact alias-assertion wire representation;
- source-kind vocabulary finalization;
- commitment algorithm vocabulary;
- privacy HMAC/redaction structure;
- exact representation-basis vocabulary;
- partial range coordinates;
- cross-receipt global identity resolution.

These are constrained by Part A semantics but remain schema/profile work.

## 14. Gate decision

Phase 1 Part A: PASS AFTER ADVERSARIAL REVIEW.

The next specification work is Phase 1 Part B:

~~~text
Transform / Derivation Semantics
~~~

Part B is expected to resolve:

- one-to-one, one-to-many, many-to-one lineage;
- exact versus partial versus unknown derivation;
- split, concat, filter, rerank, truncate, template, and normalization semantics;
- range/segment lineage;
- whether derivation can be verified or is only Producer-asserted;
- how lineage behaves when inputs influence control flow but do not contribute output content.

JSON Schema and implementation remain blocked.
