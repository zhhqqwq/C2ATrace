# C2ATrace v0.1 — Phase 1 Part C: RequestSnapshot / RequestBinding Semantics

Status: ACCEPTED AFTER ADVERSARIAL REVIEW.

Scope: ModelInvocation / ProviderAttempt / RequestSnapshot ownership and cardinality; capture-level semantics; request-representation transitions; RequestBinding paths and Regions; text and byte coordinate systems; semantic and byte digests; privacy-preserving / hash-only binding verification strength.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Design objective

Part C defines what C2ATrace means when it says that a ModelInputComponent was present in an application-visible provider request representation.

The central boundary is:

~~~text
recorded application-visible request representation
≠
provider receipt
≠
provider-internal prompt
≠
model-internal representation
~~~

Part C also separates:

~~~text
logical model invocation
physical provider attempt
request representation capture
request representation transition
component-to-request binding
~~~

A RequestBinding is always scoped to one RequestSnapshot. A claim at one capture level does not automatically propagate to another capture level.

## 2. Ownership and cardinality

### 2.1 ModelInvocation

A ModelInvocation is the logical application-level activity requesting a model result.

One ModelInvocation can have zero or more ProviderAttempts.

Zero attempts is valid when the logical invocation is abandoned, rejected, or fails before a physical ProviderAttempt is recorded.

### 2.2 ProviderAttempt

A ProviderAttempt is one physical/application-side attempt to invoke a Provider.

Every ProviderAttempt belongs to exactly one ModelInvocation.

Retries, reconnect attempts, or application-observed failover attempts are distinct ProviderAttempts.

Provider-side retries hidden from the application remain unknown unless separately evidenced.

### 2.3 RequestSnapshot

A RequestSnapshot is an immutable Artifact representing one recorded request representation at exactly one capture level.

A RequestSnapshot is scoped to exactly one owner:

~~~text
ModelInvocation
or
ProviderAttempt
~~~

The owner describes the capture scope, not necessarily the only activity that may later use the immutable snapshot.

### 2.4 Invocation-scoped snapshot

An invocation-scoped RequestSnapshot represents a request representation captured once for the logical invocation and potentially reused unchanged by more than one ProviderAttempt belonging to that same ModelInvocation.

Typical use:

~~~text
ModelInvocation
  sdk_arguments snapshot S
      ├→ ProviderAttempt A
      └→ ProviderAttempt B
~~~

Reuse is valid only when the same immutable recorded representation is reused.

### 2.5 Attempt-scoped snapshot

An attempt-scoped RequestSnapshot represents a request representation captured specifically for one ProviderAttempt.

It is not reusable as an effective request snapshot for another ProviderAttempt.

Typical use:

~~~text
ProviderAttempt A
  provider_payload P1
  prepared_http_body B1

ProviderAttempt B
  provider_payload P2
  prepared_http_body B2
~~~

### 2.6 Effective snapshot per capture level

A ProviderAttempt can be associated with at most one effective RequestSnapshot for each capture level.

Intermediate RequestSnapshots at the same level can exist in the transformation history, but only one can be designated as the effective representation for that attempt at that level.

If no representation was captured at a level, no synthetic snapshot is created merely to fill the level.

## 3. Core capture levels

Part C defines four core capture-level values conceptually:

~~~text
sdk_arguments
provider_payload
prepared_http_body
unknown
~~~

Additional levels require a future profile.

### 3.1 sdk_arguments

sdk_arguments represents the application-visible structured argument representation supplied to the instrumented provider SDK or provider adapter boundary.

It can include, as applicable:

- messages or input items;
- model identifier;
- tool definitions;
- response-format constraints;
- generation parameters;
- media references or values;
- provider-specific options.

It does not establish that all fields will survive provider-specific normalization or serialization.

### 3.2 provider_payload

provider_payload represents the provider-specific structured request payload visible to the application/adapter after the recorded normalization/defaulting/conversion steps that precede body serialization.

It can differ from sdk_arguments through:

- field renaming;
- default insertion;
- omission;
- schema conversion;
- tool-definition conversion;
- model alias resolution;
- provider-specific wrapping;
- other application-visible preparation.

It remains a structured application-visible representation, not proof of transport bytes or Provider receipt.

### 3.3 prepared_http_body

prepared_http_body represents the exact body byte sequence captured at the instrumented application-side transport boundary after the application-visible serialization steps included in that boundary.

It does not, by itself, establish:

- HTTP headers;
- later content coding or compression outside the capture boundary;
- proxy rewrites;
- TLS/framing bytes;
- bytes actually received by the Provider;
- provider-internal request representation.

The capture record therefore describes the representation basis of the prepared body.

### 3.4 unknown

unknown means the instrumentation cannot justify one of the stronger capture-level classifications.

Unknown is not silently upgraded based on payload shape, media type, adapter name, or inferred transport behavior.

