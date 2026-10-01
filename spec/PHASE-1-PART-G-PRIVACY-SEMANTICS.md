# C2ATrace v0.1 — Phase 1 Part G: Privacy Semantics

Status: DRAFT FOR ADVERSARIAL REVIEW.

Scope: package-relative privacy profiles; full / hash-only / HMAC / redacted semantics; representation disclosure versus commitment; low-entropy leakage and linkability; HMAC verifier capability; redacted representation identity; pre-/post-redaction commitments; privacy-preserving SourceObservation, RequestSnapshot, RequestBinding, Regions, and tool arguments; profile composition; verifier capability downgrade.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Design objective

Part G defines what evidence can be withheld, committed, or redacted while preserving conservative C2ATrace claims.

The central separations are:

~~~text
not disclosed in this Receipt
≠
never observed by Producer
≠
never persisted elsewhere
≠
securely deleted

hash-only
≠
confidential

HMAC commitment
≠
publicly verifiable commitment

redacted representation
≠
original representation

redacted representation verified
≠
pre-redaction representation verified

commitment equality
≠
hidden sublocation membership

privacy reduction
≠
stronger provenance
~~~

Privacy changes disclosure and verifier capability. It does not change historical provenance, Artifact identity, external truth, or claim semantics.

## 2. Privacy is package-relative

### 2.1 Disclosure scope

Privacy treatment is evaluated relative to one concrete C2ATrace disclosure package, normally a Receipt or exported subset.

The same underlying Artifact can be:

- fully disclosed in one authorized package;
- commitment-only in another;
- represented only through a redacted derivative in another;
- unavailable in another.

This does not create new Artifact identity when the underlying Artifact representation itself is unchanged.

### 2.2 Privacy is not runtime non-observation

A privacy profile describes evidence disclosed or retained in the evaluated C2ATrace package.

It does not prove that:

- the Producer never observed plaintext;
- application memory never contained plaintext;
- plaintext was never logged elsewhere;
- plaintext was deleted;
- no other Receipt discloses more.

Storage/deletion guarantees require a separate system/evidence profile.

### 2.3 Privacy is not a provenance edge

Privacy treatment does not create Derivation, RequestBinding, model causality, tool authorization, Effect truth, or Trust.

It changes the evidence available to verify existing claims.

## 3. Privacy profile model

Part G treats full / hash_only / hmac / redacted as named profile presets rather than one primitive evidence enum.

The underlying semantics distinguish:

~~~text
representation disclosure
+
commitment capability
+
optional redacted derivative disclosure
+
scope
~~~

### 3.1 full

full means the original subject representation for the declared scope is disclosed in the evaluated package.

A commitment can also be present.

full does not imply that the representation is externally truthful or complete beyond its existing Artifact semantics.

### 3.2 hash_only

hash_only means:

- the original subject representation is withheld from the evaluated package; and
- an unkeyed commitment value over an explicitly declared representation basis is disclosed.

The exact digest algorithm belongs to the later Integrity / Commitment profile.

### 3.3 hmac

hmac means:

- the original subject representation is withheld from the evaluated package; and
- a keyed commitment/MAC over an explicitly declared representation basis is disclosed.

Candidate verification requires the corresponding secret capability.

Key distribution and lifecycle are outside Part G.

### 3.4 redacted

redacted means the package discloses a redacted derivative representation instead of disclosing the original subject representation.

If the redacted bytes/text are provenance-bearing data, they are represented by a distinct Artifact generated through an explicit redaction Transform.

The original Artifact can remain represented by identity, metadata, and/or a commitment while its representation is withheld.

### 3.5 mixed

mixed means different subscopes of one logical record/package use different privacy treatments.

For example:

~~~text
ToolInvocation arguments:
  /title   → full
  /repo    → full
  /token   → hmac
~~~

mixed is a disclosure summary, not a new cryptographic construction.

### 3.6 unknown

unknown means the available package metadata does not justify a stronger privacy-profile classification.

Unknown is not treated as hidden, safe, encrypted, or commitment-protected.

## 4. Representation availability states

Part G distinguishes at least these semantic availability conditions:

~~~text
original disclosed
original withheld with commitment
redacted derivative disclosed
representation unavailable
availability unknown
~~~

Withheld is not represented by replacing the value with null, empty string, zero, omitted JSON member, or a visual placeholder unless that replacement was the actual underlying representation.

## 5. Commitment semantics under privacy

### 5.1 Commitment scope

Every privacy commitment binds one explicit subject representation scope.

A commitment over a whole Artifact and a commitment over one Region are different claims.

### 5.2 Representation basis

The commitment identifies the exact representation basis being committed, consistent with Parts A and C.

Examples include:

- captured bytes;
- canonical structured representation;
- decoded text under a declared encoding/canonicalization;
- one explicitly selected Region.

### 5.3 Commitment profile

A privacy commitment identifies enough method/profile information to determine:

- whether it is keyed or unkeyed;
- representation-basis compatibility;
- comparison domain;
- whether candidate recomputation is possible for the verifier.

Concrete algorithms remain for Integrity / Commitment profiles.

### 5.4 Commitment equality

Two compatible disclosed commitment values can be compared for value equality.

That supports only the bounded commitment-level statements permitted by Parts A/C.

It does not by itself establish external origin, Provider receipt, hidden sublocation membership, or Producer honesty.

## 6. Hash-only leakage

### 6.1 Dictionary confirmation

An unkeyed deterministic digest can allow an observer to test candidate values.

Low-entropy values such as:

- booleans;
- small enums;
- short identifiers;
- common prompt fragments;
- known email addresses;
- small numeric domains;