## 4. Request representation transitions

### 4.1 Transition model

RequestSnapshot transitions reuse the Phase 1 Part B Transform / Derivation model.

Conceptually:

~~~text
RequestSnapshot(sdk_arguments)
        ↓
Transform(request preparation)
        ↓
RequestSnapshot(provider_payload)
        ↓
Transform(serialization / preparation)
        ↓
RequestSnapshot(prepared_http_body)
~~~

A transition is recorded only when instrumentation actually records enough information to assert that relationship.

The presence of two snapshots at adjacent capture levels does not by itself establish a Transform or Derivation between them.

### 4.2 Missing levels

A recorded request pipeline can skip levels:

~~~text
sdk_arguments
    ↓ recorded Transform
prepared_http_body
~~~

or:

~~~text
provider_payload only
~~~

A missing intermediate snapshot means the representation is not supplied in the recorded provenance scope.

It does not mean the application or SDK had no such internal representation.

### 4.3 Transition direction

For the core request-preparation pipeline, the declared progression is:

~~~text
sdk_arguments
→ provider_payload
→ prepared_http_body
~~~

A transform that parses a body back into structured data for verification or analysis is not a forward request-preparation transition; it is a separate analysis Transform and must not be used to rewrite the historical capture-level ordering.

### 4.4 Mutation and snapshot identity

If the recorded representation changes at a capture level, a new RequestSnapshot identity is required.

Examples:

- retry adds a request identifier into provider payload;
- fallback changes requested model;
- serialization produces different body bytes;
- default insertion differs between attempts.

Equal digests can support representation equality but do not merge distinct capture occurrences when separate snapshots were recorded.

### 4.5 Different levels remain different snapshots

Snapshots at different capture levels remain distinct RequestSnapshot identities even when their visible content appears equal.

The reason is semantic: they make claims about different application observation boundaries.

## 5. ProviderAttempt request association

A ProviderAttempt can reference effective snapshots at zero or more capture levels.

Example:

~~~text
ModelInvocation I
  invocation-scoped S0: sdk_arguments

ProviderAttempt A
  effective sdk_arguments: S0
  effective provider_payload: P1
  effective prepared_http_body: B1

ProviderAttempt B
  effective sdk_arguments: S0
  effective provider_payload: P2
  effective prepared_http_body: B2
~~~

If attempt B changes payload or body, it gets new snapshots at those levels even when the logical invocation is the same.

If a physical attempt is recorded but request capture failed, the attempt can exist with no RequestSnapshot. The verifier reports request evidence as unavailable/unknown rather than fabricating a representation.

## 6. RequestBinding semantics

### 6.1 Purpose

A RequestBinding is an Assertion that one ModelInputComponent scope appears at one location in one RequestSnapshot.

It links:

~~~text
source scope:
  one ModelInputComponent
  optionally narrowed to one Region

to:

target:
  one RequestSnapshot
  one RequestLocation
~~~

### 6.2 One occurrence per binding

One RequestBinding represents one recorded occurrence.

If the same component appears twice in the same RequestSnapshot, two RequestBindings are used.

This prevents one binding from hiding occurrence multiplicity.

### 6.3 Source scope

A binding can cover:

- the entire ModelInputComponent; or
- one Region of the ModelInputComponent.

If only part of a component is included, the source Region is identified.

### 6.4 RequestLocation

A RequestLocation identifies the target scope within the RequestSnapshot.

Conceptually it is either:

~~~text
path selector, when applicable
+
optional Region within the selected value
~~~

or, for a byte-oriented whole body:

~~~text
byte Region over the RequestSnapshot
~~~

The exact JSON wire shape remains unfrozen.

## 7. Request path semantics

### 7.1 Path scheme

Every structured request path has an explicit path-scheme identifier.

Core v0.1 defines json_pointer as the interoperable path scheme for snapshots represented in the JSON data model.

Other path schemes require an identified profile.

A verifier that does not understand the path scheme reports the binding path as unsupported/unverified rather than guessing.

### 7.2 JSON Pointer target

For json_pointer, the path selects a value in the structured RequestSnapshot representation.

A path to a JSON string selects the decoded string value, not the lexical JSON source bytes including quotes and escape sequences.

A path to an object, array, number, boolean, or null selects that whole structured value.

### 7.3 Prepared-body paths

A prepared_http_body snapshot is fundamentally byte-oriented.

A JSON Pointer or other structured path alone is insufficient to establish byte-level location in a prepared body.

A byte-level prepared-body binding requires an explicit byte Region or a future profile that supplies a verifiable parse/serialization location proof.

## 8. Region and coordinate systems

Part C specializes the Part B Region model for request bindings.

### 8.1 Text Region

Core v0.1 text ranges use:

~~~text
unit: unicode_scalar
interval: half-open [start, end)
~~~

Offsets count Unicode scalar values in the selected decoded text value.

They do not count:

- UTF-8 bytes;
- UTF-16 code units;
- grapheme clusters;
- lexical JSON escape characters.

A valid text interval satisfies:

~~~text
0 <= start <= end <= scalar_length
~~~

### 8.2 Ill-formed Unicode

unicode_scalar can be representation-verified only when the selected text representation is a valid Unicode scalar sequence.

If a representation contains unmatched surrogate code units or another profile-specific non-scalar string form, the verifier does not reinterpret those values as Unicode scalars.

A different explicit coordinate profile is required or the range remains unverified.

### 8.3 Byte Region

Core v0.1 byte ranges use:

~~~text
unit: byte
interval: half-open [start, end)
~~~

Offsets index the exact byte sequence of the selected byte-oriented representation.

A valid byte interval satisfies:

~~~text
0 <= start <= end <= byte_length
~~~

### 8.4 Whole-value binding

If a binding targets an entire selected structured value, no sub-value Region is required.

If a binding targets the entire byte-oriented RequestSnapshot, no byte subrange is required.

Whole value is always relative to the selected representation basis.

### 8.5 Binary and media values

Core v0.1 supports binary/media partial binding at the byte Region level when the snapshot representation exposes the relevant bytes directly.

Richer media selectors such as image rectangles, audio time spans, PDF object ranges, or video tracks require future profiles.

If media was transformed into base64, multipart framing, or another encoding before the target RequestSnapshot, the binding applies to the representation visible at that snapshot. Lineage back to the original media uses Part B Transform / Derivation semantics.

## 9. Binding verification semantics

Part C refines CLAIM-002 into distinct verification outcomes.

### 9.1 Recorded binding

A RequestBinding exists in the supplied provenance.

This is only presence of the Assertion.

### 9.2 Structurally valid binding

A binding is structurally valid when:

- source component/Region references resolve;
- target RequestSnapshot resolves;
- path scheme is recognized or syntactically valid under its profile;
- path resolves when the target representation is available;
- Region basis/unit is compatible with the selected value;
- interval bounds are valid when lengths are available.

Structural validity alone does not prove that source and target representations match.

### 9.3 Commitment-matched binding evidence

A verifier can report compatible commitment equality when the source scope and the exact target scope both have comparable commitments.

Commitment equality supports equality of the committed representations under the commitment assumptions.

For a subpath or subrange of a larger RequestSnapshot, merely recording a separate digest for the claimed target region does not independently prove that the region is actually contained at that location unless the relation to the enclosing snapshot is verifiable.

### 9.4 Representation-verified binding

A binding is representation-verified when the verifier can independently obtain the source and target representations required by the binding, resolve the target location, and verify the claimed equality/mapping under the applicable representation profile.

Examples:

- text component equals selected JSON string Region;
- structured component canonical representation equals selected structured value under a declared semantic profile;
- byte component equals a byte Region of the prepared body.

### 9.5 Proof-verified future profiles

A future cryptographic inclusion-proof profile can establish subrepresentation membership without revealing the full RequestSnapshot.

Core v0.1 does not invent such proof semantics.

Until such a profile exists, hash-only subrange/path bindings generally remain structurally valid and Producer-asserted, even when recorded subrange commitments match.

## 10. Semantic digest and byte digest

### 10.1 Semantic digest

A semantic digest is a digest over a canonical byte encoding of a structured RequestSnapshot under an explicitly identified semantic canonicalization profile.

Conceptually:

~~~text
structured representation
    ↓ canonicalization profile
canonical bytes
    ↓ digest algorithm
semantic digest
~~~

The canonicalization profile is part of the digest meaning.

Semantic-digest equality means the two committed structured representations canonicalize to equal digest inputs under the same compatible profile and digest method.

It does not mean their original serialized bytes were equal.

### 10.2 Byte digest

A byte digest is a digest directly over the exact captured byte sequence of a byte-oriented RequestSnapshot.

For prepared_http_body, byte digest is the direct representation commitment when the exact captured body bytes are available to the Producer.

Byte-digest validity does not establish that the Provider received those bytes.

### 10.3 Digest compatibility

Digest values are comparable only when:

- commitment/digest algorithms are compatible; and
- representation bases are compatible; and
- for semantic digests, canonicalization profiles are compatible.

### 10.4 Semantic versus byte equality

The following implications are invalid in core v0.1:

~~~text
semantic_digest equal
⇒ byte_digest equal

byte_digest equal
⇒ same capture level

byte_digest equal
⇒ same RequestSnapshot identity

semantic_digest equal
⇒ same RequestSnapshot identity
~~~

A serialized JSON body can have different byte representation while preserving the same structured semantics.

## 11. Hash-only and privacy-preserving binding strength

### 11.1 Whole-scope commitment comparison

If a binding source covers one whole component representation and the binding target covers one whole RequestSnapshot whose comparable commitment is directly recorded, a verifier can report commitment equality without possessing plaintext.