can therefore be recoverable or confirmable by enumeration.

### 6.2 Equality linkability

Stable unkeyed commitments can reveal that two hidden representations have the same commitment value when compatible profiles are used.

That can create cross-record or cross-receipt linkability.

### 6.3 Metadata leakage

Hash-only does not hide all metadata.

Depending on the Receipt, observers can still learn:

- Artifact existence;
- graph position;
- source/tool/model metadata;
- path names;
- Region offsets;
- lengths;
- counts;
- timestamps;
- repeated commitment equality.

Part G does not define hash_only as a confidentiality guarantee.

## 7. HMAC / keyed commitment semantics

### 7.1 Secret capability

A keyed commitment verifier needs the required secret capability to recompute the commitment over a candidate representation.

A verifier without the secret cannot independently candidate-match hidden content merely because the tag is present.

### 7.2 Public versus authorized verification

An HMAC-based package can still be independently verified by a verifier that is independent of the Producer and possesses the authorized secret.

This is not public verification.

### 7.3 Secret distribution

The raw keyed-commitment secret is not part of the public commitment evidence model.

Secret distribution, rotation, storage, revocation, and access control are outside Part G.

### 7.4 Key/domain compatibility

Keyed commitments are comparable as representation evidence only under a compatible keyed-commitment profile and comparison domain.

Equal-looking tags with unknown or incompatible key domains are not automatically comparable as hidden-representation equality evidence.

### 7.5 Linkability

Stable HMAC tags can still create equality/linkability within a domain when the same effective key/domain/profile is reused.

HMAC protects against public candidate recomputation by non-key-holders; it does not automatically provide unlinkability.

## 8. Redacted representation identity

### 8.1 Redaction is a Transform

Protocol-level redaction that creates provenance-bearing replacement content is represented as:

~~~text
Original Artifact
    ↓ use
Redaction Transform
    ↓ generate
Redacted Artifact
~~~

The Redacted Artifact has a distinct identity.

### 8.2 No identity substitution

A package does not replace the original Artifact's representation with redacted replacement bytes while retaining the original Artifact identity as if those bytes were original.

If the package omits original content, the omission is represented as unavailable/withheld evidence, not as mutation of the Artifact.

### 8.3 Presentation masking

A user-interface mask that merely hides displayed text is not C2ATrace representation evidence unless it is explicitly represented as a provenance-bearing redacted Artifact.

### 8.4 Redaction lineage

Where the package claims that a redacted Artifact came from an original Artifact, it uses the existing Transform / Derivation model.

Redaction lineage does not by itself prove that sensitive information was fully removed.

## 9. Pre-redaction and post-redaction commitments

A commitment to the original Artifact and a commitment to the redacted derivative are commitments to different representations.

Conceptually:

~~~text
Original Artifact
  commitment C_original

        ↓ Redaction Transform

Redacted Artifact
  commitment C_redacted
~~~

C_original and C_redacted cannot be substituted for each other.

If the original representation is later supplied, C_original can support candidate matching under its profile.

C_redacted verifies only the redacted derivative representation.

## 10. Redaction verification boundary

A verifier with only:

- the redacted derivative; and
- a recorded original commitment;

cannot independently verify that the redaction transform correctly removed every sensitive value unless it also has the required original representation or a recognized privacy-preserving proof/profile.

A valid signature over the redaction lineage does not change that limitation.

## 11. Privacy-preserving SourceObservation

A SourceObservation retains its capture-occurrence identity even when its original representation is withheld.

Examples include:

~~~text
full SourceObservation
commitment-only SourceObservation
SourceObservation with redacted derivative
SourceObservation representation unavailable
~~~

Withholding content does not change SourceRef identity, SourceObservation identity, observation extent, or Producer-asserted origin semantics.

Representation verification is downgraded when required content/capability is unavailable.

## 12. Privacy-preserving RequestSnapshot

A RequestSnapshot retains:

- its Artifact identity;
- capture level;
- owner;
- attempt association;
- existing provenance role;

when its original representation is withheld.

Privacy treatment does not downgrade or upgrade the historical capture-level classification itself.

It only changes what a verifier can independently inspect or recompute.

A hash-only or HMAC prepared_http_body still does not prove Provider receipt.

## 13. Privacy-preserving RequestBinding

### 13.1 Full representation

When required source and target representations are fully available, RequestBinding can reach the Part C verification levels permitted by the evidence.

### 13.2 Whole-scope hash-only

For a binding whose source and target scopes are both whole committed representations, compatible unkeyed commitments can support bounded commitment-level equality without plaintext.

### 13.3 Whole-scope HMAC

For a whole-scope keyed commitment, an authorized verifier with the required secret and candidate representation can recompute and verify the commitment.

A verifier without the secret cannot independently candidate-match hidden plaintext.

### 13.4 Hidden sublocation

A whole-snapshot hash/HMAC does not establish that hidden content exists at a particular path or Region.

A Producer-recorded subregion commitment can be compared, but hidden location membership remains unverified absent the target representation or a recognized inclusion-proof profile.

### 13.5 Redacted target

Verification against a redacted derivative proves facts only about that derivative.

It does not representation-verify the original RequestSnapshot's hidden pre-redaction path/value.

## 14. RequestLocation and Region privacy leakage

RequestLocation metadata can itself be sensitive.

For example:

~~~text
/secrets/api_key
/users/123/email
~~~

or offsets can reveal:

- field existence;
- approximate secret length;
- message structure;
- content placement;
- repeated structure.

Core v0.1 RequestBinding requires enough location information to satisfy its structural semantics.

If required RequestLocation details are withheld, the package cannot present the partial record as a fully structurally validated RequestBinding with those details silently guessed.