This is a commitment-level equality result, not proof of Provider receipt or Producer honesty.

### 11.2 Subpath / subrange hash-only limitation

For a binding into a subpath or subrange of a larger RequestSnapshot, a whole-snapshot digest does not prove the claimed sublocation.

A Producer-recorded digest for the claimed subrange can be compared with the component digest, but absent the target representation or a recognized inclusion-proof profile, the verifier cannot independently prove that the committed subrange is actually present at the claimed path/range.

### 11.3 Redacted snapshot

If the stored RequestSnapshot representation is redacted, its semantic or byte digest binds the redacted representation unless the applicable profile explicitly commits to pre-redaction material.

A binding cannot be representation-verified against missing pre-redaction content merely because the redacted snapshot is validly signed.

### 11.4 HMAC

An HMAC-based commitment can support equality checks only for a verifier possessing the required secret and applying the same representation basis/profile.

Independent third-party verification without the secret is unavailable.

The exact privacy profile remains outside Part C.

## 12. Binding across capture levels

A RequestBinding is level-local.

Example:

~~~text
ContextFragment C
    ↓ RequestBinding
provider_payload P
~~~

does not automatically establish:

~~~text
C bound into prepared_http_body B
~~~

even when P has a recorded transition to B.

A later binding can be:

- explicitly recorded; or
- derived by a verifier only when an exact, coordinate-compatible transition mapping establishes the corresponding later RequestLocation.

If serialization escapes, re-encodes, restructures, compresses, or otherwise changes representation coordinates, the later exact location requires an explicit compatible mapping.

## 13. Capture-level claim matrix

| Claim | Evidence basis | Interpretation |
|---|---|---|
| Snapshot S has capture_level=sdk_arguments | STRUCTURAL + PRODUCER_ASSERTED classification | Recorded adapter-entry representation class |
| Snapshot P has capture_level=provider_payload | STRUCTURAL + PRODUCER_ASSERTED classification | Recorded provider-specific structured payload |
| Snapshot B has capture_level=prepared_http_body | STRUCTURAL + PRODUCER_ASSERTED classification | Recorded application-side prepared body bytes |
| Attempt A references effective snapshot P | STRUCTURAL + PRODUCER_ASSERTED occurrence premise | Attempt-to-snapshot association |
| Binding C→P exists | STRUCTURAL + PRODUCER_ASSERTED | Recorded inclusion assertion at P only |
| Binding C→P is representation-verified | REPRESENTATION | Target path/range independently checked |
| Binding C→P has matching recorded subrange digest only | REPRESENTATION commitment match + PRODUCER_ASSERTED location premise | Does not independently prove subrange membership |
| P transitions to B | STRUCTURAL + PRODUCER_ASSERTED; optionally REPRESENTATION-verifiable | Recorded request-preparation lineage |
| semantic digest matches | REPRESENTATION | Canonical structured representations match under profile |
| byte digest matches | REPRESENTATION | Captured byte representations match under profile |
| prepared body bytes were received by Provider | unsupported by core | Requires Provider/transport evidence |
| prepared body equals provider-internal model input | PROHIBITED_INFERENCE | Outside core visibility |
| binding at provider_payload implies binding at prepared_http_body | unsupported without mapping | Requires explicit/derived later binding |

## 14. Normative requirements

### REQ-001 — ProviderAttempt invocation ownership

Every ProviderAttempt MUST reference exactly one ModelInvocation.

Planned test: request-attempt-invocation-cardinality-001.

### REQ-002 — Attempt identity remains distinct

Distinct recorded ProviderAttempts MUST retain distinct ProviderAttempt identities even when they use identical RequestSnapshots.

Planned test: request-attempt-identity-001.

### REQ-003 — Snapshot capture level

Every RequestSnapshot MUST declare exactly one capture level.

Planned test: request-snapshot-capture-level-001.

### REQ-004 — Snapshot scope owner

Every RequestSnapshot MUST have exactly one capture-scope owner: either one ModelInvocation or one ProviderAttempt.

Planned test: request-snapshot-owner-cardinality-001.

### REQ-005 — Attempt-scoped isolation

An attempt-scoped RequestSnapshot MUST NOT be designated as an effective RequestSnapshot for a different ProviderAttempt.

Planned test: request-attempt-snapshot-isolation-001.

### REQ-006 — Invocation-scoped reuse boundary

An invocation-scoped RequestSnapshot MAY be reused as an effective snapshot only by ProviderAttempts belonging to that same ModelInvocation.

Planned test: request-invocation-snapshot-reuse-001.

### REQ-007 — Effective snapshot cardinality

For one ProviderAttempt and one capture level, at most one RequestSnapshot MUST be designated as the effective snapshot.

Planned test: request-effective-snapshot-cardinality-001.

### REQ-008 — Missing capture is not synthesized

If a request representation was not captured at a level, a conforming Producer MUST NOT create a synthetic RequestSnapshot solely to satisfy capture-level completeness.

Planned test: request-no-synthetic-snapshot-001.

### REQ-009 — Different levels have distinct identities

Two RequestSnapshots at different capture levels MUST have distinct RequestSnapshot identities even when their committed representations are equal.

Planned test: request-level-identity-separation-001.

### REQ-010 — Mutation requires new snapshot identity

When a recorded request representation changes, the changed representation MUST NOT reuse the RequestSnapshot identity of the prior representation.

Planned test: request-mutation-new-snapshot-001.

### REQ-011 — Capture-level bounded reporting

A verifier MUST NOT report a RequestSnapshot as evidence for a stronger application/provider boundary than its declared capture level establishes.

Planned test: request-capture-level-overclaim-001.

### REQ-012 — Unknown capture level remains unknown

A verifier MUST NOT upgrade capture_level=unknown based solely on payload shape, media type, adapter identity, or guessed request-processing behavior.

Planned test: request-capture-level-unknown-001.

### REQ-013 — No implicit request transition

A verifier MUST NOT infer a Transform or Derivation between RequestSnapshots solely because their capture levels are adjacent or their contents appear similar.

Planned test: request-transition-no-inference-001.

### REQ-014 — Forward preparation ordering

A Transform recorded specifically as a forward request-preparation transition MUST NOT declare a target core capture level earlier than its source core capture level in the sequence sdk_arguments → provider_payload → prepared_http_body.

Planned test: request-transition-order-001.

### REQ-015 — Cross-level binding is not automatic

A RequestBinding targeting one RequestSnapshot MUST NOT be treated as a binding to another RequestSnapshot solely because a request-transition path exists between them.

Planned test: request-binding-level-local-001.

### REQ-016 — Binding source cardinality

Every RequestBinding MUST identify exactly one ModelInputComponent, optionally narrowed to one source Region.

Planned test: request-binding-source-cardinality-001.

### REQ-017 — Binding target cardinality

Every RequestBinding MUST identify exactly one RequestSnapshot and exactly one RequestLocation within that snapshot.

Planned test: request-binding-target-cardinality-001.

### REQ-018 — One occurrence per binding

If the same ModelInputComponent occurrence is recorded at two distinct RequestLocations, the representation MUST use distinct RequestBinding Assertions for those occurrences.

Planned test: request-binding-occurrence-cardinality-001.

### REQ-019 — Partial source scope

When only part of a ModelInputComponent is claimed to be included, the RequestBinding MUST identify a source Region rather than imply whole-component inclusion.

Planned test: request-binding-partial-source-001.

### REQ-020 — Structured path scheme is explicit

Every structured RequestLocation path MUST identify its path scheme.

Planned test: request-path-scheme-001.

### REQ-021 — JSON-data-model interoperability path

For a RequestSnapshot declared to use the JSON data model, a conforming core v0.1 interoperable path MUST use the json_pointer path scheme.

Planned test: request-json-pointer-001.

### REQ-022 — Unsupported path schemes are not guessed

A verifier MUST NOT reinterpret an unsupported path scheme as JSON Pointer or another known path scheme.

Planned test: request-path-no-guess-001.

### REQ-023 — Prepared body requires byte location for byte-level claim

A verifier MUST NOT report byte-level inclusion in a prepared_http_body from a structured request path alone; an explicit byte Region or a recognized verifiable mapping profile is required.

Planned test: request-body-byte-location-001.

### REQ-024 — Text coordinate unit

A core v0.1 text RequestBinding Region MUST use Unicode scalar value offsets with half-open [start,end) interval semantics.

Planned test: request-text-coordinate-001.

### REQ-025 — Text interval bounds

A representation-verified Unicode-scalar text Region MUST satisfy 0 <= start <= end <= scalar_length of the selected decoded text value.

Planned test: request-text-range-bounds-001.

### REQ-026 — Ill-formed scalar sequences

A verifier MUST NOT report a unicode_scalar Region as representation-verified when the selected text representation cannot be interpreted as a valid Unicode scalar sequence under the applicable profile.

Planned test: request-text-invalid-scalar-001.

### REQ-027 — Byte coordinate unit

A core v0.1 byte RequestBinding Region MUST use byte offsets with half-open [start,end) interval semantics.

Planned test: request-byte-coordinate-001.

### REQ-028 — Byte interval bounds

A representation-verified byte Region MUST satisfy 0 <= start <= end <= byte_length of the selected byte representation.

Planned test: request-byte-range-bounds-001.

### REQ-029 — Region basis remains explicit

A verifier MUST NOT compare RequestBinding Regions across different representation bases or coordinate schemes without an applicable mapping profile.

Planned test: request-region-basis-001.

### REQ-030 — Binary/media core partial binding

A core v0.1 verifier MUST support byte-Region binding for binary/media request representations when the relevant bytes are directly exposed by the RequestSnapshot representation.