A future opaque-location / zero-knowledge inclusion profile can define stronger privacy.

## 15. Tool arguments and secrets

### 15.1 Withheld effective arguments

A ToolInvocation can retain its Artifact identity and execution relationship even when one or more effective argument Regions are withheld from the Receipt.

The package can disclose path/type/provenance metadata and compatible commitments while withholding the value, subject to metadata-leakage caveats.

### 15.2 Withheld is not missing

A privacy-withheld tool argument is semantically distinct from:

- an argument that was absent;
- JSON null;
- empty string;
- default value;
- unknown whether the argument existed.

### 15.3 Placeholder safety

A value such as:

~~~text
"***"
"[REDACTED]"
"<secret>"
~~~

is not represented as the effective ToolInvocation argument value unless that exact value was actually executed.

Presentation placeholders remain outside the effective argument representation.

### 15.4 Secret provenance

Argument-level provenance can remain structurally recorded even when the value is withheld.

Representation-level verification remains bounded by the commitments, candidate material, and verifier capability that are actually available.

### 15.5 Execution does not disclose the secret

The existence or completion of ToolExecution does not authorize a verifier to infer the hidden effective argument representation.

## 16. Profile composition

### 16.1 Region-level composition

Different Regions of one Artifact can use different disclosure treatments in the same package.

The package can summarize that condition as mixed.

### 16.2 Parent disclosure dominates actual secrecy

If a fully disclosed parent representation contains a child Region in plaintext, declaring the child Region hash_only or hmac does not make the child undisclosed in that package.

Privacy claims are bounded by the most revealing actual disclosure path.

### 16.3 Duplicate disclosure

Withholding one occurrence does not prove confidentiality if the same representation is disclosed elsewhere in the same package through another Artifact, field, derivative, log-like metadata, or reversible representation.

Core can detect only disclosures represented in the supplied package; it does not prove absence of external copies.

### 16.4 Multiple packages

A privacy claim about one Receipt does not prove that another Receipt, export, log, or runtime store does not reveal more.

Cross-package privacy aggregation is outside core v0.1.

## 17. Commitment linkability and comparison domains

A commitment profile can trade privacy for comparability.

Stable commitments can enable equality joins across records or Receipts.

Domain separation, key rotation, randomization, or other future profile mechanisms can reduce linkability, but can also reduce direct cross-domain equality verification.

Part G does not freeze the cryptographic construction; the profile must make its comparison domain explicit enough for the verifier not to compare incompatible commitments.

## 18. Privacy and Taint

Privacy treatment and Taint are independent.

Examples:

- secret content can be HMAC-withheld while taint_kind=secret remains present;
- redaction can produce a downstream sanitizer assertion under Part F;
- withholding a value does not clear taint;
- full disclosure does not create taint;
- a privacy profile is not a TrustAssertion.

Part G does not use privacy labels to alter Trust/Taint state.

## 19. Verification capability model

Verifier results depend on both disclosed evidence and verifier-held capabilities.

Conceptually relevant capabilities include:

~~~text
has original representation
has candidate representation
has keyed-commitment secret
has compatible commitment profile
has recognized inclusion/redaction proof
has only the public Receipt
~~~

A verifier reports only claims supported by its actual capability set.

### 19.1 Capability examples

| Evidence/capability | What can be established |
|---|---|
| Full representation only | Inspect representation; no commitment check unless commitment exists |
| Full representation + compatible unkeyed commitment | Recompute commitment; representation/commitment match |
| Hidden representation + unkeyed commitment only | Commitment value recorded; no direct plaintext inspection |
| Candidate + unkeyed commitment | Candidate commitment match under profile |
| Hidden representation + HMAC tag, no key | Tag exists/integrity can be checked; no candidate recomputation |
| Candidate + HMAC tag + correct secret | Candidate keyed-commitment match |
| Redacted derivative + its commitment | Verify redacted derivative only |
| Redacted derivative + original commitment | Does not by itself verify redaction correctness |
| Whole-snapshot commitment + hidden subpath claim | Does not prove subpath membership |
| Recognized inclusion proof | Can establish only the membership claim defined by that proof profile |

## 20. Verification-strength downgrade

Privacy omission never strengthens a claim.

If evidence required for a stronger verification level is withheld:

~~~text
representation-verified
→ commitment-matched / structural / unverified
~~~

as applicable.

A verifier does not fill missing evidence with assumptions merely because the omission was intentional for privacy.

## 21. Privacy claim matrix

| Claim | Evidence | Core Part G interpretation |
|---|---|---|
| Original representation appears in this Receipt | Direct package inspection | Disclosure fact only |
| Original representation is withheld in this Receipt | Package structure/profile | Package-relative only |
| Producer never stored plaintext | unsupported by privacy profile | Requires separate evidence |
| Hash-only hides low-entropy value | prohibited generic claim | Candidate enumeration can leak |
| HMAC candidate matches | Candidate + compatible secret/profile | Authorized keyed commitment check |
| HMAC is publicly verifiable | false in general | Secret capability is required for recomputation |
| Redacted derivative matches its commitment | Redacted representation + commitment | Redacted representation only |
| Redacted derivative correctly removed all secrets | unsupported without additional evidence | Requires original/proof/policy verification |
| Whole-scope commitments match | Compatible commitments | Bounded commitment equality |
| Hidden subrange is present at claimed path | unsupported from whole commitment | Needs target representation/inclusion proof |
| Secret ToolInvocation arg was absent | prohibited from withheld evidence | Withheld ≠ absent |
| Receipt is privacy-preserving globally | unsupported | Other packages/stores can disclose more |

## 22. Normative requirements

### PRIV-001 — Privacy treatment is disclosure-scope relative

A verifier MUST interpret a privacy profile relative to the concrete Receipt/disclosure package being evaluated and MUST NOT treat that profile as an intrinsic permanent property of the underlying Artifact.

Planned test: privacy-package-relative-001.

### PRIV-002 — Privacy profile is not non-observation proof

A verifier MUST NOT report package-level withholding as proof that the Producer/application never observed the original representation.

Planned test: privacy-not-runtime-nonobservation-001.

### PRIV-003 — Privacy profile is not deletion proof

A verifier MUST NOT report package-level withholding, hash_only, hmac, or redacted treatment as proof that plaintext was securely deleted or never persisted elsewhere.

Planned test: privacy-not-deletion-proof-001.

### PRIV-004 — Other-package disclosure remains unknown

A verifier MUST NOT infer from one Receipt's privacy profile that no other Receipt, export, log, process memory, or storage contains a more revealing representation.

Planned test: privacy-not-global-disclosure-proof-001.

### PRIV-005 — Privacy treatment does not create provenance

A verifier MUST NOT synthesize Derivation, RequestBinding, model causality, ToolDecision, Effect truth, Trust, or Taint solely from a privacy profile.

Planned test: privacy-no-provenance-upgrade-001.

### PRIV-006 — full profile means original representation disclosed

A scope classified as full MUST refer to the original subject representation being disclosed in the evaluated package rather than merely a derivative or placeholder representation.

Planned test: privacy-full-original-001.

### PRIV-007 — hash_only withholds original representation

A scope classified as hash_only MUST NOT simultaneously represent the original subject plaintext/bytes as disclosed through that same privacy scope.

Planned test: privacy-hash-only-withheld-001.

### PRIV-008 — hash_only uses unkeyed commitment semantics

A scope classified as hash_only MUST identify an unkeyed commitment method/profile and explicit representation basis.

Planned test: privacy-hash-only-profile-001.

### PRIV-009 — hmac withholds original representation

A scope classified as hmac MUST NOT simultaneously represent the original subject plaintext/bytes as disclosed through that same privacy scope.

Planned test: privacy-hmac-withheld-001.

### PRIV-010 — hmac uses keyed commitment semantics

A scope classified as hmac MUST identify a keyed commitment/MAC profile, representation basis, and key/comparison-domain reference sufficient to determine verification compatibility without exposing the raw secret key.

Planned test: privacy-hmac-profile-001.

### PRIV-011 — redacted profile uses derivative representation

A scope classified as redacted MUST NOT substitute redacted replacement bytes/text for the original Artifact representation under the original Artifact identity.

Planned test: privacy-redacted-no-identity-substitution-001.

### PRIV-012 — mixed profile is valid

A conforming privacy representation MUST permit different subscopes of one Artifact/record to use different privacy treatments.

Planned test: privacy-mixed-profile-001.

### PRIV-013 — unknown privacy remains unknown

A verifier MUST NOT upgrade privacy profile=unknown to full, hash_only, hmac, redacted, or mixed based solely on payload shape or missing content.

Planned test: privacy-profile-unknown-001.

### PRIV-014 — Withheld is not empty

A verifier MUST NOT interpret privacy-withheld representation content as an empty string, zero-length bytes, null, zero, false, empty object/array, or omitted semantic value unless that value is independently established as the actual representation.

Planned test: privacy-withheld-not-empty-001.

### PRIV-015 — Withheld is not absent

A verifier MUST NOT infer that a structured field/argument did not exist solely because its value is withheld from the disclosed representation.

Planned test: privacy-withheld-not-absent-001.

### PRIV-016 — Presentation placeholder is not underlying value

A verifier MUST NOT treat a presentation placeholder or masking token as the original/effective representation unless the provenance record establishes that the placeholder itself was the actual runtime representation.

Planned test: privacy-placeholder-not-value-001.

### PRIV-017 — Withholding does not change Artifact identity

A package MUST NOT create a new Artifact identity solely because the same underlying immutable representation is disclosed with less evidence in that package.

Planned test: privacy-withholding-no-new-artifact-001.

### PRIV-018 — Different redacted bytes require different Artifact identity

A provenance-bearing redacted representation that differs from the original MUST have its own Artifact identity.

Planned test: privacy-redacted-new-artifact-001.

### PRIV-019 — Privacy must preserve required internal references

A privacy treatment MUST NOT make required normative internal references unresolved while still claiming the Receipt satisfies GRAPH-001.

Planned test: privacy-reference-resolution-001.

### PRIV-020 — Commitment subject scope is explicit

Every privacy commitment MUST identify the exact Artifact or Region representation scope it commits.

Planned test: privacy-commitment-scope-001.

### PRIV-021 — Commitment representation basis is explicit

Every privacy commitment MUST identify the representation basis required to interpret or recompute it.

Planned test: privacy-commitment-basis-001.

### PRIV-022 — Commitment profile is explicit

Every privacy commitment MUST identify enough method/profile information to distinguish keyed from unkeyed operation and determine compatibility.

Planned test: privacy-commitment-profile-001.

### PRIV-023 — Incompatible commitments are not compared as representation evidence

A verifier MUST NOT use commitment equality as representation-equality evidence when commitment method/profile, representation basis, key domain, or comparison domain is incompatible or unknown.

Planned test: privacy-commitment-compatibility-001.

### PRIV-024 — Commitment equality is bounded

A verifier MUST NOT report equal commitment values as establishing SourceRef identity, Artifact occurrence identity, external origin, Provider receipt, or hidden sublocation membership.