Planned test: request-binary-byte-binding-001.

### REQ-031 — Encoded media is bound at visible representation

If media has been encoded or wrapped before the target RequestSnapshot, a RequestBinding MUST describe the representation visible at that snapshot; ancestry to earlier media representation MUST use Transform/Derivation lineage rather than pretending the representations are identical.

Planned test: request-media-encoded-lineage-001.

### REQ-032 — Semantic digest profile

A semantic digest MUST identify both its digest method and the semantic canonicalization profile that defines its digest input.

Planned test: request-semantic-digest-profile-001.

### REQ-033 — Byte digest basis

A byte digest MUST bind the exact declared captured byte sequence and MUST NOT be reported as a digest of later transport or Provider-received bytes without separate evidence.

Planned test: request-byte-digest-basis-001.

### REQ-034 — Digest comparability

A verifier MUST NOT compare semantic or byte digests as representation-equality evidence unless their digest methods and representation/canonicalization bases are compatible.

Planned test: request-digest-compatibility-001.

### REQ-035 — Semantic equality is not byte equality

A verifier MUST NOT infer byte equality solely from semantic-digest equality.

Planned test: request-semantic-not-byte-001.

### REQ-036 — Digest equality is not snapshot identity

A verifier MUST NOT merge RequestSnapshot identities solely because semantic or byte digests match.

Planned test: request-digest-no-identity-001.

### REQ-037 — Structural binding is not representation verification

A verifier MUST distinguish a structurally valid RequestBinding from a representation-verified RequestBinding.

Planned test: request-binding-verification-level-001.

### REQ-038 — Hash-only sublocation limitation

For a subpath or subrange binding, a verifier MUST NOT report independently verified inclusion solely from a whole-snapshot digest and/or a Producer-recorded digest for the claimed target sublocation when no target representation or recognized inclusion proof is available.

Planned test: request-hash-only-sublocation-001.

### REQ-039 — Commitment match wording

When only compatible source/target commitments are available, verifier output MUST preserve the distinction between commitment equality and independently verified target-location membership.

Planned test: request-commitment-match-wording-001.

### REQ-040 — Whole-scope commitment equality

When both the source scope and target scope are entire committed representations and their compatible commitments match, a verifier MAY report commitment-level representation equality without possessing plaintext, while preserving Producer-assertion and external-truth limitations.

Planned test: request-whole-commitment-equality-001.

### REQ-041 — Redacted snapshot scope

A verifier MUST NOT use the validity of a redacted RequestSnapshot to claim representation verification against unavailable pre-redaction request content.

Planned test: request-redacted-binding-001.

### REQ-042 — HMAC verification dependency

A verifier MUST NOT report HMAC-based representation equality unless it possesses the required secret or relies on a separately defined trusted verification result.

Planned test: request-hmac-verification-001.

### REQ-043 — Exact binding propagation

A verifier MAY derive a later-capture-level RequestBinding from an earlier binding only when an exact, coordinate-compatible request-transition mapping establishes the target RequestLocation at the later snapshot.

Planned test: request-binding-propagation-exact-001.

### REQ-044 — Partial transition blocks exact binding propagation

If a required request-transition mapping is partial, a verifier MUST NOT report the propagated later binding as exact representation-verified inclusion.

Planned test: request-binding-propagation-partial-001.

### REQ-045 — Unknown transition blocks positive propagation

If an essential request-transition contribution or location mapping is unknown, a verifier MUST NOT synthesize a positive later RequestBinding solely from the earlier binding and surrounding snapshots.

Planned test: request-binding-propagation-unknown-001.

### REQ-046 — Prepared body is not Provider receipt

A verifier MUST NOT report prepared_http_body capture as proof that the Provider received those body bytes.

Planned test: request-prepared-body-no-provider-receipt-001.

### REQ-047 — Prepared body is not wire-completeness proof

A verifier MUST NOT describe prepared_http_body as the complete on-wire HTTP request unless a future transport-evidence profile establishes headers, transfer/content codings, framing, and other required transport details.

Planned test: request-prepared-body-no-wire-overclaim-001.

### REQ-048 — Provider internals remain outside binding scope

A RequestBinding MUST NOT be reported as proof of provider-internal prompt composition or model-internal representation.

Planned test: request-binding-no-provider-internal-001.

## 15. Adversarial architecture review

### Review A — Same sdk_arguments reused across retries

~~~text
ModelInvocation I
  S = sdk_arguments

Attempt A uses S
Attempt B uses S
~~~

This is valid when S is invocation-scoped and the immutable representation is actually reused.

Attempt identities remain distinct.

Result: RESOLVED by REQ-002, REQ-004, and REQ-006.

### Review B — Retry changes payload but not logical invocation

~~~text
Attempt A
  provider_payload P1

Attempt B
  provider_payload P2
~~~

P1 and P2 are distinct snapshots. Same ModelInvocation does not collapse them.

Result: RESOLVED by REQ-010.

### Review C — Attempt captured only prepared body

No sdk_arguments or provider_payload snapshot is fabricated.

A binding can still target the prepared body if the relevant byte location is known.

Result: RESOLVED by REQ-008.

### Review D — SDK arguments contain component but payload drops it

~~~text
Component C
  ↓ bound to sdk_arguments S

S → Transform → provider_payload P
~~~

If P omits C, the S binding does not propagate to P.

Result: RESOLVED by REQ-015 and REQ-043 through REQ-045.

### Review E — Provider payload inserts defaults

A default field can be transform-generated or derived from an explicit configuration Artifact.

It is not attributed to unrelated ModelInputComponents.

Result: RESOLVED by Part B semantics.

### Review F — JSON serialization escapes a string

Structured payload:

~~~text
"line1\nline2"
~~~

Decoded string Region uses Unicode scalar offsets.

Prepared body uses serialized byte offsets including escape bytes.

A provider_payload RequestBinding therefore cannot copy its coordinates directly to prepared_http_body.

Result: RESOLVED by REQ-024, REQ-027, REQ-029, and REQ-043.

### Review G — Emoji and UTF-16 implementation

Text:

~~~text
A😀B
~~~

The core coordinate unit counts Unicode scalar values, so the emoji is one scalar regardless of a language runtime's UTF-16 code-unit indexing.

An implementation must convert correctly rather than serialize native string indices as protocol offsets.

Result: RESOLVED by REQ-024.

### Review H — Unpaired surrogate in SDK string object

A runtime may expose a string representation that cannot be interpreted as valid Unicode scalar sequence.

The verifier does not pretend the offsets are Unicode scalar offsets.

Result: RESOLVED by REQ-026.

### Review I — Same semantic JSON, different serialized bytes

~~~text
{"a":1,"b":2}
{"b":2,"a":1}
~~~

A compatible semantic canonicalization profile may produce the same semantic digest.

The byte digests can differ.

Result: RESOLVED by REQ-032 through REQ-035.

### Review J — Hash-only receipt with claimed JSON subrange

The receipt provides:

- whole provider_payload semantic digest;
- component digest;
- Producer-recorded path/range;
- no payload plaintext.

The verifier cannot recompute the selected target location from the whole digest.

It reports structural validity and any commitment match, not independently verified inclusion.

Result: RESOLVED by REQ-037 through REQ-039.

### Review K — Whole component equals whole snapshot, both hash-only

If compatible commitments match and both binding scopes are entire representations, commitment-level equality can be reported without plaintext.

This still does not prove Producer honesty or Provider receipt.

Result: RESOLVED by REQ-040.

### Review L — Prepared body JSON Pointer without byte range

A parser could locate a field semantically, but a JSON Pointer alone does not identify its serialized body byte range.

Byte-level inclusion remains unverified unless explicit mapping/proof exists.

Result: RESOLVED by REQ-023.

### Review M — Base64 media

Raw image bytes:

~~~text
Image Artifact
→ base64 Transform
→ provider_payload string
→ JSON serialization
→ prepared_http_body bytes
~~~

The original image bytes are not falsely treated as the same representation as base64 text or JSON bytes.

Result: RESOLVED by REQ-031 and Part B lineage.

### Review N — Compression after prepared_http_body capture

The recorded body bytes can be exact at the application boundary and still differ from later transferred encoded bytes.

No wire-byte overclaim is permitted.

Result: RESOLVED by REQ-033 and REQ-047.

### Review O — SDK performs hidden internal retry

If instrumentation observes only one adapter-level ProviderAttempt and cannot observe the SDK's internal retry, C2ATrace does not invent hidden ProviderAttempts.

The hidden behavior remains unknown.

Result: ACCEPTED LIMITATION under Phase 0 unknown semantics.

### Review P — Multiple snapshots at one level during mutation

An attempt can have several historical/intermediate payload snapshots, but only one is the effective provider_payload for that attempt.

This preserves mutation history without making the final request ambiguous.

Result: RESOLVED by REQ-007 and REQ-010.

### Review Q — Same prepared body bytes used by two attempts

If the snapshot was captured once at invocation scope and genuinely reused unchanged, both attempts can reference it.

If each attempt has its own body capture occurrence, separate attempt-scoped snapshots remain distinct even when byte digests match.

Digest equality never merges snapshot identity.

Result: RESOLVED by REQ-004 through REQ-006 and REQ-036.

### Review R — Binding duplicated twice in same prompt

The same component appears at two distinct request locations.

Two RequestBindings preserve occurrence multiplicity.

Result: RESOLVED by REQ-018.

### Review S — Partial component included

Only characters 100..200 of a ContextFragment are copied into the request.

The binding records a source Region rather than asserting whole-component inclusion.