Planned test: privacy-commitment-equality-bounded-001.

### PRIV-025 — Hash-only is not confidentiality proof

A verifier MUST NOT describe an unkeyed hash_only profile as proving confidentiality or resistance to candidate enumeration.

Planned test: privacy-hash-not-confidentiality-001.

### PRIV-026 — Low-entropy hash risk is preserved

A conforming privacy/verifier report MUST NOT imply that low-entropy values are safely hidden merely because only an unkeyed commitment is disclosed.

Planned test: privacy-hash-low-entropy-001.

### PRIV-027 — Stable hash equality can leak linkability

A verifier MUST NOT describe deterministic compatible hash_only commitments as unlinkable when their equality can be observed across disclosed records.

Planned test: privacy-hash-linkability-001.

### PRIV-028 — HMAC candidate verification requires secret capability

A verifier MUST NOT report a keyed-commitment candidate as independently matched unless it possesses the required secret capability or relies on a separately recognized trusted verification result.

Planned test: privacy-hmac-secret-required-001.

### PRIV-029 — HMAC is not public verification by default

A verifier without the required secret MUST NOT describe an HMAC/keyed commitment as publicly recomputable or publicly candidate-verifiable.

Planned test: privacy-hmac-not-public-001.

### PRIV-030 — Authorized secret verifier can remain independent

A verifier MUST NOT equate independent verification with public verification; an independent authorized verifier possessing the required secret MAY verify a keyed commitment under its profile.

Planned test: privacy-hmac-authorized-independent-001.

### PRIV-031 — Raw HMAC key is not commitment evidence

A public/disclosed C2ATrace package MUST NOT require embedding raw keyed-commitment secret material as part of the commitment evidence itself.

Planned test: privacy-hmac-no-raw-key-001.

### PRIV-032 — HMAC key/domain compatibility is required

A verifier MUST NOT compare HMAC/keyed commitments as hidden-representation equality evidence when the effective key/comparison domains are incompatible or unknown.

Planned test: privacy-hmac-domain-compatibility-001.

### PRIV-033 — HMAC is not unlinkability proof

A verifier MUST NOT report stable keyed commitments as unlinkable solely because observers lack the key.

Planned test: privacy-hmac-no-unlinkability-001.

### PRIV-034 — Redaction is explicit transformation

When a package claims a provenance-bearing redacted Artifact derives from an original Artifact, it MUST identify the applicable redaction Transform / Derivation lineage.

Planned test: privacy-redaction-lineage-001.

### PRIV-035 — Redaction lineage is not redaction correctness proof

A verifier MUST NOT infer that sensitive information was completely removed solely because a redaction Transform / Derivation is recorded.

Planned test: privacy-redaction-no-correctness-001.

### PRIV-036 — Pre/post commitments remain distinct

A verifier MUST NOT substitute a commitment to the redacted derivative for a commitment to the original representation or vice versa.

Planned test: privacy-redaction-commitment-separation-001.

### PRIV-037 — Redacted commitment verifies only redacted representation

A verifier MUST NOT report a verified commitment over a redacted derivative as verification of the unavailable pre-redaction representation.

Planned test: privacy-redacted-not-original-001.

### PRIV-038 — Original commitment does not verify redaction

A verifier MUST NOT infer redaction correctness solely from the presence or validity of a commitment to the original representation.

Planned test: privacy-original-commitment-no-redaction-proof-001.

### PRIV-039 — Signature does not verify redaction effectiveness

A verifier MUST NOT infer that a redaction removed all sensitive data solely because the redaction records or Receipt are cryptographically signed.

Planned test: privacy-signature-no-redaction-proof-001.

### PRIV-040 — SourceObservation commitment-only form is valid

A conforming representation MUST permit SourceObservation identity/provenance metadata to remain present while its original representation is withheld and only compatible commitment evidence is disclosed.

Planned test: privacy-source-commitment-only-001.

### PRIV-041 — SourceObservation privacy does not alter source identity

A verifier MUST NOT infer a new SourceRef or SourceObservation identity solely because the observation representation is withheld, commitment-only, or disclosed through a redacted derivative.

Planned test: privacy-source-identity-stable-001.

### PRIV-042 — Source representation withholding downgrades verification

A verifier MUST NOT report SourceObservation representation verification that requires unavailable content/capability.

Planned test: privacy-source-verification-downgrade-001.

### PRIV-043 — RequestSnapshot commitment-only form is valid

A conforming representation MUST permit RequestSnapshot identity, capture level, ownership, and attempt association to remain recorded while its original representation is withheld.

Planned test: privacy-request-commitment-only-001.

### PRIV-044 — Privacy does not change capture level

A verifier MUST NOT change or infer a stronger/weaker RequestSnapshot capture_level solely from full/hash_only/hmac/redacted privacy treatment.

Planned test: privacy-request-capture-level-stable-001.

### PRIV-045 — Private request evidence does not prove Provider receipt

A verifier MUST NOT infer Provider receipt from a hash_only, hmac, full, or redacted RequestSnapshot merely because its privacy/commitment evidence validates.

Planned test: privacy-request-no-provider-receipt-001.

### PRIV-046 — Whole-scope unkeyed commitment equality remains bounded

For whole-scope source and target representations with compatible unkeyed commitments, a verifier MAY report commitment-level equality while preserving the Part C limits on Producer assertion, identity, and external truth.

Planned test: privacy-whole-hash-equality-001.

### PRIV-047 — Whole-scope HMAC candidate match requires capability

A verifier MAY report whole-scope keyed candidate matching only when it has the required candidate representation, secret capability, and compatible profile.