Result: RESOLVED by REQ-019.

### Review T — Redacted receipt

The application sent plaintext, but the retained receipt stores only a redacted request representation.

The verifier validates the redacted representation unless a separate pre-redaction commitment/proof profile exists.

It does not claim plaintext binding verification.

Result: RESOLVED by REQ-041.

### Review U — Same body digest, different capture level labels

Equal digest does not make sdk_arguments, provider_payload, and prepared_http_body the same RequestSnapshot.

Capture boundary remains part of snapshot semantics.

Result: RESOLVED by REQ-009 and REQ-036.

### Review V — Provider acknowledges receipt

A future Provider-originated response or transport proof might establish stronger receipt evidence.

Core Part C does not upgrade prepared_http_body capture merely because the application later obtained a model response; provider-side exact request receipt still requires an evidence profile.

Result: ACCEPTED DEFERRED EXTENSION.

## 16. Architecture revisions caused by Part C

### 16.1 RequestSnapshot ownership is explicit

Phase 0's simple:

~~~text
ProviderAttempt → uses_request → RequestSnapshot
~~~

is refined.

A RequestSnapshot has exactly one capture-scope owner:

~~~text
ModelInvocation
or
ProviderAttempt
~~~

A ProviderAttempt then designates effective RequestSnapshots by capture level.

This permits logical-call snapshots to be reused across retries while preserving attempt-specific mutation.

### 16.2 RequestSnapshot transitions use Transform / Derivation

The request pipeline does not need a new transition object.

Part B already supplies the correct semantics:

~~~text
RequestSnapshot
→ Transform
→ RequestSnapshot
+
qualified Derivation / Region mapping where justified
~~~

### 16.3 RequestBinding is occurrence-specific and level-local

A RequestBinding now semantically identifies:

~~~text
one source component scope
→
one occurrence at one RequestLocation
→
one RequestSnapshot
~~~

It does not automatically propagate across request-representation transitions.

### 16.4 Structured and byte coordinates are deliberately different

Core request binding coordinates are:

~~~text
structured JSON path: json_pointer
text Region: Unicode scalar half-open interval
byte Region: byte half-open interval
~~~

Prepared-body byte locations are not inferred from structured paths.

## 17. Part C resolved decisions

Part C locks the following decisions:

1. Every ProviderAttempt belongs to exactly one ModelInvocation.
2. RequestSnapshot has an explicit ModelInvocation- or ProviderAttempt-scoped owner.
3. One attempt has at most one effective snapshot per capture level.
4. Invocation-scoped snapshots can be reused only within that invocation.
5. Request representation mutation creates a new snapshot identity.
6. Different capture levels remain different snapshot identities.
7. Core levels are sdk_arguments, provider_payload, prepared_http_body, and unknown.
8. Request transitions reuse Transform / Derivation rather than introducing a parallel lineage model.
9. Missing capture levels remain missing/unknown and are not synthesized.
10. RequestBinding is level-local and occurrence-specific.
11. JSON-data-model request paths use json_pointer in the core interoperable profile.
12. Text ranges use Unicode scalar half-open coordinates.
13. Byte ranges use byte half-open coordinates.
14. Prepared-body byte inclusion requires byte location evidence, not structured path alone.
15. Binary/media core partial binding uses byte Regions when bytes are exposed.
16. Semantic digest and byte digest have different representation bases and claims.
17. Hash-only sublocation bindings are not independently inclusion-verified without target representation or a recognized inclusion proof.
18. Exact binding propagation across capture levels requires exact coordinate-compatible request-transition lineage.
19. prepared_http_body does not prove Provider receipt, complete wire request, or provider-internal prompt.
20. RequestBinding never proves model-internal causality.

## 18. Open items handed to later phases

Part C intentionally does not freeze:

- JSON field names or object layout;
- concrete serialization of capture-scope ownership;
- provider adapter instrumentation APIs;
- semantic canonicalization algorithm selection;
- digest algorithm selection;
- cryptographic inclusion-proof structure;
- rich media selector profiles;
- non-JSON structured path schemes;
- transport-header capture model;
- Provider-originated receipt evidence;
- provider-internal evidence profiles;
- privacy HMAC/redaction wire formats;
- RequestSnapshot streaming body/chunk capture profiles.

These remain constrained by Part C semantics.

## 19. Gate decision

Phase 1 Part C: PASS AFTER ADVERSARIAL REVIEW.

The next specification work is not JSON Schema yet.

Remaining pre-Schema semantic gates include:

~~~text
ModelInvocation / ProviderAttempt / ModelOutput semantics
ToolProposal / ToolInvocation / ToolExecution / ToolResult / EffectObservation semantics
Trust / Taint semantics
Privacy semantics
Integrity / Receipt semantics
Provider adapter contract
Tool adapter contract
Verifier contract
~~~

JSON Schema and implementation remain BLOCKED.