Planned test: privacy-whole-hmac-match-001.

### PRIV-048 — Whole commitment does not prove hidden sublocation

A verifier MUST NOT report a hidden RequestBinding subpath/subrange as location-resolved or representation-verified solely from a whole-snapshot hash/HMAC commitment.

Planned test: privacy-binding-whole-commitment-no-location-001.

### PRIV-049 — Subregion commitment does not prove membership

A verifier MUST NOT report a hidden subregion as contained at a claimed RequestLocation solely because a separately recorded source and target-subregion commitment value match.

Planned test: privacy-binding-subregion-no-membership-001.

### PRIV-050 — Redacted derivative does not verify original binding

A verifier MUST NOT use a redacted derivative representation to representation-verify the unavailable original RequestSnapshot binding unless a recognized proof/profile establishes the original claim.

Planned test: privacy-binding-redacted-no-original-001.

### PRIV-051 — Withheld RequestLocation prevents full structural/location verification

When required RequestLocation/path/Region metadata is withheld, a verifier MUST NOT claim the hidden location is structurally/location resolved by guessing or reconstructing undeclared details.

Planned test: privacy-binding-hidden-location-001.

### PRIV-052 — Privacy does not upgrade RequestBinding evidence

A verifier MUST NOT report stronger RequestBinding verification merely because content was intentionally withheld for privacy.

Planned test: privacy-binding-no-upgrade-001.

### PRIV-053 — RequestLocation metadata leakage is not hidden by content withholding

A verifier MUST NOT describe a privacy profile as hiding request structure when disclosed RequestLocation paths/Regions reveal that structure.

Planned test: privacy-location-metadata-leakage-001.

### PRIV-054 — Length/offset metadata can leak

A verifier/privacy report MUST NOT imply zero content leakage when disclosed lengths, offsets, counts, or Region boundaries can reveal information about hidden representations.

Planned test: privacy-region-length-leakage-001.

### PRIV-055 — Withheld tool argument is not missing

A verifier MUST NOT infer that a ToolInvocation argument was absent solely because its effective value is withheld under privacy treatment.

Planned test: privacy-tool-arg-withheld-not-missing-001.

### PRIV-056 — Tool placeholder is not effective value

A verifier MUST NOT treat a masking/redaction placeholder as the effective ToolInvocation argument unless that exact placeholder was the runtime effective value.

Planned test: privacy-tool-placeholder-not-effective-001.

### PRIV-057 — Hidden tool argument limits representation verification

A verifier MUST NOT report exact effective argument representation verification when the argument value is unavailable and no compatible candidate/commitment/proof capability establishes it.

Planned test: privacy-tool-arg-verification-downgrade-001.

### PRIV-058 — ToolExecution does not reveal hidden arguments

A verifier MUST NOT infer the hidden ToolInvocation argument representation solely from ToolExecution occurrence, completion, ToolResult status, or EffectObservation.

Planned test: privacy-tool-execution-no-secret-inference-001.

### PRIV-059 — Argument provenance survives withholding only at available evidence strength

A verifier MAY preserve structurally recorded argument provenance for withheld values but MUST NOT report stronger representation-level derivation verification than the disclosed commitments/capabilities support.

Planned test: privacy-tool-provenance-bounded-001.

### PRIV-060 — Region-level privacy composition is permitted

A conforming representation MUST permit privacy treatment at Artifact Region granularity when the underlying Artifact/Region semantics support such scope.

Planned test: privacy-region-composition-001.

### PRIV-061 — Full parent disclosure defeats child withholding claim in that representation

If a fully disclosed parent representation includes a child Region's plaintext, a verifier MUST NOT describe that child as undisclosed in the same package merely because separate metadata labels the child hash_only or hmac.

Planned test: privacy-parent-disclosure-overrides-label-001.

### PRIV-062 — Duplicate disclosure defeats package-local withholding claim

A verifier MUST NOT describe a representation as withheld from the package when the same representation is directly disclosed elsewhere in that package and the equivalence is established.

Planned test: privacy-duplicate-disclosure-001.

### PRIV-063 — Package privacy is not global privacy

A verifier MUST NOT describe one Receipt's disclosure treatment as proof that equivalent plaintext is absent from other packages or external systems.

Planned test: privacy-package-not-global-001.

### PRIV-064 — Stable commitments can create linkability

A verifier/privacy report MUST preserve that stable comparable commitment values can create equality linkability across the comparison domain.

Planned test: privacy-commitment-linkability-001.

### PRIV-065 — Privacy profile is not anonymity proof

A verifier MUST NOT report hash_only, hmac, redacted, or mixed treatment as establishing anonymity or unlinkability unless a separate profile establishes that property.

Planned test: privacy-no-anonymity-upgrade-001.

### PRIV-066 — Signature/integrity does not add confidentiality

A verifier MUST NOT infer confidentiality, secrecy, redaction effectiveness, or non-disclosure solely from cryptographic integrity/signature validity.

Planned test: privacy-integrity-no-confidentiality-001.

### PRIV-067 — Privacy does not clear taint

A verifier MUST NOT clear or weaken TaintAssertion state solely because the representation is hash_only, hmac, withheld, or redacted for disclosure.

Planned test: privacy-no-taint-clear-001.

### PRIV-068 — Privacy does not create trust

A verifier MUST NOT synthesize TrustAssertion(state=trusted) solely from a privacy treatment.

Planned test: privacy-no-trust-upgrade-001.

### PRIV-069 — Privacy omission cannot strengthen provenance

A verifier MUST NOT strengthen SourceObservation, Derivation, RequestBinding, ToolInvocation, EffectObservation, or other provenance claims because evidence was omitted for privacy.

Planned test: privacy-no-provenance-strengthening-001.

### PRIV-070 — Verification follows actual capability set

A verifier MUST report verification results according to the representations, candidate values, secrets, commitments, and recognized proof profiles it actually possesses.

Planned test: privacy-verifier-capability-001.

### PRIV-071 — HMAC tag presence is not HMAC recomputation

A verifier without the required secret MUST NOT report a keyed commitment as recomputed/verified merely because the tag syntax, signature, or recorded value is valid.

Planned test: privacy-hmac-tag-not-recomputed-001.

### PRIV-072 — Candidate match requires candidate

A verifier MUST NOT report hidden representation candidate matching when it does not possess the candidate representation required by the applicable commitment profile.

Planned test: privacy-candidate-required-001.

### PRIV-073 — Redacted-only verifier is bounded to redacted representation

A verifier possessing only a redacted derivative MUST NOT report verification of unavailable original plaintext/bytes.

Planned test: privacy-redacted-only-capability-001.

### PRIV-074 — Weakest evidence premise is preserved

When a privacy-preserving claim composes structural, representation, producer-asserted, keyed-secret, or proof premises, verifier output MUST preserve the weakest unresolved premise rather than reporting the strongest component as the whole claim strength.

Planned test: privacy-composed-evidence-001.

### PRIV-075 — Privacy-unavailable representation is not representation-verified

A verifier MUST NOT report representation-verified equality for a hidden/unavailable representation solely because an Artifact ID, path, length, or unsigned commitment value is present.

Planned test: privacy-unavailable-not-verified-001.

### PRIV-076 — Privacy profile does not prove encryption

A verifier MUST NOT describe hash_only, hmac, redacted, mixed, or unknown profiles as encryption unless a separate encryption profile explicitly establishes encrypted representation semantics.

Planned test: privacy-no-encryption-inference-001.

## 23. Adversarial architecture review

### Review A — Same SourceObservation, two disclosure packages

Internal package discloses full source content.

External package discloses only its commitment.

The SourceObservation identity stays the same; privacy treatment is package-relative.

Result: RESOLVED by PRIV-001 and PRIV-017.

### Review B — Low-entropy boolean stored hash-only

The digest of true/false can be enumerated immediately.

hash_only does not justify a confidentiality claim.

Result: RESOLVED by PRIV-025 through PRIV-027.

### Review C — Email address hash-only

A public verifier can test a candidate list of likely email addresses against an unkeyed deterministic commitment.

Result: RESOLVED by PRIV-025 and PRIV-026.

### Review D — HMAC receipt given to public verifier

The public verifier sees a keyed tag but has no secret.

It can validate structure/integrity of the record but cannot recompute the hidden candidate commitment.

Result: RESOLVED by PRIV-028, PRIV-029, and PRIV-071.

### Review E — Independent auditor receives HMAC key

The auditor is independent of the Producer but authorized to hold the key.

The auditor can perform candidate verification without making the commitment publicly verifiable.

Result: RESOLVED by PRIV-030.

### Review F — Same HMAC reused across many Receipts

Observers can correlate equal stable tags inside the comparison domain even without knowing the plaintext.

Result: RESOLVED by PRIV-033 and PRIV-064.

### Review G — Redacted text stored under original Artifact ID

This would mutate/substitute the immutable representation.

The redacted data must be a distinct derivative Artifact or remain mere presentation masking.

Result: RESOLVED by PRIV-011, PRIV-018, and PRIV-034.

### Review H — Redacted derivative plus signed provenance

Signature validates the recorded redaction lineage but does not prove all sensitive content was removed.

Result: RESOLVED by PRIV-035 and PRIV-039.

### Review I — Original hash plus redacted representation

The original commitment can later candidate-match the original when the candidate is supplied.

It does not make the redacted derivative a verified faithful/safe redaction.

Result: RESOLVED by PRIV-036 through PRIV-038.

### Review J — Hash-only SourceObservation

The SourceObservation capture occurrence and SourceRef relation remain represented.

The verifier cannot inspect hidden bytes and downgrades representation claims accordingly.

Result: RESOLVED by PRIV-040 through PRIV-042.

### Review K — Hash-only prepared_http_body

The body commitment can preserve bounded equality checks.

It still does not prove that the Provider received those bytes.

Result: RESOLVED by PRIV-043 through PRIV-045.

### Review L — Hash-only RequestBinding with hidden JSON path target

Whole-request commitment does not prove that the hidden value exists at /messages/3/content.

Result: RESOLVED by PRIV-048 and PRIV-049.

### Review M — Path itself is secret

If the package withholds required RequestLocation details, the verifier cannot pretend the complete RequestBinding location was structurally resolved.

Result: RESOLVED by PRIV-051.

### Review N — Request content hidden but offsets retained

Offsets and lengths can leak structure and approximate secret size.

Result: RESOLVED by PRIV-053 and PRIV-054.

### Review O — Tool token replaced by "***"

If the real executed token was secret XYZ, the C2ATrace ToolInvocation must not claim "***" was the effective value.

The secret can be withheld with commitment metadata while retaining argument existence/provenance.

Result: RESOLVED by PRIV-055 through PRIV-059.

### Review P — Parent ToolInvocation JSON is full, child token says hmac

The plaintext token is already present inside the parent representation.

The child privacy label cannot undo actual disclosure.

Result: RESOLVED by PRIV-061.

### Review Q — Secret withheld in one field but copied into error metadata

If equivalence is established and the error metadata reveals the same plaintext inside the package, the value is not actually withheld package-wide.

Result: RESOLVED by PRIV-062.

### Review R — Redaction clears secret taint automatically

Privacy redaction and Part F taint discharge are distinct.

A separate sanitizer TaintAssertion/policy rule is needed.

Result: RESOLVED by PRIV-067 and Part F.

### Review S — Signed hash-only receipt described as confidential

Integrity proves neither confidentiality nor low-entropy resistance.

Result: RESOLVED by PRIV-025 and PRIV-066.

### Review T — HMAC tag from unknown key domain equals another tag

Raw string equality does not establish hidden-representation equality under an unknown/incompatible keyed comparison domain.

Result: RESOLVED by PRIV-032.

### Review U — Hidden candidate not available

A verifier cannot report candidate matching merely because a commitment is present.

Result: RESOLVED by PRIV-070 through PRIV-072.

### Review V — Mixed privacy Artifact

Some fields are full, one secret is HMAC-withheld, one long text is hash-only.

The artifact can remain one immutable underlying representation; the disclosure package is mixed.

Result: RESOLVED by PRIV-012 and PRIV-060.

### Review W — Same Artifact appears full in another Receipt

The privacy claim remains limited to the evaluated Receipt and cannot establish global non-disclosure.

Result: RESOLVED by PRIV-004 and PRIV-063.

### Review X — Privacy hides a required referenced object

A package cannot both remove the referenced object and still claim internal-reference conformance under GRAPH-001.

It must retain a resolvable privacy-safe record, use a future external-reference mechanism, or accept that the package is not conforming to that internal-reference requirement.

Result: RESOLVED by PRIV-019.

### Review Y — Redacted representation verified, original described as verified

This is a direct evidence-scope upgrade and is prohibited.

Result: RESOLVED by PRIV-037 and PRIV-073.

### Review Z — HMAC called encryption

A keyed commitment authenticates/compares candidates under its profile; it is not ciphertext.

Result: RESOLVED by PRIV-076.

## 24. Architecture revisions caused by Part G

### 24.1 Privacy is disclosure-package metadata, not Artifact identity

The same immutable Artifact can be disclosed with different privacy treatments to different audiences without changing identity.

### 24.2 Profiles are compositional presets

full / hash_only / hmac / redacted describe common combinations of disclosure and commitment behavior.

The protocol semantics remain explicit about representation disclosure, commitment profile, scope, and verifier capability.

### 24.3 Redacted provenance uses a new Artifact

Provenance-bearing redaction creates a derivative Artifact through Transform / Derivation.

This preserves GRAPH-002 immutability and prevents placeholders from becoming fake historical values.

### 24.4 HMAC separates independent from public verification

An authorized key holder can independently verify a keyed commitment.

A public verifier without the key cannot recompute it.

### 24.5 Privacy can only preserve or reduce verification strength

Withholding evidence never upgrades provenance.

This rule applies uniformly to SourceObservation, RequestBinding, ToolInvocation, and all other privacy-preserved records.

## 25. Part G resolved decisions

Part G locks the following decisions:

1. Privacy treatment is relative to a concrete Receipt/disclosure package, not intrinsic to Artifact identity.
2. Privacy profiles do not prove non-observation, non-persistence, deletion, or global confidentiality.
3. full / hash_only / hmac / redacted are compositional profile presets.
4. Withheld content is not represented as null, empty, missing, or a fake placeholder.
5. Withholding the same immutable representation does not create a new Artifact identity.
6. Provenance-bearing redacted content is a distinct derivative Artifact.
7. Privacy commitments identify explicit subject scope, representation basis, and compatible method/profile.
8. hash_only is not a confidentiality guarantee and can leak low-entropy values and equality linkability.
9. HMAC candidate verification requires a secret capability and is not public verification by default.
10. Stable HMAC values can still leak equality/linkability within a comparison domain.
11. Pre-redaction and post-redaction commitments remain distinct.
12. Redacted representation verification does not verify the hidden original or redaction correctness.
13. SourceObservation and RequestSnapshot provenance identity survives representation withholding.
14. Privacy does not change RequestSnapshot capture level or prove Provider receipt.
15. Whole-scope commitment equality does not establish hidden RequestBinding sublocation membership.
16. Withholding RequestLocation metadata prevents stronger location verification.
17. Paths, Regions, lengths, counts, and commitments can themselves leak metadata.
18. ToolInvocation secret arguments can be withheld without pretending they were absent or replaced by placeholders.
19. Region-level mixed privacy is supported.
20. Actual full parent/duplicate disclosure defeats a contradictory package-local withholding claim.
21. One Receipt's privacy profile does not establish privacy of other packages or stores.
22. Privacy treatment does not clear taint, create trust, or strengthen provenance.
23. Verifier results depend on actual candidate/secret/proof capabilities.
24. Independent keyed verification is distinct from public verification.
25. Integrity/signature validity does not add confidentiality.
26. Privacy profiles are not encryption unless a separate encryption profile establishes that semantic.

## 26. Open items handed to later phases

Part G intentionally does not freeze:

- JSON field names or privacy-descriptor wire structure;
- exact digest/MAC algorithms;
- canonicalization algorithms;
- key identifiers and key-management system;
- secret distribution/rotation/revocation;
- domain-separation construction;
- randomized commitments;
- encryption profiles;
- zero-knowledge/inclusion proofs;
- opaque RequestLocation proof profiles;
- secure deletion/retention attestations;
- access-control policy;
- cross-Receipt privacy aggregation;
- privacy budget/differential privacy semantics.

These remain constrained by Part G semantics.

## 27. Gate decision

Phase 1 Part G is ready for adversarial/mechanical review.

JSON Schema and implementation remain BLOCKED.
